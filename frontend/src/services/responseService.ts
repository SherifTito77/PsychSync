// frontend/src/services/responseService.ts
import api from './api';
export interface ResponseSession {
  id: number;
  assessment_id: number;
  assignment_id?: number;
  respondent_id?: number;
  responses: Record<string, any>;
  status: 'in_progress' | 'completed' | 'submitted';
  is_complete: boolean;
  current_section: number;
  progress_percentage: number;
  time_taken?: number;
  started_at: string;
  last_saved_at: string;
  submitted_at?: string;
}
export interface ResponseScore {
  id: number;
  response_id: number;
  total_score?: number;
  max_possible_score?: number;
  percentage_score?: number;
  subscale_scores?: Record<string, number>;
  interpretation?: string;
  calculated_at: string;
}
export interface ResponseWithScore extends ResponseSession {
  score?: ResponseScore;
}
export interface StartResponseRequest {
  assessment_id: number;
  assignment_id?: number;
}
export interface SaveProgressRequest {
  responses: Record<string, any>;
  current_section?: number;
}
export interface SubmitResponseRequest {
  responses: Record<string, any>;
  time_taken?: number;
}
export const responseService = {
  // Start new response session
  async startResponse(data: StartResponseRequest): Promise<ResponseSession> {
    const response = await api.post<ResponseSession>('/responses/start', data);
    return response.data;
  },
  // Get my responses
  async getMyResponses(statusFilter?: string): Promise<ResponseSession[]> {
    const response = await api.get<ResponseSession[]>('/responses/my-responses', {
      params: { status_filter: statusFilter },
    });
    return response.data;
  },
  // Get response by ID
  async getResponse(responseId: number): Promise<ResponseWithScore> {
    const response = await api.get<ResponseWithScore>(`/responses/${responseId}`);
    return response.data;
  },
  // Save progress
  async saveProgress(
    responseId: number,
    data: SaveProgressRequest
  ): Promise<ResponseSession> {
    const response = await api.put<ResponseSession>(
      `/responses/${responseId}/save`,
      data
    );
    return response.data;
  },
  // Submit response
  async submitResponse(
    responseId: number,
    data: SubmitResponseRequest
  ): Promise<ResponseWithScore> {
    const response = await api.post<ResponseWithScore>(
      `/responses/${responseId}/submit`,
      data
    );
    return response.data;
  },
  // Delete response
  async deleteResponse(responseId: number): Promise<void> {
    await api.delete(`/responses/${responseId}`);
  },
  // Get response score
  async getResponseScore(responseId: number): Promise<ResponseScore> {
    const response = await api.get<ResponseScore>(`/responses/${responseId}/score`);
    return response.data;
  },
};