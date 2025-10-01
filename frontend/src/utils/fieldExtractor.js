/**
 * Field Extraction Utilities
 * 
 * Extracts and formats log fields for display using the log field schema.
 */

import {
  HIDDEN_FIELDS,
  PRIORITY_FIELDS,
  getFieldDisplayName,
  formatFieldValue,
  shouldDisplayField,
  sortFieldsByPriority,
} from '../config/logFieldSchema.js';

/**
 * Extract all displayable fields from a log entry
 * 
 * @param {Object} log - Log entry with structure { text, record: { extra, level, time, message } }
 * @returns {Array<Object>} Array of field objects with format:
 *   {
 *     node: string,           // Node name (e.g., "extract_images")
 *     eventType: string|null, // Event type or null
 *     fieldName: string,      // Internal field name
 *     displayName: string,    // User-friendly field name
 *     value: string,          // Formatted value for display
 *     rawValue: any,          // Original value
 *   }
 */
export function extractFieldsFromLog(log) {
  const extra = log?.record?.extra || {};
  const node = extra.node || 'unknown';
  const eventType = extra.event_type || null;
  
  // Get all field names except hidden ones
  const fieldNames = Object.keys(extra).filter(shouldDisplayField);
  
  // Sort by priority
  const sortedFields = sortFieldsByPriority(fieldNames);
  
  // Map to field objects
  return sortedFields.map(fieldName => ({
    node,
    eventType,
    fieldName,
    displayName: getFieldDisplayName(fieldName),
    value: formatFieldValue(fieldName, extra[fieldName]),
    rawValue: extra[fieldName],
  }));
}

/**
 * Extract fields and format as display rows
 * Each row has the format: "node | event_type | field_name | value"
 * 
 * @param {Object} log - Log entry
 * @returns {Array<Object>} Array of display row objects:
 *   {
 *     node: string,
 *     eventType: string|null,
 *     fieldName: string,
 *     displayName: string,
 *     value: string,
 *     displayText: string,  // Full formatted row for display
 *   }
 */
export function extractDisplayRows(log) {
  const fields = extractFieldsFromLog(log);
  
  return fields.map(field => ({
    ...field,
    displayText: formatDisplayRow(field.node, field.eventType, field.displayName, field.value),
  }));
}

/**
 * Format a single display row
 * 
 * @param {string} node - Node name
 * @param {string|null} eventType - Event type or null
 * @param {string} fieldName - Field display name
 * @param {string} value - Formatted value
 * @returns {string} Formatted display text
 */
export function formatDisplayRow(node, eventType, fieldName, value) {
  const event = eventType || 'null';
  return `${node} | ${event} | ${fieldName} | ${value}`;
}

/**
 * Group fields by their importance for summary display
 * 
 * @param {Array<Object>} fields - Array of field objects from extractFieldsFromLog
 * @returns {Object} Grouped fields:
 *   {
 *     critical: Array,  // verdict, confidence, decision
 *     important: Array, // url, mission_id, page_number
 *     standard: Array,  // everything else
 *   }
 */
export function groupFieldsByImportance(fields) {
  const critical = [];
  const important = [];
  const standard = [];
  
  const criticalFields = ['verdict', 'confidence', 'decision', 'final_verdict', 'final_confidence'];
  const importantFields = ['url', 'priority', 'page_number', 'mission_id', 'event_type'];
  
  fields.forEach(field => {
    if (criticalFields.includes(field.fieldName)) {
      critical.push(field);
    } else if (importantFields.includes(field.fieldName)) {
      important.push(field);
    } else {
      standard.push(field);
    }
  });
  
  return { critical, important, standard };
}

/**
 * Extract key metrics from a log entry (for dashboard cards)
 * 
 * @param {Object} log - Log entry
 * @returns {Object|null} Metrics object or null if no relevant metrics:
 *   {
 *     type: string,      // 'verdict' | 'count' | 'progress' | 'status'
 *     label: string,     // Display label
 *     value: string,     // Primary value
 *     confidence?: string, // Optional confidence score
 *   }
 */
