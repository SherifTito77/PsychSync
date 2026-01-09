// Pattern Insights Dashboard Component
// Comprehensive dashboard for displaying behavioral pattern insights and anomalies

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
} from 'recharts';
import {
  Brain,
  TrendingUp,
  AlertTriangle,
  Clock,
  Users,
  Activity,
  Target,
  Zap,
  Shield,
  Eye,
  Filter,
  Download,
  RefreshCw,
  ChevronUp,
  ChevronDown,
  Info,
} from 'lucide-react';

// Types for pattern insights
interface Pattern {
  pattern_id: string;
  pattern_type: string;
  description: string;
  confidence: number;
  support: number;
  users: string[];
  severity?: 'low' | 'medium' | 'high' | 'critical';
  impact_score?: number;
  recommendations?: string[];
}

interface Anomaly {
  anomaly_id: string;
  user_id: string;
  anomaly_type: string;
  severity: string;
  description: string;
  confidence: number;
  detected_at: string;
  baseline_metrics: Record<string, number>;
  observed_metrics: Record<string, number>;
  recommendations: string[];
}

interface BehavioralProfile {
  activity_level: {
    total_events: number;
    success_rate: number;
    avg_session_duration_ms: number;
  };
  behavioral_preferences: {
    most_common_actions: Array<[string, number]>;
    activity_diversity: number;
  };
  temporal_patterns: {
    most_active_hours: number[];
    most_active_days: number[];
    activity_regularity: number;
  };
}

interface InsightsData {
  user_id: string;
  analysis_period: {
    start: string;
    end: string;
    hours: number;
  };
  events_analyzed: number;
  patterns: Pattern[];
  anomalies: Anomaly[];
  insights: Array<{
    type: 'pattern' | 'anomaly';
    description: string;
    confidence: number;
    category: string;
    impact: string;
    requires_attention?: boolean;
  }>;
  recommendations: string[];
  behavioral_profile: BehavioralProfile;
  risk_assessment: {
    risk_score: number;
    risk_level: string;
    risk_factors: string[];
    requires_monitoring: boolean;
    requires_intervention: boolean;
  };
}

