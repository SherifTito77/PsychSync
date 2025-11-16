// =================================================================
// PWA MANIFEST
// =================================================================
// public/manifest.json
{
  "name": "NBA Fantasy Analytics",
  "short_name": "NBA Analytics",
  "description": "Advanced NBA fantasy basketball analytics and lineup optimizer",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2563eb",
  "orientation": "portrait",
  "scope": "/",
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "shortcuts": [
    {
      "name": "My Lineup",
      "short_name": "Lineup",
      "description": "View and optimize your fantasy lineup",
      "url": "/lineup",
      "icons": [{ "src": "/icons/lineup.png", "sizes": "96x96" }]
    },
    {
      "name": "Top Players",
      "short_name": "Players",
      "description": "Browse top performing players",
      "url": "/players",
      "icons": [{ "src": "/icons/players.png", "sizes": "96x96" }]
    },
    {
      "name": "Live Games",
      "short_name": "Live",
      "description": "Follow live game scores",
      "url": "/live",
      "icons": [{ "src": "/icons/live.png", "sizes": "96x96" }]
    }
  ],
  "screenshots": [
    {
      "src": "/screenshots/home.png",
      "sizes": "540x720",
      "type": "image/png"
    },
    {
      "src": "/screenshots/players.png",
      "sizes": "540x720",
      "type": "image/png"
    }
  ],
  "categories": ["sports", "entertainment", "lifestyle"],
  "iarc_rating_id": "e84b072d-71b3-4d3e-86ae-31a8ce4e53b7",
  "prefer_related_applications": false
}

// =================================================================
// SERVICE WORKER
// =================================================================
// public/service-worker.js

const CACHE_NAME = 'nba-analytics-v1';
const API_CACHE_NAME = 'nba-api-cache-v1';
const IMAGE_CACHE_NAME = 'nba-images-v1';

// Static assets to cache
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/static/css/main.css',
  '/static/js/main.js',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  '/offline.html'
];

// API endpoints to cache
const API_ENDPOINTS = [
  '/api/scoring/leaderboard',
  '/api/scoring/trending',
  '/api/optimizer/player-pool'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[Service Worker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(name => name !== CACHE_NAME && 
                          name !== API_CACHE_NAME && 
                          name !== IMAGE_CACHE_NAME)
            .map(name => caches.delete(name))
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - network-first strategy for API, cache-first for assets
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API requests - network first, fallback to cache
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      networkFirstStrategy(request, API_CACHE_NAME)
    );
    return;
  }

  // Images - cache first, fallback to network
  if (request.destination === 'image') {
    event.respondWith(
      cacheFirstStrategy(request, IMAGE_CACHE_NAME)
    );
    return;
  }

  // Static assets - cache first
  event.respondWith(
    cacheFirstStrategy(request, CACHE_NAME)
  );
});

// Network-first strategy
async function networkFirstStrategy(request, cacheName) {
  try {
    const response = await fetch(request);
    
    // Cache successful responses
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    // Network failed, try cache
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/offline.html');
    }
    
    throw error;
  }
}

// Cache-first strategy
async function cacheFirstStrategy(request, cacheName) {
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    // Update cache in background
    updateCache(request, cacheName);
    return cachedResponse;
  }
  
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/offline.html');
    }
    
    throw error;
  }
}

// Background cache update
async function updateCache(request, cacheName) {
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response);
    }
  } catch (error) {
    // Silently fail background updates
  }
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-lineup') {
    event.waitUntil(syncLineup());
  }
  
  if (event.tag === 'sync-alerts') {
    event.waitUntil(syncAlerts());
  }
});

async function syncLineup() {
  try {
    const db = await openDB();
    const lineups = await db.getAll('pending-lineups');
    
    for (const lineup of lineups) {
      await fetch('/api/lineup/save', {
        method: 'POST',
        body: JSON.stringify(lineup),
        headers: { 'Content-Type': 'application/json' }
      });
      
      await db.delete('pending-lineups', lineup.id);
    }
  } catch (error) {
    console.error('[Service Worker] Sync failed:', error);
  }
}

async function syncAlerts() {
  try {
    // Fetch latest alerts
    const response = await fetch('/api/alerts/latest');
    const alerts = await response.json();
    
    // Show notifications
    for (const alert of alerts) {
      self.registration.showNotification('NBA Analytics', {
        body: alert.message,
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge.png',
        tag: alert.id,
        data: alert
      });
    }
  } catch (error) {
    console.error('[Service Worker] Alert sync failed:', error);
  }
}

