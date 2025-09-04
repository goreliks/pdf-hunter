from .schemas import StaticAnalysisState, MissionStatus, InvestigatorState
from pdf_hunter.shared.analyzers.wrappers import run_pdfid, run_pdf_parser_full_statistical_analysis, run_peepdf
from .prompts import triage_system_prompt, triage_user_prompt, investigator_system_prompt, investigator_user_prompt
import json
from langgraph.types import Command
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.constants import Send
from langchain_core.messages.utils import get_buffer_string
from .tools import pdf_parser_tools_manifest, pdf_parser_tools
from .schemas import EvidenceGraph, MergedEvidenceGraph
from typing import List, Literal
from .prompts import graph_merger_system_prompt, graph_merger_user_prompt
from .prompts import reviewer_system_prompt, reviewer_user_prompt
from .prompts import finalizer_system_prompt, finalizer_user_prompt
from pdf_hunter.config import static_analysis_triage_llm, static_analysis_investigator_llm, static_analysis_graph_merger_llm, static_analysis_reviewer_llm, static_analysis_finalizer_llm
from .schemas import TriageReport,MissionReport, ReviewerReport,FinalReport


llm_router = static_analysis_triage_llm.with_structured_output(TriageReport)
llm_investigator = static_analysis_investigator_llm.with_structured_output(MissionReport)
llm_investigator_with_tools = static_analysis_investigator_llm.bind_tools(pdf_parser_tools)
llm_graph_merger = static_analysis_graph_merger_llm.with_structured_output(MergedEvidenceGraph)
llm_reviewer = static_analysis_reviewer_llm.with_structured_output(ReviewerReport)
llm_finalizer = static_analysis_finalizer_llm.with_structured_output(FinalReport)


