/**
 * Memory-Safe Timer Hooks
 * Provides timer hooks with automatic cleanup to prevent memory leaks
 *
 * @example
 * ```tsx
 * // Simple timeout
 * useTimeout(() => console.log('Done'), 1000);
 *
 * // Conditional timeout
 * const [shouldRun, setShouldRun] = useState(false);
 * useTimeout(() => {
 *   if (shouldRun) console.log('Conditional');
 * }, 1000);
 * ```
 */

import { useEffect, useRef } from 'react';

/**
 * useTimeout - Memory-safe setTimeout with automatic cleanup
 *
 * @param callback - Function to execute after delay
 * @param delay - Delay in milliseconds (null disables the timer)
 */
export function useTimeout(callback: () => void, delay: number | null): void {
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
 * useInterval - Memory-safe setInterval with automatic cleanup
 *
 * @param callback - Function to execute at interval
 * @param delay - Interval in milliseconds (null disables the interval)
 */
export function useInterval(callback: () => void, delay: number | null): void {
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

/**
 * useConditionalTimeout - Timeout that only runs when condition is true
 *
 * @param callback - Function to execute after delay
 * @param delay - Delay in milliseconds
 * @param condition - Boolean condition, timer only runs when true
 */
export function useConditionalTimeout(
  callback: () => void,
  delay: number,
  condition: boolean
): void {
  useTimeout(() => {
    if (condition) {
      callback();
    }
  }, condition ? delay : null);
}

/**
 * useDebounce - Debounce a callback function
 *
 * @param callback - Function to debounce
 * @param delay - Delay in milliseconds
 * @returns Debounced function
 */
export function useDebounce<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const callbackRef = useRef(callback);
  const timeoutRef = useRef<NodeJS.Timeout | undefined>();

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  return ((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      callbackRef.current(...args);
    }, delay);
  }) as T;
}

/**
 * useThrottle - Throttle a callback function
 *
 * @param callback - Function to throttle
 * @param delay - Delay in milliseconds
 * @returns Throttled function
 */
export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const callbackRef = useRef(callback);
  const lastRunRef = useRef<Date>(new Date(0));
  const timeoutRef = useRef<NodeJS.Timeout | undefined>();

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  return ((...args: Parameters<T>) => {
    const now = new Date();
    const timeSinceLastRun = now.getTime() - lastRunRef.current.getTime();

    if (timeSinceLastRun >= delay) {
      lastRunRef.current = now;
      callbackRef.current(...args);
    } else {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        lastRunRef.current = new Date();
        callbackRef.current(...args);
      }, delay - timeSinceLastRun);
    }
  }) as T;
}
