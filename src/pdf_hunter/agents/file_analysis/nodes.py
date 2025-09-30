import os
import logging
import asyncio
from .schemas import FileAnalysisState, MissionStatus, InvestigatorState
from pdf_hunter.shared.analyzers.wrappers import run_pdfid, run_pdf_parser_full_statistical_analysis, run_peepdf
from .prompts import file_analysis_triage_system_prompt, file_analysis_triage_user_prompt, file_analysis_investigator_system_prompt, file_analysis_investigator_user_prompt
import json
from langgraph.types import Command
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.constants import Send
from langchain_core.messages.utils import get_buffer_string
from .tools import pdf_parser_tools_manifest, pdf_parser_tools
from pdf_hunter.shared.utils.logging_config import get_logger

logger = get_logger(__name__)
from .schemas import EvidenceGraph, MergedEvidenceGraph
from typing import List, Literal
from .prompts import file_analysis_graph_merger_system_prompt, file_analysis_graph_merger_user_prompt
from .prompts import file_analysis_reviewer_system_prompt, file_analysis_reviewer_user_prompt
from .prompts import file_analysis_finalizer_system_prompt, file_analysis_finalizer_user_prompt
from pdf_hunter.config import file_analysis_triage_llm, file_analysis_investigator_llm, file_analysis_graph_merger_llm, file_analysis_reviewer_llm, file_analysis_finalizer_llm
from pdf_hunter.config import THINKING_TOOL_ENABLED
from .schemas import TriageReport,MissionReport, ReviewerReport,FinalReport
from pdf_hunter.shared.utils.serializer import dump_state_to_file

if THINKING_TOOL_ENABLED:
    from pdf_hunter.shared.tools.think_tool import think_tool
    pdf_parser_tools_manifest[think_tool.name] = think_tool.description
    pdf_parser_tools.append(think_tool)

llm_router = file_analysis_triage_llm.with_structured_output(TriageReport)
llm_investigator = file_analysis_investigator_llm.with_structured_output(MissionReport)
llm_investigator_with_tools = file_analysis_investigator_llm.bind_tools(pdf_parser_tools)
llm_graph_merger = file_analysis_graph_merger_llm.with_structured_output(MergedEvidenceGraph)
llm_reviewer = file_analysis_reviewer_llm.with_structured_output(ReviewerReport)
llm_finalizer = file_analysis_finalizer_llm.with_structured_output(FinalReport)


async def identify_suspicious_elements(state: FileAnalysisState):
    logger.info("Identifying Suspicious Elements")
    
    try:
        file_path = state.get('file_path')
        
        # Validate required inputs
        if not file_path:
            raise ValueError("file_path is required")
        
        logger.debug(f"Analyzing file: {file_path}")

        logger.debug("Running pdfid analysis")
        pdfid_output = await run_pdfid(file_path)
        
        logger.debug("Running pdf-parser statistical analysis")
        pdf_parser_output = await run_pdf_parser_full_statistical_analysis(file_path)
        
        logger.debug("Running peepdf analysis")
        peepdf_output = await run_peepdf(file_path)
        
        structural_summary = {"pdfid": pdfid_output, "pdf_parser": pdf_parser_output, "peepdf": peepdf_output}
        additional_context = state.get('additional_context', "None")
        logger.debug("Static analysis tools completed")

        system_prompt = file_analysis_triage_system_prompt
        user_prompt = file_analysis_triage_user_prompt.format(
            additional_context=additional_context,
            structural_summary=json.dumps(structural_summary)
        )

        logger.debug("Preparing LLM triage analysis")
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        logger.debug("Invoking triage LLM")
        result = await llm_router.ainvoke(messages)
        logger.debug(f"Triage completed with decision: {result.triage_classification_decision}")

        updates = {
            "structural_summary": structural_summary,
            "triage_classification_decision": result.triage_classification_decision,
            "triage_classification_reasoning": result.triage_classification_reasoning,
            "mission_list": result.mission_list
        }

        if result.triage_classification_decision == "innocent":
            logger.info("Triage Decision: PDF is Innocent. Ending investigation.")
        elif result.triage_classification_decision == "suspicious":
            logger.info(f"Triage Decision: PDF is Suspicious. Found {len(result.mission_list)} mission(s).")
            if logger.isEnabledFor(logging.DEBUG):
                for idx, mission in enumerate(result.mission_list):
                    logger.debug(f"Mission {idx+1}: {mission.objective} (Priority: {mission.priority})")
        else:
            error_msg = "Invalid triage classification decision from LLM"
            logger.error(error_msg)
            updates["errors"] = [error_msg]

        return updates
    
    except Exception as e:
        error_msg = f"Error in identify_suspicious_elements: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": [error_msg]}


