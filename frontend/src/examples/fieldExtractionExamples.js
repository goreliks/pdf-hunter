/**
 * Field Extraction Usage Examples
 * 
 * This file demonstrates how to use the field extraction utilities
 * with real log data structures.
 */

import {
  extractFieldsFromLog,
  extractDisplayRows,
  groupFieldsByImportance,
  extractKeyMetrics,
  isSignificantEvent,
  getLogSummary,
  formatLogTimestamp,
  getLogLevelColor,
} from '../utils/fieldExtractor.js';

// Example 1: FileAnalysis TRIAGE_COMPLETE log
const triageLog = {
  text: "✅ Triage Decision: PDF is INNOCENT - No threats detected\n",
  record: {
    level: { name: "INFO", no: 20, icon: "ℹ️" },
    time: { timestamp: 1759314896.798494 },
    message: "✅ Triage Decision: PDF is INNOCENT - No threats detected",
    extra: {
      agent: "FileAnalysis",
      node: "identify_suspicious_elements",
      session_id: "ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251001_133453",
      event_type: "TRIAGE_COMPLETE",
      decision: "innocent",
      mission_count: 0,
      reasoning: "The anatomical report shows a complete absence of high-risk indicators..."
    }
  }
};

// Example 2: ImageAnalysis PAGE_ANALYSIS_COMPLETE log
const imageAnalysisLog = {
  text: "📊 Page 0 Analysis Complete | Verdict: Highly Deceptive | Confidence: 95.0%\n",
  record: {
    level: { name: "INFO", no: 20, icon: "ℹ️" },
    time: { timestamp: 1759314913.691321 },
    message: "📊 Page 0 Analysis Complete | Verdict: Highly Deceptive | Confidence: 95.0%",
    extra: {
      agent: "ImageAnalysis",
      node: "analyze_images",
      session_id: "ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251001_133453",
      event_type: "PAGE_ANALYSIS_COMPLETE",
      page_number: 0,
      verdict: "Highly Deceptive",
      confidence: 0.95,
      findings_count: 4,
      tactics_count: 3,
      benign_signals_count: 1,
      urls_prioritized: 2,
      summary: "This page exhibits multiple high-risk deception tactics..."
    }
  }
};

// Example 3: URLInvestigation INVESTIGATION_START log
const urlLog = {
  text: "🔍 Starting URL investigation: https://protect.checkpoint.com/...\n",
  record: {
    level: { name: "INFO", no: 20, icon: "ℹ️" },
    time: { timestamp: 1759314913.717791 },
    message: "🔍 Starting URL investigation",
    extra: {
      agent: "URLInvestigation",
      node: "investigate_url",
      session_id: "ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251001_133453",
      event_type: "INVESTIGATION_START",
      url: "https://protect.checkpoint.com/v2/r02/___https://www.qrcode-monkey.com/___.YzJlOmNwYWxsOmM6bzpmNmMzYzQ3M2UxYWQwN2IwOTE1NGQ0OGUyOTMxNjBjZTo3OmE5Mjg6MGVlYWM1N2Q5MTdmYWYzZTk5MDQ2NTA0MTJmOWMxMDgwZWM5ZTJiZDliZjNmNmZmOTRkZmNiNjhkZTU2NzY4MDpwOlQ6Tg",
      priority: 1
    }
  }
};

// Example 4: ReportGenerator VERDICT_DETERMINED log
const verdictLog = {
  text: "⚖️ Final Verdict Determined\n",
  record: {
    level: { name: "SUCCESS", no: 25, icon: "✅" },
    time: { timestamp: 1759315000.123456 },
    message: "⚖️ Final Verdict Determined",
    extra: {
      agent: "ReportGenerator",
      node: "determine_threat_verdict",
      session_id: "ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251001_133453",
      event_type: "VERDICT_DETERMINED",
      verdict: "Malicious",
      confidence: 0.92,
      reasoning: "Multiple high-confidence indicators of phishing activity detected..."
    }
  }
};

// =============================================================================
// USAGE EXAMPLES
// =============================================================================

console.log('=== Example 1: Extract Fields ===\n');
const fields1 = extractFieldsFromLog(triageLog);
fields1.forEach(field => {
  console.log(`${field.displayName}: ${field.value}`);
});

