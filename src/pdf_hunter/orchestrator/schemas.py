from typing import List, Optional
from typing_extensions import TypedDict, NotRequired, Annotated
import operator


from ..agents.preprocessing.schemas import ExtractedImage, ExtractedURL
from ..agents.visual_analysis.schemas import VisualAnalysisReport
from ..agents.preprocessing.schemas import PDFHashData

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

    pdf_hash: Optional[PDFHashData]
    page_count: Optional[int]

    # --- Results from Preprocessing Agent ---
    extracted_images: List[ExtractedImage]
    extracted_urls: List[ExtractedURL]

    # --- Results from Visual Analysis Agent ---
    visual_analysis_report: NotRequired[VisualAnalysisReport]
    
    # --- Global Error Tracking ---
    errors: Annotated[List[list], operator.add]


class OrchestratorInputState(TypedDict):
    file_path: str
    output_directory: str
    number_of_pages_to_process: int
