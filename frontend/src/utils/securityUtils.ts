// src/utils/securityUtils.ts
// Comprehensive security utility functions for frontend applications

/**
 * Content Security Policy configuration
 */
export const CSP_DIRECTIVES = {
  'default-src': ["'self'"],
  'script-src': [
    "'self'",
    "'unsafe-eval'", // Only if absolutely necessary for React
    "'unsafe-inline'", // Only for development
    'https://apis.google.com',
    'https://www.google-analytics.com',
    'https://meet.jit.si',
    'https://8x8.vc'
  ],
  'style-src': [
    "'self'",
    "'unsafe-inline'", // Required for Tailwind CSS
    'https://fonts.googleapis.com'
  ],
  'font-src': [
    "'self'",
    'https://fonts.gstatic.com',
    'data:'
  ],
  'img-src': [
    "'self'",
    'data:',
    'https:',
    'blob:'
  ],
  'connect-src': [
    "'self'",
    'ws://localhost:5173',
    'wss://localhost:5173',
    'http://localhost:8000',
    'http://localhost:8011',
    'https://api.stripe.com',
    'https://www.google-analytics.com',
    'https://meet.jit.si',
    'wss://meet.jit.si',
    'https://8x8.vc',
    'wss://8x8.vc'
  ],
  'frame-src': ["'self'", 'https://meet.jit.si', 'https://8x8.vc'],
  'media-src': ["'self'", 'https://meet.jit.si', 'https://8x8.vc', 'blob:'],
  'object-src': ["'none'"],
  'base-uri': ["'self'"],
  'form-action': ["'self'"],
  'frame-ancestors': ["'none'"],
  'upgrade-insecure-requests': [],
  'require-trusted-types-for': ["'script'"]
};

/**
 * Generate CSP header string
 */
export function generateCSPHeader(): string {
  const directives = Object.entries(CSP_DIRECTIVES)
    .filter(([directive]) => directive !== 'frame-ancestors') // Remove frame-ancestors for meta tag
    .map(([directive, sources]) => {
      return `${directive} ${sources.join(' ')}`;
    })
    .join('; ');

  return directives;
}

/**
 * Security-related utility functions
 */
export class SecurityUtils {
  /**
   * Sanitize HTML to prevent XSS attacks
   */
  static sanitizeHTML(html: string): string {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
  }

  /**
   * Sanitize and validate URLs
   */
  static sanitizeURL(url: string): string {
    try {
      const parsed = new URL(url, window.location.origin);

      // Allow only same-origin or specific whitelisted domains
      const allowedDomains = [
        'localhost',
        'psychsync.com',
        'api.psychsync.com',
        'cdn.psychsync.com'
      ];

      const isAllowed = allowedDomains.some(domain =>
        parsed.hostname === domain || parsed.hostname.endsWith(`.${domain}`)
      ) || parsed.hostname === window.location.hostname;

      if (!isAllowed) {
        return '#';
      }

      // Remove dangerous protocols
      const allowedProtocols = ['http:', 'https:', 'mailto:', 'tel:'];
      if (!allowedProtocols.includes(parsed.protocol)) {
        return '#';
      }

      return parsed.toString();
    } catch {
      return '#';
    }
  }

  /**
   * Validate input against XSS patterns
   */
  static containsXSS(input: string): boolean {
    const xssPatterns = [
      /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
      /javascript:/gi,
      /on\w+\s*=/gi,
      /<iframe\b[^>]*>/gi,
      /<object\b[^>]*>/gi,
      /<embed\b[^>]*>/gi,
      /<link\b[^>]*>/gi,
      /<meta\b[^>]*>/gi,
      /data:text\/html/gi,
      /vbscript:/gi,
      /<%.*%>/gi
    ];

    return xssPatterns.some(pattern => pattern.test(input));
  }

  /**
   * Deep sanitize object to remove XSS
   */
  static sanitizeObject(obj: any): any {
    if (typeof obj === 'string') {
      return this.sanitizeHTML(obj);
    }

    if (Array.isArray(obj)) {
      return obj.map(item => this.sanitizeObject(item));
    }

    if (obj && typeof obj === 'object') {
      const sanitized: any = {};
      for (const [key, value] of Object.entries(obj)) {
        sanitized[this.sanitizeHTML(key)] = this.sanitizeObject(value);
      }
      return sanitized;
    }

    return obj;
  }

