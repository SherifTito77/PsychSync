/**
 * Comparison View Component
 * Displays period-over-period comparisons and peer benchmarking
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { TrendingUp, TrendingDown, Users, Target } from 'lucide-react';

interface ComparisonViewProps {
  metrics: {
    currentPeriod: {
      wellnessScore: number;
      engagementScore: number;
      productivityScore: number;
    };
    previousPeriod: {
      wellnessScore: number;
      engagementScore: number;
      productivityScore: number;
    };
    peerAverage: {
      wellnessScore: number;
      engagementScore: number;
      productivityScore: number;
    };
    percentileRankings: {
      wellness: number;
      engagement: number;
      productivity: number;
    };
  };
  timeRange: string;
}

export const ComparisonView: React.FC<ComparisonViewProps> = ({ metrics, timeRange }) => {
  const comparisonData = [
    {
      label: 'Wellness Score',
      currentValue: metrics.currentPeriod.wellnessScore,
      previousValue: metrics.previousPeriod.wellnessScore,
      peerAverage: metrics.peerAverage.wellnessScore,
      topPercentile: metrics.percentileRankings.wellness,
      format: 'percentage' as const,
      higherIsBetter: true
    },
    {
      label: 'Engagement Score',
      currentValue: metrics.currentPeriod.engagementScore,
      previousValue: metrics.previousPeriod.engagementScore,
      peerAverage: metrics.peerAverage.engagementScore,
      topPercentile: metrics.percentileRankings.engagement,
      format: 'percentage' as const,
      higherIsBetter: true
    },
    {
      label: 'Productivity Score',
      currentValue: metrics.currentPeriod.productivityScore,
      previousValue: metrics.previousPeriod.productivityScore,
      peerAverage: metrics.peerAverage.productivityScore,
      topPercentile: metrics.percentileRankings.productivity,
      format: 'percentage' as const,
      higherIsBetter: true
    }
  ];

  const formatValue = (value: number, format?: string) => {
    switch (format) {
      case 'percentage': return `${(value * 100).toFixed(1)}%`;
      case 'score': return value.toFixed(1);
      default: return value.toString();
    }
  };

  const getChangeIndicator = (current: number, previous: number, higherIsBetter = true) => {
    const change = current - previous;
    const changePercent = ((change / previous) * 100);

    if (Math.abs(changePercent) < 5) {
      return <span className="text-gray-500 text-sm">→ Stable</span>;
    }

    const isImprovement = higherIsBetter ? change > 0 : change < 0;

    return (
      <div className={`flex items-center gap-1 text-sm ${isImprovement ? 'text-green-600' : 'text-red-600'}`}>
        {isImprovement ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
        <span>{changePercent > 0 ? '+' : ''}{changePercent.toFixed(1)}%</span>
      </div>
    );
  };

  const getPeerComparisonColor = (current: number, peerAverage: number, higherIsBetter = true) => {
    const diff = current - peerAverage;
    if (Math.abs(diff) < 0.05) return 'text-yellow-600'; // Within 5% = yellow
    if (higherIsBetter ? current > peerAverage : current < peerAverage) return 'text-green-600';
    return 'text-red-600';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5 text-blue-600" />
          Performance Comparison
          <Badge variant="outline" className="ml-2">{timeRange}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {comparisonData.map((metric, index) => (
            <div key={index} className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold">{metric.label}</h4>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-2xl font-bold">
                      {formatValue(metric.currentValue, metric.format)}
                    </span>
                    {getChangeIndicator(metric.currentValue, metric.previousValue, metric.higherIsBetter)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Users className="h-4 w-4" />
                    <span>Peer avg: {formatValue(metric.peerAverage, metric.format)}</span>
                  </div>
                  <div className={`text-sm font-semibold mt-1 ${getPeerComparisonColor(metric.currentValue, metric.peerAverage, metric.higherIsBetter)}`}>
                    Top {metric.topPercentile}th percentile
                  </div>
                </div>
              </div>

              {/* Progress bars showing comparison */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <span className="w-16">You</span>
                  <Progress
                    value={Math.min(metric.currentValue * 100, 100)}
                    className="flex-1 h-2"
                  />
                  <span className="w-16 text-right">{formatValue(metric.currentValue, metric.format)}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <span className="w-16">Peers</span>
                  <Progress
                    value={Math.min(metric.peerAverage * 100, 100)}
                    className="flex-1 h-2 bg-gray-200"
                  />
                  <span className="w-16 text-right">{formatValue(metric.peerAverage, metric.format)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Insight Box */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start gap-3">
            <Target className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h5 className="font-semibold text-blue-900 mb-1">Performance Insight</h5>
              <p className="text-sm text-blue-700">
                {comparisonData.filter(m => {
                  const diff = m.currentValue - m.peerAverage;
                  return m.higherIsBetter ? diff > 0 : diff < 0;
                }).length > comparisonData.length / 2
                  ? "You're performing above average in most metrics. Keep up the great work!"
                  : "There's room for improvement. Focus on metrics where you're below peer average."
                }
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
