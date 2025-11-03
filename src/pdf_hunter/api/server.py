"""
FastAPI server for PDF Hunter with SSE streaming.

Provides real-time log streaming via Server-Sent Events for the web dashboard.
"""
import asyncio
import hashlib
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from pdf_hunter.config.logging_config import (
    setup_logging,
    add_sse_client,
    remove_sse_client
)

# Track active analysis tasks
active_analyses = {}  # session_id -> {"status": str, "task": asyncio.Task}

# Initialize FastAPI app
app = FastAPI(
    title="PDF Hunter API",
    description="Multi-agent AI system for PDF threat analysis with real-time SSE streaming",
    version="0.1.0"
)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize logging with SSE enabled on server startup."""
    setup_logging(enable_sse=True)
    logger.info("🚀 PDF Hunter API started with SSE streaming enabled", agent="api", node="startup")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "PDF Hunter API",
        "status": "operational",
        "version": "0.1.0",
        "endpoints": {
            "root": "/",
            "health": "/health",
            "status": "/api/status",
            "analyze": "/api/analyze",
            "stream": "/api/sessions/{session_id}/stream",
            "session_status": "/api/sessions/{session_id}/status"
        }
    }


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "PDF Hunter API"}


@app.get("/api/status")
async def api_status():
    """
    Get API status and active analysis count.
    """
    return {
        "status": "operational",
        "active_analyses": len(active_analyses),
        "version": "0.1.0"
    }


@app.post("/api/analyze")
async def analyze_pdf(
    file: UploadFile = File(...),
    max_pages: int = Form(default=4, ge=1, le=10)
):
    """
    Upload a PDF file and start analysis in background.
    
    Args:
        file: PDF file to analyze
        max_pages: Maximum number of pages to analyze (1-10, default: 4)
        
    Returns:
        session_id: Unique identifier for tracking this analysis
        status: "started"
        stream_url: URL to connect for real-time log streaming
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "File must be a PDF")
    
    # Validate content type
    if file.content_type not in ['application/pdf', 'application/octet-stream']:
        raise HTTPException(400, f"Invalid content type: {file.content_type}")
    
    try:
        # Read file content
        content = await file.read()
        
        # Calculate SHA1 hash for session ID
        sha1_hash = hashlib.sha1(content).hexdigest()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{sha1_hash}_{timestamp}"
        
        # Create output directory structure
        output_dir = Path("output") / session_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save PDF to session directory
        pdf_path = output_dir / file.filename
        with open(pdf_path, 'wb') as f:
            f.write(content)
        
        # Setup logging BEFORE orchestrator runs (includes session.jsonl)
        setup_logging(
            session_id=session_id,
            output_directory=str(output_dir),
            enable_sse=True
        )
        
        logger.info(
            f"📄 PDF uploaded: {file.filename} ({len(content)} bytes)",
            agent="api",
            node="analyze_pdf",
            session_id=session_id,
            filename=file.filename,
            file_size=len(content),
            max_pages=max_pages
        )
        
        # Start analysis in background
        task = asyncio.create_task(
            run_pdf_analysis(session_id, str(pdf_path), max_pages)
        )
        
        # Track the analysis
        active_analyses[session_id] = {
            "status": "running",
            "task": task,
            "filename": file.filename,
            "started_at": datetime.now().isoformat()
        }
        
        return {
            "session_id": session_id,
            "status": "started",
            "filename": file.filename,
            "max_pages": max_pages,
            "stream_url": f"/api/sessions/{session_id}/stream",
            "status_url": f"/api/sessions/{session_id}/status"
        }
        
    except Exception as e:
        logger.error(
            f"Failed to start analysis: {e}",
            agent="api",
            node="analyze_pdf",
            exc_info=True
        )
        raise HTTPException(500, f"Failed to start analysis: {str(e)}")


