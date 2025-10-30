# Orchestrator - Technical Documentation

## Overview

**Purpose**: The Orchestrator serves as the master coordination layer for the PDF-Hunter multi-agent system. It manages the complete analysis workflow, coordinates five specialized agents, handles parallel execution patterns, and aggregates results into a unified final state.

**Location**: `src/pdf_hunter/orchestrator/`

**Type**: LangGraph StateGraph with hybrid execution patterns (sequential + parallel)

**Core Responsibility**: Orchestrate a sophisticated 5-agent pipeline from PDF ingestion to final report generation, managing state flow, session lifecycle, and error aggregation.

---

## Architecture & Design Philosophy

### Multi-Agent Coordination Pattern

The Orchestrator implements a **hybrid execution pattern** that balances sequential dependencies with parallel opportunities:

1. **Sequential Foundation**: Critical path requires ordered execution (PDF → Extraction → Analysis → Report)
2. **Parallel Opportunities**: Independent analyses run concurrently when data dependencies allow
3. **Dependency Management**: Explicit edges encode agent dependencies in the graph structure
4. **State Aggregation**: LangGraph's `operator.add` automatically merges parallel results

### Three Core Principles

The orchestration strategy embodies the system's threat detection philosophy:

1. **Autonomy is Disease**: Any automatic action capability (e.g., /OpenAction, /JavaScript) triggers prioritized investigation
2. **Deception is Confession**: Visual and structural inconsistencies are treated as evidence of malicious intent
3. **Incoherence is a Symptom**: Cross-page and cross-modal incoherence escalates suspicion

---

## Graph Structure

### Execution Flow

```
START
  ↓
PDF Extraction (Session creation, image/URL extraction)
  ├─→ File Analysis (Static PDF analysis, parallel missions)
  └─→ Image Analysis (Visual deception detection)
        ↓
      URL Investigation (Browser automation, parallel URL analysis)
        ↓
      [File Analysis + URL Investigation] → Report Generator (Synthesis, verdict)
        ↓
       END
```

### Node Definitions

**File**: `src/pdf_hunter/orchestrator/graph.py`

```python
orchestrator_builder = StateGraph(
    OrchestratorState, 
    input_schema=OrchestratorInputState
)

orchestrator_builder.add_node("PDF Extraction", preprocessing_graph)
orchestrator_builder.add_node("File Analysis", static_analysis_graph)
orchestrator_builder.add_node("Image Analysis", visual_analysis_graph)
orchestrator_builder.add_node("URL Investigation", link_analysis_graph)
orchestrator_builder.add_node("Report Generator", report_generator_graph)
```

### Edge Topology

**Sequential Edges**:
```python
orchestrator_builder.add_edge(START, "PDF Extraction")
orchestrator_builder.add_edge("PDF Extraction", "File Analysis")
orchestrator_builder.add_edge("PDF Extraction", "Image Analysis")
orchestrator_builder.add_edge("Image Analysis", "URL Investigation")
orchestrator_builder.add_edge("Report Generator", END)
```

**Join Edge** (Barrier Synchronization):
```python
orchestrator_builder.add_edge(
    ["File Analysis", "URL Investigation"],  # Both must complete
    "Report Generator"
)
```

### Parallelism Analysis

**Parallel Execution Window**:
- **File Analysis** and **Image Analysis** run concurrently after PDF Extraction
- Both consume outputs from PDF Extraction (images, URLs, metadata)
- No data dependencies between them

**Sequential Dependency**:
- **URL Investigation** depends on **Image Analysis** completing
- Reason: Image Analysis prioritizes URLs (assigns priority 1-5) which URL Investigation filters

**Synchronization Barrier**:
- **Report Generator** waits for both **File Analysis** and **URL Investigation**
- Ensures complete evidence collection before final synthesis

---

## State Management

### State Schema

**File**: `src/pdf_hunter/orchestrator/schemas.py`

