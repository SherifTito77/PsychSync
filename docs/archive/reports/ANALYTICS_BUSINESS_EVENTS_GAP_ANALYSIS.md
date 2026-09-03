# 🔍 Business Analytics Events - Gap Analysis

**Date**: January 21, 2026
**Status**: ⚠️ **CRITICAL GAPS IDENTIFIED**
**Impact**: Business dashboards cannot display 70%+ of key metrics

---

## 📊 Executive Summary

PsychSync has comprehensive business dashboards but **lacks the analytics events** needed to populate them. Current tracking covers **user actions** but **misses business outcomes** like revenue, subscriptions, feature usage, and retention.

**Critical Finding**: Dashboards are empty or display placeholder data because the required events are never tracked.

---

## 🎯 Business Metrics vs. Events Tracked

### **Revenue & Subscription Metrics**

| Dashboard Metric | Event Needed | Status | Impact |
|-----------------|--------------|--------|--------|
| Trial Signups | `subscription_trial_started` | ❌ Missing | Cannot track acquisition funnel |
| Trial → Paid Rate | `subscription_plan_upgraded` | ❌ Missing | Cannot measure conversion |
| MRR/ARR | `subscription_payment_succeeded` | ❌ Missing | Revenue dashboard broken |
| Churn Rate | `subscription_cancelled` | ❌ Missing | Cannot calculate churn |
| LTV/CAC | `subscription_started` + `subscription_upgraded` | ❌ Missing | ROI calculations impossible |
| ARPU | `subscription_payment_succeeded` + active users | ❌ Missing | Revenue per user unknown |

**Current Coverage**: 0% ❌
**Business Impact**: 🔴 CRITICAL - Revenue completely untracked

---

### **Feature Usage Metrics**

| Dashboard Metric | Event Needed | Status | Impact |
|-----------------|--------------|--------|--------|
| Clinical Tools Usage | `feature_clinical_tools_used` | ❌ Missing | Cannot prove value |
| Personality Assessments | `feature_assessment_taken` | ✅ Partial* | Only tracks funnel, not which type |
| Team Analytics | `feature_team_analytics_viewed` | ❌ Missing | Team feature adoption unknown |
| Predictive Analytics | `feature_predictive_analytics_used` | ❌ Missing | AI feature ROI unclear |
| Benchmarking | `feature_benchmarking_used` | ❌ Missing | Competitive feature adoption unknown |
| Slack Integration | `integration_slack_connected` | ❌ Missing | Integration value untracked |
| HRIS Integration | `integration_hris_connected` | ❌ Missing | Enterprise stickiness unknown |

*Current Coverage*: 10% (only assessment funnel events)
**Business Impact**: 🔴 HIGH - Cannot prove product value to customers

---

### **Engagement & Retention Metrics**

| Dashboard Metric | Event Needed | Status | Impact |
|-----------------|--------------|--------|--------|
| Monthly Active Users | `user_session_started` | ❌ Missing | MAU calculation impossible |
| Daily Active Users | `user_session_started` | ❌ Missing | DAU calculation impossible |
| Session Duration | `user_session_ended` | ❌ Missing | Engagement time unknown |
| 30-Day Retention | `user_returned` + days since signup | ❌ Missing | Retention rate unknown |
| 90-Day Retention | `user_returned` + days since signup | ❌ Missing | Long-term retention unknown |
| Assessments Per User | `funnel_assessment_completed` per user | ✅ Partial | Has events, needs aggregation |
| Team Collaboration Rate | `team_member_collaborated` | ❌ Missing | Team value unclear |

**Current Coverage**: 20% (assessment completions only)
**Business Impact**: 🟡 MEDIUM - Basic engagement tracked, deep insights missing

---

### **Support & Success Metrics**

| Dashboard Metric | Event Needed | Status | Impact |
|-----------------|--------------|--------|--------|
| Support Tickets | `support_ticket_created` | ❌ Missing | Ticket volume unknown |
| Response Time | `support_ticket_first_response` | ❌ Missing | Support quality unknown |
| CSAT Score | `support_satisfaction_survey` | ❌ Missing | Customer satisfaction unknown |
| Resolution Time | `support_ticket_resolved` | ❌ Missing | Support efficiency unknown |

**Current Coverage**: 0% ❌
**Business Impact**: 🟡 MEDIUM - Support quality invisible

---

## 📋 Complete Missing Events Catalog

### **Priority 1: Revenue & Subscription Events** 🔴 CRITICAL

