// frontend/src/services/experimentAnalytics.ts
// Analytics helper for A/B testing events
// ✅ MIGRATED: Now uses unified analytics tracker
import { apiClient } from './api';
import { getAnalytics, EVENT_CATALOG } from './analytics/tracker';

/**
 * Get variant from localStorage for experiment
 */
function getVariant(experimentName: string): string {
  const cacheKey = `ab_experiment_${experimentName}`;
  return localStorage.getItem(cacheKey) || 'control';
}

export class ExperimentAnalytics {
  /**
   * Track a conversion event
   * ✅ MIGRATED: Uses unified analytics tracker
   *
   * @param experimentName - Name of the experiment
   * @param value - Optional monetary value for the conversion
   */
  static async trackConversion(
    experimentName: string,
    value?: number
  ): Promise<void> {
    try {
      const analytics = getAnalytics();
      const variant = getVariant(experimentName);

      // Use unified tracker for A/B test events
      analytics.trackABTest(experimentName, variant, 'conversion', {
        value,
        experiment_name: experimentName, // Legacy field for backward compatibility
      });
    } catch (error) {
      console.error('Failed to track conversion:', error);
    }
  }

  /**
   * Track a click event
   * ✅ MIGRATED: Uses unified analytics tracker
   *
   * @param experimentName - Name of the experiment
   * @param element - Element identifier (e.g., 'signup_button')
   */
  static async trackClick(
    experimentName: string,
    element: string
  ): Promise<void> {
    try {
      const analytics = getAnalytics();
      const variant = getVariant(experimentName);

      // Use unified tracker for A/B test events
      analytics.track(EVENT_CATALOG.USER_BUTTON_CLICKED, {
        experiment_name: experimentName,
        variant,
        element_id: element,
        element_type: 'ab_test_element',
      });
    } catch (error) {
      console.error('Failed to track click:', error);
    }
  }

  /**
   * Track a page view event
   * ✅ MIGRATED: Uses unified analytics tracker
   *
   * @param experimentName - Name of the experiment
   */
  static async trackView(experimentName: string): Promise<void> {
    try {
      const analytics = getAnalytics();
      const variant = getVariant(experimentName);

      // Use unified tracker for A/B test exposure
      analytics.track(EVENT_CATALOG.AB_EXPOSURE, {
        experiment_name: experimentName,
        variant,
      });
    } catch (error) {
      console.error('Failed to track view:', error);
    }
  }

  /**
   * Track a custom event
   * ✅ MIGRATED: Uses unified analytics tracker
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
      const analytics = getAnalytics();
      const variant = getVariant(experimentName);

      // Map to standard event type if possible
      const standardEventType = this.mapToStandardEventType(eventType);

      if (standardEventType) {
        // Use unified tracker with standard event
        analytics.trackABTest(experimentName, variant, standardEventType as any, {
          ...properties,
          experiment_name: experimentName,
          original_event_type: eventType, // Preserve original for debugging
        });
      } else {
        // Use generic track for custom events
        analytics.track(`ab_${eventType}`, {
          experiment_name: experimentName,
          variant,
          ...properties,
        });
      }
    } catch (error) {
      console.error('Failed to track custom event:', error);
    }
  }

  /**
   * Map legacy event types to standard catalog
   */
  private static mapToStandardEventType(eventType: string): string | null {
    const eventMap: Record<string, string> = {
      'signup_complete': 'funnel_signup_completed',
      'purchase': 'funnel_purchase_completed',
      'view': 'viewed',
      'click': 'clicked',
      'conversion': 'conversion',
    };

    return eventMap[eventType] || null;
  }

  /**
   * Get experiment results
   * (Unchanged - still uses API directly)
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
   * (Unchanged - still uses API directly)
   *
   * @param status - Optional status filter
   */
  static async listExperiments(status?: string): Promise<any> {
    try {
      const params = status ? { status } : {};
      const response = await apiClient.get('/ab/experiments', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to list experiments:', error);
      return null;
    }
  }
}

// Export singleton instance
export default ExperimentAnalytics;
