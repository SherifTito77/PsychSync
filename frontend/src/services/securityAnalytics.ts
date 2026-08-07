/**
 * Security Analytics API Service
 *
 * Provides API calls for security monitoring and analytics:
 * - Security metrics
 * - Threat indicators
 * - Audit logs
 * - Risk assessment
 *
 * Author: Security Team
 * Version: 1.0
 * Date: 2025-12-26
 */

import api from './api';

// Types
export interface SecurityMetrics {
  timestamp: string;
  status: 'healthy' | 'warning' | 'critical';
  security_score: number;
  total_events: number;
  active_users: number;
  active_ips: number;
  events_by_severity: Record<string, number>;
  events_by_type: Record<string, number>;
}

export interface ThreatIndicator {
  indicator_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  description: string;
  affected_entities: string[];
  mitigation_suggestions: string[];
  timestamp: string;
}

export interface SecurityEvent {
  event_type: string;
  timestamp: string;
  user_id?: number;
  session_id?: string;
  ip_address?: string;
  severity: string;
  details: Record<string, unknown>;
}

export interface TimelineData {
  interval: string;
  hours: number;
  data: Record<string, number>;
}

export interface AuditLog {
  event_type: string;
  severity: string;
  user_id?: number;
  timestamp: string;
  ip_address?: string;
  resource_type?: string;
  resource_id?: number;
  details: Record<string, unknown>;
}

export interface UserRiskProfile {
  user_id: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  analysis_period_hours: number;
  total_events: number;
  threat_indicators_detected: number;
  high_severity_threats: number;
  last_activity: string | null;
}

export interface GetSecurityEventsParams {
  event_type?: string;
  severity?: string;
  hours?: number;
  limit?: number;
}

export interface GetThreatsParams {
  hours?: number;
  severity?: string;
}

export interface GetAuditLogsParams {
  event_type?: string;
  severity?: string;
  user_id?: number;
  hours?: number;
  limit?: number;
}

/**
 * Security Analytics API
 */
const securityAnalyticsApi = {
  /**
   * Get system security status overview
   */
  getSystemStatus: async (): Promise<SecurityMetrics> => {
    const response = await api.get('/security/analytics/status/overview');
    return response.data;
  },

  /**
   * Get active threat indicators
   */
  getActiveThreats: async (params: GetThreatsParams = {}): Promise<ThreatIndicator[]> => {
    const { hours = 24, severity } = params;
    const response = await api.get('/security/analytics/metrics/threats', {
      params: { hours, severity }
    });
    return response.data;
  },

  /**
   * Get security events with filtering
   */
  getSecurityEvents: async (params: GetSecurityEventsParams = {}): Promise<SecurityEvent[]> => {
    const { event_type, severity, hours = 24, limit = 100 } = params;
    const response = await api.get('/security/analytics/metrics/events', {
      params: { event_type, severity, hours, limit }
    });
    return response.data;
  },

  /**
   * Get security event timeline for trends
   */
  getSecurityTimeline: async (hours: number = 24, interval: 'hour' | 'day' = 'hour'): Promise<TimelineData> => {
    const response = await api.get('/security/analytics/metrics/timeline', {
      params: { hours, interval }
    });
    return response.data;
  },

  /**
   * Get audit logs with filtering
   */
  getAuditLogs: async (params: GetAuditLogsParams = {}): Promise<AuditLog[]> => {
    const { event_type, severity, user_id, hours = 24, limit = 100 } = params;
    const response = await api.get('/security/analytics/audit/logs', {
      params: { event_type, severity, user_id, hours, limit }
    });
    return response.data;
  },

  /**
   * Get audit log summary
   */
  getAuditSummary: async (hours: number = 24): Promise<{
    hours: number;
    total_events: number;
    by_type: Record<string, number>;
    by_severity: Record<string, number>;
    unique_users: number;
    unique_ips: number;
  }> => {
    const response = await api.get('/security/analytics/audit/summary', {
      params: { hours }
    });
    return response.data;
  },

  /**
   * Get active security alerts
   */
  getActiveAlerts: async (hours: number = 24): Promise<SecurityEvent[]> => {
    const response = await api.get('/security/analytics/alerts/active', {
      params: { hours }
    });
    return response.data;
  },

  /**
   * Acknowledge a security alert
   */
  acknowledgeAlert: async (alertId: string): Promise<{ status: string; alert_id: string }> => {
    const response = await api.post(`/security/analytics/alerts/${alertId}/acknowledge`);
    return response.data;
  },

  /**
   * Get user risk profile
   */
  getUserRiskProfile: async (userId: number, hours: number = 24): Promise<UserRiskProfile> => {
    const response = await api.get(`/security/analytics/risk/users/${userId}`, {
      params: { hours }
    });
    return response.data;
  },

  /**
   * Get security metrics overview
   */
  getMetricsOverview: async (): Promise<{
    timestamp: string;
    events_last_hour: Record<string, number>;
    events_by_severity: Record<string, number>;
    active_users: number;
    active_ips: number;
    total_events: number;
    threat_indicators_active: number;
    users_with_recent_activity: number;
    ips_with_recent_activity: number;
  }> => {
    const response = await api.get('/security/analytics/metrics/overview');
    return response.data;
  }
};

export default securityAnalyticsApi;
