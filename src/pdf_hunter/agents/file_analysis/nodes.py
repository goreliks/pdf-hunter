import os
import asyncio
from loguru import logger
from .schemas import FileAnalysisState, MissionStatus, InvestigatorState
from pdf_hunter.shared.analyzers.wrappers import run_pdfid, run_pdf_parser_full_statistical_analysis, run_peepdf
from .prompts import file_analysis_triage_system_prompt, file_analysis_triage_user_prompt, file_analysis_investigator_system_prompt, file_analysis_investigator_user_prompt
import json
from langgraph.types import Command
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Send
from langchain_core.messages.utils import get_buffer_string
from .tools import pdf_parser_tools_manifest, pdf_parser_tools
from .schemas import EvidenceGraph, MergedEvidenceGraph
from typing import List, Literal
from .prompts import file_analysis_graph_merger_system_prompt, file_analysis_graph_merger_user_prompt
from .prompts import file_analysis_reviewer_system_prompt, file_analysis_reviewer_user_prompt
from .prompts import file_analysis_finalizer_system_prompt, file_analysis_finalizer_user_prompt
from pdf_hunter.config import file_analysis_triage_llm, file_analysis_investigator_llm, file_analysis_graph_merger_llm, file_analysis_reviewer_llm, file_analysis_finalizer_llm
from pdf_hunter.config import THINKING_TOOL_ENABLED
from pdf_hunter.config.execution_config import LLM_TIMEOUT_TEXT
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
    """Initial triage of PDF file using static analysis tools."""
    
    try:
        file_path = state.get('file_path')
        output_directory = state.get('output_directory', 'output')
        
        # Validate required inputs
        if not file_path:
            raise ValueError("file_path is required")
        
        # Ensure the file_analysis subdirectory exists for evidence preservation
        file_analysis_dir = os.path.join(output_directory, "file_analysis")
        await asyncio.to_thread(os.makedirs, file_analysis_dir, exist_ok=True)
        
        logger.info(
            f"🔍 Starting PDF triage analysis",
            agent="FileAnalysis",
            node="identify_suspicious_elements",
            event_type="TRIAGE_START",
            file_path=file_path
        )

        logger.debug("Running pdfid analysis", agent="FileAnalysis", node="identify_suspicious_elements")
        pdfid_output = await run_pdfid(file_path)
        
        logger.debug("Running pdf-parser statistical analysis", agent="FileAnalysis", node="identify_suspicious_elements")
        pdf_parser_output = await run_pdf_parser_full_statistical_analysis(file_path)
        
        logger.debug("Running peepdf analysis", agent="FileAnalysis", node="identify_suspicious_elements")
        peepdf_output = await run_peepdf(file_path, output_directory=output_directory)
        
        structural_summary = {"pdfid": pdfid_output, "pdf_parser": pdf_parser_output, "peepdf": peepdf_output}
        additional_context = state.get('additional_context', "None")
        
        logger.debug("Static analysis tools completed", agent="FileAnalysis", node="identify_suspicious_elements")

        system_prompt = file_analysis_triage_system_prompt
        # Escape curly braces in JSON to prevent .format() errors
        safe_structural_summary = json.dumps(structural_summary).replace('{', '{{').replace('}', '}}')
        user_prompt = file_analysis_triage_user_prompt.format(
            additional_context=additional_context,
            structural_summary=safe_structural_summary
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        logger.debug("Invoking triage LLM", agent="FileAnalysis", node="identify_suspicious_elements")
        # Add timeout protection to prevent infinite hangs on triage LLM calls
        result = await asyncio.wait_for(
            llm_router.ainvoke(messages),
            timeout=LLM_TIMEOUT_TEXT
        )

        updates = {
            "structural_summary": structural_summary,
            "triage_classification_decision": result.triage_classification_decision,
            "triage_classification_reasoning": result.triage_classification_reasoning,
            "mission_list": result.mission_list
        }

        if result.triage_classification_decision == "innocent":
            logger.info(
                "✅ Triage Decision: PDF is INNOCENT - No threats detected",
                agent="FileAnalysis",
                node="identify_suspicious_elements",
                event_type="TRIAGE_COMPLETE",
                decision="innocent",
                mission_count=0,
                reasoning=result.triage_classification_reasoning
            )
        elif result.triage_classification_decision == "suspicious":
            logger.info(
                f"⚠️  Triage Decision: PDF is SUSPICIOUS - {len(result.mission_list)} investigation mission(s) created",
                agent="FileAnalysis",
                node="identify_suspicious_elements",
                event_type="TRIAGE_COMPLETE",
                decision="suspicious",
                mission_count=len(result.mission_list),
                reasoning=result.triage_classification_reasoning
            )
            # Log each mission for visibility
            for idx, mission in enumerate(result.mission_list):
                # Escape curly braces in entry point description to prevent logger.format() errors
                safe_entry = mission.entry_point_description[:50].replace('{', '{{').replace('}', '}}')
                logger.info(
                    f"📋 Mission {idx+1}: {mission.threat_type} - {safe_entry}...",
                    agent="FileAnalysis",
                    node="identify_suspicious_elements",
                    event_type="MISSION_CREATED",
                    mission_id=mission.mission_id,
                    threat_type=mission.threat_type,
                    entry_point=mission.entry_point_description
                )
        else:
            error_msg = "Invalid triage classification decision from LLM"
            logger.error(
                error_msg,
                agent="FileAnalysis",
                node="identify_suspicious_elements",
                event_type="ERROR"
            )
            updates["errors"] = [error_msg]

        return updates
    
    except asyncio.TimeoutError:
        error_msg = f"Error in identify_suspicious_elements: Triage LLM call timed out after {LLM_TIMEOUT_TEXT} seconds"
        logger.error(
            "Error in identify_suspicious_elements: Triage LLM call timed out after {} seconds",
            LLM_TIMEOUT_TEXT,
            agent="FileAnalysis",
            node="identify_suspicious_elements",
            event_type="ERROR",
            timeout_seconds=LLM_TIMEOUT_TEXT,
            exc_info=True
        )
        return {"errors": [error_msg]}
    except Exception as e:
        error_msg = f"Error in identify_suspicious_elements: {type(e).__name__}: {e}"
        logger.error(
            "Error in identify_suspicious_elements: {}: {}",
            type(e).__name__,
            str(e),
            agent="FileAnalysis",
            node="identify_suspicious_elements",
            event_type="ERROR",
            exc_info=True
        )
        return {"errors": [error_msg]}


async def create_analysis_tasks(state: FileAnalysisState):
    """Update mission statuses from NEW to IN_PROGRESS."""
    
    try:
        mission_list = state.get('mission_list', [])
        updated_missions = []
        task_count = 0
        
        logger.debug(
            f"Processing {len(mission_list)} missions",
            agent="FileAnalysis",
            node="create_analysis_tasks"
        )
        
        for mission in mission_list:
            if mission.status == MissionStatus.NEW:
                mission.status = MissionStatus.IN_PROGRESS
                task_count += 1
                logger.debug(
                    f"Queuing mission: {mission.mission_id} ({mission.threat_type})",
                    agent="FileAnalysis",
                    node="create_analysis_tasks",
                    mission_id=mission.mission_id,
                    threat_type=mission.threat_type
                )
            updated_missions.append(mission)
        
        logger.info(
            f"🚀 Queued {task_count} missions for investigation",
            agent="FileAnalysis",
            node="create_analysis_tasks",
            event_type="TASKS_CREATED",
            task_count=task_count
        )
        
        return {"mission_list": updated_missions}
    
    except Exception as e:
        error_msg = f"Error in create_analysis_tasks: {e}"
        logger.error(
            error_msg,
            agent="FileAnalysis",
            node="create_analysis_tasks",
            event_type="ERROR",
            exc_info=True
        )
        return {"errors": [error_msg]}


async def assign_analysis_tasks(state: FileAnalysisState): 
    """
    Dispatches all missions currently in 'IN_PROGRESS' status to the investigator pool.
    Routes to review if no pending missions remain.
    """
    
    try:
        mission_list = state.get('mission_list', [])
        completed_investigations = state.get('completed_investigations', {})
        file_path = state.get('file_path')
        structural_summary = state.get('structural_summary')
        
        # Validate required inputs
        if not file_path:
            raise ValueError("file_path is required")
        
        logger.debug(
            f"Checking {len(mission_list)} missions for dispatch",
            agent="FileAnalysis",
            node="assign_analysis_tasks"
        )
        
        missions_to_dispatch = [
            m for m in mission_list 
            if m.status == MissionStatus.IN_PROGRESS 
            and m.mission_id not in completed_investigations
        ]
        
        # Count already completed missions
        already_completed = len([m for m in mission_list if m.mission_id in completed_investigations])
        
        if not missions_to_dispatch:
            logger.info(
                "✓ No pending missions - proceeding to review",
                agent="FileAnalysis",
                node="assign_analysis_tasks",
                event_type="NO_PENDING_MISSIONS",
                total_missions=len(mission_list),
                completed_missions=already_completed
            )
            return "review_analysis_results"
        
        logger.info(
            f"⚡ Dispatching {len(missions_to_dispatch)} mission(s) in parallel",
            agent="FileAnalysis",
            node="assign_analysis_tasks",
            event_type="DISPATCH_MISSIONS",
            dispatch_count=len(missions_to_dispatch),
            already_completed=already_completed,
            total_missions=len(mission_list)
        )
        
        # Log each dispatched mission
        for mission in missions_to_dispatch:
            logger.debug(
                f"→ Dispatching: {mission.mission_id} ({mission.threat_type})",
                agent="FileAnalysis",
                node="assign_analysis_tasks",
                mission_id=mission.mission_id,
                threat_type=mission.threat_type
            )
        
        output_directory = state.get('output_directory', 'output')
        
        return [
            Send(
                "run_file_analysis",
                {
                    "file_path": file_path,
                    "output_directory": output_directory,
                    "mission": mission,
                    "structural_summary": structural_summary,
                    "messages": []
                }
            )
            for mission in missions_to_dispatch
        ]
    
    except Exception as e:
        error_msg = f"Error in assign_analysis_tasks: {e}"
        logger.error(
            error_msg,
            agent="FileAnalysis",
            node="assign_analysis_tasks",
            event_type="ERROR",
            exc_info=True
        )
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
        threat_type = mission.threat_type if mission else "unknown"
        
        # Dynamically build the prompt based on whether this is the first turn or not.
        if len(messages) == 0:
            # First turn: Provide the full mission briefing.
            logger.info(
                f"🔬 Starting investigation: {mission_id} ({threat_type})",
                agent="FileAnalysis",
                node="file_analyzer",
                event_type="MISSION_START",
                mission_id=mission_id,
                threat_type=threat_type,
                file_path=file_path
            )
            
            logger.debug(
                f"Investigator prompt will reference file: {file_path}",
                agent="FileAnalysis",
                node="file_analyzer",
                mission_id=mission_id,
                file_path=file_path
            )
            
            output_directory = state.get('output_directory', 'output')
            
            # Escape curly braces in LLM-generated strings to prevent .format() errors
            # (e.g., if mission description contains JavaScript like "{ cName: 'pd.doc' }")
            safe_entry_point = mission.entry_point_description.replace('{', '{{').replace('}', '}}')
            safe_reasoning = mission.reasoning.replace('{', '{{').replace('}', '}}')
            
            # Also escape curly braces in JSON to prevent .format() from interpreting them
            safe_structural_summary = json.dumps(structural_summary).replace('{', '{{').replace('}', '}}')
            safe_tool_manifest = json.dumps(pdf_parser_tools_manifest).replace('{', '{{').replace('}', '}}')
            
            user_prompt = file_analysis_investigator_user_prompt.format(
                file_path=file_path,
                output_directory=output_directory,
                mission_id=mission_id,
                threat_type=str(mission.threat_type).replace('{', '{{').replace('}', '}}'),
                entry_point_description=safe_entry_point,
                reasoning=safe_reasoning,
                structural_summary=safe_structural_summary,
                tool_manifest=safe_tool_manifest
            )
            messages = [
                SystemMessage(content=file_analysis_investigator_system_prompt),
                HumanMessage(content=user_prompt),
            ]
            logger.debug(
                "Created initial investigator prompt",
                agent="FileAnalysis",
                node="file_analyzer",
                mission_id=mission_id
            )
        else:
            # Subsequent turns: The history is already in the state.
            logger.debug(
                f"Continuing investigation step {len(messages)//2}",
                agent="FileAnalysis",
                node="file_analyzer",
                mission_id=mission_id,
                step=len(messages)//2
            )

        # --- LLM with Tools Call ---
        llm_with_tools = llm_investigator_with_tools
        
        # DEBUG: Log message sizes before LLM call
        total_chars = sum(len(str(m.content)) for m in messages if hasattr(m, 'content'))
        logger.debug(
            f"🔍 Calling LLM with {len(messages)} messages, ~{total_chars:,} chars total",
            agent="FileAnalysis",
            node="file_analyzer",
            mission_id=mission_id,
            message_count=len(messages),
            total_chars=total_chars
        )
        
        # Add timeout protection to prevent infinite hangs on investigator LLM calls
        result = await asyncio.wait_for(
            llm_with_tools.ainvoke(messages),
            timeout=LLM_TIMEOUT_TEXT
        )
        
        # --- State and Routing Logic ---
        if not result.tool_calls:
            # The agent has decided the mission is over and did not call a tool.
            logger.info(
                f"✅ Investigation complete: {mission_id}",
                agent="FileAnalysis",
                node="file_analyzer",
                event_type="MISSION_COMPLETE",
                mission_id=mission_id
            )
            
            # Add the agent's last thought to the history before asking for the report
            final_messages = messages + [result]
            
            # Create a new prompt to force the final structured output
            report_generation_prompt = [
                SystemMessage(content=file_analysis_investigator_system_prompt),
                *final_messages, 
                HumanMessage(content="Your investigation is complete. Based on your findings in the conversation above, provide your final MissionReport in the required JSON format.")
            ]

            # Add timeout protection to prevent infinite hangs on mission report LLM calls
            mission_report_obj = await asyncio.wait_for(
                llm_investigator.ainvoke(report_generation_prompt),
                timeout=LLM_TIMEOUT_TEXT
            )
            validated_report = MissionReport.model_validate(mission_report_obj)
            
            findings_count = len(validated_report.mission_subgraph.nodes)
            # Escape curly braces in summary to prevent logger.format() errors
            safe_summary = validated_report.summary_of_findings[:100].replace('{', '{{').replace('}', '}}')
            logger.info(
                f"📋 Report: {safe_summary}...",
                agent="FileAnalysis",
                node="file_analyzer",
                event_type="REPORT_GENERATED",
                mission_id=mission_id,
                findings_count=findings_count,
                final_status=validated_report.final_status.value
            )

            return {
                "mission": mission,
                "mission_report": validated_report,
                "messages": final_messages
            }
        else:
            # The agent wants to use a tool
            tool_calls = result.tool_calls
            
            # Log tool execution (handle both dict and attribute access)
            for tool_call in tool_calls:
                tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", "unknown")
                
                # Special handling for think_tool to show reflections
                if tool_name == "think_tool":
                    tool_args = tool_call.get("args") if isinstance(tool_call, dict) else getattr(tool_call, "args", {})
                    reflection_text = tool_args.get("reflection", "") if isinstance(tool_args, dict) else ""
                    if reflection_text:
                        # Escape curly braces in reflection to prevent logger.format() errors
                        safe_reflection = reflection_text.replace('{', '{{').replace('}', '}}')
                        logger.info(
                            f"💭 Strategic Reflection: {safe_reflection}",
                            agent="FileAnalysis",
                            node="file_analyzer",
                            event_type="STRATEGIC_REFLECTION",
                            mission_id=mission_id,
                            reflection=reflection_text
                        )
                else:
                    logger.debug(
                        f"🔧 Tool execution: {tool_name}",
                        agent="FileAnalysis",
                        node="file_analyzer",
                        event_type="TOOL_EXECUTION",
                        mission_id=mission_id,
                        tool_name=tool_name
                    )
            
            return {"messages": [result]}
    
    except asyncio.TimeoutError:
        error_msg = f"Error in file_analyzer: Investigator LLM call timed out after {LLM_TIMEOUT_TEXT} seconds"
        logger.error(
            "Error in file_analyzer: Investigator LLM call timed out after {} seconds",
            LLM_TIMEOUT_TEXT,
            agent="FileAnalysis",
            node="file_analyzer",
            event_type="ERROR",
            timeout_seconds=LLM_TIMEOUT_TEXT,
            exc_info=True
        )
        return {"errors": [error_msg]}
    except Exception as e:
        import traceback
        error_msg = f"Error in file_analyzer: {type(e).__name__}: {e}"
        full_traceback = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        logger.error(
            "Error in file_analyzer: {}: {}\n\nFull traceback:\n{}",
            type(e).__name__,
            str(e),
            full_traceback,
            agent="FileAnalysis",
            node="file_analyzer",
            event_type="ERROR",
            mission_id=mission_id if 'mission_id' in locals() else "unknown",
            step=len(messages)//2 if 'messages' in locals() else 0
        )
        return {"errors": [error_msg]}
    

async def merge_evidence_graphs(current_master: EvidenceGraph, new_subgraphs: List[EvidenceGraph]) -> EvidenceGraph:
    """Use LLM to intelligently merge evidence graphs, handling duplicates and conflicts"""
    
    try:
        current_nodes = len(current_master.nodes)
        new_nodes_total = sum(len(g.nodes) for g in new_subgraphs)
        
        logger.info(
            f"🔗 Merging evidence: {current_nodes} existing + {new_nodes_total} new nodes",
            agent="FileAnalysis",
            node="merge_evidence_graphs",
            event_type="MERGE_START",
            current_nodes=current_nodes,
            new_nodes=new_nodes_total,
            subgraph_count=len(new_subgraphs)
        )
        
        # Prepare the data for the LLM
        current_master_json = current_master.model_dump_json(indent=2)
        new_subgraphs_json = json.dumps([g.model_dump() for g in new_subgraphs], indent=2)
        
        # Escape curly braces in JSON to prevent .format() errors
        safe_current_master = current_master_json.replace('{', '{{').replace('}', '}}')
        safe_new_subgraphs = new_subgraphs_json.replace('{', '{{').replace('}', '}}')
        
        user_prompt = file_analysis_graph_merger_user_prompt.format(
            current_master_json=safe_current_master,
            new_subgraphs_json=safe_new_subgraphs
        )

        # Add timeout protection to prevent infinite hangs on graph merger LLM calls
        result = await asyncio.wait_for(
            llm_graph_merger.ainvoke([
                SystemMessage(content=file_analysis_graph_merger_system_prompt),
                HumanMessage(content=user_prompt)
            ]),
            timeout=LLM_TIMEOUT_TEXT
        )
        
        merged_nodes = len(result.master_graph.nodes)
        logger.info(
            f"✅ Merge complete: {merged_nodes} total nodes",
            agent="FileAnalysis",
            node="merge_evidence_graphs",
            event_type="MERGE_COMPLETE",
            merged_nodes=merged_nodes,
            merge_summary=result.merge_summary[:100]
        )
        
        return result.master_graph
    
    except asyncio.TimeoutError:
        error_msg = f"Error in merge_evidence_graphs: Graph merger LLM call timed out after {LLM_TIMEOUT_TEXT} seconds"
        logger.error(
            "Error in merge_evidence_graphs: Graph merger LLM call timed out after {} seconds",
            LLM_TIMEOUT_TEXT,
            agent="FileAnalysis",
            node="merge_evidence_graphs",
            event_type="ERROR",
            timeout_seconds=LLM_TIMEOUT_TEXT,
            exc_info=True
        )
        # Return the current master graph on error to avoid data loss
        logger.warning(
            "⚠️ Returning unmerged graph due to timeout",
            agent="FileAnalysis",
            node="merge_evidence_graphs"
        )
        return current_master
    except Exception as e:
        error_msg = f"Error in merge_evidence_graphs: {type(e).__name__}: {e}"
        logger.error(
            "Error in merge_evidence_graphs: {}: {}",
            type(e).__name__,
            str(e),
            agent="FileAnalysis",
            node="merge_evidence_graphs",
            event_type="ERROR",
            exc_info=True
        )
        # Return the current master graph on error to avoid data loss
        logger.warning(
            "⚠️ Returning unmerged graph due to error",
            agent="FileAnalysis",
            node="merge_evidence_graphs",
            event_type="MERGE_FALLBACK"
        )
        return current_master


async def review_analysis_results(state: FileAnalysisState) -> Command[Literal["summarize_file_analysis", "create_analysis_tasks"]]:
    """
    Acts as the "Chief Pathologist." This node now performs two roles:
    1. PROCESSES the raw results from the completed investigations (Reducer's job).
    2. ANALYZES the processed results to decide the next strategic step (Reviewer's job).
    """
    
    try:
        # --- Part 1: PROCESS raw investigation results (The Reducer's Logic) ---
        
        # Initialize or get copies of the data we will be modifying
        current_master_graph = state.get('master_evidence_graph', EvidenceGraph()).model_copy(deep=True)
        mission_reports = state.get('mission_reports', {}).copy()
        mission_list = state.get('mission_list', [])
        
        # Create a mutable map of missions from the current state's mission list
        mission_map = {m.mission_id: m.model_copy(deep=True) for m in mission_list}

        # The `completed_investigations` list is our raw input, automatically populated by LangGraph.
        # We must only process investigations that we haven't seen before to avoid errors on the second loop.
        newly_completed_investigations = [
            inv for inv in state.get('completed_investigations', []) 
            if inv['mission'].mission_id not in mission_reports
        ]
        
        logger.info(
            f"👨‍⚕️ Chief Pathologist reviewing {len(newly_completed_investigations)} investigation(s)",
            agent="FileAnalysis",
            node="review_analysis_results",
            event_type="REVIEW_START",
            new_investigations=len(newly_completed_investigations),
            total_reports=len(mission_reports)
        )

        new_subgraphs = []
        investigation_transcripts = []
        
        # Track status counts for logging
        successful_reports = 0
        blocked_missions = 0
        failed_missions = 0

        for investigation_packet in newly_completed_investigations:
            report = investigation_packet.get("mission_report")
            mission_id = investigation_packet['mission'].mission_id
            
            if report:
                # File the structured report
                mission_reports[report.mission_id] = report
                successful_reports += 1
                
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
                # If there's no report, check if it's a recursion limit issue or general failure
                investigation_errors = investigation_packet.get("errors", [])
                is_recursion_limit = any("recursion limit" in str(err).lower() for err in investigation_errors)
                
                if mission_id in mission_map:
                    if is_recursion_limit:
                        # Mark as BLOCKED - investigation hit complexity limit
                        mission_map[mission_id].status = MissionStatus.BLOCKED
                        blocked_missions += 1
                        logger.warning(
                            f"⚠️ Mission {mission_id} blocked (recursion limit)",
                            agent="FileAnalysis",
                            node="review_analysis_results",
                            event_type="MISSION_BLOCKED",
                            mission_id=mission_id
                        )
                    else:
                        # General failure
                        mission_map[mission_id].status = MissionStatus.FAILED
                        failed_missions += 1
                        logger.warning(
                            f"⚠️ Mission {mission_id} failed",
                            agent="FileAnalysis",
                            node="review_analysis_results",
                            event_type="MISSION_FAILED",
                            mission_id=mission_id
                        )
                
                # Still add transcript if available for reviewer context
                if 'messages' in investigation_packet:
                    threat_type = investigation_packet['mission'].threat_type
                    message_history = get_buffer_string(investigation_packet['messages'])
                    investigation_transcripts.append(
                        f"=== Mission {mission_id} ({threat_type}) - INCOMPLETE ===\n{message_history}"
                    )
        
        # Log processing summary
        logger.info(
            f"📊 Processed: {successful_reports} reports, {blocked_missions} blocked, {failed_missions} failed",
            agent="FileAnalysis",
            node="review_analysis_results",
            event_type="PROCESSING_COMPLETE",
            successful_reports=successful_reports,
            blocked_missions=blocked_missions,
            failed_missions=failed_missions
        )

        if new_subgraphs:
            master_graph = await merge_evidence_graphs(current_master_graph, new_subgraphs)
        else:
            master_graph = current_master_graph

        
        # --- Part 2: ANALYZE the complete picture (The Reviewer's Logic) ---
        logger.info(
            "🔍 Strategic review of complete evidence",
            agent="FileAnalysis",
            node="review_analysis_results",
            event_type="STRATEGIC_REVIEW_START"
        )
        
        # We use the data we just finished processing for the strategic analysis
        current_mission_list = list(mission_map.values())
        
        master_graph_json = master_graph.model_dump_json(indent=2)
        mission_reports_json = json.dumps({mid: r.model_dump() for mid, r in mission_reports.items()}, indent=2)
        mission_list_json = json.dumps([m.model_dump() for m in current_mission_list], indent=2)
        investigation_transcripts_text = "\n\n".join(investigation_transcripts)

        # Log context size before LLM call
        total_context_size = len(master_graph_json) + len(mission_reports_json) + len(mission_list_json) + len(investigation_transcripts_text)
        logger.debug(
            f"Reviewer context size: {total_context_size:,} characters",
            agent="FileAnalysis",
            node="review_analysis_results",
            context_size=total_context_size,
            graph_size=len(master_graph_json),
            reports_size=len(mission_reports_json),
            transcripts_size=len(investigation_transcripts_text)
        )

        # Escape curly braces in JSON and transcripts to prevent .format() errors
        safe_master_graph = master_graph_json.replace('{', '{{').replace('}', '}}')
        safe_mission_reports = mission_reports_json.replace('{', '{{').replace('}', '}}')
        safe_mission_list = mission_list_json.replace('{', '{{').replace('}', '}}')
        safe_transcripts = investigation_transcripts_text.replace('{', '{{').replace('}', '}}')
        
        user_prompt = file_analysis_reviewer_user_prompt.format(
            master_evidence_graph=safe_master_graph,
            mission_reports=safe_mission_reports,
            mission_list=safe_mission_list,
            investigation_transcripts=safe_transcripts
        )
        
        logger.debug(
            "Invoking reviewer LLM...",
            agent="FileAnalysis",
            node="review_analysis_results"
        )
        
        # Add timeout protection to prevent infinite hangs on reviewer LLM calls
        result = await asyncio.wait_for(
            llm_reviewer.ainvoke([
                SystemMessage(content=file_analysis_reviewer_system_prompt),
                HumanMessage(content=user_prompt)
            ]),
            timeout=LLM_TIMEOUT_TEXT
        )
        
        logger.debug(
            "Reviewer LLM responded",
            agent="FileAnalysis",
            node="review_analysis_results"
        )

        # Escape curly braces in strategic summary to prevent logger.format() errors
        safe_strategic_summary = result.strategic_summary[:150].replace('{', '{{').replace('}', '}}')
        logger.info(
            f"💡 Strategic summary: {safe_strategic_summary}...",
            agent="FileAnalysis",
            node="review_analysis_results",
            event_type="STRATEGIC_REVIEW_COMPLETE",
            is_complete=result.is_investigation_complete,
            new_missions_count=len(result.new_missions)
        )

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
            logger.info(
                "✅ Investigation complete → Finalizing report",
                agent="FileAnalysis",
                node="review_analysis_results",
                event_type="INVESTIGATION_COMPLETE",
                total_missions=len(updated_mission_list),
                total_reports=len(mission_reports)
            )
            goto = "summarize_file_analysis"
        else:
            if result.new_missions:
                logger.info(
                    f"🔄 Investigation continues → {len(result.new_missions)} new mission(s) queued",
                    agent="FileAnalysis",
                    node="review_analysis_results",
                    event_type="INVESTIGATION_CONTINUES",
                    new_missions=len(result.new_missions),
                    total_missions=len(updated_mission_list)
                )
                # Log each new mission
                for new_mission in result.new_missions:
                    logger.debug(
                        f"→ New follow-up: {new_mission.mission_id} ({new_mission.threat_type})",
                        agent="FileAnalysis",
                        node="review_analysis_results",
                        mission_id=new_mission.mission_id,
                        threat_type=new_mission.threat_type
                    )
            else:
                logger.info(
                    "🔄 Re-evaluating (no new missions generated)",
                    agent="FileAnalysis",
                    node="review_analysis_results",
                    event_type="RE_EVALUATION"
                )
            goto = "create_analysis_tasks"
            
        return Command(goto=goto, update=updates)
    
    except asyncio.TimeoutError:
        error_msg = f"Error in review_analysis_results: Reviewer LLM call timed out after {LLM_TIMEOUT_TEXT} seconds"
        logger.error(
            "Error in review_analysis_results: Reviewer LLM call timed out after {} seconds",
            LLM_TIMEOUT_TEXT,
            agent="FileAnalysis",
            node="review_analysis_results",
            event_type="ERROR",
            timeout_seconds=LLM_TIMEOUT_TEXT,
            exc_info=True
        )
        return {"errors": [error_msg]}
    except Exception as e:
        error_msg = f"Error in review_analysis_results: {type(e).__name__}: {e}"
        logger.error(
            "Error in review_analysis_results: {}: {}",
            type(e).__name__,
            str(e),
            agent="FileAnalysis",
            node="review_analysis_results",
            event_type="ERROR",
            exc_info=True
        )
        # On error, proceed to summarize to complete the flow
        return Command(goto="summarize_file_analysis", update={"errors": [error_msg]})


async def summarize_file_analysis(state: FileAnalysisState):
    
    try:
        master_evidence_graph = state.get('master_evidence_graph')
        mission_reports = state.get('mission_reports', {})
        completed_investigations = state.get('completed_investigations', [])
        
        # Validate required inputs
        if not master_evidence_graph:
            logger.warning(
                "⚠️ No master evidence graph found, using empty graph",
                agent="FileAnalysis",
                node="summarize_file_analysis",
                event_type="NO_EVIDENCE_GRAPH"
            )
            master_evidence_graph = EvidenceGraph()
        
        total_nodes = len(master_evidence_graph.nodes)
        total_reports = len(mission_reports)
        
        logger.info(
            f"📝 Generating final verdict from {total_reports} mission(s) and {total_nodes} evidence node(s)",
            agent="FileAnalysis",
            node="summarize_file_analysis",
            event_type="SUMMARY_START",
            total_reports=total_reports,
            total_evidence_nodes=total_nodes
        )

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

        # Escape curly braces in JSON and transcripts to prevent .format() errors
        safe_master_graph = master_graph_json.replace('{', '{{').replace('}', '}}')
        safe_mission_reports = mission_reports_json.replace('{', '{{').replace('}', '}}')
        safe_completed_investigations = completed_investigations_text.replace('{', '{{').replace('}', '}}')

        user_prompt = file_analysis_finalizer_user_prompt.format(
            master_evidence_graph=safe_master_graph,
            mission_reports=safe_mission_reports,
            completed_investigations=safe_completed_investigations
        )

        # Add timeout protection to prevent infinite hangs on finalizer LLM calls
        static_analysis_final_report = await asyncio.wait_for(
            llm_finalizer.ainvoke([
                SystemMessage(content=file_analysis_finalizer_system_prompt),
                HumanMessage(content=user_prompt)
            ]),
            timeout=LLM_TIMEOUT_TEXT
        )

        # Save the final state to a JSON file for debugging and records
        session_output_directory = state.get("output_directory", "output")
        session_id = state.get("session_id", "unknown_session")
        finalizer_directory = os.path.join(session_output_directory, "file_analysis")
        await asyncio.to_thread(os.makedirs, finalizer_directory, exist_ok=True)
        json_filename = f"file_analysis_final_state_session_{session_id}.json"
        json_path = os.path.join(finalizer_directory, json_filename)
        await dump_state_to_file(state, json_path)
        
        verdict = static_analysis_final_report.final_verdict
        ioc_count = len(static_analysis_final_report.indicators_of_compromise)
        attack_chain_count = len(static_analysis_final_report.attack_chain)
        
        logger.info(
            f"⚖️ Final Verdict: {verdict}",
            agent="FileAnalysis",
            node="summarize_file_analysis",
            event_type="VERDICT_GENERATED",
            verdict=verdict,
            ioc_count=ioc_count,
            attack_chain_steps=attack_chain_count
        )
        
        # Log executive summary with escaped curly braces to prevent logger.format() errors
        safe_exec_summary = static_analysis_final_report.executive_summary[:150].replace('{', '{{').replace('}', '}}')
        logger.info(
            f"📝 Executive Summary: {safe_exec_summary}...",
            agent="FileAnalysis",
            node="summarize_file_analysis",
            event_type="EXECUTIVE_SUMMARY",
            summary=static_analysis_final_report.executive_summary
        )
        
        # Log IOCs if present
        if ioc_count > 0:
            logger.info(
                f"🚨 Found {ioc_count} Indicator(s) of Compromise",
                agent="FileAnalysis",
                node="summarize_file_analysis",
                event_type="IOCS_FOUND",
                ioc_count=ioc_count
            )
            for idx, ioc in enumerate(static_analysis_final_report.indicators_of_compromise[:5], 1):  # Show first 5
                logger.debug(
                    f"  {idx}. {ioc.ioc_type}: {ioc.value}",
                    agent="FileAnalysis",
                    node="summarize_file_analysis",
                    ioc_index=idx,
                    ioc_type=ioc.ioc_type,
                    ioc_value=ioc.value
                )
        
        logger.info(
            f"✅ File analysis complete - state saved to {json_filename}",
            agent="FileAnalysis",
            node="summarize_file_analysis",
            event_type="ANALYSIS_COMPLETE",
            output_file=json_filename
        )
        
        return {"static_analysis_final_report": static_analysis_final_report}
    
    except asyncio.TimeoutError:
        error_msg = f"Error in summarize_file_analysis: Finalizer LLM call timed out after {LLM_TIMEOUT_TEXT} seconds"
        logger.error(
            "Error in summarize_file_analysis: Finalizer LLM call timed out after {} seconds",
            LLM_TIMEOUT_TEXT,
            agent="FileAnalysis",
            node="summarize_file_analysis",
            event_type="ERROR",
            timeout_seconds=LLM_TIMEOUT_TEXT,
            exc_info=True
        )
        return {"errors": [error_msg]}
    except Exception as e:
        error_msg = f"Error in summarize_file_analysis: {type(e).__name__}: {e}"
        logger.error(
            "Error in summarize_file_analysis: {}: {}",
            type(e).__name__,
            str(e),
            agent="FileAnalysis",
            node="summarize_file_analysis",
            event_type="ERROR",
            exc_info=True
        )
        return {"errors": [error_msg]}
