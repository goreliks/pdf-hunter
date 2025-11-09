import json
import os
import asyncio
from datetime import datetime
from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import get_current_run_tree
from pdf_hunter.config import report_generator_llm, final_verdict_llm
from .schemas import ReportGeneratorState, FinalVerdict
from pdf_hunter.shared.utils.serializer import serialize_state_safely, dump_state_to_file
from .prompts import REPORT_GENERATOR_SYSTEM_PROMPT, REPORT_GENERATOR_USER_PROMPT, REPORT_GENERATOR_VERDICT_SYSTEM_PROMPT, REPORT_GENERATOR_VERDICT_USER_PROMPT
from pdf_hunter.config.execution_config import LLM_TIMEOUT_TEXT


def _strip_base64_from_state(state: ReportGeneratorState) -> dict:
    """
    Strip base64_data from extracted_images to reduce token usage.

    The report generator doesn't need to see the actual images - it synthesizes
    findings from the image analysis agent. Keeping only metadata reduces
    token usage by ~80-90% on image-heavy PDFs.

    Args:
        state: The full report generator state

    Returns:
        A copy of the state with base64_data removed from extracted_images
    """
    import copy

    # Deep copy to avoid mutating original state
    sanitized_state = copy.deepcopy(dict(state))

    # Strip base64_data from each extracted image
    if "extracted_images" in sanitized_state and sanitized_state["extracted_images"]:
        sanitized_images = []
        for image in sanitized_state["extracted_images"]:
            # Convert Pydantic model to dict if needed
            image_dict = image.model_dump() if hasattr(image, 'model_dump') else dict(image)

            # Create new dict without base64_data, keeping only metadata
            sanitized_image = {
                "page_number": image_dict.get("page_number"),
                "image_format": image_dict.get("image_format"),
                "phash": image_dict.get("phash"),
                "saved_path": image_dict.get("saved_path"),
                "image_sha1": image_dict.get("image_sha1")
            }
            sanitized_images.append(sanitized_image)

        sanitized_state["extracted_images"] = sanitized_images

        logger.debug(
            f"Stripped base64 data from {len(sanitized_images)} images for token optimization",
            agent="ReportGenerator",
            node="_strip_base64_from_state",
            image_count=len(sanitized_images)
        )

    return sanitized_state


