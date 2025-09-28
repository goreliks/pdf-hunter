from langgraph.graph import StateGraph, START, END
from .nodes import generate_final_report, determine_threat_verdict, save_analysis_results

# The finalizer's state is the same as the Orchestrator's, so no need to redefine
from ...orchestrator.schemas import OrchestratorState

# We can use a simple builder here as the state is passed directly from the orchestrator
report_generator_builder = StateGraph(OrchestratorState)

report_generator_builder.add_node("generate_final_report", generate_final_report)
report_generator_builder.add_node("determine_threat_verdict", determine_threat_verdict)
report_generator_builder.add_node("save_analysis_results", save_analysis_results)

report_generator_builder.add_edge(START, "determine_threat_verdict")
report_generator_builder.add_edge("determine_threat_verdict", "generate_final_report")
report_generator_builder.add_edge("generate_final_report", "save_analysis_results")
report_generator_builder.add_edge("save_analysis_results", END)

report_generator_graph = report_generator_builder.compile()

if __name__ == "__main__":
    test_json_path = "/Users/gorelik/Courses/pdf-hunter/output/orchestrator_results/analysis_report_session_7b59304e_20250926_103934.json"
    import json
    import pprint
    with open(test_json_path, 'r', encoding='utf-8') as f:
        test_state = json.load(f)
    print(f"--- Running Report Generator on test state from: {test_json_path} ---")
    final_state = report_generator_graph.invoke(test_state)
    print("\n--- Report Generator Complete. Final State: ---")
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
