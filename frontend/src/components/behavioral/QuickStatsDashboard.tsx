/**
 * Quick Stats Dashboard Component
 * Displays high-level metrics with trends and comparisons
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

interface QuickStat {
  label: string;
  value: string | number;
  previousValue?: string | number;
  trend: 'up' | 'down' | 'neutral' | 'positive' | 'negative';
  icon: React.ReactNode;
  unit?: string;
  threshold?: {
    warning: number;
    good: number;
  };
}

interface QuickStatsDashboardProps {
  stats: QuickStat[];
  timeRange: string;
}

export const QuickStatsDashboard: React.FC<QuickStatsDashboardProps> = ({ stats, timeRange }) => {
  const formatTrend = (trend: QuickStat['trend'], value: number, previous?: number) => {
    if (!previous) return null;

    const percentChange = ((value - previous) / previous) * 100;
    const isPositive = ['up', 'positive'].includes(trend);

    return (
      <div className={`flex items-center gap-1 text-xs ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {isPositive ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
        <span>{Math.abs(percentChange).toFixed(1)}% vs prev</span>
      </div>
    );
  };

  const getValueColor = (stat: QuickStat) => {
    if (!stat.threshold) return 'text-gray-900';

    const numValue = typeof stat.value === 'number' ? stat.value : parseFloat(stat.value as string);

    if (stat.threshold && numValue >= stat.threshold.good) return 'text-green-600';
    if (stat.threshold && numValue <= stat.threshold.warning) return 'text-red-600';
    return 'text-yellow-600';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {stats.map((stat, index) => (
        <Card key={index} className="hover:shadow-md transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  {stat.icon}
                  <p className="text-sm text-gray-600">{stat.label}</p>
                </div>
                <p className={`text-2xl font-bold ${getValueColor(stat)}`}>
                  {stat.value}
                  {stat.unit && <span className="text-sm text-gray-500 ml-1">{stat.unit}</span>}
                </p>
                {formatTrend(stat.trend, Number(stat.value), stat.previousValue ? Number(stat.previousValue) : undefined)}
              </div>
              <Badge
                variant={stat.trend === 'positive' || stat.trend === 'up' ? 'secondary' :
                        stat.trend === 'negative' || stat.trend === 'down' ? 'destructive' : 'outline'}
                className="ml-2"
              >
                {stat.trend === 'positive' ? 'Good' :
                 stat.trend === 'negative' ? 'Attention' :
                 stat.trend === 'up' ? '↑' :
                 stat.trend === 'down' ? '↓' : '→'}
              </Badge>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};
