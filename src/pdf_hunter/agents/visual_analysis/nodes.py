# src/pdf_hunter/agents/visual_analysis/nodes.py

import json
from typing import List

from langchain_core.messages import SystemMessage, HumanMessage

from .schemas import VisualAnalysisState, PageAnalysisResult, VisualAnalysisReport
from .prompts import VISUAL_ANALYSIS_SYSTEM_PROMPT, VISUAL_ANALYSIS_USER_PROMPT
from pdf_hunter.config import visual_analysis_llm

llm_with_structured_output = visual_analysis_llm.with_structured_output(PageAnalysisResult)


def _create_structured_forensic_briefing(page_result: PageAnalysisResult) -> str:
    """
    Creates a concise, yet detailed, briefing of the previous page's analysis
    to be used as context for the next page.
    """
    # Find the page number from the first detailed finding, if available.
    page_num = -1 
    if page_result.detailed_findings:
        page_num = page_result.detailed_findings[0].page_number

    briefing = [
        f"Context from the previous page (Page {page_num}):",
        f"- Page Appearance: {page_result.page_description}",
        f"- Overall Verdict: {page_result.visual_verdict} (Confidence: {page_result.confidence_score:.2f})",
        f"- Summary: {page_result.summary}"
    ]

    # Filter for only the most significant forensic findings to pass as context.
    high_significance_findings = [
        f for f in page_result.detailed_findings if f.significance == "high"
    ]

    if high_significance_findings:
        briefing.append("- Key Forensic Findings:")
        for finding in high_significance_findings:
            # Extract the most critical piece of technical data (like a URL) for the briefing.
            tech_data_summary = ""
            if finding.technical_data and 'url' in finding.technical_data:
                tech_data_summary = f" (URL: '{finding.technical_data['url']}')"
            
            briefing.append(f"  * {finding.assessment}{tech_data_summary}")
    
    return "\n".join(briefing)


def visual_analysis_node(state: VisualAnalysisState):
    """
    Performs a sequential, context-aware visual analysis of each page.
    """
    print("--- Visual Analysis Node: Starting Page-by-Page Analysis ---")
    
    try:
        num_pages_to_process = state.get("number_of_pages_to_process", 1)
        all_images = state['extracted_images']
        all_urls = state['extracted_urls']

        images_to_process = sorted(
            [img for img in all_images if img.page_number < num_pages_to_process],
            key=lambda img: img.page_number
        )
        
        if not images_to_process:
            print("[WARNING] No images found for the requested page range.")
            return {"page_analyses": []}

        page_analyses_results: List[PageAnalysisResult] = []
        previous_pages_context = "This is the first page. There is no prior context."

        for image in images_to_process:
            page_num = image.page_number
            print(f"[*] Analyzing Page {page_num}...")

            urls_for_this_page = [url for url in all_urls if url.page_number == page_num]
            element_map = {
                "page_number": page_num,
                "interactive_elements": [url.model_dump() for url in urls_for_this_page]
            }

            # Format the user prompt with the context and element map.
            formatted_user_prompt = VISUAL_ANALYSIS_USER_PROMPT.format(
                element_map_json=json.dumps(element_map, indent=2),
                previous_pages_context=previous_pages_context
            )
            
            # Construct the full, correct list of messages for the LLM call.
            messages = [
                SystemMessage(content=VISUAL_ANALYSIS_SYSTEM_PROMPT),
                HumanMessage(
                    content=[
                        {"type": "text", "text": formatted_user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image.base64_data}"}
                        }
                    ]
                )
            ]

            # Invoke the LLM with the correct message structure.
            page_result = llm_with_structured_output.invoke(messages)
            page_analyses_results.append(page_result)
            print(f"--- Page {page_num} Verdict: {page_result.visual_verdict} (Confidence: {page_result.confidence_score:.2f})")

            # Generate the rich, structured briefing for the next iteration.
            previous_pages_context = _create_structured_forensic_briefing(page_result)
        
        return {"page_analyses": page_analyses_results}

    except Exception as e:
        error_msg = f"An unexpected error occurred during visual analysis: {e}"
        print(f"[ERROR] {error_msg}")
        return {"errors": [error_msg]}


