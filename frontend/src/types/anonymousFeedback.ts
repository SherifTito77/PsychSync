// Anonymous Feedback System Types
// Complete type definitions for the anonymous feedback system with enhanced privacy features
export interface AnonymousFeedbackSubmission {
  feedback_type: string;
  category: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  target_type?: string;
  target_id?: string;
  evidence_urls?: string[];
  incident_date?: string;
  organization_id: string;
}
export interface FeedbackCategory {
  description: string;
  subcategories: string[];
  severity_levels: string[];
}
export interface FeedbackCategories {
  [key: string]: FeedbackCategory;
}
export interface FeedbackSubmissionResponse {
  success: boolean;
  tracking_id: string;
  submission_id: string;
  message: string;
  instructions: {
    tracking: string;
    timeline: string;
    status_check: string;
    escalation: string;
  };
  privacy_guarantee: {
    anonymous: string;
    untraceable: string;
    no_logging: string;
    protection: string;
  };
  next_steps: string[];
  support_resources: SupportResource[];
}
export interface SupportResource {
  name: string;
  description: string;
  contact: string;
}
export interface FeedbackStatusResponse {
  found: boolean;
  status?: string;
  status_description?: string;
  submitted_at?: string;
  last_updated?: string;
  days_since_submission?: number;
  estimated_resolution_days?: number;
  public_notes?: string;
  severity?: string;
  category?: string;
  review_timeline?: string;
  privacy_reminder: string;
  can_follow_up: boolean;
  follow_up_url?: string;
  next_steps: string[];
  message?: string;
  help?: string;
  alternatives?: string[];
}
export interface FeedbackItemForReview {
  id: string;
  feedback_type: string;
  category: string;
  description: string;
  severity: string;
  target_type?: string;
  target_id_hash?: string;
  incident_date?: string;
  submitted_at: string;
  days_pending: number;
  status: string;
  evidence_count: number;
  urgency_score: number;
  recommended_actions: string[];
  psychological_safety_impact: PsychologicalSafetyImpact;
}
export interface PsychologicalSafetyImpact {
  severity_level: string;
  affected_area: string;
  requires_intervention: boolean;
  potential_team_impact: boolean;
}
export interface FeedbackReviewResponse {
  feedbacks: FeedbackItemForReview[];
  summary: FeedbackSummary;
  total_count: number;
  reviewer_id: string;
  review_timestamp: string;
  privacy_guidelines: string[];
}
export interface FeedbackSummary {
  by_category: { [key: string]: number };
  by_severity: { [key: string]: number };
  by_status: { [key: string]: number };
  by_type: { [key: string]: number };
  average_urgency_score: number;
  critical_count: number;
  high_priority_count: number;
  pending_review_count: number;
  psychological_safety_concerns: number;
  requires_immediate_action: number;
}
export interface FeedbackUpdateRequest {
  new_status: 'pending_review' | 'investigating' | 'resolved' | 'closed' | 'requires_more_info' | 'escalated';
  internal_notes?: string;
  public_notes?: string;
  actions_taken?: string;
}
export interface FeedbackStatisticsResponse {
  total_submissions: number;
  analysis_period_days: number;
  category_breakdown: { [key: string]: number };
  severity_breakdown: { [key: string]: number };
  status_breakdown: { [key: string]: number };
  type_breakdown: { [key: string]: number };
  submission_trends: { [key: string]: number };
  average_resolution_time?: number;
  insights: {
    psychological_safety_level: string;
    primary_concerns: PrimaryConcern[];
    trending_issues: TrendingIssue[];
    recommendations: string[];
  };
  benchmark_comparison: {
    submission_rate: {
      your_organization: number;
      industry_average: number;
      performance: string;
    };
    critical_issue_rate: {
      your_organization: number;
      industry_average: number;
      performance: string;
    };
    psychological_safety_health: {
      your_organization: string;
      industry_standard: string;
      gap: string;
    };
  };
  data_quality: {
    sample_size: number;
    confidence_level: string;
    period_completeness: string;
  };
}
export interface PrimaryConcern {
  category: string;
  count: number;
  severity_breakdown: { [key: string]: number };
  trend: string;
}
export interface TrendingIssue {
  category: string;
  recent_week: number;
  previous_week: number;
  trend_direction: 'increasing' | 'decreasing' | 'stable';
  trend_percentage: number;
}
export interface ReportingGuidelinesResponse {
  anonymous_feedback: {
    name: string;
    description: string;
    best_for: string[];
    how_to_access: string;
    privacy_level: string;
    protections: string[];
    limitations: string[];
    response_time: string;
    psychological_safety_focus: string;
  };
  confidential_hr: {
    name: string;
    description: string;
    best_for: string[];
    how_to_access: string;
    privacy_level: string;
    protections: string[];
    limitations: string[];
    response_time: string;
  };
  psychological_safety_resources: {
    name: string;
    description: string;
    resources: Array<{
      name: string;
      description: string;
      contact: string;
      available?: string;
    }>;
  };
  external_resources: {
    name: string;
    description: string;
    resources: Array<{
      name: string;
      description: string;
      contact: string;
      website?: string;
      handles: string[];
    }>;
  };
  situation_specific_guidance: {
    psychological_safety: {
      recommended: string;
      why: string;
      specific_actions: string[];
      support_resources: string[];
    };
    toxic_behavior: {
      recommended: string;
      why: string;
      documentation_tips: string[];
    };
    harassment: {
      recommended: string;
      why: string;
      immediate_steps: string[];
    };
  };
  psychological_safety_indicators: {
    warning_signs: string[];
    healthy_indicators: string[];
  };
}
export interface AnonymousFeedbackCategoriesResponse {
  feedback_categories: FeedbackCategories;
  severity_levels: {
    low: string;
    medium: string;
    high: string;
    critical: string;
  };
  target_types: Array<{
    type: string;
    description: string;
  }>;
  privacy_guarantee: {
    complete_anonymity: string;
    no_identification: string;
    no_tracking: string;
    legal_protection: string;
  };
}
// Form validation types
export interface FeedbackFormErrors {
  feedback_type?: string;
  category?: string;
  description?: string;
  severity?: string;
  target_type?: string;
  target_id?: string;
  evidence_urls?: string;
  incident_date?: string;
  organization_id?: string;
  general?: string;
}
// UI Component Props
export interface AnonymousFeedbackFormProps {
  onSubmit: (data: AnonymousFeedbackSubmission) => Promise<void>;
  isSubmitting?: boolean;
  initialData?: Partial<AnonymousFeedbackSubmission>;
  organizationId?: string;
}
export interface FeedbackStatusCheckProps {
  trackingId: string;
  onTrackingIdChange: (id: string) => void;
}
export interface HRReviewDashboardProps {
  organizationId?: string;
  filters?: {
    status?: string;
    severity?: string;
    feedback_type?: string;
    date_from?: string;
    date_to?: string;
  };
  onFiltersChange?: (filters: any) => void;
}
// Status and priority levels
export const FEEDBACK_SEVERITY_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
} as const;
export const FEEDBACK_STATUSES = {
  PENDING_REVIEW: 'pending_review',
  INVESTIGATING: 'investigating',
  RESOLVED: 'resolved',
  CLOSED: 'closed',
  REQUIRES_MORE_INFO: 'requires_more_info',
  ESCALATED: 'escalated'
} as const;
export const TARGET_TYPES = {
  MANAGER: 'manager',
  PEER: 'peer',
  TEAM: 'team',
  DEPARTMENT: 'department',
  ORGANIZATION: 'organization',
  POLICY: 'policy'
} as const;
// Helper functions for type guards
export function isValidSeverity(value: string): value is keyof typeof FEEDBACK_SEVERITY_LEVELS {
  return Object.values(FEEDBACK_SEVERITY_LEVELS).includes(value as any);
}
export function isValidStatus(value: string): value is keyof typeof FEEDBACK_STATUSES {
  return Object.values(FEEDBACK_STATUSES).includes(value as any);
}
export function isValidTargetType(value: string): value is keyof typeof TARGET_TYPES {
  return Object.values(TARGET_TYPES).includes(value as any);
}