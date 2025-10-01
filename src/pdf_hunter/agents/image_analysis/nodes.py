# src/pdf_hunter/agents/visual_analysis/nodes.py

import json
import os
import asyncio
from typing import List

from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

from .schemas import ImageAnalysisState, PageAnalysisResult, ImageAnalysisReport
from pdf_hunter.shared.utils.serializer import dump_state_to_file
from .prompts import IMAGE_ANALYSIS_SYSTEM_PROMPT, IMAGE_ANALYSIS_USER_PROMPT
from pdf_hunter.config import image_analysis_llm
from pdf_hunter.config.execution_config import LLM_TIMEOUT_VISION

llm_with_structured_output = image_analysis_llm.with_structured_output(PageAnalysisResult)


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
            if finding.technical_data:
                try:
                    tech_data = json.loads(finding.technical_data)
                    if 'url' in tech_data:
                        tech_data_summary = f" (URL: '{tech_data['url']}')"
                except (json.JSONDecodeError, TypeError):
                    # If technical_data is not valid JSON, skip the URL extraction
                    pass
            
            briefing.append(f"  * {finding.assessment}{tech_data_summary}")
    
    return "\n".join(briefing)


async def analyze_pdf_images(state: ImageAnalysisState):
    """
    Visual Deception Analyst (VDA) analyzes pages with a focus on visually
    deceptive content, phishing, and presentation concerns.
    """
    try:
        # Validate required inputs
        all_images = state.get('extracted_images', [])
        all_urls = state.get('extracted_urls', [])
        num_pages_to_process = state.get("number_of_pages_to_process", 1)
        session_id = state.get('session_id')
        
        # Agent start event
        logger.info(
            "🎨 Starting Visual Deception Analysis",
            agent="ImageAnalysis",
            node="analyze_images",
            event_type="AGENT_START",
            session_id=session_id,
            pages_to_analyze=num_pages_to_process,
        )
        
        if not all_images:
            logger.warning(
                "No images available for analysis",
                agent="ImageAnalysis",
                node="analyze_images",
                session_id=session_id,
            )
            return {"page_analyses": []}

        logger.debug(
            f"Processing {num_pages_to_process} pages | {len(all_images)} images | {len(all_urls)} URLs",
            agent="ImageAnalysis",
            node="analyze_images",
            session_id=session_id,
            total_images=len(all_images),
            total_urls=len(all_urls),
        )

        images_to_process = sorted(
            [img for img in all_images if img.page_number < num_pages_to_process],
            key=lambda img: img.page_number
        )
        
        if not images_to_process:
            logger.warning(
                "No images found for the requested page range",
                agent="ImageAnalysis",
                node="analyze_images",
                session_id=session_id,
            )
            return {"page_analyses": []}

        page_analyses_results: List[PageAnalysisResult] = []
        previous_pages_context = "This is the first page. There is no prior context."

        for image in images_to_process:
            page_num = image.page_number
            logger.info(
                f"🔍 Analyzing Page {page_num} for visual deception",
                agent="ImageAnalysis",
                node="analyze_images",
                event_type="PAGE_ANALYSIS_START",
                session_id=session_id,
                page_number=page_num,
            )

            urls_for_this_page = [url for url in all_urls if url.page_number == page_num]
            element_map = {
                "page_number": page_num,
                "interactive_elements": [url.model_dump() for url in urls_for_this_page]
            }

            # Format the user prompt with the context and element map.
            formatted_user_prompt = IMAGE_ANALYSIS_USER_PROMPT.format(
                element_map_json=json.dumps(element_map, indent=2),
                previous_pages_context=previous_pages_context
            )
            
            # Construct the full, correct list of messages for the LLM call.
            messages = [
                SystemMessage(content=IMAGE_ANALYSIS_SYSTEM_PROMPT),
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
            logger.debug(
                f"Sending page {page_num} to VDA LLM | {len(urls_for_this_page)} interactive elements",
                agent="ImageAnalysis",
                node="analyze_images",
                session_id=session_id,
                page_number=page_num,
                element_count=len(urls_for_this_page),
            )
            
            # Add timeout protection to prevent infinite hangs on vision LLM calls
            page_result = await asyncio.wait_for(
                llm_with_structured_output.ainvoke(messages),
                timeout=LLM_TIMEOUT_VISION
            )
            page_analyses_results.append(page_result)
            
            # Verdict event with key metrics
            logger.info(
                f"📊 Page {page_num} Analysis Complete | Verdict: {page_result.visual_verdict} | Confidence: {page_result.confidence_score:.1%} | Findings: {len(page_result.detailed_findings)} | Summary: {page_result.summary[:80]}...",
                agent="ImageAnalysis",
                node="analyze_images",
                event_type="PAGE_ANALYSIS_COMPLETE",
                session_id=session_id,
                page_number=page_num,
                page_description=page_result.page_description,
                verdict=page_result.visual_verdict,
                confidence=page_result.confidence_score,
                summary=page_result.summary,
                findings_count=len(page_result.detailed_findings),
                tactics_count=len(page_result.deception_tactics),
                benign_signals_count=len(page_result.benign_signals),
                urls_prioritized=len(page_result.prioritized_urls),
                detailed_findings=[f.model_dump() for f in page_result.detailed_findings],
                deception_tactics=[t.model_dump() for t in page_result.deception_tactics],
                benign_signals=[s.model_dump() for s in page_result.benign_signals],
            )
            
            # Log high-significance findings at WARNING level
            high_sig_findings = [f for f in page_result.detailed_findings if f.significance == "high"]
            if high_sig_findings:
                for finding in high_sig_findings:
                    logger.warning(
                        f"⚠️  Page {page_num} High-Significance Finding: {finding.element_type} - {finding.assessment[:80]}",
                        agent="ImageAnalysis",
                        node="analyze_images",
                        event_type="HIGH_SIGNIFICANCE_FINDING",
                        session_id=session_id,
                        page_number=page_num,
                        element_type=finding.element_type,
                        visual_description=finding.visual_description,
                        technical_data=finding.technical_data,
                        assessment=finding.assessment,
                        significance=finding.significance,
                    )
            
            # Log deception tactics detected
            if page_result.deception_tactics:
                tactics_summary = ", ".join([f"{t.tactic_type} ({t.confidence:.0%})" for t in page_result.deception_tactics[:3]])
                if len(page_result.deception_tactics) > 3:
                    tactics_summary += f" ... and {len(page_result.deception_tactics) - 3} more"
                
                logger.warning(
                    f"🚨 Page {page_num} Deception Tactics: {tactics_summary}",
                    agent="ImageAnalysis",
                    node="analyze_images",
                    event_type="DECEPTION_TACTICS_DETECTED",
                    session_id=session_id,
                    page_number=page_num,
                    tactics_count=len(page_result.deception_tactics),
                    deception_tactics=[t.model_dump() for t in page_result.deception_tactics],
                )
            
            # Log benign signals found
            if page_result.benign_signals:
                signals_summary = ", ".join([f"{s.signal_type} ({s.confidence:.0%})" for s in page_result.benign_signals[:3]])
                if len(page_result.benign_signals) > 3:
                    signals_summary += f" ... and {len(page_result.benign_signals) - 3} more"
                
                logger.info(
                    f"✅ Page {page_num} Benign Signals: {signals_summary}",
                    agent="ImageAnalysis",
                    node="analyze_images",
                    event_type="BENIGN_SIGNALS_DETECTED",
                    session_id=session_id,
                    page_number=page_num,
                    signals_count=len(page_result.benign_signals),
                    benign_signals=[s.model_dump() for s in page_result.benign_signals],
                )
            
            # Log prioritized URLs for investigation
            if page_result.prioritized_urls:
                url_summary = ", ".join([f"P{u.priority}: {u.url[:40]}..." for u in page_result.prioritized_urls[:3]])
                if len(page_result.prioritized_urls) > 3:
                    url_summary += f" ... and {len(page_result.prioritized_urls) - 3} more"
                
                logger.info(
                    f"🔗 Page {page_num} flagged {len(page_result.prioritized_urls)} URLs for investigation | {url_summary}",
                    agent="ImageAnalysis",
                    node="analyze_images",
                    event_type="URLS_PRIORITIZED",
                    session_id=session_id,
                    page_number=page_num,
                    url_count=len(page_result.prioritized_urls),
                    prioritized_urls=[u.model_dump() for u in page_result.prioritized_urls],
                )

            # Generate the rich, structured briefing for the next iteration.
            previous_pages_context = _create_structured_forensic_briefing(page_result)
        
        logger.success(
            f"✅ Visual analysis complete | {len(page_analyses_results)} pages analyzed",
            agent="ImageAnalysis",
            node="analyze_images",
            event_type="ANALYSIS_COMPLETE",
            session_id=session_id,
            pages_analyzed=len(page_analyses_results),
        )
        
        return {"page_analyses": page_analyses_results}

    except asyncio.TimeoutError:
        error_msg = f"Error in analyze_pdf_images: Vision LLM call timed out after {LLM_TIMEOUT_VISION} seconds"
        logger.exception(
            "❌ Visual analysis failed - timeout",
            agent="ImageAnalysis",
            node="analyze_images",
            event_type="ERROR",
            session_id=state.get('session_id'),
            error=error_msg,
            timeout_seconds=LLM_TIMEOUT_VISION
        )
        return {"errors": [error_msg]}
    except Exception as e:
        error_msg = f"Error in analyze_pdf_images: {type(e).__name__}: {e}"
        logger.exception(
            "❌ Visual analysis failed",
            agent="ImageAnalysis",
            node="analyze_images",
            event_type="ERROR",
            session_id=state.get('session_id'),
            error=error_msg,
        )
        return {"errors": [error_msg]}


async def compile_image_findings(state: ImageAnalysisState):
    """
    Aggregates all page-level analyses into a final, conclusive report using
    robust, programmatic logic.
    """
    try:
        session_id = state.get('session_id')
        page_analyses = state.get("page_analyses", [])
        
        logger.info(
            "📑 Compiling final image analysis report",
            agent="ImageAnalysis",
            node="compile_findings",
            event_type="COMPILATION_START",
            session_id=session_id,
            page_count=len(page_analyses),
        )

        if not page_analyses:
            logger.warning(
                "No page analyses available - generating empty report",
                agent="ImageAnalysis",
                node="compile_findings",
                session_id=session_id,
            )
            # Correctly instantiate the report with keywords to prevent TypeError.
            visual_analysis_report = ImageAnalysisReport(
                overall_verdict="Benign",
                overall_confidence=1.0,
                document_flow_summary="No pages were analyzed.",
                executive_summary="No pages were analyzed, so no threats were detected.",
                page_analyses=[],
                all_detailed_findings=[],
                all_deception_tactics=[],
                all_benign_signals=[],
                all_priority_urls=[]
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

        # Generate the Executive Summary (before logging so we can include it).
        summary = (
            f"Visual analysis of {len(page_analyses)} page(s) resulted in an overall verdict of '{most_severe_verdict}'.\n"
            f"The analysis produced {len(all_detailed_findings)} specific forensic findings, "
            f"which were summarized into {len(all_tactics)} deception tactics and {len(all_signals)} benign signals.\n"
            f"Flagged {len(all_priority_urls)} URLs for further investigation."
        )

        # Log verdict determination with full report details
        logger.info(
            f"🎯 Overall Verdict: {most_severe_verdict} | Confidence: {overall_confidence:.1%} | Pages: {len(page_analyses)} | Findings: {len(all_detailed_findings)} | Tactics: {len(all_tactics)} | Benign Signals: {len(all_signals)} | Priority URLs: {len(all_priority_urls)}",
            agent="ImageAnalysis",
            node="compile_findings",
            event_type="VERDICT_DETERMINED",
            session_id=session_id,
            verdict=most_severe_verdict,
            confidence=overall_confidence,
            executive_summary=summary,
            document_flow_summary=document_flow_summary,
            findings_count=len(all_detailed_findings),
            tactics_count=len(all_tactics),
            signals_count=len(all_signals),
            priority_urls_count=len(all_priority_urls),
            all_detailed_findings=[f.model_dump() for f in all_detailed_findings],
            all_deception_tactics=[t.model_dump() for t in all_tactics],
            all_benign_signals=[s.model_dump() for s in all_signals],
            all_priority_urls=[u.model_dump() for u in all_priority_urls],
        )

        # Construct the final report object.
        visual_analysis_report = ImageAnalysisReport(
            overall_verdict=most_severe_verdict,
            overall_confidence=overall_confidence,
            document_flow_summary=document_flow_summary,
            executive_summary=summary,
            page_analyses=page_analyses,
            all_detailed_findings=all_detailed_findings,
            all_deception_tactics=all_tactics,
            all_benign_signals=all_signals,
            all_priority_urls=all_priority_urls
        )

        # Save the final report to a JSON file for record-keeping.
        session_output_directory = state.get("output_directory", "output")
        session_id = state.get("session_id", "unknown")
        image_analysis_directory = os.path.join(session_output_directory, "image_analysis")
        await asyncio.to_thread(os.makedirs, image_analysis_directory, exist_ok=True)
        json_filename = f"image_analysis_state_session_{session_id}.json"
        json_path = os.path.join(image_analysis_directory, json_filename)
        
        logger.info(
            f"💾 Saving report to: {json_path}",
            agent="ImageAnalysis",
            node="compile_findings",
            event_type="REPORT_SAVED",
            session_id=session_id,
            report_path=json_path,
        )
        
        await dump_state_to_file(visual_analysis_report, json_path)
        
        logger.success(
            f"✅ Image analysis complete | Verdict: {most_severe_verdict} | {len(all_priority_urls)} URLs flagged",
            agent="ImageAnalysis",
            node="compile_findings",
            event_type="COMPILATION_COMPLETE",
            session_id=session_id,
            final_verdict=most_severe_verdict,
            final_confidence=overall_confidence,
            priority_urls_count=len(all_priority_urls),
        )
            
        return {"visual_analysis_report": visual_analysis_report}
    
    except Exception as e:
        error_msg = f"Error in compile_image_findings: {e}"
        logger.exception(
            "❌ Report compilation failed",
            agent="ImageAnalysis",
            node="compile_findings",
            event_type="ERROR",
            session_id=state.get('session_id'),
            error=str(e),
        )
        return {"errors": [error_msg]}
