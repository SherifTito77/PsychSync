# 🚀 Progressive Web App (PWA) Implementation Guide
## Mobile-First Assessment Foundation

**Purpose**: Provide comprehensive technical implementation guidance for PWA foundation
**Timeline**: Weeks 1-3 of mobile re-architecture
**Target**: Installable mobile app with offline assessment capabilities
**Success Criteria**: 90%+ offline functionality, 95%+ app install rate

---

## 🏗️ PWA Architecture Overview

### Core PWA Components

```
📱 Progressive Web App Architecture
├── Service Worker (offline capabilities)
├── Web App Manifest (app-like experience)
├── Offline-First Data Layer (IndexedDB)
├── Caching Strategy (network + cache)
├── Background Sync (data synchronization)
├── Push Notifications (engagement)
└── Installation Prompts (app discovery)
```

### Mobile Assessment PWA Benefits

- **Offline Assessment**: Complete assessments without internet
- **App-Like Experience**: Installable home screen icon, full-screen mode
- **Fast Loading**: Instant loading via intelligent caching
- **Background Sync**: Automatic data sync when online
- **Push Notifications**: Assessment reminders and engagement
- **Cross-Platform**: Single codebase for iOS and Android

---

## 🔧 Phase 1: Service Worker Implementation

### 1.1 Service Worker Registration

```javascript
// public/js/service-worker-registration.js
class PWAServiceWorkerRegistration {
  constructor() {
    this.swUrl = '/service-worker.js';
    this.swScope = '/';
  }

  async register() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register(this.swUrl, {
          scope: this.swScope
        });

        console.log('Service Worker registered:', registration);

        // Handle updates
        this.handleServiceWorkerUpdates(registration);

        return registration;
      } catch (error) {
        console.error('Service Worker registration failed:', error);
        throw error;
      }
    } else {
      console.warn('Service Worker not supported');
      return null;
    }
  }

  handleServiceWorkerUpdates(registration) {
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;

      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          // New version available
          this.showUpdatePrompt();
        }
      });
    });
  }

  showUpdatePrompt() {
    // Show user-friendly update prompt
    const updateBanner = document.createElement('div');
    updateBanner.className = 'update-banner';
    updateBanner.innerHTML = `
      <div class="update-content">
        <p>A new version of PsychSync is available!</p>
        <button id="update-btn" class="btn btn-primary">Update Now</button>
        <button id="dismiss-btn" class="btn btn-secondary">Later</button>
      </div>
    `;

    document.body.appendChild(updateBanner);

    document.getElementById('update-btn').addEventListener('click', () => {
      window.location.reload();
    });

    document.getElementById('dismiss-btn').addEventListener('click', () => {
      updateBanner.remove();
    });
  }
}

// Register service worker on page load
document.addEventListener('DOMContentLoaded', () => {
  const pwaRegistration = new PWAServiceWorkerRegistration();
  pwaRegistration.register();
});
```

### 1.2 Service Worker Core Implementation

