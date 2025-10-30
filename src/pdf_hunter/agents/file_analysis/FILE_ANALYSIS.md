# File Analysis Agent - Technical Documentation

## Design Philosophy: "The Pathologist's Gaze"

### Core Philosophy

The File Analysis Agent embodies a fundamental shift from **traditional signature-based detection** to **reasoning from first principles**. Rather than functioning as a simple automated scanner, the system leverages the vast knowledge within Large Language Models to act as an **expert digital pathologist** who understands the deeper meaning behind structural features.

**Key Philosophical Principles**:

The system operates under three immutable first principles, collectively termed **"The Pathologist's Gaze"**:

1. **Autonomy is Disease**
   - *Principle*: A benign document is a passive vessel for information
   - *Implication*: Any anatomical feature that grants the ability to initiate actions without direct user command is a sign of malignancy
   - *Examples*: `/OpenAction`, `/JavaScript`, `/Launch`, `/AA`, `/EmbeddedFile`
   - *Detection Priority*: These indicators are automatically flagged for immediate investigation

2. **Deception is Confession**
   - *Principle*: A benign anatomy is transparent and forthright
   - *Implication*: Any evidence that the true nature has been obscured is a direct admission of guilt
   - *Examples*: Obfuscated streams, hidden objects, encoded payloads
   - *Investigation Focus*: The act of hiding IS the confession

3. **Incoherence is a Symptom**
   - *Principle*: A benign anatomy is simple and structurally consistent with its purpose
   - *Implication*: Complex capabilities incongruous with apparent function indicate underlying disease
   - *Examples*: Invoice with embedded JavaScript, simple form with /Launch action
   - *Analysis Method*: Context-aware anomaly detection

### Why This Matters for Academic Writing

**Differentiating Factor**: This approach moves beyond isolated indicator detection to **narrative reconstruction** of the entire attack chain. The system doesn't just find threats—it understands **why** they're threats and **how** they work together.

**LLM as Expert Mind**: By encoding forensic expertise into prompts rather than hard-coded rules, the system exhibits:
- **Contextual reasoning**: Same feature judged differently based on document type
- **Adaptive investigation**: Discovers unexpected attack patterns
- **Holistic synthesis**: Reconstructs complete pathology map, not just isolated findings

**Implementation**: All File Analysis prompts (triage, investigator, reviewer, finalizer) begin with the "Pathologist's Gaze" framing, ensuring consistent expert reasoning throughout the analysis pipeline.

## Overview

The **File Analysis Agent** serves as the **static analysis workhorse** of the pdf-hunter multi-agent pipeline. It performs deep forensic investigation of PDF internal structures without executing any content, identifying malicious indicators through intelligent triage and parallel mission-based investigations.

**Position in Pipeline**: Executes **in parallel** with Image Analysis immediately after PDF Extraction. Forms one of two parallel analysis branches that must both complete before Report Generator synthesizes findings.

**Parallel Execution Pattern**:
```
PDF Extraction
  ├─→ FILE ANALYSIS (Branch 1: Static forensics)
  └─→ Image Analysis → URL Investigation (Branch 2: Visual + link analysis)
        ↓                           ↓
        └───────────────────────────┴─→ Report Generator (waits for BOTH)
```

**Core Purpose**: Conduct comprehensive static analysis of PDF files using external forensic tools (pdfid, pdf-parser, peepdf), then orchestrate targeted deep-dive investigations through parallel investigator agents.

## Architecture

### Graph Structure

The agent uses **LangGraph** with a sophisticated multi-stage workflow that includes an investigator subgraph for parallel mission execution:

```
START
  ↓
identify_suspicious_elements (Triage)
  ↓
create_analysis_tasks
  ↓
assign_analysis_tasks ←──────┐
  ↓                           │
  [Parallel Investigator Pool]│
  ↓                           │
review_analysis_results ──────┤ (loop if new missions)
  ↓
summarize_file_analysis
  ↓
END
```

**Investigator Subgraph** (executed in parallel for each mission):
```
START
  ↓
investigation (LLM with tools) ⟷ tools (pdf-parser wrapper)
  ↓
END (returns MissionReport)
```

**Implementation**: 
- Main graph: `src/pdf_hunter/agents/file_analysis/graph.py`
- Investigator subgraph: embedded within `graph.py`

### State Management

**Main State Schema**: `FileAnalysisState` (TypedDict)

**Inputs**:
- `session_id` (str): Unique session identifier from orchestrator
- `file_path` (str): Absolute path to PDF file
- `output_directory` (str): Base output directory for artifacts
- `additional_context` (Optional[str]): **User-provided context or investigation directives**
  - Enables domain experts to guide investigation
  - Examples: "Focus on object 42", "Email attachment from suspicious sender"
  - Automatically creates `USER_DEFINED` mission when provided
  - Default: "None" (automatic threat detection only)

**Core Investigation State**:
- `structural_summary` (Dict[str, str]): Raw outputs from pdfid, pdf-parser, peepdf
- `mission_list` (List[InvestigationMission]): Master list of all missions with status tracking
- `mission_reports` (Dict[str, MissionReport]): Completed mission results indexed by mission_id
- `master_evidence_graph` (EvidenceGraph): Unified graph of all discovered evidence

