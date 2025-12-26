/**
 * Security Monitoring Dashboard
 *
 * Displays real-time security metrics including:
 * - Authentication events (logins, failures)
 * - Authorization stats (allowed/blocked requests)
 * - CSRF violations
 * - Suspicious activity alerts
 * - Recent security events
 * - Timeline visualization
 *
 * Admin-only access required
 */

import React, { useState, useEffect } from 'react';
import {
  getSecurityMetrics,
  getSecurityEvents,
  getSecurityTimeline,
  sendTestAlert,
  SecurityMetrics,
  SecurityEvent,
  TimelineEntry
} from '../../services/securityService';
import { useAuth } from '../../contexts/AuthContext';

// Severity color mapping
const SEVERITY_COLORS: Record<string, string> = {
  info: 'bg-blue-100 text-blue-800',
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-red-100 text-red-800'
};

const SEVERITY_BORDER_COLORS: Record<string, string> = {
  info: 'border-blue-500',
  low: 'border-green-500',
  medium: 'border-yellow-500',
  high: 'border-red-500'
};

const SecurityDashboard: React.FC = () => {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<SecurityMetrics | null>(null);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState(24);
  const [eventFilter, setEventFilter] = useState<string>('');

  // Check if user is admin
  const isAdmin = user?.role === 'admin';

  // Fetch security data
  const fetchSecurityData = async () => {
    if (!isAdmin) {
      setError('Admin access required');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const [metricsData, eventsData, timelineData] = await Promise.all([
        getSecurityMetrics(timeRange),
        getSecurityEvents(50, eventFilter || undefined),
        getSecurityTimeline(timeRange)
      ]);

      setMetrics(metricsData);
      setEvents(eventsData.events);
      setTimeline(timelineData.timeline);
    } catch (err) {
      console.error('Failed to fetch security data:', err);
      setError('Failed to load security metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSecurityData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchSecurityData, 30000);
    return () => clearInterval(interval);
  }, [isAdmin, timeRange, eventFilter]);

  const handleSendTestAlert = async (alertType: string) => {
    try {
      await sendTestAlert(alertType);
      alert(`Test alert "${alertType}" sent! Check console for output.`);
    } catch (err) {
      console.error('Failed to send test alert:', err);
      alert('Failed to send test alert');
    }
  };

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md text-center">
          <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">Admin access required to view security dashboard</p>
        </div>
      </div>
    );
  }

  if (loading && !metrics) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading security metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md text-center">
          <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600">{error}</p>
          <button
            onClick={fetchSecurityData}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  // Calculate success rates
  const loginSuccessRate = metrics.authentication.total_login_attempts > 0
    ? ((metrics.authentication.successful_logins / metrics.authentication.total_login_attempts) * 100).toFixed(1)
    : '0';

  const authzSuccessRate = metrics.authorization.total_requests > 0
    ? ((metrics.authorization.authorized_requests / metrics.authorization.total_requests) * 100).toFixed(1)
    : '0';

  const csrfViolationRate = metrics.csrf.csrf_validations > 0
    ? ((metrics.csrf.csrf_violations / metrics.csrf.csrf_validations) * 100).toFixed(2)
    : '0';

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Security Dashboard</h1>
              <p className="text-gray-600 mt-1">Real-time security monitoring and threat detection</p>
            </div>
            <div className="mt-4 md:mt-0 flex items-center space-x-4">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(Number(e.target.value))}
                className="px-3 py-2 border rounded-lg text-sm"
              >
                <option value={1}>Last 1 hour</option>
                <option value={6}>Last 6 hours</option>
                <option value={24}>Last 24 hours</option>
                <option value={168}>Last 7 days</option>
              </select>
              <button
                onClick={fetchSecurityData}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm flex items-center"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Alert Actions */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">Test Alert System</h3>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleSendTestAlert('suspicious_activity')}
              className="px-3 py-1 bg-white border border-blue-300 rounded text-sm hover:bg-blue-100"
            >
              Test Suspicious Activity
            </button>
            <button
              onClick={() => handleSendTestAlert('csrf_violation')}
              className="px-3 py-1 bg-white border border-blue-300 rounded text-sm hover:bg-blue-100"
            >
              Test CSRF Violation
            </button>
            <button
              onClick={() => handleSendTestAlert('failed_login')}
              className="px-3 py-1 bg-white border border-blue-300 rounded text-sm hover:bg-blue-100"
            >
              Test Failed Login
            </button>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {/* Authentication */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Authentication</p>
              <p className="text-2xl font-bold text-gray-900">{loginSuccessRate}%</p>
              <p className="text-xs text-gray-500">{metrics.authentication.successful_logins} / {metrics.authentication.total_login_attempts} successful</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
          </div>
          {metrics.authentication.failed_logins > 0 && (
            <div className="mt-3 pt-3 border-t">
              <p className="text-xs text-red-600">{metrics.authentication.failed_logins} failed attempts</p>
            </div>
          )}
        </div>

        {/* Authorization */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Authorization</p>
              <p className="text-2xl font-bold text-gray-900">{authzSuccessRate}%</p>
              <p className="text-xs text-gray-500">{metrics.authorization.authorized_requests} / {metrics.authorization.total_requests} authorized</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            </div>
          </div>
          {metrics.authorization.unauthorized_requests > 0 && (
            <div className="mt-3 pt-3 border-t">
              <p className="text-xs text-red-600">{metrics.authorization.unauthorized_requests} unauthorized attempts</p>
            </div>
          )}
        </div>

        {/* CSRF Protection */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">CSRF Violations</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.csrf.csrf_violations}</p>
              <p className="text-xs text-gray-500">{csrfViolationRate}% violation rate</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
          </div>
          {metrics.csrf.csrf_violations > 0 && (
            <div className="mt-3 pt-3 border-t">
              <p className="text-xs text-green-600">{metrics.csrf.blocked_requests} blocked requests</p>
            </div>
          )}
        </div>

        {/* Suspicious Activity */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Suspicious Activity</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.suspicious_activity.blocked_ips}</p>
              <p className="text-xs text-gray-500">IPs blocked</p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
          </div>
          {metrics.suspicious_activity.multiple_failed_logins > 0 && (
            <div className="mt-3 pt-3 border-t">
              <p className="text-xs text-red-600">{metrics.suspicious_activity.multiple_failed_logins} multi-failure attacks</p>
            </div>
          )}
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Top Blocked IPs */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Blocked IPs</h3>
          {metrics.top_blocked_ips.length === 0 ? (
            <p className="text-gray-500 text-sm">No blocked IPs in this time range</p>
          ) : (
            <div className="space-y-3">
              {metrics.top_blocked_ips.map((ip, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div className="flex-1">
                    <p className="font-mono text-sm font-medium text-gray-900">{ip.ip}</p>
                    <p className="text-xs text-gray-600">{ip.reason}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-red-600">{ip.attempts}</p>
                    <p className="text-xs text-gray-500">attempts</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Timeline Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Security Events Timeline</h3>
          <div className="space-y-2">
            {timeline.map((entry, index) => (
              <div key={index} className="flex items-center text-xs">
                <div className="w-24 text-gray-500 flex-shrink-0">
                  {new Date(entry.hour).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
                <div className="flex-1 flex items-center space-x-1">
                  <div
                    className="bg-red-400"
                    style={{ width: `${Math.min(entry.failed_logins * 20, 100)}%`, height: '8px' }}
                    title={`Failed logins: ${entry.failed_logins}`}
                  />
                  <div
                    className="bg-yellow-400"
                    style={{ width: `${Math.min(entry.csrf_violations * 50, 100)}%`, height: '8px' }}
                    title={`CSRF violations: ${entry.csrf_violations}`}
                  />
                  <div
                    className="bg-blue-400"
                    style={{ width: `${Math.min((entry.total_requests / 100), 100)}%`, height: '8px' }}
                    title={`Total requests: ${entry.total_requests}`}
                  />
                </div>
                <div className="ml-2 flex-shrink-0">
                  <span className="inline-block w-3 h-3 bg-red-400 rounded-sm mr-1" title="Failed logins" />
                  <span className="inline-block w-3 h-3 bg-yellow-400 rounded-sm mr-1" title="CSRF" />
                  <span className="inline-block w-3 h-3 bg-blue-400 rounded-sm" title="Requests" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Events */}
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Recent Security Events</h3>
            <select
              value={eventFilter}
              onChange={(e) => setEventFilter(e.target.value)}
              className="px-3 py-1 border rounded text-sm"
            >
              <option value="">All Events</option>
              <option value="failed_login">Failed Logins</option>
              <option value="csrf_violation">CSRF Violations</option>
              <option value="authorization_failed">Authorization Failures</option>
              <option value="rate_limit_exceeded">Rate Limiting</option>
            </select>
          </div>
          {events.length === 0 ? (
            <p className="text-gray-500 text-sm">No security events in this time range</p>
          ) : (
            <div className="space-y-3">
              {events.map((event, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border-l-4 ${SEVERITY_BORDER_COLORS[event.severity]} bg-gray-50`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${SEVERITY_COLORS[event.severity]}`}>
                          {event.severity.toUpperCase()}
                        </span>
                        <span className="font-mono text-xs text-gray-600">{event.event_type}</span>
                      </div>
                      <p className="text-sm text-gray-900">{event.details}</p>
                      <div className="mt-2 flex items-center space-x-4 text-xs text-gray-600">
                        <span>IP: <span className="font-mono">{event.ip}</span></span>
                        {event.user && <span>User: {event.user}</span>}
                        <span>{new Date(event.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        event.outcome === 'blocked' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {event.outcome}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SecurityDashboard;
