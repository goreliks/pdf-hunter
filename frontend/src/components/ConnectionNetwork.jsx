import { useEffect, useState, useRef } from 'react';
import FlowingConnection from './FlowingConnection';

/**
 * ConnectionNetwork - Manages multiple flowing connections between elements
 *
 * Usage:
 * <ConnectionNetwork
 *   connections={[
 *     { fromId: 'agent-1', toId: 'agent-2', color: '#00d9ff', active: true },
 *     { fromId: 'agent-2', toId: 'agent-3', color: '#ec4899', active: false }
 *   ]}
 * />
 */
export const ConnectionNetwork = ({ connections = [], containerRef }) => {
  const [positions, setPositions] = useState({});
  const animationFrameRef = useRef();

  // Calculate positions of connected elements
  const updatePositions = () => {
    const newPositions = {};

    connections.forEach(({ fromId, toId, fromPoint = 'bottom-center', toPoint = 'top-center' }) => {
      const fromEl = document.getElementById(fromId);
      const toEl = document.getElementById(toId);

      if (fromEl && toEl) {
        const fromRect = fromEl.getBoundingClientRect();
        const toRect = toEl.getBoundingClientRect();
        const containerRect = containerRef?.current?.getBoundingClientRect() || { left: 0, top: 0 };

        // Calculate from position based on attachment point
        let fromX, fromY;
        if (fromPoint === 'bottom-center') {
          fromX = fromRect.left + fromRect.width / 2 - containerRect.left;
          fromY = fromRect.bottom - containerRect.top;
        } else if (fromPoint === 'bottom-left-quarter') {
          // Bottom edge at 25% from left
          fromX = fromRect.left + fromRect.width * 0.25 - containerRect.left;
          fromY = fromRect.bottom - containerRect.top;
        } else if (fromPoint === 'bottom-right-quarter') {
          // Bottom edge at 75% from left
          fromX = fromRect.left + fromRect.width * 0.75 - containerRect.left;
          fromY = fromRect.bottom - containerRect.top;
        } else if (fromPoint === 'left-center') {
          fromX = fromRect.left - containerRect.left;
          fromY = fromRect.top + fromRect.height / 2 - containerRect.top;
        } else if (fromPoint === 'right-center') {
          fromX = fromRect.right - containerRect.left;
          fromY = fromRect.top + fromRect.height / 2 - containerRect.top;
        } else if (fromPoint === 'top-center') {
          fromX = fromRect.left + fromRect.width / 2 - containerRect.left;
          fromY = fromRect.top - containerRect.top;
        } else {
          // Default: center
          fromX = fromRect.left + fromRect.width / 2 - containerRect.left;
          fromY = fromRect.top + fromRect.height / 2 - containerRect.top;
        }

        // Calculate to position based on attachment point
        let toX, toY;
        if (toPoint === 'top-center') {
          toX = toRect.left + toRect.width / 2 - containerRect.left;
          toY = toRect.top - containerRect.top;
        } else if (toPoint === 'top-left-quarter') {
          // Top edge at 25% from left
          toX = toRect.left + toRect.width * 0.25 - containerRect.left;
          toY = toRect.top - containerRect.top;
        } else if (toPoint === 'top-right-quarter') {
          // Top edge at 75% from left
          toX = toRect.left + toRect.width * 0.75 - containerRect.left;
          toY = toRect.top - containerRect.top;
        } else if (toPoint === 'bottom-center') {
          toX = toRect.left + toRect.width / 2 - containerRect.left;
          toY = toRect.bottom - containerRect.top;
        } else if (toPoint === 'left-center') {
          toX = toRect.left - containerRect.left;
          toY = toRect.top + toRect.height / 2 - containerRect.top;
        } else if (toPoint === 'right-center') {
          toX = toRect.right - containerRect.left;
          toY = toRect.top + toRect.height / 2 - containerRect.top;
        } else {
          // Default: center
          toX = toRect.left + toRect.width / 2 - containerRect.left;
          toY = toRect.top + toRect.height / 2 - containerRect.top;
        }

        newPositions[`${fromId}-${toId}`] = {
          from: { x: fromX, y: fromY },
          to: { x: toX, y: toY }
        };
      }
    });

    setPositions(newPositions);
  };

  useEffect(() => {
    // Initial calculation
    updatePositions();

    // Update on resize
    const handleResize = () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      animationFrameRef.current = requestAnimationFrame(updatePositions);
    };

    window.addEventListener('resize', handleResize);

    // Also update when elements might have moved (e.g., scrolling, layout changes)
    const observer = new ResizeObserver(handleResize);
    connections.forEach(({ fromId, toId }) => {
      const fromEl = document.getElementById(fromId);
      const toEl = document.getElementById(toId);
      if (fromEl) observer.observe(fromEl);
      if (toEl) observer.observe(toEl);
    });

    return () => {
      window.removeEventListener('resize', handleResize);
      observer.disconnect();
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [connections, containerRef]);

  return (
    <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 1 }}>
      {connections.map(({ fromId, toId, color, delay, duration, type, active, completed }, index) => {
        const posKey = `${fromId}-${toId}`;
        const pos = positions[posKey];

        if (!pos) return null;

        return (
          <FlowingConnection
            key={`${fromId}-${toId}-${index}`}
            from={pos.from}
            to={pos.to}
            color={color}
            delay={delay}
            duration={duration}
            type={type}
            active={active}
            completed={completed}
          />
        );
      })}
    </div>
  );
};

/**
 * ConnectionNode - Visual endpoint for connections
 *
 * Place this around elements that should have connections
 */
export const ConnectionNode = ({ id, children, glowColor = '#8b5cf6', active = false, className = '' }) => {
  return (
    <div id={id} className={`relative ${className}`}>
      {active && (
        <div
          className="absolute inset-0 rounded-lg animate-node-pulse pointer-events-none"
          style={{
            boxShadow: `0 0 0 0 ${glowColor}`
          }}
        />
      )}
      {children}
    </div>
  );
};

export default ConnectionNetwork;

