/**
 * Team Composition Optimizer Types
 *
 * Shared type definitions for team optimization functionality
 */

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
  department: string;
  skills: string[];
  skillLevels: Record<string, number>;
  personalityTraits: Record<string, number>;
  performanceScore: number;
  collaborationScore: number;
  innovationScore: number;
  leadershipPotential: number;
  adaptabilityScore: number;
  yearsOfExperience: number;
  avatar?: string;
  availability: boolean;
}

export interface TeamRequirement {
  teamSize: number;
  requiredSkills: string[];
  skillWeights: Record<string, number>;
  personalityBalance: Record<string, [number, number]>;
  objectives: string[];
  experienceDistribution: Record<string, number>;
  budget: number;
  deadline: string;
  projectType: string;
}

export interface OptimizationResult {
  recommendedMembers: string[];
  teamScore: number;
  performancePrediction: number;
  skillCoverage: Record<string, number>;
  personalityBalance: Record<string, number>;
  compatibilityScore: number;
  diversityMetrics: Record<string, number>;
  riskFactors: string[];
  recommendations: string[];
  improvementOpportunities: string[];
}

export interface TeamCompositionOptimizerProps {
  currentTeamId?: string;
  projectId?: string;
  onOptimizationComplete?: (result: OptimizationResult) => void;
}

export interface PersonalityRadarData {
  trait: string;
  current: number;
  optimal: number;
  optimized: number;
}

export interface SkillCoverageData {
  skill: string;
  coverage: number;
  weight: number;
}

export interface DiversityMetricData {
  metric: string;
  current: number;
  target: number;
  improvement: number;
}

export interface PerformancePredictionData {
  phase: string;
  score: number;
}
