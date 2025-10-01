/**
 * PDF Hunter Log Field Schema
 * 
 * ENRICHED VERSION - 2025-10-01
 * 
 * Sources:
 * - Production logs: session ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251001_133453
 * - Reference docs: docs/LOGGING_FIELD_REFERENCE.md
 * 
 * This schema defines all possible fields for each agent's node and event_type.
 * Includes both observed fields (from logs) and documented fields (from reference).
 * 
 * Use this for:
 * - Field extraction and display
 * - Field ordering/priority
 * - Type information
 * - Filtering decisions
 */

// =============================================================================
// AGENT: PdfExtraction
// =============================================================================
export const PDF_EXTRACTION_SCHEMA = {
  setup_session: {
    null: ['agent', 'node', 'session_id'],
    SESSION_CREATED: ['agent', 'event_type', 'node', 'output_directory', 'session_id'],
  },
  
  extract_pdf_images: {
    null: ['agent', 'node', 'session_id'],
    IMAGE_EXTRACTION_START: ['agent', 'event_type', 'file_path', 'node', 'session_id'],
    IMAGE_EXTRACTION_COMPLETE: ['agent', 'event_type', 'image_count', 'node', 'output_directory', 'session_id'],
  },
  
  find_embedded_urls: {
    null: ['agent', 'node', 'session_id'],
    URL_SEARCH_START: ['agent', 'event_type', 'file_path', 'node', 'session_id'],
    URL_SEARCH_COMPLETE: ['agent', 'event_type', 'node', 'session_id', 'url_count'],
  },
  
  scan_qr_codes: {
    null: ['agent', 'node', 'session_id'],
    QR_SCAN_START: ['agent', 'event_type', 'node', 'session_id', 'total_images'],
    QR_SCAN_COMPLETE: ['agent', 'event_type', 'node', 'qr_count', 'session_id', 'urls_decoded'],
  },
};

// =============================================================================
// AGENT: FileAnalysis
// =============================================================================
// =============================================================================
// AGENT: FileAnalysis
// =============================================================================
export const FILE_ANALYSIS_SCHEMA = {
  identify_suspicious_elements: {
    null: ['agent', 'node', 'session_id'],
    TRIAGE_START: ['agent', 'event_type', 'file_path', 'node', 'session_id'],
    TRIAGE_COMPLETE: ['agent', 'decision', 'event_type', 'mission_count', 'node', 'reasoning', 'session_id'],
  },
  
  create_analysis_tasks: {
    null: ['agent', 'node', 'session_id'],
    TASKS_CREATED: ['agent', 'event_type', 'node', 'session_id', 'task_count'],
  },
  
  assign_analysis_tasks: {
    null: ['agent', 'node', 'session_id'],
    MISSION_ASSIGNED: ['agent', 'event_type', 'mission_description', 'mission_id', 'node', 'session_id'],
    NO_PENDING_MISSIONS: ['agent', 'completed_missions', 'event_type', 'node', 'session_id', 'total_missions'],
  },
  
  run_investigation: {
    null: ['agent', 'node', 'session_id'],
    INVESTIGATION_START: ['agent', 'event_type', 'mission_id', 'node', 'session_id'],
    INVESTIGATION_COMPLETE: ['agent', 'event_type', 'mission_id', 'mission_status', 'node', 'session_id'],
    INVESTIGATION_BLOCKED: ['agent', 'event_type', 'mission_id', 'node', 'reason', 'session_id'],
  },
  
  review_analysis_results: {
    null: [
      ['agent', 'node', 'session_id'],
      ['agent', 'context_size', 'graph_size', 'node', 'reports_size', 'session_id', 'transcripts_size'],
    ],
    REVIEW_START: ['agent', 'blocked_missions', 'completed_missions', 'event_type', 'failed_missions', 'node', 'session_id'],
    STRATEGIC_REVIEW_START: ['agent', 'event_type', 'node', 'session_id'],
    STRATEGIC_REVIEW_COMPLETE: ['agent', 'event_type', 'is_complete', 'new_missions_count', 'node', 'session_id'],
    PROCESSING_COMPLETE: ['agent', 'blocked_missions', 'event_type', 'failed_missions', 'graph_size', 'node', 'reports_size', 'session_id', 'transcripts_size'],
    INVESTIGATION_COMPLETE: ['agent', 'event_type', 'node', 'session_id', 'total_missions', 'total_reports'],
  },
  
  merge_findings: {
    null: ['agent', 'node', 'session_id'],
    MERGE_COMPLETE: ['agent', 'event_type', 'node', 'session_id', 'total_findings'],
  },
  
  compile_file_analysis: {
    null: ['agent', 'node', 'session_id'],
    ANALYSIS_COMPLETE: ['agent', 'event_type', 'node', 'output_file', 'session_id'],
  },
  
  // Note: summarize_file_analysis appears in logs but not in reference docs
  // Including it here as it's actively used in production
  summarize_file_analysis: {
    null: ['agent', 'node', 'session_id'],
    SUMMARY_START: ['agent', 'event_type', 'node', 'session_id', 'total_evidence_nodes', 'total_reports'],
    VERDICT_GENERATED: ['agent', 'attack_chain_steps', 'event_type', 'ioc_count', 'node', 'session_id', 'verdict'],
    EXECUTIVE_SUMMARY: ['agent', 'event_type', 'node', 'session_id', 'summary'],
    ANALYSIS_COMPLETE: ['agent', 'event_type', 'node', 'output_file', 'session_id'],
  },
};

