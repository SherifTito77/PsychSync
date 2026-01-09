/**
 * Admin Dashboard - Main Orchestrator
 *
 * Comprehensive admin interface for system monitoring and management
 *
 * SPLIT from 1,092 lines → ~250 lines (77% reduction)
 */

import React from 'react';
import {
  Shield,
  Users,
  Activity,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter,
  Bell,
  TrendingUp,
  Database,
  Clock,
  CheckCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

import { useAdminDashboard } from './hooks/useAdminDashboard';
import {
  getSeverityColor,
  getStatusColor,
  formatDate,
  formatNumber
} from './utils/displayHelpers';

const AdminDashboard: React.FC<{ className?: string }> = ({ className = '' }) => {
  const {
    metrics,
    filteredUsers,
    filteredAlerts,
    recentActivities,
    loading,
    activeTab,
    searchTerm,
    autoRefresh,
    setActiveTab,
    setSearchTerm,
    setAutoRefresh,
    handleResolveAlert,
    handleUserAction,
  } = useAdminDashboard();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="h-8 w-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className={`space-y-6 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Shield className="h-8 w-8 text-purple-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
            <p className="text-sm text-gray-500">System monitoring and management</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto-Refresh: {autoRefresh ? 'On' : 'Off'}
          </Button>
        </div>
      </div>

      {/* System Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Users</p>
                  <p className="text-2xl font-bold">{formatNumber(metrics.totalUsers)}</p>
                  <p className="text-xs text-green-600">{formatNumber(metrics.activeUsers)} active</p>
                </div>
                <Users className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Compliance Score</p>
                  <p className="text-2xl font-bold">{metrics.complianceScore}%</p>
                  <p className="text-xs text-green-600">Excellent</p>
                </div>
                <Shield className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">System Health</p>
                  <p className="text-2xl font-bold capitalize">{metrics.systemHealth}</p>
                  <p className="text-xs text-gray-500">{metrics.uptime}% uptime</p>
                </div>
                <Activity className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Storage</p>
                  <p className="text-2xl font-bold">{metrics.storageUsed}%</p>
                  <p className="text-xs text-gray-500">{metrics.storageTotal} GB total</p>
                </div>
                <Database className="h-8 w-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Tabs */}
      <div className="border-b">
        <div className="flex gap-4">
          {['overview', 'users', 'alerts', 'activity'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`pb-4 px-2 capitalize transition-colors ${
                activeTab === tab
                  ? 'border-b-2 border-purple-600 text-purple-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>User Management</CardTitle>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2 top-2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search users..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-8 pr-4 py-2 border rounded-lg text-sm"
                  />
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {filteredUsers.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center">
                      <span className="text-purple-600 font-semibold">
                        {user.name.split(' ').map(n => n[0]).join('')}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium">{user.name}</p>
                      <p className="text-sm text-gray-500">{user.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge color={getStatusColor(user.status)}>{user.status}</Badge>
                    <Badge variant="outline">{user.role}</Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleUserAction(user.id, user.status === 'active' ? 'deactivate' : 'activate')}
                    >
                      {user.status === 'active' ? 'Deactivate' : 'Activate'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">Active Alerts</h2>
            <Badge className="bg-red-100 text-red-600">
              {filteredAlerts.length} Open
            </Badge>
          </div>
          {filteredAlerts.map((alert) => (
            <Card key={alert.id} className="border-l-4 border-l-red-500">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge color={getSeverityColor(alert.severity)}>
                        {alert.severity.toUpperCase()}
                      </Badge>
                      <Badge variant="outline">{alert.category}</Badge>
                      <span className="text-sm text-gray-500">
                        {formatDate(alert.timestamp)}
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold mb-1">{alert.title}</h3>
                    <p className="text-gray-600">{alert.description}</p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleResolveAlert(alert.id)}
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Resolve
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Activity Tab */}
      {activeTab === 'activity' && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivities.map((activity) => (
                <div key={activity.id} className="flex items-start gap-4">
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
                    activity.status === 'success' ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    <Activity className={`h-4 w-4 ${
                      activity.status === 'success' ? 'text-green-600' : 'text-red-600'
                    }`} />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">{activity.action}</p>
                    <p className="text-sm text-gray-600">{activity.details}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {activity.user} • {formatDate(activity.timestamp)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Stats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Total Documents</span>
                  <span className="font-bold">{metrics?.totalDocuments}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">API Calls (24h)</span>
                  <span className="font-bold">{formatNumber(metrics?.apiCalls || 0)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Error Rate</span>
                  <span className="font-bold text-red-600">{metrics?.errorRate}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Avg Response Time</span>
                  <span className="font-bold">{metrics?.responseTime}ms</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recent Alerts Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {filteredAlerts.slice(0, 5).map((alert) => (
                  <div key={alert.id} className="flex items-center justify-between text-sm">
                    <span className="flex-1 truncate">{alert.title}</span>
                    <Badge color={getSeverityColor(alert.severity)} size="sm">
                      {alert.severity}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
