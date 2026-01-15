// frontend/src/components/integrations/BehavioralInsightsDashboard.tsx
/**
 * Behavioral Insights Dashboard
 * Displays actionable insights derived from corporate data source integrations
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import corporateIntegrationService from '@/services/corporateIntegrationService';
import {
  BehavioralInsight,
  IntegrationInsightsReport,
  InsightsFilter
} from '@/types/corporateIntegrations';

const SEVERITY_COLORS = {
  low: 'bg-blue-100 text-blue-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800'
};

const SEVERITY_ICONS = {
  low: 'ℹ️',
  medium: '⚠️',
  high: '🔶',
  critical: '🚨'
};

const CATEGORY_ICONS: Record<string, string> = {
  burnout: '🔥',
  toxicity: '⚡',
  engagement: '💼',
  retention: '👥',
  leadership: '🎯',
  collaboration: '🤝'
};

interface BehavioralInsightsDashboardProps {
  organizationId: number;
  dateRange?: { start: string; end: string };
  onInsightClick?: (insightId: string) => void;
}

export const BehavioralInsightsDashboard: React.FC<BehavioralInsightsDashboardProps> = ({
  organizationId,
  dateRange,
  onInsightClick
}) => {
  const [report, setReport] = useState<IntegrationInsightsReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadReport();
  }, [organizationId]);

  const loadReport = async () => {
    try {
      setLoading(true);
      const latestReport = await corporateIntegrationService.getLatestReport();
      setReport(latestReport);
    } catch (error) {
      console.error('Failed to load insights report:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setGenerating(true);
      const newReport = await corporateIntegrationService.generateInsightsReport(
        dateRange || {
          start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          end: new Date().toISOString()
        }
      );
      setReport(newReport);
    } catch (error) {
      console.error('Failed to generate report:', error);
    } finally {
      setGenerating(false);
    }
  };

  const filteredInsights = report?.insights.filter((insight) => {
    const matchesCategory = selectedCategory === 'all' || insight.category === selectedCategory;
    const matchesSeverity = selectedSeverity === 'all' || insight.severity === selectedSeverity;
    return matchesCategory && matchesSeverity;
  }) || [];

  const insightsByCategory = report?.insights.reduce((acc, insight) => {
    if (!acc[insight.category]) {
      acc[insight.category] = [];
    }
    acc[insight.category].push(insight);
    return acc;
  }, {} as Record<string, BehavioralInsight[]>) || {};

  const insightsBySeverity = {
    critical: filteredInsights.filter((i) => i.severity === 'critical'),
    high: filteredInsights.filter((i) => i.severity === 'high'),
    medium: filteredInsights.filter((i) => i.severity === 'medium'),
    low: filteredInsights.filter((i) => i.severity === 'low')
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Behavioral Insights</h2>
          <p className="text-gray-600 mt-1">
            AI-powered insights from your corporate data sources
          </p>
        </div>
        <Button
          onClick={handleGenerateReport}
          disabled={generating}
          variant="default"
        >
          {generating ? 'Generating...' : 'Generate New Report'}
        </Button>
      </div>

      {/* Summary Stats */}
      {report?.summary && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card className={report.summary.critical_insights > 0 ? 'border-red-300' : ''}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {SEVERITY_ICONS.critical} Critical
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {report.summary.critical_insights}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {SEVERITY_ICONS.high} High
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {report.summary.high_insights}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {SEVERITY_ICONS.medium} Medium
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">
                {report.summary.medium_insights}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {SEVERITY_ICONS.low} Low
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {report.summary.low_insights}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Total Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {report.summary.total_insights}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-4 py-2 border rounded-lg bg-white"
        >
          <option value="all">All Categories</option>
          <option value="burnout">Burnout</option>
          <option value="toxicity">Toxicity</option>
          <option value="engagement">Engagement</option>
          <option value="retention">Retention</option>
          <option value="leadership">Leadership</option>
          <option value="collaboration">Collaboration</option>
        </select>

        <select
          value={selectedSeverity}
          onChange={(e) => setSelectedSeverity(e.target.value)}
          className="px-4 py-2 border rounded-lg bg-white"
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="grid" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="grid">Grid View</TabsTrigger>
          <TabsTrigger value="by-category">By Category</TabsTrigger>
          <TabsTrigger value="by-severity">By Severity</TabsTrigger>
        </TabsList>

        {/* Grid View */}
        <TabsContent value="grid" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredInsights.map((insight) => (
              <InsightCard
                key={`${insight.category}-${insight.detected_at}`}
                insight={insight}
                onClick={() => onInsightClick?.(`${insight.category}-${insight.detected_at}`)}
              />
            ))}
          </div>
        </TabsContent>

        {/* By Category */}
        <TabsContent value="by-category" className="space-y-6">
          {Object.entries(insightsByCategory).map(([category, insights]) => (
            <div key={category}>
              <h3 className="text-xl font-semibold mb-3 flex items-center gap-2">
                <span>{CATEGORY_ICONS[category] || '📊'}</span>
                <span className="capitalize">{category}</span>
                <Badge variant="outline">{insights.length}</Badge>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {insights.map((insight) => (
                  <InsightCard
                    key={`${insight.category}-${insight.detected_at}`}
                    insight={insight}
                    onClick={() => onInsightClick?.(`${insight.category}-${insight.detected_at}`)}
                  />
                ))}
              </div>
            </div>
          ))}
        </TabsContent>

        {/* By Severity */}
        <TabsContent value="by-severity" className="space-y-6">
          {(['critical', 'high', 'medium', 'low'] as const).map((severity) => {
            const severityInsights = insightsBySeverity[severity];
            if (severityInsights.length === 0) return null;

            return (
              <div key={severity}>
                <h3 className="text-xl font-semibold mb-3 flex items-center gap-2">
                  <span>{SEVERITY_ICONS[severity]}</span>
                  <span className="capitalize">{severity} Priority</span>
                  <Badge variant="outline">{severityInsights.length}</Badge>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {severityInsights.map((insight) => (
                    <InsightCard
                      key={`${insight.category}-${insight.detected_at}`}
                      insight={insight}
                      onClick={() => onInsightClick?.(`${insight.category}-${insight.detected_at}`)}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </TabsContent>
      </Tabs>

      {/* Recommendations */}
      {report?.recommendations && report.recommendations.length > 0 && (
        <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
          <CardHeader>
            <CardTitle className="text-blue-900">💡 AI Recommendations</CardTitle>
            <CardDescription>
              Actionable steps to improve your organization's behavioral health
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {report.recommendations.map((recommendation, index) => (
                <li
                  key={index}
                  className="flex items-start text-sm text-blue-900 bg-white p-3 rounded-lg shadow-sm"
                >
                  <span className="font-bold mr-3">{index + 1}.</span>
                  <span className="flex-1">{recommendation}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

interface InsightCardProps {
  insight: BehavioralInsight;
  onClick: () => void;
}

const InsightCard: React.FC<InsightCardProps> = ({ insight, onClick }) => {
  return (
    <Card
      className="hover:shadow-lg transition cursor-pointer border-l-4"
      style={{
        borderLeftColor:
          insight.severity === 'critical'
            ? '#ef4444'
            : insight.severity === 'high'
            ? '#f97316'
            : insight.severity === 'medium'
            ? '#eab308'
            : '#3b82f6'
      }}
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start gap-2">
          <CardTitle className="text-base flex items-center gap-2">
            <span>{CATEGORY_ICONS[insight.category] || '📊'}</span>
            {insight.title}
          </CardTitle>
          <Badge className={SEVERITY_COLORS[insight.severity]}>
            {SEVERITY_ICONS[insight.severity]} {insight.severity.toUpperCase()}
          </Badge>
        </div>
        <CardDescription className="text-xs">
          {new Date(insight.detected_at).toLocaleDateString()} • {insight.affected_employees.length}{' '}
          employees affected • {Math.round(insight.confidence * 100)}% confidence
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-gray-700">{insight.description}</p>

        {/* Data Sources */}
        <div className="flex flex-wrap gap-1">
          {insight.data_sources.map((source) => (
            <Badge key={source} variant="outline" className="text-xs">
              {source.replace('_', ' ')}
            </Badge>
          ))}
        </div>

        {/* Recommendations Preview */}
        {insight.recommendations.length > 0 && (
          <div className="bg-gray-50 p-2 rounded text-xs">
            <strong>Recommended:</strong> {insight.recommendations[0]}
            {insight.recommendations.length > 1 && (
              <span className="text-gray-500">
                {' '}
                +{insight.recommendations.length - 1} more
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default BehavioralInsightsDashboard;
