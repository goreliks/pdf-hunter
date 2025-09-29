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

## Key Commands & Workflows

### Development Commands
```bash
# Primary development workflow
uv sync --group dev           # Install with Jupyter support
uv run python -m pdf_hunter.orchestrator.graph  # Run complete pipeline

# Individual agent testing
uv run python -m pdf_hunter.agents.pdf_extraction.graph
uv run python -m pdf_hunter.agents.file_analysis.graph

# LangGraph Platform deployment
langgraph up                  # Deploy all graphs via API

# Notebook development
jupyter lab notebooks/development/
```

### Model Configuration
- **Default**: GPT-4o via `openai_config` in `config.py`
- **Enterprise**: Azure OpenAI via `azure_openai_config`
- **Local**: Ollama (disabled by default) - dual model setup with text/vision specialization
- Switch providers by updating LLM initializations in `config.py`

## Agent Architecture

### Orchestrator (`src/pdf_hunter/orchestrator/`)
- **Workflow**: pdf_extraction → {file_analysis || image_analysis} → url_investigation → report_generator
- **State Aggregation**: Uses `operator.add` for collecting agent results
- **Session Management**: Auto-generates session IDs and directory structures

### Agent Specialization Patterns
- **PDF Extraction**: Pure utility (no LLM) - image extraction, URL/QR detection
- **File Analysis**: Multi-tool scanning + mission-based parallel investigations
- **Image Analysis**: VDA (Visual Deception Analyst) persona for UI/UX security analysis
- **URL Investigation**: Browser automation via MCP Playwright integration
- **Report Generator**: Executive report synthesis and final verdict generation

## Critical Development Patterns

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

### File Organization by Session
```
output/{session_id}/
├── pdf_extraction/          # Page images with pHash naming
├── file_analysis/           # Evidence graphs, state persistence
├── url_investigation/       # URL investigations with screenshots
│   └── task_url_*/         # Individual URL analysis artifacts
└── report_generator/        # Final reports and verdict
```

## Testing & Debugging

### Test Assets
- `tests/hello_qr_and_link.pdf`: QR code detection testing
- `tests/test_mal_one.pdf`: Malicious PDF sample
- `notebooks/development/*.ipynb`: Agent-specific development environments

### State Persistence
- All agents automatically save final state using `dump_state_to_file()`
- JSON files named `*_final_state_session_{session_id}.json`
- Use `serialize_state_safely()` to handle Pydantic models and complex objects

### Error Handling Pattern
```python
# Standard error aggregation across all agents
errors: Annotated[List[str], operator.add]  # Agent level
errors: Annotated[List[list], operator.add]  # Orchestrator level (nested)
```

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

### Logging Configuration
```python
# Configure logging at application start
from pdf_hunter.shared.utils.logging_config import configure_logging
import logging

# Default configuration (INFO level)
configure_logging()

# Debug level with file output
configure_logging(level=logging.DEBUG, log_to_file=True)

# Session-specific logging
configure_logging(log_to_file=True, session_id=session_id)
```

### Logger Usage Pattern
```python
# Import at module level
from pdf_hunter.shared.utils.logging_config import get_logger

# Create module-specific logger
logger = get_logger(__name__)

# Use appropriate log levels
logger.debug("Detailed debugging information")
logger.info("General operational information")
logger.warning("Warning situations")
logger.error("Error events", exc_info=True)  # Include traceback
logger.critical("Critical errors")

# Conditional verbose logging
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"Complex object: {serialize_state_safely(complex_object)}")
```

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
3. Add LLM configuration in `config.py`
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