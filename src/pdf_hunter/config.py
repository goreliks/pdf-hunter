from pathlib import Path
import os
import subprocess
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()

# === MODEL CONFIGURATION ===
# Choose your preferred model provider by uncommenting one section below

# Option 1: OpenAI (Recommended - most reliable)
openai_config = {
    "model": "gpt-4o",
    "model_provider": "openai",
    "temperature": 0.0
    }

# Option 2: Azure OpenAI (Azure-hosted OpenAI models)
azure_openai_config = {
    "model": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
    "temperature": 0.0,
    "model_provider": "azure_openai"
    }


# Option 3: Ollama (Local inference) - DISABLED
# model = "qwen2.5vl:7b"
# model_provider = "ollama"
# 
# if model_provider == "ollama":
#     # Auto-download model if needed
#     try:
#         subprocess.run(['ollama', 'pull', model], check=True, capture_output=True)
#         print("✅ Ollama model ready!")
#     except:
#         print("⚠️  Make sure Ollama is running: ollama serve")

# Option 4: vLLM (Direct model loading - no server needed) - DISABLED on macOS
# from vllm import LLM, SamplingParams
# model = "Qwen/Qwen2.5-VL-7B-Instruct"
# vllm_model = LLM(model=model, trust_remote_code=True)
# model_provider = "vllm"  # Custom handling needed

# === DUAL MODEL SETUP (OLLAMA ONLY) ===
# Uncomment when using Ollama for optimized model assignment
# text_model = "qwen2.5:7b"        # Regular Qwen2.5 for text-only tasks
# vision_model = "qwen2.5vl:7b"    # Qwen2.5-VL for vision tasks (PDF page analysis)
# 
# # Ensure both models are available in Ollama
# if model_provider == "ollama":
#     for model_name in [text_model, vision_model]:
#         try:
#             subprocess.run(['ollama', 'pull', model_name], check=True, capture_output=True)
#             print(f"✅ Ollama model {model_name} ready!")
#         except:
#             print(f"⚠️  Make sure Ollama is running and can pull {model_name}")
# 
# # Default model is text model (will be overridden for visual tasks)
# model = text_model



# === AZURE OPENAI CONFIGURATION ===
# Azure OpenAI works seamlessly with init_chat_model using model_provider="azure_openai"
# The function will automatically use Azure-specific parameters when this provider is specified

# LLMs - Each agent and task has its own dedicated LLM instance
# Each model is optimized for specific analysis tasks and output formats

# === PREPROCESSING AGENT ===
# No LLM needed - handles image extraction and text parsing only

# === STATIC ANALYSIS AGENT ===
# Triage: Maliciousness assessment based on static indicators 
# Output: Structured TriageResult with confidence scores and analysis guidance
static_analysis_triage_llm = init_chat_model(**azure_openai_config)

# Investigator: Deep dive into static file forensics using structured queries
# Output: Structured InvestigationResult with detailed technical findings
static_analysis_investigator_llm = init_chat_model(**azure_openai_config)

# Graph Merger: Merge overlapping findings into coherent analyses
# Output: Structured MergedFindings with unified threat assessments
static_analysis_graph_merger_llm = init_chat_model(**azure_openai_config)

# Reviewer: Strategic analysis and mission coordination decisions
# Output: Structured ReviewerReport with investigation routing decisions
static_analysis_reviewer_llm = init_chat_model(**azure_openai_config)

# Finalizer: Final threat assessment and autopsy report generation
# Output: Structured FinalReport with comprehensive analysis summary
static_analysis_finalizer_llm = init_chat_model(**azure_openai_config)

# === VISUAL ANALYSIS AGENT ===
# Visual deception analysis of PDF page images with cross-page context
# Output: Structured PageAnalysisResult with visual forensic findings and URL prioritization
# Note: Processes base64 image data for visual threat detection
visual_analysis_llm = init_chat_model(**azure_openai_config)

# === LINK ANALYSIS AGENT ===
# Investigator: Web reconnaissance using browser automation tools (with MCP tool binding)
# Output: Investigation logs and browser interaction results
# Note: Uses tools for web browsing, screenshots, and dynamic URL analysis
link_analysis_investigator_llm = init_chat_model(**azure_openai_config)

# Analyst: Synthesis of link investigation findings and threat assessment
# Output: Structured AnalystFindings with URL reputation and threat indicators
link_analysis_analyst_llm = init_chat_model(**azure_openai_config)

# === FINALIZER AGENT ===
# Reporter: Comprehensive markdown report generation from all agent findings
# Output: Natural language markdown report for human consumption
finalizer_llm = init_chat_model(**azure_openai_config)

# Final Verdict: Authoritative malicious/benign classification decision
# Output: Structured FinalVerdict with confidence scores and reasoning
final_verdict_llm = init_chat_model(**azure_openai_config)
