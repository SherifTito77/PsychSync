import React, { useState, useEffect } from 'react';
import { pwaManager, PWAInstallStatus } from '../utils/pwaManager';

interface PWAInstallerProps {
  className?: string;
  showInstructions?: boolean;
  onInstallComplete?: () => void;
  onInstallDismissed?: () => void;
}

/**
 * 🚀 PWA Installer Component
 *
 * Handles Progressive Web App installation with platform-specific instructions
 * and intelligent install prompts based on user device and browser capabilities
 */
const PWAInstaller: React.FC<PWAInstallerProps> = ({
  className = '',
  showInstructions = true,
  onInstallComplete,
  onInstallDismissed
}) => {
  const [installStatus, setInstallStatus] = useState<PWAInstallStatus | null>(null);
  const [isInstalling, setIsInstalling] = useState(false);
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);
  const [dismissedCount, setDismissedCount] = useState(0);

  // Maximum number of times to show install prompt before giving up
  const MAX_PROMPT_DISPLAYS = 3;

  useEffect(() => {
    const checkInstallStatus = () => {
      const status = pwaManager.getInstallStatus();
      setInstallStatus(status);

      // Show install prompt if app is installable but not installed
      // and user hasn't dismissed it too many times
      const hasDismissedTooMany = dismissedCount >= MAX_PROMPT_DISPLAYS;

      if (status.isInstallable && !status.isInstalled && !hasDismissedTooMany) {
        // Delay showing prompt to avoid interrupting user flow
        setTimeout(() => {
          setShowInstallPrompt(true);
        }, 3000);
      }
    };

    checkInstallStatus();

    // Set up event listeners
    pwaManager.setOnInstallPromptReady(() => {
      checkInstallStatus();
    });

    pwaManager.setOnAppInstalled(() => {
      setInstallStatus(pwaManager.getInstallStatus());
      setShowInstallPrompt(false);
      onInstallComplete?.();
    });

    // Check install status periodically
    const interval = setInterval(checkInstallStatus, 30000);

    return () => clearInterval(interval);
  }, [dismissedCount, onInstallComplete]);

  const handleInstallClick = async () => {
    if (!installStatus?.beforeInstallPrompt) {
      return;
    }

    setIsInstalling(true);

    try {
      const success = await pwaManager.showInstallPrompt();

      if (success) {
        setShowInstallPrompt(false);
        onInstallComplete?.();
      } else {
        onInstallDismissed?.();
      }
    } catch (error) {
      console.error('Install failed:', error);
      onInstallDismissed?.();
    } finally {
      setIsInstalling(false);
    }
  };

  const handleDismiss = () => {
    setShowInstallPrompt(false);
    setDismissedCount(prev => prev + 1);
    onInstallDismissed?.();
  };

  const handleNeverShow = () => {
    setShowInstallPrompt(false);
    localStorage.setItem('pwa-install-dismissed-permanently', 'true');
  };

  const isPermanentlyDismissed = () => {
    return localStorage.getItem('pwa-install-dismissed-permanently') === 'true';
  };

  if (!installStatus || installStatus.isInstalled || isPermanentlyDismissed()) {
    return null;
  }

  if (!showInstallPrompt) {
    return null;
  }

  const getInstallButtonLabel = () => {
    if (isInstalling) return 'Installing...';

    switch (installStatus.platform) {
      case 'ios':
        return 'Add to Home Screen';
      case 'android':
        return 'Install App';
      case 'desktop':
        return 'Install App';
      default:
        return 'Install PsychSync';
    }
  };

  const getPlatformIcon = () => {
    switch (installStatus.platform) {
      case 'ios':
        return '🍎';
      case 'android':
        return '🤖';
      case 'desktop':
        return '💻';
      default:
        return '📱';
    }
  };

  return (
    <div className={`pwa-installer ${className}`}>
      {/* Install Banner */}
      <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 bg-white rounded-lg shadow-xl border border-gray-200 p-4 z-50 animate-in slide-in-from-bottom">
        <div className="flex items-start space-x-3">
          {/* App Icon */}
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-xl font-bold">P</span>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-1">
              <span className="text-lg">{getPlatformIcon()}</span>
              <h3 className="text-lg font-semibold text-gray-900">
                Install PsychSync
              </h3>
            </div>

            <p className="text-sm text-gray-600 mb-3">
              Get offline access, faster loading, and a native app experience.
            </p>

            {showInstructions && installStatus.installInstructions && (
              <div className="text-xs text-gray-500 mb-3 p-2 bg-gray-50 rounded">
                <strong>Instructions:</strong> {installStatus.installInstructions}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-2">
              <button
                onClick={handleInstallClick}
                disabled={isInstalling || !installStatus.isInstallable}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {getInstallButtonLabel()}
              </button>

              <button
                onClick={handleDismiss}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium transition-colors"
              >
                Maybe Later
              </button>

              {dismissedCount >= MAX_PROMPT_DISPLAYS - 1 && (
                <button
                  onClick={handleNeverShow}
                  className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
                >
                  Don't ask again
                </button>
              )}
            </div>
          </div>

          {/* Dismiss Button */}
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Install Styles */}
      <style>{`
        @keyframes slide-in-from-bottom {
          from {
            transform: translateY(20px);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }

        .animate-in {
          animation: slide-in-from-bottom 0.3s ease-out;
        }

        /* Respect reduced motion preference */
        @media (prefers-reduced-motion: reduce) {
          .animate-in {
            animation: none;
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};

export default PWAInstaller;
