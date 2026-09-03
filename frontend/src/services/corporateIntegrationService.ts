// frontend/src/services/corporateIntegrationService.ts
/**
 * Service for managing corporate data source integrations
 */

import api from './api';
import {
  DataSourceType,
  IntegrationResponse,
  CreateIntegrationRequest,
  UpdateIntegrationRequest,
  SyncIntegrationRequest,
  OrganizationIntegrations,
  BehavioralAnalysisRequest,
  BehavioralInsight,
  IntegrationInsightsReport,
  IntegrationHealthMetrics,
  BulkIntegrationRequest,
  ConsentRecord,
  ApiResponse
} from '@/types/corporateIntegrations';

const BASE_URL = '/integrations/corporate';

/**
 * Get all integrations for the organization
 */
export async function getOrganizationIntegrations(): Promise<OrganizationIntegrations> {
  const response = await api.get<ApiResponse<OrganizationIntegrations>>(`${BASE_URL}/organization`);
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to fetch integrations');
}

/**
 * Get a specific integration by type
 */
export async function getIntegration(
  sourceType: DataSourceType
): Promise<IntegrationResponse> {
  const response = await api.get<ApiResponse<IntegrationResponse>>(
    `${BASE_URL}/${sourceType}`
  );
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to fetch integration');
}

/**
 * Create a new integration
 */
export async function createIntegration(
  request: CreateIntegrationRequest
): Promise<IntegrationResponse> {
  const response = await api.post<ApiResponse<IntegrationResponse>>(
    `${BASE_URL}`,
    request
  );
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to create integration');
}

/**
 * Update an existing integration
 */
export async function updateIntegration(
  sourceType: DataSourceType,
  request: UpdateIntegrationRequest
): Promise<IntegrationResponse> {
  const response = await api.put<ApiResponse<IntegrationResponse>>(
    `${BASE_URL}/${sourceType}`,
    request
  );
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to update integration');
}

/**
 * Delete an integration
 */
export async function deleteIntegration(sourceType: DataSourceType): Promise<void> {
  const response = await api.delete<ApiResponse<void>>(`${BASE_URL}/${sourceType}`);
  if (!response.data.success) {
    throw new Error(response.data.error || 'Failed to delete integration');
  }
}

/**
 * Toggle integration enabled/disabled
 */
export async function toggleIntegration(
  sourceType: DataSourceType,
  enabled: boolean
): Promise<IntegrationResponse> {
  return updateIntegration(sourceType, { enabled });
}

/**
 * Trigger manual sync for an integration
 */
export async function syncIntegration(
  sourceType: DataSourceType,
  options?: SyncIntegrationRequest
): Promise<{ message: string; sync_id: string }> {
  const response = await api.post<ApiResponse<{ message: string; sync_id: string }>>(
    `${BASE_URL}/${sourceType}/sync`,
    options || {}
  );
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to trigger sync');
}

/**
 * Get integration health metrics
 */
export async function getHealthMetrics(): Promise<IntegrationHealthMetrics> {
  const response = await api.get<ApiResponse<IntegrationHealthMetrics>>(
    `${BASE_URL}/health`
  );
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to fetch health metrics');
}

/**
 * Analyze behavioral data across integrations
 */
export async function analyzeBehavioralData(
  request: BehavioralAnalysisRequest
): Promise<BehavioralInsight[]> {
  const response = await api.post<ApiResponse<BehavioralInsight[]>>(
    `${BASE_URL}/analyze`,
    request
  );
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to analyze behavioral data');
}

/**
 * Generate comprehensive insights report
 */
export async function generateInsightsReport(
  dateRange: { start: string; end: string }
): Promise<IntegrationInsightsReport> {
  const response = await api.post<ApiResponse<IntegrationInsightsReport>>(
    `${BASE_URL}/reports/generate`,
    { date_range: dateRange }
  );
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to generate insights report');
}

/**
 * Get latest insights report
 */
export async function getLatestReport(): Promise<IntegrationInsightsReport> {
  const response = await api.get<ApiResponse<IntegrationInsightsReport>>(
    `${BASE_URL}/reports/latest`
  );
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to fetch latest report');
}

/**
 * Bulk setup integrations based on organization size
 */
export async function setupBulkIntegrations(
  request: BulkIntegrationRequest
): Promise<{ created: number; integrations: IntegrationResponse[] }> {
  const response = await api.post<
    ApiResponse<{ created: number; integrations: IntegrationResponse[] }>
  >(`${BASE_URL}/bulk-setup`, request);
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to setup integrations');
}