async def create_analysis_tasks(state: FileAnalysisState):
    logger.info("Creating analysis tasks")
    
    try:
        mission_list = state.get('mission_list', [])
        updated_missions = []
        task_count = 0
        
        for mission in mission_list:
            if mission.status == MissionStatus.NEW:
                mission.status = MissionStatus.IN_PROGRESS
                task_count += 1
                logger.debug(f"Queuing mission for threat type: {mission.threat_type}")
            updated_missions.append(mission)
        
        logger.info(f"Updated {task_count} missions to IN_PROGRESS status")
        return {"mission_list": updated_missions}
    
    except Exception as e:
        error_msg = f"Error in create_analysis_tasks: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": [error_msg]}


async def assign_analysis_tasks(state: FileAnalysisState): 
    """
    Dispatches all missions currently in 'NEW' status to the investigator pool.
    Updates the status of dispatched missions to 'IN_PROGRESS'.
    """
    
    logger.info("Checking for new analysis tasks")
    
    try:
        mission_list = state.get('mission_list', [])
        completed_investigations = state.get('completed_investigations', {})
        file_path = state.get('file_path')
        structural_summary = state.get('structural_summary')
        
        # Validate required inputs
        if not file_path:
            raise ValueError("file_path is required")
        
        missions_to_dispatch = [
            m for m in mission_list 
            if m.status == MissionStatus.IN_PROGRESS 
            and m.mission_id not in completed_investigations
        ]
        
        if not missions_to_dispatch:
            logger.info("No pending analysis tasks found, proceeding to review results")
            return "review_analysis_results"
        
        logger.info(f"Dispatching {len(missions_to_dispatch)} analysis missions")
        
        return [
            Send(
                "run_file_analysis",
                {
                    "file_path": file_path,
                    "mission": mission,
                    "structural_summary": structural_summary,
                    "messages": []
                }
            )
            for mission in missions_to_dispatch
        ]
    
    except Exception as e:
        error_msg = f"Error in assign_analysis_tasks: {e}"
        logger.error(error_msg, exc_info=True)
        # Return to review on error to avoid blocking
        return "review_analysis_results"


async def file_analyzer(state: InvestigatorState):
    """
    Investigator node that runs one step of the investigation.
    """
    
    try:
        mission = state.get('mission')
        file_path = state.get('file_path')
        structural_summary = state.get('structural_summary')
        messages = state.get('messages', [])
        
        # Validate required inputs
        if not mission:
            raise ValueError("mission is required")
        if not file_path:
            raise ValueError("file_path is required")
        
        mission_id = mission.mission_id if mission else "unknown"
        
        # Dynamically build the prompt based on whether this is the first turn or not.
        if len(messages) == 0:
            # First turn: Provide the full mission briefing.
            logger.info(f"Starting new investigation for mission {mission_id}")
            logger.debug(f"Mission threat type: {mission.threat_type}")
            
            user_prompt = file_analysis_investigator_user_prompt.format(
                file_path=file_path,
                mission_id=mission_id,
                threat_type=mission.threat_type,
                entry_point_description=mission.entry_point_description,
                reasoning=mission.reasoning,
                structural_summary=json.dumps(structural_summary),
                tool_manifest=json.dumps(pdf_parser_tools_manifest)
            )
            messages = [
                SystemMessage(content=file_analysis_investigator_system_prompt),
                HumanMessage(content=user_prompt),
            ]
            logger.debug("Created initial investigator prompt")
        else:
            # Subsequent turns: The history is already in the state.
            logger.debug(f"Continuing investigation for mission {mission_id}, turn {len(messages)}")

        # --- LLM with Tools Call ---
        logger.info("Invoking investigator LLM with tools")
        llm_with_tools = llm_investigator_with_tools
        result = await llm_with_tools.ainvoke(messages)
        
        # --- State and Routing Logic ---
        if not result.tool_calls:
            # The agent has decided the mission is over and did not call a tool.
            logger.info(f"Analysis task {mission_id} complete. Generating final report.")
            
            # Add the agent's last thought to the history before asking for the report
            final_messages = messages + [result]
            
            # Create a new prompt to force the final structured output
            logger.debug("Creating report generation prompt")
            report_generation_prompt = [
                SystemMessage(content=file_analysis_investigator_system_prompt),
                *final_messages, 
                HumanMessage(content="Your investigation is complete. Based on your findings in the conversation above, provide your final MissionReport in the required JSON format.")
            ]

            logger.debug("Invoking LLM for final mission report")
            mission_report_obj = await llm_investigator.ainvoke(report_generation_prompt)
            validated_report = MissionReport.model_validate(mission_report_obj)
            
            logger.info(f"Mission report findings: {validated_report.summary_of_findings}")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Evidence points: {len(validated_report.mission_subgraph.nodes)}")
                logger.debug(f"Final status: {validated_report.final_status}")

            return {
                "mission": mission,  # Include the mission in the return
                "investigation_report": validated_report,
                "messages": final_messages
            }
        else:
            # The agent wants to use a tool
            logger.info("Investigator wants to use tools")
            
            # Handle different formats of tool_calls based on LangGraph versions
            if hasattr(result, 'tool_calls') and result.tool_calls:
                if hasattr(result.tool_calls[0], 'name'):
                    logger.info(f"Tool name: {result.tool_calls[0].name}")
                elif isinstance(result.tool_calls[0], dict) and 'name' in result.tool_calls[0]:
                    logger.info(f"Tool name: {result.tool_calls[0]['name']}")
            
            return {"messages": [result]}
    
    except Exception as e:
        error_msg = f"Error in file_analyzer: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": [error_msg]}
    

