# Frontend Vision: Real-Time PDF Threat Analysis Dashboard

## 🎯 Project Goal

We're building a **web-based dashboard** that provides real-time visibility into PDF security analysis as it happens. Think of it as a "mission control center" where security analysts watch an AI-powered investigation unfold in real-time.

---

## 🏗️ The Backend (What Exists)

The backend is a **multi-agent AI system** built with LangGraph that analyzes potentially malicious PDFs through a sophisticated pipeline:

1. **PDF Extraction Agent**: Extracts images, finds URLs, scans QR codes
2. **Image Analysis Agent**: Visual deception analyst looking for UI/UX threats (fake login forms, phishing pages)
3. **File Analysis Agent**: Deep investigation using security tools (pdfid, peepdf), spawns parallel investigation missions
4. **URL Investigation Agent**: Browser automation to analyze suspicious links
5. **Report Generator Agent**: Synthesizes findings into executive report with final verdict

**Key characteristics:**
- Agents run **asynchronously** (some in parallel)
- Each agent performs **multiple operations** over time (not instant)
- Investigations are **complex**: file analyzer spawns sub-missions, URL agent visits multiple links
- Analysis can take **5-10 minutes** for a single PDF
- Rich context: evidence discovered, tools executed, threats detected, verdicts rendered

**Logging Infrastructure:**
- **Loguru-based structured logging** - Every agent emits semantic events with rich context
- **Dual output**: Terminal (colored, human-readable) + JSONL files (machine-parseable)
- **Session-based organization**: Each analysis creates `{sha1}_{timestamp}` session with dedicated log file at `output/{session_id}/logs/session.jsonl`
- **Context binding**: Every log entry includes `agent`, `node`, `session_id`, `event_type` fields
- **50+ event types documented**: See `docs/LOGGING_FIELD_REFERENCE.md` for complete field mappings

---

## 🎨 The Frontend Vision

### **Core Concept: Agent-Centric Real-Time Dashboard**

Imagine opening a web application and seeing **5 distinct panels** - one for each agent - each showing what that agent is doing **right now, as it happens**.

```
┌─────────────────────────────────────────────────────────────┐
│  PDF Hunter Analysis Dashboard                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 📄 PDF EXTRACTION                                    │  │
│  │ Status: ✅ Complete                                  │  │
│  │                                                      │  │
│  │ Live Activity:                                       │  │
│  │ • Extracted 3 page images                           │  │
│  │ • Found 2 embedded URLs                             │  │
│  │ • Detected 1 QR code → https://suspicious.com       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🖼️ IMAGE ANALYSIS                                    │  │
│  │ Status: ✅ Complete                                  │  │
│  │                                                      │  │
│  │ Live Activity:                                       │  │
│  │ • Analyzing page 1/3...                             │  │
│  │ • ⚠️ THREAT: Fake Microsoft login form detected     │  │
│  │ • Urgency score: 8/10                               │  │
│  │ • Prioritized URL for investigation                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🔬 FILE ANALYSIS                        [ACTIVE 🔴]  │  │
│  │ Status: ⏳ Investigating...                          │  │
│  │                                                      │  │
│  │ Live Activity:                                       │  │
│  │ 🎯 Mission: JavaScript Analysis                      │  │
│  │    • Running pdfid tool...                          │  │
│  │    • 🚨 Found /OpenAction + /JS objects             │  │
│  │    • Severity: HIGH                                 │  │
│  │                                                      │  │
│  │ 🎯 Mission: Embedded File Check                      │  │
│  │    • Running peepdf scanner...                      │  │
│  │    • No embedded files found                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🌐 URL INVESTIGATION                    [ACTIVE 🔴]  │  │
│  │ Status: ⏳ Analyzing links...                        │  │
│  │                                                      │  │
│  │ Live Activity:                                       │  │
│  │ 🔗 https://suspicious.com                            │  │
│  │    • Opening browser...                             │  │
│  │    • Taking screenshot...                           │  │
│  │    • 🚨 PHISHING: Credential harvesting detected    │  │
│  │    • Verdict: MALICIOUS                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 📊 REPORT GENERATION                                 │  │
│  │ Status: ⏳ Waiting for investigations...             │  │
│  │                                                      │  │
│  │ Will synthesize findings once all agents complete    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🎯 FINAL VERDICT: [Pending...]                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 💡 Why This Matters

### **The Problem with Traditional Approaches**

**Batch Processing UI:**
- User uploads PDF → "Processing..." spinner → Final report appears
- **No visibility** into what's happening
- **No understanding** of why it takes 10 minutes
- **Anxiety**: Is it stuck? Did it find something?

**Log Files:**
- Analyst opens terminal, sees raw logs
- Thousands of lines scrolling
- Hard to follow which agent is doing what
- **Not user-friendly** for non-technical users

### **What We Want Instead: Real-Time Transparency**

**Narrative-Driven Investigation:**
- User sees the "story" of the investigation unfold
- Understands **what each agent is doing** and **why**
- Sees **evidence as it's discovered** (not just final summary)
- Builds **confidence** in the AI system's thoroughness
- Can **intervene** if needed (future feature: stop analysis early if clearly malicious)

**Example User Experience:**

```
User uploads suspicious.pdf at 14:32:15

14:32:15 | PDF Extraction starts
14:32:16 | "Extracted 3 images" appears in PDF Extraction panel
14:32:17 | Image Analysis panel lights up: "Analyzing page 1..."
14:32:20 | 🚨 Red alert in Image Analysis: "Fake login form detected!"
          User thinks: "Oh no, this IS phishing"
14:32:21 | File Analysis panel shows: "Starting JavaScript investigation..."
14:32:25 | File Analysis: "Found /OpenAction - automatic code execution!"
          User thinks: "It's getting worse..."
