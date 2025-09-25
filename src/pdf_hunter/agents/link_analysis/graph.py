import asyncio
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from langgraph.graph import StateGraph, START, END

from .schemas import LinkAnalysisState, LinkAnalysisInputState, LinkAnalysisOutputState
from ..visual_analysis.schemas import PrioritizedURL
from .nodes import llm_call, tool_node, analyst_node, should_continue


pipeline = StateGraph(LinkAnalysisState, input_schema=LinkAnalysisInputState, output_schema=LinkAnalysisOutputState)


# Add the nodes to the graph
pipeline.add_node("llm", llm_call)
pipeline.add_node("tools", tool_node)
pipeline.add_node("analyst", analyst_node)
# Define the edges, creating a linear flow
pipeline.add_edge(START, "llm")
pipeline.add_conditional_edges(
    "llm",
    should_continue,
    {"tool_node": "tools", "analyst_node": "analyst"}
)
pipeline.add_edge("tools", "llm")
pipeline.add_edge("analyst", END)
# Compile the graph and export it for external use
link_analysis_graph = pipeline.compile()



if __name__ == "__main__":
    from .schemas import PrioritizedURL
    import asyncio

    output_dir = "./mcp_outputs/final_pipeline_test"

    test_state = {
        "url_task": PrioritizedURL(
            url="https://www.fcbarcelona.com/en/",
            reason="URL for testing",
            priority=1,
            page_number=0
        ),
        "output_directory": output_dir
    }

    async def main():
        print("\n🚀 Running the full Investigator -> Analyst pipeline...")
        
        try:
            final_state = await link_analysis_graph.ainvoke(test_state)
        finally:
            # Cleanup MCP session when done
            from ...shared.utils.mcp_client import cleanup_mcp_session
            await cleanup_mcp_session()
        
        print("\n\n" + "="*50)
        print("📊✅ FINAL FORENSIC REPORT ✅📊")
        print("="*50)
        if final_state.get("link_analysis_final_report"):
            print(final_state["link_analysis_final_report"].model_dump_json(indent=2))
        else:
            print("No final report generated.")

                # Save final state to JSON file
        if final_state:
            # Generate unique filename with timestamp
            unique_id = uuid.uuid4().hex[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"link_analysis_report_session_{unique_id}_{timestamp}.json"
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Full path for the JSON file
            json_path = os.path.join(output_dir, filename)

            # Convert final state to JSON-serializable format
            def make_serializable(obj):
                if hasattr(obj, 'model_dump'):
                    return obj.model_dump()
                elif isinstance(obj, dict):
                    # Skip the MCP session key to avoid serialization issues
                    return {k: make_serializable(v) for k, v in obj.items() if k != "mcp_playwright_session"}
                elif isinstance(obj, list):
                    return [make_serializable(item) for item in obj]
                else:
                    return obj
            
            serializable_state = make_serializable(final_state)
            
            # Save to JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_state, f, indent=2, ensure_ascii=False)
            
            print(f"\n--- Final state saved to: {json_path} ---")

    asyncio.run(main())