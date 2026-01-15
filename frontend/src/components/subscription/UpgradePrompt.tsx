// src/components/subscription/UpgradePrompt.tsx
// Upgrade prompt component with social proof and ROI messaging
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { SubscriptionTier, TIER_CONFIG } from '../../types/subscription';

interface UpgradePromptProps {
  feature?: keyof import('../../types/subscription').SubscriptionPermissions;
  currentTier?: SubscriptionTier;
  size?: 'small' | 'medium' | 'large';
  variant?: 'inline' | 'card' | 'modal';
  onUpgrade?: () => void;
}

const UPGRADE_MESSAGING = {
  canAccessTeamAnalytics: {
    headline: 'Unlock Team Insights',
    description: 'See how your team compares to industry benchmarks',
    socialProof: 'Teams using analytics improved collaboration by 23%',
  },
  canAccessClinicalTools: {
    headline: 'Access Clinical Tools',
    description: 'Professional-grade mental health assessments',
    socialProof: 'Used by 500+ healthcare providers',
  },
  canAccessBenchmarking: {
    headline: 'See Industry Benchmarks',
    description: 'Compare your results to similar organizations',
    socialProof: 'Top-performing teams benchmark weekly',
  },
  canAccessPredictiveAnalytics: {
    headline: 'Predictive Hiring Insights',
    description: 'AI-powered candidate fit predictions',
    socialProof: 'Reduced hiring bias by 40%',
  },
  maxAssessmentsPerMonth: {
    headline: 'Unlimited Assessments',
    description: 'Never hit a limit on your insights',
    socialProof: 'Power users run 50+ assessments monthly',
  },
  default: {
    headline: 'Upgrade Your Plan',
    description: 'Unlock powerful features to accelerate growth',
    socialProof: 'Join 10,000+ organizations growing with PsychSync',
  },
};

const UpgradePrompt: React.FC<UpgradePromptProps> = ({
  feature,
  currentTier = SubscriptionTier.FREE,
  size = 'medium',
  variant = 'card',
  onUpgrade,
}) => {
  const navigate = useNavigate();

  const messaging = feature
    ? UPGRADE_MESSAGING[feature] || UPGRADE_MESSAGING.default
    : UPGRADE_MESSAGING.default;

  const recommendedTier = currentTier === SubscriptionTier.FREE
    ? SubscriptionTier.PREMIUM
    : SubscriptionTier.ENTERPRISE;

  const price = TIER_CONFIG[recommendedTier].price;
  const discount = currentTier === SubscriptionTier.FREE ? '20% off annual billing' : null;

  const handleUpgrade = () => {
    if (onUpgrade) {
      onUpgrade();
    } else {
      navigate('/pricing');
    }
  };

  // Small inline version
  if (variant === 'inline' && size === 'small') {
    return (
      <div className="flex items-center gap-3">
        <button
          onClick={handleUpgrade}
          className="text-sm font-semibold text-indigo-600 hover:text-indigo-700 underline"
        >
          Upgrade to {TIER_CONFIG[recommendedTier].name} →
        </button>
      </div>
    );
  }

  // Card version
  if (variant === 'card') {
    return (
      <div className="bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6 max-w-md">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-indigo-600 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>

          <div className="flex-1">
            <h4 className="text-lg font-bold text-gray-900 mb-1">
              {messaging.headline}
            </h4>
            <p className="text-sm text-gray-600 mb-3">
              {messaging.description}
            </p>

            <div className="flex items-center gap-2 mb-4">
              <span className="text-2xl font-bold text-gray-900">
                ${price.monthly}
              </span>
              <span className="text-gray-500">/month</span>
              {discount && (
                <span className="text-xs font-semibold text-green-600 bg-green-100 px-2 py-1 rounded-full">
                  {discount}
                </span>
              )}
            </div>

            <button
              onClick={handleUpgrade}
              className="w-full bg-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
            >
              Upgrade Now
            </button>

            <p className="text-xs text-gray-500 mt-3 text-center">
              {messaging.socialProof}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Full modal/banner version
  return (
    <div className="text-center space-y-4">
      <div className="text-5xl mb-4">🚀</div>

      <h3 className="text-xl font-bold text-gray-900">
        {messaging.headline}
      </h3>

      <p className="text-gray-600 max-w-md mx-auto">
        {messaging.description}
      </p>

      <div className="bg-white rounded-lg border border-gray-200 p-4 max-w-sm mx-auto">
        <div className="flex items-center justify-between mb-2">
          <span className="text-gray-600">Monthly</span>
          <span className="text-2xl font-bold text-gray-900">
            ${price.monthly}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>Annual (save 16%)</span>
          <span className="font-semibold">
            ${Math.floor(price.annual / 12)}/mo
          </span>
        </div>
      </div>

      <button
        onClick={handleUpgrade}
        className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
      >
        Upgrade to {TIER_CONFIG[recommendedTier].name}
      </button>

      <p className="text-xs text-gray-500">
        {messaging.socialProof}
      </p>
    </div>
  );
};

export default UpgradePrompt;
