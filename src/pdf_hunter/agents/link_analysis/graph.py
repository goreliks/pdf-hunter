import asyncio
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from langgraph.graph import StateGraph, START, END

from .schemas import LinkAnalysisState, LinkAnalysisInputState, LinkAnalysisOutputState, LinkInvestigatorState, LinkInvestigatorOutputState
from ..visual_analysis.schemas import PrioritizedURL
from .nodes import investigate_url, execute_browser_tools, analyze_url_content, should_continue, route_url_analysis, filter_high_priority_urls, save_url_analysis_state


link_investigator_state = StateGraph(LinkInvestigatorState, output_schema=LinkInvestigatorOutputState)

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
    # Run the investigator subgraph
    result = await link_investigator_graph.ainvoke(state)
    # The result should contain the fields from InvestigatorOutputState
    # We need to wrap it in a list so it gets aggregated via operator.add
    return {
        "link_analysis_final_reports": [result]  # This will be aggregated
    }


pipeline = StateGraph(LinkAnalysisState, input_schema=LinkAnalysisInputState, output_schema=LinkAnalysisOutputState)

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

    output_dir = "./outputs/test_link_analysis"

    test_state = {
        "visual_analysis_report": {
            "high_priority_urls": [
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
        print("\n🚀 Running the full Investigator -> Analyst pipeline...")
        
        try:
            final_state = await link_analysis_graph.ainvoke(test_state)
        finally:
            # Cleanup all MCP sessions when done
            from ...shared.utils.mcp_client import cleanup_mcp_session
            await cleanup_mcp_session()  # This will cleanup all sessions
        
        print("\n\n" + "="*50)
        print("📊✅ FINAL FORENSIC REPORT ✅📊")
        print("="*50)
        if final_state.get("link_analysis_final_reports"):
            for report in final_state["link_analysis_final_reports"]:
                print(report.model_dump_json(indent=2))
        else:
            print("No final report generated.")

    asyncio.run(main())