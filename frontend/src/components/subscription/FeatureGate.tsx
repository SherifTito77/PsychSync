// src/components/subscription/FeatureGate.tsx
// Reusable components for subscription-based feature gating
import React from 'react';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { SubscriptionTier } from '../../types/subscription';
import UpgradePrompt from './UpgradePrompt';

interface FeatureGateProps {
  feature: keyof import('../../types/subscription').SubscriptionPermissions;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showBlur?: boolean;
}

/**
 * Conditionally renders children based on user's subscription tier
 *
 * @example
 * <FeatureGate feature="canAccessTeamAnalytics">
 *   <TeamAnalyticsDashboard />
 * </FeatureGate>
 */
export const FeatureGate: React.FC<FeatureGateProps> = ({
  feature,
  children,
  fallback,
  showBlur = true,
}) => {
  const { canAccess, subscription } = useSubscription();
  const hasAccess = canAccess(feature);

  if (hasAccess) {
    return <>{children}</>;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  // Default: show blurred content with upgrade prompt
  if (showBlur) {
    return (
      <div className="relative">
        <div className="blur-sm pointer-events-none select-none opacity-50">
          {children}
        </div>
        <div className="absolute inset-0 flex items-center justify-center bg-white/10 backdrop-blur-sm rounded-lg">
          <UpgradePrompt
            feature={feature}
            currentTier={subscription?.tier || SubscriptionTier.FREE}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center p-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
      <UpgradePrompt
        feature={feature}
        currentTier={subscription?.tier || SubscriptionTier.FREE}
      />
    </div>
  );
};

interface AssessmentLimitGateProps {
  children: React.ReactNode;
  onLimitReached?: () => void;
}

/**
 * Gates features based on monthly assessment limit
 *
 * @example
 * <AssessmentLimitGate onLimitReached={() => setShowUpgradeModal(true)}>
 *   <TakeAssessmentButton />
 * </AssessmentLimitGate>
 */
export const AssessmentLimitGate: React.FC<AssessmentLimitGateProps> = ({
  children,
  onLimitReached,
}) => {
  const { hasHitLimit, getRemaining, subscription } = useSubscription();
  const hitLimit = hasHitLimit();
  const remaining = getRemaining();

  if (!hitLimit) {
    return <>{children}</>;
  }

  // Trigger callback if provided
  React.useEffect(() => {
    if (hitLimit && onLimitReached) {
      onLimitReached();
    }
  }, [hitLimit, onLimitReached]);

  return (
    <div className="space-y-4">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
        <div className="text-4xl mb-3">📊</div>
        <h3 className="text-lg font-semibold text-yellow-900 mb-2">
          Assessment Limit Reached
        </h3>
        <p className="text-yellow-700 mb-4">
          {subscription?.tier === SubscriptionTier.FREE
            ? "You've used all 3 free assessments this month. Upgrade to Premium for unlimited access!"
            : "You've reached your monthly assessment limit."}
        </p>
        <UpgradePrompt
          feature="maxAssessmentsPerMonth"
          currentTier={subscription?.tier || SubscriptionTier.FREE}
        />
      </div>

      {remaining > 0 && (
        <p className="text-sm text-gray-600 text-center">
          You have <strong>{remaining} assessment{remaining !== 1 ? 's' : ''}</strong> remaining this month.
        </p>
      )}
    </div>
  );
};

interface TierBadgeProps {
  tier?: SubscriptionTier;
  showLabel?: boolean;
}

/**
 * Displays user's current subscription tier as a badge
 */
export const TierBadge: React.FC<TierBadgeProps> = ({
  tier,
  showLabel = true,
}) => {
  const { subscription } = useSubscription();
  const currentTier = tier || subscription?.tier || SubscriptionTier.FREE;

  const tierColors = {
    [SubscriptionTier.FREE]: 'bg-gray-100 text-gray-800 border-gray-300',
    [SubscriptionTier.PREMIUM]: 'bg-indigo-100 text-indigo-800 border-indigo-300',
    [SubscriptionTier.ENTERPRISE]: 'bg-purple-100 text-purple-800 border-purple-300',
  };

  const tierIcons = {
    [SubscriptionTier.FREE]: '🆓',
    [SubscriptionTier.PREMIUM]: '⭐',
    [SubscriptionTier.ENTERPRISE]: '🏢',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold border ${tierColors[currentTier]}`}
    >
      <span>{tierIcons[currentTier]}</span>
      {showLabel && <span>{currentTier.charAt(0).toUpperCase() + currentTier.slice(1)}</span>}
    </span>
  );
};

export default FeatureGate;
