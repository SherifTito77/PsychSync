// src/types/orchestrator.ts
// AI Assessment Orchestrator types for intelligent assessment recommendations

export type AssessmentCategory =
  | 'personality'
  | 'clinical'
  | 'team'
  | 'behavioral'
  | 'strengths'
  | 'career';

export type AssessmentFramework =
  | 'big_five'
  | 'mbti'
  | 'enneagram'
  | 'disc'
  | 'predictive_index'
  | 'clifton_strengths'
  | 'social_styles'
  | 'phq9'
  | 'gad7'
  | 'stress'
  | 'wellbeing';

export interface UserContext {
  userId: string;
  role: string; // 'hr_manager', 'team_lead', 'individual', 'clinician'
  goals: string[];
  industry?: string;
  teamSize?: number;
  previousAssessments: AssessmentHistory[];
  completionRate: number;
  timeSinceLastAssessment: number; // Days
  interests: string[];
}

export interface AssessmentHistory {
  assessmentId: string;
  framework: AssessmentFramework;
  completedAt: string;
  score?: number;
  category: AssessmentCategory;
  skipped?: boolean;
  incomplete?: boolean;
}

export interface Recommendation {
  assessmentId: string;
  framework: AssessmentFramework;
  category: AssessmentCategory;
  name: string;
  description: string;
  estimatedTime: number; // Minutes
  priority: 'high' | 'medium' | 'low';
  confidence: number; // 0-1
  reasoning: string[];
  benefits: string[];
  prerequisites?: string[];
  relatedAssessments?: string[];
}

export interface OrchestratorInsight {
  type: 'opportunity' | 'gap' | 'next_step' | 'trend';
  title: string;
  description: string;
  actionable: boolean;
  recommendations: string[];
}

export interface AssessmentPath {
  pathId: string;
  name: string;
  description: string;
  duration: number; // Total minutes
  assessments: Recommendation[];
  expectedOutcome: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  targetAudience: string[];
}

export interface OrchestratorResponse {
  topRecommendations: Recommendation[];
  personalizedPath?: AssessmentPath;
  insights: OrchestratorInsight[];
  alternatives: Recommendation[];
  totalOptions: number;
  generatedAt: string;
}

export interface OrchestratorConfig {
  maxRecommendations: number;
  includeClinicalTools: boolean;
  prioritizeTeamFeatures: boolean;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'all';
  categories?: AssessmentCategory[];
  excludeFrameworks?: AssessmentFramework[];
  maxTimeAvailable?: number; // Minutes
}
