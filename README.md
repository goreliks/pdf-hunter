# 🕵️ PDF Hunter

**Advanced Multi-Agent AI Framework for PDF Threat Analysis**

PDF Hunter is a sophisticated threat hunting framework that uses multiple AI agents to analyze potentially malicious PDFs. Built with Python 3.11+ and LangGraph, it employs a multi-agent orchestration pattern with specialized agents for comprehensive PDF analysis and automated report generation.

## 🎯 Core Philosophy

The system operates under three core principles:

1. **Autonomy is Disease**: Any automatic action capability in a PDF (e.g., /OpenAction, /JavaScript, /Launch, /AA, /EmbeddedFile) is high-signal and prioritized for investigation
2. **Deception is Confession**: Visual and structural inconsistencies are treated as confessions of malicious intent  
3. **Incoherence is a Symptom**: Cross-page and cross-modal incoherence elevates suspicion

## 🏗️ Architecture Overview

PDF Hunter uses a sophisticated 5-agent pipeline orchestrated via LangGraph:

```mermaid
graph TD
    A[📄 PDF Input] --> B[🔍 PDF Extraction Agent]
    B --> C[🧬 File Analysis Agent]
    B --> D[👁️ Image Analysis Agent]
    C --> E[🌐 URL Investigation Agent]
    D --> E
    E --> F[📊 Report Generator Agent]
    F --> G[📋 Final Report]
```

### Agent Capabilities

- **🔍 PDF Extraction**: Extract metadata, images, URLs, QR codes safely
- **🧬 File Analysis**: Multi-tool PDF scanning with mission-based investigations  
- **👁️ Image Analysis**: Visual deception detection and URL prioritization
- **🌐 URL Investigation**: Automated web reconnaissance of suspicious URLs
- **📊 Report Generator**: Comprehensive report generation and final verdict

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.11+ (required, <3.12)
- **Node.js**: 16+ (for Playwright MCP server)
- **uv**: Python package manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/goreliks/pdf-hunter.git
   cd pdf-hunter
   ```

2. **Install Python dependencies**
   ```bash
   # Basic installation
   uv sync
   
   # With development tools (Jupyter notebooks)
   uv sync --group dev
   
   # Optional: vLLM support (Linux/Windows only)
   uv sync --group vllm
   ```

3. **Install Node.js dependencies** 
   ```bash
   npm install
   ```

4. **Configure environment variables**
   ```bash
   cp .env-example .env
   # Edit .env with your API keys
   ```

### Environment Configuration

Create a `.env` file with the required variables for your chosen AI provider:

**For OpenAI (Default):**
```bash
# Required: OpenAI API key for LLM operations
OPENAI_API_KEY="your_openai_api_key_here"
```

**For Azure OpenAI (Enterprise):**
```bash
# Required: Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_OPENAI_API_KEY="your_azure_openai_api_key_here"
AZURE_OPENAI_DEPLOYMENT_NAME="your_deployment_name_here"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"  # Optional
```

**Optional: Advanced features**
```bash
ANTHROPIC_API_KEY="your_anthropic_api_key_here"
LANGSMITH_API_KEY="your_langsmith_api_key_here"
LANGSMITH_TRACING_V2=true
LANGSMITH_PROJECT="pdf-hunter"
TAVILY_API_KEY="your_tavily_api_key_here"
```

### Model Configuration

PDF Hunter supports multiple AI model providers:

**🤖 OpenAI (Default)**
- Uses `gpt-4o` for all analysis tasks
- Requires OpenAI API key
- Best reliability and performance

**☁️ Azure OpenAI (Enterprise)**
- Uses `gpt-4o` via Azure deployment
- Requires Azure OpenAI resource and configuration
- Enterprise features, data residency, enhanced security
- Ideal for corporate deployments

**🏠 Ollama (Local Alternative)**
- Uses Qwen2.5:7b and Qwen2.5-VL:7b locally
- No API keys required
- Edit `src/pdf_hunter/config.py` to enable

To switch between providers, update the LLM initializations in `src/pdf_hunter/config.py` to use the desired configuration dictionary (e.g., `openai_config`, `azure_openai_config`).

## 🎮 Usage

### Basic Analysis

Analyze a PDF with the complete orchestrator:

```bash
# Run full analysis pipeline
uv run python -m pdf_hunter.orchestrator.graph
```

### Individual Agent Testing

Run agents in isolation for development and testing:

```bash
# Test individual agents
uv run python -m pdf_hunter.agents.pdf_extraction.graph
uv run python -m pdf_hunter.agents.file_analysis.graph
uv run python -m pdf_hunter.agents.image_analysis.graph
uv run python -m pdf_hunter.agents.url_investigation.graph
uv run python -m pdf_hunter.agents.report_generator.graph
```

### LangGraph Platform Deployment

Deploy all graphs as APIs:

```bash
langgraph up
```

This starts a web server with endpoints for each agent graph.

### Development Environment

Launch Jupyter for interactive development:

```bash
jupyter lab notebooks/development/
```

## 📁 Output Organization

PDF Hunter creates session-based output directories:

```
output/
├── {sha1}_{timestamp}/          # Session-specific analysis
│   ├── pdf_extraction/          # Extracted images, metadata
│   ├── file_analysis/           # Evidence graphs, mission reports
│   ├── image_analysis/          # Visual deception analysis
│   ├── url_investigation/       # URL reconnaissance reports
│   └── report_generator/        # Final reports and verdicts
│       ├── final_report_session_{id}.md
│       └── final_state_session_{id}.json
```

## 🔧 Configuration

### Logging Configuration

PDF Hunter includes a centralized logging system:

```python
# In any module:
from pdf_hunter.shared.utils.logging_config import get_logger

