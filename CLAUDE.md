# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Hunter is a multi-agent AI framework for automated PDF threat hunting built using Python 3.11+ and LangGraph. The system uses AI-powered agents orchestrated via LangGraph to analyze potentially malicious PDFs and generate comprehensive security reports. The framework employs a sophisticated multi-agent orchestration pattern with specialized agents for PDF extraction, file analysis, image analysis, URL investigation, and report generation.

The framework is fully asynchronous, utilizing Python's async/await pattern for non-blocking I/O operations to ensure compatibility with LangGraph Studio and other event loop-based environments.

## Quick Reference

- **Installation & Setup**: See README.md (lines 38-210)
- **Docker Deployment**: See README.md (lines 43-78)
- **CLI Usage**: See README.md (lines 270-337)
- **Model Configuration**: See README.md (lines 247-267) or `src/pdf_hunter/config/models_config.py`
- **Logging System**: See `docs/LOGGING_GUIDE.md` and `docs/LOGGING_FIELD_REFERENCE.md`

## Core Philosophy

The system operates under three core principles:

1. **Autonomy is Disease**: Any automatic action capability in a PDF (e.g., /OpenAction, /JavaScript, /Launch, /AA, /EmbeddedFile) is high-signal and prioritized for investigation
2. **Deception is Confession**: Visual and structural inconsistencies are treated as confessions of malicious intent
3. **Incoherence is a Symptom**: Cross-page and cross-modal incoherence elevates suspicion

## Agent Pipeline Architecture

| Agent | Purpose | Key Files | Critical Features |
|-------|---------|-----------|-------------------|
| **Orchestrator** | Master coordination | `orchestrator/` | Session mgmt, state aggregation, safe serialization |
| **PDF Extraction** | Artifact extraction | `pdf_extraction/` | Images (pHash), URLs (content + XMP metadata), QR codes |
| **File Analysis** | Static analysis | `file_analysis/` | Multi-tool scanning (pdfid, pdf-parser, peepdf), mission-based investigations, XMP provenance analysis, think_tool integration |
| **Image Analysis** | Visual deception | `image_analysis/` | VDA persona (HCI/UX + forensics), visual-technical cross-examination, URL prioritization, XMP metadata URL assessment |
| **URL Investigation** | Web reconnaissance | `url_investigation/` | MCP/Playwright browser automation, strategic reflection, URL status tracking |
| **Report Generator** | Final synthesis | `report_generator/` | Executive summary, verdict, IOC extraction, artifact cataloging |

**Workflow**: START → pdf_extraction → {file_analysis, image_analysis} → url_investigation → report_generator → END

**Key Features**:
- **Parallel Processing**: File and image analysis run concurrently
- **Session Management**: Auto-generated session IDs (`{sha1}_{timestamp}`)
- **State Persistence**: All agents save final state for debugging
- **Strategic Reflection**: Think tool integrated in investigative agents
- **XMP Metadata Integration**: Complete pipeline from extraction → visual analysis → URL investigation

## Configuration

**Config Package** (`src/pdf_hunter/config/`):
- `models_config.py` - LLM instances (10 specialized models), provider settings (OpenAI/Azure/Ollama)
- `execution_config.py` - Recursion limits, think tool flag, runtime parameters

**Recursion Limits** (prevents infinite loops while allowing complex analysis):
- Orchestrator: 30 steps
- Tool-using agents (file analysis, URL investigation): 25 steps
- Linear agents: 10-15 steps

**Think Tool**: Enable strategic reflection via `THINKING_TOOL_ENABLED = True` in execution_config.py

**Usage**:
```python
from pdf_hunter.config import FILE_ANALYSIS_CONFIG, THINKING_TOOL_ENABLED, file_analysis_triage_llm

# Apply config to graphs
agent_graph = agent_graph.with_config(FILE_ANALYSIS_CONFIG)

# Conditional tool integration
if THINKING_TOOL_ENABLED:
    from pdf_hunter.shared.tools.think_tool import think_tool
    tools.append(think_tool)
```

## File Organization

