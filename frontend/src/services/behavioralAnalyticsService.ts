// Behavioral Analytics Service
// Handles API calls for behavioral pattern recognition and analysis

import { apiClient } from './api';

export interface BehavioralPattern {
  pattern_id: string;
  user_id: string;
  pattern_type: string;
  confidence: number;
  frequency: number;
  first_seen: string;
  last_seen: string;
  contexts: any[];
  metrics: Record<string, number>;
  description: string;
  impact_assessment: string;
}

export interface AnomalyResult {
  anomaly_id: string;
  user_id: string;
  timestamp: string;
  value: number;
  anomaly_score: number;
  method: string;
  category: string;
  severity: string;
  confidence: number;
  context: Record<string, any>;
  baseline_stats: Record<string, number>;
  explanation: string;
}

export interface PatternAnalysisResponse {
  user_id: string;
  analysis_period: {
    start_time: string;
    end_time: string;
    duration_hours: number;
  };
  events_analyzed: number;
  patterns: BehavioralPattern[];
  anomalies: AnomalyResult[];
  insights: Array<{
    type: string;
    title: string;
    description: string;
    confidence: number;
    impact: string;
  }>;
  recommendations: string[];
  behavioral_profile: {
    overview: Record<string, any>;
    patterns_summary: Record<string, number>;
    risk_indicators: Record<string, any>;
    strengths: string[];
    development_areas: string[];
  };
  risk_assessment: {
    risk_score: number;
    risk_level: string;
    risk_factors: Array<{
      type: string;
      description: string;
      severity: string;
    }>;
    recommendation: string;
  };
  data_quality: {
    completeness: number;
    recency: number;
    data_sources: {
      digital_events: number;
      assessments: number;
      wellness_metrics: number;
    };
    overall_quality: number;
  };
}

export interface TeamBehavioralInsights {
  team_overview: {
    team_id: number;
    team_name: string;
    team_size: number;
    analysis_date: string;
    data_confidence: number;
  };
  behavioral_metrics: {
    team_cohesion: number;
    communication_effectiveness: number;
    collaboration_quality: number;
    psychological_safety: number;
    innovation_potential: number;
    conflict_resolution: number;
  };
  business_impact: {
    productivity: Record<string, any>;
    retention: Record<string, any>;
    innovation: Record<string, any>;
    total_monthly_value: number;
  };
  team_composition: {
    personality_diversity: Record<string, any>;
    role_alignment: Record<string, any>;
    strength_distribution: Record<string, any>;
    risk_factors: any[];
  };
  recommendations: any[];
  predictions: any;
  benchmarks: any;
}

class BehavioralAnalyticsService {
  // Individual Pattern Analysis
  async analyzeUserPatterns(
    userId: string,
    timePeriod: string = '30d',
    behavioralCategories?: string[]
  ): Promise<PatternAnalysisResponse> {
    try {
      const response = await apiClient.post(
        '/patterns/analyze',
        {
          analysis_scope: 'individual',
          user_id: userId,
          time_period: timePeriod,
          behavioral_categories: behavioralCategories || ['temporal', 'sequential', 'social'],
          analysis_options: {}
        }
      );

      return response.data;
    } catch (error) {
      console.error('Error analyzing user patterns:', error);
      throw error;
    }
  }

  // Anomaly Detection
  async detectAnomalies(
    userId: string,
    metricName: string = 'activity_score',
    timePeriodDays: number = 30,
    thresholdStdDev: number = 2.5
  ): Promise<{ anomalies: AnomalyResult[]; method_used: string; data_points_analyzed: number }> {
    try {
      const response = await apiClient.post('/anomalies/detect', {
        entity_id: userId,
        entity_type: 'user',
        metric_name: metricName,
        time_period_days: timePeriodDays,
        threshold_std_dev: thresholdStdDev
      });

      return response.data;
    } catch (error) {
      console.error('Error detecting anomalies:', error);
      throw error;
    }
  }

