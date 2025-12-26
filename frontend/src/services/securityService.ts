// Security monitoring service
import apiClient from './api';

export interface SecurityMetrics {
  time_range: {
    hours: number;
    since: string;
    until: string;
  };
  authentication: {
    total_login_attempts: number;
    successful_logins: number;
    failed_logins: number;
    unique_users_affected: number;
    blocked_by_rate_limit: number;
  };
  authorization: {
    total_requests: number;
    authorized_requests: number;
    unauthorized_requests: number;
    idor_attempts_prevented: number;
    ownership_checks_failed: number;
  };
  csrf: {
    csrf_tokens_issued: number;
    csrf_validations: number;
    csrf_violations: number;
    blocked_requests: number;
  };
  suspicious_activity: {
    multiple_failed_logins: number;
    unusual_access_patterns: number;
    rapid_requests: number;
    blocked_ips: number;
  };
  top_blocked_ips: Array<{
    ip: string;
    attempts: number;
    reason: string;
  }>;
  recent_events: SecurityEvent[];
}

export interface SecurityEvent {
  timestamp: string;
  event_type: string;
  severity: 'info' | 'low' | 'medium' | 'high';
  ip: string;
  user: string | null;
  details: string;
  outcome: string;
}

export interface SecurityEventsResponse {
  total_events: number;
  events: SecurityEvent[];
  summary: Record<string, number>;
}

export interface TimelineEntry {
  hour: string;
  failed_logins: number;
  csrf_violations: number;
  auth_failures: number;
  total_requests: number;
}

export interface SecurityTimelineResponse {
  time_range_hours: number;
  timeline: TimelineEntry[];
}

// Fetch security metrics
export const getSecurityMetrics = async (hours: number = 24): Promise<SecurityMetrics> => {
  const response = await apiClient.get<SecurityMetrics>(`/dashboard/metrics?hours=${hours}`);
  return response.data;
};

// Fetch security events
export const getSecurityEvents = async (
  limit: number = 50,
  eventType?: string
): Promise<SecurityEventsResponse> => {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (eventType) {
    params.append('event_type', eventType);
  }
  const response = await apiClient.get<SecurityEventsResponse>(`/dashboard/events?${params}`);
  return response.data;
};

// Fetch security timeline
export const getSecurityTimeline = async (hours: number = 24): Promise<SecurityTimelineResponse> => {
  const response = await apiClient.get<SecurityTimelineResponse>(`/dashboard/stats/timeline?hours=${hours}`);
  return response.data;
};

// Send test alert
export const sendTestAlert = async (alertType: string): Promise<{ message: string; alert_type: string; timestamp: string }> => {
  const formData = new FormData();
  formData.append('alert_type', alertType);
  const response = await apiClient.post(`/dashboard/test-alert`, formData);
  return response.data;
};