def triage_router(state: StaticAnalysisState):
    print("--- Triage Node: Starting Initial Analysis ---")
    file_path = state['file_path']

    pdfid_output = run_pdfid(file_path)
    pdf_parser_output = run_pdf_parser_full_statistical_analysis(file_path)
    peepdf_output = run_peepdf(file_path)
    state['structural_summary'] = {"pdfid": pdfid_output, "pdf_parser": pdf_parser_output, "peepdf": peepdf_output}
    structural_summary = state['structural_summary']
    additional_context = state.get('additional_context', "None")

    system_prompt = triage_system_prompt
    user_prompt = triage_user_prompt.format(
        additional_context=additional_context,
        structural_summary=json.dumps(structural_summary)
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    result = llm_router.invoke(messages)

    updates = {
        "structural_summary": structural_summary,
        "triage_classification_decision": result.triage_classification_decision,
        "triage_classification_reasoning": result.triage_classification_reasoning,
        "mission_list": result.mission_list
    }

    if result.triage_classification_decision == "innocent":
        print("Triage Decision: PDF is Innocent. Ending investigation.")
    elif result.triage_classification_decision == "suspicious":
        print(f"Triage Decision: PDF is Suspicious. Found {len(result.mission_list)} mission(s).")
    else:
        updates["errors"] = ["Invalid triage classification decision from LLM"]

    return updates


def update_mission_list(state: StaticAnalysisState):
    updated_missions = []
    for mission in state['mission_list']:
        if mission.status == MissionStatus.NEW:
            mission.status = MissionStatus.IN_PROGRESS
        updated_missions.append(mission)
    return {"mission_list": updated_missions}


def dispatch_investigations(state: StaticAnalysisState): 
    """
    Dispatches all missions currently in 'NEW' status to the investigator pool.
    Updates the status of dispatched missions to 'IN_PROGRESS'.
    """
    
    print("\n--- Dispatcher Node: Checking for new missions ---")
    
    missions_to_dispatch = [
        m for m in state['mission_list'] 
        if m.status == MissionStatus.IN_PROGRESS 
        and m.mission_id not in state.get('completed_investigations', {})
    ]
    if not missions_to_dispatch:
        return "reviewer_node"
    return [
        Send(
            "conduct_investigation",
            {
                "file_path": state['file_path'],
                "mission": mission,
                "structural_summary": state['structural_summary'],
                "messages": []
            }
        )
        for mission in missions_to_dispatch
    ]


def investigator_node(state: InvestigatorState):
    """
    Investigator node that runs one step of the investigation.
    """
    # Dynamically build the prompt based on whether this is the first turn or not.
    if len(state['messages']) == 0:
        # First turn: Provide the full mission briefing.
        mission = state['mission']
        user_prompt = investigator_user_prompt.format(
            file_path=state['file_path'],
            mission_id=mission.mission_id,
            threat_type=mission.threat_type,
            entry_point_description=mission.entry_point_description,
            reasoning=mission.reasoning,
            structural_summary=json.dumps(state['structural_summary']),
            tool_manifest=json.dumps(pdf_parser_tools_manifest)
        )
        messages = [
            SystemMessage(content=investigator_system_prompt),
            HumanMessage(content=user_prompt),
        ]
    else:
        # Subsequent turns: The history is already in the state.
        messages = state['messages']

    # --- LLM with Tools Call ---
    llm_with_tools = llm_investigator_with_tools
    result = llm_with_tools.invoke(messages)
    
    # --- State and Routing Logic ---
    if not result.tool_calls:
        # The agent has decided the mission is over and did not call a tool.
        print(f"Mission {state['mission'].mission_id} complete. Generating final report.")
        
        # Add the agent's last thought to the history before asking for the report
        final_messages = messages + [result]
        
        # Create a new prompt to force the final structured output
        report_generation_prompt = [
            SystemMessage(content=investigator_system_prompt),
            *final_messages, 
            HumanMessage(content="Your investigation is complete. Based on your findings in the conversation above, provide your final MissionReport in the required JSON format.")
        ]

        mission_report_obj = llm_investigator.invoke(report_generation_prompt)
        validated_report = MissionReport.model_validate(mission_report_obj)

        return {
            "mission": state['mission'],  # Include the mission in the return
            "mission_report": validated_report,
            "messages": final_messages
        }
    else:
        # The agent wants to use a tool - just add the message to state
        return {"messages": [result]}
    

def merge_evidence_graphs(current_master: EvidenceGraph, new_subgraphs: List[EvidenceGraph]) -> EvidenceGraph:
    """Use LLM to intelligently merge evidence graphs, handling duplicates and conflicts"""
    
    # Prepare the data for the LLM
    current_master_json = current_master.model_dump_json(indent=2)
    new_subgraphs_json = json.dumps([g.model_dump() for g in new_subgraphs], indent=2)
    
    user_prompt = graph_merger_user_prompt.format(
        current_master_json=current_master_json,
        new_subgraphs_json=new_subgraphs_json
    )

    result = llm_graph_merger.invoke([
        SystemMessage(content=graph_merger_system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    print(f"Graph Merge Summary: {result.merge_summary}")
    return result.master_graph


def reviewer_node(state: StaticAnalysisState) -> Command[Literal["finalizer_node", "update_mission_list"]]:
    """
    Acts as the "Chief Pathologist." This node now performs two roles:
    1. PROCESSES the raw results from the completed investigations (Reducer's job).
    2. ANALYZES the processed results to decide the next strategic step (Reviewer's job).
    """
    print("\n--- Reviewer Node: Processing and Reviewing Results ---")

    # --- Part 1: PROCESS raw investigation results (The Reducer's Logic) ---
    
    # Initialize or get copies of the data we will be modifying
    current_master_graph = state.get('master_evidence_graph', EvidenceGraph()).copy(deep=True)
    mission_reports = state.get('mission_reports', {}).copy()
    
    # Create a mutable map of missions from the current state's mission list
    mission_map = {m.mission_id: m.copy(deep=True) for m in state['mission_list']}

    # The `completed_investigations` list is our raw input, automatically populated by LangGraph.
    # We must only process investigations that we haven't seen before to avoid errors on the second loop.
    newly_completed_investigations = [
        inv for inv in state.get('completed_investigations', []) 
        if inv['mission'].mission_id not in mission_reports
    ]
    
    print(f"Reviewer: Processing {len(newly_completed_investigations)} new investigation packet(s).")

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
        print(f"Reviewer: Merging {len(new_subgraphs)} investigation graphs intelligently...")
        master_graph = merge_evidence_graphs(current_master_graph, new_subgraphs)
    else:
        master_graph = current_master_graph

    
    # --- Part 2: ANALYZE the complete picture (The Reviewer's Logic) ---
    print("Reviewer: Starting Strategic Review...")
    
    # We use the data we just finished processing for the strategic analysis
    current_mission_list = list(mission_map.values())
    
    master_graph_json = master_graph.model_dump_json(indent=2)
    mission_reports_json = json.dumps({mid: r.model_dump() for mid, r in mission_reports.items()}, indent=2)
    mission_list_json = json.dumps([m.model_dump() for m in current_mission_list], indent=2)
    investigation_transcripts_text = "\n\n".join(investigation_transcripts)

    user_prompt = reviewer_user_prompt.format(
        master_evidence_graph=master_graph_json,
        mission_reports=mission_reports_json,
        mission_list=mission_list_json,
        investigation_transcripts=investigation_transcripts_text
    )
    
    result = llm_reviewer.invoke([
        SystemMessage(content=reviewer_system_prompt),
        HumanMessage(content=user_prompt)
    ])

    print(f"Reviewer Strategic Summary: {result.strategic_summary}")

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
        print("Reviewer Decision: Investigation is complete. Proceeding to finalizer.")
        goto = "finalizer_node"
    else:
        if result.new_missions:
            print(f"Reviewer Decision: Investigation continues. Adding {len(result.new_missions)} new mission(s).")
        else:
            print("Reviewer Decision: Investigation continues, but no new missions were generated. Looping to re-evaluate.")
        goto = "update_mission_list"
        
    return Command(goto=goto, update=updates)


from langchain_core.messages.utils import get_buffer_string

def finalizer_node(state: StaticAnalysisState):
    print("\n--- Finalizer Node: Generating Final Autopsy Report ---")

    master_graph_json = state['master_evidence_graph'].model_dump_json(indent=2)
    mission_reports_json = json.dumps({mid: r.model_dump() for mid, r in state['mission_reports'].items()}, indent=2)
    
    # Format message histories as readable text
    investigation_transcripts = []
    for inv_state in state.get('completed_investigations', []):
        if 'messages' in inv_state:
            mission_id = inv_state['mission'].mission_id
            threat_type = inv_state['mission'].threat_type
            message_history = get_buffer_string(inv_state['messages'])
            investigation_transcripts.append(
                f"=== Mission {mission_id} ({threat_type}) ===\n{message_history}"
            )
    
    completed_investigations_text = "\n\n".join(investigation_transcripts)

    user_prompt = finalizer_user_prompt.format(
        master_evidence_graph=master_graph_json,
        mission_reports=mission_reports_json,
        completed_investigations=completed_investigations_text
    )

    static_analysis_final_report = llm_finalizer.invoke([
        SystemMessage(content=finalizer_system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    print(f"--- Final Report Generated ---\nFinal Verdict: {static_analysis_final_report.final_verdict}")
    
    return {"static_analysis_final_report": static_analysis_final_report}
