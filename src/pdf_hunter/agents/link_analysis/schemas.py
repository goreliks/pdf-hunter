from pydantic import BaseModel, Field
from typing import Any, List, Literal, Optional
from typing_extensions import TypedDict
from typing_extensions import Annotated, Sequence
import operator
from ..visual_analysis.schemas import PrioritizedURL
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AnalystFindings(BaseModel):
    """The synthesized analysis of the investigation log."""
    final_url: str = Field(..., description="The final destination URL reached by the Investigator.")
    verdict: Literal["Benign", "Suspicious", "Malicious", "Inaccessible"]
    confidence: float
    summary: str = Field(..., description="A concise, executive summary of the investigation, explaining the key findings and the reasoning behind the verdict.")
    detected_threats: List[str] = Field(default_factory=list)
    domain_whois_record: Optional[str] = Field(None, description="The summary of the WHOIS record for the final root domain, extracted from the investigation log.")
    screenshot_paths: List[str] = Field(default_factory=list, description="A list of all screenshot file paths mentioned in the investigation log.")

# The final, assembled forensic report.
class URLAnalysisResult(BaseModel):
    """The final, assembled forensic report, created programmatically by our code."""
    initial_url: PrioritizedURL
    full_investigation_log: List[dict]
    analyst_findings: AnalystFindings

# The state for our final two-stage pipeline graph.
class LinkAnalysisState(TypedDict):
    # Inputs
    url_task: PrioritizedURL
    output_directory: str
    link_analysis_messages: Annotated[Sequence[BaseMessage], add_messages]

    # Intermediate result
    investigation_log: Annotated[Sequence[BaseMessage], add_messages]
    errors: Annotated[List[str], operator.add]

    # Final output
    link_analysis_final_report: URLAnalysisResult

class LinkAnalysisInputState(TypedDict):
    url_task: PrioritizedURL
    output_directory: str

class LinkAnalysisOutputState(TypedDict):
    link_analysis_final_report: URLAnalysisResult
    errors: Annotated[List[str], operator.add]