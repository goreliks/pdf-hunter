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

      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
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
      setError(err.message || 'Failed to upload file');
      setIsUploading(false);
    }
  };

  const handleDevMode = () => {
    // Start dev mode with mock data
    onAnalysisStart({
      sessionId: 'dev-mode-mock-session',
      streamUrl: null,  // No real stream URL in dev mode
      statusUrl: null,
      filename: 'mock-analysis.pdf',
      devMode: true  // Enable dev mode
    });
  };

  return (
    <div className="min-h-screen gradient-bg flex items-center justify-center p-8">
      <div className="max-w-2xl w-full space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center space-x-4">
            {/* Animated pulse circle with purple/pink gradient */}
            <div className="relative">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-pulse"></div>
              <div className="absolute inset-0 w-16 h-16 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full animate-ping opacity-25"></div>
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-pink-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
              PDF Hunter
            </h1>
          </div>
          <p className="text-xl text-purple-100">
            AI-Powered PDF Threat Analysis
          </p>
          <p className="text-sm text-purple-300/70">
            Upload a PDF file to begin deep security analysis
          </p>
        </div>

        {/* Dev Mode Toggle */}
        <div className="flex justify-end">
          <button
            onClick={() => setDevMode(!devMode)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg backdrop-blur-sm transition-all duration-300 ${
              devMode
                ? 'bg-purple-500/40 border-2 border-purple-400 card-glow'
                : 'bg-gray-800/30 border-2 border-purple-500/30 hover:border-purple-400/50'
            }`}
            title="Enable dev mode to use mock data for frontend development"
          >
            <svg 
              className={`w-5 h-5 ${devMode ? 'text-purple-200' : 'text-purple-300/60'}`} 
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
            <span className={`text-sm font-medium ${devMode ? 'text-purple-200' : 'text-purple-300/70'}`}>
              Dev Mode {devMode ? 'ON' : 'OFF'}
            </span>
          </button>
        </div>

        {/* File Upload Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 cursor-pointer backdrop-blur-sm ${
            isDragging
              ? 'border-pink-500 bg-pink-500/20 scale-105 shadow-lg shadow-pink-500/30'
              : 'border-purple-500/30 bg-gray-800/30 hover:border-purple-400/50 card-glow'
          }`}
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
                className="w-16 h-16 text-purple-300/60"
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
                <p className="text-purple-300/70 text-sm">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-purple-100 text-lg font-medium">
                  Drop your PDF here or click to browse
                </p>
                <p className="text-purple-300/50 text-sm">
                  Supports PDF files up to 10MB
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Page Slider */}
        <div className="bg-gray-800/30 backdrop-blur-sm rounded-xl p-6 space-y-4 border border-purple-500/20 card-glow">
          <div className="flex items-center justify-between">
            <label className="text-purple-100 font-medium">
              Pages to Analyze
            </label>
            <span className="text-pink-400 text-2xl font-bold">
              {maxPages}
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="4"
            value={maxPages}
            onChange={(e) => setMaxPages(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-700/50 rounded-lg appearance-none cursor-pointer slider"
          />
          <div className="flex justify-between text-xs text-purple-300/60">
            <span>1 page</span>
            <span>2 pages</span>
            <span>3 pages</span>
            <span>4 pages</span>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/50 rounded-lg p-4 text-center backdrop-blur-sm">
            <p className="text-rose-400">{error}</p>
          </div>
        )}

        {/* Upload Button or Dev Mode Button */}
        {devMode ? (
          <button
            onClick={handleDevMode}
            className="w-full py-4 px-8 rounded-xl font-semibold text-lg transition-all duration-300 bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/50 transform hover:scale-105"
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
              <span>Start Dev Mode Analysis</span>
            </span>
          </button>
        ) : (
          <button
            onClick={handleUpload}
            disabled={!file || isUploading}
            className={`w-full py-4 px-8 rounded-xl font-semibold text-lg transition-all duration-300 ${
              !file || isUploading
                ? 'bg-gray-700/50 text-purple-300/40 cursor-not-allowed border border-purple-500/20'
                : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/50 transform hover:scale-105'
            }`}
          >
            {isUploading ? (
              <span className="flex items-center justify-center space-x-3">
                <svg
                  className="animate-spin h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
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
              <span>Starting Analysis...</span>
            </span>
          ) : (
            '🚀 Start Analysis'
          )}
          </button>
        )}

        {/* Info Footer */}
        <div className="text-center text-purple-300/60 text-sm space-y-2">
          <p>
            Powered by GPT-4 + LangGraph Multi-Agent System
          </p>
          <p className="text-xs">
            5 specialized agents • Real-time streaming • Comprehensive reports
          </p>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
