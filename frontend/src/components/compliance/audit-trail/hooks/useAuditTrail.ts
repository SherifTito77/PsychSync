/**
 * Audit Trail - Main Data Management Hook
 */

import { useState, useEffect, useMemo } from 'react';
import { AuditEvent, AuditFilters, SortField, SortOrder } from '../types';

/**
 * Mock audit events generator
 */
const mockAuditEvents = (): AuditEvent[] => [
  {
    id: '1',
    timestamp: new Date().toISOString(),
    eventType: 'login',
    category: 'authentication',
    severity: 'low',
    userId: 'user-1',
    userName: 'John Smith',
    userEmail: 'john.smith@company.com',
    userRole: 'admin',
    action: 'User Login',
    description: 'User successfully logged in from IP 192.168.1.100',
    ipAddress: '192.168.1.100',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    sessionId: 'session-123',
    resource: 'system',
    resourceId: 'system-1',
    status: 'success',
    source: 'web',
    location: {
      country: 'United States',
      city: 'New York',
    },
    metadata: { loginMethod: 'password' },
    relatedEvents: [],
    tags: ['authentication', 'success']
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    eventType: 'security_alert',
    category: 'security',
    severity: 'high',
    userId: 'system',
    userName: 'System',
    userEmail: 'system@company.com',
    userRole: 'system',
    action: 'Multiple Failed Logins',
    description: '5 failed login attempts detected for user jane.doe@company.com',
    ipAddress: '203.0.113.42',
    userAgent: 'Mozilla/5.0 (Unknown)',
    sessionId: 'session-unknown',
    resource: 'auth',
    resourceId: 'auth-1',
    status: 'warning',
    source: 'api',
    metadata: { attempts: 5, timeWindow: '5 minutes' },
    relatedEvents: ['event-456', 'event-457'],
    investigationStatus: 'pending',
    tags: ['security', 'brute-force']
  }
];

/**
 * Main hook for audit trail management
 */
export const useAuditTrail = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<AuditFilters>({
    searchTerm: '',
    eventType: 'all',
    category: 'all',
    severity: 'all',
    status: 'all',
    dateRange: { start: '', end: '' },
    userId: ''
  });
  const [sortField, setSortField] = useState<SortField>('timestamp');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);

  /**
   * Load audit events
   */
  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await mockAuditEvents();
      setEvents(data);
    } catch (error) {
      console.error('Failed to load audit events:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Filter events based on current filters
   */
  const filteredEvents = useMemo(() => {
    return events.filter(event => {
      // Search term filter
      if (filters.searchTerm) {
        const searchLower = filters.searchTerm.toLowerCase();
        const matchesSearch =
          event.action.toLowerCase().includes(searchLower) ||
          event.description.toLowerCase().includes(searchLower) ||
          event.userName.toLowerCase().includes(searchLower) ||
          event.userEmail.toLowerCase().includes(searchLower);

        if (!matchesSearch) return false;
      }

      // Event type filter
      if (filters.eventType !== 'all' && event.eventType !== filters.eventType) {
        return false;
      }

      // Category filter
      if (filters.category !== 'all' && event.category !== filters.category) {
        return false;
      }

      // Severity filter
      if (filters.severity !== 'all' && event.severity !== filters.severity) {
        return false;
      }

      // Status filter
      if (filters.status !== 'all' && event.status !== filters.status) {
        return false;
      }

      // Date range filter
      if (filters.dateRange.start || filters.dateRange.end) {
        const eventDate = new Date(event.timestamp);
        if (filters.dateRange.start && eventDate < new Date(filters.dateRange.start)) {
          return false;
        }
        if (filters.dateRange.end && eventDate > new Date(filters.dateRange.end)) {
          return false;
        }
      }

      // User filter
      if (filters.userId && event.userId !== filters.userId) {
        return false;
      }

      return true;
    });
  }, [events, filters]);

  /**
   * Sort events based on current sort field and order
   */
  const sortedEvents = useMemo(() => {
    return [...filteredEvents].sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'timestamp':
          comparison = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
          break;
        case 'severity':
          const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
          comparison = severityOrder[a.severity] - severityOrder[b.severity];
          break;
        case 'category':
          comparison = a.category.localeCompare(b.category);
          break;
        case 'eventType':
          comparison = a.eventType.localeCompare(b.eventType);
          break;
        default:
          comparison = 0;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [filteredEvents, sortField, sortOrder]);

  /**
   * Export events to CSV
   */
  const exportToCSV = () => {
    const headers = [
      'Timestamp',
      'Event Type',
      'Category',
      'Severity',
      'User',
      'Action',
      'Description',
      'Status',
      'Source'
    ];

    const rows = sortedEvents.map(event => [
      event.timestamp,
      event.eventType,
      event.category,
      event.severity,
      event.userName,
      event.action,
      event.description,
      event.status,
      event.source
    ]);

    const csv = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `audit-trail-${new Date().toISOString()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  /**
   * Update filter
   */
  const updateFilter = <K extends keyof AuditFilters>(key: K, value: AuditFilters[K]) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  /**
   * Clear all filters
   */
  const clearFilters = () => {
    setFilters({
      searchTerm: '',
      eventType: 'all',
      category: 'all',
      severity: 'all',
      status: 'all',
      dateRange: { start: '', end: '' },
      userId: ''
    });
  };

  /**
   * Handle sort
   */
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  // Load events on mount
  useEffect(() => {
    loadEvents();
  }, []);

  return {
    // State
    events,
    loading,
    filters,
    sortField,
    sortOrder,
    selectedEvent,

    // Computed
    filteredEvents: sortedEvents,
    eventCount: sortedEvents.length,

    // Actions
    setSelectedEvent,
    updateFilter,
    clearFilters,
    handleSort,
    exportToCSV,
    loadEvents,
  };
};
