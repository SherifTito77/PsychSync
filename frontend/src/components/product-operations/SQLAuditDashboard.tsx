/**
 * SQL Audit Dashboard - Memoized Sub-Component
 *
 * Extracted from ProductOperationsDashboard for better performance
 */

import React, { useMemo } from 'react';
import { SQLSecuritySummary, SQLQuery } from './types';

interface SQLAuditDashboardProps {
  sqlSummary: SQLSecuritySummary | null;
  sqlQueries: SQLQuery[];
  loading?: boolean;
}

// Helper functions
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

export const SQLAuditDashboard = React.memo<SQLAuditDashboardProps>(({
  sqlSummary,
  sqlQueries,
  loading = false,
}) => {
  // Memoize critical queries
  const criticalQueries = useMemo(
    () => sqlQueries.filter(q => q.risk_level === 'critical' || q.risk_level === 'high'),
    [sqlQueries]
  );

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-64 bg-gray-200 rounded-lg" />
      </div>
    );
  }

  if (!sqlSummary) {
    return (
      <div className="text-center py-12 text-gray-500">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">🔒 SQL Injection Audit Agent</h3>
          <p className="text-sm text-blue-700">
            SQL security scanning helps identify and prevent SQL injection vulnerabilities.
          </p>
        </div>
        <p>No SQL audit data available. Run a scan to see results.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Security Score Card */}
      <div className={`bg-white rounded-lg shadow-xl p-8 border-4 ${getGradeBgColor(sqlSummary.security_grade)}`}>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">SQL Security Grade</h2>
          <p className={`text-8xl font-bold ${getGradeColor(sqlSummary.security_grade)}`}>
            {sqlSummary.security_grade}
          </p>
          <p className="text-gray-600 mt-2 text-xl">
            Risk Score: {sqlSummary.overall_risk_score.toFixed(1)}/100
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Total Queries</p>
          <p className="text-4xl font-bold text-gray-900 mt-2">{sqlSummary.total_queries}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Vulnerabilities</p>
          <p className="text-4xl font-bold text-red-600 mt-2">{sqlSummary.total_vulnerabilities}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Parameterized</p>
          <p className="text-4xl font-bold text-green-600 mt-2">{sqlSummary.parameterization_rate.toFixed(1)}%</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">ORM Usage</p>
          <p className="text-4xl font-bold text-blue-600 mt-2">{sqlSummary.orm_usage_rate.toFixed(1)}%</p>
        </div>
      </div>

      {/* Critical Issues Alert */}
      {sqlSummary.critical_issues > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-900 mb-4">
            ⚠️ Critical Issues Require Immediate Attention
          </h3>
          <p className="text-red-700">
            {sqlSummary.critical_issues} critical SQL injection vulnerabilities detected.
            These should be addressed immediately to prevent potential security breaches.
          </p>
        </div>
      )}

      {/* Vulnerable Queries List */}
      {sqlQueries.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Detected SQL Queries</h3>
          </div>
          <div className="divide-y max-h-96 overflow-y-auto">
            {sqlQueries.map((query) => (
              <div key={query.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(query.risk_level)}`}>
                        {query.risk_level}
                      </span>
                      <span className="text-sm text-gray-600">
                        Risk Score: {query.risk_score.toFixed(1)}/100
                      </span>
                    </div>
                    <code className="block bg-gray-100 rounded p-3 text-sm font-mono overflow-x-auto">
                      {query.query_text}
                    </code>
                    <p className="text-sm text-gray-600 mt-2">
                      📁 {query.file_path}:{query.line_number}
                    </p>
                  </div>
                </div>

                {query.ai_suggestion && (
                  <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-900 mb-1">🤖 AI Suggestion</p>
                    <p className="text-sm text-gray-700">{query.ai_suggestion}</p>
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

SQLAuditDashboard.displayName = 'SQLAuditDashboard';

export default SQLAuditDashboard;
