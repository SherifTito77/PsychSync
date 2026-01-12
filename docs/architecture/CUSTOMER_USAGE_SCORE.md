# Customer Usage Score Formula

**Version:** 1.0
**Date:** 2026-01-10
**Status:** Proposed Scoring Model

---

## Executive Summary

The Customer Usage Score (CUS) is a composite metric (0-100) that measures how effectively a customer is utilizing PsychSync's platform. It enables customer success teams to:

- Identify at-risk customers (proactive churn prevention)
- Recognize power users (advocacy opportunities)
- Measure feature adoption (product insights)
- Optimize onboarding (conversion optimization)

---

## 1. Formula Overview

### Core Formula

```
CUS = (Engagement × 0.30) +
     (Adoption × 0.25) +
     (Integration × 0.20) +
     (Growth × 0.15) +
     (Retention × 0.10)
```

**Where:**
- **Engagement:** How actively users interact with the platform
- **Adoption:** How many features are being used
- **Integration:** How deeply PsychSync is embedded in workflows
- **Growth:** Usage trajectory over time
- **Retention:** User stickiness and repeat usage

**Score Range:** 0-100 (higher = better usage)

---

## 2. Component Calculations

### 2.1 Engagement Score (0-100, 30% weight)

**Measures:** Frequency, depth, and consistency of platform usage

```python
def calculate_engagement_score(
    dau: int,                    # Daily Active Users
    mau: int,                    # Monthly Active Users
    avg_session_duration: float, # Minutes
    sessions_per_user: float,    # Per day
    days_since_last_login: int   # Recency
) -> float:
    """
    Engagement = (DAU/MAU × 40) +
                  (Session Duration × 30) +
                  (Sessions/User × 20) +
                  (Recency × 10)
    """

    # Component 1: User Stickiness (DAU/MAU ratio)
    dau_mau_ratio = dau / max(mau, 1)
    stickiness = min(dau_mau_ratio / 0.5, 1.0) * 40  # 50% DAU/MAU = max score
    # Industry avg: 20-30%, excellent: >50%

    # Component 2: Session Depth (Duration)
    duration_score = min(avg_session_duration / 15, 1.0) * 30
    # 15 min/session = max score, industry avg: 5-8 min

    # Component 3: Usage Frequency (Sessions per User)
    frequency_score = min(sessions_per_user / 3, 1.0) * 20
    # 3 sessions/day = max score, industry avg: 1-2

    # Component 4: Recency (Days Since Last Login)
    if days_since_last_login == 0:
        recency_score = 10  # Used today
    elif days_since_last_login <= 1:
        recency_score = 8   # Last 24-48 hours
    elif days_since_last_login <= 7:
        recency_score = 5   # Last week
    elif days_since_last_login <= 30:
        recency_score = 2   # Last month
    else:
        recency_score = 0   # Inactive

    return stickiness + duration_score + frequency_score + recency_score
```

**Example Calculation:**
```
DAU = 45, MAU = 120
Avg Session Duration = 12 minutes
Sessions/User = 2.5
Days Since Last Login = 2

Engagement = (45/120 ÷ 0.5 × 40) + (12 ÷ 15 × 30) + (2.5 ÷ 3 × 20) + 5
           = 30 + 24 + 16.7 + 5
           = 75.7 / 100
```

---

### 2.2 Adoption Score (0-100, 25% weight)

**Measures:** Breadth of feature usage across the platform

