# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Hunter is a multi-agent AI framework for automated PDF threat hunting built using Python 3.11+ and LangGraph. The system uses AI-powered agents orchestrated via LangGraph to analyze potentially malicious PDFs and generate comprehensive security reports. The framework employs a sophisticated multi-agent orchestration pattern with specialized agents for preprocessing, static analysis, visual analysis, link analysis, and final reporting.

## Development Setup

### Installation

```bash
# Install dependencies using uv (preferred) 
uv sync

# For development features (Jupyter notebooks)
uv pip install -e .[dev]

# Install Playwright MCP dependency for link analysis
npm install
```

### Development Environment

The project uses:

- **Python**: 3.11+ (required, <3.12)
- **Package Management**: pyproject.toml with hatchling build backend, uv.lock for dependency management
- **LangGraph Platform**: Configured with langgraph.json for multi-graph deployment
- **Dependencies**: LangGraph, LangChain, OpenAI, PDF analysis tools (peepdf-3, pdfid, PyMuPDF), computer vision (OpenCV, pyzbar for QR codes), MCP adapters for browser automation
- **Development**: Jupyter notebooks for prototyping and testing
- **Node.js**: Required for Playwright MCP server (@playwright/mcp)

### Running the System

```bash
# Run the complete orchestrator (coordinates all agents)
uv run python -m pdf_hunter.orchestrator.graph

# Run individual agents in isolation
uv run python -m pdf_hunter.agents.preprocessing.graph
uv run python -m pdf_hunter.agents.visual_analysis.graph
uv run python -m pdf_hunter.agents.static_analysis.graph
uv run python -m pdf_hunter.agents.link_analysis.graph
uv run python -m pdf_hunter.agents.finalizer.graph

# LangGraph Platform deployment (all graphs available via API)
langgraph up

# Jupyter development environment
jupyter lab notebooks/development/
```

## Architecture Overview

### Core Philosophy and Design Principles

The system operates under three core principles:

1. **Autonomy is Disease**: Any automatic action capability in a PDF (e.g., /OpenAction, /JavaScript, /Launch, /AA, /EmbeddedFile) is high-signal and prioritized for investigation
2. **Deception is Confession**: Visual and structural inconsistencies are treated as confessions of malicious intent
3. **Incoherence is a Symptom**: Cross-page and cross-modal incoherence elevates suspicion

### Complete Agent Pipeline

**Orchestrator** (`src/pdf_hunter/orchestrator/`):
- Master coordination graph managing the entire analysis workflow
- **Updated Workflow**: START → preprocessing → {static_analysis, visual_analysis} → link_analysis → finalizer → END
- **Session Management**: Auto-generates session IDs and creates session-specific directories
- **State Management**: Aggregates results from all agents using LangGraph's additive list aggregation
- **Serialization**: Safe state serialization for persistence and debugging

**Agent 1: Preprocessing** (`src/pdf_hunter/agents/preprocessing/`):
- **Purpose**: Extract safe, high-signal artifacts without executing content
- **Session Management**: Auto-generates session ID using `{sha1}_{timestamp}` format
- **Directory Creation**: Creates session-specific directory structure for organized output
- **Initialization Node**: Validates paths, calculates file hashes (SHA1/MD5), gets page count
- **Image Extraction Node**: Renders pages to images, calculates perceptual hashes (pHash), saves with pHash-based filenames
- **URL Extraction Node**: Extracts URLs from annotations and text with coordinates
- **QR Code Detection**: Detects QR codes in extracted images using OpenCV and pyzbar
- **Output**: File metadata, page images with pHash-based naming, URLs, QR code data, session directory

**Agent 2: Static Analysis** (`src/pdf_hunter/agents/static_analysis/`):
- **Triage Node**: Multi-tool PDF scanning (pdfid, pdf-parser, peepdf)
- **Investigator Subgraph**: Parallel mission-based investigations
- **Reviewer Node**: Evidence graph merging and strategic analysis
- **Threat Detection**: OpenAction, JavaScript, AcroForm, EmbeddedFile analysis
- **State Persistence**: Automatic final state saving for debugging and analysis tracking
- **Output**: Evidence graph, mission reports, structural analysis, persistent state files

