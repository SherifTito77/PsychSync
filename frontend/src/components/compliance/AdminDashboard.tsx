import React, { useState, useEffect } from 'react';
import {
  Shield,
  Users,
  FileText,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  Calendar,
  Settings,
  Download,
  Upload,
  RefreshCw,
  Eye,
  Edit,
  Trash2,
  Plus,
  Filter,
  Search,
  ChevronDown,
  ChevronRight,
  Globe,
  Lock,
  Database,
  Zap,
  Bell,
  Mail,
  Smartphone,
  Monitor,
  Cpu,
  HardDrive,
  Wifi,
  Key,
  UserCheck,
  Award,
  Target,
  Flag,
  Star,
  ArrowUp,
  ArrowDown,
  Minus,
  MoreHorizontal,
  X,
  HelpCircle,
  AlertCircle,
  CheckSquare
} from 'lucide-react';
import Button from '../common/Button';
import { Card } from '../common/card';
import Badge from '../common/Badge';
import LoadingSpinner from '../common/LoadingSpinner';
import { useNotification } from '../../contexts/NotificationContext';
interface SystemMetrics {
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
interface User {
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
interface Alert {
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
interface Activity {
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
interface AdminDashboardProps {
  className?: string;
}
export const AdminDashboard: React.FC<AdminDashboardProps> = ({ className = '' }) => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'system' | 'alerts' | 'activity'>('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRole, setSelectedRole] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const { showNotification } = useNotification();
  useEffect(() => {
    loadDashboardData();
    if (autoRefresh) {
      const interval = setInterval(loadDashboardData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, activeTab]);
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
      showNotification('Failed to load dashboard data', 'error');
    } finally {
      setLoading(false);
    }
  };
  const handleResolveAlert = (alertId: string) => {
    setAlerts(prev => prev.map(alert =>
      alert.id === alertId
        ? { ...alert, status: 'resolved' }
        : alert
    ));
    showNotification('Alert resolved successfully', 'success');
  };
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
    showNotification(`User ${action}d successfully`, 'success');
  };
  const getSeverityColor = (severity: Alert['severity']) => {
    switch (severity) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'green';
      default: return 'gray';
    }
  };
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': case 'active': case 'success': return 'green';
      case 'warning': case 'pending': return 'yellow';
      case 'critical': case 'error': case 'failure': return 'red';
      case 'inactive': case 'suspended': return 'gray';
      default: return 'gray';
    }
  };
  const getRoleIcon = (role: User['role']) => {
    switch (role) {
      case 'admin': return <Shield className="w-4 h-4" />;
      case 'manager': return <Users className="w-4 h-4" />;
      case 'auditor': return <FileText className="w-4 h-4" />;
      default: return <UserCheck className="w-4 h-4" />;
    }
  };
  if (loading) {
    return <LoadingSpinner />;
  }
  return (
    <div className={`max-w-7xl mx-auto p-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600 mt-1">System administration and compliance management</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => setAutoRefresh(!autoRefresh)}
            icon={autoRefresh ? <Bell className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
          >
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </Button>
          <Button
            variant="outline"
            onClick={loadDashboardData}
            icon={<RefreshCw className="w-4 h-4" />}
          >
            Refresh
          </Button>
        </div>
      </div>
      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', count: null },
            { id: 'users', label: 'Users', count: users.length },
            { id: 'system', label: 'System', count: null },
            { id: 'alerts', label: 'Alerts', count: alerts.filter(a => a.status === 'open').length },
            { id: 'activity', label: 'Activity', count: activities.length }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              {tab.count !== null && tab.count > 0 && (
                <Badge
                  color={activeTab === tab.id ? 'blue' : 'gray'}
                  size="sm"
                  className="ml-2"
                >
                  {tab.count}
                </Badge>
              )}
            </button>
          ))}
        </nav>
      </div>
      {/* Tab Content */}
      {activeTab === 'overview' && metrics && (
        <div className="space-y-6">
          {/* System Health Overview */}
          <Card>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">System Health</h2>
              <Badge color={getStatusColor(metrics.systemHealth)} size="lg">
                {metrics.systemHealth.toUpperCase()}
              </Badge>
            </div>
            {/* Key Metrics Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <MetricCard
                value={metrics.totalUsers}
                icon={<Users className="w-5 h-5" />}
                color="blue"
                trend={5.2}
                trendDirection="up"
              />
              <MetricCard
                value={metrics.activeUsers}
                icon={<Activity className="w-5 h-5" />}
                color="green"
                trend={2.1}
                trendDirection="up"
              />
              <MetricCard
                value={metrics.complianceScore}
                unit="%"
                icon={<Shield className="w-5 h-5" />}
                color="purple"
                trend={1.5}
                trendDirection="up"
              />
              <MetricCard
                value={metrics.uptime}
                unit="%"
                icon={<Monitor className="w-5 h-5" />}
                color="green"
                trend={0.1}
                trendDirection="up"
              />
            </div>
            {/* Performance Metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <h3 className="font-semibold text-gray-900 mb-4">Performance Overview</h3>
                <div className="space-y-4">
                  <PerformanceMetric
                    label="Response Time"
                    value={metrics.responseTime}
                    unit="ms"
                    target={500}
                    color="blue"
                  />
                  <PerformanceMetric
                    label="Error Rate"
                    value={metrics.errorRate}
                    unit="%"
                    target={1}
                    color="red"
                    inverse
                  />
                  <PerformanceMetric
                    label="API Calls"
                    value={metrics.apiCalls}
                    unit="/min"
                    target={1000}
                    color="green"
                  />
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">Storage Usage</h3>
                <Card className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Used</span>
                    <span className="font-medium">
                      {metrics.storageUsed}GB / {metrics.storageTotal}GB
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${(metrics.storageUsed / metrics.storageTotal) * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {((metrics.storageUsed / metrics.storageTotal) * 100).toFixed(1)}% utilized
                  </p>
                </Card>
              </div>
            </div>
          </Card>
          {/* Recent Alerts and Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <h3 className="font-semibold text-gray-900 mb-4">Recent Alerts</h3>
              <div className="space-y-3">
                {alerts.slice(0, 5).map((alert) => (
                  <div key={alert.id} className="flex items-start space-x-3">
                    <div className={`p-2 rounded-full ${
                      alert.severity === 'critical' ? 'bg-red-100' :
                      alert.severity === 'high' ? 'bg-orange-100' :
                      alert.severity === 'medium' ? 'bg-yellow-100' : 'bg-green-100'
                    }`}>
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">{alert.title}</p>
                      <p className="text-xs text-gray-500">{new Date(alert.timestamp).toLocaleString()}</p>
                    </div>
                    <Badge color={getSeverityColor(alert.severity)} size="sm">
                      {alert.severity}
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
            <Card>
              <h3 className="font-semibold text-gray-900 mb-4">Recent Activity</h3>
              <div className="space-y-3">
                {activities.slice(0, 5).map((activity) => (
                  <div key={activity.id} className="flex items-start space-x-3">
                    <div className={`p-2 rounded-full ${
                      activity.status === 'success' ? 'bg-green-100' :
                      activity.status === 'failure' ? 'bg-red-100' : 'bg-yellow-100'
                    }`}>
                      <Activity className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                      <p className="text-xs text-gray-500">
                        {activity.user} • {new Date(activity.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <Badge color={getStatusColor(activity.status)} size="sm">
                      {activity.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}
      {activeTab === 'users' && (
        <div className="space-y-6">
          {/* Search and Filters */}
          <Card>
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search users..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div className="flex gap-3">
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Roles</option>
                  <option value="admin">Admin</option>
                  <option value="manager">Manager</option>
                  <option value="employee">Employee</option>
                  <option value="auditor">Auditor</option>
                </select>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="suspended">Suspended</option>
                </select>
              </div>
            </div>
          </Card>
          {/* Users Table */}
          <Card>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Department
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Compliance
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Training
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users
                    .filter(user => {
                      const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                           user.email.toLowerCase().includes(searchTerm.toLowerCase());
                      const matchesRole = selectedRole === 'all' || user.role === selectedRole;
                      const matchesStatus = selectedStatus === 'all' || user.status === selectedStatus;
                      return matchesSearch && matchesRole && matchesStatus;
                    })
                    .map((user) => (
                      <UserRow
                        key={user.id}
                        user={user}
                        onAction={handleUserAction}
                        getRoleIcon={getRoleIcon}
                        getStatusColor={getStatusColor}
                      />
                    ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
      {activeTab === 'system' && metrics && (
        <div className="space-y-6">
          {/* System Information */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SystemInfoCard
              icon={<Monitor className="w-8 h-8" />}
              items={[
                { label: 'Version', value: '2.1.0' },
                { label: 'Environment', value: 'Production' },
                { label: 'Deployed', value: '2024-03-01' },
                { label: 'Node.js', value: '18.17.0' },
                { label: 'Framework', value: 'React + TypeScript' }
              ]}
            />
            <SystemInfoCard
              icon={<Database className="w-8 h-8" />}
              items={[
                { label: 'Type', value: 'PostgreSQL' },
                { label: 'Version', value: '15.3' },
                { label: 'Size', value: `${metrics.storageUsed}GB` },
                { label: 'Connections', value: '45/100' },
                { label: 'Query Time', value: '12ms avg' }
              ]}
            />
            <SystemInfoCard
              icon={<HardDrive className="w-8 h-8" />}
              items={[
                { label: 'CPU Usage', value: '45%' },
                { label: 'Memory', value: '8.2GB / 16GB' },
                { label: 'Disk I/O', value: '125 MB/s' },
                { label: 'Network', value: '1.2 Gbps' },
                { label: 'Load Average', value: '2.3' }
              ]}
            />
            <SystemInfoCard
              icon={<Lock className="w-8 h-8" />}
              items={[
                { label: 'SSL Certificate', value: 'Valid until 2024-12-31' },
                { label: 'Firewall', value: 'Active' },
                { label: 'Last Security Scan', value: '2024-03-10' },
                { label: 'Vulnerabilities', value: '0 Critical' },
                { label: 'Authentication', value: '2FA Enabled' }
              ]}
            />
          </div>
          {/* System Logs */}
          <Card>
            <h3 className="font-semibold text-gray-900 mb-4">System Logs</h3>
            <div className="space-y-2 font-mono text-sm">
              {[
                { timestamp: '2024-03-12 10:30:15', level: 'INFO', message: 'System health check completed successfully' },
                { timestamp: '2024-03-12 10:28:42', level: 'WARN', message: 'High memory usage detected on server-2' },
                { timestamp: '2024-03-12 10:25:18', level: 'INFO', message: 'Database backup completed' },
                { timestamp: '2024-03-12 10:22:33', level: 'ERROR', message: 'Failed to connect to external API' },
                { timestamp: '2024-03-12 10:20:00', level: 'INFO', message: 'Scheduled maintenance task completed' }
              ].map((log, index) => (
                <div key={index} className="flex items-center space-x-3 p-2 rounded hover:bg-gray-50">
                  <span className="text-xs text-gray-500">{log.timestamp}</span>
                  <Badge color={log.level === 'ERROR' ? 'red' : log.level === 'WARN' ? 'yellow' : 'green'} size="sm">
                    {log.level}
                  </Badge>
                  <span className="text-gray-700">{log.message}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
      {activeTab === 'alerts' && (
        <div className="space-y-6">
          {/* Alert Statistics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              value={alerts.filter(a => a.status === 'open').length}
              icon={<AlertTriangle className="w-5 h-5" />}
              color="red"
            />
            <StatCard
              value={alerts.filter(a => a.severity === 'critical').length}
              icon={<AlertCircle className="w-5 h-5" />}
              color="red"
            />
            <StatCard
              value={alerts.filter(a => a.status === 'acknowledged').length}
              icon={<Eye className="w-5 h-5" />}
              color="yellow"
            />
            <StatCard
              value={alerts.filter(a => a.status === 'resolved').length}
              icon={<CheckCircle className="w-5 h-5" />}
              color="green"
            />
          </div>
          {/* Alerts List */}
          <Card>
            <div className="space-y-4">
              {alerts.map((alert) => (
                <AlertCard
                  key={alert.id}
                  alert={alert}
                  onResolve={() => handleResolveAlert(alert.id)}
                  getSeverityColor={getSeverityColor}
                />
              ))}
            </div>
          </Card>
        </div>
      )}
      {activeTab === 'activity' && (
        <div className="space-y-6">
          {/* Activity Filters */}
          <Card>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Activity Log</h3>
              <Button variant="outline" icon={<Download className="w-4 h-4" />}>
                Export Log
              </Button>
            </div>
          </Card>
          {/* Activity List */}
          <Card>
            <div className="space-y-3">
              {activities.map((activity) => (
                <ActivityCard
                  key={activity.id}
                  activity={activity}
                  getStatusColor={getStatusColor}
                />
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
// Helper Components
interface MetricCardProps {
  title: string;
  value: number;
  unit?: string;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
  trend?: number;
  trendDirection?: 'up' | 'down' | 'stable';
}
const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  icon,
  color,
  trend,
  trendDirection
}) => {
  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-100 text-blue-600',
      green: 'bg-green-100 text-green-600',
      yellow: 'bg-yellow-100 text-yellow-600',
      red: 'bg-red-100 text-red-600',
      purple: 'bg-purple-100 text-purple-600'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };
  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };
  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <div className="flex items-baseline mt-1">
            <p className="text-2xl font-bold text-gray-900">
              {value.toLocaleString()}
              {unit && <span className="text-sm font-normal text-gray-500 ml-1">{unit}</span>}
            </p>
          </div>
          {trend !== undefined && trendDirection && (
            <div className="flex items-center mt-2 text-sm">
              {trendDirection === 'up' ? (
                <ArrowUp className="w-4 h-4 text-green-500 mr-1" />
              ) : trendDirection === 'down' ? (
                <ArrowDown className="w-4 h-4 text-red-500 mr-1" />
              ) : (
                <Minus className="w-4 h-4 text-gray-500 mr-1" />
              )}
              <span className={getTrendColor(trendDirection)}>
                {trend > 0 ? `+${trend}%` : `${trend}%`}
              </span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-lg ${getColorClasses(color)}`}>
          {icon}
        </div>
      </div>
    </Card>
  );
};
interface PerformanceMetricProps {
  label: string;
  value: number;
  unit: string;
  target: number;
  color: string;
  inverse?: boolean;
}
const PerformanceMetric: React.FC<PerformanceMetricProps> = ({
  label,
  value,
  unit,
  target,
  color,
  inverse = false
}) => {
  const percentage = (value / target) * 100;
  const isGood = inverse ? percentage <= 100 : percentage <= 100;
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div>
        <p className="text-sm font-medium text-gray-900">{label}</p>
        <p className="text-xs text-gray-500">Target: {target}{unit}</p>
      </div>
      <div className="text-right">
        <p className={`font-semibold ${
          isGood ? 'text-green-600' : 'text-red-600'
        }`}>
          {value}{unit}
        </p>
        <div className="w-20 bg-gray-200 rounded-full h-2 mt-1">
          <div
            className={`h-2 rounded-full ${
              isGood ? 'bg-green-500' : 'bg-red-500'
            }`}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
};
interface SystemInfoCardProps {
  title: string;
  icon: React.ReactNode;
  items: Array<{ label: string; value: string }>;
}
const SystemInfoCard: React.FC<SystemInfoCardProps> = ({ title, icon, items }) => {
  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="text-blue-600">{icon}</div>
          <h3 className="font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="space-y-3">
          {items.map((item, index) => (
            <div key={index} className="flex justify-between">
              <span className="text-sm text-gray-600">{item.label}:</span>
              <span className="text-sm font-medium text-gray-900">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};
interface UserRowProps {
  user: User;
  onAction: (userId: string, action: 'activate' | 'deactivate' | 'suspend') => void;
  getRoleIcon: (role: User['role']) => React.ReactNode;
  getStatusColor: (status: string) => string;
}
const UserRow: React.FC<UserRowProps> = ({ user, onAction, getRoleIcon, getStatusColor }) => {
  const [showActions, setShowActions] = useState(false);
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <div className="flex-shrink-0 h-10 w-10">
            <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
              <UserCheck className="h-4 w-4 text-gray-500" />
            </div>
          </div>
          <div className="ml-4">
            <div className="text-sm font-medium text-gray-900">{user.name}</div>
            <div className="text-sm text-gray-500">{user.email}</div>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          {getRoleIcon(user.role)}
          <span className="ml-2 text-sm text-gray-900 capitalize">{user.role}</span>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        {user.department}
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <span className="text-sm font-medium">{user.complianceScore}%</span>
          <div className="w-16 bg-gray-200 rounded-full h-2 ml-2">
            <div
              className={`h-2 rounded-full ${
                user.complianceScore >= 90 ? 'bg-green-500' :
                user.complianceScore >= 70 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${user.complianceScore}%` }}
            />
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <span className="text-sm font-medium">{user.trainingProgress}%</span>
          <div className="w-16 bg-gray-200 rounded-full h-2 ml-2">
            <div
              className="bg-blue-500 h-2 rounded-full"
              style={{ width: `${user.trainingProgress}%` }}
            />
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <Badge color={getStatusColor(user.status)} size="sm">
          {user.status}
        </Badge>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <div className="relative">
          <Button
            variant="ghost"
            size="small"
            onClick={() => setShowActions(!showActions)}
            icon={<MoreHorizontal className="w-4 h-4" />}
          />
          {showActions && (
            <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
              {user.status !== 'active' && (
                <button
                  onClick={() => { onAction(user.id, 'activate'); setShowActions(false); }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Activate
                </button>
              )}
              {user.status === 'active' && (
                <button
                  onClick={() => { onAction(user.id, 'deactivate'); setShowActions(false); }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Deactivate
                </button>
              )}
              {user.status !== 'suspended' && (
                <button
                  onClick={() => { onAction(user.id, 'suspend'); setShowActions(false); }}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  Suspend
                </button>
              )}
            </div>
          )}
        </div>
      </td>
    </tr>
  );
};
interface AlertCardProps {
  alert: Alert;
  onResolve: () => void;
  getSeverityColor: (severity: Alert['severity']) => string;
}
const AlertCard: React.FC<AlertCardProps> = ({ alert, onResolve, getSeverityColor }) => {
  return (
    <Card>
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-full ${
              alert.severity === 'critical' ? 'bg-red-100' :
              alert.severity === 'high' ? 'bg-orange-100' :
              alert.severity === 'medium' ? 'bg-yellow-100' : 'bg-green-100'
            }`}>
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{alert.title}</h3>
              <p className="text-sm text-gray-600">{alert.description}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge color={getSeverityColor(alert.severity)} size="sm">
              {alert.severity}
            </Badge>
            <Badge color={alert.status === 'open' ? 'red' : 'green'} size="sm" variant="outline">
              {alert.status}
            </Badge>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-500">
            {alert.source} • {new Date(alert.timestamp).toLocaleString()}
          </div>
          {alert.status === 'open' && (
            <Button size="small" onClick={onResolve}>
              Resolve
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
};
interface ActivityCardProps {
  activity: Activity;
  getStatusColor: (status: string) => string;
}
const ActivityCard: React.FC<ActivityCardProps> = ({ activity, getStatusColor }) => {
  return (
    <div className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg">
      <div className={`p-2 rounded-full ${
        activity.status === 'success' ? 'bg-green-100' :
        activity.status === 'failure' ? 'bg-red-100' : 'bg-yellow-100'
      }`}>
        <Activity className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900">{activity.action}</p>
        <p className="text-xs text-gray-500">
          {activity.user} • {activity.ip} • {new Date(activity.timestamp).toLocaleString()}
        </p>
      </div>
      <Badge color={getStatusColor(activity.status)} size="sm">
        {activity.status}
      </Badge>
    </div>
  );
};
interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'yellow' | 'red';
}
const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color }) => {
  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-100 text-blue-600',
      green: 'bg-green-100 text-green-600',
      yellow: 'bg-yellow-100 text-yellow-600',
      red: 'bg-red-100 text-red-600'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };
  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value.toLocaleString()}</p>
        </div>
        <div className={`p-3 rounded-lg ${getColorClasses(color)}`}>
          {icon}
        </div>
      </div>
    </Card>
  );
};
// Mock data generators
const mockSystemMetrics = async (): Promise<SystemMetrics> => ({
  totalUsers: 1247,
  activeUsers: 892,
  totalDocuments: 3456,
  complianceScore: 87,
  systemHealth: 'healthy',
  uptime: 99.9,
  storageUsed: 125,
  storageTotal: 500,
  apiCalls: 856,
  errorRate: 0.2,
  responseTime: 145
});
const mockUsers = async (): Promise<User[]> => [
  {
    id: 'user-1',
    name: 'John Doe',
    email: 'john.doe@company.com',
    role: 'admin',
    department: 'IT',
    status: 'active',
    lastLogin: '2024-03-12T09:30:00Z',
    complianceScore: 95,
    trainingProgress: 100,
    pendingTasks: 2,
    joinedAt: '2023-01-15T10:00:00Z'
  },
  {
    id: 'user-2',
    name: 'Jane Smith',
    email: 'jane.smith@company.com',
    role: 'manager',
    department: 'HR',
    status: 'active',
    lastLogin: '2024-03-12T08:45:00Z',
    complianceScore: 88,
    trainingProgress: 75,
    pendingTasks: 5,
    joinedAt: '2023-02-20T14:30:00Z'
  },
  {
    id: 'user-3',
    name: 'Mike Johnson',
    email: 'mike.johnson@company.com',
    role: 'employee',
    department: 'Sales',
    status: 'active',
    lastLogin: '2024-03-11T16:20:00Z',
    complianceScore: 72,
    trainingProgress: 60,
    pendingTasks: 3,
    joinedAt: '2023-03-10T09:15:00Z'
  }
];
const mockAlerts = async (): Promise<Alert[]> => [
  {
    id: 'alert-1',
    type: 'security',
    severity: 'critical',
    title: 'Failed Login Attempts Detected',
    description: 'Multiple failed login attempts detected from IP 203.0.113.1',
    timestamp: '2024-03-12T10:30:00Z',
    status: 'open',
    category: 'Security',
    source: 'Authentication System',
    actions: ['Block IP', 'Reset Passwords', 'Notify User']
  },
  {
    id: 'alert-2',
    type: 'performance',
    severity: 'medium',
    title: 'High Memory Usage',
    description: 'Server memory usage exceeded 80% threshold',
    timestamp: '2024-03-12T09:45:00Z',
    status: 'acknowledged',
    category: 'Infrastructure',
    source: 'Server Monitoring',
    actions: ['Scale Resources', 'Restart Services']
  }
];
const mockActivities = async (): Promise<Activity[]> => [
  {
    id: 'activity-1',
    type: 'user',
    user: 'John Doe',
    action: 'Login',
    details: 'Successful login from IP 192.168.1.100',
    timestamp: '2024-03-12T10:30:00Z',
    ip: '192.168.1.100',
    status: 'success',
    metadata: { userAgent: 'Mozilla/5.0...', location: 'New York' }
  },
  {
    id: 'activity-2',
    type: 'admin',
    user: 'System',
    action: 'Backup Completed',
    details: 'Daily database backup completed successfully',
    timestamp: '2024-03-12T02:00:00Z',
    ip: 'localhost',
    status: 'success',
    metadata: { size: '2.5GB', duration: '45 seconds' }
  }
];