**Outputs**:
- `completed_investigations` (List[dict]): Aggregated results from parallel investigators
- `file_analysis_report` (FinalReport): Comprehensive final report with verdict

**Investigator State Schema**: `InvestigatorState` (TypedDict)

**Inputs to each investigator**:
- `file_path` (str): PDF file path
- `output_directory` (str): Session output directory
- `mission` (InvestigationMission): The specific mission to investigate
- `structural_summary` (Dict[str, str]): Reference data from initial scan
- `messages` (List[AnyMessage]): LangChain message history for tool use

**Implementation**: `src/pdf_hunter/agents/file_analysis/schemas.py`

## Core Nodes

### 1. identify_suspicious_elements (Triage Node)

**Purpose**: Initial triage to identify high-signal threat indicators and generate focused investigation missions.

**Operations**:

1. **Multi-Tool Static Analysis**:
   - **pdfid**: Keyword frequency analysis for suspicious elements (/OpenAction, /JavaScript, /Launch, /AA, /EmbeddedFile, /XFA, etc.)
   - **pdf-parser**: Full statistical analysis with `-a -O` flags for object type counts and unreferenced objects
   - **peepdf**: Enhanced PDF analysis with JavaScript analysis and vulnerability detection
   - **get_xmp_metadata**: Document provenance analysis extracting creator tools, producer, and timestamps
   - All outputs stored in `structural_summary` dictionary, including XMP metadata when present

2. **LLM-Based Triage Classification**:
   - Uses `file_analysis_triage_llm` with structured output (`TriageReport`)
   - Evaluates structural_summary against threat taxonomy
   - **Classification Decision**: "innocent" or "suspicious"
   - **Reasoning**: Detailed explanation of triage decision

3. **Mission Generation**:
   - Creates `InvestigationMission` objects for each detected threat
   - **Automatic Threat Detection**: High-signal indicators automatically trigger missions
   - **User-Directed Investigation**: `additional_context` input enables custom missions
   
   **Mission Types** (based on `ThreatType` enum):
   - `OPENACTION`: Automatic execution on open
   - `LAUNCH_ACTION`: External program execution
   - `JAVASCRIPT`: Embedded JavaScript code
   - `ACROFORM`: Interactive forms
   - `EMBEDDED_FILE`: File attachments
   - `USER_DEFINED`: **User-provided investigation requests** ⭐
   - `STRUCTURAL_ANOMALY`: Malformed structures
   
   **User-Defined Missions**:
   - **Purpose**: Allow domain experts to direct investigation toward specific areas of interest
   - **Trigger**: When `additional_context` is provided (not "None")
   - **Examples**:
     - "Investigate object 42 specifically"
     - "Check the embedded file for suspicious content"
     - "Analyze the /Launch action in detail"
     - "This came from a phishing email, focus on credential harvesting"
   - **Implementation**: Triage automatically creates `mission_user_defined_001` capturing user's request
   - **Flag**: `is_user_defined: True` marks these missions for special handling
   
   **Mission Structure**:
   - `mission_id`: Unique identifier (e.g., "mission_javascript_obj_42", "mission_user_defined_001")
   - `threat_type`: ThreatType enum value
   - `entry_point_description`: Where to start investigation
   - `source_object_id`: PDF object number if applicable
   - `reasoning`: Why this mission is necessary
   - `is_user_defined`: Boolean flag for user-directed missions

**Key Technologies**:
- **pdfid.py**: Didier Stevens' PDF keyword scanner
- **pdf-parser.py**: Didier Stevens' comprehensive PDF parser
- **peepdf**: José Miguel Esparza's interactive PDF analysis tool
- **Structured LLM Output**: Pydantic `TriageReport` schema

**Implementation**: `src/pdf_hunter/agents/file_analysis/nodes.py::identify_suspicious_elements()`

### 2. create_analysis_tasks

**Purpose**: Mark new missions as "IN_PROGRESS" to prepare them for dispatch.

**Operations**:
1. Iterates through `mission_list`
2. Updates status: `NEW` → `IN_PROGRESS` for unstarted missions
3. Logs task count for tracking

**Implementation**: `src/pdf_hunter/agents/file_analysis/nodes.py::create_analysis_tasks()`

### 3. assign_analysis_tasks

**Purpose**: Dispatch missions to the parallel investigator pool using LangGraph's `Send` API.

**Operations**:

1. **Mission Filtering**:
   - Identifies missions with `status == IN_PROGRESS`
   - Excludes already completed missions (checks `completed_investigations`)

2. **Parallel Dispatch**:
   - Uses `Send` to route each mission to the `run_file_analysis` investigator wrapper
   - Each investigator receives:
     - The mission object
     - File path and output directory
     - Reference to structural_summary
     - Empty message history for tool use

3. **Routing Logic**:
   - If missions exist → dispatch to parallel investigators
   - If no missions → route directly to `review_analysis_results`

**Key Pattern**: LangGraph's `Send` API enables true parallel execution where multiple investigators run simultaneously, each with their own tool-using LLM agent.

**Implementation**: `src/pdf_hunter/agents/file_analysis/nodes.py::assign_analysis_tasks()`

