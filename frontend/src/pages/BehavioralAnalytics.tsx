// Behavioral Analytics Page
// Comprehensive behavioral pattern analysis and mental health insights

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
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
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import {
  Brain,
  TrendingUp,
  AlertTriangle,
  Heart,
  Activity,
  Users,
  Target,
  Shield,
  Eye,
  RefreshCw,
  Download,
  Calendar,
  Clock,
  Zap,
  BarChart3,
  PieChartIcon,
  AlertCircle,
  CheckCircle,
  Info,
} from 'lucide-react';

import behavioralAnalyticsService, {
  PatternAnalysisResponse,
  TeamBehavioralInsights
} from '@/services/behavioralAnalyticsService';

const BehavioralAnalytics: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [selectedUserId, setSelectedUserId] = useState<string>('current-user');
  const [selectedTimeRange, setSelectedTimeRange] = useState('30d');
  const [patternAnalysis, setPatternAnalysis] = useState<PatternAnalysisResponse | null>(null);
  const [teamInsights, setTeamInsights] = useState<TeamBehavioralInsights | null>(null);
  const [mentalHealthInsights, setMentalHealthInsights] = useState<any>(null);
  const [wellnessMetrics, setWellnessMetrics] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const timeRanges = [
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' },
    { value: '1y', label: 'Last Year' },
  ];

  const riskLevelColors = {
    low: '#22c55e',
    medium: '#f59e0b',
    high: '#ef4444',
    critical: '#991b1b',
  };

  const behavioralColors = [
    '#3b82f6', '#8b5cf6', '#06b6d4', '#10b981',
    '#f59e0b', '#ef4444', '#6366f1', '#84cc16'
  ];

  const loadBehavioralData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load pattern analysis
      const patternData = await behavioralAnalyticsService.analyzeUserPatterns(
        selectedUserId,
        selectedTimeRange === '7d' ? 168 : selectedTimeRange === '30d' ? 720 : selectedTimeRange === '90d' ? 2160 : 8760,
        ['temporal', 'sequential', 'social', 'learning', 'performance', 'risk'],
        true
      );
      setPatternAnalysis(patternData);

      // Load mental health insights
      try {
        const mentalHealthData = await behavioralAnalyticsService.getMentalHealthInsights(selectedUserId);
        setMentalHealthInsights(mentalHealthData);
      } catch (err) {
        console.warn('Mental health insights not available:', err);
      }

      // Load wellness metrics
      try {
        const wellnessData = await behavioralAnalyticsService.getWellnessMetrics(selectedUserId, selectedTimeRange);
        setWellnessMetrics(wellnessData);
      } catch (err) {
        console.warn('Wellness metrics not available:', err);
      }

    } catch (err) {
      console.error('Error loading behavioral data:', err);
      setError('Failed to load behavioral analytics data. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [selectedUserId, selectedTimeRange]);

  useEffect(() => {
    loadBehavioralData();
  }, [loadBehavioralData]);

  const getRiskLevelVariant = (level: string) => {
    switch (level) {
      case 'low': return 'secondary';
      case 'medium': return 'outline';
      case 'high': return 'destructive';
      case 'critical': return 'destructive';
      default: return 'secondary';
    }
  };

  const formatPatternData = (patterns: any[]) => {
    return patterns.map((pattern, index) => ({
      name: pattern.pattern_type,
      confidence: pattern.confidence * 100,
      frequency: pattern.frequency,
      fill: behavioralColors[index % behavioralColors.length],
    }));
  };

  const formatWellnessData = () => {
    if (!wellnessMetrics) return [];

    return [
      { metric: 'Physical', value: wellnessMetrics.physical_wellness * 10, fullMark: 100 },
      { metric: 'Emotional', value: wellnessMetrics.emotional_wellness * 10, fullMark: 100 },
      { metric: 'Mental', value: wellnessMetrics.mental_wellness * 10, fullMark: 100 },
      { metric: 'Social', value: wellnessMetrics.social_wellness * 10, fullMark: 100 },
      { metric: 'Professional', value: wellnessMetrics.professional_wellness * 10, fullMark: 100 },
    ];
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-64 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                <Brain className="h-8 w-8 text-blue-600" />
                Behavioral Analytics
              </h1>
              <p className="text-gray-600 mt-2">
                Comprehensive behavioral pattern analysis and mental health insights
              </p>
            </div>
            <div className="flex items-center gap-4">
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {timeRanges.map(range => (
                  <option key={range.value} value={range.value}>
                    {range.label}
                  </option>
                ))}
              </select>
              <Button onClick={loadBehavioralData} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>

        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertTitle className="text-red-800">Error</AlertTitle>
            <AlertDescription className="text-red-700">{error}</AlertDescription>
          </Alert>
        )}

        {patternAnalysis && (
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="patterns">Patterns</TabsTrigger>
              <TabsTrigger value="mental-health">Mental Health</TabsTrigger>
              <TabsTrigger value="wellness">Wellness</TabsTrigger>
              <TabsTrigger value="insights">Insights</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              {/* Risk Assessment */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-blue-600" />
                    Risk Assessment
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold mb-2">
                        {(patternAnalysis.risk_assessment.risk_score * 100).toFixed(1)}%
                      </div>
                      <Badge
                        variant={getRiskLevelVariant(patternAnalysis.risk_assessment.risk_level)}
                        className="mb-2"
                      >
                        {patternAnalysis.risk_assessment.risk_level.toUpperCase()} RISK
                      </Badge>
                      <p className="text-sm text-gray-600">
                        {patternAnalysis.risk_assessment.recommendation}
                      </p>
                    </div>

                    <div className="col-span-2">
                      <h4 className="font-semibold mb-3">Risk Factors</h4>
                      <div className="space-y-2">
                        {patternAnalysis.risk_assessment.risk_factors.length > 0 ? (
                          patternAnalysis.risk_assessment.risk_factors.map((factor, index) => (
                            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                              <div>
                                <p className="font-medium">{factor.description}</p>
                                <p className="text-sm text-gray-600">Type: {factor.type}</p>
                              </div>
                              <Badge variant={factor.severity === 'high' ? 'destructive' : 'outline'}>
                                {factor.severity}
                              </Badge>
                            </div>
                          ))
                        ) : (
                          <p className="text-green-600 flex items-center gap-2">
                            <CheckCircle className="h-4 w-4" />
                            No significant risk factors detected
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Behavioral Profile */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Activity className="h-5 w-5 text-green-600" />
                      Behavioral Profile
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span>Total Patterns</span>
                        <Badge variant="secondary">
                          {patternAnalysis.behavioral_profile.overview.total_patterns}
                        </Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Average Confidence</span>
                        <Badge variant="secondary">
                          {(patternAnalysis.behavioral_profile.overview.avg_confidence * 100).toFixed(1)}%
                        </Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Data Quality</span>
                        <Badge variant="secondary">
                          {(patternAnalysis.data_quality.overall_quality * 100).toFixed(1)}%
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5 text-purple-600" />
                      Pattern Distribution
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie
                          data={Object.entries(patternAnalysis.behavioral_profile.patterns_summary).map(([key, value]) => ({
                            name: key,
                            value: value as number
                          }))}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                        >
                          {Object.entries(patternAnalysis.behavioral_profile.patterns_summary).map((_, index) => (
                            <Cell key={`cell-${index}`} fill={behavioralColors[index % behavioralColors.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Patterns Tab */}
            <TabsContent value="patterns" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-indigo-600" />
                    Detected Behavioral Patterns
                  </CardTitle>
                  <CardDescription>
                    AI-detected patterns in your behavior over the selected time period
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {patternAnalysis.patterns.length > 0 ? (
                    <div className="space-y-4">
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={formatPatternData(patternAnalysis.patterns)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="confidence" fill="#3b82f6" name="Confidence %" />
                          <Bar dataKey="frequency" fill="#8b5cf6" name="Frequency" />
                        </BarChart>
                      </ResponsiveContainer>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {patternAnalysis.patterns.map((pattern, index) => (
                          <Card key={pattern.pattern_id} className="p-4">
                            <div className="flex justify-between items-start mb-2">
                              <h4 className="font-semibold capitalize">{pattern.pattern_type}</h4>
                              <Badge variant="outline">
                                {(pattern.confidence * 100).toFixed(1)}%
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{pattern.description}</p>
                            <p className="text-xs text-gray-500">
                              Frequency: {pattern.frequency} | Impact: {pattern.impact_assessment}
                            </p>
                          </Card>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <Brain className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                      <p>No behavioral patterns detected in this time period</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Mental Health Tab */}
            <TabsContent value="mental-health" className="space-y-6">
              {mentalHealthInsights ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Heart className="h-5 w-5 text-red-600" />
                        Risk Indicators
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {Object.entries(mentalHealthInsights.risk_indicators).map(([key, value]) => (
                          <div key={key}>
                            <div className="flex justify-between items-center mb-2">
                              <span className="capitalize">{key.replace('_', ' ')}</span>
                              <Badge
                                variant={value === 'low' ? 'secondary' : value === 'medium' ? 'outline' : 'destructive'}
                              >
                                {value}
                              </Badge>
                            </div>
                            <Progress
                              value={value === 'low' ? 25 : value === 'medium' ? 50 : value === 'high' ? 75 : 90}
                              className="h-2"
                            />
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-green-600" />
                        Wellness Trends
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {Object.entries(mentalHealthInsights.wellness_trends).map(([key, value]) => (
                          <div key={key} className="flex items-center gap-2">
                            {value === 'improving' && <TrendingUp className="h-4 w-4 text-green-500" />}
                            {value === 'declining' && <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />}
                            {value === 'stable' && <Activity className="h-4 w-4 text-blue-500" />}
                            <span className="capitalize">{key.replace('_', ' ')}: {value}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <Card>
                  <CardContent className="text-center py-8">
                    <Heart className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-gray-500">Mental health insights not available</p>
                    <p className="text-sm text-gray-400 mt-2">
                      Complete mental health assessments to enable these insights
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Wellness Tab */}
            <TabsContent value="wellness" className="space-y-6">
              {wellnessMetrics ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Activity className="h-5 w-5 text-green-600" />
                        Wellness Scores
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span>Overall Wellness</span>
                            <span className="font-semibold">{wellnessMetrics.overall_wellness_score}/10</span>
                          </div>
                          <Progress value={wellnessMetrics.overall_wellness_score * 10} className="h-2" />
                        </div>
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span>Burnout Risk</span>
                            <span className="font-semibold text-red-600">{wellnessMetrics.burnout_risk_score}/10</span>
                          </div>
                          <Progress value={wellnessMetrics.burnout_risk_score * 10} className="h-2 bg-red-100">
                            <div className="bg-red-500 h-full rounded-full" />
                          </Progress>
                        </div>
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span>Stress Level</span>
                            <span className="font-semibold">{wellnessMetrics.stress_level}/10</span>
                          </div>
                          <Progress value={wellnessMetrics.stress_level * 10} className="h-2" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Target className="h-5 w-5 text-purple-600" />
                        Wellness Dimensions
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <RadarChart data={formatWellnessData()}>
                          <PolarGrid />
                          <PolarAngleAxis dataKey="metric" />
                          <PolarRadiusAxis angle={90} domain={[0, 100]} />
                          <Radar
                            name="Wellness Score"
                            dataKey="value"
                            stroke="#8b5cf6"
                            fill="#8b5cf6"
                            fillOpacity={0.6}
                          />
                        </RadarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <Card>
                  <CardContent className="text-center py-8">
                    <Activity className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-gray-500">Wellness metrics not available</p>
                    <p className="text-sm text-gray-400 mt-2">
                      Complete wellness check-ins to enable these insights
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Insights Tab */}
            <TabsContent value="insights" className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Eye className="h-5 w-5 text-blue-600" />
                      Behavioral Insights
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {patternAnalysis.insights.map((insight, index) => (
                        <div key={index} className="p-4 border border-gray-200 rounded-lg">
                          <div className="flex items-start justify-between mb-2">
                            <h4 className="font-semibold">{insight.title}</h4>
                            <Badge
                              variant={insight.impact === 'positive' ? 'secondary' :
                                       insight.impact === 'warning' ? 'destructive' : 'outline'}
                            >
                              {insight.impact}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600">{insight.description}</p>
                          <p className="text-xs text-gray-500 mt-2">
                            Confidence: {(insight.confidence * 100).toFixed(1)}%
                          </p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Info className="h-5 w-5 text-green-600" />
                      Recommendations
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {patternAnalysis.recommendations.map((recommendation, index) => (
                        <div key={index} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                          <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                          <p className="text-sm text-green-800">{recommendation}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Strengths and Development Areas */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-green-600">Strengths</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {patternAnalysis.behavioral_profile.strengths.map((strength, index) => (
                        <div key={index} className="flex items-center gap-2 text-green-700">
                          <CheckCircle className="h-4 w-4" />
                          <span>{strength}</span>
                        </div>
                      ))}
                      {patternAnalysis.behavioral_profile.strengths.length === 0 && (
                        <p className="text-gray-500 italic">Continue using the platform to identify your strengths</p>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-orange-600">Development Areas</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {patternAnalysis.behavioral_profile.development_areas.map((area, index) => (
                        <div key={index} className="flex items-center gap-2 text-orange-700">
                          <AlertTriangle className="h-4 w-4" />
                          <span>{area}</span>
                        </div>
                      ))}
                      {patternAnalysis.behavioral_profile.development_areas.length === 0 && (
                        <p className="text-gray-500 italic">No development areas identified at this time</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
};

export default BehavioralAnalytics;