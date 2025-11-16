import axios from '../api/axios';
export interface ComplianceScore {
  overall: number;
  categories: {
    labor_law: number;
    data_privacy: number;
    workplace_safety: number;
    training: number;
    documentation: number;
  };
  status: 'excellent' | 'good' | 'needs_improvement' | 'critical';
  last_updated: string;
}
export interface TrainingAssignment {
  id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  training_type: string;
  training_name: string;
  due_date: string;
  status: 'assigned' | 'in_progress' | 'completed' | 'overdue';
  assigned_at: string;
  completed_at?: string;
  completion_score?: number;
  certificate_id?: string;
}
export interface AnonymousFeedback {
  id: string;
  feedback_type: string;
  category: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: string;
  submitted_at: string;
  evidence_count: number;
  has_follow_ups: boolean;
}
export interface EmployeeRights {
  federal_rights: Record<string, any>;
  state_rights: Record<string, any>;
  industry_rights: Record<string, any>;
  how_to_report: Record<string, any>;
  faq: Array<{ question: string; answer: string }>;
}
export interface ComplianceCheck {
  organization_id: string;
  check_date: string;
  check_type: string;
  compliance_score: number;
  status: string;
  categories: Record<string, any>;
  priority_actions: Array<{
    priority: string;
    category: string;
    action: string;
    deadline: string;
  }>;
}
export const complianceService = {
  // Compliance Dashboard
  async getComplianceScore(): Promise<ComplianceScore> {
    const response = await axios.get('/api/v1/compliance/latest');
    return response.data;
  },
  async runComplianceCheck(checkType: string = 'full'): Promise<ComplianceCheck> {
    const response = await axios.post('/api/v1/compliance/check', { check_type: checkType });
    return response.data;
  },
  // Training Management
  async getTrainingAssignments(filters?: any): Promise<TrainingAssignment[]> {
    const response = await axios.get('/api/v1/compliance/training/org-report', { params: filters });
    return response.data.feedbacks || [];
  },
  async assignTraining(data: {
    user_id: string;
    training_type: string;
    due_date: string;
    required_by: string;
  }): Promise<any> {
    const response = await axios.post('/api/v1/compliance/training/assign', data);
    return response.data;
  },
  async completeTraining(assignmentId: string, completionData: {
    quiz_score: number;
    time_spent_minutes: number;
    completion_data: any;
  }): Promise<any> {
    const response = await axios.post(`/api/v1/compliance/training/${assignmentId}/complete`, completionData);
    return response.data;
  },
  async sendTrainingReminder(assignmentId: string): Promise<any> {
    const response = await axios.post(`/api/v1/compliance/training/${assignmentId}/remind`);
    return response.data;
  },
  // Anonymous Feedback
  async getFeedbackForReview(filters?: any): Promise<{ feedbacks: AnonymousFeedback[]; count: number }> {
    const response = await axios.get('/api/v1/anonymous-feedback/hr/review', { params: filters });
    return response.data;
  },
  async updateFeedbackStatus(feedbackId: string, update: {
    new_status: string;
    internal_notes?: string;
    public_notes?: string;
    actions_taken?: string;
  }): Promise<any> {
    const response = await axios.patch(`/api/v1/anonymous-feedback/hr/feedback/${feedbackId}`, update);
    return response.data;
  },
  async submitAnonymousFeedback(data: any): Promise<any> {
    const response = await axios.post('/api/v1/anonymous-feedback/submit', data);
    return response.data;
  },
  async checkFeedbackStatus(trackingId: string): Promise<any> {
    const response = await axios.get(`/api/v1/anonymous-feedback/status/${trackingId}`);
    return response.data;
  },
  // Employee Rights
  async getEmployeeRights(state?: string, industry?: string): Promise<EmployeeRights> {
    const params = new URLSearchParams();
    if (state) params.append('state', state);
    if (industry) params.append('industry', industry);
    const response = await axios.get(`/api/v1/compliance/rights?${params}`);
    return response.data;
  },
  // Analytics
  async getComplianceAnalytics(): Promise<any> {
    const response = await axios.get('/api/v1/compliance/analytics');
    return response.data;
  }
};