// =============================================================================
// AGENT: ImageAnalysis
// =============================================================================
export const IMAGE_ANALYSIS_SCHEMA = {
  analyze_images: {
    null: [
      ['agent', 'node', 'session_id', 'total_images', 'total_urls'],
      ['agent', 'element_count', 'node', 'page_number', 'session_id'],
    ],
    AGENT_START: ['agent', 'event_type', 'node', 'pages_to_analyze', 'session_id'],
    PAGE_ANALYSIS_START: ['agent', 'event_type', 'node', 'page_number', 'session_id'],
    PAGE_ANALYSIS_COMPLETE: [
      'agent', 'benign_signals', 'benign_signals_count', 'confidence', 'deception_tactics', 
      'detailed_findings', 'event_type', 'findings_count', 'node', 'page_description', 
      'page_number', 'session_id', 'summary', 'tactics_count', 'urls_prioritized', 'verdict'
    ],
    HIGH_SIGNIFICANCE_FINDING: [
      'agent', 'assessment', 'element_type', 'event_type', 'node', 'page_number', 
      'session_id', 'significance', 'technical_data', 'visual_description'
    ],
    DECEPTION_TACTICS_DETECTED: [
      'agent', 'deception_tactics', 'event_type', 'node', 'page_number', 'session_id', 'tactics_count'
    ],
    BENIGN_SIGNALS_DETECTED: [
      'agent', 'benign_signals', 'event_type', 'node', 'page_number', 'session_id', 'signals_count'
    ],
    URLS_PRIORITIZED: [
      'agent', 'event_type', 'node', 'page_number', 'prioritized_urls', 'session_id', 'url_count'
    ],
    ANALYSIS_COMPLETE: ['agent', 'event_type', 'node', 'pages_analyzed', 'session_id'],
  },
  
  compile_findings: {
    COMPILATION_START: ['agent', 'event_type', 'node', 'page_count', 'session_id'],
    VERDICT_DETERMINED: [
      'agent', 'all_benign_signals', 'all_deception_tactics', 'all_detailed_findings', 
      'all_priority_urls', 'confidence', 'document_flow_summary', 'event_type', 
      'executive_summary', 'findings_count', 'node', 'priority_urls_count', 
      'session_id', 'signals_count', 'tactics_count', 'verdict'
    ],
    REPORT_SAVED: ['agent', 'event_type', 'node', 'report_path', 'session_id'],
    COMPILATION_COMPLETE: [
      'agent', 'event_type', 'final_confidence', 'final_verdict', 'node', 'priority_urls_count', 'session_id'
    ],
  },
};

