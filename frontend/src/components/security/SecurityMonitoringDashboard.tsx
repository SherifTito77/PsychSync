/**
 * Real-Time Security Monitoring Dashboard
 *
 * Displays live security metrics, threat alerts, and system status.
 * Updates in real-time via WebSocket connections.
 *
 * Author: Security Team
 * Date: 2025-12-24
 */

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/common/card';
import { Button } from '@/components/common/Button';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Activity,
  Eye,
  Globe,
  Lock,
  Zap,
  TrendingUp,
  TrendingDown,
  Users,
  ServerCrash,
  Cpu
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

interface SecurityMetrics {
  waf: WAFMetrics;
  threatIntel: ThreatIntelMetrics;
  behavioral: BehavioralMetrics;
  authentication: AuthMetrics;
}

interface WAFMetrics {
  total_requests_checked: number;
  requests_blocked: number;
  block_rate: number;
  violations: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

interface ThreatIntelMetrics {
  malicious_ips_blocked: number;
  tor_exit_nodes_blocked: number;
  botnet_ips_blocked: number;
  reputation_checks: number;
  active_blocklists: {
    malicious_ips: number;
    tor_exit_nodes: number;
    botnet_ips: number;
    abusive_ips: number;
  };
}

interface BehavioralMetrics {
  impossible_travel_detected: number;
  velocity_violations: number;
  bot_detections: number;
  average_risk_score: number;
  high_risk_sessions: number;
}

interface AuthMetrics {
  mfa_enabled_users: number;
  failed_login_attempts: number;
  successful_logins: number;
  suspicious_activity: number;
  active_sessions: number;
}

interface SecurityAlert {
  id: string;
  type: 'critical' | 'high' | 'medium' | 'low';
  severity: number;
  title: string;
  description: string;
  source: string;
  timestamp: Date;
  actions?: AlertAction[];
}

interface AlertAction {
  label: string;
  action: () => void;
  variant?: 'danger' | 'default' | 'outline';
}

// =============================================================================
// Components
// =============================================================================

export const SecurityMonitoringDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<SecurityMetrics | null>(null);
  const [alerts, setAlerts] = useState<SecurityAlert[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Fetch metrics on mount
  useEffect(() => {
    fetchMetrics();

    // Set up WebSocket connection for real-time updates
    const ws = new WebSocket('wss://api.psychsync.com/security/monitoring');

    ws.onopen = () => {
      setIsConnected(true);
      console.log('[Security Dashboard] WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'metrics_update') {
        setMetrics(data.metrics);
        setLastUpdated(new Date());
      } else if (data.type === 'security_alert') {
        setAlerts(prev => [data.alert, ...prev].slice(0, 50)); // Keep last 50
      }
    };

    ws.onerror = (error) => {
      console.error('[Security Dashboard] WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('[Security Dashboard] WebSocket disconnected');
    };

    // Refresh metrics every 30 seconds via API (fallback)
    const interval = setInterval(fetchMetrics, 30000);

    return () => {
      ws.close();
      clearInterval(interval);
    };
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/v1/admin/security/metrics');
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
        setLastUpdated(new Date());
      }
    } catch (error) {
      console.error('[Security Dashboard] Failed to fetch metrics:', error);
    }
  };

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-2" />
          <p className="text-gray-600">Loading security metrics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Security Monitoring Dashboard</h1>
          <p className="text-sm text-gray-600">
            Real-time security metrics and threat intelligence
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 text-sm ${
            isConnected ? 'text-green-600' : 'text-red-600'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            }`} />
            {isConnected ? 'Live' : 'Disconnected'}
          </div>
          <Button variant="outline" size="sm" onClick={fetchMetrics}>
            Refresh
          </Button>
        </div>
      </div>

      {/* Last Updated */}
      <p className="text-xs text-gray-500">
        Last updated: {lastUpdated.toLocaleTimeString()}
      </p>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <OverviewCard
          title="Total Requests"
          value={metrics.waf.total_requests_checked.toLocaleString()}
          icon={<Activity className="h-5 w-5" />}
          trend={<TrendingUp className="h-4 w-4 text-blue-500" />}
          color="blue"
        />
        <OverviewCard
          title="Requests Blocked"
          value={metrics.waf.requests_blocked.toString()}
          icon={<Shield className="h-5 w-5" />}
          trend={<TrendingDown className="h-4 w-4 text-green-500" />}
          color="red"
        />
        <OverviewCard
          title="Block Rate"
          value={`${metrics.waf.block_rate.toFixed(2)}%`}
          icon={<Zap className="h-5 w-5" />}
          color="amber"
        />
        <OverviewCard
          title="Active Sessions"
          value={metrics.authentication.active_sessions.toString()}
          icon={<Users className="h-5 w-5" />}
          color="green"
        />
      </div>

      {/* WAF Stats */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Web Application Firewall</h2>
          <Shield className="h-5 w-5 text-blue-500" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatBox
            label="Critical"
            value={metrics.waf.violations.critical}
            color="red"
          />
          <StatBox
            label="High"
            value={metrics.waf.violations.high}
            color="orange"
          />
          <StatBox
            label="Medium"
            value={metrics.waf.violations.medium}
            color="yellow"
          />
          <StatBox
            label="Low"
            value={metrics.waf.violations.low}
            color="blue"
          />
          <StatBox
            label="Total"
            value={
              metrics.waf.violations.critical +
              metrics.waf.violations.high +
              metrics.waf.violations.medium +
              metrics.waf.violations.low
            }
            color="gray"
          />
        </div>
      </Card>

      {/* Threat Intelligence */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Threat Intelligence</h2>
            <Globe className="h-5 w-5 text-purple-500" />
          </div>

          <div className="space-y-3">
            <MetricRow
              label="Malicious IPs Blocked"
              value={metrics.threatIntel.malicious_ips_blocked}
              icon={<XCircle className="h-4 w-4 text-red-500" />}
            />
            <MetricRow
              label="Tor Exit Nodes Blocked"
              value={metrics.threatIntel.tor_exit_nodes_blocked}
              icon={<Eye className="h-4 w-4 text-purple-500" />}
            />
            <MetricRow
              label="Botnet IPs Blocked"
              value={metrics.threatIntel.botnet_ips_blocked}
              icon={<ServerCrash className="h-4 w-4 text-orange-500" />}
            />
            <MetricRow
              label="Reputation Checks"
              value={metrics.threatIntel.reputation_checks}
              icon={<Activity className="h-4 w-4 text-blue-500" />}
            />
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 mb-2">Active Blocklists</p>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>Malicious IPs: <strong>{metrics.threatIntel.active_blocklists.malicious_ips.toLocaleString()}</strong></div>
              <div>Tor Nodes: <strong>{metrics.threatIntel.active_blocklists.tor_exit_nodes.toLocaleString()}</strong></div>
              <div>Botnet IPs: <strong>{metrics.threatIntel.active_blocklists.botnet_ips.toLocaleString()}</strong></div>
              <div>Abusive IPs: <strong>{metrics.threatIntel.active_blocklists.abusive_ips.toLocaleString()}</strong></div>
            </div>
          </div>
        </Card>

        {/* Behavioral Analysis */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Behavioral Analysis</h2>
            <Cpu className="h-5 w-5 text-cyan-500" />
          </div>

          <div className="space-y-3">
            <MetricRow
              label="Impossible Travel Detected"
              value={metrics.behavioral.impossible_travel_detected}
              icon={<AlertTriangle className="h-4 w-4 text-red-500" />}
            />
            <MetricRow
              label="Velocity Violations"
              value={metrics.behavioral.velocity_violations}
              icon={<Zap className="h-4 w-4 text-amber-500" />}
            />
            <MetricRow
              label="Bot Detections"
              value={metrics.behavioral.bot_detections}
              icon={<ServerCrash className="h-4 w-4 text-orange-500" />}
            />
            <MetricRow
              label="High-Risk Sessions"
              value={metrics.behavioral.high_risk_sessions}
              icon={<Shield className="h-4 w-4 text-red-500" />}
            />
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Average Risk Score</span>
              <span className={`text-2xl font-bold ${
                metrics.behavioral.average_risk_score < 25 ? 'text-green-600' :
                metrics.behavioral.average_risk_score < 50 ? 'text-yellow-600' :
                metrics.behavioral.average_risk_score < 75 ? 'text-orange-600' :
                'text-red-600'
              }`}>
                {metrics.behavioral.average_risk_score.toFixed(1)}
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-2">
              <div
                className={`h-2 rounded-full ${
                  metrics.behavioral.average_risk_score < 25 ? 'bg-green-500' :
                  metrics.behavioral.average_risk_score < 50 ? 'bg-yellow-500' :
                  metrics.behavioral.average_risk_score < 75 ? 'bg-orange-500' :
                  'bg-red-500'
                }`}
                style={{ width: `${metrics.behavioral.average_risk_score}%` }}
              />
            </div>
          </div>
        </Card>
      </div>

      {/* Authentication Metrics */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Authentication</h2>
          <Lock className="h-5 w-5 text-green-500" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatBox
            label="MFA Enabled Users"
            value={`${metrics.authentication.mfa_enabled_users}%`}
            color="green"
          />
          <StatBox
            label="Failed Logins"
            value={metrics.authentication.failed_login_attempts.toString()}
            color="red"
          />
          <StatBox
            label="Successful Logins"
            value={metrics.authentication.successful_logins.toString()}
            color="green"
          />
          <StatBox
            label="Suspicious Activity"
            value={metrics.authentication.suspicious_activity.toString()}
            color="orange"
          />
          <StatBox
            label="Active Sessions"
            value={metrics.authentication.active_sessions.toString()}
            color="blue"
          />
        </div>
      </Card>

      {/* Security Alerts */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recent Security Alerts</h2>
          <Button variant="outline" size="sm">
            View All
          </Button>
        </div>

        {alerts.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-2" />
            <p className="text-gray-600">No recent security alerts</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.slice(0, 5).map((alert) => (
              <AlertCard key={alert.id} alert={alert} />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

// =============================================================================
// Sub-Components
// =============================================================================

interface OverviewCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  trend?: React.ReactNode;
  color: 'blue' | 'red' | 'green' | 'amber';
}

const OverviewCard: React.FC<OverviewCardProps> = ({
  title,
  value,
  icon,
  trend,
  color
}) => {
  const colorClasses = {
    blue: 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800',
    red: 'bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800',
    green: 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800',
    amber: 'bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800',
  };

  return (
    <Card className={`p-4 border ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          {icon}
          {trend}
        </div>
      </div>
    </Card>
  );
};

