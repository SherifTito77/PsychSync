# Feature Telemetry Requirements
## Data-Driven Product Analytics

---

## Executive Summary

This document defines PsychSync's comprehensive feature telemetry system for collecting, analyzing, and acting on user behavior data. Telemetry enables data-driven decisions, optimizes user experience, and powers the AI insights engine.

**Privacy-First Approach:** All telemetry is anonymized, aggregated, and compliant with GDPR/CCPA. Users can opt-out of non-essential tracking.

**Telemetry Goals:**
- Understand how users interact with features
- Identify friction points and optimization opportunities
- Power the AI insights engine
- Measure feature adoption and impact
- Enable real-time product analytics

---

## Part 1: Telemetry Categories

### Category 1: User Interaction Events
**What:** Actions users take in the product
**Examples:** Page views, button clicks, form submissions
**Privacy:** Anonymized (no PII)
**Retention:** 90 days

### Category 2: Performance Metrics
**What:** System performance and responsiveness
**Examples:** Page load times, API response times, error rates
**Privacy:** No user data (system metrics only)
**Retention:** 365 days (for SLA compliance)

### Category 3: Feature Usage
**What:** Which features are used, how often, by whom
**Examples:** Assessment taken, report generated, integration configured
**Privacy:** Aggregated (no individual user data in reports)
**Retention:** 180 days

### Category 4: Funnel Analytics
**What:** Conversion through multi-step processes
**Examples:** Onboarding, assessment completion, purchase flow
**Privacy:** Aggregated funnel metrics
**Retention:** 365 days

### Category 5: Error & Exception Tracking
**What:** Application errors and crashes
**Examples:** JavaScript errors, API failures, validation errors
**Privacy:** Error context only (no user data)
**Retention:** 180 days

### Category 6: A/B Testing Data
**What:** Experiment results and variant assignments
**Examples:** Feature flags, UI variants, pricing tests
**Privacy:** User-level assignment (for consistency)
**Retention:** 90 days post-experiment

---

## Part 2: Core Events to Track

### Authentication Events

```typescript
// User signs up
track("user_signed_up", {
  method: "email", // or "sso", "google_oauth"
  organization_tier: "starter", // or "business", "enterprise"
  referral_source: "organic", // or "paid", "referral"
  timestamp: DateTime
});

// User logs in
track("user_logged_in", {
  method: "email",
  success: true,
  mfa_enabled: false,
  device_type: "desktop", // or "mobile"
});

// User logs out
track("user_logged_out", {
  session_duration_seconds: 1800,
  pages_viewed: 15,
  features_used: 5
});
```

### Assessment Events

```typescript
// Assessment started
track("assessment_started", {
  framework_code: "MBTI", // or "BigFive", "Enneagram"
  assessment_type: "standard", // or "custom", "short_form"
  team_id: "team-123",
  is_retaking: false,
});

// Assessment question answered
track("assessment_question_answered", {
  assessment_id: "assessment-456",
  question_number: 15,
  question_type: "multiple_choice",
  time_spent_seconds: 12,
  is_skipped: false
});

// Assessment completed
track("assessment_completed", {
  assessment_id: "assessment-456",
  framework_code: "MBTI",
  total_questions: 93,
  time_spent_minutes: 18,
  completion_percentage: 100,
  score: 85,
  team_id: "team-123"
});
```

### Dashboard & Analytics Events

```typescript
// Dashboard viewed
track("dashboard_viewed", {
  dashboard_type: "team_analytics", // or "personal", "organization"
  time_range: "last_30_days",
  filters_applied: ["team", "date_range"],
  widgets_viewed: 5
});

// Report exported
track("report_exported", {
  report_type: "team_composition",
  format: "pdf", // or "csv", "excel"
  include_charts: true,
  team_id: "team-123"
});

// Filter applied
track("filter_applied", {
  filter_type: "date_range", // or "team", "assessment", "user"
  filter_value: "last_90_days",
  results_count: 45
});
```

### Team Management Events

```typescript
// Team created
track("team_created", {
  team_size: 15,
  department: "engineering",
  privacy_setting: "private", // or "org_visible"
});

// Team member invited
track("team_member_invited", {
  team_id: "team-123",
  invite_method: "email", // or "bulk_import", "sso"
  role: "team_member", // or "team_admin", "team_owner"
  invitation_sent: true
});

// Team member accepted
track("team_member_joined", {
  team_id: "team-123",
  invitation_to_acceptance_hours: 48
});
```

### Integration Events

