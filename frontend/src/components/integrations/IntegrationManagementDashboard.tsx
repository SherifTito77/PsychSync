// frontend/src/components/integrations/IntegrationManagementDashboard.tsx
/**
 * Integration Management Dashboard
 * Allows administrators to configure and monitor corporate data source integrations
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/Badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/Select';
import corporateIntegrationService from '@/services/corporateIntegrationService';
import {
  DataSourceType,
  IntegrationResponse,
  OrganizationIntegrations,
  IntegrationHealthMetrics,
  SyncStatus
} from '@/types/corporateIntegrations';

const DATA_SOURCE_NAMES: Record<DataSourceType, string> = {
  [DataSourceType.EMAIL_METADATA]: 'Email Metadata',
  [DataSourceType.SLACK_MESSAGES]: 'Slack Messages',
  [DataSourceType.TEAMS_MESSAGES]: 'Microsoft Teams',
  [DataSourceType.ZOOM_TRANSCRIPTS]: 'Zoom Transcripts',
  [DataSourceType.CALENDAR_EVENTS]: 'Calendar Events',
  [DataSourceType.JIRA_ACTIVITY]: 'Jira Activity',
  [DataSourceType.GITHUB_COMMITS]: 'GitHub Commits',
  [DataSourceType.CONFLUENCE_EDITS]: 'Confluence Edits',
  [DataSourceType.ASANA_TASKS]: 'Asana Tasks',
  [DataSourceType.MONDAY_PROJECTS]: 'Monday Projects',
  [DataSourceType.WORKDAY_DATA]: 'Workday HR',
  [DataSourceType.BAMBOO_HR]: 'BambooHR',
  [DataSourceType.ADP_ATTENDANCE]: 'ADP Attendance',
  [DataSourceType.TIME_TRACKING]: 'Time Tracking',
  [DataSourceType.PTO_REQUESTS]: 'PTO Requests',
  [DataSourceType.PERFORMANCE_REVIEWS]: 'Performance Reviews',
  [DataSourceType.PULSE_SURVEYS]: 'Pulse Surveys',
  [DataSourceType.ENGAGEMENT_SURVEYS]: 'Engagement Surveys',
  [DataSourceType.EXIT_INTERVIEWS]: 'Exit Interviews',
  [DataSourceType.ONE_ON_ONE_NOTES]: '1:1 Notes',
  [DataSourceType.WEARABLE_DATA]: 'Wearable Data',
  [DataSourceType.WELLNESS_APP_DATA]: 'Wellness Apps',
  [DataSourceType.MENTAL_HEALTH_CHECKS]: 'Mental Health Checks',
  [DataSourceType.VPN_LOGS]: 'VPN Logs',
  [DataSourceType.BADGE_SWIPES]: 'Badge Swipes',
  [DataSourceType.SYSTEM_LOGIN_TIMES]: 'System Login Times',
  [DataSourceType.APPLICATION_USAGE]: 'Application Usage',
  [DataSourceType.BONUS_DATA]: 'Bonus Data',
  [DataSourceType.PROMOTION_DATA]: 'Promotion Data',
  [DataSourceType.COMPENSATION_CHANGES]: 'Compensation Changes',
  [DataSourceType.TRAINING_COMPLETIONS]: 'Training Completions',
  [DataSourceType.CERTIFICATION_DATA]: 'Certification Data',
  [DataSourceType.SKILL_ASSESSMENTS]: 'Skill Assessments'
};

const STATUS_COLORS: Record<SyncStatus, string> = {
  [SyncStatus.ACTIVE]: 'bg-green-100 text-green-800',
  [SyncStatus.PAUSED]: 'bg-yellow-100 text-yellow-800',
  [SyncStatus.ERROR]: 'bg-red-100 text-red-800',
  [SyncStatus.PENDING]: 'bg-blue-100 text-blue-800',
  [SyncStatus.DISABLED]: 'bg-gray-100 text-gray-800'
};

interface IntegrationManagementDashboardProps {
  organizationId: number;
  organizationSize: number;
}

export const IntegrationManagementDashboard: React.FC<IntegrationManagementDashboardProps> = ({
  organizationId,
  organizationSize
}) => {
  const [integrations, setIntegrations] = useState<OrganizationIntegrations | null>(null);
  const [healthMetrics, setHealthMetrics] = useState<IntegrationHealthMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [syncing, setSyncing] = useState<Set<DataSourceType>>(new Set());

  useEffect(() => {
    loadData();
  }, [organizationId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [integrationsData, healthData] = await Promise.all([
        corporateIntegrationService.getOrganizationIntegrations(),
        corporateIntegrationService.getHealthMetrics()
      ]);
      setIntegrations(integrationsData);
      setHealthMetrics(healthData);
    } catch (error) {
      console.error('Failed to load integrations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleIntegration = async (sourceType: DataSourceType) => {
    try {
      const integration = integrations!.integrations.find(
        (i) => i.config.source_type === sourceType
      );
      if (integration) {
        await corporateIntegrationService.toggleIntegration(
          sourceType,
          !integration.config.enabled
        );
        await loadData();
      }
    } catch (error) {
      console.error('Failed to toggle integration:', error);
    }
  };

  const handleSyncIntegration = async (sourceType: DataSourceType) => {
    try {
      setSyncing((prev) => new Set(prev).add(sourceType));
      await corporateIntegrationService.syncIntegration(sourceType);
      await loadData();
    } catch (error) {
      console.error('Failed to sync integration:', error);
    } finally {
      setSyncing((prev) => {
        const newSet = new Set(prev);
        newSet.delete(sourceType);
        return newSet;
      });
    }
  };

  const handleBulkSetup = async () => {
    try {
      setLoading(true);
      await corporateIntegrationService.setupBulkIntegrations({
        organization_size: organizationSize,
        privacy_preference: 'balanced',
        auto_enable_recommended: true
      });
      await loadData();
    } catch (error) {
      console.error('Failed to setup integrations:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredIntegrations = integrations?.integrations.filter((integration) => {
    const matchesCategory = filterCategory === 'all' || true; // TODO: Add category mapping
    const matchesStatus = filterStatus === 'all' || integration.status.status === filterStatus;
    return matchesCategory && matchesStatus;
  }) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Corporate Data Integrations</h2>
          <p className="text-gray-600 mt-1">
            Manage data source connections for behavioral analysis
          </p>
        </div>
        <Button onClick={handleBulkSetup} variant="default">
          Setup Recommended Integrations
        </Button>
      </div>

      {/* Health Metrics */}
      {healthMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Total Integrations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{healthMetrics.total_integrations}</div>
              <p className="text-xs text-gray-500 mt-1">
                {healthMetrics.active_integrations} active
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Total Data Points
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {healthMetrics.total_data_points.toLocaleString()}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {healthMetrics.last_24h_ingestion_count} in last 24h
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Sync Health
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {Math.round(healthMetrics.data_quality_score * 100)}%
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {healthMetrics.error_integrations} errors
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Avg Sync Latency
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {Math.round(healthMetrics.avg_sync_latency_minutes)}m
              </div>
              <p className="text-xs text-gray-500 mt-1">Across all integrations</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4">
        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Filter by category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="communication">Communication</SelectItem>
            <SelectItem value="productivity">Productivity</SelectItem>
            <SelectItem value="hr">HR Systems</SelectItem>
            <SelectItem value="wellness">Wellness</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="paused">Paused</SelectItem>
            <SelectItem value="error">Error</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="disabled">Disabled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Integrations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredIntegrations.map((integration) => (
          <Card key={integration.config.source_type} className="hover:shadow-lg transition">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <CardTitle className="text-lg">
                    {DATA_SOURCE_NAMES[integration.config.source_type]}
                  </CardTitle>
                  <CardDescription className="mt-1">
                    {integration.behavioral_signals.length} behavioral signals available
                  </CardDescription>
                </div>
                <Badge className={STATUS_COLORS[integration.status.status]}>
                  {integration.status.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Stats */}
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-600">Data Points:</span>
                  <span className="ml-2 font-medium">{integration.data_points_count.toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-gray-600">Health:</span>
                  <span className="ml-2 font-medium">
                    {Math.round(integration.status.health_score * 100)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Sync:</span>
                  <span className="ml-2 font-medium">{integration.config.sync_frequency_hours}h</span>
                </div>
                <div>
                  <span className="text-gray-600">Retention:</span>
                  <span className="ml-2 font-medium">{integration.config.data_retention_days}d</span>
                </div>
              </div>

              {/* Last Sync */}
              {integration.status.last_sync && (
                <div className="text-xs text-gray-500">
                  Last synced: {new Date(integration.status.last_sync).toLocaleString()}
                </div>
              )}

              {/* Privacy Badge */}
              <Badge variant="outline" className="w-full justify-center">
                {integration.config.privacy_level.replace('_', ' ')}
                {integration.config.requires_consent && ' • Consent Required'}
              </Badge>

              {/* Actions */}
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant={integration.config.enabled ? 'outline' : 'default'}
                  className="flex-1"
                  onClick={() => handleToggleIntegration(integration.config.source_type)}
                >
                  {integration.config.enabled ? 'Disable' : 'Enable'}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1"
                  onClick={() => handleSyncIntegration(integration.config.source_type)}
                  disabled={!integration.config.enabled || syncing.has(integration.config.source_type)}
                >
                  {syncing.has(integration.config.source_type) ? 'Syncing...' : 'Sync Now'}
                </Button>
              </div>

              {/* Error Message */}
              {integration.status.error_message && (
                <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
                  {integration.status.error_message}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recommendations */}
      {integrations?.recommendations && integrations.recommendations.length > 0 && (
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader>
            <CardTitle className="text-blue-900">Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {integrations.recommendations.map((recommendation, index) => (
                <li key={index} className="flex items-start text-sm text-blue-800">
                  <span className="mr-2">•</span>
                  <span>{recommendation}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default IntegrationManagementDashboard;
