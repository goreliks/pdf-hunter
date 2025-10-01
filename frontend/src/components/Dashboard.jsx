import { useSSEStream } from '../hooks/useSSEStream';
import { groupLogsByAgent } from '../utils/logUtils';
import AgentPanel from './AgentPanel';

export default function Dashboard({ sessionId }) {
  const { logs, isConnected, error, connectionState } = useSSEStream(sessionId);
  
  // Group logs by agent for individual panels
  const agentLogs = groupLogsByAgent(logs);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <header className="mb-6">
        <h1 className="text-3xl font-bold mb-2">PDF Hunter Analysis Dashboard</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span className="text-sm">
              {connectionState === 'connected' && 'Connected'}
              {connectionState === 'connecting' && 'Connecting...'}
              {connectionState === 'reconnecting' && 'Reconnecting...'}
              {connectionState === 'error' && 'Connection Error'}
              {connectionState === 'failed' && 'Connection Failed'}
              {connectionState === 'disconnected' && 'Disconnected'}
            </span>
          </div>
          <span className="text-sm text-gray-400">Session: {sessionId}</span>
        </div>
        {error && (
          <div className="mt-2 text-red-400 text-sm">
            ⚠️ {error}
          </div>
        )}
      </header>

      {/* Agent Panels Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <AgentPanel
          agentName="PdfExtraction"
          displayName="PDF Extraction"
          logs={agentLogs.PdfExtraction}
          icon="📄"
        />
        <AgentPanel
          agentName="FileAnalysis"
          displayName="File Analysis"
          logs={agentLogs.FileAnalysis}
          icon="🔍"
        />
        <AgentPanel
          agentName="ImageAnalysis"
          displayName="Image Analysis"
          logs={agentLogs.ImageAnalysis}
          icon="🖼️"
        />
        <AgentPanel
          agentName="URLInvestigation"
          displayName="URL Investigation"
          logs={agentLogs.URLInvestigation}
          icon="🌐"
        />
        <AgentPanel
          agentName="ReportGenerator"
          displayName="Report Generator"
          logs={agentLogs.ReportGenerator}
          icon="📊"
        />
      </div>
    </div>
  );
}
