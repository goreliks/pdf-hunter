import json
import os
import logging
import asyncio
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from pdf_hunter.config import report_generator_llm, final_verdict_llm
from pdf_hunter.orchestrator.schemas import OrchestratorState
from pdf_hunter.shared.utils.serializer import serialize_state_safely, dump_state_to_file
from pdf_hunter.shared.utils.logging_config import get_logger
from .prompts import REPORT_GENERATOR_SYSTEM_PROMPT, REPORT_GENERATOR_USER_PROMPT, REPORT_GENERATOR_VERDICT_SYSTEM_PROMPT, REPORT_GENERATOR_VERDICT_USER_PROMPT
from .schemas import FinalVerdict

# Initialize logger
logger = get_logger(__name__)


async def determine_threat_verdict(state: OrchestratorState) -> dict:
    """
    Determine the overall security verdict based on all agent analyses.
    """
    logger.info("Determining final security verdict for PDF")
    
    try:
        logger.debug("Serializing state for verdict determination")
        serialized_state = serialize_state_safely(state)
        
        # Log key state information for debugging
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"PDF extraction results: {len(state.get('pdf_extraction_results', {}).get('extracted_images', []))} images")
            logger.debug(f"File analysis: {state.get('file_analysis_report', {}).get('triage_classification_decision', 'No data')}")
            logger.debug(f"URL investigation results: {len(state.get('url_investigation_results', []))} URLs analyzed")

        # This node now ONLY uses the raw state, as it runs before the report is generated.
        # This fixes the KeyError and aligns with our desired logical flow.
        logger.debug("Creating verdict determination prompt")
        messages = [
            SystemMessage(content=REPORT_GENERATOR_VERDICT_SYSTEM_PROMPT),
            HumanMessage(content=REPORT_GENERATOR_VERDICT_USER_PROMPT.format(
                serialized_state=json.dumps(serialized_state, indent=2)
                # The markdown_report is correctly removed from the input
            )),
        ]

        # Use a separate, structured-output LLM for the final verdict
        logger.debug("Invoking final verdict LLM")
        llm_with_verdict = final_verdict_llm.with_structured_output(FinalVerdict)
        response = await llm_with_verdict.ainvoke(messages)
        logger.info(f"Final verdict determined: {response.verdict} (confidence: {response.confidence})")

        return {"final_verdict": response}
    
    except Exception as e:
        error_msg = f"Error in determine_threat_verdict: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": [error_msg]}


async def generate_final_report(state: OrchestratorState) -> dict:
    """
    Generate a comprehensive final report summarizing all findings.
    Node to create a comprehensive Markdown report based on the full investigation state,
    which now includes the final verdict. Acts as the "Intelligence Briefer".
    """
    logger.info("Generating comprehensive final report")

    try:
        # The state now contains the 'final_verdict' from the previous node.
        logger.debug("Serializing full state for report generation")
        serialized_state = serialize_state_safely(state)

        logger.debug("Creating report generator prompt")
        messages = [
            SystemMessage(content=REPORT_GENERATOR_SYSTEM_PROMPT),
            HumanMessage(content=REPORT_GENERATOR_USER_PROMPT.format(serialized_state=json.dumps(serialized_state, indent=2))),
        ]

        logger.debug("Invoking report generator LLM")
        response = await report_generator_llm.ainvoke(messages)
        final_report = response.content
        
        # Log a snippet of the report for debugging
        if logger.isEnabledFor(logging.DEBUG):
            report_snippet = final_report[:200] + "..." if len(final_report) > 200 else final_report
            logger.debug(f"Generated report snippet: {report_snippet}")
        
        logger.info("Final report generation complete")
        return {"final_report": final_report}
    
    except Exception as e:
        error_msg = f"Error in generate_final_report: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": [error_msg]}


async def save_analysis_results(state: OrchestratorState) -> dict:
    """
    Write the final report and state to files.
    """
    logger.info("Saving final analysis results to files")

    try:
        session_output_directory = state.get("output_directory", "output")
        session_id = state.get("session_id", "unknown_session")
        
        logger.debug(f"Session ID: {session_id}")
        logger.debug(f"Output directory: {session_output_directory}")

        # Create report generator subdirectory
        report_generator_directory = os.path.join(session_output_directory, "report_generator")
        await asyncio.to_thread(os.makedirs, report_generator_directory, exist_ok=True)
        logger.debug(f"Created report directory: {report_generator_directory}")

        # --- Save the complete state to a JSON file for debugging and records ---
        json_filename = f"final_state_session_{session_id}.json"
        json_path = os.path.join(report_generator_directory, json_filename)
        
        logger.debug(f"Saving complete state to: {json_path}")
        await dump_state_to_file(state, json_path)
        logger.info(f"Complete state saved to: {json_path}")

        # --- Save the final, complete Markdown report ---
        report_filename = f"final_report_session_{session_id}.md"
        report_path = os.path.join(report_generator_directory, report_filename)
        
        logger.debug(f"Saving final markdown report to: {report_path}")
        
        # The 'final_report' from the state is now the complete, definitive version.
        # No "enhancing" is needed.
        final_md_report = state.get("final_report", "# PDF Hunter Report\n\nError: Final report could not be generated.")

        # Define a regular function to handle file writing
        def write_file(path, content):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Execute the function in a separate thread
        await asyncio.to_thread(write_file, report_path, final_md_report)
        logger.info(f"Final report written to: {report_path}")

        # Log final verdict summary
        final_verdict = state.get("final_verdict", None)
        if final_verdict:
            verdict = final_verdict.verdict
            confidence = final_verdict.confidence
        else:
            verdict = "Unknown"
            confidence = 0
        logger.info(f"Analysis complete - Final verdict: {verdict} (confidence: {confidence})")
        
        return {}
    
    except Exception as e:
        error_msg = f"Error in save_analysis_results: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": [error_msg]}
