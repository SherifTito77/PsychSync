// src/components/subscription/PricingTable.tsx
// Comprehensive pricing comparison table for upgrade journey
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SubscriptionTier, TIER_CONFIG } from '../../types/subscription';
import { useSubscription } from '../../contexts/SubscriptionContext';
import TierBadge from './FeatureGate';

interface PricingTableProps {
  highlightTier?: SubscriptionTier;
  onUpgrade?: (tier: SubscriptionTier) => void;
}

const PricingTable: React.FC<PricingTableProps> = ({
  highlightTier = SubscriptionTier.PREMIUM,
  onUpgrade,
}) => {
  const navigate = useNavigate();
  const { subscription } = useSubscription();
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'annual'>('monthly');

  const handleUpgrade = (tier: SubscriptionTier) => {
    if (onUpgrade) {
      onUpgrade(tier);
    } else {
      // TODO: Redirect to checkout
      console.log('Navigate to checkout for:', tier);
      navigate('/checkout', { state: { tier, billingInterval } });
    }
  };

  const currentTier = subscription?.tier || SubscriptionTier.FREE;

  const features = [
    { key: 'assessments', label: 'Assessments', free: '3/mo', premium: 'Unlimited', enterprise: 'Unlimited' },
    { key: 'team', label: 'Team Members', free: '1', premium: '25', enterprise: 'Unlimited' },
    { key: 'analytics', label: 'Team Analytics', free: false, premium: true, enterprise: true },
    { key: 'benchmarking', label: 'Industry Benchmarking', free: false, premium: true, enterprise: true },
    { key: 'clinical', label: 'Clinical Tools', free: false, premium: true, enterprise: true },
    { key: 'predictive', label: 'Predictive Analytics', free: false, premium: true, enterprise: true },
    { key: 'api', label: 'API Access', free: false, premium: false, enterprise: true },
    { key: 'whitelabel', label: 'White Labeling', free: false, premium: false, enterprise: true },
    { key: 'integrations', label: 'Integrations (Slack, Email)', free: false, premium: true, enterprise: true },
    { key: 'support', label: 'Support', free: 'Community', premium: 'Priority', enterprise: 'Dedicated CSM' },
    { key: 'history', label: 'Data Retention', free: '1 month', premium: '12 months', enterprise: 'Unlimited' },
    { key: 'export', label: 'Data Export', free: false, premium: true, enterprise: true },
  ];

  const getTierButton = (tier: SubscriptionTier) => {
    if (tier === currentTier) {
      return (
        <button
          disabled
          className="w-full py-3 px-4 rounded-lg font-semibold bg-gray-100 text-gray-500 cursor-not-allowed"
        >
          Current Plan
        </button>
      );
    }

    if (tier === SubscriptionTier.FREE) {
      return (
        <button
          disabled
          className="w-full py-3 px-4 rounded-lg font-semibold border border-gray-300 text-gray-400 cursor-not-allowed"
        >
          Downgrade
        </button>
      );
    }

    const isHighlighted = tier === highlightTier;
    const price = TIER_CONFIG[tier].price[billingInterval];

    return (
      <button
        onClick={() => handleUpgrade(tier)}
        className={`w-full py-3 px-4 rounded-lg font-semibold transition-all ${
          isHighlighted
            ? 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg'
            : 'bg-white text-gray-900 border-2 border-gray-200 hover:border-indigo-600'
        }`}
      >
        Upgrade to {TIER_CONFIG[tier].name}
      </button>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Choose Your Growth Plan
        </h2>
        <p className="text-lg text-gray-600 mb-8">
          Start free, upgrade when you're ready to scale
        </p>

        {/* Billing Toggle */}
        <div className="inline-flex items-center bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setBillingInterval('monthly')}
            className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
              billingInterval === 'monthly'
                ? 'bg-white text-gray-900 shadow'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingInterval('annual')}
            className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
              billingInterval === 'annual'
                ? 'bg-white text-gray-900 shadow'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Annual
          </button>
        </div>
        {billingInterval === 'annual' && (
          <p className="text-sm text-green-600 mt-3 font-semibold">
            💰 Save 16% with annual billing (2 months free!)
          </p>
        )}
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
        {Object.values(SubscriptionTier).map((tier) => {
          const config = TIER_CONFIG[tier];
          const price = config.price[billingInterval];
          const isHighlighted = tier === highlightTier;

          return (
            <div
              key={tier}
              className={`relative rounded-2xl p-8 ${
                isHighlighted
                  ? 'bg-gradient-to-br from-indigo-600 to-purple-600 text-white shadow-2xl scale-105'
                  : 'bg-white border-2 border-gray-200'
              }`}
            >
              {isHighlighted && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-yellow-400 text-yellow-900 text-sm font-bold px-4 py-1 rounded-full">
                    MOST POPULAR
                  </span>
                </div>
              )}

              <div className="text-center mb-6">
                <div className="text-4xl mb-3">
                  {tier === SubscriptionTier.FREE ? '🆓' : tier === SubscriptionTier.PREMIUM ? '⭐' : '🏢'}
                </div>
                <h3 className={`text-2xl font-bold mb-2 ${isHighlighted ? 'text-white' : 'text-gray-900'}`}>
                  {config.name}
                </h3>
                <div className="mb-4">
                  <span className={`text-4xl font-bold ${isHighlighted ? 'text-white' : 'text-gray-900'}`}>
                    ${price}
                  </span>
                  <span className={`text-lg ${isHighlighted ? 'text-indigo-100' : 'text-gray-500'}`}>
                    /month
                  </span>
                </div>
              </div>

              {getTierButton(tier)}

              <ul className="mt-8 space-y-4">
                {config.features.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <svg
                      className={`w-5 h-5 mr-3 flex-shrink-0 ${
                        isHighlighted ? 'text-indigo-200' : 'text-green-500'
                      }`}
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className={`text-sm ${isHighlighted ? 'text-indigo-50' : 'text-gray-600'}`}>
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>

      {/* Feature Comparison Table */}
      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Feature Comparison
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Feature
                </th>
                <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                  Free
                </th>
                <th className="px-6 py-3 text-center text-sm font-semibold text-indigo-600">
                  Premium
                </th>
                <th className="px-6 py-3 text-center text-sm font-semibold text-purple-600">
                  Enterprise
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {features.map((feature) => (
                <tr key={feature.key} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">
                    {feature.label}
                  </td>
                  <td className="px-6 py-4 text-center text-sm text-gray-600">
                    {typeof feature.free === 'boolean' ? (
                      feature.free ? (
                        <svg className="w-5 h-5 mx-auto text-green-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 mx-auto text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      )
                    ) : (
                      feature.free
                    )}
                  </td>
                  <td className="px-6 py-4 text-center text-sm text-gray-600">
                    {typeof feature.premium === 'boolean' ? (
                      feature.premium ? (
                        <svg className="w-5 h-5 mx-auto text-green-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 mx-auto text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      )
                    ) : (
                      feature.premium
                    )}
                  </td>
                  <td className="px-6 py-4 text-center text-sm text-gray-600">
                    {typeof feature.enterprise === 'boolean' ? (
                      feature.enterprise ? (
                        <svg className="w-5 h-5 mx-auto text-green-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 mx-auto text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      )
                    ) : (
                      feature.enterprise
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="mt-16">
        <h3 className="text-2xl font-bold text-gray-900 text-center mb-8">
          Frequently Asked Questions
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gray-50 rounded-lg p-6">
            <h4 className="font-semibold text-gray-900 mb-2">
              Can I change plans later?
            </h4>
            <p className="text-sm text-gray-600">
              Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately.
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-6">
            <h4 className="font-semibold text-gray-900 mb-2">
              What happens when I hit my free limit?
            </h4>
            <p className="text-sm text-gray-600">
              You'll see a friendly prompt to upgrade. Your data is always safe, and you can continue when you upgrade.
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-6">
            <h4 className="font-semibold text-gray-900 mb-2">
              Is there a free trial for Premium?
            </h4>
            <p className="text-sm text-gray-600">
              Yes! Start with 14 days of Premium access. No credit card required.
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-6">
            <h4 className="font-semibold text-gray-900 mb-2">
              Do you offer discounts for nonprofits?
            </h4>
            <p className="text-sm text-gray-600">
              Absolutely! Contact us for special pricing for nonprofits, education, and healthcare organizations.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingTable;
