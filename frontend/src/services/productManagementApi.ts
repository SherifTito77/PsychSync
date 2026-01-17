/**
 * Product Management Prompts API Service
 *
 * Frontend service for interacting with product management prompts endpoints.
 */

import { api } from './api';
import type {
  Prompt,
  Category,
  PromptExecution,
  PromptExecutionRequest,
  PromptExecutionResponse,
  PromptWorkflow,
  PromptTemplate,
  PromptFavorite,
  PromptResult,
  PromptStatistics,
  PromptsResponse,
  ExecutionHistoryResponse,
  PromptRatingRequest,
  WorkflowGoalType,
} from '@/types/productManagement';

export const productManagementApi = {
  /**
   * Get all prompts with optional filtering
   */
  getPrompts: async (filters?: {
    category?: string;
    complexity?: string;
    type?: string;
  }): Promise<PromptsResponse> => {
    const response = await api.get<PromptsResponse>('/product-management/prompts', {
      params: filters,
    });
    return response.data;
  },

  /**
   * Get a specific prompt by ID
   */
  getPrompt: async (promptId: string): Promise<Prompt> => {
    const response = await api.get<Prompt>(`/product-management/prompts/${promptId}`);
    return response.data;
  },

  /**
   * Get all categories
   */
  getCategories: async (): Promise<Category[]> => {
    const response = await api.get<Category[]>('/product-management/categories');
    return response.data;
  },

  /**
   * Get prompts in a specific category
   */
  getCategoryPrompts: async (
    categoryId: string,
    filters?: {
      complexity?: string;
      type?: string;
    }
  ): Promise<Prompt[]> => {
    const response = await api.get<Prompt[]>(
      `/product-management/categories/${categoryId}/prompts`,
      { params: filters }
    );
    return response.data;
  },

  /**
   * Get prompts related to a specific prompt
   */
  getRelatedPrompts: async (promptId: string): Promise<Prompt[]> => {
    const response = await api.get<Prompt[]>(`/product-management/prompts/${promptId}/related`);
    return response.data;
  },

  /**
   * Execute a prompt
   */
  executePrompt: async (
    request: PromptExecutionRequest
  ): Promise<PromptExecutionResponse> => {
    const response = await api.post<PromptExecutionResponse>(
      '/product-management/prompts/execute',
      request
    );
    return response.data;
  },

  /**
   * Search prompts by keyword
   */
  searchPrompts: async (query: string, category?: string): Promise<Prompt[]> => {
    const response = await api.get<Prompt[]>(`/product-management/prompts/search/${query}`, {
      params: { category },
    });
    return response.data;
  },

  /**
   * Get prompts by use case
   */
  getPromptsByUseCase: async (useCase: string): Promise<Prompt[]> => {
    const response = await api.get<Prompt[]>(`/product-management/use-cases/${useCase}`);
    return response.data;
  },

  /**
   * Get workflow for a specific goal
   */
  getWorkflow: async (goal: WorkflowGoalType): Promise<Prompt[]> => {
    const response = await api.get<Prompt[]>(`/product-management/workflows/${goal}`);
    return response.data;
  },

  /**
   * Get execution history
   */
  getExecutionHistory: async (params?: {
    limit?: number;
    prompt_id?: string;
  }): Promise<ExecutionHistoryResponse> => {
    const response = await api.get<ExecutionHistoryResponse>(
      '/product-management/executions/history',
      { params }
    );
    return response.data;
  },

  /**
   * Rate an execution
   */
  rateExecution: async (
    executionId: number,
    rating: PromptRatingRequest
  ): Promise<{ status: string; execution_id: number; rating: number }> => {
    const response = await api.post(
      `/product-management/executions/${executionId}/rate`,
      rating
    );
    return response.data;
  },

  /**
   * Add prompt to favorites
   */
  addFavorite: async (promptId: string): Promise<{ status: string; message: string }> => {
    const response = await api.post('/product-management/favorites', { prompt_id: promptId });
    return response.data;
  },

  /**
   * Get user's favorite prompts
   */
  getFavorites: async (): Promise<Prompt[]> => {
    const response = await api.get<Prompt[]>('/product-management/favorites');
    return response.data;
  },

  /**
   * Remove prompt from favorites
   */
  removeFavorite: async (promptId: string): Promise<{ status: string; message: string }> => {
    const response = await api.delete(`/product-management/favorites/${promptId}`);
    return response.data;
  },

  /**
   * Get usage statistics
   */
  getStatistics: async (): Promise<PromptStatistics> => {
    const response = await api.get<PromptStatistics>('/product-management/statistics');
    return response.data;
  },

  // TODO(human): Implement template and workflow management endpoints when backend is ready
  /**
   * Create a custom prompt template
   * Context: Organizations may want to create their own prompts
   */
  createTemplate: async (template: Omit<PromptTemplate, 'id' | 'usage_count' | 'created_at' | 'updated_at'>): Promise<PromptTemplate> => {
    // Placeholder - implement when backend endpoint is ready
    throw new Error('Not implemented yet');
  },

  /**
   * Create a custom workflow
   * Context: Teams may want to save prompt sequences for common scenarios
   */
  createWorkflow: async (workflow: Omit<PromptWorkflow, 'id' | 'usage_count' | 'created_at' | 'updated_at'>): Promise<PromptWorkflow> => {
    // Placeholder - implement when backend endpoint is ready
    throw new Error('Not implemented yet');
  },
};

// React Query hooks for data fetching
export const useProductManagementPrompts = (filters?: {
  category?: string;
  complexity?: string;
  type?: string;
}) => {
  return {
    getPrompts: () => productManagementApi.getPrompts(filters),
    getPrompt: (id: string) => productManagementApi.getPrompt(id),
    getCategories: () => productManagementApi.getCategories(),
    executePrompt: (request: PromptExecutionRequest) =>
      productManagementApi.executePrompt(request),
  };
};

export const usePromptFavorites = () => {
  return {
    getFavorites: () => productManagementApi.getFavorites(),
    addFavorite: (id: string) => productManagementApi.addFavorite(id),
    removeFavorite: (id: string) => productManagementApi.removeFavorite(id),
  };
};

export const usePromptWorkflows = () => {
  return {
    getWorkflow: (goal: WorkflowGoalType) => productManagementApi.getWorkflow(goal),
    getExecutionHistory: (params?: { limit?: number; prompt_id?: string }) =>
      productManagementApi.getExecutionHistory(params),
  };
};
