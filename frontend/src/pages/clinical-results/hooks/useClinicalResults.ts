/**
 * Clinical Results Data Hook
 *
 * Custom hook for fetching and managing clinical assessment results data.
 * Handles data fetching from location state, URL hash, or API.
 */

import { useState, useEffect } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { AssessmentResult, AssessmentMetadata, AssessmentResponseData } from '../types';
import { getSeverityInfo } from '../utils/severityCalculator';
import { getRecommendations } from '../utils/recommendations';
import { getResources } from '../utils/resources';

interface UseClinicalResultsReturn {
  result: AssessmentResult | null;
  metadata: AssessmentMetadata | null;
  loading: boolean;
  error: string | null;
}

/**
 * Hook to fetch and manage clinical assessment results
 *
 * @param tool - The assessment tool identifier
 * @returns Object containing result, metadata, loading state, and error
 *
 * @example
 * ```typescript
 * const { result, metadata, loading, error } = useClinicalResults('phq9');
 *
 * if (loading) return <LoadingSpinner />;
 * if (error) return <ErrorDisplay error={error} />;
 * if (!result) return <NoResults />;
 *
 * return <ResultsDisplay result={result} metadata={metadata} />;
 * ```
 */
export function useClinicalResults(tool: string | undefined): UseClinicalResultsReturn {
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [metadata, setMetadata] = useState<AssessmentMetadata | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadResults();
  }, [tool, location.state, window.location.hash]);

  const loadResults = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get from location state, hash, or API
      if (location.state?.result) {
        setResultFromState(location.state);
      } else if (window.location.hash) {
        await fetchByHash(window.location.hash.substring(1));
      } else if (tool) {
        await fetchFromAPI(tool);
      } else {
        setError('No assessment tool specified');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load results');
      console.error('Error loading results:', err);
    } finally {
      setLoading(false);
    }
  };

  const setResultFromState = (state: any) => {
    try {
      const severityLevel = state.result?.severity_level || state.severity_level;
      const score = state.result?.score || state.score;

      setResult({
        score,
        severity_level: severityLevel,
        severity: getSeverityInfo(severityLevel),
        crisisAlert: state.crisisAlert || state.result?.crisisAlert || false,
        recommendations: getRecommendations(tool!, severityLevel),
        resources: getResources(
          tool!,
          severityLevel,
          state.crisisAlert || state.result?.crisisAlert || false,
          score
        ),
      });

      setAssessmentMetadata(state);
    } catch (err) {
      throw new Error('Failed to process result data');
    }
  };

  const setAssessmentMetadata = (data: any) => {
    setMetadata({
      assessmentId: data.assessmentId || data.result?.id,
      completedAt: data.completedAt || data.result?.completed_at,
      notes: data.notes || data.result?.notes,
      responseData: data.responseData || data.result?.response_data,
      providerNotified: data.providerNotified || data.result?.provider_notified,
      nextAssessmentDate: data.nextAssessmentDate || data.result?.next_assessment_date,
    });
  };

  const fetchByHash = async (assessmentId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/clinical/screenings/${assessmentId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch assessment');
      }

      const data: AssessmentResponseData = await response.json();
      processAPIResponse(data);
    } catch (err) {
      throw new Error('Failed to fetch assessment by ID');
    }
  };

  const fetchFromAPI = async (toolType: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/clinical/screenings/latest/${toolType}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }

      const data: AssessmentResponseData = await response.json();
      processAPIResponse(data);
    } catch (err) {
      throw new Error('Failed to fetch latest results');
    }
  };

  const processAPIResponse = (data: AssessmentResponseData) => {
    const severityLevel = data.severity_level;
    const score = data.total_score;

    setResult({
      score,
      severity_level: severityLevel,
      severity: getSeverityInfo(severityLevel),
      crisisAlert: data.crisis_alert,
      recommendations: getRecommendations(tool!, severityLevel),
      resources: getResources(tool!, severityLevel, data.crisis_alert, score),
    });

    setMetadata({
      assessmentId: data.id?.toString() || '',
      completedAt: data.completed_at || new Date().toISOString(),
      notes: data.notes || '',
      responseData: data.response_data,
      providerNotified: data.provider_notified,
      nextAssessmentDate: data.next_assessment_date,
    });
  };

  return {
    result,
    metadata,
    loading,
    error,
  };
}
