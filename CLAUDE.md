# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Hunter is a multi-agent AI framework for automated PDF threat hunting built using Python 3.11+ and LangGraph. The system uses AI-powered agents orchestrated via LangGraph to analyze potentially malicious PDFs and generate comprehensive security reports. The framework employs a sophisticated multi-agent orchestration pattern with specialized agents for PDF extraction, file analysis, image analysis, URL investigation, and report generation.

The framework is fully asynchronous, utilizing Python's async/await pattern for non-blocking I/O operations to ensure compatibility with LangGraph Studio and other event loop-based environments.

## Development Setup

### Installation

```bash
# Install dependencies using uv (preferred) 
uv sync

# For development features (Jupyter notebooks)
uv sync --group dev

# Optional: vLLM support (Linux/Windows only, not macOS)
uv sync --group vllm

# Install Playwright MCP dependency for link analysis
npm install
```

### Development Environment

The project uses:

- **Python**: 3.11+ (required, <3.12)
- **Package Management**: pyproject.toml with hatchling build backend, uv.lock for dependency management
- **LangGraph Platform**: Configured with langgraph.json for multi-graph deployment
- **AI Models**: OpenAI GPT-4o (default), with optional Ollama support for local inference
- **Dependencies**: LangGraph, LangChain, OpenAI, PDF analysis tools (peepdf-3, pdfid, PyMuPDF), computer vision (OpenCV, pyzbar for QR codes), MCP adapters for browser automation
- **Development**: Jupyter notebooks for prototyping and testing
- **Node.js**: Required for Playwright MCP server (@playwright/mcp)

### Model Configuration

The system supports multiple AI model providers configured in `src/pdf_hunter/config/models_config.py`:

**OpenAI (Default)**
- **Model**: GPT-4o 
- **Setup**: Requires `OPENAI_API_KEY` in `.env`
- **Advantages**: Most reliable, supports vision tasks, excellent reasoning
- **Usage**: Recommended for production use

**Azure OpenAI (Enterprise)**
- **Model**: GPT-4o (via Azure deployment)
- **Setup**: Requires Azure OpenAI resource and environment variables in `.env`:
  - `AZURE_OPENAI_ENDPOINT` - Your Azure endpoint URL
  - `AZURE_OPENAI_API_KEY` - Your Azure API key
  - `AZURE_OPENAI_DEPLOYMENT_NAME` - Your model deployment name
  - `AZURE_OPENAI_API_VERSION` - API version (optional)
- **Advantages**: Enterprise features, data residency, enhanced security
- **Usage**: For enterprise deployments requiring data governance

**Ollama (Local Inference)**
- **Models**: Qwen2.5:7b (text), Qwen2.5-VL:7b (vision)
- **Setup**: Install Ollama and uncomment Ollama configuration in config/models_config.py
- **Advantages**: Local inference, no API costs, dual-model optimization
- **Usage**: For development, privacy-sensitive environments, or cost optimization

To switch providers, update the LLM initializations in `src/pdf_hunter/config/models_config.py` to use the desired configuration dictionary (e.g., `openai_config`, `azure_openai_config`).

### Configuration Architecture

PDF Hunter uses a modular configuration system with centralized management:

**Configuration Package** (`src/pdf_hunter/config/`):
- **`models_config.py`**: LLM instances, provider settings, and model configurations
- **`execution_config.py`**: Recursion limits, runtime parameters, strategic reflection settings, and execution settings
- **`__init__.py`**: Centralized imports enabling clean `from pdf_hunter.config import ...`

**Recursion Limit Management**:
- **Orchestrator**: 30 steps (multi-agent coordination workflow)
- **File Analysis**: 25 steps (main agent) / 25 steps (investigator subgraph) for enhanced tool loops
- **Tool-using Agents**: 25 steps (for agent-tool interaction loops with strategic reflection)
- **Linear Agents**: 10-15 steps (simple sequential workflows)
- **Prevents infinite loops** while allowing sufficient iterations for complex analysis and strategic thinking

