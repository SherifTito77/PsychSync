/**
 * Admin Dashboard - Main Data Management Hook
 */

import { useState, useEffect } from 'react';
import { SystemMetrics, User, Alert, Activity, TabType } from '../types';

/**
 * Mock data generators (simplified for demo)
 */
const mockSystemMetrics = (): SystemMetrics => ({
  totalUsers: 2547,
  activeUsers: 1834,
  totalDocuments: 12847,
  complianceScore: 94,
  systemHealth: 'healthy',
  uptime: 99.9,
  storageUsed: 45.6,
  storageTotal: 100,
  apiCalls: 847392,
  errorRate: 0.02,
  responseTime: 124
});

const mockUsers = (): User[] => [
  {
    id: '1',
    name: 'John Smith',
    email: 'john.smith@company.com',
    role: 'admin',
    department: 'IT',
    status: 'active',
    lastLogin: new Date().toISOString(),
    complianceScore: 98,
    trainingProgress: 100,
    pendingTasks: 3,
    joinedAt: '2024-01-15T10:00:00Z'
  }
];

const mockAlerts = (): Alert[] => [
  {
    id: '1',
    type: 'security',
    severity: 'high',
    title: 'Unusual login activity detected',
    description: 'Multiple failed login attempts from unknown IP',
    timestamp: new Date().toISOString(),
    status: 'open',
    category: 'Security',
    source: 'Auth System',
    actions: ['Review logs', 'Block IP', 'Notify user']
  }
];

const mockActivities = (): Activity[] => [
  {
    id: '1',
    type: 'admin',
    user: 'John Smith',
    action: 'User Created',
    details: 'Created new user account for Jane Doe',
    timestamp: new Date().toISOString(),
    ip: '192.168.1.100',
    status: 'success',
    metadata: { userId: '123', targetUser: 'Jane Doe' }
  }
];

/**
 * Main hook for admin dashboard data management
 */
export const useAdminDashboard = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRole, setSelectedRole] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [autoRefresh, setAutoRefresh] = useState(false);

  /**
   * Load all dashboard data
   */
  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [metricsData, usersData, alertsData, activitiesData] = await Promise.all([
        mockSystemMetrics(),
        mockUsers(),
        mockAlerts(),
        mockActivities()
      ]);
      setMetrics(metricsData);
      setUsers(usersData);
      setAlerts(alertsData);
      setActivities(activitiesData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle alert resolution
   */
  const handleResolveAlert = (alertId: string) => {
    setAlerts(prev => prev.map(alert =>
      alert.id === alertId
        ? { ...alert, status: 'resolved' as const }
        : alert
    ));
  };

  /**
   * Handle user actions (activate/deactivate/suspend)
   */
  const handleUserAction = (userId: string, action: 'activate' | 'deactivate' | 'suspend') => {
    const statusMap = {
      activate: 'active' as const,
      deactivate: 'inactive' as const,
      suspend: 'suspended' as const
    };
    setUsers(prev => prev.map(user =>
      user.id === userId
        ? { ...user, status: statusMap[action] }
        : user
    ));
  };

  /**
   * Filter users based on search and filters
   */
  const getFilteredUsers = () => {
    return users.filter(user => {
      const matchesSearch = searchTerm === '' ||
        user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesRole = selectedRole === 'all' || user.role === selectedRole;
      const matchesStatus = selectedStatus === 'all' || user.status === selectedStatus;

      return matchesSearch && matchesRole && matchesStatus;
    });
  };

  /**
   * Filter alerts based on active tab
   */
  const getFilteredAlerts = () => {
    return alerts.filter(alert => alert.status !== 'resolved');
  };

  /**
   * Get recent activities
   */
  const getRecentActivities = (count: number = 10) => {
    return activities.slice(0, count);
  };

  // Auto-refresh effect
  useEffect(() => {
    loadDashboardData();
    if (autoRefresh) {
      const interval = setInterval(loadDashboardData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, activeTab]);

  return {
    // State
    metrics,
    users,
    alerts,
    activities,
    loading,
    activeTab,
    searchTerm,
    selectedRole,
    selectedStatus,
    autoRefresh,

    // Actions
    setActiveTab,
    setSearchTerm,
    setSelectedRole,
    setSelectedStatus,
    setAutoRefresh,
    loadDashboardData,
    handleResolveAlert,
    handleUserAction,

    // Computed
    filteredUsers: getFilteredUsers(),
    filteredAlerts: getFilteredAlerts(),
    recentActivities: getRecentActivities(),
  };
};
