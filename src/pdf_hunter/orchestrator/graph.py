from langgraph.graph import StateGraph, START, END

from .schemas import OrchestratorState, OrchestratorInputState, OrchestratorOutputState
from ..agents.preprocessing.graph import preprocessing_graph
from ..agents.visual_analysis.graph import visual_analysis_graph
from ..agents.static_analysis.graph import static_analysis_graph
from ..agents.link_analysis.graph import link_analysis_graph
from ..agents.finalizer.graph import finalizer_graph
from ..shared.utils.serializer import serialize_state_safely


orchestrator_builder = StateGraph(OrchestratorState, input_schema=OrchestratorInputState, output_schema=OrchestratorOutputState)

orchestrator_builder.add_node("pdf_extraction", preprocessing_graph)
orchestrator_builder.add_node("file_analysis", static_analysis_graph)
orchestrator_builder.add_node("image_analysis", visual_analysis_graph)
orchestrator_builder.add_node("url_investigation", link_analysis_graph)
orchestrator_builder.add_node("report_generator", finalizer_graph)
orchestrator_builder.add_edge(START, "pdf_extraction")
orchestrator_builder.add_edge("pdf_extraction", "file_analysis")
orchestrator_builder.add_edge("pdf_extraction", "image_analysis")
orchestrator_builder.add_edge("image_analysis", "url_investigation")
orchestrator_builder.add_edge(["file_analysis", "url_investigation"], "report_generator")
orchestrator_builder.add_edge("report_generator", END)

orchestrator_graph = orchestrator_builder.compile()


if __name__ == "__main__":
    import pprint
    import json
    import os
    import asyncio

    async def main():
        file_path = "/Users/agorelik/src/pdf-hunter/tests/test_mal_one.pdf"
        # file_path = "/Users/agorelik/src/pdf-hunter/tests/87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf"
        file_path = "/Users/agorelik/src/pdf-hunter/tests/hello_qr_and_link.pdf"
        output_directory = "output/orchestrator_results"
        # number_of_pages_to_process = 1
        number_of_pages_to_process = 4

        orchestrator_input = {
            "file_path": file_path,
            "output_directory": "output",  # Base directory, session-specific will be created
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

        image_analysis_report = final_state.get("image_analysis_report")
        if image_analysis_report:
            print("\n--- Image Analysis Verdict ---")
            print(f"Verdict: {image_analysis_report.overall_verdict}")
            print(f"Confidence: {image_analysis_report.overall_confidence}")

        # Save final state to JSON file
        if final_state:
            # Use session-specific directory from final state
            session_output_directory = final_state.get('output_directory')
            session_id = final_state.get('session_id', 'unknown')
            filename = f"analysis_report_session_{session_id}.json"

            # Ensure output directory exists
            if session_output_directory:
                os.makedirs(session_output_directory, exist_ok=True)

                # Full path for the JSON file
                json_path = os.path.join(session_output_directory, filename)

                # Convert final state to JSON-serializable format
                serializable_state = serialize_state_safely(final_state)

                # Save to JSON file
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(serializable_state, f, indent=2, ensure_ascii=False)

                print(f"\n--- Final state saved to: {json_path} ---")
            else:
                print("\n--- Warning: No output directory found in final state ---")

    # Run the async main function
    asyncio.run(main())