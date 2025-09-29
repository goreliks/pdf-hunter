from langgraph.graph import StateGraph, START, END

from .schemas import PDFExtractionState, PDFExtractionInputState, PDFExtractionOutputState
from .nodes import setup_session, extract_pdf_images, scan_qr_codes, find_embedded_urls
from pdf_hunter.shared.utils.logging_config import configure_logging, get_logger

# Configure logging for this module
configure_logging()
logger = get_logger(__name__)


preprocessing_builder = StateGraph(PDFExtractionState, input_schema=PDFExtractionInputState, output_schema=PDFExtractionOutputState)

preprocessing_builder.add_node("setup_session", setup_session)
preprocessing_builder.add_node("extract_pdf_images", extract_pdf_images)
preprocessing_builder.add_node("find_embedded_urls", find_embedded_urls)
preprocessing_builder.add_node("scan_qr_codes", scan_qr_codes)

preprocessing_builder.add_edge(START, "setup_session")

preprocessing_builder.add_edge("setup_session", "extract_pdf_images")
preprocessing_builder.add_edge("setup_session", "find_embedded_urls")
preprocessing_builder.add_edge("setup_session", "scan_qr_codes")

preprocessing_builder.add_edge("extract_pdf_images", END)
preprocessing_builder.add_edge("find_embedded_urls", END)
preprocessing_builder.add_edge("scan_qr_codes", END)

preprocessing_graph = preprocessing_builder.compile()


if __name__ == "__main__":
    import pprint
    import logging
    import os

    # Configure more detailed logging for standalone execution
    configure_logging(level=logging.INFO, log_to_file=True)
    logger = get_logger(__name__)

    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))
    file_path = os.path.join(project_root, "tests", "assets", "pdfs", "hello_qr_and_link.pdf")
    
    output_directory = "output/pdf_extraction_results"

    initial_state = {
        "file_path": file_path,
        "output_directory": output_directory,
        "number_of_pages_to_process": 1,  # We want to process only the first page (page 0)
    }

    logger.info(f"Running PDF Extraction on: {file_path}")

    final_state = preprocessing_graph.invoke(initial_state)

    logger.info("PDF Extraction Complete")
    
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Final state: {pprint.pformat(final_state)}")

    # Verification
    if final_state.get("errors"):
        logger.warning(f"Completed with {len(final_state['errors'])} error(s)")
        for error in final_state["errors"]:
            logger.error(f"Error: {error}")
    else:
        logger.info("Completed successfully")
        logger.info(f"PDF Hash Calculated: {'Yes' if final_state.get('pdf_hash') else 'No'}")
        logger.info(f"Images Extracted: {len(final_state.get('extracted_images', []))}")
        logger.info(f"URL Findings: {len(final_state.get('extracted_urls', []))}")
        
        if final_state.get('extracted_urls') and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Example URL Finding: {pprint.pformat(final_state['extracted_urls'][0])}")