/**
 * Analytics Consent Banner Component
 *
 * GDPR-compliant consent banner for analytics tracking.
 *
 * Features:
 * - Clear, concise information about data collection
 * - Explicit opt-in action (no pre-checked boxes)
 * - Easy to understand language
 * - Link to privacy policy
 * - Dismissible only after making a choice
 * - Persistent across sessions until decision made
 *
 * GDPR Compliance:
 * - Article 7: Unambiguous consent mechanism
 * - Article 7(3): Easy withdrawal of consent
 * - Article 13: Transparent information about processing
 */

import React, { useState } from 'react';
import { useAnalyticsConsent } from '@/contexts/AnalyticsConsentContext';
import logger from '@/utils/logger';

/**
 * Analytics Consent Banner
 *
 * Displays when user hasn't made a consent decision.
 * Requires explicit opt-in for analytics tracking.
 */
export const AnalyticsConsentBanner: React.FC = () => {
  const { grantConsent, denyConsent, hasDecided } = useAnalyticsConsent();
  const [isLoading, setIsLoading] = useState(false);

  // Don't show banner if user has already decided
  if (hasDecided) {
    return null;
  }

  const handleAccept = async () => {
    setIsLoading(true);
    try {
      await grantConsent();
      logger.info('User granted analytics consent');
      // Reload page to initialize analytics with consent
      window.location.reload();
    } catch (error) {
      logger.error('Failed to grant analytics consent', error);
      setIsLoading(false);
    }
  };

  const handleDecline = async () => {
    setIsLoading(true);
    try {
      await denyConsent();
      logger.info('User denied analytics consent');
    } catch (error) {
      logger.error('Failed to deny analytics consent', error);
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900 text-white p-6 shadow-2xl z-50 animate-slide-up">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          {/* Consent Message */}
          <div className="flex-1">
            <h3 className="text-lg font-semibold mb-2">
              📊 Analytics & Usage Data
            </h3>
            <p className="text-gray-300 text-sm mb-2">
              We use analytics to understand how you use our platform and improve your experience.
              This includes tracking pages you visit, features you use, and how you interact with assessments.
            </p>
            <p className="text-gray-400 text-xs">
              <strong>We collect:</strong> Anonymous usage data, page views, feature usage patterns
            </p>
            <p className="text-gray-400 text-xs mt-1">
              <strong>We don't collect:</strong> Personal content, assessment responses without consent
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 shrink-0">
            <button
              onClick={handleDecline}
              disabled={isLoading}
              className="px-6 py-2 bg-transparent border border-gray-600 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              {isLoading ? 'Processing...' : 'Decline'}
            </button>
            <button
              onClick={handleAccept}
              disabled={isLoading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              {isLoading ? 'Processing...' : 'Accept'}
            </button>
          </div>
        </div>

        {/* Privacy Policy Link */}
        <div className="mt-4 pt-4 border-t border-gray-700 text-xs text-gray-400">
          <a
            href="/privacy"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white underline"
          >
            Read our Privacy Policy
          </a>
          {' '}&bull;{' '}
          <span>
            You can change this preference anytime in Settings
          </span>
        </div>
      </div>
    </div>
  );
};

/**
 * Minimal Consent Banner (Alternative Design)
 *
 * More compact version for less intrusive UX.
 */
export const AnalyticsConsentBannerMinimal: React.FC = () => {
  const { grantConsent, denyConsent, hasDecided } = useAnalyticsConsent();
  const [isLoading, setIsLoading] = useState(false);

  if (hasDecided) {
    return null;
  }

  const handleAccept = async () => {
    setIsLoading(true);
    try {
      await grantConsent();
      window.location.reload();
    } catch (error) {
      logger.error('Failed to grant consent', error);
      setIsLoading(false);
    }
  };

  const handleDecline = async () => {
    setIsLoading(true);
    try {
      await denyConsent();
    } catch (error) {
      logger.error('Failed to deny consent', error);
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-4 right-4 max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-xl p-4 z-50 border border-gray-200 dark:border-gray-700">
      <div className="flex items-start gap-3">
        <div className="text-2xl">📊</div>
        <div className="flex-1">
          <h4 className="font-semibold text-sm mb-1">Help us improve</h4>
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
            We use anonymous analytics to improve your experience. You can opt out anytime.
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleDecline}
              disabled={isLoading}
              className="text-xs px-3 py-1.5 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors disabled:opacity-50"
            >
              Decline
            </button>
            <button
              onClick={handleAccept}
              disabled={isLoading}
              className="text-xs px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              Accept
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsConsentBanner;
