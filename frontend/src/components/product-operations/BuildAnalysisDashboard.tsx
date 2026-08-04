/**
 * Build Analysis Dashboard - Memoized Sub-Component
 */

import React, { useMemo } from 'react';
import { BuildFailureSummary, BuildFailure } from './types';

interface BuildAnalysisDashboardProps {
  buildSummary: BuildFailureSummary | null;
  buildFailures: BuildFailure[];
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

function getRiskColor(risk: string): string {
  switch (risk.toLowerCase()) {
    case 'critical': return 'bg-red-100 text-red-800';
    case 'high': return 'bg-orange-100 text-orange-800';
    case 'medium': return 'bg-yellow-100 text-yellow-800';
    case 'low': return 'bg-green-100 text-green-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

export const BuildAnalysisDashboard = React.memo<BuildAnalysisDashboardProps>(({
  buildSummary,
  buildFailures,
  loading = false,
}) => {
  const unresolvedFailures = useMemo(
    () => buildFailures.filter(f => !f.is_resolved),
    [buildFailures]
  );

  if (loading) {
    return <div className="animate-pulse"><div className="h-64 bg-gray-200 rounded-lg" /></div>;
  }

  if (!buildSummary) {
    return <div className="text-center py-12 text-gray-500">No build analysis data available</div>;
  }

  return (
    <div className="space-y-6">
      {/* Health Grade Card */}
      <div className={`bg-white rounded-lg shadow-xl p-8 border-4 ${getGradeBgColor(buildSummary.overall_health_grade)}`}>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Build Health Grade</h2>
          <p className={`text-8xl font-bold ${getGradeColor(buildSummary.overall_health_grade)}`}>
            {buildSummary.overall_health_grade}
          </p>
          <p className="text-gray-600 mt-2 text-xl">
            Avg Resolution: {buildSummary.average_resolution_time_minutes.toFixed(0)}min
          </p>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Total Failures</p>
          <p className="text-4xl font-bold text-gray-900 mt-2">{buildSummary.total_failures}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Unresolved</p>
          <p className="text-4xl font-bold text-orange-600 mt-2">{buildSummary.unresolved_failures}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Critical</p>
          <p className="text-4xl font-bold text-red-600 mt-2">{buildSummary.critical_failures}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Flaky Tests</p>
          <p className="text-4xl font-bold text-yellow-600 mt-2">{buildSummary.flaky_test_count}</p>
        </div>
      </div>

      {/* Build Failures List */}
      {buildFailures.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Build Failures</h3>
          </div>
          <div className="divide-y max-h-96 overflow-y-auto">
            {buildFailures.map((failure) => (
              <div key={failure.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(failure.priority)}`}>
                        {failure.priority}
                      </span>
                      <span className="text-sm text-gray-600">
                        {failure.project_name} / {failure.branch_name}
                      </span>
                    </div>
                    <p className="font-medium text-gray-900">{failure.failure_type}</p>
                    <p className="text-sm text-gray-600 mt-1">{failure.error_message}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Developer: {failure.developer_name} • {new Date(failure.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                {failure.ai_suggested_fix && (
                  <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-900 mb-1">🤖 AI Suggested Fix</p>
                    <p className="text-sm text-gray-700">{failure.ai_suggested_fix}</p>
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

BuildAnalysisDashboard.displayName = 'BuildAnalysisDashboard';
export default BuildAnalysisDashboard;
