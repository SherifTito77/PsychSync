/**
 * Clinical Assessment Types
 *
 * Shared types and interfaces for clinical assessment components.
 */

export interface Question {
  id: string;
  text: string;
  options: string[];
  required: boolean;
  category?: string;
  difficulty?: 'basic' | 'intermediate' | 'advanced';
  severity_weight?: number;
  core_concept?: boolean;
}

export interface ScoringLevel {
  range: [number, number];
  label: string;
  color: string;
  description: string;
}

export interface ScoringConfig {
  min: number;
  max: number;
  levels: ScoringLevel[];
}

export interface AssessmentData {
  title: string;
  description: string;
  instructions: string;
  questions: Question[];
  scoring: ScoringConfig;
}

export interface AssessmentResponse {
  questionId: string;
  answer: string;
  timestamp: Date;
}

export interface AssessmentResult {
  score: number;
  severity_level: string;
  severity?: {
    label: string;
    color: string;
    description: string;
  };
  crisisAlert: boolean;
  responses: AssessmentResponse[];
}
