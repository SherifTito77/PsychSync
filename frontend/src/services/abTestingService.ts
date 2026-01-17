// src/services/abTestingService.ts
// Frontend A/B testing service for onboarding optimization
import { apiClient } from './api';

export interface UserSegments {
  role?: 'manager' | 'hr' | 'lead' | 'member' | 'executive';
  industry?: string;
  team_size?: 'small' | 'medium' | 'large' | 'enterprise';
  source?: string;
  device_type?: 'desktop' | 'mobile' | 'tablet';
}

export interface TestAssignment {
  test_name: string;
  variant: string;
  variant_name: string;
  features: string[];
  segments: UserSegments;
  assigned_at: string;
  assignment_method: string;
}

export interface ConversionEvent {
  test_name: string;
  variant: string;
  event_type: string;
  timestamp: string;
  data?: Record<string, any>;
}

class ABTestingService {
  private currentAssignments: Map<string, TestAssignment> = new Map();
  private userId: string | null = null;
  private sessionId: string;

  constructor() {
    this.sessionId = this.getOrCreateSessionId();
    this.loadCachedAssignments();
  }

  private getOrCreateSessionId(): string {
    let sessionId = sessionStorage.getItem('psychsync_ab_session_id');
    if (!sessionId) {
      sessionId = `ab_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('psychsync_ab_session_id', sessionId);
    }
    return sessionId;
  }

  private loadCachedAssignments(): void {
    try {
      const cached = localStorage.getItem('psychsync_ab_assignments');
      if (cached) {
        const assignments = JSON.parse(cached);
        Object.entries(assignments).forEach(([testName, assignment]) => {
          this.currentAssignments.set(testName, assignment as TestAssignment);
        });
      }
    } catch (error) {
      console.warn('Failed to load cached A/B test assignments:', error);
    }
  }

  private cacheAssignments(): void {
    try {
      const assignments: Record<string, TestAssignment> = {};
      this.currentAssignments.forEach((assignment, testName) => {
        assignments[testName] = assignment;
      });
      localStorage.setItem('psychsync_ab_assignments', JSON.stringify(assignments));
    } catch (error) {
      console.warn('Failed to cache A/B test assignments:', error);
    }
  }

  /**
   * Set user identifier for consistent test assignment
   */
  setUserId(userId: string): void {
    this.userId = userId;
  }

  /**
   * Get or create test assignment for user
   */
  async getTestAssignment(
    testName: string = 'onboarding_flow_v2',
    segments?: UserSegments
  ): Promise<TestAssignment> {
    // Check if we already have this assignment
    if (this.currentAssignments.has(testName)) {
      return this.currentAssignments.get(testName)!;
    }

    try {
      // Call backend to get assignment
      const response = await apiClient.post('/ab-testing/assign', {
        test_name: testName,
        user_id: this.userId,
        session_id: this.sessionId,
        segments: segments || this.inferSegments()
      });

      const assignment = response.data;
      this.currentAssignments.set(testName, assignment);
      this.cacheAssignments();

      // Track assignment event
      await this.trackEvent('variant_assigned', testName, {
        variant: assignment.variant,
        segments: assignment.segments
      });

      return assignment;

    } catch (error) {
      console.warn('Failed to get A/B test assignment, using default:', error);
      return this.getDefaultAssignment(testName);
    }
  }

  /**
   * Get default assignment when API fails
   */
  private getDefaultAssignment(testName: string): TestAssignment {
    return {
      test_name: testName,
      variant: 'value_first',
      variant_name: 'Value-First Approach (Default)',
      features: ['instant_insights', 'optional_email_verification', 'quick_assessment'],
      segments: this.inferSegments(),
      assigned_at: new Date().toISOString(),
      assignment_method: 'default'
    };
  }

  /**
   * Infer user segments from browser context
   */
  private inferSegments(): UserSegments {
    const urlParams = new URLSearchParams(window.location.search);
    const utmSource = urlParams.get('utm_source');

    // Infer team size from URL patterns or company domain (basic logic)
    const inferredTeamSize = this.inferTeamSize();

    return {
      role: urlParams.get('role') as any || undefined,
      industry: urlParams.get('industry') || undefined,
      team_size: inferredTeamSize,
      source: utmSource || 'direct',
      device_type: this.getDeviceType()
    };
  }

  private inferTeamSize(): 'small' | 'medium' | 'large' | 'enterprise' {
    // Basic heuristics - in production, this would be more sophisticated
    const domain = window.location.hostname;

    if (domain.includes('enterprise') || domain.includes('corp')) {
      return 'enterprise';
    }

    // Check for common large company domains
    const largeCompanyDomains = ['google', 'microsoft', 'amazon', 'apple', 'facebook'];
    if (largeCompanyDomains.some(lcd => domain.includes(lcd))) {
      return 'large';
    }

    return 'medium'; // Default assumption
  }

  private getDeviceType(): 'desktop' | 'mobile' | 'tablet' {
    const width = window.innerWidth;
    if (width < 768) return 'mobile';
    if (width < 1024) return 'tablet';
    return 'desktop';
  }

  /**
   * Check if a feature should be shown based on user's variant
   */
  shouldShowFeature(
    featureName: string,
    testName: string = 'onboarding_flow_v2'
  ): boolean {
    const assignment = this.currentAssignments.get(testName);
    if (!assignment) return true; // Default to showing feature

    return assignment.features.includes(featureName);
  }

  /**
   * Get personalized onboarding configuration
   */
  async getPersonalizedConfig(segments?: UserSegments): Promise<any> {
    const assignment = await this.getTestAssignment('onboarding_flow_v2', segments);

    try {
      const response = await apiClient.post('/ab-testing/personalized-config', {
        user_id: this.userId,
        session_id: this.sessionId,
        segments: segments || assignment.segments,
        variant: assignment.variant
      });

      return response.data;

    } catch (error) {
      console.warn('Failed to get personalized config, using default:', error);
      return this.getDefaultConfig(assignment);
    }
  }

  private getDefaultConfig(assignment: TestAssignment): any {
    return {
      flow_type: assignment.variant,
      features: assignment.features,
      show_email_verification: !assignment.features.includes('optional_email_verification'),
      show_quick_assessment: assignment.features.includes('quick_assessment'),
      show_instant_insights: assignment.features.includes('instant_insights'),
      enable_social_login: assignment.features.includes('social_login'),
      progress_steps: this.getProgressSteps(assignment.variant)
    };
  }

  private getProgressSteps(variant: string): string[] {
    const stepMaps: Record<string, string[]> = {
      'control': ['registration', 'email_verification', 'team_setup', 'assessment', 'results'],
      'value_first': ['quick_assessment', 'insight_preview', 'registration', 'team_setup', 'results'],
      'hybrid': ['quick_preview', 'registration', 'team_setup', 'assessment', 'results'],
      'personalized': ['adaptive_assessment', 'personalized_insights', 'team_setup', 'results']
    };

    return stepMaps[variant] || stepMaps['value_first'];
  }

  /**
   * Track conversion events for A/B test analysis
   */
  async trackEvent(
    eventType: string,
    testName?: string,
    eventData?: Record<string, any>
  ): Promise<void> {
    const testToTrack = testName || 'onboarding_flow_v2';
    const assignment = this.currentAssignments.get(testToTrack);

    if (!assignment) {
      console.warn('No assignment found for test:', testToTrack);
      return;
    }

    const event: ConversionEvent = {
      test_name: testToTrack,
      variant: assignment.variant,
      event_type: eventType,
      timestamp: new Date().toISOString(),
      data: eventData
    };

    try {
      await apiClient.post('/ab-testing/track-event', event);
    } catch (error) {
      // Don't fail user experience for analytics tracking
      console.warn('Failed to track A/B test event:', error);
      this.trackEventLocally(event);
    }
  }

  private trackEventLocally(event: ConversionEvent): void {
    // Store events locally for later sync
    try {
      const events = JSON.parse(localStorage.getItem('psychsync_ab_events') || '[]');
      events.push(event);

      // Keep only last 100 events
      if (events.length > 100) {
        events.splice(0, events.length - 100);
      }

      localStorage.setItem('psychsync_ab_events', JSON.stringify(events));
    } catch (error) {
      console.warn('Failed to store event locally:', error);
    }
  }

  /**
   * Get user's current variant for a test
   */
  getCurrentVariant(testName: string = 'onboarding_flow_v2'): string | null {
    const assignment = this.currentAssignments.get(testName);
    return assignment?.variant || null;
  }

  /**
   * Force a specific variant (for testing/debugging)
   */
  async forceVariant(testName: string, variant: string): Promise<void> {
    const assignment: TestAssignment = {
      test_name: testName,
      variant,
      variant_name: `Forced: ${variant}`,
      features: this.getVariantFeatures(variant),
      segments: this.inferSegments(),
      assigned_at: new Date().toISOString(),
      assignment_method: 'forced'
    };

    this.currentAssignments.set(testName, assignment);
    this.cacheAssignments();

    await this.trackEvent('variant_forced', testName, { forced_variant: variant });
  }

  private getVariantFeatures(variant: string): string[] {
    const featureMap: Record<string, string[]> = {
      'control': ['email_verification_required', 'full_registration_first', 'complex_form'],
      'value_first': ['instant_insights', 'optional_email_verification', 'quick_assessment'],
      'hybrid': ['quick_preview', 'progressive_registration', 'social_login'],
      'personalized': ['adaptive_flow', 'personalized_insights', 'smart_recommendations']
    };

    return featureMap[variant] || featureMap['value_first'];
  }

  /**
   * Get test results (for admin/analytics dashboard)
   */
  async getTestResults(testName: string = 'onboarding_flow_v2'): Promise<any> {
    try {
      const response = await apiClient.get(`/ab-testing/results/${testName}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get test results:', error);
      return null;
    }
  }

  /**
   * Sync local events to server
   */
  async syncLocalEvents(): Promise<void> {
    try {
      const events = JSON.parse(localStorage.getItem('psychsync_ab_events') || '[]');
      if (events.length === 0) return;

      // Batch send events
      await apiClient.post('/ab-testing/batch-events', { events });

      // Clear local events after successful sync
      localStorage.removeItem('psychsync_ab_events');

    } catch (error) {
      console.warn('Failed to sync local A/B test events:', error);
    }
  }

  /**
   * Get performance metrics for current variant
   */
  getVariantMetrics(testName: string = 'onboarding_flow_v2'): any {
    const assignment = this.currentAssignments.get(testName);
    if (!assignment) return null;

    // Calculate some basic client-side metrics
    const events = JSON.parse(localStorage.getItem('psychsync_ab_events') || '[]');
    const testEvents = events.filter((e: any) => e.test_name === testName && e.variant === assignment.variant);

    return {
      variant: assignment.variant,
      time_in_variant: Date.now() - new Date(assignment.assigned_at).getTime(),
      events_tracked: testEvents.length,
      completion_events: testEvents.filter((e: any) => e.event_type.includes('complete')).length,
      drop_off_events: testEvents.filter((e: any) => e.event_type.includes('drop_off')).length
    };
  }

  /**
   * Cleanup and reset all test data
   */
  reset(): void {
    this.currentAssignments.clear();
    localStorage.removeItem('psychsync_ab_assignments');
    localStorage.removeItem('psychsync_ab_events');
    sessionStorage.removeItem('psychsync_ab_session_id');
  }
}

// Export singleton instance
export const abTestingService = new ABTestingService();

// Sync events periodically
setInterval(() => {
  abTestingService.syncLocalEvents();
}, 30000); // Every 30 seconds

export default abTestingService;
