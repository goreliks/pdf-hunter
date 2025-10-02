"""CLI interface for the image analysis agent."""

import os
import asyncio
import argparse
from loguru import logger
from pdf_hunter.config.logging_config import setup_logging

from ..pdf_extraction.graph import preprocessing_graph
from .graph import visual_analysis_graph


def parse_args():
    """Parse command-line arguments for the image analysis agent."""
    parser = argparse.ArgumentParser(
        description="Image Analysis Agent - Visual Deception Analysis for PDF pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use defaults (test_mal_one.pdf, 1 page)
  uv run python -m pdf_hunter.agents.image_analysis.graph

  # Analyze specific file
  uv run python -m pdf_hunter.agents.image_analysis.graph --file hello_qr_and_link.pdf

  # Process multiple pages
  uv run python -m pdf_hunter.agents.image_analysis.graph --pages 3

  # Custom output directory
  uv run python -m pdf_hunter.agents.image_analysis.graph --output ./my_output

  # Enable debug logging
  uv run python -m pdf_hunter.agents.image_analysis.graph --debug
        """
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        default="test_mal_one.pdf",
        help="PDF file to analyze (default: test_mal_one.pdf from tests/assets/pdfs/)"
    )
    
    parser.add_argument(
        "--pages", "-p",
        type=int,
        default=1,
        help="Number of pages to process (default: 1)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory for analysis results (default: output/image_analysis_results)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to terminal (default: INFO level)"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point for the image analysis CLI."""
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
        logger.error(f"File not found: {file_path}", agent="image_analysis_test")
        return None

    # Determine output directory
    if args.output and os.path.isabs(args.output):
        output_directory = args.output
    else:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))
        output_subdir = args.output if args.output else os.path.join("output", "image_analysis_results")
        output_directory = os.path.join(project_root, output_subdir)

    pages_to_process = args.pages

    logger.info(f"Running Preprocessing on: {file_path}", agent="image_analysis_test", pages=pages_to_process)
    preprocessing_input = {
        "file_path": file_path,
        "output_directory": output_directory,
        "number_of_pages_to_process": pages_to_process,
    }
    # Use ainvoke for preprocessing
    preprocessing_results = await preprocessing_graph.ainvoke(preprocessing_input)
    
    if preprocessing_results.get("errors"):
        logger.error("Preprocessing Failed", agent="image_analysis_test")
        for error in preprocessing_results["errors"]:
            logger.error(f"Error: {error}", agent="image_analysis_test")
        return None
    else:
        logger.info("Preprocessing Succeeded. Preparing for Visual Analysis...", agent="image_analysis_test")

        visual_analysis_input = {
            "extracted_images": preprocessing_results["extracted_images"],
            "extracted_urls": preprocessing_results["extracted_urls"],
            "number_of_pages_to_process": pages_to_process,
            "session_id": preprocessing_results.get("session_id"),
            "output_directory": preprocessing_results.get("output_directory"),
        }

        logger.info(f"Running Visual Analysis on {pages_to_process} page(s)", agent="image_analysis_test")
        
        # Use ainvoke instead of invoke
        final_state = await visual_analysis_graph.ainvoke(visual_analysis_input)

        if final_state.get("errors"):
            logger.error(f"Completed with {len(final_state['errors'])} error(s)", agent="image_analysis_test")
            for error in final_state["errors"]:
                logger.error(f"Error: {error}", agent="image_analysis_test")
        else:
            logger.success("✅ Visual Analysis completed successfully", agent="image_analysis_test")
        
        return final_state


if __name__ == "__main__":
    asyncio.run(main())
