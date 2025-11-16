import React, { useState, useEffect } from 'react';
import {
  Zap,
  Slack,
  MessageSquare,
  Mail,
  Calendar,
  Users,
  Shield,
  Settings,
  Plus,
  Edit,
  Trash2,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  Globe,
  Smartphone,
  Key,
  Database,
  FileText,
  Bell,
  Link,
  Unlink,
  Eye,
  Download,
  Upload,
  ChevronDown,
  ChevronRight,
  HelpCircle,
  TestTube,
  Activity,
  Webhook,
  X
} from 'lucide-react';
import Button from '../common/Button';
import { Card } from '../common/card';
import Badge from '../common/Badge';
import LoadingSpinner from '../common/LoadingSpinner';
import { useNotification } from '../../contexts/NotificationContext';
interface Integration {
  id: string;
  name: string;
  type: 'slack' | 'teams' | 'email' | 'webhook' | 'hris' | 'sso' | 'api' | 'calendar' | 'custom';
  category: 'communication' | 'hr' | 'security' | 'productivity' | 'analytics' | 'automation';
  description: string;
  status: 'connected' | 'disconnected' | 'error' | 'pending' | 'testing';
  icon: React.ReactNode;
  version: string;
  lastSync?: string;
  lastError?: string;
  configuration: IntegrationConfig;
  webhookEndpoints: WebhookEndpoint[];
  syncSchedule?: SyncSchedule;
  statistics: {
    totalSyncs: number;
    successfulSyncs: number;
    failedSyncs: number;
    dataPointsProcessed: number;
    lastDayActivity: number;
  };
  permissions: string[];
  tags: string[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}
interface IntegrationConfig {
  apiKey?: string;
  apiSecret?: string;
  webhookUrl?: string;
  channelId?: string;
  teamId?: string;
  emailSettings?: {
    fromAddress: string;
    replyTo: string;
    template: string;
  };
  mapping: Record<string, string>;
  settings: Record<string, any>;
}
interface WebhookEndpoint {
  id: string;
  url: string;
  events: string[];
  secret: string;
  active: boolean;
  lastTriggered?: string;
  totalTriggers: number;
}
interface SyncSchedule {
  enabled: boolean;
  frequency: 'realtime' | 'hourly' | 'daily' | 'weekly' | 'monthly';
  time?: string;
  dayOfWeek?: number;
  dayOfMonth?: number;
}
interface IntegrationHubProps {
  className?: string;
}
export const IntegrationHub: React.FC<IntegrationHubProps> = ({ className = '' }) => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'integrations' | 'webhooks' | 'logs'>('overview');
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [showSetupModal, setShowSetupModal] = useState(false);
  const [showTestModal, setShowTestModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const { showNotification } = useNotification();
  useEffect(() => {
    loadIntegrations();
  }, [searchTerm, selectedCategory, selectedStatus]);
  const loadIntegrations = async () => {
    try {
      setLoading(true);
      const data = await mockIntegrations();
      const filteredData = filterIntegrations(data);
      setIntegrations(filteredData);
    } catch (error) {
      console.error('Failed to load integrations:', error);
      showNotification('Failed to load integrations', 'error');
    } finally {
      setLoading(false);
    }
  };
  const filterIntegrations = (integrationData: Integration[]) => {
    return integrationData.filter(integration => {
      const matchesSearch = integration.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           integration.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           integration.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
      const matchesCategory = selectedCategory === 'all' || integration.category === selectedCategory;
      const matchesStatus = selectedStatus === 'all' || integration.status === selectedStatus;
      return matchesSearch && matchesCategory && matchesStatus;
    });
  };
  const handleSetupIntegration = (type: Integration['type']) => {
    setSelectedIntegration(null);
    setShowSetupModal(true);
  };
  const handleConfigureIntegration = (integration: Integration) => {
    setSelectedIntegration(integration);
    setShowSetupModal(true);
  };
  const handleTestConnection = async (integration: Integration) => {
    try {
      setSelectedIntegration(integration);
      setShowTestModal(true);
      // Simulate connection test
      await new Promise(resolve => setTimeout(resolve, 2000));
      setIntegrations(prev => prev.map(int =>
        int.id === integration.id
          ? { ...int, status: 'connected', lastSync: new Date().toISOString() }
          : int
      ));
      showNotification('Connection test successful', 'success');
      setShowTestModal(false);
    } catch (error) {
      showNotification('Connection test failed', 'error');
    }
  };
  const handleDisconnectIntegration = (integrationId: string) => {
    if (confirm('Are you sure you want to disconnect this integration?')) {
      setIntegrations(prev => prev.map(int =>
        int.id === integrationId
          ? { ...int, status: 'disconnected' }
          : int
      ));
      showNotification('Integration disconnected successfully', 'success');
    }
  };
  const getStatusColor = (status: Integration['status']) => {
    switch (status) {
      case 'connected': return 'green';
      case 'disconnected': return 'gray';
      case 'error': return 'red';
      case 'pending': return 'yellow';
      case 'testing': return 'blue';
      default: return 'gray';
    }
  };
  const getCategoryColor = (category: Integration['category']) => {
    switch (category) {
      case 'communication': return 'blue';
      case 'hr': return 'purple';
      case 'security': return 'red';
      case 'productivity': return 'green';
      case 'analytics': return 'yellow';
      case 'automation': return 'orange';
      default: return 'gray';
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
          <h1 className="text-3xl font-bold text-gray-900">Integration Hub</h1>
          <p className="text-gray-600 mt-1">Connect and manage third-party integrations for enhanced compliance workflows</p>
        </div>
        <Button
          onClick={() => handleSetupIntegration('slack')}
          icon={<Plus className="w-4 h-4" />}
        >
          Add Integration
        </Button>
      </div>
      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', count: integrations.filter(i => i.status === 'connected').length },
            { id: 'integrations', label: 'Integrations', count: integrations.length },
            { id: 'webhooks', label: 'Webhooks', count: integrations.reduce((sum, i) => sum + i.webhookEndpoints.length, 0) },
            { id: 'logs', label: 'Activity Logs', count: null }
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
              {tab.count !== null && (
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
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              value={integrations.filter(i => i.status === 'connected').length}
              icon={<CheckCircle className="w-5 h-5" />}
              color="green"
            />
            <StatCard
              value={integrations.reduce((sum, i) => sum + i.webhookEndpoints.filter(w => w.active).length, 0)}
              icon={<Webhook className="w-5 h-5" />}
              color="blue"
            />
            <StatCard
              value={integrations.reduce((sum, i) => sum + i.statistics.lastDayActivity, 0)}
              icon={<RefreshCw className="w-5 h-5" />}
              color="purple"
            />
            <StatCard
              value={integrations.reduce((sum, i) => sum + i.statistics.dataPointsProcessed, 0)}
              icon={<Database className="w-5 h-5" />}
              color="yellow"
            />
          </div>
          {/* Available Integrations */}
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Integrations</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { type: 'slack', name: 'Slack', icon: <Slack className="w-8 h-8" />, description: 'Team communication and notifications' },
                { type: 'teams', name: 'Microsoft Teams', icon: <MessageSquare className="w-8 h-8" />, description: 'Collaboration and meeting integration' },
                { type: 'email', name: 'Email', icon: <Mail className="w-8 h-8" />, description: 'Automated email notifications and reports' },
                { type: 'calendar', name: 'Google Calendar', icon: <Calendar className="w-8 h-8" />, description: 'Compliance training and audit scheduling' },
                { type: 'hris', name: 'HRIS Systems', icon: <Users className="w-8 h-8" />, description: 'Employee data and organization sync' },
                { type: 'sso', name: 'Single Sign-On', icon: <Shield className="w-8 h-8" />, description: 'Enterprise authentication integration' }
              ].map((integration) => {
                const existingIntegration = integrations.find(i => i.type === integration.type);
                return (
                  <div
                    key={integration.type}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className="text-blue-600">{integration.icon}</div>
                        <h4 className="font-semibold text-gray-900">{integration.name}</h4>
                      </div>
                      {existingIntegration && (
                        <Badge color={getStatusColor(existingIntegration.status)} size="sm">
                          {existingIntegration.status}
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{integration.description}</p>
                    <Button
                      size="small"
                      variant={existingIntegration ? 'outline' : 'default'}
                      onClick={() => existingIntegration
                        ? handleConfigureIntegration(existingIntegration)
                        : handleSetupIntegration(integration.type as Integration['type'])
                      }
                    >
                      {existingIntegration ? 'Configure' : 'Connect'}
                    </Button>
                  </div>
                );
              })}
            </div>
          </Card>
          {/* Recent Activity */}
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
            <div className="space-y-3">
              {integrations
                .filter(i => i.lastSync)
                .sort((a, b) => new Date(b.lastSync!).getTime() - new Date(a.lastSync!).getTime())
                .slice(0, 5)
                .map((integration) => (
                  <div key={integration.id} className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      {integration.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {integration.name} synced successfully
                      </p>
                      <p className="text-sm text-gray-500">
                        {integration.lastSync && new Date(integration.lastSync).toLocaleString()}
                      </p>
                    </div>
                    <Badge color="green" size="sm">
                      Success
                    </Badge>
                  </div>
                ))}
            </div>
          </Card>
        </div>
      )}
      {activeTab === 'integrations' && (
        <div className="space-y-6">
          {/* Search and Filters */}
          <Card>
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search integrations..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div className="flex gap-3">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Categories</option>
                  <option value="communication">Communication</option>
                  <option value="hr">HR</option>
                  <option value="security">Security</option>
                  <option value="productivity">Productivity</option>
                  <option value="analytics">Analytics</option>
                  <option value="automation">Automation</option>
                </select>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Status</option>
                  <option value="connected">Connected</option>
                  <option value="disconnected">Disconnected</option>
                  <option value="error">Error</option>
                  <option value="pending">Pending</option>
                  <option value="testing">Testing</option>
                </select>
              </div>
            </div>
          </Card>
          {/* Integrations Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {integrations.map((integration) => (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                onConfigure={handleConfigureIntegration}
                onTest={handleTestConnection}
                onDisconnect={handleDisconnectIntegration}
                getStatusColor={getStatusColor}
                getCategoryColor={getCategoryColor}
              />
            ))}
          </div>
        </div>
      )}
      {activeTab === 'webhooks' && (
        <WebhookManagement integrations={integrations} onUpdate={loadIntegrations} />
      )}
      {activeTab === 'logs' && (
        <ActivityLogs />
      )}
      {/* Setup Modal */}
      {showSetupModal && (
        <IntegrationSetupModal
          integration={selectedIntegration}
          onClose={() => setShowSetupModal(false)}
          onSaved={() => {
            setShowSetupModal(false);
            loadIntegrations();
          }}
        />
      )}
      {/* Test Connection Modal */}
      {showTestModal && selectedIntegration && (
        <TestConnectionModal
          integration={selectedIntegration}
          onClose={() => setShowTestModal(false)}
          onSuccess={() => {
            setShowTestModal(false);
            loadIntegrations();
          }}
        />
      )}
    </div>
  );
};
// Integration Card Component
interface IntegrationCardProps {
  integration: Integration;
  onConfigure: (integration: Integration) => void;
  onTest: (integration: Integration) => void;
  onDisconnect: (id: string) => void;
  getStatusColor: (status: Integration['status']) => string;
  getCategoryColor: (category: Integration['category']) => string;
}
const IntegrationCard: React.FC<IntegrationCardProps> = ({
  integration,
  onConfigure,
  onTest,
  onDisconnect,
  getStatusColor,
  getCategoryColor
}) => {
  const [showActions, setShowActions] = useState(false);
  const successRate = integration.statistics.totalSyncs > 0
    ? (integration.statistics.successfulSyncs / integration.statistics.totalSyncs) * 100
    : 0;
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gray-100 rounded-lg">
              {integration.icon}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{integration.name}</h3>
              <p className="text-sm text-gray-500">{integration.description}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge color={getStatusColor(integration.status)} size="sm">
              {integration.status}
            </Badge>
            <div className="relative">
              <Button
                variant="ghost"
                size="small"
                onClick={() => setShowActions(!showActions)}
                icon={<ChevronDown className="w-4 h-4" />}
              />
              {showActions && (
                <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
                  <button
                    onClick={() => { onConfigure(integration); setShowActions(false); }}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                  >
                    <Edit className="w-4 h-4" />
                    <span>Configure</span>
                  </button>
                  <button
                    onClick={() => { onTest(integration); setShowActions(false); }}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                  >
                    <TestTube className="w-4 h-4" />
                    <span>Test Connection</span>
                  </button>
                  {integration.status === 'connected' && (
                    <button
                      onClick={() => { onDisconnect(integration.id); setShowActions(false); }}
                      className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center space-x-2"
                    >
                      <Unlink className="w-4 h-4" />
                      <span>Disconnect</span>
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="space-y-4">
          {/* Category and Version */}
          <div className="flex items-center justify-between">
            <Badge color={getCategoryColor(integration.category)} size="sm" variant="outline">
              {integration.category}
            </Badge>
            <span className="text-sm text-gray-500">v{integration.version}</span>
          </div>
          {/* Statistics */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Total Syncs</p>
              <p className="font-semibold">{integration.statistics.totalSyncs.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Success Rate</p>
              <p className="font-semibold text-green-600">{successRate.toFixed(1)}%</p>
            </div>
          </div>
          {/* Progress Bar */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Sync Health</span>
              <span className="font-medium">{successRate.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  successRate >= 95 ? 'bg-green-500' :
                  successRate >= 80 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${successRate}%` }}
              />
            </div>
          </div>
          {/* Webhooks */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Webhooks</span>
            <Badge color="blue" size="sm">
              {integration.webhookEndpoints.length} active
            </Badge>
          </div>
          {/* Last Sync */}
          {integration.lastSync && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Last Sync</span>
              <span className="font-medium">{new Date(integration.lastSync).toLocaleString()}</span>
            </div>
          )}
          {/* Error */}
          {integration.lastError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <p className="text-sm text-red-700">{integration.lastError}</p>
              </div>
            </div>
          )}
        </div>
        {/* Quick Actions */}
        <div className="mt-4 pt-4 border-t border-gray-100 flex gap-2">
          <Button size="small" onClick={() => onConfigure(integration)}>
            Configure
          </Button>
          <Button variant="outline" size="small" onClick={() => onTest(integration)}>
            Test
          </Button>
        </div>
      </div>
    </Card>
  );
};
// Stat Card Component
interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
}
const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color }) => {
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
// Webhook Management Component
interface WebhookManagementProps {
  integrations: Integration[];
  onUpdate: () => void;
}
const WebhookManagement: React.FC<WebhookManagementProps> = ({ integrations, onUpdate }) => {
  const allWebhooks = integrations.flatMap(integration =>
    integration.webhookEndpoints.map(webhook => ({
      ...webhook,
      integrationName: integration.name,
      integrationType: integration.type
    }))
  );
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Webhook Endpoints</h3>
        <Button icon={<Plus className="w-4 h-4" />}>
          Add Webhook
        </Button>
      </div>
      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Endpoint
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Integration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Events
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Activity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {allWebhooks.map((webhook) => (
                <tr key={webhook.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{webhook.url}</div>
                      <div className="text-xs text-gray-500">ID: {webhook.id}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900">{webhook.integrationName}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-wrap gap-1">
                      {webhook.events.slice(0, 2).map((event, index) => (
                        <Badge key={index} color="blue" size="sm">
                          {event}
                        </Badge>
                      ))}
                      {webhook.events.length > 2 && (
                        <Badge color="gray" size="sm">
                          +{webhook.events.length - 2}
                        </Badge>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge color={webhook.active ? 'green' : 'gray'} size="sm">
                      {webhook.active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {webhook.totalTriggers} triggers
                    </div>
                    {webhook.lastTriggered && (
                      <div className="text-xs text-gray-500">
                        Last: {new Date(webhook.lastTriggered).toLocaleDateString()}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Button variant="outline" size="small">
                      Edit
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
// Activity Logs Component
const ActivityLogs: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Activity Logs</h3>
        <Button variant="outline" icon={<Download className="w-4 h-4" />}>
          Export Logs
        </Button>
      </div>
      <Card>
        <div className="text-center py-12">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Integration Activity</h3>
          <p className="text-gray-500 mb-6">
            Monitor all integration activities, sync operations, and webhook events
          </p>
          <div className="space-y-3 text-left max-w-2xl mx-auto">
            {[
              { time: '2 minutes ago', action: 'Slack integration synced successfully', status: 'success' },
              { time: '15 minutes ago', action: 'Webhook triggered: employee_created', status: 'success' },
              { time: '1 hour ago', action: 'HRIS sync completed', status: 'success' },
              { time: '2 hours ago', action: 'Email notification sent for training overdue', status: 'success' }
            ].map((log, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Activity className="w-4 h-4 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{log.action}</p>
                    <p className="text-xs text-gray-500">{log.time}</p>
                  </div>
                </div>
                <Badge color="green" size="sm">
                  Success
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
};
// Modal Components
const IntegrationSetupModal: React.FC<any> = ({ integration, onClose, onSaved }) => {
  const [formData, setFormData] = useState({
    name: integration?.name || '',
    type: integration?.type || 'slack',
    description: integration?.description || '',
    configuration: integration?.configuration || {},
    syncSchedule: integration?.syncSchedule || { enabled: true, frequency: 'daily' }
  });
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSaved();
  };
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {integration ? 'Configure Integration' : 'Setup Integration'}
            </h2>
            <Button variant="ghost" size="small" onClick={onClose} icon={<X className="w-4 h-4" />} />
          </div>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Integration Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          {!integration && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
              <select
                value={formData.type}
                onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value as any }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="slack">Slack</option>
                <option value="teams">Microsoft Teams</option>
                <option value="email">Email</option>
                <option value="webhook">Webhook</option>
                <option value="hris">HRIS</option>
                <option value="sso">SSO</option>
              </select>
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>
          {/* Configuration would go here based on integration type */}
          <Card>
            <h3 className="font-medium text-gray-900 mb-3">Configuration</h3>
            <p className="text-sm text-gray-600">
              Configuration options would be displayed here based on the integration type
            </p>
          </Card>
          <div className="flex gap-3">
            <Button type="submit">
              {integration ? 'Update' : 'Connect'} Integration
            </Button>
            <Button variant="outline" type="button" onClick={onClose}>
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
const TestConnectionModal: React.FC<any> = ({ integration, onClose, onSuccess }) => {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const handleTest = async () => {
    setTesting(true);
    try {
      // Simulate test
      await new Promise(resolve => setTimeout(resolve, 2000));
      setTestResult({
        success: true,
        message: 'Connection successful',
        responseTime: '245ms',
        dataPoints: 42
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Connection failed',
        error: 'Authentication failed'
      });
    } finally {
      setTesting(false);
    }
  };
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-md w-full">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Test Connection</h2>
            <Button variant="ghost" size="small" onClick={onClose} icon={<X className="w-4 h-4" />} />
          </div>
        </div>
        <div className="p-6">
          <div className="mb-4">
            <p className="text-sm text-gray-600">Testing connection to:</p>
            <p className="font-medium text-gray-900">{integration.name}</p>
          </div>
          {!testResult && (
            <Button onClick={handleTest} disabled={testing} loading={testing} className="w-full">
              {testing ? 'Testing...' : 'Test Connection'}
            </Button>
          )}
          {testResult && (
            <div className={`p-4 rounded-lg ${
              testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
            }`}>
              <div className="flex items-center space-x-2 mb-2">
                {testResult.success ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-500" />
                )}
                <span className={`font-medium ${
                  testResult.success ? 'text-green-700' : 'text-red-700'
                }`}>
                  {testResult.message}
                </span>
              </div>
              {testResult.success && (
                <div className="space-y-1 text-sm text-green-600">
                  <p>Response time: {testResult.responseTime}</p>
                  <p>Data points processed: {testResult.dataPoints}</p>
                </div>
              )}
              {testResult.error && (
                <p className="text-sm text-red-600">{testResult.error}</p>
              )}
            </div>
          )}
          {testResult && (
            <div className="mt-4 flex gap-3">
              {testResult.success ? (
                <Button onClick={onSuccess} className="flex-1">
                  Save Configuration
                </Button>
              ) : (
                <Button onClick={() => setTestResult(null)} variant="outline" className="flex-1">
                  Try Again
                </Button>
              )}
              <Button variant="outline" onClick={onClose}>
                Close
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
// Mock data
const mockIntegrations = async (): Promise<Integration[]> => {
  return [
    {
      id: 'integration-1',
      name: 'Slack Workspace',
      type: 'slack',
      category: 'communication',
      description: 'Send compliance notifications and updates to Slack channels',
      status: 'connected',
      icon: <Slack className="w-6 h-6" />,
      version: '2.1.0',
      lastSync: '2024-03-12T10:30:00Z',
      configuration: {
        apiKey: 'xoxp-***',
        webhookUrl: 'https://hooks.slack.com/***',
        channelId: '#compliance',
        mapping: { 'compliance_alert': '#alerts', 'training_reminder': '#training' },
        settings: {
          autoMention: true,
          threadReplies: false
        }
      },
      webhookEndpoints: [
        {
          id: 'webhook-1',
          url: 'https://hooks.slack.com/services/ABC123',
          events: ['compliance_alert', 'training_reminder'],
          secret: 'slack-secret-123',
          active: true,
          totalTriggers: 245,
          lastTriggered: '2024-03-12T09:15:00Z'
        }
      ],
      syncSchedule: {
        enabled: true,
        frequency: 'realtime'
      },
      statistics: {
        totalSyncs: 1523,
        successfulSyncs: 1498,
        failedSyncs: 25,
        dataPointsProcessed: 45678,
        lastDayActivity: 67
      },
      permissions: ['send_messages', 'read_channels'],
      tags: ['notifications', 'team', 'real-time'],
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-03-01T14:30:00Z',
      createdBy: 'IT Team'
    },
    {
      id: 'integration-2',
      name: 'Microsoft Teams',
      type: 'teams',
      category: 'communication',
      description: 'Integration with Microsoft Teams for compliance communication',
      status: 'error',
      icon: <MessageSquare className="w-6 h-6" />,
      version: '1.8.0',
      lastSync: '2024-03-12T08:45:00Z',
      lastError: 'Authentication token expired',
      configuration: {
        apiKey: 'teams-api-key',
        teamId: 'team-abc123',
        mapping: { 'urgent': 'compliance-urgent' },
        settings: {
          autoReply: false,
          mentionChannel: true
        }
      },
      webhookEndpoints: [],
      statistics: {
        totalSyncs: 892,
        successfulSyncs: 856,
        failedSyncs: 36,
        dataPointsProcessed: 12345,
        lastDayActivity: 23
      },
      permissions: ['send_messages'],
      tags: ['microsoft', 'office365'],
      createdAt: '2024-02-01T09:00:00Z',
      updatedAt: '2024-03-10T16:20:00Z',
      createdBy: 'IT Team'
    },
    {
      id: 'integration-3',
      name: 'Email Notifications',
      type: 'email',
      category: 'communication',
      description: 'Automated email notifications for compliance events',
      status: 'connected',
      icon: <Mail className="w-6 h-6" />,
      version: '1.5.0',
      lastSync: '2024-03-12T11:00:00Z',
      configuration: {
        emailSettings: {
          fromAddress: 'compliance@company.com',
          replyTo: 'support@company.com',
          template: 'default'
        },
        mapping: {
          compliance_alert: 'compliance',
          training_reminder: 'training'
        },
        settings: {
          retryAttempts: 3,
          batchSize: 100
        }
      },
      webhookEndpoints: [
        {
          id: 'webhook-2',
          url: 'https://api.company.com/email-webhook',
          events: ['training_overdue', 'compliance_violation'],
          secret: 'email-secret-456',
          active: true,
          totalTriggers: 156,
          lastTriggered: '2024-03-12T10:30:00Z'
        }
      ],
      statistics: {
        totalSyncs: 2341,
        successfulSyncs: 2321,
        failedSyncs: 20,
        dataPointsProcessed: 56789,
        lastDayActivity: 89
      },
      permissions: ['send_emails'],
      tags: ['email', 'notifications', 'automated'],
      createdAt: '2024-01-01T08:00:00Z',
      updatedAt: '2024-02-15T11:45:00Z',
      createdBy: 'Compliance Team'
    }
  ];
};