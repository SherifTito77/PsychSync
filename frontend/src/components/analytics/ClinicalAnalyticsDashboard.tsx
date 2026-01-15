/**
 * Clinical Analytics Dashboard
 *
 * Population health insights and trends for clinicians and administrators
 * HIPAA-compliant data aggregation and visualization
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import Progress from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  TrendingUp,
  TrendingDown,
  Users,
  AlertTriangle,
  Activity,
  Calendar,
  BarChart,
  PieChart,
  Shield,
  Clock,
  CheckCircle,
  XCircle,
  Loader2
} from 'lucide-react';
import api from '@/services/api';

interface AnalyticsData {
  summary: {
    total_assessments: number;
    total_users: number;
    crisis_alerts_triggered: number;
    crisis_alerts_resolved: number;
    avg_response_time_minutes: number;
  };
  riskDistribution: {
    low: number;
    moderate: number;
    high: number;
    critical: number;
  };
  assessmentCounts: {
    PHQ9: number;
    GAD7: number;
    CSSRS: number;
    LSAS: number;
    EAT26: number;
    YBOCS: number;
    [key: string]: number;
  };
  trends: {
    date: string;
    total_assessments: number;
    crisis_alerts: number;
  }[];
  highRiskUsers: {
    user_id: string;
    risk_score: number;
    last_assessment: string;
    risk_flags: string[];
  }[];
}

function ClinicalAnalyticsDashboard() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('30d');

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/v1/analytics/population?period=${timeRange}`);
      setData(response.data.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <Card>
          <CardContent className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600 mr-3" />
            <span>Loading analytics...</span>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error || 'Failed to load analytics data'}</AlertDescription>
        </Alert>
      </div>
    );
  }

  const crisisResolutionRate =
    data.summary.crisis_alerts_triggered > 0
      ? (data.summary.crisis_alerts_resolved / data.summary.crisis_alerts_triggered) * 100
      : 0;

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Clinical Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Population health insights and trends
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Shield className="h-5 w-5 text-blue-600" />
          <span className="text-sm text-gray-600">HIPAA-compliant</span>
        </div>
      </div>

      {/* Time Range Selector */}
      <div className="flex gap-2">
        {['7d', '30d', '90d', '1y'].map((range) => (
          <Button
            key={range}
            onClick={() => setTimeRange(range)}
            variant={timeRange === range ? 'default' : 'outline'}
            size="sm"
          >
            {range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : range === '90d' ? '90 Days' : '1 Year'}
          </Button>
        ))}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">Total Assessments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-3xl font-bold">{data.summary.total_assessments}</div>
              <Activity className="h-8 w-8 text-blue-600 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">Active Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-3xl font-bold">{data.summary.total_users}</div>
              <Users className="h-8 w-8 text-green-600 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card className={data.summary.crisis_alerts_triggered > 0 ? 'border-orange-500' : ''}>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">Crisis Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold">{data.summary.crisis_alerts_triggered}</div>
                <div className="text-xs text-gray-600 mt-1">
                  {data.summary.crisis_alerts_resolved} resolved
                </div>
              </div>
              <AlertTriangle className={`h-8 w-8 ${
                data.summary.crisis_alerts_triggered > 0 ? 'text-orange-600' : 'text-gray-400'
              } opacity-20`} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">Avg Response Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold">
                  {data.summary.avg_response_time_minutes}m
                </div>
                <div className="text-xs text-gray-600 mt-1">Crisis response</div>
              </div>
              <Clock className="h-8 w-8 text-purple-600 opacity-20" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs for Different Views */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="risk">Risk Distribution</TabsTrigger>
          <TabsTrigger value="assessments">Assessment Types</TabsTrigger>
          <TabsTrigger value="high-risk">High Risk Users</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Risk Distribution Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Risk Level Distribution</CardTitle>
                <CardDescription>User risk levels across all assessments</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { label: 'Low', value: data.riskDistribution.low, color: 'bg-green-500' },
                    { label: 'Moderate', value: data.riskDistribution.moderate, color: 'bg-yellow-500' },
                    { label: 'High', value: data.riskDistribution.high, color: 'bg-orange-500' },
                    { label: 'Critical', value: data.riskDistribution.critical, color: 'bg-red-500' },
                  ].map((risk) => {
                    const percentage =
                      data.summary.total_assessments > 0
                        ? (risk.value / data.summary.total_assessments) * 100
                        : 0;

                    return (
                      <div key={risk.label}>
                        <div className="flex justify-between mb-2">
                          <span className="text-sm font-medium">{risk.label}</span>
                          <span className="text-sm text-gray-600">{risk.value} ({percentage.toFixed(1)}%)</span>
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Crisis Resolution Rate */}
            <Card>
              <CardHeader>
                <CardTitle>Crisis Response Performance</CardTitle>
                <CardDescription>How quickly crisis alerts are being resolved</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium">Resolution Rate</span>
                    <span className="text-sm text-gray-600">{crisisResolutionRate.toFixed(1)}%</span>
                  </div>
                  <Progress value={crisisResolutionRate} className="h-3" />
                </div>

                <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {data.summary.crisis_alerts_resolved}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">Resolved</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {data.summary.crisis_alerts_triggered - data.summary.crisis_alerts_resolved}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">Pending</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Assessment Trends */}
          <Card>
            <CardHeader>
              <CardTitle>Assessment Trends Over Time</CardTitle>
              <CardDescription>Daily assessment completions and crisis alerts</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.trends.slice(0, 7).map((trend, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <div className="text-sm font-medium">
                        {new Date(trend.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                      </div>
                      <div className="flex items-center gap-4 mt-2">
                        <span className="text-xs text-gray-600">
                          {trend.total_assessments} assessments
                        </span>
                        {trend.crisis_alerts > 0 && (
                          <Badge variant="destructive" className="text-xs">
                            {trend.crisis_alerts} crisis alerts
                          </Badge>
                        )}
                      </div>
                    </div>
                    <TrendingUp className="h-5 w-5 text-blue-600" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Risk Distribution Tab */}
        <TabsContent value="risk" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Risk Distribution by Assessment Type</CardTitle>
              <CardDescription>Breakdown of risk levels for each assessment tool</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {Object.entries(data.assessmentCounts).map(([type, count]) => {
                  const percentage = (count / data.summary.total_assessments) * 100;

                  return (
                    <div key={type}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{type}</Badge>
                          <span className="text-sm font-medium">{count} assessments</span>
                        </div>
                        <span className="text-sm text-gray-600">{percentage.toFixed(1)}%</span>
                      </div>
                      <Progress value={percentage} className="h-2" />
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Assessments Tab */}
        <TabsContent value="assessments" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Assessment Type Breakdown</CardTitle>
              <CardDescription>Usage statistics for each clinical assessment</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {Object.entries(data.assessmentCounts).map(([type, count]) => (
                  <div key={type} className="p-4 border rounded-lg text-center">
                    <div className="text-2xl font-bold mb-1">{count}</div>
                    <div className="text-sm text-gray-600">{type}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* High Risk Users Tab */}
        <TabsContent value="high-risk" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>High-Risk Users Requiring Attention</CardTitle>
              <CardDescription>
                Users with elevated risk scores who may need follow-up
              </CardDescription>
            </CardHeader>
            <CardContent>
              {data.highRiskUsers && data.highRiskUsers.length > 0 ? (
                <div className="space-y-3">
                  {data.highRiskUsers.map((user, idx) => (
                    <div key={idx} className="border rounded-lg p-4 hover:bg-red-50 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <Badge variant="destructive">
                              Risk Score: {user.risk_score}
                            </Badge>
                            <span className="text-xs text-gray-600">
                              Last assessment: {new Date(user.last_assessment).toLocaleDateString()}
                            </span>
                          </div>

                          <div className="flex flex-wrap gap-2 mt-2">
                            {user.risk_flags.map((flag, flagIdx) => (
                              <Badge key={flagIdx} variant="outline" className="text-xs">
                                {flag}
                              </Badge>
                            ))}
                          </div>
                        </div>

                        <Button size="sm" variant="outline">
                          View Details
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium mb-2">No high-risk users detected</p>
                  <p className="text-sm">All users are within safe parameters</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Export Button */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              <Shield className="h-4 w-4 inline mr-2" />
              Data is HIPAA-compliant and anonymized for reporting
            </div>
            <Button onClick={() => window.print()} variant="outline">
              Export Report
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
export default ClinicalAnalyticsDashboard;
