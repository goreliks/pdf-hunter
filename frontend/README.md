# PDF Hunter Frontend

**Real-time monitoring dashboard for PDF Hunter's multi-agent threat analysis system.**

[![React](https://img.shields.io/badge/React-19.1.1-blue.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-7.1.7-646CFF.svg)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4.17-38B2AC.svg)](https://tailwindcss.com/)

## Overview

A modern React dashboard that provides real-time streaming visualization of PDF threat hunting operations. Built with Vite for fast development and Tailwind CSS for styling, featuring a purple/pink gradient theme inspired by n8n's design aesthetic.

### Key Features

- 🔴 **Live SSE Streaming** - Real-time log streaming from backend via Server-Sent Events
- 🤖 **Multi-Agent Monitoring** - Individual panels for 5 specialized agents
- 📱 **Agent Detail Modals** - Full-screen modals with complete agent data, downloadable reports, and state files
- 🎨 **Purple/Pink Theme** - Modern gradient design with glass-morphism effects
- 📊 **View Mode Toggle** - Switch between messages, structured data, or both
- 🎯 **Smart Field Display** - Intelligent field extraction and formatting
- 💾 **localStorage Persistence** - View mode preferences saved across sessions
- 🔄 **Auto-Scroll & Manual Control** - Smart scrolling with user override detection
- 🌟 **Animated Transitions** - Smooth loading animations between screens
- 🔍 **Dev Mode** - Frontend development without backend (mock data replay)

## Architecture

### Application Flow

```
┌─────────────────┐
│  LandingPage    │  PDF Upload + Configuration
│  (File Select)  │  └─ Max Pages Slider (1-4) + Dev Mode Toggle
└────────┬────────┘
         │ Upload
         ▼
┌─────────────────┐
│  Transition     │  Loading Animation
│  Animation      │  └─ 3 Phases: Uploading → Processing → Analyzing
└────────┬────────┘
         │ Complete
         ▼
┌─────────────────┐
│   Dashboard     │  Real-time Monitoring
│                 │  ├─ Header (Status + Session ID)
│                 │  ├─ ViewModeToggle (Both/Messages/Structured)
│                 │  ├─ AgentPanels (5 Agents)
│                 │  │   └─ LogViewer (Collapsible)
│                 │  │       ├─ Messages (Log Level + Text)
│                 │  │       └─ Structured Fields (Node | Event | Field | Value)
│                 │  └─ Sidebar (Right Side)
│                 │      └─ Agent Detail Tabs (7 Tabs)
│                 │          ├─ Click tab → Opens AgentDetailModal
│                 │          └─ Full-screen modal with:
│                 │              ├─ Agent-specific data
│                 │              ├─ JSON state viewer
│                 │              ├─ Download buttons
│                 │              └─ Lightbox for images
└─────────────────┘
```

### Components

```
src/
├── components/
│   ├── LandingPage.jsx         # File upload + configuration + Dev Mode
│   ├── TransitionAnimation.jsx # Loading states (3 phases)
│   ├── Dashboard.jsx           # Main monitoring dashboard
│   ├── AgentPanel.jsx          # Individual agent status panels
│   ├── LogViewer.jsx           # Log rendering engine
│   ├── ViewModeToggle.jsx      # View mode switcher
│   ├── Sidebar.jsx             # Agent navigation sidebar
│   └── AgentDetailModal.jsx    # Full-screen agent detail modal
├── hooks/
│   └── useSSEStream.js         # SSE connection management
├── utils/
│   ├── logUtils.js             # Log routing + formatting
│   ├── fieldExtractor.js       # Field extraction + display
│   └── mockDataLoader.js       # Dev mode mock data loader
├── config/
│   ├── api.js                  # API endpoints
│   └── logFieldSchema.js       # Field mappings for all agents (579 lines)
├── dev/
│   ├── README.md               # Dev mode documentation
│   └── mock-session.jsonl      # Mock session data (3MB)
└── index.css                   # Global styles + theme + animations
```

## Installation

### Prerequisites

- **Node.js** 20+ (LTS recommended)
- **npm** 9+ or **pnpm** 8+
- **Backend Server** running on port 8000 (see main project README) - optional for Dev Mode

### Quick Start

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The development server will start at `http://localhost:5173`

### Environment Variables

Create a `.env` file in the frontend directory (optional):

```bash
# API Base URL (defaults to http://localhost:8000)
VITE_API_BASE_URL=http://localhost:8000

# Notes:
# - In Docker/production the frontend is served with `VITE_API_BASE_URL=/api` so the UI routes requests to the backend proxy.
# - The repo includes `frontend/dev/mock-session.jsonl` which the built frontend copies into `/dev` for a developer mock mode (the install script copies this into built assets when requested).
```

## Development

### Available Scripts

```bash
npm run dev      # Start Vite dev server (port 5173)
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

### Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── assets/          # Images, icons
│   ├── components/      # React components (8 files)
│   │   ├── LandingPage.jsx
│   │   ├── TransitionAnimation.jsx
│   │   ├── Dashboard.jsx
│   │   ├── AgentPanel.jsx
│   │   ├── LogViewer.jsx
│   │   ├── ViewModeToggle.jsx
│   │   ├── Sidebar.jsx
│   │   └── AgentDetailModal.jsx
│   ├── config/          # Configuration files (API, schema)
│   ├── hooks/           # Custom React hooks (SSE streaming)
│   ├── utils/           # Utility functions (log processing, mock data)
│   ├── dev/             # Dev mode assets
│   ├── App.jsx          # Root component
│   ├── main.jsx         # React entry point
│   └── index.css        # Global styles + Tailwind + animations
├── index.html           # HTML template
├── package.json         # Dependencies (@uiw/react-json-view, react-markdown)
├── vite.config.js       # Vite configuration
├── tailwind.config.js   # Tailwind configuration
├── postcss.config.js    # PostCSS configuration
├── README.md            # This file
├── CLAUDE.md            # Technical deep dive for AI assistants
└── QUICKSTART.md        # Quick reference guide
```

## Usage Guide

### 1. Upload a PDF

1. Open the application at `http://localhost:5173`
2. Drag & drop a PDF file or click to browse
3. Adjust the "Pages to Analyze" slider (1-4 pages)
4. Click "🚀 Start Analysis"

### 2. Monitor Analysis

The dashboard displays 5 agent panels:
- **📄 PDF Extraction** - Image and URL extraction
- **🔍 File Analysis** - Static analysis + threat triage
- **🖼️ Image Analysis** - Visual deception detection
- **🔗 URL Investigation** - Browser-based URL analysis
- **📊 Report Generator** - Final report synthesis

### 3. View Modes

Use the toggle in the header to switch views:
- **📋 Both** - Messages + structured fields (default)
- **💬 Messages** - Only log level + message text
- **📊 Structured** - Only structured field rows

### 4. Agent Status

Each panel shows:
- **Idle** (Gray) - No activity yet
- **Running** (Purple/Pink animated) - Currently processing
- **Complete** (Green) - Finished successfully
- **Error** (Red) - Encountered an error

### 5. Agent Detail Modals

Click the **›** button on the right side to open the agent detail sidebar with 7 tabs:

#### 📄 PDF Extraction
- **Analyzed Images** - Lightbox gallery of extracted page screenshots
- **Extraction State** - Complete JSON state with download option

#### 🔍 File Analysis
- **Triage Classification** - Initial threat assessment
- **Structural Analysis** - PDFiD, PDF Parser, Peepdf, XMP metadata outputs
- **Static Analysis Report** - Final verdict, executive summary, IOCs
- **Full State** - Complete JSON with all missions and evidence graphs

#### 🖼️ Image Analysis
- **Analyzed Pages** - Gallery of analyzed images (click for lightbox)
- **Visual Analysis Summary** - Overall verdict, confidence, executive summary
- **Document Flow Summary** - Cross-page narrative analysis
- **Analysis State** - Complete JSON state

#### 🔗 URL Investigation
- **URL Results** - Per-URL verdicts, confidence scores, summaries
- **Investigation State** - Complete JSON with browser analysis data

#### 📊 Report Generator
- **Final Verdict** - Overall threat classification
- **Confidence Score** - Final confidence percentage
- **Executive Summary** - High-level findings
- **Markdown Report** - Full formatted report with reasoning
- **Report State** - Complete JSON

#### 📋 Final State (Available after all agents complete)
- **Complete Analysis JSON** - Full system state with all agent outputs
- **Download Option** - Save analysis_report_session_{sessionId}.json

#### 📝 Raw Logs (Available after all agents complete)
- **Session JSONL** - All log entries in JSONL format
- **Download Option** - Save session.jsonl for debugging

**Note**: Tabs activate only after their respective agents complete. The sidebar remains accessible throughout the analysis.

## Log Display System

### Message Format

```
[LEVEL] Message text
```

Example:
```
INFO    Starting PDF extraction
SUCCESS ✅ Image extraction complete
```

### Structured Field Format

```
node | event_type | field_name | value
```

Example:
```
analyze_images | PAGE_ANALYSIS_COMPLETE | Verdict        | Highly Deceptive
analyze_images | PAGE_ANALYSIS_COMPLETE | Confidence     | 95.0%
analyze_images | PAGE_ANALYSIS_COMPLETE | Page           | 0
analyze_images | PAGE_ANALYSIS_COMPLETE | Findings       | 4
```

### Field Types

**Hidden Fields** (never displayed):
- `agent` - Already shown in panel header
- `node` - Already shown in structured row
- `session_id` - Not relevant during monitoring

**Priority Fields** (shown first):
- `event_type`, `verdict`, `confidence`, `decision`
- `url`, `priority`, `page_number`, `mission_id`
- `reasoning`, `summary`

**Formatted Fields**:
- **Percentages**: `0.95` → `"95.0%"` (confidence, final_confidence)
- **Complex Objects**: Show count instead of content (arrays, objects)
- **URLs**: Truncated to 60 characters if longer
- **Paths**: Show basename only

## Styling & Theming

### Color Palette

The application uses a purple/pink gradient theme inspired by n8n:

**Gradients:**
- Background: `#1a0f2e → #2d1b4e → #1e1335 → #2a1745`
- Buttons: `#8b5cf6 (purple) → #ec4899 (pink)`
- Title: `#f9a8d4 (pink) → #c084fc (purple) → #a5b4fc (indigo)`

**Agent Colors:**
- Running: Purple/Pink gradient with pulse animation
- Complete: Green gradient
- Error: Rose gradient
- Idle: Gray

**Text Colors:**
- Primary: Purple-100 (`#f3e8ff`)
- Secondary: Purple-300/70 (`rgba(216, 180, 254, 0.7)`)
- Muted: Purple-300/50 (`rgba(216, 180, 254, 0.5)`)

### Custom Styles

**Glass Morphism:**
```css
backdrop-blur-sm
bg-gray-800/30
border border-purple-500/20
```

**Card Glow:**
```css
box-shadow: 0 0 20px rgba(139, 92, 246, 0.15);
```

**Animated Gradient Background:**
```css
animation: gradientShift 15s ease infinite;
```

## API Integration

### Endpoints

```javascript
POST   /api/analyze                      # Upload PDF
GET    /api/sessions/{session_id}/stream # SSE log stream
GET    /api/sessions/{session_id}/status # Analysis status
```

### SSE Stream Format

```json
{
  "text": "Log message",
  "record": {
    "level": { "name": "INFO" },
    "message": "Log message",
    "time": { "timestamp": 1696176000 },
    "extra": {
      "agent": "ImageAnalysis",
      "node": "analyze_images",
      "event_type": "PAGE_ANALYSIS_COMPLETE",
      "verdict": "Highly Deceptive",
      "confidence": 0.95,
      "page_number": 0
    }
  }
}
```

### Connection States

- `disconnected` - Initial state
- `connecting` - Establishing connection
- `connected` - Active SSE stream
- `reconnecting` - Attempting to reconnect
- `error` - Connection error
- `failed` - Max reconnection attempts exceeded

## Field Schema System

The application uses a comprehensive field mapping system to determine which fields to display for each agent, node, and event combination.

### Schema Location

```javascript
import { logFieldSchema } from './config/logFieldSchema';
```

### Coverage

- ✅ 5 Agents (PdfExtraction, FileAnalysis, ImageAnalysis, URLInvestigation, ReportGenerator)
- ✅ 29 Nodes across all agents
- ✅ ~65 Unique events
- ✅ 65 Field display name mappings

### Usage Example

```javascript
import { extractFieldsFromLog } from './utils/fieldExtractor';

const log = {
  record: {
    extra: {
      agent: 'ImageAnalysis',
      node: 'analyze_images',
      event_type: 'PAGE_ANALYSIS_COMPLETE',
      verdict: 'Highly Deceptive',
      confidence: 0.95
    }
  }
};

const fields = extractFieldsFromLog(log);
// Returns formatted field objects with display names and values
```

## Performance Considerations

### Optimization Strategies

1. **Auto-scroll Detection**: Disables auto-scroll when user scrolls up
2. **Scroll Position Preservation**: Maintains scroll position during view mode changes
3. **Conditional Rendering**: Empty log entries return null immediately
4. **Event Batching**: SSE messages processed as they arrive
5. **localStorage Caching**: View mode preference persisted

### Limitations

- Max log entries per agent: Unlimited (but consider memory for very long sessions)
- SSE reconnection attempts: 5 (configurable in `useSSEStream.js`)
- Reconnection delay: 2 seconds

## Browser Support

- ✅ Chrome 90+ (Recommended)
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

**Requirements:**
- EventSource API support (for SSE)
- CSS Grid and Flexbox
- localStorage API

## Troubleshooting

### Common Issues

**Issue: SSE connection fails**
```
Solution: Ensure backend server is running on port 8000
Check: curl http://localhost:8000/api/sessions/{session_id}/stream
```

**Issue: No logs appearing**
```
Solution: Check browser console for SSE messages
Verify: Session ID is correct and analysis has started
```

**Issue: View mode not persisting**
```
Solution: Check browser localStorage is enabled
Clear: localStorage.removeItem('pdf-hunter-view-mode')
```

**Issue: Scrollbar not styled**
```
Solution: Custom scrollbar styles require WebKit or Firefox
Note: Falls back to default scrollbar in other browsers
```

## Contributing

### Code Style

- Use functional React components with hooks
- Follow ESLint configuration
- Use Tailwind utility classes (avoid custom CSS when possible)
- Document complex logic with comments
- Use descriptive variable names

### Component Guidelines

1. Keep components focused and single-purpose
2. Extract reusable logic into custom hooks
3. Use proper PropTypes or TypeScript (if migrating)
4. Handle loading and error states
5. Test with real backend data

## Technology Stack

- **React 19.1.1** - UI library
- **Vite 7.1.7** - Build tool and dev server
- **Tailwind CSS 3.4.17** - Utility-first CSS framework
- **PostCSS 8.5.6** - CSS processing
- **ESLint 9.36.0** - Code linting

## Future Enhancements

- [ ] CSV export for log data
- [ ] Log filtering by agent/severity
- [ ] Search functionality
- [ ] Dark/light theme toggle
- [ ] Keyboard shortcuts
- [ ] WebSocket alternative to SSE
- [ ] Mobile responsive design
- [ ] Performance metrics dashboard

## License

Part of the PDF Hunter project. See main project LICENSE file.

## Support

For issues, questions, or contributions, please refer to the main PDF Hunter repository.

---

**Built with ❤️ using React + Vite + Tailwind CSS**
