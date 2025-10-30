# URL Investigation Agent - Technical Documentation

## Overview

**Purpose**: The URL Investigation Agent performs live, interactive forensic investigation of URLs extracted from PDF documents using browser automation. It acts as a web detective, following redirect chains, analyzing page content, and determining whether URLs are benign, suspicious, or malicious.

**Location**: `src/pdf_hunter/agents/url_investigation/`

**Agent Type**: Two-stage LangGraph workflow with parallel execution
- **Main Graph**: URL filtering and parallel dispatch
- **Investigator Subgraph**: Per-URL investigation with tool loops (ReAct pattern)

---

## Architecture

### 1. Two-Level Graph Structure

**Main Graph** (`URLInvestigationState`):
```
START → filter_high_priority_urls → route_url_analysis → [conduct_link_analysis (parallel)] → save_url_analysis_state → END
```

**Investigator Subgraph** (`URLInvestigatorState`):
```
START → investigate_url → should_continue → [execute_browser_tools → investigate_url (loop)] OR [analyze_url_content → END]
```

### 2. Key Design Patterns

**Parallel URL Investigation**:
- Uses LangGraph's `Send` API for true parallelization
- Each URL gets isolated browser session and output directory
- Independent investigation logs per URL

**ReAct Agent Loop**:
- LLM analyzes state → decides on tool calls → executes tools → loops
- Observation → Orient → Decide → Act cycle
- Continues until investigation complete or recursion limit reached

**Session Isolation**:
- Each URL gets unique `task_id = f"url_{abs(hash(url_task.url))}"`
- MCP creates separate browser contexts per task
- Screenshots/traces saved to `{output_directory}/url_investigation/task_{task_id}/`

---

## Node Functions

### Main Graph Nodes

#### 1. filter_high_priority_urls

**Purpose**: Filter URLs based on priority threshold and update status tracking.

**Implementation**:
```python
async def filter_high_priority_urls(state: URLInvestigationState):
    """Filter URLs by priority and update mission status."""
```

**Process**:
1. Extracts URLs from `visual_analysis_report.prioritized_urls`
2. Filters by priority threshold (≤ `URL_INVESTIGATION_PRIORITY_LEVEL` from config, default: 5)
3. Updates `URLMissionStatus`:
   - High priority (≤ threshold) → `IN_PROGRESS`
   - Low priority (> threshold) → `NOT_RELEVANT`
4. Returns list of high priority URLs for investigation

**Configuration Reference**:
```python
from pdf_hunter.config.execution_config import URL_INVESTIGATION_PRIORITY_LEVEL
# URLs with priority <= URL_INVESTIGATION_PRIORITY_LEVEL are investigated
```

**Status Enum**:
- `NEW`: Initial state from image analysis
- `IN_PROGRESS`: Currently being analyzed
- `COMPLETED`: Successfully analyzed
- `FAILED`: Analysis failed (technical errors or inaccessible)
- `NOT_RELEVANT`: Low priority, not selected for analysis

**File**: `src/pdf_hunter/agents/url_investigation/nodes.py`

---

#### 2. route_url_analysis

**Purpose**: Parallel dispatch router using LangGraph's Send API.

**Implementation**:
```python
def route_url_analysis(state: URLInvestigationState):
    """Dispatch URL analysis tasks in parallel using Send."""
```

**Dispatch Logic**:
```python
for url_task in state["high_priority_urls"]:
    yield Send(
        "conduct_link_analysis",
        {
            "url_task": url_task,
            "output_directory": state["output_directory"],
            "session_id": state["session_id"]
        }
    )
```

**Pattern**: Each `Send` creates independent investigator subgraph execution

**File**: `src/pdf_hunter/agents/url_investigation/nodes.py`

---

#### 3. conduct_link_analysis (Wrapper)

**Purpose**: Execute investigator subgraph and handle errors gracefully.

**Implementation**:
```python
async def conduct_link_analysis(state: dict):
    """Wrapper for investigator subgraph execution."""
    result = await link_investigator_graph.ainvoke(state)
    return {
        "link_analysis_final_reports": [result["link_analysis_final_report"]],
        "errors": result.get("errors", [])
    }
```

**Error Handling**:
- Catches `GraphRecursionError` when investigation hits recursion limit
- Creates failed `URLAnalysisResult` with `verdict="Inaccessible"`
- Marks URL with `mission_status="failed"`
- Logs recursion limit context for debugging

