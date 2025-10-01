# PDF Hunter Frontend - Claude/AI Assistant Guide

**Comprehensive reference for AI assistants working with the PDF Hunter frontend codebase.**

## Quick Context

This is a **React 19.1.1 + Vite 7.1.7 + Tailwind CSS 3.4.17** single-page application that displays real-time analysis logs from a PDF threat hunting backend via **Server-Sent Events (SSE)**.

**Theme**: Purple/pink gradient design inspired by n8n, with glass-morphism effects.

**Purpose**: Monitor 5 specialized AI agents analyzing PDFs for threats in real-time.

## Project State (October 2025)

### What's Implemented ✅

1. **Three-Screen Flow**:
   - LandingPage: PDF upload + max pages slider
   - TransitionAnimation: Loading progress (3 phases)
   - Dashboard: Real-time log monitoring

2. **SSE Streaming**:
   - Custom `useSSEStream` hook
   - Auto-reconnection (5 attempts, 2s delay)
   - Connection state management
   - Log accumulation and routing

3. **View Mode Toggle**:
   - Three modes: Both, Messages, Structured
   - localStorage persistence (`pdf-hunter-view-mode`)
   - Scroll position preservation during mode changes

4. **Log Display**:
   - Two formats: Message headers + Structured field rows
   - Auto-scroll with user override detection
   - Conditional rendering based on view mode
   - Empty row prevention

5. **Field System**:
   - Comprehensive schema mapping (579 lines)
   - Display name mappings (65+ fields)
   - Smart field extraction and formatting
   - Priority-based sorting

6. **Styling**:
   - Purple/pink gradient theme throughout
   - Glass-morphism effects on containers
   - Animated gradient background
   - Custom scrollbars (purple/pink gradient)
   - Custom range sliders (purple/pink gradient)
   - Card glow effects
   - Status badges with gradients

7. **Optimizations**:
   - Text wrapping (`break-all`) on long filenames/messages
   - Terminal-optimized font size (12px)
   - Compact spacing (33% reduction)
   - Efficient rendering (early returns)

### What's NOT Implemented ❌

1. CSV export functionality
2. Log filtering/search
3. Dark/light theme toggle
4. Mobile responsive design
5. Keyboard shortcuts
6. Performance metrics dashboard
7. WebSocket alternative to SSE

## Architecture Deep Dive

### State Management

**App-level State** (App.jsx):
```javascript
const [view, setView] = useState('landing');  // 'landing' | 'transition' | 'dashboard'
const [analysisData, setAnalysisData] = useState(null);  // { sessionId, streamUrl, statusUrl, filename }
```

**Dashboard State** (Dashboard.jsx):
```javascript
const [viewMode, setViewMode] = useState(() => localStorage.getItem('pdf-hunter-view-mode') || 'both');
// Persisted to localStorage on change
```

**SSE Hook State** (useSSEStream.js):
```javascript
const [logs, setLogs] = useState([]);  // Accumulated log entries
const [isConnected, setIsConnected] = useState(false);  // Connection status
const [error, setError] = useState(null);  // Error message
const [connectionState, setConnectionState] = useState('disconnected');  // State string
```

**Agent Panel State** (AgentPanel.jsx):
```javascript
const [isExpanded, setIsExpanded] = useState(true);  // Collapse/expand panel
```

### Data Flow: Log Entry to Display

```
1. SSE Message Arrives
   ↓
2. useSSEStream.onmessage
   ↓ JSON.parse(event.data)
3. Add to logs array
   ↓ setLogs(prev => [...prev, logEntry])
4. Dashboard receives logs
   ↓ groupLogsByAgent(logs)
5. Logs routed to agent panels
   ↓ agentLogs[agentName]
6. AgentPanel passes to LogViewer
   ↓ <LogViewer logs={logs} viewMode={viewMode} />
7. LogViewer renders each log
   ↓ logs.map(log => <LogEntry />)
8. LogEntry extracts fields
   ↓ extractFieldsFromLog(log)
9. Conditional rendering based on viewMode
   ↓ Message Header + Field Rows
10. Display on screen
```

