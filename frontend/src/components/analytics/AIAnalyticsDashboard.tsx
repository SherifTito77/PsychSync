/**
 * AI Analytics Dashboard Component
 * Displays AI-enhanced analytics with predictive insights and recommendations
 */

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/common/Button';
import { api } from '@/services/api';

interface AIInsight {
  type: string;
  title: string;
  description: string;
  priority: string;
  confidence: number;
  data_points: string[];
  recommended_actions: string[];
  predicted_impact?: string;
  time_horizon?: string;
}

interface PredictiveMetric {
  metric_name: string;
  current_value: number;
  predicted_value: number;
  confidence: number;
  trend_direction: string;
  time_period: string;
  accuracy_score: number;
  influencing_factors: string[];
}

interface AIDashboardData {
  dashboard_metadata: {
    generated_at: string;
    ai_enhanced: boolean;
    confidence_threshold: number;
  };
  ai_insights: {
    total_insights: number;
    critical_insights: number;
    high_priority_insights: number;
    insights: AIInsight[];
  };
  predictive_metrics: {
    total_predictions: number;
    high_confidence_predictions: number;
    predictions: PredictiveMetric[];
  };
  risk_assessment: {
    overall_risk_level: string;
    risk_factors: string[];
    mitigation_strategies: string[];
  };
  opportunities: {
    high_potential_users: any[];
    team_optimization_opportunities: any[];
    engagement_opportunities: string[];
    development_opportunities: string[];
  };
  ai_summary: {
    key_findings: string;
    overall_health: string;
    top_priority: string;
  };
}

