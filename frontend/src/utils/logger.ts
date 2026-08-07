/**
 * Structured Logging Utility for PsychSync Frontend
 *
 * Provides structured logging with context for better debugging and monitoring
 * Replaces console.log/warn/error with production-ready logging
 */

interface LogContext {
  [key: string]: any;
}

interface LogEntry {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  context?: LogContext;
  user_id?: string;
  session_id?: string;
  correlation_id?: string;
  stack?: string;
}

class Logger {
  private sessionId: string;
  private userId: string | null = null;
  private isProduction = import.meta.env.PROD;

  constructor() {
    // Generate unique session ID
    this.sessionId = this.generateSessionId();

    // Get user ID from localStorage if available
    try {
      const userData = localStorage.getItem('user');
      if (userData) {
        const user = JSON.parse(userData);
        this.userId = user.id || null;
      }
    } catch (e) {
      // User not logged in or invalid data
    }
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }

  private generateCorrelationId(): string {
    return `corr_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }

  private getUserId(): string | null {
    return this.userId;
  }

  private getCorrelationId(): string {
    // Try to get from session storage first (for request tracing)
    const stored = sessionStorage.getItem('correlation_id');
    if (stored) {
      return stored;
    }

    // Generate new correlation ID
    const correlationId = this.generateCorrelationId();
    sessionStorage.setItem('correlation_id', correlationId);
    return correlationId;
  }

  private log(level: 'info' | 'warn' | 'error' | 'debug', message: string, context?: LogContext) {
    const logEntry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      user_id: this.getUserId(),
      session_id: this.sessionId,
      correlation_id: this.getCorrelationId(),
      context,
    };

    // Include stack trace for errors
    if (level === 'error' && context?.error instanceof Error) {
      logEntry.stack = context.error.stack;
      logEntry.context = {
        ...context,
        error_name: context.error.name,
        error_message: context.error.message,
      };
    }

    // In production, send to logging endpoint
    if (this.isProduction) {
      this.sendToServer(logEntry);
    } else {
      // In development, log to console with structured format
      this.logToConsole(logEntry);
    }
  }

  private logToConsole(logEntry: LogEntry) {
    const consoleMethod = logEntry.level === 'debug' ? 'log' : logEntry.level;
    const emoji = {
      info: 'ℹ️',
      warn: '⚠️',
      error: '❌',
      debug: '🔍',
    }[logEntry.level];

    // Format log message for console
    const formattedMessage = `${emoji} [${logEntry.level.toUpperCase()}] ${logEntry.message}`;

    // Log to appropriate console method
    (console as any)[consoleMethod](
      formattedMessage,
      {
        ...logEntry.context,
        _meta: {
          user_id: logEntry.user_id,
          session_id: logEntry.session_id,
          correlation_id: logEntry.correlation_id,
        },
      }
    );

    // Include stack trace for errors
    if (logEntry.stack) {
      console.error('Stack trace:', logEntry.stack);
    }
  }

  private async sendToServer(logEntry: LogEntry) {
    // ⚡️ PERFORMANCE: DISABLED - Sending logs to server causing page freeze when backend not running
    // Only log to console in development
    /*
    try {
      await fetch('/api/v1/logs/frontend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(logEntry),
      });
    } catch (e) {
      // If logging fails, fall back to console
      console.warn('Failed to send log to server:', e);
      this.logToConsole(logEntry);
    }
    */
  }

  // Public API
  info(message: string, context?: LogContext) {
    this.log('info', message, context);
  }

  warn(message: string, context?: LogContext) {
    this.log('warn', message, context);
  }

  error(message: string, context?: LogContext) {
    this.log('error', message, context);

    // In production, also send to error tracking service (e.g., Sentry)
    if (this.isProduction && (window as any).Sentry) {
      (window as any).Sentry.captureException(new Error(message), {
        extra: context,
        user: this.userId ? { id: this.userId } : undefined,
        tags: {
          session_id: this.sessionId,
          correlation_id: this.getCorrelationId(),
        },
      });
    }
  }

  debug(message: string, context?: LogContext) {
    if (!this.isProduction) {
      this.log('debug', message, context);
    }
  }

  // Security-specific logging
  logAuthEvent(event: string, details: LogContext) {
    this.info(`Auth: ${event}`, {
      category: 'authentication',
      ...details,
    });
  }

  logAuthFailure(event: string, error: any, details: LogContext) {
    this.error(`Auth FAILED: ${event}`, {
      category: 'authentication',
      error: error,
      ...details,
    });
  }

  logSecurityEvent(event: string, severity: 'low' | 'medium' | 'high', details: LogContext) {
    const level = severity === 'high' ? 'error' : severity === 'medium' ? 'warn' : 'info';
    this[level](`Security: ${event}`, {
      category: 'security',
      severity,
      ...details,
    });
  }

  logApiCall(endpoint: string, method: string, details?: LogContext) {
    this.debug(`API: ${method} ${endpoint}`, {
      category: 'api_call',
      endpoint,
      method,
      ...details,
    });
  }

  logApiError(endpoint: string, method: string, error: any, details?: LogContext) {
    this.error(`API FAILED: ${method} ${endpoint}`, {
      category: 'api_error',
      endpoint,
      method,
      error: error,
      status_code: error?.response?.status,
      ...details,
    });
  }
}

// Singleton instance
const logger = new Logger();

export default logger;
