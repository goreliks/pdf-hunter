from langgraph.graph import StateGraph, START, END

from .schemas import PDFExtractionState, PDFExtractionInputState, PDFExtractionOutputState
from .nodes import setup_session, extract_pdf_images, scan_qr_codes, find_embedded_urls, finalize_extraction
from pdf_hunter.config import PDF_EXTRACTION_CONFIG


preprocessing_builder = StateGraph(PDFExtractionState, input_schema=PDFExtractionInputState, output_schema=PDFExtractionOutputState)

preprocessing_builder.add_node("setup_session", setup_session)
preprocessing_builder.add_node("extract_pdf_images", extract_pdf_images)
preprocessing_builder.add_node("find_embedded_urls", find_embedded_urls)
preprocessing_builder.add_node("scan_qr_codes", scan_qr_codes)
preprocessing_builder.add_node("finalize_extraction", finalize_extraction)

preprocessing_builder.add_edge(START, "setup_session")

preprocessing_builder.add_edge("setup_session", "extract_pdf_images")
preprocessing_builder.add_edge("setup_session", "find_embedded_urls")
preprocessing_builder.add_edge("setup_session", "scan_qr_codes")

# All parallel tasks converge to finalize_extraction before END
preprocessing_builder.add_edge("extract_pdf_images", "finalize_extraction")
preprocessing_builder.add_edge("find_embedded_urls", "finalize_extraction")
preprocessing_builder.add_edge("scan_qr_codes", "finalize_extraction")

preprocessing_builder.add_edge("finalize_extraction", END)

preprocessing_graph = preprocessing_builder.compile()
preprocessing_graph = preprocessing_graph.with_config(PDF_EXTRACTION_CONFIG)


if __name__ == "__main__":
    import pprint
    import os
    import asyncio
    from loguru import logger
    from pdf_hunter.config.logging_config import setup_logging

    # Configure logging for standalone execution with DEBUG output
    setup_logging(debug_to_terminal=True)

    async def run_extraction():
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))
        file_path = os.path.join(project_root, "tests", "assets", "pdfs", "hello_qr_and_link.pdf")
        
        output_directory = "output/pdf_extraction_results"

        initial_state = {
            "file_path": file_path,
            "output_directory": output_directory,
            "number_of_pages_to_process": 1,  # We want to process only the first page (page 0)
        }

        logger.info(f"Running PDF Extraction on: {file_path}",
                    agent="pdf_extraction_test",
                    test_file=file_path)

        final_state = await preprocessing_graph.ainvoke(initial_state)

        session_id = final_state.get('session_id', 'unknown')
        logger.info("PDF Extraction Complete",
                    agent="pdf_extraction_test",
                    session_id=session_id)

        # Verification
        if final_state.get("errors"):
            logger.warning(f"Completed with {len(final_state['errors'])} error(s)",
                          agent="pdf_extraction_test",
                          session_id=session_id,
                          error_count=len(final_state["errors"]))
            for error in final_state["errors"]:
                logger.error(f"Error: {error}",
                           agent="pdf_extraction_test",
                           session_id=session_id)
        else:
            logger.success("✅ PDF Extraction completed successfully",
                          agent="pdf_extraction_test",
                          session_id=session_id,
                          images_extracted=len(final_state.get('extracted_images', [])),
                          urls_found=len(final_state.get('extracted_urls', [])))


    # Run the async function
    asyncio.run(run_extraction())