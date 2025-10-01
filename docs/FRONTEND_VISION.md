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

### **1. Data Source: Loguru Async Sink + SSE (Recommended)**

The frontend receives logs via **Server-Sent Events (SSE)** streamed directly from Loguru's async sink - a single solution that works for both local and remote deployments.

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

1. **Loguru Async Sink**: Configured as a coroutine function that pushes logs to client queues
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

**Alternative Approach (File Polling):**

For desktop apps (Electron/Tauri) with filesystem access, you can skip FastAPI and poll JSONL files directly:
- Frontend reads `output/{session_id}/logs/session.jsonl` every 100-500ms
- Zero backend changes required
- Simpler but ~100-500ms latency vs instant SSE streaming

**Why SSE Over File Polling:**

The async sink + SSE approach is recommended because:
- Works identically on same machine and remote deployments (no code changes)
- No filesystem access required (works in pure web apps)
- Real-time updates without polling overhead
- Production-grade solution with minimal implementation complexity

**File Location (Persistent Backup):**
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
JSONL File (output/{session_id}/logs/session.jsonl)
    ↓
    ↓──→ [Option A] File Polling (100-500ms intervals)
    ↓──→ [Option B] SSE Stream (real-time push)
    ↓
Frontend Event Parser
    ↓
Agent Router (routes by .record.extra.agent field)
    ↓
Agent Panels (visual display)
```

### **Key Design Decisions**

**Why JSONL Files as Source of Truth?**
- Files persist across backend restarts
- Can replay/debug sessions later
- No custom backend work required for basic polling approach
- Natural audit trail for investigations
- Same data structure works for both polling and streaming

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
├── output/                 # Analysis outputs + JSONL logs (existing)
├── docs/                   # Documentation (existing)
│   └── LOGGING_FIELD_REFERENCE.md  # Complete field mapping reference
│
└── dashboard/              # Frontend application (to be created)
    ├── package.json        # Separate npm project
    ├── src/
    │   ├── components/
    │   │   ├── AgentPanel.tsx           # Base panel component
    │   │   ├── PDFExtractionPanel.tsx   # Panel for extraction agent
    │   │   ├── ImageAnalysisPanel.tsx   # Panel for image analysis
    │   │   ├── FileAnalysisPanel.tsx    # Panel for file analysis
    │   │   ├── URLInvestigationPanel.tsx # Panel for URL investigation
    │   │   └── ReportPanel.tsx          # Final report display
    │   ├── hooks/
    │   │   ├── useLogTail.ts            # Hook for polling JSONL file
    │   │   └── useEventRouter.ts        # Hook for routing events to panels
    │   ├── types/
    │   │   └── events.ts                # TypeScript types for log events
    │   └── App.tsx
    └── public/
```

**Development Workflow:**
```bash
# Backend (terminal 1)
uv run python -m pdf_hunter.orchestrator.graph

# Frontend (terminal 2)
cd dashboard
npm run dev
```

### **Deployment Options**

**Option 1: Static Site + File Access**
- Build frontend as static React app
- Serve from same server as backend
- Frontend reads JSONL files directly from filesystem
- Best for: Local development, single-user deployments

**Option 2: API Backend + SSE**
- Add lightweight FastAPI server
- Expose endpoint: `GET /api/sessions/{session_id}/events` (SSE)
- Frontend connects to SSE stream
- Best for: Multi-user deployments, remote access

**Option 3: Hybrid Approach**
- Frontend can switch between file polling and SSE
- Environment variable controls which mode to use
- Same UI code works for both
- Best for: Maximum flexibility

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