```javascript
// public/service-worker.js
const CACHE_NAME = 'psychsync-assessment-v1';
const STATIC_CACHE = 'psychsync-static-v1';
const DYNAMIC_CACHE = 'psychsync-dynamic-v1';

const STATIC_ASSETS = [
  '/',
  '/assessment/',
  '/offline.html',
  '/css/mobile-assessment.css',
  '/css/pwa.css',
  '/js/assessment-engine.js',
  '/js/offline-manager.js',
  '/js/touch-interactions.js',
  '/images/logo-192.png',
  '/images/logo-512.png',
  '/fonts/inter.woff2',
  '/assessment/api/big-five/questions'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');

  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Static assets cached successfully');
        return self.skipWaiting(); // Activate immediately
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - implement caching strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle different request types
  if (url.origin === self.location.origin) {
    // Handle app requests
    event.respondWith(handleAppRequest(request));
  } else {
    // Handle external requests (API calls, etc.)
    event.respondWith(handleExternalRequest(request));
  }
});

// Handle application requests (HTML, CSS, JS, images)
async function handleAppRequest(request) {
  // Try cache first for static assets
  if (isStaticAsset(request.url)) {
    return cacheFirst(request);
  }

  // Try network first for dynamic content
  return networkFirst(request);
}

// Handle external requests (API calls)
async function handleExternalRequest(request) {
  // Use network first for API calls with offline fallback
  return networkFirstWithOfflineFallback(request);
}

// Caching strategies
async function cacheFirst(request) {
  const cachedResponse = await caches.match(request);

  if (cachedResponse) {
    console.log('Cache hit:', request.url);
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('Network failed, returning cached or offline page:', request.url);

    // Return cached version if available
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Return offline page for HTML requests
    if (request.headers.get('accept')?.includes('text/html')) {
      return caches.match('/offline.html');
    }

    throw error;
  }
}

async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Cache successful responses
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('Network failed, trying cache:', request.url);

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

async function networkFirstWithOfflineFallback(request) {
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Cache API responses for offline use
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('API call failed, returning cached response:', request.url);

    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Return offline API response
    return new Response(JSON.stringify({
      error: 'Offline',
      message: 'No network connection available',
      offline: true
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Helper functions
function isStaticAsset(url) {
  return STATIC_ASSETS.includes(url) ||
         url.includes('/css/') ||
         url.includes('/js/') ||
         url.includes('/images/') ||
         url.includes('/fonts/') ||
         url.includes('.woff') ||
         url.includes('.ttf') ||
         url.includes('.png') ||
         url.includes('.jpg') ||
         url.includes('.svg');
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync-assessment-data') {
    event.waitUntil(syncAssessmentData());
  }
});

async function syncAssessmentData() {
  try {
    // Get all pending offline data
    const pendingData = await getPendingOfflineData();

    for (const data of pendingData) {
      try {
        // Sync with server
        const response = await fetch('/api/assessment/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });

        if (response.ok) {
          // Remove synced data from IndexedDB
          await removeSyncedData(data.id);
        }
      } catch (error) {
        console.error('Sync failed for data:', data.id, error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Push notification handling
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'You have a new assessment reminder!',
    icon: '/images/logo-192.png',
    badge: '/images/badge-72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Open Assessment',
        icon: '/images/checkmark.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/images/xmark.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('PsychSync Assessment', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/assessment/')
    );
  } else if (event.action === 'close') {
    // Just close the notification
  } else {
    // Default action - open the app
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});
```

---

## 📱 Phase 2: Web App Manifest & App-like Experience

### 2.1 Web App Manifest

```json
// public/manifest.json
{
  "name": "PsychSync - Personality Assessment",
  "short_name": "PsychSync",
  "description": "Professional personality assessment platform for personal and team development",
  "start_url": "/assessment/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#3b82f6",
  "orientation": "portrait-primary",
  "scope": "/",
  "lang": "en",
  "categories": ["health", "productivity", "education"],
  "icons": [
    {
      "src": "/images/icon-72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/images/icon-96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/images/icon-128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/images/icon-144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/images/icon-152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/images/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/images/icon-384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/images/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable any"
    }
  ],
  "screenshots": [
    {
      "src": "/images/screenshot1.png",
      "sizes": "1280x720",
      "type": "image/png",
      "platform": "wide",
      "label": "Assessment overview screen"
    },
    {
      "src": "/images/screenshot2.png",
      "sizes": "750x1334",
      "type": "image/png",
      "platform": "narrow",
      "label": "Question interface on mobile"
    }
  ],
  "shortcuts": [
    {
      "name": "Start Big Five Assessment",
      "short_name": "Big Five",
      "description": "Begin comprehensive personality assessment",
      "url": "/assessment/big-five/",
      "icons": [
        {
          "src": "/images/big-five-icon.png",
          "sizes": "96x96"
        }
      ]
    },
    {
      "name": "View Results",
      "short_name": "Results",
      "description": "Access your assessment results",
      "url": "/results/",
      "icons": [
        {
          "src": "/images/results-icon.png",
          "sizes": "96x96"
        }
      ]
    }
  ],
  "related_applications": [],
  "prefer_related_applications": false,
  "edge_side_panel": {
    "preferred_width": 400
  }
}
```

### 2.2 App Installation Prompts

