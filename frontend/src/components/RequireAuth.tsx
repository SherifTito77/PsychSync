// src/components/RequireAuth.tsx
// Fixed: Simplified logic to prevent stuck loading states
import React, { useEffect, useRef } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from './common/LoadingSpinner';
import { getIsRefreshing, setIsExpiring, debounceAuthCheck, globalSessionState } from './SessionManager';

interface RequireAuthProps {
  children: React.ReactNode;
}

const RequireAuth: React.FC<RequireAuthProps> = ({ children }) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  // Track whether we've already checked auth for this location
  const authCheckRef = useRef<string | null>(null);

  // Only log in development to reduce console noise
  const isDevelopment = import.meta.env.MODE === 'development';
  if (isDevelopment) {
    console.log('[RequireAuth] Checking auth for path:', location.pathname);
    console.log('[RequireAuth] User:', user ? 'exists' : 'null');
    console.log('[RequireAuth] Loading:', isLoading);
    console.log('[RequireAuth] Session refreshing:', getIsRefreshing());
  }

  // Clear expiring state when we successfully have a user
  useEffect(() => {
    if (user) {
      setIsExpiring(false);
    }
  }, [user]);

  // Show loading spinner ONLY during initial auth load (isLoading=true)
  // Don't use global isRefreshing for initial auth - it's for token refresh only
  if (isLoading) {
    if (isDevelopment) {
      console.log('[RequireAuth] Showing initial auth loading spinner');
    }
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  // Use debounced redirect to prevent rapid redirects during token refresh
  if (!user) {
    // Check if session is expiring - if so, show loading to prevent redirect
    const isExpiring = globalSessionState.isExpiring;

    // Only redirect if we haven't already checked this location AND session is not expiring
    const checkKey = `${location.pathname}-${Date.now()}`;

    if (authCheckRef.current !== checkKey) {
      if (isDevelopment) {
        console.log('[RequireAuth] No user, debouncing redirect to login');
      }

      // Debounce the redirect to give token refresh a chance
      debounceAuthCheck(() => {
        // Only redirect if: no user, not refreshing, not expiring
        if (!user && !getIsRefreshing() && !isExpiring) {
          // If still no user and not refreshing, perform redirect
          if (isDevelopment) {
            console.log('[RequireAuth] Debounce completed, redirecting to login with from:', location.pathname);
          }
          // Store current path for redirect after login
          sessionStorage.setItem('redirect_after_login', location.pathname);
          window.location.href = '/login';
        } else if (isExpiring) {
          // Session is expiring, don't redirect - let SessionManager handle it
          if (isDevelopment) {
            console.log('[RequireAuth] Session expiring, waiting for SessionManager');
          }
        }
      }, 500); // 500ms debounce to allow token refresh to complete

      authCheckRef.current = checkKey;
    }

    // Show a brief loading state while debounce is active
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  // If there is a user, render the child components
  if (isDevelopment) {
    console.log('[RequireAuth] User authenticated, rendering children');
  }
  return <>{children}</>;
};

export default RequireAuth;
