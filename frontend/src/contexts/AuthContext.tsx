// src/contexts/AuthContext.tsx
// Enhanced authentication context with httpOnly cookie-based authentication
import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, ReactNode } from 'react';
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

  // Enhanced initialization with security checks
  useEffect(() => {
    const initAuth = async () => {
      try {
        // SECURITY: Check for existing user data in localStorage
        // Tokens are in httpOnly cookies, managed by backend
        const userData = localStorage.getItem('user');

        if (userData) {
          try {
            // Get current user from backend to validate session
            const currentUser = await getCurrentUser();
            if (currentUser && SecurityUtils.validateEmail(currentUser.email)) {
              setUser(currentUser);
              setLastActivity(Date.now());
            } else {
              console.warn('Invalid user data received');
              handleLogout();
            }
          } catch (error) {
            console.error('Failed to fetch current user:', error);
            // Backend will validate httpOnly cookies
            // If 401, cookies are invalid/expired
            localStorage.removeItem('user');
            setUser(null);
          }
        }
      } catch (error) {
        console.error('Authentication initialization failed:', error);
        handleLogout();
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
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
        setUser(loggedInUser);
        setLastActivity(Date.now());
        setIsSessionExpired(false);

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
  const handleLogout = useCallback(() => {
    try {
      // Log security event
      if (user) {
        SecurityUtils.storeSecurityMetrics({
          type: 'LOGOUT',
          timestamp: Date.now(),
          userId: user.id?.toString() || 'unknown'
        });
      }

      // Clear auth state
      authServiceLogout();
      setUser(null);
      setIsSessionExpired(false);
      setLastActivity(0);

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

    } catch (error) {
      console.error('Logout error:', error);
      // Force cleanup even if error occurs
      setUser(null);
      localStorage.removeItem('user');
    }
  }, [user]);

  // Token refresh functionality
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
      handleLogout();
      return false;
    }
  }, [handleLogout]);

  // Update last activity timestamp
  const updateLastActivity = useCallback(() => {
    setLastActivity(Date.now());
  }, []);

  // Session monitoring
  useEffect(() => {
    const sessionMonitor = setInterval(() => {
      const now = Date.now();
      const sessionTimeout = parseInt(import.meta.env.VITE_SESSION_TIMEOUT || '1800000'); // 30 minutes

      if (lastActivity && (now - lastActivity) > sessionTimeout) {
        setIsSessionExpired(true);
        handleLogout();
      }
    }, 60000); // Check every minute

    return () => clearInterval(sessionMonitor);
  }, [lastActivity, handleLogout]);

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
