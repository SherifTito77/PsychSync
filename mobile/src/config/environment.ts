/**
 * Environment configuration for PsychSync Mobile
 * Uses expo-constants for app configuration
 */

import Constants from 'expo-constants';

// Get API URL from app config or use default
// In production, this should be set in app.json under extra.apiUrl
const getApiUrl = (): string => {
  // Check if running in Expo Go or production build
  if (__DEV__) {
    // Development: Use localhost with port from backend
    return 'http://localhost:8000/api/v1';
  }

  // Production: Use configured URL or default
  return Constants.expoConfig?.extra?.apiUrl || 'https://api.psychsync.com/api/v1';
};

export const ENV = {
  API_BASE_URL: getApiUrl(),
  API_TIMEOUT: 30000, // 30 seconds
  REFRESH_INTERVAL: 30000, // 30 seconds for auto-refresh
  isDev: __DEV__,
  version: Constants.expoConfig?.version || '1.0.0',
};

// API Endpoints
export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/login',
  REGISTER: '/register',
  LOGOUT: '/logout',
  REFRESH_TOKEN: '/refresh',

  // Email Monitoring
  MONITORING_STATS: '/email-monitoring/stats',
  MONITORING_HISTORY: '/email-monitoring/history',

  // Email Connections
  EMAIL_CONNECTIONS: '/email-connector/connections',
  SYNC_EMAIL: '/email-connector/sync',
  TEST_IMAP: '/email-connector/connection/test-imap',
  SETUP_CONNECTION: '/email-connector/connection/setup',

  // User
  USER_PROFILE: '/users/me',
} as const;
