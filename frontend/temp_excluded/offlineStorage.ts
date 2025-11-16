/**
 * Offline Storage Utilities for PsychSync
 * 
 * Why we need this:
 * - Store assessment data when offline
 * - Cache user profile and preferences
 * - Queue failed API requests for retry
 * - Persist form progress
 * - Enable offline-first experience
 * 
 * Storage Strategy:
 * - localStorage: Small data, preferences, tokens
 * - IndexedDB: Large data, assessments, cached responses
 * - Cache API: Network responses (handled by service worker)
 */

// ============================================
// CONSTANTS
// ============================================
const STORAGE_KEYS = {
  USER_PROFILE: 'psychsync_user_profile',
  AUTH_TOKEN: 'psychsync_auth_token',
  PREFERENCES: 'psychsync_preferences',
  PENDING_ACTIONS: 'psychsync_pending_actions',
  CACHED_ASSESSMENTS: 'psychsync_cached_assessments',
  FORM_DRAFTS: 'psychsync_form_drafts',
  OFFLINE_QUEUE: 'psychsync_offline_queue',
  LAST_SYNC: 'psychsync_last_sync'
};

const DB_NAME = 'PsychSyncDB';
const DB_VERSION = 1;
const STORES = {
  ASSESSMENTS: 'assessments',
  RESPONSES: 'assessment_responses',
  TEAM_DATA: 'team_data',
  SYNC_QUEUE: 'sync_queue',
  CACHE: 'api_cache'
};

// ============================================
// LOCAL STORAGE HELPERS
// ============================================

/**
 * Store data in localStorage with error handling
 */
export const setLocalStorage = (key, value) => {
  try {
    const serialized = JSON.stringify({
      data: value,
      timestamp: Date.now()
    });
    localStorage.setItem(key, serialized);
    return true;
  } catch (error) {
    console.error('localStorage setItem error:', error);
    // Handle quota exceeded
    if (error.name === 'QuotaExceededError') {
      console.warn('localStorage quota exceeded, clearing old data');
      clearOldLocalStorage();
      try {
        localStorage.setItem(key, serialized);
        return true;
      } catch (retryError) {
        console.error('localStorage retry failed:', retryError);
        return false;
      }
    }
    return false;
  }
};

/**
 * Get data from localStorage with error handling
 */
export const getLocalStorage = (key, maxAge = null) => {
  try {
    const item = localStorage.getItem(key);
    if (!item) return null;

    const { data, timestamp } = JSON.parse(item);
    
    // Check if data is expired
    if (maxAge && Date.now() - timestamp > maxAge) {
      localStorage.removeItem(key);
      return null;
    }
    
    return data;
  } catch (error) {
    console.error('localStorage getItem error:', error);
    return null;
  }
};

/**
 * Remove item from localStorage
 */
export const removeLocalStorage = (key) => {
  try {
    localStorage.removeItem(key);
    return true;
  } catch (error) {
    console.error('localStorage removeItem error:', error);
    return false;
  }
};

/**
 * Clear old localStorage items
 */
const clearOldLocalStorage = () => {
  try {
    const keys = Object.keys(localStorage);
    const psychsyncKeys = keys.filter(key => key.startsWith('psychsync_'));
    
    // Remove items older than 30 days
    const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);
    
    psychsyncKeys.forEach(key => {
      try {
        const item = JSON.parse(localStorage.getItem(key));
        if (item.timestamp && item.timestamp < thirtyDaysAgo) {
          localStorage.removeItem(key);
        }
      } catch (e) {
        // Invalid item, remove it
        localStorage.removeItem(key);
      }
    });
  } catch (error) {
    console.error('Error clearing old localStorage:', error);
  }
};

// ============================================
// USER PROFILE & AUTH
// ============================================

export const saveUserProfile = (profile) => {
  return setLocalStorage(STORAGE_KEYS.USER_PROFILE, profile);
};

export const getUserProfile = () => {
  return getLocalStorage(STORAGE_KEYS.USER_PROFILE);
};

export const saveAuthToken = (token) => {
  return setLocalStorage(STORAGE_KEYS.AUTH_TOKEN, token);
};

export const getAuthToken = () => {
  return getLocalStorage(STORAGE_KEYS.AUTH_TOKEN);
};