```python
class OrchestratorState(TypedDict):
    # --- Initial User Inputs ---
    file_path: str
    output_directory: str
    number_of_pages_to_process: int
    pages_to_process: Optional[List[int]]
    additional_context: NotRequired[Optional[str]]
    session_id: NotRequired[Optional[str]]
    
    pdf_hash: Optional[PDFHashData]
    page_count: Optional[int]
    
    # --- Results from PDF Extraction Agent ---
    extracted_images: List[ExtractedImage]
    extracted_urls: List[ExtractedURL]
    
    # --- Results from Image Analysis Agent ---
    visual_analysis_report: NotRequired[ImageAnalysisReport]
    
    # --- Results from File Analysis Agent ---
    structural_summary: Dict[str, str]
    master_evidence_graph: NotRequired[EvidenceGraph]
    triage_classification_decision: NotRequired[str]
    triage_classification_reasoning: NotRequired[str]
    static_analysis_final_report: NotRequired[FinalReport]
    
    # --- Results from URL Investigation Agent ---
    link_analysis_final_reports: Annotated[List[URLAnalysisResult], operator.add]
    
    # --- Results from Report Generator Agent ---
    final_report: NotRequired[str]
    final_verdict: NotRequired[FinalVerdict]
    
    # --- Global Error Tracking ---
    errors: Annotated[List[list], operator.add]
```

### Input State Schema

```python
class OrchestratorInputState(TypedDict):
    file_path: str
    output_directory: NotRequired[Optional[str]]
    number_of_pages_to_process: int
    additional_context: NotRequired[Optional[str]]
    session_id: NotRequired[Optional[str]]
```

**Design Rationale**:
- Minimal input requirements (only `file_path` and `number_of_pages_to_process` mandatory)
- Optional `session_id` allows external session management (e.g., API server pre-generates)
- Optional `output_directory` defaults to `output/` in CLI
- Optional `additional_context` provides human-in-the-loop intelligence

### State Aggregation Patterns

**Additive List Aggregation**:
```python
link_analysis_final_reports: Annotated[List[URLAnalysisResult], operator.add]
errors: Annotated[List[list], operator.add]
```

**Mechanism**: 
- LangGraph automatically appends to lists annotated with `operator.add`
- Parallel URL investigations return individual `URLAnalysisResult` objects
- Orchestrator aggregates into single `link_analysis_final_reports` list
- No manual reducer needed

**Singleton Overwrites**:
- Fields like `visual_analysis_report`, `static_analysis_final_report` are singleton
- Last write wins (no conflict since only one agent writes each field)

---

## Agent Coordination

### Agent 1: PDF Extraction

**Purpose**: Safe artifact extraction without PDF content execution

**Inputs**: 
- `file_path`, `output_directory`, `number_of_pages_to_process`
- `session_id` (optional, auto-generated if missing)

**Outputs**:
- `session_id`: Format `{sha1}_{YYYYMMDD}_{HHMMSS}`
- `output_directory`: Session-specific directory created
- `pdf_hash`: SHA1 and MD5 hashes
- `page_count`: Total pages in PDF
- `extracted_images`: List of `ExtractedImage` with pHash-based naming
- `extracted_urls`: URLs from annotations, text content, and XMP metadata with coordinates and source attribution

**Special Behavior**:
- Creates session directory structure: `{output_directory}/{session_id}/`
- Generates session ID if not provided (enables idempotent reruns with same ID)
- Detects QR codes and extracts embedded URLs
- Extracts XMP metadata URLs for document provenance analysis

### Agent 2: File Analysis (Parallel with Image Analysis)

**Purpose**: Static PDF structure analysis with parallel mission-based investigations

**Inputs**:
- `file_path`, `session_id`, `output_directory`
- `additional_context` (optional)
- `structural_summary` (from PDF Extraction metadata)

**Outputs**:
- `structural_summary`: pdfid, pdf-parser, peepdf, and XMP metadata outputs
- `triage_classification_decision`: Initial threat classification
- `triage_classification_reasoning`: LLM explanation
- `master_evidence_graph`: Unified evidence graph from all missions
- `static_analysis_final_report`: Final structured report

**Execution Pattern**:
- Triage Node → Assign Missions → Parallel Investigators → Review → Report
- Uses `Send` API for true parallel mission execution
- Supports iterative deepening (reviewer can spawn new missions)

### Agent 3: Image Analysis (Parallel with File Analysis)

**Purpose**: Visual deception detection and URL prioritization

**Inputs**:
- `extracted_images`: Page images from PDF Extraction
- `extracted_urls`: URLs to contextualize and prioritize (including XMP metadata URLs)

**Outputs**:
- `visual_analysis_report`:
  - Overall verdict/confidence
  - Per-page analysis
  - Prioritized URLs (1=highest, 5=lowest priority)
  - Deception tactics detected
  - Document provenance assessment (for page 0 XMP metadata URLs)

