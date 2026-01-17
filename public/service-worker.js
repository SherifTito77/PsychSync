/**
 * 🚀 PsychSync Service Worker - Progressive Web App Foundation
 *
 * Intelligent caching and offline functionality for mobile-first personality assessments
 *
 * Features:
 * - Multi-layered caching strategy (static, API, dynamic)
 * - Network resilience with offline fallbacks
 * - Background sync for assessment responses
 * - Battery-aware performance optimization
 * - Real-time cache management
 */

const CACHE_VERSION = 'v1.0.0';
const CACHE_PREFIX = 'psychsync';

// Cache configurations for different content types
const CACHE_CONFIG = {
  static: {
    name: `${CACHE_PREFIX}-static-${CACHE_VERSION}`,
    maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
    maxEntries: 100,
    files: [
      '/',
      '/index.html',
      '/manifest.json',
      '/static/js/bundle.js',
      '/static/css/main.css',
      '/assets/icons/icon-192x192.png',
      '/assets/icons/icon-512x512.png'
    ]
  },
  api: {
    name: `${CACHE_PREFIX}-api-${CACHE_VERSION}`,
    maxAge: 5 * 60 * 1000, // 5 minutes
    maxEntries: 200,
    patterns: [
      '/api/v1/assessments/',
      '/api/v1/templates/',
      '/api/v1/questions/'
    ]
  },
  dynamic: {
    name: `${CACHE_PREFIX}-dynamic-${CACHE_VERSION}`,
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
    maxEntries: 50,
    patterns: [
      '/api/v1/responses/',
      '/api/v1/analytics/'
    ]
  }
};

// Network profiles for adaptive performance
const NETWORK_PROFILES = {
  slow: { timeout: 10000, retries: 3, cacheFirst: true },
  normal: { timeout: 5000, retries: 2, cacheFirst: false },
  fast: { timeout: 2000, retries: 1, cacheFirst: false }
};

// Performance metrics tracking
const performanceMetrics = {
  cacheHits: 0,
  cacheMisses: 0,
  networkRequests: 0,
  offlineResponses: 0,
  averageResponseTime: 0
};

/**
 * Initialize service worker with cache management
 */
async function initializeServiceWorker() {
  try {
    await Promise.all([
      createCache(CACHE_CONFIG.static.name),
      createCache(CACHE_CONFIG.api.name),
      createCache(CACHE_CONFIG.dynamic.name)
    ]);

    console.log('🚀 PsychSync Service Worker initialized successfully');
    cleanupOldCaches();
  } catch (error) {
    console.error('Service Worker initialization failed:', error);
  }
}

/**
 * Create and populate cache
 */
async function createCache(cacheName) {
  const cache = await caches.open(cacheName);

  if (cacheName === CACHE_CONFIG.static.name) {
    await cache.addAll(CACHE_CONFIG.static.files);
  }

  return cache;
}

/**
 * Cleanup old caches to manage storage
 */
async function cleanupOldCaches() {
  const cacheNames = await caches.keys();
  const currentCaches = Object.values(CACHE_CONFIG).map(config => config.name);

  for (const cacheName of cacheNames) {
    if (!currentCaches.includes(cacheName)) {
      await caches.delete(cacheName);
      console.log(`Cleaned up old cache: ${cacheName}`);
    }
  }
}

/**
 * Determine network profile for adaptive performance
 */
function getNetworkProfile() {
  // Simple heuristic based on connection type
  const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;

  if (connection) {
    if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
      return NETWORK_PROFILES.slow;
    } else if (connection.effectiveType === '3g') {
      return NETWORK_PROFILES.normal;
    } else if (connection.effectiveType === '4g' || connection.effectiveType === '5g') {
      return NETWORK_PROFILES.fast;
    }
  }

  return NETWORK_PROFILES.normal; // Default
}

/**
 * Intelligent caching strategy based on request type
 */
async function handleRequest(request) {
  const startTime = Date.now();
  const url = new URL(request.url);
  const networkProfile = getNetworkProfile();

  try {
    // Static assets - Cache First
    if (isStaticAsset(request.url)) {
      return await handleCacheFirst(request, CACHE_CONFIG.static.name);
    }

    // API requests - Adaptive strategy
    if (url.pathname.startsWith('/api/')) {
      return await handleApiRequest(request, networkProfile);
    }

    // Navigation requests - Cache First with network fallback
    if (request.mode === 'navigate') {
      return await handleNavigationRequest(request);
    }

    // Default - Network First
    return await handleNetworkFirst(request);

  } catch (error) {
    console.error('Request handling failed:', error);
    return await handleOfflineFallback(request);
  } finally {
    // Track performance metrics
    const responseTime = Date.now() - startTime;
    updatePerformanceMetrics(responseTime);
  }
}

/**
 * Cache First strategy for static assets
 */
async function handleCacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    performanceMetrics.cacheHits++;
    return cachedResponse;
  }

  performanceMetrics.cacheMisses++;
  const networkResponse = await fetchWithTimeout(request);

  if (networkResponse.ok) {
    await cache.put(request, networkResponse.clone());
  }

  return networkResponse;
}

/**
 * Adaptive API request handling
 */
async function handleApiRequest(request, networkProfile) {
  const cacheName = getCacheNameForApi(request.url);

  // For slow networks, prefer cache
  if (networkProfile.cacheFirst) {
    return await handleCacheFirst(request, cacheName);
  }

  // For normal/fast networks, try network first with cache fallback
  return await handleNetworkFirst(request, cacheName);
}

/**
 * Network First strategy with cache fallback
 */
