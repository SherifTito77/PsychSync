/**
 * Admin Dashboard - Type Definitions
 */

export interface SystemMetrics {
  totalUsers: number;
  activeUsers: number;
  totalDocuments: number;
  complianceScore: number;
  systemHealth: 'healthy' | 'warning' | 'critical';
  uptime: number;
  storageUsed: number;
  storageTotal: number;
  apiCalls: number;
  errorRate: number;
  responseTime: number;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'manager' | 'employee' | 'auditor';
  department: string;
  status: 'active' | 'inactive' | 'suspended';
  lastLogin: string;
  complianceScore: number;
  trainingProgress: number;
  pendingTasks: number;
  joinedAt: string;
}

export interface Alert {
  id: string;
  type: 'security' | 'performance' | 'compliance' | 'system' | 'user';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  timestamp: string;
  status: 'open' | 'acknowledged' | 'resolved';
  assignedTo?: string;
  category: string;
  source: string;
  actions: string[];
}

export interface Activity {
  id: string;
  type: 'user' | 'system' | 'compliance' | 'security' | 'admin';
  user: string;
  action: string;
  details: string;
  timestamp: string;
  ip: string;
  status: 'success' | 'failure' | 'warning';
  metadata: Record<string, any>;
}

export type TabType = 'overview' | 'users' | 'system' | 'alerts' | 'activity';

export type BadgeColor = 'blue' | 'gray' | 'indigo' | 'green' | 'orange' | 'purple' | 'red' | 'yellow';