```javascript
// public/js/install-prompt.js
class PWAInstallPrompt {
  constructor() {
    this.deferredPrompt = null;
    this.installButton = null;
    this.isInstallable = false;
  }

  initialize() {
    this.setupInstallPrompt();
    this.createInstallButton();
    this.checkInstallStatus();
    this.setupBeforeInstallPrompt();
  }

  setupBeforeInstallPrompt() {
    window.addEventListener('beforeinstallprompt', (e) => {
      console.log('PWA install prompt available');
      e.preventDefault();
      this.deferredPrompt = e;
      this.isInstallable = true;
      this.showInstallButton();
    });
  }

  createInstallButton() {
    this.installButton = document.createElement('button');
    this.installButton.id = 'install-btn';
    this.installButton.className = 'btn btn-primary install-btn hidden';
    this.installButton.innerHTML = `
      <svg class="icon" viewBox="0 0 24 24" width="16" height="16">
        <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
      </svg>
      Install PsychSync App
    `;

    this.installButton.addEventListener('click', () => {
      this.promptInstall();
    });

    // Add to page
    document.body.appendChild(this.installButton);
  }

  showInstallButton() {
    if (this.installButton && this.isInstallable) {
      this.installButton.classList.remove('hidden');
    }
  }

  hideInstallButton() {
    if (this.installButton) {
      this.installButton.classList.add('hidden');
    }
  }

  async promptInstall() {
    if (!this.deferredPrompt) {
      console.log('Install prompt not available');
      return;
    }

    try {
      console.log('Showing install prompt');
      const result = await this.deferredPrompt.prompt();

      console.log('Install prompt result:', result);

      if (result.outcome === 'accepted') {
        console.log('User accepted PWA installation');
        this.trackInstallation('accepted');
      } else {
        console.log('User dismissed PWA installation');
        this.trackInstallation('dismissed');
      }

      this.deferredPrompt = null;
      this.hideInstallButton();

    } catch (error) {
      console.error('Error during PWA install prompt:', error);
      this.trackInstallation('error', error);
    }
  }

  checkInstallStatus() {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      console.log('PWA is already installed');
      this.hideInstallButton();
      this.trackInstallation('already-installed');
    }
  }

  trackInstallation(status, error = null) {
    // Track installation events for analytics
    const eventData = {
      event: 'pwa_installation',
      status,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      platform: navigator.platform
    };

    if (error) {
      eventData.error = error.message;
    }

    // Send to analytics
    if (window.analytics) {
      window.analytics.track(eventData);
    }

    console.log('PWA installation tracked:', eventData);
  }

  // iOS Safari installation instructions (since beforeinstallprompt isn't supported)
  showIOSInstallInstructions() {
    if (this.isIOS()) {
      const iOSInstallPrompt = document.createElement('div');
      iOSInstallPrompt.className = 'ios-install-prompt';
      iOSInstallPrompt.innerHTML = `
        <div class="ios-prompt-content">
          <h3>Install PsychSync on iOS</h3>
          <ol>
            <li>Tap the Share button <span class="share-icon">⎋</span> in Safari</li>
            <li>Tap "Add to Home Screen" <span class="plus-icon">+</span></li>
            <li>Tap "Add" to install the app</li>
          </ol>
          <button id="dismiss-ios-prompt" class="btn btn-secondary">Got it!</button>
        </div>
      `;

      document.body.appendChild(iOSInstallPrompt);

      document.getElementById('dismiss-ios-prompt').addEventListener('click', () => {
        iOSInstallPrompt.remove();
        localStorage.setItem('ios-prompt-dismissed', 'true');
      });
    }
  }

  isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  }

  shouldShowIOSPrompt() {
    return this.isIOS() &&
           !window.matchMedia('(display-mode: standalone)').matches &&
           !localStorage.getItem('ios-prompt-dismissed');
  }
}

// Initialize install prompt
document.addEventListener('DOMContentLoaded', () => {
  const installPrompt = new PWAInstallPrompt();
  installPrompt.initialize();

  // Show iOS instructions if needed
  if (installPrompt.shouldShowIOSPrompt()) {
    setTimeout(() => {
      installPrompt.showIOSInstallInstructions();
    }, 3000);
  }
});
```

---

## 📊 Phase 3: Offline-First Data Management

### 3.1 IndexedDB Offline Data Store

