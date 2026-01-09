/**
 * Clinical Assessment Types
 *
 * Shared types for clinical assessment components
 */

export interface Question {
  id: string;
  text: string;
  options: string[];
  required: boolean;
  category: string;
  difficulty: 'basic' | 'intermediate' | 'advanced';
  severity_weight: number;
  core_concept: boolean;
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

export interface AssessmentQuestion {
  id: number | string;
  text: string;
  options: string[];
  required: boolean;
}

export interface AssessmentData {
  title: string;
  description: string;
  instructions: string;
  questions: AssessmentQuestion[];
  scoring: ScoringConfig;
}

export interface AssessmentProps {
  tool?: string;
  action?: string;
  onComplete?: (responses: Record<string, string>) => void;
  onCancel?: () => void;
}

export interface CrisisResources {
  title: string;
  description: string;
  phone?: string;
  website?: string;
  available: string;
}
