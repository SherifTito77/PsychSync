// frontend/src/services/analyticsService.ts
import api from './api';
export interface AssessmentAnalytics {
  assessment_id: number;
  assessment_title: string;
  total_responses: number;
  total_assignments: number;
  average_score?: number;
  average_time?: number;
  completion_rate: number;
  score_distribution: Array<{ range: string; count: number }>;
  recent_responses: Array<{
    id: number;
    submitted_at?: string;
    score?: number;
  }>;
}
export interface UserAnalytics {
  user_id: number;
  total_responses: number;
  completed_responses: number;
  in_progress_responses: number;
  average_score?: number;
  response_history: Array<{
    response_id: number;
    assessment_id: number;
    assessment_title: string;
    submitted_at?: string;
    score?: number;
    time_taken?: number;
  }>;
}
export interface TeamAnalytics {
  team_id: number;
  total_members: number;
  total_assessments: number;
  total_responses: number;
  completed_responses: number;
  average_score?: number;
  member_performance: Array<{
    user_id: number;
    user_name: string;
    completed_assessments: number;
    average_score?: number;
  }>;
}
export interface SystemAnalytics {
  total_users: number;
  total_assessments: number;
  total_responses: number;
  completed_responses: number;
  completion_rate: number;
  recent_activity_30d: number;
  popular_assessments: Array<{
    id: number;
    title: string;
    response_count: number;
  }>;
}
export const analyticsService = {
  async getAssessmentAnalytics(assessmentId: number): Promise<AssessmentAnalytics> {
    const response = await api.get<AssessmentAnalytics>(
      `/analytics/assessments/${assessmentId}`
    );
    return response.data;
  },
  async getMyAnalytics(): Promise<UserAnalytics> {
    const response = await api.get<UserAnalytics>('/analytics/users/me');
    return response.data;
  },
  async getUserAnalytics(userId: number): Promise<UserAnalytics> {
    const response = await api.get<UserAnalytics>(`/analytics/users/${userId}`);
    return response.data;
  },
  async getTeamAnalytics(teamId: number): Promise<TeamAnalytics> {
    const response = await api.get<TeamAnalytics>(`/analytics/teams/${teamId}`);
    return response.data;
  },
  async getSystemAnalytics(): Promise<SystemAnalytics> {
    const response = await api.get<SystemAnalytics>('/analytics/system');
    return response.data;
  },
};
