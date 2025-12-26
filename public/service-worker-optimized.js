/**
 * 🚀 Optimized PsychSync Service Worker
 *
 * Enhanced version with immediate cache responses and predictive caching
 * Addresses performance issues identified in testing
 */

const CACHE_VERSION = 'v1.1.0-optimized';
const CACHE_PREFIX = 'psychsync';

// Enhanced cache configurations with immediate response strategies
const CACHE_CONFIG = {
  static: {
    name: `${CACHE_PREFIX}-static-${CACHE_VERSION}`,
    maxAge: 30 * 24 * 60 * 60 * 1000,
    maxEntries: 150,
    files: [
      '/',
      '/index.html',
      '/manifest.json',
      '/static/js/bundle.js',
      '/static/css/main.css'
    ],
    strategy: 'cache-first-immediate' // Immediate response
  },
  api: {
    name: `${CACHE_PREFIX}-api-${CACHE_VERSION}`,
    maxAge: 3 * 60 * 1000, // 3 minutes for fresher data
    maxEntries: 300,
    patterns: [
      '/api/v1/assessments/',
      '/api/v1/templates/',
      '/api/v1/questions/',
      '/api/v1/responses/'
    ],
    strategy: 'network-first-fallback'
  },
  predictive: {
    name: `${CACHE_PREFIX}-predictive-${CACHE_VERSION}`,
    maxAge: 60 * 60 * 1000, // 1 hour
    maxEntries: 50,
    strategy: 'predictive-cache'
  }
};

// Performance optimizations
const PERFORMANCE_CONFIG = {
  maxCacheSize: 100 * 1024 * 1024, // 100MB
  compressionEnabled: true,
  immediateResponseThreshold: 50, // ms
  predictiveCaching: true,
  memoryCleanup: true
};

// Network profiles for adaptive performance
const NETWORK_PROFILES = {
  'slow-2g': { timeout: 15000, retries: 3, cacheFirst: true, quality: 'low' },
  '2g': { timeout: 10000, retries: 2, cacheFirst: true, quality: 'medium' },
  '3g': { timeout: 6000, retries: 2, cacheFirst: false, quality: 'medium' },
  '4g': { timeout: 3000, retries: 1, cacheFirst: false, quality: 'high' }
};

// Enhanced performance metrics
const performanceMetrics = {
  cacheHits: 0,
  cacheMisses: 0,
  networkRequests: 0,
  offlineResponses: 0,
  averageResponseTime: 0,
  predictiveCacheHits: 0,
  memoryUsage: 0,
  lastCleanup: Date.now()
};

// Predictive content analyzer
class PredictiveContentAnalyzer {
  constructor() {
    this.userPatterns = new Map();
    this.accessFrequency = new Map();
    this.likelyNextPages = new Set();
  }

  recordAccess(url) {
    const count = this.accessFrequency.get(url) || 0;
    this.accessFrequency.set(url, count + 1);

    // Analyze pattern every 10 accesses
    if (count % 10 === 0) {
      this.analyzePatterns();
    }
  }

  analyzePatterns() {
    // Sort by frequency
    const sortedUrls = Array.from(this.accessFrequency.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20); // Top 20 most accessed

    // Predict likely next content based on assessment flow
    sortedUrls.forEach(([url, frequency]) => {
      if (url.includes('/assessments/')) {
        // Predict user will want to see results or related assessments
        this.likelyNextPages.add('/api/v1/results/');
        this.likelyNextPages.add('/api/v1/assessments/related/');
      }
      if (url.includes('/templates/')) {
        // Predict user will want to see assessment questions
        this.likelyNextPages.add('/api/v1/questions/');
      }
    });
  }

  getPredictedUrls() {
    return Array.from(this.likelyNextPages);
  }
}

const predictiveAnalyzer = new PredictiveContentAnalyzer();

// Enhanced memory management
class MemoryManager {
  constructor() {
    this.maxCacheSize = PERFORMANCE_CONFIG.maxCacheSize;
    this.cleanupThreshold = 0.8; // Clean at 80% capacity
  }

