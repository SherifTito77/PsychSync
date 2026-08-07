// frontend/src/hooks/useExperiment.ts
// React hook for A/B testing integration
// ✅ MIGRATED: Now uses unified analytics tracker
import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../services/api';
import { getAnalytics } from '../services/analytics/tracker';

export interface ExperimentConfig {
  name: string;
  variants: string[];
  trafficSplit: Record<string, number>;
  startDate: string;
  endDate: string;
}

export interface ExperimentResult {
  variant: string;
  isLoading: boolean;
  error: string | null;
  track: (eventType: string, properties?: Record<string, any>) => Promise<void>;
  isControl: boolean;
}

/**
 * React hook for A/B testing
 *
 * @param experimentName - Name of the experiment
 * @returns Experiment result with variant and tracking function
 *
 * @example
 * const { variant, track, isLoading } = useExperiment('cta_button_color_v1');
 * if (isLoading) return <Loading />;
 * return <button className={variant === 'variant_a' ? 'bg-green' : 'bg-blue'}>Sign Up</button>;
 */
export const useExperiment = (experimentName: string): ExperimentResult => {
  const [variant, setVariant] = useState<string>('control');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ✅ FIXED: Add ref to prevent Strict Mode double-calling
  const hasAssigned = useRef(false);

  useEffect(() => {
    // ✅ FIXED: Skip second call in Strict Mode (development)
    if (hasAssigned.current) {
      if (process.env.NODE_ENV === 'development') {
        console.log(`[useExperiment] Skipping duplicate assignment for: ${experimentName}`);
      }
      return;
    }
    hasAssigned.current = true;

    const assignVariant = async () => {
      try {
        // Check localStorage first
        const cacheKey = `ab_experiment_${experimentName}`;
        const cached = localStorage.getItem(cacheKey);

        if (cached) {
          setVariant(cached);
          setIsLoading(false);
          return;
        }

        // Call assignment API
        const response = await apiClient.post('/ab/assign', {
          experiment: experimentName
        });

        const assignedVariant = (response.data as any).variant;
        setVariant(assignedVariant);

        // Cache in localStorage
        localStorage.setItem(cacheKey, assignedVariant);

        setIsLoading(false);
        setError(null);

      } catch (err) {
        console.error('Experiment assignment failed:', err);
        setError('Assignment failed');
        setVariant('control'); // Fallback to control
        setIsLoading(false);
      }
    };

    assignVariant();
  }, [experimentName]);

  // Track function
  // ✅ MIGRATED: Now uses unified analytics tracker
  const track = async (eventType: string, properties?: Record<string, any>) => {
    try {
      const analytics = getAnalytics();

      // Use unified tracker for A/B test events
      analytics.trackABTest(experimentName, variant, eventType as any, {
        ...properties,
        experiment_name: experimentName, // Legacy field for backward compatibility
      });
    } catch (err) {
      console.error('Event tracking failed:', err);
    }
  };

  return {
    variant,
    isLoading,
    error,
    track,
    isControl: variant === 'control'
  };
};

/**
 * Hook for multiple experiments at once
 */
export const useExperiments = (experimentNames: string[]): Record<string, ExperimentResult> => {
  const [results, setResults] = useState<Record<string, ExperimentResult>>({});

  useEffect(() => {
    const assignAll = async () => {
      const newResults: Record<string, ExperimentResult> = {};

      for (const name of experimentNames) {
        const cacheKey = `ab_experiment_${name}`;
        const cached = localStorage.getItem(cacheKey);

        if (cached) {
          newResults[name] = {
            variant: cached,
            isLoading: false,
            error: null,
            track: async (eventType: string, properties?: Record<string, any>) => {
              // ✅ MIGRATED: Now uses unified analytics tracker
              const analytics = getAnalytics();
              analytics.trackABTest(name, cached, eventType as any, {
                ...properties,
                experiment_name: name,
              });
            },
            isControl: cached === 'control'
          };
        } else {
          // Will be set by individual useEffect
          newResults[name] = {
            variant: 'control',
            isLoading: true,
            error: null,
            track: async () => {},
            isControl: true
          };
        }
      }

      setResults(newResults);
    };

    assignAll();
  }, experimentNames);

  return results;
};

export default useExperiment;
