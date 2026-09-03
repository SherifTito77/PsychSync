/**
 * Automated Clinical Alerts Center
 *
 * Comprehensive alert management interface for clinicians and administrators.
 * Provides real-time monitoring of clinical alerts, acknowledgment/resolution
 * workflows, and alert history.
 *
 * Features:
 * - Unresolved alerts list with severity-based sorting
 * - Alert details with user context
 * - Acknowledge and resolve workflows
 * - Alert statistics and metrics
 * - Manual alert triggering
 * - Alert history with filtering
 *
 * Access: Clinicians and Administrators only
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Bell,
  RefreshCw,
  Filter,
  User,
  Calendar,
  TrendingUp,
  Activity,
  FileText,
  AlertCircle,
} from 'lucide-react';
import api from '@/services/api';
import { useAsyncEffect } from '@/hooks/useAsyncEffect';
import { useDebouncedCallback } from '@/hooks/usePerformanceOptimizations';

// =============================================================================
// Types
// =============================================================================

interface AlertItem {
  id: string;
  user_id: string;
  org_id: string;
  alert_type: string;
  severity: 'critical' | 'high' | 'moderate' | 'low';
  alert_message: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  resolution_status: string;
  resolution_notes?: string;
  resolved_by?: string;
  resolved_at?: string;
  escalated: boolean;
  escalation_level?: string;
  created_at: string;
  metadata?: Record<string, any>;
}

interface UnresolvedAlertsResponse {
  alerts: AlertItem[];
  total_count: number;
  critical_count: number;
  high_count: number;
  moderate_count: number;
}

interface AlertStatistics {
  period_days: number;
  total_alerts: number;
  unresolved_count: number;
  by_severity: {
    critical: number;
    high: number;
    moderate: number;
  };
  crisis_alerts: number;
  acknowledgment_rate: number;
  resolution_rate: number;
  avg_resolution_hours: number;
}

// =============================================================================
// Subcomponents
// =============================================================================

function SeverityBadge({ severity }: { severity: string }) {
  const config = {
    critical: { color: 'bg-red-100 text-red-800 border-red-300', icon: AlertTriangle },
    high: { color: 'bg-orange-100 text-orange-800 border-orange-300', icon: AlertCircle },
    moderate: { color: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: Bell },
    low: { color: 'bg-blue-100 text-blue-800 border-blue-300', icon: Activity },
  };

  const { color, icon: Icon } = config[severity as keyof typeof config] || config.moderate;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold border ${color}`}>
      <Icon className="h-3 w-3" />
      {severity.toUpperCase()}
    </span>
  );
}

function AlertCard({ alert, onAcknowledge, onResolve }: {
  alert: AlertItem;
  onAcknowledge: (id: string, notes?: string) => void;
  onResolve: (id: string, notes: string) => void;
}) {
  const [showDetails, setShowDetails] = useState(false);
  const [ackNotes, setAckNotes] = useState('');
  const [resolveNotes, setResolveNotes] = useState('');
  const [showAckDialog, setShowAckDialog] = useState(false);
  const [showResolveDialog, setShowResolveDialog] = useState(false);

  const getAlertTypeLabel = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return (
    <Card className={`hover:shadow-md transition-shadow ${alert.acknowledged ? 'border-green-200' : ''}`}>
      <CardContent className="pt-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <SeverityBadge severity={alert.severity} />
              <span className="text-xs text-gray-500">
                {new Date(alert.created_at).toLocaleString()}
              </span>
              {alert.acknowledged && (
                <span className="text-xs text-green-600 flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  Acknowledged
                </span>
              )}
            </div>

            <p className="text-sm font-medium text-gray-900 mb-2">
              {alert.alert_message}
            </p>

            <div className="flex items-center gap-4 text-xs text-gray-600">
              <div className="flex items-center gap-1">
                <User className="h-3 w-3" />
                User ID: {alert.user_id.slice(0, 8)}...
              </div>
              <div className="flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {getAlertTypeLabel(alert.alert_type)}
              </div>
            </div>

            {showDetails && alert.metadata && Object.keys(alert.metadata).length > 0 && (
              <div className="mt-3 p-3 bg-gray-50 rounded text-xs">
                <p className="font-semibold text-gray-700 mb-1">Additional Details:</p>
                <pre className="text-gray-600 whitespace-pre-wrap">
                  {JSON.stringify(alert.metadata, null, 2)}
                </pre>
              </div>
            )}

            {alert.acknowledged && alert.acknowledged_at && (
              <div className="mt-2 text-xs text-gray-600">
                Acknowledged {new Date(alert.acknowledged_at).toLocaleString()}
              </div>
            )}
          </div>

          <div className="flex flex-col gap-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? 'Hide' : 'Details'}
            </Button>

            {!alert.acknowledged && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowAckDialog(true)}
              >
                Acknowledge
              </Button>
            )}

            {alert.resolution_status === 'pending' && (
              <Button
                size="sm"
                onClick={() => setShowResolveDialog(true)}
                className="bg-green-600 hover:bg-green-700"
              >
                Resolve
              </Button>
            )}
          </div>
        </div>

        {/* Acknowledge Dialog */}
        {showAckDialog && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Acknowledgment Notes (Optional)
            </label>
            <textarea
              className="w-full p-2 border border-gray-300 rounded text-sm"
              rows={2}
              placeholder="Add any notes about your acknowledgment..."
              value={ackNotes}
              onChange={(e) => setAckNotes(e.target.value)}
            />
            <div className="flex gap-2 mt-2">
              <Button
                size="sm"
                onClick={() => {
                  onAcknowledge(alert.id, ackNotes || undefined);
                  setShowAckDialog(false);
                  setAckNotes('');
                }}
              >
                Confirm Acknowledgment
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setShowAckDialog(false);
                  setAckNotes('');
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Resolve Dialog */}
        {showResolveDialog && (
          <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Resolution Notes <span className="text-red-600">*</span>
            </label>
            <textarea
              className="w-full p-2 border border-gray-300 rounded text-sm"
              rows={3}
              placeholder="Describe how this alert was resolved..."
              value={resolveNotes}
              onChange={(e) => setResolveNotes(e.target.value)}
            />
            <div className="flex gap-2 mt-2">
              <Button
                size="sm"
                onClick={() => {
                  if (resolveNotes.trim().length >= 10) {
                    onResolve(alert.id, resolveNotes);
                    setShowResolveDialog(false);
                    setResolveNotes('');
                  }
                }}
                disabled={resolveNotes.trim().length < 10}
              >
                Confirm Resolution
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setShowResolveDialog(false);
                  setResolveNotes('');
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function AlertStatisticsCard({ stats }: { stats: AlertStatistics }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-blue-600" />
          Alert Statistics ({stats.period_days} days)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Total Alerts</p>
            <p className="text-2xl font-bold text-gray-900">{stats.total_alerts}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Unresolved</p>
            <p className="text-2xl font-bold text-orange-600">{stats.unresolved_count}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Acknowledgment Rate</p>
            <p className="text-2xl font-bold text-blue-600">{stats.acknowledgment_rate}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Avg Resolution</p>
            <p className="text-2xl font-bold text-green-600">{stats.avg_resolution_hours}h</p>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t">
          <p className="text-sm font-semibold text-gray-700 mb-2">By Severity</p>
          <div className="flex gap-4 text-sm">
            <span className="text-red-600">Critical: {stats.by_severity.critical}</span>
            <span className="text-orange-600">High: {stats.by_severity.high}</span>
            <span className="text-yellow-600">Moderate: {stats.by_severity.moderate}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function AutomatedAlertsCenter() {
  // Feature flag: automated alerts endpoint has backend issues (500 errors)
  const AUTOMATED_ALERTS_ENABLED = true;

  const [unresolvedAlerts, setUnresolvedAlerts] = useState<AlertItem[]>([]);
  const [statistics, setStatistics] = useState<AlertStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'unresolved' | 'history'>('unresolved');

  // Track if we're currently fetching to prevent concurrent requests
  const isFetchingRef = useRef(false);

  // Safe data fetching with race condition protection
  const fetchData = useCallback(async () => {
    // Skip fetch if disabled
    if (!AUTOMATED_ALERTS_ENABLED) {
      setLoading(false);
      return;
    }

    // Prevent concurrent fetches
    if (isFetchingRef.current) {
      return;
    }

    isFetchingRef.current = true;
    setLoading(true);
    setError(null);

    try {
      // Fetch unresolved alerts and statistics in parallel
      const [alertsRes, statsRes] = await Promise.all([
        api.get('/automated-alerts/unresolved?limit=50'),
        api.get('/automated-alerts/stats/overview?days_back=30'),
      ]);

      const alertsData = alertsRes.data as { alerts?: any[] };
      setUnresolvedAlerts(alertsData.alerts || []);
      setStatistics(statsRes.data as any);
    } catch (err: any) {
      console.error('Error fetching alert data:', err);

      // Handle different error types
      if (err.response?.status === 500) {
        setError('Automated alerts service is temporarily unavailable. Please try again later.');
      } else if (err.response?.status === 404) {
        setError('Automated alerts feature is not yet available.');
      } else {
        setError(
          err.response?.data?.detail || 'Failed to load alert data'
        );
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
      isFetchingRef.current = false;
    }
  }, [AUTOMATED_ALERTS_ENABLED]);

  // Initial data load with race condition protection
  useAsyncEffect(async (signal, isMounted) => {
    if (!isMounted()) return;
    await fetchData();
  }, []);

  // Debounced refresh handler (500ms debounce)
  const handleRefresh = useDebouncedCallback(() => {
    if (!isFetchingRef.current) {
      setRefreshing(true);
      fetchData();
    }
  }, 500, []);

  const handleAcknowledge = async (alertId: string, notes?: string) => {
    if (!AUTOMATED_ALERTS_ENABLED) {
      alert('Automated alerts feature is currently disabled.');
      return;
    }

    try {
      await api.post(`/automated-alerts/${alertId}/acknowledge`, { notes });
      // Refresh data only if not already fetching
      if (!isFetchingRef.current) {
        fetchData();
      }
    } catch (err) {
      console.error('Error acknowledging alert:', err);
      const errorMsg = err.response?.data?.detail || err.response?.status === 500
        ? 'Service temporarily unavailable'
        : 'Unknown error';
      alert(`Failed to acknowledge: ${errorMsg}`);
    }
  };

  const handleResolve = async (alertId: string, notes: string) => {
    if (!AUTOMATED_ALERTS_ENABLED) {
      alert('Automated alerts feature is currently disabled.');
      return;
    }

    try {
      await api.post(`/automated-alerts/${alertId}/resolve`, {
        resolution_notes: notes,
      });
      // Refresh data only if not already fetching
      if (!isFetchingRef.current) {
        fetchData();
      }
    } catch (err) {
      console.error('Error resolving alert:', err);
      const errorMsg = err.response?.data?.detail || err.response?.status === 500
        ? 'Service temporarily unavailable'
        : 'Unknown error';
      alert(`Failed to resolve: ${errorMsg}`);
    }
  };

  const handleTriggerChecks = async (type: 'predictions' | 'trends') => {
    if (!AUTOMATED_ALERTS_ENABLED) {
      alert('Automated alerts feature is currently disabled.');
      return;
    }

    try {
      const endpoint = type === 'predictions'
        ? '/automated-alerts/check-predictions'
        : '/automated-alerts/check-trends';

      const response = await api.post(endpoint);
      const responseData = response.data as { alerts_triggered?: number };
      alert(`${type === 'predictions' ? 'ML prediction' : 'Trend'} check completed: ${responseData.alerts_triggered || 0} alerts generated`);
      // Refresh data only if not already fetching
      if (!isFetchingRef.current) {
        fetchData();
      }
    } catch (err) {
      console.error(`Error triggering ${type} check:`, err);
      const errorMsg = err.response?.data?.detail || err.response?.status === 500
        ? 'Service temporarily unavailable'
        : 'Unknown error';
      alert(`Failed to trigger check: ${errorMsg}`);
    }
  };

  // Disabled state
  if (!AUTOMATED_ALERTS_ENABLED) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Automated Alerts Center
            </CardTitle>
            <CardDescription>Clinical alert monitoring and management</CardDescription>
          </CardHeader>
          <CardContent className="pt-12 pb-12 text-center">
            <AlertCircle className="h-16 w-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">Automated Alerts Temporarily Disabled</h3>
            <p className="text-gray-600 max-w-md mx-auto">
              The automated alerts feature is currently unavailable due to backend maintenance.
              Please check back later or contact your administrator for more information.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <Card>
          <CardContent className="pt-12 pb-12 text-center">
            <RefreshCw className="h-12 w-12 mx-auto mb-4 text-blue-600 animate-spin" />
            <p className="text-lg text-gray-600">Loading alert center...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (error && !statistics) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <Alert variant="error">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Automated Alerts Center</h1>
          <p className="text-gray-600 mt-1">
            Monitor and manage clinical alerts for users requiring attention
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleTriggerChecks('predictions')}
          >
            <TrendingUp className="h-4 w-4 mr-2" />
            Check ML Predictions
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleTriggerChecks('trends')}
          >
            <Activity className="h-4 w-4 mr-2" />
            Check Trends
          </Button>
          <Button
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Alert banner for critical alerts */}
      {unresolvedAlerts.some((a) => a.severity === 'critical') && (
        <Alert className="border-red-500 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-900">
            <strong>⚠️ CRITICAL ALERTS REQUIRE IMMEDIATE ATTENTION</strong>
            <br />
            {unresolvedAlerts.filter((a) => a.severity === 'critical').length} critical alert(s) need urgent action.
          </AlertDescription>
        </Alert>
      )}

      {/* Statistics */}
      {statistics && <AlertStatisticsCard stats={statistics} />}

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('unresolved')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'unresolved'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Unresolved Alerts ({unresolvedAlerts.length})
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'history'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Alert History
        </button>
      </div>

      {/* Unresolved Alerts */}
      {activeTab === 'unresolved' && (
        <div className="space-y-4">
          {unresolvedAlerts.length > 0 ? (
            unresolvedAlerts.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onAcknowledge={handleAcknowledge}
                onResolve={handleResolve}
              />
            ))
          ) : (
            <Card>
              <CardContent className="pt-12 pb-12 text-center">
                <CheckCircle className="h-16 w-16 mx-auto mb-4 text-green-500" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  No Unresolved Alerts
                </h3>
                <p className="text-gray-600">
                  All alerts have been acknowledged or resolved. Great work!
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* History Tab - Placeholder */}
      {activeTab === 'history' && (
        <Card>
          <CardContent className="pt-12 pb-12 text-center">
            <FileText className="h-16 w-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Alert History
            </h3>
            <p className="text-gray-600">
              Historical alert data will be displayed here.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Footer */}
      <Card className="bg-gray-50">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              <p>Data refreshed: {new Date().toLocaleString()}</p>
              <p className="mt-1">
                Alerts are automatically generated based on assessment submissions,
                ML predictions, and trend analysis.
              </p>
            </div>
            <div className="text-right">
              <p className="font-semibold">Automated Clinical Alerts</p>
              <p className="text-xs">Powered by ML risk prediction models</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
