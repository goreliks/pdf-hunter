from typing import List, Dict, Optional, Union, Literal, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import operator
from typing_extensions import NotRequired
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class ThreatType(str, Enum):
    """Enumeration of detectable, high-signal threat indicators."""
    OPENACTION = "OpenAction"
    LAUNCH_ACTION = "Launch Action"
    JAVASCRIPT = "JavaScript"
    ACROFORM = "AcroForm"
    EMBEDDED_FILE = "Embedded File"
    USER_DEFINED = "User-Defined Context"
    STRUCTURAL_ANOMALY = "Structural Anomaly"


class MissionStatus(str, Enum):
    """The lifecycle status of an investigation mission."""
    NEW = "New"
    IN_PROGRESS = "In Progress"
    RESOLVED_MALICIOUS = "Resolved - Malicious"
    RESOLVED_BENIGN = "Resolved - Benign"
    BLOCKED = "Blocked - Needs More Information"
    FAILED = "Failed - Tool or Agent Error"


class InvestigationMission(BaseModel):
    """A single, focused investigative mission for an Investigator agent."""
    mission_id: str = Field(default_factory=lambda: f"mission_{uuid.uuid4().hex[:8]}")
    threat_type: ThreatType
    entry_point_description: str
    source_object_id: Optional[int] = None
    status: MissionStatus = MissionStatus.NEW
    reasoning: str
    is_user_defined: bool = False


class TriageReport(BaseModel):
    """The report returned by the Triage node."""
    mission_list: List[InvestigationMission]
    triage_classification_decision: Literal["innocent", "suspicious"]
    triage_classification_reasoning: str


class NodeProperty(BaseModel):
    """A single key-value pair to describe a property of an EvidenceNode."""
    key: str = Field(..., description="The name of the property (e.g., 'encoding', 'raw_content', 'value').")
    
    # We now only allow JSON primitive types and lists of those primitives.
    # Any complex object or dictionary MUST be serialized into a JSON string first.
    value: Union[str, int, float, bool, List[str], List[int], None] = Field(
        ..., 
        description="The value of the property. Must be a primitive type (str, int, float, bool, null) or a list of primitives. Complex objects should be stored as a JSON string."
    )


class EvidenceNode(BaseModel):
    """
    A single, self-contained piece of evidence in the graph (e.g., a PDF Object, an Artifact, an IOC).
    Each node represents a 'noun' in our investigation.
    """
    id: str = Field(..., description="A unique identifier for this node (e.g., 'obj_4', 'art_123a6', 'ioc_evil_com'). This is the primary key used to link nodes together.")
    
    node_type: str = Field(..., description="The classification of the evidence (e.g., 'PDFObject', 'Artifact', 'IOC', 'File'). This tells the agent what kind of entity it is looking at.")
    
    label: str = Field(..., description="A short, human-readable title for the node (e.g., '/Launch Action', 'Decoded PowerShell Payload', 'Suspicious URL').")
    
    properties: List[NodeProperty] = Field(
        default_factory=list,
        description="A list of key-value properties that store the raw data and metadata about this node."
    )


class EvidenceEdge(BaseModel):
    """
    A directional link that describes the relationship between two EvidenceNodes.
    Each edge represents a 'verb' connecting two 'nouns'.
    """
    source_id: str = Field(..., description="The unique 'id' of the node where the relationship starts.")
    
    target_id: str = Field(..., description="The unique 'id' of the node where the relationship ends.")
    
    label: str = Field(..., description="The verb that describes the relationship (e.g., 'references', 'contains', 'decodes_to', 'downloads_from').")


class EvidenceGraph(BaseModel):
    """
    The master graph representing all discovered evidence and their relationships.
    This is the central 'brain' or memory of the investigation.
    """
    nodes: List[EvidenceNode] = Field(
        default_factory=list,
        description="A list of all unique pieces of evidence (nodes) that have been discovered."
    )
    
    edges: List[EvidenceEdge] = Field(
        default_factory=list,
        description="A list of all connections (edges) that link the evidence nodes together, forming the attack chain."
    )


class MissionReport(BaseModel):
    """The structure to return by an Investigator after completing a mission."""
    mission_id: str
    final_status: MissionStatus
    summary_of_findings: str
    mission_subgraph: EvidenceGraph


class ReviewerReport(BaseModel):
    """The structured output from the Reviewer node's strategic analysis."""
    
    new_missions: List[InvestigationMission] = Field(
        default_factory=list,
        description="A list of new, targeted follow-up missions to be dispatched if the investigation is not yet complete."
    )
    
    is_investigation_complete: bool = Field(
        ...,
        description="A boolean flag. Set to 'true' ONLY if all missions are resolved and no new connections or valid leads can be generated. Otherwise, set to 'false'."
    )
    
    strategic_summary: str = Field(
        ...,
        description="A concise summary of your strategic assessment, explaining why new missions are being created or why the investigation is considered complete."
    )


