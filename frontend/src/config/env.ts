/**
 * File Path: frontend/src/config/env.ts
 * Environment configuration for frontend
 * Centralizes all environment-dependent settings
 */
// =================================================================
// ENVIRONMENT DETECTION
// =================================================================
const getEnvironment = (): 'development' | 'staging' | 'production' => {
  if (import.meta.env.MODE === 'production') {
    return 'production';
  }
  if (import.meta.env.MODE === 'staging') {
    return 'staging';
  }
  return 'development';
};
export const ENV = getEnvironment();
export const IS_DEV = ENV === 'development';
export const IS_PROD = ENV === 'production';
export const IS_STAGING = ENV === 'staging';
// =================================================================
// API CONFIGURATION
// =================================================================
const getApiBaseUrl = (): string => {
  // Check for explicit API URL env variable first
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  // Fallback based on environment
  switch (ENV) {
    case 'production':
      return 'https://api.psychsync.com';
    case 'staging':
      return 'https://api.staging.psychsync.com';
    case 'development':
    default:
      return 'http://localhost:8000';
  }
};
export const API_URL = getApiBaseUrl();
export const API_VERSION = 'v1';
export const API_BASE_URL = `${API_URL}/api/${API_VERSION}`;
// =================================================================
// FEATURE FLAGS
// =================================================================
export const FEATURES = {
  // Enable/disable features based on environment
  TEAM_OPTIMIZATION: import.meta.env.VITE_FEATURE_TEAM_OPTIMIZATION !== 'false',
  ASSESSMENT_BUILDER: import.meta.env.VITE_FEATURE_ASSESSMENT_BUILDER !== 'false',
  ANALYTICS_DASHBOARD: import.meta.env.VITE_FEATURE_ANALYTICS !== 'false',
  SOCIAL_LOGIN: import.meta.env.VITE_FEATURE_SOCIAL_LOGIN === 'true',
  EMAIL_NOTIFICATIONS: import.meta.env.VITE_FEATURE_EMAIL_NOTIFICATIONS !== 'false',
  DARK_MODE: import.meta.env.VITE_FEATURE_DARK_MODE === 'true',
} as const;
// =================================================================
// AUTHENTICATION
// =================================================================
export const AUTH_CONFIG = {
  TOKEN_KEY: 'access_token',
  REFRESH_TOKEN_KEY: 'refresh_token',
  USER_KEY: 'user',
  TOKEN_EXPIRY_KEY: 'token_expiry',
  // Token refresh threshold (5 minutes before expiry)
  REFRESH_THRESHOLD_MS: 5 * 60 * 1000,
  // Session timeout (30 minutes of inactivity)
  SESSION_TIMEOUT_MS: 30 * 60 * 1000,
} as const;
// =================================================================
// APPLICATION SETTINGS
// =================================================================
export const APP_CONFIG = {
  NAME: 'PsychSync',
  VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
  DESCRIPTION: 'Psychological Assessment & Team Optimization Platform',
  SUPPORT_EMAIL: 'support@psychsync.com',
  // Pagination
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  // File uploads
  MAX_FILE_SIZE_MB: 10,
  ALLOWED_FILE_TYPES: ['.pdf', '.doc', '.docx', '.jpg', '.png'],
  // Assessment settings
  AUTO_SAVE_INTERVAL_MS: 30000, // 30 seconds
  ASSESSMENT_TIMEOUT_MINUTES: 60,
} as const;
// =================================================================
// EXTERNAL SERVICES
// =================================================================
export const EXTERNAL_SERVICES = {
  // Google OAuth
  GOOGLE_CLIENT_ID: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
  // GitHub OAuth
  GITHUB_CLIENT_ID: import.meta.env.VITE_GITHUB_CLIENT_ID || '',
  // Analytics
  GOOGLE_ANALYTICS_ID: import.meta.env.VITE_GA_ID || '',
  // Monitoring
  SENTRY_DSN: import.meta.env.VITE_SENTRY_DSN || '',
} as const;
// =================================================================
// UI CONFIGURATION
// =================================================================
export const UI_CONFIG = {
  // Theme colors
  PRIMARY_COLOR: '#3b82f6', // blue-600
  SECONDARY_COLOR: '#8b5cf6', // purple-600
  SUCCESS_COLOR: '#10b981', // green-600
  WARNING_COLOR: '#f59e0b', // yellow-600
  ERROR_COLOR: '#ef4444', // red-600
  // Animation durations (ms)
  TRANSITION_DURATION: 200,
  TOAST_DURATION: 5000,
  LOADING_DELAY: 300,
  // Chart colors
  CHART_COLORS: [
    '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444',
    '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#6366f1'
  ],
} as const;
// =================================================================
// VALIDATION RULES
// =================================================================
export const VALIDATION = {
  EMAIL: {
    MIN_LENGTH: 5,
    MAX_LENGTH: 255,
    REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  },
  PASSWORD: {
    MIN_LENGTH: 8,
    MAX_LENGTH: 128,
    REQUIRE_UPPERCASE: true,
    REQUIRE_LOWERCASE: true,
    REQUIRE_NUMBER: true,
    REQUIRE_SPECIAL: false,
  },
  NAME: {
    MIN_LENGTH: 2,
    MAX_LENGTH: 100,
  },
  TEAM_NAME: {
    MIN_LENGTH: 3,
    MAX_LENGTH: 200,
  },
} as const;
// =================================================================
// API ENDPOINTS
// =================================================================
export const ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: `${API_BASE_URL}/auth/login`,
    REGISTER: `${API_BASE_URL}/auth/register`,
    LOGOUT: `${API_BASE_URL}/auth/logout`,
    REFRESH: `${API_BASE_URL}/auth/refresh`,
    VERIFY_EMAIL: `${API_BASE_URL}/auth/verify-email`,
    FORGOT_PASSWORD: `${API_BASE_URL}/auth/forgot-password`,
    RESET_PASSWORD: `${API_BASE_URL}/auth/reset-password`,
  },
  // Users
  USERS: {
    ME: `${API_BASE_URL}/users/me`,
    UPDATE: `${API_BASE_URL}/users/me`,
    EXPORT: `${API_BASE_URL}/users/export`,
  },
  // Assessments
  ASSESSMENTS: {
    LIST: `${API_BASE_URL}/assessments`,
    CREATE: `${API_BASE_URL}/assessments`,
    GET: (id: number) => `${API_BASE_URL}/assessments/${id}`,
    UPDATE: (id: number) => `${API_BASE_URL}/assessments/${id}`,
    DELETE: (id: number) => `${API_BASE_URL}/assessments/${id}`,
    START: (id: number) => `${API_BASE_URL}/assessments/${id}/start`,
    SUBMIT: (id: number) => `${API_BASE_URL}/assessments/${id}/submit`,
    RESULTS: (id: number) => `${API_BASE_URL}/assessments/results/${id}`,
    SCORES: `${API_BASE_URL}/assessments/scores`,
    TRENDS: `${API_BASE_URL}/assessments/trends`,
    PERSONALITY: `${API_BASE_URL}/assessments/personality-profile`,
    DOWNLOAD: `${API_BASE_URL}/assessments/report/download`,
  },
  // Teams
  TEAMS: {
    LIST: `${API_BASE_URL}/teams`,
    CREATE: `${API_BASE_URL}/teams`,
    GET: (id: number) => `${API_BASE_URL}/teams/${id}`,
    UPDATE: (id: number) => `${API_BASE_URL}/teams/${id}`,
    DELETE: (id: number) => `${API_BASE_URL}/teams/${id}`,
    INVITE: (id: number) => `${API_BASE_URL}/teams/${id}/invite`,
    INVITATIONS: `${API_BASE_URL}/teams/invitations`,
    ACCEPT_INVITE: (id: number) => `${API_BASE_URL}/teams/invitations/${id}/accept`,
  },
  // Optimization
  OPTIMIZER: {
    OPTIMIZE: `${API_BASE_URL}/optimizer/optimize`,
    ANALYZE: `${API_BASE_URL}/optimizer/analyze`,
    COMPATIBILITY: `${API_BASE_URL}/optimizer/compatibility`,
    CANDIDATES: `${API_BASE_URL}/optimizer/candidates`,
    RECOMMENDATIONS: (teamId: number) => `${API_BASE_URL}/optimizer/recommendations/${teamId}`,
  },
  // Health
  HEALTH: `${API_URL}/health`,
} as const;
// =================================================================
// LOCAL STORAGE KEYS
// =================================================================
export const STORAGE_KEYS = {
  AUTH_TOKEN: AUTH_CONFIG.TOKEN_KEY,
  REFRESH_TOKEN: AUTH_CONFIG.REFRESH_TOKEN_KEY,
  USER: AUTH_CONFIG.USER_KEY,
  THEME: 'theme',
  LANGUAGE: 'language',
  LAST_ROUTE: 'last_route',
  ASSESSMENT_DRAFT: 'assessment_draft_',
} as const;
// =================================================================
// ERROR MESSAGES
// =================================================================
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'Please log in to continue.',
  FORBIDDEN: 'You do not have permission to access this resource.',
  NOT_FOUND: 'The requested resource was not found.',
  SERVER_ERROR: 'An unexpected error occurred. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  TIMEOUT: 'Request timed out. Please try again.',
} as const;
// =================================================================
// ROUTES
// =================================================================
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  DASHBOARD: '/dashboard',
  ASSESSMENTS: '/assessments',
  ASSESSMENT_DETAIL: (id: number) => `/assessments/${id}`,
  TEAMS: '/teams',
  TEAM_DETAIL: (id: number) => `/teams/${id}`,
  TEAM_OPTIMIZER: '/optimizer',
  PROFILE: '/profile',
  SETTINGS: '/settings',
  ANALYTICS: '/analytics',
} as const;
// =================================================================
// HELPERS
// =================================================================
/**
 * Get full API URL for an endpoint
 */
