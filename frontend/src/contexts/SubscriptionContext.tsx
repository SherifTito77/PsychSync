// src/contexts/SubscriptionContext.tsx
// Context for managing user subscription state and tier checks
import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, ReactNode } from 'react';
import {
  SubscriptionTier,
  UserSubscription,
  SubscriptionPermissions,
  canAccessFeature,
  hasHitAssessmentLimit,
  getRemainingAssessments,
} from '../types/subscription';

interface SubscriptionContextType {
  subscription: UserSubscription | null;
  isLoading: boolean;
  error: string | null;
  canAccess: (feature: keyof SubscriptionPermissions) => boolean;
  hasHitLimit: () => boolean;
  getRemaining: () => number;
  upgradeTier: (newTier: SubscriptionTier) => Promise<void>;
  refreshSubscription: () => Promise<void>;
  showUpgradePrompt: boolean;
  setShowUpgradePrompt: (show: boolean) => void;
}

const SubscriptionContext = createContext<SubscriptionContextType | undefined>(undefined);

interface SubscriptionProviderProps {
  children: ReactNode;
}

export const SubscriptionProvider: React.FC<SubscriptionProviderProps> = ({ children }) => {
  const [subscription, setSubscription] = useState<UserSubscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpgradePrompt, setShowUpgradePrompt] = useState(false);

  // Fetch subscription from backend
  const refreshSubscription = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Check if user is authenticated first
      const userData = localStorage.getItem('user');
      if (!userData) {
        // No user logged in - set subscription to null
        setSubscription(null);
        setIsLoading(false);
        return;
      }

      const user = JSON.parse(userData);

      // TODO: Replace with actual API call to /api/v1/subscription
      // For now, give logged-in users access to all features
      // This prevents the upgrade popup from showing to authenticated users
      const mockSubscription: UserSubscription = {
        tier: SubscriptionTier.ENTERPRISE, // Give logged-in users full access
        billingInterval: 'monthly',
        startDate: new Date().toISOString(),
        nextBillingDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        cancelAtPeriodEnd: false,
        assessmentsUsedThisMonth: 0,
        teamAssessmentsUsedThisMonth: 0,
      };

      setSubscription(mockSubscription);
    } catch (err) {
      console.error('Failed to fetch subscription:', err);
      // On error, use mock data as fallback
      const mockSubscription: UserSubscription = {
        tier: SubscriptionTier.ENTERPRISE, // Give logged-in users full access
        billingInterval: 'monthly',
        startDate: new Date().toISOString(),
        nextBillingDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        cancelAtPeriodEnd: false,
        assessmentsUsedThisMonth: 0,
        teamAssessmentsUsedThisMonth: 0,
      };
      setSubscription(mockSubscription);
      setError('Failed to load subscription information');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load subscription on mount
  useEffect(() => {
    refreshSubscription();
  }, [refreshSubscription]);

  // Check if user can access a feature
  const canAccess = useCallback(
    (feature: keyof SubscriptionPermissions): boolean => {
      return canAccessFeature(subscription, feature);
    },
    [subscription]
  );

  // Check if user has hit assessment limit
  const hasHitLimit = useCallback((): boolean => {
    return hasHitAssessmentLimit(subscription);
  }, [subscription]);

  // Get remaining assessments
  const getRemaining = useCallback((): number => {
    return getRemainingAssessments(subscription);
  }, [subscription]);

  // ✅ MEMOIZED: setShowUpgradePrompt for consistent reference
  const setShowUpgradePromptCallback = useCallback((show: boolean) => {
    setShowUpgradePrompt(show);
  }, []);

  // Upgrade tier (call payment flow)
  const upgradeTier = useCallback(async (newTier: SubscriptionTier) => {
    try {
      // TODO: Integrate with payment provider (Stripe, etc.)
      console.log('Initiating upgrade to:', newTier);

      // For now, just update the local state
      if (subscription) {
        setSubscription({
          ...subscription,
          tier: newTier,
        });
      }

      setShowUpgradePrompt(false);
    } catch (err) {
      console.error('Failed to upgrade subscription:', err);
      throw err;
    }
  }, [subscription]);

  // ✅ MEMOIZED: Context value only changes when dependencies change
  const value: SubscriptionContextType = useMemo(() => ({
    subscription,
    isLoading,
    error,
    canAccess,
    hasHitLimit,
    getRemaining,
    upgradeTier,
    refreshSubscription,
    showUpgradePrompt,
    setShowUpgradePrompt: setShowUpgradePromptCallback,
  }), [subscription, isLoading, error, canAccess, hasHitLimit, getRemaining, upgradeTier, refreshSubscription, showUpgradePrompt, setShowUpgradePromptCallback]);

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
};

// Custom hook to use subscription context
export const useSubscription = (): SubscriptionContextType => {
  const context = useContext(SubscriptionContext);
  if (context === undefined) {
    throw new Error('useSubscription must be used within a SubscriptionProvider');
  }
  return context;
};
