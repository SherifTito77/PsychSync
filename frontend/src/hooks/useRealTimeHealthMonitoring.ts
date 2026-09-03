/**
 * Real-Time Health Monitoring Hook
 *
 * Provides real-time health monitoring capabilities using WebSocket/SSE connections.
 * Automatically pushes health updates and alerts to the client.
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import type { HealthAlert, RealTimeHealthUpdate, StressLevel } from '@/types/healthMonitoring';

interface UseRealTimeHealthMonitoringOptions {
  enabled?: boolean;
  onHealthAlert?: (alert: HealthAlert) => void;
  onHealthUpdate?: (update: RealTimeHealthUpdate) => void;
  updateInterval?: number; // Fallback polling interval in ms
}

interface HealthMonitoringState {
  isConnected: boolean;
  currentStressLevel?: StressLevel;
  latestUpdate?: RealTimeHealthUpdate;
  alerts: HealthAlert[];
  error?: string;
}

export const useRealTimeHealthMonitoring = (
  options: UseRealTimeHealthMonitoringOptions = {}
) => {
  const {
    enabled = false, // DISABLED: WebSocket endpoint not implemented yet
    onHealthAlert,
    onHealthUpdate,
    updateInterval = 60000, // 1 minute default
  } = options;

  const [state, setState] = useState<HealthMonitoringState>({
    isConnected: false,
    alerts: [],
  });

  const wsRef = useRef<WebSocket | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Handle incoming health alert
   */
  const handleHealthAlert = useCallback((alert: HealthAlert) => {
    setState(prev => ({
      ...prev,
      alerts: [alert, ...prev.alerts].slice(0, 10), // Keep last 10 alerts
    }));

    // Log critical/high severity alerts
    if (alert.severity === 'critical' || alert.severity === 'high') {
      console.error('Health Alert:', alert.message);
    }

    // Call custom handler if provided
    onHealthAlert?.(alert);
  }, [onHealthAlert]);

  /**
   * Handle real-time health update
   */
  const handleHealthUpdate = useCallback((update: RealTimeHealthUpdate) => {
    setState(prev => ({
      ...prev,
      latestUpdate: update,
      currentStressLevel: update.stress_level || prev.currentStressLevel,
    }));

    onHealthUpdate?.(update);
  }, [onHealthUpdate]);

  /**
   * Acknowledge an alert
   */
  const acknowledgeAlert = useCallback((alertId: string) => {
    setState(prev => ({
      ...prev,
      alerts: prev.alerts.map(alert =>
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      ),
    }));

    // TODO: Send acknowledgement to backend
    // await api.post(`/health-monitoring/alerts/${alertId}/acknowledge`);
  }, []);

  /**
   * Clear all alerts
   */
  const clearAlerts = useCallback(() => {
    setState(prev => ({ ...prev, alerts: [] }));
  }, []);

  /**
   * Connect to WebSocket for real-time updates
   */
  const connectWebSocket = useCallback(() => {
    // WebSocket endpoint not implemented yet - silently skip
    console.debug('Health monitoring WebSocket is disabled - endpoint not implemented on backend');
    return;

    try {
      const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/health-monitoring`;

      // Attempt WebSocket connection
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('Health monitoring WebSocket connected');
        setState(prev => ({ ...prev, isConnected: true, error: undefined }));
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'health_alert') {
            handleHealthAlert(data as HealthAlert);
          } else if (data.type === 'health_update') {
            handleHealthUpdate(data as RealTimeHealthUpdate);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Don't keep trying to reconnect - WebSocket endpoint doesn't exist yet
        disconnect();
      };

      wsRef.current.onclose = () => {
        console.log('Health monitoring WebSocket disconnected');
        setState(prev => ({ ...prev, isConnected: false }));

        // Don't auto-reconnect - WebSocket endpoint doesn't exist yet
        // This prevents infinite reconnection attempts
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      // Silently fail - WebSocket endpoint doesn't exist yet
      setState(prev => ({
        ...prev,
        isConnected: false,
      }));
    }
  }, []); // Empty deps - prevent infinite loop

  /**
   * Start polling for updates (fallback)
   */
  const startPolling = useCallback(async () => {
    // Disable polling for now - endpoint doesn't exist yet
    // This prevents unnecessary API calls and errors
    return;

    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    pollIntervalRef.current = setInterval(async () => {
      try {
        // Fetch latest health update
        const token = localStorage.getItem('access_token');
        if (!token) return;

        const response = await fetch('/api/v1/health-monitoring/latest-update', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const update: RealTimeHealthUpdate = await response.json();
          handleHealthUpdate(update);
        }
      } catch (error) {
        // Silently fail - polling endpoint doesn't exist yet
        console.debug('Polling not available yet');
      }
    }, updateInterval);
  }, [updateInterval]);

  /**
   * Disconnect and cleanup
   */
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setState(prev => ({
      ...prev,
      isConnected: false,
    }));
  }, []);

  // Setup connection on mount
  useEffect(() => {
    if (!enabled) return;

    // Try WebSocket first, fall back to polling
    // Note: WebSocket and polling endpoints don't exist yet, so this will silently fail
    connectWebSocket();
    startPolling();

    return () => {
      disconnect();
    };
  }, [enabled]); // Only depend on 'enabled' - prevent infinite loop

  return {
    ...state,
    acknowledgeAlert,
    clearAlerts,
    disconnect,
  };
};

export default useRealTimeHealthMonitoring;
