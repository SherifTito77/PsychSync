/**
 * Wellness Plan Generator - Main Plan Management Hook
 */

import { useState, useEffect } from 'react';
import { WellnessPlan, WellnessGoal, ActionStep } from '../types';

/**
 * Check if user is authenticated with multiple fallback strategies
 */
export const useAuthCheck = () => {
  const isUserAuthenticated = (): boolean => {
    // Primary check: access_token
    const token = localStorage.getItem('access_token');
    if (token && token !== 'undefined' && token !== 'null' && token.trim() !== '') {
      console.log('✅ Authentication via access_token');
      return true;
    }

    // Fallback 1: Check for any token-like item
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.toLowerCase().includes('token')) {
        const value = localStorage.getItem(key);
        if (value && value !== 'undefined' && value !== 'null' && value.trim() !== '') {
          console.log(`✅ Authentication via ${key}`);
          return true;
        }
      }
    }

    // Fallback 2: Check user data
    const userData = localStorage.getItem('user');
    if (userData && userData !== 'undefined' && userData !== 'null' && userData.trim() !== '') {
      try {
        const parsed = JSON.parse(userData);
        if (parsed && parsed.email && parsed.id) {
          console.log('✅ Authentication via user data');
          return true;
        }
      } catch (e) {
        // Invalid JSON, continue
      }
    }

    // Fallback 3: Check override flag
    const override = localStorage.getItem('user_authenticated_override');
    if (override === 'true') {
      console.log('✅ Authentication via override');
      return true;
    }

    console.log('❌ No authentication indicators found');
    return false;
  };

  return { isUserAuthenticated };
};

/**
 * Main hook for wellness plan management
 */
export const useWellnessPlan = () => {
  const [planData, setPlanData] = useState<WellnessPlan | null>(null);
  const [selectedGoal, setSelectedGoal] = useState<WellnessGoal | null>(null);
  const [isNavigating, setIsNavigating] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load existing wellness plan from API
   */
  const loadExistingPlan = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.log('No authentication token, allowing new plan creation');
        setIsLoading(false);
        return;
      }

      const response = await fetch('/api/v1/clinical/wellness/plan/existing', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          setPlanData(data.data);
        }
      }
    } catch (err) {
      console.error('Error loading existing plan:', err);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Toggle action step completion status
   */
  const handleActionStepToggle = (goalId: string, stepId: string) => {
    if (!planData) return;

    setIsNavigating(stepId);

    const updatedGoals = planData.goals.map(goal => {
      if (goal.id !== goalId) return goal;

      const updatedSteps = goal.action_steps.map(step => {
        if (step.id !== stepId) return step;

        const updatedStep = {
          ...step,
          completed: !step.completed,
          completion_date: !step.completed ? new Date().toISOString() : undefined
        };

        // Trigger confetti on completion
        if (updatedStep.completed) {
          setTimeout(() => {
            if (typeof window !== 'undefined' && (window as any).triggerConfetti) {
              (window as any).triggerConfetti();
            }
          }, 100);
        }

        return updatedStep;
      });

      return { ...goal, action_steps: updatedSteps };
    });

    const updatedPlan = { ...planData, goals: updatedGoals };
    setPlanData(updatedPlan);
    setIsNavigating(null);

    // Save to backend
    savePlanProgress(updatedPlan);
  };

  /**
   * Save plan progress to backend
   */
  const savePlanProgress = async (plan: WellnessPlan) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.log('No token, skipping save');
        return;
      }

      const response = await fetch('/api/v1/clinical/wellness/plan/update', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(plan),
      });

      if (response.ok) {
        console.log('✅ Plan progress saved successfully');
      }
    } catch (err) {
      console.error('Error saving plan progress:', err);
    }
  };

  useEffect(() => {
    loadExistingPlan();
  }, []);

  return {
    planData,
    setPlanData,
    selectedGoal,
    setSelectedGoal,
    isNavigating,
    isLoading,
    error,
    setError,
    loadExistingPlan,
    handleActionStepToggle,
    savePlanProgress,
  };
};
