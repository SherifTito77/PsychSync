/**
 * Mobile EAT-26 (Eating Attitudes Test)
 *
 * Mobile-optimized eating disorder screening
 * 26 questions, 6-point frequency scale
 * Total score range: 0-78
 *
 * Screens for dieting, bulimia, and oral control behaviors
 */

import React from 'react';
import api from '@/services/api';
import { MobileAssessmentWizard } from './MobileAssessmentWizard';

// EAT-26 Questions (26 items)
const EAT26_QUESTIONS = [
  {
    id: '1',
    text: 'Am terrified about being overweight',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Dieting',
  },
  {
    id: '2',
    text: 'Avoid eating when I am hungry',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Oral Control',
  },
  {
    id: '3',
    text: 'Find myself preoccupied with food',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Bulimia',
  },
  {
    id: '4',
    text: 'Have gone on eating binges where I feel that I may not be able to stop',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Bulimia',
  },
  {
    id: '5',
    text: 'Cut my food into small pieces',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Oral Control',
  },
  {
    id: '6',
    text: 'Aware of the calorie content of foods that I eat',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Dieting',
  },
  {
    id: '7',
    text: 'Particularly avoid food with a high carbohydrate content',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Dieting',
  },
  {
    id: '8',
    text: 'Feel that others would prefer if I ate more',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Oral Control',
  },
  {
    id: '9',
    text: 'Vomit after I have eaten',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Bulimia',
  },
  {
    id: '10',
    text: 'Feel extremely guilty after eating',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Dieting',
  },
  {
    id: '11',
    text: 'Am preoccupied with a desire to be thinner',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Dieting',
  },
  {
    id: '12',
    text: 'Think about burning up calories when I exercise',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Dieting',
  },
  {
    id: '13',
    text: 'Other people think I am too thin',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Dieting',
  },
  {
    id: '14',
    text: 'Am occupied with thoughts of food',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Bulimia',
  },
  {
    id: '15',
    text: 'Feel that food controls my life',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Bulimia',
  },
  {
    id: '16',
    text: 'Display self-control around food',
    options: [
      { value: 0, text: 'Always' },
      { value: 0, text: 'Usually' },
      { value: 0, text: 'Often' },
      { value: 1, text: 'Sometimes' },
      { value: 2, text: 'Rarely' },
      { value: 3, text: 'Never' },
    ],
    category: 'Oral Control',
  },
  {
    id: '17',
    text: 'Feel uncomfortable after eating sweets',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Oral Control',
  },
  {
    id: '18',
    text: 'Engage in dieting behavior',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Dieting',
  },
  {
    id: '19',
    text: 'Feel that my stomach is too big',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Dieting',
  },
  {
    id: '20',
    text: 'Take longer than others to eat my meals',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Oral Control',
  },
  {
    id: '21',
    text: 'Avoid foods with sugar in them',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Dieting',
  },
  {
    id: '22',
    text: 'Eat diet foods',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Dieting',
  },
  {
    id: '23',
    text: 'Feel that others pressure me to eat',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Oral Control',
  },
  {
    id: '24',
    text: 'Give too much time and thought to food',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Bulimia',
  },
  {
    id: '25',
    text: 'Check my body for fatness',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Dieting',
  },
  {
    id: '26',
    text: 'Eat when I am upset',
    options: [
      { value: 3, text: 'Always' },
      { value: 2, text: 'Usually' },
      { value: 1, text: 'Often' },
      { value: 0, text: 'Sometimes' },
      { value: 0, text: 'Rarely' },
      { value: 0, text: 'Never' },
    ],
    category: 'Bulimia',
  },
];

export function MobileEAT26() {
  const handleSubmit = async (responses: Record<string, number>) => {
    // Convert string keys to numbers for backend
    const numberedResponses: Record<number, number> = {};
    Object.entries(responses).forEach(([key, value]) => {
      numberedResponses[parseInt(key)] = value;
    });

    const response = await api.post('/api/v1/clinical/EAT26/submit', numberedResponses);
    return response.data;
  };

  return (
    <MobileAssessmentWizard
      title="Eating Attitudes Test (EAT-26)"
      description="This screening tool helps identify eating disorder risk. Please answer how often each statement applies to you."
      questions={EAT26_QUESTIONS}
      onSubmit={handleSubmit}
      submitEndpoint="/api/v1/clinical/EAT26/submit"
      showCategory={true}
    />
  );
}

export default MobileEAT26;
