# PDF Hunter AI Agent Instructions

## Project Overview

PDF Hunter is a multi-agent AI framework for PDF threat hunting built with **Python 3.11+** and **LangGraph**. The system orchestrates 5 specialized agents through a sophisticated pipeline that analyzes potentially malicious PDFs and generates comprehensive security reports.

## Core Architecture Principles

### Essential Patterns
- **LangGraph State Management**: All agents use `TypedDict` schemas with `Annotated[List[T], operator.add]` for additive list aggregation
- **Session-Based Organization**: Every analysis creates a `{sha1}_{timestamp}` session with dedicated output directories
- **Agent Specialization**: Each agent has dedicated LLM instances optimized for specific tasks (triage, investigation, synthesis)
- **Safe Serialization**: Use `serialize_state_safely()` from `shared/utils/serializer.py` for debugging state dumps

### State Schema Pattern
```python
from typing_extensions import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    errors: Annotated[List[str], operator.add]  # Standard error aggregation
    # Agent-specific fields...
```

### Strategic Reflection Tool Integration
- **Think Tool**: Systematic strategic reflection during investigation workflows
- **Configuration**: Controlled via `THINKING_TOOL_ENABLED` flag in `config/execution_config.py`
- **Usage Pattern**: Agents use think_tool after significant discoveries and at key decision points
- **Purpose**: Enhances investigation quality through deliberate pause-and-reflect methodology
- **Implementation**: LangChain tool with automatic integration into agent tool manifests

## Key Commands & Workflows

### Development Commands
```bash
# Primary development workflow
uv sync --group dev           # Install with Jupyter support

# Run complete pipeline with CLI arguments
uv run python -m pdf_hunter.orchestrator.graph --file tests/assets/pdfs/test_mal_one.pdf --debug
uv run python -m pdf_hunter.orchestrator.graph --file /path/to/pdf --pages 3 --context "Suspicious email attachment"

# Individual agent testing with CLI
uv run python -m pdf_hunter.agents.pdf_extraction.graph --file tests/assets/pdfs/hello_qr_and_link.pdf
uv run python -m pdf_hunter.agents.image_analysis.graph --file /path/to/pdf --debug
uv run python -m pdf_hunter.agents.file_analysis.graph --file /path/to/pdf --session test_session_001
uv run python -m pdf_hunter.agents.url_investigation.graph --url "https://example.com" --url "https://suspicious.site"
uv run python -m pdf_hunter.agents.report_generator.graph --state /path/to/state.json

# LangGraph Platform deployment
langgraph up                  # Deploy all graphs via API

# Notebook development
jupyter lab notebooks/development/
```

### CLI Architecture
Each agent and the orchestrator have a dedicated `cli.py` module for command-line interface:
- **Location**: `src/pdf_hunter/{orchestrator|agents/*}/cli.py`
- **Pattern**: `parse_args()` function returns arguments, `main()` async function executes graph
- **Invocation**: `if __name__ == "__main__": asyncio.run(main())`
- **Path Resolution**: Supports both absolute and relative paths with automatic project root calculation

**Common CLI Arguments:**
- `--file PATH`: PDF file to analyze (supports relative/absolute paths)
- `--pages N`: Number of pages to process (default varies by agent)
- `--output DIR`: Output directory for results (default: project_root/output)
- `--debug`: Enable debug-level logging to terminal
- `--context TEXT`: Additional context about the PDF (orchestrator only)

**Agent-Specific Arguments:**
- `--session ID`: Session identifier for file_analysis
- `--url URL`: URL to investigate (can be specified multiple times for url_investigation)
- `--state PATH`: Path to state JSON file for report_generator
- `--search-dir DIR`: Directory to search for state files (report_generator)

**Help Text:**
All CLI modules provide comprehensive help with examples:
```bash
uv run python -m pdf_hunter.orchestrator.graph --help
uv run python -m pdf_hunter.agents.pdf_extraction.graph --help
```