```python
def calculate_adoption_score(
    total_users: int,
    feature_usage: dict,  # {"assessments": 30, "analytics": 15, ...}
    org_features: List[str],  # Features org has access to
) -> float:
    """
    Adoption = (Core Features × 50) +
               (Advanced Features × 30) +
               (Integration Features × 20)
    """

    # Define feature tiers
    CORE_FEATURES = {
        "assessments",      # Taking assessments
        "responses",        # Viewing results
        "team_members",     # Team management
    }

    ADVANCED_FEATURES = {
        "analytics",        # Dashboards, reports
        "team_comparison",  # Cross-team analytics
        "assessment_builder", # Custom assessments
    }

    INTEGRATION_FEATURES = {
        "slack_integration",
        "email_integration",
        "api_access",
    }

    # Count available features per tier
    core_available = len(CORE_FEATURES & set(org_features))
    advanced_available = len(ADVANCED_FEATURES & set(org_features))
    integration_available = len(INTEGRATION_FEATURES & set(org_features))

    # Calculate adoption rates
    core_adopted = sum(
        feature_usage.get(f, 0) > 0
        for f in CORE_FEATURES
    ) / max(core_available, 1)

    advanced_adopted = sum(
        feature_usage.get(f, 0) > 0
        for f in ADVANCED_FEATURES
    ) / max(advanced_available, 1)

    integration_adopted = sum(
        feature_usage.get(f, 0) > 0
        for f in INTEGRATION_FEATURES
    ) / max(integration_available, 1)

    # Weighted score
    return (
        (core_adopted * 50) +
        (advanced_adopted * 30) +
        (integration_adopted * 20)
    )
```

**Example Calculation:**
```
Total Users: 50
Feature Usage:
  - assessments: 45 users (90%)
  - responses: 40 users (80%)
  - team_members: 35 users (70%)
  - analytics: 20 users (40%)
  - slack_integration: 10 users (20%)
  - api_access: 5 users (10%)

Core Adoption = (3/3 features used) = 100% → 50 points
Advanced Adoption = (1/1 features used) = 100% → 30 points
Integration Adoption = (2/2 features used) = 100% → 20 points

Adoption = 50 + 30 + 20 = 100 / 100
```

---

### 2.3 Integration Score (0-100, 20% weight)

**Measures:** How deeply PsychSync is embedded in workflows

```python
def calculate_integration_score(
    slack_messages_sent: int,       # Per month
    email_assessments_sent: int,    # Per month
    api_calls_made: int,            # Per month
    assessments_created: int,       # Per month
    total_assessments_taken: int,   # Per month
) -> float:
    """
    Integration = (Workflow Automation × 40) +
                  (Third-Party Connectors × 35) +
                  (API Usage × 25)
    """

    # Component 1: Workflow Automation
    # Ratio of automated vs manual assessment distribution
    if assessments_created > 0:
        automation_ratio = (email_assessments_sent + slack_messages_sent) / total_assessments_taken
        workflow_score = min(automation_ratio / 0.5, 1.0) * 40
        # 50% automated distribution = max score
    else:
        workflow_score = 0

    # Component 2: Third-Party Connectors
    connectors_used = 0
    if slack_messages_sent > 0:
        connectors_used += 1
    if email_assessments_sent > 0:
        connectors_used += 1

    connector_score = (connectors_used / 2) * 35  # Max 2 connectors currently

    # Component 3: API Usage
    api_score = min(api_calls_made / 1000, 1.0) * 25
    # 1000+ API calls/month = max score

    return workflow_score + connector_score + api_score
```

**Example Calculation:**
```
Slack Messages: 150/month
Email Assessments: 25/month
API Calls: 500/month
Assessments Created: 10/month
Total Assessments Taken: 200/month

Workflow = ((150+25)/200) ÷ 0.5 × 40 = 35.0
Connectors = (2/2) × 35 = 35.0
API = (500/1000) × 25 = 12.5

Integration = 35.0 + 35.0 + 12.5 = 82.5 / 100
```

---

### 2.4 Growth Score (0-100, 15% weight)

**Measures:** Usage trajectory over time

