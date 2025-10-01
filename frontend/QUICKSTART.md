# Frontend Quick Reference

**Last Updated:** October 1, 2025

## Current Implementation Status

### ✅ Completed Features

1. **Three-Screen Application Flow**
   - LandingPage: PDF upload with drag & drop
   - TransitionAnimation: Loading phases (3 stages)
   - Dashboard: Real-time monitoring

2. **SSE Streaming System**
   - Real-time log streaming via Server-Sent Events
   - Auto-reconnection (5 attempts, 2s delay)
   - Connection state management
   - Log accumulation and routing to agents

3. **View Mode Toggle**
   - Three modes: Both, Messages, Structured
   - localStorage persistence
   - Scroll position preservation

4. **Log Display**
   - Message format: `[LEVEL] Message text`
   - Structured format: `node | event_type | field | value`
   - Auto-scroll with manual override
   - Smart field extraction and formatting

5. **Purple/Pink Theme**
   - n8n-inspired gradient design
   - Glass-morphism effects
   - Animated gradient background
   - Custom scrollbars and sliders
   - Card glow effects

6. **Field Schema System**
   - 5 agents, 29 nodes, ~65 events mapped
   - 65+ display name mappings
   - Smart formatting (percentages, URLs, etc.)
   - Priority-based sorting

7. **Session Persistence**
   - Auto-save via sessionStorage
   - Survives page refresh
   - SSE auto-reconnect with log replay
   - "New Analysis" button to clear

8. **Dev Mode** 🆕
   - Toggle on landing page
   - Uses mock data from successful session
   - No backend required for frontend development
   - Simulates real-time log streaming
   - Auto-disables on "New Analysis"

### 📦 Tech Stack

- React 19.1.1
- Vite 7.1.7
- Tailwind CSS 3.4.17
- EventSource (SSE)
- localStorage

### 🚀 Quick Start

```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

Backend must be running on port 8000.

### 📁 Key Files

```
src/
├── components/
│   ├── LandingPage.jsx       # Upload screen + Dev Mode
│   ├── TransitionAnimation.jsx # Loading
│   ├── Dashboard.jsx          # Main dashboard
│   ├── AgentPanel.jsx         # Agent container
│   ├── LogViewer.jsx          # Log rendering
│   └── ViewModeToggle.jsx     # Mode switcher
├── hooks/
│   └── useSSEStream.js        # SSE connection
├── utils/
│   ├── logUtils.js            # Log routing
│   ├── fieldExtractor.js      # Field extraction
│   └── mockDataLoader.js      # Dev mode mock data
├── config/
│   ├── api.js                 # API endpoints
│   └── logFieldSchema.js      # Field mappings (579 lines)
├── dev/                       # Dev Mode assets
│   ├── README.md              # Dev Mode guide
│   └── mock-session.jsonl     # Mock data
└── index.css                  # Theme styles
```

### 🎨 Color Palette

**Gradients:**
```
Background: #1a0f2e → #2d1b4e → #1e1335 → #2a1745
Buttons: #8b5cf6 (purple) → #ec4899 (pink)
Title: #f9a8d4 (pink) → #c084fc (purple) → #a5b4fc (indigo)
```

**Status Colors:**
- Running: Purple/Pink gradient + pulse
- Complete: Green gradient
- Error: Rose gradient
- Idle: Gray

### 🔌 API Endpoints

```
POST /api/analyze              # Upload PDF
GET  /api/sessions/{id}/stream # SSE stream
GET  /api/sessions/{id}/status # Status check
```

### 📊 Log Structure

```javascript
{
  text: "Message",
  record: {
    level: { name: "INFO" },
    message: "Message",
    time: { timestamp: 1696176000 },
    extra: {
      agent: "ImageAnalysis",
      node: "analyze_images",
      event_type: "PAGE_ANALYSIS_COMPLETE",
      session_id: "abc123_20251001_120000",
      // Event-specific fields...
    }
  }
}
```

### 🤖 Agents

1. **📄 PdfExtraction** - Image/URL/QR extraction
2. **🔍 FileAnalysis** - Static analysis + missions
3. **🖼️ ImageAnalysis** - Visual deception detection
4. **🔗 URLInvestigation** - Browser-based URL analysis
5. **📊 ReportGenerator** - Final report synthesis

### 🔧 Common Tasks

**Enable Dev Mode:**
1. Toggle "Dev Mode" on landing page
2. Click "Start Dev Mode Analysis"
3. Dashboard loads with mock data
4. No backend required

**Update Mock Data:**
```bash
# After successful real analysis
cp ../output/{session_id}/logs/session.jsonl dev/mock-session.jsonl
```

**Add New Agent:**
1. Update `logUtils.js` - Add to agents object
2. Update `logFieldSchema.js` - Add schema
3. Update `Dashboard.jsx` - Add AgentPanel

**Add New Field:**
1. Update `logFieldSchema.js` - Add to event array
2. Add display name to `FIELD_DISPLAY_NAMES`
3. Add formatter (if needed)
4. Add to `PRIORITY_FIELDS` (if important)

**Change Colors:**
- Edit `src/index.css`
- Update gradient definitions
- Modify custom classes

### 📚 Documentation

- **README.md** - Comprehensive setup guide
- **CLAUDE.md** - Deep technical reference for AI assistants
- **.github/copilot-instructions.md** - GitHub Copilot guidance

### 🐛 Debugging

**SSE Issues:**
```bash
# Check backend
curl http://localhost:8000/api/sessions/test/stream

# Check browser console for:
'✅ SSE connection established'
'📨 Received SSE message:'
```

**Log Issues:**
```javascript
// In Dashboard.jsx
console.log('Logs:', logs.length);
console.log('Agent logs:', agentLogs);
```

**Styling Issues:**
```bash
# Hard refresh
Cmd+Shift+R (Mac) or Ctrl+Shift+R (Win)

# Restart Vite
npm run dev
```

### 📝 Development Notes

- All components are functional with hooks
- Use Tailwind utilities (avoid custom CSS)
- Follow purple/pink theme consistently
- Test with real backend data
- Handle loading/error states
- Document complex logic

---

For detailed information, see:
- **README.md** - Full documentation
- **CLAUDE.md** - Technical deep dive
- **.github/copilot-instructions.md** - AI assistant guide
