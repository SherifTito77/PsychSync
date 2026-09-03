/**
 * API Service
 *
 * Handles all HTTP communication with PsychSync backend.
 * Includes:
 * - Authentication
 * - Assessments
 * - Telehealth
 * - Chatbot
 * - Push notifications
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import NetInfo from '@react-native-community/netinfo';

const API_BASE_URL = __DEV__
  ? 'http://localhost:8000/api/v1'
  : 'https://api.psychsync.com/api/v1';

class APIService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Check network connectivity
        const netInfo = await NetInfo.fetch();
        if (!netInfo.isConnected) {
          throw new Error('No network connection available');
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // Token expired - try refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = await AsyncStorage.getItem('refresh_token');
            const response = await this.client.post('/auth/refresh', {
              refresh_token: refreshToken,
            });

            const { access_token } = response.data;
            await AsyncStorage.setItem('access_token', access_token);

            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed - logout
            await this.logout();
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // =================================================================
  // Authentication
  // =================================================================

  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', { email, password });

    await AsyncStorage.setItem('access_token', response.data.access_token);
    await AsyncStorage.setItem('refresh_token', response.data.refresh_token);
    await AsyncStorage.setItem('user_id', response.data.user.id);

    return response.data;
  }

  async signup(email: string, password: string, full_name: string) {
    const response = await this.client.post('/auth/signup', {
      email,
      password,
      full_name,
    });

    await AsyncStorage.setItem('access_token', response.data.access_token);
    await AsyncStorage.setItem('refresh_token', response.data.refresh_token);
    await AsyncStorage.setItem('user_id', response.data.user.id);

    return response.data;
  }

  async logout() {
    await AsyncStorage.multiRemove([
      'access_token',
      'refresh_token',
      'user_id',
    ]);
  }

  // =================================================================
  // Assessments
  // =================================================================

  async submitAssessment(
    assessmentType: string,
    responses: any,
    behavioral?: any
  ) {
    const endpoint = `/clinical/${assessmentType}/submit`;

    return this.client.post(endpoint, {
      responses,
      behavioral,
    });
  }

  async getAssessmentHistory(assessmentType: string, limit: number = 10) {
    return this.client.get(`/clinical/${assessmentType}/history?limit=${limit}`);
  }

  async getUserTrends(assessmentType: string) {
    return this.client.get(`/clinical/analytics/user/trends?assessment_type=${assessmentType}`);
  }

  // =================================================================
  // Telehealth
  // =================================================================

  async scheduleSession(sessionData: {
    session_type: string;
    consultation_reason: string;
    scheduled_time: string;
    duration_minutes: number;
    related_assessment_id?: string;
  }) {
    return this.client.post('/telehealth/schedule', sessionData);
  }

  async joinSession(sessionId: string) {
    return this.client.post('/telehealth/join', { session_id: sessionId });
  }

  async getActiveSessions() {
    return this.client.get('/telehealth/sessions/active');
  }

  async endSession(sessionId: string) {
    return this.client.post(`/telehealth/end/${sessionId}`);
  }

  async cancelSession(sessionId: string, reason: string) {
    return this.client.post('/telehealth/cancel', {
      session_id: sessionId,
      reason,
    });
  }

  // =================================================================
  // AI Chatbot
  // =================================================================

  async sendChatMessage(message: string, sessionId: string) {
    return this.client.post('/ai/chatbot/respond', {
      message,
      session_id: sessionId,
    });
  }

  // =================================================================
  // Push Notifications
  // =================================================================

  async registerDevice(deviceToken: string, platform: 'ios' | 'android') {
    return this.client.post('/mobile/register', {
      device_token: deviceToken,
      platform,
      push_enabled: true,
    });
  }

  async unregisterDevice(deviceToken: string) {
    return this.client.delete(`/mobile/devices/${deviceToken}`);
  }

  // =================================================================
  // Helper Methods
  // =================================================================

  async getCurrentUser() {
    const userId = await AsyncStorage.getItem('user_id');
    return this.client.get(`/users/${userId}`);
  }

  isAuthenticated(): Promise<boolean> {
    return AsyncStorage.getItem('access_token').then((token) => !!token);
  }
}

// Export singleton instance
export default new APIService();
