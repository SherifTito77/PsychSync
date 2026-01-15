import React, { useState } from 'react';
import { Check, X, Star } from 'lucide-react';
import './PricingPage.css';

interface PricingTier {
  name: string;
  badge?: string;
  price: string;
  pricePerUser: number;
  minUsers: number;
  maxUsers: number;
  description: string;
  features: Feature[];
  cta: string;
  highlighted?: boolean;
}

interface Feature {
  name: string;
  included: boolean;
  tooltip?: string;
}

const PRICING_TIERS: PricingTier[] = [
  {
    name: 'Starter',
    badge: 'Good',
    price: '$12',
    pricePerUser: 12,
    minUsers: 5,
    maxUsers: 20,
    description: 'For small teams just getting started',
    features: [
      { name: 'Core assessments (Big Five, MBTI-ish)', included: true },
      { name: 'Individual personality reports', included: true },
      { name: 'Team Personality Map', included: true },
      { name: 'Team communication guide', included: true },
      { name: 'Strengths/weaknesses summary', included: true },
      { name: 'PDF exports', included: true },
      { name: 'Conflict Early-Warning', included: false, tooltip: 'Upgrade to Team tier' },
      { name: 'Manager Playbooks', included: false, tooltip: 'Upgrade to Team tier' },
      { name: 'Slack Integration', included: false, tooltip: 'Upgrade to Team tier' },
      { name: 'Priority support', included: false, tooltip: 'Upgrade to Team tier' },
    ],
    cta: 'Start Free Trial',
  },
  {
    name: 'Team',
    badge: 'Best Value',
    price: '$18',
    pricePerUser: 18,
    minUsers: 20,
    maxUsers: 100,
    description: 'For growing companies scaling culture',
    features: [
      { name: 'Everything in Starter', included: true },
      { name: 'Conflict Early-Warning', included: true },
      { name: 'Conflict Dashboard', included: true },
      { name: 'Root Cause Analysis', included: true },
      { name: 'Historical Trends', included: true },
      { name: 'Team Comparison View', included: true },
      { name: 'Manager Playbooks (20+ templates)', included: true },
      { name: 'AI-recommended playbooks', included: true },
      { name: 'Slack Integration', included: true },
      { name: 'Microsoft Teams Integration', included: true },
      { name: 'Priority support (24-hour response)', included: true },
      { name: 'Monthly office hours', included: true },
      { name: 'Custom assessments', included: false, tooltip: 'Upgrade to Enterprise' },
      { name: 'Dedicated CSM', included: false, tooltip: 'Upgrade to Enterprise' },
      { name: 'SSO & SCIM', included: false, tooltip: 'Upgrade to Enterprise' },
    ],
    cta: 'Start Free Trial',
    highlighted: true,
  },
  {
    name: 'Enterprise',
    badge: 'Best',
    price: 'Custom',
    pricePerUser: 0, // Custom pricing
    minUsers: 100,
    maxUsers: -1, // Unlimited
    description: 'For large organizations with complex needs',
    features: [
      { name: 'Everything in Team', included: true },
      { name: 'Custom assessments', included: true },
      { name: 'White-labeling', included: true },
      { name: 'Advanced SSO (SAML 2.0, ADFS)', included: true },
      { name: 'SCIM provisioning', included: true },
      { name: 'Granular permissions (RBAC)', included: true },
      { name: 'Audit logs', included: true },
      { name: 'SOC 2 Type II compliance', included: true },
      { name: 'GDPR/CCPA compliance', included: true },
      { name: 'Dedicated Customer Success Manager', included: true },
      { name: 'Account Manager', included: true },
      { name: '24/7 support with SLA guarantee', included: true },
      { name: 'Quarterly Business Reviews (QBRs)', included: true },
      { name: 'Full REST API access', included: true },
      { name: 'Custom integrations', included: true },
      { name: 'On-premise deployment (optional)', included: true },
    ],
    cta: 'Contact Sales',
  },
];

