// Longitudinal Comparison Component
// Advanced visualizations for comparing behavioral changes over time

import React, { useState, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
  Cell,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Calendar,
  Users,
  AlertTriangle,
  CheckCircle,
  Clock,
  GitCompare,
  Filter,
  Download,
  Eye,
  Crosshair,
  Zap,
} from 'lucide-react';

// Types for longitudinal comparison
interface LongitudinalData {
  timestamp: string;
  value: number;
  user_id: string;
  user_name: string;
  metric_name: string;
  change_point?: boolean;
  change_type?: string;
  baseline?: number;
  confidence?: number;
}

interface ChangeEvent {
  id: string;
  timestamp: string;
  user_id: string;
  user_name: string;
  metric_name: string;
  change_type: string;
  severity: 'minor' | 'moderate' | 'significant' | 'critical';
  baseline_value: number;
  current_value: number;
  change_magnitude: number;
  confidence: number;
  description: string;
  algorithm: string;
}

interface TrendAnalysis {
  user_id: string;
  user_name: string;
  metric_name: string;
  trend_direction: 'increasing' | 'decreasing' | 'stable' | 'volatile';
  trend_slope: number;
  r_squared: number;
  p_value: number;
  seasonal_component: boolean;
  forecast_next?: number;
  forecast_confidence_lower?: number;
  forecast_confidence_upper?: number;
}

interface ComparisonMetrics {
  user_id: string;
  user_name: string;
  total_changes: number;
  critical_changes: number;
  avg_change_magnitude: number;
  trend_score: number;
  volatility: number;
  stability_index: number;
  last_change_date: string;
}

interface LongitudinalComparisonProps {
  users?: Array<{ id: string; name: string }>;
  metrics?: Array<{ name: string; label: string; unit: string }>;
  timeRange?: string;
  showChangePoints?: boolean;
  showForecasts?: boolean;
  showTrends?: boolean;
  className?: string;
}

const COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // yellow
  '#ef4444', // red
  '#8b5cf6', // purple
  '#22c55e', // emerald
  '#f97316', // orange
  '#06b6d4', // cyan
];

const SEVERITY_COLORS = {
  minor: '#22c55e',
  moderate: '#f59e0b',
  significant: '#f97316',
  critical: '#ef4444',
};

