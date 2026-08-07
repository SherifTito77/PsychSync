import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Progress from '@/components/ui/progress';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

interface Metric {
  name: string;
  value: number;
  unit: string;
  status: 'healthy' | 'warning' | 'critical';
  trend: number;
}

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  uptime: number;
  responseTime: number;
  errorRate: number;
  lastCheck: string;
}

interface AlertData {
  id: string;
  level: 'info' | 'warning' | 'critical';
  message: string;
  timestamp: string;
  service: string;
  acknowledged: boolean;
}

interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: number;
  timestamp: string;
}

interface DeploymentMetrics {
  id: string;
  version: string;
  status: 'success' | 'failed' | 'in_progress';
  timestamp: string;
  duration: number;
  errorRate: number;
}

// TODO(human): Implement the alert acknowledgment functionality
// This function should handle acknowledging alerts to prevent duplicate notifications
// It should make an API call to update the alert status in the backend
const acknowledgeAlert = async (alertId: string): Promise<boolean> => {
  // Connect to the alert management API
  // Update alert status to acknowledged
  // Return true on success, false on failure
  console.log('Acknowledging alert:', alertId);
  return true;
};

const ProductionMonitoringDashboard: React.FC = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics[]>([]);
  const [deployments, setDeployments] = useState<DeploymentMetrics[]>([]);
  const [loading, setLoading] = useState(true);

  // Simulated real-time data fetch
  const fetchMonitoringData = useCallback(async () => {
    setLoading(true);
    try {
      // In production, these would be actual API calls
      // Simulating data for demonstration

      // Fetch alerts
      const mockAlerts: AlertData[] = [
        {
          id: '1',
          level: 'critical',
          message: 'Database connection pool exhausted',
          timestamp: new Date().toISOString(),
          service: 'PostgreSQL',
          acknowledged: false
        },
        {
          id: '2',
          level: 'warning',
          message: 'High memory usage detected',
          timestamp: new Date(Date.now() - 300000).toISOString(),
          service: 'API Server',
          acknowledged: false
        }
      ];

      // Fetch service health
      const mockServices: ServiceHealth[] = [
        {
          name: 'API Gateway',
          status: 'healthy',
          uptime: 99.9,
          responseTime: 145,
          errorRate: 0.1,
          lastCheck: new Date().toISOString()
        },
        {
          name: 'PostgreSQL',
          status: 'degraded',
          uptime: 99.5,
          responseTime: 320,
          errorRate: 2.3,
          lastCheck: new Date().toISOString()
        },
        {
          name: 'Redis Cache',
          status: 'healthy',
          uptime: 99.99,
          responseTime: 12,
          errorRate: 0.01,
          lastCheck: new Date().toISOString()
        }
      ];

      // Generate system metrics time series
      const now = Date.now();
      const mockSystemMetrics: SystemMetrics[] = Array.from({ length: 20 }, (_, i) => ({
        cpu: Math.random() * 60 + 20,
        memory: Math.random() * 40 + 40,
        disk: Math.random() * 20 + 60,
        network: Math.random() * 80 + 10,
        timestamp: new Date(now - (19 - i) * 300000).toISOString()
      }));

      // Fetch recent deployments
      const mockDeployments: DeploymentMetrics[] = [
        {
          id: 'deploy-001',
          version: 'v1.2.3',
          status: 'success',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          duration: 180,
          errorRate: 0.05
        },
        {
          id: 'deploy-002',
          version: 'v1.2.4',
          status: 'failed',
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          duration: 45,
          errorRate: 15.2
        }
      ];

      setAlerts(mockAlerts);
      setServices(mockServices);
      setSystemMetrics(mockSystemMetrics);
      setDeployments(mockDeployments);
    } catch (error) {
      console.error('Failed to fetch monitoring data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMonitoringData();
    let intervalId: NodeJS.Timeout | undefined;
    if (autoRefresh) {
      intervalId = setInterval(fetchMonitoringData, 30000); // Refresh every 30 seconds
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [fetchMonitoringData, autoRefresh]);

  // Calculate overall system health score
  const healthScore = useMemo(() => {
    const healthyServices = services.filter(s => s.status === 'healthy').length;
    const totalServices = services.length;
    const serviceScore = (healthyServices / totalServices) * 50;

    const avgErrorRate = services.reduce((sum, s) => sum + s.errorRate, 0) / totalServices;
    const errorScore = Math.max(0, 30 - (avgErrorRate * 10));

    const avgResponseTime = services.reduce((sum, s) => sum + s.responseTime, 0) / totalServices;
    const performanceScore = Math.max(0, 20 - (avgResponseTime / 50));

    return Math.round(serviceScore + errorScore + performanceScore);
  }, [services]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'warning': case 'degraded': return 'bg-yellow-500';
      case 'critical': case 'down': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getAlertColor = (level: string): 'info' | 'success' | 'warning' | 'error' => {
    switch (level) {
      case 'critical': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'info';
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await acknowledgeAlert(alertId);
      setAlerts(prev => prev.map(alert =>
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      ));
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading monitoring dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Production Monitoring Dashboard</h1>
          <p className="text-gray-600 mt-1">Real-time system health and performance metrics</p>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium">Time Range:</label>
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value)}
              className="border rounded px-3 py-1 text-sm"
            >
              <option value="5m">5 Minutes</option>
              <option value="1h">1 Hour</option>
              <option value="6h">6 Hours</option>
              <option value="24h">24 Hours</option>
            </select>
          </div>

          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </Button>

          <Button variant="outline" size="sm" onClick={fetchMonitoringData}>
            Refresh Now
          </Button>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Health Score</CardTitle>
            <div className={`h-3 w-3 rounded-full ${healthScore > 80 ? 'bg-green-500' : healthScore > 60 ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{healthScore}/100</div>
            <p className="text-xs text-muted-foreground">
              {healthScore > 80 ? 'Excellent' : healthScore > 60 ? 'Good' : 'Needs Attention'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Services</CardTitle>
            <div className="h-3 w-3 rounded-full bg-green-500"></div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{services.length}</div>
            <p className="text-xs text-muted-foreground">
              {services.filter(s => s.status === 'healthy').length} healthy
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <div className={`h-3 w-3 rounded-full ${alerts.filter(a => !a.acknowledged && a.level === 'critical').length > 0 ? 'bg-red-500' : 'bg-yellow-500'}`}></div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{alerts.filter(a => !a.acknowledged).length}</div>
            <p className="text-xs text-muted-foreground">
              {alerts.filter(a => !a.acknowledged && a.level === 'critical').length} critical
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Uptime</CardTitle>
            <div className="h-3 w-3 rounded-full bg-green-500"></div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">99.9%</div>
            <p className="text-xs text-muted-foreground">Last 30 days</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="deployments">Deployments</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Service Health */}
            <Card>
              <CardHeader>
                <CardTitle>Service Health</CardTitle>
                <CardDescription>Real-time service status and performance</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {services.map((service) => (
                    <div key={service.name} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className={`h-3 w-3 rounded-full ${getStatusColor(service.status)}`}></div>
                        <div>
                          <p className="font-medium">{service.name}</p>
                          <p className="text-sm text-gray-500">
                            {service.responseTime}ms • {service.errorRate}% errors
                          </p>
                        </div>
                      </div>
                      <Badge variant={service.status === 'healthy' ? 'default' : 'error'}>
                        {service.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* System Resources */}
            <Card>
              <CardHeader>
                <CardTitle>System Resources</CardTitle>
                <CardDescription>Real-time resource utilization</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {systemMetrics.length > 0 && (
                    <>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>CPU Usage</span>
                          <span>{systemMetrics[systemMetrics.length - 1].cpu.toFixed(1)}%</span>
                        </div>
                        <Progress value={systemMetrics[systemMetrics.length - 1].cpu} className="h-2" />
                      </div>

                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Memory Usage</span>
                          <span>{systemMetrics[systemMetrics.length - 1].memory.toFixed(1)}%</span>
                        </div>
                        <Progress value={systemMetrics[systemMetrics.length - 1].memory} className="h-2" />
                      </div>

                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Disk Usage</span>
                          <span>{systemMetrics[systemMetrics.length - 1].disk.toFixed(1)}%</span>
                        </div>
                        <Progress value={systemMetrics[systemMetrics.length - 1].disk} className="h-2" />
                      </div>

                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Network I/O</span>
                          <span>{systemMetrics[systemMetrics.length - 1].network.toFixed(1)}%</span>
                        </div>
                        <Progress value={systemMetrics[systemMetrics.length - 1].network} className="h-2" />
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Services Tab */}
        <TabsContent value="services" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {services.map((service) => (
              <Card key={service.name}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{service.name}</CardTitle>
                    <div className={`h-3 w-3 rounded-full ${getStatusColor(service.status)}`}></div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Status</span>
                      <Badge variant={service.status === 'healthy' ? 'default' : 'error'}>
                        {service.status}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Uptime</span>
                      <span className="text-sm font-medium">{service.uptime}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Response Time</span>
                      <span className="text-sm font-medium">{service.responseTime}ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Error Rate</span>
                      <span className="text-sm font-medium">{service.errorRate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Last Check</span>
                      <span className="text-sm font-medium">
                        {new Date(service.lastCheck).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>System Metrics Over Time</CardTitle>
                <CardDescription>CPU, Memory, Disk, and Network usage trends</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={systemMetrics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="cpu" stroke="#8884d8" name="CPU %" />
                    <Line type="monotone" dataKey="memory" stroke="#82ca9d" name="Memory %" />
                    <Line type="monotone" dataKey="disk" stroke="#ffc658" name="Disk %" />
                    <Line type="monotone" dataKey="network" stroke="#ff7300" name="Network %" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Response Time Trends</CardTitle>
                <CardDescription>Service response time trends over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={systemMetrics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Area type="monotone" dataKey="cpu" stroke="#8884d8" fill="#8884d8" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts" className="space-y-4">
          <div className="space-y-4">
            {alerts.length === 0 ? (
              <Card>
                <CardContent className="text-center py-8">
                  <p className="text-gray-500">No active alerts</p>
                </CardContent>
              </Card>
            ) : (
              alerts.map((alert) => (
                <Alert key={alert.id} variant={getAlertColor(alert.level)}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <Badge variant={getAlertColor(alert.level) as any}>{alert.level.toUpperCase()}</Badge>
                        <span className="text-sm text-gray-500">{alert.service}</span>
                        <span className="text-sm text-gray-500">
                          {new Date(alert.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <AlertDescription>{alert.message}</AlertDescription>
                    </div>
                    {!alert.acknowledged && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleAcknowledgeAlert(alert.id)}
                        className="ml-4"
                      >
                        Acknowledge
                      </Button>
                    )}
                  </div>
                </Alert>
              ))
            )}
          </div>
        </TabsContent>

        {/* Deployments Tab */}
        <TabsContent value="deployments" className="space-y-4">
          <div className="space-y-4">
            {deployments.map((deployment) => (
              <Card key={deployment.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg">{deployment.version}</CardTitle>
                      <CardDescription>Deployment ID: {deployment.id}</CardDescription>
                    </div>
                    <Badge variant={deployment.status === 'success' ? 'default' : 'error'}>
                      {deployment.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Duration</p>
                      <p className="font-medium">{deployment.duration}s</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Error Rate</p>
                      <p className="font-medium">{deployment.errorRate}%</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Timestamp</p>
                      <p className="font-medium">
                        {new Date(deployment.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Status</p>
                      <p className="font-medium capitalize">{deployment.status.replace('_', ' ')}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ProductionMonitoringDashboard;