interface PatternInsightsDashboardProps {
  userId?: string;
  organizationId?: string;
  teamId?: string;
  timeRange?: '7d' | '30d' | '90d';
  className?: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const PatternInsightsDashboard: React.FC<PatternInsightsDashboardProps> = ({
  userId,
  organizationId,
  teamId,
  timeRange = '30d',
  className
}) => {
  const [data, setData] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState('overview');
  const [expandedPatterns, setExpandedPatterns] = useState<Set<string>>(new Set());
  const [filterSeverity, setFilterSeverity] = useState<string>('all');

  // TODO(human): Fetch pattern insights data from the API
  const fetchPatternInsights = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // This would be the actual API call
      // const response = await fetch(`/api/v1/analytics/patterns/insights?user_id=${userId}&time_range=${timeRange}`);
      // const insightsData = await response.json();

      // Mock data for development
      const mockData: InsightsData = {
        user_id: userId || 'user-123',
        analysis_period: {
          start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          end: new Date().toISOString(),
          hours: 720
        },
        events_analyzed: 2847,
        patterns: [
          {
            pattern_id: 'temporal_peak_hours',
            pattern_type: 'temporal',
            description: 'Most active during hours: 9, 10, 14',
            confidence: 0.85,
            support: 245,
            users: [userId || 'user-123'],
            impact_score: 0.7,
            recommendations: ['Schedule important tasks during peak hours', 'Send notifications during active periods']
          },
          {
            pattern_id: 'sequence_login_dashboard',
            pattern_type: 'sequential',
            description: 'Frequent action sequence: login -> dashboard -> reports',
            confidence: 0.78,
            support: 156,
            users: [userId || 'user-123'],
            impact_score: 0.6,
            recommendations: ['Optimize dashboard loading', 'Add quick access to reports']
          },
          {
            pattern_id: 'risk_engagement_decline',
            pattern_type: 'risk',
            description: '35% decrease in activity over last 2 weeks',
            confidence: 0.92,
            support: 89,
            users: [userId || 'user-123'],
            severity: 'high',
            impact_score: 0.9,
            recommendations: ['Proactive outreach recommended', 'Review recent system changes']
          }
        ],
        anomalies: [
          {
            anomaly_id: 'statistical_duration_42',
            user_id: userId || 'user-123',
            anomaly_type: 'statistical',
            severity: 'medium',
            description: 'Unusual session duration: 2.3 hours (z-score: 3.2)',
            confidence: 0.85,
            detected_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            baseline_metrics: { mean: 0.45, std: 0.15 },
            observed_metrics: { duration_ms: 8280000 },
            recommendations: ['Verify session timeout settings', 'Check for potential system issues']
          }
        ],
        insights: [
          {
            type: 'pattern',
            description: 'Strong peak-hour productivity pattern identified',
            confidence: 0.85,
            category: 'temporal',
            impact: 'high'
          },
          {
            type: 'anomaly',
            description: 'Recent engagement decline detected',
            confidence: 0.92,
            category: 'risk',
            impact: 'critical',
            requires_attention: true
          }
        ],
        recommendations: [
          'Monitor user engagement closely to prevent churn',
          'Consider proactive outreach or intervention',
          'Leverage user\'s efficient patterns for training others'
        ],
        behavioral_profile: {
          activity_level: {
            total_events: 2847,
            success_rate: 0.94,
            avg_session_duration_ms: 1620000
          },
          behavioral_preferences: {
            most_common_actions: [
              ['dashboard_view', 892],
              ['report_generate', 456],
              ['data_export', 234],
              ['team_collaborate', 189]
            ],
            activity_diversity: 0.34
          },
          temporal_patterns: {
            most_active_hours: [9, 10, 14],
            most_active_days: [1, 2, 3], // Monday, Tuesday, Wednesday
            activity_regularity: 0.78
          }
        },
        risk_assessment: {
          risk_score: 0.65,
          risk_level: 'medium',
          risk_factors: ['Engagement decline detected', 'High-risk behavioral patterns identified'],
          requires_monitoring: true,
          requires_intervention: false
        }
      };

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      setData(mockData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch pattern insights');
    } finally {
      setLoading(false);
    }
  }, [userId, timeRange]);

  useEffect(() => {
    fetchPatternInsights();
  }, [fetchPatternInsights]);

  const togglePatternExpansion = (patternId: string) => {
    setExpandedPatterns(prev => {
      const newSet = new Set(prev);
      if (newSet.has(patternId)) {
        newSet.delete(patternId);
      } else {
        newSet.add(patternId);
      }
      return newSet;
    });
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'minimal': return 'text-green-600';
      case 'low': return 'text-blue-600';
      case 'medium': return 'text-yellow-600';
      case 'high': return 'text-orange-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getActivityData = () => {
    if (!data?.behavioral_profile.behavioral_preferences.most_common_actions) return [];

    return data.behavioral_profile.behavioral_preferences.most_common_actions.map(([action, count]) => ({
      name: action.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value: count,
      percentage: Math.round((count / data.events_analyzed) * 100)
    }));
  };

  const getTemporalData = () => {
    const hours = Array.from({ length: 24 }, (_, i) => i);
    const peakHours = data?.behavioral_profile.temporal_patterns.most_active_hours || [];

    return hours.map(hour => ({
      hour: `${hour}:00`,
      activity: peakHours.includes(hour) ? Math.random() * 100 + 50 : Math.random() * 50 + 10,
      isPeak: peakHours.includes(hour)
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-lg">Analyzing behavioral patterns...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <CardContent className="pt-6">
          <div className="flex items-center text-red-600">
            <AlertTriangle className="h-5 w-5 mr-2" />
            <span>Error loading pattern insights: {error}</span>
          </div>
          <Button onClick={fetchPatternInsights} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Behavioral Pattern Insights</h2>
          <p className="text-gray-600">
            Analysis period: {new Date(data.analysis_period.start).toLocaleDateString()} - {new Date(data.analysis_period.end).toLocaleDateString()}
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filter
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button onClick={fetchPatternInsights} size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Risk Assessment Overview */}
      <Card className="border-l-4 border-l-orange-500">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Shield className="h-5 w-5 mr-2" />
            Risk Assessment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Risk Score</span>
                <span className={`text-lg font-bold ${getRiskLevelColor(data.risk_assessment.risk_level)}`}>
                  {Math.round(data.risk_assessment.risk_score * 100)}%
                </span>
              </div>
              <Progress value={data.risk_assessment.risk_score * 100} className="mt-2" />
            </div>
            <div>
              <span className="text-sm font-medium">Risk Level</span>
              <div className="flex items-center mt-1">
                <Badge className={getSeverityColor(data.risk_assessment.risk_level)}>
                  {data.risk_assessment.risk_level.toUpperCase()}
                </Badge>
              </div>
            </div>
            <div>
              <span className="text-sm font-medium">Status</span>
              <div className="flex items-center mt-1 space-x-2">
                {data.risk_assessment.requires_monitoring && (
                  <Badge variant="outline" className="text-yellow-600">
                    <Eye className="h-3 w-3 mr-1" />
                    Monitoring
                  </Badge>
                )}
                {data.risk_assessment.requires_intervention && (
                  <Badge variant="destructive">
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    Intervention Required
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="patterns">Patterns</TabsTrigger>
          <TabsTrigger value="anomalies">Anomalies</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Events Analyzed</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{data.events_analyzed.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">Last {data.analysis_period.hours} hours</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Patterns Found</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{data.patterns.length}</div>
                <p className="text-xs text-muted-foreground">Behavioral patterns detected</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Anomalies Detected</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{data.anomalies.length}</div>
                <p className="text-xs text-muted-foreground">Unusual behaviors identified</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {Math.round(data.behavioral_profile.activity_level.success_rate * 100)}%
                </div>
                <p className="text-xs text-muted-foreground">Activity success rate</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Activity Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Activity Distribution</CardTitle>
                <CardDescription>Most frequent user actions</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={getActivityData()}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name} ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {getActivityData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Temporal Patterns */}
            <Card>
              <CardHeader>
                <CardTitle>Temporal Patterns</CardTitle>
                <CardDescription>Activity levels throughout the day</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={getTemporalData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" />
                    <YAxis />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="activity"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Patterns Tab */}
        <TabsContent value="patterns" className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {data.patterns.map((pattern) => (
              <Card key={pattern.pattern_id} className="transition-all hover:shadow-md">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{pattern.description}</CardTitle>
                      <CardDescription className="mt-1">
                        Pattern Type: <Badge variant="outline">{pattern.pattern_type}</Badge>
                      </CardDescription>
                    </div>
                    <div className="flex flex-col items-end space-y-2">
                      {pattern.severity && (
                        <Badge className={getSeverityColor(pattern.severity)}>
                          {pattern.severity}
                        </Badge>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => togglePatternExpansion(pattern.pattern_id)}
                      >
                        {expandedPatterns.has(pattern.pattern_id) ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <span className="text-sm font-medium">Confidence</span>
                      <div className="flex items-center mt-1">
                        <Progress value={pattern.confidence * 100} className="flex-1 mr-2" />
                        <span className="text-sm">{Math.round(pattern.confidence * 100)}%</span>
                      </div>
                    </div>
                    <div>
                      <span className="text-sm font-medium">Support</span>
                      <div className="text-lg font-semibold">{pattern.support}</div>
                    </div>
                    <div>
                      <span className="text-sm font-medium">Impact Score</span>
                      <div className="text-lg font-semibold">
                        {pattern.impact_score ? Math.round(pattern.impact_score * 100) : 'N/A'}
                      </div>
                    </div>
                    <div>
                      <span className="text-sm font-medium">Users Affected</span>
                      <div className="text-lg font-semibold">{pattern.users.length}</div>
                    </div>
                  </div>

                  {expandedPatterns.has(pattern.pattern_id) && (
                    <div className="mt-4 pt-4 border-t space-y-4">
                      {pattern.recommendations && pattern.recommendations.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2 flex items-center">
                            <Target className="h-4 w-4 mr-2" />
                            Recommendations
                          </h4>
                          <ul className="list-disc list-inside space-y-1">
                            {pattern.recommendations.map((rec, index) => (
                              <li key={index} className="text-sm text-gray-600">{rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Anomalies Tab */}
        <TabsContent value="anomalies" className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {data.anomalies.map((anomaly) => (
              <Card key={anomaly.anomaly_id} className="border-l-4 border-l-orange-500">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg flex items-center">
                        <AlertTriangle className="h-5 w-5 mr-2 text-orange-500" />
                        {anomaly.description}
                      </CardTitle>
                      <CardDescription className="mt-1">
                        Detected: {new Date(anomaly.detected_at).toLocaleString()}
                      </CardDescription>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge className={getSeverityColor(anomaly.severity)}>
                        {anomaly.severity}
                      </Badge>
                      <Badge variant="outline">{anomaly.anomaly_type}</Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-medium mb-2">Baseline Metrics</h4>
                      <div className="space-y-1">
                        {Object.entries(anomaly.baseline_metrics).map(([key, value]) => (
                          <div key={key} className="flex justify-between text-sm">
                            <span className="text-gray-600">{key}:</span>
                            <span className="font-medium">{typeof value === 'number' ? value.toFixed(3) : value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">Observed Metrics</h4>
                      <div className="space-y-1">
                        {Object.entries(anomaly.observed_metrics).map(([key, value]) => (
                          <div key={key} className="flex justify-between text-sm">
                            <span className="text-gray-600">{key}:</span>
                            <span className="font-medium text-orange-600">{typeof value === 'number' ? value.toFixed(3) : value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {anomaly.recommendations && anomaly.recommendations.length > 0 && (
                    <div className="mt-4 pt-4 border-t">
                      <h4 className="font-medium mb-2 flex items-center">
                        <Zap className="h-4 w-4 mr-2" />
                        Recommended Actions
                      </h4>
                      <ul className="list-disc list-inside space-y-1">
                        {anomaly.recommendations.map((rec, index) => (
                          <li key={index} className="text-sm text-gray-600">{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Insights Tab */}
        <TabsContent value="insights" className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {data.insights.map((insight, index) => (
              <Card key={index} className={insight.requires_attention ? 'border-l-4 border-l-red-500' : ''}>
                <CardContent className="pt-6">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      {insight.type === 'anomaly' ? (
                        <AlertTriangle className="h-5 w-5 text-red-500" />
                      ) : (
                        <Brain className="h-5 w-5 text-blue-500" />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="text-gray-900">{insight.description}</p>
                      <div className="mt-2 flex items-center space-x-4 text-sm">
                        <Badge variant="outline">{insight.category}</Badge>
                        <span className="text-gray-600">Impact: {insight.impact}</span>
                        <span className="text-gray-600">Confidence: {Math.round(insight.confidence * 100)}%</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Recommendations */}
          {data.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Target className="h-5 w-5 mr-2" />
                  Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {data.recommendations.map((recommendation, index) => (
                    <li key={index} className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                        {index + 1}
                      </div>
                      <span className="text-gray-700">{recommendation}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PatternInsightsDashboard;
