import asyncio
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from langgraph.graph import StateGraph, START, END

from .nodes import investigator_node, analyst_node
from .schemas import LinkAnalysisState, LinkAnalysisInputState, LinkAnalysisOutputState
from ..visual_analysis.schemas import PrioritizedURL


pipeline = StateGraph(LinkAnalysisState, input_schema=LinkAnalysisInputState, output_schema=LinkAnalysisOutputState)

# Add the nodes to the graph
pipeline.add_node("investigator", investigator_node)
pipeline.add_node("analyst", analyst_node)

# Define the edges, creating a linear flow
pipeline.add_edge(START, "investigator")
pipeline.add_edge("investigator", "analyst")
pipeline.add_edge("analyst", END)

# Compile the graph and export it for external use
link_analysis_graph = pipeline.compile()


if __name__ == "__main__":
    import asyncio
    import os
    from pathlib import Path
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from ..visual_analysis.schemas import PrioritizedURL

    async def main():
        output_dir = "./mcp_outputs/final_pipeline_test"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        url_to_investigate = PrioritizedURL(
            url="http://hrms.wb.gov.in.hrmspanel.online/",
            priority=1,
            reason="Flagged as a potential government portal impersonation.",
            page_number=1
        )

        client = MultiServerMCPClient({
            "playwright": {
                "command": "npx",
                "args": ["@playwright/mcp@latest", "--headless", f"--output-dir={output_dir}", "--save-trace", "--isolated"],
                "transport": "stdio"
            }
        })
        
        async with client.session("playwright") as session:
            initial_input = {
                "url_task": url_to_investigate,
                "output_directory": output_dir,
                "mcp_playwright_session": session
            }
            
            print("\n🚀 Running the full Investigator -> Analyst pipeline...")
            final_state = await link_analysis_graph.ainvoke(initial_input)
            
            print("\n\n" + "="*50)
            print("📊✅ FINAL FORENSIC REPORT ✅📊")
            print("="*50)
            if final_state.get("link_analysis_final_report"):
                print(final_state["link_analysis_final_report"].model_dump_json(indent=2))
            else:
                print("Pipeline did not produce a final report.")
            
        print(f"\n🎉 Full pipeline complete! Check {os.path.abspath(output_dir)} for all artifacts.")

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
                    return {k: make_serializable(v) for k, v in obj.items()}
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