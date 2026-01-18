/**
 * Session Expiry Modal
 * Shows user-friendly warning when session expires instead of hard redirect
 * Allows users to save work before being redirected to login
 */

import React, { useEffect, useState } from 'react';
import { AlertCircle, LogOut } from 'lucide-react';

interface SessionExpiryModalProps {
  onLogout: () => void;
  countdownSeconds?: number;
}

export const SessionExpiryModal: React.FC<SessionExpiryModalProps> = ({
  onLogout,
  countdownSeconds = 30
}) => {
  const [countdown, setCountdown] = useState(countdownSeconds);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          // Auto-redirect after countdown
          onLogout();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [onLogout]);

  const handleLogoutNow = () => {
    onLogout();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <AlertCircle className="h-12 w-12 text-amber-600" />
          </div>

          <div className="flex-1">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Your Session Has Expired
            </h2>

            <div className="space-y-3">
              <p className="text-gray-600">
                For your security, you've been logged out due to inactivity.
              </p>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-sm text-amber-900">
                  <span className="font-semibold">Redirecting to login in {countdown} seconds...</span>
                </p>
                {/* Countdown progress bar */}
                <div className="mt-2 w-full bg-amber-200 rounded-full h-2">
                  <div
                    className="bg-amber-600 h-2 rounded-full transition-all duration-1000"
                    style={{ width: `${(countdown / countdownSeconds) * 100}%` }}
                  />
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-xs text-blue-900">
                  <strong>Tip:</strong> Any unsaved work may be lost. Please save your work frequently to avoid data loss.
                </p>
              </div>
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={handleLogoutNow}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <LogOut className="h-4 w-4" />
                Go to Login Now
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Hook to manage session expiry state
 */
export const useSessionExpiry = () => {
  const [showExpiryModal, setShowExpiryModal] = useState(false);

  const triggerSessionExpiry = () => {
    // Store current path for redirect after login
    sessionStorage.setItem('redirect_after_login', window.location.pathname);
    sessionStorage.setItem('session_expired', 'true');
    setShowExpiryModal(true);
  };

  const handleLogout = () => {
    // Clear auth tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');

    // Redirect to login
    window.location.href = '/login?reason=session_expired';
  };

  return {
    showExpiryModal,
    triggerSessionExpiry,
    handleLogout,
    setShowExpiryModal,
  };
};
