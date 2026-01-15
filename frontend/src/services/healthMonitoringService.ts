/**
 * Health Monitoring Service
 *
 * Service for interacting with health monitoring endpoints including:
 * - Health risk analysis
 * - Biometric data submission
 * - Health reports
 * - Consent management
 */

import api from './api';
import type {
  HealthRiskData,
  BiometricData,
  HealthReport,
  HealthDataConsent,
  ConsentUpdateRequest,
  ApiResponse,
} from '@/types/healthMonitoring';

interface HealthAnalysisRequest {
  time_window_days?: number;
  include_biometric?: boolean;
  biometric_data?: BiometricData;
}

export class HealthMonitoringService {
  private static readonly BASE_PATH = '/health-monitoring';

  /**
   * Analyze health risks based on work patterns, communication, and biometric data
   */
  static async analyzeHealthRisks(
    request: HealthAnalysisRequest = {}
  ): Promise<HealthRiskData> {
    try {
      const response = await api.post<HealthRiskData>(
        `${this.BASE_PATH}/analyze`,
        {
          time_window_days: request.time_window_days || 30,
          include_biometric: request.include_biometric || false,
          biometric_data: request.biometric_data,
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to analyze health risks:', error);
      throw error;
    }
  }

  /**
   * Get comprehensive health report for current user
   */
  static async getHealthReport(days: number = 30): Promise<HealthReport> {
    try {
      const response = await api.get<HealthReport>(
        `${this.BASE_PATH}/health-report`,
        { params: { days } }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get health report:', error);
      throw error;
    }
  }

  /**
   * Submit biometric health data from wearables or manual entry
   */
  static async submitBiometricData(
    data: BiometricData
  ): Promise<ApiResponse<{ data_id: string; risk_indicators: any }>> {
    try {
      const response = await api.post<
        ApiResponse<{ data_id: string; risk_indicators: any }>
      >(`${this.BASE_PATH}/biometric`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to submit biometric data:', error);
      throw error;
    }
  }

  /**
   * Get current consent status for health data
   */
  static async getConsentStatus(): Promise<HealthDataConsent> {
    try {
      const response = await api.get<HealthDataConsent>(
        `${this.BASE_PATH}/consent`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get consent status:', error);
      throw error;
    }
  }

  /**
   * Update consent preferences for health data collection and processing
   */
  static async updateConsentPreferences(
    request: ConsentUpdateRequest
  ): Promise<ApiResponse<{ consent_given: boolean }>> {
    try {
      const response = await api.post<ApiResponse<{ consent_given: boolean }>>(
        `${this.BASE_PATH}/consent`,
        request
      );
      return response.data;
    } catch (error) {
      console.error('Failed to update consent preferences:', error);
      throw error;
    }
  }

  /**
   * Quick health check - analyzes most recent data
   */
  static async quickHealthCheck(): Promise<HealthRiskData> {
    return this.analyzeHealthRisks({
      time_window_days: 7,
      include_biometric: false,
    });
  }

  /**
   * Comprehensive health analysis - includes all available data
   */
  static async comprehensiveHealthAnalysis(
    biometricData?: BiometricData
  ): Promise<HealthRiskData> {
    return this.analyzeHealthRisks({
      time_window_days: 90,
      include_biometric: true,
      biometric_data: biometricData,
    });
  }
}

export default HealthMonitoringService;
