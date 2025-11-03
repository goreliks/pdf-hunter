import { useState, useRef } from 'react';
import { API_BASE_URL } from '../config/api';

const LandingPage = ({ onAnalysisStart }) => {
  const [file, setFile] = useState(null);
  const [maxPages, setMaxPages] = useState(2);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [devMode, setDevMode] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile);
      setError('');
    } else {
      setError('Please drop a PDF file');
    }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError('');
    } else {
      setError('Please select a PDF file');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setIsUploading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('max_pages', maxPages.toString());

      const apiUrl = `${API_BASE_URL}/api/analyze`;

      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMessage;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || `Server error: ${response.status} ${response.statusText}`;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();

      // Start the analysis with the session ID
      onAnalysisStart({
        sessionId: data.session_id,
        streamUrl: data.stream_url,
        statusUrl: data.status_url,
        filename: file.name,
        devMode: false  // Real analysis, not dev mode
      });
    } catch (err) {
      console.error('Upload error:', err);

      // Provide more specific error messages
      let errorMessage = err.message;
      if (err.message === 'Failed to fetch') {
        errorMessage = `Cannot connect to backend server at ${API_BASE_URL}. Make sure the backend is running on port 8000.`;
      }

      setError(errorMessage);
      setIsUploading(false);
    }
  };

  const handleDevMode = () => {
    // Start dev mode with mock data
    onAnalysisStart({
      sessionId: '242fc6a46e4b36fcc00a3cfaabefe29a8cf8a5c9_20251029_181451',  // Must match output folder name
      streamUrl: null,  // No real stream URL in dev mode
      statusUrl: null,
      filename: 'mock-analysis.pdf',
      devMode: true  // Enable dev mode
    });
  };

  return (
    <div className="min-h-screen relative overflow-hidden gradient-bg">
      {/* Nebula Background */}
      <div className="nebula-bg"></div>

      {/* Cosmic Particles */}
      <div className="cosmic-particles">
        {/* Generate floating particles */}
        {[...Array(30)].map((_, i) => (
          <div
            key={`particle-${i}`}
            className="particle"
            style={{
              left: `${Math.random() * 100}%`,
              animationDuration: `${15 + Math.random() * 15}s`,
              animationDelay: `${Math.random() * 10}s`,
            }}
          />
        ))}
        {/* Generate twinkling stars */}
        {[...Array(50)].map((_, i) => (
          <div
            key={`star-${i}`}
            className="star"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`,
            }}
          />
        ))}
        {/* Generate cosmic rays */}
        {[...Array(5)].map((_, i) => (
          <div
            key={`ray-${i}`}
            className="cosmic-ray"
            style={{
              top: `${Math.random() * 100}%`,
              width: `${300 + Math.random() * 200}px`,
              animationDuration: `${3 + Math.random() * 2}s`,
              animationDelay: `${Math.random() * 5}s`,
            }}
          />
        ))}
      </div>

      {/* Dev Mode Toggle - Subtle (Outside landing-centered for absolute positioning) */}
      <div className="absolute top-6 right-6 z-20">
          <button
            onClick={() => setDevMode(!devMode)}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg backdrop-blur-xl transition-all duration-300 text-xs ${
              devMode ? 'cosmic-upload-zone' : 'opacity-40 hover:opacity-100'
            }`}
            style={devMode ? {
              borderColor: 'rgba(155, 143, 255, 0.6)',
              boxShadow: '0 0 20px rgba(155, 143, 255, 0.4)'
            } : {
              background: 'rgba(11, 13, 23, 0.4)',
              border: '1px solid rgba(155, 143, 255, 0.2)'
            }}
            title="Enable dev mode to use mock data for frontend development"
          >
            <svg
              className={`w-5 h-5 ${devMode ? 'text-blackalgo-text-light' : 'text-blackalgo-text-muted'}`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <span className={`text-sm font-medium ${devMode ? 'text-blackalgo-text-light' : 'text-blackalgo-text-muted'}`}>
              Dev Mode {devMode ? 'ON' : 'OFF'}
            </span>
          </button>
      </div>

      {/* Centered Content */}
      <div className="landing-centered">
        <div className="max-w-2xl w-full space-y-6">

        {/* AI Core Header - Compact */}
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="ai-core-compact rounded-xl inline-block">
              <div className="flex items-center gap-4">
                {/* Main Title */}
                <div>
                  <h1 className="text-5xl font-bold tactical-heading neon-text-purple tracking-wider">
                    PDF HUNTER
                  </h1>
                  <div className="text-xs tracking-widest neon-text mt-1 opacity-80">
                    AI CORE 16.1
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Subtitle */}
          <p className="text-base text-blackalgo-cyan tactical-mono" style={{
            textShadow: '0 0 10px rgba(0, 255, 209, 0.6)'
          }}>
            &gt; MULTI-AGENT THREAT DETECTION SYSTEM
          </p>
        </div>

        {/* File Upload Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`cosmic-upload-zone hud-corners terminal-scanlines rounded-2xl p-10 text-center cursor-pointer ${
            isDragging ? 'scale-105' : ''
          }`}
          style={isDragging ? {
            borderColor: 'rgba(0, 255, 209, 0.8)',
            boxShadow: '0 0 50px rgba(0, 255, 209, 0.6)'
          } : {}}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileSelect}
            className="hidden"
          />

          <div className="space-y-4">
            <div className="flex justify-center">
              <svg
                className="w-16 h-16 text-blackalgo-text-muted"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>

            {file ? (
              <div className="space-y-2">
                <p className="text-emerald-400 font-medium text-lg break-all px-4">
                  ✓ {file.name}
                </p>
                <p className="text-blackalgo-text-muted text-sm">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-blackalgo-text-light text-lg font-medium">
                  Drop your PDF here or click to browse
                </p>
                <p className="text-blackalgo-text-muted text-sm">
                  Supports PDF files up to 10MB
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Page Slider */}
        <div className="cosmic-upload-zone hud-corners terminal-scanlines rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-blackalgo-text-light font-semibold tracking-wider uppercase text-xs tactical-mono">
              <span className="neon-text">ANALYSIS DEPTH</span>
            </label>
            <span className="text-blackalgo-cyan text-2xl font-bold tactical-mono pixelated-text" style={{
              textShadow: '0 0 20px rgba(0, 255, 209, 0.8)'
            }}>
              {maxPages}
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="4"
            value={maxPages}
            onChange={(e) => setMaxPages(parseInt(e.target.value))}
            className="w-full h-2 bg-blackalgo-bg-darker/80 rounded-lg appearance-none cursor-pointer slider"
          />
          <div className="flex justify-between text-xs text-blackalgo-text-muted tactical-mono">
            <span>1 PAGE</span>
            <span>2 PAGES</span>
            <span>3 PAGES</span>
            <span>4 PAGES</span>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="cosmic-upload-zone rounded-lg p-4 text-center" style={{
            borderColor: 'rgba(251, 113, 133, 0.5)',
            boxShadow: '0 0 30px rgba(251, 113, 133, 0.3)'
          }}>
            <p className="text-rose-400 tactical-mono">&gt; ERROR: {error}</p>
          </div>
        )}

        {/* Upload Button or Dev Mode Button */}
        {devMode ? (
          <button
            onClick={handleDevMode}
            className="w-full py-5 px-8 rounded-xl font-bold text-lg transition-all duration-300 uppercase tracking-wider transform hover:scale-105 tactical-heading"
            style={{
              background: 'linear-gradient(135deg, #00FFD1 0%, #9B8FFF 100%)',
              boxShadow: '0 0 40px rgba(0, 255, 209, 0.6), 0 8px 24px rgba(0, 0, 0, 0.4)',
              color: '#0B0D17',
              border: '2px solid rgba(0, 255, 209, 0.5)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 0 60px rgba(0, 255, 209, 0.9), 0 12px 32px rgba(0, 0, 0, 0.5)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = '0 0 40px rgba(0, 255, 209, 0.6), 0 8px 24px rgba(0, 0, 0, 0.4)';
            }}
          >
            <span className="flex items-center justify-center space-x-3">
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5"
                />
              </svg>
              <span>INITIATE DEV ANALYSIS</span>
            </span>
          </button>
        ) : (
          <button
            onClick={handleUpload}
            disabled={!file || isUploading}
            className="w-full py-5 px-8 rounded-xl font-bold text-lg transition-all duration-300 transform hover:scale-105 tactical-heading uppercase tracking-wider"
            style={!file || isUploading ? {
              background: 'rgba(11, 13, 23, 0.6)',
              color: 'rgba(168, 167, 184, 0.4)',
              cursor: 'not-allowed',
              border: '2px solid rgba(109, 76, 255, 0.2)'
            } : {
              background: 'linear-gradient(135deg, #00FFD1 0%, #9B8FFF 100%)',
              color: '#0B0D17',
              boxShadow: '0 0 40px rgba(0, 255, 209, 0.6), 0 8px 24px rgba(0, 0, 0, 0.4)',
              border: '2px solid rgba(0, 255, 209, 0.5)'
            }}
            onMouseEnter={(e) => {
              if (file && !isUploading) {
                e.currentTarget.style.boxShadow = '0 0 60px rgba(0, 255, 209, 0.9), 0 12px 32px rgba(0, 0, 0, 0.5)';
              }
            }}
            onMouseLeave={(e) => {
              if (file && !isUploading) {
                e.currentTarget.style.boxShadow = '0 0 40px rgba(0, 255, 209, 0.6), 0 8px 24px rgba(0, 0, 0, 0.4)';
              }
            }}
          >
            {isUploading ? (
              <span className="flex items-center justify-center space-x-3">
                <svg
                  className="animate-spin h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  style={{ filter: 'drop-shadow(0 0 8px rgba(0, 255, 209, 0.8))' }}
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              <span>INITIALIZING THREAT SCAN...</span>
            </span>
          ) : (
            <span className="flex items-center justify-center space-x-3">
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              <span>INITIATE THREAT SCAN</span>
            </span>
          )}
          </button>
        )}

        {/* Info Footer */}
        <div className="text-center text-blackalgo-text-muted text-sm space-y-2 tactical-mono">
          <p className="text-blackalgo-purple-light" style={{
            textShadow: '0 0 8px rgba(155, 143, 255, 0.5)'
          }}>
            POWERED BY AI MULTI-AGENT SYSTEM
          </p>
          <p className="text-xs opacity-75 text-blackalgo-cyan">
            &gt; 5 SPECIALIZED AGENTS • REAL-TIME STREAMING • COMPREHENSIVE REPORTS
          </p>
        </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
