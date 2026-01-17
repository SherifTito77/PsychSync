/**
 * Product Management Prompts - Type Definitions
 *
 * Complete TypeScript types for the product management prompts system.
 */

export interface Prompt {
  id: string;
  prompt: string;
  type: PromptType;
  complexity: Complexity;
  estimated_time: string;
  outputs: string[];
  related_prompts: string[];
  use_cases: string[];
  category?: CategoryContext;
}

export type PromptType =
  | 'strategic'
  | 'tactical'
  | 'analytical'
  | 'technical'
  | 'creative'
  | 'experimental';

export type Complexity = 'low' | 'medium' | 'high';

export interface CategoryContext {
  id: string;
  name: string;
}

export interface Category {
  id: string;
  name: string;
  description: string;
  icon: string;
  prompt_count: number;
}

export interface PromptExecution {
  id: number;
  prompt_id: string;
  user_id: number;
  executed_at: string;
  context?: Record<string, any>;
  use_ai: boolean;
  outputs_generated?: string[];
  ai_output?: string;
  status: 'completed' | 'failed' | 'partial';
  quality_rating?: number;
  feedback?: string;
}

export interface PromptExecutionRequest {
  prompt_id: string;
  context?: Record<string, any>;
  use_ai: boolean;
}

export interface PromptExecutionResponse {
  prompt: Prompt;
  execution_id: number;
  executed_at: string;
  use_ai: boolean;
  ai_suggestion?: string;
}

export interface PromptWorkflow {
  id: number;
  name: string;
  description?: string;
  goal: string;
  prompt_sequence: string[];
  estimated_total_time?: string;
  usage_count: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface PromptTemplate {
  id: number;
  organization_id?: number;
  created_by: number;
  name: string;
  description?: string;
  category: string;
  base_prompt_id?: string;
  prompt_text: string;
  expected_outputs?: string[];
  use_cases?: string[];
  complexity?: Complexity;
  estimated_time?: string;
  prompt_type?: PromptType;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface PromptFavorite {
  id: number;
  user_id: number;
  prompt_id: string;
  created_at: string;
}

export interface PromptResult {
  id: number;
  execution_id: number;
  title: string;
  result_type: string;
  content: Record<string, any>;
  organization_id?: number;
  is_shared: boolean;
  shared_with?: number[];
  created_at: string;
  updated_at: string;
}

export interface PromptStatistics {
  total_executions: number;
  most_used_prompts: Array<{
    prompt_id: string;
    count: number;
  }>;
  categories_count: number;
  total_prompts: number;
}

export interface WorkflowGoal {
  goal: string;
  name: string;
  description: string;
  prompts: Prompt[];
}

export type WorkflowGoalType =
  | 'feature_launch'
  | 'retention_improvement'
  | 'enterprise_expansion'
  | 'quarterly_planning';

export interface PromptsResponse {
  total: number;
  prompts: Prompt[];
  filters: {
    category: string | null;
    complexity: string | null;
    type: string | null;
  };
}

export interface ExecutionHistoryResponse {
  total: number;
  executions: PromptExecution[];
}

export interface PromptRatingRequest {
  quality_rating: number;
  feedback?: string;
}

// Utility types for API responses
export type ApiResponse<T> = {
  data: T;
  status: number;
};

export type ApiError = {
  error: string;
  message: string;
  details?: Record<string, any>;
};
