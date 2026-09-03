/**
 * Assessment Results Service
 *
 * This service connects the frontend to the comprehensive assessment results API
 * supporting all assessment types: MBTI, Big Five, DISC, Enneagram, and custom assessments.
 */

import api from './api';

export interface AssessmentResult {
  result_id: number;
  assessment_type: string;
  assessment_id?: string;
  completed_at: string;
  updated_at?: string;
  responses_count: number;
  // MBTI specific
  type?: string;
  confidence?: number;
  description?: string;
  dimensions?: Record<string, number>;
  preferences?: string[];
  strengths?: string[];
  blind_spots?: string[];
  // Big Five specific
  traits?: Record<string, number>;
  personality_profile?: string;
  // DISC specific
  primary_style?: string;
  // Enneagram specific
  number?: string;
  wings?: string[];
  // Generic/Custom
  score?: number;
  metadata?: Record<string, any>;
  responses?: Record<string, any>;
}

export interface AssessmentResultCreate {
  assessment_type: string;
  assessment_id?: string;
  responses: Record<string, any>;
  raw_type?: string;
  processed_result?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface AssessmentResultUpdate {
  processed_result?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface AssessmentResultsResponse {
  success: boolean;
  count: number;
  results: AssessmentResult[];
  user_id?: string;
  filters?: {
    assessment_type?: string;
    limit?: number;
  };
}

export interface AssessmentResultResponse {
  success: boolean;
  result: AssessmentResult;
}

export interface AssessmentAnalytics {
  success: boolean;
  analytics: {
    total_assessments: number;
    assessment_types: Record<string, number>;
    completion_trend: Record<string, number>;
    latest_completion?: string;
  };
  user_id?: string;
  filters?: {
    assessment_type?: string;
  };
}

class AssessmentResultsService {
  /**
   * Create and store assessment result
   */
  async createAssessmentResult(
    resultData: AssessmentResultCreate
  ): Promise<AssessmentResultResponse> {
    const response = await api.post<AssessmentResultResponse>(
      '/assessment-results',
      resultData
    );
    return response.data;
  }

  /**
   * Get user's assessment results
   */
  async getAssessmentResults(
    assessmentType?: string,
    limit: number = 50
  ): Promise<AssessmentResultsResponse> {
    const params: any = { limit };
    if (assessmentType) {
      params.assessment_type = assessmentType;
    }

    const response = await api.get<AssessmentResultsResponse>(
      '/assessment-results',
      { params }
    );
    return response.data;
  }

  /**
   * Get specific assessment result by ID
   */
  async getAssessmentResult(resultId: number): Promise<AssessmentResultResponse> {
    const response = await api.get<AssessmentResultResponse>(
      `/assessment-results/${resultId}`
    );
    return response.data;
  }

  /**
   * Update assessment result (metadata, notes, etc.)
   */
  async updateAssessmentResult(
    resultId: number,
    updateData: AssessmentResultUpdate
  ): Promise<{ success: boolean; result_id: number; updated_at: string; message: string }> {
    const response = await api.put(
      `/assessment-results/${resultId}`,
      updateData
    );
    return response.data;
  }

  /**
   * Delete assessment result
   */
  async deleteAssessmentResult(resultId: number): Promise<void> {
    await api.delete(`/assessment-results/${resultId}`);
  }

  /**
   * Get analytics for user's assessment results
   */
  async getAssessmentAnalytics(
    assessmentType?: string
  ): Promise<AssessmentAnalytics> {
    const params: any = {};
    if (assessmentType) {
      params.assessment_type = assessmentType;
    }

    const response = await api.get<AssessmentAnalytics>(
      '/assessment-analytics',
      { params }
    );
    return response.data;
  }

  /**
   * Submit MBTI assessment with result storage
   */
  async submitMBTIAssessment(
    assessmentId: string,
    responses: Record<string, string>,
    rawType?: string
  ): Promise<AssessmentResultResponse> {
    const resultData: AssessmentResultCreate = {
      assessment_type: 'mbti',
      assessment_id: assessmentId,
      responses,
      raw_type: rawType,
      metadata: {
        source: 'frontend_mbti_assessment',
        version: '1.0'
      }
    };

    return this.createAssessmentResult(resultData);
  }

  /**
   * Submit Big Five assessment with result storage
   */
  async submitBigFiveAssessment(
    assessmentId: string,
    responses: Record<string, any>
  ): Promise<AssessmentResultResponse> {
    const resultData: AssessmentResultCreate = {
      assessment_type: 'big_five',
      assessment_id: assessmentId,
      responses,
      metadata: {
        source: 'frontend_big_five_assessment',
        version: '1.0'
      }
    };

    return this.createAssessmentResult(resultData);
  }

  /**
   * Submit DISC assessment with result storage
   */
  async submitDISCAssessment(
    assessmentId: string,
    responses: Record<string, any>,
    rawType?: string
  ): Promise<AssessmentResultResponse> {
    const resultData: AssessmentResultCreate = {
      assessment_type: 'disc',
      assessment_id: assessmentId,
      responses,
      raw_type: rawType,
      metadata: {
        source: 'frontend_disc_assessment',
        version: '1.0'
      }
    };

    return this.createAssessmentResult(resultData);
  }

  /**
   * Submit Enneagram assessment with result storage
   */
  async submitEnneagramAssessment(
    assessmentId: string,
    responses: Record<string, any>,
    rawType?: string
  ): Promise<AssessmentResultResponse> {
    const resultData: AssessmentResultCreate = {
      assessment_type: 'enneagram',
      assessment_id: assessmentId,
      responses,
      raw_type: rawType,
      metadata: {
        source: 'frontend_enneagram_assessment',
        version: '1.0'
      }
    };

    return this.createAssessmentResult(resultData);
  }

  /**
   * Submit custom assessment with result storage
   */
  async submitCustomAssessment(
    assessmentId: string,
    responses: Record<string, any>,
    customData: Record<string, any>
  ): Promise<AssessmentResultResponse> {
    const resultData: AssessmentResultCreate = {
      assessment_type: 'custom',
      assessment_id: assessmentId,
      responses,
      processed_result: customData,
      metadata: {
        source: 'frontend_custom_assessment',
        version: '1.0',
        ...customData
      }
    };

    return this.createAssessmentResult(resultData);
  }

  /**
   * Get MBTI assessment results for user
   */
  async getMBTIResults(): Promise<AssessmentResult[]> {
    const response = await this.getAssessmentResults('mbti');
    return response.results;
  }

  /**
   * Get Big Five assessment results for user
   */
  async getBigFiveResults(): Promise<AssessmentResult[]> {
    const response = await this.getAssessmentResults('big_five');
    return response.results;
  }

  /**
   * Get DISC assessment results for user
   */
  async getDISCResults(): Promise<AssessmentResult[]> {
    const response = await this.getAssessmentResults('disc');
    return response.results;
  }

  /**
   * Get Enneagram assessment results for user
   */
  async getEnneagramResults(): Promise<AssessmentResult[]> {
    const response = await this.getAssessmentResults('enneagram');
    return response.results;
  }

  /**
   * Get custom assessment results for user
   */
  async getCustomResults(): Promise<AssessmentResult[]> {
    const response = await this.getAssessmentResults('custom');
    return response.results;
  }

  /**
   * Get assessment history for dashboard
   */
  async getAssessmentHistory(limit: number = 10): Promise<AssessmentResult[]> {
    const response = await this.getAssessmentResults(undefined, limit);
    return response.results;
  }

  /**
   * Format MBTI result for display
   */
  formatMBTIResult(result: AssessmentResult): {
    type: string;
    confidence: number;
    description: string;
    dimensions: Record<string, number>;
    preferences: string[];
    strengths: string[];
    blindSpots: string[];
  } {
    return {
      type: result.type || 'Unknown',
      confidence: result.confidence || 0,
      description: result.description || '',
      dimensions: result.dimensions || {},
      preferences: result.preferences || [],
      strengths: result.strengths || [],
      blindSpots: result.blind_spots || []
    };
  }

  /**
   * Format Big Five result for display
   */
  formatBigFiveResult(result: AssessmentResult): {
    traits: Record<string, number>;
    profile: string;
    confidence: number;
    description: string;
  } {
    return {
      traits: result.traits || {},
      profile: result.personality_profile || '',
      confidence: result.confidence || 0,
      description: result.description || ''
    };
  }

  /**
   * Format DISC result for display
   */
  formatDISCResult(result: AssessmentResult): {
    primaryStyle: string;
    description: string;
    confidence: number;
    dimensions: Record<string, number>;
  } {
    return {
      primaryStyle: result.primary_style || 'Unknown',
      description: result.description || '',
      confidence: result.confidence || 0,
      dimensions: result.dimensions || {}
    };
  }

  /**
   * Format Enneagram result for display
   */
  formatEnneagramResult(result: AssessmentResult): {
    type: string;
    description: string;
    confidence: number;
    wings: string[];
  } {
    return {
      type: result.number || 'Unknown',
      description: result.description || '',
      confidence: result.confidence || 0,
      wings: result.wings || []
    };
  }
}

// Create and export singleton instance
const assessmentResultsService = new AssessmentResultsService();
export default assessmentResultsService;
