/**
 * Breaking Changes Dashboard - Memoized Sub-Component
 */

import React, { useMemo } from 'react';
import { BreakingChangesSummary, BreakingChange } from './types';

interface BreakingChangesDashboardProps {
  breakingChangesSummary: BreakingChangesSummary | null;
  breakingChanges: BreakingChange[];
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

export const BreakingChangesDashboard = React.memo<BreakingChangesDashboardProps>(({
  breakingChangesSummary,
  breakingChanges,
  loading = false,
}) => {
  const unapprovedChanges = useMemo(
    () => breakingChanges.filter(c => !c.is_approved),
    [breakingChanges]
  );

  const criticalChanges = useMemo(
    () => breakingChanges.filter(c => c.severity === 'critical'),
    [breakingChanges]
  );

  if (loading) {
    return <div className="animate-pulse"><div className="h-64 bg-gray-200 rounded-lg" /></div>;
  }

  if (!breakingChangesSummary) {
    return <div className="text-center py-12 text-gray-500">No breaking changes data available</div>;
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Total Changes</p>
          <p className="text-4xl font-bold text-gray-900 mt-2">{breakingChangesSummary.total_changes}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Unapproved</p>
          <p className="text-4xl font-bold text-orange-600 mt-2">{breakingChangesSummary.unapproved_changes}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Critical</p>
          <p className="text-4xl font-bold text-red-600 mt-2">{breakingChangesSummary.by_severity.critical}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">By Category</p>
          <div className="mt-2 space-y-1 text-sm">
            <div className="flex justify-between">
              <span>API</span>
              <span className="font-medium">{breakingChangesSummary.by_category.api}</span>
            </div>
            <div className="flex justify-between">
              <span>Database</span>
              <span className="font-medium">{breakingChangesSummary.by_category.database}</span>
            </div>
            <div className="flex justify-between">
              <span>UI</span>
              <span className="font-medium">{breakingChangesSummary.by_category.ui}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Critical Changes Alert */}
      {criticalChanges.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-900 mb-4">
            ⚠️ Critical Breaking Changes Require Attention
          </h3>
          <p className="text-red-700">
            {criticalChanges.length} critical breaking changes detected. These require immediate review and approval.
          </p>
        </div>
      )}

      {/* Breaking Changes List */}
      {breakingChanges.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Breaking Changes</h3>
          </div>
          <div className="divide-y max-h-96 overflow-y-auto">
            {breakingChanges.map((change) => (
              <div key={change.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(change.severity)}`}>
                        {change.severity}
                      </span>
                      <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                        {change.category}
                      </span>
                      {!change.is_approved && (
                        <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">
                          Pending Approval
                        </span>
                      )}
                    </div>
                    <h4 className="font-semibold text-gray-900">{change.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{change.description}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      Author: {change.author_name} • Scheduled: {new Date(change.scheduled_for).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                {/* Affected Components */}
                {change.affected_components && change.affected_components.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm font-medium text-gray-900 mb-2">Affected Components</p>
                    <div className="flex flex-wrap gap-2">
                      {change.affected_components.map((component, idx) => (
                        <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                          {component}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Migration Guide */}
                {change.migration_guide && (
                  <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-900 mb-1">📋 Migration Guide</p>
                    <p className="text-sm text-gray-700">{change.migration_guide}</p>
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

BreakingChangesDashboard.displayName = 'BreakingChangesDashboard';
export default BreakingChangesDashboard;
