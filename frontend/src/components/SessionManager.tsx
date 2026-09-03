/**
 * SessionManager Component
 *
 * Manages authentication state across the application, preventing race conditions
 * between token refresh and auth checks. This component:
 * 1. Listens for sessionExpired events from the API interceptor
 * 2. Shows the SessionExpiryModal when appropriate
 * 3. Coordinates with RequireAuth to prevent premature redirects
 * 4. Manages the global session refresh state
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { SessionExpiryModal } from './SessionExpiryModal';
import { useAuth } from '../contexts/AuthContext';

// Global state accessible across components
interface SessionState {
  isRefreshing: boolean;
  isExpiring: boolean;
  lastCheck: number;
}

const globalSessionState: SessionState = {
  isRefreshing: false,
  isExpiring: false,
  lastCheck: 0
};

// Export global state so other components can access it
export { globalSessionState };

// Accessor functions for global state
export const getIsRefreshing = () => globalSessionState.isRefreshing;
export const setIsRefreshing = (value: boolean) => {
  globalSessionState.isRefreshing = value;
};
export const setIsExpiring = (value: boolean) => {
  globalSessionState.isExpiring = value;
};
export const updateLastCheck = () => {
  globalSessionState.lastCheck = Date.now();
};

// Debounce timer for auth checks to prevent rapid redirects
let authCheckDebounceTimer: number | null = null;

export const debounceAuthCheck = (callback: () => void, delay: number = 500) => {
  if (authCheckDebounceTimer) {
    clearTimeout(authCheckDebounceTimer);
  }
  authCheckDebounceTimer = window.setTimeout(callback, delay);
};

export const clearAuthCheckDebounce = () => {
  if (authCheckDebounceTimer) {
    clearTimeout(authCheckDebounceTimer);
    authCheckDebounceTimer = null;
  }
};

interface SessionManagerProps {
  children: React.ReactNode;
}

export const SessionManager: React.FC<SessionManagerProps> = ({ children }) => {
  const [showExpiryModal, setShowExpiryModal] = useState(false);
  const { logout } = useAuth();
  const logoutRef = useRef(logout);
  const isMountedRef = useRef(true);

  // Keep ref in sync with latest logout function
  useEffect(() => {
    logoutRef.current = logout;
  }, [logout]);

  // Handle component lifecycle
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      clearAuthCheckDebounce();
    };
  }, []);

  // Listen for session expired events from API interceptor
  useEffect(() => {
    const handleSessionExpired = (event: Event) => {
      console.log('[SessionManager] Session expired event received:', event);

      // Prevent multiple modal instances
      if (showExpiryModal) {
        console.log('[SessionManager] Modal already showing, ignoring event');
        return;
      }

      // Mark session as expiring to prevent redirects from RequireAuth
      setIsExpiring(true);

      if (isMountedRef.current) {
        setShowExpiryModal(true);
      }
    };

    // Listen for the custom event dispatched by api.ts
    window.addEventListener('sessionExpired', handleSessionExpired);

    return () => {
      window.removeEventListener('sessionExpired', handleSessionExpired);
    };
  }, [showExpiryModal]);

  // Handle the logout action from the modal
  const handleLogout = useCallback(() => {
    console.log('[SessionManager] Handling logout from modal');

    // Clear session state
    clearAuthCheckDebounce();
    setIsExpiring(false);
    setIsRefreshing(false);

    // Perform the actual logout
    if (isMountedRef.current) {
      setShowExpiryModal(false);
    }

    // Call the auth logout
    logoutRef.current();
  }, []);

  // Listen for auth loading states from AuthContext
  useEffect(() => {
    const handleAuthLoadingStart = () => {
      console.log('[SessionManager] Auth refresh started');
      setIsRefreshing(true);
    };

    const handleAuthLoadingEnd = () => {
      console.log('[SessionManager] Auth refresh ended');
      setIsRefreshing(false);
      updateLastCheck();
    };

    // Listen for auth events
    window.addEventListener('authRefreshStart', handleAuthLoadingStart);
    window.addEventListener('authRefreshEnd', handleAuthLoadingEnd);

    return () => {
      window.removeEventListener('authRefreshStart', handleAuthLoadingStart);
      window.removeEventListener('authRefreshEnd', handleAuthLoadingEnd);
    };
  }, []);

  return (
    <>
      {children}

      {/* Session Expiry Modal - Shows when session has expired */}
      {showExpiryModal && (
        <SessionExpiryModal
          onLogout={handleLogout}
          countdownSeconds={30}
        />
      )}
    </>
  );
};

/**
 * Hook to interact with the SessionManager
 */
export const useSessionManager = () => {
  const isRefreshing = getIsRefreshing();
  const isExpiring = globalSessionState.isExpiring;

  const triggerAuthRefresh = useCallback(() => {
    const event = new CustomEvent('authRefreshStart');
    window.dispatchEvent(event);
  }, []);

  const completeAuthRefresh = useCallback(() => {
    const event = new CustomEvent('authRefreshEnd');
    window.dispatchEvent(event);
  }, []);

  return {
    isRefreshing,
    isExpiring,
    triggerAuthRefresh,
    completeAuthRefresh,
  };
};