```python
def calculate_growth_score(
    usage_30_days_ago: int,      # DAU 30 days ago
    usage_7_days_ago: int,       # DAU 7 days ago
    usage_today: int,             # DAU today
    new_users_30d: int,          # New users in last 30 days
    total_users: int,
) -> float:
    """
    Growth = (User Growth × 40) +
              (Engagement Growth × 35) +
              (Feature Expansion × 25)
    """

    # Component 1: User Growth Rate
    if total_users > 0:
        new_user_rate = new_users_30d / total_users
        user_growth_score = min(new_user_rate / 0.2, 1.0) * 40
        # 20% new user growth = max score
    else:
        user_growth_score = 0

    # Component 2: Engagement Growth (DAU trend)
    # Calculate growth rate over periods
    if usage_30_days_ago > 0:
        growth_30d = (usage_today - usage_30_days_ago) / usage_30_days_ago
    elif usage_7_days_ago > 0:
        growth_30d = (usage_today - usage_7_days_ago) / usage_7_days_ago
    else:
        growth_30d = 0

    engagement_growth_score = max(min(growth_30d / 0.5, 1.0), 0) * 35
    # 50% growth = max score, negative growth = 0

    # Component 3: Feature Expansion
    # Track new features adopted in last 30 days (placeholder)
    # Would need feature adoption history table
    feature_expansion_score = 25  # Assume neutral if no data

    return user_growth_score + engagement_growth_score + feature_expansion_score
```

**Example Calculation:**
```
DAU 30 days ago: 25
DAU 7 days ago: 35
DAU today: 45
New users (30d): 10
Total users: 80

User Growth = (10/80) ÷ 0.2 × 40 = 25.0
Engagement Growth = ((45-25)/25) ÷ 0.5 × 35 = 35.0
Feature Expansion = 25 (neutral)

Growth = 25.0 + 35.0 + 25 = 85.0 / 100
```

---

### 2.5 Retention Score (0-100, 10% weight)

**Measures:** User stickiness and repeat usage

```python
def calculate_retention_score(
    new_users_30d: int,
    retained_users_30d: int,  # Still active after 30 days
    repeat_usage_rate: float,  # % of users with 2+ sessions/month
    avg_tenure_days: float,    # Average account age
) -> float:
    """
    Retention = (30-Day Retention × 50) +
               (Repeat Usage × 30) +
               (Account Longevity × 20)
    """

    # Component 1: Cohort Retention (Day 30)
    if new_users_30d > 0:
        retention_rate = retained_users_30d / new_users_30d
        retention_score = min(retention_rate / 0.4, 1.0) * 50
        # 40% retention at day 30 = max score
        # Industry avg: 20-30%, excellent: >40%
    else:
        retention_score = 0

    # Component 2: Repeat Usage
    # % of users with 2+ sessions in past month
    repeat_score = min(repeat_usage_rate / 0.5, 1.0) * 30
    # 50% repeat users = max score

    # Component 3: Account Longevity
    longevity_score = min(avg_tenure_days / 180, 1.0) * 20
    # 6 months avg tenure = max score

    return retention_score + repeat_score + longevity_score
```

**Example Calculation:**
```
New Users (30d): 20
Retained (30d): 8 (40%)
Repeat Usage Rate: 35%
Avg Tenure: 90 days

Retention = (8/20) ÷ 0.4 × 50 = 50.0
Repeat = 0.35 ÷ 0.5 × 30 = 21.0
Longevity = (90/180) × 20 = 10.0

Retention = 50.0 + 21.0 + 10.0 = 81.0 / 100
```

---

## 3. Score Interpretation

### 3.1 Score Categories

| Score Range | Category | Description | Action |
|------------|----------|-------------|--------|
| **90-100** | **Power User** | Maximum value extraction, deep integration | 🌟 Case studies, testimonials, referral program |
| **70-89** | **Healthy** | Good engagement, solid adoption | ✅ Maintain relationship, upsell opportunities |
| **50-69** | **Growing** | Moderate usage, potential not realized | 📈 Proactive outreach, training resources |
| **30-49** | **At Risk** | Low engagement, churn likely | ⚠️ Customer success intervention, survival risk |
| **0-29** | **Critical** | Barely active, likely to churn | 🚨 Urgent intervention, save campaign |

### 3.2 Component Analysis