interface StatBoxProps {
  label: string;
  value: number | string;
  color: 'red' | 'orange' | 'yellow' | 'blue' | 'green' | 'gray';
}

const StatBox: React.FC<StatBoxProps> = ({ label, value, color }) => {
  const colorClasses = {
    red: 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300',
    orange: 'bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300',
    yellow: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300',
    blue: 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
    green: 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300',
    gray: 'bg-gray-100 dark:bg-gray-900 text-gray-700 dark:text-gray-300',
  };

  return (
    <div className="text-center">
      <div className={`text-2xl font-bold ${colorClasses[color]} rounded-lg p-2`}>
        {value}
      </div>
      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{label}</p>
    </div>
  );
};

interface MetricRowProps {
  label: string;
  value: number;
  icon: React.ReactNode;
}

const MetricRow: React.FC<MetricRowProps> = ({ label, value, icon }) => {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <span className="font-semibold">{value.toLocaleString()}</span>
    </div>
  );
};

interface AlertCardProps {
  alert: SecurityAlert;
}

const AlertCard: React.FC<AlertCardProps> = ({ alert }) => {
  const severityColors = {
    critical: 'border-red-500 bg-red-50 dark:bg-red-950',
    high: 'border-orange-500 bg-orange-50 dark:bg-orange-950',
    medium: 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950',
    low: 'border-blue-500 bg-blue-50 dark:bg-blue-950',
  };

  const severityIcons = {
    critical: <AlertTriangle className="h-5 w-5 text-red-500" />,
    high: <AlertTriangle className="h-5 w-5 text-orange-500" />,
    medium: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
    low: <AlertTriangle className="h-5 w-5 text-blue-500" />,
  };

  return (
    <div className={`p-4 rounded-lg border-l-4 ${severityColors[alert.type]}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          {severityIcons[alert.type]}
          <div>
            <h3 className="font-semibold">{alert.title}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {alert.description}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              {alert.source} • {alert.timestamp.toLocaleString()}
            </p>
          </div>
        </div>

        {alert.actions && (
          <div className="flex gap-2">
            {alert.actions.map((action, index) => (
              <Button
                key={index}
                variant={action.variant || 'outline'}
                size="sm"
                onClick={action.action}
              >
                {action.label}
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SecurityMonitoringDashboard;
