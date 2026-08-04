/**
 * Push Notification Service for PsychSync Mobile
 * Uses Expo Notifications for cross-platform support
 */

import { Alert } from 'react-native';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

class NotificationService {
  private pushToken: string | null = null;

  constructor() {
    this.configureNotifications();
  }

  /**
   * Configure notification handler
   */
  private configureNotifications() {
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });
  }

  /**
   * Request permission and register for push notifications
   */
  async registerForPushNotifications(): Promise<string | null> {
    try {
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        Alert.alert(
          'Permission Required',
          'Push notifications are needed to alert you about important email activity.'
        );
        return null;
      }

      // Get push token
      const token = await this.getPushToken();
      this.pushToken = token;

      // TODO: Send token to backend
      await this.sendTokenToBackend(token);

      return token;
    } catch (error) {
      console.error('Error registering for push notifications:', error);
      return null;
    }
  }

  /**
   * Get platform-specific push token
   */
  private async getPushToken(): Promise<string> {
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('email-alerts', {
        name: 'Email Alerts',
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#FF231F7C',
      });
    }

    const { data: token } = await Notifications.getExpoPushTokenAsync();
    return token;
  }

  /**
   * Send push token to backend for storage
   */
  private async sendTokenToBackend(token: string) {
    // TODO: Implement API call to save token to backend
    // await apiService.registerPushToken(token);
    console.log('Push token registered:', token);
  }

  /**
   * Show local notification (for immediate alerts)
   */
  async showLocalNotification(
    title: string,
    body: string,
    data?: any
  ): Promise<void> {
    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        data,
        sound: true,
      },
      trigger: null, // Show immediately
    });
  }

  /**
   * Schedule notification for later
   */
  async scheduleNotification(
    title: string,
    body: string,
    trigger: Notifications.NotificationTriggerInput,
    data?: any
  ): Promise<string> {
    return await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        data,
        sound: true,
      },
      trigger,
    });
  }

  /**
   * Cancel scheduled notification
   */
  async cancelNotification(notificationId: string): Promise<void> {
    await Notifications.cancelScheduledNotificationAsync(notificationId);
  }

  /**
   * Cancel all notifications
   */
  async cancelAllNotifications(): Promise<void> {
    await Notifications.cancelAllScheduledNotificationsAsync();
  }

  /**
   * Get all scheduled notifications
   */
  async getScheduledNotifications(): Promise<Notifications.NotificationRequest[]> {
    return await Notifications.getAllScheduledNotificationsAsync();
  }

  /**
   * Add notification response listener
   */
  addNotificationResponseListener(
    callback: (response: Notifications.NotificationResponse) => void
  ): { remove: () => void } {
    return Notifications.addNotificationResponseReceivedListener(callback);
  }

  /**
   * Add notification received listener
   */
  addNotificationReceivedListener(
    callback: (notification: Notifications.Notification) => void
  ): { remove: () => void } {
    return Notifications.addNotificationReceivedListener(callback);
  }

  /**
   * Get badge count
   */
  async getBadgeCount(): Promise<number> {
    return await Notifications.getBadgeCountAsync();
  }

  /**
   * Set badge count
   */
  async setBadgeCount(count: number): Promise<void> {
    await Notifications.setBadgeCountAsync(count);
  }
}

// Singleton instance
export const notificationService = new NotificationService();
