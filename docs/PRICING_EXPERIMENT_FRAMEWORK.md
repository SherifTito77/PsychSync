# Pricing Experiment Framework
# A/B Testing and Optimization Strategy

## Overview

This document provides a comprehensive framework for running pricing experiments at PsychSync. Pricing is not set-it-and-forget—it's a lever you should pull regularly to optimize conversion, revenue, and customer satisfaction.

---

## Experiment Categories

### 1. Price Point Testing
- Monthly pricing ($29 vs $39 vs $49)
- Annual discount percentage (16% vs 20% vs 25%)
- Tier pricing (Free/Premium/Enterprise vs Free/Pro/Premium/Enterprise)

### 2. Feature Placement
- What's in Free vs Premium
- Feature gate position in funnel
- Upgrade prompt timing

### 3. Messaging & Copy
- Value proposition phrasing
- Benefit vs feature emphasis
- Social proof wording

### 4. Presentation
- Monthly vs annual default
- Price display order (low to high vs high to low)
- Feature comparison format

### 5. Incentives
- Trial length (7 days vs 14 days vs 30 days)
- Money-back guarantee (30 days vs 60 days)
- Discounts (first month free vs 20% off first month)

---

## Experiment Structure

```typescript
interface PricingExperiment {
  id: string;
  name: string;
  hypothesis: string;
  variant: 'A' | 'B' | 'C';

  // What we're testing
  independentVariable: 'price' | 'features' | 'messaging' | 'presentation';
  changes: PricingChanges;

  // What we're measuring
  metrics: ExperimentMetrics;

  // Targeting
  audience: 'all_visitors' | 'new_users' | 'existing_free_users' | 'canceled_users';
  sampleSize: number;

  // Constraints
  duration: number;  // days
  confidenceLevel: 95 | 99;
  minimumDetectableEffect: number;  // % change

  // Safety rails
  maxChurnIncrease: number;  // % (e.g., 2%)
  maxConversionDecrease: number;  // % (e.g., 10%)

  // Results
  status: 'planned' | 'running' | 'completed' | 'cancelled';
  startDate?: string;
  endDate?: string;
  results?: ExperimentResults;
}

interface PricingChanges {
  price?: {
    monthly: number;
    annual: number;
  };
  features?: string[];
  displayOrder?: 'price_low_to_high' | 'price_high_to_low' | 'popular_first';
  defaultBilling?: 'monthly' | 'annual';
  trialLength?: number;
  guaranteeDays?: number;
  messaging?: {
    headline?: string;
    subheadline?: string;
    cta?: string;
    socialProof?: string;
  };
}
```

---

## Pre-Experiment Checklist

### ✅ Do This Before Launching Any Experiment

#### 1. Define Clear Hypothesis

**Bad Hypothesis:**
```
"We think $39/month might work better than $29/month"
```

**Good Hypothesis:**
```
"We believe increasing the Premium price from $29 to $39/month will
increase MRR by 15% while maintaining a conversion rate > 3%, because
psychology professionals have higher willingness-to-pay than our current
pricing captures, and competitors price similar tools at $49-$99."
```

#### 2. Calculate Sample Size

```typescript
// Use this calculator for A/B test sample size
function calculateSampleSize(
  baselineConversion: number,  // e.g., 5% (0.05)
  minimumDetectableEffect: number,  // e.g., 20% relative change
  confidence: number,  // 95%
  power: number  // 80% (probability of detecting effect if real)
): number {
  // Simplified calculation
  const p1 = baselineConversion;
  const p2 = baselineConversion * (1 + minimumDetectableEffect);

  // For 95% confidence, 80% power, two-tailed test
  // Requires statistical calculation or online calculator
  // Rough estimate: ~1,000 visitors per variant for 5% baseline, 20% effect

  return Math.ceil(sampleSizePerVariant * 2);
}

// Example:
calculateSampleSize(0.05, 0.20, 95, 80);
// Returns: ~2,000 visitors per variant (4,000 total)
```

#### 3. Set Success Criteria

