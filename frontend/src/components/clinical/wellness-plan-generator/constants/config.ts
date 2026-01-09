/**
 * Wellness Plan Generator - Configuration Constants
 */

import { Domain } from '../types';

export const DOMAINS: Domain[] = [
  { id: 'physical', name: 'Physical Wellness', icon: '💪', description: 'Physical health, fitness, and lifestyle habits', color: 'bg-red-50 border-red-200' },
  { id: 'emotional', name: 'Emotional Wellness', icon: '❤️', description: 'Emotional regulation and mental wellbeing', color: 'bg-pink-50 border-pink-200' },
  { id: 'social', name: 'Social Wellness', icon: '👥', description: 'Relationships and social connections', color: 'bg-blue-50 border-blue-200' },
  { id: 'intellectual', name: 'Intellectual Wellness', icon: '🧠', description: 'Cognitive health and continuous learning', color: 'bg-purple-50 border-purple-200' },
  { id: 'spiritual', name: 'Spiritual Wellness', icon: '🌟', description: 'Purpose, meaning, and values', color: 'bg-yellow-50 border-yellow-200' },
  { id: 'occupational', name: 'Occupational Wellness', icon: '💼', description: 'Work-life balance and career satisfaction', color: 'bg-green-50 border-green-200' },
  { id: 'environmental', name: 'Environmental Wellness', icon: '🏠', description: 'Living and working environment quality', color: 'bg-teal-50 border-teal-200' }
];

export const TIMEFRAMES = [
  { value: '1m', label: '1 Month - Quick Wins', description: 'Focus on immediate improvements' },
  { value: '3m', label: '3 Months - Sustainable Growth', description: 'Balanced approach for lasting change' },
  { value: '6m', label: '6 Months - Deep Transformation', description: 'Comprehensive wellness overhaul' },
  { value: '1y', label: '1 Year - Complete Lifestyle', description: 'Full lifestyle transformation' }
];

export const FOCUS_LEVELS = [
  { value: 'balanced', label: 'Balanced', description: 'Moderate focus across all areas', intensity: 0.6 },
  { value: 'focused', label: 'Focused', description: 'Targeted improvements in key areas', intensity: 0.8 },
  { value: 'intensive', label: 'Intensive', description: 'Comprehensive transformation plan', intensity: 1.0 }
];
