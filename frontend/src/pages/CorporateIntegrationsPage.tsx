/**
 * Corporate Integrations Main Page
 * Hub for managing all corporate data source integrations
 */

import React, { useState, useEffect } from 'react';
import { CorporateIntegrationsLogo, CorporateIntegrationsBadge } from '../components/integrations/CorporateIntegrationsIcon';
import { getDataSourceIcon, getCategoryIcon, getCategoryColor } from '../components/integrations/IntegrationIcons';
import IconShowcase from '../components/integrations/IconShowcase';

interface DataSource {
  type: string;
  name: string;
  description: string;
  category: string;
  priority: string;
  enabled: boolean;
  status: 'active' | 'disabled' | 'error' | 'syncing';
  health_score: number;
  last_sync?: string;
  signals_count: number;
}

const mockDataSources: DataSource[] = [
  {
    type: 'email_metadata',
    name: 'Email Metadata',
    description: 'Extract behavioral signals from email (Gmail/Outlook)',
    category: 'communication',
    priority: 'Must Have (MVP)',
    enabled: true,
    status: 'active',
    health_score: 0.95,
    last_sync: '2 hours ago',
    signals_count: 17
  },
  {
    type: 'slack_messages',
    name: 'Slack Messages',
    description: 'Analyze Slack communication patterns',
    category: 'communication',
    priority: 'High Priority',
    enabled: true,
    status: 'active',
    health_score: 0.92,
    last_sync: '1 hour ago',
    signals_count: 18
  },
  {
    type: 'calendar_events',
    name: 'Calendar Events',
    description: 'Google/Outlook calendar integration',
    category: 'productivity',
    priority: 'Must Have (MVP)',
    enabled: true,
    status: 'syncing',
    health_score: 0.88,
    signals_count: 20
  },
  {
    type: 'jira_activity',
    name: 'Jira Activity',
    description: 'Track Jira tickets and workflow',
    category: 'productivity',
    priority: 'Medium Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 10
  },
  {
    type: 'pulse_surveys',
    name: 'Pulse Surveys',
    description: 'Employee feedback surveys',
    category: 'other',
    priority: 'Must Have (MVP)',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 10
  },
  {
    type: 'wearable_data',
    name: 'Wearable Data',
    description: 'Health & fitness trackers',
    category: 'other',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 10
  }
];

const CorporateIntegrationsPage: React.FC = () => {
  const [dataSources, setDataSources] = useState<DataSource[]>(mockDataSources);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showIcons, setShowIcons] = useState(false);

  const categories = ['all', 'communication', 'productivity', 'hr', 'other'];

  const filteredSources = selectedCategory === 'all'
    ? dataSources
    : dataSources.filter(source => source.category === selectedCategory);

  const stats = {
    total: dataSources.length,
    active: dataSources.filter(s => s.status === 'active').length,
    syncing: dataSources.filter(s => s.status === 'syncing').length,
    totalSignals: dataSources.reduce((sum, s) => sum + (s.enabled ? s.signals_count : 0), 0)
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <CorporateIntegrationsLogo showText={true} />
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowIcons(!showIcons)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                {showIcons ? '📊 Hide Icons' : '🎨 View Icons'}
              </button>
              <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
                ➕ Add Integration
              </button>
            </div>
          </div>
        </div>
      </div>

      {showIcons ? (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <IconShowcase />
        </div>
      ) : (
        <>
          {/* Stats Cards */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Sources</p>
                    <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
                  </div>
                  <div className="p-3 bg-blue-100 rounded-lg text-blue-600 text-2xl">
                    📦
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Active</p>
                    <p className="text-3xl font-bold text-green-600">{stats.active}</p>
                  </div>
                  <div className="p-3 bg-green-100 rounded-lg text-green-600 text-2xl">
                    ✅
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Syncing</p>
                    <p className="text-3xl font-bold text-blue-600">{stats.syncing}</p>
                  </div>
                  <div className="p-3 bg-blue-100 rounded-lg text-blue-600 text-2xl">
                    🔄
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Signals</p>
                    <p className="text-3xl font-bold text-purple-600">{stats.totalSignals}</p>
                  </div>
                  <div className="p-3 bg-purple-100 rounded-lg text-purple-600 text-2xl">
                    📊
                  </div>
                </div>
              </div>
            </div>

            {/* Category Filter */}
            <div className="mt-8">
              <div className="flex items-center gap-2 overflow-x-auto pb-2">
                {categories.map((category) => (
                  <button
                    key={category}
                    onClick={() => setSelectedCategory(category)}
                    className={`px-4 py-2 rounded-lg font-medium capitalize transition-colors whitespace-nowrap ${
                      selectedCategory === category
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                    }`}
                  >
                    {category === 'all' ? '🔗 All Sources' : category}
                  </button>
                ))}
              </div>
            </div>

            {/* Data Sources Grid */}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredSources.map((source) => {
                const DataSourceIcon = getDataSourceIcon(source.type as any);
                const CategoryIcon = getCategoryIcon(source.category as any);
                const categoryColor = getCategoryColor(source.category as any);

                const statusColors = {
                  active: 'bg-green-100 text-green-700',
                  syncing: 'bg-blue-100 text-blue-700',
                  disabled: 'bg-gray-100 text-gray-700',
                  error: 'bg-red-100 text-red-700'
                };

                return (
                  <div
                    key={source.type}
                    className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${categoryColor} bg-opacity-10`}>
                          <DataSourceIcon className="w-6 h-6" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">{source.name}</h3>
                          <p className="text-sm text-gray-500 capitalize">{source.category}</p>
                        </div>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[source.status]}`}>
                        {source.status}
                      </span>
                    </div>

                    <p className="text-sm text-gray-600 mb-4">{source.description}</p>

                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-1">
                        <CategoryIcon className="w-4 h-4 text-gray-500" />
                        <span className="text-gray-500">{source.signals_count} signals</span>
                      </div>
                      {source.health_score > 0 && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-500">Health:</span>
                          <span className="font-medium text-green-600">
                            {Math.round(source.health_score * 100)}%
                          </span>
                        </div>
                      )}
                    </div>

                    {source.last_sync && (
                      <div className="mt-2 text-xs text-gray-500">
                        Last sync: {source.last_sync}
                      </div>
                    )}

                    <div className="mt-4 pt-4 border-t border-gray-200 flex gap-2">
                      <button className="flex-1 px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors">
                        Configure
                      </button>
                      <button className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                        Sync
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Empty State */}
            {filteredSources.length === 0 && (
              <div className="mt-12 text-center py-12">
                <div className="text-6xl mb-4">📭</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No integrations found</h3>
                <p className="text-gray-600 mb-6">
                  {selectedCategory === 'all'
                    ? 'Get started by adding your first data source integration'
                    : `No ${selectedCategory} integrations found`}
                </p>
                <button className="px-6 py-3 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
                  Browse Available Integrations
                </button>
              </div>
            )}
          </div>
        </>
      )}

      {/* Footer Info */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-blue-100 rounded-lg text-blue-600 text-2xl">
              🔗
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                30+ Data Sources Available
              </h3>
              <p className="text-gray-700 mb-4">
                Connect your corporate data sources to extract 55+ behavioral signals across email, calendar,
                Slack, Jira, GitHub, HR systems, and more. All integrations are privacy-first with
                metadata-only extraction.
              </p>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span>✅ GDPR compliant</span>
                <span>✅ Employee consent required</span>
                <span>✅ Configurable retention</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CorporateIntegrationsPage;
