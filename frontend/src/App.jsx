import { useState } from 'react'
import LandingPage from './components/LandingPage'
import TransitionAnimation from './components/TransitionAnimation'
import Dashboard from './components/Dashboard'
import './App.css'

function App() {
  const [view, setView] = useState('landing'); // 'landing' | 'transition' | 'dashboard'
  const [analysisData, setAnalysisData] = useState(null);

  const handleAnalysisStart = (data) => {
    setAnalysisData(data);
    setView('transition');
  };

  const handleTransitionComplete = () => {
    setView('dashboard');
  };

  return (
    <div className="App">
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
        />
      )}
    </div>
  )
}

export default App
