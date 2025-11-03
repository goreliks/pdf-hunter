import { useState, useEffect, useRef } from 'react';
import { useSSEStream } from '../hooks/useSSEStream';
import { groupLogsByAgent, getAgentStatus } from '../utils/logUtils';
import { loadMockSession, simulateStreaming } from '../utils/mockDataLoader';
import AgentPanel from './AgentPanel';
import ViewModeToggle from './ViewModeToggle';
import { ConnectionNetwork, ConnectionNode } from './ConnectionNetwork';
import Sidebar from './Sidebar';
import AgentDetailModal from './AgentDetailModal';

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

  // Sidebar state
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Agent detail modal state
  const [selectedAgent, setSelectedAgent] = useState(null);

  // Handle agent click from sidebar
  const handleAgentClick = (agentName) => {
    setSelectedAgent(agentName);
  };

  // Close agent detail modal
  const handleCloseAgentModal = () => {
    setSelectedAgent(null);
  };

  // Group logs by agent for individual panels
  const agentLogs = groupLogsByAgent(logs);

  // Get agent statuses
  const agentStatuses = {
    PdfExtraction: getAgentStatus(agentLogs.PdfExtraction),
    FileAnalysis: getAgentStatus(agentLogs.FileAnalysis),
    ImageAnalysis: getAgentStatus(agentLogs.ImageAnalysis),
    URLInvestigation: getAgentStatus(agentLogs.URLInvestigation),
    ReportGenerator: getAgentStatus(agentLogs.ReportGenerator),
  };

  // Extract verdict and confidence from Report Generator logs
  const getVerdictAndConfidence = () => {
    const reportLogs = agentLogs.ReportGenerator || [];

    // Try to find verdict in any Report Generator log
    for (const log of reportLogs) {
      const extra = log.record?.extra;
      if (!extra) continue;

      // Check for verdict in various possible field names
      const verdict = extra.overall_verdict || extra.verdict || extra.final_verdict;
      const confidence = extra.final_confidence || extra.confidence;

      if (verdict || confidence !== undefined) {
        console.log('Found verdict/confidence:', { verdict, confidence, event: extra.event_type });
        return { verdict, confidence };
      }
    }

    console.log('No verdict found in', reportLogs.length, 'Report Generator logs');
    return { verdict: null, confidence: null };
  };

  const { verdict, confidence } = getVerdictAndConfidence();
  const isReportComplete = agentStatuses.ReportGenerator === 'complete';
  const isAnalyzing = logs.length > 0 && !isReportComplete;

  // Container ref for connection positioning
  const containerRef = useRef(null);

  // Helper function to get node styling based on status
  const getNodeStyle = (status) => {
    switch (status) {
      case 'running':
        return {
          glowColor: '#00FFD1',
          shouldGlow: true,
          outlineStyle: null
        };
      case 'complete':
        return {
          glowColor: '#00FFD1',
          shouldGlow: false,
          outlineStyle: {
            border: '2px solid #00FFD1',
            boxShadow: '0 0 10px rgba(0, 255, 209, 0.6)',
          }
        };
      case 'error':
        return {
          glowColor: '#f43f5e',
          shouldGlow: false,
          outlineStyle: {
            border: '2px solid #f43f5e',
            boxShadow: '0 0 10px rgba(244, 63, 94, 0.6)',
          }
        };
      default: // idle
        return {
          glowColor: null,
          shouldGlow: false,
          outlineStyle: null
        };
    }
  };

  // Define agent workflow connections
  const connections = [
    // PdfExtraction splits to FileAnalysis and ImageAnalysis
    {
      fromId: 'agent-pdf',
      toId: 'agent-file',
      fromPoint: 'bottom-left-quarter', // Bottom edge at left quarter
      toPoint: 'top-center',
      color: '#00FFD1', // cyan
      delay: 0,
      duration: 2,
      type: 'straight',
      active: agentLogs.PdfExtraction?.length > 0 && agentLogs.FileAnalysis?.length > 0 && agentStatuses.FileAnalysis !== 'complete',
      completed: agentStatuses.FileAnalysis === 'complete'
    },
    {
      fromId: 'agent-pdf',
      toId: 'agent-image',
      fromPoint: 'bottom-right-quarter', // Bottom edge at right quarter
      toPoint: 'top-center',
      color: '#9B8FFF', // purple
      delay: 0.2,
      duration: 2,
      type: 'straight',
      active: agentLogs.PdfExtraction?.length > 0 && agentLogs.ImageAnalysis?.length > 0 && agentStatuses.ImageAnalysis !== 'complete',
      completed: agentStatuses.ImageAnalysis === 'complete'
    },
    // ImageAnalysis feeds into URLInvestigation
    {
      fromId: 'agent-image',
      toId: 'agent-url',
      fromPoint: 'bottom-center',
      toPoint: 'top-center',
      color: '#9B8FFF', // purple
      delay: 0.2,
      duration: 2,
      type: 'straight',
      active: agentLogs.ImageAnalysis?.length > 0 && agentLogs.URLInvestigation?.length > 0 && agentStatuses.URLInvestigation !== 'complete',
      completed: agentStatuses.URLInvestigation === 'complete'
    },
    // FileAnalysis feeds into ReportGenerator
    {
      fromId: 'agent-file',
      toId: 'agent-report',
      fromPoint: 'bottom-center',
      toPoint: 'top-left-quarter', // Top edge at left quarter
      color: '#00FFD1', // cyan
      delay: 0,
      duration: 2,
      type: 'straight',
      active: agentLogs.FileAnalysis?.length > 0 && agentLogs.ReportGenerator?.length > 0 && agentStatuses.ReportGenerator !== 'complete',
      completed: agentStatuses.ReportGenerator === 'complete'
    },
    // URLInvestigation feeds into ReportGenerator
    {
      fromId: 'agent-url',
      toId: 'agent-report',
      fromPoint: 'bottom-center',
      toPoint: 'top-right-quarter', // Top edge at right quarter
      color: '#9B8FFF', // purple
      delay: 0.2,
      duration: 2,
      type: 'straight',
      active: agentLogs.URLInvestigation?.length > 0 && agentLogs.ReportGenerator?.length > 0 && agentStatuses.ReportGenerator !== 'complete',
      completed: agentStatuses.ReportGenerator === 'complete'
    }
  ];

  return (
    <div className="min-h-screen gradient-bg holographic-overlay text-white px-16 py-8">
      {/* Header */}
      <header className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="text-3xl font-bold tactical-heading neon-text-purple tracking-wider uppercase">
              PDF HUNTER ANALYSIS {devMode && <span className="text-blackalgo-cyan text-xl">[DEV MODE]</span>}
            </h1>
            {filename && (
              <p className="text-sm text-blackalgo-cyan mt-2 tactical-mono" style={{
                textShadow: '0 0 10px rgba(0, 255, 209, 0.6)'
              }}>
                &gt; TARGET: <span className="text-blackalgo-text-light font-medium">{filename}</span>
              </p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <ViewModeToggle mode={viewMode} onChange={setViewMode} />
            {onSessionEnd && (
              <button
                onClick={onSessionEnd}
                className="px-4 py-2 rounded-lg transition-all duration-200 text-sm font-medium tactical-heading uppercase tracking-wider terminal-scanlines"
                style={{
                  background: 'linear-gradient(135deg, #00FFD1 0%, #9B8FFF 100%)',
                  color: '#0B0D17',
                  border: '2px solid rgba(0, 255, 209, 0.5)',
                  boxShadow: '0 0 20px rgba(0, 255, 209, 0.4)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 0 40px rgba(0, 255, 209, 0.8)';
                  e.currentTarget.style.transform = 'scale(1.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = '0 0 20px rgba(0, 255, 209, 0.4)';
                  e.currentTarget.style.transform = 'scale(1)';
                }}
                title="Start a new analysis"
              >
                New Analysis
              </button>
            )}
          </div>
        </div>
        <div className="flex items-center justify-between gap-4">
          {/* Left side - Connection status */}
          <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-blackalgo-bg-dark/40 backdrop-blur-sm px-3 py-1.5 rounded-lg border terminal-scanlines" style={{
            borderColor: 'rgba(0, 255, 209, 0.2)'
          }}>
            <div className={`w-3 h-3 rounded-full ${
              devMode
                ? 'bg-blackalgo-purple-light animate-pulse'
                : isConnected
                ? 'bg-blackalgo-cyan animate-pulse'
                : 'bg-rose-400'
            }`} style={{
              boxShadow: devMode
                ? '0 0 10px rgba(155, 143, 255, 0.8)'
                : isConnected
                ? '0 0 10px rgba(0, 255, 209, 0.8)'
                : '0 0 10px rgba(251, 113, 133, 0.8)'
            }}></div>
            <span className="text-sm text-blackalgo-cyan tactical-mono uppercase tracking-wider">
              {devMode && (isLoadingMock ? 'LOADING MOCK DATA...' : 'DEV MODE ACTIVE')}
              {!devMode && connectionState === 'connected' && 'CONNECTED'}
              {!devMode && connectionState === 'connecting' && 'CONNECTING...'}
              {!devMode && connectionState === 'reconnecting' && 'RECONNECTING...'}
              {!devMode && connectionState === 'error' && 'CONNECTION ERROR'}
              {!devMode && connectionState === 'failed' && 'CONNECTION FAILED'}
              {!devMode && connectionState === 'disconnected' && 'DISCONNECTED'}
            </span>
          </div>
          <span className="text-sm text-blackalgo-text-muted bg-blackalgo-bg-dark/40 backdrop-blur-sm px-3 py-1.5 rounded-lg border tactical-mono" style={{
            borderColor: 'rgba(155, 143, 255, 0.2)'
          }}>
            SESSION: <span className="text-blackalgo-purple-light">{sessionId}</span>
          </span>
          {!devMode && (
            <span className="text-xs text-blackalgo-cyan tactical-mono bg-blackalgo-bg-dark/40 backdrop-blur-sm px-3 py-1.5 rounded-lg border" style={{
              borderColor: 'rgba(0, 255, 209, 0.2)',
              textShadow: '0 0 8px rgba(0, 255, 209, 0.5)'
            }}>
              &gt; TIP: PAGE REFRESH SAFE
            </span>
          )}
          {devMode && (
            <span className="text-xs text-blackalgo-purple-light tactical-mono bg-blackalgo-bg-dark/40 backdrop-blur-sm px-3 py-1.5 rounded-lg border" style={{
              borderColor: 'rgba(155, 143, 255, 0.2)',
              textShadow: '0 0 8px rgba(155, 143, 255, 0.5)'
            }}>
              &gt; DEV MODE: MOCK DATA ACTIVE
            </span>
          )}
          </div>

          {/* Right side - Verdict and Confidence */}
          <div className="flex items-center gap-3">
            {/* Verdict Box */}
            <div className={`flex items-center gap-2 bg-blackalgo-bg-dark/40 backdrop-blur-sm px-4 py-2 rounded-lg border terminal-scanlines hud-corners transition-all duration-300 ${
              isAnalyzing && !verdict ? 'animate-pulse' : ''
            }`} style={{
              borderColor: verdict === 'Malicious' ? 'rgba(244, 63, 94, 0.5)' :
                          verdict === 'Suspicious' ? 'rgba(251, 191, 36, 0.5)' :
                          verdict === 'Benign' ? 'rgba(34, 197, 94, 0.5)' :
                          'rgba(155, 143, 255, 0.2)',
              minWidth: '180px'
            }}>
              <span className="text-xs text-blackalgo-text-muted tactical-mono uppercase tracking-wider">
                VERDICT:
              </span>
              <span className="text-sm font-bold tactical-mono uppercase tracking-wider" style={{
                color: verdict === 'Malicious' ? '#f43f5e' :
                       verdict === 'Suspicious' ? '#fbbf24' :
                       verdict === 'Benign' ? '#22c55e' :
                       '#9B8FFF',
                textShadow: verdict ? `0 0 10px ${
                  verdict === 'Malicious' ? 'rgba(244, 63, 94, 0.6)' :
                  verdict === 'Suspicious' ? 'rgba(251, 191, 36, 0.6)' :
                  verdict === 'Benign' ? 'rgba(34, 197, 94, 0.6)' :
                  'rgba(155, 143, 255, 0.6)'
                }` : 'none'
              }}>
                {verdict || (isAnalyzing ? 'ANALYZING...' : 'PENDING')}
              </span>
            </div>

            {/* Confidence Box */}
            <div className={`flex items-center gap-2 bg-blackalgo-bg-dark/40 backdrop-blur-sm px-4 py-2 rounded-lg border terminal-scanlines hud-corners transition-all duration-300 ${
              isAnalyzing && confidence === null ? 'animate-pulse' : ''
            }`} style={{
              borderColor: 'rgba(0, 255, 209, 0.2)',
              minWidth: '160px'
            }}>
              <span className="text-xs text-blackalgo-text-muted tactical-mono uppercase tracking-wider">
                CONFIDENCE:
              </span>
              <span className="text-sm font-bold tactical-mono tracking-wider" style={{
                color: '#00FFD1',
                textShadow: confidence !== null ? '0 0 10px rgba(0, 255, 209, 0.6)' : 'none'
              }}>
                {confidence !== null ? `${(confidence * 100).toFixed(1)}%` : (isAnalyzing ? 'COMPUTING...' : '--')}
              </span>
            </div>
          </div>
        </div>
        {error && (
          <div className="mt-2 text-rose-400 text-sm bg-rose-900/20 border border-rose-500/30 rounded-lg px-3 py-2 tactical-mono terminal-scanlines">
            &gt; ERROR: {error}
          </div>
        )}
      </header>

      {/* Agent Panels Grid with Connection Animations */}
      <div ref={containerRef} className="relative space-y-8">
        {/* Connection Network Overlay */}
        <ConnectionNetwork connections={connections} containerRef={containerRef} />

        {/* Row 1: PDF Extraction (Full Width) */}
        <ConnectionNode
          id="agent-pdf"
          glowColor={getNodeStyle(agentStatuses.PdfExtraction).glowColor}
          active={getNodeStyle(agentStatuses.PdfExtraction).shouldGlow}
          className="block w-full"
        >
          <div
            className="rounded-lg transition-all duration-300 w-full"
            style={getNodeStyle(agentStatuses.PdfExtraction).outlineStyle}
          >
            <AgentPanel
              agentName="PdfExtraction"
              displayName="PDF Extraction"
              logs={agentLogs.PdfExtraction}
              icon="📄"
              viewMode={viewMode}
            />
          </div>
        </ConnectionNode>

        {/* Row 2 & 3: File Analysis (Left, Full Height) + Image & URL Investigation (Right, Stacked) */}
        <div className="grid grid-cols-2 gap-8" style={{ height: '770px', maxHeight: '770px', gridTemplateRows: '770px' }}>
          {/* File Analysis - Left side, full height spanning 2 rows */}
          <ConnectionNode
            id="agent-file"
            glowColor={getNodeStyle(agentStatuses.FileAnalysis).glowColor}
            active={getNodeStyle(agentStatuses.FileAnalysis).shouldGlow}
            className="h-full overflow-hidden"
          >
            <div
              className="rounded-lg transition-all duration-300 h-full overflow-hidden"
              style={getNodeStyle(agentStatuses.FileAnalysis).outlineStyle}
            >
              <AgentPanel
                agentName="FileAnalysis"
                displayName="File Analysis"
                logs={agentLogs.FileAnalysis}
                icon="🔍"
                viewMode={viewMode}
                className="h-full"
              />
            </div>
          </ConnectionNode>

          {/* Right side - Image Analysis + URL Investigation stacked */}
          <div className="flex flex-col gap-8">
            {/* Image Analysis */}
            <ConnectionNode
              id="agent-image"
              glowColor={getNodeStyle(agentStatuses.ImageAnalysis).glowColor}
              active={getNodeStyle(agentStatuses.ImageAnalysis).shouldGlow}
            >
              <div
                className="rounded-lg transition-all duration-300"
                style={getNodeStyle(agentStatuses.ImageAnalysis).outlineStyle}
              >
                <AgentPanel
                  agentName="ImageAnalysis"
                  displayName="Image Analysis"
                  logs={agentLogs.ImageAnalysis}
                  icon="🖼️"
                  viewMode={viewMode}
                />
              </div>
            </ConnectionNode>

            {/* URL Investigation */}
            <ConnectionNode
              id="agent-url"
              glowColor={getNodeStyle(agentStatuses.URLInvestigation).glowColor}
              active={getNodeStyle(agentStatuses.URLInvestigation).shouldGlow}
            >
              <div
                className="rounded-lg transition-all duration-300"
                style={getNodeStyle(agentStatuses.URLInvestigation).outlineStyle}
              >
                <AgentPanel
                  agentName="URLInvestigation"
                  displayName="URL Investigation"
                  logs={agentLogs.URLInvestigation}
                  icon="🌐"
                  viewMode={viewMode}
                />
              </div>
            </ConnectionNode>
          </div>
        </div>

        {/* Row 4: Report Generator (Full Width) */}
        <ConnectionNode
          id="agent-report"
          glowColor={getNodeStyle(agentStatuses.ReportGenerator).glowColor}
          active={getNodeStyle(agentStatuses.ReportGenerator).shouldGlow}
          className="block w-full"
        >
          <div
            className="rounded-lg transition-all duration-300 w-full"
            style={getNodeStyle(agentStatuses.ReportGenerator).outlineStyle}
          >
            <AgentPanel
              agentName="ReportGenerator"
              displayName="Report Generator"
              logs={agentLogs.ReportGenerator}
              icon="📊"
              viewMode={viewMode}
            />
          </div>
        </ConnectionNode>
      </div>

      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        agentStatuses={agentStatuses}
        sessionId={sessionId}
        onAgentClick={handleAgentClick}
      />

      {/* Agent Detail Modal */}
      {selectedAgent && (
        <AgentDetailModal
          agentName={selectedAgent}
          sessionId={sessionId}
          onClose={handleCloseAgentModal}
        />
      )}
    </div>
  );
}
