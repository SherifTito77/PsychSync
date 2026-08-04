/**
 * useTimeoutWithCleanup Hook
 *
 * Provides a setTimeout with automatic cleanup to prevent memory leaks.
 * Solves the common issue of setTimeout firing after component unmount.
 *
 * @example
 * ```tsx
 * useTimeoutWithCleanup(() => {
 *   console.log('Timeout fired!');
 * }, 5000);
 * ```
 *
 * @example With dynamic delay
 * ```tsx
 * const [delay, setDelay] = useState(5000);
 * useTimeoutWithCleanup(() => {
 *   setShowToast(false);
 * }, delay);
 * ```
 */

import { useEffect, useRef } from 'react';

export function useTimeoutWithCleanup(
  callback: () => void,
  delay: number | null
): void {
  const timeoutRef = useRef<NodeJS.Timeout | undefined>();
  const callbackRef = useRef(callback);

  // Keep callback ref updated without causing effect re-run
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    // Don't create timeout if delay is null or 0
    if (delay === null || delay === 0) {
      return;
    }

    // Create timeout
    const timeoutId = setTimeout(() => {
      callbackRef.current();
    }, delay);

    // Store ref for cleanup
    timeoutRef.current = timeoutId;

    // Cleanup function - clears timeout on unmount or delay change
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [delay]);
}

/**
 * useIntervalWithCleanup Hook
 *
 * Provides a setInterval with automatic cleanup to prevent memory leaks.
 *
 * @example
 * ```tsx
 * useIntervalWithCleanup(() => {
 *   console.log('Interval tick');
 * }, 1000);
 * ```
 *
 * @example With conditional execution
 * ```tsx
 * const [isRunning, setIsRunning] = useState(true);
 * useIntervalWithCleanup(() => {
 *   if (isRunning) {
 *     fetchData();
 *   }
 * }, 5000);
 * ```
 */

export function useIntervalWithCleanup(
  callback: () => void,
  delay: number | null
): void {
  const intervalRef = useRef<NodeJS.Timeout | undefined>();
  const callbackRef = useRef(callback);

  // Keep callback ref updated
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    // Don't create interval if delay is null or 0
    if (delay === null || delay === 0) {
      return;
    }

    // Create interval
    const intervalId = setInterval(() => {
      callbackRef.current();
    }, delay);

    // Store ref for cleanup
    intervalRef.current = intervalId;

    // Cleanup function - clears interval on unmount or delay change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [delay]);
}
