/**
 * Health Monitoring & Intervention Types
 *
 * Type definitions for health monitoring, stress analysis,
 * burnout detection, and intervention management
 */

// ============================================================================
// Health Risk Analysis Types
// ============================================================================

export type StressLevel = 'normal' | 'elevated' | 'high' | 'critical';

export type BurnoutStage = 'none' | 'early_warning' | 'moderate' | 'severe' | 'critical';

export interface HealthRiskData {
  analysis_date: string;
  user_id: string;
  time_window_days: number;

  // Risk scores (0-1 scale)
  stress_level: StressLevel;
  burnout_stage: BurnoutStage;
  cardiovascular_risk_score: number;
  mental_health_risk: number;
  work_life_imbalance: number;
  sleep_disruption_score: number;
  social_isolation_score: number;

  // Intervention flags
  urgent_intervention_needed: boolean;
  recommend_medical_evaluation: boolean;
  recommend_immediate_break: boolean;
  recommend_workload_reduction: boolean;

  // Details
  primary_risk_factors: string[];
  warning_signs: string[];
  protective_factors: string[];

  // Data quality
  data_sources: string[];
  confidence_level: number;

  // Recommendations
  recommended_actions: string[];
}

export interface BiometricData {
  data_source: string;
  measurement_date: string;

  // Cardiovascular
  resting_heart_rate?: number;
  heart_rate_variability?: number;
  avg_heart_rate?: number;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;

  // Respiratory
  oxygen_saturation?: number;

  // Sleep
  sleep_hours?: number;
  sleep_quality_score?: number;
  deep_sleep_hours?: number;
  rem_sleep_hours?: number;

  // Activity
  steps_count?: number;
  activity_minutes?: number;
  sedentary_minutes?: number;

  device_info?: Record<string, any>;
}

// ============================================================================
// Intervention Types
// ============================================================================

export type InterventionType =
  | 'stress_management'
  | 'burnout_prevention'
  | 'sleep_hygiene'
  | 'workload_adjustment'
  | 'mental_health_support'
  | 'physical_wellness'
  | 'social_connection'
  | 'crisis_intervention';

export type InterventionUrgency = 'low' | 'medium' | 'high' | 'critical';

export interface Intervention {
  intervention_id: string;
  intervention_type: InterventionType;
  urgency: InterventionUrgency;
  title: string;
  message: string;
  actions_required: string[];
  notify_user: boolean;
  notify_manager: boolean;
  notify_hr: boolean;
  resources: InterventionResource[];
  follow_up_required: boolean;
  follow_up_days: number;
  created_at: string;
}

export interface InterventionResource {
  title: string;
  url: string;
  type: 'article' | 'video' | 'exercise' | 'crisis' | 'tool';
}

export interface InterventionCreateRequest {
  health_risks: Partial<HealthRiskData>;
  work_patterns: Record<string, any>;
}

// ============================================================================
// Health Report Types
// ============================================================================

export interface HealthReport {
  user_id: string;
  report_date: string;
  time_period_days: number;
  current_health_status: {
    stress_level: StressLevel;
    burnout_stage: BurnoutStage;
    cardiovascular_risk: number;
    mental_health_risk: number;
  };
  risk_factors: string[];
  warning_signs: string[];
  protective_factors: string[];
  data_sources_analyzed: string[];
  confidence_level: number;
  needs_attention: boolean;
  recommendations: string[];
}

// ============================================================================
// Manager Dashboard Types
// ============================================================================

export interface StressDistribution {
  normal: number;
  elevated: number;
  high: number;
  critical: number;
}

export interface CardiovascularRiskDistribution {
  low: number;
  medium: number;
  high: number;
}

export interface WeeklyStressTrend {
  week: string;
  avg_stress: number;
}

export interface ManagerDashboardData {
  team_id: string;
  team_name: string;
  analysis_date: string;
  total_team_members: number;
  members_analyzed: number;

