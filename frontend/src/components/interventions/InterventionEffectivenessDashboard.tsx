/**
 * Intervention Effectiveness Dashboard
 *
 * Comprehensive dashboard for visualizing and analyzing intervention effectiveness
 * with pre/post comparisons, statistical significance, and impact metrics.
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
import { Progress } from '@/components/ui/progress';
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
  ScatterChart,
  Scatter,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  BoxPlot,
  Box,
  ViolinPlot,
  Violin,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Activity,
  Users,
  Target,
  AlertCircle,
  CheckCircle,
  Info,
  Download,
  Filter,
  Calendar,
  DollarSign,
} from 'lucide-react';

// Types
interface InterventionData {
  id: string;
  title: string;
  type: string;
  category: string;
  status: string;
  startDate: string;
  endDate: string;
  participants: {
    target: number;
    actual: number;
  };
  budget?: number;
  roi?: number;
  effectiveness: MetricEffectiveness[];
  overallScore: number;
  recommendations: string[];
}

interface MetricEffectiveness {
  metricName: string;
  preMean: number;
  postMean: number;
  percentChange: number;
  effectSize: number;
  statisticalSignificance: boolean;
  pValue: number;
  confidenceInterval: [number, number];
  clinicalSignificance: string;
  practicalSignificance: boolean;
}

interface StatisticalSummary {
  significantMetrics: number;
  totalMetrics: number;
  averageEffectSize: number;
  powerAnalysis: {
    observedPower: number;
    requiredSampleSize: number;
    minimumDetectableEffect: number;
  };
  bayesianEvidence: {
    strong: number;
    moderate: number;
    weak: number;
  };
}

interface InterventionEffectivenessDashboardProps {
  interventionId: string;
  data?: InterventionData;
  onExport?: (format: 'pdf' | 'excel' | 'csv') => void;
  onFilterChange?: (filters: any) => void;
}

const InterventionEffectivenessDashboard: React.FC<InterventionEffectivenessDashboardProps> = ({
  interventionId,
  data,
  onExport,
  onFilterChange,
}) => {
  const [selectedTab, setSelectedTab] = useState('overview');
  const [timeRange, setTimeRange] = useState('90d');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);

  // Mock data for demonstration
  const mockData: InterventionData = {
    id: interventionId,
    title: 'Leadership Development Program',
    type: 'Training',
    category: 'Leadership',
    status: 'completed',
    startDate: '2024-01-15',
    endDate: '2024-03-15',
    participants: {
      target: 25,
      actual: 22,
    },
    budget: 50000,
    roi: 2.3,
    effectiveness: [
      {
        metricName: 'Leadership Confidence',
        preMean: 3.2,
        postMean: 4.1,
        percentChange: 28.1,
        effectSize: 1.2,
        statisticalSignificance: true,
        pValue: 0.002,
        confidenceInterval: [0.5, 1.1],
        clinicalSignificance: 'large',
        practicalSignificance: true,
      },
      {
        metricName: 'Team Engagement',
        preMean: 2.8,
        postMean: 3.6,
        percentChange: 28.6,
        effectSize: 0.9,
        statisticalSignificance: true,
        pValue: 0.015,
        confidenceInterval: [0.2, 1.0],
        clinicalSignificance: 'medium',
        practicalSignificance: true,
      },
      {
        metricName: 'Decision Making Speed',
        preMean: 3.5,
        postMean: 4.0,
        percentChange: 14.3,
        effectSize: 0.6,
        statisticalSignificance: false,
        pValue: 0.089,
        confidenceInterval: [-0.1, 0.8],
        clinicalSignificance: 'small',
        practicalSignificance: false,
      },
    ],
    overallScore: 0.82,
    recommendations: [
      'Scale program to other departments based on strong effectiveness',
      'Focus on improving decision making metrics in future iterations',
      'Consider extending program duration for sustained impact',
    ],
  };

  const currentData = data || mockData;

  const statisticalSummary: StatisticalSummary = useMemo(() => {
    const significantMetrics = currentData.effectiveness.filter(m => m.statisticalSignificance).length;
    const averageEffectSize = currentData.effectiveness.reduce((sum, m) => sum + m.effectSize, 0) / currentData.effectiveness.length;

    return {
      significantMetrics,
      totalMetrics: currentData.effectiveness.length,
      averageEffectSize,
      powerAnalysis: {
        observedPower: 0.87,
        requiredSampleSize: 18,
        minimumDetectableEffect: 0.45,
      },
      bayesianEvidence: {
        strong: 2,
        moderate: 1,
        weak: 0,
      },
    };
  }, [currentData]);

  // Prepare data for charts
  const prePostChartData = currentData.effectiveness.map(metric => ({
    metric: metric.metricName,
    'Pre-Intervention': metric.preMean,
    'Post-Intervention': metric.postMean,
    change: metric.percentChange,
  }));

  const effectSizeData = currentData.effectiveness.map(metric => ({
    metric: metric.metricName,
    effectSize: metric.effectSize,
    significance: metric.statisticalSignificance ? 'Significant' : 'Not Significant',
    practical: metric.practicalSignificance ? 'Practical' : 'Not Practical',
  }));

  const radarData = currentData.effectiveness.map(metric => ({
    metric: metric.metricName.split(' ')[0],
    pre: metric.preMean,
    post: metric.postMean,
    fullMark: 5,
  }));

  const getEffectSizeColor = (effectSize: number) => {
    if (Math.abs(effectSize) >= 0.8) return '#10b981'; // green
    if (Math.abs(effectSize) >= 0.5) return '#f59e0b'; // yellow
    if (Math.abs(effectSize) >= 0.2) return '#f97316'; // orange
    return '#ef4444'; // red
  };

  const getSignificanceBadge = (significant: boolean) => {
    return (
      <Badge variant={significant ? 'default' : 'secondary'}>
        {significant ? 'Significant' : 'Not Significant'}
      </Badge>
    );
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Effectiveness</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(currentData.overallScore * 100).toFixed(1)}%</div>
            <Progress value={currentData.overallScore * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Participants</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {currentData.participants.actual}/{currentData.participants.target}
            </div>
            <p className="text-xs text-muted-foreground">
              {((currentData.participants.actual / currentData.participants.target) * 100).toFixed(1)}% completion
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Statistical Power</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(statisticalSummary.powerAnalysis.observedPower * 100).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Adequate power (&gt;80%)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ROI</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currentData.roi}x</div>
            <p className="text-xs text-muted-foreground">
              {currentData.budget ? formatCurrency(currentData.budget) : 'N/A budget'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recommendations */}
      {currentData.recommendations.length > 0 && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertTitle>Key Recommendations</AlertTitle>
          <AlertDescription>
            <ul className="mt-2 list-disc list-inside space-y-1">
              {currentData.recommendations.map((rec, index) => (
                <li key={index} className="text-sm">{rec}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Pre/Post Comparison Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Pre/Post Intervention Comparison</CardTitle>
          <CardDescription>
            Average scores before and after the intervention
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={prePostChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" />
              <YAxis domain={[0, 5]} />
              <Tooltip />
              <Legend />
              <Bar dataKey="Pre-Intervention" fill="#94a3b8" />
              <Bar dataKey="Post-Intervention" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );

  const renderDetailedAnalysis = () => (
    <div className="space-y-6">
      {/* Statistical Significance */}
      <Card>
        <CardHeader>
          <CardTitle>Statistical Significance Summary</CardTitle>
          <CardDescription>
            {statisticalSummary.significantMetrics} of {statisticalSummary.totalMetrics} metrics show statistically significant improvements
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {statisticalSummary.significantMetrics}
              </div>
              <p className="text-sm text-muted-foreground">Significant Metrics</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {statisticalSummary.averageEffectSize.toFixed(2)}
              </div>
              <p className="text-sm text-muted-foreground">Average Effect Size</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {(statisticalSummary.powerAnalysis.observedPower * 100).toFixed(1)}%
              </div>
              <p className="text-sm text-muted-foreground">Statistical Power</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Effect Sizes */}
      <Card>
        <CardHeader>
          <CardTitle>Effect Size Analysis</CardTitle>
          <CardDescription>
            Cohen's d effect sizes with statistical significance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={effectSizeData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[-1.5, 1.5]} />
              <YAxis dataKey="metric" type="category" />
              <Tooltip />
              <Bar
                dataKey="effectSize"
                fill={(entry: any) => getEffectSizeColor(entry.effectSize)}
                name="Effect Size"
              />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Radar Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Multi-dimensional Impact</CardTitle>
          <CardDescription>
            Comprehensive view of intervention impact across all metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="metric" />
              <PolarRadiusAxis angle={90} domain={[0, 5]} />
              <Radar
                name="Pre-Intervention"
                dataKey="pre"
                stroke="#94a3b8"
                fill="#94a3b8"
                fillOpacity={0.3}
              />
              <Radar
                name="Post-Intervention"
                dataKey="post"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.3}
              />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );

  const renderMetricsTable = () => (
    <Card>
      <CardHeader>
        <CardTitle>Detailed Metrics Analysis</CardTitle>
        <CardDescription>
          Comprehensive analysis of each measured metric
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Metric</th>
                <th className="text-center p-2">Pre Mean</th>
                <th className="text-center p-2">Post Mean</th>
                <th className="text-center p-2">% Change</th>
                <th className="text-center p-2">Effect Size</th>
                <th className="text-center p-2">P-Value</th>
                <th className="text-center p-2">Significance</th>
                <th className="text-center p-2">Clinical Impact</th>
              </tr>
            </thead>
            <tbody>
              {currentData.effectiveness.map((metric, index) => (
                <tr key={index} className="border-b hover:bg-muted/50">
                  <td className="p-2 font-medium">{metric.metricName}</td>
                  <td className="text-center p-2">{metric.preMean.toFixed(2)}</td>
                  <td className="text-center p-2">{metric.postMean.toFixed(2)}</td>
                  <td className="text-center p-2">
                    <span className={`font-medium ${
                      metric.percentChange > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {metric.percentChange > 0 ? '+' : ''}{metric.percentChange.toFixed(1)}%
                    </span>
                  </td>
                  <td className="text-center p-2">
                    <span
                      className="font-medium"
                      style={{ color: getEffectSizeColor(metric.effectSize) }}
                    >
                      {metric.effectSize.toFixed(2)}
                    </span>
                  </td>
                  <td className="text-center p-2">{metric.pValue.toFixed(3)}</td>
                  <td className="text-center p-2">
                    {getSignificanceBadge(metric.statisticalSignificance)}
                  </td>
                  <td className="text-center p-2">
                    <Badge variant={metric.clinicalSignificance === 'large' ? 'default' : 'secondary'}>
                      {metric.clinicalSignificance}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{currentData.title}</h1>
          <p className="text-muted-foreground">
            Effectiveness Analysis • {currentData.type} • {currentData.category}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={currentData.status === 'completed' ? 'default' : 'secondary'}>
            {currentData.status}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onExport?.('pdf')}
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="analysis">Detailed Analysis</TabsTrigger>
          <TabsTrigger value="metrics">Metrics Table</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {renderOverview()}
        </TabsContent>

        <TabsContent value="analysis" className="space-y-4">
          {renderDetailedAnalysis()}
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          {renderMetricsTable()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default InterventionEffectivenessDashboard;