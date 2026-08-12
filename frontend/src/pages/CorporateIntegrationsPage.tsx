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
  // Communication Tools
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
    description: 'Analyze Slack communication patterns and sentiment',
    category: 'communication',
    priority: 'High Priority',
    enabled: true,
    status: 'active',
    health_score: 0.92,
    last_sync: '1 hour ago',
    signals_count: 18
  },
  {
    type: 'teams_messages',
    name: 'Microsoft Teams',
    description: 'Analyze Teams communication, chat, and collaboration',
    category: 'communication',
    priority: 'High Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 15
  },
  {
    type: 'zoom_transcripts',
    name: 'Zoom',
    description: 'Video meeting transcripts and participation analytics',
    category: 'communication',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 8
  },

  // Productivity & Project Management
  {
    type: 'calendar_events',
    name: 'Calendar Events',
    description: 'Google/Outlook calendar integration for meeting patterns',
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
    description: 'Track Jira tickets, sprints, and workflow velocity',
    category: 'productivity',
    priority: 'Medium Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 10
  },
  {
    type: 'github_commits',
    name: 'GitHub',
    description: 'Track development activity, PRs, and team collaboration',
    category: 'productivity',
    priority: 'Medium Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 12
  },
  {
    type: 'asana_tasks',
    name: 'Asana',
    description: 'Project management and task completion tracking',
    category: 'productivity',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 9
  },
  {
    type: 'trello_boards',
    name: 'Trello',
    description: 'Kanban board activity and workflow analytics',
    category: 'productivity',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 7
  },
  {
    type: 'monday_projects',
    name: 'Monday.com',
    description: 'Project management and team productivity insights',
    category: 'productivity',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 8
  },
  {
    type: 'confluence_edits',
    name: 'Confluence',
    description: 'Documentation collaboration and knowledge sharing',
    category: 'productivity',
    priority: 'Low Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 5
  },
  {
    type: 'notion_pages',
    name: 'Notion',
    description: 'Workspace collaboration and documentation analytics',
    category: 'productivity',
    priority: 'Low Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 6
  },

  // HR & Employee Data
  {
    type: 'workday_data',
    name: 'Workday',
    description: 'HRIS data for employee lifecycle and performance',
    category: 'hr',
    priority: 'Must Have (MVP)',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 25
  },
  {
    type: 'bamboo_hr',
    name: 'BambooHR',
    description: 'HR management and employee performance data',
    category: 'hr',
    priority: 'High Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 22
  },
  {
    type: 'adp_attendance',
    name: 'ADP',
    description: 'Payroll, attendance, and workforce analytics',
    category: 'hr',
    priority: 'High Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 20
  },
  {
    type: 'lever_recruiting',
    name: 'Lever',
    description: 'Recruiting pipeline and hiring analytics',
    category: 'hr',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 12
  },
  {
    type: 'greenhouse_recruiting',
    name: 'Greenhouse',
    description: 'Applicant tracking system and hiring insights',
    category: 'hr',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 11
  },

  // Sales & CRM
  {
    type: 'hubspot_crm',
    name: 'HubSpot',
    description: 'CRM data and sales team performance analytics',
    category: 'sales',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 10
  },
  {
    type: 'salesforce_crm',
    name: 'Salesforce',
    description: 'Enterprise CRM and sales pipeline analytics',
    category: 'sales',
    priority: 'Medium Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 15
  },
  {
    type: 'zendesk_support',
    name: 'Zendesk',
    description: 'Customer support tickets and team performance',
    category: 'sales',
    priority: 'Low Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 8
  },
  {
    type: 'intercom_communication',
    name: 'Intercom',
    description: 'Customer messaging and support analytics',
    category: 'sales',
    priority: 'Low Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 7
  },

  // File Storage & Collaboration
  {
    type: 'google_drive',
    name: 'Google Drive',
    description: 'Document collaboration and file sharing patterns',
    category: 'storage',
    priority: 'Medium Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 9
  },
  {
    type: 'dropbox_files',
    name: 'Dropbox',
    description: 'File sharing and collaboration analytics',
    category: 'storage',
    priority: 'Low Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 6
  },
  {
    type: 'onedrive_files',
    name: 'OneDrive',
    description: 'Microsoft 365 file collaboration insights',
    category: 'storage',
    priority: 'Low Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 7
  },

  // Monitoring & Analytics
  {
    type: 'pagerduty_incidents',
    name: 'PagerDuty',
    description: 'Incident response and on-call rotation analytics',
    category: 'monitoring',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 5
  },
  {
    type: 'datadog_metrics',
    name: 'Datadog',
    description: 'Application performance and system monitoring',
    category: 'monitoring',
    priority: 'Low Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 10
  },

  // Billing & Finance
  {
    type: 'stripe_payments',
    name: 'Stripe',
    description: 'Payment processing and subscription analytics',
    category: 'billing',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 5
  },

  // Employee Engagement & Wellness
  {
    type: 'pulse_surveys',
    name: 'Pulse Surveys',
    description: 'Employee feedback and sentiment surveys',
    category: 'wellness',
    priority: 'Must Have (MVP)',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 10
  },
  {
    type: 'engagement_surveys',
    name: 'Engagement Surveys',
    description: 'Employee engagement and satisfaction metrics',
    category: 'wellness',
    priority: 'High Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 12
  },
  {
    type: 'exit_interviews',
    name: 'Exit Interviews',
    description: 'Turnover insights and exit feedback',
    category: 'wellness',
    priority: 'Medium Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 8
  },
  {
    type: 'one_on_one_notes',
    name: '1:1 Notes',
    description: 'Manager-employee meeting notes and feedback',
    category: 'wellness',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 7
  },

  // Health & Biometric
  {
    type: 'wearable_data',
    name: 'Wearable Devices',
    description: 'Fitbit, Apple Watch, and health tracker data',
    category: 'wellness',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 15
  },
  {
    type: 'wellness_apps',
    name: 'Wellness Apps',
    description: 'Headspace, Calm, and mental wellness app data',
    category: 'wellness',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 10
  },
  {
    type: 'mental_health_checks',
    name: 'Mental Health Checks',
    description: 'Regular mental wellness assessments',
    category: 'wellness',
    priority: 'Must Have (MVP)',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 8
  },

  // System & Security
  {
    type: 'vpn_logs',
    name: 'VPN Logs',
    description: 'Remote work patterns and access logs',
    category: 'security',
    priority: 'Medium Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 12
  },
  {
    type: 'badge_swipes',
    name: 'Badge Swipes',
    description: 'Office attendance and physical access patterns',
    category: 'security',
    priority: 'Medium Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 10
  },
  {
    type: 'system_logins',
    name: 'System Logins',
    description: 'Login times and session patterns',
    category: 'security',
    priority: 'Low Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 8
  },

  // Performance & Development
  {
    type: 'performance_reviews',
    name: 'Performance Reviews',
    description: 'Employee performance ratings and feedback',
    category: 'hr',
    priority: 'High Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 10
  },
  {
    type: 'training_completions',
    name: 'Training & Development',
    description: 'Learning management system and skill development',
    category: 'hr',
    priority: 'Medium Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 9
  },
  {
    type: 'certification_data',
    name: 'Certifications',
    description: 'Professional certifications and credentials',
    category: 'hr',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 6
  },
  {
    type: 'skill_assessments',
    name: 'Skill Assessments',
    description: 'Employee skills and competency tracking',
    category: 'hr',
    priority: 'Medium Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 11
  },

  // Compensation & Benefits
  {
    type: 'bonus_data',
    name: 'Bonus Data',
    description: 'Compensation and bonus analytics',
    category: 'hr',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 7
  },
  {
    type: 'promotion_data',
    name: 'Promotions',
    description: 'Career progression and promotion history',
    category: 'hr',
    priority: 'Medium Priority',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 8
  },
  {
    type: 'compensation_changes',
    name: 'Compensation History',
    description: 'Salary and compensation changes over time',
    category: 'hr',
    priority: 'Nice to Have',
    enabled: false,
    status: 'disabled',
    health_score: 0.0,
    signals_count: 9
  }
];

