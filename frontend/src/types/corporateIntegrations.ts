// frontend/src/types/corporateIntegrations.ts
/**
 * TypeScript types for Corporate Data Source Integration
 * Matches backend schemas in app/schemas/corporate_data_sources.py
 */

export enum PrivacyLevel {
  METADATA_ONLY = 'metadata_only',
  ANONYMIZED = 'anonymized',
  FULL = 'full'
}

export enum SyncStatus {
  ACTIVE = 'active',
  PAUSED = 'paused',
  ERROR = 'error',
  PENDING = 'pending',
  DISABLED = 'disabled'
}

export enum DataSourceType {
  // Communication Platforms
  EMAIL_METADATA = 'email_metadata',
  SLACK_MESSAGES = 'slack_messages',
  TEAMS_MESSAGES = 'teams_messages',
  ZOOM_TRANSCRIPTS = 'zoom_transcripts',

  // Productivity & Collaboration
  CALENDAR_EVENTS = 'calendar_events',
  JIRA_ACTIVITY = 'jira_activity',
  GITHUB_COMMITS = 'github_commits',
  CONFLUENCE_EDITS = 'confluence_edits',
  ASANA_TASKS = 'asana_tasks',
  MONDAY_PROJECTS = 'monday_projects',

  // HR Systems
  WORKDAY_DATA = 'workday_data',
  BAMBOO_HR = 'bamboo_hr',
  ADP_ATTENDANCE = 'adp_attendance',
  TIME_TRACKING = 'time_tracking',
  PTO_REQUESTS = 'pto_requests',
  PERFORMANCE_REVIEWS = 'performance_reviews',

  // Surveys & Feedback
  PULSE_SURVEYS = 'pulse_surveys',
  ENGAGEMENT_SURVEYS = 'engagement_surveys',
  EXIT_INTERVIEWS = 'exit_interviews',
  ONE_ON_ONE_NOTES = 'one_on_one_notes',

  // Wellness & Biometrics
  WEARABLE_DATA = 'wearable_data',
  WELLNESS_APP_DATA = 'wellness_app_data',
  MENTAL_HEALTH_CHECKS = 'mental_health_checks',

  // Systems & Access
  VPN_LOGS = 'vpn_logs',
  BADGE_SWIPES = 'badge_swipes',
  SYSTEM_LOGIN_TIMES = 'system_login_times',
  APPLICATION_USAGE = 'application_usage',

  // Financial & Compensation
  BONUS_DATA = 'bonus_data',
  PROMOTION_DATA = 'promotion_data',
  COMPENSATION_CHANGES = 'compensation_changes',

  // Learning & Development
  TRAINING_COMPLETIONS = 'training_completions',
  CERTIFICATION_DATA = 'certification_data',
  SKILL_ASSESSMENTS = 'skill_assessments'
}

export interface BehavioralSignal {
  signal_name: string;
  value: number; // 0-1 normalized
  confidence: number; // 0-1
  timestamp: string;
  metadata: Record<string, any>;
}

export interface IntegrationConfig {
  source_type: DataSourceType;
  enabled: boolean;
  privacy_level: PrivacyLevel;
  sync_frequency_hours: number; // 1-168
  data_retention_days: number; // 30-1095
  requires_consent: boolean;
  api_credentials?: Record<string, string>;
  custom_settings: Record<string, any>;
}

export interface IntegrationStatus {
  source_type: DataSourceType;
  status: SyncStatus;
  last_sync?: string;
  next_sync?: string;
  records_processed: number;
  error_message?: string;
  health_score: number; // 0-1
}

export interface IntegrationResponse {
  config: IntegrationConfig;
  status: IntegrationStatus;
  behavioral_signals: string[];
  data_points_count: number;
}

export interface CreateIntegrationRequest {
  source_type: DataSourceType;
  privacy_level: PrivacyLevel;
  sync_frequency_hours?: number;
  data_retention_days?: number;
  api_credentials?: Record<string, string>;
  custom_settings?: Record<string, any>;
}

export interface UpdateIntegrationRequest {
  enabled?: boolean;
  privacy_level?: PrivacyLevel;
  sync_frequency_hours?: number;
  data_retention_days?: number;
  api_credentials?: Record<string, string>;
  custom_settings?: Record<string, any>;
}

export interface SyncIntegrationRequest {
  force_full_sync?: boolean;
  date_range?: {
    start: string;
    end: string;
  };
}

export interface BehavioralAnalysisRequest {
  source_types: DataSourceType[];
  date_range: {
    start: string;
    end: string;
  };
  employee_ids?: number[];
  analysis_type?: 'toxicity' | 'burnout' | 'team_health' | 'comprehensive';
}

export interface BehavioralInsight {
  category: 'burnout' | 'toxicity' | 'engagement' | 'retention' | 'leadership';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  affected_employees: number[];
  confidence: number;
  recommendations: string[];
  data_sources: DataSourceType[];
  detected_at: string;
}

export interface OrganizationIntegrations {
  organization_id: number;
  integrations: IntegrationResponse[];
  summary: {
    total_integrations: number;
    active_integrations: number;
    total_data_points: number;
    coverage_percentage: number;
  };
  recommendations: string[];
}

export interface IntegrationHealthMetrics {
  total_integrations: number;
  active_integrations: number;
  error_integrations: number;
  total_data_points: number;
  last_24h_ingestion_count: number;
  avg_sync_latency_minutes: number;
  data_quality_score: number; // 0-1
}

export interface ConsentRecord {
  employee_id: number;
  source_types: DataSourceType[];
  granted: boolean;
  granted_at: string;
  revoked_at?: string;
  consent_version: string;
}

export interface BulkIntegrationRequest {
  organization_size: number;
  privacy_preference: 'minimal' | 'balanced' | 'comprehensive';
  auto_enable_recommended: boolean;
}

export interface IntegrationInsightsReport {
  report_id: string;
  generated_at: string;
  date_range: {
    start: string;
    end: string;
  };
  organization_id: number;
  insights: BehavioralInsight[];
  health_metrics: IntegrationHealthMetrics;
  summary: {
    total_insights: number;
    critical_insights: number;
    high_insights: number;
    medium_insights: number;
    low_insights: number;
  };
  recommendations: string[];
}

// UI-specific types

export interface DataSourceMetadata {
  type: DataSourceType;
  name: string;
  description: string;
  category: string;
  icon: string;
  requiresAuth: boolean;
  authType: 'oauth2' | 'api_token' | 'custom';
  behavioral_signals: string[];
  priority: 'must_have' | 'high' | 'medium' | 'nice_to_have';
}

export interface IntegrationCardProps {
  integration: IntegrationResponse;
  onToggle: (sourceType: DataSourceType) => void;
  onSync: (sourceType: DataSourceType) => void;
  onConfigure: (sourceType: DataSourceType) => void;
  onViewDetails: (sourceType: DataSourceType) => void;
}

export interface InsightsDashboardProps {
  insights: BehavioralInsight[];
  dateRange: {
    start: string;
    end: string;
  };
  onInsightClick: (insightId: string) => void;
  onFilterChange: (filters: InsightsFilter) => void;
}

export interface InsightsFilter {
  categories?: string[];
  severities?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
}

// API response wrappers

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}
