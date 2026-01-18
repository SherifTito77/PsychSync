/**
 * Error Context and Notification System
 * Provides global error handling with user-friendly notifications
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { XCircle, AlertTriangle, Info, CheckCircle, X } from 'lucide-react';

export type ErrorSeverity = 'error' | 'warning' | 'info' | 'success';

export interface ErrorNotification {
  id: string;
  message: string;
  severity: ErrorSeverity;
  actionable?: boolean;
  retryable?: boolean;
  onRetry?: () => void;
  duration?: number; // Auto-dismiss after ms (0 = no auto-dismiss)
}

interface ErrorContextType {
  showError: (message: string, options?: ErrorNotificationOptions) => void;
  showWarning: (message: string, options?: ErrorNotificationOptions) => void;
  showInfo: (message: string, options?: ErrorNotificationOptions) => void;
  showSuccess: (message: string, options?: ErrorNotificationOptions) => void;
  clearError: (id: string) => void;
  clearAllErrors: () => void;
}

interface ErrorNotificationOptions {
  actionable?: boolean;
  retryable?: boolean;
  onRetry?: () => void;
  duration?: number;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

export const useError = () => {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
};

export const ErrorProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<ErrorNotification[]>([]);

  const addNotification = useCallback((
    message: string,
    severity: ErrorSeverity,
    options?: ErrorNotificationOptions
  ) => {
    const id = `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const notification: ErrorNotification = {
      id,
      message,
      severity,
      actionable: options?.actionable ?? false,
      retryable: options?.retryable ?? false,
      onRetry: options?.onRetry,
      duration: options?.duration ?? (severity === 'success' ? 3000 : severity === 'info' ? 5000 : 0),
    };

    setNotifications((prev) => [...prev, notification]);

    // Auto-dismiss if duration is set
    if (notification.duration && notification.duration > 0) {
      setTimeout(() => {
        setNotifications((prev) => prev.filter((n) => n.id !== id));
      }, notification.duration);
    }

    return id;
  }, []);

  const showError = useCallback((message: string, options?: ErrorNotificationOptions) => {
    return addNotification(message, 'error', options);
  }, [addNotification]);

  const showWarning = useCallback((message: string, options?: ErrorNotificationOptions) => {
    return addNotification(message, 'warning', options);
  }, [addNotification]);

  const showInfo = useCallback((message: string, options?: ErrorNotificationOptions) => {
    return addNotification(message, 'info', options);
  }, [addNotification]);

  const showSuccess = useCallback((message: string, options?: ErrorNotificationOptions) => {
    return addNotification(message, 'success', options);
  }, [addNotification]);

  const clearError = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearAllErrors = useCallback(() => {
    setNotifications([]);
  }, []);

  return (
    <ErrorContext.Provider
      value={{
        showError,
        showWarning,
        showInfo,
        showSuccess,
        clearError,
        clearAllErrors,
      }}
    >
      {children}
      <ErrorToastContainer notifications={notifications} onDismiss={clearError} />
    </ErrorContext.Provider>
  );
};

interface ErrorToastContainerProps {
  notifications: ErrorNotification[];
  onDismiss: (id: string) => void;
}

const ErrorToastContainer: React.FC<ErrorToastContainerProps> = ({ notifications, onDismiss }) => {
  if (notifications.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-md w-full">
      {notifications.map((notification) => (
        <ErrorToast
          key={notification.id}
          notification={notification}
          onDismiss={() => onDismiss(notification.id)}
        />
      ))}
    </div>
  );
};

interface ErrorToastProps {
  notification: ErrorNotification;
  onDismiss: () => void;
}

const ErrorToast: React.FC<ErrorToastProps> = ({ notification, onDismiss }) => {
  const getIcon = () => {
    switch (notification.severity) {
      case 'error':
        return <XCircle className="h-5 w-5" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5" />;
      case 'info':
        return <Info className="h-5 w-5" />;
      case 'success':
        return <CheckCircle className="h-5 w-5" />;
    }
  };

  const getStyles = () => {
    switch (notification.severity) {
      case 'error':
        return 'bg-red-50 border-red-200 text-red-900';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-900';
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-900';
      case 'success':
        return 'bg-green-50 border-green-200 text-green-900';
    }
  };

  const getIconColor = () => {
    switch (notification.severity) {
      case 'error':
        return 'text-red-600';
      case 'warning':
        return 'text-yellow-600';
      case 'info':
        return 'text-blue-600';
      case 'success':
        return 'text-green-600';
    }
  };

  return (
    <div
      className={`${getStyles()} border-2 rounded-lg p-4 shadow-lg flex items-start gap-3 animate-slide-in`}
      role="alert"
      aria-live="polite"
    >
      <div className={`${getIconColor()} flex-shrink-0 mt-0.5`}>
        {getIcon()}
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{notification.message}</p>

        {notification.retryable && notification.onRetry && (
          <button
            onClick={() => {
              notification.onRetry?.();
              onDismiss();
            }}
            className="mt-2 text-sm font-medium underline hover:no-underline focus:outline-none focus:ring-2 focus:ring-offset-2"
          >
            Try Again
          </button>
        )}
      </div>

      <button
        onClick={onDismiss}
        className="flex-shrink-0 inline-flex rounded-md p-1.5 hover:bg-black hover:bg-opacity-10 focus:outline-none focus:ring-2 focus:ring-offset-2"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
};

/**
 * Convenience hook for showing API errors
 */
export const useApiError = () => {
  const { showError } = useError();

  return (error: any, context?: string) => {
    const { getErrorMessage } = require('../utils/errorHandler');

    const message = getErrorMessage(error, `${context} failed. Please try again.`);
    const retryable = require('../utils/errorHandler').isRetryable(error);

    showError(message, {
      retryable,
      onRetry: retryable ? () => {
        // Caller can provide retry logic
        console.log('Retry action - implement in component');
      } : undefined,
    });
  };
};
