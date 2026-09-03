/**
 * PsychSync API Types
 * Comprehensive TypeScript definitions for the PsychSync backend API
 *
 * Generated based on backend API endpoints and schemas
 * @version 1.0.0
 */

// ============================================================================
// COMMON TYPES
// ============================================================================

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface ErrorResponse {
  detail: string;
  status_code: number;
  error_type?: string;
}

// ============================================================================
// USER & AUTH TYPES
// ============================================================================

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  department?: string;
  job_title?: string;
  bio?: string;
  role: 'admin' | 'user' | 'team_admin';
  is_active: boolean;
  is_verified: boolean;
  email_verified_at?: string;
  created_at: string;
  updated_at: string;
  organization_id?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

// ============================================================================
// TEAM TYPES
// ============================================================================

export interface Team {
  id: string;
  name: string;
  description?: string;
  organization_id: string;
  created_by_id: string;
  created_at: string;
  updated_at: string;
  members_count?: number;
}

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: 'admin' | 'member' | 'owner';
  joined_at: string;
  is_active: boolean;
}

export interface TeamCreateRequest {
  name: string;
  description?: string;
  organization_id?: string;
}

export interface TeamWithMembers extends Team {
  members: TeamMember[];
}

export interface TeamListResponse {
  teams: Team[];
  total: number;
  success: boolean;
  message: string;
}

// ============================================================================
// ASSESSMENT TYPES
// ============================================================================

export interface Assessment {
  id: string;
  title: string;
  description?: string;
  category: 'personality' | 'clinical' | 'screening' | 'behavioral';
  status: 'draft' | 'active' | 'archived';
  framework_code?: string;
  team_id?: string;
  created_by_id: string;
  estimated_duration_minutes?: number;
  instructions?: string;
  created_at: string;
  updated_at: string;
}

export interface AssessmentCreateRequest {
  title: string;
  description?: string;
  category: string;
  framework_code?: string;
  estimated_duration_minutes?: number;
  instructions?: string;
}

export interface Question {
  id: string;
  assessment_id: string;
  question_text: string;
  question_type: 'multiple_choice' | 'rating' | 'open_ended';
  options?: string[];
  order: number;
  is_required: boolean;
}

export interface ResponseCreate {
  assessment_id: string;
  responses: Record<string, any>;
  is_complete?: boolean;
  assignment_id?: string;
}

// ============================================================================
// RESPONSE TYPES
// ============================================================================