  // Pattern Matching
  async matchPatterns(
    userData: Record<string, any>,
    templateIds?: string[],
    algorithms?: string[],
    userId?: string
  ): Promise<{ matches: any[]; total_matches: number }> {
    try {
      const response = await apiClient.post('/behavioral-patterns/match-patterns', {
        user_data: userData,
        template_ids: templateIds,
        algorithms: algorithms,
        user_id: userId,
      });

      return response.data;
    } catch (error) {
      console.error('Error matching patterns:', error);
      throw error;
    }
  }

  // User Comparison
  async compareUsers(
    userIds: string[],
    timeRange: string = '30d',
    metrics?: string[]
  ): Promise<{
    comparison_data: any[];
    similarity_matrix: number[][];
    insights: any[];
    recommendations: string[];
  }> {
    try {
      const params = new URLSearchParams({ time_range: timeRange });
      if (metrics && metrics.length > 0) {
        metrics.forEach(metric => params.append('metrics', metric));
      }

      const response = await apiClient.post(
        `/behavioral-patterns/compare?${params}`,
        { user_ids: userIds }
      );

      return response.data;
    } catch (error) {
      console.error('Error comparing users:', error);
      throw error;
    }
  }

  // Get User Insights
  async getUserInsights(
    userId: string,
    timeRange: string = '30d'
  ): Promise<{
    user_id: string;
    time_range: string;
    insights: any[];
    recommendations: string[];
    risk_assessment: any;
    behavioral_profile: any;
  }> {
    try {
      const response = await apiClient.get(
        `/behavioral-patterns/insights/${userId}?time_range=${timeRange}`
      );

      return response.data;
    } catch (error) {
      console.error('Error getting user insights:', error);
      throw error;
    }
  }

  // Team Behavioral Insights
  async getTeamBehavioralInsights(
    teamId: number,
    timePeriod: string = '30d',
    includePredictions: boolean = true
  ): Promise<TeamBehavioralInsights> {
    try {
      const params = new URLSearchParams({
        time_period: timePeriod,
        include_predictions: includePredictions.toString(),
      });

      const response = await apiClient.post(
        `/team/insights?${params}`,
        { team_id: teamId }
      );

      return response.data;
    } catch (error) {
      console.error('Error getting team insights:', error);
      throw error;
    }
  }

  // HR Outcomes Metrics
  async getHROutcomesMetrics(
    organizationId: number,
    timePeriod: string = '90d',
    outcomeTypes: string[] = ['all']
  ): Promise<{
    organization_id: number;
    analysis_period: string;
    hr_outcomes: Record<string, any>;
    roi_analysis: Record<string, any>;
    executive_summary: any;
    recommendations: string[];
    forecast_trends: any;
  }> {
    try {
      const params = new URLSearchParams({ time_period: timePeriod });
      outcomeTypes.forEach(type => params.append('outcome_types', type));

      const response = await apiClient.get(
        `/behavioral-analytics/hr-outcomes/${organizationId}?${params}`
      );

      return response.data;
    } catch (error) {
      console.error('Error getting HR outcomes:', error);
      throw error;
    }
  }

  // Turnover Risk Analysis
  async getTurnoverRiskAnalysis(
    organizationId: number,
    includeInterventions: boolean = true,
    riskThreshold: number = 0.7
  ): Promise<{
    organization_id: number;
    risk_overview: {
      total_employees_analyzed: number;
      high_risk_count: number;
      average_risk_score: number;
      risk_trend: string;
    };
    high_risk_employees: any[];
    financial_impact: Record<string, any>;
    risk_factors: any;
    interventions?: any;
    success_metrics: Record<string, any>;
  }> {
    try {
      const params = new URLSearchParams({
        include_interventions: includeInterventions.toString(),
        risk_threshold: riskThreshold.toString(),
      });

      const response = await apiClient.get(
        `/behavioral-analytics/turnover-risk/${organizationId}?${params}`
      );

      return response.data;
    } catch (error) {
      console.error('Error getting turnover risk analysis:', error);
      throw error;
    }
  }