**Critical Function**: URL prioritization feeds into URL Investigation filtering, including metadata URLs for tool chain coherence analysis

### Agent 4: URL Investigation (Sequential after Image Analysis)

**Purpose**: Live browser automation for URL reconnaissance

**Inputs**:
- `visual_analysis_report.prioritized_urls`: URLs with priority levels
- `session_id`, `output_directory`: Session context

**Outputs**:
- `link_analysis_final_reports`: List of `URLAnalysisResult` (aggregated via `operator.add`)

**Filtering Logic**:
- Only investigates URLs with priority ≤ `URL_INVESTIGATION_PRIORITY_LEVEL` (default: 5)
- Updates `mission_status`:
  - High priority → `IN_PROGRESS` → `COMPLETED`/`FAILED`
  - Low priority → `NOT_RELEVANT`

**Execution Pattern**:
- Filter high-priority URLs → Route to parallel investigators
- Each URL gets isolated browser session
- MCP tools: navigate, screenshot, analyze DOM, follow redirects

### Agent 5: Report Generator (Barrier after File + URL Analysis)

**Purpose**: Final report synthesis and threat verdict

**Inputs**: Complete orchestrator state (all prior agent outputs)

**Outputs**:
- `final_verdict`: Structured verdict (threat level, confidence, IOCs)
- `final_report`: Markdown forensic report

**Execution Pattern**:
1. Determine threat verdict (structured output)
2. Generate Markdown report (narrative synthesis)
3. Save JSON state + Markdown report to disk

**Why Sequential Order**: Verdict determined from raw data analysis, then documented in report (prevents circular reasoning)

---

## Session Management

### Session ID Format

**Pattern**: `{sha1_hash}_{YYYYMMDD}_{HHMMSS}`

**Example**: `a94a8fe5ccb19ba61c4c0873d391e987982fbbd3_20250125_143022`

**Generation Logic** (in PDF Extraction):
```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
session_id = f"{sha1_hash}_{timestamp}"
```

**Benefits**:
- **Uniqueness**: SHA1 + timestamp ensures no collisions
- **Traceability**: File hash enables deduplication detection
- **Sortability**: Timestamp enables chronological ordering
- **Idempotency**: Same file + explicit session ID = reproducible runs

### Directory Structure

**Root Output Directory**: `output/` (configurable via CLI `--output`)

**Session Directory**: `output/{session_id}/`

**Agent Subdirectories**:
```
output/{session_id}/
├── pdf_extraction/
│   ├── page_1_{phash}.png
│   ├── page_2_{phash}.png
│   └── extracted_urls.json
├── file_analysis/
│   ├── mission_reports/
│   ├── evidence_graphs/
│   └── final_state.json
├── image_analysis/
│   └── visual_analysis_report.json
├── url_investigation/
│   ├── task_{url_hash}/
│   │   ├── screenshots/
│   │   └── traces/
│   └── url_analysis_results.json
├── report_generator/
│   ├── final_state_session_{session_id}.json
│   └── final_report_session_{session_id}.md
├── analysis_report_session_{session_id}.json  # Top-level state dump
└── session.log  # Structured logging output
```

### Session Lifecycle

**Phase 1: Initialization** (PDF Extraction)
- Generate or accept `session_id`
- Create session directory: `mkdir -p {output_directory}/{session_id}`
- Reconfigure logging to add session-specific log file

**Phase 2: Analysis** (All Agents)
- Each agent creates its subdirectory
- Agents write intermediate outputs to session directory
- Structured logs written to `session.log` (JSON Lines)

**Phase 3: Finalization** (Report Generator + Orchestrator)
- Report Generator saves final state to `report_generator/final_state_session_{session_id}.json`
- Orchestrator saves aggregated state to `analysis_report_session_{session_id}.json`
- Markdown report saved to `report_generator/final_report_session_{session_id}.md`

---

## Logging & Error Handling

### Logging Architecture

**Library**: Loguru with custom configuration

**File**: `src/pdf_hunter/config/logging_config.py`

**Log Destinations**:
1. **Console** (INFO or DEBUG based on `--debug` flag)
2. **Session Log** (`{output_directory}/{session_id}/session.log`)
3. **JSON Lines** format for structured logging

