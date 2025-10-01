# PDF Hunter Frontend - Copilot Instructions

## Project Context

**Real-time monitoring dashboard for PDF Hunter's multi-agent PDF threat analysis system.**

This frontend provides live visualization of analysis operations through Server-Sent Events (SSE) streaming from a FastAPI backend. Built with React 19.1.1, Vite 7.1.7, and Tailwind CSS 3.4.17.

## Core Technologies

- **React 19.1.1**: Functional components with hooks
- **Vite 7.1.7**: Build tool with HMR
- **Tailwind CSS 3.4.17**: Utility-first styling
- **SSE (Server-Sent Events)**: Real-time log streaming
- **localStorage**: View mode persistence

## Architecture Overview

### Application Flow

```
LandingPage → TransitionAnimation → Dashboard
    ↓              ↓                      ↓
  Upload      Loading Phases      Real-time Monitoring
```

### Component Hierarchy

```
App.jsx
├── LandingPage.jsx (view === 'landing')
│   ├── File upload (drag & drop)
│   └── Max pages slider (1-4)
├── TransitionAnimation.jsx (view === 'transition')
│   └── Three-phase animation
└── Dashboard.jsx (view === 'dashboard')
    ├── Header (connection status + session ID)
    ├── ViewModeToggle (both/messages/structured)
    └── AgentPanel[] (5 agents)
        └── LogViewer
            ├── LogEntry[] (messages)
            └── FieldRow[] (structured fields)
```

## Key Components

### 1. LandingPage.jsx

**Purpose**: PDF upload and configuration

**State:**
- `file` - Selected PDF file
- `maxPages` - Number of pages to analyze (1-4)
- `isDragging` - Drag-and-drop state
- `isUploading` - Upload in progress
- `error` - Error message

**Key Features:**
- Drag & drop file upload
- File type validation (PDF only)
- Page slider with gradient styling
- Form submission to `/api/analyze`
- Triggers transition on successful upload

**Styling:**
- Purple/pink gradient theme
- Glass-morphism upload area
- Animated logo circle
- Gradient text for title

### 2. TransitionAnimation.jsx

**Purpose**: Loading animation between upload and dashboard

**Phases:**
1. Uploading (0-33%)
2. Processing (33-66%)
3. Analyzing (66-100%)

**Timing:**
- 200ms per progress increment
- Total duration: ~6 seconds
- Auto-transitions to dashboard on completion

**Styling:**
- Purple/pink gradient progress bar
- Animated pulse circles
- Smooth transitions

### 3. Dashboard.jsx

**Purpose**: Main monitoring interface

**State:**
- `viewMode` - Display mode ('both' | 'messages' | 'structured')
- Persisted in localStorage as 'pdf-hunter-view-mode'

**Key Features:**
- Real-time SSE stream via `useSSEStream` hook
- Connection state indicator
- Session ID display
- 5 agent panels with collapsible logs
- View mode toggle

**Props Passed:**
- `sessionId` - From upload response
- `viewMode` - To all AgentPanels

**Connection States:**
- `disconnected`, `connecting`, `connected`
- `reconnecting`, `error`, `failed`

### 4. AgentPanel.jsx

**Purpose**: Individual agent log container

**Props:**
- `agentName` - Technical name (e.g., 'FileAnalysis')
- `displayName` - Human-readable name
- `logs` - Array of log entries for this agent
- `icon` - Emoji icon
- `viewMode` - Current view mode

**State:**
- `isExpanded` - Panel collapsed/expanded

**Status Logic:**
```javascript
// Determined from logs
'idle'     - No logs yet
'running'  - Logs present, last not complete/error
'complete' - Last log contains 'complete' or 'finished'
'error'    - Last log level is ERROR or CRITICAL
```

**Status Styling:**
- Idle: Gray badge
- Running: Purple/Pink gradient + pulse animation
- Complete: Green gradient
- Error: Rose gradient

### 5. LogViewer.jsx

**Purpose**: Renders logs with conditional display

**Props:**
- `logs` - Array of log entries
- `agentName` - For key generation
- `viewMode` - Controls what's displayed

**Key Features:**
- Auto-scroll to bottom (with user override detection)
- Scroll position preservation during mode changes
- Two display formats:
  - **Messages**: `[LEVEL] Message text`
  - **Structured Fields**: `node | event_type | field | value`

**Auto-scroll Logic:**
```javascript
// Disable auto-scroll if user scrolls up
const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
shouldAutoScrollRef.current = isAtBottom;
```

