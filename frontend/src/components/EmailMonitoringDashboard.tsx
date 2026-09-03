import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { getMonitoringStats, MonitoringStats } from '@/services/emailMonitoringService';
import { emailAlertService, AlertNotification } from '@/services/emailAlertService';

const EmailMonitoringDashboard: React.FC = () => {
  const [monitoringData, setMonitoringData] = useState<MonitoringStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<AlertNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      const result = await getMonitoringStats();

      if (result.success && result.data) {
        setMonitoringData(result.data);

        // Check for alerts
        emailAlertService.checkAlerts(result.data);

        // Update recent alerts
        const alerts = emailAlertService.getUnreadAlerts();
        setRecentAlerts(alerts.slice(0, 5)); // Show last 5
        setUnreadCount(alerts.length);

        setLoading(false);
      } else {
        setError(result.error || 'Failed to fetch monitoring data');
        setLoading(false);
      }
    };

    fetchData();

    // Listen for new alerts
    const handleNewAlert = (event: any) => {
      const alert = event.detail as AlertNotification;
      setRecentAlerts((prev) => [alert, ...prev.slice(0, 4)]);
      setUnreadCount((prev) => prev + 1);
    };

    window.addEventListener('emailAlert', handleNewAlert);

    // Auto-refresh every 30 seconds if enabled
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(fetchData, 30000);
    }

    return () => {
      window.removeEventListener('emailAlert', handleNewAlert);
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      security: 'bg-red-500',
      financial: 'bg-green-500',
      professional: 'bg-blue-500',
      social: 'bg-purple-500',
      promotional: 'bg-yellow-500',
      other: 'bg-gray-500',
    };
    return colors[category] || 'bg-gray-500';
  };

  const getActivityLevel = (count: number): { label: string; color: string } => {
    if (count > 50) return { label: 'HIGH', color: 'text-red-500' };
    if (count > 20) return { label: 'MODERATE', color: 'text-yellow-500' };
    return { label: 'NORMAL', color: 'text-green-500' };
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !monitoringData) {
    return (
      <div className="p-6">
        <Card className="bg-red-50 border-red-200">
          <CardContent className="pt-6">
            <div className="text-red-800">
              <p className="font-medium mb-2">⚠️ Failed to load monitoring data</p>
              <p className="text-sm">{error || 'Unknown error'}</p>
            </div>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const hourActivity = getActivityLevel(monitoringData.emails_last_hour);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Email Monitoring Dashboard</h1>
          <p className="text-gray-600">
            Real-time email monitoring and behavioral analytics for sherif.tito.77@gmail.com
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {/* Alert Bell */}
          <div className="relative">
            <button
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              onClick={() => {
                // Mark all as read
                emailAlertService.markAllAsRead();
                setUnreadCount(0);
              }}
              title={`${unreadCount} unread alerts`}
            >
              <span className="text-2xl">🔔</span>
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>
          </div>

          <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${
            monitoringData.status === 'running' ? 'bg-green-100' : 'bg-red-100'
          }`}>
            <div className={`w-3 h-3 rounded-full ${
              monitoringData.status === 'running' ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span className={`font-medium ${
              monitoringData.status === 'running' ? 'text-green-700' : 'text-red-700'
            }`}>
              {monitoringData.status === 'running' ? '● Running' : '● Stopped'}
            </span>
          </div>
          <Button
            variant="outline"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? '🔄 Auto-refresh ON' : '⏸️ Auto-refresh OFF'}
          </Button>
        </div>
      </div>

      {/* Alerts Section */}
      {monitoringData.alerts.length > 0 && (
        <Card className="mb-6 bg-red-50 border-red-200">
          <CardHeader>
            <CardTitle className="text-red-800">⚠️ Active Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {monitoringData.alerts.map((alert, index) => (
                <li key={index} className="text-red-700">• {alert}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Total Emails</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {monitoringData.total_emails.toLocaleString()}
            </div>
            <p className="text-sm text-gray-500 mt-1">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Last Hour</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold ${hourActivity.color}`}>
              {monitoringData.emails_last_hour}
            </div>
            <p className="text-sm text-gray-500 mt-1">{hourActivity.label} activity</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Last 24 Hours</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {monitoringData.emails_last_day}
            </div>
            <p className="text-sm text-gray-500 mt-1">
              ~{Math.round(monitoringData.emails_last_day / 24)}/hour average
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Last 7 Days</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {monitoringData.emails_last_week}
            </div>
            <p className="text-sm text-gray-500 mt-1">
              ~{Math.round(monitoringData.emails_last_week / 7)}/day average
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Category Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>Email Categories (Last 7 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(monitoringData.categories).map(([category, count]) => {
                const total = Object.values(monitoringData.categories).reduce((a, b) => a + b, 0);
                const percentage = ((count / total) * 100).toFixed(1);
                const barWidth = Math.max(2, percentage / 2);

                return (
                  <div key={category}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700 capitalize">
                        {category}
                      </span>
                      <span className="text-sm text-gray-500">{count} ({percentage}%)</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full ${getCategoryColor(category)}`}
                        style={{ width: `${barWidth}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Activity Timeline */}
        <Card>
          <CardHeader>
            <CardTitle>Activity Timeline (Last 24 Hours)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { period: '12AM-6AM', emails: Math.round(monitoringData.emails_last_day * 0.15) },
                { period: '6AM-12PM', emails: Math.round(monitoringData.emails_last_day * 0.35) },
                { period: '12PM-6PM', emails: Math.round(monitoringData.emails_last_day * 0.30) },
                { period: '6PM-12AM', emails: Math.round(monitoringData.emails_last_day * 0.20) },
              ].map((slot, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{slot.period}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-48 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${(slot.emails / monitoringData.emails_last_day) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-700 w-12 text-right">
                      {slot.emails}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Behavioral Insights */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>💡 Behavioral Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="text-sm font-medium text-blue-900 mb-2">🔒 Security Awareness</div>
              <div className="text-2xl font-bold text-blue-700">HIGH</div>
              <p className="text-xs text-blue-600 mt-1">
                {monitoringData.categories.security} security-related emails detected
              </p>
            </div>

            <div className="p-4 bg-green-50 rounded-lg">
              <div className="text-sm font-medium text-green-900 mb-2">💰 Financial Activity</div>
              <div className="text-2xl font-bold text-green-700">ACTIVE</div>
              <p className="text-xs text-green-600 mt-1">
                {monitoringData.categories.financial} financial emails tracked
              </p>
            </div>

            <div className="p-4 bg-purple-50 rounded-lg">
              <div className="text-sm font-medium text-purple-900 mb-2">💼 Professional Network</div>
              <div className="text-2xl font-bold text-purple-700">MODERATE</div>
              <p className="text-xs text-purple-600 mt-1">
                {monitoringData.categories.professional} professional contacts
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Alerts */}
      {recentAlerts.length > 0 && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>🔔 Recent Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-3 rounded-lg border-l-4 ${
                    alert.type === 'critical'
                      ? 'bg-red-50 border-red-500'
                      : alert.type === 'warning'
                      ? 'bg-yellow-50 border-yellow-500'
                      : 'bg-blue-50 border-blue-500'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{alert.title}</div>
                      <div className="text-sm text-gray-600">{alert.body}</div>
                      <div className="text-xs text-gray-400 mt-1">
                        {new Date(alert.timestamp).toLocaleString()}
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        emailAlertService.markAsRead(alert.id);
                        setRecentAlerts((prev) => prev.filter((a) => a.id !== alert.id));
                        setUnreadCount((prev) => Math.max(0, prev - 1));
                      }}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  emailAlertService.markAllAsRead();
                  setRecentAlerts([]);
                  setUnreadCount(0);
                }}
              >
                Mark All as Read
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Last Update */}
      <div className="mt-6 text-center text-sm text-gray-500">
        Last updated: {new Date(monitoringData.last_check).toLocaleString()}
        {autoRefresh && ' (Auto-refresh enabled)'}
      </div>
    </div>
  );
};

export default EmailMonitoringDashboard;
