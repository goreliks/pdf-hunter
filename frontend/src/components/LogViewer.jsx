import { useEffect, useRef } from 'react';
import { formatLogEntry, getLogLevelColor } from '../utils/logUtils';

export default function LogViewer({ logs, agentName }) {
  const logContainerRef = useRef(null);
  const shouldAutoScrollRef = useRef(true);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (shouldAutoScrollRef.current && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  // Detect if user scrolled up (disable auto-scroll)
  const handleScroll = () => {
    if (!logContainerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    
    shouldAutoScrollRef.current = isAtBottom;
  };

  return (
    <div className="bg-gray-900 p-4">
      <div
        ref={logContainerRef}
        onScroll={handleScroll}
        className="font-mono text-sm h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800"
      >
        {logs.length === 0 ? (
          <div className="text-gray-500 italic">No logs yet...</div>
        ) : (
          logs.map((log, index) => (
            <LogEntry key={`${agentName}-${index}`} log={log} />
          ))
        )}
      </div>
    </div>
  );
}

function LogEntry({ log }) {
  const record = log.record || {};
  const timestamp = new Date(record.time?.timestamp * 1000 || Date.now()).toLocaleTimeString();
  const level = (record.level?.name || 'INFO').toUpperCase();
  const levelColor = getLogLevelColor(level);
  const message = record.message || log.text || '';
  const node = record.extra?.node ? `[${record.extra.node}]` : '';
  
  // Additional metadata to show if present
  const hasMetadata = record.extra?.event_type || record.extra?.file_path || record.extra?.mission_id;

  return (
    <div className="py-1 hover:bg-gray-800 transition-colors">
      <div className="flex gap-2">
        {/* Timestamp */}
        <span className="text-gray-500">[{timestamp}]</span>
        
        {/* Log Level */}
        <span className={`font-semibold ${levelColor} min-w-[60px]`}>
          {level}
        </span>
        
        {/* Node Name */}
        {node && (
          <span className="text-purple-400">{node}</span>
        )}
        
        {/* Message */}
        <span className="text-gray-200 flex-1">{message}</span>
      </div>
      
      {/* Additional metadata (if any) */}
      {hasMetadata && (
        <div className="ml-24 text-xs text-gray-500 mt-0.5">
          {record.extra?.event_type && <span className="mr-3">Event: {record.extra.event_type}</span>}
          {record.extra?.file_path && <span className="mr-3">File: {record.extra.file_path}</span>}
          {record.extra?.mission_id && <span className="mr-3">Mission: {record.extra.mission_id}</span>}
        </div>
      )}
    </div>
  );
}
