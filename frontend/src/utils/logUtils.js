/**
 * Routes log entries to their respective agent panels
 * Groups logs by agent name for dashboard display
 * 
 * @param {Array} logs - Array of log entries from SSE stream
 * @returns {Object} - Logs grouped by agent: { PdfExtraction: [...], FileAnalysis: [...], etc. }
 */
export function groupLogsByAgent(logs) {
  const agents = {
    PdfExtraction: [],
    FileAnalysis: [],
    ImageAnalysis: [],
    URLInvestigation: [],
    ReportGenerator: [],
    Orchestrator: [],
    Unknown: [], // For logs without an agent field
  };

  logs.forEach((log) => {
    // Check both top-level and nested locations for agent name
    const agentName = log.agent || log.record?.extra?.agent || 'Unknown';
    
    if (agents[agentName]) {
      agents[agentName].push(log);
    } else {
      // If unknown agent name, add to Unknown
      agents.Unknown.push(log);
    }
  });

  return agents;
}

/**
 * Formats a log entry for display
 * 
 * @param {Object} logEntry - Single log entry from backend
 * @returns {string} - Formatted log string for terminal-like display
 */
export function formatLogEntry(logEntry) {
  const record = logEntry.record || {};
  const timestamp = record.time?.repr || new Date().toISOString();
  const level = (record.level?.name || 'INFO').toUpperCase();
  const message = record.message || logEntry.text || '';
  const node = record.extra?.node ? `[${record.extra.node}]` : '';
  
  return `[${timestamp}] ${level} ${node} ${message}`;
}

/**
 * Determines the current status of an agent based on its logs
 * 
 * @param {Array} agentLogs - Array of log entries for a specific agent
 * @returns {string} - Status: 'idle', 'running', 'complete', 'error'
 */
export function getAgentStatus(agentLogs) {
  if (!agentLogs || agentLogs.length === 0) {
    return 'idle';
  }

  const lastLog = agentLogs[agentLogs.length - 1];
  const level = lastLog.record?.level?.name?.toLowerCase();

  // Check for completion or error keywords in message
  const message = (lastLog.record?.message || lastLog.text || '').toLowerCase();
  
  if (level === 'error' || level === 'critical') {
    return 'error';
  }
  
  if (message.includes('complete') || message.includes('finished')) {
    return 'complete';
  }

  return 'running';
}

/**
 * Gets a color class for log level styling
 * 
 * @param {string} level - Log level (INFO, DEBUG, WARNING, ERROR, etc.)
 * @returns {string} - Tailwind color class
 */
export function getLogLevelColor(level) {
  const levelUpper = level?.toUpperCase();
  
  switch (levelUpper) {
    case 'DEBUG':
    case 'TRACE':
      return 'text-gray-400';
    case 'INFO':
      return 'text-blue-400';
    case 'SUCCESS':
      return 'text-green-400';
    case 'WARNING':
      return 'text-yellow-400';
    case 'ERROR':
      return 'text-red-400';
    case 'CRITICAL':
      return 'text-red-600 font-bold';
    default:
      return 'text-gray-300';
  }
}
