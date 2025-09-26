from typing import Annotated, List, Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict, NotRequired
import operator


class FinalVerdict(BaseModel):
    """The final, authoritative verdict of the entire investigation."""
    verdict: Literal["Benign", "Suspicious", "Malicious"] = Field(..., description="The final verdict on the PDF file.")
    confidence: float = Field(..., description="The confidence in the final verdict (0.0-1.0), reflecting the consistency and strength of the evidence.")
    reasoning: str = Field(..., description="A concise synthesis explaining the most critical evidence and logic that led to the final verdict.")


class FinalizerState(TypedDict):
    """The state for the Finalizer agent's internal graph."""
    # This state will be merged with the main OrchestratorState
    final_report: NotRequired[str]
    final_verdict: NotRequired[FinalVerdict]
    errors: Annotated[List[str], operator.add]
    output_directory: str