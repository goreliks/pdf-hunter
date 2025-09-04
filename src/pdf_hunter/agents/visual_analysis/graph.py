from langgraph.graph import StateGraph, START, END

from .schemas import VisualAnalysisState
from .nodes import visual_analysis_node, aggregation_node


visual_analysis_builder = StateGraph(VisualAnalysisState)

visual_analysis_builder.add_node("visual_analysis", visual_analysis_node)
visual_analysis_builder.add_node("aggregate_report", aggregation_node)

visual_analysis_builder.add_edge(START, "visual_analysis")

visual_analysis_builder.add_edge("visual_analysis", "aggregate_report")

visual_analysis_builder.add_edge("aggregate_report", END)

visual_analysis_graph = visual_analysis_builder.compile()


if __name__ == "__main__":
    import pprint
    from ..preprocessing.graph import preprocessing_graph

    file_path = "/Users/gorelik/Courses/pdf-hunter/tests/test_mal_one.pdf"
    output_directory = "output/visual_analysis_results"
    pages_to_process = 1

    print(f"--- Running Preprocessing on: {file_path} ---")
    preprocessing_input = {
        "file_path": file_path,
        "output_directory": output_directory,
        "number_of_pages_to_process": 1,
    }
    preprocessing_results = preprocessing_graph.invoke(preprocessing_input)
    
    if preprocessing_results.get("errors"):
        print("\n--- Preprocessing Failed ---")
        pprint.pprint(preprocessing_results["errors"])
    else:
        print("\n--- Preprocessing Succeeded. Preparing for Visual Analysis... ---")

        visual_analysis_input = {
            "extracted_images": preprocessing_results["extracted_images"],
            "extracted_urls": preprocessing_results["extracted_urls"],
            "number_of_pages_to_process": 1
        }

        print(f"\n--- Running Visual Analysis on {pages_to_process} page(s) ---")
        
        final_state = visual_analysis_graph.invoke(visual_analysis_input)

        print("\n--- Visual Analysis Complete. ---")

        if final_state.get("errors"):
            print("\n--- Visual Analysis Failed ---")
            pprint.pprint(final_state["errors"])
        else:
            visual_analysis_report = final_state.get("visual_analysis_report")
            if visual_analysis_report:
                print("\n--- Final Report ---")
                pprint.pprint(visual_analysis_report.model_dump())
            else:
                print("ERROR: Final report was not generated.")