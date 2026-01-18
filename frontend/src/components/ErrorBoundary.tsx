// frontend/src/components/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';
import logger from '@/utils/logger';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showRetry?: boolean;
  maxRetries?: number;
  customMessage?: string;
  enableErrorReporting?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string;
  retryCount: number;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Generate unique error ID for tracking
    const errorId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    return {
      hasError: true,
      error,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Log error details using structured logging
    logger.error('React Error Boundary caught error', {
      error_name: error.name,
      error_message: error.message,
      error_stack: error.stack,
      component_stack: errorInfo.componentStack,
      error_id: this.state.errorId,
      error_boundary: 'ErrorBoundary',
      url: window.location.href,
      user_agent: navigator.userAgent,
      category: 'react_error',
    });

    // Send error to monitoring service if enabled
    if (this.props.enableErrorReporting !== false) {
      this.reportError(error, errorInfo);
    }

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  private reportError = async (error: Error, errorInfo: ErrorInfo) => {
    try {
      const errorData = {
        errorId: this.state.errorId,
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        userId: this.getUserId(),
        retryCount: this.state.retryCount,
        buildVersion: import.meta.env.VITE_VERSION || 'unknown'
      };

      logger.logApiCall('/api/v1/errors/client', 'POST', {
        error_id: this.state.errorId,
        error_message: error.message,
      });

      // Send error to monitoring service
      await fetch('/api/v1/errors/client', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorData),
      }).catch(err => {
        logger.logApiError('/api/v1/errors/client', 'POST', err, {
          error_id: this.state.errorId,
          fallback: 'error_not_reported'
        });
      });

      logger.info('Error reported to monitoring service', {
        error_id: this.state.errorId,
      });
    } catch (reportingError) {
      logger.error('Failed to report error to monitoring service', {
        error_id: this.state.errorId,
        reporting_error: reportingError,
      });
    }
  };

  private getUserId = (): string | null => {
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr);
        return user.id;
      }
    } catch (error) {
      logger.error('Failed to get user ID for error reporting', {
        error: error,
        error_id: this.state.errorId,
      });
    }
    return null;
  };

  private handleRetry = () => {
    const maxRetries = this.props.maxRetries || 3;
    if (this.state.retryCount < maxRetries) {
      logger.info('User retrying after error', {
        error_id: this.state.errorId,
        retry_count: this.state.retryCount + 1,
        max_retries: maxRetries,
        action: 'retry',
      });

      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1
      }));
    } else {
      logger.warn('Maximum retry attempts reached', {
        error_id: this.state.errorId,
        retry_count: this.state.retryCount,
        max_retries: maxRetries,
      });
    }
  };

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    });
  };

  private handleReload = () => {
    window.location.reload();
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      const maxRetries = this.props.maxRetries || 3;
      const canRetry = this.props.showRetry !== false && this.state.retryCount < maxRetries;

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
          <div className="max-w-md w-full space-y-8">
            <div className="text-center">
              {/* Error Icon */}
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>

              <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Oops! Something went wrong
              </h2>

              <p className="mt-2 text-center text-sm text-gray-600">
                {this.props.customMessage ||
                 "We're sorry for the inconvenience. Our team has been notified and is working on a fix."}
              </p>

              {this.state.errorId && (
                <p className="mt-1 text-center text-xs text-gray-500">
                  Error ID: {this.state.errorId}
                </p>
              )}

              {/* Error Details in Development */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-4 text-left">
                  <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                    View Error Details (Development Only)
                  </summary>
                  <div className="mt-2 p-3 bg-gray-100 rounded-md">
                    <div className="mb-2">
                      <strong className="text-xs text-gray-600">Error Message:</strong>
                      <p className="text-xs font-mono text-red-600 mt-1">
                        {this.state.error.message}
                      </p>
                    </div>

                    <div className="mb-2">
                      <strong className="text-xs text-gray-600">Stack Trace:</strong>
                      <pre className="text-xs font-mono text-gray-700 mt-1 overflow-auto max-h-32">
                        {this.state.error.stack}
                      </pre>
                    </div>

                    {this.state.errorInfo && (
                      <div>
                        <strong className="text-xs text-gray-600">Component Stack:</strong>
                        <pre className="text-xs font-mono text-gray-700 mt-1 overflow-auto max-h-32">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </div>
                    )}

                    <div className="mt-2 text-xs text-gray-500">
                      <strong>Retry Count:</strong> {this.state.retryCount}/{maxRetries}
                    </div>
                  </div>
                </details>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col space-y-3">
              {canRetry && (
                <button
                  onClick={this.handleRetry}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out"
                >
                  Try Again ({maxRetries - this.state.retryCount} attempts left)
                </button>
              )}

              <div className="flex space-x-3">
                <button
                  onClick={this.handleReload}
                  className="flex-1 flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out"
                >
                  Reload Page
                </button>

                <button
                  onClick={this.handleGoHome}
                  className="flex-1 flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out"
                >
                  Go Home
                </button>
              </div>
            </div>

            {/* Retry Limit Message */}
            {this.state.retryCount >= maxRetries && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-sm text-yellow-800">
                  <strong>Maximum retry attempts reached.</strong> Please reload the page or contact support if the problem persists.
                </p>
              </div>
            )}

            {/* Support Information */}
            <div className="mt-6 text-center">
              <p className="text-xs text-gray-500">
                If this problem continues, please contact our support team with the Error ID above.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