### 4. run_file_analysis (Investigator Wrapper)

**Purpose**: Execute the investigator subgraph for a single mission and aggregate results.

**Workflow**:

1. **Subgraph Invocation**:
   - Calls `investigator_graph.ainvoke(state)`
   - Subgraph runs until mission completes or hits recursion limit

2. **Error Handling**:
   - Catches `GraphRecursionError` for stuck/complex missions
   - Marks mission as `BLOCKED` if recursion limit hit
   - Logs errors for debugging

3. **Result Aggregation**:
   - Wraps result in list: `{"completed_investigations": [result]}`
   - List wrapper enables LangGraph's `operator.add` aggregation
   - All parallel results automatically merged into main state

**Implementation**: `src/pdf_hunter/agents/file_analysis/graph.py::run_file_analysis()`

### 5. file_analyzer (Investigator Core)

**Purpose**: LLM-powered agent that uses pdf-parser tools to complete a mission.

**Agent Loop**:

1. **System Prompt**: Forensic pathologist persona with **ABSOLUTE SINGULAR FOCUS** constraint
   - **Critical Principle**: "You have been assigned ONE mission. You MUST NOT investigate multiple threats in parallel"
   - If agent encounters other threats (e.g., investigating `/OpenAction` but sees `/AcroForm`), it MUST:
     - Document the finding in evidence graph
     - NOT pursue the secondary threat
     - Stay focused on assigned mission only
   - **Rationale**: Prevents "Shiny Object Syndrome" where agents get distracted by secondary leads
   - Reviewer will create new missions for discovered threats based on strategic priority
2. **Tool Selection**: LLM chooses appropriate pdf-parser tool based on mission
3. **Tool Execution**: Calls tools via `inject_and_call_tools` wrapper
4. **Iterative Refinement**: Continues investigation until mission resolved
5. **Final Report**: Returns `MissionReport` with structured output

**Available Tools** (see Tools section below):
- `get_pdf_stats`: Object type statistics
- `search_pdf_content`: Keyword/regex search in objects/streams
- `get_object_content`: Retrieve specific object by ID
- `get_objects_by_type`: List all objects of given type
- `dump_object_stream`: Extract stream to file
- `parse_objstm`: Parse /ObjStm containers
- `get_object_stream_only`: Raw stream bytes as base64
- `extract_strings`: ASCII/Unicode string extraction
- File analysis tools: `identify_file_type`, `analyze_rtf_objects`, `search_file_for_pattern`, `view_full_text_file`
- Optional: `think_tool` for strategic reflection (if enabled)

**Key Features**:
- **InjectedToolArg Pattern**: File paths hidden from LLM, injected at runtime to prevent truncation errors
- **ObjStm Resolution**: Default `-O` flag ensures objects inside /ObjStm containers are accessible
- **Evidence Preservation**: All malicious artifacts saved to `{output_directory}/file_analysis/`
- **Think Tool Integration**: Strategic reflection after discoveries (optional, config-controlled)

**Output Structure**: `MissionReport`
- `mission_id`: Matches input mission
- `final_status`: RESOLVED_MALICIOUS, RESOLVED_BENIGN, or BLOCKED
- `summary_of_findings`: Human-readable summary
- `mission_subgraph`: EvidenceGraph with nodes (evidence) and edges (relationships)

**Implementation**: `src/pdf_hunter/agents/file_analysis/nodes.py::file_analyzer()`

### 6. review_analysis_results (Strategic Reviewer)

**Purpose**: Synthesize findings from completed missions, merge evidence graphs, and decide next steps.

**Operations**:

1. **Evidence Graph Merging**:
   - Collects `mission_subgraph` from each completed `MissionReport`
   - Uses `file_analysis_graph_merger_llm` with structured output (`MergedEvidenceGraph`)
   - **Why LLM-Based Merging?**
     - Parallel investigations may discover the same entities (nodes/edges) with varying levels of detail
     - Programmatic deduplication cannot assess semantic quality or completeness
     - LLM can holistically evaluate all graphs and select the most informative version of each entity
     - Example: Mission A finds "obj_4: /JavaScript" while Mission B finds "obj_4: /JavaScript with decoded payload XYZ" → LLM keeps the more complete version
   - **Deduplication Rules**:
     - Same entity (e.g., both graphs have "obj_4") → merge into one node, keeping best properties
     - Conflicting properties → keep most detailed/complete version
     - IOCs → prefer complete over partial extraction
     - Maintain all unique edges, remove exact duplicates
   - Updates `master_evidence_graph` with merged result

