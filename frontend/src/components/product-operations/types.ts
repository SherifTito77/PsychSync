/**
 * Product Operations Dashboard - Type Definitions
 *
 * Extracted types for better organization and reusability
 */

// Code Quality Types
export interface CodeQualitySummary {
  total_files_analyzed: number;
  total_issues: number;
  critical_issues: number;
  high_issues: number;
  medium_issues: number;
  low_issues: number;
  overall_score: number;
  quality_grade: string;
  test_coverage: number;
  code_duplication: number;
  technical_debt_ratio: number;
}

export interface CodeQualityIssue {
  id: string;
  file_path: string;
  line_number: number;
  severity: string;
  category: string;
  description: string;
  suggestion?: string;
}

// Bug Tracking Types
export interface BugSummary {
  id: string;
  date: string;
  summary_date?: string; // Alternative to date
  total_bugs: number;
  new_bugs?: number; // New bugs reported
  critical_bugs: number;
  major_bugs: number;
  minor_bugs: number;
  resolved_bugs: number;
  ai_summary?: string;
  ai_insights?: string[];
  ai_recommendations?: string[];
}

// Pull Request Types
export interface PullRequestQuality {
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

// Performance Report Types
export interface PerformanceReport {
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

// Sprint Metrics Types
export interface SprintMetrics {
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

// SQL Security Types
export interface SQLSecuritySummary {
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

export interface SQLQuery {
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

// Query Performance Types
export interface QueryPerformanceSummary {
  total_queries: number;
  slow_queries: number;
  critical_queries: number;
  avg_query_time_ms: number;
  overall_performance_grade: string;
  optimization_potential_ms: number;
  estimated_improvement_percentage: number;
}

export interface SlowQuery {
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

// Build Failure Types
export interface BuildFailureSummary {
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

export interface BuildFailure {
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

// Caching Types
export interface CacheSummary {
  total_entries: number;
  total_hits: number;
  total_misses: number;
  overall_hit_rate: number;
  low_hit_rate_entries: number;
  avg_entry_size: number;
  memory_usage_mb: number;
}

export interface CacheEntry {
  id: string;
  key: string;
  hit_count: number;
  miss_count: number;
  hit_rate: number;
  size_bytes: number;
  created_at: string;
  last_accessed: string;
  ttl_seconds: number;
}

// Breaking Changes Types
export interface BreakingChangesSummary {
  total_changes: number;
  unapproved_changes: number;
  critical_changes: number;
  by_severity: {
    critical: number;
    major: number;
    minor: number;
  };
  by_category: {
    api: number;
    database: number;
    ui: number;
  };
}

export interface BreakingChange {
  id: string;
  title: string;
  description: string;
  severity: string;
  category: string;
  affected_components: string[];
  migration_guide?: string;
  is_approved: boolean;
  created_at: string;
  scheduled_for: string;
  author_name: string;
}

// Dashboard State Types
export interface DashboardState {
  loading: boolean;
  error: string | null;
  activeTab: TabType;
  qualitySummary: CodeQualitySummary | null;
  bugSummaries: BugSummary[];
  pullRequests: PullRequestQuality[];
  performanceReport: PerformanceReport | null;
  sprints: SprintMetrics[];
  sqlSummary: SQLSecuritySummary | null;
  sqlQueries: SQLQuery[];
  queryPerfSummary: QueryPerformanceSummary | null;
  slowQueries: SlowQuery[];
  buildSummary: BuildFailureSummary | null;
  buildFailures: BuildFailure[];
  cacheSummary: CacheSummary | null;
  cacheEntries: CacheEntry[];
  breakingChangesSummary: BreakingChangesSummary | null;
  breakingChanges: BreakingChange[];
}

export type TabType =
  | 'overview'
  | 'quality'
  | 'bugs'
  | 'prs'
  | 'reports'
  | 'sql_audit'
  | 'query_performance'
  | 'build_analysis'
  | 'caching_config'
  | 'breaking_changes';
