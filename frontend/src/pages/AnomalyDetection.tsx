import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import api from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import {
  AlertTriangle,
  Activity,
  TrendingUp,
  TrendingDown,
  Shield,
  Eye,
  RefreshCw,
  Bell,
  CheckCircle,
  Clock,
  Zap,
  BarChart3,
} from 'lucide-react';
import { toast } from 'react-hot-toast';

interface Anomaly {
  id: string;
  type: string;
  severity: string;
  description: string;
  detected_at: string;
  metric_name: string;
  expected_value: number;
  actual_value: number;
  deviation_score: number;
  status: string;
  affected_users: number;
}

interface AnomalySummary {
  total_anomalies: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  resolved_count: number;
  active_count: number;
}

const AnomalyDetection: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [summary, setSummary] = useState<AnomalySummary | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState(30);

  useEffect(() => {
    loadAnomalyData();
  }, [selectedPeriod]);

  const loadAnomalyData = async () => {
    setLoading(true);
    try {
      const orgId = user?.organization_id || 'demo-org-id';
      const response = await api.get(`/anomaly/dashboard?organization_id=${orgId}&period_days=${selectedPeriod}`);
      if (response.data) {
        setSummary(response.data.summary || null);
        setAnomalies(response.data.anomalies || []);
      }
    } catch (error) {
      console.error('Error loading anomaly data:', error);
    } finally {
      setLoading(false);
    }
  };

  const runScan = async () => {
    setScanning(true);
    try {
      const orgId = user?.organization_id || 'demo-org-id';
      const response = await api.post('/anomaly/scan', {
        organization_id: orgId,
        period_days: selectedPeriod,
      });
      if (response.data) {
        toast.success(`Scan complete: ${response.data.anomalies_found || 0} anomalies detected`);
        loadAnomalyData();
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to run anomaly scan');
    } finally {
      setScanning(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getDeviationIndicator = (score: number) => {
    if (score >= 3) return <TrendingUp className="h-4 w-4 text-red-600" />;
    if (score >= 2) return <TrendingUp className="h-4 w-4 text-orange-600" />;
    return <Activity className="h-4 w-4 text-yellow-600" />;
  };

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Zap className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Anomaly Detection</h1>
            <p className="text-sm text-gray-500">ML-powered pattern detection and behavioral alerts</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(Number(e.target.value))}
            className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
            <option value={60}>Last 60 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <Button onClick={runScan} disabled={scanning}>
            <RefreshCw className={`h-4 w-4 mr-2 ${scanning ? 'animate-spin' : ''}`} />
            {scanning ? 'Scanning...' : 'Run Scan'}
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="anomalies">Anomalies</TabsTrigger>
          <TabsTrigger value="alerts">Alert Settings</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Anomalies</CardTitle>
                <AlertTriangle className="h-4 w-4 text-orange-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary?.total_anomalies || 0}</div>
                <p className="text-xs text-gray-500">Detected in {selectedPeriod} days</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Critical / High</CardTitle>
                <Shield className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {(summary?.critical_count || 0) + (summary?.high_count || 0)}
                </div>
                <p className="text-xs text-gray-500">Require attention</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active</CardTitle>
                <Bell className="h-4 w-4 text-yellow-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary?.active_count || 0}</div>
                <p className="text-xs text-gray-500">Unresolved anomalies</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Resolved</CardTitle>
                <CheckCircle className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{summary?.resolved_count || 0}</div>
                <p className="text-xs text-gray-500">Successfully addressed</p>
              </CardContent>
            </Card>
          </div>

          {anomalies.length === 0 && (
            <Card>
              <CardContent className="p-12 text-center text-gray-500">
                <Zap className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-lg font-medium">No anomalies detected</p>
                <p className="text-sm">Run a scan to detect behavioral anomalies across your organization</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Anomalies Tab */}
        <TabsContent value="anomalies" className="space-y-4">
          {anomalies.map((anomaly) => (
            <Card key={anomaly.id} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      {getDeviationIndicator(anomaly.deviation_score)}
                      <h3 className="text-lg font-semibold capitalize">
                        {anomaly.type.replace(/_/g, ' ')}
                      </h3>
                      <Badge className={getSeverityColor(anomaly.severity)}>
                        {anomaly.severity}
                      </Badge>
                      <Badge variant="outline">{anomaly.status}</Badge>
                    </div>
                    <p className="text-gray-600 mb-3">{anomaly.description}</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Metric:</span>
                        <span className="ml-1 font-medium">{anomaly.metric_name}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Expected:</span>
                        <span className="ml-1 font-medium">{anomaly.expected_value.toFixed(1)}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Actual:</span>
                        <span className="ml-1 font-medium">{anomaly.actual_value.toFixed(1)}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Deviation:</span>
                        <span className="ml-1 font-medium">{anomaly.deviation_score.toFixed(1)}σ</span>
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-gray-500 flex items-center space-x-2">
                      <Clock className="h-3 w-3" />
                      <span>{new Date(anomaly.detected_at).toLocaleString()}</span>
                      <span>|</span>
                      <span>{anomaly.affected_users} users affected</span>
                    </div>
                  </div>
                  <Button variant="outline" size="sm">
                    <Eye className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}

          {anomalies.length === 0 && (
            <Card>
              <CardContent className="p-12 text-center text-gray-500">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-lg font-medium">No anomalies to display</p>
                <p className="text-sm">Run a scan to detect patterns</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Alert Settings Tab */}
        <TabsContent value="alerts" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Alert Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Alert>
                  <Bell className="h-4 w-4" />
                  <AlertDescription>
                    Configure alert thresholds and notification preferences for anomaly detection.
                    Alerts are triggered when behavioral metrics deviate beyond configured thresholds.
                  </AlertDescription>
                </Alert>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <h4 className="font-semibold">Deviation Thresholds</h4>
                    <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                      <span>Critical Alert</span>
                      <Badge className="bg-red-100 text-red-800">≥ 3.0σ deviation</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                      <span>High Alert</span>
                      <Badge className="bg-orange-100 text-orange-800">≥ 2.5σ deviation</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                      <span>Medium Alert</span>
                      <Badge className="bg-yellow-100 text-yellow-800">≥ 2.0σ deviation</Badge>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <h4 className="font-semibold">Notification Channels</h4>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span>Email Notifications</span>
                      <Badge variant="outline">Enabled</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span>In-App Alerts</span>
                      <Badge variant="outline">Enabled</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span>Slack Integration</span>
                      <Badge variant="outline">Not configured</Badge>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AnomalyDetection;