```javascript
// public/js/offline-manager.js
class OfflineDataManager {
  constructor() {
    this.dbName = 'PsychSyncAssessments';
    this.version = 2;
    this.db = null;
  }

  async initialize() {
    try {
      this.db = await this.openDatabase();
      console.log('Offline database initialized successfully');
      return true;
    } catch (error) {
      console.error('Failed to initialize offline database:', error);
      return false;
    }
  }

  async openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = () => {
        console.error('Database error:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        console.log('Database opened successfully');
        resolve(request.result);
      };

      request.onupgradeneeded = (event) => {
        console.log('Database upgrade needed');
        const db = event.target.result;

        // Create object stores if they don't exist
        this.createObjectStores(db);
      };
    });
  }

  createObjectStores(db) {
    // Assessment questions store
    if (!db.objectStoreNames.contains('assessmentQuestions')) {
      const questionStore = db.createObjectStore('assessmentQuestions', { keyPath: 'id' });
      questionStore.createIndex('assessmentType', 'assessmentType', { unique: false });
      questionStore.createIndex('batchId', 'batchId', { unique: false });
    }

    // User responses store
    if (!db.objectStoreNames.contains('userResponses')) {
      const responseStore = db.createObjectStore('userResponses', { keyPath: ['sessionId', 'questionIndex'] });
      responseStore.createIndex('sessionId', 'sessionId', { unique: false });
      responseStore.createIndex('synced', 'synced', { unique: false });
      responseStore.createIndex('timestamp', 'timestamp', { unique: false });
    }

    // Assessment sessions store
    if (!db.objectStoreNames.contains('assessmentSessions')) {
      const sessionStore = db.createObjectStore('assessmentSessions', { keyPath: 'sessionId' });
      sessionStore.createIndex('userId', 'userId', { unique: false });
      sessionStore.createIndex('assessmentType', 'assessmentType', { unique: false });
      sessionStore.createIndex('status', 'status', { unique: false });
      sessionStore.createIndex('createdAt', 'createdAt', { unique: false });
    }

    // Sync queue store
    if (!db.objectStoreNames.contains('syncQueue')) {
      const syncStore = db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true });
      syncStore.createIndex('type', 'type', { unique: false });
      syncStore.createIndex('timestamp', 'timestamp', { unique: false });
      syncStore.createIndex('attempts', 'attempts', { unique: false });
    }

    // User preferences store
    if (!db.objectStoreNames.contains('userPreferences')) {
      db.createObjectStore('userPreferences', { keyPath: 'key' });
    }
  }

  // Assessment question management
  async cacheAssessmentQuestions(assessmentType, questions) {
    const transaction = this.db.transaction(['assessmentQuestions'], 'readwrite');
    const store = transaction.objectStore('assessmentQuestions');

    try {
      for (const question of questions) {
        await store.put({
          id: `${assessmentType}-${question.id}`,
          assessmentType,
          ...question,
          cachedAt: Date.now()
        });
      }

      console.log(`Cached ${questions.length} questions for ${assessmentType}`);
      return true;
    } catch (error) {
      console.error('Failed to cache assessment questions:', error);
      return false;
    }
  }

  async getAssessmentQuestions(assessmentType) {
    const transaction = this.db.transaction(['assessmentQuestions'], 'readonly');
    const store = transaction.objectStore('assessmentQuestions');
    const index = store.index('assessmentType');

    try {
      const questions = await index.getAll(assessmentType);

      if (questions.length > 0) {
        console.log(`Retrieved ${questions.length} cached questions for ${assessmentType}`);
        return questions;
      }

      // If no cached questions, try to fetch from network
      return await this.fetchAndCacheQuestions(assessmentType);
    } catch (error) {
      console.error('Failed to get assessment questions:', error);
      throw error;
    }
  }

  async fetchAndCacheQuestions(assessmentType) {
    try {
      const response = await fetch(`/api/assessment/${assessmentType}/questions`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const questions = await response.json();

      // Cache the questions
      await this.cacheAssessmentQuestions(assessmentType, questions);

      return questions;
    } catch (error) {
      console.error('Failed to fetch assessment questions:', error);
      throw error;
    }
  }

  // User response management
  async saveResponse(sessionId, questionIndex, response) {
    const transaction = this.db.transaction(['userResponses'], 'readwrite');
    const store = transaction.objectStore('userResponses');

    try {
      await store.put({
        sessionId,
        questionIndex,
        response,
        timestamp: Date.now(),
        synced: false
      });

      // Update session progress
      await this.updateSessionProgress(sessionId, questionIndex + 1);

      console.log(`Saved response for session ${sessionId}, question ${questionIndex}`);
      return true;
    } catch (error) {
      console.error('Failed to save response:', error);
      return false;
    }
  }

  async getResponses(sessionId) {
    const transaction = this.db.transaction(['userResponses'], 'readonly');
    const store = transaction.objectStore('userResponses');
    const index = store.index('sessionId');

    try {
      const responses = await index.getAll(sessionId);

      // Sort by questionIndex
      responses.sort((a, b) => a.questionIndex - b.questionIndex);

      console.log(`Retrieved ${responses.length} responses for session ${sessionId}`);
      return responses;
    } catch (error) {
      console.error('Failed to get responses:', error);
      throw error;
    }
  }

  // Session management
  async createSession(assessmentType, userId = null) {
    const sessionId = this.generateSessionId();
    const transaction = this.db.transaction(['assessmentSessions'], 'readwrite');
    const store = transaction.objectStore('assessmentSessions');

    try {
      await store.put({
        sessionId,
        userId,
        assessmentType,
        status: 'in_progress',
        currentQuestionIndex: 0,
        totalQuestions: 0, // Will be updated when questions are loaded
        createdAt: Date.now(),
        lastActivity: Date.now()
      });

      console.log(`Created session ${sessionId} for ${assessmentType}`);
      return sessionId;
    } catch (error) {
      console.error('Failed to create session:', error);
      throw error;
    }
  }

  async updateSessionProgress(sessionId, currentQuestionIndex) {
    const transaction = this.db.transaction(['assessmentSessions'], 'readwrite');
    const store = transaction.objectStore('assessmentSessions');

    try {
      const session = await store.get(sessionId);
      if (session) {
        session.currentQuestionIndex = currentQuestionIndex;
        session.lastActivity = Date.now();

        // Check if assessment is complete
        const questions = await this.getAssessmentQuestions(session.assessmentType);
        if (currentQuestionIndex >= questions.length) {
          session.status = 'completed';
          session.completedAt = Date.now();
        }

        await store.put(session);
      }
    } catch (error) {
      console.error('Failed to update session progress:', error);
    }
  }

  async getSession(sessionId) {
    const transaction = this.db.transaction(['assessmentSessions'], 'readonly');
    const store = transaction.objectStore('assessmentSessions');

    try {
      const session = await store.get(sessionId);
      return session;
    } catch (error) {
      console.error('Failed to get session:', error);
      throw error;
    }
  }

  // Sync queue management
  async addToSyncQueue(type, data) {
    const transaction = this.db.transaction(['syncQueue'], 'readwrite');
    const store = transaction.objectStore('syncQueue');

    try {
      const syncItem = {
        type,
        data,
        timestamp: Date.now(),
        attempts: 0
      };

      const id = await store.add(syncItem);
      console.log(`Added sync item ${id} of type ${type}`);
      return id;
    } catch (error) {
      console.error('Failed to add to sync queue:', error);
      throw error;
    }
  }

  async getSyncQueue() {
    const transaction = this.db.transaction(['syncQueue'], 'readonly');
    const store = transaction.objectStore('syncQueue');

    try {
      const items = await store.getAll();
      // Sort by timestamp (oldest first)
      items.sort((a, b) => a.timestamp - b.timestamp);
      return items;
    } catch (error) {
      console.error('Failed to get sync queue:', error);
      throw error;
    }
  }

  async removeSyncItem(id) {
    const transaction = this.db.transaction(['syncQueue'], 'readwrite');
    const store = transaction.objectStore('syncQueue');

    try {
      await store.delete(id);
      console.log(`Removed sync item ${id}`);
    } catch (error) {
      console.error('Failed to remove sync item:', error);
    }
  }

  // Utility methods
  generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Storage management
  async getStorageUsage() {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      try {
        const estimate = await navigator.storage.estimate();
        return {
          quota: estimate.quota,
          usage: estimate.usage,
          usageDetails: estimate.usageDetails
        };
      } catch (error) {
        console.error('Failed to get storage estimate:', error);
      }
    }
    return null;
  }

  async clearOldData() {
    const cutoffDate = Date.now() - (30 * 24 * 60 * 60 * 1000); // 30 days ago

    // Clear old sessions
    const sessionTransaction = this.db.transaction(['assessmentSessions'], 'readwrite');
    const sessionStore = sessionTransaction.objectStore('assessmentSessions');
    const sessionIndex = sessionStore.index('createdAt');

    try {
      const oldSessions = await sessionIndex.getAll(IDBKeyRange.upperBound(cutoffDate));
      for (const session of oldSessions) {
        await sessionStore.delete(session.sessionId);
      }

      console.log(`Cleared ${oldSessions.length} old sessions`);
    } catch (error) {
      console.error('Failed to clear old sessions:', error);
    }

    // Clear old responses
    const responseTransaction = this.db.transaction(['userResponses'], 'readwrite');
    const responseStore = responseTransaction.objectStore('userResponses');
    const responseIndex = responseStore.index('timestamp');

    try {
      const oldResponses = await responseIndex.getAll(IDBKeyRange.upperBound(cutoffDate));
      for (const response of oldResponses) {
        await responseStore.delete([response.sessionId, response.questionIndex]);
      }

      console.log(`Cleared ${oldResponses.length} old responses`);
    } catch (error) {
      console.error('Failed to clear old responses:', error);
    }
  }
}

// Export for use in other modules
window.OfflineDataManager = OfflineDataManager;
```

### 3.2 PWA CSS for Mobile-First Experience

```css
/* public/css/pwa.css */

/* PWA-specific mobile optimizations */
.pwa-container {
  /* Ensure app works in standalone mode */
  height: 100vh;
  height: 100dvh; /* Dynamic viewport height */
  overflow-x: hidden;
  position: relative;
}

/* Safe area handling for notched devices */
.safe-area-container {
  padding-top: env(safe-area-inset-top);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
  padding-bottom: calc(env(safe-area-inset-bottom) + 16px);
}

/* Status bar color for standalone mode */
@media (display-mode: standalone) {
  body {
    padding-top: env(safe-area-inset-top);
  }

  /* iOS status bar */
  .status-bar-spacer {
    height: env(safe-area-inset-top);
  }
}

/* Install button styling */
.install-btn {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
  padding: 12px 20px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border: none;
  border-radius: 25px;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.install-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.install-btn.hidden {
  display: none;
}

.install-btn .icon {
  width: 16px;
  height: 16px;
  fill: currentColor;
}

/* iOS install prompt styling */
.ios-install-prompt {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.ios-prompt-content {
  background: white;
  border-radius: 16px;
  padding: 24px;
  max-width: 400px;
  width: 100%;
  text-align: center;
}

.ios-prompt-content h3 {
  margin: 0 0 16px 0;
  color: #1f2937;
  font-size: 18px;
}

.ios-prompt-content ol {
  text-align: left;
  margin: 16px 0;
  padding-left: 20px;
}

.ios-prompt-content li {
  margin: 8px 0;
  line-height: 1.5;
  color: #4b5563;
}

.share-icon, .plus-icon {
  display: inline-block;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 12px;
  margin: 0 4px;
}

/* Update banner styling */
.update-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  z-index: 9999;
  padding: 12px 16px;
  text-align: center;
}

.update-content {
  max-width: 600px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
}

.update-content p {
  margin: 0;
  font-weight: 500;
}

.update-content .btn {
  padding: 6px 12px;
  border: 1px solid white;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  text-decoration: none;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;
}

.update-content .btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.update-content .btn-secondary {
  background: transparent;
  border-color: rgba(255, 255, 255, 0.6);
}

/* Offline indicator */
.offline-indicator {
  position: fixed;
  top: 10px;
  left: 10px;
  background: #f59e0b;
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  z-index: 1000;
  display: none;
}

.offline-indicator.show {
  display: block;
}

/* Sync indicator */
.sync-indicator {
  position: fixed;
  bottom: 20px;
  left: 20px;
  background: #10b981;
  color: white;
  padding: 8px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  z-index: 1000;
  display: none;
  align-items: center;
  gap: 6px;
}

.sync-indicator.show {
  display: flex;
}

.sync-indicator.syncing {
  background: #f59e0b;
}

.sync-indicator.error {
  background: #ef4444;
}

.sync-indicator::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.sync-indicator.syncing::before {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

/* Loading states for PWA */
.pwa-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.pwa-loading::after {
  content: '';
  width: 24px;
  height: 24px;
  border: 2px solid #e5e7eb;
  border-top: 2px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Network-aware styling */
.network-status {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  z-index: 10000;
  transform-origin: left;
  transition: transform 0.3s ease;
}

.network-status.online {
  background: #10b981;
  transform: scaleX(0);
}

.network-status.offline {
  background: #ef4444;
  transform: scaleX(1);
}

/* Responsive PWA adjustments */
@media (max-width: 480px) {
  .install-btn {
    bottom: 16px;
    right: 16px;
    padding: 10px 16px;
    font-size: 13px;
  }

  .ios-prompt-content {
    padding: 20px;
    margin: 10px;
  }

  .update-content {
    flex-direction: column;
    gap: 12px;
  }

  .update-content p {
    margin: 0 0 8px 0;
  }
}

/* Landscape mode optimizations */
@media (orientation: landscape) and (max-height: 500px) {
  .pwa-container {
    min-height: 100vh;
    overflow-y: auto;
  }

  .safe-area-container {
    padding-top: calc(env(safe-area-inset-top) + 8px);
    padding-bottom: calc(env(safe-area-inset-bottom) + 8px);
  }
}

/* Dark mode support for PWA */
@media (prefers-color-scheme: dark) {
  .ios-prompt-content {
    background: #1f2937;
    color: #f9fafb;
  }

  .ios-prompt-content h3 {
    color: #f9fafb;
  }

  .ios-prompt-content li {
    color: #d1d5db;
  }

  .share-icon, .plus-icon {
    background: #374151;
    border-color: #4b5563;
    color: #f9fafb;
  }
}

/* Print styles for PWA */
@media print {
  .install-btn,
  .offline-indicator,
  .sync-indicator,
  .update-banner {
    display: none !important;
  }

  .pwa-container {
    height: auto;
    overflow: visible;
  }
}
```

