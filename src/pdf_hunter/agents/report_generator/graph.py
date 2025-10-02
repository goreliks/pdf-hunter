from langgraph.graph import StateGraph, START, END
from .nodes import generate_final_report, determine_threat_verdict, save_analysis_results
from pdf_hunter.config import REPORT_GENERATION_CONFIG

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
report_generator_graph = report_generator_graph.with_config(REPORT_GENERATION_CONFIG)

if __name__ == "__main__":
    from .cli import run_and_verify
    import asyncio
    
    asyncio.run(run_and_verify())