**Component Structure:**
```
LogViewer
├── Container (scrollable, 256px height)
└── LogEntry[] (conditional rendering)
    ├── Message Header (if viewMode !== 'structured')
    │   ├── Log Level Badge
    │   └── Message Text
    └── FieldRow[] (if viewMode !== 'messages')
        ├── Timestamp
        ├── Node
        ├── Event Type
        ├── Field Name
        └── Field Value
```

### 6. ViewModeToggle.jsx

**Purpose**: Switch log display modes

**Modes:**
- `both` (📋) - Show messages + structured fields
- `messages` (💬) - Show only messages
- `structured` (📊) - Show only structured fields

**Styling:**
- Active: Purple/Pink gradient with shadow
- Inactive: Semi-transparent purple text
- Glass-morphism background

## Data Flow

### 1. Log Routing

```javascript
// In Dashboard.jsx
import { groupLogsByAgent } from '../utils/logUtils';

const agentLogs = groupLogsByAgent(logs);
// Returns: { PdfExtraction: [], FileAnalysis: [], ... }
```

**Routing Logic:**
```javascript
// Check log.agent OR log.record.extra.agent
const agentName = log.agent || log.record?.extra?.agent || 'Unknown';
```

### 2. Field Extraction

```javascript
// In LogViewer.jsx
import { extractFieldsFromLog } from '../utils/fieldExtractor';

const fields = extractFieldsFromLog(log);
// Returns: [{ fieldName, displayName, value, isSignificant }, ...]
```

**Field Processing:**
1. Extract from `log.record.extra`
2. Filter out hidden fields (agent, node, session_id)
3. Apply display name mappings
4. Format values (percentages, URLs, etc.)
5. Sort by priority

### 3. Field Display Names

```javascript
// From config/logFieldSchema.js
const FIELD_DISPLAY_NAMES = {
  event_type: 'Event',
  verdict: 'Verdict',
  confidence: 'Confidence',
  page_number: 'Page',
  findings_count: 'Findings',
  // ... 60+ more mappings
};
```

## Log Structure

### SSE Message Format

```json
{
  "text": "Human-readable message",
  "record": {
    "level": { "name": "INFO" },
    "message": "Same as text",
    "time": { "timestamp": 1696176000 },
    "extra": {
      "agent": "ImageAnalysis",
      "node": "analyze_images",
      "event_type": "PAGE_ANALYSIS_COMPLETE",
      "session_id": "abc123_20251001_120000",
      // ... event-specific fields
    }
  }
}
```

### Field Categories

**Hidden Fields** (never displayed):
- `agent` - Shown in panel header
- `node` - Shown in field row structure
- `session_id` - Not relevant during monitoring

**Priority Fields** (displayed first):
1. `event_type`
2. `verdict`
3. `confidence`
4. `decision`
5. `url`
6. `priority`
7. `page_number`
8. `mission_id`
9. `reasoning`
10. `summary`

**Complex Fields** (show count, not content):
- Arrays: `detailed_findings`, `prioritized_urls`, `url_list`, `qr_list`
- Objects: `images_data`, `log_messages`, `detected_threats`

**Formatted Fields:**
- **Percentages**: `confidence: 0.95` → `"95.0%"`
- **URLs**: Truncate to 60 characters if longer
- **Paths**: Show basename only
- **Booleans**: Capitalize (True/False)

## Styling System

### Theme Colors

**Purple/Pink Gradient Palette:**
```javascript
// Primary gradients
from-purple-600 to-pink-600  // Buttons, status badges
from-pink-400 via-purple-400 to-indigo-400  // Title text

// Background layers
#1a0f2e → #2d1b4e → #1e1335 → #2a1745  // Animated gradient

// Text colors
purple-100      // Primary text (#f3e8ff)
purple-300/70   // Secondary text (rgba(216, 180, 254, 0.7))
purple-300/50   // Muted text (rgba(216, 180, 254, 0.5))

// Borders
purple-500/20   // Glass-morphism borders (rgba(139, 92, 246, 0.2))
purple-500/30   // Hover borders (rgba(139, 92, 246, 0.3))
```

### Log Level Colors

```javascript
// From utils/logUtils.js
DEBUG/TRACE   → purple-300/60
INFO          → cyan-400
SUCCESS       → emerald-400
WARNING       → amber-400
ERROR         → rose-400
CRITICAL      → rose-500 font-bold
```

### Custom Classes

**Glass Morphism:**
```css
backdrop-blur-sm bg-gray-800/30 border border-purple-500/20
```

**Card Glow:**
```css
.card-glow {
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.15);
}
.card-glow:hover {
  box-shadow: 0 0 30px rgba(139, 92, 246, 0.25);
}
```