**Recursion Limit**: 20 steps (configured in `URL_INVESTIGATION_INVESTIGATOR_CONFIG`)

**File**: `src/pdf_hunter/agents/url_investigation/graph.py`

---

#### 4. save_url_analysis_state

**Purpose**: Persist complete investigation results to file.

**Implementation**:
```python
async def save_url_analysis_state(state: URLInvestigationState):
    """Save URL investigation state to JSON file."""
```

**Output**:
- File: `{output_directory}/url_investigation/url_investigation_state_session_{session_id}.json`
- Contains: All URL analysis results, errors, and metadata
- Uses safe serialization for Pydantic models

**File**: `src/pdf_hunter/agents/url_investigation/nodes.py`

---

### Investigator Subgraph Nodes

#### 5. investigate_url (Core Investigation Node)

**Purpose**: LLM-powered investigation coordinator that decides next actions.

**Implementation**:
```python
async def investigate_url(state: URLInvestigatorState):
    """LLM analyzes state and decides on tool usage."""
```

**Process**:

1. **Session Setup**:
   - Generates unique `task_id = f"url_{abs(hash(url_task.url))}"`
   - Gets MCP session: `session = await get_mcp_session(task_id, session_output_dir)`
   - Loads MCP browser tools + `domain_whois` tool
   - Optionally adds `think_tool` if `THINKING_TOOL_ENABLED=True`

2. **Tool Binding**:
   ```python
   model_with_tools = url_investigation_investigator_llm.bind_tools(all_tools)
   ```

3. **Investigation Initiation** (First Call):
   - Creates initial briefing with URL context
   - Includes extraction method and flagging reason
   - Emphasizes PDF-sourced URL nature (social engineering context)
   - Sends system prompt + initial briefing to LLM

4. **Investigation Continuation** (Subsequent Calls):
   - Uses existing message history
   - LLM reviews previous observations and tool results
   - Decides next action based on investigation progress

**Output**: Returns updated `investigation_logs` with LLM response

**File**: `src/pdf_hunter/agents/url_investigation/nodes.py`

---

#### 6. execute_browser_tools

**Purpose**: Execute tool calls from LLM decision.

**Implementation**:
```python
async def execute_browser_tools(state: URLInvestigatorState):
    """Execute tool calls using browser automation through MCP."""
```

**Process**:

1. **Tool Call Extraction**:
   - Gets last message from `investigation_logs`
   - Extracts `tool_calls` attribute
   - Validates tool calls exist

2. **Session Reuse**:
   - Uses same `task_id` as `investigate_url`
   - Gets cached MCP session for consistency
   - Reloads tools fresh for each execution

3. **Sequential Execution**:
   ```python
   for tool_call in tool_calls:
       if tool_name == "domain_whois":
           observation = await asyncio.to_thread(tool.invoke, tool_call["args"])
       elif tool_name == "think_tool":
           observation = await asyncio.to_thread(tool.invoke, tool_call["args"])
       else:
           # MCP browser tools
           observation = await tool.ainvoke(tool_call["args"])
   ```

4. **Tool Message Creation**:
   - Creates `ToolMessage` objects with observations
   - Includes `tool_call_id` for LangChain message matching

**Error Handling**:
- Wraps each tool call in try-except
- Returns error messages as tool observations
- Continues execution even if one tool fails

**Output**: Returns `ToolMessage` list appended to `investigation_logs`

**File**: `src/pdf_hunter/agents/url_investigation/nodes.py`

---

#### 7. should_continue (Router)

**Purpose**: Conditional routing between tool execution and analysis.

**Implementation**:
```python
def should_continue(state: URLInvestigatorState) -> Literal["execute_browser_tools", "analyze_url_content"]:
    """Determine whether to continue with tool execution or analysis."""
```

**Routing Logic**:
- If last message has `tool_calls` → route to `"execute_browser_tools"`
- If no tool calls → route to `"analyze_url_content"` (investigation complete)

**File**: `src/pdf_hunter/agents/url_investigation/nodes.py`

---

#### 8. analyze_url_content (Analyst Synthesis)

**Purpose**: Synthesize investigation findings into structured report.

**Implementation**:
```python
async def analyze_url_content(state: URLInvestigatorState):
    """Synthesizes all evidence and assembles final report."""
```

**Process**:

