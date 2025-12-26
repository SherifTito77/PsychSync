// Behavioral Analytics Service
// Handles API calls for behavioral pattern recognition and analysis

import { apiClient } from './authService';

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
    timeWindowHours: number = 168,
    patternTypes?: string[],
    includeAnomalies: boolean = true
  ): Promise<PatternAnalysisResponse> {
    try {
      const params = new URLSearchParams({
        time_window_hours: timeWindowHours.toString(),
        include_anomalies: includeAnomalies.toString(),
      });

      if (patternTypes && patternTypes.length > 0) {
        patternTypes.forEach(type => params.append('pattern_types', type));
      }

      const response = await apiClient.post(
        `/api/v1/behavioral-patterns/analyze?${params}`,
        { user_id: userId }
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
    data?: number[],
    method: string = 'ensemble',
    sensitivity: number = 0.1
  ): Promise<{ anomalies: AnomalyResult[]; method_used: string; data_points_analyzed: number }> {
    try {
      const response = await apiClient.post('/api/v1/behavioral-patterns/detect-anomalies', {
        user_id: userId,
        data,
        method,
        sensitivity,
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
      const response = await apiClient.post('/api/v1/behavioral-patterns/match-patterns', {
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
        `/api/v1/behavioral-patterns/compare?${params}`,
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
        `/api/v1/behavioral-patterns/insights/${userId}?time_range=${timeRange}`
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

      const response = await apiClient.get(
        `/api/v1/behavioral-analytics/team-insights/${teamId}?${params}`
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
        `/api/v1/behavioral-analytics/hr-outcomes/${organizationId}?${params}`
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
        `/api/v1/behavioral-analytics/turnover-risk/${organizationId}?${params}`
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
      const response = await apiClient.get('/api/v1/behavioral-patterns/templates');
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
        `/api/v1/behavioral-patterns/metrics/summary?${params}`
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
      const response = await apiClient.get(`/api/v1/assessments/user/${userId}/mental-health-summary`);
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
        `/api/v1/wellness/metrics/${userId}?time_range=${timeRange}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting wellness metrics:', error);
      throw error;
    }
  }
}

export const behavioralAnalyticsService = new BehavioralAnalyticsService();
export default behavioralAnalyticsService;