```typescript
// Slack integration connected
track("slack_integration_connected", {
  workspace_members: 150,
  channels_connected: 3,
  features_enabled: ["notifications", "commands", "bot"]
});

// Sync completed
track("integration_sync_completed", {
  integration_type: "slack", // or "teams", "hris"
  records_synced: 250,
  sync_duration_seconds: 45,
  success_rate: 0.98
});
```

### Feature Discovery Events

```typescript
// Feature flag viewed
track("feature_flag_viewed", {
  flag_name: "ai_insights",
  flag_enabled: true,
  user_segment: "beta_tester"
});

// New feature announced
track("feature_announcement_viewed", {
  feature_name: "calendar_integration",
  announcement_type: "in_app_modal", // or "email", "banner"
  cta_clicked: false
});

// Help documentation viewed
track("help_article_viewed", {
  article_id: "how-to-create-assessments",
  category: "assessments",
  search_query: null, // or "create custom assessment"
  from_context: "onboarding_tooltip"
});
```

---

## Part 3: Funnel Analytics

### Funnel 1: User Onboarding

**Steps:**
1. Sign up → 100% (starting point)
2. Email verified
3. Profile completed
4. First assessment started
5. First assessment completed
6. First report viewed
7. Team joined (optional)

**Measurement:**
```sql
-- Onboarding funnel analysis
WITH signup_users AS (
  SELECT user_id, MIN(created_at) as signup_date
  FROM telemetry_events
  WHERE event_name = 'user_signed_up'
  GROUP BY user_id
),

verified_users AS (
  SELECT DISTINCT e.user_id
  FROM telemetry_events e
  JOIN signup_users s ON e.user_id = s.user_id
  WHERE e.event_name = 'email_verified'
    AND e.created_at > s.signup_date
    AND e.created_at < s.signup_date + INTERVAL '7 days'
),

first_assessment_users AS (
  SELECT DISTINCT e.user_id
  FROM telemetry_events e
  JOIN signup_users s ON e.user_id = s.user_id
  WHERE e.event_name = 'assessment_completed'
    AND e.created_at > s.signup_date
    AND e.created_at < s.signup_date + INTERVAL '7 days'
)

SELECT
  COUNT(DISTINCT s.user_id) as signed_up,
  COUNT(DISTINCT v.user_id) as verified,
  COUNT(DISTINCT v.user_id)::FLOAT / COUNT(DISTINCT s.user_id) as verified_rate,
  COUNT(DISTINCT f.user_id) as completed_assessment,
  COUNT(DISTINCT f.user_id)::FLOAT / COUNT(DISTINCT s.user_id) as assessment_completion_rate
FROM signup_users s
LEFT JOIN verified_users v ON s.user_id = v.user_id
LEFT JOIN first_assessment_users f ON s.user_id = f.user_id;
```

### Funnel 2: Assessment Creation

**Steps:**
1. Assessments page visited
2. "Create Assessment" clicked
3. Framework selected
4. Questions configured
5. Preview viewed
6. Assessment published
7. First response received

**Drop-off Analysis:**
```sql
-- Where do users drop off?
SELECT
  event_name,
  COUNT(DISTINCT user_id) as unique_users,
  LAG(COUNT(DISTINCT user_id)) OVER (ORDER BY event_order) as previous_step_users,
  (COUNT(DISTINCT user_id)::FLOAT /
   LAG(COUNT(DISTINCT user_id)) OVER (ORDER BY event_order)) as retention_rate
FROM (
  SELECT
    user_id,
    event_name,
    DENSE_RANK() OVER (PARTITION BY user_id ORDER BY created_at) as event_order
  FROM telemetry_events
  WHERE event_name IN (
    'assessments_page_viewed',
    'create_assessment_clicked',
    'framework_selected',
    'questions_configured',
    'assessment_previewed',
    'assessment_published',
    'assessment_response_received'
  )
) funnels
GROUP BY event_name, event_order
ORDER BY event_order;
```

---

## Part 4: Performance Telemetry

### Frontend Performance

```typescript
// Page load performance
track("page_load", {
  page: "/dashboard",
  load_time_ms: 1200,
  dom_content_loaded_ms: 800,
  first_contentful_paint_ms: 600,
  largest_contentful_paint_ms: 1100,
  cumulative_layout_shift: 0.05,
  first_input_delay_ms: 45,
  connection_type: "4g",
  device_type: "desktop"
});

// API call performance
track("api_call", {
  endpoint: "/api/v1/assessments",
  method: "GET",
  status_code: 200,
  response_time_ms: 320,
  cache_hit: true,
  retry_count: 0
});
```

