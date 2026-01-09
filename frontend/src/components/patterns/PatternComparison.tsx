// Pattern Comparison Component
// Compare behavioral patterns across users, teams, or time periods

import React, { useState, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
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
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import {
  Users,
  Calendar,
  TrendingUp,
  Scale,
  GitCompare,
  Filter,
  Download,
  ChevronDown,
  Eye,
  Crosshair,
} from 'lucide-react';

// Types for pattern comparison
interface ComparisonPattern {
  user_id: string;
  user_name: string;
  patterns: {
    temporal: number;
    sequential: number;
    social: number;
    learning: number;
    risk: number;
    performance: number;
  };
  metrics: {
    total_events: number;
    success_rate: number;
    avg_session_duration: number;
    pattern_diversity: number;
    anomaly_count: number;
    risk_score: number;
  };
  time_period: string;
}

interface ComparisonMetric {
  name: string;
  [key: string]: string | number;
}

interface PatternComparisonProps {
  users?: Array<{ id: string; name: string }>;
  teams?: Array<{ id: string; name: string }>;
  timeRanges?: Array<{ value: string; label: string }>;
  className?: string;
}

const COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // yellow
  '#ef4444', // red
  '#8b5cf6', // purple
  '#22c55e', // green
  '#f97316', // orange
];

