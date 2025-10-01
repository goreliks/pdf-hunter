import { useEffect, useState } from 'react';

const TransitionAnimation = ({ onComplete }) => {
  const [stage, setStage] = useState('shrink'); // shrink -> rise -> fade

  useEffect(() => {
    // Shrink stage (400ms)
    const shrinkTimer = setTimeout(() => {
      setStage('rise');
    }, 400);

    // Rise stage (400ms)
    const riseTimer = setTimeout(() => {
      setStage('fade');
    }, 800);

    // Complete transition (200ms fade)
    const completeTimer = setTimeout(() => {
      onComplete();
    }, 1000);

    return () => {
      clearTimeout(shrinkTimer);
      clearTimeout(riseTimer);
      clearTimeout(completeTimer);
    };
  }, [onComplete]);

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 z-50 flex items-center justify-center overflow-hidden">
      {/* Animated Circle */}
      <div
        className={`
          absolute
          bg-blue-500 rounded-full
          transition-all duration-400 ease-in-out
          ${stage === 'shrink' ? 'w-64 h-64 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2' : ''}
          ${stage === 'rise' ? 'w-16 h-16 top-8 left-1/2 -translate-x-1/2' : ''}
          ${stage === 'fade' ? 'w-16 h-16 top-8 left-1/2 -translate-x-1/2 opacity-0' : 'opacity-100'}
        `}
      >
        {/* Pulse effect */}
        <div className="absolute inset-0 bg-blue-400 rounded-full animate-ping opacity-25"></div>
      </div>

      {/* Loading text */}
      <div
        className={`
          absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
          text-white text-xl font-medium
          transition-opacity duration-300
          ${stage === 'fade' ? 'opacity-0' : 'opacity-100'}
        `}
      >
        Initializing Analysis...
      </div>
    </div>
  );
};

export default TransitionAnimation;
