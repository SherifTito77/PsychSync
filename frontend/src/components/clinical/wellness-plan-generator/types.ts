/**
 * Wellness Plan Generator - Type Definitions
 */

export interface ActionStep {
  id: string;
  title: string;
  description: string;
  category: 'daily' | 'weekly' | 'monthly';
  difficulty: 'easy' | 'moderate' | 'challenging';
  time_required: string;
  resources: string[];
  completed: boolean;
  completion_date?: string;
}

export interface WellnessGoal {
  id: string;
  domain: string;
  title: string;
  description: string;
  priority: 'urgent' | 'high' | 'medium' | 'low';
  target_date: string;
  current_score: number;
  target_score: number;
  action_steps: ActionStep[];
}

export interface Milestone {
  id: string;
  title: string;
  description: string;
  target_date: string;
  achieved: boolean;
  celebration: string;
}

export interface WellnessPlan {
  id: string;
  user_id: string;
  created_at: string;
  focus_areas: string[];
  goals: WellnessGoal[];
  timeline: string;
  estimated_completion: string;
  success_metrics: string[];
  potential_barriers: string[];
  support_systems: string[];
  milestones: Milestone[];
  ai_recommendations: string[];
}

export interface Domain {
  id: string;
  name: string;
  icon: string;
  description: string;
  color: string;
}

export interface AIInsight {
  category: string;
  insights: string[];
  confidence: number;
}

export interface RiskAssessment {
  burnoutRisk: string;
  adherenceProbability: string;
  supportLevel: string;
  complexityLevel: string;
}

export interface AdvancedAnalytics {
  riskAssessment: RiskAssessment;
  successPredictors: string[];
  optimizationTips: string[];
}

export interface AIInsights {
  overview: AIInsight[];
  domainSpecific: Record<string, AIInsight[]>;
  advancedAnalytics: AdvancedAnalytics;
}