  // Pattern Templates
  async getPatternTemplates(): Promise<{
    templates: any[];
    total_templates: number;
  }> {
    try {
      const response = await apiClient.get('/patterns/catalog');
      return response.data;
    } catch (error) {
      console.error('Error getting pattern templates:', error);
      throw error;
    }
  }

  // Pattern Metrics Summary (Admin)
  async getPatternMetricsSummary(
    organizationId?: string,
    timeRange: string = '30d'
  ): Promise<{
    total_users_analyzed: number;
    total_patterns_detected: number;
    total_anomalies_detected: number;
    pattern_types_distribution: Record<string, number>;
    risk_levels_distribution: Record<string, number>;
    average_patterns_per_user: number;
    average_anomalies_per_user: number;
    most_common_patterns: any[];
    top_anomalies: any[];
  }> {
    try {
      const params = new URLSearchParams({ time_range: timeRange });
      if (organizationId) {
        params.append('organization_id', organizationId);
      }

      const response = await apiClient.get(
        `/behavioral-patterns/metrics/summary?${params}`
      );

      return response.data;
    } catch (error) {
      console.error('Error getting pattern metrics summary:', error);
      throw error;
    }
  }

  // Mental Health Assessment Integration
  async getMentalHealthInsights(userId: string): Promise<{
    recent_assessments: any[];
    risk_indicators: {
      depression_risk: string;
      anxiety_risk: string;
      stress_level: string;
      overall_risk: string;
    };
    recommendations: string[];
    wellness_trends: {
      mood_trend: string;
      energy_levels: string;
      sleep_quality: string;
      social_engagement: string;
    };
  }> {
    try {
      // This would integrate with clinical assessment endpoints
      const response = await apiClient.get(`/assessments/user/${userId}/mental-health-summary`);
      return response.data;
    } catch (error) {
      console.error('Error getting mental health insights:', error);
      throw error;
    }
  }

