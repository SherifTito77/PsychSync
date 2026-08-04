/**
 * Anomaly Detection Visualization Component
 * Displays ML-detected anomalies in email patterns
 */

import React, { useState, useEffect } from 'react';
import {
  ExclamationTriangleIcon,
  ChartBarIcon,
  BellIcon,
  InformationCircleIcon,
  XCircleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';

interface Anomaly {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  detected_at: string;
  details?: {
    current_value?: number;
    baseline_value?: number;
    zscore?: number;
    threshold?: number;
  };
  dismissed: boolean;
}

interface AnomalyHistory {
  date: string;
  total_anomalies: number;
  critical_count: number;
  high_count: number;
}

const AnomalyDetectionVisualization: React.FC = () => {
  console.log('🔍 AnomalyDetectionVisualization component rendering!');
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [history, setHistory] = useState<AnomalyHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null);
  const [showDismissed, setShowDismissed] = useState(false);

  useEffect(() => {
    fetchAnomalies();
    fetchAnomalyHistory();
  }, []);

  const fetchAnomalies = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      // TODO: Replace with actual API endpoint
      // const response = await fetch('/api/v1/anomaly-detection/recent', {
      //   headers: { Authorization: `Bearer ${token}` }
      // });
      // const data = await response.json();
      // setAnomalies(data.anomalies);

      // Mock data
      const mockAnomalies: Anomaly[] = [
        {
          id: '1',
          type: 'email_volume',
          severity: 'critical',
          message: 'Email volume is 4.5x higher than normal',
          detected_at: new Date(Date.now() - 30 * 60000).toISOString(),
          details: {
            current_value: 225,
            baseline_value: 50,
            zscore: 4.5,
            threshold: 2.5,
          },
          dismissed: false,
        },
        {
          id: '2',
          type: 'category_spike',
          severity: 'high',
          message: 'Security emails are 3.2x higher than normal',
          detected_at: new Date(Date.now() - 2 * 60 * 60000).toISOString(),
          details: {
            current_value: 81,
            baseline_value: 25,
            zscore: 3.2,
            threshold: 2.0,
          },
          dismissed: false,
        },
        {
          id: '3',
          type: 'sender_diversity',
          severity: 'medium',
          message: 'Unusually high number of unique senders',
          detected_at: new Date(Date.now() - 4 * 60 * 60000).toISOString(),
          details: {
            current_value: 45,
            baseline_value: 20,
          },
          dismissed: false,
        },
        {
          id: '4',
          type: 'time_pattern',
          severity: 'low',
          message: 'Activity at 3:00 AM is 1.8x lower than normal',
          detected_at: new Date(Date.now() - 6 * 60 * 60000).toISOString(),
          dismissed: false,
        },
      ];

      setAnomalies(mockAnomalies);
    } catch (error) {
      console.error('Failed to fetch anomalies:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnomalyHistory = async () => {
    try {
      // Mock history data - last 7 days
      const mockHistory: AnomalyHistory[] = Array.from({ length: 7 }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (6 - i));
        return {
          date: date.toISOString().split('T')[0],
          total_anomalies: Math.floor(Math.random() * 5) + 1,
          critical_count: Math.random() > 0.7 ? 1 : 0,
          high_count: Math.floor(Math.random() * 3),
        };
      });

      setHistory(mockHistory);
    } catch (error) {
      console.error('Failed to fetch history:', error);
    }
  };

  const handleDismiss = async (anomalyId: string) => {
    setAnomalies(
      anomalies.map((a) => (a.id === anomalyId ? { ...a, dismissed: true } : a))
    );

    // TODO: Make API call
    // await fetch(`/api/v1/anomaly-detection/${anomalyId}/dismiss`, {
    //   method: 'POST',
    //   headers: { Authorization: `Bearer ${token}` },
    // });
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return 'red';
      case 'high':
        return 'orange';
      case 'medium':
        return 'yellow';
      case 'low':
        return 'blue';
      default:
        return 'gray';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return <ExclamationTriangleIcon className="w-5 h-5" />;
      case 'medium':
        return <BellIcon className="w-5 h-5" />;
      default:
        return <InformationCircleIcon className="w-5 h-5" />;
    }
  };

  const filteredAnomalies = showDismissed
    ? anomalies
    : anomalies.filter((a) => !a.dismissed);

  const activeAnomalies = anomalies.filter((a) => !a.dismissed);
  const criticalCount = activeAnomalies.filter((a) => a.severity === 'critical').length;
  const highCount = activeAnomalies.filter((a) => a.severity === 'high').length;

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center">
          <ExclamationTriangleIcon className="w-7 h-7 mr-2 text-orange-500" />
          Anomaly Detection
        </h2>
        <p className="text-gray-600">
          ML-powered detection of unusual email patterns and behaviors
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Active Anomalies</p>
              <p className="text-3xl font-bold text-gray-900">{activeAnomalies.length}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <ChartBarIcon className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Critical</p>
              <p className="text-3xl font-bold text-red-600">{criticalCount}</p>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">High</p>
              <p className="text-3xl font-bold text-orange-600">{highCount}</p>
            </div>
            <div className="p-3 bg-orange-100 rounded-lg">
              <BellIcon className="w-6 h-6 text-orange-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Risk Level</p>
              <p className="text-xl font-bold text-gray-900">
                {criticalCount > 0 ? 'CRITICAL' : highCount > 1 ? 'HIGH' : 'NORMAL'}
              </p>
            </div>
            <div
              className={`p-3 rounded-lg ${
                criticalCount > 0
                  ? 'bg-red-100'
                  : highCount > 1
                  ? 'bg-orange-100'
                  : 'bg-green-100'
              }`}
            >
              {criticalCount > 0 ? (
                <XCircleIcon className="w-6 h-6 text-red-600" />
              ) : (
                <CheckCircleIcon className="w-6 h-6 text-green-600" />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 7-Day History Chart */}
      <div className="bg-white rounded-lg shadow p-6 mb-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          7-Day Anomaly History
        </h3>
        <div className="flex items-end justify-between h-40 gap-2">
          {history.map((day, idx) => (
            <div key={idx} className="flex-1 flex flex-col items-center">
              <div
                className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600"
                style={{
                  height: `${Math.min(day.total_anomalies * 20, 100)}%`,
                  minHeight: '4px',
                }}
                title={`${day.total_anomalies} anomalies`}
              />
              <div className="mt-2 text-xs text-gray-500 text-center">
                {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
              </div>
              <div className="text-xs font-medium text-gray-900">
                {day.total_anomalies}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Recent Anomalies ({filteredAnomalies.length})
        </h3>
        <label className="flex items-center text-sm text-gray-600">
          <input
            type="checkbox"
            checked={showDismissed}
            onChange={(e) => setShowDismissed(e.target.checked)}
            className="mr-2"
          />
          Show dismissed
        </label>
      </div>

      {/* Anomalies List */}
      <div className="space-y-3">
        {filteredAnomalies.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <CheckCircleIcon className="mx-auto h-12 w-12 text-green-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              No anomalies detected
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Your email patterns are within normal ranges
            </p>
          </div>
        ) : (
          filteredAnomalies.map((anomaly) => (
            <div
              key={anomaly.id}
              className={`bg-white rounded-lg shadow p-4 border-l-4 ${
                anomaly.dismissed ? 'opacity-50' : ''
              } border-${getSeverityColor(anomaly.severity)}-500`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <div
                    className={`p-2 rounded-lg bg-${getSeverityColor(
                      anomaly.severity
                    )}-100 mt-1`}
                  >
                    <div className={getSeverityColor(anomaly.severity) === 'red' ? 'text-red-600' : getSeverityColor(anomaly.severity) === 'orange' ? 'text-orange-600' : getSeverityColor(anomaly.severity) === 'yellow' ? 'text-yellow-600' : 'text-blue-600'}>
                      {getSeverityIcon(anomaly.severity)}
                    </div>
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-semibold text-gray-900 capitalize">
                        {anomaly.type.replace('_', ' ')}
                      </h4>
                      <span
                        className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                          anomaly.severity === 'critical'
                            ? 'bg-red-100 text-red-800'
                            : anomaly.severity === 'high'
                            ? 'bg-orange-100 text-orange-800'
                            : anomaly.severity === 'medium'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {anomaly.severity.toUpperCase()}
                      </span>
                      {anomaly.dismissed && (
                        <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-600">
                          DISMISSED
                        </span>
                      )}
                    </div>

                    <p className="text-gray-700 mb-2">{anomaly.message}</p>

                    {anomaly.details && (
                      <div className="bg-gray-50 rounded p-3 text-sm space-y-1">
                        {anomaly.details.current_value !== undefined && (
                          <div className="flex justify-between">
                            <span className="text-gray-500">Current Value:</span>
                            <span className="font-medium text-gray-900">
                              {anomaly.details.current_value}
                            </span>
                          </div>
                        )}
                        {anomaly.details.baseline_value !== undefined && (
                          <div className="flex justify-between">
                            <span className="text-gray-500">Baseline:</span>
                            <span className="font-medium text-gray-900">
                              {anomaly.details.baseline_value}
                            </span>
                          </div>
                        )}
                        {anomaly.details.zscore !== undefined && (
                          <div className="flex justify-between">
                            <span className="text-gray-500">Z-Score:</span>
                            <span className="font-medium text-gray-900">
                              {anomaly.details.zscore.toFixed(2)}
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    <p className="text-xs text-gray-500 mt-2">
                      Detected {new Date(anomaly.detected_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                {!anomaly.dismissed && (
                  <button
                    onClick={() => handleDismiss(anomaly.id)}
                    className="ml-4 px-3 py-1 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Dismiss
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Info Panel */}
      <div className="mt-8 p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <div className="flex">
          <InformationCircleIcon className="h-5 w-5 text-gray-400 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-gray-900">
              How Anomaly Detection Works
            </h3>
            <div className="mt-2 text-sm text-gray-600 space-y-1">
              <p>• <strong>Z-Score Analysis:</strong> Detects statistical deviations from baseline</p>
              <p>• <strong>IQR Method:</strong> Identifies outliers using quartile ranges</p>
              <p>• <strong>Pattern Recognition:</strong> Monitors volume, categories, timing, and senders</p>
              <p>• <strong>Risk Assessment:</strong> Critical/High anomalies require immediate attention</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnomalyDetectionVisualization;
