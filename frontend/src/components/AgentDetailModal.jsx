import { useEffect, useState } from 'react';
import JsonView from '@uiw/react-json-view';
import ReactMarkdown from 'react-markdown';

export default function AgentDetailModal({ agentName, sessionId, onClose }) {
  const [agentData, setAgentData] = useState({
    loading: true,
    error: null,
    data: null
  });

  // Lightbox state
  const [lightboxImage, setLightboxImage] = useState(null);

  // Fetch agent data when modal opens
  useEffect(() => {
    if (agentName && sessionId) {
      fetchAgentData(agentName, sessionId);
    }
  }, [agentName, sessionId]);

  // Handle ESC key to close modal or lightbox
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        if (lightboxImage) {
          setLightboxImage(null);
        } else {
          onClose();
        }
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onClose, lightboxImage]);

  const fetchAgentData = async (agentName, sessionId) => {
    setAgentData({ loading: true, error: null, data: null });

    try {
      if (agentName === 'PdfExtraction') {
        await fetchPdfExtractionData(sessionId);
      } else if (agentName === 'ReportGenerator') {
        await fetchReportGeneratorData(sessionId);
      } else if (agentName === 'URLInvestigation') {
        await fetchURLInvestigationData(sessionId);
      } else if (agentName === 'ImageAnalysis') {
        await fetchImageAnalysisData(sessionId);
      } else if (agentName === 'FileAnalysis') {
        await fetchFileAnalysisData(sessionId);
      } else if (agentName === 'AnalysisReport') {
        await fetchAnalysisReportData(sessionId);
      } else if (agentName === 'RawLogs') {
        await fetchRawLogsData(sessionId);
      }
    } catch (error) {
      console.error('Error fetching agent data:', error);
      setAgentData({
        loading: false,
        error: `Failed to load data: ${error.message}`,
        data: null
      });
    }
  };

  const fetchPdfExtractionData = async (sessionId) => {
    const outputPath = `/output/${sessionId}/pdf_extraction`;

    // Fetch JSON state first to get image information
    const stateResponse = await fetch(`${outputPath}/pdf_extraction_final_state_session_${sessionId}.json`);

    if (!stateResponse.ok) {
      throw new Error(`Failed to fetch state: ${stateResponse.status}`);
    }

    const stateData = await stateResponse.json();

    // Extract image paths from state (stored in extracted_images)
    // Structure: { page_number, base64_data, saved_path }
    const extractedImages = stateData.extracted_images || [];

    // Sort by page_number and create image paths
    const imagePaths = extractedImages
      .sort((a, b) => (a.page_number || 0) - (b.page_number || 0))
      .map(imageObj => {
        // Use saved_path to get the filename
        if (imageObj.saved_path) {
          const filename = imageObj.saved_path.split('/').pop();
          return `${outputPath}/${filename}`;
        }
        return null;
      })
      .filter(path => path !== null);

    setAgentData({
      loading: false,
      error: null,
      data: {
        images: imagePaths,
        state: stateData
      }
    });
  };

  const fetchReportGeneratorData = async (sessionId) => {
    const outputPath = `/output/${sessionId}/report_generator`;

    // Fetch JSON state
    const stateResponse = await fetch(`${outputPath}/final_state_session_${sessionId}.json`);

    if (!stateResponse.ok) {
      throw new Error(`Failed to fetch state: ${stateResponse.status}`);
    }

    const stateData = await stateResponse.json();

    // Fetch markdown report
    const reportResponse = await fetch(`${outputPath}/final_report_session_${sessionId}.md`);

    if (!reportResponse.ok) {
      throw new Error(`Failed to fetch report: ${reportResponse.status}`);
    }

    const reportText = await reportResponse.text();

    // Extract verdict info from final_verdict key
    const finalVerdict = stateData.final_verdict || {};

    setAgentData({
      loading: false,
      error: null,
      data: {
        verdict: finalVerdict.verdict || 'Unknown',
        confidence: finalVerdict.confidence || 0,
        reasoning: finalVerdict.reasoning || 'No reasoning available',
        reportMarkdown: reportText,
        state: stateData
      }
    });
  };

  const fetchURLInvestigationData = async (sessionId) => {
    const outputPath = `/output/${sessionId}/url_investigation`;

    // Fetch JSON state
    const stateResponse = await fetch(`${outputPath}/url_investigation_state_session_${sessionId}.json`);

    if (!stateResponse.ok) {
      throw new Error(`Failed to fetch state: ${stateResponse.status}`);
    }

    const stateData = await stateResponse.json();

    // Extract URL investigation results from link_analysis_final_reports
    const linkReports = stateData.link_analysis_final_reports || [];

    // Extract relevant fields from analyst_findings for each report
    const urlResults = linkReports.map(report => {
      const findings = report.analyst_findings || {};
      return {
        final_url: findings.final_url || 'Unknown URL',
        verdict: findings.verdict || 'Unknown',
        confidence: findings.confidence || 0,
        summary: findings.summary || 'No summary available'
      };
    });

    setAgentData({
      loading: false,
      error: null,
      data: {
        urlResults: urlResults,
        state: stateData
      }
    });
  };

  const fetchImageAnalysisData = async (sessionId) => {
    const outputPath = `/output/${sessionId}/image_analysis`;

    // Fetch JSON state
    const stateResponse = await fetch(`${outputPath}/image_analysis_state_session_${sessionId}.json`);

    if (!stateResponse.ok) {
      throw new Error(`Failed to fetch state: ${stateResponse.status}`);
    }

    const stateData = await stateResponse.json();

    // Extract overall verdict, confidence, and executive summary
    const overallVerdict = stateData.overall_verdict || 'Unknown';
    const overallConfidence = stateData.overall_confidence || 0;
    const executiveSummary = stateData.executive_summary || 'No summary available';
    const documentFlowSummary = stateData.document_flow_summary || 'No document flow summary available';

    // Get images from pdf_extraction state
    const pdfExtractionPath = `/output/${sessionId}/pdf_extraction`;

    // Fetch PDF extraction state to get the actual extracted images
    const pdfStateResponse = await fetch(`${pdfExtractionPath}/pdf_extraction_final_state_session_${sessionId}.json`);

    let imagePaths = [];
    if (pdfStateResponse.ok) {
      const pdfStateData = await pdfStateResponse.json();
      const extractedImages = pdfStateData.extracted_images || [];

      // Structure: { page_number, base64_data, saved_path }
      imagePaths = extractedImages
        .sort((a, b) => (a.page_number || 0) - (b.page_number || 0))
        .map(imageObj => {
          // Use saved_path to get the filename
          if (imageObj.saved_path) {
            const filename = imageObj.saved_path.split('/').pop();
            return `${pdfExtractionPath}/${filename}`;
          }
          return null;
        })
        .filter(path => path !== null);
    }

    setAgentData({
      loading: false,
      error: null,
      data: {
        overallVerdict: overallVerdict,
        overallConfidence: overallConfidence,
        executiveSummary: executiveSummary,
        documentFlowSummary: documentFlowSummary,
        images: imagePaths,
        state: stateData
      }
    });
  };

  const fetchFileAnalysisData = async (sessionId) => {
    // Load File Analysis specific state JSON (available as soon as FileAnalysis completes)
    const outputPath = `/output/${sessionId}/file_analysis`;
    const filePath = `${outputPath}/file_analysis_final_state_session_${sessionId}.json`;

    // Fetch JSON state
    const stateResponse = await fetch(filePath);

    if (!stateResponse.ok) {
      throw new Error(`File Analysis hasn't completed yet. The final state file will be created when File Analysis finishes. (Status: ${stateResponse.status})`);
    }

    const contentType = stateResponse.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error(`Expected JSON but got ${contentType}. File Analysis may still be running.`);
    }

    const stateData = await stateResponse.json();

    // Extract triage classification
    const triageDecision = stateData.triage_classification_decision || 'Unknown';
    const triageReasoning = stateData.triage_classification_reasoning || 'No reasoning available';

    // Extract structural summary sections
    const structuralSummary = stateData.structural_summary || {};
    const pdfid = structuralSummary.pdfid || 'No PDFiD data available';
    const pdfParser = structuralSummary.pdf_parser || 'No PDF Parser data available';
    const peepdf = structuralSummary.peepdf || 'No Peepdf data available';
    const xmpMetadata = structuralSummary.xmp_metadata || 'No XMP metadata available';

    // Extract static analysis final report
    const staticAnalysisReport = stateData.static_analysis_final_report || {};
    const finalVerdict = staticAnalysisReport.final_verdict || 'Unknown';
    const executiveSummary = staticAnalysisReport.executive_summary || 'No summary available';

    setAgentData({
      loading: false,
      error: null,
      data: {
        triageDecision: triageDecision,
        triageReasoning: triageReasoning,
        pdfid: pdfid,
        pdfParser: pdfParser,
        peepdf: peepdf,
        xmpMetadata: xmpMetadata,
        finalVerdict: finalVerdict,
        executiveSummary: executiveSummary,
        state: stateData
      }
    });
  };

  const fetchAnalysisReportData = async (sessionId) => {
    const outputPath = `/output/${sessionId}`;
    const filePath = `${outputPath}/analysis_report_session_${sessionId}.json`;

    // Fetch JSON state
    const stateResponse = await fetch(filePath);

    if (!stateResponse.ok) {
      throw new Error(`Failed to fetch analysis report at ${filePath}: ${stateResponse.status} ${stateResponse.statusText}`);
    }

    const stateData = await stateResponse.json();

    setAgentData({
      loading: false,
      error: null,
      data: {
        state: stateData
      }
    });
  };

  const fetchRawLogsData = async (sessionId) => {
    const logsPath = `/output/${sessionId}/logs/session.jsonl`;

    // Fetch JSONL logs
    const response = await fetch(logsPath);

    if (!response.ok) {
      throw new Error(`Failed to fetch logs: ${response.status}`);
    }

    const rawLogs = await response.text();

    setAgentData({
      loading: false,
      error: null,
      data: {
        rawLogs: rawLogs
      }
    });
  };

  const getAgentDisplayName = (name) => {
    const names = {
      PdfExtraction: 'PDF Extraction',
      FileAnalysis: 'File Analysis',
      ImageAnalysis: 'Image Analysis',
      URLInvestigation: 'URL Investigation',
      ReportGenerator: 'Report Generator',
      AnalysisReport: 'Final State',
      RawLogs: 'Raw Logs'
    };
    return names[name] || name;
  };

  const getAgentIcon = (name) => {
    const icons = {
      PdfExtraction: '📄',
      FileAnalysis: '🔍',
      ImageAnalysis: '🖼️',
      URLInvestigation: '🌐',
      ReportGenerator: '📊',
      AnalysisReport: '📋',
      RawLogs: '📝'
    };
    return icons[name] || '📋';
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 animate-fadeIn"
        onClick={onClose}
      />

      {/* Modal Overlay - Slides in from right */}
      <div className="fixed inset-y-0 right-0 w-full md:w-4/5 lg:w-3/4 xl:w-2/3 z-50 animate-slideInRight">
        {/* Modal Content */}
        <div className="h-full bg-gradient-to-br from-blackalgo-bg-dark via-gray-900 to-blackalgo-bg-dark border-l-2 border-purple-500/30 shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gray-900/80 backdrop-blur-sm border-b border-purple-500/30 p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-4xl">{getAgentIcon(agentName)}</span>
                <div>
                  <h2 className="text-3xl font-bold text-purple-100">
                    {getAgentDisplayName(agentName)}
                  </h2>
                  <p className="text-sm text-purple-300/60 mt-1">
                    Session: {sessionId}
                  </p>
                </div>
              </div>

              {/* Close Button */}
              <button
                onClick={onClose}
                className="group p-3 rounded-lg transition-all duration-200 hover:bg-purple-900/30"
                title="Close (ESC)"
              >
                <svg
                  className="w-8 h-8 text-purple-300 group-hover:text-purple-100 transition-colors"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* Content Area */}
          <div className="h-[calc(100%-88px)] overflow-y-auto p-8">
            {/* Loading State */}
            {agentData.loading && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-16 w-16 border-4 border-purple-500 border-t-transparent mx-auto mb-4" />
                  <p className="text-purple-200 text-lg">Loading agent data...</p>
                </div>
              </div>
            )}

            {/* Error State */}
            {agentData.error && (
              <div className="flex items-center justify-center h-full">
                <div className="bg-red-900/20 rounded-lg p-6 border border-red-500/30 max-w-md">
                  <p className="text-red-300 text-center">{agentData.error}</p>
                </div>
              </div>
            )}

            {/* PDF Extraction Content */}
            {!agentData.loading && !agentData.error && agentData.data && agentName === 'PdfExtraction' && (
              <div className="space-y-8">
                {/* Page Screenshots Section */}
                <div>
                  <h3 className="text-2xl font-semibold text-purple-100 mb-4 flex items-center gap-3">
                    <span className="text-3xl">🖼️</span>
                    Page Screenshots
                  </h3>
                  <div className="flex flex-wrap gap-6">
                    {agentData.data.images.map((imagePath, index) => (
                      <div
                        key={index}
                        className="bg-gray-900/50 rounded-lg p-4 border border-purple-500/20 hover:border-purple-500/40 transition-all hover:scale-105 cursor-pointer"
                        onClick={() => setLightboxImage(imagePath)}
                        title="Click to view full size"
                      >
                        <img
                          src={imagePath}
                          alt={`Page ${index}`}
                          className="max-w-[250px] max-h-[350px] object-contain rounded shadow-lg"
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'flex';
                          }}
                        />
                        <div
                          style={{ display: 'none' }}
                          className="flex items-center justify-center w-[250px] h-[350px] text-purple-300/60 text-sm bg-gray-800/50 rounded"
                        >
                          Failed to load image
                        </div>
                        <p className="text-purple-300/70 text-sm text-center mt-3 font-semibold">
                          Page {index}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* JSON State Section */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-semibold text-purple-100 flex items-center gap-3">
                      <span className="text-3xl">📋</span>
                      Extraction State
                    </h3>
                    <button
                      onClick={() => {
                        const dataStr = JSON.stringify(agentData.data.state, null, 2);
                        const blob = new Blob([dataStr], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = `pdf_extraction_state_${sessionId}.json`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(url);
                      }}
                      className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg text-sm font-medium transition-all duration-200 hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/50 hover:scale-105"
                      title="Download JSON state"
                    >
                      Download State
                    </button>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20 text-left">
                    <JsonView
                      value={agentData.data.state}
                      collapsed={false}
                      displayDataTypes={true}
                      displayObjectSize={true}
                      enableClipboard={true}
                      style={{
                        '--w-rjv-background-color': 'transparent',
                        '--w-rjv-color': '#e9d5ff',
                        '--w-rjv-key-string': '#d8b4fe',
                        '--w-rjv-arrow-color': '#9333ea',
                        '--w-rjv-info-color': '#d8b4fe80',
                        '--w-rjv-quotes-color': '#c084fc',
                        '--w-rjv-quotes-string-color': '#00ffd1',
                        '--w-rjv-type-string-color': '#00ffd1',
                        '--w-rjv-type-int-color': '#f472b6',
                        '--w-rjv-type-float-color': '#f472b6',
                        '--w-rjv-type-boolean-color': '#a855f6',
                        '--w-rjv-type-null-color': '#9333ea',
                        '--w-rjv-type-url-color': '#00ffd1',
                        '--w-rjv-curlybraces-color': '#d8b4fe',
                        '--w-rjv-colon-color': '#d8b4fe',
                        '--w-rjv-brackets-color': '#d8b4fe',
                        fontFamily: '"Share Tech Mono", monospace',
                        fontSize: '13px',
                        lineHeight: '1.6'
                      }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Report Generator Content */}
            {!agentData.loading && !agentData.error && agentData.data && agentName === 'ReportGenerator' && (
              <div className="space-y-8">
                {/* Verdict Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Verdict Card */}
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20">
                    <h3 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-2">
                      Verdict
                    </h3>
                    <p className={`text-3xl font-bold ${
                      agentData.data.verdict === 'Malicious' ? 'text-rose-400' :
                      agentData.data.verdict === 'Suspicious' ? 'text-amber-400' :
                      agentData.data.verdict === 'Benign' ? 'text-emerald-400' :
                      'text-purple-300'
                    }`}>
                      {agentData.data.verdict}
                    </p>
                  </div>

                  {/* Confidence Card */}
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20">
                    <h3 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-2">
                      Confidence
                    </h3>
                    <p className="text-3xl font-bold text-pink-400">
                      {(agentData.data.confidence * 100).toFixed(1)}%
                    </p>
                  </div>

                  {/* Reasoning Preview */}
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20">
                    <h3 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-2">
                      Analysis Type
                    </h3>
                    <p className="text-lg font-semibold text-cyan-400">
                      Threat Assessment
                    </p>
                  </div>
                </div>

                {/* Reasoning Section */}
                <div>
                  <h3 className="text-2xl font-semibold text-purple-100 mb-4 flex items-center gap-3">
                    <span className="text-3xl">💭</span>
                    Reasoning
                  </h3>
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20">
                    <p className="text-purple-200 leading-relaxed">
                      {agentData.data.reasoning}
                    </p>
                  </div>
                </div>

                {/* Markdown Report Section */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-semibold text-purple-100 flex items-center gap-3">
                      <span className="text-3xl">📄</span>
                      Analysis Report
                    </h3>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => {
                          const blob = new Blob([agentData.data.reportMarkdown], { type: 'text/markdown' });
                          const url = URL.createObjectURL(blob);
                          const link = document.createElement('a');
                          link.href = url;
                          link.download = `final_report_${sessionId}.md`;
                          document.body.appendChild(link);
                          link.click();
                          document.body.removeChild(link);
                          URL.revokeObjectURL(url);
                        }}
                        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg text-sm font-medium transition-all duration-200 hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/50 hover:scale-105"
                        title="Download markdown report"
                      >
                        Download Report
                      </button>
                      <button
                        onClick={() => {
                          document.getElementById('report-state-section')?.scrollIntoView({ behavior: 'smooth' });
                        }}
                        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg text-sm font-medium transition-all duration-200 hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/50 hover:scale-105"
                        title="Jump to Report State"
                      >
                        Jump to State ↓
                      </button>
                    </div>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20 prose prose-invert prose-purple max-w-none text-left">
                    <ReactMarkdown
                      components={{
                        h1: ({node, ...props}) => <h1 className="text-3xl font-bold text-purple-100 mb-4" {...props} />,
                        h2: ({node, ...props}) => <h2 className="text-2xl font-bold text-purple-200 mb-3 mt-6" {...props} />,
                        h3: ({node, ...props}) => <h3 className="text-xl font-semibold text-purple-300 mb-2 mt-4" {...props} />,
                        p: ({node, ...props}) => <p className="text-purple-200 mb-4 leading-relaxed" {...props} />,
                        ul: ({node, ...props}) => <ul className="list-disc list-inside text-purple-200 mb-4 space-y-2" {...props} />,
                        ol: ({node, ...props}) => <ol className="list-decimal list-inside text-purple-200 mb-4 space-y-2" {...props} />,
                        li: ({node, ...props}) => <li className="text-purple-200" {...props} />,
                        strong: ({node, ...props}) => <strong className="text-pink-400 font-semibold" {...props} />,
                        em: ({node, ...props}) => <em className="text-cyan-400 italic" {...props} />,
                        code: ({node, inline, ...props}) =>
                          inline ?
                            <code className="bg-purple-900/30 text-cyan-400 px-2 py-1 rounded text-sm font-mono" {...props} /> :
                            <code className="block bg-purple-900/30 text-cyan-400 p-4 rounded text-sm font-mono overflow-x-auto" {...props} />,
                        blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-purple-500 pl-4 italic text-purple-300/80 my-4" {...props} />,
                      }}
                    >
                      {agentData.data.reportMarkdown}
                    </ReactMarkdown>
                  </div>
                </div>

                {/* JSON State Section */}
                <div id="report-state-section">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-semibold text-purple-100 flex items-center gap-3">
                      <span className="text-3xl">📋</span>
                      Report State
                    </h3>
                    <button
                      onClick={() => {
                        const dataStr = JSON.stringify(agentData.data.state, null, 2);
                        const blob = new Blob([dataStr], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = `report_generator_state_${sessionId}.json`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(url);
                      }}
                      className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg text-sm font-medium transition-all duration-200 hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/50 hover:scale-105"
                      title="Download JSON state"
                    >
                      Download State
                    </button>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20 text-left">
                    <JsonView
                      value={agentData.data.state}
                      collapsed={false}
                      displayDataTypes={true}
                      displayObjectSize={true}
                      enableClipboard={true}
                      style={{
                        '--w-rjv-background-color': 'transparent',
                        '--w-rjv-color': '#e9d5ff',
                        '--w-rjv-key-string': '#d8b4fe',
                        '--w-rjv-arrow-color': '#9333ea',
                        '--w-rjv-info-color': '#d8b4fe80',
                        '--w-rjv-quotes-color': '#c084fc',
                        '--w-rjv-quotes-string-color': '#00ffd1',
                        '--w-rjv-type-string-color': '#00ffd1',
                        '--w-rjv-type-int-color': '#f472b6',
                        '--w-rjv-type-float-color': '#f472b6',
                        '--w-rjv-type-boolean-color': '#a855f6',
                        '--w-rjv-type-null-color': '#9333ea',
                        '--w-rjv-type-url-color': '#00ffd1',
                        '--w-rjv-curlybraces-color': '#d8b4fe',
                        '--w-rjv-colon-color': '#d8b4fe',
                        '--w-rjv-brackets-color': '#d8b4fe',
                        fontFamily: '"Share Tech Mono", monospace',
                        fontSize: '13px',
                        lineHeight: '1.6'
                      }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* URL Investigation Content */}
            {!agentData.loading && !agentData.error && agentData.data && agentName === 'URLInvestigation' && (
              <div className="space-y-8">
                {/* URL Investigation Results */}
                <div>
                  <h3 className="text-2xl font-semibold text-purple-100 mb-4 flex items-center gap-3">
                    <span className="text-3xl">🔗</span>
                    URL Investigation Results
                  </h3>
                  <div className="space-y-4">
                    {agentData.data.urlResults.map((result, index) => (
                      <div
                        key={index}
                        className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20 hover:border-purple-500/40 transition-all"
                      >
                        {/* URL */}
                        <div className="mb-4">
                          <h4 className="text-xs text-purple-300/70 uppercase tracking-wider mb-2">URL</h4>
                          <p className="text-cyan-400 text-sm font-mono break-all">
                            {result.final_url}
                          </p>
                        </div>

                        {/* Verdict and Confidence */}
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          <div>
                            <h4 className="text-xs text-purple-300/70 uppercase tracking-wider mb-2">Verdict</h4>
                            <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                              result.verdict === 'Malicious' ? 'bg-rose-900/30 text-rose-400 border border-rose-500/30' :
                              result.verdict === 'Suspicious' ? 'bg-amber-900/30 text-amber-400 border border-amber-500/30' :
                              result.verdict === 'Benign' ? 'bg-emerald-900/30 text-emerald-400 border border-emerald-500/30' :
                              'bg-purple-900/30 text-purple-400 border border-purple-500/30'
                            }`}>
                              {result.verdict}
                            </span>
                          </div>
                          <div>
                            <h4 className="text-xs text-purple-300/70 uppercase tracking-wider mb-2">Confidence</h4>
                            <p className="text-pink-400 text-lg font-bold">
                              {(result.confidence * 100).toFixed(1)}%
                            </p>
                          </div>
                        </div>

                        {/* Summary */}
                        <div>
                          <h4 className="text-xs text-purple-300/70 uppercase tracking-wider mb-2">Summary</h4>
                          <p className="text-purple-200 text-sm leading-relaxed whitespace-pre-wrap">
                            {result.summary}
                          </p>
                        </div>
                      </div>
                    ))}
                    {agentData.data.urlResults.length === 0 && (
                      <div className="bg-gray-900/50 rounded-lg p-8 border border-purple-500/20 text-center">
                        <p className="text-purple-300/60">No URL investigation results found</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* JSON State Section */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-semibold text-purple-100 flex items-center gap-3">
                      <span className="text-3xl">📋</span>
                      Investigation State
                    </h3>
                    <button
                      onClick={() => {
                        const dataStr = JSON.stringify(agentData.data.state, null, 2);
                        const blob = new Blob([dataStr], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = `url_investigation_state_${sessionId}.json`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(url);
                      }}
                      className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg text-sm font-medium transition-all duration-200 hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/50 hover:scale-105"
                      title="Download JSON state"
                    >
                      Download State
                    </button>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20 text-left">
                    <JsonView
                      value={agentData.data.state}
                      collapsed={false}
                      displayDataTypes={true}
                      displayObjectSize={true}
                      enableClipboard={true}
                      style={{
                        '--w-rjv-background-color': 'transparent',
                        '--w-rjv-color': '#e9d5ff',
                        '--w-rjv-key-string': '#d8b4fe',
                        '--w-rjv-arrow-color': '#9333ea',
                        '--w-rjv-info-color': '#d8b4fe80',
                        '--w-rjv-quotes-color': '#c084fc',
                        '--w-rjv-quotes-string-color': '#00ffd1',
                        '--w-rjv-type-string-color': '#00ffd1',
                        '--w-rjv-type-int-color': '#f472b6',
                        '--w-rjv-type-float-color': '#f472b6',
                        '--w-rjv-type-boolean-color': '#a855f6',
                        '--w-rjv-type-null-color': '#9333ea',
                        '--w-rjv-type-url-color': '#00ffd1',
                        '--w-rjv-curlybraces-color': '#d8b4fe',
                        '--w-rjv-colon-color': '#d8b4fe',
                        '--w-rjv-brackets-color': '#d8b4fe',
                        fontFamily: '"Share Tech Mono", monospace',
                        fontSize: '13px',
                        lineHeight: '1.6'
                      }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Image Analysis Content */}
            {!agentData.loading && !agentData.error && agentData.data && agentName === 'ImageAnalysis' && (
              <div className="space-y-8">
                {/* Page Screenshots Section - MOVED TO TOP */}
                <div>
                  <h3 className="text-2xl font-semibold text-purple-100 mb-4 flex items-center gap-3">
                    <span className="text-3xl">🖼️</span>
                    Analyzed Pages
                  </h3>
                  <div className="flex flex-wrap gap-6">
                    {agentData.data.images.map((imagePath, index) => (
                      <div
                        key={index}
                        className="bg-gray-900/50 rounded-lg p-4 border border-purple-500/20 hover:border-purple-500/40 transition-all hover:scale-105 cursor-pointer"
                        onClick={() => setLightboxImage(imagePath)}
                        title="Click to view full size"
                      >
                        <img
                          src={imagePath}
                          alt={`Page ${index}`}
                          className="max-w-[250px] max-h-[350px] object-contain rounded shadow-lg"
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'flex';
                          }}
                        />
                        <div
                          style={{ display: 'none' }}
                          className="flex items-center justify-center w-[250px] h-[350px] text-purple-300/60 text-sm bg-gray-800/50 rounded"
                        >
                          Failed to load image
                        </div>
                        <p className="text-purple-300/70 text-sm text-center mt-3 font-semibold">
                          Page {index}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Overall Summary Section */}
                <div>
                  <h3 className="text-2xl font-semibold text-purple-100 mb-4 flex items-center gap-3">
                    <span className="text-3xl">📊</span>
                    Visual Analysis Summary
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    {/* Verdict Card */}
                    <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20">
                      <h4 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-2">
                        Overall Verdict
                      </h4>
                      <p className={`text-3xl font-bold ${
                        agentData.data.overallVerdict === 'Highly Deceptive' ? 'text-rose-400' :
                        agentData.data.overallVerdict === 'Suspicious' ? 'text-amber-400' :
                        agentData.data.overallVerdict === 'Benign' ? 'text-emerald-400' :
                        'text-purple-300'
                      }`}>
                        {agentData.data.overallVerdict}
                      </p>
                    </div>

                    {/* Confidence Card */}
                    <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20">
                      <h4 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-2">
                        Overall Confidence
                      </h4>
                      <p className="text-3xl font-bold text-pink-400">
                        {(agentData.data.overallConfidence * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  {/* Executive Summary */}
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20">
                    <h4 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-3">
                      Executive Summary
                    </h4>
                    <p className="text-purple-200 leading-relaxed whitespace-pre-wrap">
                      {agentData.data.executiveSummary}
                    </p>
                  </div>

                  {/* Document Flow Summary */}
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20">
                    <h4 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-3">
                      Document Flow Summary
                    </h4>
                    <p className="text-purple-200 leading-relaxed whitespace-pre-wrap">
                      {agentData.data.documentFlowSummary}
                    </p>
                  </div>
                </div>

                {/* JSON State Section */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-semibold text-purple-100 flex items-center gap-3">
                      <span className="text-3xl">📋</span>
                      Analysis State
                    </h3>
                    <button
                      onClick={() => {
                        const dataStr = JSON.stringify(agentData.data.state, null, 2);
                        const blob = new Blob([dataStr], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = `image_analysis_state_${sessionId}.json`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(url);
                      }}
                      className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg text-sm font-medium transition-all duration-200 hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/50 hover:scale-105"
                      title="Download JSON state"
                    >
                      Download State
                    </button>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20 text-left">
                    <JsonView
                      value={agentData.data.state}
                      collapsed={false}
                      displayDataTypes={true}
                      displayObjectSize={true}
                      enableClipboard={true}
                      style={{
                        '--w-rjv-background-color': 'transparent',
                        '--w-rjv-color': '#e9d5ff',
                        '--w-rjv-key-string': '#d8b4fe',
                        '--w-rjv-arrow-color': '#9333ea',
                        '--w-rjv-info-color': '#d8b4fe80',
                        '--w-rjv-quotes-color': '#c084fc',
                        '--w-rjv-quotes-string-color': '#00ffd1',
                        '--w-rjv-type-string-color': '#00ffd1',
                        '--w-rjv-type-int-color': '#f472b6',
                        '--w-rjv-type-float-color': '#f472b6',
                        '--w-rjv-type-boolean-color': '#a855f6',
                        '--w-rjv-type-null-color': '#9333ea',
                        '--w-rjv-type-url-color': '#00ffd1',
                        '--w-rjv-curlybraces-color': '#d8b4fe',
                        '--w-rjv-colon-color': '#d8b4fe',
                        '--w-rjv-brackets-color': '#d8b4fe',
                        fontFamily: '"Share Tech Mono", monospace',
                        fontSize: '13px',
                        lineHeight: '1.6'
                      }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* File Analysis Content */}
            {!agentData.loading && !agentData.error && agentData.data && agentName === 'FileAnalysis' && (
              <div className="space-y-8">
                {/* Triage Classification */}
                <div>
                  <h3 className="text-2xl font-semibold text-purple-100 mb-4 flex items-center gap-3">
                    <span className="text-3xl">🎯</span>
                    Triage Classification
                  </h3>
                  <div className="space-y-4">
                    <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20">
                      <h4 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-2">
                        Decision
                      </h4>
                      <p className="text-xl font-bold text-cyan-400">
                        {agentData.data.triageDecision}
                      </p>
                    </div>
                    <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20">
                      <h4 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-3">
                        Reasoning
                      </h4>
                      <p className="text-purple-200 leading-relaxed whitespace-pre-wrap">
                        {agentData.data.triageReasoning}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Structural Summary */}
                <div>
                  <h3 className="text-2xl font-semibold text-purple-100 mb-4 flex items-center gap-3">
                    <span className="text-3xl">🔬</span>
                    Structural Summary
                  </h3>
                  <div className="space-y-4">
                    {/* PDFiD */}
                    <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20 text-left">
                      <h4 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-3">
                        PDFiD Analysis
                      </h4>
                      <pre className="text-purple-200 text-xs font-mono leading-relaxed whitespace-pre-wrap overflow-x-auto text-left">
                        {agentData.data.pdfid}
                      </pre>
                    </div>

                    {/* PDF Parser */}
                    <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20 text-left">
                      <h4 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-3">
                        PDF Parser Analysis
                      </h4>
                      <pre className="text-purple-200 text-xs font-mono leading-relaxed whitespace-pre-wrap overflow-x-auto text-left">
                        {agentData.data.pdfParser}
                      </pre>
                    </div>

                    {/* Peepdf */}
                    <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20 text-left">
                      <h4 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-3">
                        Peepdf Analysis
                      </h4>
                      <pre className="text-purple-200 text-xs font-mono leading-relaxed whitespace-pre-wrap overflow-x-auto text-left">
                        {agentData.data.peepdf}
                      </pre>
                    </div>

                    {/* XMP Metadata */}
                    <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20 text-left">
                      <h4 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-3">
                        XMP Metadata
                      </h4>
                      <pre className="text-purple-200 text-xs font-mono leading-relaxed whitespace-pre-wrap overflow-x-auto text-left">
                        {agentData.data.xmpMetadata}
                      </pre>
                    </div>
                  </div>
                </div>

                {/* File Analysis */}
                <div>
                  <h3 className="text-2xl font-semibold text-purple-100 mb-4 flex items-center gap-3">
                    <span className="text-3xl">📊</span>
                    File Analysis
                  </h3>
                  <div className="space-y-4">
                    <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20">
                      <h4 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-2">
                        Final Verdict
                      </h4>
                      <p className={`text-2xl font-bold ${
                        agentData.data.finalVerdict === 'Malicious' ? 'text-rose-400' :
                        agentData.data.finalVerdict === 'Suspicious' ? 'text-amber-400' :
                        agentData.data.finalVerdict === 'Benign' ? 'text-emerald-400' :
                        'text-purple-300'
                      }`}>
                        {agentData.data.finalVerdict}
                      </p>
                    </div>
                    <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20">
                      <h4 className="text-sm font-semibold text-purple-300/70 uppercase tracking-wider mb-3">
                        Executive Summary
                      </h4>
                      <p className="text-purple-200 leading-relaxed whitespace-pre-wrap">
                        {agentData.data.executiveSummary}
                      </p>
                    </div>
                  </div>
                </div>

                {/* JSON State Section */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-semibold text-purple-100 flex items-center gap-3">
                      <span className="text-3xl">📋</span>
                      Analysis State
                    </h3>
                    <button
                      onClick={() => {
                        const dataStr = JSON.stringify(agentData.data.state, null, 2);
                        const blob = new Blob([dataStr], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = `file_analysis_state_${sessionId}.json`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(url);
                      }}
                      className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg text-sm font-medium transition-all duration-200 hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/50 hover:scale-105"
                      title="Download JSON state"
                    >
                      Download State
                    </button>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20 text-left">
                    <JsonView
                      value={agentData.data.state}
                      collapsed={false}
                      displayDataTypes={true}
                      displayObjectSize={true}
                      enableClipboard={true}
                      style={{
                        '--w-rjv-background-color': 'transparent',
                        '--w-rjv-color': '#e9d5ff',
                        '--w-rjv-key-string': '#d8b4fe',
                        '--w-rjv-arrow-color': '#9333ea',
                        '--w-rjv-info-color': '#d8b4fe80',
                        '--w-rjv-quotes-color': '#c084fc',
                        '--w-rjv-quotes-string-color': '#00ffd1',
                        '--w-rjv-type-string-color': '#00ffd1',
                        '--w-rjv-type-int-color': '#f472b6',
                        '--w-rjv-type-float-color': '#f472b6',
                        '--w-rjv-type-boolean-color': '#a855f6',
                        '--w-rjv-type-null-color': '#9333ea',
                        '--w-rjv-type-url-color': '#00ffd1',
                        '--w-rjv-curlybraces-color': '#d8b4fe',
                        '--w-rjv-colon-color': '#d8b4fe',
                        '--w-rjv-brackets-color': '#d8b4fe',
                        fontFamily: '"Share Tech Mono", monospace',
                        fontSize: '13px',
                        lineHeight: '1.6'
                      }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Analysis Report Content */}
            {!agentData.loading && !agentData.error && agentData.data && agentName === 'AnalysisReport' && (
              <div className="space-y-8">
                {/* JSON State Section */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-semibold text-purple-100 flex items-center gap-3">
                      <span className="text-3xl">📋</span>
                      Analysis Final State
                    </h3>
                    <button
                      onClick={() => {
                        const dataStr = JSON.stringify(agentData.data.state, null, 2);
                        const blob = new Blob([dataStr], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = `analysis_report_session_${sessionId}.json`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(url);
                      }}
                      className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg text-sm font-medium transition-all duration-200 hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/50 hover:scale-105"
                      title="Download JSON state"
                    >
                      Download State
                    </button>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20 text-left">
                    <JsonView
                      value={agentData.data.state}
                      collapsed={false}
                      displayDataTypes={true}
                      displayObjectSize={true}
                      enableClipboard={true}
                      style={{
                        '--w-rjv-background-color': 'transparent',
                        '--w-rjv-color': '#e9d5ff',
                        '--w-rjv-key-string': '#d8b4fe',
                        '--w-rjv-arrow-color': '#9333ea',
                        '--w-rjv-info-color': '#d8b4fe80',
                        '--w-rjv-quotes-color': '#c084fc',
                        '--w-rjv-quotes-string-color': '#00ffd1',
                        '--w-rjv-type-string-color': '#00ffd1',
                        '--w-rjv-type-int-color': '#f472b6',
                        '--w-rjv-type-float-color': '#f472b6',
                        '--w-rjv-type-boolean-color': '#a855f6',
                        '--w-rjv-type-null-color': '#9333ea',
                        '--w-rjv-type-url-color': '#00ffd1',
                        '--w-rjv-curlybraces-color': '#d8b4fe',
                        '--w-rjv-colon-color': '#d8b4fe',
                        '--w-rjv-brackets-color': '#d8b4fe',
                        fontFamily: '"Share Tech Mono", monospace',
                        fontSize: '13px',
                        lineHeight: '1.6'
                      }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Raw Logs Content */}
            {!agentData.loading && !agentData.error && agentData.data && agentName === 'RawLogs' && (
              <div className="space-y-8">
                {/* Raw Logs Section */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-semibold text-purple-100 flex items-center gap-3">
                      <span className="text-3xl">📝</span>
                      Session Logs
                    </h3>
                    <button
                      onClick={() => {
                        const blob = new Blob([agentData.data.rawLogs], { type: 'application/x-ndjson' });
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = `session_${sessionId}.jsonl`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(url);
                      }}
                      className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg text-sm font-medium transition-all duration-200 hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/50 hover:scale-105"
                      title="Download JSONL logs"
                    >
                      Download Logs
                    </button>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-6 border border-purple-500/20 text-left">
                    <pre className="text-purple-200 text-xs font-mono leading-relaxed whitespace-pre overflow-x-auto max-h-[70vh] overflow-y-auto text-left">
                      {agentData.data.rawLogs}
                    </pre>
                  </div>
                </div>
              </div>
            )}

            {/* Placeholder for other agents */}
            {!agentData.loading && !agentData.error && agentName !== 'PdfExtraction' && agentName !== 'ReportGenerator' && agentName !== 'URLInvestigation' && agentName !== 'ImageAnalysis' && agentName !== 'FileAnalysis' && agentName !== 'AnalysisReport' && agentName !== 'RawLogs' && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <span className="text-6xl mb-4 block">{getAgentIcon(agentName)}</span>
                  <p className="text-purple-200 text-xl mb-2">
                    {getAgentDisplayName(agentName)} Details
                  </p>
                  <p className="text-purple-300/60">
                    Content viewer coming soon...
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Lightbox for full-size images */}
      {lightboxImage && (
        <>
          {/* Lightbox Backdrop */}
          <div
            className="fixed inset-0 bg-black/90 z-[60] animate-fadeIn flex items-center justify-center p-8"
            onClick={() => setLightboxImage(null)}
          >
            {/* Close button */}
            <button
              className="absolute top-8 right-8 p-3 rounded-lg bg-purple-600/20 hover:bg-purple-600/40 transition-all duration-200 group"
              onClick={() => setLightboxImage(null)}
              title="Close (ESC)"
            >
              <svg
                className="w-8 h-8 text-purple-100"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>

            {/* Full-size image */}
            <img
              src={lightboxImage}
              alt="Full size view"
              className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </>
      )}
    </>
  );
}