**Agent 3: Visual Analysis** (`src/pdf_hunter/agents/visual_analysis/`):
- **Enhanced VDA Persona**: Visual Deception Analyst combining HCI/UX security, cognitive psychology, and digital forensics
- **Core Analysis**: Visual-technical cross-examination for deception detection
- **Page-Level Analysis**: Examines visual presentation vs. technical elements
- **Cross-Page Context**: Maintains coherence analysis across document pages
- **URL Prioritization**: Ranks URLs for deeper investigation based on visual context
- **Output**: Deception tactics, benign signals, prioritized URLs for link analysis

**Agent 4: Link Analysis** (`src/pdf_hunter/agents/link_analysis/`):
- **NEW AGENT**: Dedicated deep analysis of URLs identified by visual analysis
- **MCP Integration**: Uses Playwright MCP server for browser automation
- **Link Investigator**: Automated web reconnaissance of suspicious URLs
- **Analyst Node**: Structured analysis of link findings
- **State Persistence**: Automatic state saving for debugging and recovery
- **Output**: URL reputation, content analysis, threat indicators, persistent state files

**Agent 5: Finalizer** (`src/pdf_hunter/agents/finalizer/`):
- **NEW AGENT**: Comprehensive report generation and final verdict
- **Reporter Node**: Synthesizes all agent findings into executive summary
- **Final Verdict Node**: Makes final malicious/benign determination
- **Enhanced File Output**: Uses centralized serialization for consistent state dumps
- **Output**: Final report, verdict, actionable intelligence, persistent analysis state

### Advanced Features

**QR Code Extraction** (`src/pdf_hunter/shared/utils/qr_extraction.py`):
- OpenCV-based QR code detection in PDF images
- URL extraction from QR codes with validation
- Integration with visual analysis for context

**MCP Client Integration** (`src/pdf_hunter/shared/utils/mcp_client.py`):
- Multi-server MCP client for browser automation
- Playwright integration for link analysis
- Session-aware directory management for screenshots and traces
- Task-specific output isolation under session directories

**State Serialization** (`src/pdf_hunter/shared/utils/serializer.py`):
- Safe JSON serialization of complex orchestrator state
- Handles Pydantic models, nested structures, and non-serializable objects
- `serialize_state_safely()`: Converts complex state to JSON-serializable format
- `dump_state_to_file()`: Direct file writing with automatic serialization
- Essential for debugging and state persistence across all agents

### Key Data Structures

- **Investigation Mission**: Focused threat-specific analysis tasks
- **Evidence Graph**: Structured representation of PDF attack chains
- **Visual Analysis Report**: Deception tactics and authenticity signals
- **Link Analysis Report**: URL reconnaissance and threat assessment
- **Final Report**: Executive summary with verdict and IOCs
- **Prioritized URLs**: Ranked list of links for deeper investigation

### Complete Agent Workflow

1. **Preprocessing**: Extract metadata, images, URLs, QR codes from PDF
2. **Static Analysis**: Multi-tool scanning, mission dispatch, evidence gathering
3. **Visual Analysis**: Visual deception detection, URL prioritization (runs in parallel with static analysis)
4. **Link Analysis**: Deep reconnaissance of prioritized URLs using browser automation
5. **Finalization**: Comprehensive report synthesis, final verdict, file output

The orchestrator coordinates all five agents in a sophisticated pipeline with parallel processing where appropriate.

## Configuration

### Environment Variables

Create `.env` file with:

```bash
OPENAI_API_KEY=your_key_here
```

### LangGraph Platform

The system is configured for LangGraph Platform deployment with `langgraph.json`:
- **static_analysis**: Static analysis graph endpoint
- **preprocessing**: Preprocessing graph endpoint  
- **orchestrator**: Main orchestrator graph endpoint
- **link_analysis**: Link analysis graph endpoint

### LLM Configuration

