/**
 * PsychSync Sentry Configuration for React Frontend
 * Comprehensive error tracking and performance monitoring
 */

import React from 'react';
import * as Sentry from "@sentry/react";
import { BrowserTracing } from "@sentry/react";
import { ExtraErrorData, CaptureConsole } from "@sentry/integrations";

// Configuration from environment
const SENTRY_DSN = process.env.REACT_APP_SENTRY_DSN;
const ENVIRONMENT = process.env.REACT_APP_ENVIRONMENT || "development";
const RELEASE = process.env.REACT_APP_VERSION || "unknown";
const APP_VERSION = process.env.REACT_APP_BUILD_NUMBER || "1";

// Sampling configuration
const TRACES_SAMPLE_RATE = parseFloat(process.env.REACT_APP_SENTRY_TRACES_SAMPLE_RATE || "0.1"); // 10% for production
const SESSION_REPLAY_SAMPLE_RATE = parseFloat(process.env.REACT_APP_SENTRY_SESSION_REPLAY_SAMPLE_RATE || "0.1");

// Feature flags
const ENABLE_PERFORMANCE_MONITORING = process.env.REACT_APP_SENTRY_ENABLE_PERFORMANCE !== "false";
const ENABLE_ERROR_MONITORING = process.env.REACT_APP_SENTRY_ENABLE_ERRORS !== "false";
const ENABLE_SESSION_REPLAY = process.env.REACT_APP_SENTRY_ENABLE_SESSION_REPLAY === "true";

// User agent and device info
const getUserAgentInfo = () => {
  const userAgent = navigator.userAgent;
  return {
    userAgent,
    platform: navigator.platform,
    language: navigator.language,
    cookieEnabled: navigator.cookieEnabled,
    onLine: navigator.onLine,
    screen: {
      width: window.screen.width,
      height: window.screen.height,
      colorDepth: window.screen.colorDepth,
      pixelDepth: window.screen.pixelDepth,
    },
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight,
    },
  };
};

