/**
 * useOffline Hook
 * 
 * React hook for managing offline state and syncing
 * 
 * Features:
 * - Detect online/offline status
 * - Auto-sync when connection restored
 * - Queue failed requests
 * - Show offline indicator
 * - Handle offline form submissions
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  getUnsyncedResponses,
  markResponseSynced,
  getQueuedRequests,
  removeFromQueue,
  incrementRetries,
  updateLastSync,
  getLastSync,
  isDataStale
} from '../utils/offlineStorage';

const MAX_RETRIES = 3;

/**
 * Hook for managing offline functionality
 */
export const useOffline = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isSyncing, setIsSyncing] = useState(false);
  const [pendingCount, setPendingCount] = useState(0);
  const [lastSyncTime, setLastSyncTime] = useState(null);
  const syncInProgress = useRef(false);

  // Update online status
  useEffect(() => {
    const handleOnline = () => {
      console.log('🟢 Connection restored');
      setIsOnline(true);
      // Trigger sync after coming online
      syncPendingData();
    };

    const handleOffline = () => {
      console.log('🔴 Connection lost');
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Check pending items count on mount and periodically
  useEffect(() => {
    updatePendingCount();
    
    const interval = setInterval(updatePendingCount, 30000); // Every 30s
    
    return () => clearInterval(interval);
  }, []);

  // Load last sync time
  useEffect(() => {
    const loadLastSync = async () => {
      const lastSync = await getLastSync();
      setLastSyncTime(lastSync);
    };
    loadLastSync();
  }, []);

  /**
   * Update count of pending sync items
   */
  const updatePendingCount = useCallback(async () => {
    try {
      const [responses, requests] = await Promise.all([
        getUnsyncedResponses(),
        getQueuedRequests()
      ]);
      
      setPendingCount(responses.length + requests.length);
    } catch (error) {
      console.error('Error updating pending count:', error);
    }
  }, []);

  /**
   * Sync all pending data
   */
  const syncPendingData = useCallback(async () => {
    // Prevent multiple simultaneous syncs
    if (syncInProgress.current || !navigator.onLine) {
      return;
    }

    syncInProgress.current = true;
    setIsSyncing(true);

    try {
      console.log('🔄 Starting sync...');
      
      // Sync assessment responses
      const responses = await getUnsyncedResponses();
      console.log(`Found ${responses.length} unsynced responses`);
      
      for (const response of responses) {
        try {
          // Send to API
          const apiResponse = await fetch('/api/v1/assessments/submit', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('psychsync_auth_token')}`
            },
            body: JSON.stringify(response.data)
          });

          if (apiResponse.ok) {
            await markResponseSynced(response.id);
            console.log(`✅ Synced response ${response.id}`);
          } else {
            console.error(`❌ Failed to sync response ${response.id}`);
          }
        } catch (error) {
          console.error(`Error syncing response ${response.id}:`, error);
        }
      }

      // Sync queued requests
      const requests = await getQueuedRequests();
      console.log(`Found ${requests.length} queued requests`);
      
      for (const request of requests) {
        try {
          if (request.retries >= MAX_RETRIES) {
            console.warn(`Max retries reached for request ${request.id}, removing`);
            await removeFromQueue(request.id);
            continue;
          }

          const response = await fetch(request.url, {
            method: request.method,
            headers: request.headers,
            body: request.body
          });

          if (response.ok) {
            await removeFromQueue(request.id);
            console.log(`✅ Synced request ${request.id}`);
          } else {
            await incrementRetries(request.id);
            console.error(`❌ Failed to sync request ${request.id}`);
          }
        } catch (error) {
          await incrementRetries(request.id);
          console.error(`Error syncing request ${request.id}:`, error);
        }
      }

      // Update last sync time
      await updateLastSync();
      setLastSyncTime(Date.now());
      
      // Update pending count
      await updatePendingCount();
      
      console.log('✅ Sync complete');
    } catch (error) {
      console.error('Sync error:', error);
    } finally {
      setIsSyncing(false);
      syncInProgress.current = false;
    }
  }, [updatePendingCount]);

  /**
   * Manually trigger sync
   */
  const triggerSync = useCallback(() => {
    if (!isOnline) {
      console.warn('Cannot sync while offline');
      return Promise.reject(new Error('Device is offline'));
    }
    return syncPendingData();
  }, [isOnline, syncPendingData]);

  /**
   * Check if data needs sync
   */
  const needsSync = useCallback(() => {
    return isDataStale() || pendingCount > 0;
  }, [pendingCount]);

  return {
    isOnline,
    isOffline: !isOnline,
    isSyncing,
    pendingCount,
    lastSyncTime,
    syncPendingData,
    triggerSync,
    needsSync,
    updatePendingCount
  };
};

/**
 * Hook for offline-aware API requests
 */
export const useOfflineRequest = () => {
  const { isOnline } = useOffline();

  const makeRequest = useCallback(async (url, options = {}) => {
    // If online, make normal request
    if (isOnline) {
      return fetch(url, options);
    }

    // If offline, queue request
    console.log('📥 Queueing request for later sync:', url);
    
    // Import queue function dynamically to avoid circular dependencies
    const { queueRequest } = await import('../utils/offlineStorage');
    
    await queueRequest({
      url,
      method: options.method || 'GET',
      body: options.body,
      headers: options.headers
    });

    // Return mock response indicating queued status
    return new Response(
      JSON.stringify({
        queued: true,
        message: 'Request queued for sync when online'
      }),
      {
        status: 202,
        statusText: 'Accepted',
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }, [isOnline]);

  return { makeRequest, isOnline };
};

/**
 * Hook for form with offline support
 */
export const useOfflineForm = (formId, onSubmit) => {
  const { isOnline } = useOffline();
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Load draft on mount
  useEffect(() => {
    const loadDraft = async () => {
      const { getFormDraft } = await import('../utils/offlineStorage');
      const draft = getFormDraft(formId);
      if (draft) {
        setIsDirty(true);
      }
    };
    loadDraft();
  }, [formId]);

  /**
   * Save draft to offline storage
   */
  const saveDraft = useCallback(async (data) => {
    const { saveFormDraft } = await import('../utils/offlineStorage');
    await saveFormDraft(formId, data);
    setIsDirty(true);
  }, [formId]);

  /**
   * Submit form (online or offline)
   */
  const handleSubmit = useCallback(async (data) => {
    setIsSaving(true);
    
    try {
      if (isOnline) {
        // Submit normally
        await onSubmit(data);
        
        // Clear draft after successful submit
        const { clearFormDraft } = await import('../utils/offlineStorage');
        await clearFormDraft(formId);
        setIsDirty(false);
      } else {
        // Save for later sync
        const { saveAssessmentResponse } = await import('../utils/offlineStorage');
        await saveAssessmentResponse({
          formId,
          data,
          timestamp: Date.now()
        });
        
        console.log('Form saved for offline sync');
        setIsDirty(false);
      }
    } catch (error) {
      console.error('Form submission error:', error);
      throw error;
    } finally {
      setIsSaving(false);
    }
  }, [isOnline, onSubmit, formId]);

  return {
    saveDraft,
    handleSubmit,
    isDirty,
    isSaving,
    isOnline
  };
};

/**
 * Hook for offline indicator component
 */
export const useOfflineIndicator = () => {
  const { isOnline, isSyncing, pendingCount } = useOffline();
  
  const getStatus = useCallback(() => {
    if (isSyncing) {
      return {
        type: 'syncing',
        message: 'Syncing data...',
        color: 'blue'
      };
    }
    
    if (!isOnline) {
      return {
        type: 'offline',
        message: pendingCount > 0 
          ? `Offline (${pendingCount} pending)` 
          : 'Offline',
        color: 'orange'
      };
    }
    
    if (pendingCount > 0) {
      return {
        type: 'pending',
        message: `${pendingCount} items to sync`,
        color: 'yellow'
      };
    }
    
    return {
      type: 'online',
      message: 'Online',
      color: 'green'
    };
  }, [isOnline, isSyncing, pendingCount]);

  return {
    status: getStatus(),
    isOnline,
    isSyncing,
    pendingCount
  };
};

export default useOffline;