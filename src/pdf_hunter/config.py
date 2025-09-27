from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()

# LLMs - Each agent and task has its own dedicated LLM instance
# Each model is optimized for specific analysis tasks and output formats

# === PREPROCESSING AGENT ===
# No LLM needed - handles image extraction and text parsing only

# === STATIC ANALYSIS AGENT ===
# Triage: Initial threat assessment from PDF structural data (pdfid, peepdf, pdf-parser)
# Output: Structured TriageReport with threat classification and mission dispatch
static_analysis_triage_llm = init_chat_model("openai:gpt-4o", temperature=0.0)

# Investigator: Deep threat analysis using PDF parser tools (with tool binding)
# Output: Structured MissionReport with evidence graphs and findings
# Note: Uses tools for dynamic PDF analysis (pdf-parser commands)
static_analysis_investigator_llm = init_chat_model("openai:gpt-4o", temperature=0.0)

# Graph Merger: Intelligent merging of evidence graphs from multiple investigations
# Output: Structured MergedEvidenceGraph with conflict resolution
static_analysis_graph_merger_llm = init_chat_model("openai:gpt-4o", temperature=0.0)

# Reviewer: Strategic analysis and mission coordination decisions
# Output: Structured ReviewerReport with investigation routing decisions
static_analysis_reviewer_llm = init_chat_model("openai:gpt-4o", temperature=0.0)

# Finalizer: Final threat assessment and autopsy report generation
# Output: Structured FinalReport with comprehensive analysis summary
static_analysis_finalizer_llm = init_chat_model("openai:gpt-4o", temperature=0.0)

# === VISUAL ANALYSIS AGENT ===
# Visual deception analysis of PDF page images with cross-page context
# Output: Structured PageAnalysisResult with visual forensic findings and URL prioritization
# Note: Processes base64 image data for visual threat detection
visual_analysis_llm = init_chat_model("openai:gpt-4o", temperature=0.0)

# === LINK ANALYSIS AGENT ===
# Investigator: Web reconnaissance using browser automation tools (with MCP tool binding)
# Output: Investigation logs and browser interaction results
# Note: Uses tools for web browsing, screenshots, and dynamic URL analysis
link_analysis_investigator_llm = init_chat_model("openai:gpt-4o", temperature=0.0)

# Analyst: Synthesis of link investigation findings and threat assessment
# Output: Structured AnalystFindings with URL reputation and threat indicators
link_analysis_analyst_llm = init_chat_model("openai:gpt-4o", temperature=0.0)

# === FINALIZER AGENT ===
# Reporter: Comprehensive markdown report generation from all agent findings
# Output: Natural language markdown report for human consumption
finalizer_llm = init_chat_model("openai:gpt-4o", temperature=0.0)

# Final Verdict: Authoritative malicious/benign classification decision
# Output: Structured FinalVerdict with confidence scores and reasoning
final_verdict_llm = init_chat_model("openai:gpt-4o", temperature=0.0)