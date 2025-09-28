from langgraph.graph import StateGraph, START, END

from .schemas import PreprocessingState, PreprocessingInputState, PreprocessingOutputState
from .nodes import setup_session, extract_pdf_images, scan_qr_codes, find_embedded_urls


preprocessing_builder = StateGraph(PreprocessingState, input_schema=PreprocessingInputState, output_schema=PreprocessingOutputState)

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

    file_path = "/Users/gorelik/Courses/pdf-hunter/tests/hello_qr_and_link.pdf"
    output_directory = "output/preprocessing_results"

    initial_state = {
        "file_path": file_path,
        "output_directory": output_directory,
        "number_of_pages_to_process": 1,  # We want to process only the first page (page 0)
    }

    print(f"--- Running PDF Extraction on: {file_path} ---")

    final_state = preprocessing_graph.invoke(initial_state)

    print("\n--- PDF Extraction Complete. Final State: ---")
    
    pprint.pprint(final_state)

    print("\n--- Verification ---")
    if final_state.get("errors"):
        print(f"Completed with {len(final_state['errors'])} error(s).")
    else:
        print("Completed successfully.")
        print(f"PDF Hash Calculated: {'Yes' if final_state.get('pdf_hash') else 'No'}")
        print(f"Images Extracted: {len(final_state.get('extracted_images', []))}")
        print(f"URL Findings: {len(final_state.get('extracted_urls', []))}")
        if final_state.get('extracted_urls'):
            print("Example URL Finding:")
            pprint.pprint(final_state['extracted_urls'][0])

    print(f"state: {final_state}")