**Gradient Background:**
```css
.gradient-bg {
  background: linear-gradient(135deg, #1a0f2e, #2d1b4e, #1e1335, #2a1745);
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
}
```

**Custom Scrollbar:**
```css
/* Purple/pink gradient scrollbar thumb */
::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #8b5cf6, #ec4899);
  border-radius: 6px;
}
```

**Custom Slider:**
```css
/* Purple/pink gradient range input */
.slider::-webkit-slider-thumb {
  background: linear-gradient(135deg, #ec4899, #8b5cf6);
  box-shadow: 0 0 10px rgba(236, 72, 153, 0.5);
}
```

## Hooks

### useSSEStream(sessionId)

**Purpose**: Manage SSE connection and log accumulation

**Returns:**
```javascript
{
  logs,            // Array of all log entries
  isConnected,     // Boolean connection status
  error,           // Error message or null
  connectionState  // 'disconnected' | 'connecting' | etc.
}
```

**Features:**
- Auto-connect on mount
- Auto-reconnect (5 attempts, 2s delay)
- Cleanup on unmount
- Error handling with state updates

**Implementation:**
```javascript
const eventSource = new EventSource(API_ENDPOINTS.stream(sessionId));

eventSource.onmessage = (event) => {
  const logEntry = JSON.parse(event.data);
  setLogs(prev => [...prev, logEntry]);
};

eventSource.onerror = () => {
  // Attempt reconnection
};
```

## Utility Functions

### logUtils.js

```javascript
// Group logs by agent
groupLogsByAgent(logs) → { PdfExtraction: [], FileAnalysis: [], ... }

// Get agent status from logs
getAgentStatus(agentLogs) → 'idle' | 'running' | 'complete' | 'error'

// Get log level color
getLogLevelColor(level) → 'text-cyan-400' // Tailwind class

// Format single log line
formatLogLine(log) → '[timestamp] LEVEL [node] message'
```

### fieldExtractor.js

```javascript
// Extract displayable fields
extractFieldsFromLog(log) → [{ fieldName, displayName, value }, ...]

// Extract as display rows
extractDisplayRows(log) → [{ displayText, node, eventType, ... }, ...]

// Group by importance
groupFieldsByImportance(fields) → { critical: [], important: [], standard: [] }

// Check if event is significant
isSignificantEvent(log) → boolean

// Extract key metrics for cards
extractKeyMetrics(log) → { type, label, value, confidence }
```

## API Configuration

### config/api.js

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  analyze: `${API_BASE_URL}/api/analyze`,
  stream: (sessionId) => `${API_BASE_URL}/api/sessions/${sessionId}/stream`,
  status: (sessionId) => `${API_BASE_URL}/api/sessions/${sessionId}/status`,
};
```

## Field Schema

### config/logFieldSchema.js

**Structure:**
```javascript
{
  AGENT_NAME_SCHEMA: {
    node_name: {
      event_type_or_null: ['field1', 'field2', ...]
    }
  }
}
```

**Example:**
```javascript
IMAGE_ANALYSIS_SCHEMA: {
  analyze_images: {
    PAGE_ANALYSIS_COMPLETE: [
      'agent', 'benign_signals', 'confidence', 'deception_tactics',
      'detailed_findings', 'event_type', 'node', 'page_number',
      'session_id', 'verdict'
    ]
  }
}
```

**Functions:**
```javascript
getExpectedFields(agent, node, eventType) → string[]
shouldDisplayField(fieldName) → boolean
getFieldDisplayName(fieldName) → string
formatFieldValue(fieldName, value) → string
sortFieldsByPriority(fields) → string[]
```

## Common Patterns

### Adding a New Component

```javascript
import React from 'react';

