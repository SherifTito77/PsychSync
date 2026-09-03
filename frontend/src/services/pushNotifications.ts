/**
 * Push Notification Service
 *
 * Manages FCM push notification registration and preferences
 * for mobile apps (iOS and Android).
 *
 * Features:
 * - Device token registration
 * - Permission handling
 * - Notification preferences management
 * - Test notification sending
 */

import api from './api';

// =============================================================================
// Types
// =============================================================================

export interface DeviceInfo {
  platform: 'ios' | 'android';
  device_id?: string;
  device_model?: string;
  os_version?: string;
  app_version?: string;
}

export interface TokenRegistrationRequest {
  token: string;
  platform: 'ios' | 'android';
  device_id?: string;
  device_model?: string;
  os_version?: string;
  app_version?: string;
}

export interface NotificationDelivery {
  success: boolean;
  tokens_sent: number;
  successful: number;
  failed: number;
  skipped?: boolean;
  reason?: string;
}

export interface NotificationToken {
  id: string;
  token: string;
  platform: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string;
}

export interface NotificationStatus {
  user_id: string;
  active_devices: number;
  ios_devices: number;
  android_devices: number;
  last_used: string | null;
  push_enabled: boolean;
}

export interface NotificationTemplate {
  title: string;
  body: string;
  icon: string;
  color: string;
  priority: 'normal' | 'high';
}

// =============================================================================
// Service
// =============================================================================

class PushNotificationServiceClass {
  /**
   * Request notification permission from the user
   * Returns true if permission granted
   */
  async requestPermission(): Promise<boolean> {
    try {
      if (!('Notification' in window)) {
        console.warn('This browser does not support notifications');
        return false;
      }

      const permission = await Notification.requestPermission();
      return permission === 'granted';

    } catch (error) {
      console.error('Failed to request notification permission:', error);
      return false;
    }
  }

  /**
   * Check current permission status
   */
  getPermissionStatus(): NotificationPermission {
    if (!('Notification' in window)) {
      return 'denied';
    }

    return Notification.permission;
  }

  /**
   * Register device token with backend
   */
  async registerToken(request: TokenRegistrationRequest): Promise<NotificationToken> {
    try {
      const response = await api.post('/push-notifications/register-token', request);
      return response.data;
    } catch (error: any) {
      console.error('Failed to register device token:', error);
      throw error;
    }
  }

  /**
   * Unregister device token
   */
  async unregisterToken(token: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await api.post('/push-notifications/unregister-token', { token });
      return response.data;
    } catch (error: any) {
      console.error('Failed to unregister device token:', error);
      throw error;
    }
  }

  /**
   * Get all tokens for current user
   */
  async getMyTokens(): Promise<NotificationToken[]> {
    try {
      const response = await api.get('/push-notifications/my-tokens');
      return response.data;
    } catch (error: any) {
      console.error('Failed to get user tokens:', error);
      throw error;
    }
  }

  /**
   * Get notification status
   */
  async getStatus(): Promise<NotificationStatus> {
    try {
      const response = await api.get('/push-notifications/status');
      return response.data;
    } catch (error: any) {
      console.error('Failed to get notification status:', error);
      throw error;
    }
  }

  /**
   * Send test notification
   */
  async sendTestNotification(): Promise<NotificationDelivery> {
    try {
      const response = await api.get('/push-notifications/test-send');
      return response.data;
    } catch (error: any) {
      console.error('Failed to send test notification:', error);
      throw error;
    }
  }

  /**
   * List all notification types
   */
  async getNotificationTypes(): Promise<{ notification_types: Record<string, NotificationTemplate>; total_types: number }> {
    try {
      const response = await api.get('/push-notifications/types');
      return response.data;
    } catch (error: any) {
      console.error('Failed to get notification types:', error);
      throw error;
    }
  }

  /**
   * Initialize push notifications (helper method)
   * This should be called when the app starts
   */
  async initialize(getFCMToken: () => Promise<string | null>): Promise<boolean> {
    try {
      // Check if we're in a supported environment
      const platform = this.detectPlatform();
      if (!platform) {
        console.log('Push notifications not supported on this platform');
        return false;
      }

      // Get FCM token
      const token = await getFCMToken();
      if (!token) {
        console.warn('Failed to get FCM token');
        return false;
      }

      // Get device info
      const deviceInfo = this.getDeviceInfo();

      // Register with backend
      await this.registerToken({
        token,
        platform,
        ...deviceInfo,
      });

      console.log('Push notifications initialized successfully');
      return true;

    } catch (error) {
      console.error('Failed to initialize push notifications:', error);
      return false;
    }
  }

  /**
   * Detect the current platform
   */
  private detectPlatform(): 'ios' | 'android' | null {
    const userAgent = navigator.userAgent.toLowerCase();

    // Check for iOS
    const ios = /ipad|iphone|ipod/.test(userAgent) && !(window as any).MSStream;
    if (ios) {
      return 'ios';
    }

    // Check for Android
    const android = /android/.test(userAgent);
    if (android) {
      return 'android';
    }

    return null;
  }

  /**
   * Get device information
   */
  private getDeviceInfo(): Partial<DeviceInfo> {
    const userAgent = navigator.userAgent;

    // Simple device model detection
    let device_model: string | undefined;
    if (/iphone/.test(userAgent)) {
      device_model = 'iPhone';
    } else if (/ipad/.test(userAgent)) {
      device_model = 'iPad';
    } else if (/android/.test(userAgent)) {
      // Try to extract Android device model
      const match = userAgent.match(/Android\s([^\s]+)\s/);
      device_model = match ? match[1] : 'Android Device';
    }

    return {
      device_model,
      os_version: this.getOSVersion(),
      app_version: process.env.REACT_APP_VERSION || '1.0.0',
    };
  }

  /**
   * Get OS version
   */
  private getOSVersion(): string {
    const userAgent = navigator.userAgent;
    let osVersion = 'Unknown';

    if (/iphone|ipad|ipod/.test(userAgent)) {
      const match = userAgent.match(/OS\s([\d_]+)\s/);
      osVersion = match ? match[1].replace(/_/g, '.') : 'iOS';
    } else if (/android/.test(userAgent)) {
      const match = userAgent.match(/Android\s([\d.]+)/);
      osVersion = match ? match[1] : 'Android';
    }

    return osVersion;
  }
}

// =============================================================================
// Export singleton instance
// =============================================================================

export const pushNotificationService = new PushNotificationServiceClass();

// Export type
export type NotificationPermission = 'default' | 'granted' | 'denied';
