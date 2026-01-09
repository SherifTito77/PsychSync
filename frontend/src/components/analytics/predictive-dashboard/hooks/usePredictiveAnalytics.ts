/**
 * Predictive Analytics Dashboard - Main Data Management Hook
 */

import { useState, useEffect } from 'react';
import {
  OrganizationalMetrics,
  PredictionData,
  TrendData,
  EmployeeRisk,
  InterventionImpact,
  TimeRange
} from '../types';

/**
 * Mock data generators
 */
const mockOrganizationalMetrics = (): OrganizationalMetrics => ({
  overallScore: 87,
  engagementScore: 82,
  performanceScore: 89,
  retentionRisk: 15,
  growthPotential: 78
});

const mockPredictionData = (): PredictionData[] => [
  { period: 'Jan', actual: 65, predicted: 63, confidence: 0.85 },
  { period: 'Feb', actual: 70, predicted: 68, confidence: 0.87 },
  { period: 'Mar', actual: 75, predicted: 73, confidence: 0.89 },
  { period: 'Apr', actual: 78, predicted: 76, confidence: 0.88 },
  { period: 'May', actual: 82, predicted: 80, confidence: 0.86 },
  { period: 'Jun', actual: null, predicted: 84, confidence: 0.84 },
  { period: 'Jul', actual: null, predicted: 87, confidence: 0.82 },
  { period: 'Aug', actual: null, predicted: 90, confidence: 0.80 }
];

const mockTrendData = (): TrendData[] => [
  { month: 'Jan', value: 65, benchmark: 70 },
  { month: 'Feb', value: 70, benchmark: 72 },
  { month: 'Mar', value: 75, benchmark: 74 },
  { month: 'Apr', value: 78, benchmark: 76 },
  { month: 'May', value: 82, benchmark: 78 },
  { month: 'Jun', value: 85, benchmark: 80 }
];

const mockEmployeeRisks = (): EmployeeRisk[] => [
  {
    employeeId: '1',
    name: 'John Smith',
    department: 'Engineering',
    riskLevel: 'medium',
    riskFactors: ['Decreased engagement', 'Missed deadlines'],
    probability: 0.65,
    timeframe: '3-6 months'
  },
  {
    employeeId: '2',
    name: 'Jane Doe',
    department: 'Sales',
    riskLevel: 'low',
    riskFactors: ['New hire'],
    probability: 0.20,
    timeframe: '6-12 months'
  }
];

const mockInterventionImpacts = (): InterventionImpact[] => [
  {
    intervention: 'Training Program',
    baseline: 65,
    projected: 80,
    actual: 78,
    confidence: 0.85
  },
  {
    intervention: 'Mentorship',
    baseline: 70,
    projected: 85,
    actual: null,
    confidence: 0.75
  }
];

/**
 * Main hook for predictive analytics data management
 */
export const usePredictiveAnalytics = () => {
  const [metrics, setMetrics] = useState<OrganizationalMetrics | null>(null);
  const [predictionData, setPredictionData] = useState<PredictionData[]>([]);
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [employeeRisks, setEmployeeRisks] = useState<EmployeeRisk[]>([]);
  const [interventionImpacts, setInterventionImpacts] = useState<InterventionImpact[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState<TimeRange>('6m');
  const [selectedModel, setSelectedModel] = useState<'linear' | 'exponential' | 'polynomial'>('linear');

  /**
   * Load all analytics data
   */
  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      const [
        metricsData,
        predictionsData,
        trendsData,
        risksData,
        interventionsData
      ] = await Promise.all([
        mockOrganizationalMetrics(),
        mockPredictionData(),
        mockTrendData(),
        mockEmployeeRisks(),
        mockInterventionImpacts()
      ]);

      setMetrics(metricsData);
      setPredictionData(predictionsData);
      setTrendData(trendsData);
      setEmployeeRisks(risksData);
      setInterventionImpacts(interventionsData);
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Refresh data
   */
  const refreshData = () => {
    loadAnalyticsData();
  };

  /**
   * Get high-risk employees
   */
  const getHighRiskEmployees = () => {
    return employeeRisks.filter(e => e.riskLevel === 'high' || e.riskLevel === 'critical');
  };

  /**
   * Get average confidence score
   */
  const getAverageConfidence = () => {
    if (predictionData.length === 0) return 0;
    const sum = predictionData.reduce((acc, p) => acc + p.confidence, 0);
    return (sum / predictionData.length) * 100;
  };

  /**
   * Filter data by time range
   */
  const getDataByTimeRange = <T,>(data: T[], maxItems?: number): T[] => {
    const itemCount = maxItems || (selectedTimeRange === '3m' ? 3 : selectedTimeRange === '6m' ? 6 : selectedTimeRange === '1y' ? 12 : 24);
    return data.slice(0, itemCount);
  };

  // Load data on mount and time range change
  useEffect(() => {
    loadAnalyticsData();
  }, [selectedTimeRange, selectedModel]);

  return {
    // State
    metrics,
    predictionData,
    trendData,
    employeeRisks,
    interventionImpacts,
    loading,
    selectedTimeRange,
    selectedModel,

    // Actions
    setSelectedTimeRange,
    setSelectedModel,
    refreshData,

    // Computed
    highRiskEmployees: getHighRiskEmployees(),
    averageConfidence: getAverageConfidence(),
    filteredPredictionData: getDataByTimeRange(predictionData),
    filteredTrendData: getDataByTimeRange(trendData),
  };
};
