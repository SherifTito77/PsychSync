/**
 * Product Operations Dashboard - Refactored Module
 *
 * This module contains the optimized, split version of ProductOperationsDashboard.
 *
 * Key Improvements:
 * 1. State consolidated with useReducer (19 hooks → 1 hook)
 * 2. Memoized sub-components (each tab re-renders independently)
 * 3. Custom data fetching hook with AbortController
 * 4. Type-safe actions and state
 * 5. Better separation of concerns
 *
 * Usage:
 * ```tsx
 * import { ProductOperationsDashboardOptimized } from '@/components/product-operations';
 *
 * <ProductOperationsDashboardOptimized />
 * ```
 */

export * from './types';
export * from './reducer';
export * from './useDashboardData';

// Extracted tab components (memoized)
export { CodeQualityOverview } from './CodeQualityOverview';
export { BugSummarization } from './BugSummarization';
export { PullRequestQuality } from './PullRequestQuality';
export { EngineeringPerformanceReports } from './EngineeringPerformanceReports';
export { SQLAuditDashboard } from './SQLAuditDashboard';
export { QueryPerformanceDashboard } from './QueryPerformanceDashboard';
export { BuildAnalysisDashboard } from './BuildAnalysisDashboard';
export { CachingConfigDashboard } from './CachingConfigDashboard';
export { BreakingChangesDashboard } from './BreakingChangesDashboard';

// Optimized main dashboard
export { ProductOperationsDashboardOptimized } from './ProductOperationsDashboardOptimized';

// Note: SprintMetrics is included within EngineeringPerformanceReports
