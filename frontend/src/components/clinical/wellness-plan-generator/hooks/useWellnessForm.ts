/**
 * Wellness Plan Generator - Form Management Hook
 */

import { useState } from 'react';
import { WellnessPlan } from '../types';

export interface WellnessFormState {
  selectedDomains: string[];
  timeframe: '1m' | '3m' | '6m' | '1y';
  focusLevel: 'balanced' | 'focused' | 'intensive';
}

/**
 * Hook for managing wellness plan generation form
 */
export const useWellnessForm = (onPlanGenerated: (plan: WellnessPlan) => void) => {
  const [selectedDomains, setSelectedDomains] = useState<string[]>([]);
  const [timeframe, setTimeframe] = useState<'1m' | '3m' | '6m' | '1y'>('3m');
  const [focusLevel, setFocusLevel] = useState<'balanced' | 'focused' | 'intensive'>('balanced');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Toggle domain selection
   */
  const toggleDomainSelection = (domainId: string) => {
    setSelectedDomains(prev =>
      prev.includes(domainId)
        ? prev.filter(id => id !== domainId)
        : [...prev, domainId]
    );
  };

  /**
   * Generate wellness plan via API
   */
  const generateWellnessPlan = async () => {
    if (selectedDomains.length === 0) {
      setError('Please select at least one wellness domain to focus on.');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');

      const response = await fetch('/api/v1/clinical/wellness/plan/generate', {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          focus_areas: selectedDomains,
          timeframe: timeframe,
          focus_level: focusLevel,
          preferences: {
            difficulty_preference: 'progressive',
            time_commitment: focusLevel === 'balanced' ? 'moderate' : focusLevel === 'focused' ? 'significant' : 'comprehensive',
            support_system: 'full'
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate wellness plan: ${response.statusText}`);
      }

      const data = await response.json();
      if (data.success) {
        onPlanGenerated(data.data);
      } else {
        setError('Failed to generate wellness plan');
      }
    } catch (err) {
      console.error('API Error - falling back to demo plan:', err);
      // Fall back to demo plan when API fails
      generateDemoWellnessPlan();
    } finally {
      setIsGenerating(false);
    }
  };

  /**
   * Generate demo wellness plan (fallback)
   */
  const generateDemoWellnessPlan = () => {
    const demoPlan: WellnessPlan = {
      id: `demo-${Date.now()}`,
      user_id: 'demo-user',
      created_at: new Date().toISOString(),
      focus_areas: selectedDomains,
      timeline: timeframe,
      estimated_completion: getEstimatedCompletionDate(timeframe),
      success_metrics: [
        'Improved overall wellness score by 20%',
        'Completed 80% of action steps on time',
        'Reduced stress levels by 30%',
        'Enhanced work-life balance'
      ],
      potential_barriers: [
        'Time constraints and competing priorities',
        'Initial difficulty establishing new habits',
        'Potential lack of motivation during plateau periods'
      ],
      support_systems: [
        'Wellness coach for guidance',
        'Peer support group for accountability',
        'Mobile app for tracking and reminders'
      ],
      milestones: generateMilestones(selectedDomains, timeframe),
      ai_recommendations: [
        'Start with easier domains to build momentum',
        'Schedule regular check-ins to monitor progress',
        'Celebrate small wins to maintain motivation',
        'Adjust action steps based on real-world feedback'
      ],
      goals: generateDemoGoals(selectedDomains, timeframe, focusLevel)
    };

    onPlanGenerated(demoPlan);
  };

  /**
   * Get estimated completion date
   */
  const getEstimatedCompletionDate = (timeframe: string): string => {
    const now = new Date();
    const months = timeframe === '1m' ? 1 : timeframe === '3m' ? 3 : timeframe === '6m' ? 6 : 12;
    now.setMonth(now.getMonth() + months);
    return now.toISOString();
  };

  /**
   * Generate milestones
   */
  const generateMilestones = (domains: string[], timeframe: string) => {
    const now = new Date();
    const months = timeframe === '1m' ? 1 : timeframe === '3m' ? 3 : timeframe === '6m' ? 6 : 12;

    return [
      {
        id: 'm1',
        title: 'Initial Assessment Complete',
        description: 'Complete baseline assessment and set goals',
        target_date: new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        achieved: false,
        celebration: '🎯 Start your journey with a clear vision!'
      },
      {
        id: 'm2',
        title: 'First Month Progress',
        description: 'Complete first action steps in each domain',
        target_date: new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        achieved: false,
        celebration: '🌟 Great progress! Keep the momentum going!'
      },
      {
        id: 'm3',
        title: 'Mid-Point Review',
        description: 'Review progress and adjust strategies',
        target_date: new Date(now.getTime() + (months / 2) * 30 * 24 * 60 * 60 * 1000).toISOString(),
        achieved: false,
        celebration: '🏆 Halfway there! You\'re doing amazing!'
      }
    ];
  };

  /**
   * Generate demo goals
   */
  const generateDemoGoals = (domains: string[], timeframe: string, focusLevel: string) => {
    // Simplified goal generation for demo
    return domains.slice(0, 3).map((domain, index) => ({
      id: `goal-${index}`,
      domain: domain,
      title: `Improve ${domain} wellness`,
      description: `Enhance your ${domain} wellbeing through targeted actions`,
      priority: index === 0 ? 'high' : 'medium',
      target_date: getEstimatedCompletionDate(timeframe),
      current_score: 50,
      target_score: 80,
      action_steps: [
        {
          id: `step-${index}-1`,
          title: `Daily ${domain} practice`,
          description: `Dedicate 15 minutes daily to ${domain} wellness activities`,
          category: 'daily' as const,
          difficulty: 'easy' as const,
          time_required: '15 min',
          resources: ['Mobile app', 'Guided tutorials'],
          completed: false
        },
        {
          id: `step-${index}-2`,
          title: `Weekly ${domain} review`,
          description: `Review progress and adjust strategies weekly`,
          category: 'weekly' as const,
          difficulty: 'moderate' as const,
          time_required: '30 min',
          resources: ['Journal', 'Progress tracker'],
          completed: false
        }
      ]
    }));
  };

  return {
    selectedDomains,
    setSelectedDomains,
    timeframe,
    setTimeframe,
    focusLevel,
    setFocusLevel,
    isGenerating,
    error,
    toggleDomainSelection,
    generateWellnessPlan,
  };
};