async def merge_evidence_graphs(current_master: EvidenceGraph, new_subgraphs: List[EvidenceGraph]) -> EvidenceGraph:
    """Use LLM to intelligently merge evidence graphs, handling duplicates and conflicts"""

    logger.info("Merging evidence graphs")
    
    try:
        # Prepare the data for the LLM
        current_master_json = current_master.model_dump_json(indent=2)
        new_subgraphs_json = json.dumps([g.model_dump() for g in new_subgraphs], indent=2)
        
        user_prompt = file_analysis_graph_merger_user_prompt.format(
            current_master_json=current_master_json,
            new_subgraphs_json=new_subgraphs_json
        )

        result = await llm_graph_merger.ainvoke([
            SystemMessage(content=file_analysis_graph_merger_system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        logger.info(f"Graph Merge Summary: {result.merge_summary}")
        return result.master_graph
    
    except Exception as e:
        error_msg = f"Error in merge_evidence_graphs: {e}"
        logger.error(error_msg, exc_info=True)
        # Return the current master graph on error to avoid data loss
        logger.warning("Returning unmerged master graph due to merge error")
        return current_master


async def review_analysis_results(state: FileAnalysisState) -> Command[Literal["summarize_file_analysis", "create_analysis_tasks"]]:
    """
    Acts as the "Chief Pathologist." This node now performs two roles:
    1. PROCESSES the raw results from the completed investigations (Reducer's job).
    2. ANALYZES the processed results to decide the next strategic step (Reviewer's job).
    """
    logger.info("Processing and reviewing analysis results")

    try:
        # --- Part 1: PROCESS raw investigation results (The Reducer's Logic) ---
        
        # Initialize or get copies of the data we will be modifying
        current_master_graph = state.get('master_evidence_graph', EvidenceGraph()).copy(deep=True)
        mission_reports = state.get('mission_reports', {}).copy()
        mission_list = state.get('mission_list', [])
        
        # Create a mutable map of missions from the current state's mission list
        mission_map = {m.mission_id: m.copy(deep=True) for m in mission_list}

        # The `completed_investigations` list is our raw input, automatically populated by LangGraph.
        # We must only process investigations that we haven't seen before to avoid errors on the second loop.
        newly_completed_investigations = [
            inv for inv in state.get('completed_investigations', []) 
            if inv['mission'].mission_id not in mission_reports
        ]
        
        logger.info(f"Processing {len(newly_completed_investigations)} new investigation packet(s)")

        new_subgraphs = []
        investigation_transcripts = []

        for investigation_packet in newly_completed_investigations:
            report = investigation_packet.get("mission_report")
            mission_id = investigation_packet['mission'].mission_id
            
            if report:
                # File the structured report
                mission_reports[report.mission_id] = report
                
                # Update the status of the corresponding mission in our map
                if mission_id in mission_map:
                    mission_map[mission_id].status = report.final_status
                    
                new_subgraphs.append(report.mission_subgraph)

                if 'messages' in investigation_packet:
                    threat_type = investigation_packet['mission'].threat_type
                    message_history = get_buffer_string(investigation_packet['messages'])
                    investigation_transcripts.append(
                        f"=== Mission {mission_id} ({threat_type}) ===\n{message_history}"
                    )
            else:
                # If there's no report, the mission failed.
                if mission_id in mission_map:
                    mission_map[mission_id].status = MissionStatus.FAILED


        if new_subgraphs:
            logger.info(f"Merging {len(new_subgraphs)} investigation graphs intelligently")
            master_graph = await merge_evidence_graphs(current_master_graph, new_subgraphs)
        else:
            master_graph = current_master_graph

        
        # --- Part 2: ANALYZE the complete picture (The Reviewer's Logic) ---
        logger.info("Starting strategic review of analysis results")
        
        # We use the data we just finished processing for the strategic analysis
        current_mission_list = list(mission_map.values())
        
        master_graph_json = master_graph.model_dump_json(indent=2)
        mission_reports_json = json.dumps({mid: r.model_dump() for mid, r in mission_reports.items()}, indent=2)
        mission_list_json = json.dumps([m.model_dump() for m in current_mission_list], indent=2)
        investigation_transcripts_text = "\n\n".join(investigation_transcripts)

        user_prompt = file_analysis_reviewer_user_prompt.format(
            master_evidence_graph=master_graph_json,
            mission_reports=mission_reports_json,
            mission_list=mission_list_json,
            investigation_transcripts=investigation_transcripts_text
        )
        
        result = await llm_reviewer.ainvoke([
            SystemMessage(content=file_analysis_reviewer_system_prompt),
            HumanMessage(content=user_prompt)
        ])

        logger.info(f"Strategic review summary: {result.strategic_summary}")

        # --- Part 3: Prepare State Updates and Return Routing Command ---
        
        # We must overwrite the entire mission_list with our updated version,
        # and then append the new missions from the reviewer.
        updated_mission_list = current_mission_list + result.new_missions
        
        updates = {
            "master_evidence_graph": master_graph,
            "mission_reports": mission_reports,
            "mission_list": updated_mission_list,
        }
        
        if result.is_investigation_complete:
            logger.info("Investigation is complete. Proceeding to finalizer")
            goto = "summarize_file_analysis"
        else:
            if result.new_missions:
                logger.info(f"Investigation continues with {len(result.new_missions)} new mission(s)")
            else:
                logger.info("Investigation continues, but no new missions generated. Looping to re-evaluate")
            goto = "create_analysis_tasks"
            
        return Command(goto=goto, update=updates)
    
    except Exception as e:
        error_msg = f"Error in review_analysis_results: {e}"
        logger.error(error_msg, exc_info=True)
        # On error, proceed to summarize to complete the flow
        return Command(goto="summarize_file_analysis", update={"errors": [error_msg]})


from langchain_core.messages.utils import get_buffer_string

async def summarize_file_analysis(state: FileAnalysisState):
    logger.info("Generating final analysis summary")

    try:
        master_evidence_graph = state.get('master_evidence_graph')
        mission_reports = state.get('mission_reports', {})
        completed_investigations = state.get('completed_investigations', [])
        
        # Validate required inputs
        if not master_evidence_graph:
            logger.warning("No master evidence graph found, using empty graph")
            master_evidence_graph = EvidenceGraph()

        master_graph_json = master_evidence_graph.model_dump_json(indent=2)
        mission_reports_json = json.dumps({mid: r.model_dump() for mid, r in mission_reports.items()}, indent=2)
        
        # Format message histories as readable text
        investigation_transcripts = []
        for inv_state in completed_investigations:
            if 'messages' in inv_state:
                mission_id = inv_state['mission'].mission_id
                threat_type = inv_state['mission'].threat_type
                message_history = get_buffer_string(inv_state['messages'])
                investigation_transcripts.append(
                    f"=== Mission {mission_id} ({threat_type}) ===\n{message_history}"
                )
        
        completed_investigations_text = "\n\n".join(investigation_transcripts)

        user_prompt = file_analysis_finalizer_user_prompt.format(
            master_evidence_graph=master_graph_json,
            mission_reports=mission_reports_json,
            completed_investigations=completed_investigations_text
        )

        static_analysis_final_report = await llm_finalizer.ainvoke([
            SystemMessage(content=file_analysis_finalizer_system_prompt),
            HumanMessage(content=user_prompt)
        ])

        # Save the final state to a JSON file for debugging and records
        session_output_directory = state.get("output_directory", "output")
        session_id = state.get("session_id", "unknown_session")
        finalizer_directory = os.path.join(session_output_directory, "file_analysis")
        await asyncio.to_thread(os.makedirs, finalizer_directory, exist_ok=True)
        json_filename = f"file_analysis_final_state_session_{session_id}.json"
        json_path = os.path.join(finalizer_directory, json_filename)
        await dump_state_to_file(state, json_path)
        
        logger.info(f"Final report generated with verdict: {static_analysis_final_report.final_verdict}")
        
        return {"static_analysis_final_report": static_analysis_final_report}
    
    except Exception as e:
        error_msg = f"Error in summarize_file_analysis: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": [error_msg]}
