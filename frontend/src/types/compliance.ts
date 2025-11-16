export interface ComplianceScore {
  overall: number;
  categories: {
    labor_law: number;
    data_privacy: number;
    workplace_safety: number;
    training: number;
    documentation: number;
  };
  status: 'excellent' | 'good' | 'needs_improvement' | 'critical';
  last_updated: string;
}
export interface TrainingAssignment {
  id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  training_type: string;
  training_name: string;
  due_date: string;
  status: 'assigned' | 'in_progress' | 'completed' | 'overdue';
  assigned_at: string;
  completed_at?: string;
  completion_score?: number;
  certificate_id?: string;
}
export interface AnonymousFeedback {
  id: string;
  feedback_type: string;
  category: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: string;
  submitted_at: string;
  evidence_count: number;
  has_follow_ups: boolean;
}
export interface EmployeeRights {
  federal_rights: Record<string, any>;
  state_rights: Record<string, any>;
  industry_rights: Record<string, any>;
  how_to_report: Record<string, any>;
  faq: Array<{ question: string; answer: string }>;
}
export interface ComplianceCheck {
  organization_id: string;
  check_date: string;
  check_type: string;
  compliance_score: number;
  status: string;
  categories: Record<string, any>;
  priority_actions: Array<{
    priority: string;
    category: string;
    action: string;
    deadline: string;
  }>;
}