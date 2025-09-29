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
# Static analysis with tool-using investigator subgraphs
FILE_ANALYSIS_CONFIG = {
    "run_name": "File Analysis Agent", 
    "recursion_limit": 20  # Multiple investigation missions possible
}

# Investigator subgraph within file analysis (tool loops)
FILE_ANALYSIS_INVESTIGATOR_CONFIG = {
    "run_name": "PDF Investigation Tools",
    "recursion_limit": 15  # investigation → tools → investigation loops
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
    "recursion_limit": 20  # investigate_url → browser_tools → investigate_url loops
}

# Priority threshold for URL investigation (1=highest priority, 5=lowest)
URL_INVESTIGATION_PRIORITY_LEVEL = 5

# -- REPORT GENERATION AGENT CONFIGURATION --
# Final report synthesis and verdict determination
REPORT_GENERATION_CONFIG = {
    "run_name": "Report Generator Agent",
    "recursion_limit": 10  # Linear workflow: verdict → report → save
}

