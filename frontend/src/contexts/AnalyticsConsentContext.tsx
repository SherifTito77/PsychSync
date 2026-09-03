/**
 * Analytics Consent Management Context
 *
 * Manages user consent for analytics tracking in compliance with GDPR Article 7.
 * Provides:
 * - Consent state management
 * - Consent granting/denial
 * - Consent withdrawal (opt-out)
 * - Persistent consent storage
 * - Data deletion on consent withdrawal
 * - Integration with analytics tracker
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import api from '@/services/api';
import logger from '@/utils/logger';
import { getAnalytics } from '@/services/analytics/tracker';

export type ConsentStatus = 'pending' | 'granted' | 'denied';

export interface AnalyticsConsentState {
  consentStatus: ConsentStatus;
  hasDecided: boolean;
  consentDate: string | null;
  lastUpdated: string | null;
}

export interface AnalyticsConsentContextValue extends AnalyticsConsentState {
  grantConsent: () => Promise<void>;
  denyConsent: () => Promise<void>;
  withdrawConsent: () => Promise<void>;
  resetConsent: () => void;
}

const AnalyticsConsentContext = createContext<AnalyticsConsentContextValue | undefined>(undefined);

const CONSENT_STORAGE_KEY = 'analytics_consent';
const CONSENT_DATE_KEY = 'analytics_consent_date';
const CONSENT_UPDATED_KEY = 'analytics_consent_updated';

interface AnalyticsConsentProviderProps {
  children: ReactNode;
}

/**
 * Analytics Consent Provider
 *
 * Manages GDPR-compliant consent for analytics tracking.
 * Implements:
 * - Explicit opt-in consent (GDPR Article 7)
 * - Easy withdrawal of consent (GDPR Article 7(3))
 * - Right to be forgotten (GDPR Article 17)
 * - Consent history tracking
 */
