// frontend/src/types/hris.ts - HRIS Analytics Types with Assessment Integration

export interface Employee {
  id: string;
  name: string;
  email?: string;
  position: string;
  department: string;
  location: string;
  status: 'Active' | 'Inactive' | 'On Leave';
  hire_date?: string;
  avatar_url?: string;
  // Assessment Integration
  assessment_data?: EmployeeAssessmentData;
}

export interface EmployeeAssessmentData {
  last_assessment_date?: string;
  assessments_completed: number;
  personality_profile?: PersonalityProfileSummary;
  big_five_scores?: BigFiveScores;
  mbti_type?: string;
  emotional_intelligence?: number;
  leadership_potential?: number;
  team_fit_score?: number;
  strengths?: string[];
  development_areas?: string[];
}

export interface PersonalityProfileSummary {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
  dominant_traits?: string[];
  communication_style?: string;
  work_style?: string;
}

export interface BigFiveScores {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
}

export interface DepartmentAnalytics {
  name: string;
  employee_count: number;
  percentage: number;
  avg_leadership_potential?: number;
  avg_team_fit?: number;
  top_traits?: string[];
  assessment_completion_rate?: number;
}

export interface HRISStatistics {
  totalEmployees: number;
  totalDepartments: number;
  totalPositions: number;
  totalLocations: number;
  activePercentage: number;
  assessmentCompletionRate?: number;
  avgLeadershipPotential?: number;
  departmentCounts: Array<{
    name: string;
    count: number;
    percentage: number;
  }>;
  positionCounts: Record<string, number>;
  locationCounts: Record<string, number>;
  traitDistribution?: Record<string, number>;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  percentage?: number;
}

export interface HRISExportData {
  employees: Employee[];
  statistics: HRISStatistics;
  export_date: string;
  filters?: {
    department?: string;
    location?: string;
    status?: string;
  };
}

export interface AssessmentAnalytics {
  total_assessments: number;
  completion_rate: number;
  avg_emotional_intelligence: number;
  leadership_distribution: {
    high: number;
    medium: number;
    low: number;
  };
  trait_averages: PersonalityProfileSummary;
}