### Model Configuration
- **Default**: GPT-4o via `openai_config` in `config/models_config.py`
- **Enterprise**: Azure OpenAI via `azure_openai_config`
- **Local**: Ollama (disabled by default) - dual model setup with text/vision specialization
- Switch providers by updating LLM initializations in `config/models_config.py`

## Agent Architecture

### Orchestrator (`src/pdf_hunter/orchestrator/`)
- **Workflow**: pdf_extraction → {file_analysis || image_analysis} → url_investigation → report_generator
- **State Aggregation**: Uses `operator.add` for collecting agent results
- **Session Management**: Auto-generates session IDs and directory structures

### Agent Specialization Patterns
- **PDF Extraction**: Pure utility (no LLM) - image extraction, URL/QR detection
- **File Analysis**: Multi-tool scanning + mission-based parallel investigations with strategic reflection
- **Image Analysis**: VDA (Visual Deception Analyst) persona for UI/UX security analysis
- **URL Investigation**: Browser automation via MCP Playwright integration with strategic reflection
- **Report Generator**: Executive report synthesis and final verdict generation

### Enhanced Investigation Features
- **Strategic Reflection**: All investigative agents integrate think_tool for systematic decision-making
- **Improved Logging**: Tool execution elevated to INFO level for better investigation transparency
- **Enhanced Recursion Limits**: Increased to 25 steps for tool-using agents to accommodate strategic thinking
- **Configuration Control**: Think tool usage controlled via `THINKING_TOOL_ENABLED` flag

## Critical Development Patterns

### Async Programming Pattern
- **Node Functions**: All agent node functions must be async (use `async def function_name`)
- **LLM Invocation**: Always use `await llm.ainvoke()` instead of `llm.invoke()`
- **File Operations**: Wrap synchronous I/O in `asyncio.to_thread(os.makedirs, path, exist_ok=True)`
- **State Serialization**: Use `await dump_state_to_file(state, path)` for state persistence
- **Subprocess**: Wrap subprocess calls in `asyncio.to_thread` to prevent blocking
- **MCP Integration**: Use async patterns for MCP client and browser automation
- **Non-Blocking I/O**: Ensure all I/O operations are non-blocking for LangGraph Studio compatibility

### URL Status Tracking System
URLs flow through a sophisticated status management system:
```python
# URLMissionStatus enum progression
NEW → IN_PROGRESS → {COMPLETED | FAILED | NOT_RELEVANT}
```
- Image analysis generates `PrioritizedURL` objects with contextual ranking
- URL investigation filters by priority (≤5 = analyzed, >5 = skipped)
- Status prevents duplicate analysis and enables loop prevention

### MCP Integration
- **Browser Automation**: `shared/utils/mcp_client.py` for Playwright MCP server
- **Browser Tool Syntax**: Use arrow functions for browser_evaluate: `() => document.body.innerText` (NOT `return document.body.innerText;`)
- **Session Isolation**: Task-specific directories under session paths
- **Tool Binding**: URL investigation agent uses MCP tools for web reconnaissance
- **Auto-Directory Creation**: MCP Playwright automatically creates `task_url_{task_id}` directories - DO NOT manually create them

### Critical Fixes & Patterns (October 2025)

**LLM Output Escaping for String Formatting (October 2025):**
- **Issue**: LLM-generated content containing `{`, `}`, `<`, `>` causes crashes in `.format()` calls and Loguru logger
- **Root Cause**: Python's `.format()` interprets `{}` as placeholders; Loguru's colorizer interprets `<>` as markup tags
- **Fix Pattern**: Escape braces and tags before formatting or logging:
  ```python
  # Escape before .format()
  safe_json = json.dumps(data).replace('{', '{{').replace('}', '}}')
  prompt = template.format(data=safe_json)
  
  # Escape before logger calls (prevents colorizer errors)
  safe_text = llm_output.replace('{', '{{').replace('}', '}}').replace('<', '{{').replace('>', '}}')
  logger.info(f"Result: {safe_text}", agent="Agent", node="node")
  ```