export default function NewComponent({ prop1, prop2 }) {
  // Use hooks at top
  const [state, setState] = useState(initialValue);
  
  // Event handlers
  const handleEvent = () => {
    // logic
  };
  
  // Return JSX
  return (
    <div className="purple/pink-themed-classes">
      {/* Content */}
    </div>
  );
}
```

### Styling Guidelines

1. **Use Tailwind classes** instead of custom CSS
2. **Follow theme colors** (purple/pink gradients)
3. **Add glass-morphism** for containers: `backdrop-blur-sm bg-gray-800/30 border border-purple-500/20`
4. **Use gradients** for interactive elements: `bg-gradient-to-r from-purple-600 to-pink-600`
5. **Add transitions**: `transition-all duration-300`
6. **Include hover states**: `hover:bg-purple-900/30`

### Handling New Log Fields

1. **Update Field Schema** (`config/logFieldSchema.js`):
   ```javascript
   node_name: {
     EVENT_TYPE: [...existingFields, 'new_field']
   }
   ```

2. **Add Display Name** (if needed):
   ```javascript
   FIELD_DISPLAY_NAMES.new_field = 'Display Name';
   ```

3. **Add Custom Formatter** (if needed):
   ```javascript
   if (fieldName === 'new_field') {
     return customFormat(value);
   }
   ```

4. **Update Priority** (if important):
   ```javascript
   PRIORITY_FIELDS.splice(position, 0, 'new_field');
   ```

## Performance Best Practices

1. **Conditional Rendering**: Return `null` early if no content to display
2. **Memoization**: Use `React.memo()` for expensive components
3. **Refs over State**: Use `useRef` for values that don't need re-renders
4. **Debounce**: Debounce expensive operations (if needed)
5. **Lazy Loading**: Use `React.lazy()` for code splitting (if needed)

## Development Workflow

### Starting Development

```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

### Testing with Backend

1. Start backend: `cd .. && uv run uvicorn pdf_hunter.api.server:app --reload`
2. Backend runs on port 8000
3. Upload PDF through frontend
4. Monitor logs in dashboard

### Hot Reload

- Vite provides instant HMR
- Save any file to see changes immediately
- No manual refresh needed

### Debugging

```javascript
// Add console logs
console.log('📨 Received SSE:', event.data);

// Check state in DevTools
// React DevTools extension recommended

// Verify localStorage
localStorage.getItem('pdf-hunter-view-mode');
```

## Common Issues & Solutions

### Issue: Logs not appearing

**Check:**
1. Backend server running? `curl http://localhost:8000`
2. SSE connection established? Check browser console
3. Session ID correct? Verify in header display
4. Agent name matching? Check `log.agent` or `log.record.extra.agent`

### Issue: Fields not displaying correctly

**Check:**
1. Field in schema? See `config/logFieldSchema.js`
2. Field hidden? Check `HIDDEN_FIELDS` array
3. Display name missing? Check `FIELD_DISPLAY_NAMES`
4. View mode correct? Try 'both' mode

### Issue: Styling not working

**Check:**
1. Tailwind class exists? Verify in Tailwind docs
2. Custom class defined? See `index.css`
3. Purge not removing? Check `tailwind.config.js`
4. Browser cache? Hard refresh (Cmd+Shift+R)

## File Locations Reference

```
frontend/
├── src/
│   ├── components/
│   │   ├── LandingPage.jsx         # Upload screen
│   │   ├── TransitionAnimation.jsx # Loading animation
│   │   ├── Dashboard.jsx           # Main dashboard
│   │   ├── AgentPanel.jsx          # Agent container
│   │   ├── LogViewer.jsx           # Log rendering
│   │   └── ViewModeToggle.jsx      # Mode switcher
│   ├── hooks/
│   │   └── useSSEStream.js         # SSE connection hook
│   ├── utils/
│   │   ├── logUtils.js             # Log utilities
│   │   └── fieldExtractor.js       # Field extraction
│   ├── config/
│   │   ├── api.js                  # API endpoints
│   │   └── logFieldSchema.js       # Field mappings
│   ├── App.jsx                     # Root component
│   ├── main.jsx                    # Entry point
│   └── index.css                   # Global styles
├── package.json                    # Dependencies
├── vite.config.js                  # Vite config
├── tailwind.config.js              # Tailwind config
└── README.md                       # Documentation
```

## Agent Reference

| Agent | Icon | Description |
|-------|------|-------------|
| PdfExtraction | 📄 | Extracts images, embedded URLs, QR codes |
| FileAnalysis | 🔍 | Static analysis, threat triage, missions |
| ImageAnalysis | 🖼️ | Visual deception detection, phishing analysis |
| URLInvestigation | 🔗 | Browser automation, URL reconnaissance |
| ReportGenerator | 📊 | Final report synthesis, verdict determination |

## Key Considerations

1. **Always use functional components** with hooks (no class components)
2. **Follow purple/pink theme** for all new UI elements
3. **Test with real backend** before considering complete
4. **Handle loading/error states** in all async operations
5. **Use Tailwind utilities** instead of writing custom CSS
6. **Document complex logic** with inline comments
7. **Keep components small** and focused
8. **Extract reusable logic** into hooks/utilities
9. **Preserve scroll position** during UI updates
10. **Respect user preferences** (view mode, scroll position)

---

**Last Updated**: October 2025
**React Version**: 19.1.1
**Vite Version**: 7.1.7
**Tailwind Version**: 3.4.17
