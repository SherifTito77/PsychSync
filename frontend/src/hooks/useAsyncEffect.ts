/**
 * Safe Async Effect Hook
 *
 * Prevents race conditions in useEffect by:
 * - Cancelling pending operations on unmount
 * - Checking mounted status before state updates
 * - Supporting AbortController for fetch operations
 *
 * @example
 * ```tsx
 * useAsyncEffect(async (signal, isMounted) => {
 *   const data = await fetch('/api/data', { signal });
 *   if (isMounted()) {
 *     setState(data);
 *   }
 * }, [dependency]);
 * ```
 */

import { useEffect, useRef, useCallback } from 'react';

export interface AsyncEffectOptions {
  /**
   * Whether to ignore errors when the effect is aborted
   * @default true
   */
  ignoreAbortError?: boolean;
}

/**
 * Hook for handling async operations in useEffect safely
 *
 * @param effect - Async function to run in the effect
 * @param deps - Dependency array
 * @param options - Options for the effect behavior
 */
export function useAsyncEffect(
  effect: (signal: AbortSignal, isMounted: () => boolean) => Promise<void> | void,
  deps: unknown[] = [],
  options: AsyncEffectOptions = {}
) {
  const { ignoreAbortError = true } = options;

  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;
    let isMounted = true;

    // Define the isMounted checker
    const checkMounted = (): boolean => isMounted;

    // Run the effect
    const promise = effect(signal, checkMounted);

    // Cleanup function
    return () => {
      isMounted = false;

      // Abort any ongoing operations
      abortController.abort();

      // Handle the promise if it's still pending
      if (promise) {
        promise.catch((error: Error) => {
          // Ignore abort errors if configured
          if (ignoreAbortError && error.name === 'AbortError') {
            return;
          }
          // Log other errors
          console.warn('Async effect cleanup error:', error);
        });
      }
    };
  }, deps);
}

/**
 * Hook for safe fetch with automatic cancellation
 *
 * @param url - URL to fetch
 * @param options - Fetch options
 * @param deps - Dependency array
 * @returns Object with data, loading, error states
 */
export function useSafeFetch<T = unknown>(
  url: string | null,
  options: RequestInit = {},
  deps: unknown[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useAsyncEffect(async (signal, isMounted) => {
    if (!url) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(url, {
        ...options,
        signal,
      });

      if (!isMounted()) {
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const jsonData: T = await response.json();

      if (isMounted()) {
        setData(jsonData);
      }
    } catch (err) {
      if (err instanceof Error) {
        if (err.name !== 'AbortError' && isMounted()) {
          setError(err);
        }
      }
    } finally {
      if (isMounted()) {
        setLoading(false);
      }
    }
  }, [url, ...deps]);

  return { data, loading, error };
}

/**
 * Hook for safe interval with automatic cleanup
 *
 * @param callback - Function to run on interval
 * @param delay - Delay in milliseconds (null to pause)
 * @param options - Options
 */
export function useSafeInterval(
  callback: () => void,
  delay: number | null,
  options: {
    runOnMount?: boolean;
  } = {}
) {
  const { runOnMount = true } = options;

  useEffect(() => {
    if (delay === null) {
      return;
    }

    // Run immediately if configured
    if (runOnMount) {
      callback();
    }

    const intervalId = setInterval(() => {
      callback();
    }, delay);

    return () => {
      clearInterval(intervalId);
    };
  }, [delay, callback, runOnMount]);
}

/**
 * Hook for safe timeout with automatic cleanup
 *
 * @param callback - Function to run after delay
 * @param delay - Delay in milliseconds (null to cancel)
 */
export function useSafeTimeout(
  callback: () => void,
  delay: number | null
) {
  useEffect(() => {
    if (delay === null) {
      return;
    }

    const timeoutId = setTimeout(() => {
      callback();
    }, delay);

    return () => {
      clearTimeout(timeoutId);
    };
  }, [delay, callback]);
}

// Import useState for useSafeFetch
import { useState } from 'react';