```typescript
interface SuccessCriteria {
  // Primary metrics (must succeed)
  primary: {
    metric: string;
    target: number;
    direction: 'increase' | 'decrease';
    statisticalSignificance: boolean;  // p < 0.05
  }[];

  // Secondary metrics (should succeed)
  secondary: {
    metric: string;
    target: number;
    direction: 'increase' | 'decrease';
    statisticalSignificance?: boolean;
  }[];

  // Guardrail metrics (must not fail)
  guardrails: {
    metric: string;
    threshold: number;
    direction: 'must_not_exceed';
  }[];
}

// Example:
const experimentCriteria: SuccessCriteria = {
  primary: [
    {
      metric: 'MRR',
      target: 15,  // +15%
      direction: 'increase',
      statisticalSignificance: true
    }
  ],
  secondary: [
    {
      metric: 'ARPU',
      target: 25,  // +25%
      direction: 'increase',
      statisticalSignificance: true
    },
    {
      metric: 'free_to_paid_conversion',
      target: 4,  // Must stay above 4%
      direction: 'decrease',
      statisticalSignificance: false
    }
  ],
  guardrails: [
    {
      metric: 'churn_rate',
      threshold: 5,  // Must not exceed 5%
      direction: 'must_not_exceed'
    },
    {
      metric: 'NPS',
      threshold: 40,  // Must not drop below 40
      direction: 'must_not_exceed'
    }
  ]
};
```

#### 4. Implement Analytics

```typescript
// Track experiment exposure and conversion
interface ExperimentEvent {
  eventType: 'exposed' | 'converted' | 'abandoned';
  experimentId: string;
  variant: 'A' | 'B' | 'C';
  userId?: string;
  sessionId: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

// In your pricing page:
useEffect(() => {
  // Track experiment exposure
  analytics.track('experiment_exposed', {
    experimentId: 'price_test_2025_01',
    variant: userVariant,
    sessionId: getSessionId()
  });
}, []);

// On upgrade click:
const handleUpgrade = () => {
  analytics.track('experiment_converted', {
    experimentId: 'price_test_2025_01',
    variant: userVariant,
    sessionId: getSessionId()
  });

  // Navigate to checkout
};
```

---

## Experiment Templates

### Experiment 1: Price Point Test

```typescript
// Test: Does higher price with better positioning increase ARPU?
const pricePointExperiment: PricingExperiment = {
  id: 'price_test_2025_01',
  name: 'Premium Price Point Test - $29 vs $39 vs $49',
  hypothesis: '$39 price with "Professional" positioning will increase MRR by 20%',
  variant: 'A',

  independentVariable: 'price',
  changes: {
    price: { monthly: 39, annual: 390 },
    messaging: {
      headline: 'Professional-Grade Assessment Platform',
      subheadline: 'For HR professionals and team leaders',
      socialProof: 'Trusted by 500+ HR teams'
    }
  },

  metrics: {
    primary: ['MRR', 'ARPU'],
    secondary: ['conversion_rate', 'trial_signups'],
    guardrails: ['churn_rate', 'NPS']
  },

  audience: 'new_users',
  sampleSize: 5000,  // per variant
  duration: 30,  // days
  confidenceLevel: 95,
  minimumDetectableEffect: 20,  // % change in MRR

  maxChurnIncrease: 2,
  maxConversionDecrease: 30,

  status: 'planned'
};
```

### Experiment 2: Free Trial Length Test

```typescript
// Test: Does longer trial increase conversion but reduce urgency?
const trialLengthExperiment: PricingExperiment = {
  id: 'trial_length_2025_01',
  name: 'Free Trial Length - 14 days vs 30 days',
  hypothesis: '30-day trial will increase conversion by 35% despite reduced urgency',
  variant: 'B',

  independentVariable: 'presentation',
  changes: {
    trialLength: 30,
    messaging: {
      headline: '30-Day Free Trial - No Credit Card Required',
      subheadline: 'Experience everything Premium has to offer',
      cta: 'Start Your 30-Day Trial'
    }
  },

  metrics: {
    primary: ['trial_to_paid_conversion', 'MRR'],
    secondary: ['trial_signups', 'time_to_first_value'],
    guardrails: ['trial_abuse_rate', 'support_tickets_per_user']
  },

  audience: 'all_visitors',
  sampleSize: 10000,
  duration: 60,  // days (needs 2 full trial periods)
  confidenceLevel: 95,
  minimumDetectableEffect: 15,

  maxChurnIncrease: 3,
  maxConversionDecrease: 10,

  status: 'planned'
};
```

### Experiment 3: Annual Discount Test