  /**
   * Generate secure random string
   */
  static generateSecureRandom(length: number = 32): string {
    const array = new Uint8Array(length);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Create secure hash of string
   */
  static async hashString(str: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(str);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Check if password meets security requirements
   */
  static validatePasswordStrength(password: string): {
    isValid: boolean;
    errors: string[];
    score: number;
  } {
    const errors: string[] = [];
    let score = 0;

    // Length check
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long');
    } else if (password.length >= 12) {
      score += 2;
    } else {
      score += 1;
    }

    // Complexity checks
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain lowercase letters');
    } else score += 1;

    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain uppercase letters');
    } else score += 1;

    if (!/\d/.test(password)) {
      errors.push('Password must contain numbers');
    } else score += 1;

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      errors.push('Password must contain special characters');
    } else score += 1;

    // Common patterns
    const commonPatterns = [
      /123456/,
      /password/i,
      /qwerty/i,
      /abc123/i,
      /admin/i
    ];

    if (commonPatterns.some(pattern => pattern.test(password))) {
      errors.push('Password contains common patterns');
      score = Math.max(0, score - 2);
    }

    return {
      isValid: errors.length === 0 && password.length >= 8,
      errors,
      score: Math.min(5, score)
    };
  }

  /**
   * Validate email format securely
   */
  static validateEmail(email: string): boolean {
    const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
    return emailRegex.test(email) && email.length <= 254;
  }

  /**
   * Detect suspicious activity patterns
   */
  static detectSuspiciousActivity(userActions: Array<{
    action: string;
    timestamp: number;
    userAgent?: string;
  }>): {
    isSuspicious: boolean;
    reasons: string[];
    confidence: number;
  } {
    const reasons: string[] = [];
    let confidence = 0;

    const now = Date.now();
    const recentActions = userActions.filter(action =>
      now - action.timestamp < 60000 // Last minute
    );

    // High frequency actions
    if (recentActions.length > 100) {
      reasons.push('High frequency of actions detected');
      confidence += 0.4;
    }

    // Rapid form submissions
    const formSubmissions = recentActions.filter(action =>
      action.action === 'form_submit'
    );

    if (formSubmissions.length > 5) {
      reasons.push('Multiple rapid form submissions');
      confidence += 0.3;
    }

    // Failed login attempts
    const failedLogins = userActions.filter(action =>
      action.action === 'failed_login' &&
      now - action.timestamp < 300000 // Last 5 minutes
    );

    if (failedLogins.length > 5) {
      reasons.push('Multiple failed login attempts');
      confidence += 0.5;
    }

    // Unusual timing patterns
    const actionTimes = recentActions.map(action => action.timestamp);
    const intervals = actionTimes.slice(1).map((time, index) =>
      time - actionTimes[index]
    );

    const averageInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
    if (averageInterval < 100) { // Less than 100ms between actions
      reasons.push('Bot-like activity pattern detected');
      confidence += 0.3;
    }

    return {
      isSuspicious: confidence > 0.6,
      reasons,
      confidence: Math.min(1, confidence)
    };
  }

  /**
   * Rate limiting implementation
   */
  static createRateLimiter(maxRequests: number, windowMs: number) {
    const requests: number[] = [];

    return {
      isAllowed: (): boolean => {
        const now = Date.now();

        // Remove old requests
        const validRequests = requests.filter(timestamp =>
          now - timestamp < windowMs
        );

        if (validRequests.length >= maxRequests) {
          return false;
        }

        validRequests.push(now);
        requests.length = 0;
        requests.push(...validRequests);
        return true;
      },
      getRemainingRequests: (): number => {
        const now = Date.now();
        const validRequests = requests.filter(timestamp =>
          now - timestamp < windowMs
        );
        return Math.max(0, maxRequests - validRequests.length);
      },
      reset: (): void => {
        requests.length = 0;
      }
    };
  }

  /**
   * Generate CSRF token
   */
  static generateCSRFToken(): string {
    return this.generateSecureRandom(32);
  }

  /**
   * Validate CSRF token
   */
  static validateCSRFToken(token: string, sessionToken: string): boolean {
    return token === sessionToken && token.length > 0;
  }

  /**
   * Setup security monitoring
   */
  static setupSecurityMonitoring(): void {
    // Monitor console access attempts
    const originalConsole = window.console;
    const consoleAccess: number[] = [];

    Object.defineProperty(window, 'console', {
      get: function() {
        consoleAccess.push(Date.now());
        return originalConsole;
      }
    });

    // Monitor devtools detection
    let devtools = {
      open: false,
      orientation: null
    };

    const threshold = 160;

    setInterval(() => {
      if (window.outerHeight - window.innerHeight > threshold ||
          window.outerWidth - window.innerWidth > threshold) {
        if (!devtools.open) {
          devtools.open = true;
          console.warn('Developer tools detected - security monitoring active');
        }
      } else {
        devtools.open = false;
      }
    }, 500);

    // Store monitoring data securely
    this.storeSecurityMetrics({
      consoleAccessAttempts: consoleAccess.length,
      devtoolsDetected: devtools.open,
      lastChecked: Date.now()
    });
  }

  /**
   * Store security metrics
   */
  public static storeSecurityMetrics(metrics: any): void {
    try {
      const existing = sessionStorage.getItem('security_metrics');
      const data = existing ? JSON.parse(existing) : {};
      data[Date.now()] = metrics;

      // Keep only last 100 entries
      const entries = Object.entries(data).slice(-100);
      const newData = Object.fromEntries(entries);

      sessionStorage.setItem('security_metrics', JSON.stringify(newData));
    } catch (error) {
      console.error('Failed to store security metrics:', error);
    }
  }

  /**
   * Get security report
   */
  static getSecurityReport(): {
    timestamp: number;
    securityScore: number;
    vulnerabilities: string[];
    recommendations: string[];
  } {
    const vulnerabilities: string[] = [];
    const recommendations: string[] = [];
    let securityScore = 100;

    // Check HTTPS
    if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
      vulnerabilities.push('Site not served over HTTPS');
      recommendations.push('Enable HTTPS for production');
      securityScore -= 30;
    }

    // Check CSP
    const cspMeta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
    if (!cspMeta) {
      vulnerabilities.push('No Content Security Policy detected');
      recommendations.push('Implement CSP headers');
      securityScore -= 20;
    }

    // Check for insecure dependencies (simplified)
    const scripts = document.querySelectorAll('script[src]');
    scripts.forEach(script => {
      const src = script.getAttribute('src');
      if (src && (src.includes('http:') || !src.includes('cdn'))) {
        vulnerabilities.push(`Insecure script loaded: ${src}`);
        recommendations.push('Use HTTPS CDN for all external scripts');
        securityScore -= 10;
      }
    });

    return {
      timestamp: Date.now(),
      securityScore: Math.max(0, securityScore),
      vulnerabilities,
      recommendations
    };
  }
}

/**
 * Initialize security measures
 */
export function initializeSecurity(): void {
  // Set CSP meta tag if not already set
  if (!document.querySelector('meta[http-equiv="Content-Security-Policy"]')) {
    const meta = document.createElement('meta');
    meta.setAttribute('http-equiv', 'Content-Security-Policy');
    meta.setAttribute('content', generateCSPHeader());
    document.head.appendChild(meta);
  }

  // Setup security monitoring
  if (process.env.NODE_ENV === 'production') {
    SecurityUtils.setupSecurityMonitoring();
  }

  // Add CSRF token to all forms
  const csrfToken = SecurityUtils.generateCSRFToken();
  sessionStorage.setItem('csrf_token', csrfToken);

  document.addEventListener('submit', (event) => {
    const form = event.target as HTMLFormElement;
    if (form.tagName === 'FORM') {
      let tokenInput = form.querySelector('input[name="csrf_token"]') as HTMLInputElement;

      if (!tokenInput) {
        tokenInput = document.createElement('input');
        tokenInput.type = 'hidden';
        tokenInput.name = 'csrf_token';
        form.appendChild(tokenInput);
      }

      tokenInput.value = csrfToken;
    }
  });
}

export default SecurityUtils;