// =============================================================================
// AGENT: URLInvestigation
// =============================================================================
export const URL_INVESTIGATION_SCHEMA = {
  // Reference docs use 'filter_urls', production uses 'filter_high_priority_urls'
  // Including both for compatibility
  filter_urls: {
    null: ['agent', 'node', 'session_id'],
    FILTER_START: ['agent', 'event_type', 'node', 'session_id', 'total_urls'],
    FILTER_COMPLETE: ['agent', 'event_type', 'node', 'session_id', 'urls_skipped', 'urls_to_investigate'],
  },
  
  filter_high_priority_urls: {
    null: ['agent', 'node', 'session_id'],
    FILTER_START: ['agent', 'event_type', 'node', 'session_id'],
    FILTER_COMPLETE: [
      'agent', 'event_type', 'high_priority_count', 'low_priority_count', 'node', 'session_id', 'total_urls'
    ],
  },
  
  setup_url_investigation: {
    null: ['agent', 'node', 'session_id'],
    SETUP_COMPLETE: ['agent', 'event_type', 'mission_directory', 'node', 'session_id'],
  },
  
  route_url_analysis: {
    null: ['agent', 'node', 'session_id'],
    PARALLEL_DISPATCH: ['agent', 'event_type', 'node', 'session_id', 'url_count'],
  },
  
  conduct_link_analysis_wrapper: {
    null: ['agent', 'node', 'session_id'],
    WRAPPER_START: ['agent', 'event_type', 'node', 'session_id', 'url'],
    WRAPPER_COMPLETE: ['agent', 'event_type', 'node', 'session_id', 'url'],
  },
  
  investigate_url: {
    null: ['agent', 'node', 'session_id'],
    CHAIN_START: ['agent', 'event_type', 'node', 'session_id'],
    INVESTIGATION_START: ['agent', 'event_type', 'node', 'priority', 'session_id', 'url'],
    TOOL_EXECUTION_COMPLETE: ['agent', 'event_type', 'node', 'session_id', 'tool_count', 'url'],
    ANALYSIS_COMPLETE: ['agent', 'confidence', 'event_type', 'mission_status', 'node', 'session_id', 'url', 'verdict'],
  },
  
  execute_browser_tools: {
    null: ['agent', 'node', 'session_id'],
    TOOL_EXECUTION_START: ['agent', 'event_type', 'node', 'session_id', 'tool_count', 'url'],
    TOOL_CALL: ['agent', 'event_type', 'node', 'session_id', 'tool_name'],
    TOOL_SUCCESS: ['agent', 'event_type', 'node', 'session_id', 'tool_name'],
    STRATEGIC_THINKING: ['agent', 'event_type', 'node', 'session_id', 'tool_name'],
    TOOL_EXECUTION_COMPLETE: ['agent', 'event_type', 'node', 'session_id', 'tool_count'],
  },
  
  analyze_url_content: {
    null: ['agent', 'node', 'session_id'],
    ANALYSIS_START: ['agent', 'event_type', 'log_messages', 'node', 'session_id', 'url'],
    ANALYSIS_COMPLETE: [
      'agent', 'confidence', 'detected_threats', 'event_type', 'final_url', 
      'mission_status', 'node', 'screenshot_count', 'session_id', 'summary', 'url', 'verdict'
    ],
  },
  
  compile_url_findings: {
    null: ['agent', 'node', 'session_id'],
    COMPILATION_START: ['agent', 'event_type', 'investigation_count', 'node', 'session_id'],
    COMPILATION_COMPLETE: ['agent', 'confidence', 'event_type', 'node', 'session_id', 'verdict'],
  },
  
  save_results: {
    null: ['agent', 'node', 'session_id'],
    SAVE_COMPLETE: ['agent', 'event_type', 'investigation_count', 'node', 'output_file', 'session_id'],
  },
};

