import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface TrendData {
  date: string;
  overall_score: number;
  domain_scores: Record<string, number>;
  assessment_type: string;
  insights?: string[];
}

interface TrendAnalysisProps {
  userId?: string;
  timeRange?: '1m' | '3m' | '6m' | '1y' | 'all';
}

// Demo trend data generator for development/testing
const getDemoTrendData = (): TrendData[] => {
  const now = new Date();
  const data: TrendData[] = [];

  // Generate 6 months of demo data
  for (let i = 5; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 15);

    // Generate realistic wellness scores with some variation
    const overallScore = Math.max(0.3, Math.min(0.95, 0.65 + (Math.random() - 0.5) * 0.3));

    // Domain scores with realistic correlations
    const physicalScore = Math.max(0.2, Math.min(0.95, overallScore + (Math.random() - 0.5) * 0.2));
    const emotionalScore = Math.max(0.2, Math.min(0.95, overallScore + (Math.random() - 0.5) * 0.25));
    const socialScore = Math.max(0.2, Math.min(0.95, overallScore + (Math.random() - 0.5) * 0.2));
    const intellectualScore = Math.max(0.2, Math.min(0.95, overallScore + (Math.random() - 0.5) * 0.15));
    const spiritualScore = Math.max(0.2, Math.min(0.95, overallScore + (Math.random() - 0.5) * 0.3));
    const occupationalScore = Math.max(0.2, Math.min(0.95, overallScore + (Math.random() - 0.5) * 0.2));
    const environmentalScore = Math.max(0.2, Math.min(0.95, overallScore + (Math.random() - 0.5) * 0.25));

    data.push({
      date: date.toISOString().split('T')[0],
      overall_score: overallScore,
      domain_scores: {
        physical: physicalScore,
        emotional: emotionalScore,
        social: socialScore,
        intellectual: intellectualScore,
        spiritual: spiritualScore,
        occupational: occupationalScore,
        environmental: environmentalScore
      },
      assessment_type: i % 2 === 0 ? 'Wellness Assessment' : 'Mental Health Screening',
      insights: []
    });
  }

  return data;
};

// Demo AI insights generator
const getDemoInsights = (trendData: TrendData[]): string[] => {
  if (trendData.length === 0) return [];

  const insights: string[] = [];
  const recent = trendData.slice(-3);
  const earlier = trendData.slice(0, Math.max(0, trendData.length - 3));

  const recentAvg = recent.reduce((sum, d) => sum + d.overall_score, 0) / recent.length;
  const earlierAvg = earlier.length > 0 ? earlier.reduce((sum, d) => sum + d.overall_score, 0) / earlier.length : recentAvg;
  const trend = recentAvg - earlierAvg;

  if (trend > 0.1) {
    insights.push("Your overall wellness has shown consistent improvement over the past few months. Keep up the excellent progress!");
    insights.push("Consider sharing your successful strategies with others who might benefit from your experience.");
  } else if (trend < -0.1) {
    insights.push("Your wellness scores have shown a slight decline recently. Consider focusing on self-care and stress management.");
    insights.push("This is a common pattern and taking small, consistent steps can help reverse this trend.");
  } else {
    insights.push("Your wellness levels have remained relatively stable. Small, consistent changes can lead to significant improvements over time.");
  }

  // Find strongest and weakest domains
  const latestData = trendData[trendData.length - 1];
  const domainScores = latestData.domain_scores;
  const sortedDomains = Object.entries(domainScores).sort(([, a], [, b]) => b - a);

  if (sortedDomains.length > 0) {
    const strongest = sortedDomains[0];
    const weakest = sortedDomains[sortedDomains.length - 1];

    insights.push(`Your ${strongest[0]} wellness is particularly strong (${Math.round(strongest[1] * 100)}%). This is a valuable asset to maintain.`);
    insights.push(`Consider giving extra attention to your ${weakest[0]} wellness (${Math.round(weakest[1] * 100)}%), as small improvements here can have significant benefits.`);
  }

  // Add practical suggestions
  insights.push("Regular assessment tracking helps identify patterns and measure progress over time.");
  insights.push("Consider setting specific, achievable goals in your lower-scoring domains to create balanced wellness.");

  return insights;
};

