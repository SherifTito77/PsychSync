/**
 * Email Monitoring Service
 * Fetches real-time monitoring data from the backend
 */

import api from './api';

export interface MonitoringStats {
  total_emails: number;
  emails_last_hour: number;
  emails_last_day: number;
  emails_last_week: number;
  categories: {
    security: number;
    financial: number;
    professional: number;
    social: number;
    promotional: number;
    other: number;
  };
  alerts: string[];
  last_check: string;
  status: 'running' | 'stopped' | 'error';
}

export interface MonitoringHistory {
  timestamp: string;
  emails_processed: number;
  categories: Record<string, number>;
  alerts: string[];
}

/**
 * Get current email monitoring statistics
 */
export const getMonitoringStats = async (): Promise<{
  success: boolean;
  data?: MonitoringStats;
  error?: string;
}> => {
  try {
    const response = await api.get('/email-monitoring/stats');
    return {
      success: true,
      data: response.data,
    };
  } catch (error: any) {
    console.error('Failed to fetch monitoring stats:', error);
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch monitoring statistics',
    };
  }
};

/**
 * Get monitoring history for the last N days
 */
export const getMonitoringHistory = async (days: number = 7): Promise<{
  success: boolean;
  data?: MonitoringHistory[];
  error?: string;
}> => {
  try {
    const response = await api.get(`/email-monitoring/history?days=${days}`);
    return {
      success: true,
      data: response.data.history || [],
    };
  } catch (error: any) {
    console.error('Failed to fetch monitoring history:', error);
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch monitoring history',
    };
  }
};

/**
 * Get monitoring service status
 */
export const getMonitorServiceStatus = async (): Promise<{
  success: boolean;
  running?: boolean;
  pid?: number;
  lastCheck?: string;
  error?: string;
}> => {
  try {
    // Check if the macOS service is running
    const response = await fetch('/api/monitor/status', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to check service status');
    }

    const data = await response.json();
    return {
      success: true,
      running: data.running || false,
      pid: data.pid,
      lastCheck: data.last_check,
    };
  } catch (error: any) {
    console.error('Failed to check service status:', error);
    return {
      success: false,
      error: 'Failed to check monitoring service status',
    };
  }
};
