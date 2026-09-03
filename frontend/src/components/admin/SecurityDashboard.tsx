/**
 * Security Analytics Dashboard
 *
 * Provides real-time security monitoring and threat intelligence:
 * - Security metrics overview
 * - Active threat indicators
 * - Event timeline and trends
 * - User risk assessment
 * - Alert management
 *
 * Author: Security Team
 * Version: 1.0
 * Date: 2025-12-26
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertTriangle,
  Shield,
  Activity,
  Users,
  Globe,
  TrendingUp,
  CheckCircle,
  XCircle,
  Clock,
  ShieldOff
} from 'lucide-react';
import securityAnalyticsApi from '@/services/securityAnalytics';

// Feature flag: security analytics endpoints are now implemented
const SECURITY_ANALYTICS_ENABLED = true;

// Types
interface SecurityMetrics {
  timestamp: string;
  status: 'healthy' | 'warning' | 'critical';
  security_score: number;
  total_events: number;
  active_users: number;
  active_ips: number;
  events_by_severity: Record<string, number>;
  events_by_type: Record<string, number>;
}

interface ThreatIndicator {
  indicator_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  description: string;
  affected_entities: string[];
  mitigation_suggestions: string[];
  timestamp: string;
}

interface SecurityEvent {
  event_type: string;
  timestamp: string;
  user_id?: number;
  session_id?: string;
  ip_address?: string;
  severity: string;
  details: Record<string, unknown>;
}

const SecurityDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<SecurityMetrics | null>(null);
  const [threats, setThreats] = useState<ThreatIndicator[]>([]);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedHours, setSelectedHours] = useState(24);

  useEffect(() => {
    if (SECURITY_ANALYTICS_ENABLED) {
      loadSecurityData();
      // Refresh every 60 seconds
      const interval = setInterval(loadSecurityData, 60000);
      return () => clearInterval(interval);
    } else {
      setLoading(false);
    }
  }, [selectedHours, SECURITY_ANALYTICS_ENABLED]);

  const loadSecurityData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [metricsData, threatsData, eventsData] = await Promise.all([
        securityAnalyticsApi.getSystemStatus(),
        securityAnalyticsApi.getActiveThreats({ hours: selectedHours }),
        securityAnalyticsApi.getSecurityEvents({ hours: selectedHours, limit: 50 })
      ]);

      setMetrics(metricsData);
      setThreats(threatsData);
      setEvents(eventsData);
    } catch (err: any) {
      // Handle both 404 and 500 errors gracefully
      if (err.response?.status === 500) {
        setError('Security analytics service is temporarily unavailable. Our team has been notified.');
      } else if (err.response?.status === 404) {
        setError('Security analytics feature is not yet available.');
      } else {
        setError('Failed to load security data');
      }
      console.error('Error loading security data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'high':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'critical':
        return <XCircle className="h-5 w-5 text-red-600" />;
      default:
        return <Activity className="h-5 w-5 text-gray-600" />;
    }
  };

  // Show disabled state when feature flag is off
  if (!SECURITY_ANALYTICS_ENABLED) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Card className="max-w-md">
          <CardContent className="pt-6 text-center">
            <ShieldOff className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Security Analytics Temporarily Disabled
            </h3>
            <p className="text-gray-600 mb-6">
              The security analytics dashboard is currently unavailable due to backend maintenance.
              We're working to restore full functionality as soon as possible.
            </p>
            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
              <Shield className="h-4 w-4" />
              <span>Enterprise-grade security monitoring</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Activity className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading security metrics...</p>
        </div>
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Card className="max-w-md">
          <CardContent className="pt-6 text-center">
            <AlertTriangle className="h-12 w-12 text-red-600 mx-auto mb-4" />
            <p className="text-gray-800 font-semibold mb-2">Error Loading Security Data</p>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={loadSecurityData}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Security Dashboard</h1>
          <p className="text-gray-600 mt-1">Real-time security monitoring and threat detection</p>
        </div>
        <div className="flex gap-2">
          {[1, 6, 24, 168].map((hours) => (
            <Button
              key={hours}
              variant={selectedHours === hours ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedHours(hours)}
            >
              {hours === 1 ? '1H' : hours === 6 ? '6H' : hours === 24 ? '24H' : '7D'}
            </Button>
          ))}
        </div>
      </div>

      {/* Security Status Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Security Score */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Security Score</CardTitle>
              <Shield className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{metrics.security_score}/100</div>
              <div className="flex items-center mt-2">
                {getStatusIcon(metrics.status)}
                <span className="ml-2 text-sm capitalize text-gray-600">{metrics.status}</span>
              </div>
            </CardContent>
          </Card>

          {/* Total Events */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Events</CardTitle>
              <Activity className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{metrics.total_events}</div>
              <p className="text-xs text-gray-600 mt-2">Last {selectedHours} hours</p>
            </CardContent>
          </Card>

          {/* Active Users */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Active Users</CardTitle>
              <Users className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{metrics.active_users}</div>
              <p className="text-xs text-gray-600 mt-2">Last hour</p>
            </CardContent>
          </Card>

          {/* Active IPs */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Active IPs</CardTitle>
              <Globe className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{metrics.active_ips}</div>
              <p className="text-xs text-gray-600 mt-2">Unique addresses</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Severity Breakdown */}
      {metrics && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Event Severity Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(metrics.events_by_severity).map(([severity, count]) => (
                <div key={severity} className="text-center">
                  <Badge className={getSeverityColor(severity)} variant="outline">
                    {severity}
                  </Badge>
                  <div className="text-2xl font-bold mt-2">{count as number}</div>
                  <p className="text-xs text-gray-600">events</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="threats" className="space-y-4">
        <TabsList>
          <TabsTrigger value="threats">Active Threats</TabsTrigger>
          <TabsTrigger value="events">Security Events</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
        </TabsList>

        {/* Threats Tab */}
        <TabsContent value="threats">
          <Card>
            <CardHeader>
              <CardTitle>Active Threat Indicators</CardTitle>
              <CardDescription>
                {threats.length} threat{threats.length !== 1 ? 's' : ''} detected in the last {selectedHours} hours
              </CardDescription>
            </CardHeader>
            <CardContent>
              {threats.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                  <p className="text-gray-600">No active threats detected</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {threats.map((threat, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="h-5 w-5 text-orange-600" />
                          <Badge className={getSeverityColor(threat.severity)}>
                            {threat.severity}
                          </Badge>
                          <span className="font-semibold">{threat.indicator_type}</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-600">
                          <Clock className="h-4 w-4 mr-1" />
                          {new Date(threat.timestamp).toLocaleString()}
                        </div>
                      </div>
                      <p className="text-gray-700 mb-2">{threat.description}</p>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-medium">Confidence:</span>
                        <Badge variant="outline">
                          {(threat.confidence * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      {threat.affected_entities.length > 0 && (
                        <div className="mb-2">
                          <span className="text-sm font-medium">Affected: </span>
                          <span className="text-sm text-gray-600">
                            {threat.affected_entities.join(', ')}
                          </span>
                        </div>
                      )}
                      {threat.mitigation_suggestions.length > 0 && (
                        <div>
                          <p className="text-sm font-medium mb-1">Recommended Actions:</p>
                          <ul className="list-disc list-inside text-sm text-gray-600">
                            {threat.mitigation_suggestions.map((suggestion, idx) => (
                              <li key={idx}>{suggestion}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Events Tab */}
        <TabsContent value="events">
          <Card>
            <CardHeader>
              <CardTitle>Recent Security Events</CardTitle>
              <CardDescription>
                {events.length} event{events.length !== 1 ? 's' : ''} in the last {selectedHours} hours
              </CardDescription>
            </CardHeader>
            <CardContent>
              {events.length === 0 ? (
                <div className="text-center py-12">
                  <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No security events recorded</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {events.map((event, index) => (
                    <div key={index} className="border rounded-lg p-3 hover:bg-gray-50">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge className={getSeverityColor(event.severity)} variant="outline">
                              {event.severity}
                            </Badge>
                            <span className="font-medium">{event.event_type}</span>
                          </div>
                          <div className="text-sm text-gray-600">
                            {event.user_id && <span>User: {event.user_id}</span>}
                            {event.ip_address && (
                              <span className="ml-2">IP: {event.ip_address}</span>
                            )}
                          </div>
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(event.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trends Tab */}
        <TabsContent value="trends">
          <Card>
            <CardHeader>
              <CardTitle>Security Trends</CardTitle>
              <CardDescription>Event patterns over time</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-600">
                <TrendingUp className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>Trend visualization will be available with historical data</p>
                <p className="text-sm mt-2">Timeline API endpoint provides data for charts</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SecurityDashboard;
