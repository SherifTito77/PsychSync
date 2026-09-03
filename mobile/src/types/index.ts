/**
 * Type definitions for PsychSync Mobile App
 */

export interface MonitoringStats {
  total_emails: number;
  emails_last_hour: number;
  emails_last_24h: number;
  emails_last_week: number;
  categories: Record<string, number>;
  behavioral_insights: BehavioralInsights;
  alerts: Alert[];
  generated_at: string;
}

export interface BehavioralInsights {
  security_consciousness: 'high' | 'medium' | 'low';
  financial_activity: 'high' | 'medium' | 'low';
  professional_engagement: 'high' | 'medium' | 'low';
  social_activity: 'high' | 'medium' | 'low';
  work_pattern: string;
  recommendations: string[];
}

export interface Alert {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: string;
  read: boolean;
}

export interface EmailConnection {
  id: number;
  email_address: string;
  provider: string;
  connection_status: string;
  created_at: string;
  last_sync?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  timestamp?: string;
}

export interface CategoryData {
  category: string;
  count: number;
  percentage: number;
  color: string;
}