```typescript
// Test: Does larger annual discount increase upfront commitment?
const annualDiscountExperiment: PricingExperiment = {
  id: 'annual_discount_2025_01',
  name: 'Annual Billing Discount - 16% vs 20% vs 25%',
  hypothesis: '20% annual discount (2 months free) will maximize annual plan adoption',
  variant: 'B',

  independentVariable: 'price',
  changes: {
    price: {
      monthly: 29,
      annual: 278  // 20% off ($348 → $278)
    },
    messaging: {
      headline: 'Save 20% with Annual Billing',
      subheadline: 'That\'s 2 months free!',
      cta: 'Choose Annual & Save'
    }
  },

  metrics: {
    primary: ['annual_plan_adoption', 'MRR'],
    secondary: ['LTV', 'churn_rate'],
    guardrails: ['refund_requests', 'cancellations']
  },

  audience: 'new_users',
  sampleSize: 8000,
  duration: 90,  // days (quarterly to see seasonal effects)
  confidenceLevel: 95,
  minimumDetectableEffect: 10,

  maxChurnIncrease: 2,
  maxConversionDecrease: 5,

  status: 'planned'
};
```

### Experiment 4: Anchor Price Test

```typescript
// Test: Does showing Enterprise first make Premium look more affordable?
const anchorPriceExperiment: PricingExperiment = {
  id: 'anchor_price_2025_01',
  name: 'Price Display Order - Low to High vs High to Low',
  hypothesis: 'Showing Enterprise first will increase Premium conversion by 15% (anchor effect)',
  variant: 'B',

  independentVariable: 'presentation',
  changes: {
    displayOrder: 'price_high_to_low',  // Enterprise first
    messaging: {
      // Emphasize Enterprise value to anchor high
      headline: 'Enterprise Solutions',
      socialProof: 'Fortune 500 companies trust PsychSync'
    }
  },

  metrics: {
    primary: ['premium_conversion', 'MRR'],
    secondary: ['enterprise_inquiries', 'average_revenue_per_user'],
    guardrails: ['free_conversion', 'user_confusion']
  },

  audience: 'all_visitors',
  sampleSize: 15000,
  duration: 30,
  confidenceLevel: 95,
  minimumDetectableEffect: 8,

  maxChurnIncrease: 1,
  maxConversionDecrease: 15,

  status: 'planned'
};
```

---

## Experiment Implementation

### 1. A/B Test Setup (Frontend)

```typescript
// src/components/experiments/ExperimentProvider.tsx
import React, { createContext, useContext } from 'react';

interface ExperimentContextType {
  getVariant: (experimentId: string) => 'A' | 'B' | 'C';
  isExperimentActive: (experimentId: string) => boolean;
}

const ExperimentContext = createContext<ExperimentContextType | null>(null);

export const useExperiment = () => {
  const context = useContext(ExperimentContext);
  if (!context) throw new Error('useExperiment must be within ExperimentProvider');
  return context;
};

export const ExperimentProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Get experiments from backend or localStorage
  const [experiments, setExperiments] = useState<Record<string, string>>({});

  useEffect(() => {
    // Fetch active experiments
    fetch('/api/v1/experiments/active')
      .then(res => res.json())
      .then(data => setExperiments(data));
  }, []);

  const getVariant = (experimentId: string): 'A' | 'B' | 'C' => {
    return experiments[experimentId] || 'A';
  };

  const isExperimentActive = (experimentId: string): boolean => {
    return !!experiments[experimentId];
  };

  return (
    <ExperimentContext.Provider value={{ getVariant, isExperimentActive }}>
      {children}
    </ExperimentContext.Provider>
  );
};
```

### 2. Pricing Page with Experiments

```typescript
// src/pages/Pricing.tsx with experiment integration
const Pricing: React.FC = () => {
  const { getVariant } = useExperiment();
  const variant = getVariant('price_test_2025_01');

  // Variant-specific pricing
  const pricing = {
    A: { premium: { monthly: 29, annual: 290 } },
    B: { premium: { monthly: 39, annual: 390 } },
    C: { premium: { monthly: 49, annual: 490 } }
  };

  const currentPricing = pricing[variant];

  return (
    <PricingTable
      prices={currentPricing}
      variant={variant}
      onUpgrade={(tier) => {
        analytics.track('pricing_upgrade_clicked', {
          variant,
          tier,
          experimentId: 'price_test_2025_01'
        });
      }}
    />
  );
};
```

### 3. Backend Experiment Configuration

