/**
 * Engineering Performance Reports - Memoized Sub-Component
 *
 * Extracted from ProductOperationsDashboard for better performance:
 * - Only re-renders when performanceReport changes
 * - Memoized calculations
 * - Clean separation of concerns
 */

import React, { useMemo } from 'react';
import { PerformanceReport, SprintMetrics } from './types';

interface EngineeringPerformanceReportsProps {
  performanceReport: PerformanceReport | null;
  sprints: SprintMetrics[];
  loading?: boolean;
}

export const EngineeringPerformanceReports = React.memo<EngineeringPerformanceReportsProps>(
  ({ performanceReport, sprints, loading = false }) => {
    // Memoize resolution rate calculation
    const resolutionRate = useMemo(() => {
      if (!performanceReport || performanceReport.total_bugs_created === 0) return 0;
      return (
        (performanceReport.total_bugs_resolved / performanceReport.total_bugs_created) *
        100
      ).toFixed(0);
    }, [performanceReport]);

    // Memoize top contributors with rankings
    const topContributors = useMemo(() => {
      if (!performanceReport) return [];
      return performanceReport.top_contributors.map((contributor, idx) => ({
        ...contributor,
        rank: idx,
        medal: idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : '🏅',
      }));
    }, [performanceReport]);

    if (loading) {
      return (
        <div className="animate-pulse">
          <div className="h-64 bg-gray-200 rounded-lg" />
        </div>
      );
    }

    if (!performanceReport) {
      return (
        <div className="text-center py-12 text-gray-500">No performance data available</div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Report Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg shadow-xl p-8 text-white">
          <h2 className="text-3xl font-bold mb-2">Weekly Engineering Performance Report</h2>
          <p className="text-purple-100">
            {new Date(performanceReport.period_start).toLocaleDateString()} -{' '}
            {new Date(performanceReport.period_end).toLocaleDateString()}
          </p>
        </div>

        {/* AI Summary */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span>🤖</span> AI-Generated Summary
          </h3>
          <p className="text-gray-700 leading-relaxed">{performanceReport.ai_summary}</p>
        </div>

        {/* Bug Metrics */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">🐛 Bug Metrics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-900">
                {performanceReport.total_bugs_created}
              </p>
              <p className="text-gray-600 mt-1">Created</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-green-600">
                {performanceReport.total_bugs_resolved}
              </p>
              <p className="text-gray-600 mt-1">Resolved</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-blue-600">{resolutionRate}%</p>
              <p className="text-gray-600 mt-1">Resolution Rate</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-orange-600">
                {performanceReport.avg_resolution_time_hours.toFixed(1)}h
              </p>
              <p className="text-gray-600 mt-1">Avg Resolution Time</p>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t">
            <p className="font-medium text-gray-900 mb-3">Severity Breakdown</p>
            <div className="flex gap-4">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-600 rounded"></div>
                <span className="text-gray-700">
                  Critical: {performanceReport.bugs_by_severity.critical}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-orange-600 rounded"></div>
                <span className="text-gray-700">
                  Major: {performanceReport.bugs_by_severity.major}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-yellow-600 rounded"></div>
                <span className="text-gray-700">
                  Minor: {performanceReport.bugs_by_severity.minor}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Sprint Metrics */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">🏃 Sprint Performance</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-900">
                {performanceReport.sprints_completed}
              </p>
              <p className="text-gray-600 mt-1">Sprints Completed</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-blue-600">
                {performanceReport.avg_velocity}
              </p>
              <p className="text-gray-600 mt-1">Avg Velocity</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-green-600">
                {performanceReport.completion_rate.toFixed(1)}%
              </p>
              <p className="text-gray-600 mt-1">Completion Rate</p>
            </div>
          </div>
        </div>

        {/* Top Contributors */}
        {topContributors.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">⭐ Top Contributors</h3>
            <div className="space-y-3">
              {topContributors.map((contributor) => (
                <div
                  key={contributor.rank}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{contributor.medal}</span>
                    <span className="font-medium text-gray-900">{contributor.name}</span>
                  </div>
                  <span className="text-blue-600 font-bold">
                    {contributor.issues_completed} issues
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Insights Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {performanceReport.ai_highlights.length > 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h3 className="font-semibold text-green-900 mb-4 flex items-center gap-2">
                <span>✨</span> Highlights
              </h3>
              <ul className="space-y-2">
                {performanceReport.ai_highlights.map((highlight, idx) => (
                  <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                    <span className="text-green-500 mt-1">✓</span>
                    {highlight}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {performanceReport.ai_concerns.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h3 className="font-semibold text-red-900 mb-4 flex items-center gap-2">
                <span>⚠️</span> Concerns
              </h3>
              <ul className="space-y-2">
                {performanceReport.ai_concerns.map((concern, idx) => (
                  <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                    <span className="text-red-500 mt-1">•</span>
                    {concern}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* AI Recommendations */}
        {performanceReport.ai_recommendations.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-semibold text-blue-900 mb-4 flex items-center gap-2">
              <span>💡</span> Recommendations
            </h3>
            <ul className="space-y-2">
              {performanceReport.ai_recommendations.map((recommendation, idx) => (
                <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                  <span className="text-blue-500 mt-1">→</span>
                  {recommendation}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }
);

EngineeringPerformanceReports.displayName = 'EngineeringPerformanceReports';

export default EngineeringPerformanceReports;
