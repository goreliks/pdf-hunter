
from langgraph.constants import Send, END
from .schemas import OrchestratorState

def dispatch_link_analysis(state: OrchestratorState):
    """
    Dispatch the link analysis tasks based on high priority URLs from visual analysis.
    Uses Send to parallelize URL analysis across multiple instances.
    """
    if "visual_analysis_report" in state and state["visual_analysis_report"]:
        high_priority_urls = state["visual_analysis_report"].high_priority_urls
        if high_priority_urls:
            # Use Send to dispatch each URL to a separate link_analysis instance
            return [Send("link_analysis", {
                "url_task": url,
                "output_directory": state["output_directory"],
                "mcp_playwright_session": state.get("mcp_playwright_session")
            }) for url in high_priority_urls]
    
    # No high priority URLs found, go to END
    return END