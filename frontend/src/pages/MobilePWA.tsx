/**
 * Mobile PWA Page - Fully Responsive
 * 
 * Demonstrates PWA features:
 * - Install prompt
 * - Offline mode
 * - Push notifications
 * - Responsive design
 * 
 * Responsive Breakpoints:
 * - Mobile: < 640px
 * - Tablet: 640px - 1024px
 * - Desktop: > 1024px
 */
import React, { useState, useEffect } from 'react';
// import { useOffline } from '../hooks/useOffline'; // Temporarily disabled
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}
const MobilePWA: React.FC = () => {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>('default');
  // Temporarily disabled offline functionality
  // const { isOnline, isOffline, pendingCount, isSyncing } = useOffline();
  const isOnline = true;
  const isOffline = false;
  const pendingCount = 0;
  const isSyncing = false;
  // Check if already installed
  useEffect(() => {
    // Check if running as installed PWA
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    setIsInstalled(isStandalone);
    // Listen for install prompt
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
    };
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    // Check notification permission
    if ('Notification' in window) {
      setNotificationPermission(Notification.permission);
    }
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);
  const handleInstallClick = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setIsInstalled(true);
      setDeferredPrompt(null);
    }
  };
  const handleEnableNotifications = async () => {
    if (!('Notification' in window)) {
      alert('Notifications are not supported in this browser');
      return;
    }
    const permission = await Notification.requestPermission();
    setNotificationPermission(permission);
    if (permission === 'granted') {
      new Notification('PsychSync', {
        body: 'Notifications enabled successfully!',
        icon: '/assets/icons/icon-192x192.png'
      });
    }
  };
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500">
      {/* Header - Responsive */}
      <header className="bg-white/10 backdrop-blur-lg border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-white rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-2xl">🧠</span>
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-white">
                  PsychSync
                </h1>
                <p className="text-xs sm:text-sm text-white/80 hidden sm:block">
                  Team Wellness Platform
                </p>
              </div>
            </div>
            {/* Connection Status */}
            <div className={`px-3 py-1.5 rounded-full text-xs sm:text-sm font-medium ${
              isOnline ? 'bg-green-500 text-white' : 'bg-orange-500 text-white'
            }`}>
              {isOnline ? '🟢 Online' : '🔴 Offline'}
              {pendingCount > 0 && ` (${pendingCount} pending)`}
            </div>
          </div>
        </div>
      </header>
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-12">
        {/* Hero Section - Responsive */}
        <div className="text-center mb-8 sm:mb-12">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white mb-4">
            Install PsychSync
          </h2>
          <p className="text-base sm:text-lg lg:text-xl text-white/90 max-w-2xl mx-auto px-4">
            Get the full app experience with offline access, push notifications, and native app features
          </p>
        </div>
        {/* Feature Cards - Responsive Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8 mb-8 sm:mb-12">
          {/* Install Card */}
          <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8 transform hover:scale-105 transition-transform">
            <div className="w-12 h-12 sm:w-16 sm:h-16 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center mb-4 mx-auto sm:mx-0">
              <span className="text-2xl sm:text-3xl">📱</span>
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2 text-center sm:text-left">
              Install as App
            </h3>
            <p className="text-sm sm:text-base text-gray-600 mb-4 text-center sm:text-left">
              Add PsychSync to your home screen for quick access
            </p>
            {isInstalled ? (
              <div className="bg-green-100 text-green-800 px-4 py-2 rounded-lg text-center text-sm font-medium">
                ✅ Already Installed
              </div>
            ) : deferredPrompt ? (
              <button
                onClick={handleInstallClick}
                className="w-full bg-gradient-to-r from-indigo-500 to-purple-500 text-white px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg font-medium hover:from-indigo-600 hover:to-purple-600 transition-all shadow-lg text-sm sm:text-base"
              >
                Install Now
              </button>
            ) : (
              <div className="bg-gray-100 text-gray-600 px-4 py-2 rounded-lg text-center text-sm">
                Use browser menu to install
              </div>
            )}
          </div>
          {/* Offline Card */}
          <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8 transform hover:scale-105 transition-transform">
            <div className="w-12 h-12 sm:w-16 sm:h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center mb-4 mx-auto sm:mx-0">
              <span className="text-2xl sm:text-3xl">
                {isOffline ? '📴' : '🌐'}
              </span>
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2 text-center sm:text-left">
              Works Offline
            </h3>
            <p className="text-sm sm:text-base text-gray-600 mb-4 text-center sm:text-left">
              Access your data even without internet connection
            </p>
            <div className={`px-4 py-2 rounded-lg text-center text-sm font-medium ${
              isOffline 
                ? 'bg-orange-100 text-orange-800' 
                : 'bg-green-100 text-green-800'
            }`}>
              {isOffline ? '📴 Currently Offline' : '✅ Online & Ready'}
            </div>
            {isSyncing && (
              <div className="mt-2 bg-blue-100 text-blue-800 px-4 py-2 rounded-lg text-center text-sm">
                🔄 Syncing data...
              </div>
            )}
          </div>
          {/* Notifications Card */}
          <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8 transform hover:scale-105 transition-transform sm:col-span-2 lg:col-span-1">
            <div className="w-12 h-12 sm:w-16 sm:h-16 bg-gradient-to-br from-pink-500 to-red-500 rounded-xl flex items-center justify-center mb-4 mx-auto sm:mx-0">
              <span className="text-2xl sm:text-3xl">🔔</span>
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2 text-center sm:text-left">
              Push Notifications
            </h3>
            <p className="text-sm sm:text-base text-gray-600 mb-4 text-center sm:text-left">
              Get reminders and updates instantly
            </p>
            {notificationPermission === 'granted' ? (
              <div className="bg-green-100 text-green-800 px-4 py-2 rounded-lg text-center text-sm font-medium">
                ✅ Notifications Enabled
              </div>
            ) : notificationPermission === 'denied' ? (
              <div className="bg-red-100 text-red-800 px-4 py-2 rounded-lg text-center text-sm">
                ❌ Enable in browser settings
              </div>
            ) : (
              <button
                onClick={handleEnableNotifications}
                className="w-full bg-gradient-to-r from-pink-500 to-red-500 text-white px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg font-medium hover:from-pink-600 hover:to-red-600 transition-all shadow-lg text-sm sm:text-base"
              >
                Enable Notifications
              </button>
            )}
          </div>
        </div>
        {/* Features List - Responsive */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 sm:p-8 lg:p-10 border border-white/20 mb-8">
          <h3 className="text-2xl sm:text-3xl font-bold text-white mb-6 sm:mb-8 text-center sm:text-left">
            PWA Features
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
            {[
              { icon: '⚡', title: 'Lightning Fast', desc: 'Instant load times with smart caching' },
              { icon: '📴', title: 'Offline Access', desc: 'View data without internet' },
              { icon: '🔔', title: 'Push Alerts', desc: 'Never miss important updates' },
              { icon: '📱', title: 'Native Feel', desc: 'Works like a real app' },
              { icon: '🔄', title: 'Auto Sync', desc: 'Background data synchronization' },
              { icon: '🔒', title: 'Secure', desc: 'Industry-standard encryption' }
            ].map((feature, index) => (
              <div 
                key={index} 
                className="flex items-start gap-4 p-4 bg-white/10 rounded-xl hover:bg-white/20 transition-colors"
              >
                <div className="text-3xl sm:text-4xl flex-shrink-0">
                  {feature.icon}
                </div>
                <div>
                  <h4 className="text-base sm:text-lg font-semibold text-white mb-1">
                    {feature.title}
                  </h4>
                  <p className="text-sm sm:text-base text-white/80">
                    {feature.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
        {/* Device Compatibility - Responsive */}
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8 lg:p-10">
          <h3 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-6 sm:mb-8 text-center sm:text-left">
            Works on All Devices
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6 text-center">
            <div className="p-4">
              <div className="text-4xl sm:text-5xl mb-2 sm:mb-3">📱</div>
              <div className="text-sm sm:text-base font-medium text-gray-900">iPhone</div>
              <div className="text-xs sm:text-sm text-gray-500">iOS 14+</div>
            </div>
            <div className="p-4">
              <div className="text-4xl sm:text-5xl mb-2 sm:mb-3">🤖</div>
              <div className="text-sm sm:text-base font-medium text-gray-900">Android</div>
              <div className="text-xs sm:text-sm text-gray-500">Android 8+</div>
            </div>
            <div className="p-4">
              <div className="text-4xl sm:text-5xl mb-2 sm:mb-3">💻</div>
              <div className="text-sm sm:text-base font-medium text-gray-900">Desktop</div>
              <div className="text-xs sm:text-sm text-gray-500">All Browsers</div>
            </div>
            <div className="p-4">
              <div className="text-4xl sm:text-5xl mb-2 sm:mb-3">📱</div>
              <div className="text-sm sm:text-base font-medium text-gray-900">Tablet</div>
              <div className="text-xs sm:text-sm text-gray-500">All Sizes</div>
            </div>
          </div>
        </div>
        {/* CTA Section - Responsive */}
        <div className="mt-8 sm:mt-12 text-center">
          <button
            onClick={() => window.location.href = '/dashboard'}
            className="bg-white text-indigo-600 px-6 sm:px-8 lg:px-12 py-3 sm:py-4 rounded-xl font-bold text-base sm:text-lg hover:bg-gray-100 transition-all shadow-2xl inline-flex items-center gap-2 sm:gap-3"
          >
            <span>Go to Dashboard</span>
            <span className="text-xl sm:text-2xl">→</span>
          </button>
        </div>
      </main>
      {/* Footer - Responsive */}
      <footer className="bg-white/10 backdrop-blur-lg border-t border-white/20 mt-12 sm:mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="text-center text-white/80 text-xs sm:text-sm">
            <p className="mb-2">
              PsychSync PWA • Powered by Service Workers & IndexedDB
            </p>
            <p className="text-white/60">
              © 2024 PsychSync. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
export default MobilePWA;