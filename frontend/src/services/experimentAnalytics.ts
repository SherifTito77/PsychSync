// frontend/src/services/experimentAnalytics.ts
// Analytics helper for A/B testing events
import { apiClient } from './api';

export class ExperimentAnalytics {
  /**
   * Track a conversion event
   *
   * @param experimentName - Name of the experiment
   * @param value - Optional monetary value for the conversion
   */
  static async trackConversion(
    experimentName: string,
    value?: number
  ): Promise<void> {
    try {
      // Get current variant from localStorage
      const cacheKey = `ab_experiment_${experimentName}`;
      const variant = localStorage.getItem(cacheKey) || 'control';

      await apiClient.post('/api/v1/ab/track', {
        experiment: experimentName,
        variant,
        event_type: 'conversion',
        properties: { value }
      });
    } catch (error) {
      console.error('Failed to track conversion:', error);
    }
  }

  /**
   * Track a click event
   *
   * @param experimentName - Name of the experiment
   * @param element - Element identifier (e.g., 'signup_button')
   */
  static async trackClick(
    experimentName: string,
    element: string
  ): Promise<void> {
    try {
      const cacheKey = `ab_experiment_${experimentName}`;
      const variant = localStorage.getItem(cacheKey) || 'control';

      await apiClient.post('/api/v1/ab/track', {
        experiment: experimentName,
        variant,
        event_type: 'click',
        properties: { element }
      });
    } catch (error) {
      console.error('Failed to track click:', error);
    }
  }

  /**
   * Track a page view event
   *
   * @param experimentName - Name of the experiment
   */
  static async trackView(experimentName: string): Promise<void> {
    try {
      const cacheKey = `ab_experiment_${experimentName}`;
      const variant = localStorage.getItem(cacheKey) || 'control';

      await apiClient.post('/api/v1/ab/track', {
        experiment: experimentName,
        variant,
        event_type: 'view'
      });
    } catch (error) {
      console.error('Failed to track view:', error);
    }
  }

  /**
   * Track a custom event
   *
   * @param experimentName - Name of the experiment
   * @param eventType - Type of event (e.g., 'signup_complete', 'purchase')
   * @param properties - Additional event properties
   */
  static async trackCustom(
    experimentName: string,
    eventType: string,
    properties?: Record<string, any>
  ): Promise<void> {
    try {
      const cacheKey = `ab_experiment_${experimentName}`;
      const variant = localStorage.getItem(cacheKey) || 'control';

      await apiClient.post('/api/v1/ab/track', {
        experiment: experimentName,
        variant,
        event_type: eventType,
        properties
      });
    } catch (error) {
      console.error('Failed to track custom event:', error);
    }
  }

  /**
   * Get experiment results
   *
   * @param experimentName - Name of the experiment
   * @returns Experiment results with conversion rates and significance
   */
  static async getResults(experimentName: string): Promise<any> {
    try {
      const response = await apiClient.get(`/api/v1/ab/results/${experimentName}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get experiment results:', error);
      return null;
    }
  }

  /**
   * List all experiments
   *
   * @param status - Optional status filter
   */
  static async listExperiments(status?: string): Promise<any> {
    try {
      const params = status ? { status } : {};
      const response = await apiClient.get('/api/v1/ab/experiments', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to list experiments:', error);
      return null;
    }
  }
}

// Export singleton instance
export default ExperimentAnalytics;