1. **Analyst LLM Setup**:
   ```python
   analyst_llm = url_investigation_analyst_llm.with_structured_output(AnalystFindings)
   ```

2. **Prompt Construction**:
   - Formats initial briefing as JSON
   - Formats complete investigation log as JSON
   - Includes current datetime for context

3. **Findings Generation**:
   - LLM reviews entire investigation transcript
   - Extracts key evidence: final URL, WHOIS record, screenshots
   - Determines verdict: Benign/Suspicious/Malicious/Inaccessible
   - Assigns confidence score (0.0-1.0)
   - Writes executive summary

4. **Status Update**:
   - `mission_status="completed"` → `URLMissionStatus.COMPLETED`
   - `mission_status="failed"` → `URLMissionStatus.FAILED`

5. **Report Assembly**:
   ```python
   URLAnalysisResult(
       initial_url=url_task,
       full_investigation_log=[...],
       analyst_findings=analyst_findings
   )
   ```

**Timeout Protection**: Uses `asyncio.wait_for(timeout=LLM_TIMEOUT_TEXT)` to prevent infinite hangs

**File**: `src/pdf_hunter/agents/url_investigation/nodes.py`

---

## Data Structures

### State Schemas

**URLInvestigationState** (Main Graph):
```python
class URLInvestigationState(TypedDict):
    # Inputs
    output_directory: str
    session_id: str
    visual_analysis_report: NotRequired[ImageAnalysisReport]
    high_priority_urls: List[PrioritizedURL]
    
    # Outputs
    link_analysis_final_reports: Annotated[List[URLAnalysisResult], operator.add]
    errors: Annotated[List[str], operator.add]
```

**URLInvestigatorState** (Investigator Subgraph):
```python
class URLInvestigatorState(TypedDict):
    # Inputs
    url_task: PrioritizedURL
    output_directory: str
    session_id: str
    
    # Intermediate
    investigation_logs: Annotated[Sequence[BaseMessage], operator.add]
    
    # Outputs
    errors: Annotated[List[str], operator.add]
    link_analysis_final_report: URLAnalysisResult
```

**File**: `src/pdf_hunter/agents/url_investigation/schemas.py`

---

### Data Models

**AnalystFindings** (Pydantic):
```python
class AnalystFindings(BaseModel):
    final_url: str  # Final destination URL reached
    verdict: Literal["Benign", "Suspicious", "Malicious", "Inaccessible"]
    confidence: float  # 0.0 to 1.0
    summary: str  # Executive summary of investigation
    detected_threats: List[str]
    domain_whois_record: Optional[str]
    screenshot_paths: List[str]
    mission_status: Literal["completed", "failed"]
```

**URLAnalysisResult** (Pydantic):
```python
class URLAnalysisResult(BaseModel):
    initial_url: PrioritizedURL  # Original URL from visual analysis
    full_investigation_log: List[dict]  # Complete message history
    analyst_findings: AnalystFindings  # Synthesized conclusions
```

**File**: `src/pdf_hunter/agents/url_investigation/schemas.py`

---

## Tools

### 1. MCP Playwright Tools

**Source**: Loaded dynamically from `@playwright/mcp` server via `langchain-mcp-adapters`

**Available Tools**:
- `browser_navigate`: Navigate to URL
- `browser_click`: Click element on page
- `browser_fill_form`: Fill form fields
- `browser_take_screenshot`: Capture tactical (base64) or forensic (file) screenshots
- `browser_evaluate`: Execute JavaScript (must use arrow function syntax)
- `browser_network_requests`: Inspect network activity
- Additional: `browser_scroll`, `browser_hover`, `browser_drag`, etc.

**Critical Syntax**:
```javascript
// CORRECT - arrow function
{"function": "() => document.body.innerText"}
{"function": "() => document.title"}

// INCORRECT - will fail
{"function": "return document.body.innerText;"}
{"function": "document.body.innerText"}
```

**Session Management**:
- Each URL gets isolated browser context
- Screenshots auto-saved to `task_{task_id}` directory
- Trace files captured for debugging

---

### 2. domain_whois Tool

**Purpose**: Perform WHOIS lookup on root domain for identity verification.

**Implementation**:
```python
@tool
def domain_whois(domain: str) -> str:
    """Performs WHOIS lookup on root domain."""
    w = whois.whois(domain)
    # Returns formatted summary with:
    # - Domain name
    # - Registrar
    # - Creation date
    # - Expiration date
    # - Name servers
```

