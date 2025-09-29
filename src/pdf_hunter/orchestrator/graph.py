from langgraph.graph import StateGraph, START, END

from .schemas import OrchestratorState, OrchestratorInputState, OrchestratorOutputState
from ..agents.pdf_extraction.graph import preprocessing_graph
from ..agents.image_analysis.graph import visual_analysis_graph
from ..agents.file_analysis.graph import static_analysis_graph
from ..agents.url_investigation.graph import link_analysis_graph
from ..agents.report_generator.graph import report_generator_graph
from ..shared.utils.serializer import serialize_state_safely
from ..shared.utils.logging_config import configure_logging, get_logger

# Configure logging for the orchestrator
configure_logging()
logger = get_logger(__name__)


orchestrator_builder = StateGraph(OrchestratorState, input_schema=OrchestratorInputState, output_schema=OrchestratorOutputState)

orchestrator_builder.add_node("pdf_extraction", preprocessing_graph)
orchestrator_builder.add_node("file_analysis", static_analysis_graph)
orchestrator_builder.add_node("image_analysis", visual_analysis_graph)
orchestrator_builder.add_node("url_investigation", link_analysis_graph)
orchestrator_builder.add_node("report_generator", report_generator_graph)
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
    import logging

    # Configure more detailed logging for the orchestrator when run directly
    configure_logging(level=logging.INFO, log_to_file=True)
    logger = get_logger(__name__)

    async def main():
        file_to_analyze = "test_mal_one.pdf"
        # file_to_analyze = "87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf"
        # file_to_analyze = "hello_qr_and_link.pdf"
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, "../../.."))
        file_path = os.path.join(project_root, "tests", "assets", "pdfs", "test_mal_one.pdf")
        
        # number_of_pages_to_process = 1
        number_of_pages_to_process = 4

        orchestrator_input = {
            "file_path": file_path,
            "output_directory": "output",  # Base directory, session-specific will be created
            "number_of_pages_to_process": number_of_pages_to_process,
            "additional_context": None
        }
        
        logger.info("STARTING PDF HUNTER ORCHESTRATOR")
        
        try:
            # Invoke the entire orchestrator with the initial state using async
            logger.info("Invoking orchestrator graph")
            final_state = await orchestrator_graph.ainvoke(orchestrator_input)
        finally:
            # Cleanup MCP session when done
            from ..shared.utils.mcp_client import cleanup_mcp_session
            logger.debug("Cleaning up MCP session")
            await cleanup_mcp_session()

        logger.info("PDF HUNTER ORCHESTRATOR COMPLETE")
        logger.debug("Final State of the Hunt:")
        
        if logger.isEnabledFor(logging.DEBUG):
            def pretty_print_state(state):
                printable_state = {}
                for key, value in state.items():
                    if hasattr(value, 'model_dump'):
                        printable_state[key] = value.model_dump()
                    else:
                        printable_state[key] = value
                return printable_state
            
            logger.debug(f"State details: {pretty_print_state(final_state)}")

        image_analysis_report = final_state.get("image_analysis_report")
        if image_analysis_report:
            logger.info(f"Image Analysis Verdict: {image_analysis_report.overall_verdict}")
            logger.info(f"Confidence: {image_analysis_report.overall_confidence}")

        # Save final state to JSON file
        if final_state:
            # Use session-specific directory from final state
            session_output_directory = final_state.get('output_directory')
            session_id = final_state.get('session_id', 'unknown')
            filename = f"analysis_report_session_{session_id}.json"

            # Ensure output directory exists
            if session_output_directory:
                logger.debug(f"Creating output directory: {session_output_directory}")
                os.makedirs(session_output_directory, exist_ok=True)

                # Full path for the JSON file
                json_path = os.path.join(session_output_directory, filename)
                logger.debug(f"Preparing to save state to {json_path}")

                # Convert final state to JSON-serializable format
                logger.debug("Serializing state")
                serializable_state = serialize_state_safely(final_state)

                # Save to JSON file
                logger.debug("Writing state to file")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(serializable_state, f, indent=2, ensure_ascii=False)

                logger.info(f"Final state saved to: {json_path}")
            else:
                logger.warning("No output directory found in final state")

    # Run the async main function
    asyncio.run(main())