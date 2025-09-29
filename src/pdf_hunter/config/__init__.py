"""
PDF Hunter Configuration Module

This module contains execution configuration for all agents including
recursion limits, execution parameters, runtime settings, and LLM models.
"""

# Import execution configuration
from .execution_config import (
    ORCHESTRATOR_CONFIG,
    PDF_EXTRACTION_CONFIG,
    FILE_ANALYSIS_CONFIG,
    FILE_ANALYSIS_INVESTIGATOR_CONFIG,
    IMAGE_ANALYSIS_CONFIG,
    URL_INVESTIGATION_CONFIG,
    URL_INVESTIGATION_INVESTIGATOR_CONFIG,
    URL_INVESTIGATION_PRIORITY_LEVEL,
    REPORT_GENERATION_CONFIG,
    THINKING_TOOL_ENABLED,
)

# Import model configuration
from .models_config import (
    # Model provider configs
    openai_config,
    azure_openai_config,
    
    # File Analysis Agent LLMs
    file_analysis_triage_llm,
    file_analysis_investigator_llm,
    file_analysis_graph_merger_llm,
    file_analysis_reviewer_llm,
    file_analysis_finalizer_llm,
    
    # Image Analysis Agent LLMs
    image_analysis_llm,
    
    # URL Investigation Agent LLMs
    url_investigation_investigator_llm,
    url_investigation_analyst_llm,
    
    # Report Generator Agent LLMs
    report_generator_llm,
    final_verdict_llm,
)

__all__ = [
    # Execution configuration
    "ORCHESTRATOR_CONFIG",
    "PDF_EXTRACTION_CONFIG", 
    "FILE_ANALYSIS_CONFIG",
    "FILE_ANALYSIS_INVESTIGATOR_CONFIG",
    "IMAGE_ANALYSIS_CONFIG",
    "URL_INVESTIGATION_CONFIG",
    "URL_INVESTIGATION_INVESTIGATOR_CONFIG",
    "URL_INVESTIGATION_PRIORITY_LEVEL",
    "REPORT_GENERATION_CONFIG",
    
    # Model provider configs
    "openai_config",
    "azure_openai_config",
    
    # LLM instances
    "file_analysis_triage_llm",
    "file_analysis_investigator_llm", 
    "file_analysis_graph_merger_llm",
    "file_analysis_reviewer_llm",
    "file_analysis_finalizer_llm",
    "image_analysis_llm",
    "url_investigation_investigator_llm",
    "url_investigation_analyst_llm",
    "report_generator_llm",
    "final_verdict_llm",
]