### Backend Performance

```python
# API endpoint metrics
@telemetry.track_api_call
async def get_assessments(
    current_user: User,
    db: AsyncSession
):
    """
    Automatically tracks:
    - Request count
    - Response time (p50, p95, p99)
    - Error rate
    - Request rate per second
    """
    pass
```

**Metrics Collected:**
```python
api_metrics = {
    "endpoint": "/api/v1/assessments",
    "method": "GET",
    "timestamp": datetime.now(timezone.utc),
    "status_code": 200,
    "response_time_ms": 320,
    "user_id_hash": hash(user.id),  # Anonymized
    "organization_id": user.organization_id,
    "user_agent": request.headers.get("User-Agent"),
    "ip_address_hash": hash(request.client.host),  # Anonymized
}
```

---

## Part 5: Feature Adoption Metrics

### Adoption Calculation

**Metric 1: Penetration Rate**
```
Penetration = (Users who used feature / Total active users) × 100
```

**Metric 2: Activation Rate**
```
Activation = (Users who used feature 3+ times / Users who tried feature) × 100
```

**Metric 3: Intensity**
```
Intensity = Average usage per active user (per week)
```

**Example: AI Insights Feature**
```sql
WITH active_users AS (
  SELECT DISTINCT user_id
  FROM telemetry_events
  WHERE created_at >= NOW() - INTERVAL '30 days'
),

ai_insights_users AS (
  SELECT DISTINCT user_id
  FROM telemetry_events
  WHERE event_name = 'ai_insights_viewed'
    AND created_at >= NOW() - INTERVAL '30 days'
),

ai_insights_power_users AS (
  SELECT user_id, COUNT(*) as view_count
  FROM telemetry_events
  WHERE event_name = 'ai_insights_viewed'
    AND created_at >= NOW() - INTERVAL '30 days'
  GROUP BY user_id
  HAVING COUNT(*) >= 3
)

SELECT
  COUNT(DISTINCT au.user_id) as total_active_users,
  COUNT(DISTINCT ai.user_id) as ai_insights_users,
  (COUNT(DISTINCT ai.user_id)::FLOAT / COUNT(DISTINCT au.user_id)) * 100 as penetration_rate,
  COUNT(DISTINCT ap.user_id) as activated_users,
  (COUNT(DISTINCT ap.user_id)::FLOAT / COUNT(DISTINCT ai.user_id)) * 100 as activation_rate,
  AVG(ap.view_count) as intensity_per_user
FROM active_users au
LEFT JOIN ai_insights_users ai ON au.user_id = ai.user_id
LEFT JOIN ai_insights_power_users ap ON au.user_id = ap.user_id;
```

### Feature Health Score

```python
def calculate_feature_health(feature_name: str) -> Dict:
    """
    Calculate overall feature health score (0-100).

    Components:
    - Adoption: 30% (penetration rate)
    - Engagement: 30% (intensity, retention)
    - Satisfaction: 20% (CSAT, NPS)
    - Performance: 20% (load time, error rate)
    """
    adoption_score = get_adoption_score(feature_name)  # 0-100
    engagement_score = get_engagement_score(feature_name)  # 0-100
    satisfaction_score = get_satisfaction_score(feature_name)  # 0-100
    performance_score = get_performance_score(feature_name)  # 0-100

    health_score = (
        (adoption_score * 0.30) +
        (engagement_score * 0.30) +
        (satisfaction_score * 0.20) +
        (performance_score * 0.20)
    )

    return {
        "feature": feature_name,
        "health_score": round(health_score, 1),
        "adoption": adoption_score,
        "engagement": engagement_score,
        "satisfaction": satisfaction_score,
        "performance": performance_score,
        "status": "healthy" if health_score >= 70 else "needs_attention"
    }
```

---

## Part 6: Privacy & Compliance

### Data Minimization

**Collect Only What's Needed:**
- User interactions (what features are used)
- Aggregated metrics (how many, how often)
- Performance data (load times, errors)
- Funnel analytics (conversion rates)

**Never Collect:**
- User names (use hashed IDs)
- Email addresses (use hashed IDs)
- Assessment responses (already in database)
- PII (personally identifiable information)
- IP addresses (hash them)

### Anonymization

**User ID Hashing:**
```python
import hashlib

def anonymize_user_id(user_id: str) -> str:
    """
    Hash user ID for analytics (one-way, irreversible).
    """
    salt = "psychsync_analytics_salt_2025"  # Environment variable
    hashed = hashlib.sha256(f"{user_id}{salt}".encode()).hexdigest()
    return f"anon_{hashed[:16]}"
```

