from langgraph.graph import StateGraph, START, END
from .nodes import reporter_node, final_verdict_node, write_the_results_to_file

# The finalizer's state is the same as the Orchestrator's, so no need to redefine
from ...orchestrator.schemas import OrchestratorState

# We can use a simple builder here as the state is passed directly from the orchestrator
finalizer_builder = StateGraph(OrchestratorState)

finalizer_builder.add_node("reporter", reporter_node)
finalizer_builder.add_node("final_verdict", final_verdict_node)
finalizer_builder.add_node("write_results", write_the_results_to_file)

finalizer_builder.add_edge(START, "final_verdict")
finalizer_builder.add_edge("final_verdict", "reporter")
finalizer_builder.add_edge("reporter", "write_results")
finalizer_builder.add_edge("write_results", END)

finalizer_graph = finalizer_builder.compile()

if __name__ == "__main__":
    test_json_path = "/Users/gorelik/Courses/pdf-hunter/output/orchestrator_results/analysis_report_session_7b59304e_20250926_103934.json"
    import json
    import pprint
    with open(test_json_path, 'r', encoding='utf-8') as f:
        test_state = json.load(f)
    print(f"--- Running Finalizer on test state from: {test_json_path} ---")
    final_state = finalizer_graph.invoke(test_state)
    print("\n--- Finalizer Complete. Final State: ---")
    pprint.pprint(final_state)
    print("\n--- Verification ---")
    if final_state.get("errors"):
        print(f"Completed with {len(final_state['errors'])} error(s).")
    else:
        print("Completed successfully.")
        print(f"Final Report Generated: {'Yes' if final_state.get('final_report') else 'No'}")
        print(f"Final Verdict Generated: {'Yes' if final_state.get('final_verdict') else 'No'}")
        if final_state.get('final_verdict'):
            print("Final Verdict Details:")
            pprint.pprint(final_state['final_verdict'].model_dump_json(indent=2))