```
src/pdf_hunter/
├── agents/
│   ├── pdf_extraction/     # Images, URLs, QR codes, XMP metadata
│   ├── file_analysis/      # Static analysis, missions, tools, prompts
│   ├── image_analysis/     # Visual deception analysis, URL prioritization
│   ├── url_investigation/  # Browser automation, link analysis
│   └── report_generator/   # Final report synthesis
├── orchestrator/           # Master coordination graph
├── api/                    # FastAPI server, SSE streaming, session management
├── shared/
│   ├── analyzers/          # External PDF tools (pdfid, peepdf wrappers)
│   ├── tools/              # Shared tools (think_tool for strategic reflection)
│   └── utils/              # file_operations, hashing, image_extraction,
│                           #  url_extraction, qr_extraction, mcp_client, serializer
└── config/                 # models_config, execution_config

tests/
├── agents/                 # Agent-specific tests (error handling, XMP integration)
├── api/                    # API server and SSE streaming tests
└── assets/
    ├── pdfs/               # Test PDF files
    └── images/             # Test images (QR codes)

output/{session_id}/        # Session-specific outputs
├── pdf_extraction/
├── file_analysis/
├── image_analysis/
├── url_investigation/
└── report_generator/
```

## Development Patterns

### Cross-Platform Path Handling

All agent modules use platform-independent path construction:

```python
import os

module_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))
file_path = os.path.join(project_root, "tests", "assets", "pdfs", "test_file.pdf")
```

Ensures compatibility across Windows, Linux, macOS without hardcoded paths.

### State Management

- Use `TypedDict` for LangGraph state schemas
- Leverage `operator.add` for list aggregation across parallel nodes
- Use safe serialization (`serialize_state_safely()`) for complex state persistence
- Maintain immutability where possible for debugging

### Tool Integration

- Wrap external tools using LangChain's `@tool` decorator
- Implement safe command execution with timeouts
- Handle tool errors gracefully in agent flows
- Use MCP adapters for browser automation (Playwright)

### MCP Integration

- Use `get_mcp_client()` for browser automation tasks
- Implement task-specific output directories under session paths
- Handle MCP session lifecycle with context managers
- Browser tools use arrow function syntax: `{"function": "() => document.title"}`

## Critical Development Patterns

### InjectedToolArg Pattern for File Path Management

**Problem**: LLMs truncate 100+ character file paths when generating tool calls.

**Solution**: Hide parameters from LLM, inject at runtime:

```python
from langchain_core.tools import InjectedToolArg
from typing import Annotated

@tool
def get_pdf_stats(
    use_objstm: bool = True,  # Visible to LLM
    pdf_file_path: Annotated[str, InjectedToolArg] = None  # Hidden, injected
) -> str:
    """Display PDF statistics."""
    return run_pdf_parser(pdf_file_path, options=["--stats"], use_objstm=use_objstm)

# Custom injection wrapper in graph.py
async def inject_and_call_tools(state: InvestigatorState) -> dict:
    last_message = state["messages"][-1]
    for tool_call in last_message.tool_calls:
        if "pdf_file_path" not in tool_call["args"]:
            tool_call["args"]["pdf_file_path"] = state["file_path"]
        if "output_directory" not in tool_call["args"]:
            tool_call["args"]["output_directory"] = state["output_directory"]

    tool_node = ToolNode(pdf_parser_tools)
    result = await tool_node.ainvoke({"messages": [last_message]})
    return {"messages": result["messages"]}

investigator_builder.add_node("tools", inject_and_call_tools)
```

**Benefits**: Eliminates path truncation, reduces context usage, simplifies prompts.

### Escaping LLM Output for String Operations

**Problem**: LLM output with `{`, `}`, `<`, `>` breaks `.format()` and Loguru logging.

**Solution**: Always escape before string operations:

```python
# Escape curly braces before .format()
safe_json = json.dumps(llm_data).replace('{', '{{').replace('}', '}}')
prompt = template.format(data=safe_json)

# Escape HTML tags before logging
safe_error = str(error).replace('<', '{{').replace('>', '}}')
logger.warning(f"Tool failed: {safe_error}", agent="Agent", node="node")
```

**Critical Locations**: Mission descriptions, evidence graphs, tool error messages.

### Artifact Preservation with Auto-Subdirectory Creation

**Problem**: Forensic artifacts must be saved to session-specific `file_analysis/` subdirectory.

**Solution**: Tools auto-create subdirectory when `output_directory` injected:

```python
@tool
def hex_decode(
    hex_string: str,
    strings_on_output: bool = False,
    output_directory: Annotated[Optional[str], InjectedToolArg] = None
) -> str:
    if strings_on_output and output_directory:
        target_dir = os.path.join(output_directory, "file_analysis")
        os.makedirs(target_dir, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix="decoded_", suffix=".bin", dir=target_dir)
        # Write and return: "[TEMP FILE] /path/to/output/session_id/file_analysis/decoded_abc.bin"
        return f"[OK] Decoded {len(data)} bytes.\n[TEMP FILE] {temp_path}\n..."
```

**Pattern**: LLM extracts path from tool output, adds to evidence graph. Report generator searches for paths.

### Context Overflow Prevention

**Problem**: Large decompressed streams (>1MB) exceed LLM context limits.

