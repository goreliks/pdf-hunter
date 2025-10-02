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
    from .cli import main
    import asyncio
    
    asyncio.run(main())