const LongitudinalComparison: React.FC<LongitudinalComparisonProps> = ({
  users = [],
  metrics = [],
  timeRange = '90d',
  showChangePoints = true,
  showForecasts = true,
  showTrends = true,
  className
}) => {
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string>('daily_activity');
  const [comparisonType, setComparisonType] = useState<'overlaid' | 'separate' | 'difference'>('overlaid');
  const [showStatisticalTests, setShowStatisticalTests] = useState(true);
  const [highlightChanges, setHighlightChanges] = useState(true);
  const [viewType, setViewType] = useState<'line' | 'area' | 'bar'>('line');

  // TODO(human): Fetch actual data from API
  const mockData: LongitudinalData[] = useMemo(() => {
    const data: LongitudinalData[] = [];
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 90);

    // Generate data for each selected user
    const usersToGenerate = selectedUsers.length > 0 ? selectedUsers : users.slice(0, 3).map(u => u.id);

    usersToGenerate.forEach((userId, userIndex) => {
      const user = users.find(u => u.id === userId);
      const userName = user?.name || `User ${userIndex + 1}`;

      // Generate 90 days of data
      for (let i = 0; i < 90; i++) {
        const date = new Date(startDate);
        date.setDate(date.getDate() + i);

        // Generate realistic behavioral data with trends and changes
        let baseValue = 50 + userIndex * 10;

        // Add trend
        baseValue += i * 0.3;

        // Add seasonal component
        baseValue += 10 * Math.sin(2 * Math.PI * i / 7);

        // Add random noise
        baseValue += (Math.random() - 0.5) * 15;

        // Add some change points
        const isChangePoint = (i === 30 || i === 60) && Math.random() > 0.5;
        if (isChangePoint) {
          baseValue += (Math.random() - 0.5) * 30;
        }

        data.push({
          timestamp: date.toISOString(),
          value: Math.max(0, baseValue),
          user_id: userId,
          user_name: userName,
          metric_name: selectedMetric,
          change_point: isChangePoint,
          change_type: isChangePoint ? 'level_shift' : undefined,
          baseline: 50 + userIndex * 10,
          confidence: isChangePoint ? 0.85 + Math.random() * 0.1 : undefined
        });
      }
    });

    return data;
  }, [selectedUsers, users, selectedMetric]);

  // Mock change events
  const mockChangeEvents: ChangeEvent[] = useMemo(() => {
    const events: ChangeEvent[] = [];
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 90);

    const usersToGenerate = selectedUsers.length > 0 ? selectedUsers : users.slice(0, 3).map(u => u.id);

    usersToGenerate.forEach((userId, userIndex) => {
      const user = users.find(u => u.id === userId);
      const userName = user?.name || `User ${userIndex + 1}`;

      // Generate 2-4 change events per user
      const numChanges = 2 + Math.floor(Math.random() * 3);

      for (let i = 0; i < numChanges; i++) {
        const changeDate = new Date(startDate);
        changeDate.setDate(changeDate.getDate() + Math.floor(Math.random() * 80) + 5);

        const severities: Array<'minor' | 'moderate' | 'significant' | 'critical'> =
          ['minor', 'moderate', 'significant', 'critical'];
        const severity = severities[Math.floor(Math.random() * severities.length)];

        events.push({
          id: `change_${userId}_${i}`,
          timestamp: changeDate.toISOString(),
          user_id: userId,
          user_name: userName,
          metric_name: selectedMetric,
          change_type: 'level_shift',
          severity,
          baseline_value: 45 + userIndex * 10 + Math.random() * 10,
          current_value: 60 + userIndex * 10 + Math.random() * 20,
          change_magnitude: 15 + Math.random() * 25,
          confidence: 0.7 + Math.random() * 0.25,
          description: `Significant behavioral change detected in ${selectedMetric}`,
          algorithm: 'CUSUM'
        });
      }
    });

    return events.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  }, [selectedUsers, users, selectedMetric]);

  // Mock trend analysis
  const mockTrendAnalysis: TrendAnalysis[] = useMemo(() => {
    const usersToGenerate = selectedUsers.length > 0 ? selectedUsers : users.slice(0, 3).map(u => u.id);

    return usersToGenerate.map((userId, userIndex) => {
      const user = users.find(u => u.id === userId);
      const userName = user?.name || `User ${userIndex + 1}`;

      const trendDirections: Array<'increasing' | 'decreasing' | 'stable' | 'volatile'> =
        ['increasing', 'decreasing', 'stable', 'volatile'];
      const trend_direction = trendDirections[Math.floor(Math.random() * trendDirections.length)];

      return {
        user_id: userId,
        user_name: userName,
        metric_name: selectedMetric,
        trend_direction,
        trend_slope: (Math.random() - 0.5) * 2,
        r_squared: 0.3 + Math.random() * 0.6,
        p_value: Math.random() * 0.1,
        seasonal_component: Math.random() > 0.5,
        forecast_next: 60 + userIndex * 10 + Math.random() * 20,
        forecast_confidence_lower: 55 + userIndex * 10,
        forecast_confidence_upper: 65 + userIndex * 10 + Math.random() * 20
      };
    });
  }, [selectedUsers, users, selectedMetric]);

  // Mock comparison metrics
  const mockComparisonMetrics: ComparisonMetrics[] = useMemo(() => {
    const usersToGenerate = selectedUsers.length > 0 ? selectedUsers : users.slice(0, 3).map(u => u.id);

    return usersToGenerate.map((userId, userIndex) => {
      const user = users.find(u => u.id === userId);
      const userName = user?.name || `User ${userIndex + 1}`;

      return {
        user_id: userId,
        user_name: userName,
        total_changes: 2 + Math.floor(Math.random() * 4),
        critical_changes: Math.floor(Math.random() * 2),
        avg_change_magnitude: 15 + Math.random() * 20,
        trend_score: 0.3 + Math.random() * 0.6,
        volatility: 0.2 + Math.random() * 0.4,
        stability_index: 0.4 + Math.random() * 0.4,
        last_change_date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString()
      };
    });
  }, [selectedUsers, users]);

  const handleUserToggle = (userId: string) => {
    setSelectedUsers(prev => {
      if (prev.includes(userId)) {
        return prev.filter(id => id !== userId);
      } else {
        return [...prev, userId];
      }
    });
  };

  const getSeverityColor = (severity: string) => {
    return SEVERITY_COLORS[severity as keyof typeof SEVERITY_COLORS] || '#94a3b8';
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'increasing':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'decreasing':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      case 'volatile':
        return <Activity className="h-4 w-4 text-orange-600" />;
      default:
        return <Activity className="h-4 w-4 text-blue-600" />;
    }
  };

  // Process data for visualization
  const processedData = useMemo(() => {
    if (comparisonType === 'difference') {
      // For difference comparison, calculate difference from baseline
      return mockData.map(point => ({
        ...point,
        value: point.value - (point.baseline || 0)
      }));
    }
    return mockData;
  }, [mockData, comparisonType]);

  // Custom tooltip for rich information display
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg max-w-xs">
          <p className="font-medium">{new Date(label).toLocaleDateString()}</p>
          <p className="text-sm text-gray-600">{data.user_name}</p>
          <p className="text-sm font-semibold">Value: {data.value.toFixed(2)}</p>
          {data.change_point && (
            <div className="mt-2 p-2 bg-yellow-50 rounded">
              <p className="text-xs font-medium text-yellow-800">Change Point Detected</p>
              <p className="text-xs text-yellow-700">{data.change_type?.replace('_', ' ')}</p>
              {data.confidence && (
                <p className="text-xs text-yellow-700">Confidence: {(data.confidence * 100).toFixed(1)}%</p>
              )}
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  // Render visualization based on type
  const renderVisualization = () => {
    const usersToRender = selectedUsers.length > 0 ? selectedUsers : users.slice(0, 3).map(u => u.id);

    switch (viewType) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={processedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis />
              <Tooltip content={<CustomTooltip />} />
              <Legend />

              {/* Reference line for baseline */}
              {comparisonType !== 'difference' && (
                <ReferenceLine
                  y={50}
                  stroke="#94a3b8"
                  strokeDasharray="5 5"
                  label="Baseline"
                />
              )}

              {/* Change point areas */}
              {showChangePoints && mockChangeEvents.map((event) => (
                <ReferenceArea
                  key={event.id}
                  x1={event.timestamp}
                  x2={new Date(new Date(event.timestamp).getTime() + 24 * 60 * 60 * 1000).toISOString()}
                  strokeOpacity={0.3}
                  fill={getSeverityColor(event.severity)}
                  fillOpacity={0.2}
                />
              ))}

              {/* Lines for each user */}
              {usersToRender.map((userId, index) => (
                <Line
                  key={userId}
                  type="monotone"
                  dataKey="value"
                  data={processedData.filter(d => d.user_id === userId)}
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  name={users.find(u => u.id === userId)?.name || `User ${index + 1}`}
                />
              ))}

              {/* Forecast areas */}
              {showForecasts && mockTrendAnalysis.map((trend, index) => {
                if (!trend.forecast_next) return null;

                const userIndex = usersToRender.indexOf(trend.user_id);
                if (userIndex === -1) return null;

                return (
                  <ReferenceArea
                    key={`forecast_${trend.user_id}`}
                    x1={processedData[processedData.length - 1]?.timestamp}
                    x2={new Date(new Date(processedData[processedData.length - 1]?.timestamp).getTime() + 7 * 24 * 60 * 60 * 1000).toISOString()}
                    y1={trend.forecast_confidence_lower}
                    y2={trend.forecast_confidence_upper}
                    stroke={COLORS[userIndex % COLORS.length]}
                    strokeOpacity={0.3}
                    fill={COLORS[userIndex % COLORS.length]}
                    fillOpacity={0.1}
                    label={`${trend.user_name} Forecast`}
                  />
                );
              })}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={processedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis />
              <Tooltip content={<CustomTooltip />} />
              <Legend />

              {usersToRender.map((userId, index) => (
                <Area
                  key={userId}
                  type="monotone"
                  dataKey="value"
                  data={processedData.filter(d => d.user_id === userId)}
                  stroke={COLORS[index % COLORS.length]}
                  fill={COLORS[index % COLORS.length]}
                  fillOpacity={0.3}
                  strokeWidth={2}
                  name={users.find(u => u.id === userId)?.name || `User ${index + 1}`}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={processedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis />
              <Tooltip content={<CustomTooltip />} />
              <Legend />

              {usersToRender.map((userId, index) => (
                <Bar
                  key={userId}
                  dataKey="value"
                  data={processedData.filter(d => d.user_id === userId)}
                  fill={COLORS[index % COLORS.length]}
                  name={users.find(u => u.id === userId)?.name || `User ${index + 1}`}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header and Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center">
                <GitCompare className="h-5 w-5 mr-2" />
                Longitudinal Comparison
              </CardTitle>
              <CardDescription>
                Compare behavioral patterns and changes over time
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button variant="outline" size="sm">
                <Eye className="h-4 w-4 mr-2" />
                Details
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* User Selection */}
            <div>
              <label className="text-sm font-medium mb-2 block">Select Users</label>
              <div className="space-y-2 max-h-32 overflow-y-auto border rounded p-2">
                {users.map((user) => (
                  <div key={user.id} className="flex items-center space-x-2">
                    <Checkbox
                      id={user.id}
                      checked={selectedUsers.includes(user.id)}
                      onCheckedChange={() => handleUserToggle(user.id)}
                    />
                    <label htmlFor={user.id} className="text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                      {user.name}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* Metric Selection */}
            <div>
              <label className="text-sm font-medium mb-2 block">Metric</label>
              <Select value={selectedMetric} onValueChange={setSelectedMetric}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {metrics.map((metric) => (
                    <SelectItem key={metric.name} value={metric.name}>
                      {metric.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Comparison Type */}
            <div>
              <label className="text-sm font-medium mb-2 block">Comparison Type</label>
              <Select value={comparisonType} onValueChange={(value: any) => setComparisonType(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="overlaid">Overlaid</SelectItem>
                  <SelectItem value="separate">Separate</SelectItem>
                  <SelectItem value="difference">Difference from Baseline</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* View Type */}
            <div>
              <label className="text-sm font-medium mb-2 block">View Type</label>
              <Select value={viewType} onValueChange={(value: any) => setViewType(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="line">Line Chart</SelectItem>
                  <SelectItem value="area">Area Chart</SelectItem>
                  <SelectItem value="bar">Bar Chart</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Display Options */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="showChangePoints"
                checked={showChangePoints}
                onCheckedChange={(checked) => setShowChangePoints(checked as boolean)}
              />
              <label htmlFor="showChangePoints" className="text-sm">
                Show Change Points
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="showForecasts"
                checked={showForecasts}
                onCheckedChange={(checked) => setShowForecasts(checked as boolean)}
              />
              <label htmlFor="showForecasts" className="text-sm">
                Show Forecasts
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="showTrends"
                checked={showTrends}
                onCheckedChange={(checked) => setShowTrends(checked as boolean)}
              />
              <label htmlFor="showTrends" className="text-sm">
                Show Trends
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>
            {selectedMetric} - {comparisonType === 'difference' ? 'Difference from Baseline' : 'Values Over Time'}
          </CardTitle>
          <CardDescription>
            {selectedUsers.length > 0 ? selectedUsers.length : users.slice(0, 3).length} users • Last 90 days
          </CardDescription>
        </CardHeader>
        <CardContent>
          {mockData.length > 0 ? (
            renderVisualization()
          ) : (
            <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border">
              <div className="text-center">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-sm text-gray-600">Select users to view longitudinal comparison</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Change Events Summary */}
      {mockChangeEvents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              Detected Changes ({mockChangeEvents.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {mockChangeEvents.slice(0, 5).map((event) => (
                <div key={event.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getSeverityColor(event.severity) }}
                    />
                    <div>
                      <p className="font-medium text-sm">{event.user_name}</p>
                      <p className="text-xs text-gray-600">{new Date(event.timestamp).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge className={getSeverityColor(event.severity)}>
                      {event.severity}
                    </Badge>
                    <p className="text-xs text-gray-600 mt-1">
                      Δ{event.change_magnitude.toFixed(1)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            {mockChangeEvents.length > 5 && (
              <div className="text-center mt-4">
                <Button variant="outline" size="sm">
                  View All Changes ({mockChangeEvents.length - 5} more)
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Trend Analysis Summary */}
      {showTrends && mockTrendAnalysis.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="h-5 w-5 mr-2" />
              Trend Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {mockTrendAnalysis.map((trend) => (
                <div key={trend.user_id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{trend.user_name}</h4>
                    {getTrendIcon(trend.trend_direction)}
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Direction:</span>
                      <span className="font-medium capitalize">{trend.trend_direction}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">R²:</span>
                      <span className="font-medium">{trend.r_squared.toFixed(3)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">P-value:</span>
                      <span className="font-medium">{trend.p_value.toFixed(3)}</span>
                    </div>
                    {trend.forecast_next && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Forecast:</span>
                        <span className="font-medium">{trend.forecast_next.toFixed(1)}</span>
                      </div>
                    )}
                    {trend.seasonal_component && (
                      <div className="flex items-center space-x-1">
                        <Calendar className="h-3 w-3 text-blue-500" />
                        <span className="text-xs text-blue-600">Seasonal Pattern</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Comparison Metrics Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart3 className="h-5 w-5 mr-2" />
            Comparison Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">User</th>
                  <th className="text-center p-2">Total Changes</th>
                  <th className="text-center p-2">Critical</th>
                  <th className="text-center p-2">Avg Magnitude</th>
                  <th className="text-center p-2">Trend Score</th>
                  <th className="text-center p-2">Stability</th>
                  <th className="text-center p-2">Last Change</th>
                </tr>
              </thead>
              <tbody>
                {mockComparisonMetrics.map((metrics) => (
                  <tr key={metrics.user_id} className="border-b">
                    <td className="p-2 font-medium">{metrics.user_name}</td>
                    <td className="text-center p-2">{metrics.total_changes}</td>
                    <td className="text-center p-2">
                      <Badge className={metrics.critical_changes > 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}>
                        {metrics.critical_changes}
                      </Badge>
                    </td>
                    <td className="text-center p-2">{metrics.avg_change_magnitude.toFixed(1)}</td>
                    <td className="text-center p-2">
                      <div className="flex items-center justify-center">
                        <div className="w-12 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${metrics.trend_score * 100}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="text-center p-2">
                      <div className="flex items-center justify-center">
                        {metrics.stability_index > 0.7 ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : metrics.stability_index > 0.4 ? (
                          <AlertTriangle className="h-4 w-4 text-yellow-600" />
                        ) : (
                          <Zap className="h-4 w-4 text-red-600" />
                        )}
                      </div>
                    </td>
                    <td className="text-center p-2 text-xs">
                      {new Date(metrics.last_change_date).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LongitudinalComparison;