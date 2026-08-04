/**
 * Pull Request Quality - Memoized Sub-Component
 *
 * Extracted from ProductOperationsDashboard for better performance:
 * - Only re-renders when pullRequests change
 * - Memoized calculations for statistics
 * - Optimized list rendering
 */

import React, { useMemo } from 'react';
import { PullRequestQuality as PullRequestQualityType } from './types';

interface PullRequestQualityProps {
  pullRequests: PullRequestQualityType[];
  loading?: boolean;
}

// Helper function to get risk color
function getRiskColor(risk: string): string {
  switch (risk.toLowerCase()) {
    case 'critical':
      return 'bg-red-100 text-red-800';
    case 'high':
      return 'bg-orange-100 text-orange-800';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800';
    case 'low':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export const PullRequestQuality = React.memo<PullRequestQualityProps>(({
  pullRequests,
  loading = false,
}) => {
  // Memoize statistics
  const stats = useMemo(() => {
    if (pullRequests.length === 0) return null;

    const avgScore = pullRequests.reduce((sum, pr) => sum + pr.overall_score, 0) / pullRequests.length;
    const highRiskCount = pullRequests.filter(
      pr => pr.risk_level === 'high' || pr.risk_level === 'critical'
    ).length;
    const mergedCount = pullRequests.filter(pr => pr.is_merged).length;

    return {
      total: pullRequests.length,
      avgScore: avgScore.toFixed(0),
      highRiskCount,
      mergedCount,
    };
  }, [pullRequests]);

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-64 bg-gray-200 rounded-lg" />
      </div>
    );
  }

  if (pullRequests.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No pull request data available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm font-medium">Total PRs</p>
            <p className="text-4xl font-bold text-gray-900 mt-2">{stats.total}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm font-medium">Avg Quality Score</p>
            <p className="text-4xl font-bold text-blue-600 mt-2">{stats.avgScore}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm font-medium">High Risk</p>
            <p className="text-4xl font-bold text-red-600 mt-2">{stats.highRiskCount}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm font-medium">Merged</p>
            <p className="text-4xl font-bold text-green-600 mt-2">{stats.mergedCount}</p>
          </div>
        </div>
      )}

      {/* Pull Requests List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Recent Pull Requests</h3>
        </div>
        <div className="divide-y">
          {pullRequests.map((pr) => (
            <div key={pr.id} className="p-6 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-blue-600 font-medium">#{pr.pr_number}</span>
                    <h4 className="font-semibold text-gray-900">{pr.pr_title}</h4>
                  </div>
                  <p className="text-sm text-gray-600">
                    by {pr.author_name} • {pr.files_changed} files • {pr.lines_added}+ lines
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(pr.created_at).toLocaleDateString()}
                  </p>

                  {/* Risk Factors */}
                  {pr.risk_factors && pr.risk_factors.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {pr.risk_factors.map((factor, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full"
                        >
                          {factor}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* AI Recommendations */}
                  {pr.ai_recommendations && pr.ai_recommendations.length > 0 && (
                    <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm font-medium text-blue-900 mb-2">
                        🤖 AI Recommendations
                      </p>
                      <ul className="space-y-1">
                        {pr.ai_recommendations.map((rec, idx) => (
                          <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                            <span>•</span>
                            <span>{rec.message}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <div className="ml-6 text-center">
                  <p className="text-sm text-gray-600 mb-2">Quality Score</p>
                  <p
                    className={`text-3xl font-bold ${
                      pr.overall_score >= 80
                        ? 'text-green-600'
                        : pr.overall_score >= 60
                        ? 'text-yellow-600'
                        : 'text-red-600'
                    }`}
                  >
                    {pr.overall_score.toFixed(0)}
                  </p>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium mt-2 inline-block ${getRiskColor(
                      pr.risk_level
                    )}`}
                  >
                    {pr.risk_level}
                  </span>
                  {pr.merge_confidence && (
                    <p className="text-xs text-gray-500 mt-2">
                      Merge: {(pr.merge_confidence * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});

PullRequestQuality.displayName = 'PullRequestQuality';

export default PullRequestQuality;
