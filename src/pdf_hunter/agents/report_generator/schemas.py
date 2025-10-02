from typing import Annotated, List, Literal, Dict, Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict, NotRequired
import operator

# Import the types we need from other agents
from ..file_analysis.schemas import EvidenceGraph, FinalReport
from ..image_analysis.schemas import ImageAnalysisReport
from ..url_investigation.schemas import URLAnalysisResult
from ..pdf_extraction.schemas import ExtractedImage, ExtractedURL, PDFHashData


class FinalVerdict(BaseModel):
    """The final, authoritative verdict of the entire investigation."""
    verdict: Literal["Benign", "Suspicious", "Malicious"] = Field(..., description="The final verdict on the PDF file.")
    confidence: float = Field(..., description="The confidence in the final verdict (0.0-1.0), reflecting the consistency and strength of the evidence.")
    reasoning: str = Field(..., description="A concise synthesis explaining the most critical evidence and logic that led to the final verdict.")


class ReportGeneratorOutputState(TypedDict):
    """Output state for Report Generator - what it produces."""
    final_report: NotRequired[str]
    final_verdict: NotRequired[FinalVerdict]
    errors: Annotated[List[list], operator.add]


class ReportGeneratorState(TypedDict):
    """The complete state for the Report Generator agent's internal graph."""
    # Session info
    # --- Initial User Inputs ---
    file_path: str
    output_directory: str
    number_of_pages_to_process: int
    pages_to_process: Optional[List[int]]
    additional_context: NotRequired[Optional[str]]
    session_id: NotRequired[Optional[str]]

    pdf_hash: Optional[PDFHashData]
    page_count: Optional[int]

    # --- Results from Preprocessing Agent ---
    extracted_images: List[ExtractedImage]
    extracted_urls: List[ExtractedURL]

    # --- Results from Visual Analysis Agent ---
    visual_analysis_report: NotRequired[ImageAnalysisReport]

    # --- Results from Static Analysis Agent ---
    structural_summary: Dict[str, str]
    master_evidence_graph: NotRequired[EvidenceGraph]
    triage_classification_decision: NotRequired[str]
    triage_classification_reasoning: NotRequired[str]
    static_analysis_final_report: NotRequired[FinalReport]

    # --- Results from Link Analysis Agent ---
    link_analysis_final_reports: Annotated[List[URLAnalysisResult], operator.add]

        # --- Results from Finalization Agent ---
    final_report: NotRequired[str]
    final_verdict: NotRequired[FinalVerdict]

    errors: Annotated[List[list], operator.add]