  // Wellness Data Integration
  async getWellnessMetrics(userId: string, timeRange: string = '30d'): Promise<{
    overall_wellness_score: number;
    burnout_risk_score: number;
    stress_level: number;
    engagement_level: number;
    physical_wellness: number;
    emotional_wellness: number;
    mental_wellness: number;
    social_wellness: number;
    professional_wellness: number;
    trends: {
      improving: string[];
      declining: string[];
      stable: string[];
    };
  }> {
    try {
      const response = await apiClient.get(
        `/wellness/metrics/${userId}?time_range=${timeRange}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting wellness metrics:', error);
      throw error;
    }
  }

  // Quick Stats
  async getQuickStats(userId: string, timeRange: string = '30d'): Promise<{
    assessmentsCompleted: number;
    assessmentsChange: number;
    wellnessScore: number;
    wellnessChange: number;
    riskFactorsDetected: number;
    riskFactorsChange: number;
    goalsAchieved: number;
    goalsCompletionRate: number;
    streakDays: number;
  }> {
    try {
      const response = await apiClient.get(`/behavioral/quick-stats/${userId}?time_range=${timeRange}`);
      return response.data;
    } catch (error) {
      console.error('Error getting quick stats:', error);
      // Return default values on error
      return {
        assessmentsCompleted: 0,
        assessmentsChange: 0,
        wellnessScore: 0,
        wellnessChange: 0,
        riskFactorsDetected: 0,
        riskFactorsChange: 0,
        goalsAchieved: 0,
        goalsCompletionRate: 0,
        streakDays: 0
      };
    }
  }

  // Comparison Data
  async getComparisonData(userId: string, timeRange: string = '30d'): Promise<{
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
  }> {
    try {
      const response = await apiClient.get(`/behavioral/comparison/${userId}?time_range=${timeRange}`);
      return response.data;
    } catch (error) {
      console.error('Error getting comparison data:', error);
      throw error;
    }
  }

  // Alerts & Notifications
  async getAlerts(userId: string): Promise<{
    warnings: Array<{
      id: string;
      type: 'warning';
      title: string;
      message: string;
      severity: 'low' | 'medium' | 'high';
      actionLabel?: string;
      actionLink?: string;
      timestamp: string;
      dismissible: boolean;
    }>;
    achievements: Array<{
      id: string;
      type: 'achievement';
      title: string;
      message: string;
      timestamp: string;
    }>;
    tips: Array<{
      id: string;
      type: 'info';
      title: string;
      message: string;
      timestamp: string;
    }>;
  }> {
    try {
      const response = await apiClient.get(`/behavioral/alerts/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error getting alerts:', error);
      throw error;
    }
  }

  async getRecommendations(userId: string): Promise<{
    recommendations: Array<{
      id: string;
      title: string;
      description: string;
      category: 'immediate' | 'short-term' | 'long-term';
      priority: 'critical' | 'high' | 'medium' | 'low';
      impactScore: number;
      effortLevel: 'low' | 'medium' | 'high';
      estimatedTime: string;
      actionSteps: string[];
      status: 'pending' | 'in-progress' | 'completed' | 'dismissed';
    }>;
  }> {
    try {
      const response = await apiClient.get(`/behavioral/recommendations/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error getting recommendations:', error);
      throw error;
    }
  }

  // Goals
  async getGoals(userId: string): Promise<{
    goals: Array<{
      id: string;
      title: string;
      description: string;
      category: 'wellness' | 'mental-health' | 'performance' | 'habits';
      targetValue: number;
      currentValue: number;
      unit: string;
      deadline: string;
      streak: number;
      status: 'on-track' | 'behind' | 'completed' | 'not-started';
    }>;
  }> {
    try {
      const response = await apiClient.get(`/behavioral/goals/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error getting goals:', error);
      throw error;
    }
  }

  async updateGoalProgress(goalId: string, progress: number): Promise<void> {
    try {
      await apiClient.put(`/behavioral/goals/${goalId}`, { progress });
    } catch (error) {
      console.error('Error updating goal:', error);
      throw error;
    }
  }

  async createGoal(goal: {
    title: string;
    description: string;
    category: string;
    targetValue: number;
    unit: string;
    deadline: string;
  }): Promise<void> {
    try {
      await apiClient.post('/behavioral/goals', goal);
    } catch (error) {
      console.error('Error creating goal:', error);
      throw error;
    }
  }

  // Export functionality
  async exportReport(format: string, options: {
    sections: string[];
    includeCharts: boolean;
    timestamp: string;
  }): Promise<Blob> {
    try {
      const response = await apiClient.post('/behavioral/export', {
        format,
        ...options
      }, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('Error exporting report:', error);
      throw error;
    }
  }

  async generateShareLink(options: {
    expiresIn: string;
    allowDownload: boolean;
  }): Promise<{ shareLink: string; expiresAt: string }> {
    try {
      const response = await apiClient.post('/behavioral/share', options);
      return response.data;
    } catch (error) {
      console.error('Error generating share link:', error);
      throw error;
    }
  }

  async scheduleEmailReport(options: {
    schedule: string;
    sections: string[];
  }): Promise<void> {
    try {
      await apiClient.post('/behavioral/schedule-report', options);
    } catch (error) {
      console.error('Error scheduling report:', error);
      throw error;
    }
  }

  // Trend Forecasts
  async getTrendForecasts(userId: string): Promise<{
    wellnessForecast: {
      current: number;
      predicted7Days: number;
      predicted30Days: number;
      predicted90Days: number;
      trend: 'improving' | 'stable' | 'declining';
    };
    burnoutRiskForecast: {
      current: number;
      predicted7Days: number;
      predicted30Days: number;
      riskLevel: 'low' | 'medium' | 'high';
    };
    confidence: number;
  }> {
    try {
      const response = await apiClient.get(`/behavioral/forecasts/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error getting forecasts:', error);
      throw error;
    }
  }
}

export const behavioralAnalyticsService = new BehavioralAnalyticsService();
export default behavioralAnalyticsService;