**Weak Component Identification:**
```
If Engagement < 50:
  → Low DAU/MAU, poor session frequency
  → Action: User re-engagement campaigns, feature training

If Adoption < 50:
  → Only using basic features
  → Action: Feature demos, use case consultations

If Integration < 50:
  → Manual workflows, not embedded
  → Action: Workflow automation, connector setup

If Growth < 50:
  → Flat or declining usage
  → Action: Success check-ins, value reinforcement

If Retention < 50:
  → High churn, low stickiness
  → Action: Onboarding optimization, quick wins
```

---

## 4. Implementation

### 4.1 Data Collection

```python
# app/analytics/usage_collector.py
class UsageCollector:
    """Collect and aggregate usage metrics"""

    async def collect_daily_metrics(self, org_id: UUID) -> dict:
        """Collect all metrics for daily score calculation"""

        # Engagement metrics
        dau = await self.get_dau(org_id)
        mau = await self.get_mau(org_id)
        avg_duration = await self.get_avg_session_duration(org_id, days=1)

        # Adoption metrics
        feature_usage = await self.get_feature_usage(org_id, days=30)
        org_features = await self.get_org_features(org_id)

        # Integration metrics
        slack_msgs = await self.get_slack_message_count(org_id, days=30)
        email_assessments = await self.get_email_assessment_count(org_id, days=30)
        api_calls = await self.get_api_call_count(org_id, days=30)

        return {
            "dau": dau,
            "mau": mau,
            "avg_session_duration": avg_duration,
            "feature_usage": feature_usage,
            "org_features": org_features,
            "slack_messages_sent": slack_msgs,
            "email_assessments_sent": email_assessments,
            "api_calls_made": api_calls,
        }

    async def calculate_cus(self, org_id: UUID) -> float:
        """Calculate Customer Usage Score"""
        metrics = await self.collect_daily_metrics(org_id)

        # Get historical data for growth/retention
        historical = await self.get_historical_metrics(org_id, days=30)

        engagement = calculate_engagement_score(**metrics)
        adoption = calculate_adoption_score(**metrics)
        integration = calculate_integration_score(**metrics)
        growth = calculate_growth_score(**historical)
        retention = calculate_retention_score(**historical)

        cus = (
            (engagement * 0.30) +
            (adoption * 0.25) +
            (integration * 0.20) +
            (growth * 0.15) +
            (retention * 0.10)
        )

        # Store score
        await self.store_cus(org_id, cus, {
            "engagement": engagement,
            "adoption": adoption,
            "integration": integration,
            "growth": growth,
            "retention": retention
        })

        return round(cus, 2)
```

### 4.2 Database Schema

```sql
CREATE TABLE customer_usage_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),

    -- Overall Score
    score FLOAT NOT NULL,
    score_category VARCHAR(20),  -- 'power_user', 'healthy', etc.

    -- Component Scores
    engagement_score FLOAT,
    adoption_score FLOAT,
    integration_score FLOAT,
    growth_score FLOAT,
    retention_score FLOAT,

    -- Metrics Snapshot
    metrics_json JSONB,  -- Full metrics for debugging

    -- Trend Data
    previous_score FLOAT,
    score_change FLOAT,

    -- Timestamps
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    calculated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(organization_id, period_end)
);

CREATE INDEX idx_cus_org_date ON customer_usage_scores(organization_id, period_end);
CREATE INDEX idx_cus_score ON customer_usage_scores(score);
```

### 4.3 Scheduled Calculation