### Log Structure Anatomy

```javascript
{
  text: "Human-readable message",  // Plain text version
  agent: "ImageAnalysis",  // Optional: top-level agent field
  record: {
    level: {
      name: "INFO"  // DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL
    },
    message: "Same as text field",
    time: {
      timestamp: 1696176000  // Unix timestamp
    },
    extra: {
      // THIS IS WHERE EVERYTHING LIVES
      agent: "ImageAnalysis",  // PascalCase
      node: "analyze_images",  // snake_case
      event_type: "PAGE_ANALYSIS_COMPLETE",  // UPPER_SNAKE_CASE or null
      session_id: "abc123_20251001_120000",
      
      // Event-specific fields (varies by agent/node/event)
      verdict: "Highly Deceptive",
      confidence: 0.95,
      page_number: 0,
      findings_count: 4,
      // ... more fields depending on event
    }
  }
}
```

### Field Extraction Logic

**Step 1: Extract from `record.extra`**
```javascript
const extra = log.record?.extra || {};
const fields = Object.entries(extra);
```

**Step 2: Filter Hidden Fields**
```javascript
const HIDDEN_FIELDS = ['agent', 'node', 'session_id'];
fields = fields.filter(([name]) => !HIDDEN_FIELDS.includes(name));
```

**Step 3: Get Display Names**
```javascript
const FIELD_DISPLAY_NAMES = {
  event_type: 'Event',
  verdict: 'Verdict',
  confidence: 'Confidence',
  page_number: 'Page',
  findings_count: 'Findings',
  // ... 60+ more
};

displayName = FIELD_DISPLAY_NAMES[fieldName] || fieldName;
```

**Step 4: Format Values**
```javascript
// Percentages: 0.95 → "95.0%"
if (['confidence', 'final_confidence'].includes(fieldName)) {
  return `${(value * 100).toFixed(1)}%`;
}

// Complex objects: Show count
if (Array.isArray(value)) {
  return `${value.length} items`;
}

// URLs: Truncate if > 60 chars
if (fieldName.includes('url') && value.length > 60) {
  return value.substring(0, 60) + '...';
}

// Paths: Show basename
if (fieldName.includes('path') || fieldName.includes('file')) {
  return value.split('/').pop();
}

// Default: String conversion
return String(value);
```

**Step 5: Sort by Priority**
```javascript
const PRIORITY_FIELDS = [
  'event_type', 'verdict', 'confidence', 'decision',
  'url', 'priority', 'page_number', 'mission_id',
  'reasoning', 'summary'
];

fields.sort((a, b) => {
  const aIndex = PRIORITY_FIELDS.indexOf(a.fieldName);
  const bIndex = PRIORITY_FIELDS.indexOf(b.fieldName);
  if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
  if (aIndex !== -1) return -1;
  if (bIndex !== -1) return 1;
  return 0;
});
```

### View Mode Logic

**Both Mode** (default):
```javascript
shouldShowMessage = true;
shouldShowFields = fields.length > 0;
```

**Messages Mode**:
```javascript
shouldShowMessage = true;
shouldShowFields = false;
```

**Structured Mode**:
```javascript
shouldShowMessage = false;
shouldShowFields = fields.length > 0;
```

**Empty Prevention**:
```javascript
if (!shouldShowMessage && !shouldShowFields) {
  return null;  // Don't render anything
}
```

### Auto-Scroll Logic

```javascript
// In LogViewer.jsx
const handleScroll = () => {
  const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current;
  const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;  // 50px threshold
  shouldAutoScrollRef.current = isAtBottom;
};

// In useEffect (when logs change)
if (shouldAutoScrollRef.current) {
  logContainerRef.current?.scrollTo({
    top: logContainerRef.current.scrollHeight,
    behavior: 'smooth'
  });
}
```

