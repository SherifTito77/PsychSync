/**
 * Bug Summarization - Memoized Sub-Component
 *
 * Extracted from ProductOperationsDashboard for better performance:
 * - Only re-renders when bugSummaries change
 * - Isolated component for easier testing and maintenance
 * - Can be lazy-loaded if needed
 */

import React, { useMemo } from 'react';
import { BugSummary } from './types';

interface BugSummarizationProps {
  bugSummaries: BugSummary[];
  loading?: boolean;
}

// Helper function to get trend icon (can be moved to utils if reused elsewhere)
function getTrendIcon(trend: string): string {
  switch (trend.toLowerCase()) {
    case 'up':
    case 'increasing':
      return '📈';
    case 'down':
    case 'decreasing':
      return '📉';
    case 'stable':
    case 'flat':
      return '➡️';
    default:
      return '📊';
  }
}

export const BugSummarization = React.memo<BugSummarizationProps>(({
  bugSummaries,
  loading = false,
}) => {
  // Memoize latest summary
  const latestSummary = useMemo(
    () => (bugSummaries.length > 0 ? bugSummaries[0] : null),
    [bugSummaries]
  );

  // Memoize recent summaries (last 7 days)
  const recentSummaries = useMemo(
    () => bugSummaries.slice(0, 7),
    [bugSummaries]
  );

  // Memoize total bugs calculation
  const totalBugs = useMemo(
    () => recentSummaries.reduce((sum, s) => sum + s.total_bugs, 0),
    [recentSummaries]
  );

  // Memoize critical bugs count
  const criticalBugs = useMemo(
    () => recentSummaries.reduce((sum, s) => sum + s.critical_bugs, 0),
    [recentSummaries]
  );

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-64 bg-gray-200 rounded-lg" />
      </div>
    );
  }

  if (bugSummaries.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No bug data available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Latest Summary Card */}
      {latestSummary && (
        <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg shadow p-6 border border-orange-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📅 Latest Daily Bug Summary
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-gray-900">
                {latestSummary.total_bugs}
              </p>
              <p className="text-sm text-gray-600 mt-1">Total Bugs</p>
            </div>
            <div className="bg-white rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-blue-600">
                {latestSummary.new_bugs}
              </p>
              <p className="text-sm text-gray-600 mt-1">New Today</p>
            </div>
            <div className="bg-white rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-green-600">
                {latestSummary.resolved_bugs}
              </p>
              <p className="text-sm text-gray-600 mt-1">Resolved</p>
            </div>
            <div className="bg-white rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-red-600">
                {latestSummary.critical_bugs}
              </p>
              <p className="text-sm text-gray-600 mt-1">Critical</p>
            </div>
            <div className="bg-white rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-orange-600">
                {latestSummary.major_bugs}
              </p>
              <p className="text-sm text-gray-600 mt-1">Major</p>
            </div>
          </div>

          {/* AI Summary Section */}
          {latestSummary.ai_summary && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm font-medium text-blue-900 mb-2">🤖 AI Summary</p>
              <p className="text-sm text-gray-700">{latestSummary.ai_summary}</p>
            </div>
          )}
        </div>
      )}

      {/* Statistics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">7-Day Total</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{totalBugs}</p>
          <p className="text-sm text-gray-600 mt-1">bugs reported</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Critical Issues</p>
          <p className="text-3xl font-bold text-red-600 mt-2">{criticalBugs}</p>
          <p className="text-sm text-gray-600 mt-1">need attention</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Resolution Rate</p>
          <p className="text-3xl font-bold text-green-600 mt-2">
            {totalBugs > 0
              ? ((recentSummaries.reduce((sum, s) => sum + s.resolved_bugs, 0) / totalBugs) * 100).toFixed(0)
              : 0}
            %
          </p>
          <p className="text-sm text-gray-600 mt-1">resolved</p>
        </div>
      </div>

      {/* Recent Summaries List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">
            Recent Daily Summaries
          </h3>
        </div>
        <div className="divide-y">
          {recentSummaries.map((summary) => (
            <div key={summary.id} className="p-6 hover:bg-gray-50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">
                    {new Date(summary.summary_date).toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {summary.new_bugs} new, {summary.resolved_bugs} resolved
                  </p>
                </div>
                <div className="text-right ml-6">
                  <p className="text-2xl font-bold text-gray-900">
                    {summary.total_bugs}
                  </p>
                  <p className="text-sm text-gray-600">total bugs</p>
                </div>
              </div>

              {/* AI Insights */}
              {summary.ai_insights && summary.ai_insights.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-900 mb-2">
                    💡 Key Insights
                  </p>
                  <ul className="space-y-1">
                    {summary.ai_insights.map((insight, idx) => (
                      <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                        <span>•</span>
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* AI Recommendations */}
              {summary.ai_recommendations && summary.ai_recommendations.length > 0 && (
                <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
                  <p className="text-sm font-medium text-yellow-900 mb-2">
                    📋 AI Recommendations
                  </p>
                  <ul className="space-y-1">
                    {summary.ai_recommendations.map((rec, idx) => (
                      <li key={idx} className="text-sm text-gray-700">
                        • {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});

BugSummarization.displayName = 'BugSummarization';

export default BugSummarization;