**Reconfiguration Pattern**:
```python
# Initial setup (no session context)
setup_logging(debug_to_terminal=args.debug)

# After PDF extraction creates session
async for event in orchestrator_graph.astream(input):
    if event.get('session_id') and not session_id:
        session_id = event['session_id']
        output_directory = event['output_directory']
        
        # Reconfigure to add session-specific log file
        setup_logging(
            session_id=session_id,
            output_directory=output_directory,
            debug_to_terminal=args.debug
        )
```

**Rationale**: Session ID is created during runtime (by PDF Extraction), so logging configuration must be updated mid-execution to add the session-specific log file.

### Error Aggregation

**Global Error Tracking**:
```python
errors: Annotated[List[list], operator.add]
```

**Pattern**: All agents append errors to this shared list using LangGraph's additive aggregation.

**Error Handling in Agents**:
- Wrap agent execution in try-catch
- Log errors with full stack traces
- Append to `errors` list with context
- Continue execution (partial success model)

**Example** (from URL Investigation):
```python
try:
    result = await investigator_graph.ainvoke(state)
except GraphRecursionError as e:
    logger.error(f"Recursion limit hit for URL: {url}", exc_info=True)
    errors.append({
        "agent": "URL Investigation",
        "url": url,
        "error": str(e),
        "status": "recursion_limit"
    })
    # Return partial result with 'Inaccessible' verdict
```

### MCP Session Cleanup

**Pattern**: Always cleanup MCP browser sessions in finally block

```python
try:
    async for event in orchestrator_graph.astream(input):
        final_state = event
finally:
    from ..shared.utils.mcp_client import cleanup_mcp_session
    await cleanup_mcp_session()
```

**Rationale**: Playwright browser sessions must be explicitly closed to prevent resource leaks.

---

## CLI Interface

### Arguments

**File**: `src/pdf_hunter/orchestrator/cli.py`

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--file` | `-f` | `hello_qr_and_link.pdf` | PDF file to analyze |
| `--pages` | `-p` | `4` | Number of pages to process |
| `--output` | `-o` | `output` | Base output directory |
| `--context` | `-c` | `None` | Additional context about PDF |
| `--debug` | - | `False` | Enable debug logging to terminal |

### Path Resolution

**Logic**:
- If absolute path provided → use directly
- If relative path → search in `tests/assets/pdfs/`

**Example**:
```bash
# Relative path (looks in tests/assets/pdfs/)
uv run python -m pdf_hunter.orchestrator.graph --file test_mal_one.pdf

# Absolute path
uv run python -m pdf_hunter.orchestrator.graph --file /home/user/suspicious.pdf
```

### Usage Examples

**Basic Usage** (defaults):
```bash
uv run python -m pdf_hunter.orchestrator.graph
# Analyzes hello_qr_and_link.pdf, 4 pages, output to output/
```

**Custom File + Pages**:
```bash
uv run python -m pdf_hunter.orchestrator.graph --file test_mal_one.pdf --pages 2
```

**With Context + Debug**:
```bash
uv run python -m pdf_hunter.orchestrator.graph \
  --file suspicious.pdf \
  --pages 1 \
  --context "Email attachment from unknown sender" \
  --debug
```

**Custom Output Directory**:
```bash
uv run python -m pdf_hunter.orchestrator.graph \
  --file test.pdf \
  --output ./investigation_results
```

---

## Integration Points

### API Server Integration

**File**: `src/pdf_hunter/api/server.py`

**Pattern**: API pre-generates session ID, then invokes orchestrator

```python
async def run_pdf_analysis(session_id: str, pdf_path: str, max_pages: int):
    # Session ID already created by API endpoint
    output_directory = str(Path("output") / session_id)
    
    initial_state: OrchestratorInputState = {
        "file_path": pdf_path,
        "output_directory": output_directory,
        "number_of_pages_to_process": max_pages,
        "session_id": session_id  # Pre-generated
    }
    
    final_result = await orchestrator_graph.ainvoke(initial_state)
