import json
import os
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from pdf_hunter.config import report_generator_llm, final_verdict_llm
from pdf_hunter.orchestrator.schemas import OrchestratorState
from pdf_hunter.shared.utils.serializer import serialize_state_safely, dump_state_to_file
from .prompts import REPORT_GENERATOR_SYSTEM_PROMPT, REPORT_GENERATOR_USER_PROMPT, REPORT_GENERATOR_VERDICT_SYSTEM_PROMPT, REPORT_GENERATOR_VERDICT_USER_PROMPT
from .schemas import FinalVerdict


def determine_threat_verdict(state: OrchestratorState) -> dict:
    """
    Determine the overall security verdict based on all agent analyses.
    """
    print("--- Report Generator: Determining Final Security Verdict ---")

    serialized_state = serialize_state_safely(state)

    # This node now ONLY uses the raw state, as it runs before the report is generated.
    # This fixes the KeyError and aligns with our desired logical flow.
    messages = [
        SystemMessage(content=REPORT_GENERATOR_VERDICT_SYSTEM_PROMPT),
        HumanMessage(content=REPORT_GENERATOR_VERDICT_USER_PROMPT.format(
            serialized_state=json.dumps(serialized_state, indent=2)
            # The markdown_report is correctly removed from the input
        )),
    ]

    # Use a separate, structured-output LLM for the final verdict
    llm_with_verdict = final_verdict_llm.with_structured_output(FinalVerdict)
    response = llm_with_verdict.invoke(messages)

    return {"final_verdict": response}


def generate_final_report(state: OrchestratorState) -> dict:
    """
    Generate a comprehensive final report summarizing all findings.
    Node to create a comprehensive Markdown report based on the full investigation state,
    which now includes the final verdict. Acts as the "Intelligence Briefer".
    """
    print("--- Report Generator: Generating Comprehensive Report ---")

    # The state now contains the 'final_verdict' from the previous node.
    serialized_state = serialize_state_safely(state)

    messages = [
        SystemMessage(content=REPORT_GENERATOR_SYSTEM_PROMPT),
        HumanMessage(content=REPORT_GENERATOR_USER_PROMPT.format(serialized_state=json.dumps(serialized_state, indent=2))),
    ]

    response = report_generator_llm.invoke(messages)
    final_report = response.content

    return {"final_report": final_report}


def save_analysis_results(state: OrchestratorState) -> dict:
    """
    Write the final report and state to files.
    """
    print("--- Report Generator: Saving Results to Files ---")

    session_output_directory = state.get("output_directory", "output")
    session_id = state.get("session_id", "unknown_session")

    # Create report generator subdirectory
    report_generator_directory = os.path.join(session_output_directory, "report_generator")
    os.makedirs(report_generator_directory, exist_ok=True)

    # --- Save the complete state to a JSON file for debugging and records ---
    json_filename = f"final_state_session_{session_id}.json"
    json_path = os.path.join(report_generator_directory, json_filename)

    try:
        dump_state_to_file(state, json_path)
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Error saving final state to JSON: {e}"]

    # --- Save the final, complete Markdown report ---
    report_filename = f"final_report_session_{session_id}.md"
    report_path = os.path.join(report_generator_directory, report_filename)
    
    # The 'final_report' from the state is now the complete, definitive version.
    # No "enhancing" is needed.
    final_md_report = state.get("final_report", "# PDF Hunter Report\n\nError: Final report could not be generated.")

    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(final_md_report)
        print(f"--- Final report written to: {report_path} ---")
    except Exception as e:
        print(f"--- Error writing final report to Markdown: {e} ---")

    return {}