**Think Tool Integration**:
- **Strategic Reflection**: All investigative agents use the `think_tool` for systematic decision-making
- **Configuration**: Controlled via `THINKING_TOOL_ENABLED = True` flag in execution config
- **Usage Pattern**: Agents use think_tool after significant discoveries and at key decision points
- **Purpose**: Enhances investigation quality through deliberate pause-and-reflect patterns

**Usage Examples**:
```python
# Import execution configs, strategic reflection settings, and models together
from pdf_hunter.config import FILE_ANALYSIS_CONFIG, THINKING_TOOL_ENABLED, file_analysis_triage_llm

# Apply configuration to graphs
agent_graph = agent_graph.with_config(FILE_ANALYSIS_CONFIG)

# Conditional tool integration based on configuration
if THINKING_TOOL_ENABLED:
    from pdf_hunter.shared.tools.think_tool import think_tool
    tools.append(think_tool)
```

### Running the System

```bash
# Run the complete orchestrator (coordinates all agents)
uv run python -m pdf_hunter.orchestrator.graph

# Run individual agents in isolation
uv run python -m pdf_hunter.agents.pdf_extraction.graph
uv run python -m pdf_hunter.agents.image_analysis.graph
uv run python -m pdf_hunter.agents.file_analysis.graph
uv run python -m pdf_hunter.agents.url_investigation.graph
uv run python -m pdf_hunter.agents.report_generator.graph

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
- **Updated Workflow**: START → pdf_extraction → {file_analysis, image_analysis} → url_investigation → report_generator → END
- **Session Management**: Auto-generates session IDs and creates session-specific directories
- **State Management**: Aggregates results from all agents using LangGraph's additive list aggregation
- **Serialization**: Safe state serialization for persistence and debugging

**Agent 1: PDF Extraction** (`src/pdf_hunter/agents/pdf_extraction/`):
- **Purpose**: Extract safe, high-signal artifacts without executing content
- **Session Management**: Auto-generates session ID using `{sha1}_{timestamp}` format
- **Directory Creation**: Creates session-specific directory structure for organized output
- **Initialization Node**: Validates paths, calculates file hashes (SHA1/MD5), gets page count
- **Image Extraction Node**: Renders pages to images, calculates perceptual hashes (pHash), saves with pHash-based filenames
- **URL Extraction Node**: Extracts URLs from annotations and text with coordinates
- **QR Code Detection**: Detects QR codes in extracted images using OpenCV and pyzbar
- **Output**: File metadata, page images with pHash-based naming, URLs, QR code data, session directory

**Agent 2: File Analysis** (`src/pdf_hunter/agents/file_analysis/`):
- **Triage Node**: Multi-tool PDF scanning (pdfid, pdf-parser, peepdf)
- **Investigator Subgraph**: Parallel mission-based investigations with strategic reflection
- **Think Tool Integration**: Uses strategic reflection tool for enhanced decision-making during investigations
- **Reviewer Node**: Evidence graph merging and strategic analysis
- **Threat Detection**: OpenAction, JavaScript, AcroForm, EmbeddedFile analysis
- **Improved Logging**: Tool usage now visible at INFO level for better investigation transparency
- **State Persistence**: Automatic final state saving for debugging and analysis tracking
- **Output**: Evidence graph, mission reports, structural analysis, persistent state files

**Agent 3: Image Analysis** (`src/pdf_hunter/agents/image_analysis/`):
- **Enhanced VDA Persona**: Visual Deception Analyst combining HCI/UX security, cognitive psychology, and digital forensics
- **Core Analysis**: Visual-technical cross-examination for deception detection
- **Page-Level Analysis**: Examines visual presentation vs. technical elements
- **Cross-Page Context**: Maintains coherence analysis across document pages
- **URL Prioritization**: Ranks URLs for deeper investigation based on visual context
- **Status Tracking**: URLs generated with `NEW` status for downstream processing
- **Output**: Deception tactics, benign signals, prioritized URLs with status tracking for link analysis

**Agent 4: URL Investigation** (`src/pdf_hunter/agents/url_investigation/`):
- **NEW AGENT**: Dedicated deep analysis of URLs identified by image analysis
- **MCP Integration**: Uses Playwright MCP server for browser automation with proper syntax enforcement
- **Browser Tool Syntax**: Uses arrow function format for `browser_evaluate`: `() => document.body.innerText`
- **Strategic Reflection**: Integrated think_tool for systematic investigation planning and assessment
- **URL Status Management**: Filters and updates URL mission status (`IN_PROGRESS`, `NOT_RELEVANT`)
- **Link Investigator**: Automated web reconnaissance of suspicious URLs with enhanced logging
- **Analyst Node**: Structured analysis of link findings, updates final status (`COMPLETED`/`FAILED`)
- **Loop Prevention**: Status tracking prevents duplicate analysis of completed URLs
- **State Persistence**: Automatic state saving for debugging and recovery
- **Output**: URL reputation, content analysis, threat indicators, persistent state files with status

**Agent 5: Report Generator** (`src/pdf_hunter/agents/report_generator/`):
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

**Strategic Reflection Tool** (`src/pdf_hunter/shared/tools/think_tool.py`):
- **Purpose**: Systematic strategic reflection during investigation workflows
- **Implementation**: LangChain tool with `@tool(parse_docstring=True)` decorator
- **Configuration**: Controlled via `THINKING_TOOL_ENABLED` flag in execution config
- **Usage Pattern**: Agents invoke after significant discoveries, before major decisions, and at investigation transitions
- **Integration**: Automatically added to tool manifests when enabled
- **Benefits**: Enhances investigation quality through deliberate pause-and-reflect methodology

### Key Data Structures

- **Investigation Mission**: Focused threat-specific analysis tasks
- **Evidence Graph**: Structured representation of PDF attack chains
- **Visual Analysis Report**: Deception tactics and authenticity signals
- **Link Analysis Report**: URL reconnaissance and threat assessment
- **Final Report**: Executive summary with verdict and IOCs
- **Prioritized URLs**: Ranked list of links for deeper investigation with status tracking

### Enhanced Investigation Patterns

**Strategic Reflection Integration**:
- **Think Tool Usage**: All investigative agents use `think_tool` for systematic decision-making
- **Reflection Triggers**: After significant discoveries, before major decisions, at investigation transitions
- **Quality Enhancement**: Deliberate pause-and-reflect patterns improve investigation thoroughness
- **Configuration**: Controlled via `THINKING_TOOL_ENABLED` flag for optional deployment

**Improved Investigation Transparency**:
- **Enhanced Logging**: Tool execution logging elevated to INFO level for better visibility
- **Tool Name Tracking**: All tool invocations now visible in standard logs without debug mode
- **Investigation Flow**: Clear visibility into agent decision-making and tool selection patterns
- **Strategic Reflection Tracking**: Easy identification of when agents use think_tool for reflection

#### Critical Development Patterns

### Browser Tool Syntax Requirements
URLs flow through browser automation using MCP Playwright integration:
```python
# CORRECT browser_evaluate syntax (arrow function)
{"function": "() => document.body.innerText"}
{"function": "() => document.title"}

