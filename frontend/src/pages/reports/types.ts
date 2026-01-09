/**
 * Reporting Module Types
 *
 * Type definitions for reports, templates, schedules, and analytics
 */

export interface Report {
  id: string;
  title: string;
  description: string;
  report_type: string;
  status: string;
  file_format: string;
  file_name?: string;
  file_size?: number;
  record_count?: number;
  download_count: number;
  created_at: string;
  generation_started?: string;
  generation_completed?: string;
  expires_at?: string;
  is_public: boolean;
  template_id?: string;
}

export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  report_type: string;
  category?: string;
  tags: string[];
  is_public: boolean;
  usage_count: number;
  created_at: string;
}

export interface ReportSchedule {
  id: string;
  name: string;
  description: string;
  frequency: string;
  next_run?: string;
  last_run?: string;
  template_id: string;
  delivery_method: string;
  default_format: string;
  is_active: boolean;
  success_count: number;
  failure_count: number;
}

export interface ReportAnalytics {
  period: {
    start_date: string;
    end_date: string;
  };
  generation_stats: {
    total_reports: number;
    completed_reports: number;
    failed_reports: number;
    success_rate: number;
  };
  format_distribution: Record<string, number>;
  type_distribution: Record<string, number>;
  performance: {
    avg_generation_time_seconds: number;
  };
  popular_templates: Array<{
    name: string;
    usage_count: number;
  }>;
}

export interface ReportFormState {
  title: string;
  description: string;
  report_type: string;
  template_id: string;
  export_format: string;
  data_range_start: string;
  data_range_end: string;
  team_id: string;
  is_public: boolean;
  retention_days: number;
}

export interface TemplateFormState {
  name: string;
  description: string;
  report_type: string;
  category: string;
  tags: string;
  is_public: boolean;
}

export interface ScheduleFormState {
  name: string;
  description: string;
  template_id: string;
  frequency: string;
  delivery_method: string;
  delivery_config: string;
  end_date: string;
  default_format: string;
}
