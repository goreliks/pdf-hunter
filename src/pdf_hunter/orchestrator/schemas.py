from typing import List, Optional, Dict
from typing_extensions import TypedDict, NotRequired, Annotated
import operator


from ..agents.preprocessing.schemas import ExtractedImage, ExtractedURL
from ..agents.visual_analysis.schemas import VisualAnalysisReport
from ..agents.preprocessing.schemas import PDFHashData
from ..agents.static_analysis.schemas import EvidenceGraph, FinalReport
from ..agents.link_analysis.schemas import URLAnalysisResult

class OrchestratorState(TypedDict):
    """
    The master state for the PDF-Hunter orchestrator.
    It holds the initial inputs and collects the final reports from all sub-agents.
    """
    # --- Initial User Inputs ---
    file_path: str
    output_directory: str
    number_of_pages_to_process: int
    pages_to_process: Optional[List[int]]
    additional_context: NotRequired[Optional[str]]
    session_id: str

    pdf_hash: Optional[PDFHashData]
    page_count: Optional[int]

    # --- Results from Preprocessing Agent ---
    extracted_images: List[ExtractedImage]
    extracted_urls: List[ExtractedURL]

    # --- Results from Visual Analysis Agent ---
    visual_analysis_report: NotRequired[VisualAnalysisReport]

    # --- Results from Static Analysis Agent ---
    structural_summary: Dict[str, str]
    master_evidence_graph: NotRequired[EvidenceGraph]
    triage_classification_decision: NotRequired[str]
    triage_classification_reasoning: NotRequired[str]
    static_analysis_final_report: NotRequired[FinalReport]

    # --- Results from Link Analysis Agent ---
    link_analysis_final_report: NotRequired[Annotated[List[URLAnalysisResult], operator.add]]

    # --- Global Error Tracking ---
    errors: Annotated[List[list], operator.add]


class OrchestratorInputState(TypedDict):
    session_id: str
    file_path: str
    output_directory: str
    number_of_pages_to_process: int
    additional_context: NotRequired[Optional[str]]