### Scroll Position Preservation

```javascript
// In LogViewer.jsx
useEffect(() => {
  if (prevViewModeRef.current !== viewMode) {
    // Save scroll position before mode change
    scrollPosBeforeToggleRef.current = logContainerRef.current?.scrollTop || 0;
    
    // Restore after React renders
    requestAnimationFrame(() => {
      if (logContainerRef.current) {
        logContainerRef.current.scrollTop = scrollPosBeforeToggleRef.current;
      }
    });
    
    prevViewModeRef.current = viewMode;
  }
}, [viewMode]);
```

## Agent Specifications

### 1. PdfExtraction (📄)

**Nodes**: `setup_session`, `extract_pdf_images`, `find_embedded_urls`, `scan_qr_codes`

**Key Events**:
- `SESSION_CREATED` - Session initialized
- `IMAGE_EXTRACTION_COMPLETE` - Images extracted
- `URL_SEARCH_COMPLETE` - URLs found
- `QR_SCAN_COMPLETE` - QR codes decoded

**Important Fields**:
- `output_directory` - Where files are saved
- `image_count` - Number of images extracted
- `url_count` - Number of URLs found
- `qr_count` - Number of QR codes decoded

### 2. FileAnalysis (🔍)

**Nodes**: `identify_suspicious_elements`, `create_analysis_tasks`, `assign_analysis_tasks`, `run_investigation`, `file_analyzer`, `aggregate_investigation_results`, `prepare_synthesis_data`

**Key Events**:
- `TRIAGE_COMPLETE` - Initial threat assessment
- `MISSION_ASSIGNED` - Investigation task created
- `INVESTIGATION_COMPLETE` - Mission finished
- `INVESTIGATION_BLOCKED` - Recursion limit hit
- `STRATEGIC_REFLECTION` - Think tool used

**Important Fields**:
- `decision` - "Further Investigation" or "Low Risk"
- `mission_count` - Number of investigations
- `mission_id` - Task identifier
- `mission_status` - COMPLETED, FAILED, BLOCKED
- `reasoning` - Why decision was made
- `reflection` - Strategic thinking output

### 3. ImageAnalysis (🖼️)

**Nodes**: `analyze_images`, `compile_image_findings`

**Key Events**:
- `PAGE_ANALYSIS_COMPLETE` - Individual page analyzed
- `ANALYSIS_COMPLETE` - All pages done

**Important Fields**:
- `verdict` - "Benign", "Suspicious", "Highly Deceptive"
- `confidence` - 0.0 to 1.0 (displayed as percentage)
- `page_number` - Which page (0-indexed)
- `findings_count` - Number of issues found
- `benign_signals` - Count of normal elements
- `deception_tactics` - Count of suspicious patterns

### 4. URLInvestigation (🔗)

**Nodes**: `receive_prioritized_urls`, `setup_url_task`, `execute_browser_tools`, `check_mission_completion`, `generate_url_report`, `compile_url_analysis`

**Key Events**:
- `URLS_RECEIVED` - URLs to investigate
- `URL_TASK_CREATED` - Browser task setup
- `TOOL_EXECUTION` - Browser tool used
- `STRATEGIC_THINKING` - Think tool used
- `URL_REPORT_COMPLETE` - Individual URL done
- `ALL_URLS_COMPLETE` - Investigation finished

**Important Fields**:
- `url` - The URL being investigated
- `priority` - 1-10 (≤5 = analyzed, >5 = skipped)
- `status` - NEW, IN_PROGRESS, COMPLETED, FAILED
- `tool_name` - Browser tool executed
- `verdict` - Analysis result
- `reflection` - Strategic thinking output

### 5. ReportGenerator (📊)

**Nodes**: `determine_threat_verdict`, `generate_final_report`, `save_analysis_results`

**Key Events**:
- `VERDICT_DETERMINED` - Final decision made
- `REPORT_GENERATED` - Report complete
- `RESULTS_SAVED` - Files written

