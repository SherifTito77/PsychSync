import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { AlertTriangle, Shield, Server, Lock, Activity } from 'lucide-react';

interface PortScanResult {
  port: number;
  protocol: string;
  state: string;
  service: string;
  version: string;
  banner: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommendation: string;
}

interface SSHSecurityResult {
  ssh_host: string;
  ssh_port: number;
  total_attempts: number;
  successful_attempts: number;
  blocked_attempts: number;
  average_response_time: number;
  max_concurrent_attempts: number;
  rate_limiting_detected: boolean;
  ip_blocking_detected: boolean;
  account_lockout_detected: boolean;
  security_score: number;
  recommendations: string[];
}

interface ServerBanner {
  service: string;
  banner: string;
  sensitive_info: string[];
  recommendations: string[];
}

interface FirewallRule {
  rule_number: number;
  action: string;
  protocol: string;
  source: string;
  destination: string;
  port: string;
  risk_level: string;
  recommendation: string;
}

interface CVEInfo {
  cve_id: string;
  severity: string;
  cvss_score: number;
  description: string;
  affected_software: string;
  fixed_version: string;
  references: string[];
}

interface InfrastructureSecurityMetrics {
  scan_id: string;
  timestamp: string;
  target_host: string;
  open_ports: PortScanResult[];
  ssh_security: SSHSecurityResult;
  server_banners: Record<string, ServerBanner>;
  firewall_rules: FirewallRule[];
  cve_vulnerabilities: CVEInfo[];
  risk_summary: {
    overall_status: string;
    risk_score: number;
    open_ports_count: number;
    high_risk_ports: number;
    total_cves: number;
    critical_cves: number;
    high_cves: number;
    ssh_security_score: number;
    services_with_issues: number;
  };
  recommendations: string[];
}

