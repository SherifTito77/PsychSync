// src/components/subscription/UsageDashboard.tsx
// Usage tracking dashboard for assessment limits and feature usage
import React, { memo } from 'react';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { SubscriptionTier } from '../../types/subscription';
import TierBadge from './FeatureGate';
import UpgradePrompt from './UpgradePrompt';

interface UsageMetricProps {
  label: string;
  used: number;
  limit: number | -1; // -1 = unlimited
  unit?: string;
  icon?: string;
  size?: 'small' | 'medium' | 'large';
}

const UsageMetric: React.FC<UsageMetricProps> = memo(({
  label,
  used,
  limit,
  unit = '',
  icon,
  size = 'medium',
}) => {
  const isUnlimited = limit === -1;
  const percentage = isUnlimited ? 0 : Math.min((used / limit) * 100, 100);
  const isNearLimit = !isUnlimited && percentage >= 80;
  const isAtLimit = !isUnlimited && used >= limit;

  const sizeClasses = {
    small: 'p-3',
    medium: 'p-4',
    large: 'p-6',
  };

  const barColor = isAtLimit ? 'bg-red-500' : isNearLimit ? 'bg-yellow-500' : 'bg-green-500';

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${sizeClasses[size]}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {icon && <span className="text-xl">{icon}</span>}
          <h3 className={`font-medium text-gray-900 ${size === 'large' ? 'text-lg' : 'text-sm'}`}>
            {label}
          </h3>
        </div>
        {!isUnlimited && (
          <span className={`text-sm font-semibold ${isAtLimit ? 'text-red-600' : isNearLimit ? 'text-yellow-600' : 'text-gray-500'}`}>
            {used} / {limit}
            {unit && <span className="ml-1">{unit}</span>}
          </span>
        )}
      </div>

      {isUnlimited ? (
        <div className="flex items-center justify-center py-2">
          <span className="text-green-600 font-semibold">♾️ Unlimited</span>
        </div>
      ) : (
        <>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
            <div
              className={`${barColor} h-2 rounded-full transition-all duration-300`}
              style={{ width: `${percentage}%` }}
            />
          </div>
          {isAtLimit && (
            <p className="text-xs text-red-600 font-medium">
              ⚠️ Limit reached - Upgrade for more
            </p>
          )}
          {isNearLimit && !isAtLimit && (
            <p className="text-xs text-yellow-600 font-medium">
              ⚠️ {limit - used} {unit} remaining
            </p>
          )}
        </>
      )}
    </div>
  );
});

