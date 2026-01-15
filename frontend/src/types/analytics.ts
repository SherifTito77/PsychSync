// src/types/analytics.ts
// Product KPI types for PsychSync business intelligence

export interface ProductKPIs {
  // Acquisition Metrics
  trialSignups: number;
  trialToPaidRate: number; // Percentage
  freemiumToPaidRate: number; // Percentage
  averageTimeToPurchase: number; // Days

  // Activation Metrics
  firstAssessmentCompletion: number; // Percentage
  timeToFirstValue: number; // Minutes
  onboardingCompletion: number; // Percentage

  // Engagement Metrics
  monthlyActiveUsers: number;
  dailyActiveUsers: number;
  assessmentsPerUser: number;
  teamCollaborationRate: number; // Percentage
  averageSessionDuration: number; // Minutes
  retentionRateDay30: number;
  retentionRateDay90: number;

  // Revenue Metrics
  mrr: number; // Monthly Recurring Revenue
  arr: number; // Annual Recurring Revenue
  arpu: number; // Average Revenue Per User
  ltv: number; // Lifetime Value
  cac: number; // Customer Acquisition Cost
  ltvCacRatio: number;
  churnRate: number; // Monthly churn percentage

  // Product Health
  featureUsage: FeatureUsageMetrics;
  assessmentCompletionRates: AssessmentCompletionRates;
  supportTickets: SupportMetrics;

  // Team Metrics
  totalTeams: number;
  activeTeams: number;
  averageTeamSize: number;
  teamConversionRate: number; // Free teams that upgraded
}

export interface FeatureUsageMetrics {
  clinicalTools: {
    totalUsers: number;
    activeUsers: number;
    usagePercentage: number;
  };
  personalityAssessments: {
    totalUsers: number;
    activeUsers: number;
    usagePercentage: number;
  };
  teamAnalytics: {
    totalUsers: number;
    activeUsers: number;
    usagePercentage: number;
  };
  predictiveAnalytics: {
    totalUsers: number;
    activeUsers: number;
    usagePercentage: number;
  };
  benchmarking: {
    totalUsers: number;
    activeUsers: number;
    usagePercentage: number;
  };
  integrations: {
    slack: number;
    email: number;
    hris: number;
  };
}

export interface AssessmentCompletionRates {
  phq9: number; // Percentage
  gad7: number;
  bigFive: number;
  mbti: number;
  enneagram: number;
  disc: number;
  overall: number;
}

export interface SupportMetrics {
  totalTickets: number;
  openTickets: number;
  averageResponseTime: number; // Hours
  customerSatisfaction: number; // CSAT score 1-5
}

export interface KPITrend {
  date: string;
  value: number;
  label?: string;
}

export interface KPIComparison {
  current: number;
  previous: number;
  change: number; // Percentage change
  trend: 'up' | 'down' | 'neutral';
}

export interface CohortData {
  cohort: string; // Cohort identifier (e.g., "Jan 2025")
  size: number;
  retention: number[]; // Retention rates over time periods
}

export interface FunnelStage {
  stage: string;
  count: number;
  conversionRate: number; // From previous stage
  dropOffRate: number; // Percentage lost
}

export interface ConversionFunnel {
  landingVisitors: number;
  signups: number;
  firstAssessment: number;
  secondAssessment: number;
  teamCreation: number;
  paidUpgrade: number;
}

export interface RevenueBreakdown {
  byTier: {
    free: number;
    premium: number;
    enterprise: number;
  };
  byBilling: {
    monthly: number;
    annual: number;
  };
  byFeature: {
    assessments: number;
    teamAnalytics: number;
    clinicalTools: number;
    integrations: number;
    api: number;
  };
}

// Helper function to calculate trend
export function calculateTrend(current: number, previous: number): 'up' | 'down' | 'neutral' {
  if (current > previous * 1.05) return 'up';
  if (current < previous * 0.95) return 'down';
  return 'neutral';
}

// Helper function to calculate percentage change
export function calculatePercentageChange(current: number, previous: number): number {
  if (previous === 0) return 0;
  return ((current - previous) / previous) * 100;
}

// Helper function to format currency
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

// Helper function to format percentage
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

// Helper function to format number with K/M/B suffixes
export function formatNumber(num: number): string {
  if (num >= 1000000000) {
    return (num / 1000000000).toFixed(1) + 'B';
  }
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}
