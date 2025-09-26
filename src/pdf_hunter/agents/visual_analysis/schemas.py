import operator
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Annotated, NotRequired

from ..preprocessing.schemas import ExtractedImage, ExtractedURL


class DeceptionTactic(BaseModel):
    """Information about a detected deception tactic."""
    tactic_type: str = Field(..., description="Type of deception tactic identified.")
    description: str = Field(..., description="Detailed description of the tactic.")
    confidence: float = Field(..., description="Confidence in detection (0.0-1.0).")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence for this tactic")

class BenignSignal(BaseModel):
    """Information about a detected benign/legitimate signal."""
    signal_type: str = Field(..., description="Type of benign signal.")
    description: str = Field(..., description="Detailed description of the signal.")
    confidence: float = Field(..., description="Confidence in assessment (0.0-1.0).")

class PrioritizedURL(BaseModel):
    """A URL marked for deeper analysis by downstream agents."""
    url: str = Field(..., description="The URL requiring analysis.")
    priority: int = Field(..., description="Priority level (1=highest, 5=lowest).")
    reason: str = Field(..., description="Reason for the priority assessment.")
    page_number: int = Field(..., description="The page number (0-indexed) where this URL was most prominently found.")
    source_context: Optional[str] = Field(None, description="Context about the source document (e.g., 'PDF document with verification prompt')")
    extraction_method: Optional[str] = Field(None, description="How the URL was extracted (e.g., 'qr_code', 'annotation', 'text')")


class DetailedFinding(BaseModel):
    """A specific finding from visual-technical cross-examination."""
    element_type: str = Field(..., description="Type of element (link, button, logo, etc.)")
    page_number: int = Field(..., description="Page number where finding was observed", ge=0)
    visual_description: str = Field(..., description="Description of visual appearance")
    technical_data: Optional[str] = Field(None, description="A JSON-formatted string containing relevant technical data (e.g., '{\"url\": \"http://...\", \"xref\": 15}'). Should be null if no technical data is relevant.")
    assessment: str = Field(..., description="Assessment of this finding")
    significance: Literal["low", "medium", "high"] = Field(..., description="Significance level of this finding")


class PageAnalysisResult(BaseModel):
    """
    The structured output from the visual analysis of a SINGLE page.
    This is the contract for our LLM's page-level analysis.
    """
    page_description: str = Field(..., description="A brief, objective description of the page's overall appearance, layout, and apparent purpose (e.g., 'A professional-looking corporate invoice with a prominent payment button.').")
    detailed_findings: List[DetailedFinding] = Field(
        default_factory=list, description="Specific cross-modal analysis findings"
    )
    deception_tactics: List[DeceptionTactic] = Field(default_factory=list, description="Identified deception techniques")
    benign_signals: List[BenignSignal] = Field(default_factory=list, description="Identified legitimacy indicators")
    prioritized_urls: List[PrioritizedURL] = Field(default_factory=list, description="URLs requiring deeper analysis")
    visual_verdict: Literal["Benign", "Suspicious", "Highly Deceptive"] = Field(..., description="Final visual trustworthiness judgment for this page")
    confidence_score: float = Field(..., description="Confidence in the verdict for this page (0.0-1.0).")
    summary: str = Field(..., description="Concise summary explaining conclusion and evidence weighting for this page")
    


class VisualAnalysisReport(BaseModel):
    """The complete and final output of the visual analysis agent, created by aggregating all page-level results."""
    overall_verdict: Literal["Benign", "Suspicious", "Highly Deceptive"]
    overall_confidence: float
    executive_summary: str

    document_flow_summary: str = Field(..., description="A summary of the document's structure, describing the purpose of each page in sequence.")
    
    page_analyses: List[PageAnalysisResult]
    
    all_detailed_findings: List[DetailedFinding]
    all_deception_tactics: List[DeceptionTactic]
    all_benign_signals: List[BenignSignal]
    high_priority_urls: List[PrioritizedURL]


class VisualAnalysisState(TypedDict):
    """
    State for the Visual Analysis agent.
    """
    extracted_images: List[ExtractedImage]
    extracted_urls: List[ExtractedURL]
    number_of_pages_to_process: int
    page_analyses: List[PageAnalysisResult]
    visual_analysis_report: NotRequired[VisualAnalysisReport]
    errors: Annotated[List[str], operator.add]


class VisualAnalysisInputState(TypedDict):
    extracted_images: List[ExtractedImage]
    extracted_urls: List[ExtractedURL]
    number_of_pages_to_process: int


class VisualAnalysisOutputState(TypedDict):
    page_analyses: List[PageAnalysisResult]
    visual_analysis_report: VisualAnalysisReport
    errors: Annotated[List[str], operator.add]
