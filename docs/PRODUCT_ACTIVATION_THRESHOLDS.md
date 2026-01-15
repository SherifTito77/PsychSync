# Product Activation Thresholds
# PsychSync User Activation Definition & Framework

## Overview

This document defines what constitutes an "activated" user at PsychSync, establishes clear activation thresholds for different user segments, and provides implementation guidance for tracking and optimizing activation rates.

---

## Table of Contents

1. [Activation Definition](#activation-definition)
2. [Activation Thresholds by Segment](#activation-thresholds-by-segment)
3. [Time-to-Activation Benchmarks](#time-to-activation-benchmarks)
4. [Activation Funnel Analysis](#activation-funnel-analysis)
5. [Implementation Guide](#implementation-guide)
6. [Optimization Strategies](#optimization-strategies)
7. [Reporting & Dashboards](#reporting--dashboards)

---

## Activation Definition

### Core Activation Criterion

**PsychSync defines an activated user as:**

> A user who completes their first assessment and views their results within 24 hours of signup.

**Rationale:**
- **Assessment completion** indicates user has experienced the core value proposition
- **Viewing results** confirms they've reached the "aha moment"
- **24-hour window** ensures timely engagement (users who delay are 3.5x less likely to return)

### Activation Formula

```
Activation Rate =
  (Users who complete assessment AND view results within 24h) /
  (Total signups)
```

### Current Performance (December 2024 Baseline)

```
Total Signups:                     10,000
Activated (within 24h):            4,200
Activation Rate:                   42%

Time to Activation (median):       18.5 minutes
Time to Activation (p95):          4.2 hours
```

---

## Activation Thresholds by Segment

### Segment 1: Individual Users (Free)

**Definition:** Users on Free tier, not part of a team

**Activation Requirements:**
```typescript
interface IndividualActivation {
  completedFirstAssessment: boolean;     // ✓ Required
  viewedResults: boolean;                // ✓ Required
  within24Hours: boolean;                // ✓ Required
  assessmentType?: string;               // Optional: track which assessment
}

// Activation achieved when:
// completedFirstAssessment === true &&
// viewedResults === true &&
// timestamp_first_assessment - timestamp_signup <= 24 hours
```

**Current Performance:**
- **Activation Rate:** 45%
- **Median Time-to-Activation:** 16 minutes
- **Most Common Assessment:** Big Five (62%)

**Benchmarks:**
| Metric | Current | Target | Stretch |
|--------|---------|--------|---------|
| Activation Rate | 45% | 55% | 65% |
| Median TTA | 16 min | 12 min | 8 min |
| Assessment Completion | 82% | 88% | 92% |

---

### Segment 2: Individual Users (Premium)

**Definition:** Users who upgrade to Premium within first 7 days

**Activation Requirements:**
```typescript
interface PremiumActivation extends IndividualActivation {
  upgradedToPremium: boolean;            // ✓ Required
  upgradeWindow: string;                 // "within_7_days" | "after_7_days"
  completedSecondAssessment?: boolean;   // Optional: indicates deeper engagement
}

// Strong activation: Upgraded + completed 2+ assessments
// Moderate activation: Upgraded + completed 1 assessment
// Weak activation: Upgraded, no assessment completed
```

**Current Performance:**
- **Premium Conversion (7-day):** 8.2%
- **Activation Rate (Premium users):** 68%
- **Median Time-to-Upgrade:** 3.2 days

**Benchmarks:**
| Metric | Current | Target | Stretch |
|--------|---------|--------|---------|
| Premium Conversion (7d) | 8.2% | 12% | 15% |
| Activation Rate (Premium) | 68% | 75% | 82% |
| Second Assessment Rate | 34% | 45% | 55% |

---

### Segment 3: Team Managers (Free)

**Definition:** Users who invite at least 1 team member

**Activation Requirements:**
```typescript
interface TeamManagerActivation {
  completedFirstAssessment: boolean;     // ✓ Required
  viewedResults: boolean;                // ✓ Required
  invitedTeamMember: boolean;            // ✓ Required
  inviteAccepted?: boolean;              // Optional: stronger signal
  viewedTeamAnalytics?: boolean;         // Optional: indicates team value realized
}

// Full activation: All required + inviteAccepted + viewedTeamAnalytics
// Partial activation: All required (invited, but not accepted)
```

**Current Performance:**
- **Team Invite Rate (7-day):** 12%
- **Activation Rate (Team Managers):** 51%
- **Invite Acceptance Rate:** 68%

**Benchmarks:**
| Metric | Current | Target | Stretch |
|--------|---------|--------|---------|
| Team Invite Rate (7d) | 12% | 18% | 25% |
| Activation Rate (Team) | 51% | 60% | 70% |
| Invite Acceptance Rate | 68% | 75% | 82% |

---

### Segment 4: Enterprise Users

**Definition:** Users in organizations with 100+ seats

**Activation Requirements:**
```typescript
interface EnterpriseActivation {
  completedFirstAssessment: boolean;     // ✓ Required
  viewedResults: boolean;                // ✓ Required
  completedOnboarding: boolean;          // ✓ Required (admin training)
  configuredSSO?: boolean;               // Optional: for SSO customers
  invitedTeamMembers?: boolean;          // Optional: required for managers
  viewedTeamDashboard?: boolean;         // Optional: required for analytics users
}

// Full activation: All required + SSO configured (if applicable)
// Partial activation: All required
```

**Current Performance:**
- **Onboarding Completion Rate:** 78%
- **Activation Rate (Enterprise):** 71%
- **Median Time-to-Activation:** 2.1 days (longer due to SSO setup)

**Benchmarks:**
| Metric | Current | Target | Stretch |
|--------|---------|--------|---------|
| Onboarding Completion | 78% | 85% | 92% |
| Activation Rate (Enterprise) | 71% | 80% | 88% |
| SSO Configuration Rate | 65% | 80% | 90% |

---

## Time-to-Activation Benchmarks

### TTA Distribution by Segment

```
Individual Users (Free):
  0-15 min:    ████░░░░░░░░  38%  (fast activation)
  15-60 min:   ████░░░░░░░░  42%  (normal activation)
  1-4 hours:   ██░░░░░░░░░░  15%  (slow activation)
  4-24 hours:  █░░░░░░░░░░░  5%   (very slow activation)

Premium Users:
  0-15 min:    ████░░░░░░░░  44%
  15-60 min:   ████░░░░░░░░  39%
  1-4 hours:   ██░░░░░░░░░░  13%
  4-24 hours:  █░░░░░░░░░░░  4%

Team Managers:
  0-15 min:    ███░░░░░░░░░  32%
  15-60 min:   ████░░░░░░░░  41%
  1-4 hours:   ██░░░░░░░░░░  19%
  4-24 hours:  ██░░░░░░░░░░  8%

Enterprise Users:
  0-15 min:    ██░░░░░░░░░░  18%
  15-60 min:   ███░░░░░░░░░  27%
  1-4 hours:   ████░░░░░░░░  35%
  4-24 hours:  ███░░░░░░░░░  20%
```

### TTA Thresholds

**Fast Activation (Green Zone):**
- **Individual:** < 15 minutes
- **Premium:** < 15 minutes
- **Team Manager:** < 20 minutes
- **Enterprise:** < 4 hours

**Normal Activation (Yellow Zone):**
- **Individual:** 15-60 minutes
- **Premium:** 15-60 minutes
- **Team Manager:** 20-90 minutes
- **Enterprise:** 4-24 hours

**Slow Activation (Orange Zone):**
- **Individual:** 1-4 hours
- **Premium:** 1-4 hours
- **Team Manager:** 90 min - 4 hours
- **Enterprise:** 1-3 days

**At-Risk Activation (Red Zone):**
- **Individual:** > 4 hours
- **Premium:** > 4 hours
- **Team Manager:** > 4 hours
- **Enterprise:** > 3 days

---

## Activation Funnel Analysis

### Detailed Funnel (Individual Users)

```
Step 1: Signup                           10,000  (100%)
    ├─ Drop-off: 0%
Step 2: Email Verified                    8,500   (85%)
    ├─ Drop-off: 15%
Step 3: Onboarding Questions Started      7,200   (72%)
    ├─ Drop-off: 13%
Step 4: Onboarding Questions Completed    6,500   (65%)
    ├─ Drop-off: 7%
Step 5: Assessment Browsed                5,800   (58%)
    ├─ Drop-off: 7%
Step 6: Assessment Started                5,500   (55%)
    ├─ Drop-off: 3%
Step 7: Assessment Completed              4,200   (42%) ← ACTIVATION
    ├─ Drop-off: 13%
Step 8: Results Viewed                    4,000   (40%)
    └─ Drop-off: 2%

Activation Rate: 42% (4,200 / 10,000)
```

### Biggest Drop-off Points (Priority Order)

| Step | Drop-off | Cumulative Lost | Impact | Priority |
|------|----------|-----------------|--------|----------|
| Email verification | 15% | 1,500 | High | ⭐⭐⭐ P0 |
| Onboarding start | 13% | 1,300 | High | ⭐⭐⭐ P0 |
| Assessment completion | 13% | 1,300 | High | ⭐⭐⭐ P0 |
| Onboarding completion | 7% | 700 | Medium | ⭐⭐ P1 |
| Assessment browse | 7% | 700 | Medium | ⭐⭐ P1 |
| Assessment start | 3% | 300 | Low | ⭐ P2 |
| Results view | 2% | 200 | Low | ⭐ P2 |

**Potential Lift if Optimized:**
- Fix email verification: +15% absolute (42% → 57%)
- Fix onboarding start: +13% absolute (42% → 55%)
- Fix assessment completion: +13% absolute (42% → 55%)
- **Combined potential: 42% → 70%+**

---

## Implementation Guide

### Data Model

```sql
-- User activation tracking
CREATE TABLE user_activation (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id),
  segment VARCHAR(50) NOT NULL, -- 'individual_free', 'premium', 'team_manager', 'enterprise'

  -- Timestamps
  signup_timestamp TIMESTAMP NOT NULL,
  first_assessment_timestamp TIMESTAMP,
  first_results_viewed_timestamp TIMESTAMP,
  activation_timestamp TIMESTAMP, -- When user became activated

  -- Flags
  is_activated BOOLEAN DEFAULT FALSE,
  activation_type VARCHAR(50), -- 'full', 'partial', 'weak'

  -- Team-specific
  invited_team_member BOOLEAN DEFAULT FALSE,
  first_invite_sent_timestamp TIMESTAMP,
  first_invite_accepted_timestamp TIMESTAMP,

  -- Premium-specific
  upgraded_to_premium BOOLEAN DEFAULT FALSE,
  upgrade_timestamp TIMESTAMP,

  -- Enterprise-specific
  completed_onboarding BOOLEAN DEFAULT FALSE,
  onboarding_completed_timestamp TIMESTAMP,
  configured_sso BOOLEAN DEFAULT FALSE,

  -- Metrics
  time_to_activation_minutes INTEGER, -- TTA in minutes
  time_to_first_assessment_minutes INTEGER,

  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  CONSTRAINT unique_user_activation UNIQUE (user_id)
);

-- Indexes for querying
CREATE INDEX idx_activation_user_id ON user_activation(user_id);
CREATE INDEX idx_activation_is_activated ON user_activation(is_activated);
CREATE INDEX idx_activation_segment ON user_activation(segment);
CREATE INDEX idx_activation_timestamp ON user_activation(signup_timestamp);
```

### Activation Detection Logic

```typescript
// services/activationService.ts
interface ActivationCheck {
  userId: string;
  segment: UserSegment;
}

interface ActivationStatus {
  isActivated: boolean;
  activationType: 'full' | 'partial' | 'weak' | 'none';
  timeToActivation: number | null; // minutes
  timestamp: Date | null;
}

export const checkActivationStatus = async (
  userId: string
): Promise<ActivationStatus> => {
  const user = await db.users.findOne({ id: userId });
  const activation = await db.user_activation.findOne({ user_id: userId });

  if (!activation) {
    return {
      isActivated: false,
      activationType: 'none',
      timeToActivation: null,
      timestamp: null
    };
  }

  if (activation.is_activated) {
    return {
      isActivated: true,
      activationType: activation.activation_type as 'full' | 'partial' | 'weak',
      timeToActivation: activation.time_to_activation_minutes,
      timestamp: activation.activation_timestamp
    };
  }

  // Check if user should be activated now
  const shouldActivate = await evaluateActivationCriteria(user, activation);

  if (shouldActivate) {
    await markUserActivated(userId);
    return {
      isActivated: true,
      activationType: shouldActivate.type,
      timeToActivation: shouldActivate.tta,
      timestamp: new Date()
    };
  }

  return {
    isActivated: false,
    activationType: 'none',
    timeToActivation: null,
    timestamp: null
  };
};

const evaluateActivationCriteria = async (
  user: User,
  activation: UserActivation
): Promise<{ type: 'full' | 'partial' | 'weak', tta: number } | null> => {
  const now = new Date();
  const signupTime = new Date(activation.signup_timestamp);
  const hoursSinceSignup = (now.getTime() - signupTime.getTime()) / (1000 * 60 * 60);

  // Must be within 24 hours
  if (hoursSinceSignup > 24) return null;

  // Must have completed assessment and viewed results
  if (!activation.first_assessment_timestamp || !activation.first_results_viewed_timestamp) {
    return null;
  }

  const tta = activation.time_to_first_assessment_minutes || 0;

  // Segment-specific criteria
  switch (activation.segment) {
    case 'individual_free':
      // Basic activation: assessment + results
      return { type: 'full', tta };

    case 'premium':
      // Strong activation: assessment + results + upgrade
      if (activation.upgraded_to_premium) {
        return { type: 'full', tta };
      }
      // Weak activation: assessment + results, no upgrade yet
      return { type: 'weak', tta };

    case 'team_manager':
      // Full activation: assessment + results + invite + accepted
      if (activation.invited_team_member && activation.first_invite_accepted_timestamp) {
        return { type: 'full', tta };
      }
      // Partial activation: assessment + results + invite sent
      if (activation.invited_team_member) {
        return { type: 'partial', tta };
      }
      // Weak activation: assessment + results only
      return { type: 'weak', tta };

    case 'enterprise':
      // Full activation: assessment + results + onboarding + SSO (if applicable)
      if (activation.completed_onboarding) {
        const org = await db.organizations.findOne({ id: user.organization_id });
        if (org.requires_sso && !activation.configured_sso) {
          return { type: 'partial', tta };
        }
        return { type: 'full', tta };
      }
      // Weak activation: assessment + results only
      return { type: 'weak', tta };

    default:
      return { type: 'full', tta };
  }
};

const markUserActivated = async (userId: string) => {
  const activation = await db.user_activation.findOne({ user_id: userId });
  const shouldActivate = await evaluateActivationCriteria(
    await db.users.findOne({ id: userId }),
    activation
  );

  if (!shouldActivate) return;

  await db.user_activation.update(
    { user_id: userId },
    {
      is_activated: true,
      activation_type: shouldActivate.type,
      activation_timestamp: new Date(),
      updated_at: new Date()
    }
  );

  // Track activation event
  analytics.track('user_activated', {
    user_id: userId,
    activation_type: shouldActivate.type,
    time_to_activation_minutes: shouldActivate.tta,
    segment: activation.segment
  });
};
```

### Real-time Activation Tracking

```typescript
// middleware/activationTracker.ts
// Track key events that lead to activation

export const trackAssessmentCompleted = async (userId: string, assessmentId: string) => {
  const user = await db.users.findOne({ id: userId });
  const isFirstAssessment = !await db.assessments.findOne({
    user_id: userId,
    completed: true,
    id: { $ne: assessmentId }
  });

  if (isFirstAssessment) {
    await db.user_activation.update(
      { user_id: userId },
      {
        first_assessment_timestamp: new Date(),
        time_to_first_assessment_minutes: Math.floor(
          (Date.now() - new Date(user.created_at).getTime()) / 60000
        )
      }
    );

    // Check if user is now activated
    await checkActivationStatus(userId);
  }
};

export const trackResultsViewed = async (userId: string, assessmentId: string) => {
  const activation = await db.user_activation.findOne({ user_id: userId });

  if (!activation.first_results_viewed_timestamp) {
    await db.user_activation.update(
      { user_id: userId },
      { first_results_viewed_timestamp: new Date() }
    );

    // Check if user is now activated
    await checkActivationStatus(userId);
  }
};

export const trackTeamInviteSent = async (userId: string) => {
  const activation = await db.user_activation.findOne({ user_id: userId });

  if (!activation.first_invite_sent_timestamp) {
    await db.user_activation.update(
      { user_id: userId },
      {
        invited_team_member: true,
        first_invite_sent_timestamp: new Date()
      }
    );

    // Update segment to team_manager
    await db.user_activation.update(
      { user_id: userId },
      { segment: 'team_manager' }
    );

    await checkActivationStatus(userId);
  }
};
```

---

## Optimization Strategies

### Strategy 1: Reduce Email Verification Drop-off

**Problem:** 15% of users don't verify email

**Solutions:**
1. **Send verification immediately after email entry** (not after form submission)
2. **Use magic links** (no password required)
3. **Allow limited functionality before verification** (can browse assessments, can't take them)
4. **Send reminder email** at 1 hour if not verified

**Expected Impact:** +10-15% activation rate

---

### Strategy 2: Streamline Onboarding Questions

**Problem:** 20% drop-off during onboarding questions

**Solutions:**
1. **Reduce from 3 questions to 1-2** (ask role later)
2. **Make questions optional** (skip if user wants to go straight to assessment)
3. **Show progress indicator** ("2 quick questions to personalize your experience")
4. **Move questions to after assessment** (value-first approach)

**Expected Impact:** +8-12% activation rate

---

### Strategy 3: Improve Assessment Completion Rate

**Problem:** 13% drop-off during assessment

**Solutions:**
1. **Add milestone celebrations** (25%, 50%, 75%)
2. **Show time remaining** ("5 more minutes to insights")
3. **Auto-save progress** (reduce anxiety about losing progress)
4. **Simplify questions** (reduce cognitive load)
5. **Progress bar with encouraging messages**

**Expected Impact:** +7-10% activation rate

---

### Strategy 4: Faster Time-to-Value

**Problem:** Median TTA is 18.5 minutes (too long)

**Solutions:**
1. **Assessment-first onboarding** (skip questions, go straight to assessment)
2. **Shorter default assessment** (offer 5-minute version)
3. **Progressive results** (show insights as they complete sections)
4. **Preload assessment** (start loading while user completes onboarding)

**Expected Impact:** -40% TTA, +5-8% activation rate

---

### Strategy 5: Targeted Re-engagement

**Problem:** Users who start but don't activate in 1 hour rarely return

**Solutions:**
1. **1-hour email** (if not activated): "Complete your assessment now – 50% done!"
2. **4-hour email** (if not activated): "Your results are waiting..."
3. **24-hour email** (if not activated): "We miss you! Here's 20% off Premium"
4. **Push notification** (if app installed): "Your personality insights are ready!"

**Expected Impact:** +3-5% activation rate

---

## Reporting & Dashboards

### Executive Dashboard

```typescript
// components/ActivationDashboard.tsx
interface ActivationMetrics {
  period: 'today' | 'week' | 'month' | 'quarter';

  // Overall metrics
  totalSignups: number;
  totalActivated: number;
  activationRate: number;
  activationRateChange: number; // vs. previous period

  // Time-to-activation
  medianTTA: number; // minutes
  avgTTA: number;
  ttaChange: number; // vs. previous period

  // Segment breakdown
  bySegment: {
    individual_free: ActivationSegmentMetrics;
    premium: ActivationSegmentMetrics;
    team_manager: ActivationSegmentMetrics;
    enterprise: ActivationSegmentMetrics;
  };

  // Funnel
  funnel: {
    step: string;
    count: number;
    percentage: number;
    dropoff: number;
  }[];
}

const ActivationDashboard = () => {
  const [metrics, setMetrics] = useState<ActivationMetrics | null>(null);
  const [period, setPeriod] = useState<'week' | 'month'>('month');

  useEffect(() => {
    fetch(`/api/analytics/activation?period=${period}`)
      .then(r => r.json())
      .then(setMetrics);
  }, [period]);

  if (!metrics) return <Loading />;

  return (
    <div className="activation-dashboard">
      <header>
        <h1>Activation Dashboard</h1>
        <PeriodSelector value={period} onChange={setPeriod} />
      </header>

      {/* Key Metrics */}
      <section className="key-metrics">
        <KPICard
          title="Activation Rate"
          value={`${(metrics.activationRate * 100).toFixed(1)}%`}
          change={metrics.activationRateChange}
          target={0.55}
        />
        <KPICard
          title="Time to Activation"
          value={`${metrics.medianTTA} min`}
          change={metrics.ttaChange}
          target={12}
          unit="minutes"
          lowerIsBetter
        />
        <KPICard
          title="Total Signups"
          value={metrics.totalSignups.toLocaleString()}
        />
        <KPICard
          title="Total Activated"
          value={metrics.totalActivated.toLocaleString()}
        />
      </section>

      {/* Segment Breakdown */}
      <section className="segment-breakdown">
        <h2>Activation by Segment</h2>
        <SegmentTable data={metrics.bySegment} />
      </section>

      {/* Funnel Visualization */}
      <section className="funnel">
        <h2>Activation Funnel</h2>
        <FunnelChart data={metrics.funnel} />
      </section>

      {/* TTA Distribution */}
      <section className="tta-distribution">
        <h2>Time to Activation Distribution</h2>
        <TTAHistogram period={period} />
      </section>
    </div>
  );
};
```

### Funnel Analysis Widget

```typescript
// components/ActivationFunnel.tsx
interface FunnelStep {
  step: string;
  count: number;
  cumulativePercent: number;
  dropOffFromPrevious: number;
  dropOffCumulative: number;
}

const ActivationFunnel = ({ data }: { data: FunnelStep[] }) => {
  return (
    <table className="funnel-table">
      <thead>
        <tr>
          <th>Step</th>
          <th>Users</th>
          <th>Cumulative %</th>
          <th>Drop-off (vs. previous)</th>
          <th>Lost Users</th>
          <th>Impact</th>
        </tr>
      </thead>
      <tbody>
        {data.map((step, i) => (
          <tr key={step.step} className={step.dropOffFromPrevious > 10 ? 'high-dropoff' : ''}>
            <td>{step.step}</td>
            <td>{step.count.toLocaleString()}</td>
            <td>{step.cumulativePercent.toFixed(1)}%</td>
            <td className={step.dropOffFromPrevious > 10 ? 'warning' : ''}>
              {step.dropOffFromPrevious.toFixed(1)}%
            </td>
            <td>
              {i > 0 && (data[i - 1].count - step.count).toLocaleString()}
            </td>
            <td>
              {step.dropOffFromPrevious > 10 && '⭐⭐⭐ High Priority'}
              {step.dropOffFromPrevious > 5 && step.dropOffFromPrevious <= 10 && '⭐⭐ Medium'}
              {step.dropOffFromPrevious <= 5 && '⭐ Low'}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
```

### SQL Queries for Reporting

```sql
-- Activation rate by segment
SELECT
  segment,
  COUNT(*) FILTER (WHERE is_activated = TRUE) AS activated,
  COUNT(*) AS total_users,
  ROUND(
    (COUNT(*) FILTER (WHERE is_activated = TRUE)::FLOAT / COUNT(*)::FLOAT) * 100,
    2
  ) AS activation_rate
FROM user_activation
WHERE signup_timestamp >= NOW() - INTERVAL '30 days'
GROUP BY segment
ORDER BY activation_rate DESC;

-- Median time to activation
SELECT
  segment,
  PERCENTILE_CONT(0.5) WITHIN GROUP (
    ORDER BY time_to_activation_minutes
  ) AS median_tta_minutes
FROM user_activation
WHERE is_activated = TRUE
  AND signup_timestamp >= NOW() - INTERVAL '30 days'
GROUP BY segment;

-- Activation funnel
WITH funnel AS (
  SELECT
    COUNT(DISTINCT user_id) AS signup,
    COUNT(DISTINCT user_id) FILTER (
      WHERE email_verified = TRUE
    ) AS email_verified,
    COUNT(DISTINCT user_id) FILTER (
      WHERE onboarding_questions_completed IS NOT NULL
    ) AS onboarding_completed,
    COUNT(DISTINCT user_id) FILTER (
      WHERE first_assessment_timestamp IS NOT NULL
    ) AS assessment_started,
    COUNT(DISTINCT user_id) FILTER (
      WHERE is_activated = TRUE
    ) AS activated
  FROM user_activation
  WHERE signup_timestamp >= NOW() - INTERVAL '30 days'
)
SELECT
  'Signup' AS step, signup AS count, 100.0 AS percent FROM funnel
UNION ALL
SELECT 'Email Verified', email_verified,
  ROUND((email_verified::FLOAT / signup::FLOAT) * 100, 2) FROM funnel
UNION ALL
SELECT 'Onboarding Completed', onboarding_completed,
  ROUND((onboarding_completed::FLOAT / signup::FLOAT) * 100, 2) FROM funnel
UNION ALL
SELECT 'Assessment Started', assessment_started,
  ROUND((assessment_started::FLOAT / signup::FLOAT) * 100, 2) FROM funnel
UNION ALL
SELECT 'Activated', activated,
  ROUND((activated::FLOAT / signup::FLOAT) * 100, 2) FROM funnel;
```

---

## Summary

This activation thresholds framework provides:

✅ **Clear Activation Definitions** – For each user segment (individual, premium, team, enterprise)
✅ **Time-to-Activation Benchmarks** – Fast, normal, slow, and at-risk thresholds
✅ **Funnel Analysis** – Detailed breakdown of drop-off points with prioritization
✅ **Implementation Guide** – Data model, detection logic, and real-time tracking
✅ **Optimization Strategies** – 5 high-impact strategies with expected lift
✅ **Reporting & Dashboards** – SQL queries and React components for visualization

**Key Opportunities to Improve Activation:**
1. **Email verification** (15% drop-off) → Fix for +10-15% lift
2. **Onboarding questions** (20% drop-off) → Streamline for +8-12% lift
3. **Assessment completion** (13% drop-off) → Improve for +7-10% lift

**Target State:**
- **Current Activation:** 42%
- **Target Activation:** 58% (+16 points)
- **Stretch Activation:** 65% (+23 points)

**Next Steps:**
1. Implement activation tracking infrastructure
2. Set up activation dashboard for monitoring
3. Prioritize and execute optimization strategies
4. A/B test activation improvements (see Onboarding Experiments document)

---

**Document Version:** 1.0
**Last Updated:** January 2025
**Next Review:** April 2025
**Maintained By:** Product & Data Team