// Initialize Sentry
export const initSentry = () => {
  if (!SENTRY_DSN) {
    console.warn("SENTRY_DSN not configured - Sentry disabled");
    return;
  }

  if (ENVIRONMENT === "development" && process.env.REACT_APP_FORCE_SENTRY_DEV !== "true") {
    console.info("Sentry disabled in development environment");
    return;
  }

  // Integrations
  const integrations = [
    // Performance monitoring
    new BrowserTracing({
      // Set custom transaction name
      routingInstrumentation: Sentry.reactRouterV6Instrumentation(
        React.useEffect,
        useLocation,
        useNavigationType,
        createRoutesFromChildren,
        matchRoutes
      ),
    }),

    // Additional error data
    new ExtraErrorData({
      // Capture up to 10 extra error properties
      depth: 10,
    }),

    // Capture console errors
    new CaptureConsole({
      levels: ["error"],
    }),
  ];

  // Add session replay if enabled
  if (ENABLE_SESSION_REPLAY) {
    import("@sentry/replay").then(({ Replay }) => {
      integrations.push(
        new Replay({
          sessionSampleRate: SESSION_REPLAY_SAMPLE_RATE,
          errorSampleRate: 1.0, // Always record session on error
          maskAllText: true,
          maskAllInputs: true,
          blockAllMedia: true,
        })
      );
    });
  }

  Sentry.init({
    dsn: SENTRY_DSN,

    // Environment and release
    environment: ENVIRONMENT,
    release: `${RELEASE}@${APP_VERSION}`,

    // Sampling
    tracesSampleRate: ENABLE_PERFORMANCE_MONITORING ? TRACES_SAMPLE_RATE : 0,

    // Integrations
    integrations,

    // Error filtering
    ignoreErrors: [
      // Network errors that are expected
      "Network Error",
      "NetworkError",
      "AbortError",

      // Browser extensions
      "Non-Error promise rejection captured",
      "ResizeObserver loop limit exceeded",
      "ResizeObserver loop completed with undelivered notifications",

      // Third-party script errors
      "Script error",
      "Non-Error exception captured",
    ],

    // URL filtering
    denyUrls: [
      // Chrome extensions
      /extensions\//i,
      /^chrome:\/\//i,
      /^chrome-extension:\/\//i,

      // Third-party analytics
      /google-analytics\.com/i,
      /googletagmanager\.com/i,
      /facebook\.net/i,
      /connect\.facebook\.net/i,

      // Development tools
      /localhost/i,
      /127\.0\.0\.1/i,
    ],

    // Before send for filtering sensitive data
    beforeSend: (event, hint) => {
      // Filter sensitive data from URLs
      if (event.request?.url) {
        event.request.url = event.request.url.replace(/([?&])(password|token|secret|key)=[^&]*/i, "$1$2=[FILTERED]");
      }

      // Filter sensitive data from breadcrumbs
      if (event.breadcrumbs) {
        event.breadcrumbs = event.breadcrumbs.map(crumb => {
          if (crumb.data?.url) {
            crumb.data.url = crumb.data.url.replace(/([?&])(password|token|secret|key)=[^&]*/i, "$1$2=[FILTERED]");
          }
          return crumb;
        });
      }

      // Add custom context
      event.contexts = {
        ...event.contexts,
        app: {
          name: "psychsync-frontend",
          version: APP_VERSION,
          environment: ENVIRONMENT,
        },
        device: getUserAgentInfo(),
      };

      // Add custom tags
      event.tags = {
        ...event.tags,
        service: "psychsync-frontend",
        version: RELEASE,
        environment: ENVIRONMENT,
      };

      return event;
    },

    // Before breadcrumb for filtering
    beforeBreadcrumb: (breadcrumb, hint) => {
      // Filter sensitive URLs
      if (breadcrumb.data?.url) {
        breadcrumb.data.url = breadcrumb.data.url.replace(/([?&])(password|token|secret|key)=[^&]*/i, "$1$2=[FILTERED]");
      }

      // Filter out analytics breadcrumbs
      if (breadcrumb.category === "xhr" && breadcrumb.data?.url) {
        const url = breadcrumb.data.url;
        if (url.includes("google-analytics") || url.includes("facebook")) {
          return null;
        }
      }

      return breadcrumb;
    },

    // Debug in development
    debug: ENVIRONMENT === "development",

    // Max breadcrumbs and depth
    maxBreadcrumbs: 100,

    // Performance configuration
    normalizeDepth: 4,

    // Never send PII
    sendDefaultPii: false,
  });

  console.info(`Sentry initialized - Environment: ${ENVIRONMENT}, Release: ${RELEASE}`);
};

// User tracking
export const setSentryUser = (userData: any) => {
  if (!ENABLE_ERROR_MONITORING) return;

  // Filter sensitive user data
  const filteredUser = {
    id: userData?.id,
    email: userData?.email,
    username: userData?.username,
    organizationId: userData?.organizationId,
    role: userData?.role,
  };

  // Remove undefined values
  Object.keys(filteredUser).forEach(key => {
    if (filteredUser[key] === undefined) {
      delete filteredUser[key];
    }
  });

  Sentry.setUser(filteredUser);
};

// Clear user context
export const clearSentryUser = () => {
  if (!ENABLE_ERROR_MONITORING) return;
  Sentry.setUser(null);
};

// Set context
export const setSentryContext = (key: string, value: any) => {
  if (!ENABLE_ERROR_MONITORING) return;
  Sentry.setContext(key, value);
};

// Set tags
export const setSentryTag = (key: string, value: string) => {
  if (!ENABLE_ERROR_MONITORING) return;
  Sentry.setTag(key, value);
};