/**
 * Get consent records for employees
 */
export async function getConsentRecords(employeeId?: number): Promise<ConsentRecord[]> {
  const url = employeeId
    ? `${BASE_URL}/consent?employee_id=${employeeId}`
    : `${BASE_URL}/consent`;
  const response = await api.get<ApiResponse<ConsentRecord[]>>(url);
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to fetch consent records');
}

/**
 * Grant consent for data collection
 */
export async function grantConsent(
  sourceTypes: DataSourceType[]
): Promise<ConsentRecord> {
  const response = await api.post<ApiResponse<ConsentRecord>>(
    `${BASE_URL}/consent/grant`,
    { source_types: sourceTypes }
  );
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to grant consent');
}

/**
 * Revoke consent for data collection
 */
export async function revokeConsent(sourceTypes: DataSourceType[]): Promise<void> {
  const response = await api.post<ApiResponse<void>>(
    `${BASE_URL}/consent/revoke`,
    { source_types: sourceTypes }
  );
  if (!response.data.success) {
    throw new Error(response.data.error || 'Failed to revoke consent');
  }
}

/**
 * Test integration connection
 */
export async function testConnection(
  sourceType: DataSourceType,
  credentials: Record<string, string>
): Promise<{ success: boolean; message: string }> {
  const response = await api.post<ApiResponse<{ success: boolean; message: string }>>(
    `${BASE_URL}/${sourceType}/test`,
    { api_credentials: credentials }
  );
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Connection test failed');
}

/**
 * Get available data sources (metadata)
 */
export async function getAvailableDataSources(): Promise<
  Array<{
    type: DataSourceType;
    name: string;
    description: string;
    category: string;
    priority: string;
    requires_consent: boolean;
    behavioral_signals: string[];
  }>
> {
  const response = await api.get<
    ApiResponse<
      Array<{
        type: DataSourceType;
        name: string;
        description: string;
        category: string;
        priority: string;
        requires_consent: boolean;
        behavioral_signals: string[];
      }>
    >
  >(`${BASE_URL}/available`);
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to fetch available data sources');
}

/**
 * Get integration recommendations
 */
export async function getRecommendations(
  organizationSize: number
): Promise<{
  recommended: DataSourceType[];
  reasons: Record<DataSourceType, string>;
}> {
  const response = await api.get<
    ApiResponse<{ recommended: DataSourceType[]; reasons: Record<DataSourceType, string> }>
  >(`${BASE_URL}/recommendations?organization_size=${organizationSize}`);
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to fetch recommendations');
}

/**
 * Export integration data
 */
export async function exportIntegrationData(
  sourceTypes: DataSourceType[],
  dateRange: { start: string; end: string },
  format: 'csv' | 'json' | 'excel'
): Promise<Blob> {
  const response = await api.post(
    `${BASE_URL}/export`,
    {
      source_types: sourceTypes,
      date_range: dateRange,
      format
    },
    { responseType: 'blob' }
  );
  return response.data;
}

/**
 * Get data ingestion statistics
 */
export async function getIngestionStats(
  sourceType?: DataSourceType,
  days: number = 30
): Promise<{
  total_records: number;
  by_source: Record<DataSourceType, number>;
  by_day: Array<{ date: string; count: number }>;
  error_rate: number;
}> {
  const url = sourceType
    ? `${BASE_URL}/stats/ingestion?source_type=${sourceType}&days=${days}`
    : `${BASE_URL}/stats/ingestion?days=${days}`;
  const response = await api.get<
    ApiResponse<{
      total_records: number;
      by_source: Record<DataSourceType, number>;
      by_day: Array<{ date: string; count: number }>;
      error_rate: number;
    }>
  >(url);
  if (response.data.success && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to fetch ingestion stats');
}

// Export all functions as a service object
const corporateIntegrationService = {
  getOrganizationIntegrations,
  getIntegration,
  createIntegration,
  updateIntegration,
  deleteIntegration,
  toggleIntegration,
  syncIntegration,
  getHealthMetrics,
  analyzeBehavioralData,
  generateInsightsReport,
  getLatestReport,
  setupBulkIntegrations,
  getConsentRecords,
  grantConsent,
  revokeConsent,
  testConnection,
  getAvailableDataSources,
  getRecommendations,
  exportIntegrationData,
  getIngestionStats
};

export default corporateIntegrationService;