export function extractKeyMetrics(log) {
  const extra = log?.record?.extra || {};
  
  // Verdict + Confidence
  if (extra.verdict && extra.confidence !== undefined) {
    return {
      type: 'verdict',
      label: 'Verdict',
      value: extra.verdict,
      confidence: formatFieldValue('confidence', extra.confidence),
    };
  }
  
  // Decision (FileAnalysis triage)
  if (extra.decision) {
    return {
      type: 'status',
      label: 'Decision',
      value: extra.decision,
      detail: extra.mission_count !== undefined ? `${extra.mission_count} missions` : null,
    };
  }
  
  // Count metrics
  const countFields = [
    { key: 'image_count', label: 'Images Extracted' },
    { key: 'url_count', label: 'URLs Found' },
    { key: 'qr_count', label: 'QR Codes' },
    { key: 'findings_count', label: 'Findings' },
    { key: 'tactics_count', label: 'Tactics' },
    { key: 'total_missions', label: 'Total Missions' },
    { key: 'completed_missions', label: 'Completed' },
  ];
  
  for (const { key, label } of countFields) {
    if (extra[key] !== undefined) {
      return {
        type: 'count',
        label,
        value: String(extra[key]),
      };
    }
  }
  
  return null;
}

/**
 * Check if a log entry represents a significant event
 * (used for highlighting or special display)
 * 
 * @param {Object} log - Log entry
 * @returns {boolean} True if event is significant
 */
export function isSignificantEvent(log) {
  const eventType = log?.record?.extra?.event_type;
  const level = log?.record?.level?.name;
  
  const significantEvents = [
    'TRIAGE_COMPLETE',
    'VERDICT_DETERMINED',
    'ANALYSIS_COMPLETE',
    'INVESTIGATION_COMPLETE',
    'REPORT_GENERATION_COMPLETE',
    'HIGH_SIGNIFICANCE_FINDING',
    'DECEPTION_TACTICS_DETECTED',
  ];
  
  return (
    significantEvents.includes(eventType) ||
    level === 'WARNING' ||
    level === 'ERROR' ||
    level === 'CRITICAL'
  );
}

/**
 * Get a summary text for a log entry (for compact display)
 * 
 * @param {Object} log - Log entry
 * @returns {string} Summary text
 */
export function getLogSummary(log) {
  const message = log?.record?.message || '';
  const extra = log?.record?.extra || {};
  
  // For events with verdicts, show verdict prominently
  if (extra.verdict) {
    return `Verdict: ${extra.verdict}${extra.confidence ? ` (${formatFieldValue('confidence', extra.confidence)})` : ''}`;
  }
  
  // For events with decisions
  if (extra.decision) {
    return `Decision: ${extra.decision}`;
  }
  
  // For events with URLs
  if (extra.url) {
    const url = formatFieldValue('url', extra.url);
    return `URL: ${url}`;
  }
  
  // For events with page numbers
  if (extra.page_number !== undefined) {
    return `Page ${extra.page_number}: ${message.substring(0, 60)}...`;
  }
  
  // Default: use message
  return message.length > 80 ? message.substring(0, 80) + '...' : message;
}

/**
 * Extract timestamp from log entry
 * 
 * @param {Object} log - Log entry
 * @returns {Date|null} JavaScript Date object or null
 */
export function extractTimestamp(log) {
  const timestamp = log?.record?.time?.timestamp;
  if (!timestamp) return null;
  
  // Timestamp is in seconds (with decimals), convert to milliseconds
  return new Date(timestamp * 1000);
}

/**
 * Format timestamp for display
 * 
 * @param {Object} log - Log entry
 * @returns {string} Formatted time (e.g., "14:30:45")
 */
export function formatLogTimestamp(log) {
  const date = extractTimestamp(log);
  if (!date) return 'N/A';
  
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

/**
 * Get color class for log level
 * 
 * @param {Object} log - Log entry
 * @returns {string} Tailwind color class
 */
export function getLogLevelColor(log) {
  const level = log?.record?.level?.name;
  
  const colors = {
    DEBUG: 'text-gray-400',
    INFO: 'text-blue-400',
    SUCCESS: 'text-green-400',
    WARNING: 'text-yellow-400',
    ERROR: 'text-red-400',
    CRITICAL: 'text-red-600',
  };
  
  return colors[level] || 'text-gray-300';
}
