from langgraph.graph import StateGraph, START, END

from .schemas import OrchestratorState, OrchestratorInputState, OrchestratorOutputState
from ..agents.pdf_extraction.graph import preprocessing_graph
from ..agents.image_analysis.graph import visual_analysis_graph
from ..agents.file_analysis.graph import static_analysis_graph
from ..agents.url_investigation.graph import link_analysis_graph
from ..agents.report_generator.graph import report_generator_graph
from ..shared.utils.serializer import serialize_state_safely
from ..config.logging_config import setup_logging
from pdf_hunter.config import ORCHESTRATOR_CONFIG

# Note: Logging will be configured in __main__ with session_id


orchestrator_builder = StateGraph(OrchestratorState, input_schema=OrchestratorInputState, output_schema=OrchestratorOutputState)

orchestrator_builder.add_node("PDF Extraction", preprocessing_graph)
orchestrator_builder.add_node("File Analysis", static_analysis_graph)
orchestrator_builder.add_node("Image Analysis", visual_analysis_graph)
orchestrator_builder.add_node("URL Investigation", link_analysis_graph)
orchestrator_builder.add_node("Report Generator", report_generator_graph)
orchestrator_builder.add_edge(START, "PDF Extraction")
orchestrator_builder.add_edge("PDF Extraction", "File Analysis")
orchestrator_builder.add_edge("PDF Extraction", "Image Analysis")
orchestrator_builder.add_edge("Image Analysis", "URL Investigation")
orchestrator_builder.add_edge(["File Analysis", "URL Investigation"], "Report Generator")
orchestrator_builder.add_edge("Report Generator", END)

orchestrator_graph = orchestrator_builder.compile()
orchestrator_graph = orchestrator_graph.with_config(ORCHESTRATOR_CONFIG)


if __name__ == "__main__":
    from .cli import main
    import asyncio
    
    asyncio.run(main())
