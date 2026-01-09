/**
 * Predictive Analytics Dashboard - Type Definitions
 */

export interface OrganizationalMetrics {
  overallScore: number;
  engagementScore: number;
  performanceScore: number;
  retentionRisk: number;
  growthPotential: number;
}

export interface PredictionData {
  period: string;
  actual: number;
  predicted: number;
  confidence: number;
}

export interface TrendData {
  month: string;
  value: number;
  benchmark: number;
}

export interface EmployeeRisk {
  employeeId: string;
  name: string;
  department: string;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  riskFactors: string[];
  probability: number;
  timeframe: string;
}

export interface InterventionImpact {
  intervention: string;
  baseline: number;
  projected: number;
  actual: number;
  confidence: number;
}

export type TimeRange = '3m' | '6m' | '1y' | '2y';
export type ChartType = 'line' | 'bar' | 'area' | 'radar' | 'scatter' | 'pie';
export type PredictionModel = 'linear' | 'exponential' | 'polynomial' | 'lstm';
