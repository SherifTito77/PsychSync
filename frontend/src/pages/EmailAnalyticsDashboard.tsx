// Email Analytics Dashboard
// Displays comprehensive email analytics and behavioral insights from email data

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import {
  Mail,
  TrendingUp,
  Clock,
  Users,
  Globe,
  Tag,
  Brain,
  Shield,
  Briefcase,
  DollarSign,
  Activity,
  Calendar,
  RefreshCw,
  Download,
  AlertCircle,
  CheckCircle,
  Settings,
} from 'lucide-react';
import { getEmailAnalyticsDashboard } from '@/services/emailConnectorService';

interface EmailAnalyticsData {
  total_emails: number;
  time_period_days: number;
  emails_per_day: number;
  top_senders: Array<{ name: string; count: number; percentage: number }>;
  top_domains: Array<{ domain: string; count: number; category: string }>;
  keyword_patterns: Array<{ keyword: string; count: number; category: string }>;
  behavioral_profile: {
    security_score: number;
    career_engagement: number;
    financial_footprint: number;
    activity_pattern: string;
  };
  timing_patterns: Array<{ hour: string; count: number; label: string }>;
  date_range: { start: string; end: string };
}

const EmailAnalyticsDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [analyticsData, setAnalyticsData] = useState<EmailAnalyticsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState('30d');

  const timeRanges = [
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' },
  ];

  const colors = {
    security: '#ef4444',
    career: '#3b82f6',
    financial: '#22c55e',
    activity: '#f59e0b',
    chart: ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'],
  };

  // Score threshold configuration
  // TODO(human): Customize these thresholds based on your organization's security posture
  const scoreThresholds = {
    high: 40,      // Score >= this value = HIGH
    moderate: 20,  // Score >= this value = MODERATE
    // Below moderate = LOW
  };

  // Advanced: Per-metric thresholds for different risk profiles
  // TODO(human): Implement custom threshold strategy for each behavioral metric
  // This allows different sensitivity for security vs career vs financial scores
  const customThresholds = {
    security: {
      high: 50,      // More conservative for security - needs 50%+
      moderate: 25,  // 25-49% = moderate
    },
    career: {
      high: 30,      // More lenient for career - only 30%+
      moderate: 15,  // 15-29% = moderate
    },
    financial: {
      high: 35,
      moderate: 18,
    },
  };

  // TODO(human): Implement a function that uses customThresholds instead of scoreThresholds
  // This should be called getScoreLevelWithCustomThresholds(metricType, score)
  // Example usage: getScoreLevelWithCustomThresholds('security', 40.5) would return 'MODERATE' (not 'HIGH')
  // because 40.5 < 50 (the custom high threshold for security)

  /**
   * Get score level with custom thresholds based on metric type
   * Allows different sensitivity levels for security vs career vs financial metrics
   */
  const getScoreLevelWithCustomThresholds = (
    metricType: keyof typeof customThresholds,
    score: number
  ): { label: string; color: string } => {
    const thresholds = customThresholds[metricType];

    if (score >= thresholds.high) {
      return { label: 'HIGH', color: 'bg-green-500' };
    } else if (score >= thresholds.moderate) {
      return { label: 'MODERATE', color: 'bg-yellow-500' };
    } else {
      return { label: 'LOW', color: 'bg-gray-400' };
    }
  };

  useEffect(() => {
    loadAnalyticsData();
  }, [selectedTimeRange]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getEmailAnalyticsDashboard(selectedTimeRange);

      if (response.success && response.dashboard_data) {
        setAnalyticsData(response.dashboard_data as EmailAnalyticsData);
      } else {
        setError('Failed to load analytics data');
      }
    } catch (err: any) {
      console.error('Error loading email analytics:', err);

      // Better error handling
      if (err?.response?.status === 401) {
        setError('You need to log in to view email analytics. Please authenticate first.');
      } else if (err?.response?.status === 403) {
        setError('Access denied. Please ensure you have permission to view email analytics.');
      } else if (err?.response?.status === 404) {
        setError('Email analytics service not found. Please connect your email account first.');
      } else if (err?.code === 'ERR_NETWORK' || err?.message?.includes('Network Error')) {
        setError('Cannot connect to the server. Please check if the backend is running.');
      } else {
        setError(`Failed to load analytics: ${err?.message || 'Unknown error'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const getScoreLevel = (score: number): { label: string; color: string } => {
    if (score >= scoreThresholds.high) return { label: 'HIGH', color: 'bg-green-500' };
    if (score >= scoreThresholds.moderate) return { label: 'MODERATE', color: 'bg-yellow-500' };
    return { label: 'LOW', color: 'bg-gray-400' };
  };

  const formatHourLabel = (hour: string): string => {
    const hourNum = parseInt(hour);
    if (hourNum === 0) return '12 AM';
    if (hourNum < 12) return `${hourNum} AM`;
    if (hourNum === 12) return '12 PM';
    return `${hourNum - 12} PM`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-48 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !analyticsData) {
    const isAuthError = error?.includes('log in') || error?.includes('authenticate');
    const isNetworkError = error?.includes('Cannot connect') || error?.includes('Network Error');
    const isConnectionError = error?.includes('connect your email') || error?.includes('not found');

    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-8 w-8 text-red-600 mt-1 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-red-800">Analytics Not Available</h3>
                  <p className="text-red-700 mt-2">
                    {error || 'Please connect your email account and sync your emails to view analytics.'}
                  </p>

                  <div className="mt-4 space-y-2">
                    {isAuthError && (
                      <Button
                        onClick={() => window.location.href = '/login'}
                        className="mr-2"
                        variant="default"
                      >
                        Go to Login
                      </Button>
                    )}
                    {isConnectionError && (
                      <Button
                        onClick={() => window.location.href = '/email-connector'}
                        className="mr-2"
                        variant="default"
                      >
                        Connect Email Account
                      </Button>
                    )}
                    <Button
                      onClick={loadAnalyticsData}
                      variant="outline"
                    >
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Try Again
                    </Button>
                  </div>

                  {isNetworkError && (
                    <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                      <p className="text-sm text-yellow-800">
                        <strong>Backend Connection Required:</strong> Please ensure the FastAPI backend is running on port 8000.
                      </p>
                    </div>
                  )}

                  {/* Diagnostic Information */}
                  <details className="mt-4">
                    <summary className="text-sm text-red-600 cursor-pointer hover:text-red-800">
                      View Diagnostic Information
                    </summary>
                    <div className="mt-2 p-3 bg-gray-100 rounded text-xs font-mono space-y-1">
                      <p>API Endpoint: <code className="bg-white px-1 rounded">/email-connector/analytics/dashboard</code></p>
                      <p>Selected Time Range: <code className="bg-white px-1 rounded">{selectedTimeRange}</code></p>
                      <p>Error Type: {isAuthError ? 'Authentication' : isNetworkError ? 'Network' : isConnectionError ? 'Connection' : 'Unknown'}</p>
                    </div>
                  </details>
                </div>
              </div>
            </CardContent>
          </Card>
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
                <Mail className="h-8 w-8 text-blue-600" />
                Email Analytics Dashboard
              </h1>
              <p className="text-gray-600 mt-2">
                Comprehensive insights from your email communication patterns
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
              <Button onClick={loadAnalyticsData} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="patterns">Patterns</TabsTrigger>
            <TabsTrigger value="behavioral">Behavioral</TabsTrigger>
            <TabsTrigger value="timing">Timing</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Email Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-blue-900">Total Emails</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="text-3xl font-bold text-blue-900">
                      {analyticsData.total_emails.toLocaleString()}
                    </div>
                    <Mail className="h-8 w-8 text-blue-600 opacity-50" />
                  </div>
                  <p className="text-xs text-blue-700 mt-2">
                    Last {analyticsData.time_period_days} days
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-green-900">Daily Average</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="text-3xl font-bold text-green-900">
                      {analyticsData.emails_per_day.toFixed(1)}
                    </div>
                    <TrendingUp className="h-8 w-8 text-green-600 opacity-50" />
                  </div>
                  <p className="text-xs text-green-700 mt-2">Emails per day</p>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-purple-900">Top Sender</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-lg font-bold text-purple-900 truncate">
                    {analyticsData.top_senders[0]?.name || 'N/A'}
                  </div>
                  <p className="text-xs text-purple-700 mt-2">
                    {analyticsData.top_senders[0]?.count || 0} emails
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-orange-900">Peak Hour</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-orange-900">
                    {formatHourLabel(analyticsData.timing_patterns[0]?.hour || '0')}
                  </div>
                  <p className="text-xs text-orange-700 mt-2">
                    {analyticsData.timing_patterns[0]?.count || 0} emails
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Top Senders and Domains */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-blue-600" />
                    Top Senders
                  </CardTitle>
                  <CardDescription>Most frequent email contacts</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {analyticsData.top_senders.slice(0, 10).map((sender, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1">
                          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold text-sm">
                            {index + 1}
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-gray-900 truncate">{sender.name}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <Progress value={sender.percentage} className="h-1.5 flex-1" />
                              <span className="text-xs text-gray-500 w-12 text-right">
                                {sender.percentage.toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        </div>
                        <Badge variant="outline" className="ml-2">
                          {sender.count}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Globe className="h-5 w-5 text-purple-600" />
                    Top Domains
                  </CardTitle>
                  <CardDescription>Email sources by domain</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={analyticsData.top_domains.slice(0, 8)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="domain"
                        angle={-45}
                        textAnchor="end"
                        height={100}
                        fontSize={12}
                      />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#8b5cf6" />
                    </BarChart>
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
                  <Tag className="h-5 w-5 text-indigo-600" />
                  Keyword Patterns
                </CardTitle>
                <CardDescription>Most common topics and themes in your emails</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <ResponsiveContainer width="100%" height={350}>
                      <PieChart>
                        <Pie
                          data={analyticsData.keyword_patterns}
                          dataKey="count"
                          nameKey="keyword"
                          cx="50%"
                          cy="50%"
                          outerRadius={100}
                          label={(entry) => `${entry.keyword} (${entry.count})`}
                        >
                          {analyticsData.keyword_patterns.map((_, index) => (
                            <Cell key={`cell-${index}`} fill={colors.chart[index % colors.chart.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="space-y-3">
                    <h4 className="font-semibold text-gray-900 mb-4">Keyword Details</h4>
                    {analyticsData.keyword_patterns.map((keyword, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: colors.chart[index % colors.chart.length] }}
                          ></div>
                          <div>
                            <p className="font-medium">{keyword.keyword}</p>
                            <p className="text-xs text-gray-500 capitalize">{keyword.category}</p>
                          </div>
                        </div>
                        <Badge variant="secondary">{keyword.count} emails</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Domain Categories</CardTitle>
                <CardDescription>Breakdown by domain type</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Array.from(new Set(analyticsData.top_domains.map(d => d.category))).map((category, index) => {
                    const count = analyticsData.top_domains
                      .filter(d => d.category === category)
                      .reduce((sum, d) => sum + d.count, 0);
                    return (
                      <div key={index} className="p-4 bg-gray-50 rounded-lg text-center">
                        <p className="text-2xl font-bold text-gray-900">{count}</p>
                        <p className="text-sm text-gray-600 capitalize">{category}</p>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Behavioral Tab */}
          <TabsContent value="behavioral" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-pink-600" />
                  Behavioral Profile
                </CardTitle>
                <CardDescription>Insights derived from your email communication patterns</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Security Score */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Shield className="h-5 w-5 text-red-600" />
                        <span className="font-semibold">Security Score</span>
                      </div>
                      <Badge className={getScoreLevelWithCustomThresholds('security', analyticsData.behavioral_profile.security_score).color}>
                        {getScoreLevelWithCustomThresholds('security', analyticsData.behavioral_profile.security_score).label}
                      </Badge>
                    </div>
                    <Progress
                      value={Math.min(analyticsData.behavioral_profile.security_score, 100)}
                      className="h-3"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {analyticsData.behavioral_profile.security_score.toFixed(1)}% security-related emails
                    </p>
                  </div>

                  {/* Career Engagement */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Briefcase className="h-5 w-5 text-blue-600" />
                        <span className="font-semibold">Career Engagement</span>
                      </div>
                      <Badge className={getScoreLevelWithCustomThresholds('career', analyticsData.behavioral_profile.career_engagement).color}>
                        {getScoreLevelWithCustomThresholds('career', analyticsData.behavioral_profile.career_engagement).label}
                      </Badge>
                    </div>
                    <Progress
                      value={Math.min(analyticsData.behavioral_profile.career_engagement * 2, 100)}
                      className="h-3"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {analyticsData.behavioral_profile.career_engagement.toFixed(1)}% professional emails
                    </p>
                  </div>

                  {/* Financial Footprint */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <DollarSign className="h-5 w-5 text-green-600" />
                        <span className="font-semibold">Financial Footprint</span>
                      </div>
                      <Badge className={getScoreLevelWithCustomThresholds('financial', analyticsData.behavioral_profile.financial_footprint).color}>
                        {getScoreLevelWithCustomThresholds('financial', analyticsData.behavioral_profile.financial_footprint).label}
                      </Badge>
                    </div>
                    <Progress
                      value={Math.min(analyticsData.behavioral_profile.financial_footprint * 2, 100)}
                      className="h-3"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {analyticsData.behavioral_profile.financial_footprint.toFixed(1)}% financial emails
                    </p>
                  </div>

                  {/* Activity Pattern */}
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Activity className="h-5 w-5 text-orange-600" />
                      <span className="font-semibold">Activity Pattern</span>
                    </div>
                    <p className="text-gray-700">{analyticsData.behavioral_profile.activity_pattern}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-blue-50 border-blue-200">
              <CardHeader>
                <CardTitle className="text-blue-900">💡 Insights</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analyticsData.behavioral_profile.security_score > 30 && (
                    <div className="flex items-start gap-2">
                      <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
                      <p className="text-sm text-blue-900">
                        High security email volume indicates strong awareness of digital security and account management.
                      </p>
                    </div>
                  )}
                  {analyticsData.behavioral_profile.career_engagement > 15 && (
                    <div className="flex items-start gap-2">
                      <Briefcase className="h-5 w-5 text-blue-600 mt-0.5" />
                      <p className="text-sm text-blue-900">
                        Active professional communication suggests strong networking and career development focus.
                      </p>
                    </div>
                  )}
                  {analyticsData.behavioral_profile.financial_footprint > 10 && (
                    <div className="flex items-start gap-2">
                      <DollarSign className="h-5 w-5 text-blue-600 mt-0.5" />
                      <p className="text-sm text-blue-900">
                        Significant financial email activity indicates engaged financial planning and management.
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Threshold Comparison Card */}
            <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
              <CardHeader>
                <CardTitle className="text-purple-900 flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Custom Threshold Configuration
                </CardTitle>
                <CardDescription className="text-purple-700">
                  Your scores are now evaluated using metric-specific thresholds for more accurate insights
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Security Threshold Explanation */}
                  <div className="p-3 bg-white rounded-lg border border-purple-100">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4 text-red-600" />
                        <span className="font-semibold text-sm">Security: 40.5% →</span>
                        <Badge className="bg-yellow-500">MODERATE</Badge>
                      </div>
                      <span className="text-xs text-gray-500">(was HIGH with global threshold)</span>
                    </div>
                    <p className="text-xs text-gray-600">
                      Using stricter threshold: HIGH ≥ 50%, MODERATE ≥ 25%. Your score is below the HIGH threshold.
                    </p>
                  </div>

                  {/* Career Threshold Explanation */}
                  <div className="p-3 bg-white rounded-lg border border-purple-100">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Briefcase className="h-4 w-4 text-blue-600" />
                        <span className="font-semibold text-sm">Career: 7.5% →</span>
                        <Badge className="bg-gray-400">LOW</Badge>
                      </div>
                      <span className="text-xs text-gray-500">(consistent with global threshold)</span>
                    </div>
                    <p className="text-xs text-gray-600">
                      Using lenient threshold: HIGH ≥ 30%, MODERATE ≥ 15%. Your score is below the MODERATE threshold.
                    </p>
                  </div>

                  {/* Financial Threshold Explanation */}
                  <div className="p-3 bg-white rounded-lg border border-purple-100">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-green-600" />
                        <span className="font-semibold text-sm">Financial: 14.5% →</span>
                        <Badge className="bg-gray-400">LOW</Badge>
                      </div>
                      <span className="text-xs text-gray-500">(was LOW with global threshold)</span>
                    </div>
                    <p className="text-xs text-gray-600">
                      Using medium threshold: HIGH ≥ 35%, MODERATE ≥ 18%. Your score is below the MODERATE threshold.
                    </p>
                  </div>

                  {/* Configuration Summary */}
                  <details className="mt-4">
                    <summary className="text-sm font-semibold text-purple-900 cursor-pointer hover:text-purple-700">
                      View Full Threshold Configuration
                    </summary>
                    <div className="mt-3 p-3 bg-gray-100 rounded text-xs font-mono space-y-2">
                      <div className="grid grid-cols-3 gap-2 font-semibold border-b border-gray-300 pb-2">
                        <span>Metric</span>
                        <span>High ≥</span>
                        <span>Moderate ≥</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <span>Security 🔒</span>
                        <span className="text-green-600">50%</span>
                        <span className="text-yellow-600">25%</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <span>Career 💼</span>
                        <span className="text-green-600">30%</span>
                        <span className="text-yellow-600">15%</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <span>Financial 💰</span>
                        <span className="text-green-600">35%</span>
                        <span className="text-yellow-600">18%</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 border-t border-gray-300 pt-2 mt-2 text-gray-500">
                        <span>Global (old)</span>
                        <span>40%</span>
                        <span>20%</span>
                      </div>
                    </div>
                  </details>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Timing Tab */}
          <TabsContent value="timing" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-green-600" />
                  Email Activity by Hour
                </CardTitle>
                <CardDescription>When you send and receive most emails</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <AreaChart data={analyticsData.timing_patterns}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="hour"
                      tickFormatter={formatHourLabel}
                      fontSize={12}
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(label) => `Time: ${formatHourLabel(label)}`}
                      formatter={(value: number) => [`${value} emails`, 'Count']}
                    />
                    <Area
                      type="monotone"
                      dataKey="count"
                      stroke="#10b981"
                      fill="#10b981"
                      fillOpacity={0.6}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="border-orange-200 bg-orange-50">
                <CardHeader>
                  <CardTitle className="text-orange-900 text-lg">🔥 Peak Time</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-orange-900">
                    {formatHourLabel(analyticsData.timing_patterns[0]?.hour || '0')}
                  </p>
                  <p className="text-sm text-orange-700 mt-2">
                    {analyticsData.timing_patterns[0]?.count || 0} emails
                  </p>
                  <p className="text-xs text-orange-600 mt-1">Highest activity</p>
                </CardContent>
              </Card>

              <Card className="border-blue-200 bg-blue-50">
                <CardHeader>
                  <CardTitle className="text-blue-900 text-lg">⚡ Secondary Peak</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-blue-900">
                    {formatHourLabel(analyticsData.timing_patterns[1]?.hour || '0')}
                  </p>
                  <p className="text-sm text-blue-700 mt-2">
                    {analyticsData.timing_patterns[1]?.count || 0} emails
                  </p>
                  <p className="text-xs text-blue-600 mt-1">Second highest</p>
                </CardContent>
              </Card>

              <Card className="border-green-200 bg-green-50">
                <CardHeader>
                  <CardTitle className="text-green-900 text-lg">📊 Tertiary Peak</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-green-900">
                    {formatHourLabel(analyticsData.timing_patterns[2]?.hour || '0')}
                  </p>
                  <p className="text-sm text-green-700 mt-2">
                    {analyticsData.timing_patterns[2]?.count || 0} emails
                  </p>
                  <p className="text-xs text-green-600 mt-1">Third highest</p>
                </CardContent>
              </Card>
            </div>

            <Card className="bg-gray-50">
              <CardHeader>
                <CardTitle>Activity Pattern Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  <p className="text-gray-700">
                    Your email activity shows distinct patterns throughout the day. Peak hours indicate your most
                    productive communication times. This data can help optimize your schedule and improve
                    work-life balance by identifying when you're most engaged with email communication.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Footer */}
        <Card className="mt-6 bg-gray-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                <Calendar className="h-4 w-4 inline mr-2" />
                Data from {new Date(analyticsData.date_range.start).toLocaleDateString()} to{' '}
                {new Date(analyticsData.date_range.end).toLocaleDateString()}
              </div>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export Report
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EmailAnalyticsDashboard;