**Important Fields**:
- `overall_verdict` - "Benign", "Suspicious", "Malicious"
- `final_confidence` - 0.0 to 1.0 (percentage)
- `summary` - Brief overview
- `report_path` - Where report was saved

## Styling System Reference

### Color Variables

```javascript
// Purple Shades
purple-100: #f3e8ff  // Lightest, primary text
purple-200: #e9d5ff  // Secondary text
purple-300: #d8b4fe  // Muted text (with opacity)
purple-400: #c084fc  // Accents
purple-500: #a855f6  // Borders (with opacity)
purple-600: #9333ea  // Buttons/badges
purple-900: #581c87  // Hover backgrounds (with opacity)

// Pink Shades
pink-400: #f472b6   // Gradient end
pink-500: #ec4899   // Primary pink
pink-600: #db2777   // Hover pink

// Other Colors
cyan-400: #22d3ee    // INFO logs
emerald-400: #34d399 // SUCCESS logs, connections
amber-400: #fbbf24   // WARNING logs
rose-400: #fb7185    // ERROR logs
rose-500: #f43f5e    // CRITICAL logs, disconnections

// Grays
gray-100: #f3f4f6   // Light text
gray-800: #1f2937   // Container backgrounds (with opacity)
gray-900: #111827   // Dark backgrounds
```

### Opacity Levels

```
/10 = 10% opacity  - Very subtle highlights
/20 = 20% opacity  - Borders, subtle elements
/30 = 30% opacity  - Container backgrounds
/40 = 40% opacity  - Disabled text
/50 = 50% opacity  - Muted text, tracks
/60 = 60% opacity  - Secondary text
/70 = 70% opacity  - Standard text
/80 = 80% opacity  - Primary elements
```

### Common Class Combinations

**Glass-morphism Container**:
```
bg-gray-800/30 backdrop-blur-sm border border-purple-500/20 rounded-lg
```

**Gradient Button (Active)**:
```
bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/30
```

**Gradient Button (Hover)**:
```
hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/50 hover:scale-105
```

**Status Badge (Running)**:
```
bg-gradient-to-r from-purple-600 to-pink-600 text-white animate-pulse border border-purple-400/50
```

**Card Glow**:
```
card-glow  // Custom class in index.css
```

**Animated Background**:
```
gradient-bg  // Custom class in index.css
```

### Typography

**Font Sizes**:
```
text-xs: 12px    // Log entries, structured fields (terminal-standard)
text-sm: 14px    // Secondary text, labels
text-lg: 18px    // Larger labels
text-xl: 20px    // Section headers
text-2xl: 24px   // Values, numbers
text-3xl: 30px   // Page titles
text-5xl: 48px   // Main title
```

**Font Families**:
```
font-mono  // Log viewer (monospace)
font-sans  // Everything else (default)
```

**Font Weights**:
```
font-medium: 500   // Labels
font-semibold: 600 // Headers
font-bold: 700     // Emphasis
```

**Line Heights**:
```
leading-snug: 1.375     // Compact logs
leading-relaxed: 1.625  // Normal text
```

## Common Modification Patterns

### Adding a New Agent

1. **Update groupLogsByAgent** (`utils/logUtils.js`):
```javascript
const agents = {
  // ... existing agents
  NewAgentName: [],
};
```

2. **Add schema** (`config/logFieldSchema.js`):
```javascript
export const NEW_AGENT_SCHEMA = {
  node_name: {
    EVENT_TYPE: ['field1', 'field2', ...],
    null: ['agent', 'node', 'session_id']
  }
};
```

3. **Update LOG_FIELD_SCHEMA**:
```javascript
export const LOG_FIELD_SCHEMA = {
  // ... existing agents
  NewAgentName: NEW_AGENT_SCHEMA
};
```

