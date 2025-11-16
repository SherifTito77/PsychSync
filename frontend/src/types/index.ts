// src/types/index.ts - Main Type Definitions
// --- User & Authentication Types ---
// This interface should match your backend's UserOut schema
export interface User {
  id: string; // Changed from number to string (UUID)
  email: string;
  full_name: string; // Changed from 'name' to 'full_name'
  is_active: boolean;
  created_at: string;
  updated_at: string;
  avatar_url?: string;
  // Optional fields for future-proofing, as they are not in the current backend schema
  is_verified?: boolean;
  role?: 'user' | 'admin' | 'super_admin';
}
// Data sent to the login API endpoint
export interface LoginCredentials {
  email: string;
  password: string;
}
// Data for the login form UI (can include extra fields)
export interface LoginFormData extends LoginCredentials {
  rememberMe?: boolean;
}
// Data sent to the registration API endpoint
export interface RegisterData {
  email: string;
  full_name: string; // Changed from 'name' to match backend
  password: string;
}
// Data for the registration form UI
export interface RegisterFormData extends RegisterData {
  confirmPassword: string;
}
// Response from the login endpoint
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
export interface PasswordChangeData {
  current_password: string;
  new_password: string;
}
// --- API & General Types ---
// Generic API response wrapper
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}
// For handling validation errors from the backend
export interface ValidationError {
  field: string;
  message: string;
}
// --- Team Types ---
// Note: If your backend uses UUIDs for teams, change 'id' to 'string'
export interface Team {
  id: number;
  name: string;
  status: 'active' | 'inactive';
  description: string;
}
// --- Dashboard & Analytics Types ---
export interface DashboardData {
  totalTeams: number;
  totalAssessments: number;
  avgCompatibility: number;
  predictedVelocity: number;
}
export interface PersonalityProfile {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
  leadership_potential?: number;
  collaboration_index?: number;
  stress_tolerance?: number;
  adaptability?: number;
  communication_style?: string;
  work_preferences?: string[];
}
// --- Assessment Types ---
export interface AssessmentResult {
  id: string;
  framework: string;
  results: Record<string, any>;
  confidence: number;
  created_at: string;
}
// --- Notification Types ---
export interface Notification {
  id: number;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  duration: number;
}
// --- Admin Types ---
export interface AdminUserUpdate {
  is_active?: boolean;
  role?: 'user' | 'admin' | 'super_admin';
}
// --- Anonymous Feedback Types ---
export interface AnonymousFeedbackSubmission {
  organization_id: string;
  feedback_type: string;
  category: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  target_type?: string;
  target_id?: string;
  evidence_urls?: string[];
  incident_date?: string;
}
export interface FeedbackSubmissionResult {
  success: boolean;
  tracking_id?: string;
  message?: string;
  error?: string;
  alternatives?: string[];
}
export interface AnonymousFeedbackStatus {
  tracking_id: string;
  status: 'pending' | 'under_review' | 'investigating' | 'resolved' | 'closed';
  severity: string;
  category: string;
  created_at: string;
  last_updated: string;
  hr_notes?: string;
  resolution_details?: string;
  estimated_resolution?: string;
  follow_ups_allowed: boolean;
  anonymous_follow_ups: number;
}
export interface FeedbackFollowUp {
  tracking_id: string;
  message: string;
  evidence_urls?: string[];
}
export interface FeedbackAnalytics {
  total_submissions: number;
  submissions_by_category: Record<string, number>;
  submissions_by_severity: Record<string, number>;
  resolution_rate: number;
  average_resolution_time: number;
  pending_count: number;
  critical_count: number;
  monthly_trends: Array<{
    month: string;
    submissions: number;
    resolved: number;
  }>;
}
export interface HRFeedbackItem {
  id: string;
  tracking_id: string;
  status: string;
  severity: string;
  category: string;
  description: string;
  created_at: string;
  last_updated: string;
  target_type?: string;
  incident_date?: string;
  evidence_urls?: string[];
  follow_ups_count: number;
  resolution_details?: string;
  hr_notes?: string;
  assigned_hr?: string;
  priority_score: number;
}