export const InfrastructureSecurityDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<InfrastructureSecurityMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastScan, setLastScan] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchSecurityMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/infrastructure/security-scan');
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
        setLastScan(new Date());
      }
    } catch (error) {
      console.error('Failed to fetch infrastructure security metrics:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const runPortScan = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/infrastructure/port-scan', {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        alert(`Port Scan Complete!\n\nOpen Ports: ${data.open_ports_count}\nHigh Risk Ports: ${data.high_risk_ports}`);
        fetchSecurityMetrics(); // Refresh metrics
      }
    } catch (error) {
      console.error('Failed to run port scan:', error);
      alert('Failed to run port scan');
    } finally {
      setLoading(false);
    }
  };

  const testSSHSecurity = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/infrastructure/ssh-security-test', {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        alert(`SSH Security Test Complete!\n\nSecurity Score: ${data.security_score}/100\nBlocked Attempts: ${data.blocked_attempts}`);
        fetchSecurityMetrics(); // Refresh metrics
      }
    } catch (error) {
      console.error('Failed to test SSH security:', error);
      alert('Failed to test SSH security');
    } finally {
      setLoading(false);
    }
  };

  const runFullSecurityScan = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/infrastructure/comprehensive-scan', {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        alert(`Comprehensive Security Scan Complete!\n\nOverall Risk Level: ${data.risk_summary.overall_status}\nRisk Score: ${data.risk_summary.risk_score}`);
        fetchSecurityMetrics(); // Refresh metrics
      }
    } catch (error) {
      console.error('Failed to run comprehensive security scan:', error);
      alert('Failed to run comprehensive security scan');
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
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

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'critical':
        return 'text-red-600';
      case 'high':
        return 'text-orange-600';
      case 'medium':
        return 'text-yellow-600';
      case 'low':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-yellow-600';
    if (score >= 70) return 'text-orange-600';
    return 'text-red-600';
  };

  const getOverallStatusEmoji = (status: string) => {
    switch (status.toLowerCase()) {
      case 'critical':
        return '🚨';
      case 'high':
        return '⚠️';
      case 'medium':
        return '🟡';
      case 'low':
        return '✅';
      default:
        return '📊';
    }
  };

  useEffect(() => {
    fetchSecurityMetrics();

    if (autoRefresh) {
      const interval = setInterval(fetchSecurityMetrics, 60000); // Refresh every minute
      return () => clearInterval(interval);
    }
  }, [fetchSecurityMetrics, autoRefresh]);

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const { risk_summary, open_ports, ssh_security, cve_vulnerabilities } = metrics;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Infrastructure Security Dashboard</h1>
          <p className="text-sm text-gray-500">
            Target: {metrics.target_host} | Last scan: {lastScan?.toLocaleString()}
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={runPortScan}
            disabled={loading}
            variant="outline"
          >
            <Server className="h-4 w-4 mr-2" />
            Port Scan
          </Button>
          <Button
            onClick={testSSHSecurity}
            disabled={loading}
            variant="outline"
          >
            <Lock className="h-4 w-4 mr-2" />
            SSH Test
          </Button>
          <Button
            onClick={runFullSecurityScan}
            disabled={loading}
          >
            <Shield className="h-4 w-4 mr-2" />
            Full Scan
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

      {/* Overall Risk Status */}
      <Card>
        <CardContent className="pt-6">
          <div className="text-center">
            <div className="text-6xl mb-2">
              {getOverallStatusEmoji(risk_summary.overall_status)}
            </div>
            <div className={`text-4xl font-bold ${getStatusColor(risk_summary.overall_status)}`}>
              {risk_summary.overall_status}
            </div>
            <div className={`text-2xl font-semibold mt-2 ${getScoreColor(risk_summary.risk_score)}`}>
              Risk Score: {risk_summary.risk_score}/100
            </div>
            <p className="text-lg text-gray-600 mt-2">
              Infrastructure Security Assessment
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
                {risk_summary.open_ports_count}
              </div>
              <p className="text-sm text-gray-600">Open Ports</p>
              <p className="text-xs text-red-600 mt-1">
                {risk_summary.high_risk_ports} High Risk
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {ssh_security.blocked_attempts}
              </div>
              <p className="text-sm text-gray-600">SSH Attempts Blocked</p>
              <p className="text-xs text-red-600 mt-1">
                {ssh_security.successful_attempts} Successful
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {risk_summary.critical_cves}
              </div>
              <p className="text-sm text-gray-600">Critical CVEs</p>
              <p className="text-xs text-orange-600 mt-1">
                {risk_summary.high_cves} High CVEs
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className={`text-2xl font-bold ${getScoreColor(ssh_security.security_score)}`}>
                {ssh_security.security_score}
              </div>
              <p className="text-sm text-gray-600">SSH Security Score</p>
              <p className="text-xs text-green-600 mt-1">
                {ssh_security.rate_limiting_detected ? '✅' : '❌'} Rate Limiting
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Open Ports Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Open Ports Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {open_ports.slice(0, 10).map((port) => (
              <div
                key={`${port.port}-${port.protocol}`}
                className={`p-3 border rounded-lg ${getRiskLevel(port.risk_level)}`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="font-semibold">
                      {port.port}/{port.protocol} - {port.service}
                    </h4>
                    {port.version && (
                      <p className="text-sm text-gray-600">
                        Version: {port.version}
                      </p>
                    )}
                    {port.banner && (
                      <p className="text-xs text-gray-500 mt-1 truncate">
                        Banner: {port.banner}
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <span className={`text-xs font-semibold uppercase px-2 py-1 rounded ${getRiskLevel(port.risk_level)}`}>
                      {port.risk_level}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {open_ports.length > 10 && (
            <Button variant="link" className="mt-3 w-full">
              View All Open Ports ({open_ports.length})
            </Button>
          )}
        </CardContent>
      </Card>

      {/* SSH Security Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>SSH Security Controls</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Rate Limiting</span>
                <span className={`text-sm font-semibold ${ssh_security.rate_limiting_detected ? 'text-green-600' : 'text-red-600'}`}>
                  {ssh_security.rate_limiting_detected ? '✅ Active' : '❌ Not Detected'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">IP Blocking</span>
                <span className={`text-sm font-semibold ${ssh_security.ip_blocking_detected ? 'text-green-600' : 'text-red-600'}`}>
                  {ssh_security.ip_blocking_detected ? '✅ Active' : '❌ Not Detected'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Account Lockout</span>
                <span className={`text-sm font-semibold ${ssh_security.account_lockout_detected ? 'text-green-600' : 'text-red-600'}`}>
                  {ssh_security.account_lockout_detected ? '✅ Active' : '❌ Not Detected'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Max Concurrent</span>
                <span className="text-sm font-semibold text-blue-600">
                  {ssh_security.max_concurrent_attempts}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Avg Response Time</span>
                <span className="text-sm font-semibold text-blue-600">
                  {ssh_security.average_response_time.toFixed(3)}s
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>CVE Vulnerabilities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {cve_vulnerabilities.slice(0, 8).map((cve) => (
                <div
                  key={cve.cve_id}
                  className={`p-2 border-l-4 ${getRiskLevel(cve.severity)}`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h5 className="font-semibold text-sm">{cve.cve_id}</h5>
                      <p className="text-xs text-gray-600 mt-1">{cve.description}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {cve.affected_software} - CVSS: {cve.cvss_score}
                      </p>
                    </div>
                    <span className={`text-xs font-semibold uppercase px-2 py-1 rounded ${getRiskLevel(cve.severity)}`}>
                      {cve.severity}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            {cve_vulnerabilities.length > 8 && (
              <Button variant="link" className="mt-3 w-full">
                View All CVEs ({cve_vulnerabilities.length})
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Security Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle>Security Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {metrics.recommendations.slice(0, 10).map((recommendation, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center">
                  <span className="text-xs font-semibold text-blue-600">{index + 1}</span>
                </div>
                <p className="text-sm text-gray-700">{recommendation}</p>
              </div>
            ))}
          </div>
          {metrics.recommendations.length > 10 && (
            <Button variant="link" className="mt-3 w-full">
              View All Recommendations ({metrics.recommendations.length})
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Button
              variant="outline"
              onClick={() => window.open('/api/v1/infrastructure/port-scan-report', '_blank')}
            >
              Port Scan Report
            </Button>
            <Button
              variant="outline"
              onClick={() => window.open('/api/v1/infrastructure/ssh-security-report', '_blank')}
            >
              SSH Security Report
            </Button>
            <Button
              variant="outline"
              onClick={() => window.open('/api/v1/infrastructure/vulnerability-report', '_blank')}
            >
              Vulnerability Report
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};