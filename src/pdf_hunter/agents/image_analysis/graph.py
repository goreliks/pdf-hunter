from langgraph.graph import StateGraph, START, END

from .schemas import ImageAnalysisState
from .nodes import analyze_pdf_images, compile_image_findings
from pdf_hunter.shared.utils.logging_config import configure_logging
from pdf_hunter.config import IMAGE_ANALYSIS_CONFIG

# Configure logging for this module
configure_logging()


visual_analysis_builder = StateGraph(ImageAnalysisState)

visual_analysis_builder.add_node("analyze_pdf_images", analyze_pdf_images)
visual_analysis_builder.add_node("compile_image_findings", compile_image_findings)

visual_analysis_builder.add_edge(START, "analyze_pdf_images")

visual_analysis_builder.add_edge("analyze_pdf_images", "compile_image_findings")

visual_analysis_builder.add_edge("compile_image_findings", END)

visual_analysis_graph = visual_analysis_builder.compile()
visual_analysis_graph = visual_analysis_graph.with_config(IMAGE_ANALYSIS_CONFIG)


if __name__ == "__main__":
    import pprint
    import logging
    import os
    from ..pdf_extraction.graph import preprocessing_graph
    from pdf_hunter.shared.utils.logging_config import configure_logging, get_logger

    # Configure logging with more verbose output for standalone execution
    configure_logging(level=logging.INFO, log_to_file=True)
    logger = get_logger(__name__)

    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))
    file_path = os.path.join(project_root, "tests", "assets", "pdfs", "test_mal_one.pdf")

    output_directory = "output/image_analysis_results"
    pages_to_process = 1

    logger.info(f"Running Preprocessing on: {file_path}")
    preprocessing_input = {
        "file_path": file_path,
        "output_directory": output_directory,
        "number_of_pages_to_process": 1,
    }
    preprocessing_results = preprocessing_graph.invoke(preprocessing_input)
    
    if preprocessing_results.get("errors"):
        logger.error("Preprocessing Failed")
        for error in preprocessing_results["errors"]:
            logger.error(f"Error: {error}")
    else:
        logger.info("Preprocessing Succeeded. Preparing for Visual Analysis...")

        visual_analysis_input = {
            "extracted_images": preprocessing_results["extracted_images"],
            "extracted_urls": preprocessing_results["extracted_urls"],
            "number_of_pages_to_process": 1
        }

        logger.info(f"Running Visual Analysis on {pages_to_process} page(s)")
        
        final_state = visual_analysis_graph.invoke(visual_analysis_input)

        logger.info("Visual Analysis Complete")

        if final_state.get("errors"):
            logger.error("Visual Analysis Failed")
            for error in final_state["errors"]:
                logger.error(f"Error: {error}")
        else:
            visual_analysis_report = final_state.get("visual_analysis_report")
            if visual_analysis_report:
                logger.info("Final Report Generated")
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Report details: {visual_analysis_report.model_dump()}")
            else:
                logger.error("Final report was not generated")