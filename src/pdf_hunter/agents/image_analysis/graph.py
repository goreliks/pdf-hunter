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
    from .cli import main
    import asyncio
    
    asyncio.run(main())