// =============================================================================
// AGENT: ReportGenerator
// =============================================================================
export const REPORT_GENERATOR_SCHEMA = {
  determine_threat_verdict: {
    null: ['agent', 'node', 'session_id'],
    VERDICT_DETERMINATION_START: ['agent', 'event_type', 'node', 'session_id'],
    VERDICT_DETERMINED: ['agent', 'confidence', 'event_type', 'node', 'reasoning', 'session_id', 'verdict'],
  },
  
  generate_final_report: {
    null: ['agent', 'node', 'session_id'],
    REPORT_GENERATION_START: ['agent', 'event_type', 'node', 'session_id'],
    REPORT_GENERATION_COMPLETE: [
      'agent', 'event_type', 'full_report', 'node', 'report_length', 'report_preview', 'session_id'
    ],
  },
  
  save_analysis_results: {
    null: ['agent', 'node', 'session_id'],
    SAVE_START: ['agent', 'event_type', 'node', 'session_id'],
    REPORT_SAVED: ['agent', 'event_type', 'file_path', 'node', 'session_id'],
    STATE_SAVED: ['agent', 'event_type', 'file_path', 'node', 'session_id'],
    ANALYSIS_COMPLETE: [
      'agent', 'event_type', 'final_confidence', 'final_verdict', 'node', 'report_path', 'session_id', 'state_path'
    ],
  },
};

// =============================================================================
// MASTER SCHEMA (All Agents)
// =============================================================================
export const LOG_FIELD_SCHEMA = {
  PdfExtraction: PDF_EXTRACTION_SCHEMA,
  FileAnalysis: FILE_ANALYSIS_SCHEMA,
  ImageAnalysis: IMAGE_ANALYSIS_SCHEMA,
  URLInvestigation: URL_INVESTIGATION_SCHEMA,
  ReportGenerator: REPORT_GENERATOR_SCHEMA,
};

// =============================================================================
// FIELD METADATA
// =============================================================================

/**
 * Fields that should NEVER be displayed to users
 * (internal use only or already shown in UI)
 */
export const HIDDEN_FIELDS = [
  'agent',      // Already shown as section header
  'node',       // Already shown in row format
  'session_id', // Not relevant to user during active monitoring
];

/**
 * High-priority fields that should be displayed first
 * Order matters - earlier = higher priority
 */
export const PRIORITY_FIELDS = [
  'event_type',
  'verdict',
  'confidence',
  'decision',
  'url',
  'priority',
  'page_number',
  'mission_id',
  'mission_status',
  'reasoning',
  'summary',
  'file_path',
  'image_count',
  'url_count',
  'qr_count',
];

/**
 * Fields that contain large objects/arrays (display count instead of content)
 */
export const COMPLEX_FIELDS = [
  'detailed_findings',
  'deception_tactics',
  'benign_signals',
  'prioritized_urls',
  'all_detailed_findings',
  'all_deception_tactics',
  'all_benign_signals',
  'all_priority_urls',
  'images_data',
  'url_list',
  'qr_list',
  'log_messages',
  'detected_threats',
  'full_report',
];

/**
 * Fields that are percentages (0.0 - 1.0 should be displayed as 0% - 100%)
 */
export const PERCENTAGE_FIELDS = [
  'confidence',
  'final_confidence',
];

/**
 * Field display names (for better UX)
 * Maps internal field names to user-friendly labels
 */
