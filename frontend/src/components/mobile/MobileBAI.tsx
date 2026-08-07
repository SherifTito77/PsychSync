/**
 * Mobile BAI (Beck Anxiety Inventory)
 *
 * Mobile-optimized version of the BAI assessment
 * 21 questions, 0-3 severity scale
 * Total score range: 0-63
 *
 * Measures SEVERITY of anxiety symptoms, not frequency
 */

import React from 'react';
import api from '@/services/api';
import { MobileAssessmentWizard } from './MobileAssessmentWizard';

// BAI Questions (21 items) - Measures symptom SEVERITY
const BAI_QUESTIONS = [
  {
    id: '1',
    text: 'Numbness or tingling',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '2',
    text: 'Feeling hot',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '3',
    text: 'Wobbliness in legs',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '4',
    text: 'Unable to relax',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Cognitive',
  },
  {
    id: '5',
    text: 'Fear of worst happening',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '6',
    text: 'Dizzy or lightheaded',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '7',
    text: 'Heart pounding or racing',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '8',
    text: 'Unsteady',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '9',
    text: 'Terrified or afraid',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Cognitive',
  },
  {
    id: '10',
    text: 'Nervous',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Cognitive',
  },
  {
    id: '11',
    text: 'Feeling of choking',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '12',
    text: 'Hands trembling',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '13',
    text: 'Shaky / unsteady',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '14',
    text: 'Fear of losing control',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '15',
    text: 'Difficulty breathing',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '16',
    text: 'Fear of dying',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '17',
    text: 'Scared',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '18',
    text: 'Indigestion / discomfort in stomach',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '19',
    text: 'Faint / lightheaded',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '20',
    text: 'Face flushed',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '21',
    text: 'Sweating (not due to heat)',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
];

export function MobileBAI() {
  const handleSubmit = async (responses: Record<string, number>) => {
    const response = await api.post('/clinical/BAI/submit', responses);
    return response.data as void;
  };

  return (
    <MobileAssessmentWizard
      title="Beck Anxiety Inventory"
      description="This assessment measures the severity of anxiety symptoms. Please rate how much each symptom has bothered you DURING THE PAST WEEK, including today."
      questions={BAI_QUESTIONS}
      onSubmit={handleSubmit}
      submitEndpoint="/api/v1/clinical/BAI/submit"
      showCategory={true}
    />
  );
}

export default MobileBAI;