14:32:30 | URL Investigation: "Visiting https://suspicious.com..."
14:32:35 | URL Investigation: "🚨 Credential harvesting confirmed"
14:32:40 | Report Generation: Writing final report...
14:32:45 | FINAL VERDICT appears: "MALICIOUS - High Confidence"
```

**In 30 seconds, the user:**
- Watched the investigation
- Understood the evidence
- Trusts the verdict
- Can explain findings to their team

---

## 🎯 What the Backend Provides

The backend emits **structured, semantic events** via Loguru logging system - not raw state dumps or LLM token streams.

### **Structured Event Stream**

Every log entry in `session.jsonl` follows this format:

```json
{
  "record": {
    "extra": {
      "agent": "image_analysis",
      "node": "analyze_images", 
      "session_id": "abc123_20251001_143220",
      "event_type": "PAGE_ANALYSIS_COMPLETE",
      "page_number": 1,
      "findings_count": 3,
      "tactics_count": 1,
      "urls_count": 2
    },
    "level": { "name": "INFO", "no": 20 },
    "message": "📄 Completed analysis of page 1 | Findings: 3 | Tactics: 1 | URLs: 2",
    "time": { "timestamp": 1727784740.123 }
  }
}
```

**Key characteristics:**
- **Agent-aware**: Every event has `agent` field for routing to correct panel
- **Event types**: 50+ documented event types (see `LOGGING_FIELD_REFERENCE.md`)
- **Rich metadata**: Counts, verdicts, statuses, confidence scores in structured fields
- **Session-scoped**: All events for one analysis share same `session_id`
- **Chronological**: Events appear in order they occurred
- **Machine-readable**: JSON format, consistent schema across all agents

### **Event Categories**

**Agent Lifecycle:**
- `AGENT_START` - Agent begins work
- `ANALYSIS_COMPLETE` / `COMPILATION_COMPLETE` - Agent finished successfully

**Investigation Progress:**
- `TRIAGE_START` / `TRIAGE_COMPLETE` - Initial assessment phase
- `MISSION_ASSIGNED` / `INVESTIGATION_START` - New investigation spawned
- `TOOL_EXECUTION_COMPLETE` - Security tool finished running
- `MISSION_COMPLETE` - Investigation finished

**Discoveries:**
- `IMAGE_EXTRACTION_COMPLETE` - Processed page images
- `QR_SCAN_COMPLETE` - Found QR codes with decoded URLs
- `PAGE_ANALYSIS_COMPLETE` - Analyzed one page for threats
- `VERDICT_DETERMINED` - Final judgment on threat level

**Synthesis:**
- `FILTER_COMPLETE` - Prioritized URLs for investigation
- `REPORT_GENERATION_COMPLETE` - Created final executive report

---

## 🎨 Frontend Technical Requirements

### **1. Data Source: Loguru Async Sink + SSE**

The frontend receives logs via **Server-Sent Events (SSE)** streamed directly from **Loguru's async sink** - a single solution that works for both local and remote deployments.

**Why This Works:**

Loguru natively supports **coroutine functions as sinks**, allowing us to push log events to in-memory queues in real-time. This means we can stream logs directly from the logging system to connected clients without any file I/O or polling.

```python
# Loguru supports async sinks
async def sse_sink(message):
    # Push log to all connected client queues
    for queue in connected_clients:
        await queue.put(message)

# Register the async sink
logger.add(sse_sink, serialize=True, enqueue=True)
```

**Architecture:**

```
Backend Agents
    ↓
Structured Logging (Loguru)
    ↓
Async Sink (coroutine function) ──→ In-Memory Queues (per client)
    ↓
FastAPI SSE Endpoint (/api/sessions/{id}/logs)
    ↓
Frontend EventSource (Browser)
    ↓
Agent Panels (visual display)
```

**How It Works:**

1. **Loguru Async Sink**: Coroutine function registered as Loguru sink, pushes logs to client queues
2. **FastAPI Server**: Provides SSE endpoint that yields logs from client queue
3. **Frontend**: Subscribes via EventSource, receives logs in real-time

**Key Advantages:**

- ✅ **Single Solution**: Same setup works for local machine and remote deployment
- ✅ **Zero File I/O**: No polling, logs pushed directly from memory (~0ms latency)
- ✅ **Simple Deployment**: Just run FastAPI server (`uvicorn` command)
- ✅ **Instant Streaming**: Logs appear in frontend immediately as agents execute
- ✅ **Built-in Backpressure**: Queue-based design prevents memory issues
- ✅ **Session Isolation**: Each client gets independent queue for clean separation

**Configuration:**

The SSE sink is **optionally enabled** via `enable_sse` parameter:

```python
# In logging_config.py
def setup_logging(session_id, output_directory, enable_sse=False):
    # Terminal and file sinks always enabled
    logger.add(...)  # Terminal
    logger.add(...)  # Files
    
    # SSE sink only when FastAPI server runs
    if enable_sse:
        logger.add(sse_sink, serialize=True, enqueue=True)
```

**Usage:**

- **Local/Remote with FastAPI**: `setup_logging(enable_sse=True)` - SSE streaming active
- **LangGraph Studio**: `setup_logging()` - SSE disabled, only terminal + files
- **Testing/Debug**: `setup_logging()` - SSE disabled, no overhead

**Persistent Log Files:**
```
output/{session_id}/logs/session.jsonl
```
Logs are **also saved to file** regardless of SSE configuration, providing:
- Session replay capability
- Debugging and audit trails  
- Fallback if SSE unavailable

### **2. Agent-Aware Routing**
- Each event has `record.extra.agent` field
- Frontend routes events to correct panel
- Panels update independently (image analysis completes while file analysis still running)

### **3. Visual State Management**

**Panel States:**
- `IDLE` - Waiting to start (gray)
- `ACTIVE` - Currently working (animated indicator)
- `COMPLETE` - Finished successfully (green checkmark)
- `ERROR` - Failed (red X)

**Event Display:**
- Info events: Blue 🔵 (INFO level)
- Success: Green 🟢 (SUCCESS level)
- Warnings: Amber 🟡 (WARNING level)
- Errors: Red 🔴 (ERROR level)

**Progressive Disclosure:**
- Show summary by default
- Click panel to expand for detailed event history
- Event items are interactive (click to see full field data)

### **4. Semantic Formatting**

Events contain **rich structured data** that can be formatted meaningfully:

```typescript
// Raw event from JSONL:
{
  "record": {
    "extra": {
      "agent": "FileAnalysis",
      "event_type": "TRIAGE_COMPLETE", 
      "decision": "suspicious",
      "mission_count": 3,
      "reasoning": "Found /JavaScript and /OpenAction..."
    }
  }
}

