"""
Execution Configuration for PDF Hunter Agents

This module defines recursion limits and execution parameters for all agents
in the PDF Hunter system. These limits prevent infinite loops while allowing
sufficient iterations for complex analysis tasks.

Recursion Limit Guidelines:
- Orchestrator: 25-50 (orchestrates multiple agents)
- Linear Agents: 10-15 (simple sequential workflows) 
- Tool-using Agents: 15-25 (agent-tool interaction loops)
- Complex Analysis: 20-30 (multiple investigation rounds)
"""

# General Configuration
MAXIMUM_PAGES_TO_PROCESS = 4  # Cap on pages to process for performance

# -- LLM TIMEOUT CONFIGURATION --
# Timeout values (in seconds) for LLM API calls to prevent infinite hangs
# Increased TEXT timeout to 120s to accommodate complex operations like report generation
LLM_TIMEOUT_TEXT = 120    # Timeout for text-only LLM calls (triage, investigator, analyst, etc.)
LLM_TIMEOUT_VISION = 120  # Timeout for vision LLM calls (image analysis with base64 images)

# -- ORCHESTRATOR CONFIGURATION --
# Controls the overall workflow: pdf_extraction → {file_analysis || image_analysis} → url_investigation → report_generator
ORCHESTRATOR_CONFIG = {
    "run_name": "PDF Hunter Orchestrator",
    "recursion_limit": 30  # Higher limit for multi-agent coordination
}

# -- PDF EXTRACTION AGENT CONFIGURATION --
# Pure utility agent (no LLM) - extracts images, URLs, QR codes
PDF_EXTRACTION_CONFIG = {
    "run_name": "PDF Extraction Agent",
    "recursion_limit": 10  # Simple linear workflow
}

# -- FILE ANALYSIS AGENT CONFIGURATION --
THINKING_TOOL_ENABLED = True  # Enable the "Think" tool in file analysis agent


# Static analysis with tool-using investigator subgraphs
FILE_ANALYSIS_CONFIG = {
    "run_name": "File Analysis Agent", 
    "recursion_limit": 25  # Multiple investigation missions possible
}

# Investigator subgraph within file analysis (tool loops)
FILE_ANALYSIS_INVESTIGATOR_CONFIG = {
    "run_name": "PDF Investigation Tools",
    "recursion_limit": 25  # investigation → tools → investigation loops
}

# -- IMAGE ANALYSIS AGENT CONFIGURATION --
# Visual deception analysis with LLM reasoning
IMAGE_ANALYSIS_CONFIG = {
    "run_name": "Visual Analysis Agent",
    "recursion_limit": 15  # Per-page analysis workflow
}

# -- URL INVESTIGATION AGENT CONFIGURATION --
# Browser automation with tool loops per URL
URL_INVESTIGATION_CONFIG = {
    "run_name": "URL Investigation Agent",
    "recursion_limit": 25  # Multiple URL analysis in parallel
}

# URL investigator subgraph (browser tool loops)
URL_INVESTIGATION_INVESTIGATOR_CONFIG = {
    "run_name": "Browser Investigation Tools",
    "recursion_limit": 30  # investigate_url → browser_tools → investigate_url loops (increased for complex multi-step investigations)
}

# Priority threshold for URL investigation (1=highest priority, 5=lowest)
URL_INVESTIGATION_PRIORITY_LEVEL = 2

# -- REPORT GENERATION AGENT CONFIGURATION --
# Final report synthesis and verdict determination
REPORT_GENERATION_CONFIG = {
    "run_name": "Report Generator Agent",
    "recursion_limit": 10  # Linear workflow: verdict → report → save
}

