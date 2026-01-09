/**
 * Clinical Results Types
 *
 * Shared types and interfaces for clinical assessment results display.
 */

export interface SeverityInfo {
  label: string;
  color: string;
  description: string;
}

export interface Resource {
  title: string;
  description: string;
  link?: string;
  phone?: string;
}

export interface AssessmentResult {
  score: number;
  severity_level: string;
  severity?: SeverityInfo;
  crisisAlert: boolean;
  recommendations: string[];
  resources: Resource[];
}

export interface AssessmentMetadata {
  assessmentId: string;
  completedAt: string;
  notes: string;
  responseData?: {
    duration?: string;
    questions_answered?: number;
    skipped_questions?: number;
  };
  providerNotified?: boolean;
  nextAssessmentDate?: string;
}

export interface AssessmentResponseData {
  total_score: number;
  severity_level: string;
  crisis_alert: boolean;
  id?: string;
  completed_at?: string;
  notes?: string;
  response_data?: {
    duration?: string;
    questions_answered?: number;
    skipped_questions?: number;
  };
  provider_notified?: boolean;
  next_assessment_date?: string;
}
