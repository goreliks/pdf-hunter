"""Loguru logging configuration for PDF Hunter.

This module configures Loguru with hybrid logging:
- Terminal: Colorful, human-readable with emojis
- Central JSON file: Structured JSONL for querying across sessions
- Session JSON file: Isolated per-session logs (when output_directory provided)
- SSE Sink: Real-time streaming to connected web clients (optional)
"""

from loguru import logger
import sys
import os
import asyncio
import json
from collections import defaultdict
from typing import Dict, Set


from loguru import logger
import sys
import os
import asyncio
import json
from collections import defaultdict
from typing import Dict, Set


# ============================================================================
# SSE (Server-Sent Events) Support for Real-Time Web Streaming
# ============================================================================

# Global state: Map of session_id -> set of client queues
connected_clients: Dict[str, Set[asyncio.Queue]] = defaultdict(set)

# Maximum queue size to prevent memory issues with slow clients
MAX_QUEUE_SIZE = 1000


async def sse_sink(message: str) -> None:
    """Async sink that routes log events to connected SSE clients.
    
    Parses the session_id from the log message and sends to all clients
    watching that specific session.
    
    Args:
        message: Serialized JSON log message from Loguru
    """
    try:
        # Parse message to extract session_id
        data = json.loads(message)
        session_id = data.get("record", {}).get("extra", {}).get("session_id")
        
        if not session_id or session_id == "none":
            return  # Skip messages without valid session_id
        
        # Send to all clients watching this session
        if session_id in connected_clients:
            for queue in list(connected_clients[session_id]):
                try:
                    # Non-blocking put with size check
                    if queue.qsize() < MAX_QUEUE_SIZE:
                        queue.put_nowait(message)
                    else:
                        # Queue full - client too slow, skip this message
                        logger.warning(
                            f"SSE queue full for session {session_id}, dropping message",
                            agent="system",
                            node="sse_sink"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to queue message for SSE client: {e}",
                        agent="system",
                        node="sse_sink"
                    )
    except json.JSONDecodeError:
        # Invalid JSON - skip
        pass
    except Exception as e:
        logger.error(
            f"SSE sink error: {e}",
            agent="system",
            node="sse_sink"
        )


def add_sse_client(session_id: str, queue: asyncio.Queue) -> None:
    """Register a new SSE client for a session.
    
    Args:
        session_id: Session ID to watch
        queue: Asyncio queue to receive log messages
    """
    connected_clients[session_id].add(queue)
    logger.debug(
        f"SSE client connected to session {session_id}",
        agent="system",
        node="add_sse_client",
        session_id=session_id
    )


def remove_sse_client(session_id: str, queue: asyncio.Queue) -> None:
    """Remove SSE client on disconnect.
    
    Args:
        session_id: Session ID being watched
        queue: Client queue to remove
    """
    if session_id in connected_clients:
        connected_clients[session_id].discard(queue)
        if not connected_clients[session_id]:
            # No more clients for this session - clean up
            del connected_clients[session_id]
    
    logger.debug(
        f"SSE client disconnected from session {session_id}",
        agent="system",
        node="remove_sse_client",
        session_id=session_id
    )


# ============================================================================
# Main Logging Setup
# ============================================================================


def setup_logging(
    session_id: str | None = None,
    output_directory: str | None = None,
    debug_to_terminal: bool = False,
    enable_sse: bool = False
) -> None:
    """Configure Loguru logging for PDF Hunter.
    
    Call this once at application startup (in orchestrator).
    
    Args:
        session_id: Optional session ID for session-specific logging context
        output_directory: Optional session output directory (e.g., "output/abc123_20251001_143000")
                         If provided with session_id, creates session-specific log file
        debug_to_terminal: If True, show DEBUG logs in terminal (default: False, INFO+ only)
        enable_sse: If True, enable SSE sink for real-time web streaming (default: False)
    
    Outputs:
        - Terminal (stderr): Colorful format with aligned columns
          * debug_to_terminal=False: INFO+ level (default, production)
          * debug_to_terminal=True: DEBUG+ level (development/testing)
        - Central JSON file: logs/pdf_hunter_YYYYMMDD.jsonl (all sessions, DEBUG+)
        - Session JSON file: {output_directory}/logs/session.jsonl (when output_directory provided, DEBUG+)
        - SSE sink: Real-time streaming to web clients (when enable_sse=True)
    
    Usage:
        from loguru import logger
        
        # Production mode (INFO+ in terminal, central + session logs)
        setup_logging(session_id="abc123", output_directory="output/abc123_20251001_143000")
        
        # Development mode (DEBUG+ in terminal)
        setup_logging(debug_to_terminal=True)
        
        # With SSE streaming for web dashboard
        setup_logging(session_id="abc123", output_directory="...", enable_sse=True)
        
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
    
    # SSE sink handler (if enabled)
    if enable_sse:
        logger.add(
            sse_sink,
            format="{message}",
            level="DEBUG",
            serialize=True,  # Output as JSON
            enqueue=True,  # Non-blocking async writes
            backtrace=False,  # Minimal overhead for streaming
            diagnose=False,
        )
        logger.info(
            "✅ SSE sink enabled for real-time web streaming",
            agent="system",
            node="setup_logging"
        )
    
    # Log configuration summary
    mode = "DEBUG" if debug_to_terminal else "INFO"
    log_outputs = ["terminal", "central"]
    if output_directory and session_id:
        log_outputs.append("session")
    if enable_sse:
        log_outputs.append("sse")
    
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
