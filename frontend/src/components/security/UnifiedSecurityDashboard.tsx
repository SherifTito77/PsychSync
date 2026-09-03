import React, { useState, useEffect, useCallback } from 'react';
import { useAsyncEffect } from '../../hooks/useAsyncEffect';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { InfrastructureSecurityDashboard } from './InfrastructureSecurityDashboard';
import { SecurityDashboard } from './SecurityDashboard';
import { Shield, Activity, AlertTriangle, CheckCircle, Clock, TrendingUp, TrendingDown } from 'lucide-react';

interface UnifiedSecurityMetrics {
  overall_status: 'SECURE' | 'WARNING' | 'CRITICAL' | 'UNKNOWN';
  overall_security_score: number;
  last_scan_time: string;
  active_alerts: number;
  total_alerts: number;
  scan_in_progress: boolean;
  latest_metrics: {
    timestamp: string;
    enterprise_security_score: number;
    infrastructure_risk_score: number;
    ssh_security_score: number;
    open_ports: number;
    critical_cves: number;
    active_alerts: number;
    compliance_scores: {
      soc2_type2: number;
      iso_27001: number;
      gdpr: number;
      hipaa: number;
      fedramp: number;
    };
    threat_indicators: {
      suspicious_activities: number;
      data_access_anomalies: number;
      encryption_failures: number;
      authentication_failures: number;
    };
  } | null;
}

interface SecurityAlert {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  source: string;
  title: string;
  description: string;
  resolved: boolean;
  resolved_at?: string;
}

interface SecurityTrend {
  enterprise_security_trend: number;
  infrastructure_risk_trend: number;
  ssh_security_trend: number;
  alerts_trend: number;
}