// Frontend displays as:
"⚠️ Triage Complete: Suspicious (3 missions created)"
"  ↳ Found /JavaScript and /OpenAction..."
```

### **5. Timeline/History**
- Scrollable event history per panel
- Timestamps from `record.time.timestamp`
- Can replay investigation after completion
- Filter by event type or severity level

---

## 🏆 Success Criteria

A security analyst opens the dashboard and:

1. **Immediately understands** which agents are active
2. **Sees evidence** as it's discovered (not just at the end)
3. **Follows the investigation narrative** like reading a story
4. **Trusts the verdict** because they watched the reasoning
5. **Can screenshot any panel** to show their team specific findings
6. **Feels confident** the AI did a thorough job

---

## 🔧 Architecture Overview

### **Data Flow**

```
Backend Agents
    ↓
Structured Logging (Loguru)
    ↓
Async Sink → SSE Endpoint
    ↓
Frontend EventSource
    ↓
Agent Router (routes by agent field)
    ↓
Agent Panels (visual display)
```

Also persists to: `output/{session_id}/logs/session.jsonl`

### **Key Design Decisions**

**Why JSONL Files?**
- Persist across backend restarts
- Session replay capability
- Debugging and audit trails
- Fallback if SSE unavailable

**Why Agent-Centric Panels?**
- Matches mental model of multi-agent system
- Clear separation of concerns (each agent has distinct role)
- Easy to see which agents are active vs complete
- Users can focus on specific agent if interested

**Why Event-Driven Updates?**
- Fine-grained progress visibility (not just "loading...")
- Can show evidence as it's discovered
- Users understand investigation timeline
- Builds confidence in AI thoroughness

---

## 📋 Implementation Overview

### **Project Structure**

The frontend is a **separate application** from the backend:

```
pdf-hunter/
├── src/                    # Backend Python code (existing)
│   └── pdf_hunter/
│       ├── config/
│       │   └── logging_config.py    # Loguru with async sink → SSE streaming
│       └── api/
│           └── server.py            # FastAPI SSE endpoint (receives from Loguru)
├── output/                 # Analysis outputs + JSONL logs (existing)
├── docs/                   # Documentation (existing)
│   └── LOGGING_FIELD_REFERENCE.md  # Complete field mapping reference
│
└── frontend/              # Frontend application (to be created)
    ├── package.json        # Separate npm project
    ├── src/
    └── public/
```

**Development Workflow:**
```bash
# Terminal 1: FastAPI Server with SSE
cd src/pdf_hunter/api
uvicorn server:app --reload

# Terminal 2: Frontend Development
cd frontend
npm run dev
```

**Key Backend Components:**

1. **`logging_config.py`**: Loguru configuration with async sink
   - `setup_logging(enable_sse=True)` - Activates SSE streaming
   - `async def sse_sink(message)` - Pushes logs to client queues
   - `connected_clients: Set[asyncio.Queue]` - Manages client connections

2. **`server.py`**: FastAPI application
   - `POST /api/analyze` - Upload PDF, returns session_id
   - `GET /api/sessions/{session_id}/logs` - SSE stream of log events

**Frontend Connects To:**
- `http://localhost:8000/api/analyze` - Upload endpoint
- `http://localhost:8000/api/sessions/{session_id}/logs` - EventSource SSE stream

---

## 📋 Implementation Plan

### **Phase 1: Backend - SSE Streaming Infrastructure**

**Goal:** Enable real-time log streaming from Loguru to frontend via Server-Sent Events

#### 1.1 Loguru Custom Sink with Queue
**File:** `src/pdf_hunter/config/logging_config.py`

**Changes:**
```python
# Add session-based queue management
session_queues: Dict[str, List[asyncio.Queue]] = {}

async def sse_sink(message):
    """Loguru sink that pushes logs to session queues"""
    record = json.loads(message)
    session_id = record.get('record', {}).get('extra', {}).get('session_id')
    
    if session_id and session_id in session_queues:
        # Push to all connected clients for this session
        for queue in session_queues[session_id]:
            try:
                await queue.put(message)
            except asyncio.QueueFull:
                # Drop old messages if queue full
                await queue.get()
                await queue.put(message)

def setup_logging(session_id, output_directory, enable_sse=False):
    # Existing terminal and file sinks
    logger.add(sys.stdout, ...)
    logger.add(f"{output_directory}/logs/session.jsonl", ...)
    
    # NEW: SSE sink (optional, for FastAPI mode)
    if enable_sse:
        logger.add(sse_sink, serialize=True, enqueue=True)
```

**Key Design:**
- ✅ One queue per connected client (isolation)
- ✅ Session-scoped routing (clients only get logs for their session)
- ✅ Backpressure handling (drop old messages if queue full)
- ✅ Opt-in via `enable_sse` flag (no overhead in LangGraph Studio)

#### 1.2 FastAPI Server with Upload & SSE Endpoints
**File:** `src/pdf_hunter/api/server.py` (NEW)

