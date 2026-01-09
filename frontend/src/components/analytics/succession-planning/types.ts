/**
 * Succession Planning Types
 *
 * Type definitions for HR succession planning
 */

export interface PipelineAnalysis {
  pipeline_level: string;
  total_positions: number;
  ready_candidates: number;
  gap_percentage: number;
  bench_strength: number;
  risk_level: string;
  development_recommendations: string[];
}

export interface SuccessionCandidate {
  candidate: {
    user_id: string;
    current_role: string;
    readiness_level: string;
    readiness_score: number;
    leadership_potential: number;
    mobility_score: number;
    risk_score: number;
    promotion_timeline: number;
    retention_risk: number;
  };
  target_role: {
    role_name: string;
    level: string;
    department: string;
  };
  match_score: number;
  success_probability: number;
  gap_analysis: Record<string, number>;
}

export interface SuccessionScenario {
  scenario_name: string;
  timeline_months: number;
  readiness_status: string;
  business_impact: Record<string, number>;
  financial_risk: number;
  operational_risk: number;
  required_actions: string[];
}