2. **Strategic Analysis - The Whole Picture View**:
   - **Chief Pathologist** persona with holistic perspective across all missions
   - **Critical Role**: Only agent that sees the complete investigation landscape
   - **Why Reviewer Exists** - Solving "Shiny Object Syndrome":
     - **Problem (Previous Versions)**: Individual investigators would get distracted by secondary threats
       - Example: Agent investigating `/Launch` would start pursuing `/AcroForm` findings mid-investigation
       - Resulted in unfocused, incomplete investigations and missed primary threats
     - **Solution**: Separation of concerns through architectural constraints:
       - **Investigators**: "ABSOLUTE SINGULAR FOCUS" - investigate ONLY assigned mission
       - **Reviewer**: Strategic coordinator that sees ALL evidence and decides next steps
   - **Reviewer's Mandate**:
     - Focus EXCLUSIVELY on evidence from completed `MissionReport`s and `master_evidence_graph`
     - DO NOT look for new threats in initial structural report (that's Triage's job)
     - Goal: "Resolve the threads you have already started, not create new ones from scratch"
   - **Analysis Focus**:
     - **BLOCKED missions**: Checks if other missions found missing information (passwords, keys, decoded data)
     - **RESOLVED missions**: Looks for new connections in merged graph
   - Uses `file_analysis_reviewer_llm` with structured output (`ReviewerReport`)

3. **Decision Making**:
   - **If new missions generated**: 
     - Adds to `mission_list` with status NEW
     - Routes back to `create_analysis_tasks` for next iteration
     - Logs each new follow-up mission
   - **If no new missions and all resolved**:
     - Sets `is_investigation_complete = True`
     - Routes to `summarize_file_analysis` for final report

**Key Pattern**: This creates an **iterative deepening search** where discoveries in one mission can trigger targeted follow-up missions, enabling the system to adaptively explore complex attack chains.

**Implementation**: `src/pdf_hunter/agents/file_analysis/nodes.py::review_analysis_results()`

### 7. summarize_file_analysis (Finalizer)

**Purpose**: Generate comprehensive final report with verdict and actionable intelligence.

**Operations**:

1. **Structured Report Generation**:
   - Uses `file_analysis_finalizer_llm` with structured output (`FinalReport`)
   - Inputs: Master evidence graph, all mission reports, mission list, investigation transcripts

2. **Report Components**:
   - **Classification Verdict**: "Malicious", "Suspicious", or "Benign"
   - **Confidence Score**: 0-10 scale
   - **Executive Summary**: High-level findings in plain language
   - **Attack Chain Reconstruction**: Step-by-step sequence of PDF exploitation
   - **Indicators of Compromise**: Deduplicated list of IOCs (URLs, IPs, hashes)
   - **Full Markdown Report**: Comprehensive technical analysis

3. **Evidence Preservation**:
   - Saves final state to JSON: `file_analysis_final_state_session_{session_id}.json`
   - Uses `dump_state_to_file()` for safe serialization
   - Stored in `{output_directory}/file_analysis/`

**Output**: `FinalReport` with all structured fields plus human-readable markdown

**Implementation**: `src/pdf_hunter/agents/file_analysis/nodes.py::summarize_file_analysis()`

## Tools System

### PDF Parser Tool Suite

All tools are wrappers around `pdf-parser.py` with intelligent defaults and safety features.

**Core Architecture**:
- **InjectedToolArg Pattern**: `pdf_file_path` and `output_directory` marked with `InjectedToolArg` annotation
- **Runtime Injection**: `inject_and_call_tools()` injects paths from state before ToolNode execution
- **ObjStm Resolution**: `-O` flag enabled by default via `PDFPARSER_OPTIONS` environment variable
- **Error Handling**: All tools return descriptive errors, never crash the agent

**Key Tools**:

1. **get_pdf_stats(use_objstm=True)**
   - Runs `pdf-parser --stats -O`
   - Returns object type counts, unreferenced objects, suspicious keywords
   - **Use**: First step in almost every mission

2. **search_pdf_content(search_string, in_streams=False, regex=False, ...)**
   - Searches objects or streams for IOCs
   - `--search` for objects, `--searchstream` for streams
   - `--filter` for decompressed stream search
   - **Use**: Finding specific indicators like `/JavaScript`, `/OpenAction`, URLs

3. **get_object_content(object_id, filter_stream=False)**
   - Retrieves specific object with optional stream decompression
   - Auto-filters small streams (< 100KB)
   - Auto-expands /ObjStm containers if object inside one
   - **Use**: Examining suspicious objects identified in stats/search

4. **dump_object_stream(object_id, dump_file_path, filter_stream=True)**
   - Extracts stream to file for further analysis
   - **Saved to**: `{output_directory}/file_analysis/`
   - **Use**: Preserving malicious JavaScript, embedded files, payloads

5. **parse_objstm(object_id, filtered=True)**
   - Parses /ObjStm container and shows inner objects
   - **Use**: When object yields no output due to being inside /ObjStm

6. **identify_file_type(file_path)**
   - Runs `file` command on extracted artifact
   - **Use**: First step after dumping stream to identify payload type

7. **analyze_rtf_objects(file_path)**
   - Uses `rtfobj` from oletools to analyze RTF files
   - Identifies embedded OLE objects and exploit indicators
   - **Use**: Analyzing extracted RTF payloads (CVE-2017-11882, etc.)

8. **get_xmp_metadata(pdf_file_path)**
   - Extracts XMP metadata for document provenance analysis
   - Uses InjectedToolArg pattern (file path hidden from LLM)
   - Returns creator tool, producer, timestamps, and toolkit information
   - **Use**: Detecting suspicious tool chains, rapid modifications, obfuscation patterns
   - Enables "Incoherence is a Symptom" principle application to document provenance

