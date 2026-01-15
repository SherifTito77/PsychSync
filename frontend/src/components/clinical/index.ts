/**
 * Clinical Screening Components
 *
 * Evidence-based mental health screening tools for PsychSync
 *
 * Components:
 * - PHQ9Screening: Depression screening (9 items)
 * - GAD7Screening: Anxiety screening (7 items)
 * - CSSRSScreening: Suicide risk screening (6 items)
 * - CrisisResources: Crisis support resources
 * - SafetyPlan: Personal safety plan builder
 */

export { PHQ9Screening } from './PHQ9Screening';
export { GAD7Screening } from './GAD7Screening';
export { CSSRSScreening } from './CSSRSScreening';
export { CrisisResources, CrisisBanner, SafetyPlan } from './CrisisResources';

// Types
export interface ScreeningResult {
  id: string;
  screening_type: string;
  total_score: number;
  severity_level: string;
  risk_level: string;
  interpretation: string;
  recommendations: string[];
  crisis_alert: boolean;
  risk_flags: string[];
  completed_at?: string;
}

export interface ConsentForm {
  consent_type: string;
  screening_types: string[];
  agreed_to_data_usage: boolean;
  understands_purpose: boolean;
}
