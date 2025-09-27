# src/pdf_hunter/agents/finalizer/nodes.py

import json
import os
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from pdf_hunter.config import finalizer_llm, final_verdict_llm
from pdf_hunter.orchestrator.schemas import OrchestratorState
from pdf_hunter.shared.utils.serializer import serialize_state_safely
from .prompts import FINALIZER_SYSTEM_PROMPT, FINALIZER_USER_PROMPT, FINAL_VERDICT_SYSTEM_PROMPT, FINAL_VERDICT_USER_PROMPT
from .schemas import FinalVerdict


def final_verdict_node(state: OrchestratorState) -> dict:
    """
    Node to review all evidence from the raw state to provide the final,
    authoritative verdict. Acts as the "Final Adjudicator". This runs FIRST.
    """
    print("--- Finalizer Node: Generating Final Verdict ---")

    serialized_state = serialize_state_safely(state)

    # This node now ONLY uses the raw state, as it runs before the report is generated.
    # This fixes the KeyError and aligns with our desired logical flow.
    messages = [
        SystemMessage(content=FINAL_VERDICT_SYSTEM_PROMPT),
        HumanMessage(content=FINAL_VERDICT_USER_PROMPT.format(
            serialized_state=json.dumps(serialized_state, indent=2)
            # The markdown_report is correctly removed from the input
        )),
    ]

    # Use a separate, structured-output LLM for the final verdict
    llm_with_verdict = final_verdict_llm.with_structured_output(FinalVerdict)
    response = llm_with_verdict.invoke(messages)

    return {"final_verdict": response}


def reporter_node(state: OrchestratorState) -> dict:
    """
    Node to create a comprehensive Markdown report based on the full investigation state,
    which now includes the final verdict. Acts as the "Intelligence Briefer". This runs SECOND.
    """
    print("--- Finalizer Node: Generating Final Report ---")

    # The state now contains the 'final_verdict' from the previous node.
    serialized_state = serialize_state_safely(state)

    messages = [
        SystemMessage(content=FINALIZER_SYSTEM_PROMPT),
        HumanMessage(content=FINALIZER_USER_PROMPT.format(serialized_state=json.dumps(serialized_state, indent=2))),
    ]

    response = finalizer_llm.invoke(messages)
    final_report = response.content

    return {"final_report": final_report}


def write_the_results_to_file(state: OrchestratorState) -> dict:
    """
    Node to write the final state and the final Markdown report to files. This runs LAST.
    """
    print("--- Finalizer Node: Writing Final Results to Files ---")

    session_output_directory = state.get("output_directory", "output")
    session_id = state.get("session_id", "unknown_session")

    # Create finalizer subdirectory
    finalizer_directory = os.path.join(session_output_directory, "finalizer")
    os.makedirs(finalizer_directory, exist_ok=True)

    # --- Save the complete state to a JSON file for debugging and records ---
    json_filename = f"final_state_session_{session_id}.json"
    json_path = os.path.join(finalizer_directory, json_filename)
    serializable_state = serialize_state_safely(state)

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_state, f, indent=4, ensure_ascii=False)
        print(f"--- Final state saved to: {json_path} ---")
    except Exception as e:
        print(f"--- Error writing final state to JSON: {e} ---")

    # --- Save the final, complete Markdown report ---
    report_filename = f"final_report_session_{session_id}.md"
    report_path = os.path.join(finalizer_directory, report_filename)
    
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