4. **Add to Dashboard** (`components/Dashboard.jsx`):
```javascript
<AgentPanel
  agentName="NewAgentName"
  displayName="New Agent Display Name"
  logs={agentLogs.NewAgentName}
  icon="🆕"
  viewMode={viewMode}
/>
```

### Adding a New Event Type

1. **Update schema** (`config/logFieldSchema.js`):
```javascript
AGENT_NAME_SCHEMA: {
  existing_node: {
    // ... existing events
    NEW_EVENT_TYPE: ['agent', 'node', 'event_type', 'new_field1', 'new_field2']
  }
}
```

2. **Add display names** (if new fields):
```javascript
FIELD_DISPLAY_NAMES.new_field1 = 'Display Name 1';
FIELD_DISPLAY_NAMES.new_field2 = 'Display Name 2';
```

3. **Add priority** (if important):
```javascript
PRIORITY_FIELDS.splice(index, 0, 'new_field1');
```

4. **Add formatter** (if special format needed):
```javascript
if (fieldName === 'new_field1') {
  return customFormat(value);
}
```

### Changing Theme Colors

All theme colors are in `src/index.css`:

```css
/* Change gradient background */
.gradient-bg {
  background: linear-gradient(135deg, #new1, #new2, #new3, #new4);
}

/* Change slider colors */
.slider::-webkit-slider-thumb {
  background: linear-gradient(135deg, #new-pink, #new-purple);
}

/* Change scrollbar colors */
::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #new-purple, #new-pink);
}
```

### Adding a New View Mode

1. **Add to ViewModeToggle** (`components/ViewModeToggle.jsx`):
```javascript
const modes = [
  // ... existing modes
  { value: 'new-mode', label: 'New Mode', icon: '🆕' }
];
```

2. **Update LogViewer logic** (`components/LogViewer.jsx`):
```javascript
const shouldShowMessage = viewMode !== 'structured' && viewMode !== 'new-mode';
const shouldShowFields = viewMode !== 'messages';
const shouldShowNewThing = viewMode === 'new-mode';
```

3. **Add conditional rendering**:
```javascript
{shouldShowNewThing && (
  <NewThingComponent />
)}
```

## Debugging Guide

### SSE Connection Issues

**Check 1: Backend Running?**
```bash
curl http://localhost:8000/api/sessions/test/stream
# Should return SSE events or error
```

**Check 2: Browser Console**
```javascript
// Should see these logs:
'✅ SSE connection established'
'📨 Received SSE message: {...}'
'✅ Parsed log entry: {...}'
```

**Check 3: EventSource State**
```javascript
// In useSSEStream.js, add:
console.log('EventSource readyState:', eventSource.readyState);
// 0 = CONNECTING, 1 = OPEN, 2 = CLOSED
```

