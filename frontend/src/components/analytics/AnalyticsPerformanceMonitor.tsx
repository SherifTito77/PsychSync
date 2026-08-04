/**
 * Analytics Performance Monitor
 *
 * ⚡️ PERFORMANCE OPTIMIZED:
 * - Memoized with React.memo to prevent unnecessary re-renders
 * - Update interval increased from 2s to 5s to reduce overhead
 * - Early return in production (no component overhead)
 *
 * Real-time monitoring of analytics performance to ensure it doesn't slow down user interactions
 *
 * Shows:
 * - Average track() call duration
 * - Max track() call duration
 * - Memory usage
 * - Queue size
 * - Performance status (PASS/FAIL/WARNING)
 */

import { useState, useEffect, memo } from 'react';

interface PerformanceData {
  averageTrackDuration: number;
  maxTrackDuration: number;
  p95TrackDuration: number;
  p99TrackDuration: number;
  memoryUsage: number;
  queueSize: number;
  status: 'PASS' | 'FAIL' | 'WARNING';
}

export const AnalyticsPerformanceMonitor = memo(function AnalyticsPerformanceMonitor() {
  const [performance, setPerformance] = useState<PerformanceData>({
    averageTrackDuration: 0,
    maxTrackDuration: 0,
    p95TrackDuration: 0,
    p99TrackDuration: 0,
    memoryUsage: 0,
    queueSize: 0,
    status: 'PASS',
  });
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Check if performance validator is available
    if (!(window as any).analyticsPerformanceValidator) {
      return;
    }

    // ⚡️ PERFORMANCE: Update interval increased from 2s to 5s to reduce overhead
    const interval = setInterval(() => {
      const validator = (window as any).analyticsPerformanceValidator;
      const report = validator.generateReport();
      const tracker = (window as any).analyticsTracker;

      const metrics = report.summary;

      setPerformance({
        averageTrackDuration: metrics.averageTrackDuration,
        maxTrackDuration: metrics.maxTrackDuration,
        p95TrackDuration: metrics.p95TrackDuration,
        p99TrackDuration: metrics.p99TrackDuration,
        memoryUsage: (performance as any).memory?.usedJSHeapSize || 0,
        queueSize: tracker?.queue?.length || 0,
        status: report.status,
      });
    }, 5000); // Changed from 2000 to 5000

    return () => clearInterval(interval);
  }, []);

  // Don't render if not in development
  if (import.meta.env.MODE !== 'development') {
    return null;
  }

  const formatDuration = (ms: number) => {
    if (ms < 0.01) return '< 0.01ms';
    return `${ms.toFixed(2)}ms`;
  };

  const formatMemory = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  const statusColors = {
    PASS: 'text-green-500 bg-green-50 border-green-200',
    WARNING: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    FAIL: 'text-red-600 bg-red-50 border-red-200',
  };

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={() => setVisible(!visible)}
        className="fixed bottom-4 left-4 z-50 p-2 bg-white border border-gray-300 rounded-lg shadow-lg hover:bg-gray-50"
        title="Toggle Analytics Performance Monitor"
      >
        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      </button>

      {/* Performance Panel */}
      {visible && (
        <div className="fixed bottom-16 left-4 z-50 w-80 bg-white border border-gray-300 rounded-lg shadow-xl">
          {/* Header */}
          <div className="p-3 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-800">Analytics Performance</h3>
            <span className={`px-2 py-1 text-xs font-medium rounded border ${statusColors[performance.status]}`}>
              {performance.status}
            </span>
          </div>

          {/* Metrics */}
          <div className="p-3 space-y-2 text-xs">
            {/* Track Duration */}
            <div className="space-y-1">
              <div className="flex justify-between text-gray-600">
                <span>Avg track() duration:</span>
                <span className={performance.averageTrackDuration > 1 ? 'text-yellow-600' : 'text-green-600'}>
                  {formatDuration(performance.averageTrackDuration)}
                </span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Max track() duration:</span>
                <span className={performance.maxTrackDuration > 5 ? 'text-red-600' : 'text-green-600'}>
                  {formatDuration(performance.maxTrackDuration)}
                </span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>P95 track() duration:</span>
                <span>{formatDuration(performance.p95TrackDuration)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>P99 track() duration:</span>
                <span className={performance.p99TrackDuration > 10 ? 'text-red-600' : 'text-green-600'}>
                  {formatDuration(performance.p99TrackDuration)}
                </span>
              </div>
            </div>

            {/* Divider */}
            <hr className="my-2" />

            {/* Memory & Queue */}
            <div className="space-y-1">
              <div className="flex justify-between text-gray-600">
                <span>Memory usage:</span>
                <span>{formatMemory(performance.memoryUsage)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Queue size:</span>
                <span>{performance.queueSize} events</span>
              </div>
            </div>

            {/* Performance Targets */}
            <hr className="my-2" />
            <div className="text-gray-500">
              <div className="font-medium mb-1">Performance Targets:</div>
              <ul className="space-y-0.5 ml-3">
                <li>✓ track() call: &lt; 1ms</li>
                <li>✓ Max track(): &lt; 5ms</li>
                <li>✓ P99: &lt; 10ms</li>
                <li>✓ No main thread blocking (&gt; 16ms)</li>
              </ul>
            </div>

            {/* Actions */}
            <hr className="my-2" />
            <div className="flex space-x-2">
              <button
                onClick={() => (window as any).analyticsPerformanceValidator?.validate()}
                className="flex-1 px-3 py-1.5 bg-blue-500 text-white text-xs rounded hover:bg-blue-600"
              >
                Run Test
              </button>
              <button
                onClick={() => (window as any).analyticsPerformanceValidator?.clear()}
                className="flex-1 px-3 py-1.5 bg-gray-500 text-white text-xs rounded hover:bg-gray-600"
              >
                Clear
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
});