**Special Handling**:
- Platform domains (vercel.app, herokuapp.com, github.io, netlify.app, etc.)
  - Returns warning about disposable subdomains
- Missing records: Returns "No WHOIS record found"

**Usage**: Executed via `asyncio.to_thread()` to prevent blocking

**Library**: `python-whois` package

**File**: `src/pdf_hunter/agents/url_investigation/tools.py`

---

### 3. think_tool (Optional)

**Purpose**: Strategic reflection for investigation quality enhancement.

**Configuration**: Enabled via `THINKING_TOOL_ENABLED = True` in `src/pdf_hunter/config/execution_config.py`

**Usage Pattern**:
- After significant discoveries
- Before major decisions
- At investigation transitions

**Logging**: Reflections logged at INFO level for visibility

**File**: `src/pdf_hunter/shared/tools/think_tool.py`

---

## Prompt Engineering Strategy

### Design Philosophy

The URL Investigation agent's prompts represent a **key implementation innovation** in applying structured reasoning frameworks to adversarial web analysis. Unlike generic browser automation prompts, these prompts encode domain-specific investigative methodologies.

---

### Investigator Prompt: OODA Loop Framework

**Cognitive Architecture**: Military decision-making framework (Observe → Orient → Decide → Act)

**Why OODA Loop?**
- **Prevents Cognitive Gaps**: Forces systematic observation before action
- **Handles Dynamic Threats**: Adversaries use multi-step evasion (redirects, fake pages)
- **Explicit Evidence Collection**: Tactical + forensic screenshots at each step
- **Adaptability**: Loop repeats until investigation complete, not fixed sequence

**Novel Aspects**:

1. **Practical Real-World Instructions**:
   - Cookie consent handling (explicit, mandatory)
   - Arrow function syntax requirement for `browser_evaluate`
   - Distinction between tactical screenshots (base64 for analysis) vs forensic screenshots (file for evidence)

2. **Strategic Reflection Integration**:
   ```
   "After each significant discovery or when you complete a full investigation loop, 
   use the think_tool to strategically assess your progress"
   ```
   - Explicit guidance on *when* to reflect (most prompts just list tools)
   - Four reflection questions provided for consistency
   - Improves investigation quality through deliberate pause-and-reflect

3. **Context-Aware Framing**:
   ```
   "The URL you are investigating was extracted from a PDF document (not found on a website)"
   ```
   - Primes agent to expect social engineering tactics
   - Different threat model than general web browsing
   - Emphasizes attack chain analysis

4. **Scenario-Based Guidance**:
   - Not just tool descriptions, but *when* and *why* to use each tool
   - Handles edge cases explicitly (cookie dialogs, phishing forms, redirect chains)
   - Balances structure with adaptability ("not an exhaustive list")

---

### Analyst Prompt: Separation of Concerns

**Persona**: Web Forensics Analyst (synthesis only, no tools)

**Design Rationale**:

**Problem**: Investigator logs contain noisy, iterative tool calls
**Solution**: Dedicated analyst reviews complete transcript post-investigation

**Key Constraints**:

1. **Ground Truth Enforcement**:
   ```
   "You must base your entire report *only* on the provided Investigator Log. 
   Do not infer or hallucinate actions that were not taken."
   ```
   - Prevents analyst from inventing evidence
   - Ensures traceability to actual observations

2. **Schema Adherence**:
   - Output must be valid `AnalystFindings` Pydantic model
   - No commentary outside JSON structure
   - Structured output binding enforces this at runtime

3. **Evidence Extraction Focus**:
   - Final URL (after redirects)
   - WHOIS record
   - Screenshot paths
   - Detected threats

---

### Prompt Engineering Outcomes

**Measurable Benefits**:

1. **Reduced Hallucination**: Explicit "ground truth" constraints prevent fabricated evidence
2. **Consistent Investigation Pattern**: OODA loop ensures no skipped steps
3. **Real-World Robustness**: Cookie dialog handling critical for modern web
4. **Quality Enhancement**: Strategic reflection improves verdict accuracy

**Technical Correctness**:
- Arrow function syntax requirement prevents actual tool failures
- Screenshot type distinction matches MCP Playwright capabilities
- WHOIS guidance aligned with `python-whois` library behavior

---

### Comparison to Generic Browser Automation Prompts

**Generic Approach**:
```
"You have access to browser tools. Navigate to the URL and determine if it's malicious."
```

