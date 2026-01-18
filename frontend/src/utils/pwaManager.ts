/**
 * 🚀 PsychSync PWA Manager
 *
 * Progressive Web App installation and lifecycle management
 * Handles service worker registration, app installation prompts, and offline capabilities
 */

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

interface PWAInstallStatus {
  isInstallable: boolean;
  isInstalled: boolean;
  beforeInstallPrompt: BeforeInstallPromptEvent | null;
  platform: string;
  installInstructions: string;
}

interface NetworkInformation {
  type?: string;
  effectiveType?: 'slow-2g' | '2g' | '3g' | '4g';
  downlink?: number;
  rtt?: number;
  saveData?: boolean;
}

interface OfflineStatus {
  isOnline: boolean;
  connectionType: string;
  effectiveType: string;
  downlink: number;
  rtt: number;
  saveData: boolean;
}

class PWAManager {
  private static instance: PWAManager;
  private beforeInstallPrompt: BeforeInstallPromptEvent | null = null;
  private deferredPrompt: BeforeInstallPromptEvent | null = null;
  private isInstalled = false;
  private swRegistration: ServiceWorkerRegistration | null = null;
  private isOnline = navigator.onLine;
  private connection: any = null;
  private cleanupCallbacks: Array<() => void> = [];

  private constructor() {
    this.initializeConnectionMonitoring();
    this.setupInstallDetection();
    this.setupInstallPromptListeners();
  }

  public static getInstance(): PWAManager {
    if (!PWAManager.instance) {
      PWAManager.instance = new PWAManager();
    }
    return PWAManager.instance;
  }

  /**
   * Initialize PWA functionality
   */
  public async initialize(): Promise<void> {
    try {
      await this.registerServiceWorker();
      this.setupNetworkListeners();
      this.setupVisibilityChangeListeners();

      console.log('🚀 PWA Manager initialized successfully');
    } catch (error) {
      console.error('PWA initialization failed:', error);
    }
  }

  /**
   * Register service worker
   */
  private async registerServiceWorker(): Promise<void> {
    if (!('serviceWorker' in navigator)) {
      console.warn('Service workers not supported');
      return;
    }

    try {
      this.swRegistration = await navigator.serviceWorker.register('/service-worker.js', {
        scope: '/'
      });

      console.log('✅ Service Worker registered:', this.swRegistration.scope);

      // Wait for service worker to be active
      if (this.swRegistration.active) {
        console.log('✅ Service Worker is active');
      } else {
        this.swRegistration.addEventListener('updatefound', () => {
          console.log('🔄 Service Worker update found');
          const installingWorker = this.swRegistration?.installing;

          if (installingWorker) {
            installingWorker.addEventListener('statechange', () => {
              if (installingWorker.state === 'installed' && navigator.serviceWorker.controller) {
                this.showUpdateNotification();
              }
            });
          }
        });
      }

    } catch (error) {
      console.error('Service Worker registration failed:', error);
    }
  }