**Endpoints:**
```python
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

@app.post("/api/analyze")
async def upload_pdf(
    file: UploadFile = File(...),
    max_pages: int = 4
):
    """
    1. Calculate SHA1 of uploaded PDF
    2. Create session_id: {sha1}_{timestamp}
    3. Save PDF to output/{session_id}/uploaded.pdf
    4. Start orchestrator in background (asyncio.create_task)
    5. Return session_id immediately
    """
    session_id = create_session(file)
    
    # Start analysis in background
    asyncio.create_task(run_analysis(session_id, max_pages))
    
    return {"session_id": session_id}

@app.get("/api/stream/{session_id}")
async def stream_logs(session_id: str):
    """
    Server-Sent Events stream for real-time logs
    
    1. Create queue for this client
    2. Register queue in session_queues[session_id]
    3. Yield logs as they arrive
    4. Send keepalive pings every 30s
    5. Cleanup queue on disconnect
    """
    queue = asyncio.Queue(maxsize=100)
    
    # Register client
    if session_id not in session_queues:
        session_queues[session_id] = []
    session_queues[session_id].append(queue)
    
    async def event_generator():
        try:
            while True:
                # Wait for log with timeout (for keepalive)
                try:
                    message = await asyncio.wait_for(
                        queue.get(), timeout=30.0
                    )
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield ": keepalive\n\n"
        finally:
            # Cleanup on disconnect
            session_queues[session_id].remove(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    """
    Get current analysis status
    Returns: PENDING | RUNNING | COMPLETE | FAILED
    """
    # Check session state
    return {"status": get_session_status(session_id)}
```

**Session State Management:**
```python
# Track active sessions
session_states: Dict[str, str] = {}  # {session_id: "PENDING" | "RUNNING" | "COMPLETE" | "FAILED"}

async def run_analysis(session_id: str, max_pages: int):
    session_states[session_id] = "RUNNING"
    
    try:
        # Call orchestrator
        result = await orchestrator_graph.ainvoke({
            "file_path": f"output/{session_id}/uploaded.pdf",
            "session_id": session_id,
            "max_pages": max_pages
        })
        session_states[session_id] = "COMPLETE"
    except Exception as e:
        session_states[session_id] = "FAILED"
        logger.error(f"Analysis failed: {e}")
```

**CORS Configuration:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 1.3 Orchestrator Integration
**File:** `src/pdf_hunter/orchestrator/graph.py`

**Changes:**
```python
# Update startup to enable SSE when run via API
from pdf_hunter.config.logging_config import setup_logging

# Detect if running via API (check for environment variable)
enable_sse = os.getenv("ENABLE_SSE", "false").lower() == "true"

setup_logging(
    session_id=session_id,
    output_directory=output_dir,
    enable_sse=enable_sse  # NEW parameter
)
```

**Environment Variable:**
```bash
# When starting FastAPI server
export ENABLE_SSE=true
uvicorn pdf_hunter.api.server:app --reload
```

---

### **Phase 2: Frontend - Landing Page & File Upload**

**Goal:** User can upload PDF, specify page limit, and start analysis

#### 2.1 Landing Page Component
**File:** `frontend/src/components/LandingPage.tsx`

**Features:**
```typescript
import { useState } from 'react';

function LandingPage({ onAnalysisStart }) {
  const [file, setFile] = useState<File | null>(null);
  const [maxPages, setMaxPages] = useState(4);
  const [uploading, setUploading] = useState(false);
  
  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('max_pages', maxPages.toString());
    
    const response = await fetch('http://localhost:8000/api/analyze', {
      method: 'POST',
      body: formData
    });
    
    const { session_id } = await response.json();
    
    // Transition to monitoring view
    onAnalysisStart(session_id);
  };
  
  return (
    <div className="landing-container">
      {/* Animated circle in center */}
      <div className="circle-animation">
        <div className="pulse-ring"></div>
        <div className="pdf-icon">📄</div>
      </div>
      
      <h1>PDF Hunter</h1>
      <p>Real-time threat analysis for suspicious PDFs</p>
      
      {/* Drag & drop zone */}
      <div className="upload-zone">
        <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} />
        <p>Drag and drop PDF file here</p>
      </div>
      
      {/* Page limit slider */}
      <div className="page-limit">
        <label>Pages to analyze: {maxPages}</label>
        <input 
          type="range" 
          min="1" 
          max="4" 
          value={maxPages}
          onChange={(e) => setMaxPages(parseInt(e.target.value))}
        />
      </div>
      
      {/* Start button */}
      <button 
        onClick={handleUpload}
        disabled={!file || uploading}
      >
        {uploading ? 'Starting Analysis...' : 'Start Analysis'}
      </button>
    </div>
  );
}
```

**CSS Animation:**
```css
/* Pulsing circle animation */
.circle-animation {
  position: relative;
  width: 200px;
  height: 200px;
  animation: float 3s ease-in-out infinite;
}

.pulse-ring {
  position: absolute;
  border: 3px solid rgba(59, 130, 246, 0.5);
  border-radius: 50%;
  animation: pulse 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
}

@keyframes pulse {
  0% { width: 200px; height: 200px; opacity: 1; }
  100% { width: 300px; height: 300px; opacity: 0; }
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}
```

#### 2.2 Transition Animation
**When user clicks "Start Analysis":**

```css
/* Circle shrinks, moves to top center, becomes spinning indicator */
.transition-to-monitoring {
  animation: shrink-and-move 0.8s ease-out forwards;
}

@keyframes shrink-and-move {
  0% {
    width: 200px;
    height: 200px;
    transform: translate(0, 0);
  }
  100% {
    width: 40px;
    height: 40px;
    transform: translate(0, -300px);
  }
}

/* After transition, becomes spinning loader */
.monitoring-spinner {
  animation: spin 1s linear infinite;
}
```

---

### **Phase 3: Frontend - Live Monitoring Dashboard**

**Goal:** Display 5 agent panels with real-time log streaming and automatic field extraction