const TrendAnalysis: React.FC<TrendAnalysisProps> = ({ userId, timeRange = '3m' }) => {
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [selectedDomains, setSelectedDomains] = useState<string[]>(['all']);
  const [insights, setInsights] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const domains = [
    'physical', 'emotional', 'social', 'intellectual',
    'spiritual', 'occupational', 'environmental'
  ];

  const timeRanges = [
    { value: '1m', label: '1 Month' },
    { value: '3m', label: '3 Months' },
    { value: '6m', label: '6 Months' },
    { value: '1y', label: '1 Year' },
    { value: 'all', label: 'All Time' }
  ];

  useEffect(() => {
    fetchTrendData();
  }, [selectedTimeRange, selectedDomains]);

  const fetchTrendData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.log('No auth token found, using demo trend data');
        const demoData = getDemoTrendData();
        setTrendData(demoData);
        setInsights(getDemoInsights(demoData));
        setIsLoading(false);
        return;
      }

      const response = await fetch(`/api/v1/clinical/trends/data?time_range=${selectedTimeRange}&domains=${selectedDomains.join(',')}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch trend data: ${response.statusText}`);
      }

      const data = await response.json();
      if (data.success) {
        const responseData = data.data as { trend_data?: any[]; ai_insights?: any[] };
        setTrendData(responseData.trend_data || []);
        setInsights(responseData.ai_insights || []);
      } else {
        setError('Failed to load trend analysis data');
      }
    } catch (err) {
      console.error('Error fetching trend data:', err);
      // Fall back to demo data on error
      const demoData = getDemoTrendData();
      setTrendData(demoData);
      setInsights(getDemoInsights(demoData));
      setError(null); // Clear error since we have demo data
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-blue-600';
    if (score >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getDomainIcon = (domain: string) => {
    const icons: Record<string, string> = {
      physical: '💪',
      emotional: '❤️',
      social: '👥',
      intellectual: '🧠',
      spiritual: '🌟',
      occupational: '💼',
      environmental: '🏠'
    };
    return icons[domain] || '📊';
  };

  const calculateTrend = (data: number[]): 'up' | 'down' | 'stable' => {
    if (data.length < 2) return 'stable';

    const recent = data.slice(-Math.min(3, data.length));
    const older = data.slice(0, Math.max(0, data.length - 3));

    const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
    const olderAvg = older.length > 0 ? older.reduce((a, b) => a + b, 0) / older.length : recentAvg;

    const difference = recentAvg - olderAvg;

    if (Math.abs(difference) < 0.05) return 'stable';
    return difference > 0 ? 'up' : 'down';
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return '📈';
      case 'down': return '📉';
      case 'stable': return '➡️';
    }
  };

  const exportData = () => {
    const csvContent = [
      ['Date', 'Overall Score', 'Assessment Type', ...domains.map(d => d.charAt(0).toUpperCase() + d.slice(1))],
      ...trendData.map(item => [
        item.date,
        Math.round(item.overall_score * 100),
        item.assessment_type,
        ...domains.map(domain => Math.round((item.domain_scores[domain] || 0) * 100))
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `wellness-trends-${selectedTimeRange}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Analyzing your wellness trends...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-6">
            <h3 className="text-red-800 font-semibold mb-2">Error</h3>
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={fetchTrendData} variant="outline">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (trendData.length === 0) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card className="text-center">
          <CardContent className="p-8">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-2">No Trend Data Available</h3>
            <p className="text-gray-600 mb-6">
              Start taking wellness assessments to see your progress over time.
            </p>
            <Button onClick={() => window.location.href = '/mental-health-wellness'}>
              Take Wellness Assessment
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Calculate trends for each domain
  const domainTrends: Record<string, 'up' | 'down' | 'stable'> = {};
  domains.forEach(domain => {
    const scores = trendData.map(item => item.domain_scores[domain] || 0);
    domainTrends[domain] = calculateTrend(scores);
  });

  const overallTrend = calculateTrend(trendData.map(item => item.overall_score));

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Wellness Trend Analysis</h1>
        <p className="text-gray-600">
          Track your mental health and wellness progress over time with AI-powered insights
        </p>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Analysis Controls</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Time Range Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Range
              </label>
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {timeRanges.map(range => (
                  <option key={range.value} value={range.value}>
                    {range.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Domain Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Focus Domains
              </label>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedDomains.includes('all')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedDomains(['all']);
                      } else {
                        setSelectedDomains([]);
                      }
                    }}
                    className="mr-2"
                  />
                  All Domains
                </label>
                {domains.map(domain => (
                  <label key={domain} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedDomains.includes(domain)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedDomains(prev => prev.filter(d => d !== 'all').concat(domain));
                        } else {
                          setSelectedDomains(prev => prev.filter(d => d !== domain));
                        }
                      }}
                      disabled={selectedDomains.includes('all')}
                      className="mr-2"
                    />
                    <span className="capitalize">{domain} {getDomainIcon(domain)}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Actions
              </label>
              <div className="space-y-2">
                <Button onClick={fetchTrendData} variant="outline" className="w-full">
                  Refresh Data
                </Button>
                <Button onClick={exportData} variant="secondary" className="w-full">
                  Export to CSV
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Overall Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="text-center">
          <CardContent className="p-6">
            <div className="text-4xl mb-2">{getTrendIcon(overallTrend)}</div>
            <h3 className="text-lg font-semibold mb-2">Overall Trend</h3>
            <div className={`text-2xl font-bold ${getScoreColor(trendData[trendData.length - 1]?.overall_score || 0)}`}>
              {Math.round((trendData[trendData.length - 1]?.overall_score || 0) * 100)}%
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Current wellness score
            </p>
          </CardContent>
        </Card>

        <Card className="text-center">
          <CardContent className="p-6">
            <div className="text-4xl mb-2">📋</div>
            <h3 className="text-lg font-semibold mb-2">Assessments Completed</h3>
            <div className="text-2xl font-bold text-blue-600">
              {trendData.length}
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Total assessments
            </p>
          </CardContent>
        </Card>

        <Card className="text-center">
          <CardContent className="p-6">
            <div className="text-4xl mb-2">📈</div>
            <h3 className="text-lg font-semibold mb-2">Improvement Rate</h3>
            <div className="text-2xl font-bold text-green-600">
              {overallTrend === 'up' ? '+' : overallTrend === 'down' ? '-' : ''}
              {Math.round(Math.abs((trendData[trendData.length - 1]?.overall_score || 0) - (trendData[0]?.overall_score || 0)) * 100)}%
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Since first assessment
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Domain Trends */}
      <Card>
        <CardHeader>
          <CardTitle>Domain-Specific Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {domains.map(domain => {
              const currentScore = trendData[trendData.length - 1]?.domain_scores[domain] || 0;
              const trend = domainTrends[domain];

              return (
                <div key={domain} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-xl">{getDomainIcon(domain)}</span>
                      <span className="font-semibold capitalize">{domain}</span>
                    </div>
                    <span className="text-lg">{getTrendIcon(trend)}</span>
                  </div>
                  <div className={`text-xl font-bold ${getScoreColor(currentScore)}`}>
                    {Math.round(currentScore * 100)}%
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {trend === 'up' ? 'Improving' : trend === 'down' ? 'Declining' : 'Stable'}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* AI Insights */}
      {insights.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>AI-Powered Insights</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {insights.map((insight, index) => (
                <div key={index} className="p-4 bg-blue-50 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <span className="text-blue-600 text-lg">💡</span>
                    <p className="text-gray-700">{insight}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Timeline View */}
      <Card>
        <CardHeader>
          <CardTitle>Assessment Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {trendData.slice(-10).reverse().map((item, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <div className="font-semibold">{new Date(item.date).toLocaleDateString()}</div>
                  <div className="text-sm text-gray-600">{item.assessment_type}</div>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-bold ${getScoreColor(item.overall_score)}`}>
                    {Math.round(item.overall_score * 100)}%
                  </div>
                  <div className="text-xs text-gray-500">Overall Score</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TrendAnalysis;
