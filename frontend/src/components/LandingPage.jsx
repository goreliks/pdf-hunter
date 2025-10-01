import { useState, useRef } from 'react';
import { API_BASE_URL } from '../config/api';

const LandingPage = ({ onAnalysisStart }) => {
  const [file, setFile] = useState(null);
  const [maxPages, setMaxPages] = useState(2);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
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
        filename: file.name
      });
    } catch (err) {
      setError(err.message || 'Failed to upload file');
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-8">
      <div className="max-w-2xl w-full space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center space-x-4">
            {/* Animated pulse circle */}
            <div className="relative">
              <div className="w-16 h-16 bg-blue-500 rounded-full animate-pulse"></div>
              <div className="absolute inset-0 w-16 h-16 bg-blue-400 rounded-full animate-ping opacity-25"></div>
            </div>
            <h1 className="text-5xl font-bold text-white">PDF Hunter</h1>
          </div>
          <p className="text-xl text-gray-300">
            AI-Powered PDF Threat Analysis
          </p>
          <p className="text-sm text-gray-400">
            Upload a PDF file to begin deep security analysis
          </p>
        </div>

        {/* File Upload Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 cursor-pointer ${
            isDragging
              ? 'border-blue-500 bg-blue-500/10 scale-105'
              : 'border-gray-600 bg-gray-800/50 hover:border-gray-500'
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
                className="w-16 h-16 text-gray-400"
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
                <p className="text-green-400 font-medium text-lg">
                  ✓ {file.name}
                </p>
                <p className="text-gray-400 text-sm">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-gray-300 text-lg font-medium">
                  Drop your PDF here or click to browse
                </p>
                <p className="text-gray-500 text-sm">
                  Supports PDF files up to 10MB
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Page Slider */}
        <div className="bg-gray-800/50 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-gray-300 font-medium">
              Pages to Analyze
            </label>
            <span className="text-blue-400 text-2xl font-bold">
              {maxPages}
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="4"
            value={maxPages}
            onChange={(e) => setMaxPages(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
          />
          <div className="flex justify-between text-xs text-gray-500">
            <span>1 page</span>
            <span>2 pages</span>
            <span>3 pages</span>
            <span>4 pages</span>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 text-center">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={!file || isUploading}
          className={`w-full py-4 px-8 rounded-xl font-semibold text-lg transition-all duration-300 ${
            !file || isUploading
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-500 hover:shadow-lg hover:shadow-blue-500/50 transform hover:scale-105'
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

        {/* Info Footer */}
        <div className="text-center text-gray-500 text-sm space-y-2">
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
