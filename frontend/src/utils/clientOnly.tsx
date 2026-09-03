/**
 * Client-Side Rendering Utilities
 *
 * Prevents hydration-like errors in SPAs by ensuring browser APIs
 * are only accessed after component mount.
 *
 * @example
 * ```tsx
 * // ❌ BAD: Direct access during render
 * function MyComponent() {
 *   const data = localStorage.getItem('key'); // Can cause issues
 *   return <div>{data}</div>;
 * }
 *
 * // ✅ GOOD: Use client-only utilities
 * function MyComponent() {
 *   const isMounted = useIsMounted();
 *   const [data, setData] = useState(null);
 *
 *   useEffect(() => {
 *     if (isMounted) {
 *       setData(localStorage.getItem('key'));
 *     }
 *   }, [isMounted]);
 *
 *   if (!isMounted) return null; // or show loading
 *   return <div>{data}</div>;
 * }
 * ```
 */

import { useEffect, useState } from 'react';

/**
 * Hook to track if component is mounted on the client
 * Returns true only after the component has mounted on the client
 *
 * This prevents hydration mismatches by ensuring code only runs
 * after client-side hydration is complete.
 */
export function useIsMounted(): boolean {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  return isMounted;
}

/**
 * Hook to safely access localStorage
 * Returns null during SSR, actual value on client after mount
 *
 * @param key - localStorage key to read
 * @param defaultValue - fallback value if key doesn't exist
 * @returns stored value or defaultValue
 */
export function useLocalStorage<T = string>(
  key: string,
  defaultValue: T
): T | null {
  const isMounted = useIsMounted();
  const [value, setValue] = useState<T | null>(defaultValue);

  useEffect(() => {
    if (!isMounted) return;

    try {
      const item = localStorage.getItem(key);
      if (item) {
        // Try to parse as JSON, fallback to string
        try {
          setValue(JSON.parse(item));
        } catch {
          setValue(item as unknown as T);
        }
      }
    } catch (error) {
      console.warn(`Failed to read localStorage key "${key}":`, error);
      setValue(defaultValue);
    }
  }, [key, isMounted]);

  return isMounted ? value : null;
}

/**
 * Higher-order component pattern for client-only rendering
 * Wraps a component to only render on the client (not during SSR)
 *
 * @example
 * ```tsx
 * const MyComponent = () => {
 *   const data = localStorage.getItem('key'); // Safe now!
 *   return <div>{data}</div>;
 * };
 *
 * export default withClientOnly(MyComponent);
 * ```
 */
export function withClientOnly<P extends object>(
  Component: React.ComponentType<P>
): React.ComponentType<P> {
  return function ClientOnlyWrapper(props: P) {
    const isMounted = useIsMounted();

    if (!isMounted) {
      return null; // or return a loading placeholder
    }

    return <Component {...props} />;
  };
}

/**
 * Safe wrapper to check if code is running in a browser environment
 * Use this for code that needs to access browser APIs outside of React
 *
 * @example
 * ```ts
 * if (isBrowser()) {
 *   console.log(window.location.href);
 * }
 * ```
 */
export function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof document !== 'undefined';
}

/**
 * Safe localStorage.getItem with error handling
 * Returns null if not in browser or on error
 *
 * @param key - localStorage key
 * @returns stored value or null
 */
export function safeGetItem(key: string): string | null {
  if (!isBrowser()) return null;

  try {
    return localStorage.getItem(key);
  } catch (error) {
    console.warn(`Failed to get localStorage key "${key}":`, error);
    return null;
  }
}

/**
 * Safe localStorage.setItem with error handling
 *
 * @param key - localStorage key
 * @param value - value to store (will be JSON.stringify'd if object)
 * @returns true if successful, false otherwise
 */
export function safeSetItem(key: string, value: any): boolean {
  if (!isBrowser()) return false;

  try {
    const serialized = typeof value === 'string' ? value : JSON.stringify(value);
    localStorage.setItem(key, serialized);
    return true;
  } catch (error) {
    console.warn(`Failed to set localStorage key "${key}":`, error);
    return false;
  }
}

/**
 * Safe localStorage.removeItem with error handling
 *
 * @param key - localStorage key to remove
 * @returns true if successful, false otherwise
 */
export function safeRemoveItem(key: string): boolean {
  if (!isBrowser()) return false;

  try {
    localStorage.removeItem(key);
    return true;
  } catch (error) {
    console.warn(`Failed to remove localStorage key "${key}":`, error);
    return false;
  }
}

/**
 * ClientOnly component wrapper
 * Children only render on the client after hydration
 *
 * @example
 * ```tsx
 * <ClientOnly fallback={<div>Loading...</div>}>
 *   <MyComponentWithBrowserAPIs />
 * </ClientOnly>
 * ```
 */
export const ClientOnly: React.FC<{
  children: React.ReactNode;
  fallback?: React.ReactNode;
}> = ({ children, fallback = null }) => {
  const isMounted = useIsMounted();
  return <>{isMounted ? children : fallback}</>;
};
