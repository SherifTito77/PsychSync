/**
 * Clinical Results Data Hook - React Query Version
 *
 * Enhanced version with React Query integration for efficient data fetching,
 * caching, and automatic background refetching.
 *
 * Benefits of React Query:
 * - Automatic caching (5 minutes)
 * - Request deduplication
 * - Background refetching
 * - Optimistic updates
 * - Better error handling
 */

import { useQuery } from '@tanstack/react-query';
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

// Query keys for React Query cache management
const CLINICAL_RESULTS_QUERY_KEYS = {
  all: ['clinicalResults'] as const,
  detail: (tool: string, id?: string) => ['clinicalResults', tool, id] as const,
  latest: (tool: string) => ['clinicalResults', tool, 'latest'] as const,
};

/**
 * Fetch assessment by ID from API
 */
async function fetchAssessmentById(assessmentId: string): Promise<AssessmentResponseData> {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/clinical/screenings/${assessmentId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Unauthorized - Please login');
    }
    if (response.status === 404) {
      throw new Error('Assessment not found');
    }
    throw new Error('Failed to fetch assessment');
  }

  return response.json();
}

/**
 * Fetch latest assessment by tool type
 */
async function fetchLatestAssessment(tool: string): Promise<AssessmentResponseData> {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/clinical/screenings/latest/${tool}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Unauthorized - Please login');
    }
    if (response.status === 404) {
      throw new Error('No assessment found for this tool');
    }
    throw new Error('Failed to fetch latest assessment');
  }

  return response.json();
}

/**
 * Process API response and calculate scores
 */
function processAPIResponse(
  data: AssessmentResponseData,
  tool: string
): { result: AssessmentResult; metadata: AssessmentMetadata } {
  const severityLevel = data.severity_level;
  const score = data.total_score;

  const result: AssessmentResult = {
    score,
    severity_level: severityLevel,
    severity: getSeverityInfo(severityLevel),
    crisisAlert: data.crisis_alert,
    recommendations: getRecommendations(tool, severityLevel),
    resources: getResources(tool, severityLevel, data.crisis_alert, score),
  };

  const metadata: AssessmentMetadata = {
    assessmentId: data.id?.toString() || '',
    completedAt: data.completed_at || new Date().toISOString(),
    notes: data.notes || '',
    responseData: data.response_data,
    providerNotified: data.provider_notified,
    nextAssessmentDate: data.next_assessment_date,
  };

  return { result, metadata };
}

/**
 * Hook to fetch and manage clinical assessment results with React Query
 *
 * This hook automatically:
 * - Caches results for 5 minutes
 * - Deduplicates duplicate requests
 * - Refetches on window focus
 * - Handles loading and error states
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

  // Check if data is in location state (from navigation)
  const hasLocationState = location.state?.result;

  // If data is in location state, use it directly (no API call needed)
  if (hasLocationState) {
    try {
      const state = location.state;
      const severityLevel = state.result?.severity_level || state.severity_level;
      const score = state.result?.score || state.score;

      const result: AssessmentResult = {
        score,
        severity_level: severityLevel,
        severity: getSeverityInfo(severityLevel),
        crisisAlert: state.crisisAlert || state.result?.crisisAlert || false,
        recommendations: getRecommendations(tool!, severityLevel),
        resources: getResources(tool!, severityLevel, state.crisisAlert || state.result?.crisisAlert || false, score),
      };

      const metadata: AssessmentMetadata = {
        assessmentId: state.assessmentId || state.result?.id,
        completedAt: state.completedAt || state.result?.completed_at,
        notes: state.notes || state.result?.notes,
        responseData: state.responseData || state.result?.response_data,
        providerNotified: state.providerNotified || state.result?.provider_notified,
        nextAssessmentDate: state.nextAssessmentDate || state.result?.next_assessment_date,
      };

      return {
        result,
        metadata,
        loading: false,
        error: null,
      };
    } catch (error) {
      return {
        result: null,
        metadata: null,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to process results',
      };
    }
  }

  // Use React Query for API fetching
  const assessmentId = window.location.hash?.substring(1);

  // Fetch by hash ID if present
  const hashQuery = useQuery({
    queryKey: CLINICAL_RESULTS_QUERY_KEYS.detail(tool || '', assessmentId),
    queryFn: () => fetchAssessmentById(assessmentId!),
    enabled: !!assessmentId && !!tool,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  // Fetch latest by tool if no hash
  const latestQuery = useQuery({
    queryKey: CLINICAL_RESULTS_QUERY_KEYS.latest(tool || ''),
    queryFn: () => fetchLatestAssessment(tool!),
    enabled: !assessmentId && !!tool,
    retry: false,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });

  // Determine which query to use
  const activeQuery = assessmentId ? hashQuery : latestQuery;

  // Process query data
  if (activeQuery.data) {
    try {
      const { result, metadata } = processAPIResponse(activeQuery.data, tool!);
      return {
        result,
        metadata,
        loading: activeQuery.isLoading,
        error: null,
      };
    } catch (error) {
      return {
        result: null,
        metadata: null,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to process results',
      };
    }
  }

  // Return loading/error states
  return {
    result: null,
    metadata: null,
    loading: activeQuery.isLoading,
    error: activeQuery.error?.message || null,
  };
}

/**
 * Invalidate and refetch clinical results
 *
 * Use this after submitting a new assessment to ensure fresh data.
 *
 * @example
 * ```typescript
 * const queryClient = useQueryClient();
 * await submitAssessment(data);
 * await invalidateClinicalResults(queryClient, 'phq9');
 * ```
 */
export async function invalidateClinicalResults(
  queryClient: any,
  tool: string
): Promise<void> {
  await queryClient.invalidateQueries({
    queryKey: CLINICAL_RESULTS_QUERY_KEYS.all,
  });
}
