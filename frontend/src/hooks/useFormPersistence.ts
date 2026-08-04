/**
 * useFormPersistence Hook
 *
 * Provides automatic form data persistence to localStorage
 * to prevent data loss during navigation, redirects, or page refreshes.
 *
 * Features:
 * - Automatically saves form data to localStorage as user types
 * - Automatically restores form data when component mounts
 * - Debounced saving to reduce localStorage writes
 * - Optional clear on success/submit
 * - Configurable storage key
 */

import { useEffect, useRef, useState } from 'react';

interface UseFormPersistenceOptions<T> {
  storageKey: string;
  defaultValue: T;
  enabled?: boolean;
  debounceMs?: number;
  onRestore?: (data: T) => void;
  onClear?: () => void;
}

export function useFormPersistence<T extends object>({
  storageKey,
  defaultValue,
  enabled = true,
  debounceMs = 500,
  onRestore,
  onClear,
}: UseFormPersistenceOptions<T>) {
  const [data, setData] = useState<T>(defaultValue);
  const [hasSavedData, setHasSavedData] = useState(false);
  const saveTimeoutRef = useRef<number | null>(null);
  const isMountedRef = useRef(true);

  // Check for saved data on mount
  useEffect(() => {
    if (!enabled) return;

    try {
      const savedData = localStorage.getItem(storageKey);
      if (savedData) {
        const parsed = JSON.parse(savedData);
        setData(parsed);
        setHasSavedData(true);

        if (onRestore && isMountedRef.current) {
          onRestore(parsed);
        }

        console.log(`[useFormPersistence] Restored data from ${storageKey}`);
      }
    } catch (error) {
      console.error(`[useFormPersistence] Failed to restore data from ${storageKey}:`, error);
    }

    // Cleanup on unmount
    return () => {
      isMountedRef.current = false;
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [storageKey, enabled, onRestore]);

  // Debounced save to localStorage
  const saveData = useRef((value: T) => {
    if (!enabled) return;

    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Set new timeout for debounced save
    saveTimeoutRef.current = window.setTimeout(() => {
      if (!isMountedRef.current) return;

      try {
        localStorage.setItem(storageKey, JSON.stringify(value));
        console.log(`[useFormPersistence] Saved data to ${storageKey}`);
      } catch (error) {
        console.error(`[useFormPersistence] Failed to save data to ${storageKey}:`, error);
      }
    }, debounceMs);
  });

  // Watch for data changes and save
  useEffect(() => {
    if (enabled) {
      saveData.current(data);
    }
  }, [data, enabled, debounceMs]);

  // Clear saved data
  const clearSavedData = () => {
    if (!enabled) return;

    try {
      localStorage.removeItem(storageKey);
      setHasSavedData(false);

      if (onClear) {
        onClear();
      }

      console.log(`[useFormPersistence] Cleared data from ${storageKey}`);
    } catch (error) {
      console.error(`[useFormPersistence] Failed to clear data from ${storageKey}:`, error);
    }
  };

  // Restore to default value
  const restoreDefault = () => {
    setData(defaultValue);
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    // Don't clear saved data, just reset current state
  };

  return {
    data,
    setData,
    hasSavedData,
    clearSavedData,
    restoreDefault,
  };
}

/**
 * Hook to listen for session expiry warnings
 * and optionally save form data before redirect
 */
export function useSessionExpiryHandler<T extends object>(
  saveFn: () => void
) {
  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      // Save data when page is about to unload
      saveFn();

      // Don't show confirmation dialog (browser may ignore anyway)
      // return undefined;
    };

    const handleSessionExpiring = () => {
      console.log('[useSessionExpiryHandler] Session expiring, saving form data');
      saveFn();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('sessionExpiring', handleSessionExpiring);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('sessionExpiring', handleSessionExpiring);
    };
  }, [saveFn]);
}
