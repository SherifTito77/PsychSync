// src/api/axios.ts
import axios from 'axios';
// Create an Axios instance with base configuration
const apiClient = axios.create({
  baseURL: 'http://localhost:8000', // Your API's base URL
  headers: {
    'Content-Type': 'application/json',
  },
});
// Add a request interceptor to include the JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      // FIX: Ensure config.headers exists before assigning to it
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
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
      console.error('Unauthorized! Logging out and redirecting to login.');
      // Simple logout function to avoid circular dependency
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
export default apiClient;