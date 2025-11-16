/**
 * Push Notification Utilities
 * 
 * Helper functions for web push notifications
 */

/**
 * Convert VAPID key from base64 to Uint8Array
 * Required format for push subscription
 */
export const urlBase64ToUint8Array = (base64String) => {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
};

/**
 * Check if push notifications are supported
 */
export const isPushSupported = () => {
  return (
    'Notification' in window &&
    'serviceWorker' in navigator &&
    'PushManager' in window
  );
};

/**
 * Get current notification permission
 */
export const getNotificationPermission = () => {
  if (!('Notification' in window)) {
    return 'unsupported';
  }
  return Notification.permission;
};

/**
 * Request notification permission
 */
export const requestNotificationPermission = async () => {
  if (!('Notification' in window)) {
    throw new Error('Notifications not supported');
  }

  const permission = await Notification.requestPermission();
  return permission;
};

/**
 * Show a local notification (doesn't require subscription)
 */
export const showLocalNotification = async (title, options = {}) => {
  if (!isPushSupported()) {
    console.warn('Notifications not supported');
    return;
  }

  if (Notification.permission !== 'granted') {
    console.warn('Notification permission not granted');
    return;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    await registration.showNotification(title, {
      icon: '/assets/icons/icon-192x192.png',
      badge: '/assets/icons/badge-72x72.png',
      vibrate: [200, 100, 200],
      ...options
    });
  } catch (error) {
    console.error('Error showing notification:', error);
  }
};

/**
 * Subscribe to push notifications
 */
export const subscribeToPush = async (vapidPublicKey) => {
  if (!isPushSupported()) {
    throw new Error('Push notifications not supported');
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    
    // Check for existing subscription
    let subscription = await registration.pushManager.getSubscription();
    
    if (!subscription) {
      // Create new subscription
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
      });
    }
    
    return subscription;
  } catch (error) {
    console.error('Error subscribing to push:', error);
    throw error;
  }
};

/**
 * Unsubscribe from push notifications
 */
export const unsubscribeFromPush = async () => {
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    
    if (subscription) {
      await subscription.unsubscribe();
      return true;
    }
    
    return false;
  } catch (error) {
    console.error('Error unsubscribing:', error);
    throw error;
  }
};

/**
 * Get current push subscription
 */
export const getPushSubscription = async () => {
  try {
    const registration = await navigator.serviceWorker.ready;
    return await registration.pushManager.getSubscription();
  } catch (error) {
    console.error('Error getting subscription:', error);
    return null;
  }
};

/**
 * Check if user is subscribed
 */
export const isSubscribed = async () => {
  try {
    const subscription = await getPushSubscription();
    return subscription !== null;
  } catch (error) {
    return false;
  }
};

/**
 * Format notification payload
 */
export const formatNotificationPayload = (title, body, options = {}) => {
  return {
    title,
    body,
    icon: options.icon || '/assets/icons/icon-192x192.png',
    badge: options.badge || '/assets/icons/badge-72x72.png',
    vibrate: options.vibrate || [200, 100, 200],
    data: options.data || {},
    actions: options.actions || [],
    tag: options.tag || undefined,
    requireInteraction: options.requireInteraction || false,
    silent: options.silent || false,
    timestamp: Date.now()
  };
};

/**
 * Test push notification
 */
export const testPushNotification = async () => {
  await showLocalNotification('Test Notification', {
    body: 'Push notifications are working!',
    icon: '/assets/icons/icon-192x192.png',
    badge: '/assets/icons/badge-72x72.png',
    tag: 'test-notification',
    actions: [
      { action: 'open', title: 'Open App' },
      { action: 'close', title: 'Close' }
    ]
  });
};

export default {
  urlBase64ToUint8Array,
  isPushSupported,
  getNotificationPermission,
  requestNotificationPermission,
  showLocalNotification,
  subscribeToPush,
  unsubscribeFromPush,
  getPushSubscription,
  isSubscribed,
  formatNotificationPayload,
  testPushNotification
};