**Tool Manifest**: `pdf_parser_tools_manifest` provides tool descriptions for LLM prompt

**Implementation**: `src/pdf_hunter/agents/file_analysis/tools.py`

### External Analysis Tools Integration

**pdfid, pdf-parser, peepdf** are invoked via async wrappers:

```python
async def run_pdfid(pdf_filename: str) -> str
async def run_pdf_parser_full_statistical_analysis(pdf_filename: str) -> str  
async def run_peepdf(pdf_filename: str, output_directory: Optional[str]) -> str
```

**Key Feature**: peepdf automatically moves `peepdf_jserrors-*.txt` files to `{output_directory}/file_analysis/` for evidence preservation.

**Implementation**: `src/pdf_hunter/shared/analyzers/wrappers.py`

## Data Structures

### Evidence Graph System

The **Evidence Graph** is the central knowledge representation that captures all discovered evidence and relationships.

**Core Components**:

1. **EvidenceNode** (represents evidence):
   - `id`: Unique identifier (e.g., "obj_4", "art_123a6", "ioc_evil_com")
   - `node_type`: Classification ("PDFObject", "Artifact", "IOC", "File")
   - `label`: Human-readable title
   - `properties`: List of `NodeProperty` (key-value pairs)

2. **EvidenceEdge** (represents relationships):
   - `source_id`: Starting node ID
   - `target_id`: Ending node ID
   - `label`: Relationship verb ("references", "contains", "decodes_to", "downloads_from")

3. **EvidenceGraph**:
   - `nodes`: List[EvidenceNode]
   - `edges`: List[EvidenceEdge]

**Example Graph**:
```json
{
  "nodes": [
    {"id": "obj_4", "node_type": "PDFObject", "label": "/OpenAction", "properties": [...]},
    {"id": "obj_18", "node_type": "PDFObject", "label": "/JavaScript", "properties": [...]},
    {"id": "art_js_payload", "node_type": "Artifact", "label": "Decoded JavaScript", "properties": [...]}
  ],
  "edges": [
    {"source_id": "obj_4", "target_id": "obj_18", "label": "triggers"},
    {"source_id": "obj_18", "target_id": "art_js_payload", "label": "contains"}
  ]
}
```

**Implementation**: `src/pdf_hunter/agents/file_analysis/schemas.py`

### Mission System

**InvestigationMission**:
- `mission_id`: Unique identifier (format: "mission_{threat_type}_{number}")
- `threat_type`: ThreatType enum value
- `entry_point_description`: Where to start investigation
- `source_object_id`: Optional PDF object number
- `status`: MissionStatus enum value
- `reasoning`: Why this mission exists
- `is_user_defined`: Flag for user-provided context missions

**ThreatType Enum**:
- OPENACTION: Automatic execution on open
- LAUNCH_ACTION: External program execution
- JAVASCRIPT: Embedded JavaScript code
- ACROFORM: Interactive forms
- EMBEDDED_FILE: File attachments
- **USER_DEFINED**: User-provided investigation directives (created when `additional_context` is provided)
- STRUCTURAL_ANOMALY: Malformed structures

**MissionStatus Enum**:
- NEW: Not yet started
- IN_PROGRESS: Assigned to investigator
- RESOLVED_MALICIOUS: Confirmed threat
- RESOLVED_BENIGN: False positive
- BLOCKED: Needs additional information
- FAILED: Tool/agent error

**Key Feature - User-Directed Investigation**:

The `additional_context` input enables domain experts to direct the investigation system:

```python
# Automatic threat detection only
additional_context = None  # or "None"
→ Missions created for: /OpenAction, /JavaScript, /Launch, etc.

# User-directed investigation
additional_context = "Investigate object 42 specifically"
→ Additional mission created: mission_user_defined_001
→ Investigator receives directive and focuses on object 42

# Combined automatic + user-directed
additional_context = "Focus on embedded file credential harvesting"
→ Automatic missions: /OpenAction, /EmbeddedFile, /JavaScript
→ User mission: mission_user_defined_001 with credential harvesting focus
```

**Benefits**:
- ✅ Leverages domain expert knowledge
- ✅ Enables targeted investigation of specific concerns
- ✅ Combines with automatic threat detection (not replacement)
- ✅ Preserves expert intent through entire investigation pipeline

**Implementation**: `src/pdf_hunter/agents/file_analysis/schemas.py`

## LLM Configuration

The agent uses **5 specialized LLM instances**, each optimized for specific tasks. Critically, **all prompts are infused with the "Pathologist's Gaze" philosophy**, ensuring consistent expert reasoning across the entire analysis pipeline.

### Prompt Engineering Strategy

**Persona-Driven Prompts**: All system prompts begin with:
```python
"""You are Dr. Evelyn Reed, a world-class Digital Pathologist. 
Your entire worldview is defined by the "Pathologist's Gaze": 
you see a file's anatomy, not its data.

Your analysis must be guided by these core principles of pathology:
- Principle 1: Autonomy is Disease
- Principle 2: Deception is Confession  
- Principle 3: Incoherence is a Symptom
"""
```