# INCORRECT syntax (will fail)
{"function": "return document.body.innerText;"}
{"function": "document.body.innerText"}
```
- Prompt explicitly specifies arrow function format to ensure LLM generates correct syntax
- Browser tools execute sequentially for MCP session safety
- Multiple tool calls per investigation turn provide comprehensive evidence collection

### URL Status Tracking System

**URLMissionStatus Enum** (`src/pdf_hunter/agents/image_analysis/schemas.py`):
- `NEW`: URLs initially flagged by visual analysis (default state)
- `IN_PROGRESS`: URLs currently being analyzed by link analysis agent
- `COMPLETED`: URLs successfully analyzed with findings
- `FAILED`: URLs that could not be analyzed due to errors
- `NOT_RELEVANT`: Low-priority URLs not selected for analysis

**Status Workflow**:
1. **Image Analysis**: Generates `PrioritizedURL` objects with `NEW` status
2. **URL Investigation Filter**: Updates status to `IN_PROGRESS` (priority ≤ 5) or `NOT_RELEVANT` (priority > 5)
3. **URL Investigation Completion**: Analyst node updates to `COMPLETED` or `FAILED` based on analysis outcome
4. **State Persistence**: Status tracked in session files for loop prevention and debugging

### Complete Agent Workflow

1. **PDF Extraction**: Extract metadata, images, URLs, QR codes from PDF
2. **File Analysis**: Multi-tool scanning, mission dispatch, evidence gathering
3. **Image Analysis**: Visual deception detection, URL prioritization (runs in parallel with file analysis)
4. **URL Investigation**: Deep reconnaissance of prioritized URLs using browser automation
5. **Report Generation**: Comprehensive report synthesis, final verdict, file output

The orchestrator coordinates all five agents in a sophisticated pipeline with parallel processing where appropriate.

### URL Status Tracking Workflow

**Detailed URL Lifecycle Management:**

1. **PDF Extraction Stage**:
   - URLs extracted from PDF annotations and text
   - QR codes detected and decoded to URLs
   - All URLs stored as `ExtractedURL` objects (no status tracking at this stage)

2. **Image Analysis Stage**:
   - LLM analyzes visual context and generates `PrioritizedURL` objects
   - Each URL assigned priority (1=highest, 5=lowest) and contextual reasoning
   - All URLs initialized with `mission_status = NEW`
   - URLs aggregated into `image_analysis_report.all_priority_urls`

3. **URL Investigation Filter Stage** (`filter_high_priority_urls`):
   - Processes URLs from image analysis report
   - **High Priority URLs** (priority ≤ 5): Status updated to `IN_PROGRESS`
   - **Low Priority URLs** (priority > 5): Status updated to `NOT_RELEVANT`
   - Only high priority URLs dispatched for deep analysis

4. **URL Investigation Stage**:
   - Each high priority URL analyzed in parallel using browser automation
   - MCP tools perform web reconnaissance, screenshot capture, domain analysis
   - Investigation logs captured for analyst review

5. **URL Investigation Completion Stage** (`analyst_node`):
   - Analyst LLM synthesizes investigation findings
   - Status updated based on analysis outcome:
     - `COMPLETED`: Successful analysis with findings
     - `FAILED`: Analysis failed due to technical errors or inaccessible URLs
   - Final URL status persisted in `URLAnalysisResult`

**Loop Prevention Benefits:**
- Status tracking enables future enhancements for iterative analysis
- Completed URLs can be skipped in subsequent runs  
- Failed URLs can be retried with different strategies
- Analysis progress visible in debugging and state files

## Configuration

### Environment Variables

Create `.env` file with your chosen AI provider configuration:

**For OpenAI:**
```bash
OPENAI_API_KEY=your_key_here
```

**For Azure OpenAI:**
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_key_here
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

### LangGraph Platform

The system is configured for LangGraph Platform deployment with `langgraph.json`:
- **file_analysis**: File analysis graph endpoint
- **pdf_extraction**: PDF extraction graph endpoint  
- **orchestrator**: Main orchestrator graph endpoint
- **url_investigation**: URL investigation graph endpoint

### LLM Configuration

- **Default Model**: GPT-4o (configured in `src/pdf_hunter/config/models_config.py`)
- **Temperature**: 0.0 for consistent, deterministic analysis
- **Agent-Specific Models**: Each agent and task has dedicated LLM instances for optimal performance

#### LLM Specialization by Task Type:

**Tool-Using Models** (Function Calling Optimized):
- `file_analysis_investigator_llm`: PDF parser tool binding for deep analysis
- `url_investigation_investigator_llm`: Browser automation and MCP tool binding

**Structured Output Models** (Pydantic Schema Generation):
- All triage, analysis, and verdict models use structured output for consistent data formats
- Graph merger models for intelligent evidence consolidation

**Natural Language Generation**:
- `report_generator_llm`: Human-readable markdown report generation
- Report synthesis models for executive summaries

**Analysis vs. Synthesis Models**:
- **Analysis Models**: Process raw data (triage, investigation)
- **Synthesis Models**: High-level reasoning and decision making (reviewer, analyst, report generator)

## Testing

### Test Files

Sample files are organized in subdirectories under `tests/assets/`:
- `tests/assets/pdfs/`: Contains PDF test files
  - `hello_qr.pdf` / `hello_qr_and_link.pdf`: QR code test cases
  - `test_mal_one.pdf`: Malicious PDF sample
  - Various threat pattern samples for regression testing
- `tests/assets/images/`: Contains test images
  - `qrmonkey.jpg`: QR code test image

All agent modules use cross-platform path handling to reference these test files, ensuring compatibility across Windows, Linux, and macOS systems.

### Notebook Development

- `notebooks/development/static_analysis.ipynb`: File analysis agent development
- `notebooks/development/preprocessing.ipynb`: PDF extraction development  
- `notebooks/development/link_analysis_agent.ipynb`: URL investigation development
- Step-by-step agent execution and debugging capabilities
- Prototype new features before integration

## File Organization

```bash
src/
└── pdf_hunter/              # Main package directory
    ├── agents/
    │   ├── pdf_extraction/      # PDF extraction agent
    │   │   ├── graph.py         # LangGraph workflow definition
    │   │   ├── nodes.py         # Individual workflow nodes
    │   │   └── schemas.py       # State and data models
    │   ├── file_analysis/       # File analysis agent
    │   │   ├── graph.py         # LangGraph workflow definition
    │   │   ├── nodes.py         # Individual workflow nodes
    │   │   ├── schemas.py       # State and data models
    │   │   ├── prompts.py       # LLM prompts for each node
    │   │   └── tools.py         # LangChain tool implementations
    │   ├── image_analysis/      # Image analysis agent
    │   │   ├── graph.py         # LangGraph workflow definition
    │   │   ├── nodes.py         # Individual workflow nodes
    │   │   ├── prompts.py       # Enhanced VDA prompts
    │   │   └── schemas.py       # State and data models
    │   ├── url_investigation/   # NEW - URL investigation agent
    │   │   ├── graph.py         # URL investigator graph
    │   │   ├── nodes.py         # URL investigation nodes
    │   │   ├── prompts.py       # URL investigation prompts
    │   │   ├── schemas.py       # URL investigation schemas
    │   │   ├── sync_runner.py   # Synchronous execution wrapper
    │   │   └── tools.py         # MCP tools for browser automation
    │   └── report_generator/    # NEW - Report generation agent
    │       ├── graph.py         # Report generator workflow
    │       ├── nodes.py         # Report generation nodes
    │       ├── prompts.py       # Final report prompts
    │       └── schemas.py       # Report generator schemas
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
    └── config/                  # Configuration package
        ├── __init__.py          # Centralized imports
        ├── execution_config.py  # Recursion limits & runtime settings
        └── models_config.py     # LLM instances & provider settings