export interface Response {
  id: string;
  assessment_id: string;
  respondent_id?: string;
  status: 'in_progress' | 'complete' | 'abandoned';
  responses: Record<string, any>;
  score?: number;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ResponseScore {
  response_id: string;
  score: number;
  max_score: number;
  percentage: number;
  subscores?: Record<string, number>;
  interpretation?: string;
}

export interface ResponseWithScore extends Omit<Response, 'score'> {
  score?: ResponseScore;
}

// ============================================================================
// PERSONALITY & PSYCHOMETRICS TYPES
// ============================================================================

export interface BigFiveScores {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
}

export interface TeamPersonalityMap {
  team_id: string;
  composition_type: string;
  team_size: number;
  openness: DimensionStats;
  conscientiousness: DimensionStats;
  extraversion: DimensionStats;
  agreeableness: DimensionStats;
  neuroticism: DimensionStats;
  strengths: string[];
  gaps: string[];
  internal_compatibility: number;
  diversity_score: number;
  created_at: string;
  updated_at: string;
}

export interface DimensionStats {
  avg: number;
  min: number;
  max: number;
  std_dev: number;
  distribution: number[];
}

export interface TeamComparison {
  team_id: string;
  composition_type: string;
  team_size: number;
  diversity_score: number;
  internal_compatibility: number;
  openness: DimensionStats;
  conscientiousness: DimensionStats;
  extraversion: DimensionStats;
  agreeableness: DimensionStats;
  neuroticism: DimensionStats;
}

// ============================================================================
// ANALYTICS TYPES
// ============================================================================

export interface TeamAnalytics {
  team_id: string;
  team_name: string;
  total_assessments: number;
  completed_assessments: number;
  average_score: number;
  completion_rate: number;
  top_traits?: string[];
  areas_for_improvement?: string[];
  period: {
    start: string;
    end: string;
  };
}

export interface UserAnalytics {
  user_id: string;
  total_assessments: number;
  completed_assessments: number;
  average_score: number;
  personality_traits?: BigFiveScores;
  team_contributions: {
    team_id: string;
    team_name: string;
    role: string;
  }[];
}

// ============================================================================
// NOTIFICATION TYPES
// ============================================================================

export interface Notification {
  id: string;
  user_id: string;
  type: 'assessment' | 'team' | 'system' | 'alert';
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  action_url?: string;
}

// ============================================================================
// ORGANIZATION TYPES
// ============================================================================

export interface Organization {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// API ENDPOINT PATHS
// ============================================================================

export type ApiEndpoints = {
  // Auth
  login: '/api/v1/auth/login';
  register: '/api/v1/auth/register';
  logout: '/api/v1/auth/logout';
  refreshToken: '/api/v1/auth/refresh';

  // Users
  getUsers: '/api/v1/users';
  getUser: (id: string) => string;
  updateUser: (id: string) => string;
  deleteUser: (id: string) => string;

  // Teams
  getTeams: '/api/v1/teams';
  getTeam: (id: string) => string;
  createTeam: '/api/v1/teams';
  updateTeam: (id: string) => string;
  deleteTeam: (id: string) => string;
  addTeamMember: (id: string) => string;
  removeTeamMember: (id: string, userId: string) => string;

  // Assessments
  getAssessments: '/api/v1/assessments';
  getAssessment: (id: string) => string;
  createAssessment: '/api/v1/assessments';
  updateAssessment: (id: string) => string;
  deleteAssessment: (id: string) => string;

  // Responses
  getResponses: '/api/v1/responses';
  getResponse: (id: string) => string;
  startResponse: '/api/v1/responses/start';
  submitResponse: (id: string) => string;
  saveProgress: (id: string) => string;

  // Team Personality
  getTeamComposition: (teamId: string) => string;
  compareTeams: '/api/v1/teams/compare';

  // Analytics
  getTeamAnalytics: (teamId: string) => string;
  getUserAnalytics: (userId: string) => string;

  // Health
  health: '/api/v1/health';
}

// ============================================================================
// HTTP CLIENT CONFIG
// ============================================================================

export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
}

// ============================================================================
// EXPORT DEFAULTS
// ============================================================================

export const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : 'http://localhost:8000');

export const ENDPOINTS: ApiEndpoints = {
  login: '/api/v1/auth/login',
  register: '/api/v1/auth/register',
  logout: '/api/v1/auth/logout',
  refreshToken: '/api/v1/auth/refresh',

  getUsers: '/api/v1/users',
  getUser: (id: string) => `/api/v1/users/${id}`,
  updateUser: (id: string) => `/api/v1/users/${id}`,
  deleteUser: (id: string) => `/api/v1/users/${id}`,

  getTeams: '/api/v1/teams',
  getTeam: (id: string) => `/api/v1/teams/${id}`,
  createTeam: '/api/v1/teams',
  updateTeam: (id: string) => `/api/v1/teams/${id}`,
  deleteTeam: (id: string) => `/api/v1/teams/${id}`,
  addTeamMember: (id: string) => `/api/v1/teams/${id}/members`,
  removeTeamMember: (id: string, userId: string) => `/api/v1/teams/${id}/members/${userId}`,

  getAssessments: '/api/v1/assessments',
  getAssessment: (id: string) => `/api/v1/assessments/${id}`,
  createAssessment: '/api/v1/assessments',
  updateAssessment: (id: string) => `/api/v1/assessments/${id}`,
  deleteAssessment: (id: string) => `/api/v1/assessments/${id}`,

  getResponses: '/api/v1/responses',
  getResponse: (id: string) => `/api/v1/responses/${id}`,
  startResponse: '/api/v1/responses/start',
  submitResponse: (id: string) => `/api/v1/responses/${id}/submit`,
  saveProgress: (id: string) => `/api/v1/responses/${id}/save`,

  getTeamComposition: (teamId: string) => `/api/v1/teams/${teamId}/personality`,
  compareTeams: '/api/v1/teams/compare',

  getTeamAnalytics: (teamId: string) => `/api/v1/analytics/team/${teamId}`,
  getUserAnalytics: (userId: string) => `/api/v1/analytics/user/${userId}`,

  health: '/api/v1/health',
};
