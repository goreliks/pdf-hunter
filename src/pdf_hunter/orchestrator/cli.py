"""CLI interface for the PDF Hunter orchestrator."""

import json
import os
import asyncio
import argparse
from loguru import logger

from .graph import orchestrator_graph
from ..shared.utils.serializer import serialize_state_safely
from ..config.logging_config import setup_logging


def parse_args():
    """Parse command-line arguments for the orchestrator."""
    parser = argparse.ArgumentParser(
        description="PDF Hunter - Multi-agent AI framework for PDF threat hunting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use defaults (hello_qr_and_link.pdf, 4 pages)
  uv run python -m pdf_hunter.orchestrator.graph

  # Analyze specific file
  uv run python -m pdf_hunter.orchestrator.graph --file /path/to/suspicious.pdf

  # Process only first page
  uv run python -m pdf_hunter.orchestrator.graph --pages 1

  # Combine options with additional context
  uv run python -m pdf_hunter.orchestrator.graph --file test_mal_one.pdf --pages 2 --context "Received from suspicious email"
        """
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        default="hello_qr_and_link.pdf",
        help="PDF file to analyze (default: hello_qr_and_link.pdf from tests/assets/pdfs/)"
    )
    
    parser.add_argument(
        "--pages", "-p",
        type=int,
        default=4,
        help="Number of pages to process (default: 4)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output",
        help="Base output directory (default: output)"
    )
    
    parser.add_argument(
        "--context", "-c",
        type=str,
        default=None,
        help="Additional context about the PDF (optional)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to terminal (default: INFO level)"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point for the orchestrator CLI."""
    args = parse_args()
    
    # Configure logging with consistent format from the start
    setup_logging(debug_to_terminal=args.debug)
    
    # Determine file path - if absolute path provided, use it directly
    # Otherwise, look in tests/assets/pdfs/
    if os.path.isabs(args.file):
        file_path = args.file
    else:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, "../../.."))
        file_path = os.path.join(project_root, "tests", "assets", "pdfs", args.file)
    
    # Validate file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}", agent="Orchestrator")
        return
    
    orchestrator_input = {
        "file_path": file_path,
        "output_directory": args.output,
        "number_of_pages_to_process": args.pages,
        "additional_context": args.context
    }
    
    logger.info("🚀 Starting PDF Hunter orchestrator",
                agent="Orchestrator",
                file_path=file_path,
                pages_to_process=args.pages,
                additional_context=args.context)
    
    session_id = None
    output_directory = None
    
    try:
        # Stream the orchestrator to reconfigure logging after PDF extraction
        async for event in orchestrator_graph.astream(orchestrator_input, stream_mode="values"):
            # After PDF extraction completes, we have session_id and output_directory
            if event.get('session_id') and event.get('output_directory') and not session_id:
                session_id = event['session_id']
                output_directory = event['output_directory']
                
                # Reconfigure logging to add session-specific log file
                # (Initial setup at startup uses generic config; now we have session context)
                logger.info("📝 Adding session-specific log file",
                           agent="Orchestrator",
                           session_id=session_id,
                           output_directory=output_directory)
                setup_logging(session_id=session_id, 
                             output_directory=output_directory,
                             debug_to_terminal=args.debug)
            
            final_state = event
            
    finally:
        # Cleanup MCP session when done
        from ..shared.utils.mcp_client import cleanup_mcp_session
        logger.debug("Cleaning up MCP session", agent="Orchestrator")
        await cleanup_mcp_session()

    session_id = final_state.get('session_id', 'unknown')
    logger.info("✅ PDF Hunter orchestrator complete",
                agent="Orchestrator",
                session_id=session_id)

    image_analysis_report = final_state.get("image_analysis_report")
    if image_analysis_report:
        logger.info(f"Image Analysis Verdict: {image_analysis_report.overall_verdict}",
                   agent="Orchestrator",
                   session_id=session_id,
                   verdict=image_analysis_report.overall_verdict,
                   confidence=image_analysis_report.overall_confidence)

    # Save final state to JSON file
    if final_state:
        # Use session-specific directory from final state
        session_output_directory = final_state.get('output_directory')
        filename = f"analysis_report_session_{session_id}.json"

        # Ensure output directory exists
        if session_output_directory:
            os.makedirs(session_output_directory, exist_ok=True)

            # Full path for the JSON file
            json_path = os.path.join(session_output_directory, filename)

            # Convert final state to JSON-serializable format
            serializable_state = serialize_state_safely(final_state)

            # Save to JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_state, f, indent=2, ensure_ascii=False)

            logger.info(f"Final state saved to: {json_path}",
                       agent="Orchestrator",
                       session_id=session_id,
                       output_file=json_path)
        else:
            logger.warning("No output directory found in final state",
                         agent="Orchestrator",
                         session_id=session_id)


if __name__ == "__main__":
    # Configure logging with DEBUG output to terminal for development/testing
    setup_logging(debug_to_terminal=True)
    asyncio.run(main())
