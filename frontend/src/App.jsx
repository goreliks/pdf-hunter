import { useState, useEffect } from 'react'
import LandingPage from './components/LandingPage'
import TransitionAnimation from './components/TransitionAnimation'
import Dashboard from './components/Dashboard'
import ConnectionDemo from './components/ConnectionDemo'
import './App.css'

const SESSION_STORAGE_KEY = 'pdf-hunter-session';

function App() {
  // Check for demo mode via URL parameter
  const urlParams = new URLSearchParams(window.location.search);
  const isDemoMode = urlParams.get('demo') === 'true';

  // Initialize state from sessionStorage if available
  const [view, setView] = useState(() => {
    if (isDemoMode) return 'demo';
    const savedSession = sessionStorage.getItem(SESSION_STORAGE_KEY);
    return savedSession ? 'dashboard' : 'landing';
  });
  
  const [analysisData, setAnalysisData] = useState(() => {
    const savedSession = sessionStorage.getItem(SESSION_STORAGE_KEY);
    return savedSession ? JSON.parse(savedSession) : null;
  });

  // Persist session data to sessionStorage whenever it changes
  // Don't persist dev mode sessions
  useEffect(() => {
    if (analysisData && !analysisData.devMode) {
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(analysisData));
    } else if (analysisData && analysisData.devMode) {
      // Dev mode: don't persist, clear any existing session
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
    } else {
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
    }
  }, [analysisData]);

  const handleAnalysisStart = (data) => {
    setAnalysisData(data);
    setView('transition');
  };

  const handleTransitionComplete = () => {
    setView('dashboard');
  };

  const handleSessionEnd = () => {
    // Clear session and return to landing page
    setAnalysisData(null);
    setView('landing');
  };

  return (
    <div className="App">
      {view === 'demo' && (
        <ConnectionDemo />
      )}
      {view === 'landing' && (
        <LandingPage onAnalysisStart={handleAnalysisStart} />
      )}
      {view === 'transition' && (
        <TransitionAnimation onComplete={handleTransitionComplete} />
      )}
      {view === 'dashboard' && analysisData && (
        <Dashboard
          sessionId={analysisData.sessionId}
          streamUrl={analysisData.streamUrl}
          statusUrl={analysisData.statusUrl}
          filename={analysisData.filename}
          onSessionEnd={handleSessionEnd}
          devMode={analysisData.devMode || false}
        />
      )}
    </div>
  )
}

export default App