```

**Benefits**:
- API can track session status before analysis starts
- Session-specific log streaming available immediately
- Supports server-sent events (SSE) for real-time log streaming

### LangGraph Platform Deployment

**File**: `langgraph.json`

```json
{
  "dependencies": ["."],
  "graphs": {
    "orchestrator": "pdf_hunter.orchestrator.graph:orchestrator_graph",
    "file_analysis": "pdf_hunter.agents.file_analysis.graph:static_analysis_graph",
    "pdf_extraction": "pdf_hunter.agents.pdf_extraction.graph:preprocessing_graph",
    "url_investigation": "pdf_hunter.agents.url_investigation.graph:link_analysis_graph"
  },
  "env": ".env"
}
```

**Deployment**:
```bash
langgraph up
```

**Access**: All graphs (orchestrator + individual agents) available via LangGraph Studio API

---

## Configuration

### Recursion Limits

**File**: `src/pdf_hunter/config/execution_config.py`

```python
ORCHESTRATOR_CONFIG = {
    "run_name": "PDF Hunter Orchestrator",
    "recursion_limit": 30
}
```

**Rationale**:
- Orchestrator coordinates 5 agents sequentially/parallel
- Each agent may have multiple internal steps
- 30 steps allows sufficient coordination overhead
- Prevents infinite loops in case of graph cycles

**Agent-Specific Limits**:
- PDF Extraction: 10 (simple linear workflow)
- File Analysis: 25 (multiple investigation missions)
- Image Analysis: 15 (per-page analysis)
- URL Investigation: 25 (multiple URL analysis)
- Report Generator: 10 (linear workflow)

### LangGraph Configuration Application

```python
orchestrator_graph = orchestrator_builder.compile()
orchestrator_graph = orchestrator_graph.with_config(ORCHESTRATOR_CONFIG)
```

**Applied Settings**:
- `run_name`: Displayed in LangGraph Studio
- `recursion_limit`: Maximum graph traversal steps
- `checkpointer`: (Optional) For persistence and human-in-the-loop

---

## State Serialization

### Serialization Utility

**File**: `src/pdf_hunter/shared/utils/serializer.py`

**Function**: `serialize_state_safely(state: dict) -> dict`

**Handles**:
- Pydantic models → `.model_dump()`
- Nested structures → Recursive serialization
- Non-serializable objects → Fallback to `str()`
- Binary data → Base64 encoding
- Datetime objects → ISO format strings

### Final State Persistence

**Location**: `{output_directory}/{session_id}/analysis_report_session_{session_id}.json`

**Saved By**: Orchestrator CLI after graph completion

```python
# Convert to JSON-serializable format
serializable_state = serialize_state_safely(final_state)

# Save with pretty formatting
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(serializable_state, f, indent=2, ensure_ascii=False)
```

**Use Cases**:
- **Debugging**: Inspect complete state at any point
- **Auditing**: Forensic review of analysis decisions
- **Reprocessing**: Load state to generate alternative reports
- **Testing**: Validate agent outputs against expected state

---

## Key Design Decisions

### 1. Hybrid Execution Pattern

**Decision**: Mix of sequential and parallel agent execution

**Rationale**:
- **Sequential** where dependencies exist (PDF → Analysis → Report)
- **Parallel** where independence allows (File Analysis || Image Analysis)
- **Balance** performance with correctness

**Implementation**: LangGraph edge topology + barrier synchronization

### 2. Session ID Generation in PDF Extraction

**Decision**: Session ID created by first agent (PDF Extraction), not Orchestrator

**Rationale**:
- Requires PDF hash calculation (part of PDF Extraction's job)
- Enables file-based idempotency (same file + same explicit ID = same session)
- PDF Extraction already handles file I/O, natural place for session initialization

**Consequence**: Logging must be reconfigured mid-execution when session ID becomes available

### 3. Additive State Aggregation

**Decision**: Use `operator.add` annotation for list fields that aggregate across parallel nodes

**Rationale**:
- Eliminates need for manual reducer nodes
- LangGraph automatically merges parallel results
- Simplifies graph structure (fewer nodes)

**Fields Using This Pattern**:
- `link_analysis_final_reports` (multiple parallel URL investigations)
- `errors` (errors from any agent/node)

### 4. No Output State Schema

**Decision**: Commented out `OrchestratorOutputState` in schemas

```python
# class OrchestratorOutputState(TypedDict):
#     final_verdict: NotRequired[FinalVerdict]
```

**Rationale**:
- Full state contains more information than just final verdict
- Debugging/auditing requires complete state
- Output schema would require duplication or filtering
- Downstream consumers (API, Report Generator) access full state

### 5. Barrier Synchronization for Report Generator

**Decision**: Report Generator waits for both File Analysis AND URL Investigation

```python
orchestrator_builder.add_edge(
    ["File Analysis", "URL Investigation"],
    "Report Generator"
)
```

**Rationale**:
- Report needs complete evidence from both structural and web-based analysis
- URL Investigation depends on Image Analysis (prioritization)
- File Analysis independent of Image Analysis (can run parallel)
- Barrier ensures all evidence collected before synthesis

### 6. Streaming State with Reconfiguration

**Decision**: Use `astream(stream_mode="values")` and reconfigure logging mid-execution

**Rationale**:
- Session ID unknown at orchestrator start
- Logging needs session context for file output
- Streaming allows reacting to state changes (session creation)
- Alternative (pre-generate ID in orchestrator) would duplicate PDF hash logic

---

## Error Handling Patterns

### Partial Success Model

**Philosophy**: System continues execution even if individual components fail

**Example**: URL Investigation recursion limit
```python
try:
    result = await investigator_graph.ainvoke(state)