export const clearAuthData = () => {
  removeLocalStorage(STORAGE_KEYS.AUTH_TOKEN);
  removeLocalStorage(STORAGE_KEYS.USER_PROFILE);
  removeLocalStorage(STORAGE_KEYS.PREFERENCES);
};

// ============================================
// USER PREFERENCES
// ============================================

export const savePreferences = (preferences) => {
  return setLocalStorage(STORAGE_KEYS.PREFERENCES, preferences);
};

export const getPreferences = () => {
  return getLocalStorage(STORAGE_KEYS.PREFERENCES) || {
    theme: 'light',
    notifications: true,
    language: 'en',
    autoSync: true
  };
};

export const updatePreference = (key, value) => {
  const prefs = getPreferences();
  prefs[key] = value;
  return savePreferences(prefs);
};

// ============================================
// INDEXEDDB HELPERS
// ============================================

/**
 * Open IndexedDB connection
 */
const openDB = () => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      // Create object stores
      if (!db.objectStoreNames.contains(STORES.ASSESSMENTS)) {
        const assessmentStore = db.createObjectStore(STORES.ASSESSMENTS, { keyPath: 'id' });
        assessmentStore.createIndex('timestamp', 'timestamp', { unique: false });
      }
      
      if (!db.objectStoreNames.contains(STORES.RESPONSES)) {
        const responseStore = db.createObjectStore(STORES.RESPONSES, { keyPath: 'id', autoIncrement: true });
        responseStore.createIndex('assessmentId', 'assessmentId', { unique: false });
        responseStore.createIndex('synced', 'synced', { unique: false });
        responseStore.createIndex('timestamp', 'timestamp', { unique: false });
      }
      
      if (!db.objectStoreNames.contains(STORES.TEAM_DATA)) {
        db.createObjectStore(STORES.TEAM_DATA, { keyPath: 'id' });
      }
      
      if (!db.objectStoreNames.contains(STORES.SYNC_QUEUE)) {
        const syncStore = db.createObjectStore(STORES.SYNC_QUEUE, { keyPath: 'id', autoIncrement: true });
        syncStore.createIndex('timestamp', 'timestamp', { unique: false });
      }
      
      if (!db.objectStoreNames.contains(STORES.CACHE)) {
        const cacheStore = db.createObjectStore(STORES.CACHE, { keyPath: 'key' });
        cacheStore.createIndex('expiry', 'expiry', { unique: false });
      }
    };
  });
};

/**
 * Generic IndexedDB operations
 */