- **Applies To**: All LLM outputs before `.format()` calls; Playwright errors before logging
- **Critical Locations**: Mission descriptions, evidence graphs, error messages, HTML in Playwright errors

**Session-Specific File Paths (October 2025):**
- **Issue**: Decoded/extracted files saved to `/tmp` or `/private/tmp` instead of session directory
- **Root Cause**: Tools lacked `output_directory` parameter; prompts didn't specify full paths
- **Fix Pattern**:
  1. Add `output_directory` parameter to tools that write temp files (`hex_decode`, `b64_decode`)
  2. Pass `output_directory` through state to all investigator nodes
  3. Update prompts with explicit path examples: `"{output_directory}/file_analysis/obj_18_malicious.js"`
  4. Ensure `file_analysis/` subdirectory created early in workflow
- **Benefits**: All forensic artifacts preserved in session directory for audit trail

**Context Overflow Prevention (October 2025):**
- **Issue**: Large decompressed streams (>1MB) caused `context_length_exceeded` errors
- **Root Cause**: `get_object_content` auto-filtered large streams, returning full decompressed content to LLM
- **Fix Pattern**:
  ```python
  # Check compressed stream size BEFORE filtering
  stream_size = int(length_match.group(1))
  MAX_FILTER_SIZE = 100000  # 100KB
  if stream_size > MAX_FILTER_SIZE:
      return metadata_only  # Don't decompress, guide agent to use dump_object_stream
  ```
- **Critical**: Size check must happen before `filter_stream=True` processing
- **Guidance**: Add helpful message telling agent to use `dump_object_stream` for large files

**RTF Analysis Tool Pattern (October 2025):**
- **Issue**: Agent called `analyze_rtf_objects` repeatedly, hitting recursion limit
- **Root Cause**: Tool returns all available info in one call, but agent kept searching for more
- **Fix Pattern**:
  1. Add "KNOW WHEN TO STOP" guidance to tool docstring and agent prompt
  2. Explicitly state when tool is READ-ONLY and cannot extract payloads
  3. List what tool CAN and CANNOT do to prevent unrealistic expectations
  4. Add stopping criteria: "If you see CVE indicator, you have sufficient evidence → STOP"
- **Applies To**: Any analysis tool that provides complete results in one call

**URL Investigation Double Nesting Fix:**
- **Issue**: Wrapper function in `url_investigation/graph.py` was wrapping entire subgraph result, creating `link_analysis_final_reports[0].link_analysis_final_report` instead of `link_analysis_final_reports[0]`
- **Fix**: Extract `result["link_analysis_final_report"]` before wrapping:
  ```python
  return {
      "link_analysis_final_reports": [result["link_analysis_final_report"]],
      "errors": result.get("errors", [])
  }
  ```
- **Root Cause**: Subgraph's output_schema preserved key wrapper, then wrapper function added another layer

**Loguru JSON Logging Pattern:**
- **Issue**: Logging JSON directly in f-strings causes format errors: `logger.debug(f"Data: {json_str}")` fails because Loguru treats `{}` as format placeholders
- **Fix**: Pass JSON as extra fields, not in message string:
  ```python
  # ❌ WRONG - Causes format errors
  logger.debug(f"Report: {report.model_dump_json(indent=2)}")
  
  # ✅ CORRECT - Pass as extra field
  logger.debug("Report available", report_data=report.model_dump())
  ```
- **Rule**: Never log raw JSON/dicts in message strings with Loguru

**Report Generator State Schema:**
- **Issue**: Report Generator was using OrchestratorState directly, lacking proper input/output separation
- **Fix**: Created dedicated `ReportGeneratorState` (full input) and `ReportGeneratorOutputState` (filtered output)
- **Pattern**: All agents should have dedicated state schemas even when similar to orchestrator state