**IP Address Hashing:**
```python
def anonymize_ip(ip_address: str) -> str:
    """
    Hash IP address (remove last octet for privacy).
    """
    parts = ip_address.split(".")
    parts[-1] = "0"
    anonymized = ".".join(parts)
    return anonymized
```

### Consent Management

**Opt-In for Non-Essential:**
```typescript
// User consent preferences
const userConsent = {
  essential: true,      // Required (cannot opt-out)
  analytics: false,     // Optional (can opt-out)
  marketing: false,     // Optional (can opt-out)
  third_party: false    // Optional (can opt-out)
};

// Only track if consent given
if (userConsent.analytics) {
  track("feature_used", { feature: "analytics_dashboard" });
}
```

**Privacy Policy:**
```
We collect analytics data to improve PsychSync. You can opt-out at any time
in your privacy settings. Essential data (for security, billing) is always
collected and cannot be disabled.

Learn more: psychsync.com/privacy
```

---

## Part 7: Telemetry Infrastructure

### Data Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Frontend   │───>│  Event API   │───>│  Queue      │───>│  Processor   │
│  (Browser)  │    │  (FastAPI)   │    │  (Redis)    │    │  (Worker)    │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                                                                  │
                                                                  ▼
                                                           ┌─────────────┐
                                                           │  Warehouse   │
                                                           │ (PostgreSQL) │
                                                           └─────────────┘
                                                                  │
                                                                  ▼
                                                           ┌─────────────┐
                                                           │  Analytics   │
                                                           │  (Grafana)   │
                                                           └─────────────┘
