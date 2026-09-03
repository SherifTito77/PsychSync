// src/types/subscription.ts
// Subscription tier system for PsychSync monetization

export enum SubscriptionTier {
  FREE = 'free',
  PREMIUM = 'premium',
  ENTERPRISE = 'enterprise',
}

export interface SubscriptionPermissions {
  // Assessment limits
  maxAssessmentsPerMonth: number;
  maxTeamAssessmentsPerMonth: number;

  // Features
  canAccessTeamAnalytics: boolean;
  canAccessClinicalTools: boolean;
  canAccessBenchmarking: boolean;
  canAccessPredictiveAnalytics: boolean;
  canUseAPIAccess: boolean;
  canUseIntegrations: boolean;
  canCustomizeAssessments: boolean;
  canWhiteLabel: boolean;

  // Support
  supportLevel: 'community' | 'email' | 'priority' | 'dedicated';

  // Team features
  maxTeamMembers: number;
  canCollaborateOnAssessments: boolean;
  canAccessTeamInsights: boolean;

  // Data & exports
  canExportData: boolean;
  canAccessHistoricalData: boolean; // months of history
  historicalDataLimit: number;
}

export const TIER_CONFIG: Record<SubscriptionTier, {
  name: string;
  price: { monthly: number; annual: number };
  permissions: SubscriptionPermissions;
  features: string[];
}> = {
  [SubscriptionTier.FREE]: {
    name: 'Free',
    price: { monthly: 0, annual: 0 },
    permissions: {
      maxAssessmentsPerMonth: 3,
      maxTeamAssessmentsPerMonth: 0,
      canAccessTeamAnalytics: false,
      canAccessClinicalTools: false,
      canAccessBenchmarking: false,
      canAccessPredictiveAnalytics: false,
      canUseAPIAccess: false,
      canUseIntegrations: false,
      canCustomizeAssessments: false,
      canWhiteLabel: false,
      supportLevel: 'community',
      maxTeamMembers: 1,
      canCollaborateOnAssessments: false,
      canAccessTeamInsights: false,
      canExportData: false,
      canAccessHistoricalData: true,
      historicalDataLimit: 1, // 1 month
    },
    features: [
      '3 personality assessments per month',
      'Basic personality reports',
      'Personal development insights',
      'Community support',
    ],
  },
  [SubscriptionTier.PREMIUM]: {
    name: 'Premium',
    price: { monthly: 29, annual: 290 }, // 2 months free on annual
    permissions: {
      maxAssessmentsPerMonth: -1, // Unlimited
      maxTeamAssessmentsPerMonth: 50,
      canAccessTeamAnalytics: true,
      canAccessClinicalTools: true,
      canAccessBenchmarking: true,
      canAccessPredictiveAnalytics: true,
      canUseAPIAccess: false,
      canUseIntegrations: true,
      canCustomizeAssessments: true,
      canWhiteLabel: false,
      supportLevel: 'priority',
      maxTeamMembers: 25,
      canCollaborateOnAssessments: true,
      canAccessTeamInsights: true,
      canExportData: true,
      canAccessHistoricalData: true,
      historicalDataLimit: 12, // 12 months
    },
    features: [
      'Unlimited assessments',
      'Advanced team analytics',
      'Industry benchmarking',
      'Clinical assessment tools',
      'Predictive hiring analytics',
      'Team collaboration (25 members)',
      'Slack & Email integrations',
      'Priority support',
      '12 months data retention',
    ],
  },
  [SubscriptionTier.ENTERPRISE]: {
    name: 'Enterprise',
    price: { monthly: 99, annual: 990 },
    permissions: {
      maxAssessmentsPerMonth: -1,
      maxTeamAssessmentsPerMonth: -1,
      canAccessTeamAnalytics: true,
      canAccessClinicalTools: true,
      canAccessBenchmarking: true,
      canAccessPredictiveAnalytics: true,
      canUseAPIAccess: true,
      canUseIntegrations: true,
      canCustomizeAssessments: true,
      canWhiteLabel: true,
      supportLevel: 'dedicated',
      maxTeamMembers: -1, // Unlimited
      canCollaborateOnAssessments: true,
      canAccessTeamInsights: true,
      canExportData: true,
      canAccessHistoricalData: true,
      historicalDataLimit: -1, // Unlimited
    },
    features: [
      'Everything in Premium',
      'Unlimited team members',
      'API access',
      'White-label branding',
      'SSO & SCIM provisioning',
      'Dedicated Customer Success Manager',
      'Unlimited data retention',
      'Custom integrations',
      'HIPAA compliance available',
    ],
  },
};

export interface UserSubscription {
  tier: SubscriptionTier;
  billingInterval: 'monthly' | 'annual';
  startDate: string;
  nextBillingDate: string;
  cancelAtPeriodEnd: boolean;
  assessmentsUsedThisMonth: number;
  teamAssessmentsUsedThisMonth: number;
}

// Helper function to check if user can access a feature
export function canAccessFeature(
  subscription: UserSubscription | null,
  feature: keyof SubscriptionPermissions
): boolean {
  if (!subscription) {
    // Default to free tier if no subscription
    return !!TIER_CONFIG[SubscriptionTier.FREE].permissions[feature];
  }

  const tierConfig = TIER_CONFIG[subscription.tier];
  return !!tierConfig.permissions[feature];
}

// Helper function to check if user has hit assessment limit
export function hasHitAssessmentLimit(subscription: UserSubscription | null): boolean {
  if (!subscription) {
    return TIER_CONFIG[SubscriptionTier.FREE].permissions.maxAssessmentsPerMonth <= 3;
  }

  const limit = TIER_CONFIG[subscription.tier].permissions.maxAssessmentsPerMonth;
  if (limit === -1) return false; // Unlimited

  return subscription.assessmentsUsedThisMonth >= limit;
}

// Helper function to get remaining assessments
export function getRemainingAssessments(subscription: UserSubscription | null): number {
  if (!subscription) {
    const limit = TIER_CONFIG[SubscriptionTier.FREE].permissions.maxAssessmentsPerMonth;
    return Math.max(0, limit - 3);
  }

  const limit = TIER_CONFIG[subscription.tier].permissions.maxAssessmentsPerMonth;
  if (limit === -1) return -1; // Unlimited

  return Math.max(0, limit - subscription.assessmentsUsedThisMonth);
}