**Check 4: CORS Issues?**
```javascript
// Backend should have:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Logs Not Displaying

**Check 1: Logs Arriving?**
```javascript
// In Dashboard.jsx, add:
console.log('Total logs:', logs.length);
console.log('Agent logs:', agentLogs);
```

**Check 2: Agent Routing**
```javascript
// Check log structure:
console.log('Sample log:', logs[0]);
console.log('Agent field:', logs[0]?.agent || logs[0]?.record?.extra?.agent);
```

**Check 3: View Mode**
```javascript
// Check current mode:
console.log('View mode:', viewMode);
localStorage.getItem('pdf-hunter-view-mode');
```

**Check 4: Fields Extracted?**
```javascript
// In LogViewer.jsx, add:
const fields = extractFieldsFromLog(log);
console.log('Extracted fields:', fields);
```

### Styling Issues

**Check 1: Tailwind Purge**
```javascript
// In tailwind.config.js, ensure:
content: [
  './index.html',
  './src/**/*.{js,ts,jsx,tsx}',
],
```

**Check 2: Custom Classes**
```css
/* In index.css, verify custom classes exist */
.gradient-bg { /* ... */ }
.card-glow { /* ... */ }
.slider { /* ... */ }
```

**Check 3: Browser DevTools**
```
1. Inspect element
2. Check computed styles
3. Verify Tailwind classes applied
4. Check for !important overrides
```

**Check 4: Hot Reload**
```bash
# Sometimes Vite needs restart
# Ctrl+C to stop
npm run dev
```

### Performance Issues

**Check 1: Log Count**
```javascript
// In Dashboard.jsx
console.log('Total log entries:', logs.length);
// If > 10,000, consider pagination
```

**Check 2: Re-renders**
```javascript
// Add to components:
console.log('Component rendered');
// Should not render excessively
```

**Check 3: Memoization**
```javascript
// Wrap expensive components:
const MemoizedLogViewer = React.memo(LogViewer);
```

**Check 4: Virtualization**
```javascript
// For long log lists, consider react-virtual or react-window
// Not currently implemented
```

## File Modification Guide

### When to Edit Each File

**LandingPage.jsx**:
- Change upload UI
- Add/remove configuration options
- Modify validation rules
- Update API endpoint

**TransitionAnimation.jsx**:
- Change loading animation
- Add/remove phases
- Modify timing/duration
- Update visual effects

**Dashboard.jsx**:
- Add/remove agents
- Change layout
- Modify header content
- Update view mode logic

**AgentPanel.jsx**:
- Change panel UI
- Modify expand/collapse behavior
- Update status logic
- Add panel-level features

**LogViewer.jsx**:
- Change log rendering
- Modify scroll behavior
- Update conditional display
- Add log-level features

**ViewModeToggle.jsx**:
- Add/remove modes
- Change mode icons/labels
- Modify styling
- Update mode logic

**useSSEStream.js**:
- Change SSE connection logic
- Modify reconnection behavior
- Update error handling
- Add connection features

**logUtils.js**:
- Add agent routing
- Change status logic
- Update log formatting
- Add utility functions

**fieldExtractor.js**:
- Change field extraction
- Add formatters
- Modify priority logic
- Add extraction features

**api.js**:
- Update API endpoints
- Change base URL
- Add new endpoints
- Modify request logic

**logFieldSchema.js**:
- Add agent schemas
- Update event mappings
- Add display names
- Modify formatters

**index.css**:
- Change theme colors
- Add custom classes
- Modify animations
- Update scrollbar styles

## Testing Checklist

### Manual Testing

**Upload Flow**:
- [ ] File drag & drop works
- [ ] File click to browse works
- [ ] PDF-only validation works
- [ ] Slider changes pages
- [ ] Upload button enables/disables
- [ ] Error messages display correctly

**Transition**:
- [ ] Animation plays smoothly
- [ ] Progress bar animates
- [ ] Phases change correctly
- [ ] Automatically transitions to dashboard

**Dashboard**:
- [ ] Connection status shows correctly
- [ ] Session ID displays
- [ ] View mode toggle works
- [ ] All 5 agent panels appear
- [ ] Panels expand/collapse

**Log Display**:
- [ ] Messages appear in real-time
- [ ] Structured fields display correctly
- [ ] View modes switch properly
- [ ] Auto-scroll works
- [ ] Manual scroll disables auto-scroll
- [ ] No empty rows appear

**Styling**:
- [ ] Purple/pink theme consistent
- [ ] Gradient backgrounds animate
- [ ] Scrollbars styled
- [ ] Sliders styled
- [ ] Hover effects work
- [ ] Responsive to window resize

**Error Handling**:
- [ ] Connection errors display
- [ ] Reconnection attempts work
- [ ] Error logs show in red
- [ ] Error panels show error status

## Version History

**October 2025**: Current version
- React 19.1.1 implementation
- Three-screen flow complete
- View mode toggle with persistence
- Field extraction system complete
- Purple/pink theme fully implemented
- Optimized spacing and typography
- Custom scrollbars and sliders

---

**This document is maintained for AI assistants (Claude, Copilot, etc.) to quickly understand the entire frontend codebase and make accurate modifications.**