export const AIAnalyticsDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<AIDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInsightType, setSelectedInsightType] = useState<string>('all');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadAIDashboard();
  }, []);

  const loadAIDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/ai-analytics/dashboard?time_period_days=30');
      setDashboardData(response.data.data);
    } catch (err: any) {
      console.error('Error loading AI dashboard:', err);
      setError(err.response?.data?.message || 'Failed to load AI analytics');
    } finally {
      setLoading(false);
    }
  };

  const refreshAnalytics = async () => {
    try {
      setRefreshing(true);
      await api.post('/ai-analytics/refresh');
      await loadAIDashboard();
    } catch (err: any) {
      console.error('Error refreshing analytics:', err);
      setError('Failed to refresh analytics');
    } finally {
      setRefreshing(false);
    }
  };

  const filteredInsights = dashboardData?.ai_insights.insights.filter(insight =>
    selectedInsightType === 'all' || insight.type === selectedInsightType
  ) || [];

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'increasing': return '📈';
      case 'decreasing': return '📉';
      case 'stable': return '➡️';
      default: return '❓';
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="h-48 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Card className="p-6 text-center">
          <div className="text-red-600 mb-4">⚠️ {error}</div>
          <Button onClick={loadAIDashboard}>Retry</Button>
        </Card>
      </div>
    );
  }

  if (!dashboardData) {
    return <div className="p-6">No data available</div>;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Analytics Dashboard</h1>
          <p className="text-gray-600 mt-2">
            AI-enhanced insights with {dashboardData.ai_insights.total_insights} insights and {dashboardData.predictive_metrics.total_predictions} predictions
          </p>
        </div>
        <div className="flex space-x-3">
          <Button
            variant="outline"
            onClick={refreshAnalytics}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : '🔄 Refresh'}
          </Button>
          <Button onClick={() => window.open('/docs', '_blank')}>
            📊 View Documentation
          </Button>
        </div>
      </div>

      {/* AI Summary */}
      <Card className="p-6 bg-gradient-to-r from-blue-50 to-purple-50">
        <h2 className="text-xl font-semibold mb-4">🤖 AI Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <div className="text-sm text-gray-600">Key Findings</div>
            <div className="font-medium">{dashboardData.ai_summary.key_findings}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Overall Health</div>
            <div className="font-medium capitalize">{dashboardData.ai_summary.overall_health}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Top Priority</div>
            <div className="font-medium">{dashboardData.ai_summary.top_priority}</div>
          </div>
        </div>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm text-gray-600">Critical Insights</div>
          <div className="text-2xl font-bold text-red-600">{dashboardData.ai_insights.critical_insights}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-600">High Priority</div>
          <div className="text-2xl font-bold text-orange-600">{dashboardData.ai_insights.high_priority_insights}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-600">High Confidence Predictions</div>
          <div className="text-2xl font-bold text-green-600">{dashboardData.predictive_metrics.high_confidence_predictions}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-600">Risk Level</div>
          <div className="text-2xl font-bold capitalize">
            <span className={`${
              dashboardData.risk_assessment.overall_risk_level === 'high' ? 'text-red-600' :
              dashboardData.risk_assessment.overall_risk_level === 'medium' ? 'text-yellow-600' :
              'text-green-600'
            }`}>
              {dashboardData.risk_assessment.overall_risk_level}
            </span>
          </div>
        </Card>
      </div>

      {/* AI Insights */}
      <Card className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">🧠 AI Insights</h2>
          <select
            value={selectedInsightType}
            onChange={(e) => setSelectedInsightType(e.target.value)}
            className="border border-gray-300 rounded px-3 py-1 text-sm"
          >
            <option value="all">All Types</option>
            <option value="prediction">Predictions</option>
            <option value="anomaly_detection">Anomaly Detection</option>
            <option value="trend_analysis">Trend Analysis</option>
            <option value="recommendation">Recommendations</option>
            <option value="risk_assessment">Risk Assessment</option>
            <option value="opportunity_identification">Opportunities</option>
          </select>
        </div>

        <div className="space-y-4">
          {filteredInsights.map((insight, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(insight.priority)}`}>
                      {insight.priority.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500">
                      Confidence: {Math.round(insight.confidence * 100)}%
                    </span>
                    {insight.time_horizon && (
                      <span className="text-xs text-gray-500">
                        ⏱️ {insight.time_horizon}
                      </span>
                    )}
                  </div>
                  <h3 className="font-semibold text-lg">{insight.title}</h3>
                  <p className="text-gray-600 mt-1">{insight.description}</p>

                  {insight.predicted_impact && (
                    <div className="mt-2 text-sm text-blue-600">
                      💡 Predicted Impact: {insight.predicted_impact}
                    </div>
                  )}
                </div>
              </div>

              {insight.recommended_actions.length > 0 && (
                <div className="mt-4">
                  <div className="text-sm font-medium text-gray-700 mb-2">Recommended Actions:</div>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {insight.recommended_actions.map((action, actionIndex) => (
                      <li key={actionIndex} className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        {action}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Predictive Metrics */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">📈 Predictive Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dashboardData.predictive_metrics.predictions.map((metric, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium">{metric.metric_name}</h3>
                <span className="text-lg">
                  {getTrendIcon(metric.trend_direction)}
                </span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Current:</span>
                  <span className="font-medium">{Math.round(metric.current_value * 100)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Predicted:</span>
                  <span className="font-medium text-blue-600">{Math.round(metric.predicted_value * 100)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Confidence:</span>
                  <span className="font-medium">{Math.round(metric.confidence * 100)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Accuracy:</span>
                  <span className="font-medium">{Math.round(metric.accuracy_score * 100)}%</span>
                </div>
              </div>

              {metric.influencing_factors.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="text-xs text-gray-600 mb-1">Key Factors:</div>
                  <div className="flex flex-wrap gap-1">
                    {metric.influencing_factors.map((factor, factorIndex) => (
                      <span key={factorIndex} className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Opportunities */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">🎯 Growth Opportunities</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {dashboardData.opportunities.engagement_opportunities.length > 0 && (
            <div>
              <h3 className="font-medium mb-3">Engagement Opportunities</h3>
              <ul className="space-y-2">
                {dashboardData.opportunities.engagement_opportunities.map((opportunity, index) => (
                  <li key={index} className="flex items-start text-sm">
                    <span className="text-green-500 mr-2">→</span>
                    {opportunity}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {dashboardData.opportunities.development_opportunities.length > 0 && (
            <div>
              <h3 className="font-medium mb-3">Development Opportunities</h3>
              <ul className="space-y-2">
                {dashboardData.opportunities.development_opportunities.map((opportunity, index) => (
                  <li key={index} className="flex items-start text-sm">
                    <span className="text-blue-500 mr-2">→</span>
                    {opportunity}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </Card>

      {/* Risk Assessment */}
      {dashboardData.risk_assessment.risk_factors.length > 0 && (
        <Card className="p-6 border-l-4 border-orange-500">
          <h2 className="text-xl font-semibold mb-4">⚠️ Risk Assessment</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium mb-3 text-orange-600">Risk Factors</h3>
              <ul className="space-y-2">
                {dashboardData.risk_assessment.risk_factors.map((factor, index) => (
                  <li key={index} className="flex items-start text-sm">
                    <span className="text-orange-500 mr-2">⚡</span>
                    {factor}
                  </li>
                ))}
              </ul>
            </div>

            {dashboardData.risk_assessment.mitigation_strategies.length > 0 && (
              <div>
                <h3 className="font-medium mb-3 text-green-600">Mitigation Strategies</h3>
                <ul className="space-y-2">
                  {dashboardData.risk_assessment.mitigation_strategies.map((strategy, index) => (
                    <li key={index} className="flex items-start text-sm">
                      <span className="text-green-500 mr-2">✓</span>
                      {strategy}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Footer */}
      <div className="text-center text-sm text-gray-500 pt-4">
        Last updated: {new Date(dashboardData.dashboard_metadata.generated_at).toLocaleString()} •
        AI-Powered Analytics v1.0 •
        Confidence Threshold: {Math.round(dashboardData.dashboard_metadata.confidence_threshold * 100)}%
      </div>
    </div>
  );
};