**Pydantic Model Access Pattern:**
- **Issue**: `final_verdict.get("verdict")` fails because `final_verdict` is a Pydantic model, not a dict
- **Fix**: Access Pydantic model attributes directly:
  ```python
  # ❌ WRONG
  verdict = state.get("final_verdict", {}).get("verdict", "Unknown")
  
  # ✅ CORRECT
  final_verdict = state.get("final_verdict")
  verdict = final_verdict.verdict if final_verdict else "Unknown"
  ```

**LangGraph Studio UI Limitation:**
- **Known Issue**: Subgraph nodes returning large state values (~11KB markdown reports) may not display properly in Studio execution trace
- **Behavior**: Graph executes correctly, state is correct, but UI can't render node name in trace
- **Workaround**: Accept as cosmetic issue or reduce output schema to exclude large strings
- **Not a Bug**: Functional behavior is 100% correct, only Studio UI rendering affected

### File Organization by Session
```
output/{session_id}/
├── logs/                    # Session-specific logs
│   └── session.jsonl       # Structured JSONL for this session only
├── pdf_extraction/          # Page images with pHash naming
├── file_analysis/           # Evidence graphs, state persistence
├── url_investigation/       # URL investigations with screenshots
│   └── task_url_*/         # Individual URL analysis artifacts
└── report_generator/        # Final reports and verdict
```

Central logs:
```
logs/
└── pdf_hunter_YYYYMMDD.jsonl  # All sessions from a given day
```

## Testing & Debugging

### Test Assets
- Test files are organized in subdirectories:
  - `tests/assets/pdfs/hello_qr_and_link.pdf`: QR code detection testing
  - `tests/assets/pdfs/test_mal_one.pdf`: Malicious PDF sample
  - `tests/assets/images/qrmonkey.jpg`: QR code image testing
- `notebooks/development/*.ipynb`: Agent-specific development environments

### Cross-Platform Path Handling
When referencing test files in modules or CLI:
```python
import os

# Get the module's directory
module_dir = os.path.dirname(os.path.abspath(__file__))

# Navigate to project root (adjust the number of "../" based on module depth)
project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))

# Construct path to test file
file_path = os.path.join(project_root, "tests", "assets", "pdfs", "test_file.pdf")
```

**CLI Path Resolution:**
- Relative paths are resolved against the project root
- Absolute paths are used as-is
- Default paths in CLI modules use project-relative resolution
- Example: `--file tests/assets/pdfs/test.pdf` or `--file /absolute/path/to/test.pdf`

### State Persistence
- All agents automatically save final state using `dump_state_to_file()`
- JSON files named `*_final_state_session_{session_id}.json`
- Use `serialize_state_safely()` to handle Pydantic models and complex objects

### Configuration Structure
- **Execution Config**: `config/execution_config.py` - Recursion limits and runtime parameters
- **Model Config**: `config/models_config.py` - LLM instances and provider settings
- **Centralized Imports**: `from pdf_hunter.config import AGENT_CONFIG, agent_llm`

### Recursion Limits & Loop Prevention
- **Default LangGraph Limit**: 25 super-steps per graph
- **Orchestrator**: 30 steps (multi-agent coordination)
- **Tool-using Agents**: 15-25 steps (agent-tool interaction loops)
- **Linear Agents**: 10-15 steps (sequential workflows)
- **Configuration**: Centrally managed in `config/execution_config.py`

### Error Handling Pattern

**Comprehensive Implementation (September 2025):**
All 5 agents (~30 node functions) implement universal error handling with:

