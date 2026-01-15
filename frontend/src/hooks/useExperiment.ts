// frontend/src/hooks/useExperiment.ts
// React hook for A/B testing integration
import { useState, useEffect } from 'react';
import { apiClient } from '../services/api';

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

  useEffect(() => {
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
        const response = await apiClient.post('/api/v1/ab/assign', {
          experiment: experimentName
        });

        const assignedVariant = response.data.variant;
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
  const track = async (eventType: string, properties?: Record<string, any>) => {
    try {
      await apiClient.post('/api/v1/ab/track', {
        experiment: experimentName,
        variant,
        event_type: eventType,
        properties,
        timestamp: new Date().toISOString()
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
              await apiClient.post('/api/v1/ab/track', {
                experiment: name,
                variant: cached,
                event_type: eventType,
                properties
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