```python
# app/analytics/tasks.py
@celery.task
def calculate_all_cus():
    """Daily task to calculate CUS for all organizations"""

    orgs = db.session.query(Organization).filter(
        Organization.is_active == True
    ).all()

    for org in orgs:
        try:
            calculate_cus.delay(org.id)
        except Exception as e:
            logger.error(f"Failed to calculate CUS for {org.id}: {e}")

    logger.info(f"Calculated CUS for {len(orgs)} organizations")

# Schedule: Daily at 2 AM
celery.conf.beat_schedule = {
    'calculate-daily-cus': {
        'task': 'app.analytics.tasks.calculate_all_cus',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

---

## 5. Benchmarking

### 5.1 Industry Benchmarks

| Metric | Industry Average | Top 10% | PsychSync Target |
|--------|------------------|---------|------------------|
| **DAU/MAU Ratio** | 25% | 50% | 30% |
| **Session Duration** | 5 min | 15 min | 8 min |
| **Sessions/User/Day** | 1.2 | 3.0 | 1.5 |
| **30-Day Retention** | 20% | 40% | 25% |
| **Feature Adoption** | 30% | 70% | 45% |
| **API Usage/Month** | 100 | 1000+ | 250 |

### 5.2 CUS Distribution Analysis

```sql
-- Analyze CUS distribution across all orgs
SELECT
    CASE
        WHEN score >= 90 THEN 'Power User (90-100)'
        WHEN score >= 70 THEN 'Healthy (70-89)'
        WHEN score >= 50 THEN 'Growing (50-69)'
        WHEN score >= 30 THEN 'At Risk (30-49)'
        ELSE 'Critical (0-29)'
    END as category,
    COUNT(*) as org_count,
    AVG(score) as avg_score,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY score) as median_score
FROM customer_usage_scores
WHERE period_end >= NOW() - INTERVAL '7 days'
GROUP BY category
ORDER BY category;
```

---

## 6. Use Cases

### 6.1 Customer Health Dashboard

```python
@router.get("/api/v1/admin/analytics/customer-health")
async def get_customer_health_dashboard(
    min_score: float = 0,
    max_score: float = 100,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_admin)
):
    """
    Customer health monitoring dashboard
    Shows CUS distribution, at-risk customers, trends
    """

    query = db.session.query(CustomerUsageScore)

    if category:
        query = query.filter(score_category=category)

    results = query.order_by(CustomerUsageScore.score.asc()).all()

    return {
        "total_customers": len(results),
        "avg_score": mean(r.score for r in results),
        "at_risk_customers": [r for r in results if r.score < 50],
        "top_performers": [r for r in results if r.score >= 90],
    }
```

### 6.2 Churn Prediction Model

```python
def predict_churn_probability(cus_history: List[float]) -> float:
    """
    Use CUS trend to predict churn probability

    Churn Risk Indicators:
    - Declining score (-10 points over 90 days)
    - Low retention (<30)
    - Flat or negative growth
    """
    if len(cus_history) < 3:
        return 0.0  # Not enough data

    # Calculate trend
    recent_score = cus_history[-1]
    previous_score = cus_history[0]
    score_change = recent_score - previous_score

    # Base risk on score level
    base_risk = max(0, (50 - recent_score) / 50)

    # Adjust for trend
    if score_change < -10:
        trend_multiplier = 1.5
    elif score_change < 0:
        trend_multiplier = 1.2
    else:
        trend_multiplier = 0.8

    churn_probability = min(base_risk * trend_multiplier, 1.0)

    return round(churn_probability, 2)
```

---

## 7. Alerts & Actions

### 7.1 Automated Alert Rules

```python
# app/analytics/alerts.py
class UsageAlerts:

    @staticmethod
    async def check_critical_customers():
        """Identify customers needing immediate attention"""

        critical = db.session.query(CustomerUsageScore).filter(
            CustomerUsageScore.score < 30,
            CustomerUsageScore.period_end >= NOW() - interval(days=7)
        ).all()

        for cus in critical:
            # Send alert to customer success
            await send_slack_alert(
                f"🚨 CRITICAL: {cus.organization.name} (Score: {cus.score})"
            )

            # Create task for CSM
            await create_intervention_task(
                org_id=cus.organization_id,
                priority="high",
                reason="Critical usage score",
            )

    @staticmethod
    async def check_declining_customers():
        """Identify customers with declining scores"""

        scores = db.session.query(CustomerUsageScore).filter(
            CustomerUsageScore.period_end >= NOW() - interval(days=90)
        ).all()

        for org_id in set(s.organization_id for s in scores):
            org_scores = [s for s in scores if s.organization_id == org_id]
            if len(org_scores) >= 2:
                latest = org_scores[-1].score
                earliest = org_scores[0].score

                if latest - earliest < -15:  # Declined by 15+ points
                    await send_email(
                        to="customer-success@psychsync.com",
                        subject=f"⚠️ Declining Usage: {org_id}",
                        body=f"Score dropped from {earliest} to {latest}"
                    )