**PDF Hunter Approach**:
- Structured cognitive framework (OODA)
- Explicit evidence collection protocol
- Context-aware threat model (PDF-sourced URLs)
- Practical failure mode handling (cookie dialogs)
- Strategic reflection points
- Two-stage analysis (investigation → synthesis)

**Result**: More systematic, reproducible, and robust URL analysis

---

### System Prompts

#### Investigator System Prompt

**File**: `src/pdf_hunter/agents/url_investigation/prompts.py` (`URL_INVESTIGATION_INVESTIGATOR_SYSTEM_PROMPT`)

**Full Structure**:

1. **Mission Context**: PDF-sourced URL, social engineering awareness
2. **OODA Loop Definition**: Four-step investigation cycle
3. **Tactical Guidance**: Scenario-specific tool usage
4. **Completion Criteria**: Three investigation end states

**Critical Instructions**:
- First action: `browser_navigate` to target URL
- After page state changes: Restart OBSERVE step
- Cookie dialogs: Mandatory dismissal before analysis
- Suspicious domains: WHOIS verification required
- Phishing forms: Fill with fake credentials to trace endpoint

**Hard Limits** (Resource Management):
- **Browser Action Budget**:
  - Standard pages (simple content): 6-8 actions maximum
  - Multi-step flows (redirects, login sequences): 10-12 actions maximum
  - **Absolute hard limit**: 15 browser actions
- **Action Counting Rules**:
  - Actions that COUNT: `browser_navigate`, `browser_click`, `browser_fill_form` (state-changing interactions)
  - Actions that DO NOT count: `browser_take_screenshot`, `browser_evaluate`, `browser_network_requests`, `domain_whois`, `think_tool` (observation/analysis tools)
- **Rationale**: Prevents excessive investigation loops while allowing thorough analysis of complex attack chains

---

#### Analyst System Prompt

**File**: `src/pdf_hunter/agents/url_investigation/prompts.py` (`URL_INVESTIGATION_ANALYST_SYSTEM_PROMPT`)

**Four Core Rules**:

1. **Ground Truth is the Log**: No inference beyond provided evidence
2. **Synthesize and Extract**: Read, summarize, extract key data
3. **Extract Key Data**: Final URL, WHOIS, screenshots, conclusion
4. **Adhere to Schema**: Valid `AnalystFindings` JSON only

**No Tool Access**: Analyst cannot execute tools, only review transcript

---

## MCP Integration

### Session Management

**Implementation**: `src/pdf_hunter/shared/utils/mcp_client.py`

**Architecture**:
```python
get_mcp_session(task_id, base_output_dir)
  ↓
get_mcp_client_async(task_id, base_output_dir)
  ↓
MultiServerMCPClient(config)
```

**Configuration**:
```python
{
    "playwright": {
        "command": "npx",
        "args": [
            "@playwright/mcp@latest",
            "--headless",
            f"--output-dir={task_output_dir}",
            "--save-trace",
            "--isolated"
        ],
        "transport": "stdio"
    }
}
```

**Output Directory Structure**:
```
{session_output_dir}/
└── url_investigation/
    └── task_url_{hash}/
        ├── screenshots/
        ├── traces/
        └── ...
```

---

### Session Isolation

**Problem**: Parallel URL investigations need independent browser contexts

**Solution**:
1. Generate unique `task_id` per URL: `f"url_{abs(hash(url_task.url))}"`
2. Each task gets dedicated MCP client with isolated output directory
3. Browser contexts don't interfere with each other

**Session Reuse**:
- `investigate_url` and `execute_browser_tools` use same `task_id`
- MCP session cached in `_session_managers` dict
- Tools reloaded fresh each time for safety

**Cleanup**: `await cleanup_mcp_session()` called by orchestrator on shutdown

---

## Configuration

### Execution Config

**Location**: `src/pdf_hunter/config/execution_config.py`

```python
# Main graph recursion limit
URL_INVESTIGATION_CONFIG = {
    "run_name": "URL Investigation Agent",
    "recursion_limit": 25  # Multiple URLs in parallel
}

# Investigator subgraph recursion limit  
URL_INVESTIGATION_INVESTIGATOR_CONFIG = {
    "run_name": "Browser Investigation Tools",
    "recursion_limit": 20  # investigate_url → browser_tools loops
}

# Priority threshold for investigation
URL_INVESTIGATION_PRIORITY_LEVEL = 5  # URLs with priority ≤ this value are investigated
```

