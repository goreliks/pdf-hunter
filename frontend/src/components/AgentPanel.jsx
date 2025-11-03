import { useState, useRef, useEffect } from 'react';
import { getAgentStatus } from '../utils/logUtils';
import LogViewer from './LogViewer';

export default function AgentPanel({ agentName, displayName, logs, icon, viewMode, className = '' }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const status = getAgentStatus(logs);

  // Status badge colors
  const statusColors = {
    idle: 'bg-gray-600/80 text-gray-300 border border-gray-500/30',
    running: 'bg-gradient-to-r from-purple-600 to-pink-600 text-white animate-pulse border border-purple-400/50',
    complete: 'bg-gradient-to-r from-green-600 to-emerald-600 text-white border border-green-400/50',
    error: 'bg-gradient-to-r from-red-600 to-rose-600 text-white border border-red-400/50',
  };

  const statusText = {
    idle: 'Idle',
    running: 'Running...',
    complete: 'Complete',
    error: 'Error',
  };

  return (
    <div className={`hud-corners bg-gray-800/50 backdrop-blur-sm rounded-lg border border-purple-500/20 overflow-hidden card-glow terminal-scanlines transition-all duration-300 w-full ${className.includes('h-full') ? 'flex flex-col min-h-0' : ''} ${className}`}>
      {/* Panel Header */}
      <div
        className={`flex items-center justify-between p-4 cursor-pointer hover:bg-purple-900/20 transition-colors relative ${className.includes('h-full') ? 'flex-shrink-0' : ''}`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <div>
            <h2 className="text-lg font-semibold text-purple-100 tactical-heading" style={{ fontSize: '0.9rem', letterSpacing: '2px' }}>{displayName}</h2>
            <p className="text-xs text-purple-300/60 tactical-mono">{logs.length} log entries</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Status Badge */}
          <span className={`px-3 py-1 rounded-full text-xs font-medium tactical-mono ${statusColors[status]}`}>
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
        <div className={`border-t border-purple-500/20 bg-gray-900/50 ${className.includes('h-full') ? 'flex-1 flex flex-col min-h-0' : ''}`}>
          <LogViewer
            logs={logs}
            agentName={agentName}
            viewMode={viewMode}
            fillHeight={className.includes('h-full')}
          />
        </div>
      )}
    </div>
  );
}
