/**
 * Error Boundary Coverage Analysis & Utilities
 *
 * This file documents what errors the ErrorBoundary CATCHES and what it DOESN'T CATCH,
 * plus utilities to handle errors that fall through the cracks.
 */

/**
 * WHAT ERROR BOUNDARY CATCHES ✅
 * ---------------------------------
 * 1. Render method errors
 * 2. Lifecycle method errors (componentDidMount, componentDidUpdate, etc.)
 * 3. Errors in constructor
 * 4. Errors during component tree reconciliation
 * 5. Errors thrown from child components
 * 6. Lazy loading component errors (React.Suspense failures)
 *
 * WHAT ERROR BOUNDARY DOESN'T CATCH ❌
 * --------------------------------------
 * 1. Event handler errors (onClick, onChange, etc.)
 * 2. Asynchronous code (setTimeout, setInterval, Promises)
 * 3. Server-side errors (not applicable - this is SPA)
 * 4. Errors in error callbacks (onError prop)
 * 5. Errors thrown in the error boundary itself
 * 6. Errors in event listeners
 * 7. Navigation errors (outside React tree)
 * 8. Resource loading errors (images, scripts, stylesheets)
 * 9. Network errors (fetch, axios) - unless thrown in render
 * 10. Unhandled promise rejections
 */

import React, { useEffect, useCallback, useState } from 'react';
import logger from '@/utils/logger';

/**
 * Error types for better categorization
 */
export enum ErrorType {
  RENDER = 'render',
  EVENT_HANDLER = 'event_handler',
  ASYNC = 'async',
  NETWORK = 'network',
  NAVIGATION = 'navigation',
  RESOURCE = 'resource',
  UNKNOWN = 'unknown'
}

/**
 * Wraps an async function with error handling
 * Use this for async code in useEffect, event handlers, etc.
 *
 * @example
 * ```tsx
 * useEffect(() => {
 *   const fetchData = async () => {
 *     await withErrorHandling(async () => {
 *       const data = await fetch('/api/data');
 *       return data.json();
 *     }, {
 *       context: 'fetching data',
 *       showError: true
 *     });
 *   };
 *   fetchData();
 * }, []);
 * ```
 */
export async function withErrorHandling<T>(
  fn: () => Promise<T>,
  options: {
    context?: string;
    showError?: boolean;
    fallback?: T;
    onError?: (error: Error) => void;
  } = {}
): Promise<T | null> {
  const { context, showError = false, fallback = null, onError } = options;

  try {
    return await fn();
  } catch (error) {
    const errorObj = error instanceof Error ? error : new Error(String(error));

    logger.error('Async error caught by withErrorHandling', {
      error_message: errorObj.message,
      error_stack: errorObj.stack,
      context: context || 'unknown',
      error_type: ErrorType.ASYNC
    });

    if (onError) {
      onError(errorObj);
    }

    if (showError) {
      // You could dispatch to a toast/snackbar here
      console.error(`Error in ${context}:`, errorObj.message);
    }

    return fallback as T | null;
  }
}

/**
 * Wrap an event handler with error handling
 *
 * @example
 * ```tsx
 * const handler = wrapEventHandler(
 *   () => { throw new Error('Oops!'); },
 *   'button click'
 * );
 * const button = React.createElement('button', { onClick: handler }, 'Click Me');
 * ```
 */
export function wrapEventHandler<T extends (...args: any[]) => any>(
  handler: T,
  context: string = 'event handler'
): T {
  return ((...args: any[]) => {
    try {
      const result = handler(...args);

      // If handler returns a promise, handle it
      if (result instanceof Promise) {
        return result.catch((error) => {
          logger.error('Event handler promise error', {
            error_message: error.message,
            error_stack: error.stack,
            context,
            error_type: ErrorType.EVENT_HANDLER
          });
          return null;
        });
      }

      return result;
    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error(String(error));

      logger.error('Event handler error', {
        error_message: errorObj.message,
        error_stack: errorObj.stack,
        context,
        error_type: ErrorType.EVENT_HANDLER
      });

      return null;
    }
  }) as T;
}

/**
 * Hook for safe async operations in useEffect
 * Handles cleanup and error tracking
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { execute, loading, error } = useSafeAsyncEffect();
 *   useEffect(() => {
 *     execute(async () => {
 *       const data = await fetch('/api/data');
 *       return data.json();
 *     }, 'fetching data');
 *   }, []);
 *   if (loading) return null;
 *   if (error) return React.createElement('div', null, 'Error: ', error.message);
 *   return React.createElement('div', null, 'Content');
 * }
 * ```
 */
export function useSafeAsyncEffect() {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  const execute = useCallback(async <T,>(
    fn: () => Promise<T>,
    context: string = 'async operation'
  ): Promise<T | null> => {
    setLoading(true);
    setError(null);

    try {
      const result = await fn();
      setLoading(false);
      return result;
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error(String(err));

      logger.error('Safe async effect error', {
        error_message: errorObj.message,
        error_stack: errorObj.stack,
        context,
        error_type: ErrorType.ASYNC
      });

      setError(errorObj);
      setLoading(false);
      return null;
    }
  }, []);

  return { execute, loading, error };
}

/**
 * Hook to wrap event handlers with automatic error handling
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { handleError } = useErrorHandler();
 *   const handleClick = () => handleError(
 *     () => { throw new Error('Button clicked!'); },
 *     'button click'
 *   );
 *   return React.createElement('button', { onClick: handleClick }, 'Click Me');
 * }
 * ```
 */
export function useErrorHandler() {
  const handleError = useCallback(<T extends (...args: any[]) => any,>(
    handler: T,
    context: string = 'operation'
  ): T => {
    return wrapEventHandler(handler, context) as T;
  }, []);

  const handleAsync = useCallback(async <T,>(
    fn: () => Promise<T>,
    options: { context?: string; fallback?: T } = {}
  ): Promise<T | null> => {
    return withErrorHandling(fn, options);
  }, []);

  return { handleError, handleAsync };
}

/**
 * Utility to report errors to monitoring
 * Extracts this logic so it can be used outside of ErrorBoundary
 */
export async function reportErrorToMonitoring(
  error: Error,
  context: {
    errorId?: string;
    context?: string;
    errorType?: ErrorType;
    additionalInfo?: Record<string, any>;
  } = {}
): Promise<void> {
  const { errorId, context: errorContext, errorType = ErrorType.UNKNOWN, additionalInfo } = context;

  try {
    const errorData = {
      errorId: errorId || `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      message: error.message,
      stack: error.stack,
      context: errorContext || 'manual_report',
      errorType,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      ...additionalInfo
    };

    // ⚡️ PERFORMANCE: DISABLED - Error reporting to backend causing issues when backend not running
    /*
    await fetch('/api/v1/errors/client', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(errorData)
    });
    */
  } catch (reportingError) {
    console.error('Failed to report error to monitoring:', reportingError);
  }
}

/**
 * Check if running in development mode
 */
export function isDevelopment(): boolean {
  return import.meta.env.MODE === 'development' || import.meta.env.NODE_ENV === 'development';
}

/**
 * Development-only error logging
 * Logs detailed error info in development, minimal in production
 */
export function devLogError(error: Error, context: string) {
  if (isDevelopment()) {
    console.group(`🔴 Error in ${context}`);
    console.error('Message:', error.message);
    console.error('Stack:', error.stack);
    console.groupEnd();
  }
}