#### 3.0 Real-Time Field Display Architecture

**The Complete Flow: From Backend Log → Frontend Display**

```
Backend Agent emits log:
  logger.info("Page analysis complete",
              agent="ImageAnalysis",
              node="analyze_images", 
              event_type="PAGE_ANALYSIS_COMPLETE",
              verdict="Highly Deceptive",
              confidence=0.95,
              page_number=0,
              findings_count=4)
              
         ↓
         
Loguru SSE Sink pushes to queue:
  {
    "record": {
      "extra": {
        "agent": "ImageAnalysis",
        "node": "analyze_images",
        "event_type": "PAGE_ANALYSIS_COMPLETE",
        "verdict": "Highly Deceptive",
        "confidence": 0.95,
        "page_number": 0,
        "findings_count": 4
      }
    }
  }
  
         ↓
         
FastAPI SSE endpoint streams to frontend:
  data: {"record": {"extra": {...}}}
  
         ↓
         
Frontend EventSource receives log:
  eventSource.onmessage = (event) => { ... }
  
         ↓
         
Schema-driven routing:
  agent = log.record.extra.agent  // "ImageAnalysis"
  logs[agent].push(log)           // Add to ImageAnalysis panel
  
         ↓
         
AgentPanel component re-renders:
  <AgentPanel logs={logs.ImageAnalysis} />
  
         ↓
         
Field extraction system processes log:
  const rows = extractDisplayRows(log)
  
  ┌─────────────────────────────────────────────────────────┐
  │ 1. Lookup schema for ImageAnalysis.analyze_images      │
  │    .PAGE_ANALYSIS_COMPLETE                              │
  │                                                         │
  │ 2. Expected fields: [verdict, confidence, page_number, │
  │    findings_count, summary, ...]                        │
  │                                                         │
  │ 3. Filter out hidden: agent, node, session_id          │
  │                                                         │
  │ 4. Apply display names:                                 │
  │    confidence → "Confidence"                            │
  │    findings_count → "Findings"                          │
  │    verdict → "Verdict"                                  │
  │                                                         │
  │ 5. Format values:                                       │
  │    0.95 → "95.0%" (percentage field)                    │
  │    4 → "4" (already formatted)                          │
  │                                                         │
  │ 6. Sort by priority:                                    │
  │    [verdict, confidence, page_number, findings, ...]    │
  │                                                         │
  │ 7. Generate display rows:                               │
  │    "analyze_images | PAGE_ANALYSIS_COMPLETE | Verdict | Highly Deceptive" │
  │    "analyze_images | PAGE_ANALYSIS_COMPLETE | Confidence | 95.0%"         │
  │    "analyze_images | PAGE_ANALYSIS_COMPLETE | Page | 0"                   │
  │    "analyze_images | PAGE_ANALYSIS_COMPLETE | Findings | 4"               │
  └─────────────────────────────────────────────────────────┘
  
         ↓
         
User sees in ImageAnalysis panel:
  ┌──────────────────────────────────────────────┐
  │ 🖼️ IMAGE ANALYSIS                    [✅]    │
  │                                              │
  │ 13:35:13 | Completed analysis of page 0     │
  │                                              │
  │ analyze_images | PAGE_ANALYSIS_COMPLETE | Verdict    | Highly Deceptive │
  │ analyze_images | PAGE_ANALYSIS_COMPLETE | Confidence | 95.0%            │
  │ analyze_images | PAGE_ANALYSIS_COMPLETE | Page       | 0                │
  │ analyze_images | PAGE_ANALYSIS_COMPLETE | Findings   | 4                │
  └──────────────────────────────────────────────┘
```

**Key Points:**

✅ **Automatic Routing**: `agent` field determines which panel receives the log (ImageAnalysis vs FileAnalysis)

✅ **Schema-Driven Display**: Field extraction system knows exactly what fields to expect for each agent/node/event combination

✅ **Real-Time Updates**: As soon as log arrives via SSE, it's processed and displayed in ~10ms

✅ **No Manual Mapping**: Frontend doesn't hardcode field logic - everything driven by `logFieldSchema.js`

✅ **100% Coverage**: Works for all 5 agents, 29 nodes, 65 events (enriched schema)

✅ **Consistent Format**: Every field follows `node | event_type | field_name | value` regardless of agent

#### 3.1 Dashboard Layout
**File:** `frontend/src/components/Dashboard.tsx`

```typescript
import { useEffect, useState } from 'react';
import AgentPanel from './AgentPanel';
import { extractFieldsFromLog } from '../utils/fieldExtractor';

function Dashboard({ sessionId }) {
  const [logs, setLogs] = useState<Record<string, any[]>>({
    PdfExtraction: [],
    FileAnalysis: [],
    ImageAnalysis: [],
    URLInvestigation: [],
    ReportGenerator: []
  });
  
  useEffect(() => {
    // Connect to SSE stream
    const eventSource = new EventSource(
      `http://localhost:8000/api/stream/${sessionId}`
    );
    
    eventSource.onmessage = (event) => {
      const log = JSON.parse(event.data);
      const agent = log.record.extra.agent;
      
      // 🔥 CRITICAL: Schema-driven routing
      // Each log is automatically routed to the correct agent panel
      // based on the 'agent' field (PdfExtraction, ImageAnalysis, etc.)
      // The agent panel will then use extractDisplayRows() or extractFieldsFromLog()
      // to display fields in the standardized format
      setLogs(prev => ({
        ...prev,
        [agent]: [...prev[agent], log]
      }));
    };
    
    eventSource.onerror = () => {
      console.error('SSE connection lost');
      eventSource.close();
    };
    
    return () => eventSource.close();
  }, [sessionId]);
  
  return (
    <div className="dashboard">
      {/* Spinning indicator at top */}
      <div className="session-header">
        <div className="spinner"></div>
        <h2>Analysis in Progress</h2>
        <p className="session-id">{sessionId}</p>
      </div>
      
      {/* Agent panels */}
      <div className="agent-panels">
        <AgentPanel 
          agent="PdfExtraction"
          logs={logs.PdfExtraction}
          icon="📄"
        />
        <AgentPanel 
          agent="ImageAnalysis"
          logs={logs.ImageAnalysis}
          icon="🖼️"
        />
        <AgentPanel 
          agent="FileAnalysis"
          logs={logs.FileAnalysis}
          icon="🔬"
        />
        <AgentPanel 
          agent="URLInvestigation"
          logs={logs.URLInvestigation}
          icon="🌐"
        />
        <AgentPanel 
          agent="ReportGenerator"
          logs={logs.ReportGenerator}
          icon="📊"
        />
      </div>
      
      {/* Final verdict card (appears at end) */}
      <FinalVerdict logs={logs.ReportGenerator} />
    </div>
  );
}
```

#### 3.2 Agent Panel Component
**File:** `frontend/src/components/AgentPanel.tsx`

```typescript
import { extractDisplayRows, getLogLevelColor } from '../utils/fieldExtractor';