---

## ✅ Implementation Checklist

### Week 1: Foundation Setup
- [ ] Service worker implementation with caching strategies
- [ ] Web app manifest configuration
- [ ] Basic offline HTML page
- [ ] PWA CSS styling for mobile optimization
- [ ] Service worker registration system

### Week 2: Offline Capabilities
- [ ] IndexedDB data management system
- [ ] Assessment question caching
- [ ] User response storage
- [ ] Session management
- [ ] Background sync setup

### Week 3: App Experience
- [ ] Installation prompt system
- [ ] iOS installation instructions
- [ ] App shell architecture
- [ ] Push notification setup
- [ ] Update mechanism

### Success Metrics
- **Install Rate**: 60%+ of mobile users install PWA
- **Offline Functionality**: 95%+ of features work offline
- **Load Performance**: <2s first load, <500s subsequent loads
- **Storage Efficiency**: <50MB offline storage usage
- **Sync Reliability**: 98%+ successful background sync

---

## 🎯 Expected Results

### Immediate Benefits (Weeks 1-3)
- **Installable App Experience**: Users can install to home screen
- **Offline Assessment**: Complete assessments without internet
- **Fast Loading**: Near-instant app startup
- **Background Sync**: Automatic data synchronization

### Long-term Benefits (Post-PWA)
- **Increased Engagement**: 60% higher session duration
- **Better Retention**: 40% improvement in 30-day retention
- **App Store Presence**: Available in app stores via PWA
- **Cross-Platform**: Single codebase for iOS/Android/Web

This PWA implementation provides the foundation for the complete mobile-first re-architecture, establishing the offline-first, app-like experience that modern mobile users expect.

---

**Status**: ✅ **PWA IMPLEMENTATION GUIDE COMPLETE**
**Next Phase**: Mobile-Native Interaction Patterns
**Success Timeline**: 3 weeks to implement PWA foundation
**Business Impact**: Foundation for mobile assessment excellence
