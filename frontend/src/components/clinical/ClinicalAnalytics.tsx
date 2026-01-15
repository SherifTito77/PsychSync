import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/card';
import WellbeingScore from './WellbeingScore';
import RiskLevelIndicator from './RiskLevelIndicator';

interface AnalyticsData {
  totalScreenings: number;
  averageScore: number;
  riskDistribution: {
    minimal: number;
    mild: number;
    moderate: number;
    severe: number;
  };
  toolUsage: {
    phq9: number;
    gad7: number;
    wellbeing: number;
  };
  trendData: {
    date: string;
    phq9Score?: number;
    gad7Score?: number;
    wellbeingScore?: number;
  }[];
}

interface ClinicalAnalyticsProps {
  userId?: string;
  timeframe: 'week' | 'month' | 'quarter' | 'year';
  showTrends?: boolean;
  showComparisons?: boolean;
}

const ClinicalAnalytics: React.FC<ClinicalAnalyticsProps> = ({
  userId,
  timeframe = 'month',
  showTrends = true,
  showComparisons = false,
}) => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalyticsData();
  }, [userId, timeframe]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/v1/clinical/analytics?user_id=${userId || 'me'}&timeframe=${timeframe}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch analytics data');
      }

      const data = await response.json();
      setAnalyticsData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'minimal':
        return 'bg-green-500';
      case 'mild':
        return 'bg-yellow-500';
      case 'moderate':
        return 'bg-orange-500';
      case 'severe':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getToolUsagePercentage = (toolCount: number) => {
    if (!analyticsData) return 0;
    return analyticsData.totalScreenings > 0
      ? Math.round((toolCount / analyticsData.totalScreenings) * 100)
      : 0;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <CardContent className="p-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="h-5 w-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-medium text-red-900">Error Loading Analytics</h3>
              <p className="text-sm text-red-700">{error}</p>
              <button
                onClick={fetchAnalyticsData}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Try Again
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!analyticsData) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <p className="text-gray-500">No analytics data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mr-4">
                <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Total Screenings</p>
                <p className="text-2xl font-bold text-gray-900">{analyticsData.totalScreenings}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mr-4">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Average Score</p>
                <p className="text-2xl font-bold text-gray-900">{analyticsData.averageScore.toFixed(1)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mr-4">
                <svg className="h-6 w-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Most Used Tool</p>
                <p className="text-lg font-bold text-gray-900 capitalize">
                  {analyticsData.toolUsage.phq9 >= analyticsData.toolUsage.gad7 ? 'PHQ-9' : 'GAD-7'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mr-4">
                <svg className="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Risk Level</p>
                <div className="flex items-center mt-1">
                  <div className={`w-3 h-3 rounded-full mr-2 ${getRiskLevelColor(
                    analyticsData.riskDistribution.severe > 0 ? 'severe' :
                    analyticsData.riskDistribution.moderate > 0 ? 'moderate' :
                    analyticsData.riskDistribution.mild > 0 ? 'mild' : 'minimal'
                  )}`}></div>
                  <p className="text-lg font-bold text-gray-900 capitalize">
                    {analyticsData.riskDistribution.severe > 0 ? 'Elevated' :
                     analyticsData.riskDistribution.moderate > 0 ? 'Moderate' :
                     analyticsData.riskDistribution.mild > 0 ? 'Low' : 'Minimal'}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Risk Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Risk Level Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(analyticsData.riskDistribution).map(([level, count]) => (
                <div key={level} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-4 h-4 rounded-full mr-3 ${getRiskLevelColor(level)}`}></div>
                    <span className="capitalize text-sm font-medium text-gray-700">{level}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getRiskLevelColor(level)}`}
                        style={{
                          width: `${analyticsData.totalScreenings > 0 ? (count / analyticsData.totalScreenings) * 100 : 0}%`
                        }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600 w-12 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Tool Usage */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Assessment Tool Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">PHQ-9 (Depression)</span>
                <div className="flex items-center space-x-3">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${getToolUsagePercentage(analyticsData.toolUsage.phq9)}%` }}
                    ></div>
                  </div>
                  <span className="text-sm text-gray-600 w-12 text-right">{analyticsData.toolUsage.phq9}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">GAD-7 (Anxiety)</span>
                <div className="flex items-center space-x-3">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${getToolUsagePercentage(analyticsData.toolUsage.gad7)}%` }}
                    ></div>
                  </div>
                  <span className="text-sm text-gray-600 w-12 text-right">{analyticsData.toolUsage.gad7}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Wellbeing Assessment</span>
                <div className="flex items-center space-x-3">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-purple-500 h-2 rounded-full"
                      style={{ width: `${getToolUsagePercentage(analyticsData.toolUsage.wellbeing)}%` }}
                    ></div>
                  </div>
                  <span className="text-sm text-gray-600 w-12 text-right">{analyticsData.toolUsage.wellbeing}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trend Data */}
      {showTrends && analyticsData.trendData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Score Trends Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analyticsData.trendData.slice(-7).map((data, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      {new Date(data.date).toLocaleDateString()}
                    </span>
                    <div className="flex space-x-4">
                      {data.phq9Score !== undefined && (
                        <div className="text-sm">
                          <span className="text-gray-500">PHQ-9:</span>
                          <span className="ml-2 font-medium">{data.phq9Score}</span>
                        </div>
                      )}
                      {data.gad7Score !== undefined && (
                        <div className="text-sm">
                          <span className="text-gray-500">GAD-7:</span>
                          <span className="ml-2 font-medium">{data.gad7Score}</span>
                        </div>
                      )}
                      {data.wellbeingScore !== undefined && (
                        <div className="text-sm">
                          <span className="text-gray-500">Wellbeing:</span>
                          <span className="ml-2 font-medium">{data.wellbeingScore}%</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Wellbeing Score Overview */}
      {analyticsData.toolUsage.wellbeing > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Current Wellbeing Status</CardTitle>
          </CardHeader>
          <CardContent>
            <WellbeingScore
              score={analyticsData.trendData[analyticsData.trendData.length - 1]?.wellbeingScore || 0}
              maxScore={100}
              category="overall"
              showDetails={true}
              size="lg"
              trend={
                analyticsData.trendData.length >= 2
                  ? (analyticsData.trendData[analyticsData.trendData.length - 1]?.wellbeingScore || 0) >
                    (analyticsData.trendData[analyticsData.trendData.length - 2]?.wellbeingScore || 0)
                    ? 'up' : 'down'
                  : 'stable'
              }
              previousScore={analyticsData.trendData[analyticsData.trendData.length - 2]?.wellbeingScore}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ClinicalAnalytics;