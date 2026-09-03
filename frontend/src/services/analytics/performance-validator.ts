/**
 * Analytics Performance Validator
 *
 * Validates that analytics events do not slow down user interactions
 *
 * Key Performance Targets:
 * - track() call: < 1ms (should be synchronous queue operation)
 * - Event processing: < 5ms (validation + queueing)
 * - Memory usage: < 10MB for 10,000 events
 * - No blocking of main thread
 */

import { UnifiedAnalyticsTracker } from './tracker';

export interface PerformanceMetrics {
  trackCallDuration: number;      // Time to call track()
  eventProcessingDuration: number; // Time to process and queue event
  memoryUsage: number;             // Memory in bytes
  queueSize: number;               // Number of events in queue
  timestamp: number;
}

export class AnalyticsPerformanceValidator {
  private metrics: PerformanceMetrics[] = [];
  private readonly MAX_METRICS = 1000;

  /**
   * Validate that track() doesn't block
   */
  validateTrackPerformance(tracker: UnifiedAnalyticsTracker, eventName: string): PerformanceMetrics {
    const startTime = performance.now();

    // Measure track() call duration
    const trackStart = performance.now();
    tracker.track(eventName, { test_data: 'performance_test' });
    const trackEnd = performance.now();

    // Measure memory usage
    const memoryStart = (performance as any).memory?.usedJSHeapSize || 0;

    const metrics: PerformanceMetrics = {
      trackCallDuration: trackEnd - trackStart,
      eventProcessingDuration: 0, // Calculated below
      memoryUsage: memoryStart,
      queueSize: (tracker as any).queue?.length || 0,
      timestamp: Date.now(),
    };

    // Estimate event processing time (track() - network call time)
    // Since track() is synchronous, this should be near zero
    metrics.eventProcessingDuration = metrics.trackCallDuration;

    this.addMetric(metrics);
    return metrics;
  }

  /**
   * Validate rapid event tracking doesn't block
   */
  validateRapidTracking(tracker: UnifiedAnalyticsTracker, eventCount: number = 100): {
    totalDuration: number;
    averageDuration: number;
    maxDuration: number;
    minDuration: number;
    blockedMainThread: boolean;
  } {
    const durations: number[] = [];
    let blockedMainThread = false;

    // Track many events rapidly
    for (let i = 0; i < eventCount; i++) {
      const start = performance.now();
      tracker.track(`performance_test_${i}`, { iteration: i });
      const end = performance.now();
      durations.push(end - start);

      // Check if main thread was blocked (> 16ms = 1 frame at 60fps)
      if (end - start > 16) {
        blockedMainThread = true;
      }
    }

    const totalDuration = durations.reduce((a, b) => a + b, 0);
    const maxDuration = Math.max(...durations);
    const minDuration = Math.min(...durations);
    const averageDuration = totalDuration / eventCount;

    return {
      totalDuration,
      averageDuration,
      maxDuration,
      minDuration,
      blockedMainThread,
    };
  }

  /**
   * Validate memory usage doesn't grow unbounded
   */
  validateMemoryUsage(tracker: UnifiedAnalyticsTracker): {
    currentMemoryUsage: number;
    eventsInQueue: number;
    memoryPerEvent: number;
    acceptable: boolean;
  } {
    const memoryUsage = (performance as any).memory?.usedJSHeapSize || 0;
    const queueSize = (tracker as any).queue?.length || 0;

    // Calculate average memory per event
    const memoryPerEvent = queueSize > 0 ? memoryUsage / queueSize : 0;

    // Memory is acceptable if:
    // - Less than 10MB for 10,000 events
    // - Less than 1KB per event
    const acceptable = memoryUsage < 10 * 1024 * 1024 && memoryPerEvent < 1024;

    return {
      currentMemoryUsage: memoryUsage,
      eventsInQueue: queueSize,
      memoryPerEvent,
      acceptable,
    };
  }

