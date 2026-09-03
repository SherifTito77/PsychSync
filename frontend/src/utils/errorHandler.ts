/**
 * Global Error Handler Utility
 * Provides user-friendly error messages and handling strategies
 */

export interface UserFriendlyError {
  userMessage: string;
  technicalMessage?: string;
  actionable: boolean;
  retryable: boolean;
  errorCode?: string;
}

export interface ErrorOptions {
  actionable?: boolean;
  retryable?: boolean;
  onRetry?: () => void;
  context?: Record<string, any>;
}

/**
 * Parse error and return user-friendly information
 */
export const handleError = (error: any, context: string = 'Operation'): UserFriendlyError => {
  // Network errors (no response from server)
  if (!error.response && error.request) {
    return {
      userMessage: 'Unable to connect to the server. Please check your internet connection and try again.',
      technicalMessage: 'Network error - no response received',
      actionable: true,
      retryable: true,
      errorCode: 'NETWORK_ERROR',
    };
  }

  // Request configuration errors
  if (!error.response && !error.request) {
    return {
      userMessage: 'Unable to complete the request. Please refresh the page and try again.',
      technicalMessage: error.message || 'Request configuration error',
      actionable: true,
      retryable: true,
      errorCode: 'REQUEST_ERROR',
    };
  }

  // HTTP status code errors
  const status = error.response?.status;
  const data = error.response?.data;

  switch (status) {
    case 400:
      return {
        userMessage: data?.detail || 'Invalid request. Please check your input and try again.',
        technicalMessage: 'Bad request',
        actionable: true,
        retryable: false,
        errorCode: 'BAD_REQUEST',
      };

    case 401:
      return {
        userMessage: 'Your session has expired. Please log in again.',
        technicalMessage: 'Authentication required',
        actionable: true,
        retryable: false,
        errorCode: 'UNAUTHORIZED',
      };

    case 403:
      return {
        userMessage: "You don't have permission to perform this action. Please contact your administrator if you believe this is an error.",
        technicalMessage: 'Authorization failed',
        actionable: false,
        retryable: false,
        errorCode: 'FORBIDDEN',
      };

    case 404:
      return {
        userMessage: 'The requested resource was not found. It may have been moved or deleted.',
        technicalMessage: 'Resource not found',
        actionable: false,
        retryable: false,
        errorCode: 'NOT_FOUND',
      };

    case 409:
      return {
        userMessage: data?.detail || 'This action conflicts with existing data. Please refresh and try again.',
        technicalMessage: 'Conflict detected',
        actionable: true,
        retryable: true,
        errorCode: 'CONFLICT',
      };

    case 422:
      return {
        userMessage: data?.detail || 'Invalid data provided. Please check your input and try again.',
        technicalMessage: 'Validation error',
        actionable: true,
        retryable: false,
        errorCode: 'VALIDATION_ERROR',
      };

    case 429:
      return {
        userMessage: 'You have made too many requests. Please wait a moment and try again.',
        technicalMessage: 'Rate limit exceeded',
        actionable: true,
        retryable: true,
        errorCode: 'RATE_LIMIT',
      };

    case 500:
      return {
        userMessage: 'Something went wrong on our end. Our team has been notified. Please try again.',
        technicalMessage: data?.detail || 'Internal server error',
        actionable: true,
        retryable: true,
        errorCode: 'SERVER_ERROR',
      };

    case 502:
    case 503:
    case 504:
      return {
        userMessage: 'Service temporarily unavailable. Please wait a moment and try again.',
        technicalMessage: 'Service unavailable',
        actionable: true,
        retryable: true,
        errorCode: 'SERVICE_UNAVAILABLE',
      };

    default:
      return {
        userMessage: data?.detail || data?.user_message || 'An unexpected error occurred. Please try again.',
        technicalMessage: error.message || 'Unknown error',
        actionable: true,
        retryable: true,
        errorCode: 'UNKNOWN_ERROR',
      };
  }
};

/**
 * Extract actionable error message for display
 */
export const getErrorMessage = (error: any, fallback: string = 'An error occurred'): string => {
  const handled = handleError(error);

  // Check for specific backend error message format
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }

  if (error.response?.data?.user_message) {
    return error.response.data.user_message;
  }

  if (error.response?.data?.message) {
    return error.response.data.message;
  }

  return handled.userMessage;
};

/**
 * Determine if error is retryable
 */
export const isRetryable = (error: any): boolean => {
  const handled = handleError(error);
  return handled.retryable;
};

/**
 * Get error code for analytics/monitoring
 */
export const getErrorCode = (error: any): string => {
  const handled = handleError(error);
  return handled.errorCode || 'UNKNOWN';
};

/**
 * Log error with context for monitoring
 */
export const logError = (error: any, context: string, additionalContext?: Record<string, any>) => {
  const errorCode = getErrorCode(error);
  const errorMessage = getErrorMessage(error);

  console.error(`[${errorCode}] ${context}:`, {
    message: errorMessage,
    technical: error.message,
    status: error.response?.status,
    context: additionalContext,
  });

  // In production, send to error tracking service
  if (import.meta.env.PROD && window.onerror) {
    // Example: Send to Sentry, LogRocket, etc.
    // errorTrackingService.captureException(error, { context, ...additionalContext });
  }
};
