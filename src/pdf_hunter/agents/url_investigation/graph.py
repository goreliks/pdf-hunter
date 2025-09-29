import asyncio
import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from langgraph.graph import StateGraph, START, END

from .schemas import URLInvestigationState, URLInvestigationInputState, URLInvestigationOutputState, URLInvestigatorState, URLInvestigatorOutputState
from ..image_analysis.schemas import PrioritizedURL
from .nodes import investigate_url, execute_browser_tools, analyze_url_content, should_continue, route_url_analysis, filter_high_priority_urls, save_url_analysis_state
from ...shared.utils.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)


link_investigator_state = StateGraph(URLInvestigatorState, output_schema=URLInvestigatorOutputState)

# Add the nodes to the graph
link_investigator_state.add_node("investigate_url", investigate_url)
link_investigator_state.add_node("execute_browser_tools", execute_browser_tools)
link_investigator_state.add_node("analyze_url_content", analyze_url_content)
link_investigator_state.add_edge(START, "investigate_url")
link_investigator_state.add_conditional_edges(
    "investigate_url",
    should_continue
)
link_investigator_state.add_edge("execute_browser_tools", "investigate_url")
link_investigator_state.add_edge("analyze_url_content", END)
# Compile the graph and export it for external use
link_investigator_graph = link_investigator_state.compile()


async def conduct_link_analysis(state: dict):
    """
    Wrapper for the investigator subgraph that ensures outputs are collected
    into the completed_investigations list.
    """
    url_task = state.get("url_task")
    url = url_task.url if url_task else "unknown URL"
    
    logger.info(f"Starting link analysis for URL: {url}")
    
    try:
        # Run the investigator subgraph
        logger.debug("Invoking link investigator graph")
        result = await link_investigator_graph.ainvoke(state)
        
        # The result should contain the fields from InvestigatorOutputState
        # We need to wrap it in a list so it gets aggregated via operator.add
        logger.info(f"Link analysis complete for URL: {url}")
        return {
            "link_analysis_final_reports": [result]  # This will be aggregated
        }
    except Exception as e:
        logger.error(f"Error during link analysis for URL {url}: {str(e)}", exc_info=True)
        # Re-raise to allow proper handling by the orchestrator
        raise


pipeline = StateGraph(URLInvestigationState, input_schema=URLInvestigationInputState, output_schema=URLInvestigationOutputState)

pipeline.add_node("filter_high_priority_urls", filter_high_priority_urls)
pipeline.add_node("conduct_link_analysis", conduct_link_analysis)
pipeline.add_node("save_url_analysis_state", save_url_analysis_state)
pipeline.add_edge(START, "filter_high_priority_urls")
pipeline.add_conditional_edges("filter_high_priority_urls", route_url_analysis, ["conduct_link_analysis", "save_url_analysis_state"])
pipeline.add_edge("conduct_link_analysis", "save_url_analysis_state")
pipeline.add_edge("save_url_analysis_state", END)

link_analysis_graph = pipeline.compile()

if __name__ == "__main__":
    from .schemas import PrioritizedURL
    import asyncio
    from ...shared.utils.logging_config import configure_logging

    # Configure more detailed logging when running directly
    configure_logging(level=logging.INFO)
    
    output_dir = "./outputs/test_link_analysis"
    logger.info(f"Setting up test with output directory: {output_dir}")

    test_state = {
        "visual_analysis_report": {
            "all_priority_urls": [
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
        },
        "output_directory": output_dir
    }

    async def main():
        logger.info("Running the full URL Investigator -> Analyst pipeline")
        
        try:
            logger.debug("Invoking link analysis graph with test state")
            final_state = await link_analysis_graph.ainvoke(test_state)
            logger.info("Link analysis graph execution complete")
        except Exception as e:
            logger.error(f"Error during link analysis: {str(e)}", exc_info=True)
            raise
        finally:
            # Cleanup all MCP sessions when done
            from ...shared.utils.mcp_client import cleanup_mcp_session
            logger.debug("Cleaning up MCP sessions")
            await cleanup_mcp_session()  # This will cleanup all sessions
        
        logger.info("Generating final forensic report")
        if final_state.get("link_analysis_final_reports"):
            logger.info(f"Generated {len(final_state['link_analysis_final_reports'])} URL analysis reports")
            for i, report in enumerate(final_state["link_analysis_final_reports"]):
                url = report.get("initial_url", {}).get("url", f"Report #{i}")
                logger.info(f"Report for URL: {url}")
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Report details: {report.model_dump_json(indent=2)}")
        else:
            logger.warning("No final report generated")

    asyncio.run(main())