const ANNUAL_DISCOUNT = 0.2; // 20% discount for annual billing

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('monthly');
  const [userCount, setUserCount] = useState(50);

  const calculatePrice = (tier: PricingTier) => {
    if (tier.name === 'Enterprise') return 'Custom';

    const price = billingPeriod === 'annual'
      ? tier.pricePerUser * 12 * (1 - ANNUAL_DISCOUNT)
      : tier.pricePerUser;

    return Math.round(price * userCount);
  };

  const handleContactSales = () => {
    // TODO: Open sales contact modal or navigate to contact page
    window.location.href = 'mailto:sales@psychsync.io?subject=Enterprise Pricing Inquiry';
  };

  const handleStartTrial = (tier: PricingTier) => {
    // TODO: Navigate to signup page with tier pre-selected
    window.location.href = `/signup?tier=${tier.name.toLowerCase()}`;
  };

  return (
    <div className="pricing-page">
      {/* Hero Section */}
      <div className="pricing-hero">
        <h1>Simple, Transparent Pricing</h1>
        <p className="subtitle">
          Choose the plan that fits your team. All plans include a 14-day free trial.
        </p>

        {/* Billing Toggle */}
        <div className="billing-toggle">
          <button
            className={`toggle-btn ${billingPeriod === 'monthly' ? 'active' : ''}`}
            onClick={() => setBillingPeriod('monthly')}
          >
            Monthly
          </button>
          <button
            className={`toggle-btn ${billingPeriod === 'annual' ? 'active' : ''}`}
            onClick={() => setBillingPeriod('annual')}
          >
            Annual
          </button>
          <span className="discount-badge">Save 20%</span>
        </div>

        {/* User Count Slider (for Team tier) */}
        <div className="user-count-slider">
          <label>Team Size: {userCount} users</label>
          <input
            type="range"
            min="5"
            max="500"
            value={userCount}
            onChange={(e) => setUserCount(parseInt(e.target.value))}
            className="slider"
          />
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="pricing-cards">
        {PRICING_TIERS.map((tier) => (
          <div
            key={tier.name}
            className={`pricing-card ${tier.highlighted ? 'highlighted' : ''}`}
          >
            {tier.badge && (
              <div className="tier-badge">
                {tier.badge === 'Best Value' && <Star className="star-icon" />}
                {tier.badge}
              </div>
            )}

            <div className="card-header">
              <h2>{tier.name}</h2>
              <p className="description">{tier.description}</p>
            </div>

            <div className="price-section">
              <div className="price">
                {tier.name === 'Enterprise' ? (
                  <span className="custom-price">Custom</span>
                ) : (
                  <>
                    <span className="currency">$</span>
                    <span className="amount">{tier.price}</span>
                    <span className="period">/user/month</span>
                  </>
                )}
              </div>
              {tier.name !== 'Enterprise' && (
                <div className="total-price">
                  Total: ${calculatePrice(tier)}/month for {userCount} users
                </div>
              )}
            </div>

            <button
              className={`cta-button ${tier.highlighted ? 'primary' : 'secondary'}`}
              onClick={() => tier.name === 'Enterprise' ? handleContactSales() : handleStartTrial(tier)}
            >
              {tier.cta}
            </button>

            <div className="features">
              {tier.features.map((feature, index) => (
                <div
                  key={index}
                  className={`feature ${feature.included ? 'included' : 'excluded'}`}
                  title={feature.tooltip}
                >
                  {feature.included ? (
                    <Check className="icon included" />
                  ) : (
                    <X className="icon excluded" />
                  )}
                  <span>{feature.name}</span>
                  {!feature.included && tier.badge === 'Best Value' && (
                    <span className="upgrade-hint">→</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* FAQ Section */}
      <div className="pricing-faq">
        <h2>Frequently Asked Questions</h2>

        <div className="faq-item">
          <h3>Can I change plans later?</h3>
          <p>Yes! You can upgrade or downgrade your plan at any time. Prorated adjustments will be applied to your billing.</p>
        </div>

        <div className="faq-item">
          <h3>What happens if my team grows?</h3>
          <p>
            If you exceed your plan's user limit, we'll notify you and you can upgrade to the next tier.
            Your team won't lose access to PsychSync.
          </p>
        </div>

        <div className="faq-item">
          <h3>Is there a free trial?</h3>
          <p>
            Yes! All plans include a 14-day free trial. No credit card required until you're ready to upgrade.
          </p>
        </div>

        <div className="faq-item">
          <h3>What payment methods do you accept?</h3>
          <p>We accept all major credit cards (Visa, Mastercard, American Express) and wire transfers for Enterprise plans.</p>
        </div>
      </div>

      {/* Enterprise CTA */}
      <div className="enterprise-cta">
        <h2>Need a Custom Solution?</h2>
        <p>
          For organizations with 500+ users or custom requirements, our Enterprise team can build a tailored solution for you.
        </p>
        <button className="cta-button primary" onClick={handleContactSales}>
          Contact Enterprise Sales
        </button>
      </div>
    </div>
  );
}
