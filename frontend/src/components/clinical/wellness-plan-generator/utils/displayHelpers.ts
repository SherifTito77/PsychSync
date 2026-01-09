/**
 * Wellness Plan Generator - Display Helper Utilities
 */

import { WellnessPlan, WellnessGoal, ActionStep } from '../types';

/**
 * Get color classes for priority badges
 */
export const getPriorityColor = (priority: string): string => {
  switch (priority) {
    case 'urgent': return 'text-red-600 bg-red-50 border-red-200';
    case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
    case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'low': return 'text-green-600 bg-green-50 border-green-200';
    default: return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

/**
 * Get color classes for difficulty badges
 */
export const getDifficultyColor = (difficulty: string): string => {
  switch (difficulty) {
    case 'easy': return 'text-green-600 bg-green-50 border-green-200';
    case 'moderate': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'challenging': return 'text-red-600 bg-red-50 border-red-200';
    default: return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

/**
 * Format date string to readable format
 */
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

/**
 * Calculate completion percentage for a goal
 */
export const calculateGoalProgress = (goal: WellnessGoal): number => {
  if (!goal.action_steps || goal.action_steps.length === 0) return 0;
  const completed = goal.action_steps.filter(step => step.completed).length;
  return Math.round((completed / goal.action_steps.length) * 100);
};

/**
 * Calculate overall plan progress
 */
export const calculatePlanProgress = (plan: WellnessPlan): number => {
  if (!plan.goals || plan.goals.length === 0) return 0;
  const totalProgress = plan.goals.reduce((sum, goal) => sum + calculateGoalProgress(goal), 0);
  return Math.round(totalProgress / plan.goals.length);
};

/**
 * Get status text for milestone
 */
export const getMilestoneStatus = (achieved: boolean): string => {
  return achieved ? '🎉 Achieved!' : 'In Progress';
};

/**
 * Get category icon
 */
export const getCategoryIcon = (category: string): string => {
  switch (category) {
    case 'daily': return '📅';
    case 'weekly': return '📆';
    case 'monthly': return '🗓️';
    default: return '📋';
  }
};