**Why Expert Persona Matters**:
- **Primes LLM reasoning**: Activates relevant forensic knowledge
- **Consistent worldview**: All agents think like pathologists, not generic analyzers
- **First principles reasoning**: Guides decisions through philosophical lens rather than pattern matching

### Specialized LLM Instances

1. **file_analysis_triage_llm**:
   - **Task**: Initial maliciousness assessment from static scans
   - **Prompt Focus**: Apply "Autonomy is Disease" to identify high-signal threats
   - **Output**: Structured `TriageReport` with mission list
   - **Model**: GPT-4o (default) or Qwen2.5:7b (Ollama)

2. **file_analysis_investigator_llm**:
   - **Task**: Deep forensic investigation with tool use
   - **Prompt Focus**: "ABSOLUTE SINGULAR FOCUS" + first principles reasoning
   - **Output**: Tool calls + structured `MissionReport`
   - **Model**: GPT-4o (default) or Qwen2.5:7b (Ollama)

3. **file_analysis_graph_merger_llm**:
   - **Task**: Intelligent evidence graph merging
   - **Prompt Focus**: Semantic quality assessment (not just deduplication)
   - **Output**: Structured `MergedEvidenceGraph`
   - **Model**: GPT-4o (default) or Qwen2.5:7b (Ollama)

4. **file_analysis_reviewer_llm**:
   - **Task**: Strategic analysis and mission routing
   - **Prompt Focus**: "Chief Pathologist" holistic view across all evidence
   - **Output**: Structured `ReviewerReport`
   - **Model**: GPT-4o (default) or Qwen2.5:7b (Ollama)

5. **file_analysis_finalizer_llm**:
   - **Task**: Final report generation with verdict
   - **Prompt Focus**: Attack chain reconstruction from first principles
   - **Output**: Structured `FinalReport`
   - **Model**: GPT-4o (default) or Qwen2.5:7b (Ollama)

**Configuration**:
- Models defined in `src/pdf_hunter/config/models_config.py`
- Provider agnostic via LangChain's `init_chat_model()`
- Supports OpenAI, Azure OpenAI, and Ollama

**Implementation**: 
- Models: `src/pdf_hunter/config/models_config.py`
- Prompts: `src/pdf_hunter/agents/file_analysis/prompts.py`

## Execution Configuration

**Recursion Limits**:
- Main graph: 50 iterations (FILE_ANALYSIS_CONFIG)
- Investigator subgraph: 25 iterations (FILE_ANALYSIS_INVESTIGATOR_CONFIG)

**Think Tool**:
- Controlled by `THINKING_TOOL_ENABLED` flag
- When enabled, added to all investigators for strategic reflection
- Implementation: `src/pdf_hunter/shared/tools/think_tool.py`

**Logging**:
- Structured logging via loguru
- Tool usage logged at INFO level for transparency
- Investigation transcripts preserved in final state
- Setup: `src/pdf_hunter/config/logging_config.py`

**Configuration Files**:
- `src/pdf_hunter/config/__init__.py`
- `src/pdf_hunter/config/execution_config.py`
- `src/pdf_hunter/config/models_config.py`

## Key Design Patterns

### 1. InjectedToolArg Pattern

**Problem**: LLMs truncate 100+ character file paths in tool calls causing "File not found" errors.

**Solution**:
```python
from langchain_core.tools import InjectedToolArg
from typing import Annotated

@tool
def get_pdf_stats(
    use_objstm: bool = True,  # Visible to LLM
    pdf_file_path: Annotated[str, InjectedToolArg] = None  # Hidden
) -> str:
    ...

# In graph.py
async def inject_and_call_tools(state: InvestigatorState):
    for tool_call in last_message.tool_calls:
        tool_call["args"]["pdf_file_path"] = state["file_path"]
        tool_call["args"]["output_directory"] = state["output_directory"]
    ...
```

**Benefits**:
- ✅ LLM never generates file paths (no truncation)
- ✅ Reduced context window usage
- ✅ Runtime injection from state
- ✅ Simplified prompts

### 2. Parallel Mission Dispatch with Send

**Pattern**: LangGraph's `Send` API for true parallel execution

```python
def assign_analysis_tasks(state):
    missions = [m for m in state["mission_list"] if m.status == IN_PROGRESS]
    
    if missions:
        return [Send("run_file_analysis", {"mission": m, ...}) for m in missions]
    else:
        return {"next_step": "review"}
```

**Result**: Multiple investigators run simultaneously, each with independent tool-using LLM.

### 3. Iterative Deepening Search

**Pattern**: Reviewer node can generate new missions based on discoveries

```
Triage → Missions [A, B, C] → Investigate Parallel → Review
           ↑                                            ↓
           └────────────── New Missions [D, E] ─────────┘
```

**Enables**: Adaptive exploration of complex attack chains where one discovery leads to targeted follow-up.

### 4. Evidence Graph as Central Memory

**Pattern**: All discoveries stored in unified graph structure

- **Nodes**: Individual pieces of evidence (PDF objects, artifacts, IOCs)
- **Edges**: Relationships between evidence (triggers, contains, decodes_to)
- **Merge Logic**: Intelligent deduplication across parallel investigations

**Benefits**:
- Prevents redundant investigation
- Enables attack chain reconstruction
- Provides structured data for downstream agents

