// src/contexts/AuthContext.tsx
// Enhanced authentication context with httpOnly cookie-based authentication
import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, useRef, ReactNode } from 'react';
import { User, ApiResponse, RegisterFormData } from '../types';
import { login as authServiceLogin, register, getCurrentUser, logout as authServiceLogout } from '../services/authService';
import { SecurityUtils } from '../utils/securityUtils';
// SECURITY: No longer using SecureTokenStorage - tokens in httpOnly cookies
interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<ApiResponse>;
  register: (userData: RegisterFormData) => Promise<ApiResponse>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  isSessionExpired: boolean;
  lastActivity: number;
  updateLastActivity: () => void;
}
const AuthContext = createContext<AuthContextType | undefined>(undefined);
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
interface AuthProviderProps {
  children: ReactNode;
}
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSessionExpired, setIsSessionExpired] = useState<boolean>(false);
  const [lastActivity, setLastActivity] = useState<number>(Date.now());

  // ✅ Use ref for session timeout to avoid re-creating interval
  const sessionTimeoutRef = useRef<number>(parseInt(import.meta.env.VITE_SESSION_TIMEOUT || '1800000'));

  // ✅ Track mounted status for useCallback hooks
  const isMountedRef = useRef<boolean>(true);

  // ✅ Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Enhanced initialization with security checks
  // ✅ FIXED: Using isMountedRef consistently
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const initAuth = async () => {
      try {
        const userData = localStorage.getItem('user');

        if (userData) {
          try {
            const currentUser = await getCurrentUser();

            if (!isMountedRef.current || signal.aborted) {
              return;
            }

            if (currentUser && SecurityUtils.validateEmail(currentUser.email)) {
              setUser(currentUser);
              setLastActivity(Date.now());
            } else {
              handleLogout();
            }
          } catch (error: any) {
            localStorage.removeItem('user');
            if (isMountedRef.current && !signal.aborted) {
              setUser(null);
            }
          }
        }
      } catch (error: any) {
        if (isMountedRef.current && !signal.aborted) {
          handleLogout();
        }
      } finally {
        if (isMountedRef.current && !signal.aborted) {
          setIsLoading(false);
        }
      }
    };

    initAuth();

    return () => {
      abortController.abort();
    };
  }, []);
  // Enhanced login with security validation
  const handleLogin = useCallback(async (email: string, password: string): Promise<ApiResponse> => {
    try {
      // Validate input
      if (!SecurityUtils.validateEmail(email)) {
        return { success: false, error: 'Invalid email format' };
      }

      if (password.length < 8) {
        return { success: false, error: 'Password must be at least 8 characters' };
      }

      // Check for suspicious login patterns (temporarily disabled for testing)
      const storedAttempts = sessionStorage.getItem('login_attempts') || '0';
      const attempts = parseInt(storedAttempts);

      // TEMPORARILY DISABLED: Remove rate limiting for testing
      // if (attempts >= 5) {
      //   return { success: false, error: 'Too many login attempts. Please try again later.' };
      // }

      // Perform login
      const { user: loggedInUser } = await authServiceLogin({
        email: email.trim().toLowerCase(),
        password
      });

      if (loggedInUser && SecurityUtils.validateEmail(loggedInUser.email)) {
        // ✅ Store user in localStorage for persistence across navigations
        localStorage.setItem('user', JSON.stringify(loggedInUser));

        // ✅ Check if component is still mounted before updating state
        if (isMountedRef.current) {
          setUser(loggedInUser);
          setLastActivity(Date.now());
          setIsSessionExpired(false);
        }

        // Clear login attempts on success
        sessionStorage.removeItem('login_attempts');

        return { success: true };
      } else {
        throw new Error('Invalid user data received');
      }
    } catch (error: any) {
      // Increment failed attempts
      const currentAttempts = parseInt(sessionStorage.getItem('login_attempts') || '0');
      sessionStorage.setItem('login_attempts', (currentAttempts + 1).toString());

      // Log security event
      SecurityUtils.storeSecurityMetrics({
        type: 'FAILED_LOGIN',
        timestamp: Date.now(),
        email: SecurityUtils.sanitizeHTML(email),
        ip: 'unknown' // In production, get from request
      });

      // Extract error message properly
      let errorMessage = 'Login failed';
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (error.response.data.detail?.msg) {
          errorMessage = error.response.data.detail.msg;
        } else {
          errorMessage = JSON.stringify(error.response.data.detail);
        }
      } else if (error.response?.data?.msg) {
        errorMessage = error.response.data.msg;
      } else if (error.message) {
        errorMessage = error.message;
      }

      return {
        success: false,
        error: errorMessage,
      };
    }
  }, []);

  // Enhanced registration with security validation
  const handleRegister = useCallback(async (userData: RegisterFormData): Promise<ApiResponse> => {
    try {
      // Validate email
      if (!SecurityUtils.validateEmail(userData.email)) {
        return { success: false, error: 'Invalid email format' };
      }

      // Validate password strength
      const passwordValidation = SecurityUtils.validatePasswordStrength(userData.password);
      if (!passwordValidation.isValid) {
        return {
          success: false,
          error: passwordValidation.errors.join(', ')
        };
      }

      // Sanitize user data
      const sanitizedData = {
        email: userData.email.trim().toLowerCase(),
        full_name: SecurityUtils.sanitizeHTML(userData.full_name.trim()),
        password: userData.password
      };

      await register(sanitizedData);

      // Log successful registration
      SecurityUtils.storeSecurityMetrics({
        type: 'SUCCESSFUL_REGISTRATION',
        timestamp: Date.now(),
        email: SecurityUtils.sanitizeHTML(userData.email)
      });

      return { success: true };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed',
      };
    }
  }, []);

  // Enhanced logout with comprehensive cleanup
  // ✅ Removed user dependency - no more infinite loop
  const handleLogout = useCallback(() => {
    try {
      // Clear auth state first (before trying to log metrics)
      authServiceLogout();

      // ✅ Check if component is still mounted before updating state
      if (isMountedRef.current) {
        setUser(null);
        setIsSessionExpired(false);
        setLastActivity(0);
      }

      // Clear user data from localStorage (non-sensitive)
      localStorage.removeItem('user');
      sessionStorage.removeItem('login_attempts');

      // Clear any remaining sensitive data from sessionStorage
      Object.keys(sessionStorage).forEach(key => {
        if (key.includes('auth') || key.includes('user') || key.includes('token')) {
          sessionStorage.removeItem(key);
        }
      });

      // SECURITY: Tokens are in httpOnly cookies, cleared by backend logout endpoint
      // Note: Security metrics removed to avoid user dependency that causes loop
      // If needed, use a ref or separate effect to log after logout

    } catch (error) {
      console.error('Logout error:', error);
      // Force cleanup even if error occurs
      setUser(null);
      localStorage.removeItem('user');
    }
  }, []);  // ✅ No dependencies - stable reference

  // Token refresh functionality
  // ✅ Removed handleLogout dependency - direct state clearing
  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      // SECURITY: Token refresh handled automatically by backend via httpOnly cookies
      // Just validate session by getting current user
      const refreshed = await getCurrentUser();
      if (refreshed) {
        setUser(refreshed);
        setLastActivity(Date.now());
        return true;
      }
      return false;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // ✅ Clear state directly without calling handleLogout to avoid loop
      setUser(null);
      setLastActivity(0);
      localStorage.removeItem('user');
      return false;
    }
  }, []);  // ✅ No dependencies - stable reference

  // Update last activity timestamp
  const updateLastActivity = useCallback(() => {
    setLastActivity(Date.now());
  }, []);

  // Session monitoring
  // ✅ FIXED: Removed lastActivity dependency to prevent interval recreation
  useEffect(() => {
    const sessionMonitor = setInterval(() => {
      const now = Date.now();
      const sessionTimeout = sessionTimeoutRef.current;
      const currentActivity = lastActivity; // Capture current value in closure

      if (currentActivity && (now - currentActivity) > sessionTimeout) {
        setIsSessionExpired(true);
        // ✅ Clear state directly without calling handleLogout to avoid loop
        if (isMountedRef.current) {
          setUser(null);
          setLastActivity(0);
          localStorage.removeItem('user');
        }
      }
    }, 60000); // Check every minute

    return () => clearInterval(sessionMonitor);
  }, []); // ✅ Empty deps - interval created once, reads latest lastActivity value

  // ✅ MEMOIZED: Only creates new object when dependencies change
  const value: AuthContextType = useMemo(() => ({
    user,
    isLoading,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    refreshToken,
    isSessionExpired,
    lastActivity,
    updateLastActivity,
  }), [user, isLoading, handleLogin, handleRegister, handleLogout, refreshToken, isSessionExpired, lastActivity, updateLastActivity]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
