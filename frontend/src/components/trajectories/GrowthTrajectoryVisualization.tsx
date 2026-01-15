/**
 * Growth Trajectory Visualization
 *
 * Advanced visualization component for displaying individual and team growth trajectories
 * with interactive features, milestone tracking, and prediction confidence bands.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Progress from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  ScatterChart,
  Scatter,
  ReferenceLine,
  ReferenceArea,
  ComposedChart,
  Bar,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Target,
  Calendar,
  Users,
  Brain,
  Zap,
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity,
  BarChart3,
  PieChart,
  Settings,
  Download,
  Play,
  Pause,
} from 'lucide-react';

// Types
interface TrajectoryPoint {
  date: string;
  value: number;
  predicted?: boolean;
  confidenceInterval?: [number, number];
  growthRate?: number;
  milestone?: string;
}

interface Milestone {
  id: string;
  name: string;
  targetValue: number;
  currentValue: number;
  achievementDate?: string;
  probability: number;
  status: 'pending' | 'in_progress' | 'achieved' | 'delayed';
  priority: 'low' | 'medium' | 'high' | 'critical';
}

interface PredictionData {
  predictionDate: string;
  predictedValue: number;
  confidenceInterval: [number, number];
  uncertaintyLevel: 'very_low' | 'low' | 'moderate' | 'high' | 'very_high';
  method: string;
  featureImportance: Record<string, number>;
}

interface GrowthTrajectoryData {
  id: string;
  userId: string;
  competencyDomain: string;
  modelType: string;
  accuracy: number;
  growthStage: string;
  growthVelocity: number;
  asymptoticPotential?: number;
  historicalData: TrajectoryPoint[];
  predictions: PredictionData[];
  milestones: Milestone[];
  benchmarkComparison?: {
    individual: number;
    team: number;
    organization: number;
    industry: number;
  };
}

interface GrowthTrajectoryVisualizationProps {
  trajectoryData: GrowthTrajectoryData;
  onMilestoneClick?: (milestone: Milestone) => void;
  onInterventionSuggest?: (date: string, value: number) => void;
  showComparison?: boolean;
  interactiveMode?: boolean;
}

const GrowthTrajectoryVisualization: React.FC<GrowthTrajectoryVisualizationProps> = ({
  trajectoryData,
  onMilestoneClick,
  onInterventionSuggest,
  showComparison = true,
  interactiveMode = true,
}) => {
  const [selectedTab, setSelectedTab] = useState('trajectory');
  const [timeRange, setTimeRange] = useState('12m'); // 3m, 6m, 12m, 24m
  const [showConfidence, setShowConfidence] = useState(true);
  const [animationPlaying, setAnimationPlaying] = useState(false);
  const [selectedMilestone, setSelectedMilestone] = useState<string | null>(null);

  // Combine historical and prediction data
  const combinedData = useMemo(() => {
    const historical = trajectoryData.historicalData.map(point => ({
      ...point,
      predicted: false,
    }));

    const predictions = trajectoryData.predictions.map(pred => ({
      date: pred.predictionDate,
      value: pred.predictedValue,
      predicted: true,
      confidenceInterval: pred.confidenceInterval,
      growthRate: undefined,
    }));

    return [...historical, ...predictions].sort((a, b) =>
      new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  }, [trajectoryData]);

  // Filter data based on time range
  const filteredData = useMemo(() => {
    const now = new Date();
    const monthsAgo = parseInt(timeRange.replace('m', ''));
    const cutoffDate = new Date(now.getFullYear(), now.getMonth() - monthsAgo, now.getDate());

    return combinedData.filter(point =>
      new Date(point.date) >= cutoffDate
    );
  }, [combinedData, timeRange]);

  // Prepare data for different chart types
  const trajectoryChartData = useMemo(() => {
    return filteredData.map(point => ({
      date: point.date,
      actual: point.predicted ? null : point.value,
      predicted: point.predicted ? point.value : null,
      confidenceLower: point.confidenceInterval?.[0],
      confidenceUpper: point.confidenceInterval?.[1],
    }));
  }, [filteredData]);

  const velocityData = useMemo(() => {
    const velocityPoints = [];
    for (let i = 1; i < filteredData.length; i++) {
      const prev = filteredData[i - 1];
      const curr = filteredData[i];
      const daysDiff = (new Date(curr.date).getTime() - new Date(prev.date).getTime()) / (1000 * 60 * 60 * 24);
      const valueDiff = curr.value - prev.value;
      const velocity = daysDiff > 0 ? valueDiff / daysDiff * 30 : 0; // Monthly velocity

      velocityPoints.push({
        date: curr.date,
        velocity: velocity,
        acceleration: i > 1 ? velocity - velocityPoints[i - 2].velocity : 0,
      });
    }
    return velocityPoints;
  }, [filteredData]);

  const milestoneData = useMemo(() => {
    return trajectoryData.milestones.map(milestone => ({
      name: milestone.name,
      target: milestone.targetValue,
      current: milestone.currentValue,
      progress: (milestone.currentValue / milestone.targetValue) * 100,
      status: milestone.status,
      probability: milestone.probability,
      priority: milestone.priority,
    }));
  }, [trajectoryData.milestones]);

  const benchmarkData = useMemo(() => {
    if (!trajectoryData.benchmarkComparison) return [];

    return [
      { metric: 'Current Performance', individual: trajectoryData.benchmarkComparison.individual },
      { metric: 'Team Average', individual: trajectoryData.benchmarkComparison.team },
      { metric: 'Organization Average', individual: trajectoryData.benchmarkComparison.organization },
      { metric: 'Industry Average', individual: trajectoryData.benchmarkComparison.industry },
    ];
  }, [trajectoryData.benchmarkComparison]);

  // Helper functions
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getMilestoneColor = (status: string) => {
    switch (status) {
      case 'achieved': return '#10b981'; // green
      case 'in_progress': return '#3b82f6'; // blue
      case 'delayed': return '#f59e0b'; // yellow
      case 'pending': return '#94a3b8'; // gray
      default: return '#94a3b8';
    }
  };

  const getUncertaintyColor = (level: string) => {
    switch (level) {
      case 'very_low': return '#10b981';
      case 'low': return '#22c55e';
      case 'moderate': return '#f59e0b';
      case 'high': return '#f97316';
      case 'very_high': return '#ef4444';
      default: return '#94a3b8';
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border rounded-lg shadow-lg">
          <p className="font-semibold">{formatDate(label)}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.value?.toFixed(2)}
            </p>
          ))}
          {data.confidenceInterval && (
            <p className="text-sm text-gray-600">
              95% CI: [{data.confidenceInterval[0]?.toFixed(2)}, {data.confidenceInterval[1]?.toFixed(2)}]
            </p>
          )}
          {data.milestone && (
            <p className="text-sm font-medium text-blue-600">
              🎯 {data.milestone}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  const renderTrajectoryChart = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Growth Trajectory - {trajectoryData.competencyDomain}
        </CardTitle>
        <CardDescription>
          Historical performance with future predictions and confidence intervals
        </CardDescription>
        <div className="flex items-center gap-4 mt-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span className="text-sm">Historical</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm">Predicted</span>
          </div>
          {showConfidence && (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-200 rounded-full"></div>
              <span className="text-sm">95% Confidence</span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={trajectoryChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              interval="preserveStartEnd"
            />
            <YAxis />
            <Tooltip content={<CustomTooltip />} />
            <Legend />

            {/* Confidence interval area */}
            {showConfidence && (
              <Area
                type="monotone"
                dataKey="confidenceUpper"
                stroke="transparent"
                fill="#10b981"
                fillOpacity={0.1}
              />
            )}

            {/* Actual values */}
            <Line
              type="monotone"
              dataKey="actual"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 3 }}
              connectNulls={false}
            />

            {/* Predicted values */}
            <Line
              type="monotone"
              dataKey="predicted"
              stroke="#10b981"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              connectNulls={false}
            />

            {/* Milestone markers */}
            {trajectoryData.milestones.map((milestone, index) => (
              <ReferenceLine
                key={milestone.id}
                y={milestone.targetValue}
                stroke={getMilestoneColor(milestone.status)}
                strokeWidth={2}
                strokeDasharray="3 3"
                label={{
                  value: milestone.name,
                  position: 'right',
                  style: { fontSize: '12px' }
                }}
              />
            ))}

            {/* Asymptotic potential line */}
            {trajectoryData.asymptoticPotential && (
              <ReferenceLine
                y={trajectoryData.asymptoticPotential}
                stroke="#ef4444"
                strokeWidth={2}
                strokeDasharray="8 4"
                label={{
                  value: "Potential Ceiling",
                  position: 'right',
                  style: { fontSize: '12px' }
                }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>

        {/* Trajectory statistics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {trajectoryData.growthVelocity.toFixed(4)}
            </div>
            <p className="text-sm text-gray-600">Growth Velocity</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {(trajectoryData.accuracy * 100).toFixed(1)}%
            </div>
            <p className="text-sm text-gray-600">Model Accuracy</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {trajectoryData.growthStage}
            </div>
            <p className="text-sm text-gray-600">Growth Stage</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {trajectoryData.modelType}
            </div>
            <p className="text-sm text-gray-600">Model Type</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderVelocityChart = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="h-5 w-5" />
          Growth Velocity & Acceleration
        </CardTitle>
        <CardDescription>
          Monthly growth rate and acceleration patterns over time
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={velocityData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              interval="preserveStartEnd"
            />
            <YAxis />
            <Tooltip />
            <Legend />

            {/* Velocity bars */}
            <Bar
              dataKey="velocity"
              fill="#3b82f6"
              name="Growth Velocity"
            />

            {/* Acceleration line */}
            <Line
              type="monotone"
              dataKey="acceleration"
              stroke="#ef4444"
              strokeWidth={2}
              name="Acceleration"
              dot={{ r: 3 }}
            />

            {/* Zero reference line */}
            <ReferenceLine y={0} stroke="#94a3b8" strokeWidth={1} />
          </ComposedChart>
        </ResponsiveContainer>

        {/* Velocity insights */}
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-semibold text-blue-800 mb-2">Velocity Insights</h4>
          <p className="text-sm text-blue-700">
            Current velocity: {velocityData.length > 0 ? velocityData[velocityData.length - 1].velocity.toFixed(4) : 'N/A'}
            {velocityData.length > 1 && (
              <>
                {' '}•
                {' '}Trend: {velocityData[velocityData.length - 1].velocity > velocityData[velocityData.length - 2].velocity ? '📈 Increasing' : '📉 Decreasing'}
                {' '}•
                {' '}Acceleration: {velocityData[velocityData.length - 1].acceleration.toFixed(4)}
              </>
            )}
          </p>
        </div>
      </CardContent>
    </Card>
  );

  const renderMilestones = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5" />
          Growth Milestones
        </CardTitle>
        <CardDescription>
          Progress tracking towards key development milestones
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {milestoneData.map((milestone, index) => (
            <div
              key={index}
              className={`p-4 border rounded-lg cursor-pointer transition-colors hover:bg-gray-50 ${
                selectedMilestone === milestone.name ? 'ring-2 ring-blue-500' : ''
              }`}
              onClick={() => {
                setSelectedMilestone(milestone.name);
                onMilestoneClick?.({
                  id: trajectoryData.milestones[index].id,
                  name: milestone.name,
                  targetValue: milestone.target,
                  currentValue: milestone.current,
                  probability: milestone.probability,
                  status: milestone.status,
                  priority: milestone.priority,
                } as Milestone);
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold">{milestone.name}</h3>
                <Badge
                  variant={
                    milestone.status === 'achieved' ? 'default' :
                    milestone.status === 'in_progress' ? 'secondary' :
                    milestone.status === 'delayed' ? 'destructive' : 'outline'
                  }
                >
                  {milestone.status}
                </Badge>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Progress</span>
                  <span>{milestone.current.toFixed(1)} / {milestone.target.toFixed(1)}</span>
                </div>
                <Progress value={milestone.progress} className="h-2" />
              </div>

              <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
                <div>
                  <span className="text-gray-600">Achievement Probability: </span>
                  <span className="font-medium">{(milestone.probability * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-gray-600">Priority: </span>
                  <Badge variant={milestone.priority === 'critical' ? 'destructive' : 'secondary'}>
                    {milestone.priority}
                  </Badge>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Milestone summary */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {milestoneData.filter(m => m.status === 'achieved').length}
            </div>
            <p className="text-sm text-gray-600">Achieved</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {milestoneData.filter(m => m.status === 'in_progress').length}
            </div>
            <p className="text-sm text-gray-600">In Progress</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">
              {milestoneData.filter(m => m.status === 'pending').length}
            </div>
            <p className="text-sm text-gray-600">Pending</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {milestoneData.filter(m => m.status === 'delayed').length}
            </div>
            <p className="text-sm text-gray-600">Delayed</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderComparison = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Performance Comparison
        </CardTitle>
        <CardDescription>
          Compare individual performance against team, organization, and industry benchmarks
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={benchmarkData} layout="horizontal">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="metric" type="category" width={120} />
            <Tooltip />
            <Bar dataKey="individual" fill="#3b82f6" name="Performance Score" />
          </BarChart>
        </ResponsiveContainer>

        {/* Benchmark insights */}
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="p-3 bg-blue-50 rounded-lg">
            <h4 className="font-semibold text-blue-800">Percentile Ranking</h4>
            <p className="text-sm text-blue-700 mt-1">
              Individual performs in the
              {trajectoryData.benchmarkComparison ?
                ` top ${(1 - trajectoryData.benchmarkComparison.individual / 5) * 100}%` :
                ' N/A'}
              {' '}compared to industry standards
            </p>
          </div>
          <div className="p-3 bg-green-50 rounded-lg">
            <h4 className="font-semibold text-green-800">Growth Rate Comparison</h4>
            <p className="text-sm text-green-700 mt-1">
              Growth velocity is
              {trajectoryData.growthVelocity > 0.01 ? ' above ' : ' below '}
              average for this competency domain
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderPredictions = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          Prediction Analysis
        </CardTitle>
        <CardDescription>
          Detailed breakdown of prediction methods and uncertainty levels
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {trajectoryData.predictions.slice(0, 10).map((prediction, index) => (
            <div key={index} className="p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold">{formatDate(prediction.predictionDate)}</h4>
                <Badge
                  style={{ backgroundColor: getUncertaintyColor(prediction.uncertaintyLevel) }}
                  className="text-white"
                >
                  {prediction.uncertaintyLevel.replace('_', ' ')}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Predicted Value: </span>
                  <span className="font-medium">{prediction.predictedValue.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-gray-600">Method: </span>
                  <span className="font-medium">{prediction.method}</span>
                </div>
              </div>

              <div className="mt-2">
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span>Confidence Interval</span>
                  <span>
                    [{prediction.confidenceInterval[0]?.toFixed(2)}, {prediction.confidenceInterval[1]?.toFixed(2)}]
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{
                      width: `${Math.max(0, Math.min(100, (prediction.predictedValue / 5) * 100))}%`
                    }}
                  ></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold">Growth Trajectory Analysis</h1>
          <p className="text-muted-foreground">
            {trajectoryData.competencyDomain} • {trajectoryData.growthStage} Stage
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Time Range:</label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-1 border rounded-md"
            >
              <option value="3m">3 Months</option>
              <option value="6m">6 Months</option>
              <option value="12m">12 Months</option>
              <option value="24m">24 Months</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="confidence"
              checked={showConfidence}
              onChange={(e) => setShowConfidence(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="confidence" className="text-sm font-medium">
              Show Confidence
            </label>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setAnimationPlaying(!animationPlaying)}
          >
            {animationPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>

          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="trajectory">Trajectory</TabsTrigger>
          <TabsTrigger value="velocity">Velocity</TabsTrigger>
          <TabsTrigger value="milestones">Milestones</TabsTrigger>
          <TabsTrigger value="comparison">Comparison</TabsTrigger>
          <TabsTrigger value="predictions">Predictions</TabsTrigger>
        </TabsList>

        <TabsContent value="trajectory" className="space-y-4">
          {renderTrajectoryChart()}
        </TabsContent>

        <TabsContent value="velocity" className="space-y-4">
          {renderVelocityChart()}
        </TabsContent>

        <TabsContent value="milestones" className="space-y-4">
          {renderMilestones()}
        </TabsContent>

        <TabsContent value="comparison" className="space-y-4">
          {showComparison && renderComparison()}
        </TabsContent>

        <TabsContent value="predictions" className="space-y-4">
          {renderPredictions()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default GrowthTrajectoryVisualization;