except GraphRecursionError:
    # Mark as failed but continue
    result = URLAnalysisResult(
        url=url,
        verdict="Inaccessible",
        mission_status="failed",
        error="Recursion limit exceeded"
    )
```

**Benefits**:
- Partial results better than no results
- Enables forensic review of successful portions
- Supports iterative debugging (fix one failure at a time)

### Structured Error Tracking

**Pattern**: Errors stored with context, not just messages

```python
errors.append({
    "agent": "URL Investigation",
    "node": "investigate_url",
    "url": url,
    "error": str(e),
    "timestamp": datetime.now().isoformat(),
    "stack_trace": traceback.format_exc()
})
```

**Benefits**:
- Root cause analysis (which agent failed?)
- Error correlation (multiple errors same root cause?)
- Debugging context (what was being processed?)

---

## Testing & Usage

### Unit Testing

**Not Implemented Yet**

**Recommended Structure**:
```python
# tests/orchestrator/test_orchestrator_graph.py
import pytest
from pdf_hunter.orchestrator.graph import orchestrator_graph

@pytest.mark.asyncio
async def test_orchestrator_basic_flow():
    input_state = {
        "file_path": "tests/assets/pdfs/hello_qr_and_link.pdf",
        "number_of_pages_to_process": 1
    }
    
    result = await orchestrator_graph.ainvoke(input_state)
    
    assert result["session_id"] is not None
    assert result["final_report"] is not None
    assert result["final_verdict"] is not None
```

### Integration Testing

**Manual Testing Pattern**:
```bash
# Test benign PDF
uv run python -m pdf_hunter.orchestrator.graph \
  --file hello_qr_and_link.pdf \
  --pages 1 \
  --debug

# Test malicious PDF
uv run python -m pdf_hunter.orchestrator.graph \
  --file test_mal_one.pdf \
  --pages 2 \
  --debug

# Test with context
uv run python -m pdf_hunter.orchestrator.graph \
  --file suspicious.pdf \
  --context "Received in phishing campaign email" \
  --debug
```

**Validation**:
1. Check `session.log` for errors
2. Inspect `analysis_report_session_{session_id}.json` for completeness
3. Review `final_report_session_{session_id}.md` for coherence
4. Verify all agent subdirectories created

### LangGraph Studio Testing

**Launch**:
```bash
langgraph up
```

**Access**: `http://localhost:8000`

**Features**:
- Visual graph execution
- Step-by-step state inspection
- Breakpoints and human-in-the-loop
- Thread management for concurrent runs

---

## Future Enhancements

### Known Limitations

1. **No State Pruning**: Complete state passed between agents (can be large)
2. **No Rollback**: Cannot undo agent execution (no transactional semantics)
3. **Limited Error Recovery**: Partial success model, but no retry logic
4. **Synchronous Barriers**: Report Generator must wait for all upstream agents (no early termination on high-confidence verdict)

---

## Summary

The Orchestrator is a **sophisticated multi-agent coordination layer** that:

✅ **Manages 5 specialized agents** in a hybrid sequential/parallel workflow
✅ **Handles session lifecycle** from PDF ingestion to final report generation  
✅ **Aggregates results** using LangGraph's state management primitives
✅ **Tracks errors globally** with partial success model
✅ **Provides CLI and API interfaces** for flexible deployment
✅ **Enables observability** through structured logging and state serialization
✅ **Supports parallelism** where data dependencies allow (File + Image Analysis)
✅ **Implements barrier synchronization** for complete evidence collection before reporting

The orchestrator embodies the **coordination logic** that transforms five independent agent capabilities into a **cohesive threat analysis pipeline**, balancing performance, correctness, and debuggability.