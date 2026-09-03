/**
 * Analytics Consent Settings Component
 *
 * Allows users to manage their analytics consent preferences.
 *
 * GDPR Compliance:
 * - Article 7(3): Consent must be withdrawable as easily as it is given
 * - Article 17: Right to be forgotten (data deletion)
 * - Article 16: Right to rectification (data access/modification)
 */

import React, { useState } from 'react';
import { useAnalyticsConsent, ConsentStatus } from '@/contexts/AnalyticsConsentContext';
import logger from '@/utils/logger';

interface AnalyticsConsentSettingsProps {
  className?: string;
}

/**
 * Analytics Consent Settings Panel
 *
 * Provides full control over analytics consent including:
 * - View current consent status
 * - Withdraw consent and delete data
 * - Grant consent if previously denied
 * - View consent history
 */
export const AnalyticsConsentSettings: React.FC<AnalyticsConsentSettingsProps> = ({
  className = ''
}) => {
  const {
    consentStatus,
    hasDecided,
    consentDate,
    lastUpdated,
    grantConsent,
    denyConsent,
    withdrawConsent,
  } = useAnalyticsConsent();

  const [isProcessing, setIsProcessing] = useState(false);
  const [showDataDeletionWarning, setShowDataDeletionWarning] = useState(false);

  const handleGrantConsent = async () => {
    setIsProcessing(true);
    try {
      await grantConsent();
      logger.info('Analytics consent granted from settings');
      // Reload to apply changes
      setTimeout(() => window.location.reload(), 500);
    } catch (error) {
      logger.error('Failed to grant consent', error);
      setIsProcessing(false);
    }
  };

  const handleWithdrawConsent = async () => {
    if (!showDataDeletionWarning) {
      setShowDataDeletionWarning(true);
      return;
    }

    setIsProcessing(true);
    try {
      await withdrawConsent();
      logger.info('Analytics consent withdrawn from settings');
      setShowDataDeletionWarning(false);
      // Reload to apply changes
      setTimeout(() => window.location.reload(), 500);
    } catch (error) {
      logger.error('Failed to withdraw consent', error);
      setIsProcessing(false);
      setShowDataDeletionWarning(false);
    }
  };

  const handleDenyConsent = async () => {
    setIsProcessing(true);
    try {
      await denyConsent();
      logger.info('Analytics consent denied from settings');
    } catch (error) {
      logger.error('Failed to deny consent', error);
      setIsProcessing(false);
    }
  };

  const getStatusBadge = (status: ConsentStatus) => {
    const styles = {
      granted: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      denied: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    };

    const labels = {
      granted: 'Enabled',
      denied: 'Disabled',
      pending: 'Pending',
    };

    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${styles[status]}`}>
        {labels[status]}
      </span>
    );
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg p-6 ${className}`}>
      <h2 className="text-xl font-semibold mb-4">Analytics & Usage Data</h2>

      {/* Current Status */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
            Current Status:
          </span>
          {hasDecided ? getStatusBadge(consentStatus) : getStatusBadge('pending')}
        </div>

        {/* Consent History */}
        {hasDecided && (
          <div className="text-xs text-gray-500 dark:text-gray-500 space-y-1 mt-3">
            <div className="flex justify-between">
              <span>Consent granted:</span>
              <span>{formatDate(consentDate)}</span>
            </div>
            <div className="flex justify-between">
              <span>Last updated:</span>
              <span>{formatDate(lastUpdated)}</span>
            </div>
          </div>
        )}
      </div>

      {/* What We Collect */}
      <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <h3 className="text-sm font-semibold mb-2">What we collect:</h3>
        <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
          <li>✓ Pages you visit and how long you stay</li>
          <li>✓ Features you use most often</li>
          <li>✓ Assessment completion patterns</li>
          <li>✓ Browser type and device information</li>
          <li>✓ Anonymous session ID</li>
        </ul>
      </div>

      {/* What We Don't Collect */}
      <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <h3 className="text-sm font-semibold mb-2">What we don't collect:</h3>
        <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
          <li>✗ Personal assessment responses</li>
          <li>✗ Names, email addresses, or phone numbers</li>
          <li>✗ Files you upload</li>
          <li>✗ Chat messages or communication content</li>
        </ul>
      </div>

      {/* Actions */}
      <div className="space-y-3">
        {consentStatus === 'granted' && (
          <>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              You're currently sharing analytics data to help us improve the platform.
            </p>

            <button
              onClick={handleWithdrawConsent}
              disabled={isProcessing}
              className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isProcessing ? 'Processing...' : 'Disable Analytics & Delete Data'}
            </button>

            {showDataDeletionWarning && (
              <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                <p className="text-xs text-yellow-800 dark:text-yellow-200 font-medium mb-2">
                  ⚠️ This will:
                </p>
                <ul className="text-xs text-yellow-700 dark:text-yellow-300 space-y-1 ml-4">
                  <li>• Disable all analytics tracking</li>
                  <li>• Delete your historical analytics data</li>
                  <li>• Clear tracking identifiers from your browser</li>
                </ul>
                <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-2">
                  This action cannot be undone. Click again to confirm.
                </p>
              </div>
            )}
          </>
        )}

        {consentStatus === 'denied' && (
          <>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              Analytics tracking is currently disabled. You can enable it anytime to help us improve.
            </p>

            <button
              onClick={handleGrantConsent}
              disabled={isProcessing}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isProcessing ? 'Processing...' : 'Enable Analytics'}
            </button>
          </>
        )}

        {!hasDecided && (
          <p className="text-sm text-gray-500 italic">
            You haven't made a decision about analytics yet. You'll see a consent banner on your next visit.
          </p>
        )}
      </div>

      {/* Privacy Policy Link */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700 text-center">
        <a
          href="/privacy"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:text-blue-700 underline"
        >
          Read our full Privacy Policy
        </a>
      </div>
    </div>
  );
};

/**
 * Compact Analytics Toggle Component
 *
 * Minimal version for use in settings pages.
 */
export const AnalyticsToggle: React.FC = () => {
  const { consentStatus, hasDecided, grantConsent, withdrawConsent } = useAnalyticsConsent();
  const [isProcessing, setIsProcessing] = useState(false);

  const isEnabled = hasDecided && consentStatus === 'granted';

  const handleToggle = async () => {
    setIsProcessing(true);
    try {
      if (isEnabled) {
        await withdrawConsent();
      } else {
        await grantConsent();
      }
      setTimeout(() => window.location.reload(), 500);
    } catch (error) {
      logger.error('Failed to toggle analytics', error);
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex items-center justify-between">
      <div>
        <h4 className="text-sm font-medium">Analytics & Usage Data</h4>
        <p className="text-xs text-gray-500">Help us improve your experience</p>
      </div>

      <button
        onClick={handleToggle}
        disabled={isProcessing}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          isEnabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
        } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            isEnabled ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  );
};

export default AnalyticsConsentSettings;