  async getCurrentUsage() {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      try {
        const estimate = await navigator.storage.estimate();
        return {
          usage: estimate.usage || 0,
          quota: estimate.quota || 0,
          percentage: ((estimate.usage || 0) / (estimate.quota || 1)) * 100
        };
      } catch (error) {
        return { usage: 0, quota: 0, percentage: 0 };
      }
    }
    return { usage: 0, quota: 0, percentage: 0 };
  }

  async shouldCleanup() {
    const usage = await this.getCurrentUsage();
    return usage.percentage > (this.cleanupThreshold * 100);
  }

  async performCleanup() {
    try {
      const cacheNames = await caches.keys();
      const cachesWithMetadata = [];

      for (const name of cacheNames) {
        if (name.includes(CACHE_PREFIX)) {
          const cache = await caches.open(name);
          const requests = await cache.keys();
          cachesWithMetadata.push({ name, count: requests.length, cache });
        }
      }

      // Sort by usage and remove least used
      cachesWithMetadata
        .sort((a, b) => a.count - b.count)
        .slice(0, 2) // Remove 2 least used caches
        .forEach(async (cacheInfo) => {
          await caches.delete(cacheInfo.name);
          console.log(`Cleaned up cache: ${cacheInfo.name}`);
        });

      performanceMetrics.lastCleanup = Date.now();
    } catch (error) {
      console.error('Cache cleanup failed:', error);
    }
  }
}

const memoryManager = new MemoryManager();

// Initialize optimized service worker
async function initializeServiceWorker() {
  try {
    console.log('🚀 Initializing Optimized PsychSync Service Worker...');

    // Create caches with optimized strategies
    await Promise.all([
      createCache(CACHE_CONFIG.static.name, CACHE_CONFIG.static),
      createCache(CACHE_CONFIG.api.name, CACHE_CONFIG.api),
      createCache(CACHE_CONFIG.predictive.name, CACHE_CONFIG.predictive)
    ]);

    // Perform initial memory cleanup
    await memoryManager.performCleanup();

    // Start predictive caching
    if (PERFORMANCE_CONFIG.predictiveCaching) {
      startPredictiveCaching();
    }

    console.log('✅ Optimized Service Worker initialized successfully');
    cleanupOldCaches();

  } catch (error) {
    console.error('Service Worker initialization failed:', error);
  }
}

async function createCache(cacheName, config) {
  const cache = await caches.open(cacheName);

  if (config.files) {
    // Preload critical files with error handling
    const preloadPromises = config.files.map(async (url) => {
      try {
        const response = await fetch(url, { cache: 'no-store' });
        if (response.ok) {
          await cache.put(url, response);
        }
      } catch (error) {
        console.warn(`Failed to preload ${url}:`, error.message);
      }
    });

    await Promise.allSettled(preloadPromises);
  }

  return cache;
}

async function cleanupOldCaches() {
  try {
    const cacheNames = await caches.keys();
    const currentCaches = Object.values(CACHE_CONFIG).map(config => config.name);

    for (const cacheName of cacheNames) {
      if (!currentCaches.includes(cacheName)) {
        await caches.delete(cacheName);
        console.log(`Cleaned up old cache: ${cacheName}`);
      }
    }
  } catch (error) {
    console.error('Cache cleanup failed:', error);
  }
}

// Enhanced request handler with immediate response optimization
async function handleRequest(request) {
  const startTime = performance.now();
  const url = new URL(request.url);
  const networkProfile = getNetworkProfile();

  try {
    // Record access for predictive analysis
    predictiveAnalyzer.recordAccess(url.pathname);

    // Static assets - Immediate cache-first with no network delay
    if (isStaticAsset(request.url)) {
      return await handleImmediateCacheFirst(request, CACHE_CONFIG.static.name);
    }

    // API requests - Adaptive strategy
    if (url.pathname.startsWith('/api/')) {
      return await handleAdaptiveApiRequest(request, networkProfile);
    }

    // Navigation requests - Cache-first with network fallback
    if (request.mode === 'navigate') {
      return await handleNavigationRequest(request);
    }

    // Predictive content
    if (shouldPreloadPredictively(url.pathname)) {
      preloadPredictiveContent(url.pathname);
    }

    // Default - Network-first with caching
    return await handleOptimizedNetworkFirst(request);

  } catch (error) {
    console.error('Request handling failed:', error);
    return await handleOfflineFallback(request);
  } finally {
    // Track performance
    const responseTime = performance.now() - startTime;
    updatePerformanceMetrics(responseTime);
  }
}