  /**
   * Generate performance report
   */
  generateReport(): {
    summary: {
      totalMeasurements: number;
      averageTrackDuration: number;
      maxTrackDuration: number;
      p95TrackDuration: number;
      p99TrackDuration: number;
      blockedMainThreadCount: number;
    };
    status: 'PASS' | 'FAIL' | 'WARNING';
    recommendations: string[];
  } {
    if (this.metrics.length === 0) {
      return {
        summary: {
          totalMeasurements: 0,
          averageTrackDuration: 0,
          maxTrackDuration: 0,
          p95TrackDuration: 0,
          p99TrackDuration: 0,
          blockedMainThreadCount: 0,
        },
        status: 'FAIL',
        recommendations: ['No performance metrics collected. Run performance tests first.'],
      };
    }

    const durations = this.metrics.map(m => m.trackCallDuration);
    const sorted = [...durations].sort((a, b) => a - b);

    const average = durations.reduce((a, b) => a + b, 0) / durations.length;
    const max = Math.max(...durations);
    const p95 = sorted[Math.floor(sorted.length * 0.95)];
    const p99 = sorted[Math.floor(sorted.length * 0.99)];

    // Count times where main thread was blocked (> 16ms)
    const blockedMainThreadCount = durations.filter(d => d > 16).length;

    // Determine status
    let status: 'PASS' | 'FAIL' | 'WARNING' = 'PASS';
    const recommendations: string[] = [];

    // Performance criteria:
    // - Average track call < 1ms
    // - Max track call < 5ms
    // - P99 < 10ms
    // - No main thread blocking

    if (average > 1) {
      status = 'WARNING';
      recommendations.push(`Average track duration (${average.toFixed(2)}ms) exceeds 1ms target`);
    }

    if (max > 5) {
      status = 'FAIL';
      recommendations.push(`Max track duration (${max.toFixed(2)}ms) exceeds 5ms limit`);
    }

    if (p99 > 10) {
      status = 'FAIL';
      recommendations.push(`P99 track duration (${p99.toFixed(2)}ms) exceeds 10ms limit`);
    }

    if (blockedMainThreadCount > 0) {
      status = 'FAIL';
      recommendations.push(`${blockedMainThreadCount} events blocked main thread (> 16ms)`);
    }

    if (recommendations.length === 0) {
      recommendations.push('✅ All performance targets met!');
    }

    return {
      summary: {
        totalMeasurements: this.metrics.length,
        averageTrackDuration: average,
        maxTrackDuration: max,
        p95TrackDuration: p95,
        p99TrackDuration: p99,
        blockedMainThreadCount,
      },
      status,
      recommendations,
    };
  }

  /**
   * Add metric to history (maintains max size)
   */
  private addMetric(metric: PerformanceMetrics): void {
    this.metrics.push(metric);

    // Keep only the most recent metrics
    if (this.metrics.length > this.MAX_METRICS) {
      this.metrics = this.metrics.slice(-this.MAX_METRICS);
    }
  }

  /**
   * Clear all metrics
   */
  clearMetrics(): void {
    this.metrics = [];
  }

  /**
   * Get metrics history
   */
  getMetrics(): PerformanceMetrics[] {
    return [...this.metrics];
  }
}

// Global validator instance
let validatorInstance: AnalyticsPerformanceValidator | null = null;

export function getPerformanceValidator(): AnalyticsPerformanceValidator {
  if (!validatorInstance) {
    validatorInstance = new AnalyticsPerformanceValidator();
  }
  return validatorInstance;
}

/**
 * Run comprehensive performance validation
 */
export async function validateAnalyticsPerformance(): Promise<{
  trackPerformance: PerformanceMetrics;
  rapidTracking: ReturnType<AnalyticsPerformanceValidator['validateRapidTracking']>;
  memoryUsage: ReturnType<AnalyticsPerformanceValidator['validateMemoryUsage']>;
  report: ReturnType<AnalyticsPerformanceValidator['generateReport']>;
}> {
  const validator = getPerformanceValidator();
  validator.clearMetrics();

  // Get tracker from window
  const tracker = (window as any).analyticsTracker;
  if (!tracker) {
    console.log('⚠️ [Performance] Analytics tracker not initialized - skipping validation');
    console.log('ℹ️ [Performance] This is normal if analytics hasn\'t been set up yet');
    return {
      trackPerformance: {
        duration: 0,
        eventCount: 0,
        averageTime: 0,
        status: 'skipped'
      },
      rapidTracking: {
        duration: 0,
        eventCount: 0,
        averageTime: 0,
        status: 'skipped'
      },
      memoryUsage: {
        before: 0,
        after: 0,
        delta: 0,
        status: 'skipped'
      },
      report: {
        status: 'skipped',
        summary: [],
        recommendations: ['Analytics tracker not initialized - set up analytics to enable performance monitoring']
      }
    };
  }

  console.log('🔍 [Performance] Starting analytics performance validation...');

  // Test 1: Single track call performance
  console.log('📊 [Performance] Testing single track call...');
  const trackPerformance = validator.validateTrackPerformance(tracker, 'performance_test_single');

  // Test 2: Rapid tracking performance
  console.log('📊 [Performance] Testing rapid tracking (100 events)...');
  const rapidTracking = validator.validateRapidTracking(tracker, 100);

  // Test 3: Memory usage
  console.log('📊 [Performance] Testing memory usage...');
  const memoryUsage = validator.validateMemoryUsage(tracker);

  // Generate report
  const report = validator.generateReport();

  console.log('✅ [Performance] Validation complete!');
  console.table(report.summary);
  console.log('Status:', report.status);
  console.log('Recommendations:', report.recommendations);

  return {
    trackPerformance,
    rapidTracking,
    memoryUsage,
    report,
  };
}

/**
 * Make validator available globally for console debugging
 */
if (typeof window !== 'undefined') {
  (window as any).analyticsPerformanceValidator = {
    validate: validateAnalyticsPerformance,
    getMetrics: () => getPerformanceValidator().getMetrics(),
    generateReport: () => getPerformanceValidator().generateReport(),
    clear: () => getPerformanceValidator().clearMetrics(),
  };
}
