// Change Point Detection Visualization Component
// Advanced visualization for detecting and displaying behavioral change points

import React, { useState, useMemo, useCallback } from 'react';
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
  ComposedChart,
  Bar,
} from 'recharts';
import {
  Activity,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Zap,
  Target,
  Eye,
  Filter,
  Settings,
  Info,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

// Types for change point detection
interface ChangePoint {
  id: string;
  timestamp: string;
  metric_name: string;
  algorithm: string;
  change_type: string;
  severity: 'minor' | 'moderate' | 'significant' | 'critical';
  baseline_value: number;
  current_value: number;
  change_magnitude: number;
  confidence: number;
  statistical_significance: number;
  description: string;
  recommended_actions: string[];
  false_positive_probability: number;
}

interface DetectionResult {
  metric_name: string;
  time_series_data: Array<{ timestamp: string; value: number }>;
  change_points: ChangePoint[];
  algorithm_performance: {
    algorithm: string;
    true_positives: number;
    false_positives: number;
    precision: number;
    recall: number;
    f1_score: number;
  }[];
  baseline_statistics: {
    mean: number;
    std: number;
    min: number;
    max: number;
  };
  post_change_statistics: {
    mean: number;
    std: number;
    min: number;
    max: number;
  };
}

interface DetectionAlgorithm {
  name: string;
  description: string;
  parameters: Record<string, any>;
  is_active: boolean;
}

interface ChangePointDetectionProps {
  userId?: string;
  timeRange?: string;
  metrics?: Array<{ name: string; label: string }>;
  className?: string;
}

const SEVERITY_COLORS = {
  minor: '#22c55e',
  moderate: '#f59e0b',
  significant: '#f97316',
  critical: '#ef4444',
};

const ALGORITHM_COLORS = {
  'cusum': '#3b82f6',
  'ewma': '#10b981',
  'page_hinkley': '#f59e0b',
  'bayesian': '#8b5cf6',
  'change_finder': '#ef4444',
  'ensemble': '#06b6d4',
};

const ChangePointDetection: React.FC<ChangePointDetectionProps> = ({
  userId,
  timeRange = '90d',
  metrics = [],
  className
}) => {
  const [selectedMetric, setSelectedMetric] = useState<string>('user_engagement');
  const [selectedAlgorithms, setSelectedAlgorithms] = useState<string[]>(['cusum', 'ewma', 'ensemble']);
  const [sensitivityLevel, setSensitivityLevel] = useState<string>('medium');
  const [showStatisticalTests, setShowStatisticalTests] = useState(true);
  const [showConfidenceBands, setShowConfidenceBands] = useState(true);
  const [expandedChanges, setExpandedChanges] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'overview' | 'detailed' | 'comparison'>('overview');

  // Mock detection results
  const mockDetectionResults: DetectionResult[] = useMemo(() => {
    const results: DetectionResult[] = [];
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 90);

    // Generate data for each metric
    const metricsToGenerate = metrics.length > 0 ? metrics : [
      { name: 'user_engagement', label: 'User Engagement' },
      { name: 'session_duration', label: 'Session Duration' },
      { name: 'task_completion', label: 'Task Completion' }
    ];

    metricsToGenerate.forEach((metric) => {
      // Generate time series data
      const timeSeriesData = [];
      let currentValue = 50;

      for (let i = 0; i < 90; i++) {
        const date = new Date(startDate);
        date.setDate(date.getDate() + i);

        // Add trend and noise
        currentValue += (Math.random() - 0.48) * 5; // Slight upward trend with noise
        currentValue = Math.max(10, Math.min(100, currentValue)); // Keep within bounds

        // Add some sudden changes
        if ((i === 30 || i === 60) && Math.random() > 0.3) {
          currentValue += (Math.random() - 0.5) * 30;
        }

        timeSeriesData.push({
          timestamp: date.toISOString(),
          value: currentValue
        });
      }

      // Generate change points
      const changePoints: ChangePoint[] = [];
      const numChanges = 2 + Math.floor(Math.random() * 3);

      for (let i = 0; i < numChanges; i++) {
        const changeDay = 15 + Math.floor(Math.random() * 60);
        const changeDate = new Date(startDate);
        changeDate.setDate(changeDate.getDate() + changeDay);

        const severities: Array<'minor' | 'moderate' | 'significant' | 'critical'> =
          ['minor', 'moderate', 'significant', 'critical'];
        const severity = severities[Math.floor(Math.random() * severities.length)];

        const algorithms = ['cusum', 'ewma', 'page_hinkley', 'ensemble'];
        const algorithm = algorithms[Math.floor(Math.random() * algorithms.length)];

        const changePoint: ChangePoint = {
          id: `change_${metric.name}_${i}`,
          timestamp: changeDate.toISOString(),
          metric_name: metric.name,
          algorithm,
          change_type: 'level_shift',
          severity,
          baseline_value: 45 + Math.random() * 10,
          current_value: 55 + Math.random() * 20,
          change_magnitude: 10 + Math.random() * 25,
          confidence: 0.7 + Math.random() * 0.25,
          statistical_significance: Math.random() * 0.1,
          description: `Significant ${severity} change detected in ${metric.label}`,
          recommended_actions: [
            'Investigate recent behavioral changes',
            'Review system modifications',
            'Monitor for continued changes'
          ],
          false_positive_probability: Math.random() * 0.2
        };
        changePoints.push(changePoint);
      }

      // Calculate statistics
      const values = timeSeriesData.map(d => d.value);
      const baselineStatistics = {
        mean: np.mean(values.slice(0, 30)),
        std: np.std(values.slice(0, 30)),
        min: Math.min(...values.slice(0, 30)),
        max: Math.max(...values.slice(0, 30))
      };

      const postChangeStatistics = {
        mean: np.mean(values.slice(-30)),
        std: np.std(values.slice(-30)),
        min: Math.min(...values.slice(-30)),
        max: Math.max(...values.slice(-30))
      };

      // Mock algorithm performance
      const algorithmPerformance = selectedAlgorithms.map(algo => ({
        algorithm: algo,
        true_positives: Math.floor(Math.random() * 5) + 1,
        false_positives: Math.floor(Math.random() * 2),
        precision: 0.7 + Math.random() * 0.25,
        recall: 0.6 + Math.random() * 0.3,
        f1_score: 0.65 + Math.random() * 0.25
      }));

      results.push({
        metric_name: metric.name,
        time_series_data,
        change_points: changePoints.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()),
        algorithm_performance,
        baseline_statistics,
        post_change_statistics
      });
    });

    return results;
  }, [metrics, selectedAlgorithms]);

  const currentResult = mockDetectionResults.find(r => r.metric_name === selectedMetric) || mockDetectionResults[0];

  const toggleChangeExpansion = (changeId: string) => {
    setExpandedChanges(prev => {
      const newSet = new Set(prev);
      if (newSet.has(changeId)) {
        newSet.delete(changeId);
      } else {
        newSet.add(changeId);
      }
      return newSet;
    });
  };

  const getSeverityColor = (severity: string) => {
    return SEVERITY_COLORS[severity as keyof typeof SEVERITY_COLORS] || '#94a3b8';
  };

  const getAlgorithmColor = (algorithm: string) => {
    return ALGORITHM_COLORS[algorithm as keyof typeof ALGORITHM_COLORS] || '#94a3b8';
  };

  // Calculate performance metrics
  const overallPerformance = useMemo(() => {
    if (!currentResult || currentResult.algorithm_performance.length === 0) {
      return {
        avg_precision: 0,
        avg_recall: 0,
        avg_f1_score: 0,
        total_changes: 0,
        critical_changes: 0
      };
    }

    const performance = currentResult.algorithm_performance;
    return {
      avg_precision: performance.reduce((sum, p) => sum + p.precision, 0) / performance.length,
      avg_recall: performance.reduce((sum, p) => sum + p.recall, 0) / performance.length,
      avg_f1_score: performance.reduce((sum, p) => sum + p.f1_score, 0) / performance.length,
      total_changes: currentResult.change_points.length,
      critical_changes: currentResult.change_points.filter(cp => cp.severity === 'critical').length
    };
  }, [currentResult]);

  // Custom tooltip for change points
  const ChangePointTooltip = ({ active, payload }: any) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium">{new Date(data.timestamp).toLocaleString()}</p>
          <p className="text-sm text-gray-600">Value: {data.value.toFixed(2)}</p>
          {data.changePoint && (
            <div className="mt-2 p-2 bg-red-50 rounded">
              <p className="text-xs font-medium text-red-800">Change Point</p>
              <p className="text-xs text-red-700">Algorithm: {data.changePoint.algorithm}</p>
              <p className="text-xs text-red-700">Severity: {data.changePoint.severity}</p>
              <p className="text-xs text-red-700">Confidence: {(data.changePoint.confidence * 100).toFixed(1)}%</p>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  // Process data for visualization with change points highlighted
  const processedData = useMemo(() => {
    if (!currentResult) return [];

    return currentResult.time_series_data.map((point, index) => {
      const changePoint = currentResult.change_points.find(cp =>
        new Date(cp.timestamp).toDateString() === new Date(point.timestamp).toDateString()
      );

      return {
        ...point,
        changePoint,
        value: point.value,
        baseline: currentResult.baseline_statistics.mean,
        upperBand: currentResult.baseline_statistics.mean + 2 * currentResult.baseline_statistics.std,
        lowerBand: currentResult.baseline_statistics.mean - 2 * currentResult.baseline_statistics.std
      };
    });
  }, [currentResult]);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header and Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center">
                <Target className="h-5 w-5 mr-2" />
                Change Point Detection
              </CardTitle>
              <CardDescription>
                Detect and analyze significant behavioral changes over time
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Configure
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

            {/* Algorithm Selection */}
            <div>
              <label className="text-sm font-medium mb-2 block">Algorithms</label>
              <div className="space-y-2">
                {['cusum', 'ewma', 'page_hinkley', 'bayesian', 'change_finder', 'ensemble'].map((algo) => (
                  <div key={algo} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={algo}
                      checked={selectedAlgorithms.includes(algo)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedAlgorithms(prev => [...prev, algo]);
                        } else {
                          setSelectedAlgorithms(prev => prev.filter(a => a !== algo));
                        }
                      }}
                      className="rounded"
                    />
                    <label htmlFor={algo} className="text-sm capitalize">
                      {algo.replace('_', ' ')}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* Sensitivity Level */}
            <div>
              <label className="text-sm font-medium mb-2 block">Sensitivity</label>
              <Select value={sensitivityLevel} onValueChange={setSensitivityLevel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="very_high">Very High</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Display Options */}
            <div>
              <label className="text-sm font-medium mb-2 block">Display Options</label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="showStatisticalTests"
                    checked={showStatisticalTests}
                    onChange={(e) => setShowStatisticalTests(e.target.checked)}
                    className="rounded"
                  />
                  <label htmlFor="showStatisticalTests" className="text-sm">
                    Statistical Tests
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="showConfidenceBands"
                    checked={showConfidenceBands}
                    onChange={(e) => setShowConfidenceBands(e.target.checked)}
                    className="rounded"
                  />
                  <label htmlFor="showConfidenceBands" className="text-sm">
                    Confidence Bands
                  </label>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Detection Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {overallPerformance.avg_precision.toFixed(3)}
              </div>
              <div className="text-xs text-gray-600">Avg Precision</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {overallPerformance.avg_recall.toFixed(3)}
              </div>
              <div className="text-xs text-gray-600">Avg Recall</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {overallPerformance.avg_f1_score.toFixed(3)}
              </div>
              <div className="text-xs text-gray-600">Avg F1 Score</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {overallPerformance.total_changes}
              </div>
              <div className="text-xs text-gray-600">Total Changes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {overallPerformance.critical_changes}
              </div>
              <div className="text-xs text-gray-600">Critical Changes</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>
            {selectedMetric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} - Change Point Analysis
          </CardTitle>
          <CardDescription>
            {selectedAlgorithms.length} algorithms • {currentResult?.change_points.length || 0} change points detected
          </CardDescription>
        </CardHeader>
        <CardContent>
          {processedData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart data={processedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis />
                <Tooltip content={<ChangePointTooltip />} />
                <Legend />

                {/* Confidence bands */}
                {showConfidenceBands && (
                  <>
                    <Area
                      type="monotone"
                      dataKey="upperBand"
                      stroke="none"
                      fill="#fbbf24"
                      fillOpacity={0.2}
                      name="Upper Confidence Band"
                    />
                    <Area
                      type="monotone"
                      dataKey="lowerBand"
                      stroke="none"
                      fill="#fbbf24"
                      fillOpacity={0.2}
                      name="Lower Confidence Band"
                    />
                  </>
                )}

                {/* Baseline reference line */}
                <ReferenceLine
                  y={currentResult?.baseline_statistics.mean}
                  stroke="#94a3b8"
                  strokeDasharray="5 5"
                  label="Baseline"
                />

                {/* Time series line */}
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  name="Metric Value"
                />

                {/* Change point indicators */}
                {currentResult?.change_points.map((changePoint) => (
                  <ReferenceLine
                    key={changePoint.id}
                    x={changePoint.timestamp}
                    stroke={getSeverityColor(changePoint.severity)}
                    strokeWidth={2}
                    strokeDasharray="3 3"
                    label={`${changePoint.algorithm} - ${changePoint.severity}`}
                  />
                ))}

                {/* Change point markers */}
                <Scatter
                  data={processedData.filter(d => d.changePoint)}
                  fill="red"
                  shape="star"
                />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border">
              <div className="text-center">
                <Activity className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-sm text-gray-600">No data available for analysis</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Change Points Details */}
      {currentResult?.change_points.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              Detected Change Points ({currentResult.change_points.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {currentResult.change_points.map((changePoint) => (
                <div
                  key={changePoint.id}
                  className="border rounded-lg p-4 transition-all hover:shadow-md"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h4 className="font-medium">{changePoint.description}</h4>
                        <Badge className={getSeverityColor(changePoint.severity)}>
                          {changePoint.severity}
                        </Badge>
                        <Badge variant="outline" className={getAlgorithmColor(changePoint.algorithm)}>
                          {changePoint.algorithm.replace('_', ' ')}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">
                        {new Date(changePoint.timestamp).toLocaleString()}
                      </p>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Baseline:</span>
                          <span className="ml-1 font-medium">{changePoint.baseline_value.toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Current:</span>
                          <span className="ml-1 font-medium">{changePoint.current_value.toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Magnitude:</span>
                          <span className="ml-1 font-medium">{changePoint.change_magnitude.toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Confidence:</span>
                          <span className="ml-1 font-medium">{(changePoint.confidence * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleChangeExpansion(changePoint.id)}
                      >
                        {expandedChanges.has(changePoint.id) ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>

                  {expandedChanges.has(changePoint.id) && (
                    <div className="mt-4 pt-4 border-t space-y-4">
                      <div>
                        <h5 className="font-medium mb-2">Statistical Significance</h5>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600">P-value:</span>
                            <span className="ml-1">{changePoint.statistical_significance.toFixed(4)}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">False Positive Risk:</span>
                            <span className="ml-1">{(changePoint.false_positive_probability * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>

                      {changePoint.recommended_actions.length > 0 && (
                        <div>
                          <h5 className="font-medium mb-2">Recommended Actions</h5>
                          <ul className="list-disc list-inside space-y-1">
                            {changePoint.recommended_actions.map((action, index) => (
                              <li key={index} className="text-sm text-gray-700">{action}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Algorithm Performance Comparison */}
      {currentResult?.algorithm_performance.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Algorithm Performance Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Algorithm</th>
                    <th className="text-center p-2">Precision</th>
                    <th className="text-center p-2">Recall</th>
                    <th className="text-center p-2">F1 Score</th>
                    <th className="text-center p-2">True Positives</th>
                    <th className="text-center p-2">False Positives</th>
                  </tr>
                </thead>
                <tbody>
                  {currentResult.algorithm_performance.map((perf) => (
                    <tr key={perf.algorithm} className="border-b">
                      <td className="p-2 font-medium capitalize">
                        <div className="flex items-center space-x-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: getAlgorithmColor(perf.algorithm) }}
                          />
                          {perf.algorithm.replace('_', ' ')}
                        </div>
                      </td>
                      <td className="text-center p-2">{perf.precision.toFixed(3)}</td>
                      <td className="text-center p-2">{perf.recall.toFixed(3)}</td>
                      <td className="text-center p-2 font-medium">{perf.f1_score.toFixed(3)}</td>
                      <td className="text-center p-2">{perf.true_positives}</td>
                      <td className="text-center p-2">{perf.false_positives}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Utility function for numpy operations (in real app, would use actual numpy)
const np = {
  mean: (arr: number[]) => arr.reduce((sum, val) => sum + val, 0) / arr.length,
  std: (arr: number[]) => {
    const mean = np.mean(arr);
    const variance = arr.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / arr.length;
    return Math.sqrt(variance);
  }
};

export default ChangePointDetection;
