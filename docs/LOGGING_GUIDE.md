# Loguru Logging Migration Guide

## Overview
PDF Hunter now uses **Loguru** for simple, powerful, structured logging with:
- ✅ Colorful terminal output with emojis
- ✅ Structured JSONL files for querying/streaming
- ✅ Automatic field serialization
- ✅ No wrapper classes or decorators needed

## Setup (One Time)

In orchestrator startup:
```python
from pdf_hunter.config.logging_config import setup_logging

# Call once at the start
setup_logging(session_id=session_id)
```

## Usage in Agents

### Simple Import
```python
from loguru import logger
```

### Basic Logging
```python
# Add context as keyword arguments
logger.info("Starting extraction",
            agent="pdf_extraction",
            session_id=state.get("session_id"),
            node="extract_images")

logger.success("✅ Completed successfully",
               agent="pdf_extraction",
               image_count=len(images))
```

### Event Types
```python
# Evidence found
logger.warning("⚠️  Found suspicious object",
               agent="file_analysis",
               event_type="EVIDENCE_FOUND",
               evidence_type="javascript",
               object_id="/JS")

# Mission start
logger.info("Mission created",
            agent="file_analysis",
            event_type="MISSION_START",
            mission_id=mission.mission_id,
            mission_data=mission.model_dump())

# Threat detected
logger.error("❌ Threat detected",
             agent="file_analysis",
             event_type="THREAT_DETECTED",
             threat_type="malicious_js",
             severity="high")
```

### Structured Data
```python
# Complex objects auto-serialize to JSON
logger.info("Analysis complete",
            agent="file_analysis",
            evidence_graph=evidence_graph.model_dump(),
            findings_count=len(findings),
            mission_results=[m.model_dump() for m in missions])
```

### Error Logging
```python
try:
    result = await some_operation()
except Exception as e:
    logger.exception("Operation failed",  # .exception() includes traceback
                     agent="url_investigation",
                     event_type="ERROR",
                     url=url,
                     error_type=type(e).__name__)
    return {"errors": [f"Failed: {e}"]}
```

## Log Levels

Loguru provides these levels (use what makes sense):
- `logger.trace()` - Very detailed debugging
- `logger.debug()` - Debug information (JSON only, not terminal)
- `logger.info()` - General information
- `logger.success()` - Success events (green in terminal!)
- `logger.warning()` - Warnings
- `logger.error()` - Errors
- `logger.critical()` - Critical failures

## Output Examples

### Terminal (Colorful)
```
23:18:53 | INFO     | pdf_extraction       | 🚀 Starting PDF extraction
23:18:53 | SUCCESS  | pdf_extraction       | ✅ Extracted 3 images successfully
23:18:53 | WARNING  | file_analysis        | ⚠️  Found suspicious JavaScript
23:18:53 | ERROR    | url_investigation    | ❌ Failed to investigate URL
```

### JSON File (logs/pdf_hunter_YYYYMMDD.jsonl)
```json
{
  "text": "⚠️  Found suspicious JavaScript",
  "record": {
    "level": {"name": "WARNING", "no": 30},
    "message": "⚠️  Found suspicious JavaScript",
    "time": {"timestamp": 1759263533.418},
    "extra": {
      "agent": "file_analysis",
      "session_id": "abc123_20250930_143000",
      "event_type": "EVIDENCE_FOUND",
      "evidence_type": "javascript",
      "object_id": "/JS"
    }
  }
}
```

## Migration Checklist

For each agent:
1. ✅ Change import: `from loguru import logger` (instead of get_logger)
2. ✅ Add context kwargs to existing logger calls:
   - `agent="agent_name"`
   - `session_id=state.get("session_id")`
   - `node="node_name"` (optional)
   - `event_type="EVENT_TYPE"` (for important events)
3. ✅ Add emojis to messages (optional but fun! 🎉)
4. ✅ Use `.success()` for success events
5. ✅ Use `.exception()` instead of `.error()` for exceptions
6. ✅ Test: Run agent and check terminal + JSON output

## Event Types Taxonomy

Standard event types for frontend dashboard:
- `AGENT_START` - Agent begins execution
- `AGENT_COMPLETE` - Agent finishes successfully
- `EVIDENCE_FOUND` - Security evidence discovered
- `MISSION_START` - Investigation mission created
- `MISSION_COMPLETE` - Mission finished
- `THREAT_DETECTED` - Threat identified
- `TOOL_EXECUTION` - Forensic tool executed
- `URL_ANALYZED` - URL investigation complete
- `ERROR` - Error occurred
- `VERDICT_DETERMINED` - Final verdict reached

## Files

- **Configuration**: `src/pdf_hunter/config/logging_config.py`
- **Log Output**: `logs/pdf_hunter_YYYYMMDD.jsonl` (daily rotation, 30-day retention, compressed)

## Benefits

✅ **Simple**: No wrapper classes, use Loguru directly  
✅ **Colorful**: Beautiful terminal output with automatic colors  
✅ **Structured**: All context fields in JSON for querying  
✅ **Flexible**: Add any fields as kwargs  
✅ **Frontend-Ready**: JSONL perfect for streaming to dashboard  
✅ **Thread-Safe**: Async writes with `enqueue=True`  
✅ **Auto-Rotation**: Daily files, compressed archives  
