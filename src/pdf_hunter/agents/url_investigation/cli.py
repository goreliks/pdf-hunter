"""CLI interface for the URL investigation agent."""

import asyncio
import argparse
import os
from loguru import logger
from pdf_hunter.config.logging_config import setup_logging

from .schemas import PrioritizedURL
from .graph import link_analysis_graph


def parse_args():
    """Parse command-line arguments for the URL investigation agent."""
    parser = argparse.ArgumentParser(
        description="URL Investigation Agent - Test standalone URL analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default test URLs
  uv run python -m pdf_hunter.agents.url_investigation.graph

  # Test with custom URLs
  uv run python -m pdf_hunter.agents.url_investigation.graph --url https://example.com --url https://suspicious-site.com

  # Custom output directory
  uv run python -m pdf_hunter.agents.url_investigation.graph --output ./test_output

  # Enable debug logging
  uv run python -m pdf_hunter.agents.url_investigation.graph --debug
        """
    )
    
    parser.add_argument(
        "--url", "-u",
        action="append",
        type=str,
        help="URL to investigate (can be specified multiple times for multiple URLs)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory for analysis results (default: output/test_url_analysis in project root)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to terminal (default: INFO level)"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point for the URL investigation CLI."""
    args = parse_args()
    
    # Configure logging
    setup_logging(debug_to_terminal=args.debug or True)
    
    # Determine output directory - if absolute path provided, use it directly
    # Otherwise, use path relative to project root
    if args.output and os.path.isabs(args.output):
        output_dir = args.output
    else:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))
        output_subdir = args.output if args.output else os.path.join("output", "test_url_analysis")
        output_dir = os.path.join(project_root, output_subdir)
    
    logger.info(f"Setting up test with output directory: {output_dir}", agent="TestRunner", node="setup")
    
    # Determine URLs to test
    if args.url:
        # Use URLs from command line
        priority_urls = [
            PrioritizedURL(
                url=url,
                reason="URL provided via command line",
                priority=i + 1,
                page_number=0
            )
            for i, url in enumerate(args.url)
        ]
        logger.info(f"Testing {len(priority_urls)} URLs from command line", agent="TestRunner", node="setup")
    else:
        # Use default test URLs
        priority_urls = [
            PrioritizedURL(
                url="https://www.qrcode-monkey.com/",
                reason="Example URL for testing",
                priority=1,
                page_number=0
            ),
            PrioritizedURL(
                url="https://docs.langchain.com/oss/python/langgraph/graph-api#command",
                reason="Test URL for testing",
                priority=2,
                page_number=1
            )
        ]
        logger.info("Using default test URLs", agent="TestRunner", node="setup")

    test_state = {
        "visual_analysis_report": {
            "all_priority_urls": priority_urls
        },
        "output_directory": output_dir
    }

    logger.info("Running the full URL Investigator -> Analyst pipeline", agent="TestRunner", node="main")
    
    try:
        logger.debug("Invoking link analysis graph with test state", agent="TestRunner", node="main")
        final_state = await link_analysis_graph.ainvoke(test_state)
        logger.info("Link analysis graph execution complete", agent="TestRunner", node="main")
    except Exception as e:
        logger.error(f"Error during link analysis: {str(e)}", agent="TestRunner", node="main", exc_info=True)
        raise
    finally:
        # Cleanup all MCP sessions when done
        from ...shared.utils.mcp_client import cleanup_mcp_session
        logger.debug("Cleaning up MCP sessions", agent="TestRunner", node="main")
        await cleanup_mcp_session()  # This will cleanup all sessions
    
    logger.info("Generating final forensic report", agent="TestRunner", node="verify")
    if final_state.get("link_analysis_final_reports"):
        logger.info(f"Generated {len(final_state['link_analysis_final_reports'])} URL analysis reports", agent="TestRunner", node="verify")
        for i, report in enumerate(final_state["link_analysis_final_reports"]):
            # Handle both dict and Pydantic model formats
            if isinstance(report, dict):
                url = report.get('initial_url', {}).get('url', f"Report #{i}")
                logger.info(f"Report for URL: {url}", agent="TestRunner", node="verify")
                logger.debug(f"Report verdict: {report.get('analyst_findings', {}).get('verdict', 'Unknown')}", agent="TestRunner", node="verify")
            else:
                url = report.initial_url.url if hasattr(report, 'initial_url') else f"Report #{i}"
                logger.info(f"Report for URL: {url}", agent="TestRunner", node="verify")
                logger.debug(f"Report details: {report.model_dump_json(indent=2)}", agent="TestRunner", node="verify")
    else:
        logger.warning("No final report generated", agent="TestRunner", node="verify")


if __name__ == "__main__":
    asyncio.run(main())
