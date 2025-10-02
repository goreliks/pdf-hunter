"""CLI interface for the PDF extraction agent."""

import os
import asyncio
import argparse
from loguru import logger
from pdf_hunter.config.logging_config import setup_logging

from .graph import preprocessing_graph


def parse_args():
    """Parse command-line arguments for the PDF extraction agent."""
    parser = argparse.ArgumentParser(
        description="PDF Extraction Agent - Extract images, URLs, and QR codes from PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use defaults (hello_qr_and_link.pdf, 1 page)
  uv run python -m pdf_hunter.agents.pdf_extraction.graph

  # Extract from specific file
  uv run python -m pdf_hunter.agents.pdf_extraction.graph --file test_mal_one.pdf

  # Process multiple pages
  uv run python -m pdf_hunter.agents.pdf_extraction.graph --pages 5

  # Custom output directory
  uv run python -m pdf_hunter.agents.pdf_extraction.graph --output ./my_extractions

  # Enable debug logging
  uv run python -m pdf_hunter.agents.pdf_extraction.graph --debug
        """
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        default="hello_qr_and_link.pdf",
        help="PDF file to extract from (default: hello_qr_and_link.pdf from tests/assets/pdfs/)"
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
        help="Output directory for extraction results (default: output/pdf_extraction_results)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to terminal (default: INFO level)"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point for the PDF extraction CLI."""
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
        logger.error(f"File not found: {file_path}", agent="pdf_extraction_test")
        return None
    
    # Determine output directory
    if args.output and os.path.isabs(args.output):
        output_directory = args.output
    else:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))
        output_subdir = args.output if args.output else os.path.join("output", "pdf_extraction_results")
        output_directory = os.path.join(project_root, output_subdir)

    initial_state = {
        "file_path": file_path,
        "output_directory": output_directory,
        "number_of_pages_to_process": args.pages,
    }

    logger.info(f"Running PDF Extraction on: {file_path}",
                agent="pdf_extraction_test",
                test_file=file_path)

    final_state = await preprocessing_graph.ainvoke(initial_state)

    session_id = final_state.get('session_id', 'unknown')
    logger.info("PDF Extraction Complete",
                agent="pdf_extraction_test",
                session_id=session_id)

    # Verification
    if final_state.get("errors"):
        logger.warning(f"Completed with {len(final_state['errors'])} error(s)",
                      agent="pdf_extraction_test",
                      session_id=session_id,
                      error_count=len(final_state["errors"]))
        for error in final_state["errors"]:
            logger.error(f"Error: {error}",
                       agent="pdf_extraction_test",
                       session_id=session_id)
    else:
        logger.success("✅ PDF Extraction completed successfully",
                      agent="pdf_extraction_test",
                      session_id=session_id,
                      images_extracted=len(final_state.get('extracted_images', [])),
                      urls_found=len(final_state.get('extracted_urls', [])))


if __name__ == "__main__":
    asyncio.run(main())
