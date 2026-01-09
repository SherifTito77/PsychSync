/**
 * Predictive Analytics Dashboard - Chart Helper Utilities
 */

import { EmployeeRisk } from '../types';

/**
 * Get color for risk level
 */
export const getRiskColor = (riskLevel: EmployeeRisk['riskLevel']): string => {
  switch (riskLevel) {
    case 'critical': return 'bg-red-500';
    case 'high': return 'bg-orange-500';
    case 'medium': return 'bg-yellow-500';
    case 'low': return 'bg-green-500';
    default: return 'bg-gray-500';
  }
};

/**
 * Get risk level text color
 */
export const getRiskTextColor = (riskLevel: EmployeeRisk['riskLevel']): string => {
  switch (riskLevel) {
    case 'critical': return 'text-red-600';
    case 'high': return 'text-orange-600';
    case 'medium': return 'text-yellow-600';
    case 'low': return 'text-green-600';
    default: return 'text-gray-600';
  }
};

/**
 * Chart colors for consistent theming
 */
export const CHART_COLORS = {
  primary: '#8b5cf6', // purple
  secondary: '#3b82f6', // blue
  success: '#10b981', // green
  warning: '#f59e0b', // yellow
  danger: '#ef4444', // red
  info: '#6366f1', // indigo
};

/**
 * Format percentage
 */
export const formatPercentage = (value: number): string => {
  return `${Math.round(value)}%`;
};

/**
 * Format decimal as percentage
 */
export const formatDecimalAsPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * Prepare prediction chart data
 */
export const preparePredictionChartData = (data: any[]) => {
  return data.map(item => ({
    ...item,
    actual: item.actual ?? null,
    upperBound: item.predicted * (1 + (1 - item.confidence)),
    lowerBound: item.predicted * (1 - (1 - item.confidence))
  }));
};

/**
 * Get trend direction
 */
export const getTrendDirection = (current: number, previous: number): 'up' | 'down' | 'neutral' => {
  const threshold = 0.02; // 2% threshold for neutral
  const change = (current - previous) / previous;

  if (Math.abs(change) < threshold) return 'neutral';
  return change > 0 ? 'up' : 'down';
};
