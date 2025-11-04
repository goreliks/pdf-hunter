import { useEffect, useState } from 'react';

/**
 * FlowingConnection - Animated SVG path connecting two points with flowing particles
 *
 * @param {Object} from - Start position {x, y}
 * @param {Object} to - End position {x, y}
 * @param {string} color - Hex color for the connection (e.g., '#00d9ff')
 * @param {number} delay - Animation delay in milliseconds
 * @param {number} duration - Animation duration in seconds
 * @param {string} type - 'straight', 'curved', or 'bezier'
 * @param {boolean} active - Whether the connection is currently active
 */
export const FlowingConnection = ({
  from,
  to,
  color = '#00d9ff',
  delay = 0,
  duration = 2,
  type = 'curved',
  active = true
}) => {
  const [pathId] = useState(() => `path-${Math.random().toString(36).substr(2, 9)}`);

  // Calculate path based on type
  const getPath = () => {
    switch (type) {
      case 'straight':
        return `M ${from.x},${from.y} L ${to.x},${to.y}`;

      case 'bezier':
        const midX = (from.x + to.x) / 2;
        const midY = (from.y + to.y) / 2;
        const controlY = Math.min(from.y, to.y) - 80;
        return `M ${from.x},${from.y} Q ${midX},${controlY} ${to.x},${to.y}`;

      case 'curved':
      default:
        // Smooth curve with horizontal then vertical segments
        const diffX = to.x - from.x;
        const diffY = to.y - from.y;
        const midPoint = from.x + diffX * 0.6;
        return `M ${from.x},${from.y} L ${midPoint},${from.y} Q ${midPoint + 20},${from.y} ${midPoint + 20},${from.y + 20} L ${midPoint + 20},${to.y - 20} Q ${midPoint + 20},${to.y} ${midPoint + 40},${to.y} L ${to.x},${to.y}`;
    }
  };

  if (!active) return null;

  return (
    <svg
      className="absolute inset-0 pointer-events-none overflow-visible"
      style={{ zIndex: 5 }}
    >
      <defs>
        {/* Gradient for the flowing effect */}
        <linearGradient id={`grad-${pathId}`} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={color} stopOpacity="0">
            <animate
              attributeName="stop-opacity"
              values="0;0.8;0"
              dur={`${duration}s`}
              begin={`${delay / 1000}s`}
              repeatCount="indefinite"
            />
          </stop>
          <stop offset="50%" stopColor={color} stopOpacity="1">
            <animate
              attributeName="stop-opacity"
              values="0;1;0"
              dur={`${duration}s`}
              begin={`${delay / 1000}s`}
              repeatCount="indefinite"
            />
          </stop>
          <stop offset="100%" stopColor={color} stopOpacity="0">
            <animate
              attributeName="stop-opacity"
              values="0;0.8;0"
              dur={`${duration}s`}
              begin={`${delay / 1000}s`}
              repeatCount="indefinite"
            />
          </stop>
        </linearGradient>

        {/* Glow filter */}
        <filter id={`glow-${pathId}`}>
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      {/* Base path (static glow) */}
      <path
        d={getPath()}
        stroke={color}
        strokeWidth="1"
        fill="none"
        opacity="0.2"
        filter={`url(#glow-${pathId})`}
      />

      {/* Animated flowing path */}
      <path
        d={getPath()}
        stroke={`url(#grad-${pathId})`}
        strokeWidth="2"
        fill="none"
        strokeDasharray="20 200"
        strokeDashoffset="0"
        filter={`url(#glow-${pathId})`}
        className="animate-flow"
        style={{
          animationDuration: `${duration}s`,
          animationDelay: `${delay}ms`
        }}
      />

      {/* Particle dots */}
      {[0, 0.33, 0.66].map((offset, i) => (
        <circle
          key={i}
          r="3"
          fill={color}
          opacity="0"
          filter={`url(#glow-${pathId})`}
        >
          <animateMotion
            dur={`${duration}s`}
            begin={`${(delay / 1000) + (offset * duration)}s`}
            repeatCount="indefinite"
            path={getPath()}
          />
          <animate
            attributeName="opacity"
            values="0;1;1;0"
            keyTimes="0;0.1;0.9;1"
            dur={`${duration}s`}
            begin={`${(delay / 1000) + (offset * duration)}s`}
            repeatCount="indefinite"
          />
        </circle>
      ))}
    </svg>
  );
};

export default FlowingConnection;

