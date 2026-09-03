/**
 * Error Boundary Coverage Test
 *
 * This file demonstrates and tests what the ErrorBoundary catches and what it doesn't.
 * Use this for development and testing to ensure error handling is comprehensive.
 *
 * RUN THIS FILE IN DEVELOPMENT TO TEST:
 * 1. Start the dev server
 * 2. Navigate to /test-error-boundary (add a route in App.tsx for testing)
 * 3. Click each button to test different error scenarios
 */

import React, { useState, useEffect } from 'react';
import ErrorBoundary from '@/components/ErrorBoundary';
import { withErrorHandling, wrapEventHandler } from '@/utils/errorHandlingCoverage';

/**
 * Component that throws an error during render
 * THIS WILL BE CAUGHT BY ERROR BOUNDARY ✅
 */
function RenderErrorComponent() {
  throw new Error('Render error - This SHOULD be caught by ErrorBoundary');
  return <div>This will never render</div>;
}

/**
 * Component that throws an error in useEffect
 * THIS WILL BE CAUGHT BY ERROR BOUNDARY ✅
 */
function EffectErrorComponent() {
  useEffect(() => {
    throw new Error('Effect error - This SHOULD be caught by ErrorBoundary');
  }, []);

  return <div>This will trigger an error in useEffect</div>;
}

/**
 * Component with a button that throws error in event handler
 * THIS WILL NOT BE CAUGHT BY ERROR BOUNDARY ❌
 * (Needs event handler error wrapping)
 */
function EventHandlerErrorComponent() {
  const badEventHandler = () => {
    throw new Error('Event handler error - This WILL NOT be caught by ErrorBoundary');
  };

  return (
    <div className="p-4 mb-4 border rounded">
      <h3 className="text-lg font-bold mb-2">Event Handler Error (NOT Caught ❌)</h3>
      <p className="mb-2">Clicking this button throws an error in onClick handler</p>
      <button
        onClick={badEventHandler}
        className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
      >
        Throw Event Handler Error
      </button>
    </div>
  );
}

/**
 * Component with WRAPPED event handler that throws error
 * THIS ERROR WILL BE CAUGHT AND LOGGED ✅
 */
function WrappedEventHandlerComponent() {
  const safeEventHandler = wrapEventHandler(() => {
    throw new Error('Wrapped event handler error - This WILL be caught and logged');
  }, 'test button click');

  return (
    <div className="p-4 mb-4 border rounded">
      <h3 className="text-lg font-bold mb-2">Wrapped Event Handler (Caught ✅)</h3>
      <p className="mb-2">Clicking this button throws an error in WRAPPED onClick handler</p>
      <button
        onClick={safeEventHandler}
        className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
      >
        Throw Wrapped Event Handler Error
      </button>
    </div>
  );
}

/**
 * Component with async error in useEffect
 * THIS WILL NOT BE CAUGHT BY ERROR BOUNDARY ❌
 * (Needs async error handling)
 */
