/**
 * Biometric Integrations Service
 *
 * API service for wearable device connections, biometric data sync,
 * and health metrics retrieval.
 */

import api from './api';

export interface BiometricProvider {
  id: string;
  name: string;
  auth_type: 'oauth2' | 'oauth1' | 'native_bridge';
  requires_mobile: boolean;
  connected: boolean;
  last_sync: string | null;
  data_points: number;
  scopes: string[];
}

export interface ConnectResult {
  success: boolean;
  auth_type: string;
  auth_url?: string;
  requires_mobile?: boolean;
  message: string;
}

export interface BiometricMetrics {
  success: boolean;
  has_data: boolean;
  period_days?: number;
  total_records?: number;
  sources?: string[];
  latest?: {
    date: string;
    resting_heart_rate: number | null;
    heart_rate_variability: number | null;
    sleep_hours: number | null;
    sleep_quality_score: number | null;
    steps_count: number | null;
    stress_score: number | null;
    recovery_score: number | null;
    activity_minutes: number | null;
  };
  cardiovascular_risk?: {
    risks_detected: boolean;
    risk_count: number;
    risks: Array<{ indicator: string; severity: string; value: number; message: string }>;
    max_severity: string;
  };
  sleep_quality?: Record<string, any>;
  activity_level?: string;
  message?: string;
}

export interface SyncSettings {
  consent_given: boolean;
  data_retention_days: number;
  biometric_collection: boolean;
  biometric_sharing: boolean;
  anonymization_allowed: boolean;
  data_sources: string[];
}

export interface BiometricSubmission {
  data_source: string;
  measurement_date: string;
  resting_heart_rate?: number;
  heart_rate_variability?: number;
  sleep_hours?: number;
  sleep_quality_score?: number;
  deep_sleep_hours?: number;
  rem_sleep_hours?: number;
  steps_count?: number;
  activity_minutes?: number;
  stress_score?: number;
  recovery_score?: number;
  oxygen_saturation?: number;
  device_info?: Record<string, any>;
}

const BASE_PATH = '/biometric';

export const biometricService = {
  async getProviders(): Promise<BiometricProvider[]> {
    const response = await api.get<{ success: boolean; providers: BiometricProvider[] }>(
      `${BASE_PATH}/providers`
    );
    return response.data.providers;
  },

  async connectProvider(provider: string, redirectUri?: string): Promise<ConnectResult> {
    const response = await api.post<ConnectResult>(
      `${BASE_PATH}/connect/${provider}`,
      { redirect_uri: redirectUri }
    );
    return response.data;
  },

  async disconnectProvider(provider: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post<{ success: boolean; message: string }>(
      `${BASE_PATH}/disconnect/${provider}`
    );
    return response.data;
  },

  async getMetrics(days: number = 30, source?: string): Promise<BiometricMetrics> {
    const params: Record<string, any> = { days };
    if (source) params.source = source;
    const response = await api.get<BiometricMetrics>(`${BASE_PATH}/metrics`, { params });
    return response.data;
  },

  async submitData(data: BiometricSubmission): Promise<{ success: boolean; data_id: string; risk_indicators: any }> {
    const response = await api.post(`${BASE_PATH}/data`, data);
    return response.data;
  },

  async getSettings(): Promise<SyncSettings> {
    const response = await api.get<{ success: boolean } & SyncSettings>(`${BASE_PATH}/settings`);
    return response.data;
  },

  async updateSettings(settings: {
    sync_frequency_minutes?: number;
    data_retention_days?: number;
    share_anonymized?: boolean;
    enable_stress_alerts?: boolean;
    allow_manager_view?: boolean;
  }): Promise<{ success: boolean; message: string }> {
    const response = await api.put(`${BASE_PATH}/settings`, settings);
    return response.data;
  },
};

export default biometricService;
