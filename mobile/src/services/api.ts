/**
 * API Service for PsychSync Mobile App
 * Communicates with the FastAPI backend
 */

import { MonitoringStats, EmailConnection, ApiResponse } from '../types';
import { ENV, API_ENDPOINTS } from '../config/environment';
import * as SecureStore from 'expo-secure-store';

class ApiService {
  private token: string | null = null;
  private readonly TOKEN_KEY = 'auth_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';

  constructor() {
    this.loadToken();
  }

  /**
   * Load authentication token from secure storage
   */
  private loadToken() {
    try {
      // SecureStore doesn't work on web platform
      if (typeof window !== 'undefined') {
        // Web: Use localStorage (synchronous)
        const storedToken = localStorage.getItem(this.TOKEN_KEY);
        if (storedToken) {
          this.token = storedToken;
        }
      } else {
        // Native: Use SecureStore (async, but fire and forget for now)
        SecureStore.getItemAsync(this.TOKEN_KEY).then((token) => {
          this.token = token;
        });
      }
    } catch (error) {
      // Silent fail - token will just be null
      this.token = null;
    }
  }

  /**
   * Set authentication token and store securely
   */
  async setToken(token: string, refreshToken?: string) {
    try {
      this.token = token;

      // Web: Use localStorage, Native: Use SecureStore
      if (typeof window !== 'undefined') {
        localStorage.setItem(this.TOKEN_KEY, token);
        if (refreshToken) {
          localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
        }
      } else {
        await SecureStore.setItemAsync(this.TOKEN_KEY, token);
        if (refreshToken) {
          await SecureStore.setItemAsync(this.REFRESH_TOKEN_KEY, refreshToken);
        }
      }
    } catch (error) {
      console.error('Error storing token:', error);
    }
  }

  /**
   * Clear all stored tokens
   */
  async clearTokens() {
    try {
      this.token = null;

      // Web: Use localStorage, Native: Use SecureStore
      if (typeof window !== 'undefined') {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.REFRESH_TOKEN_KEY);
      } else {
        await SecureStore.deleteItemAsync(this.TOKEN_KEY);
        await SecureStore.deleteItemAsync(this.REFRESH_TOKEN_KEY);
      }
    } catch (error) {
      console.error('Error clearing tokens:', error);
    }
  }

  /**
   * Get current token
   */
  getToken(): string | null {
    return this.token;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.token !== null;
  }

  /**
   * Make authenticated API request
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...options.headers,
      };

      if (this.token) {
        headers['Authorization'] = `Bearer ${this.token}`;
        console.log(`🔑 Sending authenticated request to: ${endpoint}`);
      } else {
        console.warn(`⚠️ No token available for: ${endpoint}`);
      }

      const response = await fetch(`${ENV.API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        console.error(`❌ API Error ${response.status}:`, data.detail || data.message);
        return {
          success: false,
          error: data.detail || data.message || 'Request failed',
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  /**
   * Get email monitoring stats
   */
  async getMonitoringStats(): Promise<ApiResponse<MonitoringStats>> {
    return this.request<MonitoringStats>(API_ENDPOINTS.MONITORING_STATS);
  }

  /**
   * Get email connections
   */
  async getEmailConnections(): Promise<ApiResponse<EmailConnection[]>> {
    return this.request<EmailConnection[]>(API_ENDPOINTS.EMAIL_CONNECTIONS);
  }

  /**
   * Sync email connection
   */
  async syncEmailConnection(connectionId: number): Promise<ApiResponse<any>> {
    return this.request<any>(API_ENDPOINTS.SYNC_EMAIL, {
      method: 'POST',
      body: JSON.stringify({ connection_id: connectionId }),
    });
  }

  /**
   * Test email connection
   */
  async testEmailConnection(credentials: {
    email_provider: string;
    email_address: string;
    password: string;
    server: string;
    port: number;
  }): Promise<ApiResponse<any>> {
    return this.request<any>(API_ENDPOINTS.TEST_IMAP, {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  /**
   * Setup email connection
   */
  async setupEmailConnection(credentials: {
    email_provider: string;
    email_address: string;
    password: string;
    server: string;
    port: number;
  }): Promise<ApiResponse<any>> {
    return this.request<any>(API_ENDPOINTS.SETUP_CONNECTION, {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  /**
   * Get monitoring history
   */
  async getMonitoringHistory(days: number = 7): Promise<ApiResponse<any>> {
    return this.request<any>(`${API_ENDPOINTS.MONITORING_HISTORY}?days=${days}`);
  }

  /**
   * Login
   */
  async login(email: string, password: string): Promise<ApiResponse<any>> {
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch(`${ENV.API_BASE_URL}${API_ENDPOINTS.LOGIN}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.detail || data.message || 'Login failed',
        };
      }

      // Store tokens if present
      if (data.access_token) {
        await this.setToken(data.access_token, data.refresh_token);
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  /**
   * Register
   */
  async register(data: {
    email: string;
    password: string;
    full_name: string;
  }): Promise<ApiResponse<any>> {
    return this.request<any>(API_ENDPOINTS.REGISTER, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Logout
   */
  async logout(): Promise<ApiResponse<any>> {
    const response = await this.request<any>(API_ENDPOINTS.LOGOUT, {
      method: 'POST',
    });

    // Clear tokens regardless of response
    await this.clearTokens();

    return response;
  }

  /**
   * Get user profile
   */
  async getUserProfile(): Promise<ApiResponse<any>> {
    return this.request<any>(API_ENDPOINTS.USER_PROFILE);
  }
}

// Singleton instance
export const apiService = new ApiService();