```

### 7.2 Proactive Outreach Triggers

```python
OUTREACH_TRIGGERS = {
    "cus_below_50": {
        "condition": lambda c: c.score < 50,
        "action": "schedule_success_call",
        "urgency": "high",
    },
    "cus_decline_10": {
        "condition": lambda c: c.score_change < -10,
        "action": "send_resources",
        "urgency": "medium",
    },
    "new_customer_day_30": {
        "condition": lambda c: c.days_since_signup == 30 and c.score < 40,
        "action": "onboarding_checkin",
        "urgency": "medium",
    },
    "power_user_opportunity": {
        "condition": lambda c: c.score >= 90,
        "action": "request_case_study",
        "urgency": "low",
    }
}
```

---

## 8. A/B Testing & Optimization

### 8.1 Weight Optimization

```python
# A/B test different weight configurations
WEIGHT_VARIANTS = [
    {"engagement": 0.35, "adoption": 0.25, "integration": 0.15, "growth": 0.15, "retention": 0.10},
    {"engagement": 0.30, "adoption": 0.30, "integration": 0.20, "growth": 0.10, "retention": 0.10},
    {"engagement": 0.25, "adoption": 0.25, "integration": 0.25, "growth": 0.15, "retention": 0.10},
]

def validate_weights(weights: dict, actual_churn: List[float]) -> float:
    """Validate if CUS correlates with churn (lower = better)"""
    from sklearn.metrics import roc_auc_score

    cus_scores = [calculate_cus(org, weights) for org in orgs]

    # Invert CUS (higher = better, so lower churn risk)
    auc = roc_auc_score(actual_churn, [-s for s in cus_scores])

    return auc
```

---

## 9. Reporting

### 9.1 Executive Report

```python
@router.get("/api/v1/analytics/cus-report")
async def generate_cus_report(
    period: str = "monthly",
    format: str = "pdf"
):
    """
    Generate comprehensive CUS report for leadership

    Includes:
    - Overall distribution
    - Component breakdowns
    - Trend analysis
    - At-risk customers
    - Success stories
    - Recommendations
    """

    orgs = await get_all_active_orgs()
    scores = [await calculate_cus(org.id) for org in orgs]

    report = {
        "period": period,
        "total_customers": len(scores),
        "average_score": mean(scores),
        "distribution": {
            "power_user": len([s for s in scores if s >= 90]),
            "healthy": len([s for s in scores if 70 <= s < 90]),
            "growing": len([s for s in scores if 50 <= s < 70]),
            "at_risk": len([s for s in scores if 30 <= s < 50]),
            "critical": len([s for s in scores if s < 30]),
        },
        "top_5_customers": sorted(scores, reverse=True)[:5],
        "bottom_5_customers": sorted(scores)[:5],
        "trends": await_get_score_trends(days=90),
        "churn_prediction": await_predict_churn(scores),
    }

    if format == "pdf":
        return generate_pdf(report)
    else:
        return report
```

---

## 10. Success Metrics

- ✅ **Predictive Power:** CUS <30 predicts 80%+ of churn within 90 days
- ✅ **Actionability:** Each component has clear improvement actions
- ✅ **Simplicity:** Easy to explain to non-technical stakeholders
- ✅ **Computation:** <100ms to calculate for any org
- ✅ **Accuracy:** <5% false positive rate (identifying at-risk customers)

**Target Outcomes:**
- Reduce churn by 15% through early intervention
- Increase feature adoption by 20% via targeted outreach
- Improve customer satisfaction by identifying pain points early
