/**
 * Security Monitoring Dashboard Component
 *
 * Real-time security monitoring dashboard with:
 * - Authentication metrics
 * - Authorization metrics
 * - Rate limiting status
 * - Failed login attempts
 * - Suspicious activity alerts
 * - Security event timeline
 */

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api/v1` : (import.meta.env.PROD ? '/api/v1' : 'http://localhost:8000/api/v1');

const securityService = {
  getSecurityMetrics: async (timeRange: string) => {
    const response = await axios.get(`${API_BASE}/security/metrics?range=${timeRange}`);
    return response.data;
  },
  getSecurityTimeline: async (timeRange: string) => {
    const response = await axios.get(`${API_BASE}/security/timeline?range=${timeRange}`);
    return response.data;
  },
  sendTestAlert: async (alert: any) => {
    const response = await axios.post(`${API_BASE}/security/test-alert`, alert);
    return response.data;
  }
};

interface DashboardSecurityData {
  authentication: {
    total_login_attempts: number;
    successful_logins: number;
    failed_logins: number;
    login_success_rate: number;
    unique_users_logged_in: number;
    avg_session_duration: number;
  };
  authorization: {
    total_requests: number;
    successful_requests: number;
    denied_requests: number;
    authz_success_rate: number;
    most_denied_resource: string;
    high_privilege_denials: number;
  };
  rate_limiting: {
    total_rate_limited: number;
    top_offenders: Array<{
      ip: string;
      attempts: number;
    }>;
    locked_accounts: number;
  };
  csrf: {
    total_csrf_violations: number;
    blocked_attacks: number;
  };
  suspicious: {
    total_incidents: number;
    active_investigations: number;
    incidents: Array<{
      id: string;
      type: string;
      severity: 'low' | 'medium' | 'high' | 'critical';
      description: string;
      timestamp: string;
      status: string;
    }>;
  };
}

interface TimelineEvent {
  timestamp: string;
  event_type: string;
  user_id?: string;
  ip_address?: string;
  details: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
}

export const SecurityMonitoringDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardSecurityData | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState<number>(24); // hours

  useEffect(() => {
    loadSecurityData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(loadSecurityData, 30000);

    return () => clearInterval(interval);
  }, [selectedTimeRange]);

  const loadSecurityData = async () => {
    try {
      setLoading(true);

      // Load metrics
      const metricsData = await securityService.getSecurityMetrics(String(selectedTimeRange));
      setMetrics(metricsData as DashboardSecurityData);

      // Load timeline
      const timelineData = await securityService.getSecurityTimeline(String(selectedTimeRange));
      setTimeline(timelineData as TimelineEvent[]);

      setError(null);
    } catch (err) {
      console.error('Failed to load security data:', err);
      setError('Failed to load security data');
    } finally {
      setLoading(false);
    }
  };

  const handleSendTestAlert = async () => {
    try {
      await securityService.sendTestAlert({
        type: 'TEST_ALERT',
        severity: 'warning',
        message: 'This is a test security alert'
      });

      // Refresh data
      await loadSecurityData();
    } catch (err) {
      console.error('Failed to send test alert:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
        <span className="ml-4 text-gray-600">Loading security data...</span>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <Card className="p-6">
        <div className="text-red-600">Error: {error || 'Failed to load security data'}</div>
      </Card>
    );
  }

  const loginSuccessRate = metrics.authentication.total_login_attempts > 0
    ? ((metrics.authentication.successful_logins / metrics.authentication.total_login_attempts) * 100).toFixed(1)
    : '0';

  const authzSuccessRate = metrics.authorization.total_requests > 0
    ? ((metrics.authorization.successful_requests / metrics.authorization.total_requests) * 100).toFixed(1)
    : '0';

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-red-600';
      case 'error': return 'bg-red-600';
      case 'medium': return 'bg-orange-500';
      case 'warning': return 'bg-yellow-500';
      case 'low': return 'bg-blue-500';
      case 'info': return 'bg-blue-400';
      default: return 'bg-gray-500';
    }
  };

  const getSeverityTextColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600';
      case 'high': return 'text-red-600';
      case 'error': return 'text-red-600';
      case 'medium': return 'text-orange-600';
      case 'warning': return 'text-yellow-600';
      case 'low': return 'text-blue-600';
      case 'info': return 'text-blue-500';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Security Monitoring Dashboard</h2>
          <p className="text-gray-600 mt-1">Real-time security metrics and alerts</p>
        </div>

        <div className="flex items-center space-x-4">
          {/* Time Range Selector */}
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            <option value={1}>Last 1 hour</option>
            <option value={6}>Last 6 hours</option>
            <option value={24}>Last 24 hours</option>
            <option value={168}>Last 7 days</option>
          </select>

          {/* Test Alert Button */}
          <button
            onClick={handleSendTestAlert}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
          >
            Send Test Alert
          </button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Authentication Card */}
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Authentication</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {metrics.authentication.successful_logins}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {loginSuccessRate}% success rate
              </p>
            </div>
            <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
              <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className="mt-4 text-sm">
            <span className="text-red-600">{metrics.authentication.failed_logins} failed</span>
            <span className="mx-2 text-gray-400">|</span>
            <span className="text-gray-600">{metrics.authentication.total_login_attempts} total</span>
          </div>
        </Card>

        {/* Authorization Card */}
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Authorization</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {authzSuccessRate}%
              </p>
              <p className="text-sm text-gray-600 mt-1">
                Success rate
              </p>
            </div>
            <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
              <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016zM4.5 9a7.5 7.5 0 1115 0 7.5 7.5 0 01-15 0z" />
              </svg>
            </div>
          </div>
          <div className="mt-4 text-sm">
            <span className="text-orange-600">{metrics.authorization.denied_requests} denied</span>
            <span className="mx-2 text-gray-400">|</span>
            <span className="text-gray-600">{metrics.authorization.total_requests} total</span>
          </div>
        </Card>

        {/* Rate Limiting Card */}
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Rate Limiting</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {metrics.rate_limiting.total_rate_limited}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                Requests blocked
              </p>
            </div>
            <div className="h-12 w-12 bg-yellow-100 rounded-full flex items-center justify-center">
              <svg className="h-6 w-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
          </div>
          <div className="mt-4 text-sm">
            <span className="text-red-600">{metrics.rate_limiting.locked_accounts} locked</span>
            <span className="mx-2 text-gray-400">|</span>
            <span className="text-gray-600">{metrics.csrf.total_csrf_violations} CSRF</span>
          </div>
        </Card>

        {/* Suspicious Activity Card */}
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Suspicious Activity</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {metrics.suspicious.total_incidents}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                Incidents detected
              </p>
            </div>
            <div className="h-12 w-12 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.932-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.932 3z" />
              </svg>
            </div>
          </div>
          <div className="mt-4 text-sm">
            <span className="text-orange-600">{metrics.suspicious.active_investigations} investigating</span>
            <span className="mx-2 text-gray-400">|</span>
            <span className="text-gray-600">{metrics.csrf.blocked_attacks} blocked</span>
          </div>
        </Card>
      </div>

      {/* Charts and Lists */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Security Timeline */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Security Event Timeline</h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {timeline.map((event, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className={`h-2 w-2 rounded-full mt-2 ${getSeverityColor(event.severity)}`} />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-gray-900">{event.event_type}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{event.details}</p>
                  {event.user_id && (
                    <p className="text-xs text-gray-500 mt-1">
                      User: {event.user_id} | IP: {event.ip_address}
                    </p>
                  )}
                </div>
              </div>
            ))}
            {timeline.length === 0 && (
              <p className="text-gray-500 text-center py-8">No security events in this time range</p>
            )}
          </div>
        </Card>

        {/* Top Offenders */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Rate Limit Top Offenders</h3>
          <div className="space-y-3">
            {metrics.rate_limiting.top_offenders.map((offender, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{offender.ip}</p>
                  <p className="text-sm text-gray-600">
                    {offender.attempts} attempts
                  </p>
                </div>
                <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm">
                  Rate Limited
                </span>
              </div>
            ))}
            {metrics.rate_limiting.top_offenders.length === 0 && (
              <p className="text-gray-500 text-center py-8">No rate limit violations</p>
              )}
          </div>
        </Card>
      </div>

      {/* Suspicious Incidents Table */}
      {metrics.suspicious.incidents.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Suspicious Incidents</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Time
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {metrics.suspicious.incidents.map((incident) => (
                  <tr key={incident.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {incident.type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        incident.severity === 'critical' ? 'bg-red-100 text-red-800' :
                        incident.severity === 'high' ? 'bg-red-100 text-red-800' :
                        incident.severity === 'medium' ? 'bg-orange-100 text-orange-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {incident.severity.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {incident.description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        incident.status === 'investigating' ? 'bg-yellow-100 text-yellow-800' :
                        incident.status === 'resolved' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {incident.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(incident.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};

export default SecurityMonitoringDashboard;
