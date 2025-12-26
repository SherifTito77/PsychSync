// Pattern Visualization Component
// Advanced visualizations for behavioral patterns and anomalies

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
  Cell,
  HeatmapChart,
  TreemapChart,
} from 'recharts';
import {
  Network,
  Activity,
  Clock,
  TrendingUp,
  AlertCircle,
  BarChart3,
  LineChart as LineChartIcon,
  PieChart as PieChartIcon,
} from 'lucide-react';

// Types for pattern visualization
interface PatternData {
  timestamp: string;
  value: number;
  category?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  baseline?: number;
  confidence?: number;
}

interface AnomalyPoint {
  timestamp: string;
  value: number;
  anomaly_score: number;
  type: string;
  description: string;
}

interface NetworkNode {
  id: string;
  label: string;
  x: number;
  y: number;
  size: number;
  color: string;
  type: 'user' | 'action' | 'pattern' | 'anomaly';
}

interface NetworkEdge {
  source: string;
  target: string;
  weight: number;
  type: 'sequence' | 'similarity' | 'correlation';
}

interface HeatmapData {
  x: string;
  y: string;
  value: number;
  intensity: number;
}

type VisualizationType = 'line' | 'area' | 'scatter' | 'heatmap' | 'network' | 'distribution';

interface PatternVisualizationProps {
  data: PatternData[];
  anomalies?: AnomalyPoint[];
  type?: VisualizationType;
  title?: string;
  description?: string;
  height?: number;
  interactive?: boolean;
  showBaseline?: boolean;
  timeRange?: { start: string; end: string };
  categories?: string[];
  className?: string;
}

const COLORS = {
  primary: '#3b82f6',
  secondary: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#8b5cf6',
  success: '#22c55e',
  anomaly: '#ef4444',
  baseline: '#94a3b8',
};

const SEVERITY_COLORS = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#f97316',
  critical: '#ef4444',
};