// Immediate cache-first response (optimizes cache response time)
async function handleImmediateCacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    // Immediate response - no network check needed
    performanceMetrics.cacheHits++;
    return cachedResponse;
  }

  // Cache miss - fetch and cache immediately
  performanceMetrics.cacheMisses++;
  const networkResponse = await fetchWithTimeout(request, 2000); // Short timeout for static assets

  if (networkResponse.ok) {
    // Cache in background (don't wait)
    cache.put(request, networkResponse.clone()).catch(err =>
      console.warn('Cache storage failed:', err.message)
    );
  }

  return networkResponse;
}

// Adaptive API request handling
async function handleAdaptiveApiRequest(request, networkProfile) {
  const cacheName = getCacheNameForApi(request.url);

  if (networkProfile.cacheFirst || networkProfile.quality === 'low') {
    // Poor network - prefer cache
    return await handleImmediateCacheFirst(request, cacheName);
  }

  // Good network - try network first with immediate cache fallback
  return await handleNetworkFirstWithCacheFallback(request, cacheName);
}

async function handleNetworkFirstWithCacheFallback(request, cacheName) {
  const cache = await caches.open(cacheName);

  try {
    const networkResponse = await fetchWithTimeout(request, networkProfile?.timeout || 5000);
    performanceMetrics.networkRequests++;

    if (networkResponse.ok) {
      // Cache successful responses
      cache.put(request, networkResponse.clone()).catch(() => {}); // Fire and forget
      return networkResponse;
    }
  } catch (error) {
    console.warn('Network request failed, trying cache:', request.url);
  }

  // Fallback to cache
  const cachedResponse = await cache.match(request);
  if (cachedResponse) {
    performanceMetrics.cacheHits++;
    return cachedResponse;
  }

  throw new Error('No network or cache response available');
}

async function handleNavigationRequest(request) {
  try {
    const networkResponse = await fetchWithTimeout(request, 3000);
    if (networkResponse.ok) {
      return networkResponse;
    }
  } catch (error) {
    console.warn('Navigation request failed, serving from cache');
  }

  // Fallback to cached app shell
  const cache = await caches.open(CACHE_CONFIG.static.name);
  const cachedApp = await cache.match('/');

  if (cachedApp) {
    return cachedApp;
  }

  // Ultimate fallback - basic offline page
  return new Response(createOfflinePage(), {
    status: 200,
    statusText: 'OK',
    headers: { 'Content-Type': 'text/html' }
  });
}

