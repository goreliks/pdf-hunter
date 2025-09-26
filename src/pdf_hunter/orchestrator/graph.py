from langgraph.graph import StateGraph, START, END

from .schemas import OrchestratorState, OrchestratorInputState
from ..agents.preprocessing.graph import preprocessing_graph
from ..agents.visual_analysis.graph import visual_analysis_graph
from ..agents.static_analysis.graph import static_analysis_graph
from ..agents.link_analysis.graph import link_analysis_graph
from .nodes import dispatch_link_analysis
from ..shared.utils.mcp_client import get_mcp_client


orchestrator_builder = StateGraph(OrchestratorState, input_schema=OrchestratorInputState)

orchestrator_builder.add_node("preprocessing", preprocessing_graph)
orchestrator_builder.add_node("static_analysis", static_analysis_graph)
orchestrator_builder.add_node("visual_analysis", visual_analysis_graph)
orchestrator_builder.add_node("link_analysis", link_analysis_graph)
orchestrator_builder.add_edge(START, "preprocessing")
orchestrator_builder.add_edge("preprocessing", "static_analysis")
orchestrator_builder.add_edge("preprocessing", "visual_analysis")
orchestrator_builder.add_edge("static_analysis", END)
orchestrator_builder.add_edge("link_analysis", END)
orchestrator_builder.add_conditional_edges("visual_analysis", dispatch_link_analysis, [END, "link_analysis"])

orchestrator_graph = orchestrator_builder.compile()


if __name__ == "__main__":
    import pprint
    import uuid
    import json
    import os
    import asyncio
    from datetime import datetime

    async def main():
        file_path = "/Users/gorelik/Courses/pdf-hunter/tests/test_mal_one.pdf"
        # file_path = "/Users/gorelik/Courses/pdf-hunter/tests/87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf"
        file_path = "/Users/gorelik/Courses/pdf-hunter/tests/hello_qr_and_link.pdf"
        output_directory = "output/orchestrator_results"
        # number_of_pages_to_process = 1
        number_of_pages_to_process = 4

        orchestrator_input = {
            "session_id": uuid.uuid4().hex[:8],
            "file_path": file_path,
            "output_directory": output_directory,
            "number_of_pages_to_process": number_of_pages_to_process,
            "additional_context": "None"
        }
        
        print("--- STARTING PDF HUNTER ORCHESTRATOR ---")
        
        try:
            # Invoke the entire orchestrator with the initial state using async
            final_state = await orchestrator_graph.ainvoke(orchestrator_input)
        finally:
            # Cleanup MCP session when done
            from ..shared.utils.mcp_client import cleanup_mcp_session
            await cleanup_mcp_session()

        print("\n\n--- PDF HUNTER ORCHESTRATOR COMPLETE ---")
        print("\n--- Final State of the Hunt: ---")
        
        def pretty_print_state(state):
            printable_state = {}
            for key, value in state.items():
                if hasattr(value, 'model_dump'):
                    printable_state[key] = value.model_dump()
                else:
                    printable_state[key] = value
            pprint.pprint(printable_state)

        pretty_print_state(final_state)

        visual_analysis_report = final_state.get("visual_analysis_report")
        if visual_analysis_report:
            print("\n--- Visual Analysis Verdict ---")
            print(f"Verdict: {visual_analysis_report.overall_verdict}")
            print(f"Confidence: {visual_analysis_report.overall_confidence}")

        # Save final state to JSON file
        if final_state:
            # Generate unique filename with timestamp
            unique_id = uuid.uuid4().hex[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_report_session_{unique_id}_{timestamp}.json"
            
            # Ensure output directory exists
            os.makedirs(output_directory, exist_ok=True)
            
            # Full path for the JSON file
            json_path = os.path.join(output_directory, filename)
            
            # Convert final state to JSON-serializable format
            def make_serializable(obj):
                if hasattr(obj, 'model_dump'):
                    return obj.model_dump()
                elif isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items() if k != 'mcp_playwright_session'}
                elif isinstance(obj, list):
                    return [make_serializable(item) for item in obj]
                else:
                    return obj
            
            serializable_state = make_serializable(final_state)
            
            # Save to JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_state, f, indent=2, ensure_ascii=False)
            
            print(f"\n--- Final state saved to: {json_path} ---")

    # Run the async main function
    asyncio.run(main())