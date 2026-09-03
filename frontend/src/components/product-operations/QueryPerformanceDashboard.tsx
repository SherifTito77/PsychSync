/**
 * Query Performance Dashboard - Memoized Sub-Component
 */

import React, { useMemo } from 'react';
import { QueryPerformanceSummary, SlowQuery } from './types';

interface QueryPerformanceDashboardProps {
  queryPerfSummary: QueryPerformanceSummary | null;
  slowQueries: SlowQuery[];
  loading?: boolean;
}

function getGradeColor(grade: string): string {
  const gradeNum = grade.replace(/[^A-Z]/g, '');
  if (gradeNum === 'A' || gradeNum === 'A+') return 'text-green-600';
  if (gradeNum === 'B') return 'text-blue-600';
  if (gradeNum === 'C') return 'text-yellow-600';
  return 'text-red-600';
}

function getGradeBgColor(grade: string): string {
  const gradeNum = grade.replace(/[^A-Z]/g, '');
  if (gradeNum === 'A' || gradeNum === 'A+') return 'border-green-500';
  if (gradeNum === 'B') return 'border-blue-500';
  if (gradeNum === 'C') return 'border-yellow-500';
  return 'border-red-500';
}

export const QueryPerformanceDashboard = React.memo<QueryPerformanceDashboardProps>(({
  queryPerfSummary,
  slowQueries,
  loading = false,
}) => {
  const criticalQueries = useMemo(
    () => slowQueries.filter(q => q.performance_tier === 'critical' || q.performance_tier === 'slow'),
    [slowQueries]
  );

  if (loading) {
    return <div className="animate-pulse"><div className="h-64 bg-gray-200 rounded-lg" /></div>;
  }

  if (!queryPerfSummary) {
    return <div className="text-center py-12 text-gray-500">No query performance data available</div>;
  }

  return (
    <div className="space-y-6">
      {/* Performance Grade Card */}
      <div className={`bg-white rounded-lg shadow-xl p-8 border-4 ${getGradeBgColor(queryPerfSummary.overall_performance_grade)}`}>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Query Performance Grade</h2>
          <p className={`text-8xl font-bold ${getGradeColor(queryPerfSummary.overall_performance_grade)}`}>
            {queryPerfSummary.overall_performance_grade}
          </p>
          <p className="text-gray-600 mt-2 text-xl">
            Avg Query Time: {queryPerfSummary.avg_query_time_ms.toFixed(1)}ms
          </p>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Total Queries</p>
          <p className="text-4xl font-bold text-gray-900 mt-2">{queryPerfSummary.total_queries}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Slow Queries</p>
          <p className="text-4xl font-bold text-orange-600 mt-2">{queryPerfSummary.slow_queries}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Critical</p>
          <p className="text-4xl font-bold text-red-600 mt-2">{queryPerfSummary.critical_queries}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Optimization Potential</p>
          <p className="text-4xl font-bold text-blue-600 mt-2">{queryPerfSummary.optimization_potential_ms.toFixed(0)}ms</p>
        </div>
      </div>

      {/* Slow Queries List */}
      {slowQueries.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Slow Queries Detected</h3>
          </div>
          <div className="divide-y max-h-96 overflow-y-auto">
            {slowQueries.map((query) => (
              <div key={query.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        query.performance_tier === 'critical' ? 'bg-red-100 text-red-800' :
                        query.performance_tier === 'slow' ? 'bg-orange-100 text-orange-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {query.performance_tier}
                      </span>
                      <span className="text-sm text-gray-600">
                        Avg Time: {query.avg_time_ms.toFixed(1)}ms
                      </span>
                    </div>
                    <code className="block bg-gray-100 rounded p-3 text-sm font-mono overflow-x-auto">
                      {query.query_text}
                    </code>
                  </div>
                </div>

                {query.ai_suggestion && (
                  <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-900 mb-1">🤖 AI Suggestion</p>
                    <p className="text-sm text-gray-700">{query.ai_suggestion}</p>
                  </div>
                )}

                {query.suggested_index && (
                  <div className="mt-2 p-3 bg-green-50 rounded-lg">
                    <p className="text-sm font-medium text-green-900 mb-1">📈 Suggested Index</p>
                    <code className="text-sm text-gray-700">{query.suggested_index}</code>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
});

QueryPerformanceDashboard.displayName = 'QueryPerformanceDashboard';
export default QueryPerformanceDashboard;