export const AnalyticsConsentProvider: React.FC<AnalyticsConsentProviderProps> = ({ children }) => {
  const [consentState, setConsentState] = useState<AnalyticsConsentState>({
    consentStatus: 'pending',
    hasDecided: false,
    consentDate: null,
    lastUpdated: null,
  });

  /**
   * Load consent from localStorage on mount
   */
  useEffect(() => {
    const loadConsent = () => {
      try {
        const storedConsent = localStorage.getItem(CONSENT_STORAGE_KEY);
        const consentDate = localStorage.getItem(CONSENT_DATE_KEY);
        const lastUpdated = localStorage.getItem(CONSENT_UPDATED_KEY);

        if (storedConsent === 'granted' || storedConsent === 'denied') {
          setConsentState({
            consentStatus: storedConsent,
            hasDecided: true,
            consentDate: consentDate || new Date().toISOString(),
            lastUpdated: lastUpdated || new Date().toISOString(),
          });
        }
      } catch (error) {
        logger.error('Failed to load analytics consent from localStorage', error);
      }
    };

    loadConsent();
  }, []);

  /**
   * ✅ GDPR COMPLIANT: Grant consent for analytics tracking
   *
   * User has explicitly opted in to analytics tracking.
   * Stores consent with timestamp for audit trail.
   */
  const grantConsent = useCallback(async () => {
    try {
      const now = new Date().toISOString();

      // Update localStorage
      localStorage.setItem(CONSENT_STORAGE_KEY, 'granted');
      localStorage.setItem(CONSENT_DATE_KEY, now);
      localStorage.setItem(CONSENT_UPDATED_KEY, now);

      setConsentState({
        consentStatus: 'granted',
        hasDecided: true,
        consentDate: now,
        lastUpdated: now,
      });

      // ✅ GDPR: Notify tracker to start collecting data
      try {
        const tracker = getAnalytics();
        tracker.setConsent(true);
      } catch (error) {
        logger.warn('Failed to notify tracker of consent grant', error);
      }

      // Optionally notify backend of consent grant
      try {
        await api.post('/analytics/consent', {
          action: 'grant',
          timestamp: now,
        });
      } catch (error) {
        logger.warn('Failed to notify backend of consent grant', error);
        // Don't block on backend error - localStorage is sufficient
      }

      logger.info('Analytics consent granted');
    } catch (error) {
      logger.error('Failed to grant analytics consent', error);
      throw error;
    }
  }, []);

  /**
   * ✅ GDPR COMPLIANT: Deny consent for analytics tracking
   *
   * User has explicitly opted out of analytics tracking.
   * Stores denial with timestamp for audit trail.
   */
  const denyConsent = useCallback(async () => {
    try {
      const now = new Date().toISOString();

      // Update localStorage
      localStorage.setItem(CONSENT_STORAGE_KEY, 'denied');
      localStorage.setItem(CONSENT_UPDATED_KEY, now);

      setConsentState({
        consentStatus: 'denied',
        hasDecided: true,
        consentDate: null,
        lastUpdated: now,
      });

      // Optionally notify backend of consent denial
      try {
        await api.post('/analytics/consent', {
          action: 'deny',
          timestamp: now,
        });
      } catch (error) {
        logger.warn('Failed to notify backend of consent denial', error);
      }

      logger.info('Analytics consent denied');
    } catch (error) {
      logger.error('Failed to deny analytics consent', error);
      throw error;
    }
  }, []);

  /**
   * ✅ GDPR COMPLIANT: Withdraw consent (opt-out)
   *
   * Implements GDPR Article 7(3): Consent must be withdrawable as easily as it is given.
   * Implements GDPR Article 17: Right to be forgotten (deletes existing analytics data).
   *
   * This will:
   * 1. Change consent status to denied
   * 2. Notify tracker to stop collecting data
   * 3. Request deletion of existing analytics data from backend
   * 4. Clear any tracking identifiers from localStorage
   */
  const withdrawConsent = useCallback(async () => {
    try {
      const now = new Date().toISOString();

      // Update localStorage
      localStorage.setItem(CONSENT_STORAGE_KEY, 'denied');
      localStorage.setItem(CONSENT_UPDATED_KEY, now);

      setConsentState({
        consentStatus: 'denied',
        hasDecided: true,
        consentDate: null,
        lastUpdated: now,
      });

      // ✅ GDPR: Notify tracker to stop collecting data and clear queue
      try {
        const tracker = getAnalytics();
        tracker.setConsent(false);
      } catch (error) {
        logger.warn('Failed to notify tracker of consent withdrawal', error);
      }

      // ✅ GDPR: Request deletion of existing analytics data
      try {
        await api.delete('/analytics/my-data');
        logger.info('Analytics data deleted per GDPR Article 17');
      } catch (error) {
        logger.warn('Failed to delete analytics data from backend', error);
        // Don't block on backend error
      }

      // Clear any tracking identifiers from localStorage
      const trackingKeys = [
        'ajs_user_id',
        'ajs_anonymous_id',
        'failed_analytics_events',
        'analytics_queue',
      ];
      trackingKeys.forEach(key => {
        try {
          localStorage.removeItem(key);
        } catch {
          // Ignore errors
        }
      });

      logger.info('Analytics consent withdrawn and data cleared');
    } catch (error) {
      logger.error('Failed to withdraw analytics consent', error);
      throw error;
    }
  }, []);

  /**
   * Reset consent (for testing purposes)
   */
  const resetConsent = useCallback(() => {
    localStorage.removeItem(CONSENT_STORAGE_KEY);
    localStorage.removeItem(CONSENT_DATE_KEY);
    localStorage.removeItem(CONSENT_UPDATED_KEY);

    setConsentState({
      consentStatus: 'pending',
      hasDecided: false,
      consentDate: null,
      lastUpdated: null,
    });

    logger.info('Analytics consent reset');
  }, []);

  const value: AnalyticsConsentContextValue = {
    ...consentState,
    grantConsent,
    denyConsent,
    withdrawConsent,
    resetConsent,
  };

  return (
    <AnalyticsConsentContext.Provider value={value}>
      {children}
    </AnalyticsConsentContext.Provider>
  );
};

/**
 * Hook to access analytics consent state and actions
 *
 * @throws Error if used outside AnalyticsConsentProvider
 */
export const useAnalyticsConsent = (): AnalyticsConsentContextValue => {
  const context = useContext(AnalyticsConsentContext);

  if (!context) {
    throw new Error('useAnalyticsConsent must be used within AnalyticsConsentProvider');
  }

  return context;
};

/**
 * Hook to check if analytics tracking is allowed
 * Returns true only if user has granted explicit consent
 */
export const useAnalyticsAllowed = (): boolean => {
  const { consentStatus, hasDecided } = useAnalyticsConsent();
  return hasDecided && consentStatus === 'granted';
};

export default AnalyticsConsentProvider;
