import { useState, useEffect, useRef, useCallback } from 'react';
import { API_ENDPOINTS } from '../config/api';

/**
 * Custom hook for streaming Server-Sent Events from PDF Hunter backend
 * 
 * @param {string} sessionId - The session ID from upload response
 * @returns {Object} - { logs, isConnected, error, connectionState }
 */
export function useSSEStream(sessionId) {
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const [connectionState, setConnectionState] = useState('disconnected');
  
  const eventSourceRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  
  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY = 2000; // 2 seconds

  // Connect to SSE stream
  const connect = useCallback(() => {
    if (!sessionId) {
      return;
    }

    setConnectionState('connecting');
    setError(null);

    // Create new EventSource connection
    const eventSource = new EventSource(API_ENDPOINTS.stream(sessionId));
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log('✅ SSE connection established');
      setIsConnected(true);
      setConnectionState('connected');
      reconnectAttemptsRef.current = 0;
    };

    eventSource.onmessage = (event) => {
      try {
        console.log('📨 Received SSE message:', event.data);
        
        // Parse the log entry
        const logEntry = JSON.parse(event.data);
        
        console.log('✅ Parsed log entry:', logEntry);
        
        // Add to logs array
        setLogs((prevLogs) => [...prevLogs, logEntry]);
        
      } catch (err) {
        console.error('❌ Failed to parse SSE message:', err, event.data);
      }
    };

    eventSource.onerror = (err) => {
      console.error('❌ SSE connection error:', err);
      setIsConnected(false);
      setConnectionState('error');
      eventSource.close();
      
      // Attempt to reconnect
      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttemptsRef.current += 1;
        setConnectionState('reconnecting');
        
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log(`🔄 Reconnecting (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})...`);
          connect();
        }, RECONNECT_DELAY);
      } else {
        setError('Connection lost. Maximum reconnection attempts reached.');
        setConnectionState('failed');
      }
    };

    eventSource.addEventListener('keepalive', (event) => {
      console.log('💓 Keepalive ping received');
    });

  }, [sessionId]);

  // Connect when component mounts
  useEffect(() => {
    if (sessionId) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [sessionId, connect]);

  return {
    logs,
    isConnected,
    error,
    connectionState,
  };
}
