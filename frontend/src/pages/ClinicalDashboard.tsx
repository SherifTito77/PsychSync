import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import ClinicalAnalytics from '@/components/clinical/ClinicalAnalytics';

interface AlertData {
  id: string;
  alert_type: string;
  severity: string;
  alert_message: string;
  user_id: string;
  user_name: string;
  created_at: string;
  acknowledged: boolean;
  resolution_status: string;
}

interface AssessmentStats {
  total: number;
  this_week: number;
  crisis_alerts: number;
  moderate_high_severity: number;
}

const ClinicalDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [stats, setStats] = useState<AssessmentStats>({
    total: 0,
    this_week: 0,
    crisis_alerts: 0,
    moderate_high_severity: 0,
  });
  const [filter, setFilter] = useState<'all' | 'unacknowledged' | 'critical'>('all');
  const [activeView, setActiveView] = useState<'alerts' | 'analytics'>('alerts');
  const [selectedUserId, setSelectedUserId] = useState<string | undefined>();
  const [timeframe, setTimeframe] = useState<'week' | 'month' | 'quarter' | 'year'>('month');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [alertsResponse, statsResponse] = await Promise.all([
        fetch('/api/v1/clinical/alerts', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }),
        fetch('/api/v1/clinical/stats', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }),
      ]);

      if (alertsResponse.ok) {
        const alertsData = await alertsResponse.json();
        setAlerts(alertsData);
      }

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/clinical/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        setAlerts(prev =>
          prev.map(alert =>
            alert.id === alertId ? { ...alert, acknowledged: true } : alert
          )
        );
      }
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  const handleResolveAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/clinical/alerts/${alertId}/resolve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          resolution_notes: 'Resolved from dashboard',
        }),
      });

      if (response.ok) {
        setAlerts(prev =>
          prev.map(alert =>
            alert.id === alertId ? { ...alert, resolution_status: 'resolved' } : alert
          )
        );
      }
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    switch (filter) {
      case 'unacknowledged':
        return !alert.acknowledged;
      case 'critical':
        return alert.severity === 'critical' || alert.severity === 'high';
      default:
        return true;
    }
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'moderate':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  const getAlertTypeLabel = (alertType: string) => {
    const labels: Record<string, string> = {
      suicide_risk: 'Suicide Risk',
      self_harm: 'Self-Harm',
      severe_symptoms: 'Severe Symptoms',
      high_distress: 'High Distress',
    };
    return labels[alertType] || alertType;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading clinical dashboard...</p>
        </div>
      </div>
    );
  }

  const unacknowledgedCount = alerts.filter(alert => !alert.acknowledged).length;
  const criticalCount = alerts.filter(alert => alert.severity === 'critical' || alert.severity === 'high').length;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Clinical Dashboard</h1>
          <p className="text-gray-600 mb-6">
            Monitor clinical alerts and manage mental health assessments
          </p>

          {/* View Toggle */}
          <div className="flex space-x-2">
            <Button
              variant={activeView === 'alerts' ? 'default' : 'outline'}
              onClick={() => setActiveView('alerts')}
              className="flex items-center space-x-2"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Clinical Alerts</span>
              {unacknowledgedCount > 0 && (
                <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">
                  {unacknowledgedCount}
                </span>
              )}
            </Button>
            <Button
              variant={activeView === 'analytics' ? 'default' : 'outline'}
              onClick={() => setActiveView('analytics')}
              className="flex items-center space-x-2"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span>Analytics & Insights</span>
            </Button>
          </div>
        </div>

        {/* Critical Alert Banner */}
        {(unacknowledgedCount > 0 || criticalCount > 0) && (
          <Alert variant="destructive" className="mb-8">
            <Alert.Heading>Immediate Attention Required</Alert.Heading>
            <p className="mt-2">
              {unacknowledgedCount} unacknowledged alert{unacknowledgedCount !== 1 ? 's' : ''}{' '}
              {criticalCount > 0 && `including ${criticalCount} critical case${criticalCount !== 1 ? 's' : ''}`} require your immediate attention.
            </p>
            <div className="mt-4">
              <Button
                onClick={() => setFilter('critical')}
                variant="destructive"
                className="mr-4"
              >
                View Critical Alerts
              </Button>
              <Button
                onClick={() => setFilter('unacknowledged')}
                variant="outline"
              >
                View Unacknowledged
              </Button>
            </div>
          </Alert>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="bg-blue-100 rounded-full p-3">
                    <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <p className="text-sm font-medium text-gray-500 truncate">Total Assessments</p>
                  <p className="text-2xl font-semibold text-gray-900">{stats.total}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="bg-green-100 rounded-full p-3">
                    <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <p className="text-sm font-medium text-gray-500 truncate">This Week</p>
                  <p className="text-2xl font-semibold text-gray-900">{stats.this_week}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="bg-red-100 rounded-full p-3">
                    <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <p className="text-sm font-medium text-gray-500 truncate">Crisis Alerts</p>
                  <p className="text-2xl font-semibold text-gray-900">{stats.crisis_alerts}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="bg-yellow-100 rounded-full p-3">
                    <svg className="h-6 w-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <p className="text-sm font-medium text-gray-500 truncate">Moderate/High Severity</p>
                  <p className="text-2xl font-semibold text-gray-900">{stats.moderate_high_severity}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button
                  onClick={() => navigate('/clinical/alerts')}
                  className="h-16 flex flex-col items-center justify-center"
                >
                  <svg className="h-6 w-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  Manage Alerts
                </Button>
                <Button
                  onClick={() => navigate('/clinical/referrals')}
                  className="h-16 flex flex-col items-center justify-center"
                  variant="outline"
                >
                  <svg className="h-6 w-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  View Referrals
                </Button>
                <Button
                  onClick={() => navigate('/admin/clinical-analytics')}
                  className="h-16 flex flex-col items-center justify-center"
                  variant="outline"
                >
                  <svg className="h-6 w-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Analytics
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Alerts Section */}
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Recent Clinical Alerts</h2>
            <div className="flex space-x-2">
              <Button
                variant={filter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('all')}
              >
                All ({alerts.length})
              </Button>
              <Button
                variant={filter === 'unacknowledged' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('unacknowledged')}
              >
                Unacknowledged ({unacknowledgedCount})
              </Button>
              <Button
                variant={filter === 'critical' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('critical')}
              >
                Critical ({criticalCount})
              </Button>
            </div>
          </div>

          {/* Conditional Content Rendering */}
          {activeView === 'alerts' ? (
            <div>
              <div className="space-y-4">
                {filteredAlerts.length === 0 ? (
                  <Card>
                    <CardContent className="p-8 text-center">
                      <p className="text-gray-500">
                        No alerts found for the selected filter.
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  filteredAlerts.map((alert) => (
                    <Card key={alert.id} className={!alert.acknowledged ? 'border-l-4 border-l-red-500' : ''}>
                      <CardContent className="p-6">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center mb-2">
                              <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityColor(alert.severity)}`}>
                                {alert.severity.toUpperCase()}
                              </span>
                              <span className="ml-2 text-sm text-gray-500">
                                {getAlertTypeLabel(alert.alert_type)}
                              </span>
                              <span className="ml-2 text-sm text-gray-500">
                                {new Date(alert.created_at).toLocaleString()}
                              </span>
                            </div>
                            <p className="text-gray-900 font-medium mb-2">
                              {alert.user_name} - {alert.alert_message}
                            </p>
                            <p className="text-sm text-gray-600">
                              Status: {alert.resolution_status || 'pending'} |
                              {alert.acknowledged ? ' Acknowledged' : ' Not acknowledged'}
                            </p>
                          </div>
                          <div className="flex space-x-2 ml-4">
                            {!alert.acknowledged && (
                              <Button
                                size="sm"
                                onClick={() => handleAcknowledgeAlert(alert.id)}
                              >
                                Acknowledge
                              </Button>
                            )}
                            {alert.resolution_status !== 'resolved' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleResolveAlert(alert.id)}
                              >
                                Resolve
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => navigate(`/clinical/alerts/${alert.id}`)}
                            >
                              Details
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>

              {filteredAlerts.length > 0 && (
                <div className="mt-6 text-center">
                  <Button
                    onClick={() => navigate('/clinical/alerts')}
                    variant="outline"
                  >
                    View All Alerts
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div>
              {/* Analytics Controls */}
              <div className="mb-6 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <label className="text-sm font-medium text-gray-700">Timeframe:</label>
                  <select
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value as 'week' | 'month' | 'quarter' | 'year')}
                    className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="week">Last Week</option>
                    <option value="month">Last Month</option>
                    <option value="quarter">Last Quarter</option>
                    <option value="year">Last Year</option>
                  </select>
                </div>
                <div className="flex items-center space-x-4">
                  <label className="text-sm font-medium text-gray-700">Patient:</label>
                  <select
                    value={selectedUserId || ''}
                    onChange={(e) => setSelectedUserId(e.target.value || undefined)}
                    className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Patients</option>
                    {/* This would be populated with actual patient data */}
                  </select>
                </div>
              </div>

              {/* Analytics Component */}
              <ClinicalAnalytics
                userId={selectedUserId}
                timeframe={timeframe}
                showTrends={true}
                showComparisons={true}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClinicalDashboard;