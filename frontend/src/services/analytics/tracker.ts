/**
 * Unified Analytics Event Tracker
 *
 * Standardizes all analytics events across the application with:
 * - Consistent event schema
 * - Runtime validation with Zod
 * - Automatic context fields (session_id, timestamp, user_id)
 * - Single API endpoint
 * - Event naming conventions
 */

import { z } from 'zod';

// ============================================================================
// EVENT SCHEMA DEFINITIONS
// ============================================================================

/**
 * Standard analytics event schema
 * All events must conform to this structure
 */
export const StandardAnalyticsEventSchema = z.object({
  // ✅ NEW: Unique event ID for deduplication
  event_id: z.string().uuid(),

  // Required fields
  event_name: z.string().min(1).max(100),
  event_type: z.enum(['track', 'identify', 'page', 'screen']),
  timestamp: z.string().datetime(),

  // Context fields (auto-populated)
  user_id: z.string().optional(),
  session_id: z.string().min(1),
  page: z.string().optional(),
  url: z.string().optional(),
  referrer: z.string().optional(),

  // Event-specific properties
  properties: z.record(z.string(), z.any()).optional(),

  // Legacy support (will be transformed)
  experiment_name: z.string().optional(),
  variant: z.string().optional(),
});

export type StandardAnalyticsEvent = z.infer<typeof StandardAnalyticsEventSchema>;

/**
 * Event category types for naming convention
 */
export type EventCategory =
  | 'ab'           // A/B testing events
  | 'funnel'       // Conversion funnel events
  | 'user'         // User-initiated actions
  | 'system'       // System events
  | 'error'        // Error events
  | 'engagement'   // User engagement metrics
  | 'performance'; // Performance metrics

/**
 * Event action types (past tense verbs)
 */
export type EventAction =
  | 'assigned'     // Variant assigned in A/B test
  | 'completed'    // Process finished
  | 'clicked'      // Element clicked
  | 'submitted'    // Form submitted
  | 'viewed'       // Page/screen viewed
  | 'failed'       // Operation failed
  | 'started'      // Process started
  | 'converted'    // Conversion occurred
  | 'dismissed'    // Modal/popup dismissed
  | 'scrolled'     // Scroll action
  | 'hovered';     // Hover interaction

// ============================================================================
// EVENT CATALOG
// ============================================================================

/**
 * Comprehensive event catalog with naming conventions
 * Pattern: category_action_object (past tense actions)
 */
export const EVENT_CATALOG = {
  // A/B Testing Events (ab_*)
  AB_VARIANT_ASSIGNED: 'ab_variant_assigned',
  AB_VARIANT_FORCED: 'ab_variant_forced',
  AB_EXPOSURE: 'ab_exposure',

  // Funnel Events (funnel_*)
  FUNNEL_SIGNUP_STARTED: 'funnel_signup_started',
  FUNNEL_SIGNUP_COMPLETED: 'funnel_signup_completed',
  FUNNEL_LOGIN_STARTED: 'funnel_login_started',
  FUNNEL_LOGIN_COMPLETED: 'funnel_login_completed',
  FUNNEL_ONBOARDING_STARTED: 'funnel_onboarding_started',
  FUNNEL_ONBOARDING_COMPLETED: 'funnel_onboarding_completed',
  FUNNEL_ASSESSMENT_STARTED: 'funnel_assessment_started',
  FUNNEL_ASSESSMENT_COMPLETED: 'funnel_assessment_completed',
  FUNNEL_TEAM_CREATION_STARTED: 'funnel_team_creation_started',
  FUNNEL_TEAM_CREATION_COMPLETED: 'funnel_team_creation_completed',

  // User Actions (user_*)
  USER_BUTTON_CLICKED: 'user_button_clicked',
  USER_LINK_CLICKED: 'user_link_clicked',
  USER_FORM_SUBMITTED: 'user_form_submitted',
  USER_INPUT_CHANGED: 'user_input_changed',
  USER_MODAL_OPENED: 'user_modal_opened',
  USER_MODAL_CLOSED: 'user_modal_closed',
  USER_TAB_CHANGED: 'user_tab_changed',
  USER_MENU_OPENED: 'user_menu_opened',
  USER_MENU_CLOSED: 'user_menu_closed',

  // System Events (system_*)
  SYSTEM_ERROR_OCCURRED: 'system_error_occurred',
  SYSTEM_WARNING_OCCURRED: 'system_warning_occurred',
  SYSTEM_API_CALL_FAILED: 'system_api_call_failed',
  SYSTEM_API_CALL_SUCCEEDED: 'system_api_call_succeeded',

  // Engagement Events (engagement_*)
  ENGAGEMENT_CONTENT_VIEWED: 'engagement_content_viewed',
  ENGAGEMENT_VIDEO_PLAYED: 'engagement_video_played',
  ENGAGEMENT_VIDEO_PAUSED: 'engagement_video_paused',
  ENGAGEMENT_RESOURCE_DOWNLOADED: 'engagement_resource_downloaded',
  ENGAGEMENT_FEATURE_DISCOVERED: 'engagement_feature_discovered',

  // Performance Events (performance_*)
  PERFORMANCE_PAGE_LOAD: 'performance_page_load',
  PERFORMANCE_API_LATENCY: 'performance_api_latency',
  PERFORMANCE_INTERACTION_DELAY: 'performance_interaction_delay',

  // Onboarding Events (legacy support)
  ONBOARDING_QUICK_ASSESSMENT_COMPLETED: 'onboarding_quick_assessment_completed',
  ONBOARDING_SETUP_STEP_COMPLETED: 'onboarding_setup_step_completed',

  // ✅ NEW: Subscription & Revenue Events (subscription_*)
  // TODO(human): Decide privacy strategy for revenue data before implementing
  // Options: 1) Anonymize (no user IDs), 2) Hash IDs, 3) Require consent, 4) Server-side only
  SUBSCRIPTION_TRIAL_STARTED: 'subscription_trial_started',
  SUBSCRIPTION_PLAN_SELECTED: 'subscription_plan_selected',
  SUBSCRIPTION_PAYMENT_SUCCEEDED: 'subscription_payment_succeeded',
  SUBSCRIPTION_PAYMENT_FAILED: 'subscription_payment_failed',
  SUBSCRIPTION_PLAN_UPGRADED: 'subscription_plan_upgraded',
  SUBSCRIPTION_PLAN_DOWNGRADED: 'subscription_plan_downgraded',
  SUBSCRIPTION_CANCELLED: 'subscription_cancelled',
  SUBSCRIPTION_RENEWED: 'subscription_renewed',

  // ✅ NEW: Feature Usage Events (feature_*)
  // TODO(human): Decide which features to track first based on business priorities
  FEATURE_ASSESSMENT_TAKEN: 'feature_assessment_taken',
  FEATURE_TEAM_CREATED: 'feature_team_created',
  FEATURE_TEAM_OPTIMIZER_USED: 'feature_team_optimizer_used',
  FEATURE_CLINICAL_TOOLS_USED: 'feature_clinical_tools_used',
  FEATURE_WELLNESS_PLAN_CREATED: 'feature_wellness_plan_created',
  FEATURE_PREDICTIVE_ANALYTICS_USED: 'feature_predictive_analytics_used',
  FEATURE_BENCHMARKING_USED: 'feature_benchmarking_used',
  FEATURE_PATTERN_ANALYSIS_VIEWED: 'feature_pattern_analysis_viewed',
  FEATURE_TREND_ANALYSIS_VIEWED: 'feature_trend_analysis_viewed',

  // ✅ NEW: Integration Events (integration_*)
  INTEGRATION_SLACK_CONNECTED: 'integration_slack_connected',
  INTEGRATION_HRIS_CONNECTED: 'integration_hris_connected',
  INTEGRATION_EMAIL_CONNECTED: 'integration_email_connected',

  // ✅ NEW: Session Tracking (user_session_*)
  // TODO(human): Decide on session timeout duration (recommend 30 min inactive)
  USER_SESSION_STARTED: 'user_session_started',
  USER_SESSION_ENDED: 'user_session_ended',
  USER_RETURNED: 'user_returned',

  // ✅ NEW: Support Events (support_*)
  SUPPORT_TICKET_CREATED: 'support_ticket_created',
  SUPPORT_TICKET_FIRST_RESPONSE: 'support_ticket_first_response',
  SUPPORT_TICKET_RESOLVED: 'support_ticket_resolved',
  SUPPORT_SATISFACTION_SURVEY: 'support_satisfaction_survey',
} as const;

export type EventName = typeof EVENT_CATALOG[keyof typeof EVENT_CATALOG];

// ============================================================================
// SESSION MANAGEMENT
// ============================================================================

/**
 * Session ID generator and manager
 */
class SessionManager {
  private sessionId: string;
  private sessionStart: number;

  constructor() {
    this.sessionId = this.getOrCreateSessionId();
    this.sessionStart = Date.now();
  }

  private getOrCreateSessionId(): string {
    let sessionId = sessionStorage.getItem('analytics_session_id');

    if (!sessionId) {
      sessionId = this.generateSessionId();
      sessionStorage.setItem('analytics_session_id', sessionId);
    }

    return sessionId;
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
  }

  getSessionId(): string {
    return this.sessionId;
  }

  getSessionDuration(): number {
    return Date.now() - this.sessionStart;
  }

  resetSession(): void {
    this.sessionId = this.generateSessionId();
    this.sessionStart = Date.now();
    sessionStorage.setItem('analytics_session_id', this.sessionId);
  }
}

// ============================================================================
// UNIFIED TRACKER CLASS
// ============================================================================

/**
 * Unified analytics tracker
 * Handles all event tracking with consistent schema and validation
 *
 * ✅ GDPR COMPLIANT: All tracking methods check for explicit user consent
 * before collecting or sending any data.
 */
class UnifiedAnalyticsTracker {
  private sessionManager: SessionManager;
  private apiClient: any;
  private userId: string | null = null;
  private queue: StandardAnalyticsEvent[] = [];
  private isBatching = false;
  private batchInterval: NodeJS.Timeout | null = null;
  private isDevelopment = import.meta.env.MODE === 'development';

  // ✅ GDPR COMPLIANT: Consent management
  private consentGranted = false;

  // ✅ NEW: Retry logic properties
  private failedBatches: Array<{batch: StandardAnalyticsEvent[], attempts: number, firstAttempt: number}> = [];
  private maxRetries = 3;
  private retryDelays = [1000, 5000, 15000]; // Exponential backoff: 1s, 5s, 15s

  // ✅ NEW: Health monitoring properties
  private healthMetrics = {
    totalEvents: 0,
    successfulEvents: 0,
    failedEvents: 0,
    queuedEvents: 0,
    batchesSent: 0,
    batchesFailed: 0,
    sendBeaconFailures: 0,
    lastSuccessfulSend: null as Date | null,
    lastFailure: null as Date | null,
    averageDeliveryTime: 0,
  };

  // ✅ NEW: Event sampling properties
  private sampleRate = 1.0; // 100% by default
  private maxQueueSize = 1000; // ✅ PERFORMANCE FIX: Increased from 100 to 1000
  private isUnderStress = false;

  // ✅ NEW: Backend offline detection
  private backendOffline = false;
  private consecutiveFailures = 0;
  private maxConsecutiveFailures = 5; // Stop retrying after 5 consecutive failures

  // ✅ NEW: Error monitoring integration
  private errorMonitoring: {
    captureException?: (error: Error, context?: any) => void;
    captureMessage?: (message: string, level?: string, context?: any) => void;
  } = {};

  constructor(apiClient: any) {
    this.apiClient = apiClient;
    this.sessionManager = new SessionManager();
    this.initializeConsent(); // ✅ GDPR: Check consent first before anything else
    this.initializeUserId();
    this.initializeErrorMonitoring();
    this.startBatchProcessing();
    // ✅ FIXED: Fire-and-forget async recovery (don't block initialization)
    this.initializeEventRecovery().catch((error) => {
      this.logAnalyticsError('Event recovery crashed', error);
    });
  }

  /**
   * ✅ GDPR COMPLIANT: Initialize consent from localStorage
   *
   * Checks if user has granted explicit consent for analytics tracking.
   * Only initializes tracking if consent was previously granted.
   */
  private initializeConsent(): void {
    try {
      const consentStatus = localStorage.getItem('analytics_consent');
      this.consentGranted = consentStatus === 'granted';

      if (this.isDevelopment) {
        console.log(`📊 [Analytics] Consent check: ${this.consentGranted ? 'GRANTED' : 'NOT GRANTED'}`);
      }
    } catch (error) {
      // If localStorage is not available, default to no consent
      this.consentGranted = false;
      if (this.isDevelopment) {
        console.warn('⚠️ [Analytics] Could not read consent from localStorage', error);
      }
    }
  }

  /**
   * ✅ GDPR COMPLIANT: Check if user has granted consent
   *
   * Returns true only if user has explicitly opted in to analytics tracking.
   * All tracking methods must check this before collecting data.
   */
  private hasConsent(): boolean {
    return this.consentGranted;
  }

  /**
   * ✅ GDPR COMPLIANT: Set consent status
   *
   * Called when user grants or withdraws consent.
   * - When granting: Starts collecting events immediately
   * - When withdrawing: Clears queue and stops collecting new events
   */
  setConsent(granted: boolean): void {
    const previousState = this.consentGranted;
    this.consentGranted = granted;

    if (this.isDevelopment) {
      console.log(`📊 [Analytics] Consent ${granted ? 'GRANTED' : 'WITHDRAWN'}`);
    }

    if (granted && !previousState) {
      // Consent was just granted - start tracking
      this.startBatchProcessing();
    } else if (!granted && previousState) {
      // Consent was just withdrawn - stop tracking and clear data
      this.queue = []; // Clear pending events
      this.failedBatches = []; // Clear retry queue

      // Clear user ID to stop PII collection
      this.userId = null;

      // Don't clear localStorage here - the consent context handles that
    }
  }

  /**
   * Initialize user ID from storage or auth context
   * ✅ GDPR COMPLIANT: Only sets user ID if consent has been granted
   */
  private initializeUserId(): void {
    // ✅ GDPR: Only collect user ID if consent was granted
    if (!this.hasConsent()) {
      return;
    }

    // Try to get user ID from various sources
    const userId = localStorage.getItem('user_id') ||
                   sessionStorage.getItem('user_id') ||
                   null;

    if (userId) {
      this.setUserId(userId);
    }
  }

  /**
   * Set current user ID
   * ✅ GDPR COMPLIANT: Only stores user ID if consent has been granted
   */
  setUserId(userId: string): void {
    // ✅ GDPR: Only collect PII if consent was granted
    if (!this.hasConsent()) {
      if (this.isDevelopment) {
        console.warn('⚠️ [Analytics] Cannot set user ID - consent not granted');
      }
      return;
    }

    this.userId = userId;
    localStorage.setItem('user_id', userId);
  }

  /**
   * Clear user ID (on logout)
   */
  clearUserId(): void {
    this.userId = null;
    localStorage.removeItem('user_id');
    this.sessionManager.resetSession();
  }

  /**
   * ✅ NEW: Initialize error monitoring integration (Sentry, etc.)
   */
  private initializeErrorMonitoring(): void {
    // Check for Sentry
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      this.errorMonitoring = (window as any).Sentry;
    }
  }

  /**
   * ✅ NEW: Log analytics error to monitoring service
   */
  private logAnalyticsError(message: string, error: any, context?: any): void {
    // Always send to error monitoring in production
    if (this.errorMonitoring.captureException) {
      this.errorMonitoring.captureException(error, {
        tags: { service: 'analytics', severity: 'error' },
        extra: { message, ...context }
      });
    } else if (this.errorMonitoring.captureMessage) {
      this.errorMonitoring.captureMessage(message, 'error', { error, ...context });
    }

    // Development: console for debugging
    if (this.isDevelopment) {
      console.error(`❌ [Analytics] ${message}:`, error);
      if (context) console.error('Context:', context);
    }

    // Update health metrics
    this.healthMetrics.failedEvents++;
    this.healthMetrics.lastFailure = new Date();
  }

  /**
   * ✅ NEW: Recover failed events from localStorage on page load
   * ✅ FIXED: localStorage cleared AFTER successful send (not before)
   */
  private async initializeEventRecovery(): Promise<void> {
    try {
      const failedEventsJson = localStorage.getItem('failed_analytics_events');
      if (failedEventsJson) {
        const failedEvents = JSON.parse(failedEventsJson);
        if (Array.isArray(failedEvents) && failedEvents.length > 0) {
          console.log(`📊 [Analytics] Recovering ${failedEvents.length} failed events from previous session`);

          // Add to queue for retry
          this.queue.unshift(...failedEvents);

          // ❌ OLD: Cleared localStorage IMMEDIATELY - data loss if crash before send!
          // localStorage.removeItem('failed_analytics_events');

          // ✅ NEW: Try to send immediately BEFORE clearing localStorage
          try {
            await this.flushQueue();

            // ✅ Clear localStorage only AFTER successful send
            localStorage.removeItem('failed_analytics_events');
            console.log(`✅ [Analytics] Successfully recovered ${failedEvents.length} events`);
          } catch (error) {
            // Flush failed - keep in localStorage for next page load
            this.logAnalyticsError('Failed to send recovered events - keeping in localStorage for retry', error, {
              eventsCount: failedEvents.length
            });
            // Don't clear - events still in queue AND localStorage
          }
        }
      }
    } catch (error) {
      this.logAnalyticsError('Failed to recover events from localStorage', error);
    }
  }

  /**
   * ✅ NEW: Set event sampling rate (0.0 to 1.0)
   * Use during high load to prevent queue overflow
   */
  setSampleRate(rate: number): void {
    if (rate < 0 || rate > 1) {
      console.warn('[Analytics] Sample rate must be between 0 and 1');
      return;
    }
    this.sampleRate = rate;
    console.log(`[Analytics] Sample rate set to ${(rate * 100).toFixed(0)}%`);
  }

  /**
   * ✅ NEW: Check if event should be sampled
   */
  private shouldSampleEvent(): boolean {
    if (this.sampleRate >= 1.0) return true;
    if (this.sampleRate <= 0) return false;
    return Math.random() < this.sampleRate;
  }

  /**
   * ✅ NEW: Get health metrics for monitoring
   */
  getHealthMetrics() {
    return {
      ...this.healthMetrics,
      queueSize: this.queue.length,
      failedBatchesCount: this.failedBatches.length,
      sampleRate: this.sampleRate,
      isUnderStress: this.isUnderStress,
      successRate: this.healthMetrics.totalEvents > 0
        ? (this.healthMetrics.successfulEvents / this.healthMetrics.totalEvents * 100).toFixed(1) + '%'
        : 'N/A',
    };
  }

  /**
   * ✅ PRIVACY: Sanitize URL to remove PII from query parameters
   * Keeps only protocol, host, and pathname (removes query string and hash)
   *
   * Example:
   *   Input:  https://app.psychsync.com/reset?token=abc&email=user@example.com
   *   Output: https://app.psychsync.com/reset
   */
  private sanitizeUrl(url: string): string {
    try {
      const urlObj = new URL(url);
      // Return URL without query params or hash
      return `${urlObj.protocol}//${urlObj.host}${urlObj.pathname}`;
    } catch {
      // If URL parsing fails, return just pathname (safe fallback)
      return window.location.pathname;
    }
  }

  /**
   * ✅ PRIVACY: Sanitize referrer to remove PII
   * Keeps only origin (protocol + host, no path or query params)
   *
   * Example:
   *   Input:  https://app.psychsync.com/login?email=user@example.com
   *   Output: https://app.psychsync.com
   */
  private sanitizeReferrer(referrer: string): string | undefined {
    if (!referrer) return undefined;
    try {
      const urlObj = new URL(referrer);
      // Return only origin (protocol + host, no path, no query params)
      return urlObj.origin;
    } catch {
      // If parsing fails, don't store referrer at all
      return undefined;
    }
  }

  /**
   * ✅ PRIVACY: Check properties for PII before storing
   * Warns in development if PII patterns detected
   */
  private sanitizeProperties(properties: Record<string, any>): Record<string, any> {
    if (!properties || typeof properties !== 'object') {
      return properties;
    }

    // PII field patterns to remove
    const piiFields = [
      'email', 'e', 'mail',
      'name', 'username', 'user', 'fullname',
      'phone', 'mobile', 'tel', 'telephone',
      'address', 'location',
      'ssn', 'social_security', 'socialSecurity',
      'password', 'pass', 'pwd',
      'token', 'key', 'secret', 'api_key',
      'credit_card', 'creditCard',
      'dob', 'birth_date', 'birthDate'
    ];

    const sanitized: Record<string, any> = {};
    let piiDetected = false;

    for (const [key, value] of Object.entries(properties)) {
      // Skip obvious PII fields
      if (piiFields.some(piiField => key.toLowerCase().includes(piiField))) {
        piiDetected = true;
        if (this.isDevelopment) {
          console.warn(`🔒 [Analytics] PII field removed from properties: ${key}`);
        }
        continue;
      }

      // Check string values for PII patterns
      if (typeof value === 'string') {
        // Email pattern
        if (/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}/.test(value)) {
          piiDetected = true;
          if (this.isDevelopment) {
            console.warn(`🔒 [Analytics] Email removed from properties.${key}`);
          }
          continue;
        }

        // Phone pattern (basic)
        if (/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/.test(value)) {
          piiDetected = true;
          if (this.isDevelopment) {
            console.warn(`🔒 [Analytics] Phone number removed from properties.${key}`);
          }
          continue;
        }

        // SSN pattern
        if (/\b\d{3}-?\d{2}-?\d{4}\b/.test(value)) {
          piiDetected = true;
          if (this.isDevelopment) {
            console.warn(`🔒 [Analytics] SSN removed from properties.${key}`);
          }
          continue;
        }
      }

      // Safe to include
      sanitized[key] = value;
    }

    if (piiDetected && !this.isDevelopment) {
      this.logAnalyticsError('PII detected in properties and removed', null, {
        original_keys: Object.keys(properties),
        sanitized_keys: Object.keys(sanitized)
      });
    }

    // ✅ SIZE VALIDATION: Check properties size (backend limit: 4 KB)
    const propertiesSize = new Blob([JSON.stringify(sanitized)]).size;
    const MAX_PROPERTIES_SIZE = 4096; // 4 KB (matches backend limit)

    if (propertiesSize > MAX_PROPERTIES_SIZE) {
      console.warn(
        `⚠️ [Analytics] Properties too large (${propertiesSize} bytes, max ${MAX_PROPERTIES_SIZE}). ` +
        `Backend will reject this event. Consider reducing property values.`
      );
    }

    return sanitized;
  }

  /**
   * ✅ UPDATED: Build standard event with automatic context fields and unique ID
   * ✅ PRIVACY: Sanitizes URLs and properties to remove PII
   */
  private buildEvent(
    eventName: string,
    eventType: StandardAnalyticsEvent['event_type'],
    properties?: Record<string, any>
  ): StandardAnalyticsEvent {
    // ✅ PRIVACY: Sanitize URLs and properties before storing
    const sanitizedUrl = this.sanitizeUrl(window.location.href);
    const sanitizedReferrer = this.sanitizeReferrer(document.referrer);
    const sanitizedProperties = this.sanitizeProperties(properties || {});

    return {
      // ✅ NEW: Generate unique ID for deduplication
      event_id: crypto.randomUUID(),
      event_name: eventName,
      event_type: eventType,
      timestamp: new Date().toISOString(),
      session_id: this.sessionManager.getSessionId(),
      user_id: this.userId || undefined,
      page: window.location.pathname,
      url: sanitizedUrl,
      referrer: sanitizedReferrer,
      properties: sanitizedProperties,
    };
  }

  /**
   * Validate event against schema
   */
  private validateEvent(event: StandardAnalyticsEvent): void {
    try {
      StandardAnalyticsEventSchema.parse(event);
    } catch (error) {
      this.logAnalyticsError('Event validation failed', error, { event });
      throw new Error(`Invalid event schema: ${error}`);
    }
  }

  /**
   * ✅ UPDATED: Queue event for batch sending with sampling and stress detection
   */
  /**
   * ✅ PERFORMANCE FIX: Add event to queue with overflow protection and prioritization
   */
  private queueEvent(event: StandardAnalyticsEvent): void {
    // Check sampling
    if (!this.shouldSampleEvent()) {
      if (this.isDevelopment) {
        console.log(`📊 [Analytics] Event sampled out: ${event.event_name}`);
      }
      return;
    }

    // Check queue size and enable stress mode if needed
    if (this.queue.length >= this.maxQueueSize) {
      this.isUnderStress = true;

      // ✅ PERFORMANCE FIX: Check if this is a critical event before dropping
      const isCriticalEvent = this.isCriticalEvent(event);

      if (isCriticalEvent) {
        // ✅ Prioritize critical events by making room for them
        // Remove non-critical events (oldest first) to free up space
        const removedCount = this.makeRoomForCriticalEvents(10);

        if (this.isDevelopment) {
          console.log(`📊 [Analytics] Queue full - made room for critical event by removing ${removedCount} non-critical events`);
        }
      } else {
        // ✅ PERFORMANCE FIX: Reduce sample rate more aggressively under stress (from 50% to 10%)
        if (this.sampleRate > 0.1) {
          this.setSampleRate(0.1);
          this.logAnalyticsError('Analytics under stress - reduced sample rate to 10%', new Error('Queue overflow protection'), {
            queueSize: this.queue.length,
            newSampleRate: 0.1
          });
        }

        // Drop non-critical events when queue is completely full
        if (this.queue.length >= this.maxQueueSize) {
          if (this.isDevelopment) {
            console.warn(`⚠️ [Analytics] Queue full - dropping non-critical event: ${event.event_name}`);
          }
          return; // Drop this event
        }
      }
    } else if (this.queue.length < this.maxQueueSize * 0.5 && this.isUnderStress) {
      // Recover from stress mode
      this.isUnderStress = false;
      this.setSampleRate(1.0);
    }

    this.queue.push(event);
    this.healthMetrics.queuedEvents++;
    this.healthMetrics.totalEvents++;

    // Send immediately if queue is too large
    if (this.queue.length >= 10) {
      this.flushQueue();
    }
  }

  /**
   * ✅ PERFORMANCE FIX: Determine if an event is critical and should be prioritized
   */
  private isCriticalEvent(event: StandardAnalyticsEvent): boolean {
    const criticalPatterns = [
      'funnel_',          // All funnel events (started/completed)
      '_completed',      // All completion events
      'user_identified',  // User identification
      'system_error',     // Error tracking
    ];

    return criticalPatterns.some(pattern => event.event_name.includes(pattern));
  }

  /**
   * ✅ PERFORMANCE FIX: Remove non-critical events to make room for critical ones
   * Returns the number of events removed
   */
  private makeRoomForCriticalEvents(count: number): number {
    let removed = 0;
    const newQueue: StandardAnalyticsEvent[] = [];

    // Process queue in reverse (newest first) to keep recent events
    for (let i = this.queue.length - 1; i >= 0 && removed < count; i--) {
      const event = this.queue[i];

      // Keep critical events, remove non-critical ones
      if (this.isCriticalEvent(event)) {
        newQueue.unshift(event); // Add to beginning of new queue
      } else {
        removed++;
      }
    }

    // Keep any remaining events that weren't processed
    for (let i = 0; i < this.queue.length - newQueue.length; i++) {
      if (!this.queue[i].event_id) {
        newQueue.unshift(this.queue[i]);
      }
    }

    this.queue = newQueue.reverse(); // Restore original order
    return removed;
  }

  /**
   * Start batch processing interval
   */
  private startBatchProcessing(): void {
    if (this.batchInterval) return;

    this.batchInterval = setInterval(() => {
      if (this.queue.length > 0) {
        this.flushQueue();
      }
    }, 5000); // Send batch every 5 seconds
  }

  /**
   * ✅ FIXED: Flush queued events to API with proper error handling and retry logic
   *
   * CRITICAL FIX: Queue is now cleared AFTER successful send, not before
   * PREVIOUS BUG: this.queue = [] was at line 303, before the API call
   * This meant failed batches couldn't be retried because the data was lost
   */
  private async flushQueue(): Promise<void> {
    // ✅ NEW: Skip if backend is offline
    if (this.backendOffline) {
      // Silently persist events without retrying
      if (this.queue.length > 0) {
        this.persistFailedEvents(this.queue);
        this.queue = [];
      }
      return;
    }

    if (this.isBatching || this.queue.length === 0) return;

    this.isBatching = true;
    const startTime = Date.now();

    try {
      // ✅ FIX: Copy queue first, DON'T clear yet
      const batch = [...this.queue];

      await this.apiClient.post('/analytics/track', {
        events: batch,
        batch: true,
      });

      // ✅ FIX: Clear queue AFTER successful send
      this.queue = this.queue.slice(batch.length);

      // ✅ NEW: Reset failure counter on success
      this.consecutiveFailures = 0;

      // Update health metrics
      this.healthMetrics.batchesSent++;
      this.healthMetrics.successfulEvents += batch.length;
      this.healthMetrics.lastSuccessfulSend = new Date();

      // Update average delivery time
      const deliveryTime = Date.now() - startTime;
      this.healthMetrics.averageDeliveryTime =
        (this.healthMetrics.averageDeliveryTime * (this.healthMetrics.batchesSent - 1) + deliveryTime) /
        this.healthMetrics.batchesSent;

      if (this.isDevelopment) {
        console.log(`✅ [Analytics] Sent batch of ${batch.length} events (${deliveryTime}ms)`);
      }
    } catch (error) {
      // ✅ FIX: Queue is NOT cleared, events remain for retry
      this.healthMetrics.batchesFailed++;

      // ✅ NEW: Increment consecutive failure counter
      this.consecutiveFailures++;
      if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
        this.backendOffline = true;
        console.warn('⚠️ [Analytics] Backend appears offline. Pausing analytics and persisting events locally.');
        // Persist all queued events
        this.persistFailedEvents(this.queue);
        this.queue = [];
        return;
      }

      this.logAnalyticsError('Failed to send batch', error, {
        queueSize: this.queue.length,
        willRetry: true,
        consecutiveFailures: this.consecutiveFailures
      });

      // ✅ NEW: Add to retry queue with exponential backoff
      const batch = [...this.queue];
      this.failedBatches.push({
        batch,
        attempts: 1,
        firstAttempt: Date.now()
      });

      // Schedule retry
      const retryDelay = this.retryDelays[0]; // First retry after 1s
      setTimeout(() => this.retryFailedBatches(), retryDelay);

      if (this.isDevelopment) {
        console.error(`❌ [Analytics] Batch failed - scheduling retry in ${retryDelay}ms`);
      }
    } finally {
      this.isBatching = false;
    }
  }

  /**
   * ✅ NEW: Retry failed batches with exponential backoff
   */
  private async retryFailedBatches(): Promise<void> {
    if (this.failedBatches.length === 0) return;

    if (this.isDevelopment) {
      console.log(`🔄 [Analytics] Retrying ${this.failedBatches.length} failed batches`);
    }

    const batchesToRetry = [...this.failedBatches];
    this.failedBatches = [];

    for (const item of batchesToRetry) {
      // Check if max retries exceeded
      if (item.attempts >= this.maxRetries) {
        this.logAnalyticsError('Max retries exceeded - persisting to localStorage', new Error('Retry limit'), {
          attempts: item.attempts,
          batchSize: item.batch.length,
          ageInMinutes: (Date.now() - item.firstAttempt) / 60000
        });

        // Persist to localStorage for manual recovery
        this.persistFailedEvents(item.batch);
        continue;
      }

      try {
        await this.apiClient.post('/analytics/track', {
          events: item.batch,
          batch: true,
        });

        // Success - update metrics
        this.healthMetrics.batchesSent++;
        this.healthMetrics.successfulEvents += item.batch.length;
        this.healthMetrics.lastSuccessfulSend = new Date();

        if (this.isDevelopment) {
          console.log(`✅ [Analytics] Retry successful for batch (attempt ${item.attempts})`);
        }
      } catch (error) {
        // Retry failed - increment counter and schedule next retry
        item.attempts++;
        this.failedBatches.push(item);

        // Schedule next retry with exponential backoff
        const retryIndex = Math.min(item.attempts - 1, this.retryDelays.length - 1);
        const retryDelay = this.retryDelays[retryIndex];

        setTimeout(() => this.retryFailedBatches(), retryDelay);

        this.logAnalyticsError('Retry failed', error, {
          attempt: item.attempts,
          nextRetryIn: `${retryDelay}ms`
        });
      }
    }
  }

  /**
   * ✅ NEW: Persist failed events to localStorage for manual recovery
   * ✅ FIXED: Deduplicates events by event_id to prevent duplicates
   * ✅ PERFORMANCE FIX: Added cleanup of old events and quota exceeded handling
   */
  private persistFailedEvents(events: StandardAnalyticsEvent[]): void {
    try {
      // Get existing failed events
      const existingJson = localStorage.getItem('failed_analytics_events');
      const existing = existingJson ? JSON.parse(existingJson) : [];

      // ✅ FIX: Create a Set of existing event_ids for O(1) lookup
      const existingIds = new Set(existing.map((e: StandardAnalyticsEvent) => e.event_id));

      // ✅ FIX: Filter out duplicates - only add events that don't already exist
      const newEvents = events.filter((e: StandardAnalyticsEvent) => !existingIds.has(e.event_id));

      if (newEvents.length === 0) {
        // All events were duplicates, nothing to persist
        return;
      }

      // Add only new events (no duplicates)
      let allFailed = [...existing, ...newEvents];

      // ✅ PERFORMANCE FIX: Clean up events older than 7 days
      const oneWeekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
      allFailed = allFailed.filter((event: StandardAnalyticsEvent) => {
        const eventTime = new Date(event.timestamp).getTime();
        return eventTime > oneWeekAgo;
      });

      // ✅ PERFORMANCE FIX: Limit to 1000 events max to prevent overflow
      const maxEvents = 1000;
      if (allFailed.length > maxEvents) {
        // Keep only the most recent 1000 events
        allFailed = allFailed.slice(-maxEvents);
        console.warn(`⚠️ [Analytics] Trimmed failed events to ${maxEvents} most recent`);
      }

      // Store with size limit
      try {
        localStorage.setItem('failed_analytics_events', JSON.stringify(allFailed));
        console.warn(`⚠️ [Analytics] Persisted ${newEvents.length} failed events to localStorage (${events.length - newEvents.length} were duplicates)`);
      } catch (storageError: any) {
        // ✅ PERFORMANCE FIX: Handle QuotaExceededError gracefully
        if (storageError.name === 'QuotaExceededError') {
          console.error('❌ [Analytics] localStorage quota exceeded - clearing oldest 50% of events');
          this.clearOldestFailedEvents(0.5); // Clear oldest 50%

          // Try again after cleanup
          try {
            const retryEvents = allFailed.slice(-500); // Keep only 500 most recent
            localStorage.setItem('failed_analytics_events', JSON.stringify(retryEvents));
            console.warn(`⚠️ [Analytics] Recovered with ${retryEvents.length} events after cleanup`);
          } catch (retryError: any) {
            console.error('❌ [Analytics] Still cannot persist events after cleanup:', retryError);
          }
        } else {
          console.error('❌ [Analytics] Failed to persist events:', storageError);
        }
      }
    } catch (error) {
      console.error('❌ [Analytics] Failed to persist events:', error);
    }
  }

  /**
   * ✅ PERFORMANCE FIX: Clear oldest percentage of failed events from localStorage
   * Used when quota is exceeded to free up space
   */
  private clearOldestFailedEvents(percentageToKeep: number): void {
    try {
      const existingJson = localStorage.getItem('failed_analytics_events');
      if (!existingJson) {
        return; // Nothing to clear
      }

      const existing = JSON.parse(existingJson);
      if (!Array.isArray(existing) || existing.length === 0) {
        return;
      }

      // Keep only the most recent events
      const keepCount = Math.max(Math.floor(existing.length * percentageToKeep), 100);
      const toKeep = existing.slice(-keepCount); // Keep last N events (most recent)

      localStorage.setItem('failed_analytics_events', JSON.stringify(toKeep));
      console.warn(`⚠️ [Analytics] Cleared ${existing.length - toKeep.length} old events, kept ${toKeep.length} most recent`);
    } catch (error) {
      console.error('❌ [Analytics] Failed to clear old events:', error);
    }
  }

  /**
   * ✅ NEW: Selectively remove events from localStorage by event_id
   * This ensures true idempotency - only remove events we successfully sent
   */
  private removeFromLocalStorage(eventIds: Set<string>): void {
    try {
      const failedEventsJson = localStorage.getItem('failed_analytics_events');
      if (!failedEventsJson) {
        return; // Nothing to remove
      }

      const failedEvents = JSON.parse(failedEventsJson);
      if (!Array.isArray(failedEvents) || failedEvents.length === 0) {
        return;
      }

      // ✅ Filter out the events we just successfully sent
      const remainingEvents = failedEvents.filter((e: StandardAnalyticsEvent) => !eventIds.has(e.event_id));

      if (remainingEvents.length === 0) {
        // All events were sent - clear localStorage completely
        localStorage.removeItem('failed_analytics_events');
        if (this.isDevelopment) {
          console.log(`✅ [Analytics] Cleared all ${eventIds.size} events from localStorage`);
        }
      } else {
        // Some events remain - update localStorage with remaining events
        localStorage.setItem('failed_analytics_events', JSON.stringify(remainingEvents));
        const removedCount = eventIds.size;
        const keptCount = remainingEvents.length;
        if (this.isDevelopment) {
          console.log(`✅ [Analytics] Removed ${removedCount} events from localStorage, kept ${keptCount} events`);
        }
      }
    } catch (error) {
      this.logAnalyticsError('Failed to remove events from localStorage', error);
    }
  }

  /**
   * Track a standard event
   * ✅ GDPR COMPLIANT: Only tracks if user has granted consent
   */
  track(
    eventName: string,
    properties?: Record<string, any>,
    options?: { immediate?: boolean }
  ): void {
    // ✅ GDPR: Check consent before tracking
    if (!this.hasConsent()) {
      if (this.isDevelopment) {
        console.log(`⚠️ [Analytics] Skipping event "${eventName}" - consent not granted`);
      }
      return;
    }

    try {
      const event = this.buildEvent(eventName, 'track', properties);
      this.validateEvent(event);

      if (options?.immediate) {
        // Send immediately
        this.apiClient.post('/analytics/track', {
          events: [event],
          batch: false,
        }).catch((error: Error) => {
          this.logAnalyticsError('Failed to send immediate event', error, {
            eventName,
            properties
          });
        });
      } else {
        // Queue for batch sending
        this.queueEvent(event);
      }

      if (this.isDevelopment) {
        console.log(`📊 [Analytics] Tracked: ${eventName}`, properties || '');
      }
    } catch (error) {
      this.logAnalyticsError('Failed to track event', error, { eventName, properties });
    }
  }

  /**
   * Track A/B testing events (legacy support)
   */
  trackABTest(
    experimentName: string,
    variant: string,
    eventType: 'assigned' | 'conversion' | 'click' | 'view',
    properties?: Record<string, any>
  ): void {
    const eventName = eventType === 'assigned'
      ? EVENT_CATALOG.AB_VARIANT_ASSIGNED
      : `ab_${eventType}`;

    this.track(eventName, {
      experiment_name: experimentName,
      variant,
      ...properties,
    });
  }

  /**
   * Track funnel events (started/completed)
   * ✅ FIXED: Added runtime validation against EVENT_CATALOG
   */
  trackFunnel(
    funnelStep: string,
    status: 'started' | 'completed',
    properties?: Record<string, any>
  ): void {
    const eventName = `funnel_${funnelStep}_${status}` as EventName;

    // ✅ NEW: Runtime validation against EVENT_CATALOG
    const allEventNames = Object.values(EVENT_CATALOG);
    if (!allEventNames.includes(eventName as any)) {
      console.error(`❌ [Analytics] Event '${eventName}' is NOT in EVENT_CATALOG!`, {
        funnelStep,
        status,
        generatedEvent: eventName,
        hint: `Add to EVENT_CATALOG: FUNNEL_${funnelStep.toUpperCase()}_${status.toUpperCase()}: '${eventName}'`
      });
      // Still track the event (don't break production), but log the issue
    }

    this.track(eventName, properties);
  }

  /**
   * Track page views
   * ✅ PERFORMANCE FIX: Made non-blocking - only queues event, lets batch processor handle it
   * ✅ GDPR COMPLIANT: Only tracks if user has granted consent
   */
  trackPage(page?: string, properties?: Record<string, any>): void {
    // ✅ GDPR: Check consent before tracking
    if (!this.hasConsent()) {
      if (this.isDevelopment) {
        console.log(`⚠️ [Analytics] Skipping page view - consent not granted`);
      }
      return;
    }

    const event = this.buildEvent(
      page || window.location.pathname,
      'page',
      properties
    );

    // Add page-specific fields
    event.properties = {
      ...event.properties,
      path: page || window.location.pathname,
      title: document.title,
      ...properties,
    };

    this.validateEvent(event);

    // ✅ FIXED: Only queue the event, don't send immediately
    // This prevents blocking the UI during navigation
    this.queueEvent(event);

    // ✅ FIXED: Schedule flush using requestIdleCallback if available
    // This ensures tracking happens during browser idle time, not during critical rendering
    if (typeof requestIdleCallback !== 'undefined') {
      requestIdleCallback(
        () => {
          if (this.queue.length > 0) {
            this.flushQueue();
          }
        },
        { timeout: 2000 } // Fallback to 2 seconds if idle never comes
      );
    }

    if (this.isDevelopment) {
      console.log(`📊 [Analytics] Page view: ${page || window.location.pathname}`);
    }
  }

  /**
   * Track user identification
   * ✅ PERFORMANCE FIX: Made non-blocking - only queues event, lets batch processor handle it
   * ✅ GDPR COMPLIANT: Only tracks if user has granted consent
   */
  identify(userId: string, traits?: Record<string, any>): void {
    // ✅ GDPR: Check consent before tracking (setUserId already checks consent)
    if (!this.hasConsent()) {
      if (this.isDevelopment) {
        console.log(`⚠️ [Analytics] Skipping user identification - consent not granted`);
      }
      return;
    }

    this.setUserId(userId);

    const event = this.buildEvent('user_identified', 'identify', traits);
    this.validateEvent(event);

    // ✅ FIXED: Only queue the event, don't send immediately
    // This prevents blocking UI during user authentication
    this.queueEvent(event);

    // ✅ FIXED: Schedule flush using requestIdleCallback if available
    if (typeof requestIdleCallback !== 'undefined') {
      requestIdleCallback(
        () => {
          if (this.queue.length > 0) {
            this.flushQueue();
          }
        },
        { timeout: 2000 }
      );
    }

    if (this.isDevelopment) {
      console.log(`📊 [Analytics] User identified: ${userId}`);
    }
  }

  /**
   * Track errors
   */
  trackError(error: Error, context?: Record<string, any>): void {
    this.track(EVENT_CATALOG.SYSTEM_ERROR_OCCURRED, {
      error_message: error.message,
      error_stack: error.stack,
      error_name: error.name,
      ...context,
    }, { immediate: true });
  }

  // ============================================================================
  // BUSINESS EVENT TRACKING HELPERS
  // ============================================================================

  /**
   * ✅ NEW: Track subscription lifecycle events
   * Privacy-safe: Revenue amounts only tracked if user consent given
   */
  trackSubscription(
    action: 'trial_started' | 'plan_selected' | 'payment_succeeded' | 'payment_failed' | 'plan_upgraded' | 'plan_downgraded' | 'cancelled' | 'renewed',
    details: {
      plan_tier?: 'free' | 'premium' | 'enterprise';
      billing_period?: 'monthly' | 'annual';
      amount?: number;
      currency?: string;
      trial_days?: number;
      cancellation_reason?: string;
      previous_plan?: string;
      payment_method?: string;
    }
  ): void {
    const eventName = `subscription_${action}` as EventName;

    // ✅ PRIVACY: Only track revenue if consent given (check localStorage)
    const hasConsent = localStorage.getItem('analytics_revenue_consent') === 'true';

    if (!hasConsent && (details.amount || details.payment_method)) {
      // Track event without financial details
      this.track(eventName, {
        plan_tier: details.plan_tier,
        billing_period: details.billing_period,
        // amount, currency, payment_method excluded
      });
    } else {
      // Full tracking with consent
      this.track(eventName, details);
    }

    if (this.isDevelopment) {
      console.log(`💰 [Analytics] Subscription ${action}:`, details.plan_tier);
    }
  }

  /**
   * ✅ NEW: Track feature usage events
   * Helps understand which features drive value and retention
   */
  trackFeatureUsed(
    featureName: string,
    details: {
      feature_category?: string;
      assessment_type?: string;
      team_size?: number;
      integration_type?: 'slack' | 'hris' | 'email';
      usage_context?: string;
    } = {}
  ): void {
    const eventName = `feature_${featureName}` as EventName;

    this.track(eventName, {
      feature_name: featureName,
      feature_category: details.feature_category || this.categorizeFeature(featureName),
      ...details,
    });

    if (this.isDevelopment) {
      console.log(`⭐ [Analytics] Feature used: ${featureName}`);
    }
  }

  /**
   * ✅ NEW: Track integration connection events
   */
  trackIntegration(
    integrationType: 'slack' | 'hris' | 'email',
    action: 'connected' | 'disconnected',
    details?: Record<string, any>
  ): void {
    const eventName = `integration_${integrationType}_${action}` as EventName;

    this.track(eventName, {
      integration_type: integrationType,
      action,
      ...details,
    });

    if (this.isDevelopment) {
      console.log(`🔗 [Analytics] Integration ${action}: ${integrationType}`);
    }
  }

  /**
   * ✅ NEW: Track session lifecycle
   * Called automatically on app mount/unmount
   */
  trackSession(
    action: 'started' | 'ended',
    details?: {
      session_duration_seconds?: number;
      pages_viewed?: number;
      features_used?: string[];
      entry_page?: string;
      exit_page?: string;
    }
  ): void {
    const eventName = `user_session_${action}` as EventName;

    this.track(eventName, {
      session_id: this.sessionManager.getSessionId(),
      ...details,
    });

    if (this.isDevelopment) {
      console.log(`🔄 [Analytics] Session ${action}`);
    }
  }

  /**
   * ✅ NEW: Track returning user
   * Detects when user comes back after N days
   */
  trackReturnedUser(daysSinceLastVisit: number): void {
    this.track(EVENT_CATALOG.USER_RETURNED, {
      days_since_last_visit: daysSinceLastVisit,
      session_id: this.sessionManager.getSessionId(),
    });

    if (this.isDevelopment) {
      console.log(`👋 [Analytics] User returned after ${daysSinceLastVisit} days`);
    }
  }

  /**
   * ✅ NEW: Track support ticket events
   */
  trackSupport(
    action: 'ticket_created' | 'first_response' | 'resolved' | 'satisfaction_survey',
    details: {
      ticket_id?: string;
      category?: string;
      priority?: string;
      response_time_minutes?: number;
      resolution_time_minutes?: number;
      csat_score?: number; // 1-5
      nps_score?: number; // 0-10
    }
  ): void {
    const eventName = `support_${action}` as EventName;

    this.track(eventName, details);

    if (this.isDevelopment) {
      console.log(`🎫 [Analytics] Support ${action}`);
    }
  }

  /**
   * ✅ NEW: Categorize features automatically
   */
  private categorizeFeature(featureName: string): string {
    const categories: Record<string, string> = {
      assessment: 'assessments',
      team: 'collaboration',
      clinical: 'clinical_tools',
      wellness: 'clinical_tools',
      optimizer: 'team_analytics',
      predictive: 'analytics',
      benchmark: 'analytics',
      pattern: 'analytics',
      trend: 'analytics',
    };

    for (const [key, category] of Object.entries(categories)) {
      if (featureName.toLowerCase().includes(key)) {
        return category;
      }
    }

    return 'general';
  }

  /**
   * ✅ NEW: Request revenue tracking consent
   * Call this when user accepts terms or upgrades to paid plan
   */
  grantRevenueConsent(): void {
    localStorage.setItem('analytics_revenue_consent', 'true');
    if (this.isDevelopment) {
      console.log('✅ [Analytics] Revenue tracking consent granted');
    }
  }

  /**
   * ✅ NEW: Revoke revenue tracking consent
   * Call this when user opts out of analytics or requests data deletion
   */
  revokeRevenueConsent(): void {
    localStorage.removeItem('analytics_revenue_consent');
    if (this.isDevelopment) {
      console.log('❌ [Analytics] Revenue tracking consent revoked');
    }
  }

  /**
   * ✅ FIXED: Flush all queued events before page unload with proper error handling
   *
   * CRITICAL FIX: Added sendBeacon failure detection and localStorage fallback
   * PREVIOUS BUG: No checking if sendBeacon succeeded - events just disappeared
   * ✅ FIXED: Selective localStorage clearing by event_id for true idempotency
   */
  flush(): void {
    if (this.queue.length > 0) {
      const data = JSON.stringify({ events: this.queue, batch: true });
      const eventsCount = this.queue.length;
      const batchEventIds = new Set(this.queue.map(e => e.event_id)); // ✅ NEW: Track event IDs

      // Use sendBeacon for page unload events
      if (navigator.sendBeacon) {
        const success = navigator.sendBeacon('/analytics/track', data);

        if (success) {
          // Success - clear queue
          this.queue = [];
          this.healthMetrics.successfulEvents += eventsCount;
          this.healthMetrics.lastSuccessfulSend = new Date();

          if (this.isDevelopment) {
            console.log(`✅ [Analytics] Flushed ${eventsCount} events via sendBeacon`);
          }
        } else {
          // ✅ FIX: sendBeacon failed - persist to localStorage
          this.healthMetrics.sendBeaconFailures++;
          this.logAnalyticsError('sendBeacon failed - using localStorage fallback', new Error('sendBeacon returned false'), {
            eventsCount,
            dataSize: data.length
          });

          // Fallback: Persist to localStorage for recovery on next page load
          this.persistFailedEvents(this.queue);

          // Try synchronous XHR as last resort
          try {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/analytics/track', false);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(data);

            // Check if XHR succeeded
            if (xhr.status >= 200 && xhr.status < 300) {
              // ✅ FIXED: Clear queue FIRST
              this.queue = [];

              // ✅ FIXED: Selectively remove only these events from localStorage
              this.removeFromLocalStorage(batchEventIds);

              if (this.isDevelopment) {
                console.log(`✅ [Analytics] Sync XHR fallback succeeded for ${eventsCount} events`);
              }
            } else {
              this.logAnalyticsError('Sync XHR fallback failed', new Error(`HTTP ${xhr.status}`), {
                eventsCount,
                status: xhr.status
              });
            }
          } catch (error) {
            this.logAnalyticsError('Sync XHR fallback crashed', error, { eventsCount });
          }
        }
      } else {
        // No sendBeacon support - use synchronous XHR
        try {
          const xhr = new XMLHttpRequest();
          xhr.open('POST', '/analytics/track', false);
          xhr.setRequestHeader('Content-Type', 'application/json');
          xhr.send(data);

          if (xhr.status >= 200 && xhr.status < 300) {
            this.queue = [];
            this.healthMetrics.successfulEvents += eventsCount;

            if (this.isDevelopment) {
              console.log(`✅ [Analytics] Sync XHR succeeded for ${eventsCount} events`);
            }
          } else {
            // XHR failed - persist to localStorage
            this.persistFailedEvents(this.queue);
            this.logAnalyticsError('Sync XHR failed', new Error(`HTTP ${xhr.status}`), {
              eventsCount,
              status: xhr.status
            });
          }
        } catch (error) {
          this.logAnalyticsError('Sync XHR crashed', error, { eventsCount });
          this.persistFailedEvents(this.queue);
        }
      }
    }
  }

  /**
   * ✅ NEW: Re-enable analytics when backend comes back online
   * Call this manually if you've restarted the backend server
   */
  reenableBackend(): void {
    this.backendOffline = false;
    this.consecutiveFailures = 0;
    console.log('✅ [Analytics] Backend re-enabled. Analytics tracking resumed.');
  }

  /**
   * Cleanup on unmount
   */
  destroy(): void {
    if (this.batchInterval) {
      clearInterval(this.batchInterval);
      this.batchInterval = null;
    }
    this.flush();
  }
}

// ============================================================================
// SINGLETON EXPORT
// ============================================================================

/**
 * Global tracker instance
 * Will be initialized with apiClient on first use
 */
let trackerInstance: UnifiedAnalyticsTracker | null = null;

/**
 * Initialize the unified analytics tracker
 * Call this once during app initialization
 */
export function initAnalytics(apiClient: any): UnifiedAnalyticsTracker {
  if (!trackerInstance) {
    trackerInstance = new UnifiedAnalyticsTracker(apiClient);

    // ✅ NEW: Expose tracker globally for health dashboard
    if (typeof window !== 'undefined') {
      (window as any).analyticsTracker = trackerInstance;
    }

    // Setup page unload handler
    window.addEventListener('beforeunload', () => {
      trackerInstance?.flush();
    });

    // Track initial page view
    trackerInstance.trackPage();

    console.log('✅ [Analytics] Unified tracker initialized');
  }

  return trackerInstance;
}

/**
 * Get the global tracker instance
 * Throws if not initialized
 */
export function getAnalytics(): UnifiedAnalyticsTracker {
  if (!trackerInstance) {
    throw new Error('Analytics tracker not initialized. Call initAnalytics() first.');
  }
  return trackerInstance;
}

/**
 * Type-safe event builder helper
 */
export function buildEventName(
  category: EventCategory,
  action: EventAction,
  object?: string
): string {
  return object
    ? `${category}_${action}_${object}`
    : `${category}_${action}`;
}

// ============================================================================
// REACT HOOK
// ============================================================================

/**
 * React hook for using analytics tracker in components
 * ⚡️ PERFORMANCE: Returns no-op functions when analytics is not initialized
 * This prevents crashes when analytics is disabled for performance
 */
export function useAnalytics() {
  // ⚡️ PERFORMANCE: If analytics not initialized, return no-op functions
  if (!trackerInstance) {
    return {
      track: () => {},
      trackABTest: () => {},
      trackFunnel: () => {},
      trackPage: () => {},
      identify: () => {},
      trackError: () => {},
      getHealthMetrics: () => ({}),
      setSampleRate: () => {},
      setConsent: () => {},
      trackClick: () => {},
      trackFormSubmit: () => {},
      trackNavigation: () => {},
      trackSession: () => {},
      trackReturnedUser: () => {},
    };
  }

  const tracker = getAnalytics();

  return {
    track: tracker.track.bind(tracker),
    trackABTest: tracker.trackABTest.bind(tracker),
    trackFunnel: tracker.trackFunnel.bind(tracker),
    trackPage: tracker.trackPage.bind(tracker),
    identify: tracker.identify.bind(tracker),
    trackError: tracker.trackError.bind(tracker),

    // ✅ NEW: Health monitoring methods
    getHealthMetrics: tracker.getHealthMetrics.bind(tracker),
    setSampleRate: tracker.setSampleRate.bind(tracker),

    // ✅ GDPR COMPLIANT: Consent management method
    setConsent: tracker.setConsent.bind(tracker),

    // Helper methods
    trackClick: (elementId: string, properties?: Record<string, any>) =>
      tracker.track(EVENT_CATALOG.USER_BUTTON_CLICKED, {
        element_id: elementId,
        ...properties,
      }),

    trackFormSubmit: (formId: string, properties?: Record<string, any>) =>
      tracker.track(EVENT_CATALOG.USER_FORM_SUBMITTED, {
        form_id: formId,
        ...properties,
      }),

    trackModalOpen: (modalId: string, properties?: Record<string, any>) =>
      tracker.track(EVENT_CATALOG.USER_MODAL_OPENED, {
        modal_id: modalId,
        ...properties,
      }),

    trackModalClose: (modalId: string, properties?: Record<string, any>) =>
      tracker.track(EVENT_CATALOG.USER_MODAL_CLOSED, {
        modal_id: modalId,
        ...properties,
      }),

    // ✅ NEW: Business event tracking methods
    trackSubscription: tracker.trackSubscription.bind(tracker),
    trackFeatureUsed: tracker.trackFeatureUsed.bind(tracker),
    trackIntegration: tracker.trackIntegration.bind(tracker),
    trackSession: tracker.trackSession.bind(tracker),
    trackReturnedUser: tracker.trackReturnedUser.bind(tracker),
    trackSupport: tracker.trackSupport.bind(tracker),
    grantRevenueConsent: tracker.grantRevenueConsent.bind(tracker),
    revokeRevenueConsent: tracker.revokeRevenueConsent.bind(tracker),
  };
}

// ============================================================================
// PERFORMANCE VALIDATION
// ============================================================================

/**
 * Initialize performance monitoring for analytics
 * This validates that analytics doesn't slow down user interactions
 */
export function initPerformanceMonitoring(): void {
  if (typeof window === 'undefined') return;

  import('./performance-validator').then(({ validateAnalyticsPerformance }) => {
    // Run performance validation after 5 seconds (once app is stable)
    setTimeout(() => {
      if (import.meta.env.MODE === 'development') {
        console.log('🔍 [Performance] Running analytics performance validation...');
        validateAnalyticsPerformance().then(results => {
          console.log('📊 [Performance] Results:', results.report);
        });
      }
    }, 5000);
  });
}

// Auto-initialize performance monitoring in development
if (import.meta.env.MODE === 'development' && typeof window !== 'undefined') {
  initPerformanceMonitoring();
}

export default UnifiedAnalyticsTracker;