export const getApiUrl = (path: string): string => {
  if (path.startsWith('http')) {
    return path;
  }
  return `${API_BASE_URL}${path.startsWith('/') ? '' : '/'}${path}`;
};
/**
 * Check if feature is enabled
 */
export const isFeatureEnabled = (feature: keyof typeof FEATURES): boolean => {
  return FEATURES[feature] === true;
};
/**
 * Get environment variable with fallback
 */
export const getEnvVar = (key: string, fallback: string = ''): string => {
  return import.meta.env[key] || fallback;
};
/**
 * Log only in development
 */
export const devLog = (...args: any[]): void => {
  if (IS_DEV) {
    console.log('[DEV]', ...args);
  }
};
/**
 * Log errors
 */
export const errorLog = (...args: any[]): void => {
  console.error('[ERROR]', ...args);
  // Send to error tracking service in production
  if (IS_PROD && EXTERNAL_SERVICES.SENTRY_DSN) {
    // Would integrate with Sentry here
  }
};
// =================================================================
// TYPE EXPORTS
// =================================================================
export type Environment = typeof ENV;
export type FeatureFlags = typeof FEATURES;
export type AppConfig = typeof APP_CONFIG;
// =================================================================
// EXPORT DEFAULT CONFIG
// =================================================================
export default {
  ENV,
  IS_DEV,
  IS_PROD,
  IS_STAGING,
  API_URL,
  API_BASE_URL,
  FEATURES,
  AUTH_CONFIG,
  APP_CONFIG,
  EXTERNAL_SERVICES,
  UI_CONFIG,
  VALIDATION,
  ENDPOINTS,
  STORAGE_KEYS,
  ERROR_MESSAGES,
  ROUTES,
} as const;
