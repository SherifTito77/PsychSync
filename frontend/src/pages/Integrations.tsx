import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/layout/DashboardLayout';

interface Integration {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: 'communication' | 'productivity' | 'development' | 'analytics' | 'billing';
  connected: boolean;
  connectedAt?: string;
  config?: {
    webhookUrl?: string;
    apiKey?: string;
    channels?: string[];
    calendars?: string[];
    repositories?: string[];
  };
  features: string[];
  pricing: 'free' | 'premium' | 'enterprise';
  status: 'active' | 'inactive' | 'error';
  lastSync?: string;
}

const Integrations: React.FC = () => {
  const [integrations, setIntegrations] = useState<Integration[]>([
    {
      id: 'slack',
      name: 'Slack',
      description: 'Get real-time notifications and updates in your Slack workspace',
      icon: '💬',
      category: 'communication',
      connected: false,
      features: ['Real-time notifications', 'Team updates', 'Assessment alerts', 'Daily summaries'],
      pricing: 'free',
      status: 'inactive'
    },
    {
      id: 'stripe',
      name: 'Stripe',
      description: 'Manage billing, payments, and subscriptions seamlessly',
      icon: '💳',
      category: 'billing',
      connected: false,
      features: ['Payment processing', 'Subscription management', 'Invoice generation', 'Webhook handling'],
      pricing: 'premium',
      status: 'inactive'
    },
    {
      id: 'google_calendar',
      name: 'Google Calendar',
      description: 'Sync team events, meetings, and assessment schedules',
      icon: '📅',
      category: 'productivity',
      connected: false,
      features: ['Event synchronization', 'Meeting scheduling', 'Assessment reminders', 'Team availability'],
      pricing: 'free',
      status: 'inactive'
    },
    {
      id: 'github',
      name: 'GitHub',
      description: 'Connect development repositories and track team collaboration',
      icon: '🐙',
      category: 'development',
      connected: false,
      features: ['Repository analytics', 'Commit tracking', 'Pull request insights', 'Team performance'],
      pricing: 'free',
      status: 'inactive'
    },
    {
      id: 'jira',
      name: 'Jira',
      description: 'Integrate project management and issue tracking',
      icon: '📋',
      category: 'development',
      connected: false,
      features: ['Issue synchronization', 'Sprint analytics', 'Team velocity tracking', 'Project insights'],
      pricing: 'premium',
      status: 'inactive'
    },
    {
      id: 'microsoft_teams',
      name: 'Microsoft Teams',
      description: 'Collaborate and get notifications within Microsoft Teams',
      icon: '🟢',
      category: 'communication',
      connected: false,
      features: ['Team notifications', 'Chat integration', 'Meeting scheduling', 'File sharing'],
      pricing: 'premium',
      status: 'inactive'
    },
    {
      id: 'hubspot',
      name: 'HubSpot',
      description: 'Sync customer data and sales team insights',
      icon: '🎯',
      category: 'analytics',
      connected: false,
      features: ['Contact synchronization', 'Sales analytics', 'Team performance', 'CRM integration'],
      pricing: 'enterprise',
      status: 'inactive'
    },
    {
      id: 'zoom',
      name: 'Zoom',
      description: 'Schedule and manage video meetings and assessments',
      icon: '📹',
      category: 'productivity',
      connected: false,
      features: ['Meeting scheduling', 'Recording management', 'Team meetings', 'Webinar support'],
      pricing: 'premium',
      status: 'inactive'
    }
  ]);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [configModal, setConfigModal] = useState<{ open: boolean; integration: Integration | null }>({
    open: false,
    integration: null
  });

  useEffect(() => {
    loadIntegrations();
  }, []);

  const loadIntegrations = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/integrations');
      if (response.ok) {
        const data = await response.json();
        setIntegrations(prev => prev.map(integration => {
          const connectedIntegration = data.find((d: Integration) => d.id === integration.id);
          return connectedIntegration || integration;
        }));
      }
    } catch (error) {
      console.error('Failed to load integrations:', error);
      showMessage('Failed to load integrations', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showMessage = (text: string, type: 'success' | 'error') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 3000);
  };

  const toggleIntegration = async (integration: Integration) => {
    try {
      setLoading(true);

      if (integration.connected) {
        // Disconnect
        const response = await fetch(`/api/v1/integrations/${integration.id}/disconnect`, {
          method: 'POST'
        });

        if (response.ok) {
          setIntegrations(prev => prev.map(int =>
            int.id === integration.id
              ? { ...int, connected: false, status: 'inactive' as const, config: undefined }
              : int
          ));
          showMessage(`${integration.name} disconnected successfully`, 'success');
        }
      } else {
        // Show configuration modal
        setConfigModal({ open: true, integration });
      }
    } catch (error) {
      console.error('Failed to toggle integration:', error);
      showMessage('Failed to update integration', 'error');
    } finally {
      setLoading(false);
    }
  };

  const connectIntegration = async (config: any) => {
    if (!configModal.integration) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/v1/integrations/${configModal.integration.id}/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        const data = await response.json();
        setIntegrations(prev => prev.map(int =>
          int.id === configModal.integration!.id
            ? {
                ...int,
                connected: true,
                status: 'active' as const,
                config: data.config,
                connectedAt: new Date().toISOString()
              }
            : int
        ));
        showMessage(`${configModal.integration.name} connected successfully`, 'success');
        setConfigModal({ open: false, integration: null });
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Connection failed');
      }
    } catch (error: any) {
      console.error('Failed to connect integration:', error);
      showMessage(error.message || 'Failed to connect integration', 'error');
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (integrationId: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/integrations/${integrationId}/test`, {
        method: 'POST'
      });

      if (response.ok) {
        showMessage('Connection test successful', 'success');
      } else {
        throw new Error('Connection test failed');
      }
    } catch (error) {
      showMessage('Connection test failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const categories = [
    { id: 'all', label: 'All Integrations', icon: '🔗' },
    { id: 'communication', label: 'Communication', icon: '💬' },
    { id: 'productivity', label: 'Productivity', icon: '📊' },
    { id: 'development', label: 'Development', icon: '💻' },
    { id: 'analytics', label: 'Analytics', icon: '📈' },
    { id: 'billing', label: 'Billing', icon: '💳' }
  ];

  const filteredIntegrations = integrations.filter(integration => {
    const matchesCategory = selectedCategory === 'all' || integration.category === selectedCategory;
    const matchesSearch = integration.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         integration.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const getPricingBadge = (pricing: string) => {
    const colors = {
      free: 'bg-green-100 text-green-800',
      premium: 'bg-blue-100 text-blue-800',
      enterprise: 'bg-purple-100 text-purple-800'
    };
    return colors[pricing as keyof typeof colors] || colors.free;
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      error: 'bg-red-100 text-red-800'
    };
    return colors[status as keyof typeof colors] || colors.inactive;
  };

  if (loading && !integrations[0].connected) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Integrations</h1>
          <p className="text-gray-600">Connect PsychSync with your favorite tools and services</p>
        </div>

        {/* Message */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}

        {/* Search and Filter */}
        <div className="mb-6 space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search integrations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Category Tabs */}
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  selectedCategory === category.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <span className="mr-2">{category.icon}</span>
                {category.label}
              </button>
            ))}
          </div>
        </div>

        {/* Integration Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredIntegrations.map((integration) => (
            <div
              key={integration.id}
              className={`bg-white rounded-lg shadow-md border-2 transition-all ${
                integration.connected ? 'border-blue-500' : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              {/* Card Header */}
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className="text-4xl mr-3">{integration.icon}</div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{integration.name}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getPricingBadge(integration.pricing)}`}>
                          {integration.pricing}
                        </span>
                        {integration.connected && (
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(integration.status)}`}>
                            {integration.status}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                <p className="text-gray-600 text-sm mb-4">{integration.description}</p>

                {/* Features */}
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Features:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {integration.features.slice(0, 3).map((feature, index) => (
                      <li key={index} className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        {feature}
                      </li>
                    ))}
                    {integration.features.length > 3 && (
                      <li className="text-gray-400">
                        +{integration.features.length - 3} more features
                      </li>
                    )}
                  </ul>
                </div>

                {/* Connection Status */}
                {integration.connected && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-md">
                    <div className="text-sm text-blue-800">
                      <div className="font-medium">Connected</div>
                      {integration.connectedAt && (
                        <div className="text-xs">Connected on {new Date(integration.connectedAt).toLocaleDateString()}</div>
                      )}
                      {integration.lastSync && (
                        <div className="text-xs">Last sync: {new Date(integration.lastSync).toLocaleString()}</div>
                      )}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <button
                    onClick={() => toggleIntegration(integration)}
                    disabled={loading}
                    className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
                      integration.connected
                        ? 'bg-red-600 text-white hover:bg-red-700'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    {integration.connected ? 'Disconnect' : 'Connect'}
                  </button>

                  {integration.connected && (
                    <button
                      onClick={() => testConnection(integration.id)}
                      disabled={loading}
                      className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50"
                    >
                      Test
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Configuration Modal */}
        {configModal.open && configModal.integration && (
          <IntegrationConfigModal
            integration={configModal.integration}
            onClose={() => setConfigModal({ open: false, integration: null })}
            onConnect={connectIntegration}
            loading={loading}
          />
        )}

        {/* Empty State */}
        {filteredIntegrations.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No integrations found</h3>
            <p className="text-gray-600">
              {searchTerm ? 'Try adjusting your search terms' : 'No integrations available in this category'}
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

// Integration Configuration Modal Component
const IntegrationConfigModal: React.FC<{
  integration: Integration;
  onClose: () => void;
  onConnect: (config: any) => void;
  loading: boolean;
}> = ({ integration, onClose, onConnect, loading }) => {
  const [config, setConfig] = useState<any>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onConnect(config);
  };

  const renderConfigFields = () => {
    switch (integration.id) {
      case 'slack':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Slack Workspace URL</label>
              <input
                type="url"
                placeholder="https://your-workspace.slack.com"
                value={config.workspaceUrl || ''}
                onChange={(e) => setConfig({ ...config, workspaceUrl: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Bot Token</label>
              <input
                type="password"
                placeholder="xoxb-your-bot-token"
                value={config.botToken || ''}
                onChange={(e) => setConfig({ ...config, botToken: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Notification Channel</label>
              <input
                type="text"
                placeholder="#team-updates"
                value={config.channel || ''}
                onChange={(e) => setConfig({ ...config, channel: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </>
        );

      case 'stripe':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Stripe Publishable Key</label>
              <input
                type="text"
                placeholder="pk_test_..."
                value={config.publishableKey || ''}
                onChange={(e) => setConfig({ ...config, publishableKey: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Stripe Secret Key</label>
              <input
                type="password"
                placeholder="sk_test_..."
                value={config.secretKey || ''}
                onChange={(e) => setConfig({ ...config, secretKey: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Webhook Secret</label>
              <input
                type="password"
                placeholder="whsec_..."
                value={config.webhookSecret || ''}
                onChange={(e) => setConfig({ ...config, webhookSecret: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </>
        );

      case 'google_calendar':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Google Client ID</label>
              <input
                type="text"
                placeholder="your-google-client-id"
                value={config.clientId || ''}
                onChange={(e) => setConfig({ ...config, clientId: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Calendar ID (optional)</label>
              <input
                type="text"
                placeholder="primary"
                value={config.calendarId || ''}
                onChange={(e) => setConfig({ ...config, calendarId: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </>
        );

      default:
        return (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
            <input
              type="password"
              placeholder="Enter your API key"
              value={config.apiKey || ''}
              onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        );
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <div className="flex items-center mb-4">
          <div className="text-3xl mr-3">{integration.icon}</div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Connect {integration.name}</h3>
            <p className="text-sm text-gray-600">Configure your {integration.name} integration</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {renderConfigFields()}

          <div className="bg-gray-50 p-4 rounded-md">
            <p className="text-sm text-gray-600">
              Need help? Check our{' '}
              <a href="#" className="text-blue-600 hover:underline">integration guide</a>
              {' '}or contact support.
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Connecting...' : 'Connect'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Integrations;