### LLM Config

**Location**: `src/pdf_hunter/config/models_config.py`

```python
# Investigator LLM (tool-using)
url_investigation_investigator_llm = init_chat_model(
    model=MODEL_NAME,
    temperature=0.0,
    # Tool binding for MCP browser tools + domain_whois
)

# Analyst LLM (structured output)
url_investigation_analyst_llm = init_chat_model(
    model=MODEL_NAME,
    temperature=0.0,
    # Pydantic schema binding for AnalystFindings
)
```

**Model Configuration**: 
- Robust and configurable via centralized configuration
- Supports multiple LLM providers through unified interface
- Temperature set to 0.0 for deterministic, consistent analysis

---

## Integration Points

### Input from Image Analysis

**Required State Fields**:
```python
{
    "output_directory": str,  # Session output directory
    "session_id": str,        # Session identifier
    "visual_analysis_report": ImageAnalysisReport  # Contains prioritized_urls
}
```

**PrioritizedURL Structure**:
```python
{
    "url": str,              # The URL to investigate
    "page_number": int,      # PDF page where found
    "priority": int,         # 1 (highest) to 5 (lowest)
    "reason": str,           # Why flagged (from visual analysis)
    "source_context": str,   # Context around URL
    "extraction_method": str,  # How extracted (annotation/text/QR)
    "mission_status": URLMissionStatus  # NEW, IN_PROGRESS, COMPLETED, FAILED
}
```

---

### Output to Report Generator

**Provided State Fields**:
```python
{
    "link_analysis_final_reports": List[URLAnalysisResult],
    "errors": List[str]
}
```

**URLAnalysisResult Contents**:
- Initial URL context and flagging reason
- Complete investigation message history
- Final verdict with confidence
- Detected threats list
- Screenshot file paths
- WHOIS record summary

**State File**:
- Location: `{output_directory}/url_investigation/url_investigation_state_session_{session_id}.json`
- Format: Safe JSON serialization of all Pydantic models
- Purpose: Debugging, audit trail, report generation

---

## Error Handling

### Investigation-Level Errors

**Recursion Limit Exceeded**:
- Caught in `conduct_link_analysis` wrapper
- Creates failed `URLAnalysisResult` with `verdict="Inaccessible"`
- Summary explains investigation complexity/loop
- Marks URL with `mission_status="failed"`

**Tool Execution Errors**:
- Each tool call wrapped in try-except
- Error returned as tool observation
- LLM sees error and can retry or conclude

**LLM Timeout Protection**:
- Analyst call wrapped in `asyncio.wait_for(timeout=LLM_TIMEOUT_TEXT)`
- Prevents infinite hangs on synthesis
- Returns error with timeout context

---

### Node-Level Error Handling

**Pattern** (all nodes):
```python
async def node_function(state):
    try:
        # Validate required inputs
        if not state.get("required_field"):
            raise ValueError("required_field is required")
        
        # Node logic
        ...
        
        return {"output": result}
    
    except Exception as e:
        error_msg = f"Error in node_function: {e}"
        logger.error(error_msg, agent="URLInvestigation", node="node_name", exc_info=True)
        return {"errors": [error_msg]}
```

**Benefits**:
- No crashes from missing state fields
- Errors aggregated in state for debugging
- Partial analysis completion possible

---

## Key Technologies

### Browser Automation
- **@playwright/mcp**: MCP server providing Playwright browser tools
- **langchain-mcp-adapters**: Bridges MCP tools to LangChain format
- **Node.js**: Required for Playwright MCP server execution

### Domain Analysis
- **python-whois**: WHOIS lookup library for domain verification

### LLM Integration
- **LangChain**: Tool binding and message management
- **Pydantic**: Structured output schemas for consistent data

### Async Architecture
- **asyncio**: Non-blocking LLM calls and tool execution
- **asyncio.to_thread**: Wraps blocking WHOIS calls
- **async/await**: Prevents LangGraph Studio blocking errors

---

## Development & Testing

### Testing Strategy

**Unit Tests**: Not yet implemented (focus was on integration testing)

**Integration Testing**:
- Test with known phishing URLs
- Verify multi-step redirect following
- Validate WHOIS lookups on recent domains
- Check screenshot capture and trace generation

