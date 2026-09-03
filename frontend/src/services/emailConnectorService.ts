/**
 * Email Connector Service
 * API service for email integration and analytics
 */

import api from './api';

export interface EmailConnection {
  connection_id: string;
  provider: string;
  email_address: string;
  connection_status: 'connected' | 'disconnected' | 'failed';
  sync_enabled: boolean;
  created_at: string;
  last_sync?: string;
}

export interface EmailProvider {
  id: string;
  name: string;
  auth_type: 'OAuth2' | 'Basic';
  features: string[];
  setup_difficulty: 'Easy' | 'Intermediate' | 'Advanced';
}

export interface ConnectionSetupParams {
  provider: string;
  email_address: string;
  connection_parameters: Record<string, any>;
  permissions?: string[];
  sync_settings?: Record<string, any>;
  auto_sync_enabled?: boolean;
}

export interface IMAPConnectionParams {
  email_address: string;
  server: string;
  port: number;
  use_ssl: boolean;
  username?: string;
  password: string;
  sync_folder?: string;
}

/**
 * Get all available email providers
 */
export const getAvailableProviders = async (): Promise<{
  success: boolean;
  providers: Record<string, EmailProvider>;
}> => {
  const response = await api.get('/email-connector/providers/available');
  return response.data;
};

/**
 * Get all email connections for current user
 */
export const getEmailConnections = async (): Promise<{
  success: boolean;
  connections: EmailConnection[];
  total_connections: number;
}> => {
  const response = await api.get('/email-connector/connections');
  return response.data;
};

/**
 * Setup email connection
 */
export const setupEmailConnection = async (
  params: ConnectionSetupParams
): Promise<{
  success: boolean;
  connection_id?: string;
  connection_status: string;
  error_message?: string;
}> => {
  const response = await api.post('/email-connector/connection/setup', params);
  return response.data;
};

/**
 * Disconnect email account
 */
export const disconnectEmail = async (
  connectionId: string,
  removeData: boolean = false
): Promise<{
  success: boolean;
  connection_id: string;
  data_removed: boolean;
}> => {
  const response = await api.delete(`/email-connector/connection/${connectionId}`, {
    data: { remove_data: removeData },
  });
  return response.data;
};

/**
 * Get OAuth authorization URL
 */
export const getOAuthUrl = async (
  provider: string,
  redirectUri?: string
): Promise<{
  success: boolean;
  auth_url: string;
  state: string;
}> => {
  const response = await api.post('/email-connector/oauth/url', {
    provider,
    redirect_uri: redirectUri,
  });
  return response.data;
};

/**
 * Handle OAuth callback
 */
export const handleOAuthCallback = async (
  provider: string,
  code: string,
  state: string
): Promise<{
  success: boolean;
  connection_id?: string;
  email_address?: string;
  error?: string;
}> => {
  const response = await api.post('/email-connector/oauth/callback', {
    provider,
    code,
    state,
  });
  return response.data;
};

/**
 * Test IMAP connection
 */
export const testIMAPConnection = async (
  params: IMAPConnectionParams
): Promise<{
  success: boolean;
  connection_status: string;
  error_message?: string;
}> => {
  const response = await api.post('/email-connector/connection/test-imap', params);
  return response.data;
};

/**
 * Trigger manual email sync
 */
export const triggerManualSync = async (
  connectionId: string,
  syncOptions: Record<string, any> = {}
): Promise<{
  success: boolean;
  sync_task_id: string;
  sync_status: string;
  emails_to_sync: number;
}> => {
  const response = await api.post('/email-connector/sync/manual', {
    connection_id: connectionId,
    sync_options: syncOptions,
  });
  return response.data;
};

/**
 * Get email sync status
 */
export const getSyncStatus = async (
  connectionId: string
): Promise<{
  success: boolean;
  sync_status: Record<string, any>;
}> => {
  const response = await api.get(`/email-connector/sync/status/${connectionId}`);
  return response.data;
};

/**
 * Update email configuration
 */
export const updateEmailConfiguration = async (
  connectionId: string,
  configurationUpdates: Record<string, any>
): Promise<{
  success: boolean;
  updated_configuration: Record<string, any>;
}> => {
  const response = await api.post('/email-connector/configuration/update', {
    connection_id: connectionId,
    configuration_updates: configurationUpdates,
  });
  return response.data;
};

/**
 * Get email analytics dashboard
 */
export const getEmailAnalyticsDashboard = async (
  timePeriod: string = '30d'
): Promise<{
  success: boolean;
  dashboard_data: Record<string, any>;
}> => {
  const response = await api.get('/email-connector/analytics/dashboard', {
    params: { time_period: timePeriod },
  });
  return response.data;
};

/**
 * Start email communication analytics
 */
export const startEmailAnalytics = async (
  dateRange: { start_date: string; end_date: string },
  analysisCategories: string[]
): Promise<{
  success: boolean;
  total_emails_analyzed: number;
  communication_insights: string[];
}> => {
  const response = await api.post('/email-connector/analytics/communication', {
    date_range: dateRange,
    analysis_categories: analysisCategories,
    email_filters: {},
  });
  return response.data;
};

export default {
  getAvailableProviders,
  getEmailConnections,
  setupEmailConnection,
  disconnectEmail,
  getOAuthUrl,
  handleOAuthCallback,
  testIMAPConnection,
  triggerManualSync,
  getSyncStatus,
  updateEmailConfiguration,
  getEmailAnalyticsDashboard,
  startEmailAnalytics,
};
