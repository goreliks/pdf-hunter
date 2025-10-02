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
    from .cli import main
    import asyncio
    
    asyncio.run(main())