### 5. Architectural Solutions to Agent-Level Pathologies

The system's architecture evolved through several iterations to solve three critical agent-level problems that plagued earlier versions:

#### Problem 1: "Shiny Object Syndrome"
**Definition**: Investigators getting distracted by secondary, unrelated threats during focused investigations.

**Example**:
```
❌ Old Behavior:
Mission: Investigate /Launch action
  → Finds /Launch → starts analyzing
  → Notices /AcroForm → starts analyzing that too
  → Sees /JavaScript → pivots to JavaScript analysis
  → Result: Incomplete /Launch investigation, shallow analysis of everything
```

**Solution**: **ABSOLUTE SINGULAR FOCUS** architectural constraint

**Implementation**:
- **Investigator Level** (Tactical):
  - Rule: Investigate ONLY assigned mission
  - If other threats discovered → document in graph but DO NOT pursue
  - Prompt constraint: "You MUST NOT investigate multiple threats in parallel"
  
- **Reviewer Level** (Strategic):
  - Only agent that sees complete picture across ALL missions
  - Creates new missions for discovered secondary threats
  - Prioritizes based on strategic importance across entire investigation
  - Mandate: "Resolve threads already started, not create new ones from scratch"

**Benefits**:
- ✅ Each investigator produces focused, complete analysis
- ✅ No wasted effort on low-priority tangents
- ✅ Strategic prioritization by meta-agent with full context

#### Problem 2: "Cognitive Tunneling"
**Definition**: Single-threaded agents getting stuck on low-priority tasks while high-priority threats remain unaddressed.

**Example**:
```
❌ Old Behavior:
Single Agent: Analyze entire PDF
  → Finds /AcroForm (low priority) → spends 80% of time on forms analysis
  → Finds /OpenAction → /JavaScript (high priority) → rushed analysis in remaining 20%
  → Result: Thorough analysis of benign feature, missed critical threats
```

**Solution**: **Parallel Mission Dispatch with Priority-Based Triage**

**Implementation**:
- **Triage Node**: Identifies ALL threats and creates focused missions
- **Mission Assignment**: All high-priority missions dispatched simultaneously in parallel
- **No Sequential Bottleneck**: Multiple investigators work independently
- **Priority Encoded in Triage**: High-signal threats (/OpenAction, /JavaScript, /Launch) always generate missions

**Benefits**:
- ✅ High-priority threats get immediate, dedicated attention
- ✅ No single low-priority task can block critical analysis
- ✅ Parallel execution prevents tunnel vision

#### Problem 3: "Contextual Amnesia"
**Definition**: Earlier versions lost investigation context over time as agents progressed, leading to disconnected findings and inability to reconstruct attack chains.

**Example**:
```
❌ Old Behavior:
Mission 1: Found /Launch action (context lost after completion)
Mission 2: Found encoded payload (no memory of /Launch)
Mission 3: Found download URL (no memory of payload or /Launch)
  → Result: Three isolated findings, no attack chain reconstruction
```

**Solution**: **Persistent Master Evidence Graph as Central Memory**

**Implementation**:
- **State Schema**: `master_evidence_graph: EvidenceGraph` maintained throughout investigation
- **Graph Merging**: All mission discoveries merged into master graph by dedicated LLM
- **Relationship Preservation**: Edges capture connections between findings
- **Reviewer Access**: Strategic coordinator sees ENTIRE context across all missions
- **Comment in Code**: `# --- THE SHARED BRAIN - Curated Results ---`