def aggregation_node(state: VisualAnalysisState):
    """
    Aggregates all page-level analyses into a final, conclusive report using
    robust, programmatic logic.
    """
    print("--- Visual Analysis Node: Aggregating Final Report ---")
    page_analyses = state.get("page_analyses", [])

    if not page_analyses:
        print("[INFO] No page analyses were performed. Generating empty report.")
        # Correctly instantiate the report with keywords to prevent TypeError.
        visual_analysis_report = VisualAnalysisReport(
            overall_verdict="Benign",
            overall_confidence=1.0,
            document_flow_summary="No pages were analyzed.",
            executive_summary="No pages were analyzed, so no threats were detected.",
            page_analyses=[],
            all_detailed_findings=[],
            all_deception_tactics=[],
            all_benign_signals=[],
            high_priority_urls=[]
        )
        return {"visual_analysis_report": visual_analysis_report}

    # Ensure pages are sorted for a logical flow summary.
    sorted_analyses = sorted(page_analyses, key=lambda p: p.detailed_findings[0].page_number if p.detailed_findings else 0)

    # --- Generate the Document Flow Summary ---
    flow_steps = []
    for analysis in sorted_analyses:
        page_num = analysis.detailed_findings[0].page_number if analysis.detailed_findings else 'N/A'
        flow_steps.append(f"Page {page_num}: {analysis.page_description}")
    document_flow_summary = "\n".join(flow_steps)
    
    # Determine Overall Verdict based on the most severe finding.
    verdict_severity = {"Benign": 0, "Suspicious": 1, "Highly Deceptive": 2}
    most_severe_verdict = max(page_analyses, key=lambda p: verdict_severity[p.visual_verdict]).visual_verdict

    # Correctly calculate Overall Confidence based on the "weakest link" principle.
    pages_with_highest_threat = [p for p in page_analyses if p.visual_verdict == most_severe_verdict]
    overall_confidence = max(p.confidence_score for p in pages_with_highest_threat)

    # Aggregate all findings into flat lists for the final report.
    all_detailed_findings = [finding for p in page_analyses for finding in p.detailed_findings]
    all_tactics = [tactic for p in page_analyses for tactic in p.deception_tactics]
    all_signals = [signal for p in page_analyses for signal in p.benign_signals]
    all_priority_urls = [url for p in page_analyses for url in p.prioritized_urls]
    high_priority_urls = [url for url in all_priority_urls if url.priority <= 2]

    # Generate the Executive Summary.
    summary = (
        f"Visual analysis of {len(page_analyses)} page(s) resulted in an overall verdict of '{most_severe_verdict}'.\n"
        f"The analysis produced {len(all_detailed_findings)} specific forensic findings, "
        f"which were summarized into {len(all_tactics)} deception tactics and {len(all_signals)} benign signals.\n"
        f"Flagged {len(high_priority_urls)} high-priority URLs for further investigation."
    )

    # Construct the final report object.
    visual_analysis_report = VisualAnalysisReport(
        overall_verdict=most_severe_verdict,
        overall_confidence=overall_confidence,
        document_flow_summary=document_flow_summary,
        executive_summary=summary,
        page_analyses=page_analyses,
        all_detailed_findings=all_detailed_findings,
        all_deception_tactics=all_tactics,
        all_benign_signals=all_signals,
        high_priority_urls=high_priority_urls
    )
    
    print(f"--- Final Verdict: {visual_analysis_report.overall_verdict} (Confidence: {visual_analysis_report.overall_confidence:.2f}) ---")
    return {"visual_analysis_report": visual_analysis_report}