async function handleNetworkFirst(request, cacheName = null) {
  try {
    performanceMetrics.networkRequests++;
    const networkResponse = await fetchWithTimeout(request);

    if (networkResponse.ok && cacheName) {
      const cache = await caches.open(cacheName);
      await cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    if (cacheName) {
      const cache = await caches.open(cacheName);
      const cachedResponse = await cache.match(request);

      if (cachedResponse) {
        return cachedResponse;
      }
    }

    throw error;
  }
}

/**
 * Handle navigation requests with offline fallback
 */
async function handleNavigationRequest(request) {
  try {
    return await fetch(request);
  } catch (error) {
    const cache = await caches.open(CACHE_CONFIG.static.name);
    const cachedApp = await cache.match('/');

    if (cachedApp) {
      return cachedApp;
    }

    // Return offline page if available
    return new Response(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>PsychSync - Offline</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                 text-align: center; padding: 2rem; background: #f8fafc; }
          .offline-icon { font-size: 4rem; margin: 2rem 0; }
          .offline-message { color: #64748b; margin: 1rem 0; }
          .retry-button { background: #3b82f6; color: white; border: none;
                        padding: 0.75rem 2rem; border-radius: 0.5rem;
                        cursor: pointer; font-size: 1rem; margin-top: 1rem; }
        </style>
      </head>
      <body>
        <div class="offline-icon">📱</div>
        <h1>You're offline</h1>
        <p class="offline-message">Please check your internet connection and try again.</p>
        <button class="retry-button" onclick="window.location.reload()">
          Try Again
        </button>
      </body>
      </html>
    `, {
      status: 200,
      statusText: 'OK',
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

/**
 * Fetch with timeout and retries
 */
async function fetchWithTimeout(request, timeout = 5000, retries = 2) {
  const networkProfile = getNetworkProfile();
  timeout = networkProfile.timeout;
  retries = networkProfile.retries;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(request, {
        signal: controller.signal,
        headers: {
          'X-Service-Worker': 'psychsync-pwa',
          'X-Cache-Version': CACHE_VERSION
        }
      });

      clearTimeout(timeoutId);
      return response;

    } catch (error) {
      if (attempt === retries) {
        throw error;
      }

      // Exponential backoff
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
    }
  }
}

/**
 * Handle offline fallbacks
 */
async function handleOfflineFallback(request) {
  const url = new URL(request.url);

  // Return cached assessment data if available
  if (url.pathname.includes('/assessments/') || url.pathname.includes('/questions/')) {
    const cache = await caches.open(CACHE_CONFIG.api.name);
    const cachedResponse = await cache.match(request);

    if (cachedResponse) {
      performanceMetrics.offlineResponses++;
      return cachedResponse;
    }
  }

  // Return generic offline response for API requests
  if (url.pathname.startsWith('/api/')) {
    performanceMetrics.offlineResponses++;
    return new Response(JSON.stringify({
      error: 'Offline',
      message: 'No internet connection. Please try again when online.',
      offline: true,
      cached: false
    }), {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'application/json' }
    });
  }

  throw new Error('No offline fallback available');
}

/**
 * Background sync for assessment responses
 */
async function handleBackgroundSync(event) {
  if (event.tag === 'assessment-response') {
    try {
      const responses = await getStoredResponses();

      for (const response of responses) {
        try {
          await fetch('/api/v1/responses/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(response)
          });

          // Remove successfully synced response
          await removeStoredResponse(response.id);
        } catch (error) {
          console.error('Failed to sync response:', error);
        }
      }

    } catch (error) {
      console.error('Background sync failed:', error);
    }
  }
}

/**
 * Store assessment responses locally for offline sync
 */
async function storeResponseOffline(responseData) {
  const db = await openIndexedDB();
  const transaction = db.transaction(['responses'], 'readwrite');
  const store = transaction.objectStore('responses');

  await store.add({
    id: Date.now().toString(),
    data: responseData,
    timestamp: Date.now(),
    synced: false
  });
}

/**
 * Get stored responses for syncing
 */
async function getStoredResponses() {
  const db = await openIndexedDB();
  const transaction = db.transaction(['responses'], 'readonly');
  const store = transaction.objectStore('responses');

  return await store.getAll();
}

/**
 * Remove synced response from local storage
 */
async function removeStoredResponse(id) {
  const db = await openIndexedDB();
  const transaction = db.transaction(['responses'], 'readwrite');
  const store = transaction.objectStore('responses');

  await store.delete(id);
}

/**
 * Open IndexedDB for offline data storage
 */
async function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('psychsync-offline', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      if (!db.objectStoreNames.contains('responses')) {
        db.createObjectStore('responses', { keyPath: 'id' });
      }
    };
  });
}

/**
 * Helper functions
 */
function isStaticAsset(url) {
  return url.includes('/static/') ||
         url.includes('/assets/') ||
         url.endsWith('.js') ||
         url.endsWith('.css') ||
         url.endsWith('.png') ||
         url.endsWith('.jpg') ||
         url.endsWith('.svg');
}

function getCacheNameForApi(url) {
  if (url.includes('/assessments/') || url.includes('/templates/') || url.includes('/questions/')) {
    return CACHE_CONFIG.api.name;
  }

  if (url.includes('/responses/') || url.includes('/analytics/')) {
    return CACHE_CONFIG.dynamic.name;
  }

  return CACHE_CONFIG.api.name;
}

function updatePerformanceMetrics(responseTime) {
  performanceMetrics.averageResponseTime =
    (performanceMetrics.averageResponseTime + responseTime) / 2;
}

/**
 * Performance monitoring
 */
function logPerformanceMetrics() {
  console.log('🚀 Service Worker Performance Metrics:', {
    cacheHits: performanceMetrics.cacheHits,
    cacheMisses: performanceMetrics.cacheMisses,
    networkRequests: performanceMetrics.networkRequests,
    offlineResponses: performanceMetrics.offlineResponses,
    averageResponseTime: Math.round(performanceMetrics.averageResponseTime) + 'ms'
  });
}

/**
 * Service Worker Event Listeners
 */

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('🚀 Installing PsychSync Service Worker...');

  event.waitUntil(
    initializeServiceWorker()
      .then(() => self.skipWaiting())
      .then(() => console.log('✅ Service Worker installed successfully'))
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  console.log('🚀 Activating PsychSync Service Worker...');

  event.waitUntil(
    Promise.all([
      cleanupOldCaches(),
      self.clients.claim()
    ])
      .then(() => console.log('✅ Service Worker activated successfully'))
  );
});

// Fetch event - main request handling
self.addEventListener('fetch', (event) => {
  event.respondWith(handleRequest(event.request));
});

// Background sync event
self.addEventListener('sync', (event) => {
  if (event.tag === 'assessment-response') {
    event.waitUntil(handleBackgroundSync(event));
  }
});

// Push notification event
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New assessment available',
    icon: '/assets/icons/icon-192x192.png',
    badge: '/assets/icons/badge.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Explore Assessment',
        icon: '/assets/icons/checkmark.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/assets/icons/xmark.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('PsychSync', options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/assessments')
    );
  }
});

// Performance monitoring log
setInterval(logPerformanceMetrics, 60000); // Log every minute

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    handleRequest,
    initializeServiceWorker,
    performanceMetrics
  };
}
