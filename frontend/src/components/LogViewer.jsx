import { useEffect, useRef } from 'react';
import { getLogLevelColor } from '../utils/logUtils';
import { extractFieldsFromLog } from '../utils/fieldExtractor';

export default function LogViewer({ logs, agentName, viewMode = 'both', fillHeight = false }) {
  const logContainerRef = useRef(null);
  const shouldAutoScrollRef = useRef(true);
  const prevViewModeRef = useRef(viewMode);
  const scrollPosBeforeToggleRef = useRef(0);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (shouldAutoScrollRef.current && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  // Preserve scroll position when view mode changes
  useEffect(() => {
    if (prevViewModeRef.current !== viewMode && logContainerRef.current) {
      // Save scroll position before mode change
      scrollPosBeforeToggleRef.current = logContainerRef.current.scrollTop;
      
      // Restore scroll position after React re-renders
      requestAnimationFrame(() => {
        if (logContainerRef.current) {
          logContainerRef.current.scrollTop = scrollPosBeforeToggleRef.current;
        }
      });
    }
    prevViewModeRef.current = viewMode;
  }, [viewMode]);

  // Detect if user scrolled up (disable auto-scroll)
  const handleScroll = () => {
    if (!logContainerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    
    shouldAutoScrollRef.current = isAtBottom;
  };

  return (
    <div className={`bg-gray-900/30 p-4 ${fillHeight ? 'flex-1 flex flex-col min-h-0' : ''}`}>
      <div
        ref={logContainerRef}
        onScroll={handleScroll}
        className={`font-mono text-xs ${fillHeight ? 'flex-1 min-h-0' : 'h-64'} overflow-y-auto overflow-x-auto scrollbar-thin scrollbar-thumb-purple-500/50 scrollbar-track-gray-800/50 transition-opacity duration-150`}
      >
        {logs.length === 0 ? (
          <div className="text-purple-300/40 italic">No logs yet...</div>
        ) : (
          logs.map((log, index) => (
            <LogEntry key={`${agentName}-${index}`} log={log} viewMode={viewMode} />
          ))
        )}
      </div>
    </div>
  );
}

function LogEntry({ log, viewMode }) {
  const record = log.record || {};
  
  // Extract timestamp (HH:MM:SS format)
  const timestamp = record.time?.timestamp 
    ? new Date(record.time.timestamp * 1000).toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
      })
    : '00:00:00';
  
  const level = (record.level?.name || 'INFO').toUpperCase();
  const levelColor = getLogLevelColor(level);
  const message = record.message || log.text || '';
  
  // Extract structured fields
  const fields = extractFieldsFromLog(log);
  const node = record.extra?.node || 'unknown';
  const eventType = record.extra?.event_type || 'null';
  
  // Determine what to show based on view mode
  const shouldShowMessage = (viewMode === 'both' || viewMode === 'messages') && message;
  const shouldShowFields = (viewMode === 'both' || viewMode === 'structured') && fields.length > 0;
  
  // Don't render anything if there's nothing to show in current view mode
  if (!shouldShowMessage && !shouldShowFields) {
    return null;
  }
  
  return (
    <div className="py-2 border-b border-purple-500/10 hover:bg-purple-900/10 transition-colors">
      {/* Message Header - show based on view mode */}
      {shouldShowMessage && (
        <div className="flex gap-3 mb-1.5">
          {/* Log Level */}
          <span className={`font-semibold text-xs ${levelColor} min-w-[70px] shrink-0`}>
            {level}
          </span>
          
          {/* Message */}
          <span className="text-purple-100/80 text-xs break-all">{message}</span>
        </div>
      )}
      
      {/* Structured Fields - show based on view mode */}
      {shouldShowFields && fields.map((field, idx) => (
        <FieldRow
          key={idx}
          timestamp={timestamp}
          node={node}
          eventType={eventType}
          fieldName={field.displayName}
          value={field.value}
        />
      ))}
    </div>
  );
}

function FieldRow({ timestamp, node, eventType, fieldName, value }) {
  return (
    <div className="flex items-start gap-2 py-1 text-xs font-mono leading-snug">
      {/* Timestamp */}
      <span className="text-purple-300/50 shrink-0 w-[65px]">{timestamp}</span>

      {/* Separator */}
      <span className="text-purple-400/40 font-bold shrink-0">|</span>

      {/* Node */}
      <span className="text-fuchsia-400 shrink-0 w-[100px] truncate" title={node}>{node}</span>

      {/* Separator */}
      <span className="text-purple-400/40 font-bold shrink-0">|</span>

      {/* Event Type */}
      <span className="text-violet-400 shrink-0 w-[120px] truncate" title={eventType}>{eventType}</span>

      {/* Separator */}
      <span className="text-purple-400/40 font-bold shrink-0">|</span>

      {/* Field Name */}
      <span className="text-pink-400 shrink-0 w-[90px] truncate" title={fieldName}>{fieldName}</span>

      {/* Separator */}
      <span className="text-purple-400/40 font-bold shrink-0">|</span>

      {/* Value */}
      <span className="text-purple-100/90 flex-1 min-w-0 break-words" style={{ wordBreak: 'break-word', overflowWrap: 'break-word' }}>{value}</span>
    </div>
  );
}