# Create a module-specific logger
logger = get_logger(__name__)

# Use appropriate log levels
logger.info("Starting process")
logger.warning("Potential issue detected")
logger.error("Error occurred", exc_info=True)
```

Configure logging levels for more detailed output:

```python
from pdf_hunter.shared.utils.logging_config import configure_logging
import logging

# Default configuration (INFO level)
configure_logging()

# Debug level with file output for troubleshooting
configure_logging(level=logging.DEBUG, log_to_file=True)
```

Log files are stored in a `logs/` directory with naming pattern `pdf_hunter_{session_id}_{timestamp}.log`.

### LLM Configuration

PDF Hunter uses 10 specialized LLM instances optimized for different tasks:

- **Tool-Using Models**: Function calling for PDF analysis and web reconnaissance
- **Structured Output Models**: Pydantic schema generation for consistent data
- **Analysis Models**: Raw data processing (triage, investigation)
- **Synthesis Models**: High-level reasoning (review, finalization)

Configure in `src/pdf_hunter/config.py`:

```python
# Example: Switch to Ollama for local inference
# Uncomment Ollama configuration and update LLM initializations:
# file_analysis_triage_llm = init_chat_model(**ollama_config)
```

### Platform Configuration

LangGraph platform configuration in `langgraph.json`:

```json
{
    "dependencies": ["."],
    "graphs": {
        "file_analysis": "pdf_hunter.agents.file_analysis.graph:file_analysis_graph",
        "pdf_extraction": "pdf_hunter.agents.pdf_extraction.graph:pdf_extraction_graph", 
        "orchestrator": "pdf_hunter.orchestrator.graph:orchestrator_graph",
        "url_investigation": "pdf_hunter.agents.url_investigation.graph:url_investigation_graph"
    },
    "env": ".env"
}
```

## 🧪 Testing

### Sample PDFs

Test files are included in `tests/`:

- `hello_qr.pdf` / `hello_qr_and_link.pdf`: QR code test cases
- `test_mal_one.pdf`: Malicious PDF sample
- Various threat pattern samples for regression testing

### Running Tests

```bash
# Run unit tests (when available)
uv run pytest

# Test individual components
uv run python -m pdf_hunter.agents.pdf_extraction.graph
```

## 🛠️ Development

### Architecture

- **src-layout**: Standard Python package structure
- **LangGraph**: Multi-agent workflow orchestration
- **Pydantic**: Type-safe data models and validation
- **MCP**: Browser automation via Model Context Protocol

### Key Dependencies

**Core Framework:**
- **LangGraph**: Multi-agent orchestration
- **LangChain**: LLM integration and tool binding
- **Pydantic**: Data validation and schemas

**PDF Analysis:**
- **PyMuPDF**: PDF rendering and content extraction
- **peepdf-3**: Enhanced PDF structure analysis
- **pdfid**: PDF structure scanning

**Computer Vision:**
- **OpenCV**: Image processing and QR code detection
- **pyzbar**: QR/barcode decoding
- **Pillow**: Image manipulation
- **imagehash**: Perceptual hashing

**Browser Automation:**
- **@playwright/mcp**: MCP server for browser automation
- **langchain-mcp-adapters**: MCP integration with LangChain

### Development Workflow

1. **Setup development environment**
   ```bash
   uv sync --all-groups
   uv pip install -e .[dev]
   ```

2. **Use Jupyter notebooks for prototyping**
   ```bash
   jupyter lab notebooks/development/
   ```

3. **Test individual agents before integration**

4. **Follow existing patterns for new agents**

## 🔒 Security Considerations

PDF Hunter is a **defensive security tool** designed for safe PDF analysis:

- ✅ Sandboxed PDF parsing using external tools
- ✅ No direct PDF execution or rendering
- ✅ Structured analysis without file modification  
- ✅ Safe command execution with input validation
- ✅ Browser automation in isolated MCP environments
- ✅ Secure state serialization excluding sensitive data

## 📊 Features

### Advanced Capabilities

- **🎯 Multi-Modal Analysis**: Combines structural, visual, and behavioral analysis
- **🤖 AI-Powered Insights**: 10 specialized LLMs for different analysis tasks
- **🔄 Parallel Processing**: Concurrent analysis for improved performance
- **📈 Evidence Graphs**: Structured representation of attack chains
- **🌐 Web Reconnaissance**: Automated URL investigation with MCP Playwright integration
- **📋 Executive Reports**: Human-readable analysis summaries
- **🔍 QR Code Detection**: Automated QR code extraction and analysis
- **💾 State Persistence**: Complete analysis state saving for debugging

### Threat Detection

- **Autonomy Features**: JavaScript, OpenAction, Launch actions, Auto-Actions
- **Embedded Content**: Files, forms, multimedia elements
- **Visual Deception**: Layout inconsistencies, social engineering tactics
- **URL Analysis**: Link reputation, redirection chains, threat indicators
- **Structural Anomalies**: PDF structure irregularities and malformations

## 📚 Documentation

- **CLAUDE.md**: Complete developer guide and architecture documentation
- **notebooks/**: Interactive development and testing examples
- **src/pdf_hunter/**: Inline code documentation and type hints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the ISC License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://www.langchain.com/langgraph) for multi-agent orchestration
- Uses [OpenAI GPT-4o](https://openai.com/) for AI-powered analysis
- PDF analysis powered by [PyMuPDF](https://pymupdf.readthedocs.io/) and [peepdf](https://eternal-todo.com/tools/peepdf-pdf-analysis-tool)
- Browser automation via [Playwright MCP](https://github.com/microsoft/playwright-mcp)

---

**⚠️ Disclaimer**: PDF Hunter is designed for defensive security analysis. Always analyze suspicious files in isolated environments and follow your organization's security policies.
