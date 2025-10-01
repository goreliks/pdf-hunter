import { useState, useRef, useEffect } from 'react';
import { getAgentStatus } from '../utils/logUtils';
import LogViewer from './LogViewer';

export default function AgentPanel({ agentName, displayName, logs, icon }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const status = getAgentStatus(logs);
  
  // Status badge colors
  const statusColors = {
    idle: 'bg-gray-600 text-gray-300',
    running: 'bg-blue-600 text-blue-100 animate-pulse',
    complete: 'bg-green-600 text-green-100',
    error: 'bg-red-600 text-red-100',
  };

  const statusText = {
    idle: 'Idle',
    running: 'Running...',
    complete: 'Complete',
    error: 'Error',
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
      {/* Panel Header */}
      <div
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-750 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <div>
            <h2 className="text-lg font-semibold">{displayName}</h2>
            <p className="text-xs text-gray-400">{logs.length} log entries</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Status Badge */}
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColors[status]}`}>
            {statusText[status]}
          </span>
          
          {/* Expand/Collapse Icon */}
          <svg
            className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Panel Content */}
      {isExpanded && (
        <div className="border-t border-gray-700">
          <LogViewer logs={logs} agentName={agentName} />
        </div>
      )}
    </div>
  );
}