  /**
   * Setup install prompt listeners
   */
  private setupInstallPromptListeners(): void {
    const handleBeforeInstall = (event: Event) => {
      event.preventDefault();
      this.beforeInstallPrompt = event as BeforeInstallPromptEvent;
      this.deferredPrompt = event as BeforeInstallPromptEvent;

      console.log('📱 Install prompt detected');
      this.onInstallPromptReady();
    };

    const handleAppInstalled = () => {
      this.isInstalled = true;
      this.beforeInstallPrompt = null;
      this.deferredPrompt = null;

      console.log('✅ App successfully installed');
      this.onAppInstalled();
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);
    window.addEventListener('appinstalled', handleAppInstalled);

    // Register cleanup
    this.cleanupCallbacks.push(() => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
      window.removeEventListener('appinstalled', handleAppInstalled);
    });
  }

  /**
   * Setup network status monitoring
   */
  private setupNetworkListeners(): void {
    const handleOnline = () => {
      this.isOnline = true;
      this.onNetworkStatusChange(true);
    };

    const handleOffline = () => {
      this.isOnline = false;
      this.onNetworkStatusChange(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Register cleanup
    this.cleanupCallbacks.push(() => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    });
  }

  /**
   * Setup visibility change listeners
   */
  private setupVisibilityChangeListeners(): void {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        this.checkForUpdates();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Register cleanup
    this.cleanupCallbacks.push(() => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    });
  }

  /**
   * Initialize connection monitoring
   */
  private initializeConnectionMonitoring(): void {
    const connection = (navigator as any).connection ||
                      (navigator as any).mozConnection ||
                      (navigator as any).webkitConnection;

    if (connection) {
      this.connection = connection;

      const handleConnectionChange = () => {
        console.log('🌐 Connection changed:', {
          type: connection.effectiveType,
          downlink: connection.downlink,
          rtt: connection.rtt,
          saveData: connection.saveData
        });

        this.onConnectionChange();
      };

      connection.addEventListener('change', handleConnectionChange);

      // Register cleanup
      this.cleanupCallbacks.push(() => {
        connection.removeEventListener('change', handleConnectionChange);
      });
    }
  }

  /**
   * Setup install detection
   */
  private setupInstallDetection(): void {
    // Check if app is running in standalone mode
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                        (window.navigator as any).standalone === true;

    if (isStandalone) {
      this.isInstalled = true;
      console.log('📱 App is running in standalone mode');
    }

    // Listen for display mode changes
    const mediaQuery = window.matchMedia('(display-mode: standalone)');
    const handleMediaQueryChange = (e: MediaQueryListEvent) => {
      this.isInstalled = e.matches;
    };

    mediaQuery.addEventListener('change', handleMediaQueryChange);

    // Register cleanup
    this.cleanupCallbacks.push(() => {
      mediaQuery.removeEventListener('change', handleMediaQueryChange);
    });
  }

  /**
   * Show install prompt
   */
  public async showInstallPrompt(): Promise<boolean> {
    if (!this.beforeInstallPrompt || this.isInstalled) {
      return false;
    }

    try {
      await this.beforeInstallPrompt.prompt();
      const { outcome } = await this.beforeInstallPrompt.userChoice;

      console.log(`Install prompt ${outcome}`);

      if (outcome === 'accepted') {
        this.beforeInstallPrompt = null;
        return true;
      }

      return false;
    } catch (error) {
      console.error('Install prompt failed:', error);
      return false;
    }
  }

  /**
   * Get PWA install status
   */
  public getInstallStatus(): PWAInstallStatus {
    const platform = this.getPlatform();
    const installInstructions = this.getInstallInstructions(platform);

    return {
      isInstallable: !!this.beforeInstallPrompt,
      isInstalled: this.isInstalled,
      beforeInstallPrompt: this.beforeInstallPrompt,
      platform,
      installInstructions
    };
  }

  /**
   * Get offline status
   */
  public getOfflineStatus(): OfflineStatus {
    return {
      isOnline: this.isOnline,
      connectionType: this.connection?.type || 'unknown',
      effectiveType: this.connection?.effectiveType || 'unknown',
      downlink: this.connection?.downlink || 0,
      rtt: this.connection?.rtt || 0,
      saveData: this.connection?.saveData || false
    };
  }

  /**
   * Check for service worker updates
   */
  private async checkForUpdates(): Promise<void> {
    if (!this.swRegistration) return;

    try {
      await this.swRegistration.update();
    } catch (error) {
      console.error('Failed to check for updates:', error);
    }
  }

  /**
   * Show update notification
   */
  private showUpdateNotification(): void {
    // This would integrate with your notification system
    console.log('🔄 App update available');

    // You could show a custom notification here
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('PsychSync Update Available', {
        body: 'A new version of the app is available. Please refresh to get the latest features.',
        icon: '/assets/icons/icon-192x192.png',
        tag: 'app-update'
      });
    }
  }

  /**
   * Get platform-specific information
   */
  private getPlatform(): string {
    const userAgent = navigator.userAgent.toLowerCase();

    if (userAgent.includes('iphone') || userAgent.includes('ipad')) {
      return 'ios';
    } else if (userAgent.includes('android')) {
      return 'android';
    } else if (userAgent.includes('mac')) {
      return 'macos';
    } else if (userAgent.includes('win')) {
      return 'windows';
    }

    return 'desktop';
  }

  /**
   * Get platform-specific install instructions
   */
  private getInstallInstructions(platform: string): string {
    switch (platform) {
      case 'ios':
        return 'Tap the Share button and then "Add to Home Screen"';
      case 'android':
        return 'Tap the menu button and then "Add to Home Screen"';
      case 'desktop':
        return 'Click the install button in the address bar';
      default:
        return 'Look for the install button in your browser';
    }
  }

  /**
   * Request notification permission
   */
  public async requestNotificationPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      console.warn('Notifications not supported');
      return 'denied';
    }

    if (Notification.permission === 'granted') {
      return 'granted';
    }

    try {
      const permission = await Notification.requestPermission();
      console.log(`Notification permission: ${permission}`);
      return permission;
    } catch (error) {
      console.error('Failed to request notification permission:', error);
      return 'denied';
    }
  }

  /**
   * Subscribe to push notifications
   */
  public async subscribeToPushNotifications(): Promise<PushSubscription | null> {
    if (!this.swRegistration) {
      console.error('Service Worker not registered');
      return null;
    }

    try {
      const subscription = await this.swRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(
          // This would be your VAPID public key
          'BM_xFTJtKhMkYaHAKnBk1r5J9KpFbChfJ3gHqKjX4zqkX9xLrM7n8qPpQrSsTuVwXyZbNcLmVdKnQpStRqNpK'
        )
      });

      console.log('✅ Push notification subscription successful');
      return subscription;
    } catch (error) {
      console.error('Push notification subscription failed:', error);
      return null;
    }
  }

  /**
   * Clear application data
   */
  public async clearApplicationData(): Promise<void> {
    try {
      // Clear caches
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map(name => caches.delete(name)));
      }

      // Clear IndexedDB
      if ('indexedDB' in window) {
        const databases = await indexedDB.databases();
        await Promise.all(
          databases.map(db => indexedDB.deleteDatabase(db.name!))
        );
      }

      // Clear localStorage
      localStorage.clear();

      // Clear sessionStorage
      sessionStorage.clear();

      console.log('✅ Application data cleared successfully');
    } catch (error) {
      console.error('Failed to clear application data:', error);
    }
  }

  /**
   * Get storage usage information
   */
  public async getStorageUsage(): Promise<{
    quota: number;
    usage: number;
    usageDetails: StorageEstimate | null;
  }> {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      try {
        const estimate = await navigator.storage.estimate();
        return {
          quota: estimate.quota || 0,
          usage: estimate.usage || 0,
          usageDetails: estimate
        };
      } catch (error) {
        console.error('Failed to get storage usage:', error);
      }
    }

    return { quota: 0, usage: 0, usageDetails: null };
  }

  /**
   * Utility function to convert VAPID key
   */
  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }

    return outputArray as any;
  }

  /**
   * Event callbacks (to be overridden by consuming code)
   */
  private onInstallPromptReady(): void {
    // Default implementation - can be overridden
    console.log('📱 Install prompt ready');
  }

  private onAppInstalled(): void {
    // Default implementation - can be overridden
    console.log('✅ App installed successfully');
  }

  private onNetworkStatusChange(isOnline: boolean): void {
    // Default implementation - can be overridden
    console.log(`🌐 Network status changed: ${isOnline ? 'online' : 'offline'}`);
  }

  private onConnectionChange(): void {
    // Default implementation - can be overridden
    console.log('🌐 Connection properties changed');
  }

  /**
   * Public event setter methods
   */
  public setOnInstallPromptReady(callback: () => void): void {
    this.onInstallPromptReady = callback;
  }

  public setOnAppInstalled(callback: () => void): void {
    this.onAppInstalled = callback;
  }

  public setOnNetworkStatusChange(callback: (isOnline: boolean) => void): void {
    this.onNetworkStatusChange = callback;
  }

  public setOnConnectionChange(callback: () => void): void {
    this.onConnectionChange = callback;
  }

  /**
   * Cleanup all event listeners and resources
   * Call this when the app is shutting down or the PWA manager is no longer needed
   */
  public cleanup(): void {
    console.log('🧹 Cleaning up PWA Manager resources...');

    // Execute all cleanup callbacks
    this.cleanupCallbacks.forEach(cleanup => cleanup());
    this.cleanupCallbacks = [];

    // Clear references
    this.beforeInstallPrompt = null;
    this.deferredPrompt = null;
    this.swRegistration = null;
    this.connection = null;

    console.log('✅ PWA Manager cleanup complete');
  }
}

// Export singleton instance
export const pwaManager = PWAManager.getInstance();

// Export types
export type { BeforeInstallPromptEvent, PWAInstallStatus, OfflineStatus };

// Default export
export default PWAManager;