export const UnifiedSecurityDashboard: React.FC = () => {
  const [unifiedMetrics, setUnifiedMetrics] = useState<UnifiedSecurityMetrics | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<SecurityAlert[]>([]);
  const [trends, setTrends] = useState<SecurityTrend | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'infrastructure' | 'enterprise'>('overview');

  const fetchUnifiedSecurityStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/security/unified/status');
      if (response.ok) {
        const data = await response.json();
        setUnifiedMetrics(data);
      }
    } catch (error) {
      console.error('Failed to fetch unified security status:', error);
    }
  }, []);

  const fetchRecentAlerts = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/security/unified/alerts?limit=20');
      if (response.ok) {
        const data = await response.json();
        setRecentAlerts(data.alerts || []);
      }
    } catch (error) {
      console.error('Failed to fetch recent alerts:', error);
    }
  }, []);

  const fetchSecurityTrends = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/security/unified/trends');
      if (response.ok) {
        const data = await response.json();
        setTrends(data.trends || null);
      }
    } catch (error) {
      console.error('Failed to fetch security trends:', error);
    }
  }, []);

  const runComprehensiveScan = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/security/unified/scan', {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        alert(`Comprehensive Security Scan Complete!\n\nDuration: ${data.scan_duration.toFixed(2)} seconds\nAlerts Created: ${data.alerts_created}`);
        // Refresh all data
        await Promise.all([
          fetchUnifiedSecurityStatus(),
          fetchRecentAlerts(),
          fetchSecurityTrends()
        ]);
      }
    } catch (error) {
      console.error('Failed to run comprehensive scan:', error);
      alert('Failed to run comprehensive security scan');
    } finally {
      setLoading(false);
    }
  };

  const resolveAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/security/unified/alerts/${alertId}/resolve`, {
        method: 'POST'
      });
      if (response.ok) {
        fetchRecentAlerts(); // Refresh alerts
        fetchUnifiedSecurityStatus(); // Refresh metrics
      }
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  const getOverallStatusColor = (status: string) => {
    switch (status) {
      case 'SECURE':
        return 'text-green-600';
      case 'WARNING':
        return 'text-yellow-600';
      case 'CRITICAL':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getOverallStatusIcon = (status: string) => {
    switch (status) {
      case 'SECURE':
        return <CheckCircle className="h-8 w-8 text-green-600" />;
      case 'WARNING':
        return <AlertTriangle className="h-8 w-8 text-yellow-600" />;
      case 'CRITICAL':
        return <Shield className="h-8 w-8 text-red-600" />;
      default:
        return <Activity className="h-8 w-8 text-gray-600" />;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-yellow-600';
    if (score >= 70) return 'text-orange-600';
    return 'text-red-600';
  };

  const getTrendIcon = (trend: number) => {
    if (trend > 0) return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (trend < 0) return <TrendingDown className="h-4 w-4 text-red-600" />;
    return <div className="h-4 w-4" />;
  };

  const getAlertLevelColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'border-red-200 bg-red-50 text-red-800';
      case 'ERROR':
        return 'border-orange-200 bg-orange-50 text-orange-800';
      case 'WARNING':
        return 'border-yellow-200 bg-yellow-50 text-yellow-800';
      case 'INFO':
        return 'border-blue-200 bg-blue-50 text-blue-800';
      default:
        return 'border-gray-200 bg-gray-50 text-gray-800';
    }
  };

  // ✅ FIXED: Memory leak prevention - separate initialization and interval
  useEffect(() => {
    const initialize = async () => {
      try {
        await Promise.all([
          fetchUnifiedSecurityStatus(),
          fetchRecentAlerts(),
          fetchSecurityTrends()
        ]);
        setLoading(false);
      } catch (error: any) {
        console.error('Error initializing dashboard:', error);
        setLoading(false);
      }
    };
    initialize();
  }, [fetchUnifiedSecurityStatus, fetchRecentAlerts, fetchSecurityTrends]);

  useEffect(() => {
    // Set up interval for auto-refresh
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchUnifiedSecurityStatus();
        fetchRecentAlerts();
      }, 60000); // Refresh every minute

      // Return cleanup for the interval
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  if (loading || !unifiedMetrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const latestMetrics = unifiedMetrics.latest_metrics;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Unified Security Dashboard</h1>
          <p className="text-sm text-gray-500">
            Last scan: {unifiedMetrics.last_scan_time ? new Date(unifiedMetrics.last_scan_time).toLocaleString() : 'Never'}
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={runComprehensiveScan}
            disabled={loading || unifiedMetrics.scan_in_progress}
            variant="outline"
          >
            <Shield className="h-4 w-4 mr-2" />
            {unifiedMetrics.scan_in_progress ? 'Scanning...' : 'Full Scan'}
          </Button>
          <Button
            onClick={() => setAutoRefresh(!autoRefresh)}
            variant={autoRefresh ? "default" : "outline"}
          >
            <Activity className="h-4 w-4 mr-2" />
            Auto-refresh
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('infrastructure')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'infrastructure'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Infrastructure
          </button>
          <button
            onClick={() => setActiveTab('enterprise')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'enterprise'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Enterprise
          </button>
        </nav>
      </div>

      {activeTab === 'overview' && (
        <>
          {/* Overall Status */}
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="flex justify-center mb-2">
                  {getOverallStatusIcon(unifiedMetrics.overall_status)}
                </div>
                <div className={`text-4xl font-bold ${getOverallStatusColor(unifiedMetrics.overall_status)}`}>
                  {unifiedMetrics.overall_status}
                </div>
                <div className={`text-2xl font-semibold mt-2 ${getScoreColor(unifiedMetrics.overall_security_score)}`}>
                  Security Score: {unifiedMetrics.overall_security_score.toFixed(1)}%
                </div>
                <p className="text-lg text-gray-600 mt-2">
                  Platform Security Assessment
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {unifiedMetrics.active_alerts}
                  </div>
                  <p className="text-sm text-gray-600">Active Alerts</p>
                  <div className="flex justify-center items-center mt-1">
                    {getTrendIcon(trends?.alerts_trend || 0)}
                    <span className={`text-xs ml-1 ${trends?.alerts_trend > 0 ? 'text-red-600' : trends?.alerts_trend < 0 ? 'text-green-600' : 'text-gray-600'}`}>
                      {trends?.alerts_trend || 0}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className={`text-2xl font-bold ${getScoreColor(latestMetrics?.enterprise_security_score || 0)}`}>
                    {latestMetrics?.enterprise_security_score.toFixed(1) || 0}%
                  </div>
                  <p className="text-sm text-gray-600">Enterprise Security</p>
                  <div className="flex justify-center items-center mt-1">
                    {getTrendIcon(trends?.enterprise_security_trend || 0)}
                    <span className="text-xs text-gray-600 ml-1">
                      {trends?.enterprise_security_trend?.toFixed(1) || 0}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className={`text-2xl font-bold ${getScoreColor(latestMetrics?.ssh_security_score || 0)}`}>
                    {latestMetrics?.ssh_security_score.toFixed(1) || 0}%
                  </div>
                  <p className="text-sm text-gray-600">SSH Security</p>
                  <div className="flex justify-center items-center mt-1">
                    {getTrendIcon(trends?.ssh_security_trend || 0)}
                    <span className="text-xs text-gray-600 ml-1">
                      {trends?.ssh_security_trend?.toFixed(1) || 0}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {latestMetrics?.critical_cves || 0}
                  </div>
                  <p className="text-sm text-gray-600">Critical CVEs</p>
                  <p className="text-xs text-orange-600 mt-1">
                    {latestMetrics?.open_ports || 0} Open Ports
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Compliance Scores */}
          <Card>
            <CardHeader>
              <CardTitle>Compliance Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                {latestMetrics && Object.entries(latestMetrics.compliance_scores).map(([standard, score]) => (
                  <div key={standard} className="text-center">
                    <div className={`text-lg font-semibold ${getScoreColor(score as number)}`}>
                      {score as number}%
                    </div>
                    <p className="text-xs text-gray-600 uppercase mt-1">
                      {standard.replace('_', ' ')}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent Alerts */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Security Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentAlerts.slice(0, 8).map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-3 border rounded-lg ${getAlertLevelColor(alert.level)}`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="font-semibold text-sm">{alert.title}</h4>
                        <p className="text-sm mt-1">{alert.description}</p>
                        <div className="flex items-center space-x-2 mt-2">
                          <span className="text-xs uppercase font-semibold">
                            {alert.level}
                          </span>
                          <span className="text-xs text-gray-500">
                            {alert.source}
                          </span>
                          <span className="text-xs text-gray-500">
                            {new Date(alert.timestamp).toLocaleString()}
                          </span>
                        </div>
                      </div>
                      {!alert.resolved && (
                        <Button
                          size="sm"
                          onClick={() => resolveAlert(alert.id)}
                          variant="outline"
                          className="ml-2"
                        >
                          Resolve
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              {recentAlerts.length === 0 && (
                <div className="text-center py-4 text-gray-500">
                  No recent alerts
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {activeTab === 'infrastructure' && (
        <InfrastructureSecurityDashboard />
      )}

      {activeTab === 'enterprise' && (
        <SecurityDashboard />
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <Button
              variant="outline"
              onClick={() => window.open('/api/v1/security/unified/report', '_blank')}
            >
              Generate Report
            </Button>
            <Button
              variant="outline"
              onClick={() => window.open('/api/v1/security/audit-log', '_blank')}
            >
              View Audit Logs
            </Button>
            <Button
              variant="outline"
              onClick={() => window.open('/api/v1/security/threat-intelligence', '_blank')}
            >
              Threat Intelligence
            </Button>
            <Button
              variant="outline"
              onClick={() => window.open('/api/v1/compliance/security-report', '_blank')}
            >
              Compliance Report
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