```python
# Universal Node Function Pattern
async def node_function(state: AgentState) -> dict:
    """Node function with comprehensive error handling."""
    try:
        # 1. Input Validation - Check required fields at entry
        if not state.get("required_field"):
            error_msg = "Error in node_function: Missing required field 'required_field'"
            logger.error(error_msg)
            return {"errors": [error_msg]}
        
        # 2. Safe State Access - Use .get() with defaults
        optional_field = state.get("optional_field", default_value)
        
        # 3. Core Business Logic
        result = await perform_operation(state)
        
        # 4. Success Return
        return {"result": result}
        
    except Exception as e:
        # 5. Standardized Error Handling
        error_msg = f"Error in node_function: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": [error_msg]}

# Standard error aggregation across all agents
errors: Annotated[List[str], operator.add]  # Agent level
errors: Annotated[List[list], operator.add]  # Orchestrator level (nested)

# GraphRecursionError handling for complexity/loop prevention
from langgraph.errors import GraphRecursionError

# In investigator wrappers (file_analysis, url_investigation):
try:
    result = await investigator_graph.ainvoke(state)
except GraphRecursionError as e:
    # File Analysis: Mark mission as BLOCKED, preserve transcript for reviewer
    # URL Investigation: Create URLAnalysisResult with "Inaccessible" verdict
    error_msg = f"Investigation hit recursion limit - too complex or stuck"
    logger.warning(error_msg)
    return partial_result_with_error_context
```

**Coverage:**
- PDF Extraction: 4/4 nodes (setup_session, extract_pdf_images, find_embedded_urls, scan_qr_codes)
- Image Analysis: 2/2 nodes (analyze_pdf_images, compile_image_findings)
- Report Generator: 3/3 nodes (determine_threat_verdict, generate_final_report, save_analysis_results)
- URL Investigation: 6/6 nodes + GraphRecursionError handling in wrapper
- File Analysis: 8/8 nodes + GraphRecursionError handling in wrapper

**Test Coverage:** 19 test cases across 5 test files in `tests/agents/` covering:
- Missing files and invalid paths
- Empty data structures
- Permission errors
- Malformed state
- Tool execution failures

**Key Principles:**
- **No State Mutation**: Always use `return {"errors": [msg]}` pattern, never direct state modification
- **Early Validation**: Check required fields before processing
- **Defensive Access**: Use `state.get("key")` instead of `state["key"]`
- **Standardized Messages**: Format as `"Error in {function_name}: {error_details}"`
- **Graceful Degradation**: Partial completion allowed when individual components fail
- **Transparent Reporting**: All errors logged and aggregated in final state
- **Recursion Protection**: Specialized handling for complexity limits prevents system crashes

**Mission ID Generation (September 2025):**
- `InvestigationMission.mission_id` changed from `default_factory` (random UUID) to LLM-generated semantic IDs
- Format: `mission_<threat_type>_<number>` (e.g., `mission_openaction_001`, `mission_javascript_obj_42`)
- Benefits: Predictable IDs, consistent tracking, LLM can reference missions meaningfully
- Implementation: Required field with clear description and format examples in schema + prompt guidance

## Dependencies & Integration Points

### Critical Dependencies
- **LangGraph**: Multi-agent orchestration and state management
- **Playwright MCP**: Browser automation for link analysis (`npm install` required)
- **PDF Tools**: peepdf-3, pdfid, PyMuPDF for static analysis
- **Computer Vision**: OpenCV + pyzbar for QR code detection
- **Python**: Strict requirement for >=3.11,<3.12

### Environment Setup
- `.env` configuration for AI providers (OpenAI/Azure OpenAI)
- `langgraph.json` defines deployable graphs for platform
- `pyproject.toml` with hatchling backend and dependency groups

## Logging System

### Logging Architecture

PDF Hunter uses **Loguru** for structured logging with three output streams:

**Terminal Output:**
- Colorful, human-readable format with emojis
- INFO+ level by default (production)
- DEBUG+ level when `debug_to_terminal=True` (development)

**Central Log File:**
- `logs/pdf_hunter_YYYYMMDD.jsonl` - All sessions, daily rotation
- Structured JSONL format (one JSON object per line)
- DEBUG+ level for complete historical record

