from langgraph.graph import StateGraph, START, END

from .schemas import PreprocessingState, PreprocessingInputState, PreprocessingOutputState
from .nodes import initialization_node, image_extraction_node, qr_extraction_node, url_extraction_node


preprocessing_builder = StateGraph(PreprocessingState, input_schema=PreprocessingInputState, output_schema=PreprocessingOutputState)

preprocessing_builder.add_node("initialize", initialization_node)
preprocessing_builder.add_node("extract_images", image_extraction_node)
preprocessing_builder.add_node("extract_urls", url_extraction_node)
preprocessing_builder.add_node("extract_qr_codes", qr_extraction_node)

preprocessing_builder.add_edge(START, "initialize")

preprocessing_builder.add_edge("initialize", "extract_images")
preprocessing_builder.add_edge("initialize", "extract_urls")
preprocessing_builder.add_edge("initialize", "extract_qr_codes")

preprocessing_builder.add_edge("extract_images", END)
preprocessing_builder.add_edge("extract_urls", END)
preprocessing_builder.add_edge("extract_qr_codes", END)

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

    print(f"--- Running Preprocessing on: {file_path} ---")

    final_state = preprocessing_graph.invoke(initial_state)

    print("\n--- Preprocessing Complete. Final State: ---")
    
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