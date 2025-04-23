import axios from 'axios';

export const localApiClient = axios.create({
  baseURL: import.meta.env.VITE_LOCAL_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

export const hubApiClient = axios.create({
  baseURL: import.meta.env.VITE_HUB_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 5000,
});