  // Aggregate metrics (anonymized)
  average_stress_level: number;
  stress_distribution: StressDistribution;

  high_risk_members_count: number; // Count only, no identities
  critical_interventions_active: number;

  // Trends
  weekly_stress_trend: WeeklyStressTrend[];
  cardiovascular_risk_distribution: CardiovascularRiskDistribution;

  // Action items (anonymized)
  recommended_team_actions: string[];
  organizational_risk_factors: string[];
}

// ============================================================================
// Consent Types
// ============================================================================

export interface HealthDataConsent {
  consent_given: boolean;
  consent_date?: string;
  biometric_collection: boolean;
  biometric_processing: boolean;
  biometric_sharing: boolean;
  data_sources: string[];
  data_retention_days: number;
}

export interface ConsentUpdateRequest {
  biometric_collection: boolean;
  biometric_processing: boolean;
  biometric_sharing: boolean;
  data_sources?: string[];
  data_retention_days: number;
}

// ============================================================================
// Intervention Effectiveness Types
// ============================================================================

export type InterventionStatus = 'planned' | 'active' | 'completed' | 'cancelled' | 'paused';
export type InterventionPriority = 'low' | 'medium' | 'high' | 'critical';

export interface InterventionProgram {
  id: string;
  organization_id: string;
  team_id?: string;
  created_by: string;
  title: string;
  description?: string;
  intervention_type: string;
  category: string;
  target_metrics?: string[];
  expected_outcomes?: string[];
  success_criteria?: Record<string, any>;
  start_date: string;
  end_date?: string;
  duration_days?: number;
  status: InterventionStatus;
  priority: InterventionPriority;
  budget?: number;
  participants_target?: number;
  actual_participants?: number;
  completion_rate?: number;
  implementation_details?: Record<string, any>;
  external_references?: string[];
  tags?: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InterventionParticipant {
  id: string;
  user_id: string;
  participant_role: 'participant' | 'facilitator' | 'observer';
  enrollment_date: string;
  completion_status: string;
  engagement_score?: number;
  attendance_rate?: number;
}

export interface Measurement {
  id: string;
  intervention_id: string;
  user_id: string;
  metric_name: string;
  metric_value: number;
  metric_type: string;
  measurement_date: string;
  measurement_method?: string;
  data_source?: string;
  confidence_level?: number;
  sample_size?: number;
  qualitative_notes?: string;
  created_at: string;
}

export interface EffectivenessResult {
  intervention_id: string;
  metric_name: string;
  effect_size: number;
  confidence_interval?: number[];
  p_value?: number;
  statistical_significance?: boolean;
  test_type: string;
  sample_size_pre?: number;
  sample_size_post?: number;
  pre_intervention_mean?: number;
  post_intervention_mean?: number;
  percent_improvement?: number;
  clinical_significance?: string;
  practical_significance?: boolean;
  effect_category: string;
  recommendations?: string;
  created_at: string;
}

export interface AnalysisSummary {
  intervention_id: string;
  analysis_date: string;
  total_metrics: number;
  significant_metrics: number;
  average_effect_size: number;
  statistical_power: number;
  bayesian_evidence: {
    strong: number;
    moderate: number;
    weak: number;
  };
  overall_recommendation: string;
  confidence_score: number;
  limitations: string[];
}

// ============================================================================
// Real-time Monitoring Types
// ============================================================================

export interface HealthAlert {
  id: string;
  user_id: string;
  alert_type: 'stress_spike' | 'burnout_detected' | 'critical_health' | 'biometric_anomaly';
  severity: InterventionUrgency;
  message: string;
  timestamp: string;
  acknowledged: boolean;
}

export interface RealTimeHealthUpdate {
  user_id: string;
  timestamp: string;
  stress_level?: StressLevel;
  heart_rate?: number;
  sleep_hours?: number;
  activity_minutes?: number;
}

// ============================================================================
// API Response Wrappers
// ============================================================================

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  limit: number;
}
