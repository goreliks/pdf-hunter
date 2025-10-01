import React from 'react';

/**
 * ViewModeToggle - Control how logs are displayed
 * 
 * Modes:
 * - both: Show messages + structured fields (default)
 * - messages: Show only log messages
 * - structured: Show only structured field rows
 */
const ViewModeToggle = ({ mode, onChange }) => {
  const modes = [
    { value: 'both', label: 'Both', icon: '📋' },
    { value: 'messages', label: 'Messages', icon: '💬' },
    { value: 'structured', label: 'Structured', icon: '📊' },
  ];

  return (
    <div className="flex items-center gap-2 bg-gray-800/50 backdrop-blur-sm rounded-lg p-1 border border-purple-500/20">
      <span className="text-xs text-purple-300/60 px-2">View:</span>
      {modes.map((m) => (
        <button
          key={m.value}
          onClick={() => onChange(m.value)}
          className={`
            px-3 py-1.5 rounded text-sm font-medium transition-all
            ${mode === m.value
              ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/30'
              : 'text-purple-200 hover:text-white hover:bg-purple-900/30'
            }
          `}
          title={`Show ${m.label.toLowerCase()}`}
        >
          <span className="mr-1">{m.icon}</span>
          {m.label}
        </button>
      ))}
    </div>
  );
};

export default ViewModeToggle;