const PatternComparison: React.FC<PatternComparisonProps> = ({
  users = [],
  teams = [],
  timeRanges = [
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' },
  ],
  className
}) => {
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>('30d');
  const [comparisonType, setComparisonType] = useState<'users' | 'teams' | 'time'>('users');
  const [viewType, setViewType] = useState<'radar' | 'line' | 'bar'>('radar');
  const [showDetails, setShowDetails] = useState(false);

  // TODO(human): Fetch actual comparison data from API
  const comparisonData = useMemo(() => {
    // Mock data for demonstration
    const mockData: ComparisonPattern[] = [
      {
        user_id: 'user1',
        user_name: 'Alice Johnson',
        time_period: selectedTimeRange,
        patterns: {
          temporal: 0.85,
          sequential: 0.72,
          social: 0.68,
          learning: 0.91,
          risk: 0.15,
          performance: 0.79,
        },
        metrics: {
          total_events: 2847,
          success_rate: 0.94,
          avg_session_duration: 27,
          pattern_diversity: 0.34,
          anomaly_count: 3,
          risk_score: 0.12,
        },
      },
      {
        user_id: 'user2',
        user_name: 'Bob Smith',
        time_period: selectedTimeRange,
        patterns: {
          temporal: 0.78,
          sequential: 0.85,
          social: 0.92,
          learning: 0.67,
          risk: 0.08,
          performance: 0.88,
        },
        metrics: {
          total_events: 3521,
          success_rate: 0.97,
          avg_session_duration: 45,
          pattern_diversity: 0.42,
          anomaly_count: 1,
          risk_score: 0.05,
        },
      },
      {
        user_id: 'user3',
        user_name: 'Carol Davis',
        time_period: selectedTimeRange,
        patterns: {
          temporal: 0.62,
          sequential: 0.58,
          social: 0.34,
          learning: 0.73,
          risk: 0.35,
          performance: 0.67,
        },
        metrics: {
          total_events: 1567,
          success_rate: 0.89,
          avg_session_duration: 18,
          pattern_diversity: 0.28,
          anomaly_count: 7,
          risk_score: 0.42,
        },
      },
      {
        user_id: 'user4',
        user_name: 'David Wilson',
        time_period: selectedTimeRange,
        patterns: {
          temporal: 0.91,
          sequential: 0.67,
          social: 0.71,
          learning: 0.85,
          risk: 0.12,
          performance: 0.92,
        },
        metrics: {
          total_events: 4234,
          success_rate: 0.96,
          avg_session_duration: 52,
          pattern_diversity: 0.38,
          anomaly_count: 2,
          risk_score: 0.08,
        },
      },
    ];

    // Filter by selected users
    if (selectedUsers.length > 0) {
      return mockData.filter(user => selectedUsers.includes(user.user_id));
    }

    return mockData.slice(0, 3); // Default to first 3 users
  }, [selectedUsers, selectedTimeRange]);

  // Prepare data for radar chart
  const radarData = useMemo(() => {
    const patternTypes = ['temporal', 'sequential', 'social', 'learning', 'risk', 'performance'];

    return patternTypes.map(pattern => {
      const dataPoint: ComparisonMetric = { name: pattern.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) };

      comparisonData.forEach(user => {
        dataPoint[user.user_name] = Math.round(user.patterns[pattern as keyof typeof user.patterns] * 100);
      });

      return dataPoint;
    });
  }, [comparisonData]);

  // Prepare data for line chart (time series comparison)
  const lineData = useMemo(() => {
    // Generate time series data points
    const timePoints = Array.from({ length: 30 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (29 - i));
      return date.toISOString().split('T')[0];
    });

    return timePoints.map(date => {
      const dataPoint: ComparisonMetric = { name: date };

      comparisonData.forEach(user => {
        // Generate mock time series data
        dataPoint[user.user_name] = Math.floor(Math.random() * 50 + 30 + (Math.random() * 20));
      });

      return dataPoint;
    });
  }, [comparisonData]);

  // Prepare data for bar chart (metrics comparison)
  const barData = useMemo(() => {
    const metricNames = [
      { key: 'total_events', label: 'Total Events' },
      { key: 'success_rate', label: 'Success Rate (%)' },
      { key: 'avg_session_duration', label: 'Avg Session (min)' },
      { key: 'pattern_diversity', label: 'Pattern Diversity' },
      { key: 'anomaly_count', label: 'Anomalies' },
      { key: 'risk_score', label: 'Risk Score (%)' },
    ];

    return metricNames.map(({ key, label }) => {
      const dataPoint: ComparisonMetric = { name: label };

      comparisonData.forEach(user => {
        const value = user.metrics[key as keyof typeof user.metrics];
        if (key === 'success_rate' || key === 'pattern_diversity' || key === 'risk_score') {
          dataPoint[user.user_name] = Math.round(value * 100);
        } else if (key === 'avg_session_duration') {
          dataPoint[user.user_name] = Math.round(value);
        } else {
          dataPoint[user.user_name] = value;
        }
      });

      return dataPoint;
    });
  }, [comparisonData]);

  // Calculate similarity scores between users
  const similarityMatrix = useMemo(() => {
    const matrix: number[][] = [];

    comparisonData.forEach((user1, i) => {
      const row: number[] = [];
      comparisonData.forEach((user2, j) => {
        if (i === j) {
          row.push(1.0);
        } else {
          // Simple similarity calculation based on patterns
          const patterns1 = Object.values(user1.patterns);
          const patterns2 = Object.values(user2.patterns);
          const similarity = patterns1.reduce((acc, val, idx) => {
            return acc + (1 - Math.abs(val - patterns2[idx]));
          }, 0) / patterns1.length;
          row.push(Math.round(similarity * 100) / 100);
        }
      });
      matrix.push(row);
    });

    return matrix;
  }, [comparisonData]);

  const handleUserToggle = (userId: string) => {
    setSelectedUsers(prev => {
      if (prev.includes(userId)) {
        return prev.filter(id => id !== userId);
      } else {
        return [...prev, userId];
      }
    });
  };

  const renderVisualization = () => {
    switch (viewType) {
      case 'radar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="name" />
              <PolarRadiusAxis angle={90} domain={[0, 100]} />
              {comparisonData.map((user, index) => (
                <Radar
                  key={user.user_id}
                  name={user.user_name}
                  dataKey={user.user_name}
                  stroke={COLORS[index % COLORS.length]}
                  fill={COLORS[index % COLORS.length]}
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              ))}
              <Legend />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={lineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              {comparisonData.map((user, index) => (
                <Line
                  key={user.user_id}
                  type="monotone"
                  dataKey={user.user_name}
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Legend />
              {comparisonData.map((user, index) => (
                <Bar
                  key={user.user_id}
                  dataKey={user.user_name}
                  fill={COLORS[index % COLORS.length]}
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
                Pattern Comparison
              </CardTitle>
              <CardDescription>
                Compare behavioral patterns across users, teams, or time periods
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button variant="outline" size="sm" onClick={() => setShowDetails(!showDetails)}>
                <Eye className="h-4 w-4 mr-2" />
                {showDetails ? 'Hide' : 'Show'} Details
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Comparison Type Selector */}
            <div>
              <label className="text-sm font-medium mb-2 block">Compare</label>
              <Select value={comparisonType} onValueChange={(value: any) => setComparisonType(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="users">Users</SelectItem>
                  <SelectItem value="teams">Teams</SelectItem>
                  <SelectItem value="time">Time Periods</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Time Range Selector */}
            <div>
              <label className="text-sm font-medium mb-2 block">Time Range</label>
              <Select value={selectedTimeRange} onValueChange={setSelectedTimeRange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {timeRanges.map((range) => (
                    <SelectItem key={range.value} value={range.value}>
                      {range.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* View Type Selector */}
            <div>
              <label className="text-sm font-medium mb-2 block">View Type</label>
              <Select value={viewType} onValueChange={(value: any) => setViewType(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="radar">Radar Chart</SelectItem>
                  <SelectItem value="line">Line Chart</SelectItem>
                  <SelectItem value="bar">Bar Chart</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* User Selection */}
      {comparisonType === 'users' && users.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Select Users to Compare</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {users.map((user) => (
                <div key={user.id} className="flex items-center space-x-2">
                  <Checkbox
                    id={user.id}
                    checked={selectedUsers.includes(user.id)}
                    onCheckedChange={() => handleUserToggle(user.id)}
                  />
                  <label htmlFor={user.id} className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                    {user.name}
                  </label>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>
            {viewType === 'radar' && 'Pattern Strength Comparison'}
            {viewType === 'line' && 'Activity Trend Comparison'}
            {viewType === 'bar' && 'Metrics Comparison'}
          </CardTitle>
          <CardDescription>
            {comparisonData.length} {comparisonType} selected for comparison
          </CardDescription>
        </CardHeader>
        <CardContent>
          {comparisonData.length > 0 ? (
            renderVisualization()
          ) : (
            <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border">
              <div className="text-center">
                <Users className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-sm text-gray-600">Select {comparisonType} to compare</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detailed Comparison Table */}
      {showDetails && comparisonData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Crosshair className="h-5 w-5 mr-2" />
              Detailed Comparison
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Metric</th>
                    {comparisonData.map((user) => (
                      <th key={user.user_id} className="text-center p-2">{user.user_name}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {/* Pattern Scores */}
                  {Object.keys(comparisonData[0].patterns).map((pattern) => (
                    <tr key={pattern} className="border-b">
                      <td className="p-2 font-medium">
                        {pattern.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </td>
                      {comparisonData.map((user, index) => (
                        <td key={user.user_id} className="text-center p-2">
                          <Badge
                            variant="outline"
                            className={
                              user.patterns[pattern as keyof typeof user.patterns] > 0.8
                                ? 'bg-green-50 text-green-700'
                                : user.patterns[pattern as keyof typeof user.patterns] > 0.5
                                ? 'bg-yellow-50 text-yellow-700'
                                : 'bg-red-50 text-red-700'
                            }
                          >
                            {Math.round(user.patterns[pattern as keyof typeof user.patterns] * 100)}%
                          </Badge>
                        </td>
                      ))}
                    </tr>
                  ))}

                  {/* Raw Metrics */}
                  <tr className="font-semibold bg-gray-50">
                    <td colSpan={comparisonData.length + 1} className="p-2">
                      Performance Metrics
                    </td>
                  </tr>
                  {[
                    { key: 'total_events', label: 'Total Events', format: (v: number) => v.toLocaleString() },
                    { key: 'success_rate', label: 'Success Rate', format: (v: number) => `${Math.round(v * 100)}%` },
                    { key: 'avg_session_duration', label: 'Avg Session', format: (v: number) => `${Math.round(v)} min` },
                    { key: 'pattern_diversity', label: 'Pattern Diversity', format: (v: number) => Math.round(v * 100) },
                    { key: 'anomaly_count', label: 'Anomalies', format: (v: number) => v.toString() },
                    { key: 'risk_score', label: 'Risk Score', format: (v: number) => Math.round(v * 100) },
                  ].map(({ key, label, format }) => (
                    <tr key={key} className="border-b">
                      <td className="p-2">{label}</td>
                      {comparisonData.map((user) => (
                        <td key={user.user_id} className="text-center p-2">
                          {format(user.metrics[key as keyof typeof user.metrics] as number)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Similarity Matrix */}
            {comparisonData.length > 1 && (
              <div className="mt-6">
                <h4 className="font-medium mb-3">Pattern Similarity Matrix</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="p-2"></th>
                        {comparisonData.map((user) => (
                          <th key={user.user_id} className="text-center p-2">{user.user_name}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {comparisonData.map((user1, i) => (
                        <tr key={user1.user_id} className="border-b">
                          <td className="p-2 font-medium">{user1.user_name}</td>
                          {similarityMatrix[i].map((similarity, j) => (
                            <td key={j} className="text-center p-2">
                              <div
                                className={`inline-block px-2 py-1 rounded text-xs ${
                                  similarity > 0.8
                                    ? 'bg-green-100 text-green-700'
                                    : similarity > 0.6
                                    ? 'bg-yellow-100 text-yellow-700'
                                    : 'bg-red-100 text-red-700'
                                }`}
                              >
                                {Math.round(similarity * 100)}%
                              </div>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default PatternComparison;