const UsageDashboard: React.FC = () => {
  const { subscription, canAccess, hasHitLimit, getRemaining } = useSubscription();

  if (!subscription) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
        Loading usage information...
      </div>
    );
  }

  const tierConfig = {
    [SubscriptionTier.FREE]: {
      maxAssessments: 3,
      maxTeamAssessments: 0,
      maxTeamMembers: 1,
    },
    [SubscriptionTier.PREMIUM]: {
      maxAssessments: -1,
      maxTeamAssessments: 50,
      maxTeamMembers: 25,
    },
    [SubscriptionTier.ENTERPRISE]: {
      maxAssessments: -1,
      maxTeamAssessments: -1,
      maxTeamMembers: -1,
    },
  };

  const limits = tierConfig[subscription.tier];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Usage Overview</h2>
          <p className="text-gray-600 text-sm mt-1">
            Track your assessment usage and limits
          </p>
        </div>
        <TierBadge tier={subscription.tier} />
      </div>

      {/* Current Tier Info */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6 border border-indigo-200">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">
              Current Plan: {subscription.tier.charAt(0).toUpperCase() + subscription.tier.slice(1)}
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              {subscription.tier === SubscriptionTier.FREE && (
                <>
                  You're on the free plan. Get 3 assessments per month at no cost.
                  Upgrade anytime to unlock unlimited assessments and premium features.
                </>
              )}
              {subscription.tier === SubscriptionTier.PREMIUM && (
                <>
                  You have Premium access with unlimited assessments and 50 team assessments per month.
                  Enjoy advanced analytics and team collaboration features.
                </>
              )}
              {subscription.tier === SubscriptionTier.ENTERPRISE && (
                <>
                  You have Enterprise access with unlimited everything.
                  Contact your CSM for personalized support.
                </>
              )}
            </p>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>
                Next billing: <strong>{new Date(subscription.nextBillingDate).toLocaleDateString()}</strong>
              </span>
              {subscription.cancelAtPeriodEnd && (
                <span className="text-yellow-600 font-medium">
                  ⚠️ Cancels at period end
                </span>
              )}
            </div>
          </div>
          {subscription.tier === SubscriptionTier.FREE && (
            <UpgradePrompt
              feature="maxAssessmentsPerMonth"
              currentTier={subscription.tier}
              size="small"
              variant="card"
            />
          )}
        </div>
      </div>

      {/* Usage Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <UsageMetric
          label="Assessments This Month"
          used={subscription.assessmentsUsedThisMonth}
          limit={limits.maxAssessments}
          unit="assessments"
          icon="📝"
        />

        {canAccess('canAccessTeamInsights') && (
          <UsageMetric
            label="Team Assessments"
            used={subscription.teamAssessmentsUsedThisMonth}
            limit={limits.maxTeamAssessments}
            unit="assessments"
            icon="👥"
          />
        )}

        {canAccess('maxTeamMembers') && limits.maxTeamMembers > 1 && (
          <UsageMetric
            label="Team Members"
            used={5} // TODO: Get actual team member count
            limit={limits.maxTeamMembers}
            unit="members"
            icon="👤"
          />
        )}

        {subscription.tier === SubscriptionTier.FREE && (
          <UsageMetric
            label="Data Retention"
            used={1}
            limit={1}
            unit="month"
            icon="📊"
          />
        )}

        {subscription.tier !== SubscriptionTier.FREE && (
          <UsageMetric
            label="Data Retention"
            used={subscription.tier === SubscriptionTier.PREMIUM ? 6 : 24}
            limit={subscription.tier === SubscriptionTier.PREMIUM ? 12 : -1}
            unit="months"
            icon="📊"
          />
        )}
      </div>

      {/* Feature Access */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Feature Access</h3>
        <div className="space-y-3">
          <FeatureAccessItem
            name="Team Analytics"
            hasAccess={canAccess('canAccessTeamAnalytics')}
            tierRequired="Premium"
          />
          <FeatureAccessItem
            name="Clinical Tools"
            hasAccess={canAccess('canAccessClinicalTools')}
            tierRequired="Premium"
          />
          <FeatureAccessItem
            name="Benchmarking"
            hasAccess={canAccess('canAccessBenchmarking')}
            tierRequired="Premium"
          />
          <FeatureAccessItem
            name="Predictive Analytics"
            hasAccess={canAccess('canAccessPredictiveAnalytics')}
            tierRequired="Premium"
          />
          <FeatureAccessItem
            name="Integrations (Slack, Email)"
            hasAccess={canAccess('canUseIntegrations')}
            tierRequired="Premium"
          />
          <FeatureAccessItem
            name="API Access"
            hasAccess={canAccess('canUseAPIAccess')}
            tierRequired="Enterprise"
          />
          <FeatureAccessItem
            name="White Labeling"
            hasAccess={canAccess('canWhiteLabel')}
            tierRequired="Enterprise"
          />
        </div>
      </div>

      {/* Upgrade CTA for Free Users */}
      {subscription.tier === SubscriptionTier.FREE && hasHitLimit() && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="text-4xl">🚀</div>
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-900 mb-2">
                Ready to Unlock Unlimited Assessments?
              </h3>
              <p className="text-yellow-800 text-sm mb-4">
                Upgrade to Premium and get unlimited assessments, team analytics, clinical tools,
                and much more. Plans start at just $29/month.
              </p>
              <UpgradePrompt
                feature="maxAssessmentsPerMonth"
                currentTier={subscription.tier}
                size="medium"
                variant="card"
              />
            </div>
          </div>
        </div>
      )}

      {/* Billing Info */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Billing Information</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Plan</span>
            <span className="font-medium">{subscription.tier.charAt(0).toUpperCase() + subscription.tier.slice(1)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Billing Cycle</span>
            <span className="font-medium">{subscription.billingInterval.charAt(0).toUpperCase() + subscription.billingInterval.slice(1)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Started</span>
            <span className="font-medium">{new Date(subscription.startDate).toLocaleDateString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Next Billing</span>
            <span className="font-medium">{new Date(subscription.nextBillingDate).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

interface FeatureAccessItemProps {
  name: string;
  hasAccess: boolean;
  tierRequired: string;
}

const FeatureAccessItem: React.FC<FeatureAccessItemProps> = memo(({ name, hasAccess, tierRequired }) => (
  <div className="flex items-center justify-between py-2">
    <span className="text-gray-700">{name}</span>
    {hasAccess ? (
      <span className="flex items-center text-green-600 text-sm font-medium">
        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
        Included
      </span>
    ) : (
      <span className="flex items-center text-gray-500 text-sm">
        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
        {tierRequired} only
      </span>
    )}
  </div>
));

FeatureAccessItem.displayName = 'FeatureAccessItem';

UsageDashboard.displayName = 'UsageDashboard';

export default UsageDashboard;
