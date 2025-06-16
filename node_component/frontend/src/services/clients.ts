import axios from 'axios';

/**
 * Axios instance for local Node API calls.
 * @returns {AxiosInstance} The Axios instance configured for local Node API calls.
 */
export const localApiClient = axios.create({
  baseURL: import.meta.env.VITE_LOCAL_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

/**
 * Axios instance for Hub API calls.
 * @returns {AxiosInstance} The Axios instance configured for Hub API calls.
 */
export const hubApiClient = axios.create({
  baseURL: import.meta.env.VITE_HUB_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 5000,
});

/**
 * Client for Server-Sent Events (SSE) to connect to the Hub API.
 * @returns {EventSource} The EventSource instance for SSE connections.
 */
export const sseClient = {
  getEventSource: (endpoint: string) => {
    const hubBaseUrl = import.meta.env.VITE_HUB_API_BASE_URL;
    return new EventSource(`${hubBaseUrl}${endpoint}`);
  },
};
