"""Loguru logging configuration for PDF Hunter.

This module configures Loguru with hybrid logging:
- Terminal: Colorful, human-readable with emojis
- Central JSON file: Structured JSONL for querying across sessions
- Session JSON file: Isolated per-session logs (when output_directory provided)
"""

from loguru import logger
import sys
import os
import logging


from loguru import logger
import sys
import os


def setup_logging(session_id: str | None = None, output_directory: str | None = None, debug_to_terminal: bool = False) -> None:
    """Configure Loguru logging for PDF Hunter.
    
    Call this once at application startup (in orchestrator).
    
    Args:
        session_id: Optional session ID for session-specific logging context
        output_directory: Optional session output directory (e.g., "output/abc123_20251001_143000")
                         If provided with session_id, creates session-specific log file
        debug_to_terminal: If True, show DEBUG logs in terminal (default: False, INFO+ only)
    
    Outputs:
        - Terminal (stderr): Colorful format with aligned columns
          * debug_to_terminal=False: INFO+ level (default, production)
          * debug_to_terminal=True: DEBUG+ level (development/testing)
        - Central JSON file: logs/pdf_hunter_YYYYMMDD.jsonl (all sessions, DEBUG+)
        - Session JSON file: {output_directory}/logs/session.jsonl (when output_directory provided, DEBUG+)
    
    Usage:
        from loguru import logger
        
        # Production mode (INFO+ in terminal, central + session logs)
        setup_logging(session_id="abc123", output_directory="output/abc123_20251001_143000")
        
        # Development mode (DEBUG+ in terminal)
        setup_logging(debug_to_terminal=True)
        
        # In any agent node
        logger.info("Starting extraction",
                    agent="pdf_extraction",
                    session_id=session_id,
                    node="extract_images")
    """
    # Remove default handler
    logger.remove()
    
    # Set global defaults for all log messages (ensures frontend always gets agent field)
    # Individual log calls can override these with their own agent/node values
    default_extra = {
        "agent": "system",
        "node": "unknown",
        "session_id": session_id or "none"
    }
    logger.configure(extra=default_extra)
    
    # Terminal handler: Colorful, human-readable with emojis
    # Use a format function to handle optional extra fields
    def terminal_format(record):
        agent = record["extra"].get("agent", "system")
        timestamp = record["time"].strftime("%H:%M:%S")
        level = record["level"].name
        message = record["message"]
        
        # Escape curly braces in message to prevent format errors
        # (messages often contain dicts like {'key': 'value'})
        message = message.replace("{", "{{").replace("}", "}}")
        
        # Color formatting
        colors = {
            "DEBUG": "blue",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "magenta",
            "SUCCESS": "green"
        }
        color = colors.get(level, "white")
        
        return (
            f"<green>{timestamp}</green> | "
            f"<level>{level: <8}</level> | "
            f"<cyan>{agent:<20}</cyan> | "
            f"<{color}>{message}</{color}>\n"
        )
    
    terminal_level = "DEBUG" if debug_to_terminal else "INFO"
    logger.add(
        sys.stderr,
        format=terminal_format,
        level=terminal_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Central JSON file handler: Structured JSONL for querying across all sessions
    logger.add(
        "logs/pdf_hunter_{time:YYYYMMDD}.jsonl",
        format="{message}",
        level="DEBUG",
        rotation="00:00",  # New file at midnight
        retention="30 days",  # Keep logs for 30 days
        compression="zip",  # Compress old logs
        serialize=True,  # Output as JSON (one object per line = JSONL)
        backtrace=True,
        diagnose=True,
        enqueue=True,  # Thread-safe async writes
    )
    
    # Session-specific JSON file handler (if output_directory provided)
    if output_directory and session_id:
        session_log_dir = os.path.join(output_directory, "logs")
        os.makedirs(session_log_dir, exist_ok=True)
        session_log_path = os.path.join(session_log_dir, "session.jsonl")
        
        logger.add(
            session_log_path,
            format="{message}",
            level="DEBUG",
            serialize=True,  # Output as JSON (one object per line = JSONL)
            backtrace=True,
            diagnose=True,
            enqueue=True,  # Thread-safe async writes
        )
    
    # Log configuration summary
    mode = "DEBUG" if debug_to_terminal else "INFO"
    log_outputs = ["terminal", "central"]
    if output_directory and session_id:
        log_outputs.append("session")
    
    logger.info(
        f"🚀 Logging configured (terminal: {mode}+ level, outputs: {', '.join(log_outputs)})",
        agent="system",
        node="setup_logging",
        debug_to_terminal=debug_to_terminal,
        output_directory=output_directory or "none"
    )


def get_logger():
    """Get the configured Loguru logger instance.
    
    DEPRECATED: Use `from loguru import logger` directly instead.
    This function exists only for backward compatibility.
    
    Returns:
        The global Loguru logger instance
    """
    return logger