async def determine_threat_verdict(state: ReportGeneratorState) -> dict:
    """
    Determine the overall security verdict based on all agent analyses.
    """
    logger.info("🎯 Starting final verdict determination", agent="ReportGenerator", node="determine_threat_verdict", event_type="VERDICT_DETERMINATION_START")

    try:
        logger.debug("Serializing state for verdict determination", agent="ReportGenerator", node="determine_threat_verdict")
        # Strip base64 image data before serialization to reduce token usage
        sanitized_state = _strip_base64_from_state(state)
        serialized_state = serialize_state_safely(sanitized_state)
        
        # Log key state information for debugging
        logger.debug(
            f"State snapshot: {len(state.get('extracted_images', []))} images | "
            f"Triage: {state.get('triage_classification_decision', 'No data')} | "
            f"URLs analyzed: {len(state.get('link_analysis_final_reports', []))}",
            agent="ReportGenerator",
            node="determine_threat_verdict"
        )

        # This node now ONLY uses the raw state, as it runs before the report is generated.
        # This fixes the KeyError and aligns with our desired logical flow.
        logger.debug("Creating verdict determination prompt", agent="ReportGenerator", node="determine_threat_verdict")
        messages = [
            SystemMessage(content=REPORT_GENERATOR_VERDICT_SYSTEM_PROMPT),
            HumanMessage(content=REPORT_GENERATOR_VERDICT_USER_PROMPT.format(
                serialized_state=json.dumps(serialized_state, indent=2)
                # The markdown_report is correctly removed from the input
            )),
        ]

        # Use a separate, structured-output LLM for the final verdict
        logger.debug("Invoking final verdict LLM", agent="ReportGenerator", node="determine_threat_verdict")
        llm_with_verdict = final_verdict_llm.with_structured_output(FinalVerdict)
        # Add timeout protection to prevent infinite hangs on verdict LLM calls
        response = await asyncio.wait_for(
            llm_with_verdict.ainvoke(messages),
            timeout=LLM_TIMEOUT_TEXT
        )
        
        # Log complete FinalVerdict with all schema fields
        reasoning_preview = response.reasoning[:100] + "..." if len(response.reasoning) > 100 else response.reasoning
        logger.info(
            f"🎯 Final Verdict: {response.verdict} | Confidence: {response.confidence:.1%} | Reasoning: {reasoning_preview}",
            agent="ReportGenerator",
            node="determine_threat_verdict",
            event_type="VERDICT_DETERMINED",
            verdict=response.verdict,
            confidence=response.confidence,
            reasoning_preview=reasoning_preview,
            full_reasoning=response.reasoning  # Full text in JSON for streaming
        )

        return {"final_verdict": response}
    
    except asyncio.TimeoutError:
        error_msg = f"Error in determine_threat_verdict: Verdict LLM call timed out after {LLM_TIMEOUT_TEXT} seconds"
        logger.error(
            "Error in determine_threat_verdict: Verdict LLM call timed out after {} seconds",
            LLM_TIMEOUT_TEXT,
            agent="ReportGenerator",
            node="determine_threat_verdict",
            event_type="ERROR",
            timeout_seconds=LLM_TIMEOUT_TEXT,
            exc_info=True
        )
        return {"errors": [[error_msg]]}
    except Exception as e:
        error_msg = f"Error in determine_threat_verdict: {type(e).__name__}: {e}"
        logger.error(
            "Error in determine_threat_verdict: {}: {}",
            type(e).__name__,
            str(e),
            agent="ReportGenerator",
            node="determine_threat_verdict",
            event_type="ERROR",
            exc_info=True
        )
        return {"errors": [[error_msg]]}


async def generate_final_report(state: ReportGeneratorState):
    """
    Generate a comprehensive final report summarizing all findings.
    Node to create a comprehensive Markdown report based on the full investigation state,
    which now includes the final verdict. Acts as the "Intelligence Briefer".
    """
    logger.info("📝 Starting final report generation", agent="ReportGenerator", node="generate_final_report", event_type="REPORT_GENERATION_START")

    try:
        # The state now contains the 'final_verdict' from the previous node.
        logger.debug("Serializing full state for report generation", agent="ReportGenerator", node="generate_final_report")
        # Strip base64 image data before serialization to reduce token usage
        sanitized_state = _strip_base64_from_state(state)
        serialized_state = serialize_state_safely(sanitized_state)

        logger.debug("Creating report generator prompt", agent="ReportGenerator", node="generate_final_report")
        messages = [
            SystemMessage(content=REPORT_GENERATOR_SYSTEM_PROMPT),
            HumanMessage(content=REPORT_GENERATOR_USER_PROMPT.format(serialized_state=json.dumps(serialized_state, indent=2))),
        ]

        logger.debug("Invoking report generator LLM", agent="ReportGenerator", node="generate_final_report")
        # Add timeout protection to prevent infinite hangs on report generator LLM calls
        response = await asyncio.wait_for(
            report_generator_llm.ainvoke(messages),
            timeout=LLM_TIMEOUT_TEXT
        )
        final_report = response.content
        
        # Log report generation completion with full markdown report for streaming
        report_snippet = final_report[:200] + "..." if len(final_report) > 200 else final_report
        logger.debug(f"Generated report snippet: {report_snippet}", agent="ReportGenerator", node="generate_final_report")
        
        logger.info(
            f"📝 Report generated: {len(final_report)} chars",
            agent="ReportGenerator",
            node="generate_final_report",
            event_type="REPORT_GENERATION_COMPLETE",
            report_length=len(final_report),
            report_preview=report_snippet,
            markdown_report=final_report  # Full markdown report for frontend rendering
        )
        
        return {"final_report": final_report}
    
    except asyncio.TimeoutError:
        error_msg = f"Error in generate_final_report: LLM call timed out after {LLM_TIMEOUT_TEXT} seconds"
        logger.error(
            "Error in generate_final_report: LLM call timed out after {} seconds",
            LLM_TIMEOUT_TEXT,
            agent="ReportGenerator",
            node="generate_final_report",
            event_type="ERROR",
            timeout_seconds=LLM_TIMEOUT_TEXT,
            exc_info=True
        )
        return {"errors": [[error_msg]]}
    except Exception as e:
        error_msg = f"Error in generate_final_report: {type(e).__name__}: {e}"
        logger.error(
            "Error in generate_final_report: {}: {}",
            type(e).__name__,
            str(e),
            agent="ReportGenerator",
            node="generate_final_report",
            event_type="ERROR",
            exc_info=True
        )
        return {"errors": [[error_msg]]}



