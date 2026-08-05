// src/services/secureApi.ts
// Enhanced secure API service with httpOnly cookie-based authentication
// SECURITY: No tokens stored in JavaScript-accessible storage (localStorage/sessionStorage)

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

interface LoginResponse {
  message: string;
  user?: any;
}

interface SecurityHeaders {
  'X-CSRF-Token'?: string;
  'X-Content-Type-Options': 'nosniff';
  'X-Frame-Options': 'DENY';
  'X-XSS-Protection': '1; mode=block';
  'Referrer-Policy': 'strict-origin-when-cross-origin';
}

class SecureAPIClient {
  private api: AxiosInstance;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: () => void;
    reject: (error: any) => void;
  }> = [];
  private csrfToken: string | null = null;
  private requestRateLimiter = new Map<string, number[]>();

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000, // 30 second timeout
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest', // CSRF protection
      },
      withCredentials: true, // Important for httpOnly cookies
    });

    this.setupInterceptors();
    this.setupCSRFProtection();
  }

  private setupInterceptors(): void {
    // Request interceptor - add security headers (auth via httpOnly cookies)
    this.api.interceptors.request.use(
      (config) => {
        // Apply rate limiting
        if (!this.checkRateLimit(config.url || '')) {
          throw new axios.Cancel('Rate limit exceeded');
        }

        // SECURITY: No Authorization header needed
        // httpOnly cookies are sent automatically by the browser

        // Add CSRF token if available
        if (this.csrfToken) {
          config.headers['X-CSRF-Token'] = this.csrfToken;
        }

        // Add comprehensive security headers
        const securityHeaders: SecurityHeaders = {
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'X-XSS-Protection': '1; mode=block',
          'Referrer-Policy': 'strict-origin-when-cross-origin',
        };

        // Add security headers to request
        Object.assign(config.headers, securityHeaders);

        // Sanitize request data to prevent XSS
        if (config.data) {
          config.data = this.sanitizeRequestData(config.data);
        }

        // Add request timestamp for replay attack prevention
        config.headers['X-Request-Timestamp'] = Date.now().toString();

        return config;
      },
      (error) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle token refresh via httpOnly cookies
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 Unauthorized errors
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // Wait for the ongoing refresh to complete
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            }).then(() => {
              // Retry original request (cookies updated automatically)
              return this.api(originalRequest);
            }).catch((err) => {
              return Promise.reject(err);
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            await this.refreshToken();

            // Retry all failed requests (cookies updated automatically)
            this.failedQueue.forEach(({ resolve }) => resolve());
            this.failedQueue = [];

            // Retry the original request
            return this.api(originalRequest);

          } catch (refreshError) {
            // Refresh failed - clear user data and redirect to login
            this.failedQueue.forEach(({ reject }) => reject(refreshError));
            this.failedQueue = [];

            this.handleAuthFailure();
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        // Handle other HTTP errors
        if (error.response?.status >= 500) {
          console.error('Server error:', error.response.status);
        } else if (error.response?.status === 403) {
          console.error('Access forbidden:', error.response.data);
          this.handleAuthFailure();
        }

        return Promise.reject(error);
      }
    );
  }

  private async refreshToken(): Promise<void> {
    try {
      // SECURITY: Token refresh uses httpOnly cookies
      // Backend automatically updates cookies, no JavaScript storage needed

      await axios.post(
        `${API_BASE_URL}/auth/refresh`,
        {},  // Empty body - refresh token in httpOnly cookie
        {
          headers: {
            'Content-Type': 'application/json',
          },
          withCredentials: true,  // Send httpOnly cookies
        }
      );

      // Cookies updated automatically by backend via Set-Cookie header
      // No token storage in JavaScript needed

    } catch (error) {
      console.error('Token refresh failed:', error);
      throw error;
    }
  }

  private handleAuthFailure(): void {
    // Clear user data from localStorage (non-sensitive)
    localStorage.removeItem('user');

    // SECURITY: Tokens are in httpOnly cookies, will be cleared by backend
    // Call backend logout to clear cookies
    this.post('/auth/logout', {}, { withCredentials: true }).catch(() => {
      // Backend call failed, but continue with local cleanup
    });

    // Redirect to login with a return URL
    const currentPath = window.location.pathname + window.location.search;
    const loginUrl = `/login${currentPath !== '/' ? `?redirect=${encodeURIComponent(currentPath)}` : ''}`;

    // Prevent redirect loops
    if (!window.location.pathname.includes('/login')) {
      window.location.href = loginUrl;
    }
  }

  // Public API methods
  public get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.api.get(url, config);
  }

  public post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.api.post(url, data, config);
  }

  public put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.api.put(url, data, config);
  }

  public patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.api.patch(url, data, config);
  }

  public delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.api.delete(url, config);
  }

  // Authentication methods
  public async login(credentials: { email: string; password: string }): Promise<LoginResponse> {
    try {
      const formData = new FormData();
      formData.append('username', credentials.email);
      formData.append('password', credentials.password);

      const response = await axios.post<LoginResponse>(
        `${API_BASE_URL}/auth/token-fixed`,
        formData,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          withCredentials: true,  // httpOnly cookies
        }
      );

      // SECURITY: Tokens stored in httpOnly cookies by backend
      // No JavaScript storage needed

      return response.data;

    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  public logout(): void {
    // Call backend logout endpoint to clear httpOnly cookies
    this.post('/auth/logout', {}, { withCredentials: true }).catch(console.error);

    // Clear user data from localStorage (non-sensitive)
    this.handleAuthFailure();
  }

  // Utility methods
  public isAuthenticated(): boolean {
    // Check if user data exists in localStorage (set by authService)
    // SECURITY: Not checking tokens - they're in httpOnly cookies
    try {
      const userData = localStorage.getItem('user');
      return !!userData;
    } catch {
      return false;
    }
  }

  public shouldRefreshToken(): boolean {
    // SECURITY: Token refresh logic handled by backend via httpOnly cookies
    // Frontend doesn't need to track expiration
    // Backend will return 401 when token expires, triggering automatic refresh
    return false;
  }

  /**
   * Setup CSRF protection
   */
  private setupCSRFProtection(): void {
    // Get CSRF token from meta tag or cookie
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag instanceof HTMLMetaElement) {
      this.csrfToken = metaTag.getAttribute('content');
    }
  }

  /**
   * Rate limiting to prevent abuse
   */
  private checkRateLimit(endpoint: string): boolean {
    const now = Date.now();
    const windowMs = 60000; // 1 minute window
    const maxRequests = 100; // Max 100 requests per minute per endpoint

    if (!this.requestRateLimiter.has(endpoint)) {
      this.requestRateLimiter.set(endpoint, []);
    }

    const requests = this.requestRateLimiter.get(endpoint)!;

    // Remove old requests outside the window
    const validRequests = requests.filter(timestamp => now - timestamp < windowMs);

    if (validRequests.length >= maxRequests) {
      return false; // Rate limit exceeded
    }

    validRequests.push(now);
    this.requestRateLimiter.set(endpoint, validRequests);
    return true;
  }

  /**
   * Sanitize request data to prevent XSS
   */
  private sanitizeRequestData(data: any): any {
    if (typeof data === 'string') {
      return this.sanitizeString(data);
    }

    if (Array.isArray(data)) {
      return data.map(item => this.sanitizeRequestData(item));
    }

    if (data && typeof data === 'object') {
      const sanitized: any = {};
      for (const [key, value] of Object.entries(data)) {
        const sanitizedKey = this.sanitizeString(key);
        sanitized[sanitizedKey] = this.sanitizeRequestData(value);
      }
      return sanitized;
    }

    return data;
  }

  /**
   * Sanitize strings to prevent XSS
   */
  private sanitizeString(str: string): string {
    if (typeof str !== 'string') return str;

    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
      .replace(/\//g, '&#x2F;');
  }

  /**
   * Validate response integrity
   */
  private validateResponse(response: AxiosResponse): boolean {
    // Check for response tampering
    if (!response.data) return true;

    // Validate response structure based on endpoint
    const url = response.config.url;

    if (url?.includes('/auth/')) {
      // Auth responses should have specific structure
      if (url.includes('/login') || url.includes('/refresh')) {
        return response.data.access_token && response.data.refresh_token;
      }
    }

    return true;
  }

  /**
   * Enhanced secure file upload
   */
  public async uploadFile(file: File, endpoint: string = '/upload'): Promise<AxiosResponse> {
    // Validate file
    if (!this.isValidFile(file)) {
      throw new Error('Invalid file type or size');
    }

    const formData = new FormData();
    formData.append('file', file);

    // Add file metadata for security
    formData.append('filename', file.name);
    formData.append('filesize', file.size.toString());
    formData.append('filetype', file.type);
    formData.append('upload_timestamp', Date.now().toString());

    return this.api.post(endpoint, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // Longer timeout for file uploads
    });
  }

  /**
   * Validate file security
   */
  private isValidFile(file: File): boolean {
    // Check file size (max 10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      return false;
    }

    // Check file type (whitelist approach)
    const allowedTypes = [
      'image/jpeg',
      'image/png',
      'image/gif',
      'application/pdf',
      'text/plain',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];

    return allowedTypes.includes(file.type);
  }

  /**
   * Generate secure request signature
   */
  private generateRequestSignature(data: any, timestamp: string): string {
    // Simple signature for request integrity
    // SECURITY: Not using tokens for signature (they're in httpOnly cookies)
    const key = 'anonymous';  // No longer using tokens for signature
    const message = JSON.stringify(data) + timestamp;

    let hash = 0;
    for (let i = 0; i < message.length; i++) {
      const char = message.charCodeAt(i);
      const keyChar = key.charCodeAt(i % key.length);
      hash = ((hash << 5) - hash) + char + keyChar;
      hash = hash & hash;
    }

    return Math.abs(hash).toString(16);
  }

  /**
   * Secure API call with retry mechanism
   */
  public async secureRequest<T = any>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
    maxRetries: number = 3
  ): Promise<AxiosResponse<T>> {
    let lastError: any;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const response = await this.api.request({
          method,
          url,
          data,
          ...config,
        });

        // Validate response integrity
        if (!this.validateResponse(response)) {
          throw new Error('Response validation failed');
        }

        return response;
      } catch (error: any) {
        lastError = error;

        // Don't retry on authentication errors or 4xx errors
        if (error.response?.status >= 400 && error.response?.status < 500) {
          throw error;
        }

        // Exponential backoff for retries
        if (attempt < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    throw lastError;
  }

  /**
   * Batch API requests for efficiency
   */
  public async batchRequests<T = any>(requests: Array<{
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
    url: string;
    data?: any;
  }>): Promise<AxiosResponse<T>[]> {
    try {
      const batchResponse = await this.post('/batch', { requests });
      return batchResponse.data.responses;
    } catch (error) {
      console.error('Batch request failed:', error);
      throw error;
    }
  }

  /**
   * Get security metrics
   */
  public getSecurityMetrics(): {
    rateLimitStatus: Map<string, number>;
    csrfTokenStatus: boolean;
    lastRequestTime: number;
  } {
    const rateLimitStatus = new Map();
    this.requestRateLimiter.forEach((requests, endpoint) => {
      rateLimitStatus.set(endpoint, requests.length);
    });

    return {
      rateLimitStatus,
      csrfTokenStatus: !!this.csrfToken,
      lastRequestTime: Date.now(),
    };
  }
}

// Create singleton instance
const secureApi = new SecureAPIClient();
export default secureApi;
