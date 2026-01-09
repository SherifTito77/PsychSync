/**
 * Wellbeing Assessment Types
 *
 * Shared types and interfaces for wellbeing assessment components.
 */

export interface WellbeingQuestion {
  id: string;
  category: string;
  text: string;
  options: string[];
}

export interface CategoryScore {
  category: string;
  score: number;
  maxScore: number;
  percentage: number;
  level: 'low' | 'medium' | 'high';
}

export interface WellbeingGoal {
  id: string;
  category: string;
  actionItems: string[];
  targetDate: Date;
  completed: boolean;
  createdAt: Date;
}

export interface WellnessStreak {
  currentStreak: number;
  longestStreak: number;
  lastAssessmentDate: string | null;
}

export interface StoredAssessmentResult {
  id: string;
  date: string;
  overallPercentage: number;
  categoryScores: CategoryScore[];
}

export interface AssessmentResponse {
  questionId: string;
  answer: string;
  timestamp: Date;
}
