// src/services/kpiService.ts
// Product KPI analytics service for business intelligence
import api from './api';
import {
  ProductKPIs,
  KPITrend,
  KPIComparison,
  CohortData,
  ConversionFunnel,
  RevenueBreakdown,
} from '../types/analytics';

/**
 * KPI Service - Fetches product and business metrics
 * TODO: Integrate with actual backend endpoints
 */
class KPIService {
  /**
   * Get current KPIs for the dashboard
   */
  async getCurrentKPIs(): Promise<ProductKPIs> {
    // TODO: Replace with actual API call
    // const response = await api.get('/api/v1/analytics/kpi');
    // return response.data;

    // Mock data for now
    return this.getMockKPIs();
  }

  /**
   * Get historical trends for a specific metric
   */
  async getKPITrend(metric: keyof ProductKPIs, period: '7d' | '30d' | '90d' | '12m'): Promise<KPITrend[]> {
    // TODO: Replace with actual API call
    // const response = await api.get(`/api/v1/analytics/kpi/${metric}/trend?period=${period}`);
    // return response.data;

    // Mock trend data
    const days = period === '7d' ? 7 : period === '30d' ? 30 : period === '90d' ? 90 : 12;
    const data: KPITrend[] = [];

    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() - i);

      data.push({
        date: date.toISOString().split('T')[0],
        value: Math.random() * 100 + 50,
      });
    }

    return data.reverse();
  }

  /**
   * Get cohort retention data
   */
  async getCohortData(): Promise<CohortData[]> {
    // TODO: Replace with actual API call
    // const response = await api.get('/api/v1/analytics/cohorts');
    // return response.data;

    // Mock cohort data
    return [
      {
        cohort: 'Jan 2025',
        size: 1250,
        retention: [100, 85, 72, 65, 58, 52, 48, 45],
      },
      {
        cohort: 'Dec 2024',
        size: 1180,
        retention: [100, 87, 74, 68, 61, 55, 51, 48],
      },
      {
        cohort: 'Nov 2024',
        size: 1100,
        retention: [100, 89, 77, 71, 64, 59, 55, 52],
      },
    ];
  }

  /**
   * Get conversion funnel data
   */
  async getConversionFunnel(): Promise<ConversionFunnel> {
    // TODO: Replace with actual API call
    // const response = await api.get('/api/v1/analytics/funnel');
    // return response.data;

    return {
      landingVisitors: 50000,
      signups: 7500,
      firstAssessment: 5200,
      secondAssessment: 3800,
      teamCreation: 1200,
      paidUpgrade: 450,
    };
  }

  /**
   * Get revenue breakdown
   */
  async getRevenueBreakdown(): Promise<RevenueBreakdown> {
    // TODO: Replace with actual API call
    // const response = await api.get('/api/v1/analytics/revenue');
    // return response.data;

    return {
      byTier: {
        free: 0,
        premium: 28500,
        enterprise: 42000,
      },
      byBilling: {
        monthly: 18400,
        annual: 52100,
      },
      byFeature: {
        assessments: 15000,
        teamAnalytics: 25000,
        clinicalTools: 18000,
        integrations: 5000,
        api: 12500,
      },
    };
  }

  /**
   * Get KPI comparison (current vs previous period)
   */
  async getKPIComparison(metric: keyof ProductKPIs): Promise<KPIComparison> {
    const current = await this.getCurrentKPIs();
    const currentValue = current[metric] as number;

    // Mock previous period value (20% difference)
    const previousValue = currentValue * (1 + (Math.random() * 0.4 - 0.2));

    const change = ((currentValue - previousValue) / previousValue) * 100;
    const trend = change > 5 ? 'up' : change < -5 ? 'down' : 'neutral';

    return {
      current: currentValue,
      previous: previousValue,
      change,
      trend,
    };
  }

  /**
   * Mock KPI data for development
   */
  private getMockKPIs(): ProductKPIs {
    return {
      // Acquisition
      trialSignups: 1250,
      trialToPaidRate: 6.8,
      freemiumToPaidRate: 4.2,
      averageTimeToPurchase: 14,

      // Activation
      firstAssessmentCompletion: 71.2,
      timeToFirstValue: 4.8,
      onboardingCompletion: 68.5,

      // Engagement
      monthlyActiveUsers: 12500,
      dailyActiveUsers: 3200,
      assessmentsPerUser: 3.8,
      teamCollaborationRate: 34.2,
      averageSessionDuration: 12.5,
      retentionRateDay30: 68.5,
      retentionRateDay90: 45.2,

      // Revenue
      mrr: 70500,
      arr: 846000,
      arpu: 28.50,
      ltv: 342,
      cac: 85,
      ltvCacRatio: 4.02,
      churnRate: 3.2,

      // Product Health
      featureUsage: {
        clinicalTools: {
          totalUsers: 2800,
          activeUsers: 1100,
          usagePercentage: 39.3,
        },
        personalityAssessments: {
          totalUsers: 9500,
          activeUsers: 6200,
          usagePercentage: 65.3,
        },
        teamAnalytics: {
          totalUsers: 3200,
          activeUsers: 1400,
          usagePercentage: 43.8,
        },
        predictiveAnalytics: {
          totalUsers: 1800,
          activeUsers: 650,
          usagePercentage: 36.1,
        },
        benchmarking: {
          totalUsers: 2200,
          activeUsers: 950,
          usagePercentage: 43.2,
        },
        integrations: {
          slack: 450,
          email: 1200,
          hris: 180,
        },
      },
      assessmentCompletionRates: {
        phq9: 78.5,
        gad7: 82.1,
        bigFive: 71.3,
        mbti: 85.2,
        enneagram: 76.8,
        disc: 74.5,
        overall: 78.1,
      },
      supportTickets: {
        totalTickets: 245,
        openTickets: 38,
        averageResponseTime: 4.2,
        customerSatisfaction: 4.6,
      },

      // Team Metrics
      totalTeams: 890,
      activeTeams: 652,
      averageTeamSize: 8.5,
      teamConversionRate: 12.8,
    };
  }
}

export const kpiService = new KPIService();