const PatternVisualization: React.FC<PatternVisualizationProps> = ({
  data,
  anomalies = [],
  type = 'line',
  title,
  description,
  height = 400,
  interactive = true,
  showBaseline = true,
  timeRange,
  categories = [],
  className
}) => {
  const [selectedVisualization, setSelectedVisualization] = useState<VisualizationType>(type);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [hoveredPoint, setHoveredPoint] = useState<any>(null);

  // Process data for visualization
  const processedData = useMemo(() => {
    let filteredData = data;

    // Filter by category if selected
    if (selectedCategory !== 'all' && selectedCategory !== '') {
      filteredData = data.filter(d => d.category === selectedCategory);
    }

    // Sort by timestamp
    return filteredData.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  }, [data, selectedCategory]);

  // Process anomalies for visualization
  const processedAnomalies = useMemo(() => {
    return anomalies.map(anomaly => ({
      ...anomaly,
      timestamp: new Date(anomaly.timestamp).getTime()
    }));
  }, [anomalies]);

  // Generate heatmap data
  const heatmapData = useMemo(() => {
    const hourValues = Array.from({ length: 24 }, (_, i) => i);
    const dayValues = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    return dayValues.map(day =>
      hourValues.map(hour => {
        // TODO(human): Calculate actual heatmap values from pattern data
        const value = Math.random() * 100;
        const intensity = value / 100;

        return {
          x: `${hour}:00`,
          y: day,
          value,
          intensity
        };
      })
    ).flat();
  }, []);

  // Generate network visualization data
  const networkData = useMemo(() => {
    const nodes: NetworkNode[] = [];
    const edges: NetworkEdge[] = [];

    // TODO(human): Generate actual network data from patterns
    // This is mock data for demonstration
    const actionNodes = [
      { id: 'login', label: 'Login', type: 'action' as const, x: 100, y: 100, size: 20, color: COLORS.primary },
      { id: 'dashboard', label: 'Dashboard', type: 'action' as const, x: 200, y: 150, size: 30, color: COLORS.primary },
      { id: 'reports', label: 'Reports', type: 'action' as const, x: 300, y: 100, size: 25, color: COLORS.primary },
      { id: 'export', label: 'Export', type: 'action' as const, x: 400, y: 200, size: 15, color: COLORS.primary },
    ];

    const patternNodes = [
      { id: 'pattern1', label: 'Morning Routine', type: 'pattern' as const, x: 150, y: 250, size: 35, color: COLORS.success },
      { id: 'pattern2', label: 'Report Generation', type: 'pattern' as const, x: 350, y: 50, size: 30, color: COLORS.success },
    ];

    nodes.push(...actionNodes, ...patternNodes);

    // Create edges based on sequence patterns
    edges.push(
      { source: 'login', target: 'dashboard', weight: 0.9, type: 'sequence' as const },
      { source: 'dashboard', target: 'reports', weight: 0.7, type: 'sequence' as const },
      { source: 'reports', target: 'export', weight: 0.4, type: 'sequence' as const },
      { source: 'pattern1', target: 'login', weight: 0.8, type: 'similarity' as const },
      { source: 'pattern1', target: 'dashboard', weight: 0.9, type: 'similarity' as const },
    );

    return { nodes, edges };
  }, []);

  // Custom tooltip for better data display
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium">{new Date(data.timestamp).toLocaleString()}</p>
          <p className="text-sm">Value: {data.value.toFixed(2)}</p>
          {data.category && <p className="text-sm">Category: {data.category}</p>}
          {data.confidence && <p className="text-sm">Confidence: {(data.confidence * 100).toFixed(1)}%</p>}
          {data.severity && (
            <Badge className={getSeverityBadgeClass(data.severity)}>
              {data.severity}
            </Badge>
          )}
        </div>
      );
    }
    return null;
  };

  // Get severity badge color
  const getSeverityBadgeClass = (severity: string) => {
    switch (severity) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Render different visualization types
  const renderVisualization = () => {
    switch (selectedVisualization) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={processedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              {showBaseline && processedData[0]?.baseline && (
                <ReferenceLine
                  y={processedData[0].baseline}
                  stroke={COLORS.baseline}
                  strokeDasharray="5 5"
                  label="Baseline"
                />
              )}
              <Line
                type="monotone"
                dataKey="value"
                stroke={COLORS.primary}
                strokeWidth={2}
                dot={interactive}
                activeDot={interactive ? { r: 8 } : false}
                name="Pattern Value"
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={processedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Area
                type="monotone"
                dataKey="value"
                stroke={COLORS.primary}
                fill={COLORS.primary}
                fillOpacity={0.3}
                name="Pattern Value"
              />
              {categories.length > 1 && (
                <Area
                  type="monotone"
                  dataKey="confidence"
                  stroke={COLORS.secondary}
                  fill={COLORS.secondary}
                  fillOpacity={0.2}
                  name="Confidence"
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <ScatterChart data={processedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                type="number"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis dataKey="value" />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Scatter
                name="Pattern Data"
                data={processedData}
                fill={COLORS.primary}
              />
              {processedAnomalies.length > 0 && (
                <Scatter
                  name="Anomalies"
                  data={processedAnomalies}
                  fill={COLORS.anomaly}
                  shape="star"
                />
              )}
            </ScatterChart>
          </ResponsiveContainer>
        );

      case 'heatmap':
        return (
          <ResponsiveContainer width="100%" height={height}>
            {/* TODO(human): Implement actual heatmap visualization
                This requires a custom heatmap component or additional library */}
            <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg border">
              <div className="text-center">
                <div className="grid grid-cols-7 gap-1 mb-4">
                  {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, i) => (
                    <div key={i} className="text-xs font-medium">{day}</div>
                  ))}
                </div>
                <div className="text-sm text-gray-600">
                  Heatmap visualization showing activity patterns by hour and day
                </div>
              </div>
            </div>
          </ResponsiveContainer>
        );

      case 'network':
        return (
          <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg border">
            <div className="text-center">
              <Network className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p className="text-sm text-gray-600">
                Network visualization showing pattern relationships
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Nodes: {networkData.nodes.length} | Edges: {networkData.edges.length}
              </p>
            </div>
          </div>
        );

      case 'distribution':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={processedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="value" fill={COLORS.primary} name="Pattern Value">
                {processedData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.severity ? SEVERITY_COLORS[entry.severity] : COLORS.primary}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  const visualizationTypes = [
    { value: 'line', label: 'Line Chart', icon: LineChartIcon },
    { value: 'area', label: 'Area Chart', icon: BarChart3 },
    { value: 'scatter', label: 'Scatter Plot', icon: Activity },
    { value: 'heatmap', label: 'Heatmap', icon: BarChart3 },
    { value: 'network', label: 'Network', icon: Network },
    { value: 'distribution', label: 'Distribution', icon: PieChartIcon },
  ];

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            {title && <CardTitle>{title}</CardTitle>}
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          <div className="flex items-center space-x-2">
            {/* Category Filter */}
            {categories.length > 0 && (
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map((category) => (
                    <SelectItem key={category} value={category}>
                      {category}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {/* Visualization Type Selector */}
            <Select value={selectedVisualization} onValueChange={(value: any) => setSelectedVisualization(value)}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {visualizationTypes.map((vizType) => (
                  <SelectItem key={vizType.value} value={vizType.value}>
                    <div className="flex items-center">
                      <vizType.icon className="h-4 w-4 mr-2" />
                      {vizType.label}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Statistics Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{processedData.length}</div>
              <div className="text-xs text-gray-600">Data Points</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {processedData.length > 0 ? Math.max(...processedData.map(d => d.value)).toFixed(1) : '0'}
              </div>
              <div className="text-xs text-gray-600">Max Value</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{processedAnomalies.length}</div>
              <div className="text-xs text-gray-600">Anomalies</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {processedData.length > 0 ? (processedData.reduce((sum, d) => sum + d.value, 0) / processedData.length).toFixed(1) : '0'}
              </div>
              <div className="text-xs text-gray-600">Average</div>
            </div>
          </div>

          {/* Main Visualization */}
          {processedData.length > 0 ? (
            renderVisualization()
          ) : (
            <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border">
              <div className="text-center">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-sm text-gray-600">No pattern data available</p>
              </div>
            </div>
          )}

          {/* Anomaly Indicators */}
          {processedAnomalies.length > 0 && (
            <div className="border-t pt-4">
              <h4 className="font-medium mb-2 flex items-center">
                <AlertCircle className="h-4 w-4 mr-2" />
                Recent Anomalies ({processedAnomalies.length})
              </h4>
              <div className="space-y-2">
                {processedAnomalies.slice(0, 3).map((anomaly, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-red-50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <Badge className={getSeverityBadgeClass(anomaly.severity)}>
                        {anomaly.severity}
                      </Badge>
                      <span className="text-sm">{anomaly.description}</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(anomaly.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default PatternVisualization;