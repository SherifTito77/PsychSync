/**
 * Mobile Y-BOCS (Yale-Brown Obsessive Compulsive Scale)
 *
 * Mobile-optimized OCD severity assessment
 * 10 questions (5 obsessions + 5 compulsions)
 * 0-4 severity scale per question
 * Total score range: 0-40
 *
 * Gold standard for OCD assessment
 */

import React from 'react';
import api from '@/services/api';
import { MobileAssessmentWizard } from './MobileAssessmentWizard';

// Y-BOCS Questions (10 items)
const YBOCS_QUESTIONS = [
  // Obsession Items (1-5)
  {
    id: 'item_1_time_obsessions',
    text: 'Time occupied by obsessive thoughts',
    options: [
      { value: 0, text: 'None - Not at all' },
      { value: 1, text: 'Mild - Less than 1 hour/day' },
      { value: 2, text: 'Moderate - 1-3 hours/day' },
      { value: 3, text: 'Severe - 3-8 hours/day' },
      { value: 4, text: 'Extreme - More than 8 hours/day' },
    ],
    category: 'Obsessions',
  },
  {
    id: 'item_2_interference_obsessions',
    text: 'Interference due to obsessive thoughts',
    options: [
      { value: 0, text: 'None - No interference' },
      { value: 1, text: 'Mild - Slight interference' },
      { value: 2, text: 'Moderate - Definite, but manageable' },
      { value: 3, text: 'Severe - Substantial impairment' },
      { value: 4, text: 'Extreme - Incapacitating' },
    ],
    category: 'Obsessions',
  },
  {
    id: 'item_3_distress_obsessions',
    text: 'Distress associated with obsessive thoughts',
    options: [
      { value: 0, text: 'None - No distress' },
      { value: 1, text: 'Mild - Not too disturbing' },
      { value: 2, text: 'Moderate - Disturbing, but manageable' },
      { value: 3, text: 'Severe - Very disturbing' },
      { value: 4, text: 'Extreme - Constant, disabling distress' },
    ],
    category: 'Obsessions',
  },
  {
    id: 'item_4_resistance_obsessions',
    text: 'Resistance against obsessive thoughts',
    options: [
      { value: 0, text: 'N/A - No attempt needed' },
      { value: 1, text: 'Mild - Try to resist most of the time' },
      { value: 2, text: 'Moderate - Try to resist some of the time' },
      { value: 3, text: 'Severe - Yield to almost all obsessions' },
      { value: 4, text: 'Extreme - Completely give in to all' },
    ],
    category: 'Obsessions',
  },
  {
    id: 'item_5_control_obsessions',
    text: 'Degree of control over obsessive thoughts',
    options: [
      { value: 0, text: 'Complete - Full control' },
      { value: 1, text: 'Much - Usually able to control' },
      { value: 2, text: 'Moderate - Sometimes can control' },
      { value: 3, text: 'Little - Rarely able to control' },
      { value: 4, text: 'None - Control completely absent' },
    ],
    category: 'Obsessions',
  },

  // Compulsion Items (6-10)
  {
    id: 'item_6_time_compulsions',
    text: 'Time spent performing compulsive behaviors',
    options: [
      { value: 0, text: 'None - Not at all' },
      { value: 1, text: 'Mild - Less than 1 hour/day' },
      { value: 2, text: 'Moderate - 1-3 hours/day' },
      { value: 3, text: 'Severe - 3-8 hours/day' },
      { value: 4, text: 'Extreme - More than 8 hours/day' },
    ],
    category: 'Compulsions',
  },
  {
    id: 'item_7_interference_compulsions',
    text: 'Interference due to compulsive behaviors',
    options: [
      { value: 0, text: 'None - No interference' },
      { value: 1, text: 'Mild - Slight interference' },
      { value: 2, text: 'Moderate - Definite, but manageable' },
      { value: 3, text: 'Severe - Substantial impairment' },
      { value: 4, text: 'Extreme - Incapacitating' },
    ],
    category: 'Compulsions',
  },
  {
    id: 'item_8_distress_compulsions',
    text: 'Distress if prevented from performing compulsions',
    options: [
      { value: 0, text: 'None - No distress' },
      { value: 1, text: 'Mild - Only slight distress' },
      { value: 2, text: 'Moderate - Moderate, but manageable' },
      { value: 3, text: 'Severe - Very distressing' },
      { value: 4, text: 'Extreme - Overwhelming, disabling' },
    ],
    category: 'Compulsions',
  },
  {
    id: 'item_9_resistance_compulsions',
    text: 'Resistance against compulsive behaviors',
    options: [
      { value: 0, text: 'N/A - No attempt needed' },
      { value: 1, text: 'Mild - Try to resist most of the time' },
      { value: 2, text: 'Moderate - Try to resist some of the time' },
      { value: 3, text: 'Severe - Yield to almost all compulsions' },
      { value: 4, text: 'Extreme - Completely give in to all' },
    ],
    category: 'Compulsions',
  },
  {
    id: 'item_10_control_compulsions',
    text: 'Degree of control over compulsive behaviors',
    options: [
      { value: 0, text: 'Complete - Full control' },
      { value: 1, text: 'Much - Usually able to control' },
      { value: 2, text: 'Moderate - Sometimes can control' },
      { value: 3, text: 'Little - Rarely able to control' },
      { value: 4, text: 'None - Control completely absent' },
    ],
    category: 'Compulsions',
  },
];

export function MobileYBOCS() {
  const handleSubmit = async (responses: Record<string, number>) => {
    const response = await api.post('/api/v1/clinical/YBOCS/submit', responses);
    return response.data;
  };

  return (
    <MobileAssessmentWizard
      title="Yale-Brown OCD Scale (Y-BOCS)"
      description="This assessment measures the severity of obsessive-compulsive symptoms. Rate each item based on your experiences THIS WEEK."
      questions={YBOCS_QUESTIONS}
      onSubmit={handleSubmit}
      submitEndpoint="/api/v1/clinical/YBOCS/submit"
      showCategory={true}
    />
  );
}

export default MobileYBOCS;
