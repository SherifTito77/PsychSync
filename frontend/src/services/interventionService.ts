/**
 * Intervention Service
 *
 * Service for managing health interventions including:
 * - Creating intervention plans
 * - Tracking intervention effectiveness
 * - Managing intervention programs
 * - Analyzing intervention outcomes
 */

import api from './api';
import type {
  Intervention,
  InterventionCreateRequest,
  InterventionProgram,
  InterventionParticipant,
  Measurement,
  EffectivenessResult,
  AnalysisSummary,
  ApiResponse,
  PaginatedResponse,
} from '@/types/healthMonitoring';

export interface CreateInterventionProgramRequest {
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
  priority?: 'low' | 'medium' | 'high' | 'critical';
  budget?: number;
  participants_target?: number;
  implementation_details?: Record<string, any>;
  external_references?: string[];
  tags?: string[];
  team_id?: string;
}

export interface UpdateInterventionProgramRequest {
  title?: string;
  description?: string;
  status?: 'planned' | 'active' | 'completed' | 'cancelled' | 'paused';
  end_date?: string;
  actual_participants?: number;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  budget?: number;
}

export interface EnrollParticipantsRequest {
  user_ids: string[];
  participant_role?: 'participant' | 'facilitator' | 'observer';
  enrollment_notes?: string;
}

export interface AddMeasurementRequest {
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
}

export interface AnalyzeEffectivenessRequest {
  intervention_id: string;
  metrics?: string[];
  control_group_id?: string;
  follow_up_days?: number;
  significance_level?: number;
  power_threshold?: number;
}

export class InterventionService {
  private static readonly BASE_PATH = '/intervention-effectiveness';

  /**
   * Create intervention plan based on health risks
   */
  static async createInterventionPlan(
    request: InterventionCreateRequest
  ): Promise<Intervention[]> {
    try {
      const response = await api.post<Intervention[]>(
        '/health-monitoring/interventions',
        request
      );
      return response.data;
    } catch (error) {
      console.error('Failed to create intervention plan:', error);
      throw error;
    }
  }

  /**
   * Create a new intervention program
   */
  static async createProgram(
    request: CreateInterventionProgramRequest
  ): Promise<InterventionProgram> {
    try {
      const response = await api.post<InterventionProgram>(
        `${this.BASE_PATH}/interventions`,
        request
      );
      return response.data;
    } catch (error) {
      console.error('Failed to create intervention program:', error);
      throw error;
    }
  }

  /**
   * List intervention programs with filtering
   */
  static async listPrograms(params?: {
    status?: string;
    intervention_type?: string;
    category?: string;
    team_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<InterventionProgram[]> {
    try {
      const response = await api.get<InterventionProgram[]>(
        `${this.BASE_PATH}/interventions`,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to list intervention programs:', error);
      throw error;
    }
  }

  /**
   * Get specific intervention program details
   */
  static async getProgram(
    interventionId: string
  ): Promise<InterventionProgram> {
    try {
      const response = await api.get<InterventionProgram>(
        `${this.BASE_PATH}/interventions/${interventionId}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get intervention program:', error);
      throw error;
    }
  }

  /**
   * Update intervention program details
   */
  static async updateProgram(
    interventionId: string,
    request: UpdateInterventionProgramRequest
  ): Promise<InterventionProgram> {
    try {
      const response = await api.put<InterventionProgram>(
        `${this.BASE_PATH}/interventions/${interventionId}`,
        request
      );
      return response.data;
    } catch (error) {
      console.error('Failed to update intervention program:', error);
      throw error;
    }
  }

  /**
   * Delete/cancel intervention program
   */
  static async deleteProgram(interventionId: string): Promise<ApiResponse<void>> {
    try {
      const response = await api.delete<ApiResponse<void>>(
        `${this.BASE_PATH}/interventions/${interventionId}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to delete intervention program:', error);
      throw error;
    }
  }

  /**
   * Enroll participants in intervention program
   */
  static async enrollParticipants(
    interventionId: string,
    request: EnrollParticipantsRequest
  ): Promise<{ enrolled_count: number; total_participants: number }> {
    try {
      const response = await api.post<{
        enrolled_count: number;
        total_participants: number;
      }>(`${this.BASE_PATH}/interventions/${interventionId}/participants`, request);
      return response.data;
    } catch (error) {
      console.error('Failed to enroll participants:', error);
      throw error;
    }
  }

  /**
   * List intervention participants
   */
  static async listParticipants(
    interventionId: string
  ): Promise<InterventionParticipant[]> {
    try {
      const response = await api.get<InterventionParticipant[]>(
        `${this.BASE_PATH}/interventions/${interventionId}/participants`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to list participants:', error);
      throw error;
    }
  }

  /**
   * Add pre-intervention measurement
   */
  static async addPreMeasurement(
    interventionId: string,
    request: AddMeasurementRequest
  ): Promise<Measurement> {
    try {
      const response = await api.post<Measurement>(
        `${this.BASE_PATH}/interventions/${interventionId}/measurements/pre`,
        request
      );
      return response.data;
    } catch (error) {
      console.error('Failed to add pre-measurement:', error);
      throw error;
    }
  }

  /**
   * Add post-intervention measurement
   */
  static async addPostMeasurement(
    interventionId: string,
    request: AddMeasurementRequest
  ): Promise<Measurement> {
    try {
      const response = await api.post<Measurement>(
        `${this.BASE_PATH}/interventions/${interventionId}/measurements/post`,
        request
      );
      return response.data;
    } catch (error) {
      console.error('Failed to add post-measurement:', error);
      throw error;
    }
  }

  /**
   * List intervention measurements
   */
  static async listMeasurements(
    interventionId: string,
    measurementType: 'pre' | 'post',
    params?: {
      metric_name?: string;
      user_id?: string;
    }
  ): Promise<Measurement[]> {
    try {
      const response = await api.get<Measurement[]>(
        `${this.BASE_PATH}/interventions/${interventionId}/measurements`,
        {
          params: {
            measurement_type: measurementType,
            ...params,
          },
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to list measurements:', error);
      throw error;
    }
  }

  /**
   * Analyze intervention effectiveness
   */
  static async analyzeEffectiveness(
    request: AnalyzeEffectivenessRequest
  ): Promise<AnalysisSummary> {
    try {
      const response = await api.post<AnalysisSummary>(
        `${this.BASE_PATH}/analyze`,
        request
      );
      return response.data;
    } catch (error) {
      console.error('Failed to analyze effectiveness:', error);
      throw error;
    }
  }

  /**
   * Get saved effectiveness analysis results
   */
  static async getEffectivenessResults(
    interventionId: string,
    metricName?: string
  ): Promise<EffectivenessResult[]> {
    try {
      const response = await api.get<EffectivenessResult[]>(
        `${this.BASE_PATH}/interventions/${interventionId}/effectiveness`,
        {
          params: { metric_name: metricName },
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get effectiveness results:', error);
      throw error;
    }
  }

  /**
   * Get active interventions for current user
   */
  static async getMyActiveInterventions(): Promise<InterventionProgram[]> {
    return this.listPrograms({
      status: 'active',
      limit: 50,
    });
  }

  /**
   * Get all interventions for organization
   */
  static async getOrganizationInterventions(): Promise<InterventionProgram[]> {
    return this.listPrograms({
      limit: 100,
    });
  }
}

export default InterventionService;
