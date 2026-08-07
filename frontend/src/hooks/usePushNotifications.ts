/**
 * React Hook for Push Notifications
 *
 * Custom hook for managing FCM push notifications in React components.
 * Provides methods for initialization, permission handling, and status checking.
 *
 * Usage:
 * ```tsx
 * const { status, register, sendTest } = usePushNotifications();
 * ```
 */

import { useState, useEffect, useCallback } from 'react';
import { pushNotificationService, NotificationPermission } from '@/services/pushNotifications';

interface UsePushNotificationsOptions {
  /**
   * Function to get FCM token from the mobile app
   * This should be provided by the mobile app bridge
   */
  getFCMToken?: () => Promise<string | null>;

  /**
   * Auto-initialize on mount
   */
  autoInit?: boolean;
}

interface UsePushNotificationsReturn {
  // State
  status: NotificationPermission;
  isInitialized: boolean;
  isLoading: boolean;
  error: string | null;

  // Token info
  hasActiveTokens: boolean;
  tokenCount: number;

  // Methods
  requestPermission: () => Promise<boolean>;
  register: () => Promise<boolean>;
  sendTest: () => Promise<void>;
  checkStatus: () => Promise<void>;
}

export function usePushNotifications(
  options: UsePushNotificationsOptions = {}
): UsePushNotificationsReturn {
  const { getFCMToken, autoInit = false } = options;

  const [status, setStatus] = useState<NotificationPermission>('default');
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasActiveTokens, setHasActiveTokens] = useState(false);
  const [tokenCount, setTokenCount] = useState(0);

  /**
   * Request notification permission from the user
   */
  const requestPermission = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const granted = await pushNotificationService.requestPermission();
      setStatus(granted ? 'granted' : 'denied');
      return granted;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to request permission';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Register device token and initialize push notifications
   */
  const register = useCallback(async () => {
    if (!getFCMToken) {
      setError('getFCMToken function not provided');
      return false;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Check permission first
      let currentStatus = pushNotificationService.getPermissionStatus();

      if (currentStatus === 'default') {
        const granted = await requestPermission();
        if (!granted) {
          setError('Notification permission denied');
          return false;
        }
        currentStatus = 'granted';
      }

      if (currentStatus !== 'granted') {
        setError('Notification permission not granted');
        return false;
      }

      // Initialize with backend
      const success = await pushNotificationService.initialize(getFCMToken);

      if (success) {
        setIsInitialized(true);
        await checkStatus();
      }

      return success;

    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to register';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [getFCMToken, requestPermission]);

  /**
   * Send a test notification
   */
  const sendTest = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      await pushNotificationService.sendTestNotification();

      // Show success message
      if ('Notification' in window && status === 'granted') {
        new Notification('Test Notification', {
          body: 'If you see this, push notifications are working!',
          icon: '/favicon.ico',
        });
      }

    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to send test';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [status]);

  /**
   * Check current notification status and token info
   */
  const checkStatus = useCallback(async () => {
    try {
      const [currentStatus, notifStatus] = await Promise.all([
        Promise.resolve(pushNotificationService.getPermissionStatus()),
        pushNotificationService.getStatus(),
      ]);

      setStatus(currentStatus);
      setHasActiveTokens(notifStatus.push_enabled);
      setTokenCount(notifStatus.active_devices);

      setIsInitialized(notifStatus.push_enabled);

    } catch (err) {
      console.error('Failed to check status:', err);
    }
  }, []);

  // Auto-initialize on mount if requested
  useEffect(() => {
    if (autoInit && getFCMToken) {
      register();
    } else {
      // Just check status
      checkStatus();
    }
  }, [autoInit, getFCMToken]);

  return {
    // State
    status,
    isInitialized,
    isLoading,
    error,
    hasActiveTokens,
    tokenCount,

    // Methods
    requestPermission,
    register,
    sendTest,
    checkStatus,
  };
}
