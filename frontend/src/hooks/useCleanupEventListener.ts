/**
 * Memory-Safe Event Listener Hooks
 * Provides event listener hooks with automatic cleanup to prevent memory leaks
 *
 * @example
 * ```tsx
 * // Simple event listener
 * useEventListener('click', handleClick, document);
 *
 * // Window resize listener
 * useEventListener('resize', handleResize, window);
 *
 * // Keyboard shortcuts
 * useEventListener('keydown', handleKeyDown, window);
 * ```
 */

import { useEffect, useRef } from 'react';

/**
 * useEventListener - Memory-safe event listener with automatic cleanup
 *
 * @param eventName - Name of the event (e.g., 'click', 'resize', 'keydown')
 * @param handler - Function to execute when event is triggered
 * @param element - Target element (defaults to window)
 * @param options - Event listener options
 */
export function useEventListener<
  K extends keyof MediaQueryListEventMap | keyof WindowEventMap | keyof DocumentEventMap
>(
  eventName: K,
  handler: (event: any) => void,
  element: HTMLElement | Document | Window | MediaQueryList = window,
  options?: boolean | AddEventListenerOptions
): void {
  const handlerRef = useRef(handler);

  // Keep handler ref updated without causing effect re-run
  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  useEffect(() => {
    // Don't add listener if element doesn't support addEventListener
    if (!element || !element.addEventListener) {
      return;
    }

    // Create event listener with ref to latest handler
    const eventListener = (event: Event) => {
      handlerRef.current(event);
    };

    // Add event listener
    element.addEventListener(eventName, eventListener, options);

    // Cleanup function - removes event listener on unmount or dependency change
    return () => {
      element.removeEventListener(eventName, eventListener, options);
    };
  }, [eventName, element, options]);
}

/**
 * useWindowResize - Convenience hook for window resize events
 *
 * @param handler - Function to execute when window is resized
 */
export function useWindowResize(handler: () => void): void {
  useEventListener('resize', handler, window);
}

/**
 * useWindowScroll - Convenience hook for window scroll events
 *
 * @param handler - Function to execute when window is scrolled
 */
export function useWindowScroll(handler: () => void): void {
  useEventListener('scroll', handler, window);
}

/**
 * useKeyDown - Convenience hook for keyboard events
 *
 * @param key - Specific key to listen for (e.g., 'Escape', 'Enter')
 * @param handler - Function to execute when key is pressed
 * @param element - Target element (defaults to window)
 */
export function useKeyDown(
  key: string,
  handler: (event: KeyboardEvent) => void,
  element: Window | Document = window
): void {
  useEventListener('keydown', (event: KeyboardEvent) => {
    if (event.key === key) {
      handler(event);
    }
  }, element);
}

/**
 * useClickOutside - Detect clicks outside a specific element
 *
 * @param ref - React ref to the element
 * @param handler - Function to execute when click outside is detected
 */
export function useClickOutside(
  ref: React.RefObject<HTMLElement>,
  handler: (event: MouseEvent) => void
): void {
  useEventListener(
    'click',
    (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler(event);
      }
    },
    document,
    // Use capture phase to detect clicks before they reach children
    { capture: true }
  );
}

/**
 * useMediaQuery - Respond to media query changes
 *
 * @param query - CSS media query (e.g., '(max-width: 768px)')
 * @returns Boolean indicating if media query matches
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = React.useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEventListener(
    'change',
    (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    },
    window.matchMedia(query)
  );

  return matches;
}

// Import React for useState
import React from 'react';
