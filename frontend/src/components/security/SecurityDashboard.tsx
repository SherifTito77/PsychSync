import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';

interface SecurityMetrics {
  overall_score: number;
  security_events_24h: number;
  failed_logins_24h: number;
  blocked_ips: number;
  active_incidents: number;
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
  system_health: {
    api_availability: number;
    database_performance: number;
    encryption_status: number;
    audit_log_status: number;
  };
}

interface SecurityIncident {
  id: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  title: string;
  description: string;
  created_at: string;
  status: 'open' | 'investigating' | 'resolved';
  affected_systems: string[];
}

interface SecurityAlert {
  id: string;
  type: 'THREAT' | 'COMPLIANCE' | 'SYSTEM';
  message: string;
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  timestamp: string;
}

export const SecurityDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<SecurityMetrics | null>(null);
  const [incidents, setIncidents] = useState<SecurityIncident[]>([]);
  const [alerts, setAlerts] = useState<SecurityAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchSecurityMetrics = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/security/metrics');
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (error) {
      console.error('Failed to fetch security metrics:', error);
    }
  }, []);

  const fetchSecurityIncidents = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/security/incidents');
      if (response.ok) {
        const data = await response.json();
        setIncidents(data.incidents || []);
      }
    } catch (error) {
      console.error('Failed to fetch security incidents:', error);
    }
  }, []);

  const fetchSecurityAlerts = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/security/alerts');
      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || []);
      }
    } catch (error) {
      console.error('Failed to fetch security alerts:', error);
    }
  }, []);

  const runSecurityHealthCheck = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/security/health-check', {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        alert(`Security Health Check Complete!\n\nOverall Score: ${data.overall_score}%\nStatus: ${data.overall_status}`);
        fetchSecurityMetrics(); // Refresh metrics
      }
    } catch (error) {
      console.error('Failed to run security health check:', error);
      alert('Failed to run security health check');
    } finally {
      setLoading(false);
    }
  };

  const acknowledgeIncident = async (incidentId: string) => {
    try {
      const response = await fetch(`/api/v1/security/incidents/${incidentId}/acknowledge`, {
        method: 'POST'
      });
      if (response.ok) {
        fetchSecurityIncidents(); // Refresh incidents
      }
    } catch (error) {
      console.error('Failed to acknowledge incident:', error);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
      case 'HIGH':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'MEDIUM':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'LOW':
        return 'text-green-600 bg-green-50 border-green-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-yellow-600';
    if (score >= 70) return 'text-orange-600';
    return 'text-red-600';
  };

  const getOverallStatusEmoji = (score: number) => {
    if (score >= 90) return '🏆';
    if (score >= 80) return '✅';
    if (score >= 70) return '⚠️';
    return '🚨';
  };

  useEffect(() => {
    const initializeDashboard = async () => {
      await Promise.all([
        fetchSecurityMetrics(),
        fetchSecurityIncidents(),
        fetchSecurityAlerts()
      ]);
      setLoading(false);
    };

    initializeDashboard();

    // Set up real-time updates
    const interval = setInterval(() => {
      fetchSecurityMetrics();
      fetchSecurityAlerts();
      setLastUpdate(new Date());
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, [fetchSecurityMetrics, fetchSecurityIncidents, fetchSecurityAlerts]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Failed to load security metrics</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Security Dashboard</h1>
          <p className="text-sm text-gray-500">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={runSecurityHealthCheck}
            disabled={loading}
            variant="outline"
          >
            {loading ? 'Running...' : 'Run Health Check'}
          </Button>
          <Button onClick={() => window.location.reload()}>
            Refresh
          </Button>
        </div>
      </div>

      {/* Overall Security Score */}
      <Card>
        <CardContent className="pt-6">
          <div className="text-center">
            <div className="text-6xl mb-2">
              {getOverallStatusEmoji(metrics.overall_score)}
            </div>
            <div className={`text-4xl font-bold ${getScoreColor(metrics.overall_score)}`}>
              {metrics.overall_score.toFixed(1)}%
            </div>
            <p className="text-lg text-gray-600 mt-2">
              Overall Security Score
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {metrics.security_events_24h}
              </div>
              <p className="text-sm text-gray-600">Security Events (24h)</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {metrics.failed_logins_24h}
              </div>
              <p className="text-sm text-gray-600">Failed Logins (24h)</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {metrics.blocked_ips}
              </div>
              <p className="text-sm text-gray-600">Blocked IPs</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {metrics.active_incidents}
              </div>
              <p className="text-sm text-gray-600">Active Incidents</p>
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
            {Object.entries(metrics.compliance_scores).map(([standard, score]) => (
              <div key={standard} className="text-center">
                <div className={`text-lg font-semibold ${getScoreColor(score)}`}>
                  {score}%
                </div>
                <p className="text-xs text-gray-600 uppercase mt-1">
                  {standard.replace('_', ' ')}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Threat Indicators */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Threat Indicators</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(metrics.threat_indicators).map(([indicator, count]) => (
                <div key={indicator} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 capitalize">
                    {indicator.replace('_', ' ')}
                  </span>
                  <span className={`font-semibold ${count > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {count}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(metrics.system_health).map(([component, status]) => (
                <div key={component} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 capitalize">
                    {component.replace('_', ' ')}
                  </span>
                  <span className={`font-semibold ${status >= 95 ? 'text-green-600' : 'text-yellow-600'}`}>
                    {status}%
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Incidents */}
      {incidents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Security Incidents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {incidents.slice(0, 5).map((incident) => (
                <div
                  key={incident.id}
                  className={`p-3 border rounded-lg ${getSeverityColor(incident.severity)}`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h4 className="font-semibold">{incident.title}</h4>
                      <p className="text-sm mt-1">{incident.description}</p>
                      <div className="flex items-center space-x-2 mt-2">
                        <span className="text-xs uppercase font-semibold">
                          {incident.severity}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(incident.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                    {incident.status === 'open' && (
                      <Button
                        size="sm"
                        onClick={() => acknowledgeIncident(incident.id)}
                        variant="outline"
                      >
                        Acknowledge
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            {incidents.length > 5 && (
              <Button variant="link" className="mt-3 w-full">
                View All Incidents ({incidents.length})
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Recent Alerts */}
      {alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Security Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.slice(0, 10).map((alert) => (
                <div
                  key={alert.id}
                  className={`p-2 text-sm border-l-4 ${getSeverityColor(alert.severity)}`}
                >
                  <div className="flex justify-between items-start">
                    <p>{alert.message}</p>
                    <span className="text-xs text-gray-500 ml-2 whitespace-nowrap">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            {alerts.length > 10 && (
              <Button variant="link" className="mt-3 w-full">
                View All Alerts ({alerts.length})
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Button
              variant="outline"
              onClick={() => window.open('/api/v1/compliance/security-report', '_blank')}
            >
              Generate Compliance Report
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
          </div>
        </CardContent>
      </Card>
    </div>
  );
};