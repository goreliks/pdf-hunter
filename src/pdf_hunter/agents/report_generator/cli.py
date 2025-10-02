"""CLI interface for the report generator agent."""

import json
import pprint
import os
import asyncio
import argparse
import glob
from loguru import logger
from pdf_hunter.config.logging_config import setup_logging

from .graph import report_generator_graph


def parse_args():
    """Parse command-line arguments for the report generator agent."""
    parser = argparse.ArgumentParser(
        description="Report Generator Agent - Generate final security reports and verdicts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-find most recent analysis state
  uv run python -m pdf_hunter.agents.report_generator.graph

  # Use specific state file
  uv run python -m pdf_hunter.agents.report_generator.graph --state /path/to/analysis_state.json

  # Search in specific output directory
  uv run python -m pdf_hunter.agents.report_generator.graph --search-dir ./output

  # Enable debug logging
  uv run python -m pdf_hunter.agents.report_generator.graph --debug
        """
    )
    
    parser.add_argument(
        "--state", "-s",
        type=str,
        help="Path to analysis state JSON file (if not provided, searches for most recent)"
    )
    
    parser.add_argument(
        "--search-dir", "-d",
        type=str,
        default=None,
        help="Directory to search for analysis state files (default: output/ in project root)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to terminal (default: INFO level)"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point for the report generator CLI."""
    args = parse_args()
    
    # Configure logging
    setup_logging(debug_to_terminal=args.debug or True)
    
    test_json_path = args.state
    
    # If no state file specified, search for one
    if not test_json_path:
        # Determine search directory - if absolute path provided, use it directly
        # Otherwise, use output directory relative to project root
        if args.search_dir and os.path.isabs(args.search_dir):
            output_dir = args.search_dir
        else:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))
            search_subdir = args.search_dir if args.search_dir else "output"
            output_dir = os.path.join(project_root, search_subdir)
        logger.info(f"Looking for analysis state files in: {output_dir}", agent="TestRunner", node="search_files")
        
        # Find all JSON files in the output directory (recursively)
        all_json_files = glob.glob(f"{output_dir}/**/*.json", recursive=True)
        
        # Filter for state files (typically contain "state" or "analysis" in name)
        state_files = [f for f in all_json_files if 'state' in os.path.basename(f).lower() or 'analysis' in os.path.basename(f).lower()]
        
        if not state_files:
            logger.warning("No state files found, trying any JSON files", agent="TestRunner", node="search_files")
            state_files = all_json_files
        
        if not state_files:
            logger.warning("No JSON files found in output directory", agent="TestRunner", node="search_files")
            
            # Create a minimal test state
            logger.info("Creating minimal test state", agent="TestRunner", node="create_test_state")
            test_state = {
                "file_path": "/path/to/test.pdf",
                "session_id": "test_session_id",
                "output_directory": "output/test_session",
                "file_analysis_report": {
                    "verdict": "suspicious",
                    "findings": ["Sample test finding for report generator"],
                    "evidence_graph": {"nodes": [], "edges": []}
                },
                "image_analysis_report": {
                    "page_verdicts": [{"page": 0, "verdict": "benign", "confidence": 0.9}],
                    "all_priority_urls": []
                },
                "url_investigation_results": []
            }
            return test_state
        
        # Sort by modification time (most recent first)
        state_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        test_json_path = state_files[0]
        logger.info(f"Found {len(state_files)} state file(s), using most recent", agent="TestRunner", node="search_files")
    
    # Validate file exists
    if not os.path.exists(test_json_path):
        logger.error(f"State file not found: {test_json_path}", agent="TestRunner", node="load_state")
        return None
    
    logger.info(f"Using JSON file: {test_json_path}", agent="TestRunner", node="load_state")
    
    try:
        with open(test_json_path, 'r', encoding='utf-8') as f:
            test_state = json.load(f)
        
        logger.info(f"🚀 Running Report Generator on test state from: {test_json_path}", agent="TestRunner", node="run_graph")
        # Use ainvoke instead of invoke
        final_state = await report_generator_graph.ainvoke(test_state)
        
        logger.success("✅ Report Generator Complete", agent="TestRunner", node="run_graph")
        return final_state
    except FileNotFoundError:
        logger.error(f"File not found: {test_json_path}", agent="TestRunner", node="run_graph")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {test_json_path}", agent="TestRunner", node="run_graph")
        return None
    except Exception as e:
        logger.error(f"Error running report generator: {str(e)}", agent="TestRunner", node="run_graph", exc_info=True)
        return None


async def run_and_verify():
    """Run the report generator and verify results."""
    final_state = await main()
    
    # Verify the results
    if final_state:
        print("\n--- Verification ---")
        if final_state.get("errors"):
            logger.warning(f"Completed with {len(final_state['errors'])} error(s).", agent="TestRunner", node="verify")
        else:
            logger.success("✅ Completed successfully.", agent="TestRunner", node="verify")
            logger.info(f"Final Report Generated: {'Yes' if final_state.get('final_report') else 'No'}", agent="TestRunner", node="verify")
            logger.info(f"Final Verdict Generated: {'Yes' if final_state.get('final_verdict') else 'No'}", agent="TestRunner", node="verify")
            if final_state.get('final_verdict'):
                logger.info("Final Verdict Details:", agent="TestRunner", node="verify")
                pprint.pprint(final_state['final_verdict'].model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(run_and_verify())
