# Report Generator Agent - Technical Documentation

## Overview

**Agent Name**: Report Generator
**Location**: `src/pdf_hunter/agents/report_generator/`
**Purpose**: Final synthesis and verdict determination agent that produces comprehensive forensic reports and authoritative malicious/benign classifications

The Report Generator is the terminal agent in the PDF Hunter analysis pipeline. It receives findings from all upstream agents (File Analysis, Image Analysis, URL Investigation) and performs two critical functions:

1. **Final Adjudication**: Conducts holistic analysis of all evidence to determine the definitive security verdict
2. **Intelligence Briefing**: Synthesizes multi-domain findings into a professional, human-readable forensic report

## Architecture

### Graph Structure

**Implementation**: `src/pdf_hunter/agents/report_generator/graph.py`

```python
report_generator_builder = StateGraph(
    ReportGeneratorState, 
    output_schema=ReportGeneratorOutputState
)

# Node sequence
START → determine_threat_verdict → generate_final_report → save_analysis_results → END
```

**Graph Configuration**:
```python
REPORT_GENERATION_CONFIG = {
    "run_name": "Report Generator Agent",
    "recursion_limit": 10  # Linear workflow: verdict → report → save
}
```

**Rationale**: Simple linear pipeline with no loops or branching - all decisions made sequentially

### Node Descriptions

#### 1. `determine_threat_verdict`
**File**: `src/pdf_hunter/agents/report_generator/nodes.py::determine_threat_verdict()`

**Purpose**: Final adjudication node that synthesizes all agent findings into authoritative verdict

**Process**:
1. Serializes complete investigation state using `serialize_state_safely()`
2. Invokes `final_verdict_llm` with structured output binding to `FinalVerdict` schema
3. Applies 120s timeout protection via `asyncio.wait_for()`
4. Returns verdict with confidence score and reasoning

**LLM Configuration**:
- Model: Configurable via `final_verdict_llm` in `models_config.py`
- Temperature: 0.0
- Output: Structured Pydantic `FinalVerdict` object

**Output Schema** (`FinalVerdict`):
```python
class FinalVerdict(BaseModel):
    verdict: Literal["Benign", "Suspicious", "Malicious"]
    confidence: float  # 0.0-1.0
    reasoning: str     # Concise synthesis of critical evidence
```

**Key Design Decision**: Runs BEFORE report generation to ensure verdict is based on raw data analysis, not influenced by report narrative

#### 2. `generate_final_report`
**File**: `src/pdf_hunter/agents/report_generator/nodes.py::generate_final_report()`

**Purpose**: Intelligence briefing node that creates comprehensive markdown forensic report

**Process**:
1. Receives state with `final_verdict` from previous node
2. Serializes state including verdict
3. Invokes `report_generator_llm` with natural language generation
4. Applies 120s timeout protection
5. Returns complete markdown report string

**LLM Configuration**:
- Model: Configurable via `report_generator_llm` in `models_config.py`
- Temperature: 0.0
- Output: Natural language markdown (no structured output)