```typescript
// Subscription Lifecycle
SUBSCRIPTION_TRIAL_STARTED: 'subscription_trial_started',
SUBSCRIPTION_PLAN_SELECTED: 'subscription_plan_selected',
SUBSCRIPTION_PAYMENT_SUCCEEDED: 'subscription_payment_succeeded',
SUBSCRIPTION_PAYMENT_FAILED: 'subscription_payment_failed',
SUBSCRIPTION_PLAN_UPGRADED: 'subscription_plan_upgraded',
SUBSCRIPTION_PLAN_DOWNGRADED: 'subscription_plan_downgraded',
SUBSCRIPTION_CANCELLED: 'subscription_cancelled',
SUBSCRIPTION_RENEWED: 'subscription_renewed',
SUBSCRIPTION_PAUSED: 'subscription_paused',

// Properties needed:
{
  plan_tier: 'free' | 'premium' | 'enterprise',
  billing_period: 'monthly' | 'annual',
  amount: number,
  currency: string,
  payment_method: string,
  trial_days?: number,
  cancellation_reason?: string,
  previous_plan?: string,
}
```

**Business Questions Answered**:
- What's our MRR/ARR?
- What's our churn rate?
- What's our trial-to-paid conversion?
- What's our upgrade path?
- Why do customers cancel?

---

### **Priority 2: Feature Usage Events** 🔴 HIGH

```typescript
// Core Product Features
FEATURE_ASSESSMENT_TAKEN: 'feature_assessment_taken',
FEATURE_TEAM_CREATED: 'feature_team_created',
FEATURE_TEAM_MEMBER_ADDED: 'feature_team_member_added',
FEATURE_TEAM_OPTIMIZER_USED: 'feature_team_optimizer_used',

// Clinical Tools
FEATURE_CLINICAL_TOOLS_USED: 'feature_clinical_tools_used',
FEATURE_ASSESSMENT_SCORED: 'feature_assessment_scored',
FEATURE_CLINICAL_REPORT_GENERATED: 'feature_clinical_report_generated',
FEATURE_WELLNESS_PLAN_CREATED: 'feature_wellness_plan_created',

// Analytics & Insights
FEATURE_PREDICTIVE_ANALYTICS_USED: 'feature_predictive_analytics_used',
FEATURE_PATTERN_ANALYSIS_VIEWED: 'feature_pattern_analysis_viewed',
FEATURE_TREND_ANALYSIS_VIEWED: 'feature_trend_analysis_viewed',
FEATURE_BENCHMARKING_USED: 'feature_benchmarking_used',

// Integrations
INTEGRATION_SLACK_CONNECTED: 'integration_slack_connected',
INTEGRATION_HRIS_CONNECTED: 'integration_hris_connected',
INTEGRATION_EMAIL_CONNECTED: 'integration_email_connected',

// Properties needed:
{
  feature_name: string,
  feature_category: string,
  assessment_type?: string,  // for assessments
  team_size?: number,  // for team features
  integration_type?: string,  // for integrations
  usage_context: string,  // where/why used
}
```

**Business Questions Answered**:
- Which features drive retention?
- Which features justify subscription cost?
- What's our feature adoption rate?
- Which integrations reduce churn?
- What's the "aha moment" for users?

---

### **Priority 3: Engagement & Session Events** 🟡 MEDIUM

```typescript
// Session Tracking
USER_SESSION_STARTED: 'user_session_started',
USER_SESSION_ENDED: 'user_session_ended',
USER_PAGE_VIEW: 'user_page_view',
USER_RETURNED: 'user_returned',

// Engagement Depth
ENGAGEMENT_SCROLL_DEPTH: 'engagement_scroll_depth',
ENGAGEMENT_TIME_ON_PAGE: 'engagement_time_on_page',
ENGAGEMENT_FEATURE_INTERACTION: 'engagement_feature_interaction',

// Properties needed:
{
  session_id: string,
  session_duration_seconds: number,
  pages_viewed: number,
  features_used: string[],
  entry_page: string,
  exit_page: string,
  device_type: string,
  days_since_last_visit: number,  // for returned users
}
```

**Business Questions Answered**:
- What's our DAU/MAU?
- What's our retention curve?
- How long do sessions last?
- What's stickiness (DAU/MAU ratio)?
- When do users churn?

---

### **Priority 4: Support & Success Events** 🟡 MEDIUM

