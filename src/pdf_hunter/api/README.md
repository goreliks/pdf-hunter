# FastAPI Server for PDF Hunter

## Running the Server

```bash
# Start the server (from project root)
uv run uvicorn pdf_hunter.api.server:app --reload --port 8000

# Or run directly
cd src/pdf_hunter/api
uv run python server.py
```

Server will be available at: `http://localhost:8000`

## Testing SSE Endpoint with curl

First, run an analysis to create a session (use an existing session ID if available):

```bash
# Check if a session exists
SESSION_ID="ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251001_113920"

# Test SSE streaming
curl -N http://localhost:8000/api/sessions/$SESSION_ID/stream
```

The `-N` flag disables buffering so you see events in real-time.

## Endpoints

- `GET /` - Health check
- `GET /api/sessions/{session_id}/stream` - SSE log streaming
- `GET /api/sessions/{session_id}/status` - Check session status

## Testing Manually

### Terminal 1: Start the server
```bash
uv run uvicorn pdf_hunter.api.server:app --reload --port 8000
```

### Terminal 2: Test SSE streaming
```bash
# Use an existing session ID (check output/ directory)
curl -N http://localhost:8000/api/sessions/ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251001_113920/stream
```

You should see:
1. Historical logs from `session.jsonl` replayed
2. Then it waits for live logs (30-second keepalive pings)

### Terminal 3 (Optional): Send test logs
```bash
uv run python tests/api/test_sse_manual.py
```

This will send 5 test messages that should appear in Terminal 2's stream in real-time.

## What's Working

✅ **Step 1 Complete**: Enhanced `logging_config.py` with SSE sink
- Async SSE sink routes logs to connected clients
- Session-aware routing (logs only go to correct session)
- Memory-safe (queue size limits)
- Fully tested (`tests/api/test_sse_sink.py`)

✅ **Step 2 Complete**: FastAPI server with SSE endpoint
- Real-time log streaming via Server-Sent Events
- Historical log replay + live streaming
- Session status checking
- Security: Session ID validation, CORS configuration
- Fully tested (`tests/api/test_server.py`)

## Next Steps

**Step 3**: Create React frontend with Vite + Tailwind
**Step 4**: Implement SSE client hook (`useSSEStream`)
**Step 5**: Build Dashboard with 5 agent panels
**Step 6**: End-to-end testing