```

### Event Schema

```sql
-- Telemetry events table
CREATE TABLE telemetry_events (
    id UUID PRIMARY KEY,
    event_name VARCHAR(100) NOT NULL,
    user_id_hash VARCHAR(64),  -- Anonymized user ID
    organization_id UUID,
    event_properties JSONB NOT NULL,
    user_agent TEXT,
    ip_address_hashed VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Indexes for performance
CREATE INDEX idx_telemetry_event_name ON telemetry_events(event_name);
CREATE INDEX idx_telemetry_user_hash ON telemetry_events(user_id_hash);
CREATE INDEX idx_telemetry_org_id ON telemetry_events(organization_id);
CREATE INDEX idx_telemetry_created_at ON telemetry_events(created_at);

-- Partition by month (data retention)
CREATE TABLE telemetry_events_y2025m01 PARTITION OF telemetry_events
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### Real-Time Analytics

```python
# Real-time feature usage dashboard
from prometheus_client import Counter, Histogram

# Metrics
feature_usage_counter = Counter(
    'feature_usage_total',
    'Total feature usage',
    ['feature_name', 'user_type']
)

feature_duration_histogram = Histogram(
    'feature_duration_seconds',
    'Feature usage duration',
    ['feature_name']
)

# Track usage
@telemetry.track_feature_usage
async def use_feature(feature_name: str, user: User):
    feature_usage_counter.labels(
        feature_name=feature_name,
        user_type=user.organization.tier
    ).inc()

    # Measure duration
    with feature_duration_histogram.labels(feature_name=feature_name).time():
        # Feature logic here
        pass
```

---

## Part 8: Alerting & Monitoring

### Real-Time Alerts

**Alert 1: Feature Adoption Drop**
**Condition:** Feature adoption drops by >20% week-over-week
**Severity:** P2 (High)
**Action:** Product investigation

**Alert 2: Error Rate Spike**
**Condition:** Error rate exceeds 5% for any feature
**Severity:** P1 (Critical)
**Action:** Engineering response

**Alert 3: Performance Degradation**
**Condition:** p95 response time >2x baseline
**Severity:** P2 (High)
**Action:** Performance investigation

**Alert 4: Anomaly Detection**
**Condition:** Unusual activity pattern (statistical anomaly)
**Severity:** P3 (Medium)
**Action:** Review and investigate

### Dashboard Queries

**Feature Adoption Trends:**
```sql
-- Weekly feature adoption (last 12 weeks)
SELECT
  DATE_TRUNC('week', created_at) as week,
  event_name,
  COUNT(DISTINCT user_id_hash) as unique_users
FROM telemetry_events
WHERE created_at >= NOW() - INTERVAL '12 weeks'
  AND event_name IN (
    'assessment_started',
    'team_created',
    'report_viewed',
    'ai_insights_viewed',
    'integration_connected'
  )
GROUP BY week, event_name
ORDER BY week DESC, event_name;
```

**Power User Identification:**
```sql
-- Top 10% most active users (for customer outreach)
WITH user_activity AS (
  SELECT
    user_id_hash,
    COUNT(*) as event_count,
    COUNT(DISTINCT event_name) as unique_features_used
  FROM telemetry_events
  WHERE created_at >= NOW() - INTERVAL '30 days'
  GROUP BY user_id_hash
),
percentile_threshold AS (
  SELECT percentile_cont(0.90) WITHIN GROUP (ORDER BY event_count) as p90
  FROM user_activity
)
SELECT
  u.user_id_hash,
  u.event_count,
  u.unique_features_used
FROM user_activity u, percentile_threshold p
WHERE u.event_count >= p.p90
ORDER BY u.event_count DESC
LIMIT 100;
```

---

## Part 9: A/B Testing Support

### Experiment Framework

```typescript
// A/B test assignment
const experiment = {
  name: "onboarding_flow_redesign",
  variants: ["control", "variant_a", "variant_b"],
  allocation: { control: 0.5, variant_a: 0.25, variant_b: 0.25 },
  target_metric: "onboarding_completion_rate",
  min_sample_size: 1000
};

// Assign user to variant
function assignVariant(user_id: string, experiment: Experiment): string {
  const hash = hashUserId(user_id + experiment.name);
  const bucket = hash % 100;

  let cumulative = 0;
  for (const [variant, allocation] of Object.entries(experiment.allocation)) {
    cumulative += allocation * 100;
    if (bucket < cumulative) {
      return variant;
    }
  }

  return "control"; // Fallback
}

// Track variant assignment
track("ab_test_assigned", {
  experiment: experiment.name,
  variant: assignedVariant,
  user_hash: anonymizeUserId(user_id)
});
```

### Experiment Analysis

```sql
-- A/B test results
WITH variant_users AS (
  SELECT
    event_properties->>'variant' as variant,
    user_id_hash
  FROM telemetry_events
  WHERE event_name = 'ab_test_assigned'
    AND event_properties->>'experiment' = 'onboarding_flow_redesign'
),

completed_users AS (
  SELECT
    v.variant,
    COUNT(DISTINCT e.user_id_hash) as completed
  FROM variant_users v
  JOIN telemetry_events e ON v.user_id_hash = e.user_id_hash
  WHERE e.event_name = 'onboarding_completed'
  GROUP BY v.variant
)

SELECT
  v.variant,
  COUNT(*) as total_users,
  c.completed,
  (c.completed::FLOAT / COUNT(*)) as conversion_rate,
  -- Statistical significance
  -- (Chi-square test or Z-test for proportions)
FROM variant_users v
LEFT JOIN completed_users c ON v.variant = c.variant
GROUP BY v.variant, c.completed;
```

---

## Part 10: Success Metrics

### Telemetry Health

**Data Quality:**
- Event volume: Target 1M+ events/day
- Processing lag: <5 seconds (real-time)
- Data loss: <0.01%

**Coverage:**
- User tracking: 100% of active users
- Feature coverage: 100% of features instrumented
- Platform coverage: Web, mobile, Slack, Teams

**Analytics Maturity:**
- Real-time dashboards: 100% of key metrics
- Automated alerts: 100% of critical metrics
- Self-service: 90% of questions answerable via dashboards

---

## Conclusion

PsychSync's telemetry system provides comprehensive visibility into user behavior, enabling data-driven decisions while respecting privacy.

**Key Capabilities:**
- ✅ 50+ core events tracked
- ✅ Real-time analytics dashboards
- ✅ Privacy-first design (anonymized, opt-out)
- ✅ A/B testing support
- ✅ Funnel and adoption analytics
- ✅ Performance monitoring

**Privacy Commitment:**
- ✅ No PII collected
- ✅ User consent respected
- ✅ Data minimization
- ✅ GDPR/CCPA compliant

`★ Insight ─────────────────────────────────────`
**Telemetry Paradox**: Collect too much data and you violate privacy and slow down your app. Collect too little and you're flying blind. The secret is "just enough" telemetry—track what matters (feature usage, funnels, performance) and skip what doesn't (mouse movements, keystrokes, scrolling). This PsychSync telemetry spec focuses on actionable metrics, not data hoarding.
`─────────────────────────────────────────────────`

**Data is the voice of your customer. Telemetry turns that voice into action. 📊**
