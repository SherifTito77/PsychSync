/**
 * Analytics Health Metrics Demo Component
 *
 * Demonstrates how to use the analytics health metrics API programmatically
 * This is an example component showing the useAnalytics hook with health monitoring
 */

import React, { useState, useEffect } from 'react';
import { useAnalytics } from '../../services/analytics/tracker';

export const AnalyticsHealthDemo: React.FC = () => {
  const { getHealthMetrics, setSampleRate, track } = useAnalytics();
  const [health, setHealth] = useState<ReturnType<typeof getHealthMetrics> | null>(null);
  const [sampleRate, setSampleRateState] = useState(1.0);

  // Update health metrics every 5 seconds
  useEffect(() => {
    const updateMetrics = () => {
      try {
        const metrics = getHealthMetrics();
        setHealth(metrics);
      } catch (error) {
        console.error('Failed to get health metrics:', error);
      }
    };

    updateMetrics();
    const interval = setInterval(updateMetrics, 5000);

    return () => clearInterval(interval);
  }, [getHealthMetrics]);

  const handleSampleRateChange = (newRate: number) => {
    setSampleRateState(newRate);
    setSampleRate(newRate);
    console.log(`Sample rate changed to ${(newRate * 100).toFixed(0)}%`);
  };

  const trackTestEvents = () => {
    // Track some test events to populate the analytics
    for (let i = 0; i < 10; i++) {
      track('test_event', {
        testNumber: i,
        timestamp: new Date().toISOString()
      });
    }
    console.log('Tracked 10 test events');
  };

  if (!health) {
    return (
      <div className="p-6 bg-gray-50 rounded-lg">
        <h2 className="text-xl font-bold mb-4">Analytics Health Metrics Demo</h2>
        <p className="text-gray-600">Loading health metrics...</p>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-md max-w-4xl">
      <h2 className="text-2xl font-bold mb-6 text-gray-900">
        📊 Analytics Health Metrics Demo
      </h2>

      {/* Success Rate Display */}
      <div className="mb-6 p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-lg border border-green-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-green-800">Success Rate</p>
            <p className="text-3xl font-bold text-green-900">{health.successRate}</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-semibold text-green-800">Total Events</p>
            <p className="text-3xl font-bold text-green-900">{health.totalEvents.toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Successful Events */}
        <div className="p-4 bg-green-50 rounded-lg border border-green-200">
          <p className="text-xs font-semibold text-green-700 uppercase">Successful Events</p>
          <p className="text-2xl font-bold text-green-900">{health.successfulEvents.toLocaleString()}</p>
        </div>

        {/* Failed Events */}
        <div className="p-4 bg-red-50 rounded-lg border border-red-200">
          <p className="text-xs font-semibold text-red-700 uppercase">Failed Events</p>
          <p className="text-2xl font-bold text-red-900">{health.failedEvents.toLocaleString()}</p>
        </div>

        {/* Queued Events */}
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-xs font-semibold text-blue-700 uppercase">In Queue</p>
          <p className="text-2xl font-bold text-blue-900">{health.queueSize}</p>
        </div>

        {/* Failed Batches */}
        <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
          <p className="text-xs font-semibold text-orange-700 uppercase">Failed Batches</p>
          <p className="text-2xl font-bold text-orange-900">{health.failedBatchesCount}</p>
        </div>

        {/* Batches Sent */}
        <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
          <p className="text-xs font-semibold text-purple-700 uppercase">Batches Sent</p>
          <p className="text-2xl font-bold text-purple-900">{health.batchesSent}</p>
        </div>

        {/* sendBeacon Failures */}
        <div className="p-4 bg-pink-50 rounded-lg border border-pink-200">
          <p className="text-xs font-semibold text-pink-700 uppercase">sendBeacon Failures</p>
          <p className="text-2xl font-bold text-pink-900">{health.sendBeaconFailures}</p>
        </div>

        {/* Average Delivery Time */}
        <div className="p-4 bg-teal-50 rounded-lg border border-teal-200">
          <p className="text-xs font-semibold text-teal-700 uppercase">Avg Delivery Time</p>
          <p className="text-2xl font-bold text-teal-900">{health.averageDeliveryTime.toFixed(0)}ms</p>
        </div>

        {/* Current Sample Rate */}
        <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-200">
          <p className="text-xs font-semibold text-indigo-700 uppercase">Current Sample Rate</p>
          <p className="text-2xl font-bold text-indigo-900">{(health.sampleRate * 100).toFixed(0)}%</p>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-3 text-gray-900">System Status</h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">Under Stress:</span>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
              health.isUnderStress
                ? 'bg-red-100 text-red-800'
                : 'bg-green-100 text-green-800'
            }`}>
              {health.isUnderStress ? '⚠️ YES' : '✅ NO'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">Last Successful Send:</span>
            <span className="text-sm text-gray-900">
              {health.lastSuccessfulSend
                ? new Date(health.lastSuccessfulSend).toLocaleTimeString()
                : 'Never'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">Last Failure:</span>
            <span className="text-sm text-gray-900">
              {health.lastFailure
                ? new Date(health.lastFailure).toLocaleTimeString()
                : 'None'}
            </span>
          </div>
        </div>
      </div>

      {/* Sample Rate Control */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h3 className="text-lg font-semibold mb-3 text-gray-900">Event Sampling Control</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sample Rate: {(sampleRate * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={sampleRate}
              onChange={(e) => handleSampleRateChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleSampleRateChange(1.0)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors text-sm"
            >
              100% (Normal)
            </button>
            <button
              onClick={() => handleSampleRateChange(0.5)}
              className="px-4 py-2 bg-yellow-600 text-white rounded-lg font-semibold hover:bg-yellow-700 transition-colors text-sm"
            >
              50% (Moderate)
            </button>
            <button
              onClick={() => handleSampleRateChange(0.1)}
              className="px-4 py-2 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 transition-colors text-sm"
            >
              10% (Low)
            </button>
          </div>
        </div>
      </div>

      {/* Test Actions */}
      <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-3 text-gray-900">Test Actions</h3>
        <div className="space-y-2">
          <button
            onClick={trackTestEvents}
            className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
          >
            Track 10 Test Events
          </button>
          <button
            onClick={() => {
              const metrics = getHealthMetrics();
              console.log('Current Health Metrics:', metrics);
              alert('Health metrics logged to console - check browser DevTools!');
            }}
            className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg font-semibold hover:bg-gray-700 transition-colors"
          >
            Log Health Metrics to Console
          </button>
          <button
            onClick={() => {
              const failed = localStorage.getItem('failed_analytics_events');
              const count = failed ? JSON.parse(failed).length : 0;
              alert(`Failed events in localStorage: ${count}\n\nOpen DevTools Console to see full details.`);
              console.log('Failed Events:', failed ? JSON.parse(failed) : []);
            }}
            className="w-full px-4 py-2 bg-orange-600 text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors"
          >
            Check Failed Events in localStorage
          </button>
        </div>
      </div>

      {/* Code Example */}
      <div className="mt-6 p-4 bg-gray-900 rounded-lg">
        <h3 className="text-lg font-semibold mb-3 text-white">Usage Example</h3>
        <pre className="text-sm text-green-400 overflow-x-auto">
{`// In your component:
import { useAnalytics } from '@/services/analytics/tracker';

function MyComponent() {
  const { getHealthMetrics, setSampleRate, track } = useAnalytics();

  // Get current health
  const health = getHealthMetrics();
  console.log('Success rate:', health.successRate);

  // Adjust sampling under load
  if (health.queueSize > 50) {
    setSampleRate(0.5); // Sample 50% of events
  }

  // Track events normally
  track('user_action', { action: 'button_click' });

  return <div>...</div>;
}`}
        </pre>
      </div>
    </div>
  );
};

export default AnalyticsHealthDemo;
