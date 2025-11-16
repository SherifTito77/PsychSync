// frontend/src/services/assessmentService.ts
import api from './api';
export interface Question {
  id: number;
  section_id: number;
  question_type: 'multiple_choice' | 'rating_scale' | 'text' | 'yes_no' | 'likert';
  question_text: string;
  help_text?: string;
  order: number;
  is_required: boolean;
  config?: any;
  created_at: string;
  updated_at: string;
}
export interface Section {
  id: number;
  assessment_id: number;
  title: string;
  description?: string;
  order: number;
  questions: Question[];
  created_at: string;
  updated_at: string;
}
export interface Assessment {
  id: number;
  title: string;
  description?: string;
  category: string;
  status: 'draft' | 'active' | 'archived';
  version: number;
  instructions?: string;
  estimated_duration?: number;
  is_public: boolean;
  allow_anonymous: boolean;
  randomize_questions: boolean;
  show_progress: boolean;
  created_by_id: number;
  team_id?: number;
  created_at: string;
  updated_at: string;
  published_at?: string;
}
export interface AssessmentWithSections extends Assessment {
  sections: Section[];
  question_count: number;
}
export interface CreateAssessmentRequest {
  title: string;
  description?: string;
  category: string;
  instructions?: string;
  estimated_duration?: number;
  team_id?: number;
  is_public?: boolean;
  allow_anonymous?: boolean;
  randomize_questions?: boolean;
  show_progress?: boolean;
  sections?: CreateSectionRequest[];
}
export interface CreateSectionRequest {
  title: string;
  description?: string;
  order: number;
  questions?: CreateQuestionRequest[];
}
export interface CreateQuestionRequest {
  question_type: string;
  question_text: string;
  help_text?: string;
  order: number;
  is_required?: boolean;
  config?: any;
}
export interface UpdateAssessmentRequest {
  title?: string;
  description?: string;
  category?: string;
  instructions?: string;
  estimated_duration?: number;
  status?: string;
  is_public?: boolean;
  allow_anonymous?: boolean;
  randomize_questions?: boolean;
  show_progress?: boolean;
}
export interface Assignment {
  id: number;
  assessment_id: number;
  team_id?: number;
  assigned_to_user_id?: number;
  assigned_by_id: number;
  due_date?: string;
  is_active: boolean;
  created_at: string;
  completed_at?: string;
}
export interface ResponseSubmit {
  assignment_id?: number;
  responses: Record<string, any>;
  is_complete: boolean;
}
export const assessmentService = {
  // Assessment CRUD
  async createAssessment(data: CreateAssessmentRequest): Promise<Assessment> {
    const response = await api.post<Assessment>('/assessments', data);
    return response.data;
  },
  async getAssessments(
    category?: string,
    status?: string
  ): Promise<Assessment[]> {
    const response = await api.get<{ assessments: Assessment[]; total: number }>(
      '/assessments',
      {
        params: { category, status },
      }
    );
    return response.data.assessments;
  },
  async getAssessment(assessmentId: number): Promise<AssessmentWithSections> {
    const response = await api.get<AssessmentWithSections>(
      `/assessments/${assessmentId}`
    );
    return response.data;
  },
  async updateAssessment(
    assessmentId: number,
    data: UpdateAssessmentRequest
  ): Promise<Assessment> {
    const response = await api.put<Assessment>(
      `/assessments/${assessmentId}`,
      data
    );
    return response.data;
  },
  async deleteAssessment(assessmentId: number): Promise<void> {
    await api.delete(`/assessments/${assessmentId}`);
  },
  async publishAssessment(assessmentId: number): Promise<Assessment> {
    const response = await api.post<Assessment>(
      `/assessments/${assessmentId}/publish`
    );
    return response.data;
  },
  async archiveAssessment(assessmentId: number): Promise<Assessment> {
    const response = await api.post<Assessment>(
      `/assessments/${assessmentId}/archive`
    );
    return response.data;
  },
  async duplicateAssessment(assessmentId: number): Promise<Assessment> {
    const response = await api.post<Assessment>(
      `/assessments/${assessmentId}/duplicate`
    );
    return response.data;
  },
  // Section Management
  async addSection(
    assessmentId: number,
    data: CreateSectionRequest
  ): Promise<Section> {
    const response = await api.post<Section>(
      `/assessments/${assessmentId}/sections`,
      data
    );
    return response.data;
  },
  async deleteSection(assessmentId: number, sectionId: number): Promise<void> {
    await api.delete(`/assessments/${assessmentId}/sections/${sectionId}`);
  },
  // Question Management
  async addQuestion(
    assessmentId: number,
    sectionId: number,
    data: CreateQuestionRequest
  ): Promise<Question> {
    const response = await api.post<Question>(
      `/assessments/${assessmentId}/sections/${sectionId}/questions`,
      data
    );
    return response.data;
  },
  async deleteQuestion(assessmentId: number, questionId: number): Promise<void> {
    await api.delete(`/assessments/${assessmentId}/questions/${questionId}`);
  },
  // Assignment Management
  async createAssignment(
    assessmentId: number,
    data: {
      team_id?: number;
      assigned_to_user_id?: number;
      due_date?: string;
    }
  ): Promise<Assignment> {
    const response = await api.post<Assignment>(
      `/assessments/${assessmentId}/assignments`,
      { assessment_id: assessmentId, ...data }
    );
    return response.data;
  },
  async getMyAssignments(isActive?: boolean): Promise<Assignment[]> {
    const response = await api.get<Assignment[]>('/assessments/assignments/me', {
      params: { is_active: isActive },
    });
    return response.data;
  },
  // Response Management
  async submitResponse(
    assessmentId: number,
    data: ResponseSubmit
  ): Promise<any> {
    const response = await api.post(
      `/assessments/${assessmentId}/responses`,
      data
    );
    return response.data;
  },
  async getAssessmentResponses(assessmentId: number): Promise<any[]> {
    const response = await api.get<any[]>(`/assessments/${assessmentId}/responses`);
    return response.data;
  },
};
