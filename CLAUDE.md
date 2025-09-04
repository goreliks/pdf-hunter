# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a PDF analysis and threat hunting framework built using Python 3.11+ and LangGraph. The system uses AI-powered agents to analyze potentially malicious PDFs and generate comprehensive security reports. The framework employs a multi-agent orchestration pattern with specialized nodes for triage, investigation, review, and final reporting.

## Development Setup

### Installation

```bash
# Install dependencies using uv (preferred) or pip
uv sync
# OR
pip install -r requirements.txt

# For development features (Jupyter notebooks)
pip install -e .[dev]
```

### Development Environment

The project uses:

- **Python**: 3.11+ (required, <3.12)
- **Package Management**: pyproject.toml with hatchling build backend
- **Dependencies**: LangGraph, LangChain, OpenAI, PDF analysis tools (peepdf-3, pdfid, PyMuPDF)
- **Development**: Jupyter notebooks for prototyping and testing

### Running the System

```bash
# Main entry point for static analysis (from project root)
uv run python -m pdf_hunter.agents.static_analysis.graph

# Main entry point for preprocessing
uv run python -m pdf_hunter.agents.preprocessing.graph

# Alternative with editable install
uv pip install -e .
python -m pdf_hunter.agents.static_analysis.graph
python -m pdf_hunter.agents.preprocessing.graph

# Jupyter development
jupyter lab notebooks/development/
```

## Architecture Overview

### Core Components

**Orchestrator** (`src/pdf_hunter/orchestrator/`):

- Master coordination graph that manages the entire analysis workflow
- Currently placeholder with minimal implementation

**Preprocessing Agent** (`src/pdf_hunter/agents/preprocessing/`):

- Initial processing of PDF files before detailed analysis
- **Initialization Node**: Validates paths, calculates file hashes, and gets page count
- **Image Extraction Node**: Extracts images from pages, calculates perceptual hashes
- **URL Extraction Node**: Extracts URLs from annotations and text

**Static Analysis Agent** (`src/pdf_hunter/agents/static_analysis/`):

- Complete multi-node LangGraph implementation
- **Triage Node**: Initial PDF scanning using external tools (pdfid, pdf-parser, peepdf)
- **Investigator Subgraph**: Specialized missions for specific threats (OpenAction, JavaScript, etc.)
- **Reviewer Node**: Strategic analysis and evidence graph merging
- **Finalizer Node**: Comprehensive report generation

**Shared Components** (`src/pdf_hunter/shared/`):

- **Analyzers**: Wrappers and external PDF tools (pdf-parser.py, pdfid.py in `external/` subdirectory)
- **Utils**: Common utilities and helper functions
  - **file_operations.py**: File system operations (directory creation)
  - **hashing.py**: File hash calculation (SHA1, MD5)
  - **image_extraction.py**: PDF image extraction and processing
  - **url_extraction.py**: URL extraction from PDF annotations and text
- **Schemas**: Shared data models (placeholder)

**Archive** (`archive/`):

- Legacy tools and prompts from previous iterations
- Historical PDF analysis tools and utilities
- Old prompt templates and utility functions

### Key Data Structures

**Investigation Mission**: Single-focused tasks with threat types (OpenAction, JavaScript, AcroForm, etc.)
**Evidence Graph**: Nodes (PDF objects, artifacts, IOCs) and edges (relationships) representing the attack chain
**Mission Report**: Structured findings from individual investigations
**Final Report**: Executive summary, attack chain reconstruction, and IOCs

### Agent Workflow

1. **Preprocessing**: Extract basic data from PDF (images, URLs, hashes)
2. **Triage**: Scan PDF with multiple tools, classify as innocent/suspicious, generate missions
3. **Mission Dispatch**: Parallel investigation of specific threats
4. **Investigation**: Tool-assisted deep analysis of PDF objects and content
5. **Review**: Evidence graph merging, strategic assessment, additional mission generation
6. **Finalization**: Comprehensive report with verdict and actionable intelligence

## Configuration

### Environment Variables

Create `.env` file with:

```bash
OPENAI_API_KEY=your_key_here
```

### LLM Configuration

- **Default Model**: GPT-4.1 (configured in `src/pdf_hunter/config.py`)
- **Temperature**: 0.0 for consistent analysis
- All agents use the same model configuration for consistency

## Testing

### Test Files

- Sample PDFs in `tests/` directory
- Include both malicious and benign samples for validation
- Use files with known threat patterns for regression testing

### Notebook Development

- `notebooks/development/static_analysis.ipynb`: Static analysis development and testing notebook
- `notebooks/development/preprocessing.ipynb`: Preprocessing development and testing notebook
- Contains step-by-step agent execution and debugging
- Use for prototyping new features before integrating into main codebase

## File Organization

```bash
src/
└── pdf_hunter/              # Main package directory
    ├── agents/
    │   ├── preprocessing/       # Preprocessing agent implementation
    │   │   ├── graph.py         # LangGraph workflow definition
    │   │   ├── nodes.py         # Individual workflow nodes
    │   │   └── schemas.py       # State and data models
    │   ├── static_analysis/     # Main analysis agent implementation
    │   │   ├── graph.py         # LangGraph workflow definition
    │   │   ├── nodes.py         # Individual workflow nodes
    │   │   ├── schemas.py       # State and data models
    │   │   ├── prompts.py       # LLM prompts for each node
    │   │   └── tools.py         # LangChain tool implementations
    │   └── visual_analysis/     # Placeholder for future visual analysis
    ├── orchestrator/            # Master coordination
    │   ├── graph.py             # Main orchestrator workflow
    │   ├── nodes.py             # Orchestrator nodes
    │   └── schemas.py           # Orchestrator state schemas
    ├── shared/
    │   ├── analyzers/
    │   │   ├── external/        # External PDF tools (pdf-parser.py, pdfid.py)
    │   │   └── wrappers.py      # Python wrappers for external tools
    │   ├── schemas/             # Shared data models
    │   └── utils/               # Common utilities
    │       ├── file_operations.py # File system operations
    │       ├── hashing.py       # File hash calculation
    │       ├── image_extraction.py # PDF image extraction
    │       └── url_extraction.py # URL extraction from PDFs
    └── config.py                # Global configuration

archive/                     # Legacy code and tools
├── tools/                   # Old PDF analysis tools
├── *_prompts.py             # Historical prompt templates
└── utils.py                 # Legacy utilities

notebooks/                   # Jupyter development environment
├── development/             # Main development notebooks
│   ├── preprocessing.ipynb  # Preprocessing agent development
│   └── static_analysis.ipynb # Static analysis agent development
├── examples/                # Example usage
└── experiments/             # Experimental features

tests/                       # PDF samples and test data
├── agents/                  # Agent-specific tests
└── *.pdf                    # Sample PDF files

output/                      # Generated analysis reports
└── preprocessing_results/   # Results from preprocessing agent
```

## Development Patterns

### Adding New Threat Types

1. Update `ThreatType` enum in schemas
2. Add detection logic in triage prompts
3. Create specialized investigation prompts
4. Update evidence graph schema if needed

### Tool Integration

- Wrap external tools using LangChain's `@tool` decorator
- Implement safe command execution with timeouts
- Handle tool errors gracefully in agent flows

### State Management

- Use TypedDict for LangGraph state schemas
- Leverage `operator.add` for list aggregation across parallel nodes
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

## Security Considerations

This is a **defensive security tool** for PDF threat analysis. The codebase handles potentially malicious files safely through:

- Sandboxed PDF parsing using external tools
- No direct PDF execution or rendering
- Structured analysis without file modification
- Safe command execution with input validation
