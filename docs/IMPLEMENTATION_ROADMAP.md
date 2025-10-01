# PDF Hunter Frontend Implementation Roadmap

**Goal:** Build a real-time monitoring dashboard that streams PDF analysis logs as they happen

**Current Status:** October 1, 2025
- ✅ Backend multi-agent system functional
- ✅ Structured logging with Loguru in place
- ✅ Session-based JSONL logs working
- ✅ Frontend field schema system complete (100% coverage)
- ⏳ SSE streaming infrastructure (not yet implemented)
- ⏳ Frontend dashboard UI (not yet implemented)

---

## 📋 Implementation Phases

### **Phase 1: Backend SSE Infrastructure** (Week 1: Days 1-3)

**Objective:** Enable real-time log streaming from Loguru to clients via Server-Sent Events

#### Step 1.1: Add Queue-Based SSE Sink to Loguru
**File:** `src/pdf_hunter/config/logging_config.py`
**Time Estimate:** 2-3 hours

**Tasks:**
1. [ ] Import required libraries
   ```python
   import asyncio
   from typing import Dict, List, Set
   ```

2. [ ] Add global state for session queues
   ```python
   # Session-based queue management
   session_queues: Dict[str, List[asyncio.Queue]] = {}
   queue_lock = asyncio.Lock()
   ```

3. [ ] Create async SSE sink function
   ```python
   async def sse_sink(message):
       """Loguru sink that pushes logs to all connected clients for a session"""
       try:
           record = json.loads(message)
           session_id = record.get('record', {}).get('extra', {}).get('session_id')
           
           if not session_id:
               return
           
           async with queue_lock:
               if session_id in session_queues:
                   # Push to all connected clients for this session
                   for queue in session_queues[session_id][:]:  # Copy to avoid modification during iteration
                       try:
                           await asyncio.wait_for(
                               queue.put(message),
                               timeout=0.1
                           )
                       except (asyncio.QueueFull, asyncio.TimeoutError):
                           # Drop old messages if queue full or timeout
                           logger.debug(f"Queue full for session {session_id}, dropping old message")
       except Exception as e:
           # Don't let sink errors crash logging
           logger.error(f"Error in SSE sink: {e}", exc_info=True)
   ```

4. [ ] Update `setup_logging()` to support SSE
   ```python
   def setup_logging(
       session_id: str = None,
       output_directory: str = None,
       debug_to_terminal: bool = False,
       enable_sse: bool = False  # NEW parameter
   ):
       # ... existing terminal and file sinks ...
       
       # NEW: SSE sink (optional, for FastAPI mode)
       if enable_sse and session_id:
           logger.add(
               sse_sink,
               serialize=True,
               enqueue=True,
               backtrace=False,
               diagnose=False
           )
           logger.info(f"SSE sink enabled for session {session_id}")
   ```

5. [ ] Add helper functions for queue management
   ```python
   async def register_client_queue(session_id: str, queue: asyncio.Queue):
       """Register a client queue for a session"""
       async with queue_lock:
           if session_id not in session_queues:
               session_queues[session_id] = []
           session_queues[session_id].append(queue)
           logger.debug(f"Client registered for session {session_id}")
   
   async def unregister_client_queue(session_id: str, queue: asyncio.Queue):
       """Unregister a client queue when they disconnect"""
       async with queue_lock:
           if session_id in session_queues:
               try:
                   session_queues[session_id].remove(queue)
                   if not session_queues[session_id]:
                       del session_queues[session_id]
                   logger.debug(f"Client unregistered from session {session_id}")
               except ValueError:
                   pass
   ```

**Testing:**
- [ ] Test sink doesn't crash when no clients connected
- [ ] Test multiple clients can connect to same session
- [ ] Test queue doesn't grow unbounded (backpressure works)

---

#### Step 1.2: Create FastAPI Server
**File:** `src/pdf_hunter/api/server.py` (NEW)
**Time Estimate:** 4-5 hours

