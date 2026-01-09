/**
 * Audit Trail - Type Definitions
 */

export interface AuditEvent {
  id: string;
  timestamp: string;
  eventType: 'login' | 'logout' | 'document_access' | 'data_export' | 'settings_change' | 'user_action' | 'system_event' | 'security_alert' | 'compliance_check';
  category: 'authentication' | 'data_access' | 'system_config' | 'user_management' | 'security' | 'compliance';
  severity: 'low' | 'medium' | 'high' | 'critical';
  userId: string;
  userName: string;
  userEmail: string;
  userRole: string;
  action: string;
  description: string;
  ipAddress: string;
  userAgent: string;
  sessionId: string;
  resource: string;
  resourceId: string;
  oldValue?: any;
  newValue?: any;
  status: 'success' | 'failure' | 'warning';
  source: 'web' | 'mobile' | 'api' | 'system' | 'integration';
  location?: {
    country: string;
    city: string;
    coordinates?: [number, number];
  };
  metadata: Record<string, any>;
  relatedEvents: string[];
  investigationStatus?: 'none' | 'pending' | 'investigating' | 'resolved';
  investigationNotes?: string;
  assignedTo?: string;
  tags: string[];
}

export interface Investigation {
  id: string;
  title: string;
  description: string;
  status: 'open' | 'in_progress' | 'closed' | 'escalated';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assignedTo: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  dueDate?: string;
  tags: string[];
  events: string[];
}

export interface AuditFilters {
  searchTerm: string;
  eventType: string;
  category: string;
  severity: string;
  status: string;
  dateRange: {
    start: string;
    end: string;
  };
  userId: string;
}

export type SortField = 'timestamp' | 'severity' | 'category' | 'eventType';
export type SortOrder = 'asc' | 'desc';
