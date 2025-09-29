"""
Shared logging configuration for PDF Hunter.
Provides consistent logging setup across all agents and components.
"""
import logging
import os
import sys
from datetime import datetime

LOGGING_LEVEL = logging.INFO

def configure_logging(level=LOGGING_LEVEL, log_to_file=False, session_id=None):
    """
    Configure logging for PDF Hunter components.
    
    Args:
        level: The logging level (default: INFO)
        log_to_file: Whether to also log to a file (default: False)
        session_id: Optional session ID for log file naming
        
    Returns:
        The root logger instance
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates when reconfigured
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Always add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate log filename with timestamp and optional session ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if session_id:
            log_filename = f"{log_dir}/pdf_hunter_{session_id}_{timestamp}.log"
        else:
            log_filename = f"{log_dir}/pdf_hunter_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name):
    """
    Get a logger with the specified name.
    
    Args:
        name: The logger name (typically __name__)
        
    Returns:
        A logger instance
    """
    return logging.getLogger(name)