notebooks/                   # Jupyter development environment
├── development/             # Main development notebooks
│   ├── preprocessing.ipynb  # PDF extraction agent development
│   ├── static_analysis.ipynb # File analysis agent development
│   └── link_analysis_agent.ipynb # URL investigation development
├── examples/                # Example usage
└── experiments/             # Experimental features

tests/                       # Test assets and code
├── agents/                  # Agent-specific test code
├── assets/                  # Organized test assets
│   ├── pdfs/                # PDF test files
│   │   ├── hello_qr.pdf     # QR code test samples
│   │   ├── hello_qr_and_link.pdf
│   │   ├── test_mal_one.pdf # Malicious PDF sample
│   │   └── *.pdf            # Additional test PDFs
│   └── images/              # Test images
│       └── qrmonkey.jpg     # QR code test image

output/                      # Generated analysis reports (session-based organization)
├── {sha1}_{timestamp}/  # Session-specific directory for each PDF analysis
│   ├── pdf_extraction/      # PDF extraction agent outputs
│   │   └── extracted_images/
│   ├── file_analysis/       # File analysis outputs and state files
│   │   └── file_analysis_final_state_session_{sha1}_{timestamp}.json
│   ├── image_analysis/      # Image analysis outputs (when run standalone)
│   ├── url_investigation/   # URL investigation artifacts
│   │   └── task_url_XXX/    # Task-specific browser screenshots and analysis
│   └── report_generator/    # Final reports and state files
│       ├── final_report_session_{sha1}_{timestamp}.md
│       └── final_state_session_{sha1}_{timestamp}.json
└── mcp_outputs/             # Legacy MCP output directory (for standalone usage)