console.log('\n=== Example 2: Extract Display Rows ===\n');
const rows2 = extractDisplayRows(imageAnalysisLog);
rows2.forEach(row => {
  console.log(row.displayText);
});

console.log('\n=== Example 3: Group by Importance ===\n');
const fields3 = extractFieldsFromLog(imageAnalysisLog);
const grouped3 = groupFieldsByImportance(fields3);
console.log('Critical:', grouped3.critical.map(f => f.displayName));
console.log('Important:', grouped3.important.map(f => f.displayName));
console.log('Standard:', grouped3.standard.map(f => f.displayName));

console.log('\n=== Example 4: Extract Key Metrics ===\n');
const metrics1 = extractKeyMetrics(triageLog);
console.log('Triage metrics:', metrics1);

const metrics2 = extractKeyMetrics(imageAnalysisLog);
console.log('Image analysis metrics:', metrics2);

const metrics4 = extractKeyMetrics(verdictLog);
console.log('Final verdict metrics:', metrics4);

console.log('\n=== Example 5: Check Significant Events ===\n');
console.log('Triage is significant?', isSignificantEvent(triageLog));
console.log('Image analysis is significant?', isSignificantEvent(imageAnalysisLog));
console.log('URL investigation is significant?', isSignificantEvent(urlLog));
console.log('Verdict is significant?', isSignificantEvent(verdictLog));

console.log('\n=== Example 6: Get Summaries ===\n');
console.log('Triage summary:', getLogSummary(triageLog));
console.log('Image analysis summary:', getLogSummary(imageAnalysisLog));
console.log('URL investigation summary:', getLogSummary(urlLog));
console.log('Verdict summary:', getLogSummary(verdictLog));

console.log('\n=== Example 7: Format Timestamps ===\n');
console.log('Triage time:', formatLogTimestamp(triageLog));
console.log('Image analysis time:', formatLogTimestamp(imageAnalysisLog));
console.log('URL investigation time:', formatLogTimestamp(urlLog));
console.log('Verdict time:', formatLogTimestamp(verdictLog));

console.log('\n=== Example 8: Get Log Level Colors ===\n');
console.log('Triage color:', getLogLevelColor(triageLog));
console.log('Image analysis color:', getLogLevelColor(imageAnalysisLog));
console.log('Verdict color:', getLogLevelColor(verdictLog));

// =============================================================================
// REACT COMPONENT USAGE EXAMPLE (JSX - Copy to React components)
// =============================================================================

/*
Example React component showing how to display extracted fields:

export function LogEntryDisplay({ log }) {
  const fields = extractFieldsFromLog(log);
  const timestamp = formatLogTimestamp(log);
  const levelColor = getLogLevelColor(log);
  const isSignificant = isSignificantEvent(log);
  
  return (
    <div className={`log-entry ${isSignificant ? 'border-l-4 border-yellow-400' : ''}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-gray-500">[{timestamp}]</span>
        <span className={levelColor}>{log.record.level.name}</span>
      </div>
      
      <div className="mb-2">{log.record.message}</div>
      
      <div className="space-y-1">
        {fields.map((field, idx) => (
          <div key={idx} className="flex gap-2 text-sm font-mono">
            <span className="text-purple-400">{field.node}</span>
            <span className="text-gray-500">|</span>
            <span className="text-blue-400">{field.eventType || 'null'}</span>
            <span className="text-gray-500">|</span>
            <span className="text-gray-300">{field.displayName}</span>
            <span className="text-gray-500">|</span>
            <span className="text-green-400">{field.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

Example React component for a metrics card:

export function MetricsCard({ log }) {
  const metrics = extractKeyMetrics(log);
  
  if (!metrics) return null;
  
  return (
    <div className="bg-gray-800 rounded p-4">
      <div className="text-sm text-gray-400 mb-1">{metrics.label}</div>
      <div className="text-2xl font-bold">{metrics.value}</div>
      {metrics.confidence && (
        <div className="text-sm text-gray-400 mt-1">
          Confidence: {metrics.confidence}
        </div>
      )}
      {metrics.detail && (
        <div className="text-sm text-gray-400 mt-1">{metrics.detail}</div>
      )}
    </div>
  );
}
*/