async def save_analysis_results(state: ReportGeneratorState):
    """
    Write the final report and state to files.
    """
    logger.info("💾 Starting file save operations", agent="ReportGenerator", node="save_analysis_results", event_type="SAVE_START")

    try:
        session_output_directory = state.get("output_directory", "output")
        session_id = state.get("session_id", "unknown_session")
        
        logger.debug(f"Session ID: {session_id} | Output: {session_output_directory}", agent="ReportGenerator", node="save_analysis_results")

        # Create report generator subdirectory
        report_generator_directory = os.path.join(session_output_directory, "report_generator")
        await asyncio.to_thread(os.makedirs, report_generator_directory, exist_ok=True)
        logger.debug(f"Created report directory: {report_generator_directory}", agent="ReportGenerator", node="save_analysis_results")

        # --- Save the complete state to a JSON file for debugging and records ---
        json_filename = f"final_state_session_{session_id}.json"
        json_path = os.path.join(report_generator_directory, json_filename)
        
        logger.debug(f"Saving complete state to: {json_path}", agent="ReportGenerator", node="save_analysis_results")
        await dump_state_to_file(state, json_path)
        logger.info(f"💾 State saved: {json_path}", agent="ReportGenerator", node="save_analysis_results", event_type="STATE_SAVED", file_path=json_path)

        # --- Save the final, complete Markdown report ---
        report_filename = f"final_report_session_{session_id}.md"
        report_path = os.path.join(report_generator_directory, report_filename)
        
        logger.debug(f"Saving final markdown report to: {report_path}", agent="ReportGenerator", node="save_analysis_results")
        
        # The 'final_report' from the state is now the complete, definitive version.
        # No "enhancing" is needed.
        final_md_report = state.get("final_report", "# PDF Hunter Report\n\nError: Final report could not be generated.")

        # Define a regular function to handle file writing
        def write_file(path, content):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Execute the function in a separate thread
        await asyncio.to_thread(write_file, report_path, final_md_report)
        logger.info(f"💾 Report saved: {report_path}", agent="ReportGenerator", node="save_analysis_results", event_type="REPORT_SAVED", file_path=report_path)

        # Log final verdict summary
        final_verdict = state.get("final_verdict", None)
        if final_verdict:
            verdict = final_verdict.verdict
            confidence = final_verdict.confidence
            reasoning_preview = final_verdict.reasoning[:80] + "..." if len(final_verdict.reasoning) > 80 else final_verdict.reasoning
        else:
            verdict = "Unknown"
            confidence = 0.0
            reasoning_preview = "No verdict available"
        
        logger.info(
            f"✅ Analysis Complete | Verdict: {verdict} | Confidence: {confidence:.1%} | Reasoning: {reasoning_preview}",
            agent="ReportGenerator",
            node="save_analysis_results",
            event_type="ANALYSIS_COMPLETE",
            final_verdict=verdict,
            final_confidence=confidence,
            report_path=report_path,
            state_path=json_path,
            session_id=session_id
        )
        
        return {}
    
    except Exception as e:
        error_msg = f"Error in save_analysis_results: {e}"
        logger.error(error_msg, agent="ReportGenerator", node="save_analysis_results", event_type="ERROR", exc_info=True)
        return {"errors": [[error_msg]]}
