import { useState, useEffect, useRef } from 'react';
import { useSSEStream } from '../hooks/useSSEStream';
import { groupLogsByAgent } from '../utils/logUtils';
import { loadMockSession, simulateStreaming } from '../utils/mockDataLoader';
import AgentPanel from './AgentPanel';
import ViewModeToggle from './ViewModeToggle';

export default function Dashboard({ sessionId, filename, onSessionEnd, devMode = false }) {
  const { logs: sseLogs, isConnected, error, connectionState } = useSSEStream(sessionId, !devMode);
  const [mockLogs, setMockLogs] = useState([]);
  const [isLoadingMock, setIsLoadingMock] = useState(false);
  const hasLoadedMockRef = useRef(false);

  // Use mock logs in dev mode, SSE logs otherwise
  const logs = devMode ? mockLogs : sseLogs;

  // Load and stream mock data in dev mode
  useEffect(() => {
    // Prevent double-loading in React Strict Mode
    if (devMode && !hasLoadedMockRef.current) {
      hasLoadedMockRef.current = true;
      setIsLoadingMock(true);
      loadMockSession().then(loadedLogs => {
        if (loadedLogs.length > 0) {
          // Simulate streaming with delays
          simulateStreaming(loadedLogs, (log) => {
            setMockLogs(prev => [...prev, log]);
          }, 100); // 100ms delay between logs
        }
        setIsLoadingMock(false);
      });
    }

    // Reset flag when devMode changes
    return () => {
      if (!devMode) {
        hasLoadedMockRef.current = false;
      }
    };
  }, [devMode]);
  
  // View mode state with localStorage persistence
  const [viewMode, setViewMode] = useState(() => {
    return localStorage.getItem('pdf-hunter-view-mode') || 'both';
  });

  // Persist view mode to localStorage
  useEffect(() => {
    localStorage.setItem('pdf-hunter-view-mode', viewMode);
  }, [viewMode]);
  
  // Group logs by agent for individual panels
  const agentLogs = groupLogsByAgent(logs);

  return (
    <div className="min-h-screen gradient-bg text-white px-8 py-6">
      {/* Header */}
      <header className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-pink-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
              PDF Hunter Analysis Dashboard {devMode && <span className="text-purple-400 text-xl">(Dev Mode)</span>}
            </h1>
            {filename && (
              <p className="text-sm text-purple-300/70 mt-1">
                Analyzing: <span className="text-purple-200 font-medium">{filename}</span>
              </p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <ViewModeToggle mode={viewMode} onChange={setViewMode} />
            {onSessionEnd && (
              <button
                onClick={onSessionEnd}
                className="px-4 py-2 bg-gray-800/50 hover:bg-gray-700/50 text-purple-200 rounded-lg border border-purple-500/30 hover:border-purple-400/50 transition-all duration-200 text-sm font-medium"
                title="Start a new analysis"
              >
                New Analysis
              </button>
            )}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-gray-800/30 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-purple-500/20">
            <div className={`w-3 h-3 rounded-full ${
              devMode
                ? 'bg-purple-400 shadow-lg shadow-purple-400/50'
                : isConnected
                ? 'bg-emerald-400 shadow-lg shadow-emerald-400/50 animate-pulse'
                : 'bg-rose-400 shadow-lg shadow-rose-400/50'
            }`}></div>
            <span className="text-sm text-purple-100">
              {devMode && (isLoadingMock ? 'Loading Mock Data...' : 'Dev Mode Active')}
              {!devMode && connectionState === 'connected' && 'Connected'}
              {!devMode && connectionState === 'connecting' && 'Connecting...'}
              {!devMode && connectionState === 'reconnecting' && 'Reconnecting...'}
              {!devMode && connectionState === 'error' && 'Connection Error'}
              {!devMode && connectionState === 'failed' && 'Connection Failed'}
              {!devMode && connectionState === 'disconnected' && 'Disconnected'}
            </span>
          </div>
          <span className="text-sm text-purple-300/70 bg-gray-800/30 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-purple-500/20">
            Session: <span className="font-mono text-purple-200">{sessionId}</span>
          </span>
          {!devMode && (
            <span className="text-xs text-purple-400/60 bg-gray-800/30 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-purple-500/20">
              💡 Tip: You can refresh this page without losing progress
            </span>
          )}
          {devMode && (
            <span className="text-xs text-purple-400/60 bg-gray-800/30 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-purple-500/20">
              🔧 Dev Mode: Using mock data for frontend development
            </span>
          )}
        </div>
        {error && (
          <div className="mt-2 text-rose-400 text-sm bg-rose-900/20 border border-rose-500/30 rounded-lg px-3 py-2">
            ⚠️ {error}
          </div>
        )}
      </header>

      {/* Agent Panels Grid */}
      <div className="grid grid-cols-1 gap-4">
        <AgentPanel
          agentName="PdfExtraction"
          displayName="PDF Extraction"
          logs={agentLogs.PdfExtraction}
          icon="📄"
          viewMode={viewMode}
        />
        <AgentPanel
          agentName="FileAnalysis"
          displayName="File Analysis"
          logs={agentLogs.FileAnalysis}
          icon="🔍"
          viewMode={viewMode}
        />
        <AgentPanel
          agentName="ImageAnalysis"
          displayName="Image Analysis"
          logs={agentLogs.ImageAnalysis}
          icon="🖼️"
          viewMode={viewMode}
        />
        <AgentPanel
          agentName="URLInvestigation"
          displayName="URL Investigation"
          logs={agentLogs.URLInvestigation}
          icon="🌐"
          viewMode={viewMode}
        />
        <AgentPanel
          agentName="ReportGenerator"
          displayName="Report Generator"
          logs={agentLogs.ReportGenerator}
          icon="📊"
          viewMode={viewMode}
        />
      </div>
    </div>
  );
}
