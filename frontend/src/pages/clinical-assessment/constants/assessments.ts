/**
 * Clinical Assessment Configurations
 *
 * Assessment configurations for different clinical tools (PHQ-9, GAD-7, PSS, etc.).
 * Contains scoring levels and metadata for each assessment type.
 */

import { AssessmentData } from '../types';

export const ASSESSMENT_CONFIGS: Record<string, AssessmentData> = {
  phq9: {
    title: 'PHQ-9 Depression Screening',
    description: 'Patient Health Questionnaire-9 - Enhanced Assessment',
    instructions: 'Over the last 2 weeks, how often have you been bothered by any of the following problems?',
    questions: [], // Will be populated dynamically from question bank
    scoring: {
      min: 0,
      max: 27,
      levels: [
        { range: [0, 4], label: 'Minimal', color: 'green', description: 'Little to no depression symptoms' },
        { range: [5, 9], label: 'Mild', color: 'yellow', description: 'Mild depression symptoms' },
        { range: [10, 14], label: 'Moderate', color: 'orange', description: 'Moderate depression symptoms' },
        { range: [15, 19], label: 'Moderately Severe', color: 'red', description: 'Moderately severe depression symptoms' },
        { range: [20, 27], label: 'Severe', color: 'red', description: 'Severe depression symptoms' },
      ],
    },
  },
  gad7: {
    title: 'GAD-7 Anxiety Screening',
    description: 'Generalized Anxiety Disorder-7',
    instructions: 'Over the last 2 weeks, how often have you been bothered by the following problems?',
    questions: [
      { id: 'gad7_1', text: 'Feeling nervous, anxious, or on edge', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
      { id: 'gad7_2', text: 'Not being able to stop or control worrying', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
      { id: 'gad7_3', text: 'Worrying too much about different things', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
      { id: 'gad7_4', text: 'Trouble relaxing', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
      { id: 'gad7_5', text: 'Being so restless that it is hard to sit still', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
      { id: 'gad7_6', text: 'Becoming easily annoyed or irritable', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
      { id: 'gad7_7', text: 'Feeling afraid, as if something awful might happen', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
    ],
    scoring: {
      min: 0,
      max: 21,
      levels: [
        { range: [0, 4], label: 'Minimal', color: 'green', description: 'Little to no anxiety symptoms' },
        { range: [5, 9], label: 'Mild', color: 'yellow', description: 'Mild anxiety symptoms' },
        { range: [10, 14], label: 'Moderate', color: 'orange', description: 'Moderate anxiety symptoms' },
        { range: [15, 21], label: 'Severe', color: 'red', description: 'Severe anxiety symptoms' },
      ],
    },
  },
  stress: {
    title: 'Perceived Stress Scale (PSS)',
    description: 'Perceived Stress Scale - Stress Assessment',
    instructions: 'In the last month, how often have you felt the following ways?',
    questions: [], // Will be populated dynamically with PSS-10 questions
    scoring: {
      min: 0,
      max: 40,
      levels: [
        { range: [0, 13], label: 'Minimal', color: 'green', description: 'Low perceived stress' },
        { range: [14, 20], label: 'Mild', color: 'yellow', description: 'Mild perceived stress' },
        { range: [21, 27], label: 'Moderate', color: 'orange', description: 'Moderate perceived stress' },
        { range: [28, 40], label: 'Severe', color: 'red', description: 'High perceived stress' },
      ],
    },
  },
};