function createOfflinePage() {
  return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>PsychSync - Offline</title>
      <meta name="theme-color" content="#3b82f6">
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
               min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { text-align: center; color: white; padding: 2rem; max-width: 400px; }
        .icon { font-size: 4rem; margin-bottom: 1rem; }
        h1 { font-size: 1.5rem; margin-bottom: 1rem; }
        .message { font-size: 1rem; opacity: 0.9; margin-bottom: 1.5rem; }
        .button { background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3);
                 color: white; padding: 0.75rem 1.5rem; border-radius: 0.5rem;
                 text-decoration: none; display: inline-block; transition: all 0.3s; }
        .button:hover { background: rgba(255,255,255,0.3); }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="icon">🧠</div>
        <h1>You're Offline</h1>
        <p class="message">PsychSync is available offline. Your cached data and assessments are still accessible.</p>
        <a href="/" class="button">Continue Using App</a>
      </div>
    </body>
    </html>
  `;
}

// Predictive caching
function shouldPreloadPredictively(pathname) {
  const predictedUrls = predictiveAnalyzer.getPredictedUrls();
  return predictedUrls.some(predicted => pathname.includes(predicted));
}

async function preloadPredictiveContent(currentPath) {
  const predictedUrls = predictiveAnalyzer.getPredictedUrls();
  const cache = await caches.open(CACHE_CONFIG.predictive.name);

  predictedUrls.forEach(async (url) => {
    if (!await cache.match(url)) {
      try {
        const response = await fetch(url);
        if (response.ok) {
          await cache.put(url, response);
          performanceMetrics.predictiveCacheHits++;
        }
      } catch (error) {
        // Silently fail predictive caching
      }
    }
  });
}

function startPredictiveCaching() {
  // Analyze patterns periodically
  setInterval(async () => {
    predictiveAnalyzer.analyzePatterns();

    // Perform cleanup if needed
    if (await memoryManager.shouldCleanup()) {
      await memoryManager.performCleanup();
    }
  }, 60000); // Every minute
}

// Helper functions
function isStaticAsset(url) {
  return url.includes('/static/') ||
         url.includes('/assets/') ||
         url.endsWith('.js') ||
         url.endsWith('.css') ||
         url.endsWith('.png') ||
         url.endsWith('.jpg') ||
         url.endsWith('.svg') ||
         url.endsWith('.webp');
}

function getCacheNameForApi(url) {
  if (url.includes('/responses/') || url.includes('/analytics/')) {
    return CACHE_CONFIG.api.name;
  }
  return CACHE_CONFIG.api.name;
}

function getNetworkProfile() {
  const connection = (navigator as any).connection ||
                    (navigator as any).mozConnection ||
                    (navigator as any).webkitConnection;

  if (connection?.effectiveType) {
    return NETWORK_PROFILES[connection.effectiveType] || NETWORK_PROFILES['4g'];
  }

  return NETWORK_PROFILES['4g']; // Default to good connection
}

async function fetchWithTimeout(request, timeout = 5000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(request, {
      signal: controller.signal,
      headers: {
        'X-Service-Worker': 'psychsync-optimized',
        'X-Cache-Version': CACHE_VERSION
      }
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

function updatePerformanceMetrics(responseTime) {
  performanceMetrics.averageResponseTime =
    (performanceMetrics.averageResponseTime + responseTime) / 2;

  // Report metrics periodically
  if (Math.random() < 0.01) { // 1% sampling
    reportMetrics();
  }
}

function reportMetrics() {
  const total = performanceMetrics.cacheHits + performanceMetrics.cacheMisses;
  const hitRate = total > 0 ? (performanceMetrics.cacheHits / total) * 100 : 0;

  // Send metrics to analytics (implementation depends on your analytics setup)
  if ('sendBeacon' in navigator) {
    const data = {
      cacheHitRate: hitRate,
      averageResponseTime: Math.round(performanceMetrics.averageResponseTime),
      predictiveCacheHits: performanceMetrics.predictiveCacheHits,
      timestamp: Date.now()
    };

    navigator.sendBeacon('/api/sw-metrics', JSON.stringify(data));
  }
}

// Service Worker Event Listeners with optimizations
self.addEventListener('install', (event) => {
  console.log('🚀 Installing Optimized PsychSync Service Worker...');

  event.waitUntil(
    initializeServiceWorker()
      .then(() => self.skipWaiting())
      .then(() => console.log('✅ Optimized Service Worker installed successfully'))
  );
});

self.addEventListener('activate', (event) => {
  console.log('🚀 Activating Optimized PsychSync Service Worker...');

  event.waitUntil(
    Promise.all([
      cleanupOldCaches(),
      self.clients.claim(),
      // Claim all open pages immediately
      clients.matchAll().then(clientList => {
        clientList.forEach(client => {
          client.postMessage({ type: 'SW_UPDATED' });
        });
      })
    ])
      .then(() => console.log('✅ Optimized Service Worker activated successfully'))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(handleRequest(event.request));
});

// Background sync with error handling
self.addEventListener('sync', (event) => {
  if (event.tag === 'assessment-response') {
    event.waitUntil(handleBackgroundSync(event).catch(console.error));
  }
});

async function handleBackgroundSync(event) {
  try {
    const responses = await getStoredResponses();

    for (const response of responses) {
      try {
        const fetchResponse = await fetch('/api/v1/responses/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(response.data)
        });

        if (fetchResponse.ok) {
          await removeStoredResponse(response.id);
        }
      } catch (error) {
        console.error('Failed to sync response:', error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// IndexedDB helpers (simplified versions)
async function getStoredResponses() {
  // Implementation depends on your IndexedDB setup
  return [];
}

async function removeStoredResponse(id) {
  // Implementation depends on your IndexedDB setup
}

// Performance logging
setInterval(() => {
  console.log('🚀 Optimized SW Performance Metrics:', {
    cacheHitRate: performanceMetrics.cacheHits + performanceMetrics.cacheMisses > 0
      ? Math.round((performanceMetrics.cacheHits / (performanceMetrics.cacheHits + performanceMetrics.cacheMisses)) * 100) + '%'
      : '0%',
    avgResponseTime: Math.round(performanceMetrics.averageResponseTime) + 'ms',
    predictiveHits: performanceMetrics.predictiveCacheHits,
    lastCleanup: new Date(performanceMetrics.lastCleanup).toLocaleTimeString()
  });
}, 30000); // Log every 30 seconds

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    handleRequest,
    initializeServiceWorker,
    performanceMetrics,
    predictiveAnalyzer,
    memoryManager
  };
}