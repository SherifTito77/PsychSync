/**
 * Product Operations Dashboard
 *
 * Comprehensive dashboard for AI-powered engineering operations
 * Combines code quality monitoring, Jira bug tracking, and performance reports
 *
 * Features:
 * - Code Quality Overview (score, grade, trends)
 * - Bug Summarization (daily summaries, severity breakdown)
 * - Pull Request Quality (risk assessment, merge confidence)
 * - Engineering Performance Reports (weekly reports with AI insights)
 * - Sprint Metrics (velocity, completion rate)
 * - SQL Injection Audit (vulnerability scanning, risk assessment)
 * - Query Performance Optimization (slow query analysis, index recommendations)
 */

import React, { useState, useEffect } from 'react';
import api from '../services/api';

// New interfaces for SQL Audit
interface SQLSecuritySummary {
  total_queries: number;
  total_vulnerabilities: number;
  safe_queries: number;
  at_risk_queries: number;
  overall_risk_score: number;
  security_grade: string;
  critical_issues: number;
  parameterization_rate: number;
  orm_usage_rate: number;
}

interface SQLQuery {
  id: string;
  query_text: string;
  file_path: string;
  line_number: number;
  risk_level: string;
  risk_score: number;
  vulnerability_type?: string;
  ai_suggestion?: string;
  safe_example?: string;
}

// New interfaces for Query Performance
interface QueryPerformanceSummary {
  total_queries: number;
  slow_queries: number;
  critical_queries: number;
  avg_query_time_ms: number;
  overall_performance_grade: string;
  optimization_potential_ms: number;
  estimated_improvement_percentage: number;
}

interface SlowQuery {
  id: string;
  query_text: string;
  query_signature: string;
  performance_tier: string;
  avg_time_ms: number;
  bottleneck_type?: string;
  ai_suggestion?: string;
  suggested_index?: string;
  estimated_improvement?: number;
}

// Build Failure Analysis interfaces
interface BuildFailureSummary {
  total_failures: number;
  unresolved_failures: number;
  critical_failures: number;
  high_priority_failures: number;
  overall_health_grade: string;
  average_resolution_time_minutes: number;
  most_common_failure_type: string;
  flaky_test_count: number;
  top_contributing_factor: string;
}

interface BuildFailure {
  id: string;
  build_id: string;
  project_name: string;
  branch_name: string;
  commit_hash: string;
  failure_type: string;
  failure_stage: string;
  error_message: string;
  stack_trace?: string;
  failed_tests?: string[];
  developer_name: string;
  root_cause_category: string;
  suspected_culprit_file?: string;
  ai_suggested_fix?: string;
  priority: string;
  is_resolved: boolean;
  created_at: string;
}

// Caching Configuration interfaces
interface CacheSummary {
  total_cache_entries: number;
  overall_hit_rate: number;
  total_memory_usage_mb: number;
  avg_response_time_ms: number;
  configuration_grade: string;
  optimization_opportunities: number;
  potential_improvement_mb: number;
  active_cache_types: string[];
}

interface CacheEntry {
  id: string;
  cache_key: string;
  cache_type: string;
  endpoint_path: string;
  data_size_bytes: number;
  ttl_seconds: number;
  hit_count: number;
  miss_count: number;
  hit_rate: number;
  miss_rate: number;
  last_accessed: string;
}

// Breaking Changes interfaces
interface BreakingChangesSummary {
  total_changes: number;
  unresolved_changes: number;
  critical_changes: number;
  high_priority_changes: number;
  overall_risk_score: number;
  risk_grade: string;
  backwards_compatible_count: number;
  breaking_changes_count: number;
  most_common_change_type: string;
  most_affected_component: string;
}

interface BreakingChange {
  id: string;
  change_type: string;
  affected_component: string;
  description: string;
  severity: string;
  source_branch: string;
  commit_hash: string;
  file_path: string;
  line_number: number;
  backwards_compatible: boolean;
  migration_required: boolean;
  affected_endpoints?: string[];
  ai_risk_assessment?: string;
  ai_mitigation_suggestion?: string;
  is_approved: boolean;
  created_at: string;
}

interface CodeQualitySummary {
  current_score: number;
  current_grade: string;
  trend: string;
  trend_percentage: number;
  total_issues: number;
  critical_issues: number;
  major_issues: number;
  test_coverage: number;
  technical_debt_hours: number;
  files_scanned: number;
  last_scan_date: string;
}

interface BugSummary {
  id: string;
  summary_date: string;
  total_bugs: number;
  new_bugs: number;
  resolved_bugs: number;
  critical_bugs: number;
  major_bugs: number;
  minor_bugs: number;
  ai_summary?: string;
  ai_insights?: string[];
  ai_recommendations?: string[];
}

interface PullRequestQuality {
  id: string;
  pr_number: number;
  pr_title: string;
  author_name: string;
  created_at: string;
  overall_score: number;
  risk_level: string;
  risk_factors?: string[];
  files_changed: number;
  lines_added: number;
  ai_recommendations?: Array<{
    type: string;
    message: string;
    priority: string;
  }>;
  merge_confidence?: number;
  is_merged: boolean;
}

interface PerformanceReport {
  period_start: string;
  period_end: string;
  total_bugs_created: number;
  total_bugs_resolved: number;
  bugs_by_severity: {
    critical: number;
    major: number;
    minor: number;
  };
  avg_resolution_time_hours: number;
  sprints_completed: number;
  avg_velocity: number;
  completion_rate: number;
  top_contributors: Array<{
    name: string;
    issues_completed: number;
  }>;
  ai_summary: string;
  ai_highlights: string[];
  ai_concerns: string[];
  ai_recommendations: string[];
}

interface SprintMetrics {
  id: string;
  sprint_id: string;
  sprint_name: string;
  start_date: string;
  end_date: string;
  state: string;
  completed_points: number;
  completion_rate: number;
  bugs_found: number;
  bugs_fixed: number;
  team_velocity?: number;
}

const ProductOperationsDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'quality' | 'bugs' | 'prs' | 'reports' | 'sql_audit' | 'query_performance' | 'build_analysis' | 'caching_config' | 'breaking_changes'>('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [qualitySummary, setQualitySummary] = useState<CodeQualitySummary | null>(null);
  const [bugSummaries, setBugSummaries] = useState<BugSummary[]>([]);
  const [pullRequests, setPullRequests] = useState<PullRequestQuality[]>([]);
  const [performanceReport, setPerformanceReport] = useState<PerformanceReport | null>(null);
  const [sprints, setSprints] = useState<SprintMetrics[]>([]);

  // AI agents states
  const [sqlSummary, setSqlSummary] = useState<SQLSecuritySummary | null>(null);
  const [sqlQueries, setSqlQueries] = useState<SQLQuery[]>([]);
  const [queryPerfSummary, setQueryPerfSummary] = useState<QueryPerformanceSummary | null>(null);
  const [slowQueries, setSlowQueries] = useState<SlowQuery[]>([]);

  // New AI agents states
  const [buildSummary, setBuildSummary] = useState<BuildFailureSummary | null>(null);
  const [buildFailures, setBuildFailures] = useState<BuildFailure[]>([]);
  const [cacheSummary, setCacheSummary] = useState<CacheSummary | null>(null);
  const [cacheEntries, setCacheEntries] = useState<CacheEntry[]>([]);
  const [breakingChangesSummary, setBreakingChangesSummary] = useState<BreakingChangesSummary | null>(null);
  const [breakingChanges, setBreakingChanges] = useState<BreakingChange[]>([]);

  // Fetch all data on mount
  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch data in parallel using the configured api service
      const [
        qualityRes,
        bugsRes,
        prsRes,
        reportRes,
        sprintsRes,
        sqlSummaryRes,
        sqlQueriesRes,
        queryPerfSummaryRes,
        slowQueriesRes,
        buildSummaryRes,
        buildFailuresRes,
        cacheSummaryRes,
        cacheEntriesRes,
        breakingChangesSummaryRes,
        breakingChangesRes,
      ] = await Promise.all([
        api.get('/metrics/summary'),
        api.get('/jira_integration/bugs/summary?project_key=PROJ&days=14'),
        api.get('/pull-requests?limit=10'),
        api.get('/jira_integration/reports/performance?project_key=PROJ&days=7'),
        api.get('/jira_integration/sprints?project_key=PROJ'),
        // AI agent endpoints
        api.get('/sql_audit/queries/summary').catch(() => ({ data: null })),
        api.get('/sql_audit/queries?limit=5').catch(() => ({ data: [] })),
        api.get('/query_performance/queries/summary').catch(() => ({ data: null })),
        api.get('/query_performance/queries?limit=5').catch(() => ({ data: [] })),
        // New AI agent endpoints
        api.get('/build_analysis/failures/summary').catch(() => ({ data: null })),
        api.get('/build_analysis/failures/unresolved?limit=5').catch(() => ({ data: [] })),
        api.get('/caching_config/entries/summary').catch(() => ({ data: null })),
        api.get('/caching_config/entries/low_hit_rate?limit=5').catch(() => ({ data: [] })),
        api.get('/breaking_changes/changes/summary').catch(() => ({ data: null })),
        api.get('/breaking_changes/changes/unapproved?limit=5').catch(() => ({ data: [] })),
      ]);

      setQualitySummary(qualityRes.data);
      setBugSummaries(bugsRes.data);
      setPullRequests(prsRes.data);
      setPerformanceReport(reportRes.data);
      setSprints(sprintsRes.data);

      // Set AI agent data
      setSqlSummary(sqlSummaryRes.data);
      setSqlQueries(sqlQueriesRes.data || []);
      setQueryPerfSummary(queryPerfSummaryRes.data);
      setSlowQueries(slowQueriesRes.data || []);
      setBuildSummary(buildSummaryRes.data);
      setBuildFailures(buildFailuresRes.data || []);
      setCacheSummary(cacheSummaryRes.data);
      setCacheEntries(cacheEntriesRes.data || []);
      setBreakingChangesSummary(breakingChangesSummaryRes.data);
      setBreakingChanges(breakingChangesRes.data || []);
    } catch (err: any) {
      console.error('Error fetching dashboard data:', err);
      setError(err.response?.data?.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (grade: string) => {
    if (grade.startsWith('A')) return 'text-green-600';
    if (grade.startsWith('B')) return 'text-blue-600';
    if (grade.startsWith('C')) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getGradeBgColor = (grade: string) => {
    if (grade.startsWith('A')) return 'bg-green-100 border-green-200';
    if (grade.startsWith('B')) return 'bg-blue-100 border-blue-200';
    if (grade.startsWith('C')) return 'bg-yellow-100 border-yellow-200';
    return 'bg-red-100 border-red-200';
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'critical': return 'text-red-700 bg-red-100';
      case 'high': return 'text-orange-700 bg-orange-100';
      case 'medium': return 'text-yellow-700 bg-yellow-100';
      case 'low': return 'text-green-700 bg-green-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return '📈';
      case 'declining': return '📉';
      default: return '➡️';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Product Operations Dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h3 className="text-red-800 font-semibold mb-2">Error Loading Dashboard</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchAllData}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Product Operations Dashboard</h1>
              <p className="text-gray-600 mt-1">AI-Powered Engineering Intelligence</p>
            </div>
            <button
              onClick={fetchAllData}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <span>🔄</span>
              Refresh Data
            </button>
          </div>

          {/* Tab Navigation */}
          <div className="mt-6 border-b border-gray-200">
            <nav className="flex space-x-8">
              {[
                { id: 'overview', label: 'Overview', icon: '📊' },
                { id: 'quality', label: 'Code Quality', icon: '✅' },
                { id: 'bugs', label: 'Bug Tracking', icon: '🐛' },
                { id: 'prs', label: 'Pull Requests', icon: '🔀' },
                { id: 'reports', label: 'Performance', icon: '📈' },
                { id: 'sql_audit', label: 'SQL Audit', icon: '🔒' },
                { id: 'query_performance', label: 'Query Performance', icon: '⚡' },
                { id: 'build_analysis', label: 'Build Analysis', icon: '🔨' },
                { id: 'caching_config', label: 'Caching', icon: '💾' },
                { id: 'breaking_changes', label: 'Breaking Changes', icon: '🚨' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
                >
                  <span>{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'overview' && (
          <OverviewTab
            qualitySummary={qualitySummary}
            bugSummaries={bugSummaries}
            pullRequests={pullRequests}
            performanceReport={performanceReport}
            getGradeColor={getGradeColor}
            getGradeBgColor={getGradeBgColor}
            getRiskColor={getRiskColor}
            getTrendIcon={getTrendIcon}
          />
        )}

        {activeTab === 'quality' && (
          <QualityTab
            qualitySummary={qualitySummary}
            getGradeColor={getGradeColor}
            getGradeBgColor={getGradeBgColor}
            getTrendIcon={getTrendIcon}
          />
        )}

        {activeTab === 'bugs' && (
          <BugsTab
            bugSummaries={bugSummaries}
            getTrendIcon={getTrendIcon}
          />
        )}

        {activeTab === 'prs' && (
          <PRsTab
            pullRequests={pullRequests}
            getRiskColor={getRiskColor}
          />
        )}

        {activeTab === 'reports' && (
          <ReportsTab
            performanceReport={performanceReport}
            sprints={sprints}
          />
        )}

        {activeTab === 'sql_audit' && (
          <SQLAuditTab
            sqlSummary={sqlSummary}
            sqlQueries={sqlQueries}
            getGradeColor={getGradeColor}
            getGradeBgColor={getGradeBgColor}
            getRiskColor={getRiskColor}
          />
        )}

        {activeTab === 'query_performance' && (
          <QueryPerformanceTab
            queryPerfSummary={queryPerfSummary}
            slowQueries={slowQueries}
            getGradeColor={getGradeColor}
            getGradeBgColor={getGradeBgColor}
          />
        )}

        {activeTab === 'build_analysis' && (
          <BuildAnalysisTab
            buildSummary={buildSummary}
            buildFailures={buildFailures}
            getGradeColor={getGradeColor}
            getGradeBgColor={getGradeBgColor}
            getRiskColor={getRiskColor}
          />
        )}

        {activeTab === 'caching_config' && (
          <CachingConfigTab
            cacheSummary={cacheSummary}
            cacheEntries={cacheEntries}
            getGradeColor={getGradeColor}
            getGradeBgColor={getGradeBgColor}
          />
        )}

        {activeTab === 'breaking_changes' && (
          <BreakingChangesTab
            breakingChangesSummary={breakingChangesSummary}
            breakingChanges={breakingChanges}
            getGradeColor={getGradeColor}
            getGradeBgColor={getGradeBgColor}
            getRiskColor={getRiskColor}
          />
        )}
      </div>
    </div>
  );
};

// Overview Tab Component
const OverviewTab: React.FC<{
  qualitySummary: CodeQualitySummary | null;
  bugSummaries: BugSummary[];
  pullRequests: PullRequestQuality[];
  performanceReport: PerformanceReport | null;
  getGradeColor: (grade: string) => string;
  getGradeBgColor: (grade: string) => string;
  getRiskColor: (risk: string) => string;
  getTrendIcon: (trend: string) => string;
}> = ({
  qualitySummary,
  bugSummaries,
  pullRequests,
  performanceReport,
  getGradeColor,
  getGradeBgColor,
  getRiskColor,
  getTrendIcon,
}) => {
  const latestBugSummary = bugSummaries[0];

  return (
    <div className="space-y-6">
      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Code Quality Score */}
        {qualitySummary && (
          <div className={`bg-white rounded-lg shadow p-6 border-2 ${getGradeBgColor(qualitySummary.current_grade)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">Code Quality</p>
                <p className="text-3xl font-bold mt-2">{getGradeColor(qualitySummary.current_grade).includes('green') ? '✅' : '⚠️'}</p>
                <p className={`text-4xl font-bold ${getGradeColor(qualitySummary.current_grade)}`}>
                  {qualitySummary.current_grade}
                </p>
                <p className="text-gray-600 mt-1">
                  Score: {qualitySummary.current_score.toFixed(1)}/100
                </p>
              </div>
              <div className="text-right">
                <span className="text-4xl">{getTrendIcon(qualitySummary.trend)}</span>
                <p className="text-sm text-gray-600 mt-2">
                  {qualitySummary.trend_percentage > 0 ? '+' : ''}{qualitySummary.trend_percentage.toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Bug Summary */}
        {latestBugSummary && (
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm font-medium">Bug Status</p>
            <p className="text-3xl font-bold mt-2 text-orange-600">🐛</p>
            <p className="text-4xl font-bold text-gray-900 mt-2">
              {latestBugSummary.total_bugs}
            </p>
            <div className="mt-4 space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-red-600">Critical: {latestBugSummary.critical_bugs}</span>
                <span className="text-orange-600">Major: {latestBugSummary.major_bugs}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-600">Resolved: {latestBugSummary.resolved_bugs}</span>
                <span className="text-blue-600">New: {latestBugSummary.new_bugs}</span>
              </div>
            </div>
          </div>
        )}

        {/* Sprint Velocity */}
        {performanceReport && (
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm font-medium">Sprint Velocity</p>
            <p className="text-3xl font-bold mt-2">🏃</p>
            <p className="text-4xl font-bold text-gray-900 mt-2">
              {performanceReport.avg_velocity}
            </p>
            <p className="text-sm text-gray-600 mt-2">story points</p>
            <div className="mt-4 pt-4 border-t">
              <p className="text-sm text-gray-600">Completion Rate</p>
              <p className="text-2xl font-bold text-green-600">
                {performanceReport.completion_rate.toFixed(1)}%
              </p>
            </div>
          </div>
        )}

        {/* PR Risk Overview */}
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">PR Risk Overview</p>
          <p className="text-3xl font-bold mt-2">🔀</p>
          <p className="text-4xl font-bold text-gray-900 mt-2">
            {pullRequests.length}
          </p>
          <p className="text-sm text-gray-600 mt-2">recent PRs</p>
          <div className="mt-4 space-y-1 text-sm">
            {pullRequests.slice(0, 3).map((pr) => (
              <div key={pr.id} className="flex items-center justify-between">
                <span className="text-gray-700 truncate">#{pr.pr_number}</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(pr.risk_level)}`}>
                  {pr.risk_level}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Insights */}
      {performanceReport && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg shadow p-6 border border-blue-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">🤖 AI-Generated Insights</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Highlights */}
            {performanceReport.ai_highlights.length > 0 && (
              <div>
                <h4 className="font-medium text-green-800 mb-2 flex items-center gap-2">
                  <span>✨</span> Highlights
                </h4>
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

            {/* Concerns */}
            {performanceReport.ai_concerns.length > 0 && (
              <div>
                <h4 className="font-medium text-red-800 mb-2 flex items-center gap-2">
                  <span>⚠️</span> Concerns
                </h4>
                <ul className="space-y-2">
                  {performanceReport.ai_concerns.map((concern, idx) => (
                    <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="text-red-500 mt-1">!</span>
                      {concern}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2">
            <span>📊</span>
            Run Quality Scan
          </button>
          <button className="bg-orange-600 text-white px-4 py-3 rounded-lg hover:bg-orange-700 flex items-center justify-center gap-2">
            <span>🐛</span>
            Generate Bug Report
          </button>
          <button className="bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700 flex items-center justify-center gap-2">
            <span>📈</span>
            Create Performance Report
          </button>
        </div>
      </div>
    </div>
  );
};

// Quality Tab Component
const QualityTab: React.FC<{
  qualitySummary: CodeQualitySummary | null;
  getGradeColor: (grade: string) => string;
  getGradeBgColor: (grade: string) => string;
  getTrendIcon: (trend: string) => string;
}> = ({ qualitySummary, getGradeColor, getGradeBgColor, getTrendIcon }) => {
  if (!qualitySummary) {
    return <div className="text-center py-12 text-gray-500">No quality data available</div>;
  }

  return (
    <div className="space-y-6">
      {/* Quality Score Card */}
      <div className={`bg-white rounded-lg shadow-xl p-8 border-4 ${getGradeBgColor(qualitySummary.current_grade)}`}>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Overall Code Quality</h2>
          <div className="flex items-center justify-center gap-8">
            <div>
              <p className={`text-8xl font-bold ${getGradeColor(qualitySummary.current_grade)}`}>
                {qualitySummary.current_grade}
              </p>
              <p className="text-gray-600 mt-2 text-xl">
                {qualitySummary.current_score.toFixed(1)}/100
              </p>
            </div>
            <div className="text-left">
              <p className="text-gray-600 mb-2">Trend</p>
              <p className="text-4xl">{getTrendIcon(qualitySummary.trend)}</p>
              <p className={`text-lg font-medium mt-2 ${
                qualitySummary.trend === 'improving' ? 'text-green-600' :
                qualitySummary.trend === 'declining' ? 'text-red-600' :
                'text-gray-600'
              }`}>
                {qualitySummary.trend}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Issue Breakdown</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Critical</span>
              <span className="text-lg font-bold text-red-600">{qualitySummary.critical_issues}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Major</span>
              <span className="text-lg font-bold text-orange-600">{qualitySummary.major_issues}</span>
            </div>
            <div className="flex justify-between items-center border-t pt-3">
              <span className="text-gray-900 font-medium">Total Issues</span>
              <span className="text-2xl font-bold text-gray-900">{qualitySummary.total_issues}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Test Coverage</h3>
          <div className="text-center">
            <p className="text-5xl font-bold text-blue-600">{qualitySummary.test_coverage.toFixed(1)}%</p>
            <div className="mt-4 bg-gray-200 rounded-full h-3">
              <div
                className="bg-blue-600 h-3 rounded-full"
                style={{ width: `${qualitySummary.test_coverage}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Technical Debt</h3>
          <div className="text-center">
            <p className="text-5xl font-bold text-purple-600">{qualitySummary.technical_debt_hours.toFixed(0)}h</p>
            <p className="text-gray-600 mt-2">Estimated remediation time</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Scan Information</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Files Scanned</p>
            <p className="text-2xl font-bold text-gray-900">{qualitySummary.files_scanned}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Last Scan</p>
            <p className="text-sm font-medium text-gray-900">
              {new Date(qualitySummary.last_scan_date).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Bugs Tab Component
const BugsTab: React.FC<{
  bugSummaries: BugSummary[];
  getTrendIcon: (trend: string) => string;
}> = ({ bugSummaries, getTrendIcon }) => {
  if (bugSummaries.length === 0) {
    return <div className="text-center py-12 text-gray-500">No bug data available</div>;
  }

  return (
    <div className="space-y-6">
      {/* Latest Summary */}
      {bugSummaries[0] && (
        <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg shadow p-6 border border-orange-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📅 Latest Daily Bug Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-gray-900">{bugSummaries[0].total_bugs}</p>
              <p className="text-sm text-gray-600 mt-1">Total Bugs</p>
            </div>
            <div className="bg-white rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-blue-600">{bugSummaries[0].new_bugs}</p>
              <p className="text-sm text-gray-600 mt-1">New Today</p>
            </div>
            <div className="bg-white rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-green-600">{bugSummaries[0].resolved_bugs}</p>
              <p className="text-sm text-gray-600 mt-1">Resolved</p>
            </div>
            <div className="bg-white rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-red-600">{bugSummaries[0].critical_bugs}</p>
              <p className="text-sm text-gray-600 mt-1">Critical</p>
            </div>
            <div className="bg-white rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-orange-600">{bugSummaries[0].major_bugs}</p>
              <p className="text-sm text-gray-600 mt-1">Major</p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Summaries */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Recent Daily Summaries</h3>
        </div>
        <div className="divide-y">
          {bugSummaries.slice(0, 7).map((summary) => (
            <div key={summary.id} className="p-6 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">
                    {new Date(summary.summary_date).toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {summary.new_bugs} new, {summary.resolved_bugs} resolved
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900">{summary.total_bugs}</p>
                  <p className="text-sm text-gray-600">total bugs</p>
                </div>
              </div>

              {summary.ai_summary && (
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm font-medium text-blue-900 mb-2">🤖 AI Summary</p>
                  <p className="text-sm text-gray-700">{summary.ai_summary}</p>
                </div>
              )}

              {summary.ai_insights && summary.ai_insights.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-900 mb-2">Key Insights</p>
                  <ul className="space-y-1">
                    {summary.ai_insights.map((insight, idx) => (
                      <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                        <span>💡</span>
                        {insight}
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
};

// PRs Tab Component
const PRsTab: React.FC<{
  pullRequests: PullRequestQuality[];
  getRiskColor: (risk: string) => string;
}> = ({ pullRequests, getRiskColor }) => {
  if (pullRequests.length === 0) {
    return <div className="text-center py-12 text-gray-500">No pull request data available</div>;
  }

  return (
    <div className="space-y-6">
      {/* PR Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Total PRs</p>
          <p className="text-4xl font-bold text-gray-900 mt-2">{pullRequests.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Avg Quality Score</p>
          <p className="text-4xl font-bold text-blue-600 mt-2">
            {(pullRequests.reduce((sum, pr) => sum + pr.overall_score, 0) / pullRequests.length).toFixed(0)}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">High Risk</p>
          <p className="text-4xl font-bold text-red-600 mt-2">
            {pullRequests.filter(pr => pr.risk_level === 'high' || pr.risk_level === 'critical').length}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Merged</p>
          <p className="text-4xl font-bold text-green-600 mt-2">
            {pullRequests.filter(pr => pr.is_merged).length}
          </p>
        </div>
      </div>

      {/* Pull Requests List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Recent Pull Requests</h3>
        </div>
        <div className="divide-y">
          {pullRequests.map((pr) => (
            <div key={pr.id} className="p-6 hover:bg-gray-50">
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

                  {pr.ai_recommendations && pr.ai_recommendations.length > 0 && (
                    <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm font-medium text-blue-900 mb-2">🤖 AI Recommendations</p>
                      <ul className="space-y-1">
                        {pr.ai_recommendations.map((rec, idx) => (
                          <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                            <span>•</span>
                            {rec.message}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <div className="ml-6 text-center">
                  <p className="text-sm text-gray-600 mb-2">Quality Score</p>
                  <p className={`text-3xl font-bold ${
                    pr.overall_score >= 80 ? 'text-green-600' :
                    pr.overall_score >= 60 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {pr.overall_score.toFixed(0)}
                  </p>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium mt-2 inline-block ${getRiskColor(pr.risk_level)}`}>
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
};

// Reports Tab Component
const ReportsTab: React.FC<{
  performanceReport: PerformanceReport | null;
  sprints: SprintMetrics[];
}> = ({ performanceReport, sprints }) => {
  if (!performanceReport) {
    return <div className="text-center py-12 text-gray-500">No performance data available</div>;
  }

  return (
    <div className="space-y-6">
      {/* Report Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg shadow-xl p-8 text-white">
        <h2 className="text-3xl font-bold mb-2">Weekly Engineering Performance Report</h2>
        <p className="text-purple-100">
          {new Date(performanceReport.period_start).toLocaleDateString()} - {new Date(performanceReport.period_end).toLocaleDateString()}
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
            <p className="text-4xl font-bold text-gray-900">{performanceReport.total_bugs_created}</p>
            <p className="text-gray-600 mt-1">Created</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-green-600">{performanceReport.total_bugs_resolved}</p>
            <p className="text-gray-600 mt-1">Resolved</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-blue-600">
              {performanceReport.total_bugs_resolved > 0
                ? ((performanceReport.total_bugs_resolved / performanceReport.total_bugs_created) * 100).toFixed(0)
                : 0}%
            </p>
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
              <span className="text-gray-700">Critical: {performanceReport.bugs_by_severity.critical}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-orange-600 rounded"></div>
              <span className="text-gray-700">Major: {performanceReport.bugs_by_severity.major}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-yellow-600 rounded"></div>
              <span className="text-gray-700">Minor: {performanceReport.bugs_by_severity.minor}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sprint Metrics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🏃 Sprint Performance</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          <div className="text-center">
            <p className="text-4xl font-bold text-gray-900">{performanceReport.sprints_completed}</p>
            <p className="text-gray-600 mt-1">Sprints Completed</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-blue-600">{performanceReport.avg_velocity}</p>
            <p className="text-gray-600 mt-1">Avg Velocity</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-green-600">{performanceReport.completion_rate.toFixed(1)}%</p>
            <p className="text-gray-600 mt-1">Completion Rate</p>
          </div>
        </div>
      </div>

      {/* Top Contributors */}
      {performanceReport.top_contributors.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">⭐ Top Contributors</h3>
          <div className="space-y-3">
            {performanceReport.top_contributors.map((contributor, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">
                    {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : '🏅'}
                  </span>
                  <span className="font-medium text-gray-900">{contributor.name}</span>
                </div>
                <span className="text-blue-600 font-bold">{contributor.issues_completed} issues</span>
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
                  <span className="text-red-500 mt-1">!</span>
                  {concern}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

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

      {/* Sprint Details */}
      {sprints.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Sprint Details</h3>
          <div className="space-y-4">
            {sprints.map((sprint) => (
              <div key={sprint.id} className="p-4 border rounded-lg hover:bg-gray-50">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-semibold text-gray-900">{sprint.sprint_name}</h4>
                    <p className="text-sm text-gray-600">
                      {new Date(sprint.start_date).toLocaleDateString()} - {new Date(sprint.end_date).toLocaleDateString()}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    sprint.state === 'active' ? 'bg-green-100 text-green-800' :
                    sprint.state === 'closed' ? 'bg-gray-100 text-gray-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {sprint.state}
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Completed Points</p>
                    <p className="font-bold text-gray-900">{sprint.completed_points}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Completion Rate</p>
                    <p className="font-bold text-green-600">{sprint.completion_rate?.toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Bugs Found/Fixed</p>
                    <p className="font-bold text-gray-900">{sprint.bugs_found} / {sprint.bugs_fixed}</p>
                  </div>
                  {sprint.team_velocity && (
                    <div>
                      <p className="text-gray-600">Velocity</p>
                      <p className="font-bold text-blue-600">{sprint.team_velocity} pts</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// SQL Audit Tab Component
const SQLAuditTab: React.FC<{
  sqlSummary: SQLSecuritySummary | null;
  sqlQueries: SQLQuery[];
  getGradeColor: (grade: string) => string;
  getGradeBgColor: (grade: string) => string;
  getRiskColor: (risk: string) => string;
}> = ({ sqlSummary, sqlQueries, getGradeColor, getGradeBgColor, getRiskColor }) => {
  if (!sqlSummary) {
    return (
      <div className="space-y-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">🔒 SQL Injection Audit Agent</h3>
          <p className="text-sm text-blue-700">SQL security scanning helps identify and prevent SQL injection vulnerabilities.</p>
        </div>
        <div className="text-center py-12 text-gray-500">
          No SQL audit data available. Run a scan to see results.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Security Score Card */}
      <div className={`bg-white rounded-lg shadow-xl p-8 border-4 ${getGradeBgColor(sqlSummary.security_grade)}`}>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">SQL Security Grade</h2>
          <div>
            <p className={`text-8xl font-bold ${getGradeColor(sqlSummary.security_grade)}`}>
              {sqlSummary.security_grade}
            </p>
            <p className="text-gray-600 mt-2 text-xl">
              Risk Score: {sqlSummary.overall_risk_score.toFixed(1)}/100
            </p>
          </div>
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

      {/* Critical Issues */}
      {sqlSummary.critical_issues > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-900 mb-4">⚠️ Critical Issues Require Immediate Attention</h3>
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
          <div className="divide-y">
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

                {query.vulnerability_type && (
                  <div className="mt-3">
                    <span className="text-sm font-medium text-gray-900">Vulnerability Type: </span>
                    <span className="text-sm text-red-600">{query.vulnerability_type}</span>
                  </div>
                )}

                {query.ai_suggestion && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-900 mb-2">🤖 AI Suggestion</p>
                    <p className="text-sm text-gray-700">{query.ai_suggestion}</p>
                  </div>
                )}

                {query.safe_example && (
                  <div className="mt-4 p-4 bg-green-50 rounded-lg">
                    <p className="text-sm font-medium text-green-900 mb-2">✅ Safe Example</p>
                    <code className="block text-sm font-mono">{query.safe_example}</code>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2">
            <span>🔍</span>
            Run SQL Security Scan
          </button>
          <button className="bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 flex items-center justify-center gap-2">
            <span>🔧</span>
            Auto-fix Vulnerabilities
          </button>
          <button className="bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700 flex items-center justify-center gap-2">
            <span>📊</span>
            Generate Security Report
          </button>
        </div>
      </div>
    </div>
  );
};

// Query Performance Tab Component
const QueryPerformanceTab: React.FC<{
  queryPerfSummary: QueryPerformanceSummary | null;
  slowQueries: SlowQuery[];
  getGradeColor: (grade: string) => string;
  getGradeBgColor: (grade: string) => string;
}> = ({ queryPerfSummary, slowQueries, getGradeColor, getGradeBgColor }) => {
  if (!queryPerfSummary) {
    return (
      <div className="space-y-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-yellow-900 mb-2">⚡ Query Performance Optimization Agent</h3>
          <p className="text-sm text-yellow-700">Query performance analysis helps identify and optimize slow database queries.</p>
        </div>
        <div className="text-center py-12 text-gray-500">
          No query performance data available. Run a performance analysis to see results.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Performance Score Card */}
      <div className={`bg-white rounded-lg shadow-xl p-8 border-4 ${getGradeBgColor(queryPerfSummary.overall_performance_grade)}`}>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Query Performance Grade</h2>
          <div>
            <p className={`text-8xl font-bold ${getGradeColor(queryPerfSummary.overall_performance_grade)}`}>
              {queryPerfSummary.overall_performance_grade}
            </p>
            <p className="text-gray-600 mt-2 text-xl">
              Avg: {queryPerfSummary.avg_query_time_ms.toFixed(1)}ms per query
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
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
          <p className="text-gray-600 text-sm font-medium">Critical Queries</p>
          <p className="text-4xl font-bold text-red-600 mt-2">{queryPerfSummary.critical_queries}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Optimization Potential</p>
          <p className="text-4xl font-bold text-blue-600 mt-2">
            {queryPerfSummary.optimization_potential_ms.toFixed(0)}ms
          </p>
        </div>
      </div>

      {/* Performance Insights */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">📊 Performance Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-blue-700">
              <span className="font-medium">Estimated Improvement:</span>{' '}
              {queryPerfSummary.estimated_improvement_percentage.toFixed(1)}% faster with optimization
            </p>
          </div>
          <div>
            <p className="text-sm text-blue-700">
              <span className="font-medium">Critical Queries:</span>{' '}
              {queryPerfSummary.critical_queries} queries require immediate attention
            </p>
          </div>
        </div>
      </div>

      {/* Slow Queries List */}
      {slowQueries.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Slow Queries Detected</h3>
          </div>
          <div className="divide-y">
            {slowQueries.map((query) => (
              <div key={query.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        query.performance_tier === 'critical' ? 'bg-red-100 text-red-800' :
                        query.performance_tier === 'slow' ? 'bg-orange-100 text-orange-800' :
                        query.performance_tier === 'moderate' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {query.performance_tier}
                      </span>
                      <span className="text-sm text-gray-600">
                        {query.avg_time_ms.toFixed(1)}ms average
                      </span>
                    </div>
                    <code className="block bg-gray-100 rounded p-3 text-sm font-mono overflow-x-auto">
                      {query.query_text}
                    </code>
                    {query.query_signature && (
                      <p className="text-xs text-gray-500 mt-2">
                        Signature: {query.query_signature}
                      </p>
                    )}
                  </div>
                </div>

                {query.bottleneck_type && (
                  <div className="mt-3">
                    <span className="text-sm font-medium text-gray-900">Bottleneck Type: </span>
                    <span className="text-sm text-orange-600">{query.bottleneck_type}</span>
                  </div>
                )}

                {query.ai_suggestion && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-900 mb-2">🤖 AI Suggestion</p>
                    <p className="text-sm text-gray-700">{query.ai_suggestion}</p>
                  </div>
                )}

                {query.suggested_index && (
                  <div className="mt-4 p-4 bg-green-50 rounded-lg">
                    <p className="text-sm font-medium text-green-900 mb-2">💡 Suggested Index</p>
                    <code className="block text-sm font-mono">{query.suggested_index}</code>
                  </div>
                )}

                {query.estimated_improvement && (
                  <div className="mt-3 p-3 bg-purple-50 rounded-lg">
                    <p className="text-sm text-purple-900">
                      <span className="font-medium">Estimated Improvement:</span>{' '}
                      {query.estimated_improvement.toFixed(1)}% faster
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2">
            <span>⚡</span>
            Analyze Query Performance
          </button>
          <button className="bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 flex items-center justify-center gap-2">
            <span>🔧</span>
            Apply Auto-optimizations
          </button>
          <button className="bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700 flex items-center justify-center gap-2">
            <span>📊</span>
            Generate Performance Report
          </button>
        </div>
      </div>
    </div>
  );
};

// Build Analysis Tab Component
const BuildAnalysisTab: React.FC<{
  buildSummary: BuildFailureSummary | null;
  buildFailures: BuildFailure[];
  getGradeColor: (grade: string) => string;
  getGradeBgColor: (grade: string) => string;
  getRiskColor: (risk: string) => string;
}> = ({ buildSummary, buildFailures, getGradeColor, getGradeBgColor, getRiskColor }) => {
  if (!buildSummary) {
    return (
      <div className="space-y-6">
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-orange-900 mb-2">🔨 Build Failure Analysis Agent</h3>
          <p className="text-sm text-orange-700">Build failure analysis helps identify root causes and patterns in CI/CD failures.</p>
        </div>
        <div className="text-center py-12 text-gray-500">No build data available. Trigger a build to see analysis.</div>
      </div>
    );
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
            Avg Resolution: {buildSummary.average_resolution_time_minutes.toFixed(1)} min
          </p>
        </div>
      </div>

      {/* Key Metrics */}
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
          <p className="text-4xl font-bold text-purple-600 mt-2">{buildSummary.flaky_test_count}</p>
        </div>
      </div>

      {/* Build Failures List */}
      {buildFailures.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Recent Build Failures</h3>
          </div>
          <div className="divide-y">
            {buildFailures.map((failure) => (
              <div key={failure.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(failure.priority)}`}>
                        {failure.priority}
                      </span>
                      <span className="text-sm text-gray-600">{failure.failure_type}</span>
                      <span className="text-sm text-gray-500">{failure.branch_name}</span>
                    </div>
                    <p className="font-medium text-gray-900">{failure.project_name} - {failure.build_id}</p>
                    <p className="text-sm text-gray-600 mt-1">by {failure.developer_name}</p>
                    <code className="block bg-gray-100 rounded p-3 text-sm font-mono mt-2 overflow-x-auto">
                      {failure.error_message}
                    </code>
                  </div>
                </div>

                {failure.root_cause_category && (
                  <div className="mt-3">
                    <span className="text-sm font-medium text-gray-900">Root Cause: </span>
                    <span className="text-sm text-orange-600">{failure.root_cause_category}</span>
                  </div>
                )}

                {failure.ai_suggested_fix && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-900 mb-2">🤖 AI Suggested Fix</p>
                    <p className="text-sm text-gray-700">{failure.ai_suggested_fix}</p>
                  </div>
                )}

                {failure.failed_tests && failure.failed_tests.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm font-medium text-gray-900 mb-2">Failed Tests:</p>
                    <div className="flex flex-wrap gap-2">
                      {failure.failed_tests.map((test, idx) => (
                        <span key={idx} className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded">
                          {test}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2">
            <span>🔍</span>
            Analyze Build Failures
          </button>
          <button className="bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 flex items-center justify-center gap-2">
            <span>🔧</span>
            Identify Patterns
          </button>
          <button className="bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700 flex items-center justify-center gap-2">
            <span>📊</span>
            Generate Report
          </button>
        </div>
      </div>
    </div>
  );
};

// Caching Config Tab Component
const CachingConfigTab: React.FC<{
  cacheSummary: CacheSummary | null;
  cacheEntries: CacheEntry[];
  getGradeColor: (grade: string) => string;
  getGradeBgColor: (grade: string) => string;
}> = ({ cacheSummary, cacheEntries, getGradeColor, getGradeBgColor }) => {
  if (!cacheSummary) {
    return (
      <div className="space-y-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">💾 Caching Configuration Agent</h3>
          <p className="text-sm text-blue-700">Caching configuration analysis helps optimize cache hit rates and memory usage.</p>
        </div>
        <div className="text-center py-12 text-gray-500">No cache data available. Configure caching to see analysis.</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Configuration Grade Card */}
      <div className={`bg-white rounded-lg shadow-xl p-8 border-4 ${getGradeBgColor(cacheSummary.configuration_grade)}`}>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Cache Configuration Grade</h2>
          <p className={`text-8xl font-bold ${getGradeColor(cacheSummary.configuration_grade)}`}>
            {cacheSummary.configuration_grade}
          </p>
          <p className="text-gray-600 mt-2 text-xl">
            Hit Rate: {(cacheSummary.overall_hit_rate * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Total Entries</p>
          <p className="text-4xl font-bold text-gray-900 mt-2">{cacheSummary.total_cache_entries}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Memory Usage</p>
          <p className="text-4xl font-bold text-blue-600 mt-2">{cacheSummary.total_memory_usage_mb.toFixed(1)} MB</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Optimization Opportunities</p>
          <p className="text-4xl font-bold text-orange-600 mt-2">{cacheSummary.optimization_opportunities}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Potential Savings</p>
          <p className="text-4xl font-bold text-green-600 mt-2">{cacheSummary.potential_improvement_mb.toFixed(1)} MB</p>
        </div>
      </div>

      {/* Cache Entries List */}
      {cacheEntries.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Low Hit Rate Cache Entries</h3>
          </div>
          <div className="divide-y">
            {cacheEntries.map((entry) => (
              <div key={entry.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                        {entry.cache_type}
                      </span>
                      <span className={`text-sm font-medium ${
                        entry.hit_rate < 0.3 ? 'text-red-600' :
                        entry.hit_rate < 0.5 ? 'text-orange-600' :
                        'text-green-600'
                      }`}>
                        Hit Rate: {(entry.hit_rate * 100).toFixed(1)}%
                      </span>
                    </div>
                    <code className="block bg-gray-100 rounded p-3 text-sm font-mono">
                      {entry.cache_key}
                    </code>
                    <p className="text-sm text-gray-600 mt-2">{entry.endpoint_path}</p>
                  </div>
                </div>

                <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Hits</p>
                    <p className="font-bold text-green-600">{entry.hit_count}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Misses</p>
                    <p className="font-bold text-red-600">{entry.miss_count}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Size</p>
                    <p className="font-bold text-gray-900">{(entry.data_size_bytes / 1024).toFixed(1)} KB</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2">
            <span>⚡</span>
            Analyze Cache Performance
          </button>
          <button className="bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 flex items-center justify-center gap-2">
            <span>🔧</span>
            Apply Optimizations
          </button>
          <button className="bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700 flex items-center justify-center gap-2">
            <span>🗑️</span>
            Clear Low-Performing Entries
          </button>
        </div>
      </div>
    </div>
  );
};

// Breaking Changes Tab Component
const BreakingChangesTab: React.FC<{
  breakingChangesSummary: BreakingChangesSummary | null;
  breakingChanges: BreakingChange[];
  getGradeColor: (grade: string) => string;
  getGradeBgColor: (grade: string) => string;
  getRiskColor: (risk: string) => string;
}> = ({ breakingChangesSummary, breakingChanges, getGradeColor, getGradeBgColor, getRiskColor }) => {
  if (!breakingChangesSummary) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-900 mb-2">🚨 Breaking Changes Detection Agent</h3>
          <p className="text-sm text-red-700">Breaking changes detection helps identify incompatible changes before they reach production.</p>
        </div>
        <div className="text-center py-12 text-gray-500">No breaking changes data available. Run a pre-merge scan to see results.</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Risk Grade Card */}
      <div className={`bg-white rounded-lg shadow-xl p-8 border-4 ${getGradeBgColor(breakingChangesSummary.risk_grade)}`}>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Breaking Changes Risk Grade</h2>
          <p className={`text-8xl font-bold ${getGradeColor(breakingChangesSummary.risk_grade)}`}>
            {breakingChangesSummary.risk_grade}
          </p>
          <p className="text-gray-600 mt-2 text-xl">
            Risk Score: {breakingChangesSummary.overall_risk_score.toFixed(1)}/100
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Total Changes</p>
          <p className="text-4xl font-bold text-gray-900 mt-2">{breakingChangesSummary.total_changes}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Unresolved</p>
          <p className="text-4xl font-bold text-orange-600 mt-2">{breakingChangesSummary.unresolved_changes}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Critical</p>
          <p className="text-4xl font-bold text-red-600 mt-2">{breakingChangesSummary.critical_changes}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-medium">Breaking (Non-Compat)</p>
          <p className="text-4xl font-bold text-purple-600 mt-2">{breakingChangesSummary.breaking_changes_count}</p>
        </div>
      </div>

      {/* Breaking Changes List */}
      {breakingChanges.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Detected Breaking Changes</h3>
          </div>
          <div className="divide-y">
            {breakingChanges.map((change) => (
              <div key={change.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(change.severity)}`}>
                        {change.severity}
                      </span>
                      <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                        {change.change_type}
                      </span>
                      {!change.backwards_compatible && (
                        <span className="px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                          Breaking
                        </span>
                      )}
                    </div>
                    <p className="font-medium text-gray-900">{change.affected_component}</p>
                    <p className="text-sm text-gray-700 mt-2">{change.description}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      📁 {change.file_path}:{change.line_number} • 🌿 {change.source_branch}
                    </p>
                  </div>
                </div>

                {change.affected_endpoints && change.affected_endpoints.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm font-medium text-gray-900 mb-2">Affected Endpoints:</p>
                    <div className="flex flex-wrap gap-2">
                      {change.affected_endpoints.map((endpoint, idx) => (
                        <span key={idx} className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">
                          {endpoint}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {change.ai_risk_assessment && (
                  <div className="mt-4 p-4 bg-red-50 rounded-lg">
                    <p className="text-sm font-medium text-red-900 mb-2">🤖 AI Risk Assessment</p>
                    <p className="text-sm text-gray-700">{change.ai_risk_assessment}</p>
                  </div>
                )}

                {change.ai_mitigation_suggestion && (
                  <div className="mt-4 p-4 bg-green-50 rounded-lg">
                    <p className="text-sm font-medium text-green-900 mb-2">💡 Mitigation Suggestion</p>
                    <p className="text-sm text-gray-700">{change.ai_mitigation_suggestion}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2">
            <span>🔍</span>
            Scan for Breaking Changes
          </button>
          <button className="bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 flex items-center justify-center gap-2">
            <span>📋</span>
            Generate Migration Guides
          </button>
          <button className="bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700 flex items-center justify-center gap-2">
            <span>✅</span>
            Approve Safe Changes
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductOperationsDashboard;