**Tasks:**
1. [ ] Create basic FastAPI app structure
   ```python
   from fastapi import FastAPI, UploadFile, File, HTTPException
   from fastapi.responses import StreamingResponse
   from fastapi.middleware.cors import CORSMiddleware
   import asyncio
   import hashlib
   from datetime import datetime
   from pathlib import Path
   
   app = FastAPI(title="PDF Hunter API", version="1.0.0")
   
   # CORS for frontend (Vite dev server on 5173)
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5173", "http://localhost:5174"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. [ ] Add session state tracking
   ```python
   from enum import Enum
   
   class SessionStatus(str, Enum):
       PENDING = "PENDING"
       RUNNING = "RUNNING"
       COMPLETE = "COMPLETE"
       FAILED = "FAILED"
   
   # Global session state
   session_states: Dict[str, SessionStatus] = {}
   session_lock = asyncio.Lock()
   ```

3. [ ] Implement `/api/analyze` endpoint (file upload)
   ```python
   @app.post("/api/analyze")
   async def upload_and_analyze(
       file: UploadFile = File(...),
       max_pages: int = 4
   ):
       """
       Upload PDF and start analysis
       Returns session_id immediately, analysis runs in background
       """
       # Validate file
       if not file.filename.endswith('.pdf'):
           raise HTTPException(400, "Only PDF files allowed")
       
       # Read file content
       content = await file.read()
       
       # Calculate SHA1
       sha1 = hashlib.sha1(content).hexdigest()
       
       # Create session ID
       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
       session_id = f"{sha1}_{timestamp}"
       
       # Create output directory
       output_dir = Path(f"output/{session_id}")
       output_dir.mkdir(parents=True, exist_ok=True)
       
       # Save uploaded PDF
       pdf_path = output_dir / "uploaded.pdf"
       with open(pdf_path, "wb") as f:
           f.write(content)
       
       # Mark session as pending
       async with session_lock:
           session_states[session_id] = SessionStatus.PENDING
       
       # Start analysis in background
       asyncio.create_task(run_analysis(session_id, str(pdf_path), max_pages))
       
       return {
           "session_id": session_id,
           "status": "PENDING",
           "message": "Analysis started"
       }
   ```

4. [ ] Implement background analysis task
   ```python
   async def run_analysis(session_id: str, pdf_path: str, max_pages: int):
       """Run the orchestrator in background"""
       from pdf_hunter.config.logging_config import setup_logging
       from pdf_hunter.orchestrator.graph import create_orchestrator_graph
       
       try:
           # Update status
           async with session_lock:
               session_states[session_id] = SessionStatus.RUNNING
           
           # Setup logging with SSE enabled
           output_dir = f"output/{session_id}"
           setup_logging(
               session_id=session_id,
               output_directory=output_dir,
               enable_sse=True  # Enable SSE streaming
           )
           
           # Create and run orchestrator
           graph = create_orchestrator_graph()
           
           # Run in thread pool to avoid blocking
           result = await asyncio.to_thread(
               graph.invoke,
               {
                   "file_path": pdf_path,
                   "session_id": session_id,
                   "max_pages": max_pages
               }
           )
           
           # Mark complete
           async with session_lock:
               session_states[session_id] = SessionStatus.COMPLETE
           
           logger.info(f"Analysis complete for session {session_id}")
           
       except Exception as e:
           async with session_lock:
               session_states[session_id] = SessionStatus.FAILED
           
           logger.error(f"Analysis failed for {session_id}: {e}", exc_info=True)
   ```

5. [ ] Implement `/api/stream/{session_id}` endpoint (SSE)
   ```python
   @app.get("/api/stream/{session_id}")
   async def stream_logs(session_id: str):
       """
       Server-Sent Events stream for real-time logs
       """
       from pdf_hunter.config.logging_config import register_client_queue, unregister_client_queue
       
       # Create queue for this client
       queue = asyncio.Queue(maxsize=100)
       
       # Register queue
       await register_client_queue(session_id, queue)
       
       async def event_generator():
           try:
               last_ping = asyncio.get_event_loop().time()
               
               while True:
                   now = asyncio.get_event_loop().time()
                   timeout = 30.0 - (now - last_ping)
                   
                   if timeout <= 0:
                       # Send keepalive ping
                       yield ": keepalive\n\n"
                       last_ping = now
                       continue
                   
                   try:
                       # Wait for log with timeout
                       message = await asyncio.wait_for(queue.get(), timeout=timeout)
                       yield f"data: {message}\n\n"
                       last_ping = now
                       
                   except asyncio.TimeoutError:
                       # Send keepalive ping
                       yield ": keepalive\n\n"
                       last_ping = now
                       
           except asyncio.CancelledError:
               logger.info(f"Client disconnected from session {session_id}")
           finally:
               # Cleanup
               await unregister_client_queue(session_id, queue)
       
       return StreamingResponse(
           event_generator(),
           media_type="text/event-stream",
           headers={
               "Cache-Control": "no-cache",
               "Connection": "keep-alive",
               "X-Accel-Buffering": "no"
           }
       )
   ```

6. [ ] Implement `/api/status/{session_id}` endpoint
   ```python
   @app.get("/api/status/{session_id}")
   async def get_status(session_id: str):
       """Get current analysis status"""
       async with session_lock:
           status = session_states.get(session_id, "UNKNOWN")
       
       return {
           "session_id": session_id,
           "status": status
       }
   ```

7. [ ] Add health check endpoint
   ```python
   @app.get("/api/health")
   async def health_check():
       return {"status": "healthy", "timestamp": datetime.now().isoformat()}
   ```

**Testing:**
- [ ] Test file upload creates session_id
- [ ] Test SSE connection streams logs
- [ ] Test keepalive pings every 30s
- [ ] Test multiple concurrent sessions
- [ ] Test client disconnect cleanup

---

#### Step 1.3: Integration Testing
**Time Estimate:** 2-3 hours

**Tasks:**
1. [ ] Create test script for SSE streaming
   ```python
   # tests/api/test_sse_stream.py
   import asyncio
   import httpx
   
   async def test_sse_stream():
       # Upload a test PDF
       async with httpx.AsyncClient() as client:
           with open("tests/assets/pdfs/test_mal_one.pdf", "rb") as f:
               response = await client.post(
                   "http://localhost:8000/api/analyze",
                   files={"file": f},
                   data={"max_pages": 2}
               )
           
           session_id = response.json()["session_id"]
           print(f"Session ID: {session_id}")
           
           # Connect to SSE stream
           async with client.stream(
               "GET",
               f"http://localhost:8000/api/stream/{session_id}"
           ) as response:
               async for line in response.aiter_lines():
                   if line.startswith("data: "):
                       data = line[6:]  # Remove "data: " prefix
                       print(f"Received: {data[:100]}...")
   ```

2. [ ] Test with curl
   ```bash
   # Terminal 1: Start server
   cd src/pdf_hunter/api
   ENABLE_SSE=true uvicorn server:app --reload
   
   # Terminal 2: Upload PDF
   curl -X POST http://localhost:8000/api/analyze \
     -F "file=@tests/assets/pdfs/test_mal_one.pdf" \
     -F "max_pages=2"
   
   # Terminal 3: Stream logs (use session_id from upload)
   curl -N http://localhost:8000/api/stream/{session_id}
   ```

3. [ ] Verify logs stream in real-time
   - [ ] PdfExtraction events appear first
   - [ ] ImageAnalysis events follow
   - [ ] FileAnalysis events appear
   - [ ] All events have correct structure

---

### **Phase 2: Frontend Setup & Landing Page** (Week 1: Days 4-5)

**Objective:** Create React app with landing page and file upload

#### Step 2.1: Initialize Frontend Project
**Time Estimate:** 1 hour

**Tasks:**
1. [ ] Create Vite + React + TypeScript project
   ```bash
   cd /Users/gorelik/Courses/pdf-hunter
   npm create vite@latest frontend -- --template react-ts
   cd frontend
   npm install
   ```

2. [ ] Install dependencies
   ```bash
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```

3. [ ] Configure Tailwind CSS
   ```javascript
   // tailwind.config.js
   export default {
     content: [
       "./index.html",
       "./src/**/*.{js,ts,jsx,tsx}",
     ],
     theme: {
       extend: {},
     },
     plugins: [],
   }
   ```

4. [ ] Update main CSS
   ```css
   /* src/index.css */
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```

5. [ ] Test dev server
   ```bash
   npm run dev
   # Should open on http://localhost:5173
   ```

**Testing:**
- [ ] Dev server starts without errors
- [ ] Tailwind CSS classes work
- [ ] Hot reload works

---

#### Step 2.2: Create Landing Page Component
**File:** `frontend/src/components/LandingPage.tsx`
**Time Estimate:** 3-4 hours

**Tasks:**
1. [ ] Create component structure
   ```typescript
   import { useState, useRef } from 'react';
   
   interface LandingPageProps {
     onAnalysisStart: (sessionId: string) => void;
   }
   
   export function LandingPage({ onAnalysisStart }: LandingPageProps) {
     const [file, setFile] = useState<File | null>(null);
     const [maxPages, setMaxPages] = useState(4);
     const [uploading, setUploading] = useState(false);
     const [error, setError] = useState<string | null>(null);
     const fileInputRef = useRef<HTMLInputElement>(null);
     
     // ... implementation
   }
   ```

2. [ ] Implement file upload handler
   ```typescript
   const handleUpload = async () => {
     if (!file) return;
     
     setUploading(true);
     setError(null);
     
     try {
       const formData = new FormData();
       formData.append('file', file);
       formData.append('max_pages', maxPages.toString());
       
       const response = await fetch('http://localhost:8000/api/analyze', {
         method: 'POST',
         body: formData
       });
       
       if (!response.ok) {
         throw new Error(`Upload failed: ${response.statusText}`);
       }
       
       const data = await response.json();
       onAnalysisStart(data.session_id);
       
     } catch (err) {
       setError(err instanceof Error ? err.message : 'Upload failed');
       setUploading(false);
     }
   };
   ```

3. [ ] Create drag-and-drop zone
   ```typescript
   const handleDrop = (e: React.DragEvent) => {
     e.preventDefault();
     const droppedFile = e.dataTransfer.files[0];
     if (droppedFile && droppedFile.type === 'application/pdf') {
       setFile(droppedFile);
       setError(null);
     } else {
       setError('Please drop a PDF file');
     }
   };
   
   return (
     <div
       className="upload-zone"
       onDrop={handleDrop}
       onDragOver={(e) => e.preventDefault()}
       onClick={() => fileInputRef.current?.click()}
     >
       <input
         ref={fileInputRef}
         type="file"
         accept=".pdf"
         onChange={(e) => {
           const selectedFile = e.target.files?.[0];
           if (selectedFile) setFile(selectedFile);
         }}
         style={{ display: 'none' }}
       />
       {/* UI elements */}
     </div>
   );
   ```

4. [ ] Add animated circle
   ```typescript
   <div className="circle-animation">
     <div className="pulse-ring"></div>
     <div className="pdf-icon">📄</div>
   </div>
   ```

5. [ ] Add page slider
   ```typescript
   <div className="page-limit">
     <label>Pages to analyze: {maxPages}</label>
     <input
       type="range"
       min="1"
       max="4"
       value={maxPages}
       onChange={(e) => setMaxPages(parseInt(e.target.value))}
       className="slider"
     />
     <div className="slider-labels">
       <span>1</span>
       <span>2</span>
       <span>3</span>
       <span>4</span>
     </div>
   </div>
   ```

6. [ ] Add CSS animations
   ```css
   /* src/components/LandingPage.css */
   .circle-animation {
     position: relative;
     width: 200px;
     height: 200px;
     animation: float 3s ease-in-out infinite;
   }
   
   .pulse-ring {
     position: absolute;
     width: 100%;
     height: 100%;
     border: 3px solid rgba(59, 130, 246, 0.5);
     border-radius: 50%;
     animation: pulse 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
   }
   
   @keyframes pulse {
     0% {
       transform: scale(1);
       opacity: 1;
     }
     100% {
       transform: scale(1.5);
       opacity: 0;
     }
   }
   
   @keyframes float {
     0%, 100% { transform: translateY(0); }
     50% { transform: translateY(-20px); }
   }
   ```

**Testing:**
- [ ] File selection works
- [ ] Drag and drop works
- [ ] Page slider updates correctly
- [ ] Upload button disabled when no file
- [ ] Error messages display
- [ ] Animation smooth

---

#### Step 2.3: Create Transition Animation
**File:** `frontend/src/components/TransitionAnimation.tsx`
**Time Estimate:** 2 hours

**Tasks:**
1. [ ] Create transition component
   ```typescript
   interface TransitionProps {
     onComplete: () => void;
   }
   
   export function TransitionAnimation({ onComplete }: TransitionProps) {
     useEffect(() => {
       const timer = setTimeout(onComplete, 800);
       return () => clearTimeout(timer);
     }, [onComplete]);
     
     return (
       <div className="transition-container">
         <div className="shrinking-circle">
           <div className="pdf-icon">📄</div>
         </div>
       </div>
     );
   }
   ```

2. [ ] Add CSS animation
   ```css
   .shrinking-circle {
     animation: shrink-and-rise 0.8s ease-out forwards;
   }
   
   @keyframes shrink-and-rise {
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
   ```

**Testing:**
- [ ] Animation plays smoothly
- [ ] Callback triggers after 800ms
- [ ] Circle moves to correct position

---

### **Phase 3: Frontend Dashboard** (Week 2: Days 6-10)

**Objective:** Create live monitoring dashboard with agent panels

#### Step 3.1: Create Dashboard Component
**File:** `frontend/src/components/Dashboard.tsx`
**Time Estimate:** 4-5 hours

**Tasks:**
1. [ ] Create dashboard structure
   ```typescript
   interface DashboardProps {
     sessionId: string;
   }
   
   export function Dashboard({ sessionId }: DashboardProps) {
     const [logs, setLogs] = useState<Record<string, any[]>>({
       PdfExtraction: [],
       FileAnalysis: [],
       ImageAnalysis: [],
       URLInvestigation: [],
       ReportGenerator: []
     });
     const [connected, setConnected] = useState(false);
     const eventSourceRef = useRef<EventSource | null>(null);
     
     // ... implementation
   }
   ```

2. [ ] Implement SSE connection
   ```typescript
   useEffect(() => {
     const eventSource = new EventSource(
       `http://localhost:8000/api/stream/${sessionId}`
     );
     
     eventSource.onopen = () => {
       console.log('SSE connected');
       setConnected(true);
     };
     
     eventSource.onmessage = (event) => {
       try {
         const log = JSON.parse(event.data);
         const agent = log.record?.extra?.agent;
         
         if (agent && agent in logs) {
           setLogs(prev => ({
             ...prev,
             [agent]: [...prev[agent], log]
           }));
         }
       } catch (err) {
         console.error('Error parsing log:', err);
       }
     };
     
     eventSource.onerror = () => {
       console.error('SSE connection error');
       setConnected(false);
     };
     
     eventSourceRef.current = eventSource;
     
     return () => {
       eventSource.close();
     };
   }, [sessionId]);
   ```

3. [ ] Create layout
   ```typescript
   return (
     <div className="dashboard">
       {/* Header with spinner */}
       <div className="dashboard-header">
         <div className={`spinner ${connected ? 'active' : ''}`}></div>
         <h2>Analysis in Progress</h2>
         <ConnectionStatus connected={connected} />
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
     </div>
   );
   ```

**Testing:**
- [ ] SSE connection establishes
- [ ] Logs routed to correct panels
- [ ] Connection status updates
- [ ] Layout responsive

---

#### Step 3.2: Create Agent Panel Component
**File:** `frontend/src/components/AgentPanel.tsx`
**Time Estimate:** 5-6 hours

**Tasks:**
1. [ ] Create panel structure
   ```typescript
   import { extractDisplayRows, getLogLevelColor } from '../utils/fieldExtractor';
   
   interface AgentPanelProps {
     agent: string;
     logs: any[];
     icon: string;
   }
   
   export function AgentPanel({ agent, logs, icon }: AgentPanelProps) {
     const [expanded, setExpanded] = useState(false);
     const status = getAgentStatus(logs);
     const recentLogs = logs.slice(-5);
     
     // ... implementation
   }
   ```

2. [ ] Implement status detection
   ```typescript
   function getAgentStatus(logs: any[]): string {
     if (logs.length === 0) return 'IDLE';
     
     const latestLog = logs[logs.length - 1];
     const eventType = latestLog.record?.extra?.event_type;
     
     if (eventType?.includes('COMPLETE')) return 'COMPLETE';
     if (eventType?.includes('START')) return 'ACTIVE';
     
     return 'ACTIVE';
   }
   ```

3. [ ] Create panel UI
   ```typescript
   return (
     <div className={`agent-panel status-${status.toLowerCase()}`}>
       <div
         className="panel-header"
         onClick={() => setExpanded(!expanded)}
       >
         <span className="icon">{icon}</span>
         <h3>{agent}</h3>
         <StatusBadge status={status} />
         <button className="expand-btn">
           {expanded ? '▼' : '▶'}
         </button>
       </div>
       
       <div className="panel-body">
         {recentLogs.map((log, idx) => (
           <LogEntry key={idx} log={log} compact={!expanded} />
         ))}
         
         {expanded && logs.length > 5 && (
           <div className="full-history">
             {logs.slice(0, -5).map((log, idx) => (
               <LogEntry key={idx} log={log} compact={false} />
             ))}
           </div>
         )}
       </div>
     </div>
   );
   ```

4. [ ] Add status badge
   ```typescript
   function StatusBadge({ status }: { status: string }) {
     const icons = {
       IDLE: '⏳',
       ACTIVE: '🔴',
       COMPLETE: '✅',
       ERROR: '❌'
     };
     
     return (
       <span className={`status-badge status-${status.toLowerCase()}`}>
         {icons[status as keyof typeof icons]} {status}
       </span>
     );
   }
   ```

**Testing:**
- [ ] Panels display correctly
- [ ] Status updates in real-time
- [ ] Expand/collapse works
- [ ] Recent logs display
- [ ] Auto-scroll to latest

---

#### Step 3.3: Create Log Entry Component
**File:** `frontend/src/components/LogEntry.tsx`
**Time Estimate:** 3-4 hours

**Tasks:**
1. [ ] Create component with field extraction
   ```typescript
   import {
     extractFieldsFromLog,
     extractDisplayRows,
     formatLogTimestamp,
     getLogLevelColor
   } from '../utils/fieldExtractor';
   
   interface LogEntryProps {
     log: any;
     compact?: boolean;
   }
   
   export function LogEntry({ log, compact = false }: LogEntryProps) {
     const timestamp = formatLogTimestamp(log);
     const message = log.record?.message || '';
     const levelColor = getLogLevelColor(log);
     
     if (compact) {
       const rows = extractDisplayRows(log);
       return (
         <div className={`log-entry compact ${levelColor}`}>
           <span className="timestamp">{timestamp}</span>
           <div className="fields">
             {rows.map((row, idx) => (
               <div key={idx} className="field-row">{row}</div>
             ))}
           </div>
         </div>
       );
     }
     
     const fields = extractFieldsFromLog(log);
     
     return (
       <div className={`log-entry expanded ${levelColor}`}>
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

**Testing:**
- [ ] Fields extracted correctly
- [ ] Display format matches spec (node | event | field | value)
- [ ] Timestamps formatted (HH:MM:SS)
- [ ] Log level colors applied
- [ ] Compact vs expanded modes work

---

#### Step 3.4: Connection Status Indicator
**File:** `frontend/src/components/ConnectionStatus.tsx`
**Time Estimate:** 1 hour

**Tasks:**
1. [ ] Create status component
   ```typescript
   interface ConnectionStatusProps {
     connected: boolean;
   }
   
   export function ConnectionStatus({ connected }: ConnectionStatusProps) {
     return (
       <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
         <div className="status-dot"></div>
         <span>{connected ? 'Live' : 'Disconnected'}</span>
       </div>
     );
   }
   ```

2. [ ] Add CSS
   ```css
   .status-dot {
     width: 10px;
     height: 10px;
     border-radius: 50%;
     animation: pulse 2s ease-in-out infinite;
   }
   
   .connected .status-dot {
     background-color: #10b981;
   }
   
   .disconnected .status-dot {
     background-color: #ef4444;
   }
   ```

**Testing:**
- [ ] Status updates correctly
- [ ] Animation works
- [ ] Colors correct

---

### **Phase 4: Integration & Testing** (Week 2-3: Days 11-15)

**Objective:** End-to-end testing and bug fixes

#### Step 4.1: End-to-End Testing
**Time Estimate:** 6-8 hours

**Test Scenarios:**

1. [ ] **Test 1: Simple Benign PDF**
   - Upload academic paper (5 pages)
   - Set page limit to 2
   - Verify only 2 pages analyzed
   - Verify PdfExtraction completes
   - Verify ImageAnalysis shows "Benign"
   - Verify FileAnalysis shows "innocent" decision
   - Verify final verdict "Benign"

2. [ ] **Test 2: PDF with URLs**
   - Upload PDF with embedded URLs
   - Verify URL extraction logs appear
   - Verify ImageAnalysis prioritizes URLs
   - Verify URLInvestigation analyzes links
   - Verify browser tool logs appear

3. [ ] **Test 3: Malicious PDF**
   - Upload known malicious PDF
   - Verify FileAnalysis detects JavaScript
   - Verify missions created
   - Verify tool execution logs
   - Verify final verdict "Malicious"

4. [ ] **Test 4: Concurrent Sessions**
   - Open two browser tabs
   - Upload different PDFs simultaneously
   - Verify logs don't mix
   - Verify both complete successfully

5. [ ] **Test 5: Reconnection**
   - Start analysis
   - Close browser tab
   - Reopen with same session_id
   - Verify historical logs load
   - Verify can't resume streaming (expected)

6. [ ] **Test 6: Error Handling**
   - Upload invalid file
   - Verify error message
   - Upload corrupted PDF
   - Verify graceful failure

**Testing Checklist:**
- [ ] All 5 agents display correctly
- [ ] Logs route to correct panels
- [ ] Fields display in correct format
- [ ] Percentages formatted (0.95 → 95.0%)
- [ ] URLs truncated properly
- [ ] Timestamps show HH:MM:SS
- [ ] Status badges update
- [ ] Connection indicator works
- [ ] Auto-scroll works
- [ ] Expand/collapse works
- [ ] Page limit enforced
- [ ] Session isolation works

---

#### Step 4.2: Performance Testing
**Time Estimate:** 2-3 hours

**Tasks:**
1. [ ] Test with rapid log generation
   - Modify backend to log every 100ms
   - Verify frontend doesn't lag
   - Check memory usage in DevTools

2. [ ] Test with long-running analysis
   - Upload complex PDF (10+ minutes)
   - Verify connection stays alive
   - Verify keepalive pings work

3. [ ] Test queue backpressure
   - Disconnect frontend
   - Let backend continue logging
   - Verify queue doesn't grow unbounded

**Testing:**
- [ ] No memory leaks
- [ ] UI stays responsive
- [ ] No dropped logs (within reason)

---

#### Step 4.3: UI/UX Polish
**Time Estimate:** 4-6 hours

**Tasks:**
1. [ ] Add loading states
   - Spinner on upload
   - Skeleton loaders for panels
   - Progress indicators

2. [ ] Improve animations
   - Smooth transitions
   - Fade in/out for logs
   - Hover states

3. [ ] Add keyboard shortcuts
   - Esc to collapse all panels
   - Space to expand/collapse focused panel
   - Arrow keys to navigate

4. [ ] Responsive design
   - Mobile layout
   - Tablet layout
   - Desktop layout

5. [ ] Accessibility
   - ARIA labels
   - Keyboard navigation
   - Screen reader support

**Testing:**
- [ ] Smooth animations
- [ ] All interactions responsive
- [ ] Works on different screen sizes
- [ ] Passes accessibility audit

---

### **Phase 5: Documentation & Deployment** (Week 3-4: Days 16-20)

#### Step 5.1: Documentation
**Time Estimate:** 4-5 hours

**Tasks:**
1. [ ] Update README.md
   - Installation instructions
   - Running backend + frontend
   - Environment variables
   - Troubleshooting

2. [ ] Create API documentation
   - OpenAPI/Swagger for FastAPI
   - Endpoint descriptions
   - Request/response examples

3. [ ] Create user guide
   - How to upload PDF
   - How to read panels
   - Understanding verdicts
   - Screenshots

4. [ ] Create developer guide
   - Architecture overview
   - Adding new agents
   - Extending field schema
   - Contributing guidelines

**Deliverables:**
- [ ] README.md updated
- [ ] API docs at /docs
- [ ] USER_GUIDE.md
- [ ] DEVELOPER_GUIDE.md

---

#### Step 5.2: Deployment Preparation
**Time Estimate:** 3-4 hours

**Tasks:**
1. [ ] Create production build
   ```bash
   cd frontend
   npm run build
   ```

2. [ ] Configure backend for production
   - Environment variables
   - CORS settings
   - Logging levels

3. [ ] Create Docker setup (optional)
   ```dockerfile
   # Dockerfile for backend
   # Dockerfile for frontend
   # docker-compose.yml
   ```

4. [ ] Create deployment guide
   - Local deployment
   - Docker deployment
   - Cloud deployment (AWS/Azure/GCP)

**Deliverables:**
- [ ] Production-ready build
- [ ] Deployment documentation
- [ ] Docker setup (optional)

---

## 📊 Progress Tracking

### Week 1 Summary
- **Days 1-3:** Backend SSE infrastructure
- **Days 4-5:** Frontend setup + landing page
- **Milestone:** Can upload PDF and see file upload UI

### Week 2 Summary
- **Days 6-10:** Dashboard with agent panels
- **Days 11-12:** Integration testing
- **Milestone:** Live monitoring dashboard functional

### Week 3 Summary
- **Days 13-15:** Bug fixes + polish
- **Days 16-20:** Documentation + deployment
- **Milestone:** Production-ready system

---

## 🎯 Success Criteria

**Minimum Viable Product (MVP):**
- ✅ User can upload PDF
- ✅ User can set page limit (1-4)
- ✅ Analysis starts automatically
- ✅ Logs stream in real-time via SSE
- ✅ 5 agent panels display correctly
- ✅ Fields show in correct format (node | event | field | value)
- ✅ Final verdict displays

**Nice to Have:**
- ⭐ Session replay (view completed analyses)
- ⭐ Export report as PDF
- ⭐ Pause/resume analysis
- ⭐ Real-time charts (threat score over time)
- ⭐ Email notifications on completion

---

## 🚀 Getting Started

### Immediate Next Steps (This Week)

**Day 1 (Today):**
1. ✅ Review implementation plan
2. ⏳ Create branch: `git checkout -b feature/sse-streaming`
3. ⏳ Start Step 1.1: Add SSE sink to logging_config.py
4. ⏳ Test sink with dummy logs

**Day 2:**
1. Complete Step 1.2: Create FastAPI server
2. Test file upload endpoint
3. Test SSE streaming with curl

**Day 3:**
1. Complete Step 1.3: Integration testing
2. Upload real PDF and verify logs stream
3. Fix any issues found

**Day 4:**
1. Start Step 2.1: Initialize frontend project
2. Complete Step 2.2: Landing page component
3. Test file upload from browser

**Day 5:**
1. Complete Step 2.3: Transition animation
2. Connect landing page to backend
3. End-to-end test: upload → transition → dashboard (skeleton)

---

## 📝 Notes

- **Field Schema System:** Already complete ✅ (573 lines, 100% coverage)
- **Backend Agents:** Already functional ✅
- **Structured Logging:** Already in place ✅
- **Focus:** SSE streaming + frontend UI

---

## 🔗 Resources

- FastAPI SSE: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
- EventSource API: https://developer.mozilla.org/en-US/docs/Web/API/EventSource
- React + SSE: https://www.smashingmagazine.com/2018/02/sse-websockets-data-flow-http2/
- Tailwind CSS: https://tailwindcss.com/docs

---

**Last Updated:** October 1, 2025  
**Status:** Ready to begin implementation  
**Next Action:** Start Step 1.1 - Add SSE sink to Loguru
