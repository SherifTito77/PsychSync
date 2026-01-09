/**
 * Audit Trail - Display Helper Utilities
 */

import { AuditEvent } from '../types';
import {
  Shield,
  FileText,
  Activity,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Globe,
  Smartphone,
  Database,
  Lock,
} from 'lucide-react';

/**
 * Get color for severity level
 */
export const getSeverityColor = (severity: AuditEvent['severity']): string => {
  switch (severity) {
    case 'critical': return 'text-red-600 bg-red-50 border-red-200';
    case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
    case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'low': return 'text-green-600 bg-green-50 border-green-200';
    default: return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

/**
 * Get color for status
 */
export const getStatusColor = (status: AuditEvent['status']): string => {
  switch (status) {
    case 'success': return 'text-green-600';
    case 'failure': return 'text-red-600';
    case 'warning': return 'text-yellow-600';
    default: return 'text-gray-600';
  }
};

/**
 * Get icon for event type
 */
export const getEventTypeIcon = (eventType: AuditEvent['eventType']) => {
  switch (eventType) {
    case 'login':
    case 'logout':
      return Shield;
    case 'document_access':
    case 'data_export':
      return FileText;
    case 'system_event':
      return Activity;
    case 'security_alert':
      return AlertTriangle;
    default:
      return Activity;
  }
};

/**
 * Get icon for source
 */
export const getSourceIcon = (source: AuditEvent['source']) => {
  switch (source) {
    case 'web': return Globe;
    case 'mobile': return Smartphone;
    case 'api': return Database;
    case 'system': return Activity;
    default: return Shield;
  }
};

/**
 * Get status icon
 */
export const getStatusIcon = (status: AuditEvent['status']) => {
  switch (status) {
    case 'success': return CheckCircle;
    case 'failure': return XCircle;
    case 'warning': return AlertTriangle;
    default: return Activity;
  }
};

/**
 * Format timestamp to readable string
 */
export const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

/**
 * Format timestamp to relative time
 */
export const formatRelativeTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return formatTimestamp(timestamp);
};

/**
 * Mask IP address for privacy
 */
export const maskIPAddress = (ip: string): string => {
  const parts = ip.split('.');
  if (parts.length === 4) {
    return `${parts[0]}.${parts[1]}.***.***`;
  }
  return ip;
};

/**
 * Mask email for privacy
 */
export const maskEmail = (email: string): string => {
  const [username, domain] = email.split('@');
  if (username.length <= 2) return `${username[0]}***@${domain}`;
  return `${username.slice(0, 2)}***@${domain}`;
};