function AsyncErrorComponent() {
  useEffect(() => {
    const timer = setTimeout(() => {
      throw new Error('Async error in setTimeout - This WILL NOT be caught by ErrorBoundary');
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="p-4 mb-4 border rounded">
      <h3 className="text-lg font-bold mb-2">Async Error (NOT Caught ❌)</h3>
      <p>Throws an error after 1 second in setTimeout (check console)</p>
    </div>
  );
}

/**
 * Component with HANDLED async error in useEffect
 * THIS ERROR WILL BE CAUGHT AND LOGGED ✅
 */
function HandledAsyncErrorComponent() {
  useEffect(() => {
    withErrorHandling(
      async () => {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        throw new Error('Handled async error - This WILL be caught and logged');
      },
      {
        context: 'Handled async operation',
        showError: true
      }
    );
  }, []);

  return (
    <div className="p-4 mb-4 border rounded">
      <h3 className="text-lg font-bold mb-2">Handled Async Error (Caught ✅)</h3>
      <p>Throws an error after 1 second but it's handled (check console)</p>
    </div>
  );
}

/**
 * Component that simulates network error
 * THIS WILL NOT BE CAUGHT BY ERROR BOUNDARY ❌
 * (Unless promise is rejected and unhandled)
 */
function NetworkErrorComponent() {
  const [error, setError] = useState<string | null>(null);

  const fetchWithError = async () => {
    try {
      // Simulate network error
      await fetch('http://localhost:9999/this-does-not-exist');
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      // This is caught by try/catch, so ErrorBoundary won't see it
    }
  };

  return (
    <div className="p-4 mb-4 border rounded">
      <h3 className="text-lg font-bold mb-2">Network Error (Handled Locally ✅)</h3>
      <p className="mb-2">Network errors are typically handled in try/catch blocks</p>
      <button
        onClick={fetchWithError}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Simulate Network Error
      </button>
      {error && <p className="mt-2 text-red-600">Error: {error}</p>}
    </div>
  );
}

/**
 * Component that throws an error in a promise chain without catch
 * THIS WILL BE CAUGHT BY GLOBAL HANDLER (unhandledrejection) ⚠️
 */
function UnhandledPromiseComponent() {
  const triggerUnhandledRejection = () => {
    // This promise rejects but has no .catch()
    Promise.reject(new Error('Unhandled promise rejection - Caught by global handler'));
  };

  return (
    <div className="p-4 mb-4 border rounded">
      <h3 className="text-lg font-bold mb-2">Unhandled Promise Rejection (Caught by Global Handler ⚠️)</h3>
      <p className="mb-2">Triggers unhandled rejection - check console for global handler logs</p>
      <button
        onClick={triggerUnhandledRejection}
        className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
      >
        Trigger Unhandled Promise Rejection
      </button>
    </div>
  );
}

/**
 * Main test component
 */
export default function ErrorBoundaryTest() {
  const [selectedTest, setSelectedTest] = useState<string | null>(null);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Error Boundary Coverage Test</h1>

      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded">
        <h2 className="text-xl font-bold mb-2">What ErrorBoundary Catches ✅</h2>
        <ul className="list-disc list-inside space-y-1">
          <li>Render method errors</li>
          <li>Lifecycle method errors (useEffect, etc.)</li>
          <li>Component tree reconciliation errors</li>
          <li>Lazy loading errors (Suspense failures)</li>
        </ul>

        <h2 className="text-xl font-bold mt-4 mb-2">What ErrorBoundary Does NOT Catch ❌</h2>
        <ul className="list-disc list-inside space-y-1">
          <li>Event handler errors (onClick, onChange, etc.)</li>
          <li>Async code (setTimeout, setInterval, promises without await)</li>
          <li>Network errors (fetch, axios) - unless thrown in render</li>
          <li>Unhandled promise rejections (caught by global handler)</li>
        </ul>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <button
          onClick={() => setSelectedTest('render')}
          className="p-4 border rounded hover:bg-gray-50"
        >
          Test Render Error (Caught ✅)
        </button>
        <button
          onClick={() => setSelectedTest('effect')}
          className="p-4 border rounded hover:bg-gray-50"
        >
          Test Effect Error (Caught ✅)
        </button>
        <button
          onClick={() => setSelectedTest('event')}
          className="p-4 border rounded hover:bg-gray-50"
        >
          Test Event Handler Error (NOT Caught ❌)
        </button>
        <button
          onClick={() => setSelectedTest('wrapped')}
          className="p-4 border rounded hover:bg-gray-50"
        >
          Test Wrapped Event Handler (Caught ✅)
        </button>
        <button
          onClick={() => setSelectedTest('async')}
          className="p-4 border rounded hover:bg-gray-50"
        >
          Test Async Error (NOT Caught ❌)
        </button>
        <button
          onClick={() => setSelectedTest('handled-async')}
          className="p-4 border rounded hover:bg-gray-50"
        >
          Test Handled Async Error (Caught ✅)
        </button>
        <button
          onClick={() => setSelectedTest('network')}
          className="p-4 border rounded hover:bg-gray-50"
        >
          Test Network Error (Handled Locally ✅)
        </button>
        <button
          onClick={() => setSelectedTest('promise')}
          className="p-4 border rounded hover:bg-gray-50"
        >
          Test Unhandled Promise (Global Handler ⚠️)
        </button>
      </div>

      <ErrorBoundary
        enableErrorReporting={true}
        showRetry={true}
        customMessage="Error boundary caught this error!"
      >
        <div className="border-t pt-4">
          {selectedTest === 'render' && <RenderErrorComponent />}
          {selectedTest === 'effect' && <EffectErrorComponent />}
          {selectedTest === 'event' && <EventHandlerErrorComponent />}
          {selectedTest === 'wrapped' && <WrappedEventHandlerComponent />}
          {selectedTest === 'async' && <AsyncErrorComponent />}
          {selectedTest === 'handled-async' && <HandledAsyncErrorComponent />}
          {selectedTest === 'network' && <NetworkErrorComponent />}
          {selectedTest === 'promise' && <UnhandledPromiseComponent />}

          {!selectedTest && (
            <div className="text-center text-gray-500">
              Select a test above to see error handling in action
            </div>
          )}
        </div>
      </ErrorBoundary>

      <div className="mt-6 p-4 bg-gray-50 border rounded">
        <h3 className="text-lg font-bold mb-2">Test Results Guide:</h3>
        <ul className="space-y-2 text-sm">
          <li><strong>✅ Caught:</strong> ErrorBoundary shows error UI, logs to console, reports to API</li>
          <li><strong>❌ NOT Caught:</strong> App may crash or show white screen, check console</li>
          <li><strong>⚠️ Global Handler:</strong> Caught by window.addEventListener('unhandledrejection')</li>
        </ul>
      </div>
    </div>
  );
}