// Push notifications
self.addEventListener('push', (event) => {
  const data = event.data.json();
  
  const options = {
    body: data.body,
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge.png',
    tag: data.tag || 'default',
    data: data.data,
    actions: [
      {
        action: 'view',
        title: 'View Details'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ],
    vibrate: [200, 100, 200]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'view') {
    const url = event.notification.data?.url || '/';
    
    event.waitUntil(
      clients.openWindow(url)
    );
  }
});

// IndexedDB helper
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('nba-analytics', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      if (!db.objectStoreNames.contains('pending-lineups')) {
        db.createObjectStore('pending-lineups', { keyPath: 'id', autoIncrement: true });
      }
      
      if (!db.objectStoreNames.contains('cached-players')) {
        db.createObjectStore('cached-players', { keyPath: 'id' });
      }
    };
  });
}

// =================================================================
// PWA REGISTRATION
// =================================================================
// src/pwa-init.js

export function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/service-worker.js')
        .then(registration => {
          console.log('SW registered:', registration);
          
          // Check for updates every hour
          setInterval(() => {
            registration.update();
          }, 60 * 60 * 1000);
          
          // Listen for updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New version available
                showUpdateNotification();
              }
            });
          });
        })
        .catch(error => {
          console.error('SW registration failed:', error);
        });
    });
  }
}

function showUpdateNotification() {
  if (confirm('A new version is available. Reload to update?')) {
    window.location.reload();
  }
}

// =================================================================
// PWA INSTALL PROMPT
// =================================================================
// src/components/InstallPrompt.jsx

export function useInstallPrompt() {
  const [installPrompt, setInstallPrompt] = React.useState(null);
  const [isInstalled, setIsInstalled] = React.useState(false);

  React.useEffect(() => {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true);
      return;
    }

    // Listen for install prompt
    const handleBeforeInstall = (e) => {
      e.preventDefault();
      setInstallPrompt(e);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);

    // Check if app was installed
    window.addEventListener('appinstalled', () => {
      setIsInstalled(true);
      setInstallPrompt(null);
    });

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
    };
  }, []);

  const handleInstall = async () => {
    if (!installPrompt) return;

    installPrompt.prompt();
    const { outcome } = await installPrompt.userChoice;

    if (outcome === 'accepted') {
      console.log('User accepted install');
    }

    setInstallPrompt(null);
  };

  return { installPrompt, isInstalled, handleInstall };
}

// =================================================================
// OFFLINE DETECTION
// =================================================================
// src/hooks/useOnlineStatus.js

export function useOnlineStatus() {
  const [isOnline, setIsOnline] = React.useState(navigator.onLine);

  React.useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      // Sync pending changes
      if ('serviceWorker' in navigator && 'sync' in registration) {
        navigator.serviceWorker.ready.then(registration => {
          registration.sync.register('sync-lineup');
          registration.sync.register('sync-alerts');
        });
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

// =================================================================
// PUSH NOTIFICATIONS
// =================================================================
// src/services/notifications.js

export async function requestNotificationPermission() {
  if (!('Notification' in window)) {
    console.log('Notifications not supported');
    return false;
  }

  const permission = await Notification.requestPermission();
  return permission === 'granted';
}

export async function subscribeToPushNotifications() {
  const registration = await navigator.serviceWorker.ready;
  
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(process.env.REACT_APP_VAPID_PUBLIC_KEY)
  });

  // Send subscription to backend
  await fetch('/api/notifications/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(subscription)
  });

  return subscription;
}

function urlBase64ToUint8Array(base64String) {
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
}

// =================================================================
// OFFLINE.HTML
// =================================================================
/*
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Offline - NBA Analytics</title>
  <style>
    body {
      font-family: -apple-system, system-ui, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      text-align: center;
      padding: 20px;
    }
    .container {
      max-width: 400px;
    }
    h1 {
      font-size: 48px;
      margin: 0 0 20px;
    }
    p {
      font-size: 18px;
      opacity: 0.9;
      margin: 0 0 30px;
    }
    button {
      background: white;
      color: #667eea;
      border: none;
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>📡</h1>
    <h2>You're Offline</h2>
    <p>Check your internet connection and try again</p>
    <button onclick="window.location.reload()">Retry</button>
  </div>
</body>
</html>
*/