/**
 * Performance Monitoring Dashboard
 *
 * Real-time visualization of system performance metrics including:
 * - Query performance and slow queries
 * - Connection pool health
 * - Memory and CPU usage
 * - Response time percentiles (P50/P95/P99)
 * - N+1 query detection
 * - System alerts
 *
 * @component
 * @example
 * return <PerformanceMonitoringDashboard />
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/Badge';

interface QueryMetric {
  execution_count: number;
  avg_time: number;
  max_time: number;
  last_executed: string | null;
}

interface SlowQuery {
  query: string;
  execution_time: number;
  timestamp: string;
  result_size: number;
  endpoint: string | null;
}

interface PoolMetrics {
  total_connections: number;
  checked_out: number;
}

interface SystemMetrics {
  memory_usage_mb: number;
  cpu_usage_percent: number;
}

interface ResponseTimes {
  p50: number;
  p95: number;
  p99: number;
}

interface PerformanceSnapshot {
  query_metrics: Record<string, QueryMetric>;
  slow_queries: SlowQuery[];
  pool_metrics: PoolMetrics;
  system_metrics: SystemMetrics;
  response_times: ResponseTimes;
  issues_detected: {
    n_plus_1_queries: number;
    unbounded_queries: number;
    slow_queries: number;
  };
}

interface HealthStatus {
  status: 'healthy' | 'degraded';
  alerts: Array<{
    severity: 'critical' | 'warning';
    type: string;
    [key: string]: any;
  }>;
  metrics: PerformanceSnapshot;
}

export const PerformanceMonitoringDashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isDemoData, setIsDemoData] = useState(false);

  const fetchMetrics = async () => {
    console.log('🔄 fetchMetrics called');
    try {
      setError(null);
      setLoading(true);

      // Get access token from localStorage
      const token = localStorage.getItem('access_token');
      console.log('📝 Token exists:', !!token);
      console.log('📝 Token length:', token?.length || 0);

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      // Add Authorization header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        console.log('✅ Auth header added');
      } else {
        console.log('⚠️ No token found in localStorage');
      }

      console.log('📡 Fetching /api/v1/monitoring/health...');
      const response = await fetch('/api/v1/monitoring/health', {
        headers,
      });

      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        // If not authenticated or not admin, show demo data instead of error
        if (response.status === 403 || response.status === 401) {
          console.warn('Admin access required, showing demo data');
          setIsDemoData(true); // Mark as demo data
          // Show demo data instead of throwing error
          setHealth({
            status: 'healthy',
            alerts: [],
            metrics: {
              query_metrics: {
                'SELECT': { execution_count: 1523, avg_time: 0.023, max_time: 0.152, last_executed: new Date().toISOString() },
                'INSERT': { execution_count: 45, avg_time: 0.035, max_time: 0.089, last_executed: new Date().toISOString() },
              },
              slow_queries: [
                { query: 'SELECT * FROM responses WHERE user_id = ...', execution_time: 5.2, timestamp: new Date().toISOString(), result_size: 15000, endpoint: null },
              ],
              pool_metrics: { total_connections: 60, checked_out: 12 },
              system_metrics: { memory_usage_mb: 245, cpu_usage_percent: 12.3 },
              response_times: { p50: 0.145, p95: 0.167, p99: 0.234 },
              issues_detected: { n_plus_1_queries: 0, unbounded_queries: 0, slow_queries: 1 },
            },
          });
          setLoading(false);
          return;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: HealthStatus = await response.json();
      setHealth(data);
      setIsDemoData(false); // Real data
      console.log('✅ Real data loaded successfully!');
      console.log('📊 Status:', data.status);
      console.log('📊 Alerts:', data.alerts?.length || 0);
    } catch (err) {
      // If fetch fails completely, show demo data
      console.warn('❌ Failed to fetch metrics, showing demo data:', err);
      setIsDemoData(true); // Mark as demo data
      setHealth({
        status: 'healthy',
        alerts: [],
        metrics: {
          query_metrics: {
            'SELECT': { execution_count: 1523, avg_time: 0.023, max_time: 0.152, last_executed: new Date().toISOString() },
            'INSERT': { execution_count: 45, avg_time: 0.035, max_time: 0.089, last_executed: new Date().toISOString() },
          },
          slow_queries: [
            { query: 'SELECT * FROM responses WHERE user_id = ...', execution_time: 5.2, timestamp: new Date().toISOString(), result_size: 15000, endpoint: null },
          ],
          pool_metrics: { total_connections: 60, checked_out: 12 },
          system_metrics: { memory_usage_mb: 245, cpu_usage_percent: 12.3 },
          response_times: { p50: 0.145, p95: 0.167, p99: 0.234 },
          issues_detected: { n_plus_1_queries: 0, unbounded_queries: 0, slow_queries: 1 },
        },
      });
      console.log('✅ fetchMetrics completed');
    } finally {
      setLoading(false);
      console.log('🔄 Loading state set to false');
    }
  };

  useEffect(() => {
    fetchMetrics();

    if (autoRefresh) {
      const interval = setInterval(fetchMetrics, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <div className="text-red-600 text-2xl">⚠️</div>
            <div>
              <h3 className="font-semibold text-red-900">Error Loading Metrics</h3>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!health) {
    return null;
  }

  const { status, alerts, metrics } = health;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Performance Monitoring</h2>
          <p className="text-gray-600 text-sm mt-1">
            Real-time system performance metrics
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Badge
            variant={status === 'healthy' ? 'success' : 'warning'}
            className="text-sm px-3 py-1"
          >
            {status === 'healthy' ? '✅ Healthy' : '⚠️ Degraded'}
          </Badge>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            Auto-refresh (5s)
          </label>
          <button
            onClick={() => {
              console.log('🔄 Refresh button clicked!');
              // Clear cached demo data flag on manual refresh
              setIsDemoData(false);
              setLoading(true); // Show loading state
              fetchMetrics();
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
          >
            Refresh Now {loading ? '...' : ''}
          </button>
        </div>
      </div>

      {/* Demo Data Banner */}
      {isDemoData && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="text-yellow-600 text-2xl">⚠️</div>
              <div>
                <h3 className="font-semibold text-yellow-900">Demo Mode</h3>
                <p className="text-yellow-700 text-sm mt-1">
                  Unable to connect to the monitoring API (authentication required). Showing demo data.
                  Please login as an administrator to view real metrics.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-gray-900">Active Alerts</h3>
          <div className="grid gap-3">
            {alerts.map((alert, idx) => (
              <Card
                key={idx}
                className={`border-l-4 ${
                  alert.severity === 'critical'
                    ? 'border-red-500 bg-red-50'
                    : 'border-yellow-500 bg-yellow-50'
                }`}
              >
                <CardContent className="pt-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xl">
                          {alert.severity === 'critical' ? '🔴' : '⚠️'}
                        </span>
                        <h4 className="font-semibold text-gray-900 capitalize">
                          {alert.type.replace(/_/g, ' ')}
                        </h4>
                        <Badge
                          variant={alert.severity === 'critical' ? 'danger' : 'warning'}
                          className="text-xs"
                        >
                          {alert.severity.toUpperCase()}
                        </Badge>
                      </div>
                      <p className="text-gray-700 text-sm mt-1">{alert.message}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Response Times */}
        <MetricCard
          title="Response Times"
          value={`${(metrics.response_times.p95 * 1000).toFixed(0)}ms`}
          subtitle={`P95: ${(metrics.response_times.p95 * 1000).toFixed(0)}ms | P99: ${(metrics.response_times.p99 * 1000).toFixed(0)}ms`}
          color="blue"
        />

        {/* Memory Usage */}
        <MetricCard
          title="Memory Usage"
          value={`${metrics.system_metrics.memory_usage_mb.toFixed(0)} MB`}
          subtitle={`CPU: ${metrics.system_metrics.cpu_usage_percent.toFixed(1)}%`}
          color={metrics.system_metrics.memory_usage_mb > 1000 ? 'red' : 'green'}
        />

        {/* Connection Pool */}
        <MetricCard
          title="Connection Pool"
          value={`${metrics.pool_metrics.checked_out}/${metrics.pool_metrics.total_connections}`}
          subtitle="Active connections"
          color={metrics.pool_metrics.checked_out / metrics.pool_metrics.total_connections > 0.9 ? 'red' : 'green'}
        />

        {/* Issues Detected */}
        <MetricCard
          title="Issues Detected"
          value={Object.values(metrics.issues_detected).reduce((a, b) => a + b, 0).toString()}
          subtitle={`${metrics.issues_detected.slow_queries} slow queries`}
          color={Object.values(metrics.issues_detected).reduce((a, b) => a + b, 0) > 0 ? 'yellow' : 'green'}
        />
      </div>

      {/* Slow Queries Table */}
      {metrics.slow_queries.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Slow Queries (Last 20)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Query</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Time (s)</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Rows</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.slow_queries.map((query, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-mono text-xs max-w-md truncate" title={query.query}>
                        {query.query}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="danger">{query.execution_time.toFixed(3)}s</Badge>
                      </td>
                      <td className="py-3 px-4">{query.result_size.toLocaleString()}</td>
                      <td className="py-3 px-4 text-gray-600">
                        {new Date(query.timestamp).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Query Performance Breakdown */}
      {Object.keys(metrics.query_metrics).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Query Performance Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(metrics.query_metrics).map(([query, metric]) => (
                <div key={query} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <code className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">{query}</code>
                      <Badge variant="info" className="text-xs">
                        {metric.execution_count} execs
                      </Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-6 text-sm">
                    <div>
                      <span className="text-gray-600">Avg: </span>
                      <span className="font-semibold">{(metric.avg_time * 1000).toFixed(1)}ms</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Max: </span>
                      <span className={`font-semibold ${metric.max_time > 1.0 ? 'text-red-600' : 'text-gray-900'}`}>
                        {(metric.max_time * 1000).toFixed(1)}ms
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  color: 'blue' | 'green' | 'red' | 'yellow';
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, subtitle, color }) => {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    red: 'bg-red-50 border-red-200',
    yellow: 'bg-yellow-50 border-yellow-200',
  };

  const iconMap = {
    blue: '⚡',
    green: '✅',
    red: '🔴',
    yellow: '⚠️',
  };

  return (
    <Card className={`${colorClasses[color]} border`}>
      <CardContent className="pt-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-gray-600 text-sm font-medium">{title}</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
            <p className="text-gray-600 text-xs mt-1">{subtitle}</p>
          </div>
          <div className="text-2xl">{iconMap[color]}</div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PerformanceMonitoringDashboard;
