# Churn Prediction Signals & Triggers
# PsychSync Customer Retention & Churn Prevention System

## Overview

This document provides a comprehensive framework for predicting customer churn through behavioral signals, usage patterns, and engagement metrics. Includes automated triggers, intervention workflows, and retention playbooks.

---

## Table of Contents

1. [Churn Prediction Framework](#churn-prediction-framework)
2. [Behavioral Signals](#behavioral-signals)
3. [Usage-Based Signals](#usage-based-signals)
4. [Sentiment Signals](#sentiment-signals)
5. [Risk Scoring Model](#risk-scoring-model)
6. [Intervention Triggers](#intervention-triggers)
7. [Retention Playbooks](#retention-playbooks)
8. [Implementation Guide](#implementation-guide)

---

## Churn Prediction Framework

### Definition

**Churn**: A customer who cancels their subscription or downgrades from a paid tier to free.

**Churn Prediction**: Identifying customers likely to churn within the next 30 days based on behavioral patterns and engagement signals.

### Prediction Goals

```
Target Metrics:
- Predict churn 30 days in advance
- Achieve 70%+ precision (minimize false positives)
- Achieve 60%+ recall (catch most churn risks)
- Reduce churn rate by 20% through interventions
```

### Risk Categories

| Risk Level | Churn Probability | Action Required |
|------------|-------------------|-----------------|
| **Critical** | 80-100% | Immediate intervention (within 24h) |
| **High** | 60-79% | Active outreach (within 72h) |
| **Medium** | 40-59% | Automated nurturing (within 1 week) |
| **Low** | 20-39% | Monitor and track |
| **Safe** | 0-19% | No action needed |

---

## Behavioral Signals

### Signal 1: Usage Decline

**Definition:** Sustained decrease in product usage over time.

**Metrics:**
```typescript
interface UsageDeclineSignal {
  // Assessment completion rate
  assessments_last_30_days: number;
  assessments_previous_30_days: number;
  decline_percentage: number;

  // Session frequency
  sessions_last_30_days: number;
  avg_sessions_previous_months: number;
  session_decline_percentage: number;

  // Feature usage
  features_used_last_30_days: number;
  avg_features_used_previous_months: number;

  // Risk thresholds
  is_declining: boolean;
  risk_score: number; // 0-100
}

// Calculation
const calculateUsageDecline = (user: User): UsageDeclineSignal => {
  const last30 = getUsageData(user.id, 30);
  const previous30 = getUsageData(user.id, 60, 30);

  const assessmentDecline =
    ((previous30.assessments - last30.assessments) / previous30.assessments) * 100;

  const sessionDecline =
    ((previous30.sessions - last30.sessions) / previous30.sessions) * 100;

  // High-risk thresholds
  const isDeclining =
    assessmentDecline > 50 || // 50%+ fewer assessments
    sessionDecline > 40 ||     // 40%+ fewer sessions
    last30.assessments === 0;   // No assessments at all

  const riskScore = isDeclining
    ? Math.max(assessmentDecline, sessionDecline)
    : 0;

  return {
    assessments_last_30_days: last30.assessments,
    assessments_previous_30_days: previous30.assessments,
    decline_percentage: Math.max(assessmentDecline, sessionDecline),
    sessions_last_30_days: last30.sessions,
    avg_sessions_previous_months: previous30.sessions,
    session_decline_percentage: sessionDecline,
    features_used_last_30_days: last30.uniqueFeatures,
    avg_features_used_previous_months: previous30.uniqueFeatures,
    is_declining: isDeclining,
    risk_score: Math.min(riskScore, 100)
  };
};
```

**Risk Levels:**
- **Critical:** No usage for 14+ days
- **High:** 70%+ usage decline
- **Medium:** 40-69% usage decline
- **Low:** 20-39% usage decline

---

### Signal 2: Feature Adoption Stagnation

**Definition:** User has stopped exploring new features or using advanced capabilities.

**Metrics:**
```typescript
interface AdoptionStagnationSignal {
  // Feature exploration
  days_since_new_feature_used: number;
  new_features_tried: number;
  total_available_features: number;
  adoption_rate: number;

  // Core vs. advanced features
  uses_core_features_only: boolean;
  advanced_features_used: string[];

  // Team features (if applicable)
  invited_team_members: boolean;
  viewed_team_analytics: boolean;

  // Risk assessment
  is_stagnating: boolean;
  risk_score: number;
}

const calculateAdoptionStagnation = (user: User): AdoptionStagnationSignal => {
  const lastFeatureUse = getLastNewFeatureUseDate(user.id);
  const daysSince = Math.floor((Date.now() - lastFeatureUse) / (1000 * 60 * 60 * 24));

  const advancedFeatures = ['team_analytics', 'custom_reports', 'api_access', 'integrations'];
  const usedAdvanced = advancedFeatures.filter(f => hasUsedFeature(user.id, f));

  const isStagnating =
    daysSince > 60 || // No new features for 2 months
    usedAdvanced.length === 0; // Never used advanced features

  return {
    days_since_new_feature_used: daysSince,
    new_features_tried: getFeatureCount(user.id),
    total_available_features: getTotalFeatures(),
    adoption_rate: getFeatureCount(user.id) / getTotalFeatures(),
    uses_core_features_only: usedAdvanced.length === 0,
    advanced_features_used: usedAdvanced,
    invited_team_members: hasInvitedTeam(user.id),
    viewed_team_analytics: hasViewedTeamAnalytics(user.id),
    is_stagnating: isStagnating,
    risk_score: isStagnating ? Math.min(daysSince, 100) : 0
  };
};
```

**Risk Levels:**
- **Critical:** No new features for 90+ days
- **High:** No new features for 60-89 days
- **Medium:** No new features for 30-59 days
- **Low:** Core features only, but active

---

### Signal 3: Failed Conversion Attempts

**Definition:** User tried to upgrade but abandoned the process.

**Metrics:**
```typescript
interface FailedConversionSignal {
  // Upgrade attempts
  upgrade_click_count: number;
  upgrade_page_views: number;
  checkout_initiated: boolean;
  checkout_completed: boolean;

  // Abandonment
  last_upgrade_attempt: Date;
  abandonment_stage: 'pricing' | 'checkout' | 'payment' | 'none';

  // Friction signals
  support_tickets_related_to_billing: number;

  // Risk assessment
  has_failed_conversion: boolean;
  risk_score: number;
}

const calculateFailedConversion = (user: User): FailedConversionSignal => {
  const upgradeEvents = getEvents(user.id, 'upgrade_click', 90);
  const checkoutEvents = getEvents(user.id, 'checkout_initiated', 90);
  const completedEvents = getEvents(user.id, 'checkout_completed', 90);

  const hasFailed = checkoutEvents.length > 0 && completedEvents.length === 0;

  return {
    upgrade_click_count: upgradeEvents.length,
    upgrade_page_views: getEvents(user.id, 'pricing_page_view', 90).length,
    checkout_initiated: checkoutEvents.length > 0,
    checkout_completed: completedEvents.length > 0,
    last_upgrade_attempt: getLastEventDate(user.id, 'checkout_initiated'),
    abandonment_stage: getAbandonmentStage(user.id),
    support_tickets_related_to_billing: getSupportTickets(user.id, 'billing', 90).length,
    has_failed_conversion: hasFailed,
    risk_score: hasFailed ? 80 : 0 // High risk - showed intent but failed
  };
};
```

**Risk Levels:**
- **Critical:** 3+ failed upgrade attempts
- **High:** 1-2 failed upgrade attempts
- **Medium:** Pricing page views but no action
- **Low:** Minimal engagement with pricing

---

### Signal 4: Support Sentiment Shift

**Definition:** Increasing negative sentiment or frustration in support interactions.

**Metrics:**
```typescript
interface SupportSentimentSignal {
  // Ticket metrics
  support_tickets_last_30_days: number;
  avg_tickets_per_month: number;
  ticket_increase_percentage: number;

  // Sentiment analysis
  negative_sentiment_tickets: number;
  sentiment_score: number; // -1 to +1
  sentiment_decline: number;

  // Issue types
  bug_reports: number;
  feature_requests: number;
  complaints: number;

  // Risk assessment
  has_sentiment_decline: boolean;
  risk_score: number;
}

const calculateSupportSentiment = (user: User): SupportSentimentSignal => {
  const tickets = getSupportTickets(user.id, 30);
  const historical = getHistoricalTicketAverage(user.id);

  const sentiments = tickets.map(t => analyzeSentiment(t.message));
  const avgSentiment = sentiments.reduce((a, b) => a + b, 0) / sentiments.length;

  const negativeCount = sentiments.filter(s => s < -0.3).length;
  const hasDecline = avgSentiment < -0.2 || negativeCount >= 2;

  return {
    support_tickets_last_30_days: tickets.length,
    avg_tickets_per_month: historical,
    ticket_increase_percentage: ((tickets.length - historical) / historical) * 100,
    negative_sentiment_tickets: negativeCount,
    sentiment_score: avgSentiment,
    sentiment_decline: historical - avgSentiment,
    bug_reports: tickets.filter(t => t.type === 'bug').length,
    feature_requests: tickets.filter(t => t.type === 'feature_request').length,
    complaints: tickets.filter(t => t.type === 'complaint').length,
    has_sentiment_decline: hasDecline,
    risk_score: hasDecline ? Math.abs(avgSentiment) * 100 : 0
  };
};
```

**Risk Levels:**
- **Critical:** 3+ negative sentiment tickets
- **High:** 2 negative sentiment tickets or rapid decline
- **Medium:** 1 negative sentiment ticket
- **Low:** Increased ticket volume but neutral sentiment

---

## Usage-Based Signals

### Signal 5: Assessment Limit Reached

**Definition:** Free tier users hitting monthly assessment limits without upgrading.

**Metrics:**
```typescript
interface AssessmentLimitSignal {
  assessments_completed: number;
  assessment_limit: number;
  limit_reached: boolean;
  times_limit_reached: number; // How many months in a row

  // Behavior at limit
  attempted_assessment_when_limit_reached: boolean;
  days_since_limit_reached: number;

  // Response to limit
  viewed_pricing_page: boolean;
  viewed_upgrade_prompt: boolean;

  // Risk assessment
  risk_score: number;
}

const calculateAssessmentLimit = (user: User): AssessmentLimitSignal => {
  const usage = getCurrentMonthUsage(user.id);
  const limit = getAssessmentLimit(user.subscription_tier);

  const limitReached = usage.assessments >= limit;
  const monthsReached = countMonthsLimitReached(user.id);

  return {
    assessments_completed: usage.assessments,
    assessment_limit: limit,
    limit_reached: limitReached,
    times_limit_reached: monthsReached,
    attempted_assessment_when_limit_reached: hasEvent(user.id, 'assessment_attempt_blocked', 30),
    days_since_limit_reached: limitReached ? getDaysSinceLimitReached(user.id) : 0,
    viewed_pricing_page: hasEvent(user.id, 'pricing_page_view', 7),
    viewed_upgrade_prompt: hasEvent(user.id, 'upgrade_prompt_viewed', 7),
    risk_score: limitReached && !viewed_pricing_page ? 70 : 0
  };
};
```

**Risk Levels:**
- **Critical:** Limit reached, no pricing page view, 7+ days
- **High:** Limit reached, no upgrade action, 3-6 days
- **Medium:** Limit reached for 2+ consecutive months
- **Low:** Limit reached but engaging with upgrade prompts

---

### Signal 6: Login Frequency Decline

**Definition:** User logging in less frequently over time.

**Metrics:**
```typescript
interface LoginFrequencySignal {
  // Recent login frequency
  logins_last_30_days: number;
  logins_previous_30_days: number;
  login_decline_percentage: number;

  // Days since last login
  days_since_last_login: number;
  avg_days_between_logins: number;

  // Login patterns
  typical_login_days: string[]; // ['Monday', 'Tuesday', 'Wednesday']
  broke_typical_pattern: boolean;

  // Risk assessment
  is_declining: boolean;
  risk_score: number;
}

const calculateLoginFrequency = (user: User): LoginFrequencySignal => {
  const last30 = getLogins(user.id, 30);
  const previous30 = getLogins(user.id, 60, 30);

  const decline = ((previous30.length - last30.length) / previous30.length) * 100;
  const lastLogin = last30.length > 0 ? last30[0].date : null;
  const daysSince = lastLogin ? Math.floor((Date.now() - lastLogin) / (1000 * 60 * 60 * 24)) : 999;

  const typicalDays = getTypicalLoginDays(user.id, 90);
  const brokePattern = last30.length < 3 && typicalDays.length >= 2;

  return {
    logins_last_30_days: last30.length,
    logins_previous_30_days: previous30.length,
    login_decline_percentage: decline,
    days_since_last_login: daysSince,
    avg_days_between_logins: getAverageDaysBetweenLogins(user.id, 90),
    typical_login_days: typicalDays,
    broke_typical_pattern: brokePattern,
    is_declining: decline > 50 || daysSince > 14,
    risk_score: decline > 50 ? decline : (daysSince > 14 ? daysSince * 2 : 0)
  };
};
```

**Risk Levels:**
- **Critical:** No login for 21+ days
- **High:** No login for 14-20 days OR 60%+ login decline
- **Medium:** No login for 7-13 days OR 40-59% login decline
- **Low:** No login for 4-6 days

---

## Sentiment Signals

### Signal 7: NPS & Survey Feedback

**Definition:** Low NPS scores or negative feedback in surveys.

**Metrics:**
```typescript
interface SurveySentimentSignal {
  // NPS scores
  latest_nps_score: number;
  avg_nps_score: number;
  nps_decline: number;

  // Survey responses
  latest_survey_response: string;
  sentiment_analysis: 'positive' | 'neutral' | 'negative';

  // Churn indicators in feedback
  mentioned_competitors: boolean;
  mentioned_cancellation: boolean;
  mentioned_pricing: boolean;

  // Risk assessment
  is_negative_sentiment: boolean;
  risk_score: number;
}

const calculateSurveySentiment = (user: User): SurveySentimentSignal => {
  const latestSurvey = getLatestSurvey(user.id);
  const historicalNPS = getHistoricalNPS(user.id);

  const npsDecline = historicalNPS - latestSurvey.nps_score;

  const feedback = latestSurvey.feedback.toLowerCase();
  const hasChurnSignals =
    feedback.includes('cancel') ||
    feedback.includes('switch') ||
    feedback.includes('competitor');

  return {
    latest_nps_score: latestSurvey.nps_score,
    avg_nps_score: historicalNPS,
    nps_decline: npsDecline,
    latest_survey_response: latestSurvey.feedback,
    sentiment_analysis: latestSurvey.nps_score >= 9 ? 'positive' :
                      latestSurvey.nps_score >= 7 ? 'neutral' : 'negative',
    mentioned_competitors: feedback.includes('competitor') || feedback.includes('alternative'),
    mentioned_cancellation: feedback.includes('cancel'),
    mentioned_pricing: feedback.includes('expensive') || feedback.includes('price'),
    is_negative_sentiment: latestSurvey.nps_score <= 6 || hasChurnSignals,
    risk_score: latestSurvey.nps_score <= 6 ? 70 : (npsDecline > 3 ? 50 : 0)
  };
};
```

**Risk Levels:**
- **Critical:** NPS 0-3 OR mentions cancellation/competitors
- **High:** NPS 4-6 OR >3 point NPS decline
- **Medium:** NPS 7-8 with concerns expressed
- **Low:** NPS 7-8 neutral

---

### Signal 8: Competitor Research

**Definition:** User researching or mentioning competitors.

**Metrics:**
```typescript
interface CompetitorResearchSignal {
  // Explicit mentions
  mentioned_competitors_in_support: boolean;
  mentioned_competitors_in_survey: boolean;

  // Behavioral signals
  viewed_competitor_comparison: boolean;
  exported_data_for_migration: boolean;

  // Competitors mentioned
  competitors_mentioned: string[];

  // Risk assessment
  is_researching_competitors: boolean;
  risk_score: number;
}

const calculateCompetitorResearch = (user: User): CompetitorResearchSignal => {
  const supportMentions = getSupportTickets(user.id, 90)
    .filter(t => t.message.includes('Crystal Knows') ||
                t.message.includes('Hacker Rank') ||
                t.message.includes(' Gallup'));

  const viewedComparison = hasEvent(user.id, 'competitor_comparison_view', 60);
  const exportedData = hasEvent(user.id, 'data_export', 30);

  const competitors = [...new Set([
    ...supportMentions.map(t => extractCompetitor(t.message)),
    ...(viewedComparison ? ['Various'] : [])
  ])];

  return {
    mentioned_competitors_in_support: supportMentions.length > 0,
    mentioned_competitors_in_survey: getLatestSurvey(user.id).feedback.includes('competitor'),
    viewed_competitor_comparison: viewedComparison,
    exported_data_for_migration: exportedData,
    competitors_mentioned: competitors,
    is_researching_competitors: supportMentions.length > 0 || viewedComparison || exportedData,
    risk_score: exportedData ? 90 : (viewedComparison ? 60 : (supportMentions.length > 0 ? 50 : 0))
  };
};
```

**Risk Levels:**
- **Critical:** Exported data (preparing to leave)
- **High:** Viewed competitor comparison or mentioned competitor
- **Medium:** Generic comparison questions
- **Low:** No signals

---

## Risk Scoring Model

### Composite Risk Score

```typescript
interface ChurnRiskScore {
  overall_risk: 'critical' | 'high' | 'medium' | 'low' | 'safe';
  overall_score: number; // 0-100
  signal_scores: {
    usage_decline: number;
    adoption_stagnation: number;
    failed_conversion: number;
    support_sentiment: number;
    assessment_limit: number;
    login_frequency: number;
    survey_sentiment: number;
    competitor_research: number;
  };
  primary_risk_factors: string[];
  recommended_actions: string[];
}

const calculateChurnRisk = (user: User): ChurnRiskScore => {
  // Calculate individual signal scores
  const usageDecline = calculateUsageDecline(user);
  const adoptionStagnation = calculateAdoptionStagnation(user);
  const failedConversion = calculateFailedConversion(user);
  const supportSentiment = calculateSupportSentiment(user);
  const assessmentLimit = calculateAssessmentLimit(user);
  const loginFrequency = calculateLoginFrequency(user);
  const surveySentiment = calculateSurveySentiment(user);
  const competitorResearch = calculateCompetitorResearch(user);

  // Weighted average (higher weight = more important)
  const weights = {
    usage_decline: 0.25,          // Most important
    login_frequency: 0.20,
    competitor_research: 0.15,    // High urgency
    failed_conversion: 0.12,
    assessment_limit: 0.10,
    support_sentiment: 0.08,
    adoption_stagnation: 0.05,
    survey_sentiment: 0.05
  };

  const overallScore =
    (usageDecline.risk_score * weights.usage_decline) +
    (loginFrequency.risk_score * weights.login_frequency) +
    (competitorResearch.risk_score * weights.competitor_research) +
    (failedConversion.risk_score * weights.failed_conversion) +
    (assessmentLimit.risk_score * weights.assessment_limit) +
    (supportSentiment.risk_score * weights.support_sentiment) +
    (adoptionStagnation.risk_score * weights.adoption_stagnation) +
    (surveySentiment.risk_score * weights.survey_sentiment);

  // Determine risk category
  const overallRisk =
    overallScore >= 80 ? 'critical' :
    overallScore >= 60 ? 'high' :
    overallScore >= 40 ? 'medium' :
    overallScore >= 20 ? 'low' : 'safe';

  // Identify top risk factors
  const signalScores = {
    usage_decline: usageDecline.risk_score,
    adoption_stagnation: adoptionStagnation.risk_score,
    failed_conversion: failedConversion.risk_score,
    support_sentiment: supportSentiment.risk_score,
    assessment_limit: assessmentLimit.risk_score,
    login_frequency: loginFrequency.risk_score,
    survey_sentiment: surveySentiment.risk_score,
    competitor_research: competitorResearch.risk_score
  };

  const sortedFactors = Object.entries(signalScores)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3)
    .map(([signal]) => signal);

  // Generate recommended actions
  const recommendedActions = generateRecommendations(overallRisk, sortedFactors);

  return {
    overall_risk: overallRisk,
    overall_score: Math.round(overallScore),
    signal_scores: signalScores,
    primary_risk_factors: sortedFactors,
    recommended_actions
  };
};

const generateRecommendations = (
  risk: string,
  factors: string[]
): string[] => {
  const recommendations = {
    critical: [
      'Immediate customer success outreach within 24 hours',
      'Offer personalized discount or incentive',
      'Schedule executive call if enterprise',
      'Assign dedicated success manager'
    ],
    high: [
      'Customer success outreach within 72 hours',
      'Send personalized re-engagement email',
      'Offer training or resources',
      'Check for unresolved support issues'
    ],
    medium: [
      'Add to automated nurturing campaign',
      'Send feature highlight newsletter',
      'Invite to webinar or training',
      'Monitor for signal escalation'
    ],
    low: [
      'Continue normal monitoring',
      'Include in monthly newsletter',
      'Track risk score trends'
    ],
    safe: [
      'No action needed',
      'Continue normal engagement'
    ]
  };

  return recommendations[risk] || [];
};
```

---

## Intervention Triggers

### Automated Trigger System

```typescript
// services/churnTriggers.ts
interface TriggerConfig {
  name: string;
  condition: (user: User) => boolean;
  action: (user: User) => void;
  priority: 'critical' | 'high' | 'medium' | 'low';
  cooldown_days: number; // Minimum time between triggers
}

const triggers: TriggerConfig[] = [
  {
    name: 'critical_usage_decline',
    condition: (user) => {
      const decline = calculateUsageDecline(user);
      return decline.is_declining && decline.risk_score >= 80;
    },
    action: (user) => {
      sendEmail(user.email, 'critical_usage_decline');
      notifySlack(user.id, 'critical_churn_risk');
      createTask('customer_success', 'immediate_outreach', user.id);
    },
    priority: 'critical',
    cooldown_days: 30
  },
  {
    name: 'competitor_research_detected',
    condition: (user) => {
      const research = calculateCompetitorResearch(user);
      return research.exported_data_for_migration;
    },
    action: (user) => {
      sendEmail(user.email, 'win_back_offer');
      notifySlack(user.id, 'competitor_risk');
      createTask('sales', 'retention_call', user.id);
    },
    priority: 'critical',
    cooldown_days: 60
  },
  {
    name: 'assessment_limit_reached',
    condition: (user) => {
      const limit = calculateAssessmentLimit(user);
      return limit.limit_reached &&
             limit.days_since_limit_reached >= 7 &&
             !limit.viewed_pricing_page;
    },
    action: (user) => {
      sendEmail(user.email, 'upgrade_reminder');
      showInAppMessage(user.id, 'upgrade_prompt');
    },
    priority: 'medium',
    cooldown_days: 7
  },
  {
    name: 'negative_nps_detected',
    condition: (user) => {
      const sentiment = calculateSurveySentiment(user);
      return sentiment.is_negative_sentiment;
    },
    action: (user) => {
      createTask('customer_success', 'follow_up_survey', user.id);
      sendEmail(user.email, 'feedback_appreciation');
    },
    priority: 'high',
    cooldown_days: 14
  },
  {
    name: 'login_frequency_decline',
    condition: (user) => {
      const login = calculateLoginFrequency(user);
      return login.days_since_last_login >= 14;
    },
    action: (user) => {
      sendEmail(user.email, 'we_miss_you');
      showInAppMessage(user.id, 'new_features_highlight');
    },
    priority: 'medium',
    cooldown_days: 14
  }
];

// Trigger executor
const executeTriggers = async (userId: string) => {
  const user = await getUser(userId);
  const risk = calculateChurnRisk(user);

  // Check each trigger
  for (const trigger of triggers) {
    // Skip if on cooldown
    if (await isOnCooldown(userId, trigger.name)) {
      continue;
    }

    // Check if condition is met
    if (trigger.condition(user)) {
      // Execute action
      await trigger.action(user);

      // Set cooldown
      await setCooldown(userId, trigger.name, trigger.cooldown_days);

      // Log trigger
      await logTriggerExecution(userId, trigger.name, trigger.priority);
    }
  }

  // Update risk score in database
  await updateUserRiskScore(userId, risk);
};

// Scheduled job (runs daily)
const scheduledChurnCheck = async () => {
  const activeUsers = await getActiveUsers(); // Users active in last 90 days

  for (const user of activeUsers) {
    await executeTriggers(user.id);
  }
};
```

---

## Retention Playbooks

### Playbook 1: Critical Risk Intervention

**When:** Overall risk score 80-100

**Timeline:** Within 24 hours

**Steps:**
1. **Immediate notification**
   - Slack alert to Customer Success Manager
   - Email to user (personalized, from CSM)
   - Flag account for priority support

2. **Research (30 minutes)**
   - Review usage history
   - Check support tickets
   - Identify pain points
   - Prepare personalized message

3. **Outreach (call preferred)**
   ```
   Subject: Checking in on your PsychSync experience

   Hi [Name],

   I noticed you haven't been using PsychSync as much lately, and I wanted
   to reach out personally to see how things are going.

   Is there anything we can do to help you get more value? I'd love to
   hop on a quick 15-minute call to understand your experience better.

   Are you free [suggest 2-3 time slots]?

   Best regards,
   [CSM Name]
   ```

4. **Retention offer (if appropriate)**
   - 20% discount for 3 months
   - Free month of Premium
   - Additional training/onboarding
   - Custom feature development (Enterprise)

5. **Follow-up**
   - Send summary after call
   - Set check-in for 2 weeks
   - Monitor usage daily for 2 weeks

---

### Playbook 2: High Risk Nurturing

**When:** Overall risk score 60-79

**Timeline:** Within 72 hours

**Steps:**
1. **Automated email sequence**
   ```
   Email 1 (Day 0):
   Subject: We've missed you, [Name]!

   Hi [Name],

   It's been a little while since you've used PsychSync, and we wanted
   to check in.

   Based on your usage, you might be interested in:
   [Feature 1] - [Brief description]
   [Feature 2] - [Brief description]

   Log in to explore: [Link]

   Best,
   The PsychSync Team

   Email 2 (Day 3):
   Subject: Quick tip: [Feature] can help you [benefit]

   Hi [Name],

   Did you know that [feature] can help you [solve problem]?

   Here's a 2-minute video showing how: [Link]

   Enjoy!

   Email 3 (Day 7):
   Subject: Your feedback matters

   Hi [Name],

   We're always looking to improve PsychSync. Would you mind sharing
   what would make the product more valuable for you?

   [Link to 2-question survey]

   Your response will shape our roadmap.

   Thanks for being part of PsychSync!
   ```

2. **In-app messaging**
   - Targeted feature highlights
   - "New since you last visited" modal
   - Personalized recommendations

3. **Monitor for escalation**
   - If no response in 7 days → escalate to critical
   - If positive response → downgrade to medium risk

---

### Playbook 3: Assessment Limit Conversion

**When:** User hits assessment limit without upgrading

**Timeline:** Day 0, 7, 14 after limit

**Steps:**
1. **Day 0: Immediate notification**
   - In-app banner: "You've used all your assessments"
   - CTA: "Upgrade for unlimited assessments"

2. **Day 7: First follow-up**
   ```
   Subject: Ready to unlock unlimited assessments?

   Hi [Name],

   You've used all 3 of your free assessments this month. We're glad
   you're finding value in PsychSync!

   Upgrade to Premium and get:
   ✓ Unlimited assessments
   ✓ Team analytics
   ✓ Advanced insights

   [Button: Upgrade Now - 20% off first month]

   This offer expires in 7 days.
   ```

3. **Day 14: Last chance**
   ```
   Subject: Last chance: 20% off Premium

   Hi [Name],

   Your discount expires tomorrow!

   Unlock unlimited assessments and all Premium features for just
   $23/month (normally $29).

   [Button: Claim Your Discount]

   Don't miss out.
   ```

---

### Playbook 4: Failed Conversion Recovery

**When:** User started checkout but didn't complete

**Timeline:** Within 2 hours

**Steps:**
1. **Immediate email**
   ```
   Subject: Complete your upgrade

   Hi [Name],

   I noticed you started upgrading to Premium but didn't finish.

   Did you have any questions? I'm here to help!

   Common questions:
   - "Can I cancel anytime?" → Yes!
   - "Is there a free trial?" → We offer a 30-day money-back guarantee
   - "What payment methods do you accept?" → Credit card, or annual invoicing for Enterprise

   [Button: Complete Your Upgrade]

   Questions? Just reply to this email.

   Best regards,
   [CSM Name]
   ```

2. **Live chat (if available)**
   - Proactive message: "Hi! I noticed you had questions about upgrading. Can I help?"

3. **Retargeting (if enabled)**
   - Facebook/LinkedIn ads: "Ready to unlock unlimited assessments?"
   - Discount offer: $10 off first month

---

## Implementation Guide

### Database Schema

```sql
-- Churn risk scores table
CREATE TABLE churn_risk_scores (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id),
  calculated_at TIMESTAMP DEFAULT NOW(),

  -- Overall risk
  overall_risk VARCHAR(20) NOT NULL, -- 'critical', 'high', 'medium', 'low', 'safe'
  overall_score INTEGER NOT NULL CHECK (overall_score BETWEEN 0 AND 100),

  -- Signal scores
  usage_decline_score INTEGER,
  adoption_stagnation_score INTEGER,
  failed_conversion_score INTEGER,
  support_sentiment_score INTEGER,
  assessment_limit_score INTEGER,
  login_frequency_score INTEGER,
  survey_sentiment_score INTEGER,
  competitor_research_score INTEGER,

  -- Primary factors
  primary_risk_factors TEXT[], -- ['usage_decline', 'login_frequency']

  -- Interventions
  last_intervention_date TIMESTAMP,
  intervention_count INTEGER DEFAULT 0,

  UNIQUE(user_id, calculated_at)
);

-- Trigger executions log
CREATE TABLE churn_trigger_executions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id),
  trigger_name VARCHAR(100) NOT NULL,
  priority VARCHAR(20) NOT NULL,
  executed_at TIMESTAMP DEFAULT NOW(),
  action_taken TEXT NOT NULL,
  result VARCHAR(50), -- 'sent', 'failed', 'skipped'
  result_details TEXT
);

-- Cooldown tracking
CREATE TABLE churn_trigger_cooldowns (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id),
  trigger_name VARCHAR(100) NOT NULL,
  cooldown_until TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, trigger_name)
);

-- Indexes
CREATE INDEX idx_churn_risk_user ON churn_risk_scores(user_id);
CREATE INDEX idx_churn_risk_overall ON churn_risk_scores(overall_risk);
CREATE INDEX idx_churn_risk_date ON churn_risk_scores(calculated_at DESC);
CREATE INDEX idx_churn_trigger_user ON churn_trigger_executions(user_id);
CREATE INDEX idx_churn_trigger_date ON churn_trigger_executions(executed_at DESC);
```

### API Endpoints

```python
# app/api/v1/endpoints/churn_prediction.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import get_current_user
from app.db.models.user import User
from typing import List
from pydantic import BaseModel

router = APIRouter()

class ChurnRiskResponse(BaseModel):
    overall_risk: str
    overall_score: int
    signal_scores: dict
    primary_risk_factors: List[str]
    recommended_actions: List[str]

@router.get("/risk/{user_id}", response_model=ChurnRiskResponse)
async def get_churn_risk(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get churn risk score for a user.
    Requires customer_success or admin role.
    """
    if current_user.role not in ['customer_success', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Calculate risk
    risk_score = calculateChurnRisk(user)

    # Store in database
    store_risk_score(db, user_id, risk_score)

    return risk_score

@router.get("/at-risk")
async def get_at_risk_users(
    risk_level: str = 'high',
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of users at or above specified risk level.
    """
    if current_user.role not in ['customer_success', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    query = """
        SELECT DISTINCT ON (user_id) user_id, overall_risk, overall_score, calculated_at
        FROM churn_risk_scores
        WHERE overall_risk IN :risk_levels
        ORDER BY user_id, calculated_at DESC
        LIMIT :limit
    """

    risk_levels = {
        'critical': ['critical'],
        'high': ['critical', 'high'],
        'medium': ['critical', 'high', 'medium'],
        'low': ['critical', 'high', 'medium', 'low']
    }

    results = db.execute(query, {
        'risk_levels': tuple(risk_levels[risk_level]),
        'limit': limit
    }).fetchall()

    return {
        'users': results,
        'count': len(results)
    }

@router.post("/intervene/{user_id}")
async def trigger_intervention(
    user_id: str,
    intervention_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger an intervention for a user.
    """
    if current_user.role not in ['customer_success', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Execute intervention
    if intervention_type == 'email':
        sendEmail(user.email, 'manual_intervention')
    elif intervention_type == 'slack_notification':
        notifySlack(user.id, 'manual_intervention')
    elif intervention_type == 'create_task':
        createTask('customer_success', 'manual_outreach', user_id)

    # Log intervention
    log_intervention(db, user_id, intervention_type, current_user.id)

    return {"message": "Intervention executed"}
```

---

## Summary

This churn prediction framework provides:

✅ **8 Behavioral Signals** – Usage decline, adoption stagnation, failed conversions, support sentiment, assessment limits, login frequency, survey sentiment, competitor research
✅ **Risk Scoring Model** – Weighted composite score with 0-100 scale
✅ **Automated Triggers** – Configurable trigger system with cooldown periods
✅ **4 Retention Playbooks** – Critical, high, medium, and low risk interventions
✅ **Implementation Guide** – Database schema, API endpoints, trigger logic
✅ **Action Templates** – Email sequences, outreach scripts, offers

**Expected Impact:**
- **Predict 70%+ of churn** 30 days in advance
- **Reduce churn by 20%** through proactive interventions
- **Save $50K+ annually** in retained revenue
- **Improve customer satisfaction** through proactive support

**Next Steps:**
1. Implement tracking infrastructure
2. Calculate baseline churn rate
3. Train team on intervention playbooks
4. Set up automated triggers
5. Monitor and refine models

---

**Document Version:** 1.0
**Last Updated:** January 2025
**Next Review:** April 2025
**Maintained By:** Customer Success & Data Team