**Test Assets**:
- Located in `tests/assets/pdfs/`
- PDFs with embedded malicious/suspicious URLs
- Used for end-to-end orchestrator testing

---

### Notebook Development

**Location**: `notebooks/development/link_analysis_agent.ipynb`

**Purpose**:
- Prototype investigation workflows
- Test MCP tool integration
- Debug prompt engineering
- Analyze investigation logs

**Pattern**:
- Load sample URL from test PDF
- Execute investigator subgraph step-by-step
- Inspect message history and tool outputs
- Iterate on prompts and logic

---

## Why This Design?

### Parallel Execution

**Problem**: Sequential URL investigation too slow for PDFs with many links

**Solution**: LangGraph's `Send` API for true parallelization
- Each URL investigated independently
- Results aggregated via `operator.add`
- Session isolation prevents interference

**Trade-off**: Higher resource usage, but faster overall analysis

---

### ReAct Pattern

**Problem**: Static tool sequence can't adapt to URL behavior

**Solution**: LLM decides next action based on observations
- Handles redirects dynamically
- Adapts to page content (login forms, downloads, etc.)
- Terminates when investigation complete

**Benefit**: Robust handling of unpredictable attack chains

---

### Two-Stage Analysis

**Problem**: Investigation logs too noisy for direct synthesis

**Solution**: Separate investigator (collect evidence) from analyst (synthesize)
- Investigator focuses on data collection
- Analyst reviews complete transcript
- Clear separation of concerns

**Benefit**: Higher quality findings with clean structured output

---

## Performance Considerations

### Timeouts

**Analyst LLM**: `LLM_TIMEOUT_TEXT` seconds (default: 60s)
- Prevents infinite hangs on synthesis
- Rare in practice (analyst simple task)

**Tool Execution**: No explicit timeout
- MCP handles browser timeouts internally
- Individual tool failures logged but don't block

---

### Session Cleanup

**When**: Orchestrator shutdown
**How**: `await cleanup_mcp_session()`
**Purpose**: Close browser contexts, free resources

---

## Logging

### Investigation Events

**Key Log Points**:
- Investigation start (INFO): URL, priority
- Tool execution start (INFO): Tool name, count
- Tool execution complete (INFO): Result count
- Analysis complete (INFO): Verdict, confidence, summary preview
- Recursion limit (WARNING): URL, limit context
- Errors (ERROR): Full exception context

**Log Format**:
```python
logger.info(
    f"🔍 Starting URL investigation: {url}",
    agent="URLInvestigation",
    node="investigate_url",
    event_type="INVESTIGATION_START",
    url=url,
    priority=priority
)
```

---

### Strategic Reflection Logging

**When `THINKING_TOOL_ENABLED=True`**:
```python
logger.info(
    f"💭 Strategic Reflection: {reflection_text}",
    agent="URLInvestigation",
    node="execute_browser_tools",
    event_type="STRATEGIC_REFLECTION"
)
```

**Purpose**: Track investigation quality and decision-making

---

## Critical Implementation Details

### 1. Browser Tool Syntax

**CRITICAL**: LLM must generate arrow functions for `browser_evaluate`

**Correct**:
```json
{"function": "() => document.body.innerText"}
```

**Incorrect** (will fail):
```json
{"function": "document.body.innerText"}
{"function": "return document.body.innerText;"}
```

**Mitigation**: System prompt explicitly specifies arrow function requirement

---

### 2. Cookie Consent Handling

**Problem**: Cookie dialogs block content access

**Solution**: System prompt instructs immediate dismissal
- Look for "Accept", "Agree", "OK", "Allow" buttons
- Click before content analysis
- Document dismissal in logs

**Importance**: CRITICAL for successful investigations

---

### 3. Session Consistency

**Pattern**: Both `investigate_url` and `execute_browser_tools` use same `task_id`

**Why**: Browser state persists across tool calls
- Navigation in investigate_url affects execute_browser_tools
- Screenshots capture current page state
- WHOIS results reference current domain

**Implementation**: Hash URL to generate deterministic task_id

---

## Future Enhancements (Not Implemented)

1. **Loop Prevention**: Use `URLMissionStatus` to skip completed URLs in reruns
2. **Retry Logic**: Retry failed URLs with different strategies
3. **Dynamic Priority Adjustment**: Increase priority based on findings
4. **Interactive Mode**: Human-in-the-loop for complex investigations

---

*This documentation reflects the actual implementation as verified in the codebase.*