```python
# app/api/v1/routes/experiments.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import random

router = APIRouter()

@router.get("/active")
async def get_active_experiments(
    db: AsyncSession = Depends(get_db)
):
    """Return active experiments for current user"""
    experiments = {
        "price_test_2025_01": {
            "enabled": True,
            "variants": ["A", "B", "C"],
            "allocation": [0.34, 0.33, 0.33],  # Percent per variant
            "target_audience": "new_users"
        },
        "trial_length_2025_01": {
            "enabled": True,
            "variants": ["A", "B"],
            "allocation": [0.5, 0.5],
            "target_audience": "all_visitors"
        }
    }

    # Assign variant based on user hash (consistent)
    user_id = get_current_user_id()
    for exp_id, config in experiments.items():
        variant = assign_variant(user_id, config["allocation"])
        experiments[exp_id]["variant"] = variant

    return experiments

def assign_variant(user_id: str, allocation: list) -> str:
    """Consistently assign variant based on user hash"""
    hash_value = hash(user_id) % 100
    cumulative = 0
    for i, percentage in enumerate(allocation):
        cumulative += percentage * 100
        if hash_value < cumulative:
            return chr(65 + i)  # 'A', 'B', 'C', etc.
    return 'A'  # Default
```

---

## Analyzing Results

### Statistical Significance Calculator

```typescript
interface ExperimentResults {
  experimentId: string;
  variants: {
    [key: string]: {
      visitors: number;
      conversions: number;
      conversionRate: number;
      revenue: number;
    };
  };
  winner: string;
  confidence: number;
  improvement: number;
  isSignificant: boolean;
}

function calculateSignificance(
  controlConversions: number,
  controlVisitors: number,
  treatmentConversions: number,
  treatmentVisitors: number
): { pValue: number; isSignificant: boolean; confidence: number } {
  // Z-test for two proportions
  const p1 = controlConversions / controlVisitors;
  const p2 = treatmentConversions / treatmentVisitors;
  const pooledP = (controlConversions + treatmentConversions) / (controlVisitors + treatmentVisitors);
  const se = Math.sqrt(pooledP * (1 - pooledP) * (1/controlVisitors + 1/treatmentVisitors));
  const z = (p2 - p1) / se;

  // Convert z to p-value (two-tailed)
  const pValue = 2 * (1 - normalCDF(Math.abs(z)));

  return {
    pValue,
    isSignificant: pValue < 0.05,
    confidence: (1 - pValue) * 100
  };
}
```

### Post-Experiment Analysis Template

```typescript
interface ExperimentReport {
  // Metadata
  experimentId: string;
  name: string;
  dates: { start: string; end: string };
  duration: number;

  // Results
  winner: 'A' | 'B' | 'C' | 'inconclusive';
  winningVariant: PricingChanges;
  metrics: {
    primary: ExperimentMetricResults;
    secondary: ExperimentMetricResults;
    guardrails: GuardrailResults;
  };

  // Business Impact
  projectedAnnualImpact: number;
  confidence: number;

  // Recommendation
  recommendation: 'implement' | 'continue' | 'abandon' | 'modify_and_retest';
  rationale: string;

  // Learnings
  insights: string[];
  surprises: string[];
  nextExperiments: string[];
}
```

---

## Experiment Calendar

### Q1 2025 Experiment Schedule

| Month | Experiment | Target | Primary Metric |
|-------|-----------|--------|----------------|
| Jan | Price Point ($29 vs $39) | New users | MRR |
| Feb | Trial Length (14 vs 30 days) | All users | Trial → Paid |
| Mar | Annual Discount (16% vs 20%) | New users | Annual Adoption |

### Q2 2025 Experiment Schedule

| Month | Experiment | Target | Primary Metric |
|-------|-----------|--------|----------------|
| Apr | Anchor Price (display order) | All users | Premium Conversion |
| May | Feature Gate Position (soft vs hard) | Free users | Upgrade Rate |
| Jun | Messaging (features vs benefits) | All users | Conversion Rate |

---

## Guardrails & Safety

### Automatic Stop Conditions

```typescript
// Check these DAILY during experiment
interface SafetyCheck {
  condition: string;
  threshold: number;
  action: 'continue' | 'stop_immediately' | 'warn_team';
}

const safetyChecks: SafetyCheck[] = [
  {
    condition: 'Conversion rate drop > 30%',
    threshold: 30,
    action: 'stop_immediately'
  },
  {
    condition: 'Churn rate increase > 2%',
    threshold: 2,
    action: 'stop_immediately'
  },
  {
    condition: 'NPS drop > 15 points',
    threshold: 15,
    action: 'warn_team'
  },
  {
    condition: 'Enterprise complaint > 3',
    threshold: 3,
    action: 'stop_immediately'
  },
  {
    condition: 'Revenue decline > 10%',
    threshold: 10,
    action: 'stop_immediately'
  }
];
```

### Daily Monitoring Dashboard