function AgentPanel({ agent, logs, icon }) {
  const [expanded, setExpanded] = useState(false);
  
  // Determine status from logs
  const status = getAgentStatus(logs);
  
  // Get latest significant events
  const recentEvents = logs
    .filter(log => log.record.extra.event_type)
    .slice(-5);
  
  return (
    <div className={`agent-panel status-${status}`}>
      <div className="panel-header" onClick={() => setExpanded(!expanded)}>
        <span className="icon">{icon}</span>
        <h3>{agent}</h3>
        <StatusBadge status={status} />
      </div>
      
      <div className="panel-body">
        {/* Show recent activity */}
        {recentEvents.map((log, idx) => {
          const rows = extractDisplayRows(log);
          const color = getLogLevelColor(log);
          
          return (
            <div key={idx} className={`event ${color}`}>
              {rows.map((row, i) => (
                <div key={i} className="field-row">{row}</div>
              ))}
            </div>
          );
        })}
        
        {/* Expanded view: full log history */}
        {expanded && (
          <div className="full-history">
            {logs.map((log, idx) => (
              <LogEntry key={idx} log={log} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function getAgentStatus(logs) {
  if (logs.length === 0) return 'IDLE';
  
  const latestEvent = logs[logs.length - 1].record.extra.event_type;
  
  if (latestEvent?.includes('COMPLETE')) return 'COMPLETE';
  if (latestEvent?.includes('START')) return 'ACTIVE';
  
  return 'ACTIVE';
}

function StatusBadge({ status }) {
  const icons = {
    IDLE: '⏳',
    ACTIVE: '🔴',
    COMPLETE: '✅',
    ERROR: '❌'
  };
  
  return <span className="status-badge">{icons[status]} {status}</span>;
}
```

#### 3.3 Field Display Integration
**File:** `frontend/src/components/LogEntry.tsx`

**CRITICAL: This is where the field schema system comes into play**

Every log event that arrives via SSE is automatically processed through our **complete field extraction system** to:
1. **Route fields to the correct agent panel** (based on `agent` field)
2. **Display fields in the standardized format**: `node | event_type | field_name | value`
3. **Apply proper formatting** (percentages, URLs, paths, counts)
4. **Show user-friendly display names** (not raw field names)
5. **Sort fields by priority** (verdict/confidence first, metadata last)

```typescript
import { 
  extractFieldsFromLog, 
  extractDisplayRows,
  formatLogTimestamp,
  getLogLevelColor 
} from '../utils/fieldExtractor';

function LogEntry({ log }) {
  // Extract all fields using our complete schema system
  // This automatically:
  // - Looks up expected fields for this agent/node/event combination
  // - Filters out hidden fields (agent, node, session_id)
  // - Applies display name mappings
  // - Formats values (0.95 → "95.0%", arrays → counts, etc.)
  // - Sorts by priority (verdict first, technical fields last)
  const fields = extractFieldsFromLog(log);
  
  const timestamp = formatLogTimestamp(log);
  const message = log.record.message;
  
  return (
    <div className="log-entry">
      <div className="log-header">
        <span className="timestamp">{timestamp}</span>
        <span className="message">{message}</span>
      </div>
      
      <div className="log-fields">
        {fields.map((field, idx) => (
          <div key={idx} className="field">
            <span className="field-name">{field.displayName}:</span>
            <span className="field-value">{field.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Real Example - What the User Sees:**

When this log arrives via SSE:
```json
{
  "record": {
    "extra": {
      "agent": "ImageAnalysis",
      "node": "analyze_images",
      "event_type": "PAGE_ANALYSIS_COMPLETE",
      "page_number": 0,
      "verdict": "Highly Deceptive",
      "confidence": 0.95,
      "findings_count": 4,
      "tactics_count": 3,
      "urls_prioritized": 2,
      "summary": "This page exhibits multiple high-risk deception tactics..."
    },
    "level": { "name": "INFO" },
    "time": { "timestamp": 1727784740.123 }
  }
}
```

The field extraction system automatically transforms it to this display:

```
📄 ImageAnalysis Panel
13:35:13 | Completed analysis of page 0

analyze_images | PAGE_ANALYSIS_COMPLETE | Event          | PAGE_ANALYSIS_COMPLETE
analyze_images | PAGE_ANALYSIS_COMPLETE | Verdict        | Highly Deceptive
analyze_images | PAGE_ANALYSIS_COMPLETE | Confidence     | 95.0%
analyze_images | PAGE_ANALYSIS_COMPLETE | Page           | 0
analyze_images | PAGE_ANALYSIS_COMPLETE | Summary        | This page exhibits multiple...
analyze_images | PAGE_ANALYSIS_COMPLETE | Findings       | 4
analyze_images | PAGE_ANALYSIS_COMPLETE | Tactics        | 3
analyze_images | PAGE_ANALYSIS_COMPLETE | URLs Flagged   | 2
```

**Key Features:**

✅ **Schema-Driven Routing**: Log automatically goes to ImageAnalysis panel (not FileAnalysis or URLInvestigation)

✅ **Standardized Format**: Every field follows `node | event_type | field_name | value` format

✅ **Smart Field Filtering**: Hidden fields (`agent`, `node`, `session_id`) automatically excluded

✅ **User-Friendly Names**: `findings_count` → "Findings", `urls_prioritized` → "URLs Flagged"

✅ **Automatic Formatting**: 
- `confidence: 0.95` → "95.0%"
- `urls_prioritized: 2` → "2" (already formatted)
- Long URLs truncated to 60 chars

✅ **Priority Sorting**: Critical fields (verdict, confidence) appear first

✅ **100% Coverage**: Works for all 5 agents, 29 nodes, ~65 events (thanks to enriched schema!)

**Alternative: Compact Display Mode**

For collapsed panels, use `extractDisplayRows()` to get pre-formatted strings:

```typescript
// In AgentPanel.tsx (collapsed view)
const rows = extractDisplayRows(log);

// Returns array of formatted strings:
[
  "analyze_images | PAGE_ANALYSIS_COMPLETE | Verdict | Highly Deceptive",
  "analyze_images | PAGE_ANALYSIS_COMPLETE | Confidence | 95.0%",
  "analyze_images | PAGE_ANALYSIS_COMPLETE | Page | 0",
  // ...
]

// Display as simple list
return (
  <div className="compact-view">
    {rows.map((row, idx) => (
      <div key={idx} className="field-row">{row}</div>
    ))}
  </div>
);
```

**Alternative: Compact Display Mode**

For collapsed panels, use `extractDisplayRows()` to get pre-formatted strings:

```typescript
// In AgentPanel.tsx (collapsed view)
const rows = extractDisplayRows(log);

// Returns array of formatted strings:
[
  "analyze_images | PAGE_ANALYSIS_COMPLETE | Verdict | Highly Deceptive",
  "analyze_images | PAGE_ANALYSIS_COMPLETE | Confidence | 95.0%",
  "analyze_images | PAGE_ANALYSIS_COMPLETE | Page | 0",
  // ...
]

// Display as simple list
return (
  <div className="compact-view">
    {rows.map((row, idx) => (
      <div key={idx} className="field-row">{row}</div>
    ))}
  </div>
);
```

**Multi-Agent Example: How Fields Route to Correct Panels**

As the analysis progresses, logs from different agents arrive and are automatically routed:

```
Time: 14:32:15
Event arrives: PdfExtraction.IMAGE_EXTRACTION_COMPLETE
Fields displayed in PdfExtraction panel:
  ✓ extract_pdf_images | IMAGE_EXTRACTION_COMPLETE | Event | IMAGE_EXTRACTION_COMPLETE
  ✓ extract_pdf_images | IMAGE_EXTRACTION_COMPLETE | Images | 3
  ✓ extract_pdf_images | IMAGE_EXTRACTION_COMPLETE | Output Directory | /output/...

Time: 14:32:18
Event arrives: ImageAnalysis.PAGE_ANALYSIS_START
Fields displayed in ImageAnalysis panel:
  ✓ analyze_images | PAGE_ANALYSIS_START | Event | PAGE_ANALYSIS_START
  ✓ analyze_images | PAGE_ANALYSIS_START | Page | 0

Time: 14:32:20
Event arrives: ImageAnalysis.PAGE_ANALYSIS_COMPLETE
Fields displayed in ImageAnalysis panel:
  ✓ analyze_images | PAGE_ANALYSIS_COMPLETE | Verdict | Highly Deceptive
  ✓ analyze_images | PAGE_ANALYSIS_COMPLETE | Confidence | 95.0%
  ✓ analyze_images | PAGE_ANALYSIS_COMPLETE | Page | 0
  ✓ analyze_images | PAGE_ANALYSIS_COMPLETE | Findings | 4

Time: 14:32:22
Event arrives: FileAnalysis.TRIAGE_COMPLETE
Fields displayed in FileAnalysis panel:
  ✓ identify_suspicious_elements | TRIAGE_COMPLETE | Event | TRIAGE_COMPLETE
  ✓ identify_suspicious_elements | TRIAGE_COMPLETE | Decision | suspicious
  ✓ identify_suspicious_elements | TRIAGE_COMPLETE | Missions | 3
  ✓ identify_suspicious_elements | TRIAGE_COMPLETE | Reasoning | Found /JavaScript and /OpenAction...

Time: 14:32:30
Event arrives: URLInvestigation.INVESTIGATION_START
Fields displayed in URLInvestigation panel:
  ✓ investigate_url | INVESTIGATION_START | Event | INVESTIGATION_START
  ✓ investigate_url | INVESTIGATION_START | URL | https://suspicious.com
  ✓ investigate_url | INVESTIGATION_START | Priority | 1
```

**The Magic: Zero Hardcoding**

The frontend doesn't need to know:
- What fields exist for each event
- How to format percentages vs counts vs URLs
- What display names to use
- What order to show fields in

All of this is **driven by the enriched schema system** (`logFieldSchema.js` with 573 lines of complete mappings).

When a new event type is added to the backend, as long as it's documented in the schema, the frontend will automatically display it correctly with **zero code changes**!
  const timestamp = formatLogTimestamp(log);
  const message = log.record.message;
  
  return (
    <div className="log-entry">
      <div className="log-header">
        <span className="timestamp">{timestamp}</span>
        <span className="message">{message}</span>
      </div>
      
      <div className="log-fields">
        {fields.map((field, idx) => (
          <div key={idx} className="field">
            <span className="field-name">{field.displayName}:</span>
            <span className="field-value">{field.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Display Format:**
```
node | event_type | field_name | value
───────────────────────────────────────
analyze_images | PAGE_ANALYSIS_COMPLETE | Verdict | Highly Deceptive
analyze_images | PAGE_ANALYSIS_COMPLETE | Confidence | 95.0%
analyze_images | PAGE_ANALYSIS_COMPLETE | Page | 0
analyze_images | PAGE_ANALYSIS_COMPLETE | Findings | 4
```

#### 3.4 Connection Status Indicator
**File:** `frontend/src/components/ConnectionStatus.tsx`

```typescript
function ConnectionStatus({ connected }) {
  return (
    <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
      <div className="status-dot"></div>
      <span>{connected ? 'Live' : 'Disconnected'}</span>
    </div>
  );
}
```

---

### **Phase 4: Integration & Testing**

#### 4.1 End-to-End Testing Checklist

**Backend:**
- [ ] Loguru SSE sink pushes logs to queues
- [ ] FastAPI `/api/analyze` accepts PDF upload
- [ ] FastAPI `/api/stream/{session_id}` streams logs via SSE
- [ ] Session state transitions: PENDING → RUNNING → COMPLETE
- [ ] Queue cleanup on client disconnect
- [ ] Keepalive pings every 30s

**Frontend:**
- [ ] Landing page accepts PDF file
- [ ] Page slider (1-4) works
- [ ] Transition animation from landing to dashboard
- [ ] EventSource connects to SSE endpoint
- [ ] Logs routed to correct agent panels
- [ ] Fields display in "node | event | field | value" format
- [ ] Status badges update (IDLE → ACTIVE → COMPLETE)
- [ ] Timestamps display in HH:MM:SS format
- [ ] Log level colors applied correctly
- [ ] Connection status indicator works
- [ ] Auto-scroll to latest logs
- [ ] Panel expand/collapse works

**Integration:**
- [ ] Upload PDF → analysis starts → logs stream in real-time
- [ ] Multiple concurrent sessions work (session isolation)
- [ ] Page limit enforcement (1-4 pages processed)
- [ ] Final verdict displays correctly
- [ ] Session state persists across page refresh
- [ ] Browser disconnect doesn't crash backend

#### 4.2 Test Scenarios

**Test 1: Benign PDF**
- Upload simple PDF (e.g., academic paper)
- Verify PdfExtraction completes
- Verify ImageAnalysis shows "Benign" verdict
- Verify FileAnalysis creates 0 missions (innocent)
- Verify final verdict: "Benign"

**Test 2: Suspicious PDF**
- Upload PDF with embedded URLs
- Verify QR code detection works
- Verify URLs prioritized by ImageAnalysis
- Verify URLInvestigation analyzes links
- Verify file analysis creates missions

**Test 3: Malicious PDF**
- Upload known malicious PDF with JavaScript
- Verify FileAnalysis detects /JS and /OpenAction
- Verify missions created for JavaScript investigation
- Verify final verdict: "Malicious"

**Test 4: Page Limit**
- Upload 10-page PDF with page limit = 2
- Verify only 2 pages analyzed
- Verify log shows: "Processing 2 of 10 pages"

**Test 5: Concurrent Sessions**
- Upload PDF A (session_id_A)
- Upload PDF B (session_id_B)
- Verify logs don't mix between sessions
- Verify both analyses complete successfully

---

### **Technology Stack**

**Backend:**
- Python 3.11+
- FastAPI 0.117.1
- Loguru (structured logging)
- asyncio (async queue management)

**Frontend:**
- React 19.1.1
- TypeScript 5.x
- Vite 7.1.7 (dev server)
- Tailwind CSS 3.4.0 (styling)
- EventSource API (SSE client)

**Field Schema System (Already Complete ✅):**
- `frontend/src/config/logFieldSchema.js` (~573 lines)
  - Complete mappings for 5 agents, 29 nodes, ~65 events
  - 65 field display names
  - Priority/complex/percentage field metadata
- `frontend/src/utils/fieldExtractor.js` (~300 lines)
  - 8 extraction/formatting functions
  - All tested and validated
- `frontend/src/examples/fieldExtractionExamples.js` (~200 lines)
  - Working examples and test cases

---

## 🚀 Next Steps

### Immediate Priorities

1. **Backend Phase 1** (Week 1)
   - Implement Loguru SSE sink with queue management
   - Create FastAPI server with `/api/analyze` and `/api/stream` endpoints
   - Add session state tracking
   - Test SSE streaming with curl/EventSource

2. **Frontend Phase 2** (Week 1-2)
   - Set up Vite + React + TypeScript project
   - Build landing page with file upload and animation
   - Create Dashboard layout with 5 agent panels
   - Integrate field extraction utilities (already complete)

3. **Integration Phase** (Week 2-3)
   - Connect frontend EventSource to backend SSE
   - Test end-to-end: upload → stream → display
   - Add error handling and reconnection logic
   - Polish UI/UX and animations

4. **Testing & Refinement** (Week 3-4)
   - Run with various PDF types (benign, suspicious, malicious)
   - Verify all events display correctly
   - Performance testing with rapid log generation
   - Fix edge cases and polish

---

## 🎯 The End Goal

A beautiful, real-time dashboard where **transparency builds trust**. Users don't just get a verdict - they **witness the investigation**. They see the AI agents working together, discovering evidence, following leads, and reaching conclusions.

The foundation is already in place:
- ✅ **Structured logging** with Loguru (implemented)
- ✅ **50+ event types** documented with full field mappings
- ✅ **Session-based JSONL files** ready to be consumed
- ✅ **Agent-aware context** in every log entry

All that remains is building the frontend that **reads and displays** this rich event stream.

This is what modern security tooling should look like: **intelligent, transparent, and human-centered**.
