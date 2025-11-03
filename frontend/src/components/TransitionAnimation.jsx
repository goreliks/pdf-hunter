import { useEffect, useState } from 'react';

const TransitionAnimation = ({ onComplete }) => {
  const [phase, setPhase] = useState(0); // 0: portal opening, 1: warping, 2: arriving

  useEffect(() => {
    // Phase 1: Portal opening (800ms)
    const phase1Timer = setTimeout(() => {
      setPhase(1);
    }, 800);

    // Phase 2: Warping through space (800ms)
    const phase2Timer = setTimeout(() => {
      setPhase(2);
    }, 1600);

    // Complete transition (400ms)
    const completeTimer = setTimeout(() => {
      onComplete();
    }, 2000);

    return () => {
      clearTimeout(phase1Timer);
      clearTimeout(phase2Timer);
      clearTimeout(completeTimer);
    };
  }, [onComplete]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-hidden nebula-bg terminal-scanlines">
      {/* Grid Pattern Overlay */}
      <div className="absolute inset-0 pointer-events-none" style={{
        backgroundImage: `
          repeating-linear-gradient(90deg, transparent, transparent 79px, rgba(133, 127, 255, 0.15) 79px, rgba(133, 127, 255, 0.15) 80px),
          repeating-linear-gradient(0deg, transparent, transparent 79px, rgba(133, 127, 255, 0.15) 79px, rgba(133, 127, 255, 0.15) 80px)
        `,
        backgroundSize: '80px 80px'
      }}></div>

      {/* Cosmic Portal Effect */}
      <div className="absolute inset-0 flex items-center justify-center">
        {/* Outer rings */}
        {[...Array(5)].map((_, i) => (
          <div
            key={`ring-${i}`}
            className="absolute rounded-full border-2"
            style={{
              width: `${100 + i * 80}px`,
              height: `${100 + i * 80}px`,
              borderColor: i % 2 === 0 ? 'rgba(0, 255, 209, 0.3)' : 'rgba(155, 143, 255, 0.3)',
              animation: `portalRing ${1.5 - i * 0.1}s ease-in-out infinite`,
              animationDelay: `${i * 0.1}s`,
              opacity: phase === 2 ? 0 : 1,
              transition: 'opacity 0.4s ease-out'
            }}
          />
        ))}

        {/* Central vortex */}
        <div
          className="absolute rounded-full"
          style={{
            width: phase === 0 ? '0px' : phase === 1 ? '500px' : '100vw',
            height: phase === 0 ? '0px' : phase === 1 ? '500px' : '100vh',
            background: 'radial-gradient(circle, rgba(0, 255, 209, 0.2) 0%, rgba(155, 143, 255, 0.1) 50%, transparent 100%)',
            transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
            boxShadow: '0 0 100px rgba(0, 255, 209, 0.5), inset 0 0 100px rgba(155, 143, 255, 0.3)'
          }}
        />

        {/* Spinning energy particles */}
        {[...Array(12)].map((_, i) => (
          <div
            key={`particle-${i}`}
            className="absolute w-2 h-2 rounded-full"
            style={{
              background: i % 2 === 0 ? '#00FFD1' : '#9B8FFF',
              left: '50%',
              top: '50%',
              transform: `rotate(${i * 30}deg) translateY(-${80 + phase * 40}px)`,
              boxShadow: `0 0 10px ${i % 2 === 0 ? '#00FFD1' : '#9B8FFF'}`,
              opacity: phase === 2 ? 0 : 1,
              transition: 'all 0.6s ease-out',
              animation: 'particlePulse 1s ease-in-out infinite',
              animationDelay: `${i * 0.08}s`
            }}
          />
        ))}

        {/* Center core pulse */}
        <div
          className="absolute rounded-full"
          style={{
            width: '120px',
            height: '120px',
            background: 'radial-gradient(circle, #00FFD1 0%, #9B8FFF 100%)',
            boxShadow: '0 0 60px rgba(0, 255, 209, 0.8), inset 0 0 30px rgba(155, 143, 255, 0.5)',
            animation: 'corePulse 1.5s ease-in-out infinite',
            opacity: phase === 2 ? 0 : 1,
            transition: 'opacity 0.4s ease-out',
            transform: phase === 1 ? 'scale(1.5)' : 'scale(1)'
          }}
        >
          <div className="absolute inset-0 rounded-full" style={{
            background: 'radial-gradient(circle, transparent 30%, rgba(0, 255, 209, 0.4) 70%)',
            animation: 'ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite'
          }}></div>
        </div>
      </div>

      {/* Status Text */}
      <div className="absolute bottom-20 left-1/2 -translate-x-1/2 text-center">
        <div
          className="text-blackalgo-cyan text-xl font-semibold tactical-mono tracking-wider"
          style={{
            textShadow: '0 0 20px rgba(0, 255, 209, 0.8)',
            opacity: phase === 2 ? 0 : 1,
            transition: 'opacity 0.4s ease-out'
          }}
        >
          {phase === 0 && '&gt; INITIALIZING AGENTS'}
          {phase === 1 && '&gt; ESTABLISHING NEURAL LINK'}
          {phase === 2 && '&gt; ENTERING ANALYSIS MODE'}
        </div>

        {/* Loading bar */}
        <div className="mt-4 w-64 h-1 bg-blackalgo-bg-darker/60 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{
              width: `${(phase + 1) * 33.33}%`,
              background: 'linear-gradient(90deg, #00FFD1 0%, #9B8FFF 100%)',
              boxShadow: '0 0 20px rgba(0, 255, 209, 0.6)',
              transition: 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)'
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default TransitionAnimation;