class IndicatorOfCompromise(BaseModel):
    """A single, actionable Indicator of Compromise (IOC)."""
    value: str = Field(..., description="The value of the indicator (e.g., a URL, domain, IP address, or file hash).")
    ioc_type: str = Field(..., description="The type of indicator (e.g., 'URL', 'Domain', 'IPv4', 'SHA256').")
    source_mission_id: str = Field(..., description="The ID of the mission that discovered this IOC.")

class AttackChainLink(BaseModel):
    """A single step in the reconstructed attack chain."""
    source_node_id: str = Field(..., description="The ID of the source node in the evidence graph.")
    source_node_label: str = Field(..., description="The human-readable label of the source node.")
    edge_label: str = Field(..., description="The relationship between the source and target (e.g., 'executes', 'downloads_from').")
    target_node_id: str = Field(..., description="The ID of the target node in the evidence graph.")
    target_node_label: str = Field(..., description="The human-readable label of the target node.")
    description: str = Field(..., description="A human-readable summary of this step in the attack.")

class FinalReport(BaseModel):
    """The complete and final output of the static analysis investigation."""
    
    final_verdict: Literal["Benign", "Suspicious", "Malicious"] = Field(
        ...,
        description="The final, conclusive verdict on the analyzed file."
    )
    
    executive_summary: str = Field(
        ...,
        description="A high-level, 2-3 sentence summary of the investigation's findings. This is for quick ingestion by an analyst."
    )
    
    attack_chain: List[AttackChainLink] = Field(
        default_factory=list,
        description="A chronological, step-by-step reconstruction of the malicious activity found in the file."
    )
    
    indicators_of_compromise: List[IndicatorOfCompromise] = Field(
        default_factory=list,
        description="A de-duplicated list of all actionable Indicators of Compromise found."
    )

    full_markdown_report: str = Field(
        ...,
        description="A comprehensive, human-readable report in Markdown format, detailing the entire investigation process, evidence, and conclusions."
    )


class MergedEvidenceGraph(BaseModel):
    """The intelligently merged master evidence graph"""
    master_graph: EvidenceGraph
    merge_summary: str = Field(
        description="Brief explanation of how conflicts were resolved and duplicates were merged"
    )

    
# States

class TriageState(TypedDict):
    session_id: str
    file_path: str
    output_directory: str
    mission_list: Annotated[List[InvestigationMission], operator.add]
    structural_summary: Dict[str, str]
    additional_context: NotRequired[Optional[str]]
    triage_classification_decision: str
    triage_classification_reasoning: str


class InvestigatorOutputState(TypedDict):
    mission: InvestigationMission
    mission_report: NotRequired[MissionReport]
    errors: NotRequired[Annotated[List[str], operator.add]]
    messages: Annotated[list[AnyMessage], add_messages]


class InvestigatorState(TypedDict):
    """
    The state object for the investigator node.
    """
    file_path: str
    mission: InvestigationMission
    mission_report: NotRequired[MissionReport]
    errors: NotRequired[Annotated[List[str], operator.add]]
    structural_summary: Dict[str, str]
    messages: Annotated[list[AnyMessage], add_messages]


class StaticAnalysisState(TypedDict):
    """
    The main state object for the orchestrating graph.
    """
    # --- Static Session Info ---
    session_id: str
    file_path: str
    output_directory: str
    additional_context: NotRequired[Optional[str]]
    structural_summary: Dict[str, str]

    # --- Mission Control ---
    # The master list of all missions, managed by Triage, Reducer, and Reviewer.
    mission_list: List[InvestigationMission] 

    # --- THE SHARED BRAIN - Curated Results ---
    # This is the clean, structured data for high-level reasoning.
    mission_reports: Dict[str, MissionReport]
    master_evidence_graph: EvidenceGraph

    # --- THE SHARED BRAIN & AUDIT TRAIL (COMBINED) ---
    # THIS IS YOUR KEY INSIGHT:
    # By making this a list with operator.add, LangGraph will automatically
    # collect the output of every parallel `conduct_investigation` run
    # and append it to this list. This removes the need for a reducer node.
    completed_investigations: Annotated[List[InvestigatorOutputState], operator.add]

    # --- Global Error Handling & Triage Results ---
    errors: Annotated[List[str], operator.add]
    triage_classification_decision: str
    triage_classification_reasoning: str

    static_analysis_final_report: NotRequired[FinalReport]


class StaticAnalysisInputState(TypedDict):
    session_id: str
    file_path: str
    output_directory: str
    additional_context: NotRequired[Optional[str]]


class StaticAnalysisOutputState(TypedDict):
    structural_summary: Dict[str, str]
    master_evidence_graph: EvidenceGraph
    triage_classification_decision: str
    triage_classification_reasoning: str
    static_analysis_final_report: NotRequired[FinalReport]
    errors: Annotated[List[str], operator.add]
