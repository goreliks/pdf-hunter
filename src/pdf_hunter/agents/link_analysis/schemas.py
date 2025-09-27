from pydantic import BaseModel, Field
from typing import Any, List, Literal, NotRequired, Optional
from typing_extensions import TypedDict
from typing_extensions import Annotated, Sequence
import operator
from ..visual_analysis.schemas import PrioritizedURL, VisualAnalysisReport
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
    output_directory: str
    session_id: str        # Added for session management
    visual_analysis_report: NotRequired[VisualAnalysisReport]

    errors: Annotated[List[str], operator.add]

    link_analysis_final_reports: Annotated[List[URLAnalysisResult], operator.add]

class LinkAnalysisInputState(TypedDict):
    output_directory: str
    session_id: str        # Added for session management
    visual_analysis_report: NotRequired[VisualAnalysisReport]


class LinkAnalysisOutputState(TypedDict):
    output_directory: str  # Added to pass session directory to other agents
    session_id: str        # Added to pass session ID to other agents
    link_analysis_final_reports: Annotated[List[URLAnalysisResult], operator.add]
    errors: NotRequired[Annotated[List[str], operator.add]]


class LinkInvestigatorState(TypedDict):
    """
    State for the Link Investigator sub-agent.
    """
    # Inputs
    url_task: PrioritizedURL
    output_directory: str
    session_id: str        # Added for session management

    # Intermediate
    investigation_logs: Annotated[Sequence[BaseMessage], operator.add]

    # Outputs
    errors: NotRequired[Annotated[List[str], operator.add]]
    link_analysis_final_report: URLAnalysisResult


class LinkInvestigatorOutputState(TypedDict):
    link_analysis_final_report: URLAnalysisResult
    errors: NotRequired[Annotated[List[str], operator.add]]