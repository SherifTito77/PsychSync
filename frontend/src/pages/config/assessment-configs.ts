// Assessment configurations - Extracted for performance optimization
// These are static configurations that should be created once, not on every render

import { Question } from '../data/phq9-question-bank';

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

// GAD-7 Questions
const GAD7_QUESTIONS: Question[] = [
  {
    id: 'gad7_1',
    text: 'Feeling nervous, anxious, or on edge',
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anxiety',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'gad7_2',
    text: 'Not being able to stop or control worrying',
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anxiety',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'gad7_3',
    text: 'Worrying too much about different things',
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anxiety',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'gad7_4',
    text: 'Trouble relaxing',
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anxiety',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'gad7_5',
    text: 'Being so restless that it is hard to sit still',
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anxiety',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'gad7_6',
    text: 'Becoming easily annoyed or irritable',
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anxiety',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'gad7_7',
    text: 'Feeling afraid, as if something awful might happen',
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anxiety',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
];

// PSS-10 Questions
const PSS_QUESTIONS: Question[] = [
  {
    id: 'pss_1',
    text: 'In the last month, how often have you been upset because of something that happened unexpectedly?',
    options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'],
    required: true,
    category: 'stress',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'pss_2',
    text: 'In the last month, how often have you felt that you were unable to control the important things in your life?',
    options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'],
    required: true,
    category: 'stress',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'pss_3',
    text: 'In the last month, how often have you felt nervous and "stressed"?',
    options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'],
    required: true,
    category: 'stress',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'pss_4',
    text: 'In the last month, how often have you felt confident about your ability to handle your personal problems?',
    options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'],
    required: true,
    category: 'stress',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'pss_5',
    text: 'In the last month, how often have you felt that things were going your way?',
    options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'],
    required: true,
    category: 'stress',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'pss_6',
    text: 'In the last month, how often have you found that you could not cope with all the things that you had to do?',
    options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'],
    required: true,
    category: 'stress',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'pss_7',
    text: 'In the last month, how often have you been able to control irritations in your life?',
    options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'],
    required: true,
    category: 'stress',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'pss_8',
    text: 'In the last month, how often have you felt that you were on top of things?',
    options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'],
    required: true,
    category: 'stress',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'pss_9',
    text: 'In the last month, how often have you been angered because of things that were outside of your control?',
    options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'],
    required: true,
    category: 'stress',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'pss_10',
    text: 'In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?',
    options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'],
    required: true,
    category: 'stress',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
];

// Scoring configurations
export const PHQ9_SCORING: ScoringConfig = {
  min: 0,
  max: 27,
  levels: [
    { range: [0, 4], label: 'Minimal', color: 'green', description: 'Little to no depression symptoms' },
    { range: [5, 9], label: 'Mild', color: 'yellow', description: 'Mild depression symptoms' },
    { range: [10, 14], label: 'Moderate', color: 'orange', description: 'Moderate depression symptoms' },
    { range: [15, 19], label: 'Moderately Severe', color: 'red', description: 'Moderately severe depression symptoms' },
    { range: [20, 27], label: 'Severe', color: 'red', description: 'Severe depression symptoms' },
  ],
};

export const GAD7_SCORING: ScoringConfig = {
  min: 0,
  max: 21,
  levels: [
    { range: [0, 4], label: 'Minimal', color: 'green', description: 'Little to no anxiety symptoms' },
    { range: [5, 9], label: 'Mild', color: 'yellow', description: 'Mild anxiety symptoms' },
    { range: [10, 14], label: 'Moderate', color: 'orange', description: 'Moderate anxiety symptoms' },
    { range: [15, 21], label: 'Severe', color: 'red', description: 'Severe anxiety symptoms' },
  ],
};

export const PSS_SCORING: ScoringConfig = {
  min: 0,
  max: 40,
  levels: [
    { range: [0, 13], label: 'Minimal', color: 'green', description: 'Low perceived stress' },
    { range: [14, 20], label: 'Mild', color: 'yellow', description: 'Mild perceived stress' },
    { range: [21, 27], label: 'Moderate', color: 'orange', description: 'Moderate perceived stress' },
    { range: [28, 40], label: 'Severe', color: 'red', description: 'High perceived stress' },
  ],
};

// Base assessment configurations
export const BASE_ASSESSMENTS: Record<string, AssessmentData> = {
  phq9: {
    title: 'PHQ-9 Depression Screening',
    description: 'Patient Health Questionnaire-9 - Enhanced Assessment',
    instructions: 'Over the last 2 weeks, how often have you been bothered by any of the following problems?',
    questions: [], // Will be populated dynamically
    scoring: PHQ9_SCORING,
  },
  gad7: {
    title: 'GAD-7 Anxiety Screening',
    description: 'Generalized Anxiety Disorder-7',
    instructions: 'Over the last 2 weeks, how often have you been bothered by the following problems?',
    questions: GAD7_QUESTIONS,
    scoring: GAD7_SCORING,
  },
  stress: {
    title: 'Perceived Stress Scale (PSS)',
    description: 'Perceived Stress Scale - Stress Assessment',
    instructions: 'In the last month, how often have you felt the following ways?',
    questions: PSS_QUESTIONS,
    scoring: PSS_SCORING,
  },
};

// Helper function to get assessment config
export const getAssessmentConfig = (tool: string): AssessmentData | null => {
  return BASE_ASSESSMENTS[tool] || null;
};
