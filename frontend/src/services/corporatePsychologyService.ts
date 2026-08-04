/**
 * Corporate Psychology Service
 *
 * API service for Corporate Psychology Encoding System.
 * Provides methods to fetch organizational psychology metrics, signals, and interventions.
 *
 * All data is at ORGANIZATIONAL level - NO individual information.
 */

import api from './api';

// ═══════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════

export interface PsychologyMetrics {
  organization_id: string;
  team_id?: string;
  measurement_period_start: string;
  measurement_period_end: string;

  // Core encodings (0-100 scale)
  cognitive_load_index: number;
  trust_stability_score: number;
  emotional_volatility_score: number;
  coordination_friction_score: number;
  psychological_debt_score: number;
  recovery_resilience_score: number;

  // Aggregate metrics
  organizational_health_index: number;
  overall_risk_score: number;
  risk_horizon: 'immediate' | 'emerging' | 'structural';
  health_trajectory: 'improving' | 'stable' | 'declining';

  created_at: string;
}

export interface SystemSignal {
  id: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  risk_horizon: 'immediate' | 'emerging' | 'structural';
  signal_summary: string;
  change_description: string;
  operational_impact: string;
  current_value: number;
  probability_range: string;
  recommended_actions: string[];
  urgency: string;
  status: string;
  created_at: string;
}

export interface Intervention {
  id: string;
  organization_id: string;
  team_id?: string;
  intervention_title: string;
  intervention_category: string;
  expected_outcomes: string;
  status: string;
  progress_percentage: number;
  created_at: string;
}

export interface AnalysisRequest {
  organization_id: string;
  team_id?: string;
  measurement_period_days?: number;
  include_culture_metrics?: boolean;
  include_wellness_metrics?: boolean;
  include_behavioral_metrics?: boolean;
  include_communication_metrics?: boolean;
}

export interface AnalysisResponse {
  success: boolean;
  message: string;
  metrics_id?: string;
  signals_generated: number;
  interventions_recommended: number;
}

export interface InterventionRequest {
  organization_id: string;
  team_id?: string;
  intervention_title: string;
  intervention_description: string;
  intervention_category: string;
  expected_outcomes: string;
  business_rationale: string;
  implementation_approach: string;
  estimated_duration_weeks: number;
  resource_requirements: string;
}

// ═══════════════════════════════════════════════════════════════
// API Service
// ═══════════════════════════════════════════════════════════════

class CorporatePsychologyService {
  private readonly basePath = '/corporate-psychology';

  /**
   * Get current psychology metrics for an organization
   */
  async getMetrics(
    organizationId: string,
    teamId?: string,
  ): Promise<PsychologyMetrics> {
    const params = teamId ? `?team_id=${teamId}` : '';
    const response = await api.get<{ data: PsychologyMetrics }>(
      `${this.basePath}/metrics/${organizationId}${params}`,
    );
    return response.data;
  }

  /**
   * Run psychology analysis for an organization
   */
  async runAnalysis(request: AnalysisRequest): Promise<AnalysisResponse> {
    const response = await api.post<{ data: AnalysisResponse }>(
      `${this.basePath}/analyze`,
      request,
    );
    return response.data;
  }

  /**
   * Get system signals (alerts) for an organization
   */
  async getSignals(
    organizationId: string,
    options?: {
      team_id?: string;
      status?: string;
      severity?: string;
      limit?: number;
    },
  ): Promise<SystemSignal[]> {
    const params = new URLSearchParams();
    if (options?.team_id) params.append('team_id', options.team_id);
    if (options?.status) params.append('status', options.status);
    if (options?.severity) params.append('severity', options.severity);
    if (options?.limit) params.append('limit', options.limit.toString());

    const queryString = params.toString();
    const response = await api.get<{ data: SystemSignal[] }>(
      `${this.basePath}/signals/${organizationId}${queryString ? `?${queryString}` : ''}`,
    );
    return response.data;
  }

  /**
   * Get interventions for an organization
   */
  async getInterventions(
    organizationId: string,
    options?: {
      team_id?: string;
      status?: string;
      category?: string;
    },
  ): Promise<Intervention[]> {
    const params = new URLSearchParams();
    if (options?.team_id) params.append('team_id', options.team_id);
    if (options?.status) params.append('status', options.status);
    if (options?.category) params.append('category', options.category);

    const queryString = params.toString();
    const response = await api.get<{ data: Intervention[] }>(
      `${this.basePath}/interventions/${organizationId}${queryString ? `?${queryString}` : ''}`,
    );
    return response.data;
  }

  /**
   * Create a new structural intervention
   */
  async createIntervention(request: InterventionRequest): Promise<Intervention> {
    const response = await api.post<{ data: Intervention }>(
      `${this.basePath}/interventions`,
      request,
    );
    return response.data;
  }
}

// Export singleton instance
export default new CorporatePsychologyService();
