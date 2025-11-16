/**
 * PsychSync Service Worker - PWA Offline Support
 * 
 * Why we need this:
 * - Enable offline access to completed assessments
 * - Cache critical app resources for faster loading
 * - Allow users to complete assessments without internet
 * - Sync data when connection is restored
 * - Improve user experience in low-connectivity areas
 * 
 * Features:
 * - Cache-first strategy for static assets
 * - Network-first for API calls with offline fallback
 * - Background sync for pending submissions
 * - Push notification support
 */

const CACHE_VERSION = 'psychsync-v1.0.0';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;
const API_CACHE = `${CACHE_VERSION}-api`;

// Resources to cache immediately on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/static/css/main.css',
  '/static/js/main.js',
  '/offline.html',
  '/assets/logo.svg',
  '/assets/icons/icon-192x192.png',
  '/assets/icons/icon-512x512.png'
];

// API routes that can work offline
const CACHEABLE_API_ROUTES = [
  '/api/v1/assessments/types',
  '/api/v1/teams',
  '/api/v1/users/me'
];

// Maximum cache size
const MAX_CACHE_SIZE = 50;

/**
 * Install Event - Cache static assets
 */
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[Service Worker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
      .catch((error) => {
        console.error('[Service Worker] Installation failed:', error);
      })
  );
});

/**
 * Activate Event - Clean up old caches
 */
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              return cacheName.startsWith('psychsync-') && 
                     cacheName !== STATIC_CACHE &&
                     cacheName !== DYNAMIC_CACHE &&
                     cacheName !== API_CACHE;
            })
            .map((cacheName) => {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

/**
 * Fetch Event - Intercept network requests
 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }
  
  // Handle different request types
  if (request.method === 'GET') {
    if (url.pathname.startsWith('/api/')) {
      event.respondWith(handleApiRequest(request));
    } else if (url.pathname.match(/\.(js|css|png|jpg|jpeg|svg|woff|woff2)$/)) {
      event.respondWith(handleStaticAsset(request));
    } else {
      event.respondWith(handleNavigationRequest(request));
    }
  } else if (request.method === 'POST' || request.method === 'PUT') {
    event.respondWith(handleMutationRequest(request));
  }
});

/**
 * Handle API requests - Network first, cache fallback
 */
async function handleApiRequest(request) {
  const url = new URL(request.url);
  const isCacheable = CACHEABLE_API_ROUTES.some(route => 
    url.pathname.startsWith(route)
  );
  
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    // Cache successful responses for cacheable routes
    if (networkResponse.ok && isCacheable) {
      const cache = await caches.open(API_CACHE);
      cache.put(request, networkResponse.clone());
      await limitCacheSize(API_CACHE, MAX_CACHE_SIZE);
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[Service Worker] Network failed, trying cache:', request.url);
    
    // Try cache fallback
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline response
    return new Response(
      JSON.stringify({
        error: 'offline',
        message: 'You are currently offline. Please check your connection.'
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

/**
 * Handle static assets - Cache first, network fallback
 */
async function handleStaticAsset(request) {
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
      await limitCacheSize(DYNAMIC_CACHE, MAX_CACHE_SIZE);
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[Service Worker] Failed to fetch asset:', request.url);
    return new Response('Asset not available offline', { status: 404 });
  }
}

/**
 * Handle navigation requests - Network first with offline page fallback
 */
async function handleNavigationRequest(request) {
  try {
    return await fetch(request);
  } catch (error) {
    const cache = await caches.open(STATIC_CACHE);
    const offlinePage = await cache.match('/offline.html');
    return offlinePage || new Response('Offline', { status: 503 });
  }
}

/**
 * Handle mutation requests (POST, PUT, DELETE) - Queue for sync
 */
async function handleMutationRequest(request) {
  try {
    return await fetch(request);
  } catch (error) {
    console.log('[Service Worker] Mutation failed, queueing for sync');
    
    // Clone request for background sync
    const requestData = {
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(request.headers.entries()),
      body: await request.clone().text()
    };
    
    // Store in IndexedDB for background sync
    await queueForSync(requestData);
    
    // Register sync event
    if ('sync' in self.registration) {
      await self.registration.sync.register('sync-mutations');
    }
    
    return new Response(
      JSON.stringify({
        queued: true,
        message: 'Request queued for sync when online'
      }),
      {
        status: 202,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

/**
 * Background Sync Event - Retry failed requests
 */
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-mutations') {
    event.waitUntil(syncQueuedRequests());
  }
});

/**
 * Sync queued requests when online
 */
async function syncQueuedRequests() {
  const db = await openSyncDatabase();
  const tx = db.transaction('sync-queue', 'readonly');
  const store = tx.objectStore('sync-queue');
  const requests = await store.getAll();
  
  for (const requestData of requests) {
    try {
      const response = await fetch(requestData.url, {
        method: requestData.method,
        headers: requestData.headers,
        body: requestData.body
      });
      
      if (response.ok) {
        // Remove from queue
        const deleteTx = db.transaction('sync-queue', 'readwrite');
        await deleteTx.objectStore('sync-queue').delete(requestData.id);
        
        console.log('[Service Worker] Synced request:', requestData.url);
        
        // Notify client
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
          client.postMessage({
            type: 'SYNC_COMPLETE',
            url: requestData.url
          });
        });
      }
    } catch (error) {
      console.error('[Service Worker] Sync failed:', error);
    }
  }
}

/**
 * Push Notification Event
 */
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  
  const options = {
    body: data.body || 'You have a new notification',
    icon: '/assets/icons/icon-192x192.png',
    badge: '/assets/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: {
      url: data.url || '/',
      timestamp: Date.now()
    },
    actions: data.actions || [
      { action: 'open', title: 'Open' },
      { action: 'close', title: 'Close' }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'PsychSync', options)
  );
});

/**
 * Notification Click Event
 */
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'close') {
    return;
  }
  
  const urlToOpen = event.notification.data?.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if app is already open
        for (const client of clientList) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

/**
 * Message Event - Handle messages from clients
 */
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(DYNAMIC_CACHE)
        .then(cache => cache.addAll(event.data.urls))
    );
  }
});

/**
 * Utility: Limit cache size
 */
async function limitCacheSize(cacheName, maxSize) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  
  if (keys.length > maxSize) {
    await cache.delete(keys[0]);
    await limitCacheSize(cacheName, maxSize); // Recursive
  }
}

/**
 * Utility: Queue request for sync
 */
async function queueForSync(requestData) {
  const db = await openSyncDatabase();
  const tx = db.transaction('sync-queue', 'readwrite');
  const store = tx.objectStore('sync-queue');
  
  await store.add({
    ...requestData,
    id: Date.now(),
    timestamp: new Date().toISOString()
  });
}

/**
 * Utility: Open IndexedDB for sync queue
 */
function openSyncDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('psychsync-sync', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('sync-queue')) {
        db.createObjectStore('sync-queue', { keyPath: 'id' });
      }
    };
  });
}

console.log('[Service Worker] Loaded successfully');