.langgraph_api/             # LangGraph Platform state
├── .langgraph_checkpoint.*.pckl  # Checkpoint files
└── *.pckl                  # Platform state files
```

## Development Patterns

### Cross-Platform Path Handling

All agent modules use platform-independent path construction to ensure compatibility across Windows, Linux, and macOS:

```python
import os

# Get the module's directory
module_dir = os.path.dirname(os.path.abspath(__file__))

# Navigate up to the project root
project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))

# Construct path to test file using os.path.join
file_path = os.path.join(project_root, "tests", "assets", "pdfs", "test_file.pdf")
```

This approach ensures that:
- Paths work correctly on Windows (backslash), Linux/macOS (forward slash)
- Files are referenced relative to the module location, not absolute paths
- The code is portable across different development environments

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
- **Module execution**: Run with `python -m pdf_hunter.agents.file_analysis.graph`

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

### LLM Architecture
- **LangChain Integration**: Unified LLM interface with `init_chat_model`
- **Specialized Models**: Each analysis task uses dedicated LLM instances (10 total)
- **Multi-Provider Support**: OpenAI GPT-4o (default) with Ollama support for local inference
- **Dual-Model Optimization**: When using Ollama, supports separate models for text (Qwen2.5:7b) and vision (Qwen2.5-VL:7b) tasks
- **Function Calling**: Tool-using models optimized for PDF analysis and web reconnaissance
- **Structured Output**: Pydantic schema generation for consistent data formats
- **Clean Dependencies**: Removed Hugging Face transformers/torch dependencies for simplified deployment

## Recent Architecture Improvements

### Async/Await Implementation (September 2025)
- **Non-blocking Architecture**: Converted all node functions to async to prevent blocking errors in LangGraph Studio
- **Consistent Async Pattern**: All LLM calls now use await llm.ainvoke() instead of llm.invoke()
- **Async File Operations**: Using asyncio.to_thread to wrap synchronous file I/O operations
- **Asynchronous Subprocess Execution**: Subprocess calls wrapped with asyncio.to_thread to avoid blocking
- **MCP Integration**: Improved MCP client with async patterns for better browser automation
- **I/O Safety**: All file creation, reading, and writing operations now follow non-blocking patterns
- **State Persistence**: Updated serializer utility for async file operations
- **Enhanced Compatibility**: Full LangGraph Studio compatibility for complex agent workflows

### Error Collection Standardization (September 2025)
- **Consistent Error Fields**: Standardized all agent schemas to use `errors: Annotated[List[str], operator.add]`
- **Orchestrator Error Aggregation**: Maintains `errors: Annotated[List[list], operator.add]` for collecting agent error groups
- **Removed NotRequired**: Eliminated inconsistent `NotRequired` usage from error fields across all agents
- **Import Path Fixes**: Resolved Pydantic enum serialization warnings by using consistent import paths
- **Enhanced Debugging**: Grouped error collection provides better agent traceability for complex multi-agent workflows
- **State Validation**: All agents now guarantee error field presence for reliable error propagation

### Model Configuration Overhaul (September 2025)
- **Simplified Providers**: Moved from complex multi-provider setup to clean OpenAI default + Ollama option
- **Dependency Cleanup**: Removed all Hugging Face transformers, torch, and accelerate dependencies
- **Dual-Model Support**: Added support for specialized text/vision models when using Ollama
- **Configuration Centralization**: All model settings managed in `src/pdf_hunter/config/models_config.py`
- **Flexible Switching**: Easy provider switching via configuration comments

### Strategic Reflection Integration (September 2025)
- **Think Tool Implementation**: Added systematic strategic reflection tool for investigation enhancement
- **Configuration Control**: `THINKING_TOOL_ENABLED` flag in execution config for optional deployment
- **Agent Integration**: Automatic tool integration into file analysis and URL investigation agents
- **Investigation Quality**: Deliberate pause-and-reflect methodology for enhanced decision-making
- **Usage Pattern**: Strategic reflection after significant discoveries and at key decision points

### Investigation Transparency Improvements (September 2025)
- **Enhanced Tool Logging**: Elevated tool execution logging from DEBUG to INFO level
- **Tool Name Visibility**: All tool calls now visible in standard logs without debug mode
- **Strategic Reflection Tracking**: Clear visibility of think_tool usage for quality assessment
- **Investigation Flow Transparency**: Tool selection patterns and decision points traceable
- **Recursion Limit Adjustments**: Increased file analysis limits to 25 steps for enhanced tool loops

### Performance Optimizations
- **Cleaner Dependencies**: Reduced package size by removing unused ML dependencies
- **Local Inference Option**: Ollama support enables offline/private deployments
- **Task-Specific Models**: Vision tasks can use specialized VL models for better accuracy

## Security Considerations

This is a **defensive security tool** for PDF threat analysis. The codebase handles potentially malicious files safely through:

- Sandboxed PDF parsing using external tools
- No direct PDF execution or rendering  
- Structured analysis without file modification
- Safe command execution with input validation
- Browser automation in isolated environments via MCP
- Secure state serialization excluding sensitive session data

## Logging System

The project uses a centralized logging system implemented in `src/pdf_hunter/shared/utils/logging_config.py`:

- **Hierarchical Loggers**: Named loggers matching Python module hierarchy
- **Configurable Levels**: Supports DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Enhanced Tool Visibility**: Tool execution logging elevated to INFO level for better investigation tracking
- **Consistent Formatting**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **File Logging**: Optional log file output with session-based naming
- **Console Output**: Standard output to console with proper formatting

### Tool Execution Transparency

Recent improvements provide better visibility into agent tool usage:

- **Tool Names at INFO Level**: All tool calls now logged at INFO level, visible in standard logs
- **Strategic Reflection Tracking**: think_tool usage clearly visible for investigation quality assessment
- **Investigation Flow Visibility**: Tool selection patterns and decision points traceable in logs
- **No Debug Mode Required**: Tool visibility available in production INFO-level logging

### Using the Logging System

```python
# Import logging utilities at the top of each module
from pdf_hunter.shared.utils.logging_config import get_logger

