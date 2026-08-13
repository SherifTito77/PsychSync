// src/api/axios.ts
import axios from 'axios';
// Create an Axios instance with base configuration
const apiClient = axios.create({
  baseURL: '', // Callers use full paths like /api/v1/...; Vite proxy handles /api
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // IMPORTANT: Allows browser to send/receive cookies
});

// Add a request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers = config.headers || {};
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle global errors like 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.error('Unauthorized! Redirecting to login.');
      // Cookies are cleared automatically by backend logout
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
export default apiClient;
