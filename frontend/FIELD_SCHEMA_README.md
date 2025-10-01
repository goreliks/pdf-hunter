# Log Field Schema System

**Complete field mapping and extraction system for PDF Hunter frontend.**

## Overview

This system provides **100% accurate field mappings** for all agents and events, combining:
- **Production Logs**: Actual field observations from session runs
- **Reference Documentation**: Complete event coverage from `docs/LOGGING_FIELD_REFERENCE.md`

**Coverage:**
- ✅ 5 Agents (PdfExtraction, FileAnalysis, ImageAnalysis, URLInvestigation, ReportGenerator)
- ✅ 29 Nodes across all agents
- ✅ ~65 Unique events
- ✅ 65 Field display name mappings

**Last Updated:** October 1, 2025 (Enriched with reference docs)

## System Components

- **Schema Definition** (`logFieldSchema.js`): Complete field mappings for all agents
- **Field Utilities** (`fieldExtractor.js`): Extraction, formatting, and display helpers
- **Type Safety**: Consistent field handling across components
- **Usage Examples**: Real-world examples with actual log structures

## Files

```
frontend/src/
├── config/
│   └── logFieldSchema.js         # Master schema + metadata
├── utils/
│   └── fieldExtractor.js         # Extraction utilities
└── examples/
    └── fieldExtractionExamples.js # Usage examples + React components
```

## Quick Start

### 1. Extract Fields from a Log

```javascript
import { extractFieldsFromLog } from './utils/fieldExtractor';

const log = {
  record: {
    extra: {
      agent: 'ImageAnalysis',
      node: 'analyze_images',
      event_type: 'PAGE_ANALYSIS_COMPLETE',
      page_number: 0,
      verdict: 'Highly Deceptive',
      confidence: 0.95,
      findings_count: 4,
    }
  }
};

const fields = extractFieldsFromLog(log);
// Returns:
// [
//   { fieldName: 'event_type', displayName: 'Event', value: 'PAGE_ANALYSIS_COMPLETE', ... },
//   { fieldName: 'verdict', displayName: 'Verdict', value: 'Highly Deceptive', ... },
//   { fieldName: 'confidence', displayName: 'Confidence', value: '95.0%', ... },
//   { fieldName: 'page_number', displayName: 'Page', value: '0', ... },
//   { fieldName: 'findings_count', displayName: 'Findings', value: '4', ... },
// ]
```

### 2. Format as Display Rows

```javascript
import { extractDisplayRows } from './utils/fieldExtractor';

const rows = extractDisplayRows(log);
// Each row has format: "node | event_type | field_name | value"
// Example:
// "analyze_images | PAGE_ANALYSIS_COMPLETE | Verdict | Highly Deceptive"
// "analyze_images | PAGE_ANALYSIS_COMPLETE | Confidence | 95.0%"
// "analyze_images | PAGE_ANALYSIS_COMPLETE | Page | 0"
```

### 3. Extract Key Metrics (for Dashboard Cards)

```javascript
import { extractKeyMetrics } from './utils/fieldExtractor';

const metrics = extractKeyMetrics(log);
// Returns: { type: 'verdict', label: 'Verdict', value: 'Highly Deceptive', confidence: '95.0%' }
```

### 4. Check Event Significance

```javascript
import { isSignificantEvent } from './utils/fieldExtractor';

if (isSignificantEvent(log)) {
  // Highlight this log entry
}
```

## Schema Structure

### Agents

- `FileAnalysis` - Static file analysis and threat triage
- `ImageAnalysis` - Visual deception analysis
- `URLInvestigation` - URL and QR code investigation
- `ReportGenerator` - Final report synthesis

### Field Categories

**Hidden Fields** (never displayed):
- `agent` - Already shown in section header
- `node` - Already shown in display row
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
- `detailed_findings`, `deception_tactics`, `benign_signals`
- `prioritized_urls`, `images_data`, `url_list`, `qr_list`
- `log_messages`, `detected_threats`, `full_report`

**Percentage Fields** (0.0-1.0 → 0%-100%):
- `confidence`, `final_confidence`

## API Reference

### Schema Functions

```javascript
import {
  getExpectedFields,
  shouldDisplayField,
  getFieldDisplayName,
  formatFieldValue,
  sortFieldsByPriority,
} from './config/logFieldSchema';

// Get expected fields for a specific agent/node/event
const fields = getExpectedFields('ImageAnalysis', 'analyze_images', 'PAGE_ANALYSIS_COMPLETE');
// Returns: ['agent', 'benign_signals', 'confidence', 'verdict', ...]

// Check if field should be displayed
shouldDisplayField('event_type'); // true
shouldDisplayField('session_id'); // false

// Get display name
getFieldDisplayName('findings_count'); // "Findings"
getFieldDisplayName('page_number');    // "Page"

// Format value
formatFieldValue('confidence', 0.95);  // "95.0%"
formatFieldValue('url', 'https://...');  // Truncated if > 60 chars

// Sort fields by priority
sortFieldsByPriority(['page_number', 'verdict', 'node']);
// Returns: ['verdict', 'page_number', 'node']
```

### Extraction Functions

