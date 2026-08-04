/**
 * Code Quality Overview - Memoized Sub-Component
 *
 * Extracted from ProductOperationsDashboard for better performance:
 * - Only re-renders when qualitySummary changes
 * - Isolated component for easier testing and maintenance
 * - Can be lazy-loaded if needed
 */

import React, { useMemo } from 'react';
import { CodeQualitySummary } from './types';

interface CodeQualityOverviewProps {
  qualitySummary: CodeQualitySummary | null;
  loading: boolean;
}

export const CodeQualityOverview = React.memo<CodeQualityOverviewProps>(({
  qualitySummary,
  loading,
}) => {
  // Memoize grade color calculation
  const gradeColor = useMemo(() => {
    if (!qualitySummary) return 'gray';
    const score = qualitySummary.quality_grade;
    if (score === 'A' || score === 'A+') return 'green';
    if (score === 'B' || score === 'B+') return 'blue';
    if (score === 'C') return 'yellow';
    return 'red';
  }, [qualitySummary]);

  // Memoize issue breakdown
  const issueBreakdown = useMemo(() => {
    if (!qualitySummary) return [];
    return [
      { label: 'Critical', value: qualitySummary.critical_issues, color: 'red' },
      { label: 'High', value: qualitySummary.high_issues, color: 'orange' },
      { label: 'Medium', value: qualitySummary.medium_issues, color: 'yellow' },
      { label: 'Low', value: qualitySummary.low_issues, color: 'blue' },
    ];
  }, [qualitySummary]);

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-32 bg-gray-200 rounded-lg" />
      </div>
    );
  }

  if (!qualitySummary) {
    return (
      <div className="p-6 text-center text-gray-500">
        No quality data available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overall Score Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Code Quality Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div
              className={`text-5xl font-bold text-${gradeColor}-600 mb-2`}
            >
              {qualitySummary.quality_grade}
            </div>
            <div className="text-sm text-gray-600">Quality Grade</div>
          </div>
          <div className="text-center">
            <div className="text-5xl font-bold text-blue-600 mb-2">
              {qualitySummary.overall_score}
            </div>
            <div className="text-sm text-gray-600">Overall Score</div>
          </div>
          <div className="text-center">
            <div className="text-5xl font-bold text-purple-600 mb-2">
              {qualitySummary.test_coverage}%
            </div>
            <div className="text-sm text-gray-600">Test Coverage</div>
          </div>
        </div>
      </div>

      {/* Issues Breakdown */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-md font-semibold mb-4">Issues by Severity</h4>
        <div className="space-y-3">
          {issueBreakdown.map((issue) => (
            <div key={issue.label} className="flex items-center justify-between">
              <span className="text-sm font-medium">{issue.label}</span>
              <div className="flex items-center gap-2">
                <div
                  className={`w-32 h-2 bg-${issue.color}-500 rounded-full`}
                />
                <span className="text-sm font-semibold">{issue.value}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">Code Duplication</div>
          <div className="text-2xl font-bold">
            {qualitySummary.code_duplication}%
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">Technical Debt Ratio</div>
          <div className="text-2xl font-bold">
            {qualitySummary.technical_debt_ratio}%
          </div>
        </div>
      </div>
    </div>
  );
});

CodeQualityOverview.displayName = 'CodeQualityOverview';

export default CodeQualityOverview;