// Capture exception
export const captureSentryException = (
  error: Error,
  level: Sentry.SeverityLevel = "error",
  extra?: Record<string, any>,
  tags?: Record<string, string>
) => {
  if (!ENABLE_ERROR_MONITORING) return;

  Sentry.withScope((scope) => {
    scope.setLevel(level);

    if (extra) {
      Object.keys(extra).forEach(key => {
        scope.setExtra(key, extra[key]);
      });
    }

    if (tags) {
      Object.keys(tags).forEach(key => {
        scope.setTag(key, tags[key]);
      });
    }

    Sentry.captureException(error);
  });
};

// Capture message
export const captureSentryMessage = (
  message: string,
  level: Sentry.SeverityLevel = "info",
  extra?: Record<string, any>,
  tags?: Record<string, string>
) => {
  if (!ENABLE_ERROR_MONITORING) return;

  Sentry.withScope((scope) => {
    scope.setLevel(level);

    if (extra) {
      Object.keys(extra).forEach(key => {
        scope.setExtra(key, extra[key]);
      });
    }

    if (tags) {
      Object.keys(tags).forEach(key => {
        scope.setTag(key, tags[key]);
      });
    }

    Sentry.captureMessage(message, level);
  });
};

// Performance monitoring
export const startSentryTransaction = (name: string, op: string = "navigation") => {
  if (!ENABLE_PERFORMANCE_MONITORING) return null;
  return Sentry.startTransaction({
    name,
    op,
  });
};

// Custom hook for performance monitoring
export const useSentryPerformance = (name: string) => {
  const [transaction, setTransaction] = useState<Sentry.Transaction | null>(null);

  useEffect(() => {
    const tx = startSentryTransaction(name);
    setTransaction(tx);

    return () => {
      if (tx) {
        tx.finish();
      }
    };
  }, [name]);

  return transaction;
};

// Error boundary for React
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const PsychSyncErrorBoundary: React.FC<ErrorBoundaryProps> = ({ children, fallback }) => {
  return (
    <Sentry.ErrorBoundary
      fallback={fallback || (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>We've been notified about this issue and will fix it soon.</p>
          <button onClick={() => window.location.reload()}>
            Refresh Page
          </button>
        </div>
      )}
      beforeCapture={(scope, error) => {
        scope.setTag("error_boundary", true);
        scope.setContext("error_info", {
          message: error.message,
          name: error.name,
        });
      }}
    >
      {children}
    </Sentry.ErrorBoundary>
  );
};

// Health check
export const checkSentryHealth = () => {
  return {
    configured: !!SENTRY_DSN,
    environment: ENVIRONMENT,
    release: RELEASE,
    version: APP_VERSION,
    performanceMonitoring: ENABLE_PERFORMANCE_MONITORING,
    errorMonitoring: ENABLE_ERROR_MONITORING,
    sessionReplay: ENABLE_SESSION_REPLAY,
    tracesSampleRate: TRACES_SAMPLE_RATE,
    sessionReplaySampleRate: SESSION_REPLAY_SAMPLE_RATE,
  };
};

// Stripe specific error handling
export const captureStripeError = (error: any, context: string) => {
  const tags = {
    provider: "stripe",
    context,
  };

  const extra = {
    stripeErrorType: error.type,
    stripeErrorCode: error.code,
    stripeDeclineCode: error.decline_code,
    stripeChargeId: error.charge_id,
    stripePaymentIntentId: error.payment_intent_id,
  };

  captureSentryException(error, "error", extra, tags);
};

// API error handling
export const captureApiError = (error: any, endpoint: string, method: string) => {
  const tags = {
    apiEndpoint: endpoint,
    httpMethod: method,
    statusCode: error.response?.status?.toString(),
  };

  const extra = {
    responseData: error.response?.data,
    requestUrl: error.config?.url,
    requestMethod: error.config?.method,
  };

  captureSentryException(error, "error", extra, tags);
};

// Export Sentry for advanced usage
export { Sentry };