async def run_pdf_analysis(session_id: str, pdf_path: str, max_pages: int):
    """
    Run the PDF Hunter analysis pipeline in background.
    
    Note: session_id is pre-generated and passed to the orchestrator.
    Logging is already configured before this function is called.
    
    Args:
        session_id: Pre-generated session identifier
        pdf_path: Path to PDF file
        max_pages: Maximum pages to analyze
    """
    try:
        # Import here to avoid circular dependencies
        from pdf_hunter.orchestrator.graph import orchestrator_graph
        from pdf_hunter.orchestrator.schemas import OrchestratorInputState
        
        logger.info(
            f"🚀 Starting PDF analysis pipeline",
            agent="api",
            node="run_pdf_analysis",
            session_id=session_id,
            pdf_path=pdf_path,
            max_pages=max_pages
        )
        
        # Extract output directory from session_id (it was created in analyze_pdf)
        output_directory = str(Path("output") / session_id)
        
        # Prepare initial state with pre-generated session_id
        initial_state: OrchestratorInputState = {
            "file_path": pdf_path,
            "output_directory": output_directory,
            "number_of_pages_to_process": max_pages,
            "additional_context": None,
            "session_id": session_id  # Pass pre-generated session_id
        }
        
        # Run the orchestrator (no streaming needed since logging is already setup)
        final_result = await orchestrator_graph.ainvoke(initial_state)

        # Save final state to JSON file (same as CLI)
        if final_result:
            from pdf_hunter.shared.utils.serializer import serialize_state_safely
            import json

            filename = f"analysis_report_session_{session_id}.json"
            json_path = Path(output_directory) / filename

            # Convert final state to JSON-serializable format
            serializable_state = serialize_state_safely(final_result)

            # Save to JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_state, f, indent=2, ensure_ascii=False)

            logger.info(
                f"📄 Final state saved to: {json_path}",
                agent="api",
                node="run_pdf_analysis",
                session_id=session_id,
                output_file=str(json_path)
            )

        # Update status
        if session_id in active_analyses:
            active_analyses[session_id]["status"] = "complete"

        logger.success(
            f"✅ PDF analysis complete",
            agent="api",
            node="run_pdf_analysis",
            session_id=session_id,
            errors=len(final_result.get("errors", [])) if final_result.get("errors") else 0
        )
        
    except Exception as e:
        # Update status
        if session_id in active_analyses:
            active_analyses[session_id]["status"] = "failed"
        
        logger.error(
            f"❌ PDF analysis failed: {e}",
            agent="api",
            node="run_pdf_analysis",
            session_id=session_id,
            exc_info=True
        )



@app.get("/api/sessions/{session_id}/stream")
async def stream_logs(session_id: str):
    """
    SSE endpoint for streaming log events in real-time.
    
    First replays historical events from session.jsonl (if exists),
    then streams live events from the queue.
    
    Args:
        session_id: Session ID in format {sha1}_{timestamp}
        
    Returns:
        StreamingResponse with text/event-stream content type
    """
    # Validate session_id format
    if not re.match(r'^[a-f0-9]{40}_\d{8}_\d{6}$', session_id):
        raise HTTPException(400, "Invalid session ID format. Expected: {sha1}_{YYYYMMDD}_{HHMMSS}")
    
    async def event_generator():
        """Generate SSE events: historical replay + live streaming."""
        
        # Step 1: Replay historical events from session.jsonl (if exists)
        log_file = Path(f"output/{session_id}/logs/session.jsonl")
        
        if log_file.exists():
            logger.info(
                f"Replaying historical logs for session {session_id}",
                agent="api",
                node="stream_logs",
                session_id=session_id
            )
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            yield f"data: {line}\n\n"
                            await asyncio.sleep(0)  # Allow other tasks to run
            except Exception as e:
                logger.error(
                    f"Failed to replay logs: {e}",
                    agent="api",
                    node="stream_logs",
                    session_id=session_id
                )
        
        # Step 2: Stream live events from queue
        queue = asyncio.Queue()
        add_sse_client(session_id, queue)
        
        logger.info(
            f"Client connected to SSE stream for session {session_id}",
            agent="api",
            node="stream_logs",
            session_id=session_id
        )
        
        try:
            while True:
                # Wait for next message with 30-second timeout
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive ping to prevent connection timeout
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            logger.info(
                f"Client disconnected from session {session_id}",
                agent="api",
                node="stream_logs",
                session_id=session_id
            )
        finally:
            remove_sse_client(session_id, queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering if deployed
        }
    )


@app.get("/api/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """
    Check if a session exists and its analysis status.
    
    Args:
        session_id: Session ID to check
        
    Returns:
        Status: "running", "complete", "failed", or "not_found"
    """
    # Validate session_id format
    if not re.match(r'^[a-f0-9]{40}_\d{8}_\d{6}$', session_id):
        raise HTTPException(400, "Invalid session ID format")
    
    # Check active analyses first
    if session_id in active_analyses:
        analysis_info = active_analyses[session_id]
        status = analysis_info["status"]
        
        # Check if final report exists for "complete" status
        report_path = Path(f"output/{session_id}/analysis_report_session_{session_id}.json")
        
        return {
            "status": status,
            "session_id": session_id,
            "filename": analysis_info.get("filename"),
            "started_at": analysis_info.get("started_at"),
            "report_available": report_path.exists(),
            "stream_url": f"/api/sessions/{session_id}/stream"
        }
    
    # Check if final report exists (completed before server started)
    report_path = Path(f"output/{session_id}/analysis_report_session_{session_id}.json")
    if report_path.exists():
        return {
            "status": "complete",
            "session_id": session_id,
            "report_available": True
        }
    
    # Check if session directory exists (might be from previous run)
    session_dir = Path(f"output/{session_id}")
    if session_dir.exists():
        # Has logs but no report - could be incomplete/failed
        log_file = session_dir / "logs" / "session.jsonl"
        return {
            "status": "incomplete",
            "session_id": session_id,
            "report_available": False,
            "has_logs": log_file.exists()
        }
    
    # Session not found
    return {
        "status": "not_found",
        "session_id": session_id,
        "report_available": False
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