- **Default Model**: GPT-4.1 (configured in `src/pdf_hunter/config.py`)
- **Temperature**: 0.0 for consistent analysis
- All agents use the same model configuration for consistency

## Testing

### Test Files

Sample PDFs in `tests/` directory:
- `hello_qr.pdf` / `hello_qr_and_link.pdf`: QR code test cases
- `test_mal_one.pdf`: Malicious PDF sample
- Various threat pattern samples for regression testing

### Notebook Development

- `notebooks/development/static_analysis.ipynb`: Static analysis development
- `notebooks/development/preprocessing.ipynb`: Preprocessing development  
- `notebooks/development/link_analysis_agent.ipynb`: NEW - Link analysis development
- Step-by-step agent execution and debugging capabilities
- Prototype new features before integration

## File Organization

```bash
src/
└── pdf_hunter/              # Main package directory
    ├── agents/
    │   ├── preprocessing/       # Preprocessing agent
    │   │   ├── graph.py         # LangGraph workflow definition
    │   │   ├── nodes.py         # Individual workflow nodes
    │   │   └── schemas.py       # State and data models
    │   ├── static_analysis/     # Static analysis agent
    │   │   ├── graph.py         # LangGraph workflow definition
    │   │   ├── nodes.py         # Individual workflow nodes
    │   │   ├── schemas.py       # State and data models
    │   │   ├── prompts.py       # LLM prompts for each node
    │   │   └── tools.py         # LangChain tool implementations
    │   ├── visual_analysis/     # Visual analysis agent
    │   │   ├── graph.py         # LangGraph workflow definition
    │   │   ├── nodes.py         # Individual workflow nodes
    │   │   ├── prompts.py       # Enhanced VDA prompts
    │   │   └── schemas.py       # State and data models
    │   ├── link_analysis/       # NEW - Link analysis agent
    │   │   ├── graph.py         # Link investigator graph
    │   │   ├── nodes.py         # Link analysis nodes
    │   │   ├── prompts.py       # Link analysis prompts
    │   │   ├── schemas.py       # Link analysis schemas
    │   │   ├── sync_runner.py   # Synchronous execution wrapper
    │   │   └── tools.py         # MCP tools for browser automation
    │   └── finalizer/           # NEW - Report generation agent
    │       ├── graph.py         # Finalizer workflow
    │       ├── nodes.py         # Report generation nodes
    │       ├── prompts.py       # Final report prompts
    │       └── schemas.py       # Finalizer schemas
    ├── orchestrator/            # Master coordination
    │   ├── graph.py             # Complete 5-agent orchestration
    │   ├── nodes.py             # Orchestrator nodes
    │   └── schemas.py           # Orchestrator state schemas
    ├── shared/
    │   ├── analyzers/
    │   │   ├── external/        # External PDF tools
    │   │   └── wrappers.py      # Python wrappers for external tools
    │   ├── schemas/             # Shared data models
    │   └── utils/               # Common utilities
    │       ├── file_operations.py # File system operations
    │       ├── hashing.py       # File hash calculation
    │       ├── image_extraction.py # PDF image extraction with pHash-based file naming
    │       ├── url_extraction.py # URL extraction from PDFs
    │       ├── qr_extraction.py # NEW - QR code detection and extraction
    │       ├── mcp_client.py    # NEW - MCP client for browser automation
    │       └── serializer.py    # NEW - Safe state serialization
    └── config.py                # Global configuration

notebooks/                   # Jupyter development environment
├── development/             # Main development notebooks
│   ├── preprocessing.ipynb  # Preprocessing agent development
│   ├── static_analysis.ipynb # Static analysis agent development
│   └── link_analysis_agent.ipynb # NEW - Link analysis development
├── examples/                # Example usage
└── experiments/             # Experimental features

tests/                       # PDF samples and test data
├── agents/                  # Agent-specific tests
├── hello_qr.pdf            # QR code test samples
├── hello_qr_and_link.pdf   
├── test_mal_one.pdf        # Malicious PDF sample
└── *.pdf                   # Additional test files

output/                      # Generated analysis reports (session-based organization)
├── {sha1}_{timestamp}/  # Session-specific directory for each PDF analysis
│   ├── preprocessing/       # Preprocessing agent outputs
│   │   └── extracted_images/
│   ├── static_analysis/     # Static analysis outputs and state files
│   │   └── static_analysis_final_state_session_{sha1}_{timestamp}.json
│   ├── visual_analysis/     # Visual analysis outputs (when run standalone)
│   ├── link_analysis/       # Link analysis investigation artifacts
│   │   └── task_url_XXX/    # Task-specific browser screenshots and analysis
│   └── finalizer/           # Final reports and state files
│       ├── final_report_session_{sha1}_{timestamp}.md
│       └── final_state_session_{sha1}_{timestamp}.json
└── mcp_outputs/             # Legacy MCP output directory (for standalone usage)

.langgraph_api/             # LangGraph Platform state
├── .langgraph_checkpoint.*.pckl  # Checkpoint files
└── *.pckl                  # Platform state files
```

