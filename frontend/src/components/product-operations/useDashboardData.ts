/**
 * useDashboardData - Custom Hook for Data Fetching
 *
 * Consolidates all API calls into a single hook with:
 * - AbortController support for cleanup
 * - Parallel data fetching
 * - Error handling
 * - Type-safe responses
 */

import { useCallback, useEffect } from 'react';
import api from '../../services/api';
import { dashboardActions } from './reducer';
import type { DashboardState } from './types';

interface UseDashboardDataOptions {
  enabled?: boolean;
  onDataReceived?: (data: Partial<DashboardState>) => void;
  onError?: (error: string) => void;
}

export function useDashboardData(
  dispatch: React.Dispatch<ReturnType<typeof dashboardActions[keyof typeof dashboardActions]>>,
  options: UseDashboardDataOptions = {}
) {
  const { enabled = true, onDataReceived, onError } = options;

  const fetchAllData = useCallback(async (signal?: AbortSignal) => {
    try {
      dispatch(dashboardActions.setLoading(true));
      dispatch(dashboardActions.setError(null));

      // Fetch all data in parallel with AbortSignal for cancellation
      const [
        qualityRes,
        bugsRes,
        prsRes,
        reportRes,
        sprintsRes,
        sqlSummaryRes,
        sqlQueriesRes,
        queryPerfSummaryRes,
        slowQueriesRes,
        buildSummaryRes,
        buildFailuresRes,
        cacheSummaryRes,
        cacheEntriesRes,
        breakingChangesSummaryRes,
        breakingChangesRes,
      ] = await Promise.all([
        api.get('/metrics/summary', { signal } as any).catch(() => ({ data: null })),
        api.get('/jira_integration/bugs/summary?project_key=PROJ&days=14', { signal } as any).catch(() => ({ data: null })),
        api.get('/pull-requests?limit=10', { signal } as any).catch(() => ({ data: [] })),
        api.get('/jira_integration/reports/performance?project_key=PROJ&days=7', { signal } as any).catch(() => ({ data: null })),
        api.get('/jira_integration/sprints?project_key=PROJ', { signal } as any).catch(() => ({ data: [] })),
        api.get('/sql_audit/queries/summary', { signal } as any).catch(() => ({ data: null })),
        api.get('/sql_audit/queries?limit=5', { signal } as any).catch(() => ({ data: [] })),
        api.get('/query_performance/queries/summary', { signal } as any).catch(() => ({ data: null })),
        api.get('/query_performance/queries?limit=5', { signal } as any).catch(() => ({ data: [] })),
        api.get('/build_analysis/failures/summary', { signal } as any).catch(() => ({ data: null })),
        api.get('/build_analysis/failures/unresolved?limit=5', { signal } as any).catch(() => ({ data: [] })),
        api.get('/caching_config/entries/summary', { signal } as any).catch(() => ({ data: null })),
        api.get('/caching_config/entries/low_hit_rate?limit=5', { signal } as any).catch(() => ({ data: [] })),
        api.get('/breaking_changes/changes/summary', { signal } as any).catch(() => ({ data: null })),
        api.get('/breaking_changes/changes/unapproved?limit=5', { signal } as any).catch(() => ({ data: [] })),
      ]);

      // Batch update all data in a single re-render
      const newData = {
        qualitySummary: qualityRes.data,
        bugSummaries: bugsRes.data,
        pullRequests: prsRes.data,
        performanceReport: reportRes.data,
        sprints: sprintsRes.data,
        sqlSummary: sqlSummaryRes.data,
        sqlQueries: sqlQueriesRes.data || [],
        queryPerfSummary: queryPerfSummaryRes.data,
        slowQueries: slowQueriesRes.data || [],
        buildSummary: buildSummaryRes.data,
        buildFailures: buildFailuresRes.data || [],
        cacheSummary: cacheSummaryRes.data,
        cacheEntries: cacheEntriesRes.data || [],
        breakingChangesSummary: breakingChangesSummaryRes.data,
        breakingChanges: breakingChangesRes.data || [],
        loading: false,
      };

      dispatch(dashboardActions.batchSetData(newData));
      onDataReceived?.(newData);
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        return; // Ignore abort errors
      }

      const errorMessage = err instanceof Error
        ? (err as any).response?.data?.message || 'Failed to load dashboard data'
        : 'An unknown error occurred';

      dispatch(dashboardActions.setError(errorMessage));
      onError?.(errorMessage);
    }
  }, [dispatch, onDataReceived, onError]);

  // Initial fetch
  useEffect(() => {
    if (!enabled) return;

    const abortController = new AbortController();

    fetchAllData(abortController.signal);

    return () => {
      abortController.abort();
    };
  }, [enabled, fetchAllData]);

  return { fetchAllData };
}
