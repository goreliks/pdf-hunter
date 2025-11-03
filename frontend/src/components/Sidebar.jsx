import { useState } from 'react';

export default function Sidebar({ isOpen, onToggle, agentStatuses, sessionId, onAgentClick }) {
  const [activeSection, setActiveSection] = useState('pdf-extraction');

  // Handle section click
  const handleSectionClick = (section) => {
    if (section.active) {
      setActiveSection(section.id);

      // Open the modal for all sections
      if (onAgentClick) {
        const agentNames = {
          'pdf-extraction': 'PdfExtraction',
          'file-analysis': 'FileAnalysis',
          'image-analysis': 'ImageAnalysis',
          'url-investigation': 'URLInvestigation',
          'report-generator': 'ReportGenerator',
          'analysis-report': 'AnalysisReport',
          'raw-logs': 'RawLogs'
        };
        onAgentClick(agentNames[section.id]);
      }
    }
  };

  // Define sidebar sections
  const sections = [
    {
      id: 'pdf-extraction',
      name: 'PDF Extraction',
      icon: '📄',
      active: agentStatuses.PdfExtraction === 'complete',
    },
    {
      id: 'file-analysis',
      name: 'File Analysis',
      icon: '🔍',
      active: agentStatuses.FileAnalysis === 'complete',
    },
    {
      id: 'image-analysis',
      name: 'Image Analysis',
      icon: '🖼️',
      active: agentStatuses.ImageAnalysis === 'complete',
    },
    {
      id: 'url-investigation',
      name: 'URL Investigation',
      icon: '🌐',
      active: agentStatuses.URLInvestigation === 'complete',
    },
    {
      id: 'report-generator',
      name: 'Report Generator',
      icon: '📊',
      active: agentStatuses.ReportGenerator === 'complete',
    },
    {
      id: 'analysis-report',
      name: 'Final State',
      icon: '📋',
      active: agentStatuses.ReportGenerator === 'complete',
    },
    {
      id: 'raw-logs',
      name: 'Raw Logs',
      icon: '📝',
      active: agentStatuses.ReportGenerator === 'complete',
    },
  ];

  const renderContent = () => {
    switch (activeSection) {
      case 'pdf-extraction':
        return (
          <div className="space-y-4 text-center">
            <div className="text-6xl mb-4">📄</div>
            <h3 className="text-xl font-semibold text-purple-100">PDF Extraction Results</h3>
            <p className="text-purple-300/70 text-sm">
              View extracted artifacts: images, URLs, QR codes, and metadata.
            </p>
            <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-lg p-4 border border-purple-500/30 mt-4">
              <p className="text-purple-200 text-sm">
                Click this section again or press the button above to open full details in a new view.
              </p>
            </div>
          </div>
        );

      case 'file-analysis':
        return (
          <div className="space-y-4 text-center">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold text-purple-100">File Analysis Report</h3>
            <p className="text-purple-300/70 text-sm">
              Static analysis results, suspicious elements, and investigation findings.
            </p>
            <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-lg p-4 border border-purple-500/30 mt-4">
              <p className="text-purple-200 text-sm">
                Click this section to open detailed file analysis in full view.
              </p>
            </div>
          </div>
        );

      case 'image-analysis':
        return (
          <div className="space-y-4 text-center">
            <div className="text-6xl mb-4">🖼️</div>
            <h3 className="text-xl font-semibold text-purple-100">Image Analysis Report</h3>
            <p className="text-purple-300/70 text-sm">
              Visual deception analysis and findings from extracted images.
            </p>
            <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-lg p-4 border border-purple-500/30 mt-4">
              <p className="text-purple-200 text-sm">
                Click this section to open image analysis details in full view.
              </p>
            </div>
          </div>
        );

      case 'url-investigation':
        return (
          <div className="space-y-4 text-center">
            <div className="text-6xl mb-4">🌐</div>
            <h3 className="text-xl font-semibold text-purple-100">URL Investigation Report</h3>
            <p className="text-purple-300/70 text-sm">
              Browser automation results and URL analysis findings.
            </p>
            <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-lg p-4 border border-purple-500/30 mt-4">
              <p className="text-purple-200 text-sm">
                Click this section to open URL investigation results in full view.
              </p>
            </div>
          </div>
        );

      case 'report-generator':
        return (
          <div className="space-y-4 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-semibold text-purple-100">Final Report</h3>
            <p className="text-purple-300/70 text-sm">
              Comprehensive threat assessment and executive summary.
            </p>
            <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-lg p-4 border border-purple-500/30 mt-4">
              <p className="text-purple-200 text-sm">
                Click this section to open the final report in full view.
              </p>
            </div>
          </div>
        );

      case 'analysis-report':
        return (
          <div className="space-y-4 text-center">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-xl font-semibold text-purple-100">Final State</h3>
            <p className="text-purple-300/70 text-sm">
              Complete analysis final state in JSON format with download option.
            </p>
            <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-lg p-4 border border-purple-500/30 mt-4">
              <p className="text-purple-200 text-sm">
                Click this section to open the analysis final state in full view.
              </p>
            </div>
          </div>
        );

      case 'raw-logs':
        return (
          <div className="space-y-4 text-center">
            <div className="text-6xl mb-4">📝</div>
            <h3 className="text-xl font-semibold text-purple-100">Raw Logs</h3>
            <p className="text-purple-300/70 text-sm">
              Complete session logs in JSONL format with download option.
            </p>
            <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-lg p-4 border border-purple-500/30 mt-4">
              <p className="text-purple-200 text-sm">
                Click this section to open raw logs in full view.
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <>
      {/* Toggle Button - Fixed position */}
      <button
        onClick={onToggle}
        className="fixed right-0 top-1/2 -translate-y-1/2 z-50 bg-gradient-to-l from-purple-600 to-pink-600 text-white px-3 py-6 rounded-l-lg shadow-lg transition-all duration-300 hover:px-4"
        style={{
          boxShadow: '0 0 20px rgba(155, 143, 255, 0.4)',
        }}
      >
        <div className="flex flex-col items-center gap-1">
          <span className="text-xs font-semibold">{isOpen ? '›' : '‹'}</span>
        </div>
      </button>

      {/* Sidebar Panel */}
      <div
        className={`fixed right-0 top-0 h-screen bg-gray-900/95 backdrop-blur-md border-l border-purple-500/30 shadow-2xl transition-all duration-300 z-40 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        style={{
          width: '400px',
          boxShadow: isOpen ? '-10px 0 40px rgba(155, 143, 255, 0.2)' : 'none',
        }}
      >
        <div className="h-full flex flex-col">
          {/* Sidebar Header */}
          <div className="p-6 border-b border-purple-500/30">
            <h2 className="text-2xl font-bold text-purple-100 tactical-heading neon-text-purple" style={{ fontSize: '1.5rem', letterSpacing: '2px' }}>ANALYSIS DETAILS</h2>
            <p className="text-sm text-purple-300/60 mt-1 tactical-mono">View completed agent reports</p>
          </div>

          {/* Section Navigation */}
          <div className="flex-shrink-0 p-4 space-y-2 border-b border-purple-500/30">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => handleSectionClick(section)}
                disabled={!section.active}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 text-left ${
                  section.active
                    ? activeSection === section.id
                      ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                      : 'bg-gray-800/50 text-purple-100 hover:bg-gray-800'
                    : 'bg-gray-900/50 text-purple-300/40 cursor-not-allowed'
                }`}
                style={
                  section.active && activeSection === section.id
                    ? { boxShadow: '0 0 20px rgba(155, 143, 255, 0.4)' }
                    : {}
                }
              >
                <span className="text-xl">{section.icon}</span>
                <div className="flex-1">
                  <div className="text-sm font-medium tactical-mono uppercase" style={{ letterSpacing: '0.5px' }}>{section.name}</div>
                  {!section.active && (
                    <div className="text-xs text-purple-400/40 tactical-mono">Not yet complete</div>
                  )}
                </div>
                {section.active && (
                  <span className="text-purple-300/60">
                    {activeSection === section.id ? '✓' : '›'}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-6">
            {renderContent()}
          </div>
        </div>
      </div>
    </>
  );
}