const CorporateIntegrationsPage: React.FC = () => {
  const [dataSources, setDataSources] = useState<DataSource[]>(mockDataSources);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Load real integration state from API; merge with static mock for description/priority
  React.useEffect(() => {
    const token = localStorage.getItem('auth_token');
    Promise.all([
      fetch('/api/v1/integrations/corporate/available', {
        headers: { Authorization: `Bearer ${token}` },
      }).then(r => r.ok ? r.json() : []),
      fetch('/api/v1/integrations/corporate/organization', {
        headers: { Authorization: `Bearer ${token}` },
      }).then(r => r.ok ? r.json() : null),
    ])
      .then(([available, orgData]) => {
        if (!orgData?.integrations) return;
        const metaMap: Record<string, { description: string; category: string; priority: string }> =
          Object.fromEntries((available as any[]).map((s: any) => [s.type, s]));
        const merged: DataSource[] = orgData.integrations.map((int: any) => {
          const t = int.config?.source_type?.value ?? int.config?.source_type ?? '';
          const meta = metaMap[t] ?? {};
          const mock = mockDataSources.find(m => m.type === t);
          return {
            type: t,
            name: t.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
            description: meta.description ?? mock?.description ?? '',
            category: meta.category ?? mock?.category ?? 'other',
            priority: meta.priority ?? mock?.priority ?? 'Medium Priority',
            enabled: int.status?.status === 'active',
            status: int.status?.status ?? 'disabled',
            health_score: int.status?.health_score ?? 0,
            last_sync: int.status?.last_sync ?? undefined,
            signals_count: int.behavioral_signals?.length ?? 0,
          };
        });
        if (merged.length > 0) setDataSources(merged);
      })
      .catch(() => {/* keep mock fallback */});
  }, []);
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showIcons, setShowIcons] = useState(false);

  const categories = ['all', 'communication', 'productivity', 'hr', 'sales', 'storage', 'monitoring', 'billing', 'wellness', 'security'];
  const priorities = ['all', 'Must Have (MVP)', 'High Priority', 'Medium Priority', 'Nice to Have', 'Low Priority'];

  const filteredSources = dataSources.filter(source => {
    const matchesCategory = selectedCategory === 'all' || source.category === selectedCategory;
    const matchesPriority = selectedPriority === 'all' || source.priority === selectedPriority;
    const matchesSearch = searchQuery === '' ||
      source.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      source.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      source.type.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesPriority && matchesSearch;
  });

  const stats = {
    total: dataSources.length,
    active: dataSources.filter(s => s.status === 'active').length,
    syncing: dataSources.filter(s => s.status === 'syncing').length,
    disabled: dataSources.filter(s => s.status === 'disabled').length,
    totalSignals: dataSources.reduce((sum, s) => sum + (s.enabled ? s.signals_count : 0), 0),
    avgHealth: dataSources.filter(s => s.enabled).reduce((sum, s) => sum + s.health_score, 0) / (dataSources.filter(s => s.enabled).length || 1)
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
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
                    <p className="text-sm font-medium text-gray-600">Disabled</p>
                    <p className="text-3xl font-bold text-gray-600">{stats.disabled}</p>
                  </div>
                  <div className="p-3 bg-gray-100 rounded-lg text-gray-600 text-2xl">
                    ⏸️
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

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg Health</p>
                    <p className="text-3xl font-bold text-green-600">{Math.round(stats.avgHealth * 100)}%</p>
                  </div>
                  <div className="p-3 bg-green-100 rounded-lg text-green-600 text-2xl">
                    ❤️
                  </div>
                </div>
              </div>
            </div>

            {/* Search and Filters */}
            <div className="mt-8 space-y-4">
              {/* Search Bar */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="🔍 Search integrations by name, description, or type..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-3 pl-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Priority Filter */}
              <div className="flex items-center gap-2 overflow-x-auto pb-2">
                <span className="text-sm font-medium text-gray-700 mr-2">Priority:</span>
                {priorities.map((priority) => (
                  <button
                    key={priority}
                    onClick={() => setSelectedPriority(priority)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                      selectedPriority === priority
                        ? 'bg-orange-600 text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                    }`}
                  >
                    {priority === 'all' ? 'All Priorities' : priority}
                  </button>
                ))}
              </div>

            {/* Category Filter */}
            <div className="">
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
            <div className="mt-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">
                  {filteredSources.length === dataSources.length ? 'All Integrations' : 'Filtered Results'}
                </h2>
                <span className="text-sm text-gray-600">
                  Showing {filteredSources.length} of {dataSources.length} integrations
                </span>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
                      <div className="flex flex-col gap-2 items-end">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[source.status]}`}>
                          {source.status}
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          source.priority === 'Must Have (MVP)' ? 'bg-red-100 text-red-700' :
                          source.priority === 'High Priority' ? 'bg-orange-100 text-orange-700' :
                          source.priority === 'Medium Priority' ? 'bg-yellow-100 text-yellow-700' :
                          source.priority === 'Nice to Have' ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {source.priority}
                        </span>
                      </div>
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
