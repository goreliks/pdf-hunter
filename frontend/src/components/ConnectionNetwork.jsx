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

    connections.forEach(({ fromId, toId }) => {
      const fromEl = document.getElementById(fromId);
      const toEl = document.getElementById(toId);

      if (fromEl && toEl) {
        const fromRect = fromEl.getBoundingClientRect();
        const toRect = toEl.getBoundingClientRect();
        const containerRect = containerRef?.current?.getBoundingClientRect() || { left: 0, top: 0 };

        newPositions[`${fromId}-${toId}`] = {
          from: {
            x: fromRect.left + fromRect.width / 2 - containerRect.left,
            y: fromRect.top + fromRect.height / 2 - containerRect.top
          },
          to: {
            x: toRect.left + toRect.width / 2 - containerRect.left,
            y: toRect.top + toRect.height / 2 - containerRect.top
          }
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
      {connections.map(({ fromId, toId, color, delay, duration, type, active }, index) => {
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
export const ConnectionNode = ({ id, children, glowColor = '#8b5cf6', active = false }) => {
  return (
    <div id={id} className="relative inline-block">
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

