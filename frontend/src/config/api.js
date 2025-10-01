// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  analyze: `${API_BASE_URL}/api/analyze`,
  stream: (sessionId) => `${API_BASE_URL}/api/sessions/${sessionId}/stream`,
  status: (sessionId) => `${API_BASE_URL}/api/sessions/${sessionId}/status`,
};