```typescript
// Support Tickets
SUPPORT_TICKET_CREATED: 'support_ticket_created',
SUPPORT_TICKET_FIRST_RESPONSE: 'support_ticket_first_response',
SUPPORT_TICKET_RESOLVED: 'support_ticket_resolved',
SUPPORT_SATISFACTION_SURVEY: 'support_satisfaction_survey',

// Properties needed:
{
  ticket_id: string,
  category: string,
  priority: string,
  response_time_minutes: number,
  resolution_time_minutes: number,
  csat_score?: number,  // 1-5
  nps_score?: number,  // 0-10
}
```

**Business Questions Answered**:
- What's our support volume?
- How fast do we respond?
- Are customers satisfied?
- Which issues cause tickets?

---

## 🔍 Implementation Strategy

### **Option 1: Backend-Generated Events** (Recommended)

**Approach**: Generate business events from database state changes

**Pros**:
- ✅ Guaranteed to capture all events (even web payments)
- ✅ Single source of truth
- ✅ Can backfill historical data
- ✅ No client-side implementation needed

**Cons**:
- ❌ Requires backend work
- ❌ May need event streaming architecture

**Implementation**:
```python
# Backend: FastAPI endpoint
@app.post("/api/v1/subscription/webhook")
async def stripe_webhook(request: Request):
    event = await request.json()

    if event['type'] == 'payment_intent.succeeded':
        # Track analytics event
        analytics.track({
            'event_name': 'subscription_payment_succeeded',
            'user_id': event['data']['object']['customer'],
            'properties': {
                'amount': event['data']['object']['amount'],
                'currency': event['data']['object']['currency'],
                'plan_tier': get_plan_tier(event['data']['object']['product'])
            }
        })
```

---

### **Option 2: Frontend-Generated Events**

**Approach**: Track events when users perform actions

**Pros**:
- ✅ Easy to implement
- ✅ Captures user context
- ✅ Immediate feedback

**Cons**:
- ❌ Misses backend events (webhooks, stripe)
- ❌ Can be blocked by ad blockers
- ❌ Privacy concerns with revenue data

**Implementation**:
```typescript
// Frontend: Payment success page
useEffect(() => {
  if (paymentSuccess) {
    track('subscription_payment_succeeded', {
      plan_tier: selectedPlan,
      amount: planPrice,
      currency: 'USD',
      billing_period: billingPeriod
    });
  }
}, [paymentSuccess]);
```

---

### **Option 3: Hybrid Approach** (Best Practice)

**Approach**: Frontend for user actions, backend for system events

**Frontend Tracks**:
- Feature usage
- Page views
- User interactions
- Support tickets

**Backend Tracks**:
- Payments
- Subscriptions
- Churn
- Revenue calculations

---

## 🚨 Privacy & Compliance Considerations

### **GDPR/PII Concerns**

**Revenue Data**: Payment amounts are **personal data** under GDPR
- ✅ Must encrypt in transit
- ✅ Must store securely
- ✅ User right to access/delete
- ❌ Cannot track user-identifying revenue without consent

**Solution Options**:
1. **Anonymize**: Track aggregate revenue only (no user IDs)
2. **Hash**: Hash user IDs before sending to analytics
3. **Consent**: Require explicit consent for financial tracking
4. **Server-side**: Keep revenue data server-side, send aggregates only

---

## 📝 Next Steps

### **Phase 1: Critical Events** (Week 1)
1. Add subscription lifecycle events
2. Add payment success/failure events
3. Implement feature usage tracking
4. Add session tracking (start/end)

### **Phase 2: Implementation** (Week 2)
1. Choose implementation strategy (backend/hybrid)
2. Implement event tracking code
3. Test with real user flows
4. Verify dashboards populate

### **Phase 3: Validation** (Week 3)
1. Validate event data accuracy
2. Create dashboard alerts
3. Set up revenue reports
4. Train team on new metrics

---

## ❓ Design Decisions Needed

Before implementing, need decisions on:

1. **Privacy Strategy**: How will we handle revenue data privacy?
2. **Implementation**: Backend vs. frontend vs. hybrid?
3. **Backfilling**: Should we backfill historical subscription data?
4. **Aggregation**: Real-time or batched aggregation?
5. **Retention**: How long to store granular event data?

---

**Status**: ⚠️ **REQUIRES INPUT** - Cannot proceed without design decisions
**Next Action**: Review with product and engineering teams

---

**Generated**: January 21, 2026
**Analyst**: Analytics Systems Auditor