**Session Log File:**
- `output/{session_id}/logs/session.jsonl` - Single session only
- Structured JSONL format for session-specific analysis
- DEBUG+ level, auto-created when session starts

### Logging Configuration

```python
# In orchestrator/graph.py startup
from pdf_hunter.config.logging_config import setup_logging

# Production mode (INFO+ in terminal, all logs in files)
setup_logging(
    session_id=session_id,
    output_directory=output_dir  # Creates session.jsonl
)

# Development mode (DEBUG+ in terminal)
setup_logging(debug_to_terminal=True)
```

### Logger Usage Pattern

```python
# Import at module level
from loguru import logger

# Basic logging with agent context
logger.info("Starting extraction",
            agent="PdfExtraction",
            node="extract_images",
            session_id=state.get("session_id"))

# Event-based logging
logger.success("✅ Extraction complete",
               agent="PdfExtraction",
               node="extract_images",
               event_type="IMAGE_EXTRACTION_COMPLETE",
               image_count=len(images))

# Error logging with automatic traceback
logger.exception("❌ Operation failed",
                agent="PdfExtraction",
                node="extract_images")

# Complex objects auto-serialize to JSON
logger.debug("State dump",
            agent="FileAnalysis",
            state_data=state.model_dump())
```

### Agent Naming Convention

All agents use **PascalCase** for the `agent` field:
- `PdfExtraction` (not `pdf_extraction`)
- `FileAnalysis` (not `file_analysis`)
- `ImageAnalysis` (not `image_analysis`)
- `URLInvestigation` (not `url_investigation`)
- `ReportGenerator` (not `report_generator`)

### Log Levels

- `logger.trace()` - Very detailed debugging
- `logger.debug()` - Debug information (JSON only, not terminal by default)
- `logger.info()` - General operational events
- `logger.success()` - Success events (green checkmark in terminal)
- `logger.warning()` - Warning conditions
- `logger.error()` - Error events
- `logger.critical()` - Critical system failures

## Common Pitfalls

- **Don't** modify state directly - use LangGraph's additive aggregation patterns
- **Don't** hardcode file paths - use session-based directory management
- **Don't** skip state serialization - debugging relies on persistent state files
- **Don't** use print statements - use the logger instead
- **Do** use dedicated LLM instances per agent task for optimal performance
- **Do** follow the URL status lifecycle for URL investigation features
- **Do** leverage existing shared utilities before creating new ones
- **Do** use appropriate log levels (debug for details, info for operations)

## Adding New Features

### New Agent Pattern
1. Create agent directory under `src/pdf_hunter/agents/`
2. Implement `graph.py`, `nodes.py`, `schemas.py`, `prompts.py`
3. Add LLM configuration in `config/models_config.py`
4. Register graph in `langgraph.json`
5. Update orchestrator workflow if needed

### New Analysis Capabilities
- Extend existing agent schemas with new fields
- Add specialized LLM instances for new task types
- Follow established patterns for tool integration and state management

### Adding Logging to New Components
1. Import logging utilities at the top of your module:
   ```python
   from pdf_hunter.shared.utils.logging_config import get_logger
   ```
2. Create a module-specific logger:
   ```python
   logger = get_logger(__name__)
   ```
3. Replace print statements with appropriate log levels:
   ```python
   # Instead of: print(f"Extracted {len(results)} items")
   logger.info(f"Extracted {len(results)} items")
   ```
4. Add detailed logs for debugging:
   ```python
   logger.debug(f"Processing item: {item.id}")
   ```
5. Use conditional logging for expensive operations:
   ```python
   if logger.isEnabledFor(logging.DEBUG):
       logger.debug(f"Complex state: {serialize_state_safely(state)}")
   ```
6. Include exception tracebacks in error logs:
   ```python
   try:
       # code that might fail
   except Exception as e:
       logger.error(f"Operation failed: {e}", exc_info=True)
       return {"errors": [f"Error: {e}"]}
   ```