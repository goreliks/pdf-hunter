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
    import pprint
    import json
    import os
    import asyncio
    from loguru import logger

    # Configure logging with DEBUG output to terminal for development/testing
    # Note: Session-specific log will be added after PDF extraction completes
    setup_logging(debug_to_terminal=True)

    async def main():
        # file_to_analyze = "test_mal_one.pdf"
        # file_to_analyze = "87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf"
        file_to_analyze = "hello_qr_and_link.pdf"
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, "../../.."))
        file_path = os.path.join(project_root, "tests", "assets", "pdfs", file_to_analyze)
        
        # number_of_pages_to_process = 1
        number_of_pages_to_process = 4

        orchestrator_input = {
            "file_path": file_path,
            "output_directory": "output",  # Base directory, session-specific will be created
            "number_of_pages_to_process": number_of_pages_to_process,
            "additional_context": None
        }
        
        logger.info("🚀 Starting PDF Hunter orchestrator",
                    agent="Orchestrator",
                    file_path=file_path,
                    pages_to_process=number_of_pages_to_process)
        
        session_id = None
        output_directory = None
        
        try:
            # Stream the orchestrator to reconfigure logging after PDF extraction
            async for event in orchestrator_graph.astream(orchestrator_input, stream_mode="values"):
                # After PDF extraction completes, we have session_id and output_directory
                if event.get('session_id') and event.get('output_directory') and not session_id:
                    session_id = event['session_id']
                    output_directory = event['output_directory']
                    
                    # Reconfigure logging to add session-specific log file
                    logger.info("📝 Adding session-specific log file",
                               agent="Orchestrator",
                               session_id=session_id,
                               output_directory=output_directory)
                    setup_logging(session_id=session_id, 
                                 output_directory=output_directory,
                                 debug_to_terminal=True)
                
                final_state = event
                
        finally:
            # Cleanup MCP session when done
            from ..shared.utils.mcp_client import cleanup_mcp_session
            logger.debug("Cleaning up MCP session", agent="Orchestrator")
            await cleanup_mcp_session()

        session_id = final_state.get('session_id', 'unknown')
        logger.info("✅ PDF Hunter orchestrator complete",
                    agent="Orchestrator",
                    session_id=session_id)

        image_analysis_report = final_state.get("image_analysis_report")
        if image_analysis_report:
            logger.info(f"Image Analysis Verdict: {image_analysis_report.overall_verdict}",
                       agent="Orchestrator",
                       session_id=session_id,
                       verdict=image_analysis_report.overall_verdict,
                       confidence=image_analysis_report.overall_confidence)

        # Save final state to JSON file
        if final_state:
            # Use session-specific directory from final state
            session_output_directory = final_state.get('output_directory')
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

                logger.info(f"Final state saved to: {json_path}",
                           agent="Orchestrator",
                           session_id=session_id,
                           output_file=json_path)
            else:
                logger.warning("No output directory found in final state",
                             agent="Orchestrator",
                             session_id=session_id)

    # Run the async main function
    asyncio.run(main())