**Benefits**:
- ✅ Complete investigation context preserved across all missions
- ✅ Enables attack chain reconstruction from disconnected findings
- ✅ Reviewer can identify connections (e.g., Mission B found password for Mission A's encrypted object)
- ✅ No findings lost or isolated

**Example Flow with Solutions**:
```
✅ Current Architecture:

Triage → Generates missions: [/Launch (P1), /JavaScript (P1), /AcroForm (P3)]

Parallel Investigators:
  Investigator A: /Launch → thorough analysis → adds to master graph
  Investigator B: /JavaScript → finds payload → adds to master graph
  Investigator C: /AcroForm → benign finding → adds to master graph

Reviewer:
  → Sees master graph with ALL context
  → Notes: /Launch triggers /JavaScript (connection discovered)
  → Creates Mission D: Investigate relationship between obj_4 and obj_18
  → Result: Complete attack chain reconstructed
```

**Combined Impact**: These three architectural solutions work together to create a system that maintains focus (no distraction), prioritizes correctly (no tunneling), and preserves context (no amnesia) throughout complex investigations.

## CLI Usage

**Run with defaults**:
```bash
uv run python -m pdf_hunter.agents.file_analysis.graph
```

**Analyze specific file**:
```bash
uv run python -m pdf_hunter.agents.file_analysis.graph --file suspicious.pdf
```

**Custom output directory**:
```bash
uv run python -m pdf_hunter.agents.file_analysis.graph --output ./analysis
```

**Add user context for automatic investigation**:
```bash
# General context about source
uv run python -m pdf_hunter.agents.file_analysis.graph --context "Email attachment from unknown sender"

# Specific investigation directive
uv run python -m pdf_hunter.agents.file_analysis.graph --context "Investigate object 42 specifically"

# Domain expert guidance
uv run python -m pdf_hunter.agents.file_analysis.graph --context "Focus on embedded file - suspected credential harvester"
```

**Custom session ID**:
```bash
uv run python -m pdf_hunter.agents.file_analysis.graph --session test_001
```

**Enable debug logging**:
```bash
uv run python -m pdf_hunter.agents.file_analysis.graph --debug
```

**Combined example with all options**:
```bash
uv run python -m pdf_hunter.agents.file_analysis.graph \
  --file suspicious.pdf \
  --output ./my_analysis \
  --context "Phishing email, check for credential forms" \
  --session phishing_001 \
  --debug
```

**Implementation**: `src/pdf_hunter/agents/file_analysis/cli.py`

## Integration with Pipeline

**Inputs from PDF Extraction**:
- `file_path`: Path to PDF
- `session_id`: Session identifier
- `output_directory`: Base output directory
- (PDF extraction results not directly used, but available in session directory)

**Outputs to Downstream Agents**:
- `file_analysis_report` (FinalReport): Comprehensive analysis with verdict
- `master_evidence_graph` (EvidenceGraph): Unified evidence graph
- `mission_reports` (Dict): Individual mission findings
- Extracted artifacts in `{output_directory}/file_analysis/`

**Used by**:
- **Report Generator**: Synthesizes findings from all agents
- **URL Investigation**: References file analysis findings for context

## Critical Implementation Notes

1. **Never use localStorage/sessionStorage** - not supported in LangGraph
2. **All artifacts saved to disk** - Evidence preservation protocol
3. **ObjStm resolution is default** - Ensures inner objects accessible
4. **Tool paths injected at runtime** - Never generated by LLM
5. **Async everywhere** - Non-blocking for LangGraph Studio compatibility
6. **State serialization for debugging** - Final state always saved to JSON
7. **Structured logging** - Investigation transparency and audit trail

## Testing

**Test Files**:
- `tests/agents/test_file_analysis_errors.py`
- Sample PDFs: `tests/assets/pdfs/`

**Test PDFs**:
- `87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf`: Known malicious
- `test_mal_one.pdf`: Test malware sample
- `hello_qr.pdf`, `hello_qr_and_link.pdf`: Benign test cases

---

## Summary

The File Analysis Agent represents a paradigm shift in PDF threat detection through its unique combination of architectural sophistication and philosophical grounding.

### Key Research Contributions

**1. First Principles Reasoning Architecture**
- Moves beyond signature-based detection to **expert-level reasoning**
- Embodies "Pathologist's Gaze" philosophy across all analysis stages
- LLM as expert mind rather than pattern matcher

**2. Solutions to Fundamental Agent-Level Pathologies**

Three critical architectural innovations solve problems that plagued earlier multi-agent systems:

- **Solving "Shiny Object Syndrome"**: 
  - Problem: Agents distracted by secondary, unrelated threats
  - Solution: ABSOLUTE SINGULAR FOCUS constraint + Strategic Reviewer coordination
  - Impact: Focused, complete investigations with intelligent prioritization

- **Solving "Cognitive Tunneling"**: 
  - Problem: Single-threaded agents stuck on low-priority tasks
  - Solution: Parallel Mission Dispatch with priority-based triage
  - Impact: High-priority threats get immediate, dedicated attention

- **Solving "Contextual Amnesia"**: 
  - Problem: Investigation context lost over time
  - Solution: Persistent Master Evidence Graph as central memory
  - Impact: Complete attack chain reconstruction from disconnected findings

**3. Sophisticated Multi-Agent Coordination**
- **Intelligent Triage**: LLM-based classification from first principles
- **Parallel Investigation**: Multiple specialized investigators with singular focus
- **User-Directed Investigation**: Domain experts can guide investigation via `additional_context` input
- **Evidence Graph**: Unified knowledge representation enabling narrative reconstruction
- **Iterative Deepening**: Adaptive exploration based on strategic discoveries
- **Strategic Review**: Meta-agent with holistic view coordinates investigation flow

**4. Novel Design Patterns**
- **Separation of Concerns**: Tactical investigators + strategic reviewer
- **InjectedToolArg**: Elegant solution to LLM path truncation
- **LLM-Based Merging**: Semantic quality assessment for graph deduplication
- **Think Tool Integration**: Systematic reflection for enhanced decision-making

**5. Forensic Rigor**
- Tool mastery: pdf-parser wrapper suite with intelligent defaults
- Evidence preservation: All artifacts saved to disk
- Structured logging: Complete investigation audit trail
- Reproducible analysis: Deterministic with saved state

### Academic Significance

This architecture enables the system to handle complex, multi-stage PDF attacks that would require multiple manual investigation passes by expert analysts. The system doesn't just detect threats—it **understands** them, **reasons** about them, and **reconstructs** the complete attack narrative through first principles thinking embedded in every prompt.

The "Pathologist's Gaze" philosophy transforms the LLM from a generic text processor into a domain expert capable of contextual reasoning, adaptive investigation, and holistic synthesis—capabilities that distinguish this approach from traditional rule-based or ML classification systems.