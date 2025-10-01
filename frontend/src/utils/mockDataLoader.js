/**
 * Mock Data Loader for Dev Mode
 * 
 * Loads mock session logs from frontend/dev/mock-session.jsonl
 * for frontend development without running the backend.
 */

export async function loadMockSession() {
  try {
    const response = await fetch('/dev/mock-session.jsonl');
    
    if (!response.ok) {
      throw new Error(`Failed to load mock data: ${response.status} ${response.statusText}`);
    }
    
    const text = await response.text();
    
    // Parse JSONL (one JSON object per line)
    const logs = text
      .trim()
      .split('\n')
      .filter(line => line.trim())  // Remove empty lines
      .map((line, index) => {
        try {
          return JSON.parse(line);
        } catch (err) {
          console.error(`Failed to parse log line ${index + 1}:`, line, err);
          return null;
        }
      })
      .filter(log => log !== null);  // Remove failed parses
    
    console.log(`[Dev Mode] Loaded ${logs.length} mock logs`);
    return logs;
    
  } catch (error) {
    console.error('[Dev Mode] Failed to load mock session:', error);
    // Return empty array instead of throwing - graceful degradation
    return [];
  }
}

/**
 * Simulate SSE streaming by emitting logs with delays
 * @param {Array} logs - Array of log objects from JSONL
 * @param {Function} onLog - Callback for each log
 * @param {Number} delayMs - Delay between logs (default 100ms)
 */
export async function simulateStreaming(logs, onLog, delayMs = 100) {
  for (const log of logs) {
    onLog(log);
    // Add delay between logs to simulate real-time streaming
    await new Promise(resolve => setTimeout(resolve, delayMs));
  }
}
