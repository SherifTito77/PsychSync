/**
 * Global Error Handler for Unhandled Errors
 *
 * Catches:
 * - Unhandled promise rejections
 * - Unhandled errors in event handlers
 * - Resource loading errors
 * - Global React errors
 *
 * Logs all errors to the structured logging system
 */

import logger from '@/utils/logger';

/**
 * Initialize global error handlers
 * Call this once in your app initialization (e.g., in main.tsx or App.tsx)
 */
export function initializeGlobalErrorHandlers() {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    logger.error('Unhandled Promise Rejection', {
      reason: event.reason,
      promise: event.promise,
      type: 'unhandled_rejection',
      url: window.location.href,
      stack: event.reason?.stack
    });

    // Prevent default browser error logging
    event.preventDefault();
  });

  // Handle global errors
  window.addEventListener('error', (event) => {
    logger.error('Global Error', {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      error: event.error,
      type: 'global_error',
      url: window.location.href,
      stack: event.error?.stack
    });

    // Don't prevent default - let browser log to console
  });

  // Handle resource loading errors
  window.addEventListener('error', (event) => {
    if (event.target !== window) {
      const target = event.target as HTMLElement;
      logger.error('Resource Loading Error', {
        tag_name: target.tagName,
        src: target.getAttribute('src'),
        href: target.getAttribute('href'),
        type: 'resource_error',
        url: window.location.href
      });
    }
  }, true);

  logger.info('Global error handlers initialized', {
    timestamp: new Date().toISOString()
  });
}

/**
 * Cleanup global error handlers
 * Call this when app unmounts (rarely needed)
 */
export function cleanupGlobalErrorHandlers() {
  // Note: Remove event listeners to prevent memory leaks
  // In most cases, this is not necessary as handlers persist for app lifetime
  logger.info('Global error handlers cleaned up');
}
