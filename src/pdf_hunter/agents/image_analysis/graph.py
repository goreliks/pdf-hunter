from langgraph.graph import StateGraph, START, END

from .schemas import ImageAnalysisState
from .nodes import analyze_pdf_images, compile_image_findings
from pdf_hunter.config import IMAGE_ANALYSIS_CONFIG


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
    import os
    import asyncio
    from loguru import logger
    from ..pdf_extraction.graph import preprocessing_graph
    from pdf_hunter.config.logging_config import setup_logging

    # Configure logging for standalone execution with DEBUG output
    setup_logging(debug_to_terminal=True)

    async def run_analysis():
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))
        file_path = os.path.join(project_root, "tests", "assets", "pdfs", "test_mal_one.pdf")

        output_directory = "output/image_analysis_results"
        pages_to_process = 1

        logger.info(f"Running Preprocessing on: {file_path}", agent="image_analysis_test")
        preprocessing_input = {
            "file_path": file_path,
            "output_directory": output_directory,
            "number_of_pages_to_process": 1,
        }
        # Use ainvoke for preprocessing
        preprocessing_results = await preprocessing_graph.ainvoke(preprocessing_input)
        
        if preprocessing_results.get("errors"):
            logger.error("Preprocessing Failed", agent="image_analysis_test")
            for error in preprocessing_results["errors"]:
                logger.error(f"Error: {error}", agent="image_analysis_test")
            return None
        else:
            logger.info("Preprocessing Succeeded. Preparing for Visual Analysis...", agent="image_analysis_test")

            visual_analysis_input = {
                "extracted_images": preprocessing_results["extracted_images"],
                "extracted_urls": preprocessing_results["extracted_urls"],
                "number_of_pages_to_process": 1,
                "session_id": preprocessing_results.get("session_id"),
                "output_directory": preprocessing_results.get("output_directory"),
            }

            logger.info(f"Running Visual Analysis on {pages_to_process} page(s)", agent="image_analysis_test")
            
            # Use ainvoke instead of invoke
            final_state = await visual_analysis_graph.ainvoke(visual_analysis_input)

            if final_state.get("errors"):
                logger.error(f"Completed with {len(final_state['errors'])} error(s)", agent="image_analysis_test")
                for error in final_state["errors"]:
                    logger.error(f"Error: {error}", agent="image_analysis_test")
            else:
                logger.success("✅ Visual Analysis completed successfully", agent="image_analysis_test")
            
            return final_state
    
    # Run the async function with asyncio.run()
    final_state = asyncio.run(run_analysis())