export const FIELD_DISPLAY_NAMES = {
  // Common fields
  event_type: 'Event',
  file_path: 'File Path',
  output_directory: 'Output Directory',
  mission_count: 'Missions',
  task_count: 'Tasks',
  
  // PdfExtraction fields
  image_count: 'Images',
  url_count: 'URLs Found',
  qr_count: 'QR Codes',
  urls_decoded: 'URLs from QR',
  total_images: 'Total Images',
  
  // FileAnalysis fields
  decision: 'Decision',
  reasoning: 'Reasoning',
  mission_id: 'Mission ID',
  mission_description: 'Description',
  mission_status: 'Status',
  completed_missions: 'Completed',
  total_missions: 'Total Missions',
  new_investigations: 'New Investigations',
  total_reports: 'Reports',
  blocked_missions: 'Blocked',
  failed_missions: 'Failed',
  successful_reports: 'Successful',
  is_complete: 'Complete',
  new_missions_count: 'New Missions',
  total_evidence_nodes: 'Evidence Nodes',
  attack_chain_steps: 'Attack Steps',
  ioc_count: 'IOCs',
  output_file: 'Output File',
  total_findings: 'Total Findings',
  context_size: 'Context Size',
  graph_size: 'Graph Size',
  reports_size: 'Reports Size',
  transcripts_size: 'Transcripts Size',
  
  // ImageAnalysis fields
  pages_to_analyze: 'Pages',
  page_number: 'Page',
  findings_count: 'Findings',
  tactics_count: 'Tactics',
  benign_signals_count: 'Benign Signals',
  signals_count: 'Signals',
  urls_prioritized: 'URLs Flagged',
  url_count: 'URL Count',
  pages_analyzed: 'Pages Analyzed',
  page_count: 'Pages',
  priority_urls_count: 'Priority URLs',
  page_description: 'Description',
  element_count: 'Elements',
  element_type: 'Element Type',
  significance: 'Significance',
  visual_description: 'Visual',
  technical_data: 'Technical Data',
  assessment: 'Assessment',
  document_flow_summary: 'Document Flow',
  executive_summary: 'Executive Summary',
  
  // URLInvestigation fields
  url: 'URL',
  priority: 'Priority',
  high_priority_count: 'High Priority',
  low_priority_count: 'Low Priority',
  total_urls: 'Total URLs',
  urls_to_investigate: 'To Investigate',
  urls_skipped: 'Skipped',
  tool_count: 'Tools',
  tool_name: 'Tool',
  mission_directory: 'Mission Directory',
  screenshot_count: 'Screenshots',
  final_url: 'Final URL',
  investigation_count: 'Investigations',
  
  // ReportGenerator fields
  verdict: 'Verdict',
  confidence: 'Confidence',
  summary: 'Summary',
  report_length: 'Report Length',
  report_preview: 'Preview',
  report_path: 'Report Path',
  final_verdict: 'Final Verdict',
  final_confidence: 'Confidence',
  state_path: 'State Path',
  full_report: 'Full Report',
  
  // Complex object fields
  detailed_findings: 'Detailed Findings',
  deception_tactics: 'Deception Tactics',
  benign_signals: 'Benign Signals',
  prioritized_urls: 'Prioritized URLs',
  all_detailed_findings: 'All Findings',
  all_deception_tactics: 'All Tactics',
  all_benign_signals: 'All Benign Signals',
  all_priority_urls: 'All Priority URLs',
  detected_threats: 'Detected Threats',
  log_messages: 'Log Messages',
};

/**
 * Field value transformers
 * Maps field names to formatting functions
 */
