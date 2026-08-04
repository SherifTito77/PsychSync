/**
 * Memory-Safe Hooks Collection
 *
 * This module exports all custom hooks designed to prevent memory leaks.
 * Use these hooks instead of raw setTimeout, setInterval, addEventListener, or WebSocket.
 *
 * @example
 * ```tsx
 * import { useTimeout, useEventListener, useWebSocket } from '@/hooks/cleanupHooks';
 *
 * // Instead of setTimeout
 * useTimeout(() => console.log('Done'), 1000);
 *
 * // Instead of addEventListener
 * useEventListener('click', handleClick);
 *
 * // Instead of new WebSocket()
 * const ws = useWebSocket('ws://localhost:8000');
 * ```
 */

// Timer hooks
export {
  useTimeout,
  useInterval,
  useConditionalTimeout,
  useDebounce,
  useThrottle,
} from './useCleanupTimer';

// Event listener hooks
export {
  useEventListener,
  useWindowResize,
  useWindowScroll,
  useKeyDown,
  useClickOutside,
  useMediaQuery,
} from './useCleanupEventListener';

// WebSocket hooks
export {
  useWebSocket,
  useWebSocketWithRef,
  ReadyState,
} from './useCleanupWebSocket';

/**
 * MIGRATION GUIDE
 * ===============
 *
 * ❌ OLD (Memory Leak):
 * ```tsx
 * useEffect(() => {
 *   setTimeout(() => console.log('Done'), 1000);
 * }, []);
 * ```
 *
 * ✅ NEW (Memory Safe):
 * ```tsx
 * import { useTimeout } from '@/hooks/cleanupHooks';
 *
 * useTimeout(() => console.log('Done'), 1000);
 * ```
 *
 * ---
 *
 * ❌ OLD (Memory Leak):
 * ```tsx
 * useEffect(() => {
 *   const interval = setInterval(() => {
 *     console.log('Tick');
 *   }, 1000);
 * }, []);
 * ```
 *
 * ✅ NEW (Memory Safe):
 * ```tsx
 * import { useInterval } from '@/hooks/cleanupHooks';
 *
 * useInterval(() => console.log('Tick'), 1000);
 * ```
 *
 * ---
 *
 * ❌ OLD (Memory Leak):
 * ```tsx
 * useEffect(() => {
 *   document.addEventListener('click', handleClick);
 * }, []);
 * ```
 *
 * ✅ NEW (Memory Safe):
 * ```tsx
 * import { useEventListener } from '@/hooks/cleanupHooks';
 *
 * useEventListener('click', handleClick, document);
 * ```
 *
 * ---
 *
 * ❌ OLD (Memory Leak):
 * ```tsx
 * useEffect(() => {
 *   const ws = new WebSocket('ws://localhost:8000');
 *   ws.onmessage = (e) => console.log(e.data);
 * }, []);
 * ```
 *
 * ✅ NEW (Memory Safe):
 * ```tsx
 * import { useWebSocket } from '@/hooks/cleanupHooks';
 *
 * const ws = useWebSocket('ws://localhost:8000', {
 *   onMessage: (data) => console.log(data)
 * });
 * ```
 */
