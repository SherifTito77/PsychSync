// // // // // // src/services/api.ts
// frontend/src/services/api.ts - Updated for HTTPS support
import axios from 'axios';

// Use HTTPS in production, HTTP in development
const isHttpsEnvironment = import.meta.env.PROD || import.meta.env.VITE_FORCE_HTTPS === 'true';

// ✅ SECURITY FIX: Request queuing to prevent race conditions during token refresh
let isRefreshing = false;
let failedQueue: Array<() => void> = [];

// Import https agent for SSL certificate handling (Node.js environment only)
let httpsAgent: any = undefined;
if (typeof window === 'undefined' && isHttpsEnvironment && !import.meta.env.PROD) {
  try {
    const https = require('https');
    httpsAgent = new https.Agent({
      rejectUnauthorized: false // Only for development with self-signed certs
    });
  } catch (e) {
    console.warn('HTTPS agent not available:', e);
  }
}
const defaultPort = isHttpsEnvironment ? '443' : '8000';
const defaultProtocol = isHttpsEnvironment ? 'https' : 'http';
// ✅ FIX: Use localhost:8000 for backend API
const defaultHost = 'localhost';

const API_BASE_URL = import.meta.env.VITE_API_URL || `http://localhost:8000/api/v1`;
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // SECURITY: Include credentials for httpOnly cookie support
  withCredentials: true,
  // SSL certificate validation for development (Node.js only)
  httpsAgent: httpsAgent,
});
// Request interceptor - add auth token and CSRF protection
api.interceptors.request.use(
  (config) => {
    // SECURITY: Tokens are now stored in httpOnly cookies
    // Cookies are sent automatically by the browser

    // However, we still add it for backward compatibility during transition
    // and for endpoints that might not support cookies yet
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // SECURITY: Add CSRF token to state-changing requests
    // The backend sets a csrf_token cookie (non-httpOnly) that we need to send in the header
    const dangerousMethods = ['post', 'put', 'delete', 'patch'];
    if (dangerousMethods.includes(config.method?.toLowerCase() || '')) {
      const csrfToken = getCsrfTokenFromCookie();
      if (csrfToken && config.headers) {
        config.headers['X-CSRF-Token'] = csrfToken;
      }
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Helper function to extract CSRF token from cookie
function getCsrfTokenFromCookie(): string | null {
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrf_token') {
      return decodeURIComponent(value);
    }
  }
  return null;
}
interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // ✅ SECURITY FIX: If already refreshing, queue the request
    if (isRefreshing) {
      // Store request for retry after refresh completes
      return new Promise<void>((resolve) => {
        failedQueue.push(() => {
          resolve(api(originalRequest));
        });
      });
    }

    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      isRefreshing = true;
      originalRequest._retry = true;

      // Dispatch auth refresh start event for SessionManager
      window.dispatchEvent(new CustomEvent('authRefreshStart'));

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          // Try to refresh token - send as form data
          const response = await axios.post<TokenResponse>(
            `${API_BASE_URL}/auth/refresh`,
            new URLSearchParams({ refresh_token: refreshToken }),
            {
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
              }
            }
          );
          const { access_token, refresh_token: newRefreshToken } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefreshToken);

          // ✅ FIX: Mark refresh complete and process queued requests
          isRefreshing = false;

          // Dispatch auth refresh end event for SessionManager
          window.dispatchEvent(new CustomEvent('authRefreshEnd'));

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;

          // Process all queued requests with new token
          failedQueue.forEach((prom) => prom());
          failedQueue = [];

          return api(originalRequest);
        }
      } catch (refreshError) {
        // ✅ FIX: Mark refresh complete and process queued requests (even failed)
        isRefreshing = false;

        // Dispatch auth refresh end event even on failure
        window.dispatchEvent(new CustomEvent('authRefreshEnd'));

        // Process all queued requests (they will fail with same error)
        failedQueue.forEach((prom) => prom());
        failedQueue = [];

        // Refresh failed - trigger session expiry flow
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');

        // Store session state for redirect after login
        sessionStorage.setItem('session_expired', 'true');
        sessionStorage.setItem('redirect_after_login', window.location.pathname);

        // Dispatch custom event for SessionExpiryModal to catch
        const sessionExpiryEvent = new CustomEvent('sessionExpired', {
          detail: { reason: 'token_refresh_failed' }
        });
        window.dispatchEvent(sessionExpiryEvent);

        // ✅ FIX: Don't force redirect, let modal handle it
        // Removed: setTimeout(() => {
        //   if (window.location.pathname !== '/login') {
        //     window.location.href = '/login?reason=session_expired';
        //   }
        // }, 30000);

        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
// Named exports for compatibility
export { api as apiClient };
export default api;