```typescript
// Monitor these metrics daily during experiments
interface ExperimentDashboard {
  date: string;
  experimentId: string;

  // Funnel metrics
  visitors_per_variant: Record<string, number>;
  signups_per_variant: Record<string, number>;
  conversions_per_variant: Record<string, number>;

  // Revenue metrics
  mrr_per_variant: Record<string, number>;
  arr_per_variant: Record<string, number>;

  // Quality metrics
  refund_rate: Record<string, number>;
  support_tickets: Record<string, number>;
  nps: Record<string, number>;

  // Safety status
  safety_status: 'green' | 'yellow' | 'red';
  alert_triggered: boolean;
  recommended_action?: string;
}
```

---

## Common Pitfalls to Avoid

### ❌ Don't: Test Too Many Variables at Once

```typescript
// BAD: Testing everything at once
const badExperiment = {
  changes: {
    price: { monthly: 39 },
    features: ['api', 'white-label'],
    messaging: { headline: 'New!' },
    trialLength: 30
  }
};
// Problem: If conversion changes, which variable caused it?
```

```typescript
// GOOD: Test one variable at a time
const goodExperiment = {
  changes: {
    price: { monthly: 39 }
    // Keep everything else constant
  }
};
```

### ❌ Don't: Run Experiments During Seasonal Peaks

```
AVOID testing during:
- December (holidays, budgets frozen)
- January (New Year resolutions - unique behavior)
- Quarter ends (budget cycles)
- Industry conference weeks

INSTEAD: Test during "normal" periods (Feb, March, June, July, Sept, Oct)
```

### ❌ Don't: Ignore Statistical Significance

```typescript
// BAD: Declaring winner too early
Variant B: 12 conversions from 100 visitors (12%)
Variant A: 10 conversions from 100 visitors (10%)
→ "B wins! 🎉" WRONG

// GOOD: Wait for significance
Required sample size at 12% baseline: ~600 visitors
Run until both variants have 600+ visitors, then check p-value
```

---

## Experiment Playbook

### Step 1: Hypothesis Workshop (Week 1)

```
Gather: Product, Engineering, Data Science
Agenda:
1. Review current metrics (conversion, ARPU, churn)
2. Brainstorm pricing hypotheses
3. Prioritize by impact vs effort
4. Select 1-2 experiments for next quarter
```

### Step 2: Design Experiment (Week 2)

```
For each hypothesis:
1. Define control and variants
2. Calculate sample size
3. Set success criteria
4. Implement tracking
5. Create experiment ticket
```

### Step 3: Launch (Week 3-X)

```
1. Deploy to production with feature flags
2. Monitor daily for first week
3. Review safety checks
4. Adjust if guardrails triggered
```

### Step 4: Analyze & Decide (Week X+1)

```
1. Compile results
2. Calculate statistical significance
3. Review guardrail metrics
4. Make decision: ship, revert, or extend
5. Document learnings
```

---

## Pricing Experiment Examples from Real Companies

### Dropbox (2014): Dropbox for Business Pricing

**Hypothesis:** Enterprise pricing was too low, leaving money on table.

**Experiment:** Increased prices by ~40%

**Result:** MRR increased 35%, churn didn't change significantly

**Learning:** Enterprise customers are less price-sensitive than expected

### Buffer (2016): Pricing Restructure

**Hypothesis:** Simpler pricing with fewer tiers would increase conversions.

**Experiment:** Went from 8 tiers to 3 tiers

**Result:** Conversion increased 20%, confusion decreased significantly

**Learning:** Choice paralysis is real in pricing

### Slack (2017): Free Tier Limitations

**Hypothesis:** Limiting free tier message history would increase paid conversions.

**Experiment:** 10,000 message limit on free tier

**Result:** 10% increase in paid signups, minimal backlash

**Learning**: Free users need a "push" to upgrade, but not too hard

---

## Summary

**Key Principles:**

1. **Test One Variable at a Time** - Isolate cause and effect
2. **Calculate Sample Size First** - Don't stop early
3. **Set Guardrails** - Protect key metrics
4. **Monitor Daily** - Catch issues early
5. **Document Learnings** - Build institutional knowledge

**Experiment Frequency:**
- Run 1-2 experiments per quarter
- Each experiment lasts 30-90 days
- Always have control group (A/B testing)

**Success Rate Expectation:**
- 30% of experiments will show positive results
- 30% will show no difference
- 40% will have negative results (this is learning!)

**The goal isn't to be right all the time. The goal is to learn continuously.**