## Development Patterns

### Adding New Threat Types

1. Update `ThreatType` enum in schemas
2. Add detection logic in triage prompts
3. Create specialized investigation prompts
4. Update evidence graph schema if needed

### MCP Integration

- Use `get_mcp_client()` for browser automation tasks
- Implement task-specific output directories
- Handle MCP session lifecycle properly
- Integrate MCP tools with LangChain tool ecosystem

### Tool Integration

- Wrap external tools using LangChain's `@tool` decorator
- Implement safe command execution with timeouts
- Handle tool errors gracefully in agent flows
- Use MCP adapters for complex external integrations

### State Management

- Use TypedDict for LangGraph state schemas
- Leverage `operator.add` for list aggregation across parallel nodes
- Use safe serialization for complex state persistence
- Maintain immutability where possible for debugging

## Package Structure

### Standard src-layout

The project follows Python's standard src-layout pattern with the `pdf_hunter` package under `src/`:

- **Clear package name**: Users import `pdf_hunter` modules instead of generic `src`
- **Reproducibility**: Works without setting `PYTHONPATH` after `uv sync`
- **Editable installs**: `uv pip install -e .` for development
- **Module execution**: Run with `python -m pdf_hunter.agents.static_analysis.graph`

### Import Patterns

- **Relative imports** within the same package: `from .nodes import ...`
- **Absolute imports** across packages: `from pdf_hunter.shared.analyzers import ...`
- **Cross-package references**: `from pdf_hunter.config import ...`

## Advanced Dependencies

### Computer Vision Stack
- **OpenCV**: QR code detection and image processing
- **pyzbar**: QR/barcode decoding
- **Pillow**: Image manipulation
- **imagehash**: Perceptual hashing for duplicate detection and intelligent file naming

### Browser Automation
- **@playwright/mcp**: MCP server for browser automation
- **langchain-mcp-adapters**: MCP integration with LangChain
- **Node.js dependencies**: Required for Playwright MCP server

### Analysis Tools
- **peepdf-3**: Enhanced PDF analysis
- **pdfid**: PDF structure analysis  
- **PyMuPDF**: PDF rendering and content extraction
- **python-whois**: Domain analysis for link investigation

## Security Considerations

This is a **defensive security tool** for PDF threat analysis. The codebase handles potentially malicious files safely through:

- Sandboxed PDF parsing using external tools
- No direct PDF execution or rendering  
- Structured analysis without file modification
- Safe command execution with input validation
- Browser automation in isolated environments via MCP
- Secure state serialization excluding sensitive session data

## Important Implementation Reminders

- **Never create files unless absolutely necessary** - always prefer editing existing files
- **Follow existing code patterns** - examine neighboring files for conventions
- **Use safe serialization** - leverage `serialize_state_safely()` for complex state
- **Handle MCP sessions properly** - use context managers and task isolation
- **Test with sample PDFs** - use files in `tests/` directory for validation
- **Maintain agent isolation** - each agent should be runnable independently
- **Follow LangGraph patterns** - use proper state management and edge definitions