```javascript
import {
  extractFieldsFromLog,
  extractDisplayRows,
  groupFieldsByImportance,
  extractKeyMetrics,
  isSignificantEvent,
  getLogSummary,
  formatLogTimestamp,
  getLogLevelColor,
} from './utils/fieldExtractor';

// Extract all displayable fields
const fields = extractFieldsFromLog(log);

// Extract as formatted display rows
const rows = extractDisplayRows(log);

// Group by importance
const { critical, important, standard } = groupFieldsByImportance(fields);

// Extract metrics for cards
const metrics = extractKeyMetrics(log);

// Check significance
const isImportant = isSignificantEvent(log);

// Get compact summary
const summary = getLogSummary(log);

// Format timestamp
const time = formatLogTimestamp(log); // "14:30:45"

// Get level color
const color = getLogLevelColor(log); // "text-blue-400"
```

## React Component Examples

### Display All Fields

```jsx
import { extractFieldsFromLog } from './utils/fieldExtractor';

function LogFieldDisplay({ log }) {
  const fields = extractFieldsFromLog(log);
  
  return (
    <div className="space-y-1">
      {fields.map((field, idx) => (
        <div key={idx} className="flex gap-2 font-mono text-sm">
          <span className="text-purple-400">{field.node}</span>
          <span>|</span>
          <span className="text-blue-400">{field.eventType || 'null'}</span>
          <span>|</span>
          <span className="text-gray-300">{field.displayName}</span>
          <span>|</span>
          <span className="text-green-400">{field.value}</span>
        </div>
      ))}
    </div>
  );
}
```

### Metrics Card

```jsx
import { extractKeyMetrics } from './utils/fieldExtractor';

function MetricsCard({ log }) {
  const metrics = extractKeyMetrics(log);
  
  if (!metrics) return null;
  
  return (
    <div className="bg-gray-800 rounded p-4">
      <div className="text-sm text-gray-400">{metrics.label}</div>
      <div className="text-2xl font-bold">{metrics.value}</div>
      {metrics.confidence && (
        <div className="text-sm text-gray-400">
          Confidence: {metrics.confidence}
        </div>
      )}
    </div>
  );
}
```

### Significant Event Highlighting

```jsx
import { isSignificantEvent, getLogLevelColor } from './utils/fieldExtractor';

function LogEntry({ log }) {
  const isSignificant = isSignificantEvent(log);
  const levelColor = getLogLevelColor(log);
  
  return (
    <div className={`
      p-2 rounded
      ${isSignificant ? 'border-l-4 border-yellow-400 bg-gray-800' : ''}
    `}>
      <span className={levelColor}>
        {log.record.message}
      </span>
    </div>
  );
}
```

## Field Formatters

The system includes built-in formatters for common field types:

| Field Type | Format |
|------------|--------|
| Percentages | `0.95` → `"95.0%"` |
| URLs | Truncate to 60 chars + "..." |
| File paths | Show basename only |
| Arrays | Show count (e.g., "3 items") |
| Long text | Truncate to 100 chars + "..." |
| Booleans | `true` → "Yes", `false` → "No" |

## Adding New Agents/Events

When new agents or events are added:

1. **Extract actual log structure** using:
   ```bash
   jq -r 'select(.record.extra.agent == "NewAgent") | "\(.record.extra.node)|\(.record.extra.event_type // "null")|\(.record.extra | keys | join(","))"' session.jsonl | sort | uniq
   ```

2. **Update `logFieldSchema.js`**:
   ```javascript
   export const NEW_AGENT_SCHEMA = {
     node_name: {
       EVENT_TYPE: ['agent', 'node', 'session_id', 'new_field1', 'new_field2'],
     },
   };
   
   export const LOG_FIELD_SCHEMA = {
     // ... existing agents
     NewAgent: NEW_AGENT_SCHEMA,
   };
   ```

3. **Add field display names** (if needed):
   ```javascript
   export const FIELD_DISPLAY_NAMES = {
     // ... existing names
     new_field1: 'Field 1',
     new_field2: 'Field 2',
   };
   ```

4. **Add formatters** (if needed):
   ```javascript
   export const FIELD_FORMATTERS = {
     // ... existing formatters
     new_field1: (val) => /* custom formatting */,
   };
   ```

## Maintenance

**Schema is frozen** - This schema was generated from production logs and should remain stable. Only update when:
- New agents are added to the system
- New event types are introduced
- Field names change in the backend

**Validation**: Run the examples file to verify schema accuracy:
```bash
cd frontend
npm run test:schema  # (if test script is configured)
# Or run directly:
node src/examples/fieldExtractionExamples.js
```

## Integration with Dashboard

```jsx
import { extractDisplayRows, formatLogTimestamp } from './utils/fieldExtractor';

function AgentSection({ logs }) {
  return (
    <div className="agent-section">
      {logs.map((log, idx) => {
        const rows = extractDisplayRows(log);
        const timestamp = formatLogTimestamp(log);
        
        return (
          <div key={idx} className="log-entry">
            <div className="timestamp">[{timestamp}]</div>
            {rows.map((row, rowIdx) => (
              <div key={rowIdx} className="field-row">
                {row.displayText}
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}
```

## Performance Considerations

- **Field extraction** is O(n) where n = number of fields in log.extra
- **Sorting** is O(n log n) but n is typically < 20
- **Formatting** functions are cached for complex objects
- All utilities are **pure functions** - safe for React re-renders

## Testing

See `examples/fieldExtractionExamples.js` for comprehensive test cases with real log structures.

---

**Generated**: 2025-10-01  
**Source**: session `ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251001_133453`  
**Version**: 1.0.0