**Report Structure**: See [Report Template](#report-template-structure) section

#### 3. `save_analysis_results`
**File**: `src/pdf_hunter/agents/report_generator/nodes.py::save_analysis_results()`

**Purpose**: File persistence node that saves final outputs to disk

**Process**:
1. Creates `report_generator/` subdirectory in session output directory
2. Saves complete state as JSON: `final_state_session_{session_id}.json`
3. Saves markdown report: `final_report_session_{session_id}.md`

**File Operations**:
- Uses `dump_state_to_file()` from serializer utility
- Thread-safe directory creation with `asyncio.to_thread(os.makedirs)`
- No state transformation - directly persists from state dict

**Output Files**:
```
{output_directory}/report_generator/
├── final_state_session_{session_id}.json
└── final_report_session_{session_id}.md
```

---

## State Schema

### Input State: `ReportGeneratorState`
**File**: `src/pdf_hunter/agents/report_generator/schemas.py`

Complete state received from orchestrator containing all agent findings:

```python
class ReportGeneratorState(TypedDict):
    # === Initial User Inputs ===
    file_path: str
    output_directory: str
    number_of_pages_to_process: int
    pages_to_process: Optional[List[int]]
    additional_context: NotRequired[Optional[str]]
    session_id: NotRequired[Optional[str]]
    
    # === PDF Metadata ===
    pdf_hash: Optional[PDFHashData]  # MD5, SHA1, SHA256
    page_count: Optional[int]
    
    # === PDF Extraction Results ===
    extracted_images: List[ExtractedImage]
    extracted_urls: List[ExtractedURL]
    
    # === Image Analysis Results ===
    visual_analysis_report: NotRequired[ImageAnalysisReport]
    
    # === File Analysis Results ===
    structural_summary: Dict[str, str]
    master_evidence_graph: NotRequired[EvidenceGraph]
    triage_classification_decision: NotRequired[str]
    triage_classification_reasoning: NotRequired[str]
    static_analysis_final_report: NotRequired[FinalReport]
    
    # === URL Investigation Results ===
    link_analysis_final_reports: Annotated[List[URLAnalysisResult], operator.add]
    
    # === Report Generator Outputs ===
    final_report: NotRequired[str]
    final_verdict: NotRequired[FinalVerdict]
    
    # === Error Tracking ===
    errors: Annotated[List[list], operator.add]
```

**Key Observations**:
- Receives ALL upstream agent outputs
- State is read-only - no modifications to input fields
- Only adds `final_report` and `final_verdict`

### Output State: `ReportGeneratorOutputState`
**File**: `src/pdf_hunter/agents/report_generator/schemas.py`

Minimal output schema for orchestrator:

```python
class ReportGeneratorOutputState(TypedDict):
    final_report: NotRequired[str]        # Markdown report
    final_verdict: NotRequired[FinalVerdict]  # Structured verdict
    errors: Annotated[List[list], operator.add]
```

**Design Rationale**: LangGraph output schema pattern - only returns what the agent produces, not entire state

---

## Prompts and Personas

### Verdict Determination Prompts

#### System Prompt: "The Final Adjudicator"
**File**: `src/pdf_hunter/agents/report_generator/prompts.py::REPORT_GENERATOR_VERDICT_SYSTEM_PROMPT`

**Persona**: Master analyst with ultimate authority for holistic evidence synthesis

**Core Mission**: 
- Conduct final critical check of all raw data
- Serve as fail-safe against incomplete or incorrect agent conclusions
- Determine the most likely **intent** of the file author

**Analytical Lenses**:
1. **Correlation and Contradiction**: Cross-agent finding alignment
2. **Deception as Evidence**: Deceptive tactics indicate suspicious intent
3. **Weakest Link Principle**: Overall trust defined by most dangerous component

**Key Design Decision**: Emphasizes that verdict is NOT a simple summary of agent verdicts, but an independent holistic analysis

#### User Prompt Template
**File**: `src/pdf_hunter/agents/report_generator/prompts.py::REPORT_GENERATOR_VERDICT_USER_PROMPT`

**Structure**:
```
The investigation is complete. You have been provided with the complete 
raw case file containing all findings from the specialized analysis agents. 
You must now issue the final, authoritative judgment.

**Complete Case File (Raw Intelligence Data):**
```json
{serialized_state}
```

**Your Adjudication Task:**
Perform your holistic analysis based on your guiding principles. Weigh all 
the raw evidence, scrutinize the correlations and contradictions, and 
determine the most likely overall intent of this file.

Issue your final judgment in the required `FinalVerdict` JSON format.
```

**Variables**:
- `{serialized_state}`: Full JSON-serialized state from all agents

### Report Generation Prompts

#### System Prompt: "The Lead Intelligence Briefer"
**File**: `src/pdf_hunter/agents/report_generator/prompts.py::REPORT_GENERATOR_SYSTEM_PROMPT`

**Persona**: Master intelligence analyst skilled in distilling complex technical data into comprehensive forensic reports

**Core Mission**:
- Create definitive "single source of truth" for investigation
- Document verdict and build complete narrative supporting it
- Balance depth (forensic review) with clarity (human analyst comprehension)

**Guiding Principle**: "Clarity from Complexity" - transform structured JSON into professional, human-readable report

**Key Design Decision**: Report generation happens AFTER verdict determination, so briefer documents pre-determined verdict rather than influencing it

#### User Prompt Template
**File**: `src/pdf_hunter/agents/report_generator/prompts.py::REPORT_GENERATOR_USER_PROMPT`

**Structure**:
```
The multi-domain investigation and final adjudication are complete. All 
specialized agents have submitted their findings. Compile the official, 
detailed forensic report in Markdown format. The final verdict has already 
been determined and is included in the case file.

**Complete Case File (Raw Intelligence Data + Final Verdict):**
```json
{serialized_state}
```

**Your Forensic Reporting Framework:**
[See Report Template Structure below]

Your final output must be the complete Markdown report only. Do not include 
any other text or commentary.
```

**Variables**:
- `{serialized_state}`: Full state INCLUDING `final_verdict` from previous node

---

## Report Template Structure

The report follows a standardized forensic report template:

### Section 1: Final Verdict and Executive Summary
- **Verdict**: Benign/Suspicious/Malicious
- **Confidence Level**: Percentage score
- **Reasoning Summary**: Critical evidence synthesis
- **Investigation Overview**: Scope and key findings

### Section 2: Case File Details
- **Case & File Identifiers**: Session ID, file path, cryptographic hashes (MD5, SHA1, SHA256)
- **Document Composition**: Page count, processed pages, extracted elements (images, URLs)

### Section 3: Executive Summary
- High-level synthesis of all agent findings
- Quick overview of investigation scope
- Critical findings from each analysis phase

### Section 4: Detailed Investigative Narrative
Chronological reconstruction with 4 phases:

1. **Preprocessing and Static Triage**: Initial file impression and reasoning
2. **In-Depth Static Analysis**: Structural investigation, attack chain description
3. **Visual Analysis**: Visual trustworthiness assessment, deception tactics, legitimacy signals
4. **Dynamic Link Analysis**: URL investigation journey and safety conclusions

### Section 5: Correlated Threat Intelligence
- **Critical cross-domain analysis**: Connections between agent findings
- Examples:
  - Visual deception button ↔ Malicious URL correlation
  - Statically discovered script ↔ Visual hiding technique
  - Cross-agent confirmations and contradictions

### Section 6: Evidence & Indicators of Compromise
- **Evidence Log**: 
  - Extracted/decoded file paths (from `master_evidence_graph`)
  - Screenshot file paths from URL investigations
  - All preserved artifacts
- **Actionable IoCs**: 
  - De-duplicated list of malicious/suspicious URLs and domains
  - File hashes of dropped payloads
  - Clear statement if no IoCs found

**Formatting Requirements**:
- Clear Markdown syntax (headings, subheadings, bullet points, numbered lists)
- Professional, precise, unambiguous language
- Report only (no meta-commentary)

---

## LLM Configuration

### Model Setup
**File**: `src/pdf_hunter/config/models_config.py`

```python
# Report Generator LLMs
report_generator_llm = init_chat_model(**azure_openai_config)
final_verdict_llm = init_chat_model(**azure_openai_config)
```

**Provider Configuration**:
```python
# Configuration is centralized in models_config.py
# All model parameters defined in configuration file
azure_openai_config = {
    "model": AZURE_OPENAI_DEPLOYMENT_NAME,
    "temperature": 0.0,  # Deterministic analysis
    "azure_endpoint": AZURE_OPENAI_ENDPOINT,
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "api_version": AZURE_OPENAI_API_VERSION,
    "model_provider": "azure_openai"
}
```

The system features a robust and configurable LLM architecture. All model endpoints, API versions, and deployment names are centralized in the configuration file rather than environment variables, enabling flexible deployment across different environments and model providers. The configuration supports any LLM backend with appropriate capabilities, making the system adaptable to evolving model offerings.

**Required Model Capabilities**:
- **Structured Output**: Support for Pydantic schema binding for `FinalVerdict` generation
- **Large Context**: Sufficient context window to handle serialized investigation state
- **Natural Language Generation**: Strong prose generation for comprehensive forensic reports

### LLM Specialization

| LLM Instance | Purpose | Output Type | Why Separate? |
|--------------|---------|-------------|----------------|
| `final_verdict_llm` | Verdict determination | Structured (Pydantic) | Requires `.with_structured_output()` binding |
| `report_generator_llm` | Report synthesis | Natural language (Markdown) | No structured output needed |

**Key Design Decision**: Separate LLMs because:
1. Different output types (structured vs. unstructured)
2. Different prompting strategies (analytical vs. narrative)
3. Potential for different model selection (e.g., Claude for reports, GPT for structured output)

### Timeout Configuration
**File**: `src/pdf_hunter/config/execution_config.py`

```python
LLM_TIMEOUT_TEXT = 120  # 120 seconds for text-only LLM calls
```

**Protection Mechanism**:
```python
response = await asyncio.wait_for(
    llm.ainvoke(messages),
    timeout=LLM_TIMEOUT_TEXT
)
```

**Rationale**: Report generation can be time-consuming with large state serialization; 120s prevents infinite hangs while allowing complex synthesis

---

## Integration Points

### Input from Orchestrator
**Required State Fields**:
```python
{
    "file_path": str,
    "output_directory": str,
    "session_id": str,
    "pdf_hash": PDFHashData,
    "page_count": int,
    "extracted_images": List[ExtractedImage],
    "extracted_urls": List[ExtractedURL],
    "visual_analysis_report": ImageAnalysisReport,
    "structural_summary": Dict[str, str],
    "master_evidence_graph": EvidenceGraph,
    "triage_classification_decision": str,
    "static_analysis_final_report": FinalReport,
    "link_analysis_final_reports": List[URLAnalysisResult]
}
```

**Orchestrator Graph Edge**:
```python
# From orchestrator/graph.py
orchestrator_builder.add_edge(
    ["File Analysis", "URL Investigation"],  # Wait for both
    "Report Generator"
)
```

**Dependency Pattern**: Report Generator waits for both File Analysis and URL Investigation to complete (Image Analysis feeds into URL Investigation)

### Output to Orchestrator
**Provided State Fields**:
```python
{
    "final_report": str,        # Markdown forensic report
    "final_verdict": FinalVerdict  # Structured verdict
}
```

**Terminal Agent**: Report Generator connects directly to orchestrator `END` node

### File System Outputs
**Output Directory Structure**:
```
{output_directory}/
└── report_generator/
    ├── final_state_session_{session_id}.json
    └── final_report_session_{session_id}.md
```

**JSON State File** (`final_state_session_{session_id}.json`):
- Complete serialized investigation state
- Includes all agent findings and final verdict
- Used for debugging, auditing, and forensic review

**Markdown Report File** (`final_report_session_{session_id}.md`):
- Human-readable forensic report
- Standalone document (no external dependencies)
- Can be shared with stakeholders

---

## Key Design Decisions

### 1. Verdict Before Report
**Decision**: `determine_threat_verdict` runs before `generate_final_report`

**Rationale**:
- Verdict based on raw data analysis, not narrative influence
- Report generation can document and support pre-determined verdict
- Prevents circular reasoning (report influencing verdict that report describes)

**Implementation**: Linear graph edge enforces ordering

### 2. Holistic Analysis Philosophy
**Decision**: Final Adjudicator persona emphasizes independent analysis over agent summary

**Rationale**:
- Individual agents have narrow domain focus (visual, static, etc.)
- Cross-domain correlations may reveal intent invisible to single agent
- "Weakest link" principle: most dangerous component defines overall threat
- Deception tactics across multiple domains compound suspicion

**Implementation**: Prompts explicitly instruct LLM to not simply summarize agent verdicts

### 3. Separate LLM Instances
**Decision**: `final_verdict_llm` and `report_generator_llm` are separate

**Rationale**:
- Different output types require different capabilities
- Structured output binding vs. natural language generation
- Potential for model specialization (best model for each task)
- Separate error handling and timeout management

**Implementation**: Two LLM instances in `models_config.py`

### 4. State Serialization Strategy
**Decision**: Full state serialization passed to LLM context

**Rationale**:
- LLM has complete information for holistic analysis
- No risk of missing critical evidence from upstream agents
- Enables cross-agent correlation analysis
- Large context windows make this feasible for typical investigation sizes

**Implementation**: `serialize_state_safely()` utility handles complex state objects

### 5. File Persistence Pattern
**Decision**: Save both JSON state and markdown report

**Rationale**:
- JSON: Machine-readable, debuggable, auditable, replayable
- Markdown: Human-readable, shareable, presentation-ready
- Dual format supports both technical and non-technical stakeholders

**Implementation**: `save_analysis_results` node handles both formats

---

## Dependencies

### Core Dependencies

**LangChain**:
- `langchain_core.messages.SystemMessage`, `HumanMessage`: Prompt construction
- `.with_structured_output()`: Pydantic binding for verdict generation
- `init_chat_model()`: Model initialization with provider abstraction

**LangGraph**:
- `StateGraph`: Graph construction and node orchestration
- State management with typed schemas

**Pydantic**:
- `BaseModel`: Schema enforcement for `FinalVerdict`
- Field validation and type checking

**Loguru**:
- Structured logging with JSON output
- Event-based logging for monitoring
- Context propagation (agent, node, session_id)

### Utility Dependencies

**State Serialization** (`src/pdf_hunter/shared/utils/serializer.py`):
- `serialize_state_safely()`: Converts complex state to JSON-serializable format
- `dump_state_to_file()`: Direct file writing with automatic serialization
- Handles Pydantic models, nested structures, non-serializable objects

**Async File Operations**:
- `asyncio.to_thread()`: Non-blocking directory creation
- Async file writing for large reports

### Schema Imports

Report Generator imports schemas from all upstream agents:

```python
from ..file_analysis.schemas import EvidenceGraph, FinalReport
from ..image_analysis.schemas import ImageAnalysisReport
from ..url_investigation.schemas import URLAnalysisResult
from ..pdf_extraction.schemas import ExtractedImage, ExtractedURL, PDFHashData
```

**Design Pattern**: State schema consolidation - single source of truth for all investigation data

---

## Error Handling

### Timeout Protection
Both verdict and report generation protected by timeouts:

```python
try:
    response = await asyncio.wait_for(
        llm.ainvoke(messages),
        timeout=LLM_TIMEOUT_TEXT  # 120 seconds
    )
except asyncio.TimeoutError:
    error_msg = f"LLM call timed out after {LLM_TIMEOUT_TEXT} seconds"
    logger.error(error_msg, exc_info=True)
    return {"errors": [[error_msg]]}
```

### Exception Handling
Broad exception catching with detailed logging:

```python
except Exception as e:
    error_msg = f"Error in {node_name}: {type(e).__name__}: {e}"
    logger.error(error_msg, exc_info=True)
    return {"errors": [[error_msg]]}
```

### Error State Management
Errors accumulate via `operator.add` annotation:

```python
errors: Annotated[List[list], operator.add]
```

**Pattern**: Errors from Report Generator append to existing errors from upstream agents

---

## Testing and CLI

### Standalone Testing
**File**: `src/pdf_hunter/agents/report_generator/cli.py`

**Usage**:
```bash
python -m pdf_hunter.agents.report_generator.cli
```

**Test Pattern**:
```python
async def main():
    """Load test state and run report generator."""
    test_json_path = "path/to/test_state.json"
    
    with open(test_json_path, 'r', encoding='utf-8') as f:
        test_state = json.load(f)
    
    final_state = await report_generator_graph.ainvoke(test_state)
    return final_state

async def run_and_verify():
    """Run and verify results."""
    final_state = await main()
    
    if final_state:
        logger.info(f"Final Report Generated: {'Yes' if final_state.get('final_report') else 'No'}")
        logger.info(f"Final Verdict Generated: {'Yes' if final_state.get('final_verdict') else 'No'}")
```

**Test Input**: Requires complete investigation state JSON from previous agents

**Verification**:
- Checks for `final_report` and `final_verdict` presence
- Logs error count if present
- Pretty-prints verdict details

---

## Logging Strategy

### Event-Based Logging
All major operations emit structured log events:

```python
logger.info(
    "🎯 Final Verdict: {verdict} | Confidence: {confidence:.1%}",
    agent="ReportGenerator",
    node="determine_threat_verdict",
    event_type="VERDICT_DETERMINED",
    verdict=response.verdict,
    confidence=response.confidence,
    reasoning_preview=reasoning_preview,
    full_reasoning=response.reasoning
)
```

### Log Event Types
- `VERDICT_DETERMINATION_START`
- `VERDICT_DETERMINED`
- `REPORT_GENERATION_START`
- `REPORT_GENERATION_COMPLETE`
- `SAVE_START`
- `STATE_SAVED`
- `ERROR`

### Context Propagation
Every log includes:
- `agent`: "ReportGenerator"
- `node`: Current node name
- `session_id`: Investigation session ID (when available)

### Debug vs. Info Logging
- **Debug**: Serialization steps, prompt creation, file paths
- **Info**: Major milestones (verdict determined, report generated, files saved)
- **Error**: Exceptions, timeouts, failures

---

## Future Enhancements

### Potential Improvements

1. **Report Templates**: Configurable report formats (executive summary only, full forensic, etc.)
2. **Multi-Language Support**: Generate reports in multiple languages
3. **Confidence Calibration**: Automated confidence score validation against ground truth
4. **Report Sections Toggle**: Allow selective report section generation
5. **Streaming Reports**: Generate report incrementally as agents complete
6. **Report Diffing**: Compare reports across file versions
7. **IoC Extraction Tool**: Automated IoC extraction with STIX/TAXII export

### Known Limitations

1. **No Iterative Refinement**: Single-pass verdict and report generation (no self-critique)
2. **State Size Design**: Application designed for typical phishing/malicious PDFs (4-5 pages max), as such documents traditionally have few pages. URL investigation volume controlled by Image Analysis agent's prioritization and low priority threshold (1-2 for critical URLs only), preventing overwhelming state sizes.
3. **No Report Validation**: Generated markdown not validated for completeness

---

## Summary

The Report Generator agent serves as the capstone of PDF Hunter's analysis pipeline:

**Core Functions**:
1. **Holistic Verdict Determination**: Independent analysis of all evidence to classify threat level
2. **Comprehensive Report Synthesis**: Transform multi-domain findings into professional forensic documentation
3. **Evidence Preservation**: Persist complete investigation state for auditing and review

**Key Strengths**:
- Dual-persona design (Adjudicator + Briefer) ensures verdict integrity
- Structured output for verdict enables programmatic use
- Rich markdown reports for human comprehension
- Complete state preservation supports forensic rigor

**Integration Role**:
- Terminal agent in orchestrator graph
- Receives findings from File Analysis, Image Analysis, URL Investigation
- Produces final outputs consumed by users and downstream systems

**Technical Excellence**:
- Robust error handling with timeout protection
- Comprehensive logging for observability
- Clean separation of concerns (verdict vs. report)
- Type-safe schemas throughout

This agent represents the synthesis of all PDF Hunter capabilities into actionable intelligence.