# Create a module-specific logger
logger = get_logger(__name__)

# Use appropriate log levels
logger.debug("Detailed debugging information")
logger.info("General operational information")
logger.warning("Warning situations that should be addressed")
logger.error("Error events that might still allow the application to continue")
logger.critical("Very serious error events that might cause the application to terminate")

# Conditional verbose logging
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"Detailed object state: {complex_object}")
```

### Configuring Logging

The orchestrator automatically configures logging when run. For individual agent testing or custom needs:

```python
from pdf_hunter.shared.utils.logging_config import configure_logging

# Default configuration (INFO level, console only)
configure_logging()

# Debug level with file output
configure_logging(level=logging.DEBUG, log_to_file=True)

# Session-specific logging
configure_logging(log_to_file=True, session_id=session_id)
```

## Important Implementation Reminders

- **Never create files unless absolutely necessary** - always prefer editing existing files
- **Follow existing code patterns** - examine neighboring files for conventions
- **Use safe serialization** - leverage `serialize_state_safely()` for complex state
- **Handle MCP sessions properly** - use context managers and task isolation
- **Test with sample PDFs** - use files in `tests/` directory for validation
- **Maintain agent isolation** - each agent should be runnable independently
- **Follow LangGraph patterns** - use proper state management and edge definitions
- **Use proper logging** - leverage the logging system instead of print statements