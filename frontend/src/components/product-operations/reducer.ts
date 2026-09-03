/**
 * Product Operations Dashboard - State Reducer
 *
 * Consolidates 19+ useState hooks into a single useReducer
 * Reduces re-renders by batching related state updates
 */

import { DashboardState, TabType } from './types';

export type DashboardAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_ACTIVE_TAB'; payload: TabType }
  | { type: 'SET_QUALITY_SUMMARY'; payload: DashboardState['qualitySummary'] }
  | { type: 'SET_BUG_SUMMARIES'; payload: DashboardState['bugSummaries'] }
  | { type: 'SET_PULL_REQUESTS'; payload: DashboardState['pullRequests'] }
  | { type: 'SET_PERFORMANCE_REPORT'; payload: DashboardState['performanceReport'] }
  | { type: 'SET_SPRINTS'; payload: DashboardState['sprints'] }
  | { type: 'SET_SQL_SUMMARY'; payload: DashboardState['sqlSummary'] }
  | { type: 'SET_SQL_QUERIES'; payload: DashboardState['sqlQueries'] }
  | { type: 'SET_QUERY_PERF_SUMMARY'; payload: DashboardState['queryPerfSummary'] }
  | { type: 'SET_SLOW_QUERIES'; payload: DashboardState['slowQueries'] }
  | { type: 'SET_BUILD_SUMMARY'; payload: DashboardState['buildSummary'] }
  | { type: 'SET_BUILD_FAILURES'; payload: DashboardState['buildFailures'] }
  | { type: 'SET_CACHE_SUMMARY'; payload: DashboardState['cacheSummary'] }
  | { type: 'SET_CACHE_ENTRIES'; payload: DashboardState['cacheEntries'] }
  | { type: 'SET_BREAKING_CHANGES_SUMMARY'; payload: DashboardState['breakingChangesSummary'] }
  | { type: 'SET_BREAKING_CHANGES'; payload: DashboardState['breakingChanges'] }
  | { type: 'BATCH_SET_DATA'; payload: Partial<DashboardState> };

export const initialDashboardState: DashboardState = {
  loading: true,
  error: null,
  activeTab: 'overview',
  qualitySummary: null,
  bugSummaries: [],
  pullRequests: [],
  performanceReport: null,
  sprints: [],
  sqlSummary: null,
  sqlQueries: [],
  queryPerfSummary: null,
  slowQueries: [],
  buildSummary: null,
  buildFailures: [],
  cacheSummary: null,
  cacheEntries: [],
  breakingChangesSummary: null,
  breakingChanges: [],
};

export function dashboardReducer(
  state: DashboardState,
  action: DashboardAction
): DashboardState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };

    case 'SET_ACTIVE_TAB':
      return { ...state, activeTab: action.payload };

    case 'SET_QUALITY_SUMMARY':
      return { ...state, qualitySummary: action.payload };

    case 'SET_BUG_SUMMARIES':
      return { ...state, bugSummaries: action.payload };

    case 'SET_PULL_REQUESTS':
      return { ...state, pullRequests: action.payload };

    case 'SET_PERFORMANCE_REPORT':
      return { ...state, performanceReport: action.payload };

    case 'SET_SPRINTS':
      return { ...state, sprints: action.payload };

    case 'SET_SQL_SUMMARY':
      return { ...state, sqlSummary: action.payload };

    case 'SET_SQL_QUERIES':
      return { ...state, sqlQueries: action.payload };

    case 'SET_QUERY_PERF_SUMMARY':
      return { ...state, queryPerfSummary: action.payload };

    case 'SET_SLOW_QUERIES':
      return { ...state, slowQueries: action.payload };

    case 'SET_BUILD_SUMMARY':
      return { ...state, buildSummary: action.payload };

    case 'SET_BUILD_FAILURES':
      return { ...state, buildFailures: action.payload };

    case 'SET_CACHE_SUMMARY':
      return { ...state, cacheSummary: action.payload };

    case 'SET_CACHE_ENTRIES':
      return { ...state, cacheEntries: action.payload };

    case 'SET_BREAKING_CHANGES_SUMMARY':
      return { ...state, breakingChangesSummary: action.payload };

    case 'SET_BREAKING_CHANGES':
      return { ...state, breakingChanges: action.payload };

    case 'BATCH_SET_DATA':
      return { ...state, ...action.payload };

    default:
      return state;
  }
}

/**
 * Helper action creators for common operations
 */
export const dashboardActions = {
  setLoading: (loading: boolean) => ({ type: 'SET_LOADING' as const, payload: loading }),
  setError: (error: string | null) => ({ type: 'SET_ERROR' as const, payload: error }),
  setActiveTab: (tab: TabType) => ({ type: 'SET_ACTIVE_TAB' as const, payload: tab }),

  // Batch update all data at once (single re-render)
  batchSetData: (data: Partial<DashboardState>) => ({
    type: 'BATCH_SET_DATA' as const,
    payload: data,
  }),
};
