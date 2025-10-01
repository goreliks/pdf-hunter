import asyncio
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from loguru import logger
from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphRecursionError

from .schemas import URLInvestigationState, URLInvestigationInputState, URLInvestigationOutputState, URLInvestigatorState, URLInvestigatorOutputState, URLAnalysisResult, AnalystFindings
from ..image_analysis.schemas import PrioritizedURL
from .nodes import investigate_url, execute_browser_tools, analyze_url_content, should_continue, route_url_analysis, filter_high_priority_urls, save_url_analysis_state
from pdf_hunter.config import URL_INVESTIGATION_CONFIG, URL_INVESTIGATION_INVESTIGATOR_CONFIG


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
link_investigator_graph = link_investigator_graph.with_config(URL_INVESTIGATION_INVESTIGATOR_CONFIG)


async def conduct_link_analysis(state: dict):
    """
    Wrapper for the investigator subgraph that ensures outputs are collected
    into the completed_investigations list.
    """
    url_task = state.get("url_task")
    url = url_task.url if url_task else "unknown URL"
    
    logger.info(f"🔍 Starting link analysis for URL: {url}", agent="URLInvestigation", node="conduct_link_analysis_wrapper", event_type="WRAPPER_START", url=url)
    
    try:
        # Run the investigator subgraph
        logger.debug("Invoking link investigator graph", agent="URLInvestigation", node="conduct_link_analysis_wrapper")
        result = await link_investigator_graph.ainvoke(state)
        
        # The result should contain the fields from InvestigatorOutputState
        # We need to wrap it in a list so it gets aggregated via operator.add
        logger.info(f"✅ Link analysis complete for URL: {url}", agent="URLInvestigation", node="conduct_link_analysis_wrapper", event_type="WRAPPER_COMPLETE", url=url)
        return {
            "link_analysis_final_reports": [result]  # This will be aggregated
        }
    
    except GraphRecursionError as e:
        # Handle recursion limit specifically - mark URL analysis as failed with context
        error_msg = f"URL analysis for {url} hit recursion limit - investigation too complex or stuck in loop"
        logger.warning(error_msg, agent="URLInvestigation", node="conduct_link_analysis_wrapper", event_type="RECURSION_LIMIT", url=url)
        logger.debug(f"Recursion error details: {e}", agent="URLInvestigation", node="conduct_link_analysis_wrapper")
        
        # Create a minimal URLAnalysisResult marking the investigation as failed
        failed_result = URLAnalysisResult(
            initial_url=url_task,
            full_investigation_log=[{
                "error": error_msg,
                "status": "recursion_limit_exceeded"
            }],
            analyst_findings=AnalystFindings(
                final_url=url_task.url,
                verdict="Inaccessible",
                confidence=0.0,
                summary=f"Investigation exceeded recursion limit of {URL_INVESTIGATION_INVESTIGATOR_CONFIG.get('recursion_limit', 20)} steps. The URL analysis could not be completed due to complexity or infinite loop. Manual investigation may be required.",
                detected_threats=[],
                mission_status="failed"
            )
        )
        
        return {
            "link_analysis_final_reports": [{"link_analysis_final_report": failed_result}],
            "errors": [error_msg]
        }
    
    except Exception as e:
        error_msg = f"Error in conduct_link_analysis for URL {url}: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": [error_msg]}


pipeline = StateGraph(URLInvestigationState, input_schema=URLInvestigationInputState, output_schema=URLInvestigationOutputState)

pipeline.add_node("filter_high_priority_urls", filter_high_priority_urls)
pipeline.add_node("conduct_link_analysis", conduct_link_analysis)
pipeline.add_node("save_url_analysis_state", save_url_analysis_state)
pipeline.add_edge(START, "filter_high_priority_urls")
pipeline.add_conditional_edges("filter_high_priority_urls", route_url_analysis, ["conduct_link_analysis", "save_url_analysis_state"])
pipeline.add_edge("conduct_link_analysis", "save_url_analysis_state")
pipeline.add_edge("save_url_analysis_state", END)

link_analysis_graph = pipeline.compile()
link_analysis_graph = link_analysis_graph.with_config(URL_INVESTIGATION_CONFIG)

if __name__ == "__main__":
    from .schemas import PrioritizedURL
    import asyncio
    from pdf_hunter.config.logging_config import setup_logging

    # Configure more detailed logging when running directly with DEBUG output
    setup_logging(debug_to_terminal=True)
    
    output_dir = "./output/test_url_analysis"
    logger.info(f"Setting up test with output directory: {output_dir}", agent="TestRunner", node="setup")

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

    asyncio.run(main())