export const FIELD_FORMATTERS = {
  // Percentages
  confidence: (val) => typeof val === 'number' ? `${(val * 100).toFixed(1)}%` : val,
  final_confidence: (val) => typeof val === 'number' ? `${(val * 100).toFixed(1)}%` : val,
  
  // URLs (truncate)
  url: (val) => typeof val === 'string' && val.length > 60 ? val.substring(0, 60) + '...' : val,
  final_url: (val) => typeof val === 'string' && val.length > 60 ? val.substring(0, 60) + '...' : val,
  
  // File paths (show basename)
  file_path: (val) => typeof val === 'string' ? val.split('/').pop() : val,
  output_file: (val) => typeof val === 'string' ? val.split('/').pop() : val,
  report_path: (val) => typeof val === 'string' ? val.split('/').pop() : val,
  saved_path: (val) => typeof val === 'string' ? val.split('/').pop() : val,
  
  // Complex objects (show count)
  detailed_findings: (val) => Array.isArray(val) ? `${val.length} items` : val,
  deception_tactics: (val) => Array.isArray(val) ? `${val.length} tactics` : val,
  benign_signals: (val) => Array.isArray(val) ? `${val.length} signals` : val,
  prioritized_urls: (val) => Array.isArray(val) ? `${val.length} URLs` : val,
  all_detailed_findings: (val) => Array.isArray(val) ? `${val.length} items` : val,
  all_deception_tactics: (val) => Array.isArray(val) ? `${val.length} tactics` : val,
  all_benign_signals: (val) => Array.isArray(val) ? `${val.length} signals` : val,
  all_priority_urls: (val) => Array.isArray(val) ? `${val.length} URLs` : val,
  images_data: (val) => Array.isArray(val) ? `${val.length} images` : val,
  url_list: (val) => Array.isArray(val) ? `${val.length} URLs` : val,
  qr_list: (val) => Array.isArray(val) ? `${val.length} QR codes` : val,
  log_messages: (val) => Array.isArray(val) ? `${val.length} messages` : val,
  detected_threats: (val) => Array.isArray(val) ? `${val.length} threats` : val,
  
  // Long text (truncate)
  reasoning: (val) => typeof val === 'string' && val.length > 100 ? val.substring(0, 100) + '...' : val,
  summary: (val) => typeof val === 'string' && val.length > 100 ? val.substring(0, 100) + '...' : val,
  report_preview: (val) => typeof val === 'string' && val.length > 100 ? val.substring(0, 100) + '...' : val,
  full_report: (val) => typeof val === 'string' ? `${val.length} characters` : val,
  
  // Booleans
  is_complete: (val) => val ? 'Yes' : 'No',
};

/**
 * Get expected fields for a given agent, node, and event_type
 * @param {string} agent - Agent name (e.g., 'FileAnalysis')
 * @param {string} node - Node name (e.g., 'identify_suspicious_elements')
 * @param {string|null} eventType - Event type or null
 * @returns {string[]|null} Array of field names or null if not found
 */
export function getExpectedFields(agent, node, eventType = null) {
  const agentSchema = LOG_FIELD_SCHEMA[agent];
  if (!agentSchema) return null;
  
  const nodeSchema = agentSchema[node];
  if (!nodeSchema) return null;
  
  const fields = nodeSchema[eventType || 'null'];
  if (!fields) return null;
  
  // Handle multiple possible field sets for null events
  if (Array.isArray(fields[0])) {
    return fields[0]; // Return first variant
  }
  
  return fields;
}

/**
 * Check if a field should be displayed
 * @param {string} fieldName - Field name to check
 * @returns {boolean} True if field should be displayed
 */
export function shouldDisplayField(fieldName) {
  return !HIDDEN_FIELDS.includes(fieldName);
}

/**
 * Get display name for a field
 * @param {string} fieldName - Internal field name
 * @returns {string} User-friendly display name
 */
export function getFieldDisplayName(fieldName) {
  return FIELD_DISPLAY_NAMES[fieldName] || fieldName
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Format a field value for display
 * @param {string} fieldName - Field name
 * @param {*} value - Field value
 * @returns {string} Formatted value
 */
export function formatFieldValue(fieldName, value) {
  const formatter = FIELD_FORMATTERS[fieldName];
  if (formatter) {
    return formatter(value);
  }
  
  // Default formatting
  if (value === null || value === undefined) return 'N/A';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

/**
 * Sort fields by priority for display
 * @param {string[]} fieldNames - Array of field names
 * @returns {string[]} Sorted field names
 */
export function sortFieldsByPriority(fieldNames) {
  return [...fieldNames].sort((a, b) => {
    const aPriority = PRIORITY_FIELDS.indexOf(a);
    const bPriority = PRIORITY_FIELDS.indexOf(b);
    
    // Both are priority fields
    if (aPriority >= 0 && bPriority >= 0) return aPriority - bPriority;
    
    // Only a is priority
    if (aPriority >= 0) return -1;
    
    // Only b is priority
    if (bPriority >= 0) return 1;
    
    // Neither is priority - alphabetical
    return a.localeCompare(b);
  });
}
