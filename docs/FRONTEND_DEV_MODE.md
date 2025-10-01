# Frontend Dev Mode Implementation

**Date:** October 2, 2025  
**Status:** ✅ Complete

## Overview

Dev Mode allows frontend developers to work on the UI without running the Python backend or waiting for LLM analysis. It uses mock data from a successful analysis session to simulate real-time SSE streaming.

## Architecture

### File Structure

```
frontend/
├── dev/
│   ├── README.md              # Usage instructions
│   └── mock-session.jsonl     # Real session logs
├── src/
│   ├── components/
│   │   ├── LandingPage.jsx    # Dev Mode toggle + button
│   │   └── Dashboard.jsx      # Dev mode detection + mock streaming
│   ├── hooks/
│   │   └── useSSEStream.js    # Disabled in dev mode
│   ├── utils/
│   │   └── mockDataLoader.js  # Load and stream mock data
│   └── App.jsx                # Dev mode routing + no persistence
```

### Data Flow

```
User toggles Dev Mode ON
  ↓
LandingPage shows "Start Dev Mode Analysis" button
  ↓
handleDevMode() creates fake session:
  - sessionId: 'dev-mode-mock-session'
  - devMode: true
  - streamUrl: null
  - filename: 'mock-analysis.pdf'
  ↓
App.jsx receives devMode flag
  - Does NOT persist to sessionStorage
  - Passes devMode=true to Dashboard
  ↓
Dashboard detects devMode:
  - useSSEStream disabled (enabled=false)
  - loadMockSession() from mockDataLoader
  - simulateStreaming() with 100ms delays
  ↓
Logs appear in real-time simulation
  ↓
"New Analysis" button clears session
```

## User Experience

### Landing Page

**Dev Mode OFF (default):**
- Standard upload interface
- "Start Analysis" button requires file upload

**Dev Mode ON:**
- Toggle shows purple glow
- Upload area still visible (but ignored)
- "Start Dev Mode Analysis" button (always enabled)
- No file upload required

### Dashboard

**Dev Mode Indicator:**
- Title shows "(Dev Mode)" suffix
- Status badge: "Dev Mode Active" (purple dot)
- Tip: "🔧 Dev Mode: Using mock data for frontend development"
- Session ID: "dev-mode-mock-session"

**Behavior:**
- Logs stream with 100ms delay between entries
- No SSE connection (backend not needed)
- "New Analysis" button returns to landing

## Implementation Details

### 1. Mock Data Loader (`mockDataLoader.js`)

```javascript
// Load JSONL file
export async function loadMockSession()

// Simulate streaming with delays
export async function simulateStreaming(logs, onLog, delayMs = 100)
```

### 2. Landing Page Toggle

```javascript
const [devMode, setDevMode] = useState(false);

// Toggle button with gear icon
<button onClick={() => setDevMode(!devMode)}>
  Dev Mode {devMode ? 'ON' : 'OFF'}
</button>

// Conditional button rendering
{devMode ? (
  <button onClick={handleDevMode}>Start Dev Mode Analysis</button>
) : (
  <button onClick={handleUpload}>Start Analysis</button>
)}
```

### 3. Dashboard Dev Mode

```javascript
export default function Dashboard({ devMode = false }) {
  // Disable SSE when in dev mode
  const { logs: sseLogs } = useSSEStream(sessionId, !devMode);
  const [mockLogs, setMockLogs] = useState([]);
  
  // Use appropriate log source
  const logs = devMode ? mockLogs : sseLogs;
  
  // Load mock data on mount if dev mode
  useEffect(() => {
    if (devMode) {
      loadMockSession().then(loadedLogs => {
        simulateStreaming(loadedLogs, (log) => {
          setMockLogs(prev => [...prev, log]);
        }, 100);
      });
    }
  }, [devMode]);
}
```

### 4. App.jsx Session Management

```javascript
// Don't persist dev mode sessions to sessionStorage
useEffect(() => {
  if (analysisData && !analysisData.devMode) {
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(analysisData));
  } else if (analysisData && analysisData.devMode) {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
  }
}, [analysisData]);
```

### 5. SSE Hook Conditional

```javascript
export function useSSEStream(sessionId, enabled = true) {
  // Skip connection if disabled (dev mode)
  const connect = useCallback(() => {
    if (!sessionId || !enabled) return;
    // ... connection logic
  }, [sessionId, enabled]);
}
```

## Updating Mock Data

After a successful analysis run:

```bash
cd frontend

# Copy session logs
cp ../output/{session_id}/logs/session.jsonl dev/mock-session.jsonl

# Format: {sha1}_{YYYYMMDD}_{HHMMSS}
# Example:
cp ../output/ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251002_000432/logs/session.jsonl \
   dev/mock-session.jsonl
```

**Requirements:**
- Must be a **successful** session (all agents completed)
- JSONL format (one JSON object per line)
- Contains logs from all 5 agents
- Real data structure (not fabricated)

## Benefits

1. **No Backend Required**: Frontend devs work independently
2. **Fast Iteration**: No LLM waiting time (~60-120s → instant)
3. **Consistent Data**: Same mock data every time
4. **Real Structure**: Uses actual log format and event types
5. **Full Features**: All dashboard features work (view modes, scrolling, etc.)
6. **Easy Testing**: Test UI changes without API calls

## Limitations

1. **Static Data**: Same logs every time (predictable)
2. **No Errors**: Mock data from successful run only
3. **No Variation**: Can't test different PDFs/scenarios
4. **Speed Fixed**: 100ms delay between logs (not configurable yet)

## Future Enhancements

1. **Multiple Mock Sessions**:
   - `dev/mock-session-success.jsonl`
   - `dev/mock-session-errors.jsonl`
   - `dev/mock-session-large.jsonl`
   - Selector dropdown on landing page

2. **Speed Control**:
   - Slider: Slow (500ms) / Normal (100ms) / Fast (10ms) / Instant (0ms)
   - Useful for testing different loading scenarios

3. **Pause/Resume**:
   - Pause streaming mid-analysis
   - Step through logs one-by-one
   - Jump to specific agent

4. **Error Injection**:
   - Simulate connection errors
   - Inject error logs
   - Test error handling UI

## Testing

**Manual Test:**
1. Start frontend: `npm run dev`
2. Toggle Dev Mode ON
3. Click "Start Dev Mode Analysis"
4. Verify:
   - Dashboard shows "(Dev Mode)"
   - Logs stream with delays
   - Status shows "Dev Mode Active"
   - All agent panels populate
   - "New Analysis" returns to landing
5. Refresh page: Session clears (no persistence)

**No Backend Test:**
1. Kill backend (Ctrl+C)
2. Enable Dev Mode
3. Start analysis
4. Should work perfectly without backend

## Documentation

- **frontend/dev/README.md** - Usage guide for devs
- **frontend/QUICKSTART.md** - Updated with Dev Mode section
- **This file** - Implementation deep dive

---

**Status:** ✅ Fully implemented and tested  
**Last Updated:** October 2, 2025