const dbOperation = async (storeName, mode, operation) => {
  try {
    const db = await openDB();
    const transaction = db.transaction(storeName, mode);
    const store = transaction.objectStore(storeName);
    
    return new Promise((resolve, reject) => {
      const request = operation(store);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error('IndexedDB operation error:', error);
    throw error;
  }
};

// ============================================
// ASSESSMENT STORAGE
// ============================================

/**
 * Save assessment to IndexedDB
 */
export const saveAssessment = async (assessment) => {
  return dbOperation(STORES.ASSESSMENTS, 'readwrite', (store) => {
    return store.put({
      ...assessment,
      timestamp: Date.now()
    });
  });
};

/**
 * Get assessment from IndexedDB
 */
export const getAssessment = async (id) => {
  return dbOperation(STORES.ASSESSMENTS, 'readonly', (store) => {
    return store.get(id);
  });
};

/**
 * Get all cached assessments
 */
export const getAllAssessments = async () => {
  return dbOperation(STORES.ASSESSMENTS, 'readonly', (store) => {
    return store.getAll();
  });
};

/**
 * Delete assessment
 */
export const deleteAssessment = async (id) => {
  return dbOperation(STORES.ASSESSMENTS, 'readwrite', (store) => {
    return store.delete(id);
  });
};

// ============================================
// ASSESSMENT RESPONSES (OFFLINE SUBMISSIONS)
// ============================================

/**
 * Save assessment response for later sync
 */
export const saveAssessmentResponse = async (response) => {
  return dbOperation(STORES.RESPONSES, 'readwrite', (store) => {
    return store.add({
      ...response,
      synced: false,
      timestamp: Date.now()
    });
  });
};

/**
 * Get all unsynced responses
 */
export const getUnsyncedResponses = async () => {
  const db = await openDB();
  const transaction = db.transaction(STORES.RESPONSES, 'readonly');
  const store = transaction.objectStore(STORES.RESPONSES);
  const index = store.index('synced');
  
  return new Promise((resolve, reject) => {
    const request = index.getAll(false);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
};

/**
 * Mark response as synced
 */
export const markResponseSynced = async (id) => {
  const db = await openDB();
  const transaction = db.transaction(STORES.RESPONSES, 'readwrite');
  const store = transaction.objectStore(STORES.RESPONSES);
  
  const response = await new Promise((resolve) => {
    const req = store.get(id);
    req.onsuccess = () => resolve(req.result);
  });
  
  if (response) {
    response.synced = true;
    response.syncedAt = Date.now();
    await new Promise((resolve) => {
      const req = store.put(response);
      req.onsuccess = () => resolve();
    });
  }
};

/**
 * Delete synced responses older than 7 days
 */
export const cleanupOldResponses = async () => {
  const db = await openDB();
  const transaction = db.transaction(STORES.RESPONSES, 'readwrite');
  const store = transaction.objectStore(STORES.RESPONSES);
  const index = store.index('timestamp');
  
  const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
  
  return new Promise((resolve) => {
    const request = index.openCursor();
    let deletedCount = 0;
    
    request.onsuccess = (event) => {
      const cursor = event.target.result;
      if (cursor) {
        const response = cursor.value;
        if (response.synced && response.timestamp < sevenDaysAgo) {
          cursor.delete();
          deletedCount++;
        }
        cursor.continue();
      } else {
        resolve(deletedCount);
      }
    };
  });
};

// ============================================
// SYNC QUEUE
// ============================================

/**
 * Add request to sync queue
 */
export const queueRequest = async (request) => {
  return dbOperation(STORES.SYNC_QUEUE, 'readwrite', (store) => {
    return store.add({
      url: request.url,
      method: request.method,
      body: request.body,
      headers: request.headers,
      timestamp: Date.now(),
      retries: 0
    });
  });
};

/**
 * Get all queued requests
 */
export const getQueuedRequests = async () => {
  return dbOperation(STORES.SYNC_QUEUE, 'readonly', (store) => {
    return store.getAll();
  });
};

/**
 * Remove request from queue
 */
export const removeFromQueue = async (id) => {
  return dbOperation(STORES.SYNC_QUEUE, 'readwrite', (store) => {
    return store.delete(id);
  });
};

/**
 * Increment retry count
 */
export const incrementRetries = async (id) => {
  const db = await openDB();
  const transaction = db.transaction(STORES.SYNC_QUEUE, 'readwrite');
  const store = transaction.objectStore(STORES.SYNC_QUEUE);
  
  const request = await new Promise((resolve) => {
    const req = store.get(id);
    req.onsuccess = () => resolve(req.result);
  });
  
  if (request) {
    request.retries = (request.retries || 0) + 1;
    await new Promise((resolve) => {
      const req = store.put(request);
      req.onsuccess = () => resolve();
    });
  }
};

// ============================================
// API CACHE
// ============================================

/**
 * Cache API response
 */
export const cacheAPIResponse = async (key, data, ttl = 3600000) => {
  return dbOperation(STORES.CACHE, 'readwrite', (store) => {
    return store.put({
      key,
      data,
      timestamp: Date.now(),
      expiry: Date.now() + ttl
    });
  });
};

/**
 * Get cached API response
 */
export const getCachedAPIResponse = async (key) => {
  try {
    const cached = await dbOperation(STORES.CACHE, 'readonly', (store) => {
      return store.get(key);
    });
    
    if (!cached) return null;
    
    // Check if expired
    if (Date.now() > cached.expiry) {
      await dbOperation(STORES.CACHE, 'readwrite', (store) => {
        return store.delete(key);
      });
      return null;
    }
    
    return cached.data;
  } catch (error) {
    console.error('Error getting cached response:', error);
    return null;
  }
};

/**
 * Clear expired cache entries
 */
export const clearExpiredCache = async () => {
  const db = await openDB();
  const transaction = db.transaction(STORES.CACHE, 'readwrite');
  const store = transaction.objectStore(STORES.CACHE);
  const index = store.index('expiry');
  
  return new Promise((resolve) => {
    const request = index.openCursor();
    let deletedCount = 0;
    
    request.onsuccess = (event) => {
      const cursor = event.target.result;
      if (cursor) {
        if (cursor.value.expiry < Date.now()) {
          cursor.delete();
          deletedCount++;
        }
        cursor.continue();
      } else {
        resolve(deletedCount);
      }
    };
  });
};

// ============================================
// FORM DRAFTS
// ============================================

/**
 * Save form draft
 */
export const saveFormDraft = (formId, data) => {
  const drafts = getLocalStorage(STORAGE_KEYS.FORM_DRAFTS) || {};
  drafts[formId] = {
    data,
    timestamp: Date.now()
  };
  return setLocalStorage(STORAGE_KEYS.FORM_DRAFTS, drafts);
};

/**
 * Get form draft
 */
export const getFormDraft = (formId) => {
  const drafts = getLocalStorage(STORAGE_KEYS.FORM_DRAFTS) || {};
  return drafts[formId]?.data || null;
};

/**
 * Clear form draft
 */
export const clearFormDraft = (formId) => {
  const drafts = getLocalStorage(STORAGE_KEYS.FORM_DRAFTS) || {};
  delete drafts[formId];
  return setLocalStorage(STORAGE_KEYS.FORM_DRAFTS, drafts);
};

// ============================================
// SYNC STATUS
// ============================================

/**
 * Update last sync time
 */
export const updateLastSync = () => {
  return setLocalStorage(STORAGE_KEYS.LAST_SYNC, Date.now());
};

/**
 * Get last sync time
 */
export const getLastSync = () => {
  return getLocalStorage(STORAGE_KEYS.LAST_SYNC);
};

/**
 * Check if data is stale (needs sync)
 */
export const isDataStale = (maxAge = 3600000) => {
  const lastSync = getLastSync();
  if (!lastSync) return true;
  return Date.now() - lastSync > maxAge;
};

// ============================================
// CLEAR ALL DATA
// ============================================

/**
 * Clear all offline data
 */
export const clearAllOfflineData = async () => {
  try {
    // Clear localStorage
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
    
    // Clear IndexedDB
    const db = await openDB();
    const stores = [
      STORES.ASSESSMENTS,
      STORES.RESPONSES,
      STORES.TEAM_DATA,
      STORES.SYNC_QUEUE,
      STORES.CACHE
    ];
    
    for (const storeName of stores) {
      const transaction = db.transaction(storeName, 'readwrite');
      const store = transaction.objectStore(storeName);
      await new Promise((resolve) => {
        const req = store.clear();
        req.onsuccess = () => resolve();
      });
    }
    
    return true;
  } catch (error) {
    console.error('Error clearing offline data:', error);
    return false;
  }
};

// ============================================
// STORAGE INFO
// ============================================

/**
 * Get storage usage information
 */
export const getStorageInfo = async () => {
  try {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      const estimate = await navigator.storage.estimate();
      return {
        usage: estimate.usage,
        quota: estimate.quota,
        usagePercent: (estimate.usage / estimate.quota * 100).toFixed(2),
        available: estimate.quota - estimate.usage
      };
    }
    return null;
  } catch (error) {
    console.error('Error getting storage info:', error);
    return null;
  }
};

// Export all utilities
export default {
  // localStorage
  setLocalStorage,
  getLocalStorage,
  removeLocalStorage,
  
  // User & Auth
  saveUserProfile,
  getUserProfile,
  saveAuthToken,
  getAuthToken,
  clearAuthData,
  
  // Preferences
  savePreferences,
  getPreferences,
  updatePreference,
  
  // Assessments
  saveAssessment,
  getAssessment,
  getAllAssessments,
  deleteAssessment,
  
  // Responses
  saveAssessmentResponse,
  getUnsyncedResponses,
  markResponseSynced,
  cleanupOldResponses,
  
  // Sync Queue
  queueRequest,
  getQueuedRequests,
  removeFromQueue,
  incrementRetries,
  
  // Cache
  cacheAPIResponse,
  getCachedAPIResponse,
  clearExpiredCache,
  
  // Form Drafts
  saveFormDraft,
  getFormDraft,
  clearFormDraft,
  
  // Sync Status
  updateLastSync,
  getLastSync,
  isDataStale,
  
  // Utilities
  clearAllOfflineData,
  getStorageInfo
};