/**
 * App Theme Constants
 *
 * Consistent design system for PsychSync mobile app.
 * Follows mental health app best practices:
 * - Calming colors (blues, purples)
 * - Clear typography hierarchy
 * - Accessible contrast ratios (WCAG AA)
 */

import { MD3LightTheme } from 'react-native-paper';

export const theme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: '#6C63FF',
    primaryDark: '#5A52D5',
    secondary: '#26A69A',
    accent: '#FF6B6B',
    background: '#F5F5F5',
    surface: '#FFFFFF',
    error: '#EF5350',
    success: '#66BB6A',
    warning: '#FFA726',
    text: '#212121',
    textSecondary: '#757575',
    border: '#E0E0E0',
  },
  fonts: {
    regular: 'Roboto-Regular',
    medium: 'Roboto-Medium',
    bold: 'Roboto-Bold',
  },
  fontSizes: {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 18,
    xl: 20,
    xxl: 24,
    xxxl: 32,
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 16,
    xl: 24,
  },
};

export const assessmentTypes = {
  LSAS: {
    name: 'Social Anxiety',
    shortName: 'LSAS',
    description: 'Liebowitz Social Anxiety Scale',
    icon: 'people-outline',
    color: '#6C63FF',
  },
  EAT26: {
    name: 'Eating Attitudes',
    shortName: 'EAT-26',
    description: 'Eating Attitudes Test',
    icon: 'restaurant-outline',
    color: '#26A69A',
  },
  YBOCS: {
    name: 'OCD Assessment',
    shortName: 'Y-BOCS',
    description: 'Yale-Brown Obsessive Compulsive Scale',
    icon: 'refresh-outline',
    color: '#FF6B6B',
  },
  PHQ9: {
    name: 'Depression',
    shortName: 'PHQ-9',
    description: 'Patient Health Questionnaire',
    icon: 'sentiment-dissatisfied',
    color: '#9C27B0',
  },
  GAD7: {
    name: 'Anxiety',
    shortName: 'GAD-7',
    description: 'Generalized Anxiety Disorder',
    icon: 'flash-on',
    color: '#FF9800',
  },
};

export const severityLevels = {
  minimal: { color: '#66BB6A', label: 'Minimal' },
  mild: { color: '#FFA726', label: 'Mild' },
  moderate: { color: '#FF7043', label: 'Moderate' },
  moderately_severe: { color: '#EF5350', label: 'Moderately Severe' },
  severe: { color: '#C62828', label: 'Severe' },
};

export const crisisResources = [
  {
    name: 'National Suicide Prevention Lifeline',
    phone: '988',
    description: '24/7 crisis support',
  },
  {
    name: 'Crisis Text Line',
    text: 'HOME to 741741',
    description: 'Text-based crisis support',
  },
  {
    name: 'Emergency Services',
    phone: '911',
    description: 'Immediate emergency assistance',
  },
];
