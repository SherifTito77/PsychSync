// frontend/src/services/templateService.ts
import api from './api';
import { Assessment } from './assessmentService';
export interface Template {
  id: number;
  name: string;
  description?: string;
  category: string;
  author?: string;
  version: string;
  is_official: boolean;
  is_public: boolean;
  usage_count: number;
  created_by_id?: number;
  created_at: string;
  updated_at: string;
}
export interface TemplateWithData extends Template {
  template_data: string;
}
export const templateService = {
  async getTemplates(
    category?: string,
    isOfficial?: boolean
  ): Promise<Template[]> {
    const response = await api.get<{ templates: Template[]; total: number }>(
      '/templates',
      {
        params: { category, is_official: isOfficial },
      }
    );
    return response.data.templates;
  },
  async searchTemplates(query: string): Promise<Template[]> {
    const response = await api.get<Template[]>('/templates/search', {
      params: { q: query },
    });
    return response.data;
  },
  async getTemplate(templateId: number): Promise<TemplateWithData> {
    const response = await api.get<TemplateWithData>(`/templates/${templateId}`);
    return response.data;
  },
  async createAssessmentFromTemplate(
    templateId: number,
    teamId?: number
  ): Promise<Assessment> {
    const response = await api.post<Assessment>(
      `/templates/${templateId}/use`,
      null,
      {
        params: { team_id: teamId },
      }
    );
    return response.data;
  },
  async createTemplateFromAssessment(
    assessmentId: number,
    name: string,
    description?: string
  ): Promise<Template> {
    const response = await api.post<Template>(
      `/templates/from-assessment/${assessmentId}`,
      null,
      {
        params: { name, description },
      }
    );
    return response.data;
  },
};