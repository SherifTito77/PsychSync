// src/services/api.ts
import axios from 'axios';

// Use HTTPS in production, HTTP in development
const isHttpsEnvironment = import.meta.env.PROD || import.meta.env.VITE_FORCE_HTTPS === 'true';

// In development use a relative path so Vite proxy handles CORS.
// In production use VITE_API_URL or the current origin.
const API_BASE_URL: string =
  import.meta.env.VITE_API_URL ||
  (isHttpsEnvironment ? `https://${window.location.hostname}/api/v1` : '/api/v1');
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': 'fetch',
  },
  // SECURITY: Include credentials for httpOnly cookie support
  withCredentials: true,
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
    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          // Try to refresh token
          const response = await axios.post<TokenResponse>(`${API_BASE_URL}/auth/refresh`, {}, {
            headers: { Authorization: `Bearer ${refreshToken}` }
          });
          const { access_token, refresh_token } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
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

        // Fallback: redirect after delay (in case modal not mounted)
        setTimeout(() => {
          if (window.location.pathname !== '/login') {
            window.location.href = '/login?reason=session_expired';
          }
        }, 30000); // 30 seconds to allow user to see modal

        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
// Named exports for compatibility
export { api as apiClient };
export default api;