**Solution**: Check compressed size before filtering:

```python
if "Contains stream" in output and "/Filter" in output:
    length_match = re.search(r'/Length\s+(\d+)', output)
    if length_match:
        stream_size = int(length_match.group(1))
        if stream_size > 100000:  # 100KB compressed
            output += f"\n\n[NOTE: Stream is {stream_size:,} bytes (>100KB). Auto-filter skipped.]"
            return output  # Return metadata only
```

### Agent Loop Prevention

**Problem**: Agent calls same read-only tool repeatedly, hitting recursion limits.

**Solution**: Add explicit stopping criteria to tool docstrings:

```python
@tool
def analyze_rtf_objects(file_path: str) -> str:
    """
    Analyze RTF files for embedded objects.

    What this tool CANNOT DO:
    - Extract OLE payloads to disk
    - Provide more details than shown
    - Return different results if called multiple times

    IMPORTANT: Once you see exploit indicator, DO NOT call again.
    """
```

**Agent Prompt Guidance**:
```
KNOW WHEN TO STOP:
- Known exploit identified (CVE) → SUFFICIENT EVIDENCE → STOP
- Tool says it CANNOT do something → ACCEPT IT → STOP trying
- Calling same tool twice returns identical results → DO NOT CALL IT AGAIN
```

## Key Implementation Patterns

### Async/Await Requirements
- All node functions must be async
- LLM calls use `await llm.ainvoke()`
- File I/O wrapped in `asyncio.to_thread()`
- Subprocess calls wrapped with `asyncio.to_thread()`

### Error Handling Standards
- Universal try-except in all nodes
- Safe state access with `state.get()`
- Error aggregation via `Annotated[List[str], operator.add]`
- GraphRecursionError handling for investigator subgraphs:
  - File analysis: Mark as `BLOCKED`, preserve transcript
  - URL investigation: Create result with `verdict="Inaccessible"`, `mission_status="failed"`

### Strategic Reflection
- Think tool for systematic decision-making
- Configuration-controlled via `THINKING_TOOL_ENABLED`
- Used after significant discoveries, before major decisions

### Logging Standards
- Use Loguru, not print statements
- Agent field in PascalCase: `PdfExtraction`, `FileAnalysis`, `ImageAnalysis`, `URLInvestigation`, `ReportGenerator`
- Include `agent`, `node`, `session_id` in all log calls
- See `docs/LOGGING_GUIDE.md` for complete patterns

## URL Status Tracking

**URLMissionStatus Enum**:
- `NEW` - Initially flagged by visual analysis
- `IN_PROGRESS` - Currently being analyzed
- `COMPLETED` - Successfully analyzed with findings
- `FAILED` - Analysis failed (errors or inaccessible)
- `NOT_RELEVANT` - Low-priority, not selected for analysis

**Workflow**: Image Analysis (NEW) → URL Investigation Filter (IN_PROGRESS/NOT_RELEVANT) → Analyst Node (COMPLETED/FAILED)

## Advanced Features

- **QR Code Extraction**: `shared/utils/qr_extraction.py` - OpenCV-based detection, URL extraction
- **MCP Client**: `shared/utils/mcp_client.py` - Multi-server client for browser automation
- **Serialization**: `shared/utils/serializer.py` - Safe JSON serialization of complex state
- **Think Tool**: `shared/tools/think_tool.py` - Strategic reflection for investigation quality
- **XMP Metadata**: Complete pipeline from `pdf_extraction` → `file_analysis` → `image_analysis`

## Security Considerations

Defensive security tool for PDF threat analysis with safe handling:
- Sandboxed PDF parsing (external tools)
- No direct PDF execution or rendering
- Structured analysis without file modification
- Safe command execution with input validation
- Browser automation in isolated MCP environments

## Implementation Reminders

- **Never create files unless absolutely necessary** - always prefer editing
- **Follow existing code patterns** - examine neighboring files
- **Use safe serialization** - `serialize_state_safely()` for complex state
- **Handle MCP sessions properly** - use context managers, task isolation
- **Test with sample PDFs** - use files in `tests/assets/pdfs/`
- **Maintain agent isolation** - each agent should be runnable independently
- **Follow LangGraph patterns** - proper state management and edge definitions
- **Use proper logging** - Loguru with agent/node/session context

## Package Structure

Standard src-layout with `pdf_hunter` package under `src/`:
- Import: `from pdf_hunter.config import ...`
- Execution: `python -m pdf_hunter.agents.file_analysis.graph`
- Relative imports within package: `from .nodes import ...`
- Absolute imports across packages: `from pdf_hunter.shared.analyzers import ...`
