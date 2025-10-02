"""CLI interface for the file analysis agent."""

import json
import os
import uuid
import asyncio
import argparse
from datetime import datetime
from loguru import logger
from pdf_hunter.config.logging_config import setup_logging

from .graph import static_analysis_graph


def parse_args():
    """Parse command-line arguments for the file analysis agent."""
    parser = argparse.ArgumentParser(
        description="File Analysis Agent - Static analysis and threat investigation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use defaults (87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf)
  uv run python -m pdf_hunter.agents.file_analysis.graph

  # Analyze specific file
  uv run python -m pdf_hunter.agents.file_analysis.graph --file test_mal_one.pdf

  # Custom output directory
  uv run python -m pdf_hunter.agents.file_analysis.graph --output ./my_analysis

  # Add additional context
  uv run python -m pdf_hunter.agents.file_analysis.graph --context "Suspicious email attachment"

  # Custom session ID
  uv run python -m pdf_hunter.agents.file_analysis.graph --session my_test_session

  # Enable debug logging
  uv run python -m pdf_hunter.agents.file_analysis.graph --debug
        """
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        default="87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf",
        help="PDF file to analyze (default: 87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf from tests/assets/pdfs/)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory for analysis results (default: output/file_analysis_results)"
    )
    
    parser.add_argument(
        "--context", "-c",
        type=str,
        default=None,
        help="Additional context about the PDF (optional)"
    )
    
    parser.add_argument(
        "--session", "-s",
        type=str,
        default=None,
        help="Session ID for this analysis (default: auto-generated)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to terminal (default: INFO level)"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point for the file analysis CLI."""
    args = parse_args()
    
    # Configure logging
    setup_logging(debug_to_terminal=args.debug or True)
    
    # Determine file path - if absolute path provided, use it directly
    # Otherwise, look in tests/assets/pdfs/
    if os.path.isabs(args.file):
        file_path = args.file
    else:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))
        file_path = os.path.join(project_root, "tests", "assets", "pdfs", args.file)
    
    # Validate file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}", agent="FileAnalysis")
        return None
    
    # Determine output directory
    if args.output and os.path.isabs(args.output):
        output_directory = args.output
    else:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))
        output_subdir = args.output if args.output else os.path.join("output", "file_analysis_results")
        output_directory = os.path.join(project_root, output_subdir)
    
    additional_context = args.context or "None"
    session_id = args.session or str(uuid.uuid4().hex[:8])
    
    logger.info(
        f"Running file analysis on: {file_path}",
        agent="FileAnalysis",
        session_id=session_id
    )

    final_state = None
    async for event in static_analysis_graph.astream({"file_path":file_path,"output_directory": output_directory, "additional_context": additional_context, "session_id": session_id}, stream_mode="values"):
        # Don't log full event as it can be very large
        event_keys = list(event.keys()) if isinstance(event, dict) else "Non-dict event"
        logger.debug(f"Event received with keys: {event_keys}")
        final_state = event
        
    # Save final state to JSON file if available
    if final_state:
        # Generate unique filename with timestamp
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_report_session_{unique_id}_{timestamp}.json"
        
        # Convert final state to JSON-serializable format
        def make_serializable(obj):
            if hasattr(obj, 'model_dump'):
                return obj.model_dump()
            elif isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            else:
                return obj
        
        serializable_state = make_serializable(final_state)
        
        # Ensure output directory exists
        await asyncio.to_thread(os.makedirs, output_directory, exist_ok=True)
        
        # Full path for the JSON file
        json_path = os.path.join(output_directory, filename)
        
        # Save to JSON file
        logger.info(f"Saving final state to {json_path}")
        
        # Define the function to be run in a thread
        def write_json_file():
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_state, f, indent=2, ensure_ascii=False)
        
        # Run the file operation in a separate thread
        await asyncio.to_thread(write_json_file)
        logger.info(f"Final state saved to: {json_path}")
    
    return final_state


if __name__ == "__main__":
    asyncio.run(main())
