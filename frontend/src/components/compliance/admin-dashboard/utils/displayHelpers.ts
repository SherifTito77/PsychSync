/**
 * Admin Dashboard - Display Helper Utilities
 */

import { BadgeColor, Alert, User } from '../types';
import {
  Shield,
  Users,
  FileText,
  TrendingUp,
  Activity,
  Award,
  Target,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react';

/**
 * Get color classes for severity badges
 */
export const getSeverityColor = (severity: Alert['severity']): BadgeColor => {
  switch (severity) {
    case 'critical': return 'red';
    case 'high': return 'orange';
    case 'medium': return 'yellow';
    case 'low': return 'green';
    default: return 'gray';
  }
};

/**
 * Get color classes for status badges
 */
export const getStatusColor = (status: string): BadgeColor => {
  switch (status) {
    case 'active': return 'green';
    case 'inactive': return 'gray';
    case 'suspended': return 'red';
    case 'resolved': return 'green';
    case 'open': return 'red';
    case 'acknowledged': return 'yellow';
    default: return 'gray';
  }
};

/**
 * Get icon for user role
 */
export const getRoleIcon = (role: User['role']) => {
  switch (role) {
    case 'admin': return Shield;
    case 'manager': return Target;
    case 'auditor': return FileText;
    case 'employee': return Users;
    default: return Users;
  }
};

/**
 * Get icon for alert type
 */
export const getAlertTypeIcon = (type: Alert['type']) => {
  switch (type) {
    case 'security': return Shield;
    case 'performance': return TrendingUp;
    case 'compliance': return FileText;
    case 'system': return Activity;
    case 'user': return Users;
    default: return AlertTriangle;
  }
};

/**
 * Get status icon
 */
export const getStatusIcon = (status: string) => {
  switch (status) {
    case 'active':
    case 'resolved':
    case 'success':
      return CheckCircle;
    case 'inactive':
    case 'open':
    case 'failure':
      return XCircle;
    default:
      return AlertTriangle;
  }
};

/**
 * Format date to readable string
 */
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  });
};

/**
 * Format number with K/M/B suffixes
 */
export const formatNumber = (num: number): string => {
  if (num >= 1000000000) return `${(num / 1000000000).toFixed(1)}B`;
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

/**
 * Get trend color based on direction
 */
export const getTrendColor = (direction: 'up' | 'down' | 'neutral'): string => {
  switch (direction) {
    case 'up': return 'text-green-600';
    case 'down': return 'text-red-600';
    case 'neutral': return 'text-gray-600';
    default: return 'text-gray-600';
  }
};
