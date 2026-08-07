/**
 * Manager Dashboard Service
 *
 * Service for accessing anonymized team health analytics and management features.
 * Designed for managers, HR, and leadership to monitor team wellness trends
 * while maintaining individual privacy.
 */

import api from './api';
import type {
  ManagerDashboardData,
  ApiResponse,
} from '@/types/healthMonitoring';

export interface TeamHealthFilters {
  team_id?: string;
  days?: number;
}

export class ManagerDashboardService {
  private static readonly BASE_PATH = '/health-monitoring/manager-dashboard';
  private static activeControllers: Map<string, AbortController> = new Map();

  /**
   * Cancel ongoing request
   */
  private static cancelRequest(key: string) {
    const controller = this.activeControllers.get(key);
    if (controller) {
      controller.abort();
      this.activeControllers.delete(key);
    }
  }

  /**
   * Get anonymized team health dashboard
   *
   Privacy-focused:
   * - No individual user identifiers
   * - Aggregate metrics only
   * - Anonymized risk distributions
   * - Count-based reporting
   *
   * @param filters - Optional filters for team and time period
   * @returns Manager dashboard data with anonymized team health metrics
   */
  static async getTeamDashboard(
    filters: TeamHealthFilters = {},
    signal?: AbortSignal
  ): Promise<ManagerDashboardData> {
    try {
      console.log('[ManagerDashboard] Fetching team dashboard with filters:', filters);

      // Create request config with abort signal
      const config: any = {
        params: {
          team_id: filters.team_id,
          days: filters.days || 30,
        },
      };

      // Add abort signal if provided
      if (signal) {
        config.signal = signal;
      }

      const response = await api.get<ManagerDashboardData>(
        this.BASE_PATH,
        config
      );
      console.log('[ManagerDashboard] Received response:', response.data);
      return response.data;
    } catch (error) {
      console.error('[ManagerDashboard] Failed to get team dashboard:', error);
      throw error;
    }
  }

  /**
   * Get organization-wide health overview
   */
  static async getOrganizationOverview(days: number = 30, signal?: AbortSignal): Promise<ManagerDashboardData> {
    return this.getTeamDashboard({ days }, signal);
  }

  /**
   * Get specific team health overview
   */
  static async getTeamOverview(teamId: string, days: number = 30, signal?: AbortSignal): Promise<ManagerDashboardData> {
    return this.getTeamDashboard({
      team_id: teamId,
      days,
    }, signal);
  }

  /**
   * Get weekly team health trends
   */
  static async getWeeklyTrends(teamId?: string): Promise<ManagerDashboardData> {
    return this.getTeamDashboard({
      team_id: teamId,
      days: 90, // 3 months for weekly trends
    });
  }

  /**
   * Get quarterly team health report
   */
  static async getQuarterlyReport(teamId?: string): Promise<ManagerDashboardData> {
    return this.getTeamDashboard({
      team_id: teamId,
      days: 90,
    });
  }

  /**
   * Check if current user has manager/HR access
   */
  static async checkManagerAccess(): Promise<boolean> {
    try {
      const response = await api.get<{ has_access: boolean }>(
        '/health-monitoring/manager-access'
      );
      return response.data.has_access;
    } catch (error) {
      console.error('Failed to check manager access:', error);
      return false;
    }
  }
}

export default ManagerDashboardService;
