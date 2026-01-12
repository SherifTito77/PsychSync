# Team Analytics Data Model

**Version:** 1.0
**Date:** 2026-01-10
**Status:** Proposed Data Model

---

## Executive Summary

This document defines a comprehensive data model for team-level analytics, enabling PsychSync to provide actionable insights on team dynamics, personality composition, performance trends, and growth trajectories.

---

## 1. Core Analytics Entities

### 1.1 Team Analytics Snapshot

```python
class TeamAnalyticsSnapshot(Base):
    """
    Point-in-time snapshot of team metrics
    Generated daily/weekly/monthly
    """
    __tablename__ = "team_analytics_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    # Snapshot Metadata
    period_type = Column(Enum(PeriodType), nullable=False)  # DAILY, WEEKLY, MONTHLY
    period_start = Column TIMESTAMP(timezone=True), nullable=False
    period_end = Column TIMESTAMP(timezone=True), nullable=False
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))

    # Team Size & Composition
    total_members = Column(Integer, nullable=False)
    active_members = Column(Integer)  # Members who completed assessments
    new_members = Column(Integer)
    departed_members = Column(Integer)

    # Assessment Engagement
    assessments_completed = Column(Integer, default=0)
    assessments_in_progress = Column(Integer, default=0)
    assessment_completion_rate = Column(Float)  # 0.0 to 1.0

    # Performance Metrics
    avg_team_score = Column(Float)  # Average assessment score
    score_distribution = Column(JSONB)  # Histogram of scores
    top_performers = Column(ARRAY(UUID))  # User IDs of top 10%
    needs_improvement = Column(ARRAY(UUID))  # User IDs of bottom 25%

    # Personality Diversity Metrics
    personality_diversity_index = Column(Float)  # 0.0 to 1.0
    trait_balance = Column(JSONB)  # Big Five distribution
    role_alignment = Column(Float)  # Match between personality & role

    # Team Dynamics
    communication_score = Column(Float)  # From email/Slack analysis
    collaboration_index = Column(Float)  # Cross-team interactions
    conflict_indicators = Column(JSONB)  # Early warning signs

    # Well-being Metrics
    avg_stress_level = Column(Float)  # 0.0 to 1.0
    burnout_risk_members = Column(ARRAY(UUID))  # At-risk user IDs
    wellness_score = Column(Float)  # Composite well-being

    # Growth & Development
    skill_gaps = Column(JSONB)  # Areas needing development
    high_potential_members = Column(ARRAY(UUID))
    learning_engagement = Column(Float)  # Training participation

    # Indexes
    __table_args__ = (
        Index('idx_team_snapshot_team_period', 'team_id', 'period_start', 'period_end'),
        Index('idx_team_snapshot_org_period', 'organization_id', 'period_start'),
    )
```

### 1.2 Team Personality Profile

```python
class TeamPersonalityProfile(Base):
    """
    Aggregated personality profile for the entire team
    Based on aggregated Big Five, MBTI, or other framework results
    """
    __tablename__ = "team_personality_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    assessment_framework = Column(String(50), nullable=False)  # 'big_five', 'mbti', etc.
    snapshot_date = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))

    # Team-Level Traits (Averages)
    avg_openness = Column(Float)  # Big Five: Openness
    avg_conscientiousness = Column(Float)
    avg_extraversion = Column(Float)
    avg_agreeableness = Column(Float)
    avg_neuroticism = Column(Float)

    # Trait Variance (Diversity)
    openness_variance = Column(Float)
    conscientiousness_variance = Column(Float)
    extraversion_variance = Column(Float)
    agreeableness_variance = Column(Float)
    neuroticism_variance = Column(Float)

    # Personality Clusters
    dominant_type = Column(String(50))  # Most common personality
    personality_clusters = Column(JSONB)  # K-means clusters
    cluster_distribution = Column(JSONB)  # % of team per cluster

    # Role Fit Analysis
    role_compatibility_score = Column(Float)  # Match with job requirements
    recommended_role_adjustments = Column(JSONB)

    # Team Composition Advice
    strengths = Column(ARRAY(String))
    weaknesses = Column(ARRAY(String))
    ideal_additions = Column(JSONB)  # Personality types to recruit
```

### 1.3 Team Performance Trend

```python
class TeamPerformanceTrend(Base):
    """
    Longitudinal tracking of team performance over time
    Enables trend analysis and predictive modeling
    """
    __tablename__ = "team_performance_trends"

    id = Column(UUID(as_uuid=True), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)  # 'avg_score', 'engagement', etc.
    recorded_at = Column(TIMESTAMP(timezone=True), nullable=False)

    # Metric Values
    value = Column(Float, nullable=False)
    baseline_value = Column(Float)  # Initial measurement
    variance_from_baseline = Column(Float)
    percentile_rank = Column(Float)  # vs other teams

    # Trend Indicators
    moving_avg_7 = Column(Float)  # 7-day moving average
    moving_avg_30 = Column(Float)  # 30-day moving average
    trend_direction = Column(String(10))  # 'up', 'down', 'stable'
    trend_strength = Column(Float)  # 0.0 to 1.0

    # Predictions
    predicted_value_30 = Column(Float)  # ML prediction in 30 days
    prediction_confidence = Column(Float)  # 0.0 to 1.0

    __table_args__ = (
        Index('idx_trend_team_metric', 'team_id', 'metric_name', 'recorded_at'),
        Index('idx_trend_team_date', 'team_id', 'recorded_at'),
    )
```

### 1.4 Team Member Analytics

```python
class TeamMemberAnalytics(Base):
    """
    Individual-level analytics within team context
    Enables comparison against team averages
    """
    __tablename__ = "team_member_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    period_start = Column(TIMESTAMP(timezone=True), nullable=False)
    period_end = Column(TIMESTAMP(timezone=True), nullable=False)

    # Performance vs Team Average
    personal_score = Column(Float)
    team_avg_score = Column(Float)
    percentile_in_team = Column(Float)  # 0.0 to 1.0
    performance_tier = Column(String(20))  # 'top', 'upper_mid', 'lower_mid', 'bottom'

    # Contribution Metrics
    assessments_completed = Column(Integer)
    response_quality_score = Column(Float)  # Thoughtfulness, completeness
    participation_rate = Column(Float)  # Responses sent / responses requested

    # Personality Fit
    personality_fit_score = Column(Float)  # Match with team culture
    cultural_contribution = Column(Float)  # Adds to team diversity?
    role_alignment_score = Column(Float)

    # Collaboration Indicators
    peer_ratings_avg = Column(Float)  # From 360 feedback
    mentorship_given = Column(Integer)  # # of mentees helped
    mentorship_received = Column(Float)  # Quality of mentoring received

    # Growth Metrics
    skill_development_rate = Column(Float)  # Improvement over time
    goal_completion_rate = Column(Float)
    potential_score = Column(Float)  # 9-box grid potential

    # Risk Flags
    burnout_risk = Column(Float)  # 0.0 to 1.0
    flight_risk = Column(Float)  # Likelihood of leaving
    engagement_decline = Column(Boolean)  # Dropping participation?

    __table_args__ = (
        Index('idx_member_analytics_user_period', 'user_id', 'period_start'),
        Index('idx_member_analytics_team_period', 'team_id', 'period_start'),
    )
```

---

## 2. Assessment-Specific Analytics

### 2.1 Team Assessment Summary

```python
class TeamAssessmentSummary(Base):
    """
    Aggregated results for assessments completed by team
    One row per assessment type per period
    """
    __tablename__ = "team_assessment_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    assessment_type = Column(String(50), nullable=False)  # 'big_five', 'mbti', etc.
    period_start = Column(TIMESTAMP(timezone=True), nullable=False)
    period_end = Column(TIMESTAMP(timezone=True), nullable=False)

    # Completion Stats
    total_team_members = Column(Integer)
    completed_count = Column(Integer)
    completion_rate = Column(Float)

    # Score Distribution
    min_score = Column(Float)
    max_score = Column(Float)
    avg_score = Column(Float)
    median_score = Column(Float)
    std_deviation = Column(Float)
    percentiles = Column(JSONB)  # {25: value, 50: value, 75: value, 90: value}

    # Comparison Data
    vs_organization_avg = Column(Float)  # Difference from org average
    vs_industry_benchmark = Column(Float)  # Difference from industry
    percentile_vs_other_teams = Column(Float)

    # Dimension-Level Breakdown
    dimension_scores = Column(JSONB)
    # Example: {
    #   "openness": {"avg": 0.75, "std": 0.12, "min": 0.45, "max": 0.95},
    #   "conscientiousness": {"avg": 0.68, "std": 0.15, "min": 0.30, "max": 0.92}
    # }

    # Insights
    strengths = Column(ARRAY(String))  # Top 3 scoring dimensions
    weaknesses = Column(ARRAY(String))  # Bottom 3 scoring dimensions
    outliers = Column(JSONB)  # Unusual scores worth investigating
    recommendations = Column(ARRAY(String))
```

### 2.2 Team Comparison Analytics

```python
class TeamComparison(Base):
    """
    Cross-team analytics for benchmarking
    Enables team-vs-team and team-vs-org comparisons
    """
    __tablename__ = "team_comparisons"

    id = Column(UUID(as_uuid=True), primary_key=True)
    team_a_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    team_b_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))  # NULL for org comparison
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    comparison_date = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))

    # Similarity Score
    overall_similarity = Column(Float)  # 0.0 to 1.0 (1 = identical)
    personality_similarity = Column(Float)
    performance_similarity = Column(Float)
    composition_similarity = Column(Float)

    # Dimensional Comparison
    dimension_differences = Column(JSONB)
    # Example: {
    #   "openness": {"team_a": 0.75, "team_b": 0.68, "diff": 0.07},
    #   "conscientiousness": {"team_a": 0.82, "team_b": 0.79, "diff": 0.03}
    # }

    # Relative Performance
    performance_gap = Column(Float)  # team_a_avg - team_b_avg
    statistical_significance = Column(Float)  # p-value
    confidence_interval = Column(JSONB)  # {"lower": 0.02, "upper": 0.15}

    # Best Practices
    practices_team_a_does_better = Column(ARRAY(String))
    practices_team_b_does_better = Column(ARRAY(String))
    collaborative_opportunities = Column(ARRAY(String))
```

---

## 3. Predictive Analytics Models

### 3.1 Team Performance Prediction

```python
class TeamPerformancePrediction(Base):
    """
    ML-based predictions for team future performance
    """
    __tablename__ = "team_performance_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    model_version = Column(String(50), nullable=False)  # e.g., "v1.2.0"
    prediction_date = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))

    # Prediction Targets
    target_period_start = Column(TIMESTAMP(timezone=True), nullable=False)
    target_period_end = Column(TIMESTAMP(timezone=True), nullable=False)

    # Predicted Metrics
    predicted_avg_score = Column(Float)
    predicted_retention_rate = Column(Float)
    predicted_engagement_score = Column(Float)
    predicted_collaboration_score = Column(Float)

    # Confidence Intervals
    prediction_confidence = Column(Float)  # 0.0 to 1.0
    confidence_interval_low = Column(JSONB)
    confidence_interval_high = Column(JSONB)

    # Feature Importance (Explainability)
    top_influencing_factors = Column(JSONB)
    # Example: [
    #   {"feature": "personality_diversity", "importance": 0.35},
    #   {"feature": "team_size", "importance": 0.22},
    #   {"feature": "communication_frequency", "importance": 0.18}
    # ]

    # Risk Assessment
    performance_decline_risk = Column(Float)  # 0.0 to 1.0
    key_risk_factors = Column(ARRAY(String))
    mitigation_strategies = Column(ARRAY(String))
```

### 3.2 Team Succession Planning

```python
class TeamSuccessionPlanning(Base):
    """
    Analytics for leadership pipeline and critical roles
    """
    __tablename__ = "team_succession_planning"

    id = Column(UUID(as_uuid=True), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    analysis_date = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))

    # Critical Roles
    critical_roles = Column(JSONB)
    # Example: [
    #   {"role": "tech_lead", "incumbent": "user_id", "readiness": 0.6},
    #   {"role": "product_owner", "incumbent": "user_id", "readiness": 0.8}
    # ]

    # Replacement Candidates
    replacement_candidates = Column(JSONB)
    # Example: {
    #   "tech_lead": [
    #     {"user_id": "xxx", "readiness": 0.9, "time_to_readiness": 6},
    #     {"user_id": "yyy", "readiness": 0.7, "time_to_readiness": 12}
    #   ]
    # }

    # Gap Analysis
    readiness_gap = Column(Float)  # Average readiness vs required
    pipeline_strength = Column(Float)  # 0.0 to 1.0
    time_to_fill_critical_roles = Column(Integer)  # Months

    # Action Plans
    development_priorities = Column(JSONB)
    recruitment_needs = Column(JSONB)
    knowledge_transfer_risks = Column(ARRAY(String))
```

---

## 4. Real-Time Analytics

### 4.1 Team Activity Stream

```python
class TeamActivityStream(Base):
    """
    Real-time team activities for live dashboards
    Retained for 90 days then archived
    """
    __tablename__ = "team_activity_stream"

    id = Column(UUID(as_uuid=True), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    timestamp = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    # Activity Details
    activity_type = Column(String(50), nullable=False)  # 'assessment_completed', 'user_joined', etc.
    activity_source = Column(String(50))  # 'web', 'mobile', 'api', 'slack'
    metadata = Column(JSONB)  # Flexible context

    # Engagement
    visibility = Column(String(20))  # 'public', 'team', 'private'
    reaction_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)

    # Analytics Flags
    is_milestone = Column(Boolean, default=False)
    sentiment = Column(String(20))  # 'positive', 'neutral', 'negative'

    __table_args__ = (
        Index('idx_activity_team_time', 'team_id', 'timestamp'),
        Index('idx_activity_user_time', 'user_id', 'timestamp'),
    )
```

### 4.2 Team Health Indicators

```python
class TeamHealthIndicators(Base):
    """
    Daily health check metrics for team wellness
    Triggers alerts when thresholds exceeded
    """
    __tablename__ = "team_health_indicators"

    id = Column(UUID(as_uuid=True), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    measured_at = Column(TIMESTAMP(timezone=True), nullable=False)

    # Engagement Metrics
    active_users_today = Column(Integer)
    dau_mau_ratio = Column(Float)  # Daily Active / Monthly Active
    session_duration_avg = Column(Float)  # Minutes
    actions_per_session_avg = Column(Float)

    # Sentiment Metrics
    avg_sentiment_score = Column(Float)  # -1.0 to 1.0
    negative_sentiment_count = Column(Integer)
    conflict_indicators = Column(Integer)

    # Wellness Metrics
    stress_indicators = Column(Integer)  # High stress keywords
    burnout_alerts = Column(Integer)  # Declining engagement + high stress
    help_requests = Column(Integer)

    # Performance Metrics
    assessment_completion_rate = Column(Float)
    goal_progress_avg = Column(Float)

    # Health Score (Composite)
    overall_health_score = Column(Float)  # 0.0 to 1.0
    health_status = Column(String(20))  # 'excellent', 'good', 'fair', 'poor', 'critical'

    # Alerts
    alert_triggered = Column(Boolean, default=False)
    alert_type = Column(ARRAY(String))  # ['low_engagement', 'high_conflict', 'burnout_risk']
    recommended_actions = Column(ARRAY(String))
```

---

## 5. Integration & Data Flow

### 5.1 ETL Pipeline Architecture

```
┌─────────────────────────────────────────────────────┐
│              Data Ingestion Layer                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Web      │  │ Mobile   │  │  Third   │        │
│  │ Events   │  │ Events   │  │  Party   │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼────────────┼────────────┼────────────────┘
        │            │            │
        ▼            ▼            ▼
┌─────────────────────────────────────────────────────┐
│           Event Queue (Redis/Celery)                │
│  - Validation                                        │
│  - Enrichment (add tenant context)                  │
│  - Deduplication                                     │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐      ┌──────────────┐
│ Real-time     │      │ Batch        │
│ Processing    │      │ Processing   │
│ (Activity     │      │ (Snapshots,  │
│  Stream)      │      │  Aggregates) │
└───────┬───────┘      └──────┬───────┘
        │                     │
        ▼                     ▼
┌─────────────────────────────────────────────────────┐
│           Analytics Database                         │
│  - Timeseries (trends)                              │
│  - Aggregates (snapshots)                            │
│  - Fact tables (comparison)                          │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│           BI & Visualization                        │
│  - Dashboards                                        │
│  - Reports                                           │
│  - Alerts                                            │
└─────────────────────────────────────────────────────┘
```

### 5.2 Data Retention Policy

```python
DATA_RETENTION = {
    "team_activity_stream": 90,  # days
    "team_health_indicators": 365,  # days (1 year)
    "team_analytics_snapshots": None,  # forever
    "team_performance_trends": None,  # forever
    "team_member_analytics": 1825,  # days (5 years)
    "team_performance_predictions": 365,  # days (1 year)
}
```

---

## 6. Query Examples

### 6.1 Get Team Trend Analysis

```sql
WITH monthly_avg AS (
    SELECT
        DATE_TRUNC('month', period_end) as month,
        AVG(avg_team_score) as team_avg,
        AVG(assessment_completion_rate) as completion_avg
    FROM team_analytics_snapshots
    WHERE team_id = :team_id
      AND period_end >= NOW() - INTERVAL '12 months'
    GROUP BY month
)
SELECT
    month,
    team_avg,
    completion_avg,
    LAG(team_avg) OVER (ORDER BY month) as prev_month_avg,
    team_avg - LAG(team_avg) OVER (ORDER BY month) as month_over_month
FROM monthly_avg
ORDER BY month DESC;
```

### 6.2 Identify At-Risk Teams

```sql
SELECT
    t.id,
    t.name,
    tas.overall_health_score,
    tas.burnout_alerts,
    tas.active_users_today,
    tas.dau_mau_ratio
FROM teams t
JOIN team_health_indicators tas ON tas.team_id = t.id
WHERE tas.measured_at >= NOW() - INTERVAL '7 days'
  AND (
    tas.overall_health_score < 0.4
    OR tas.burnout_alerts > 3
    OR tas.dau_mau_ratio < 0.3
  )
ORDER BY tas.overall_health_score ASC;
```

### 6.3 Team vs Organization Benchmark

```sql
WITH team_stats AS (
    SELECT
        AVG(avg_team_score) as avg_score,
        STDDEV(avg_team_score) as score_stddev
    FROM team_analytics_snapshots
    WHERE organization_id = :org_id
      AND period_end >= NOW() - INTERVAL '30 days'
),
org_avg AS (
    SELECT AVG(avg_team_score) as org_avg
    FROM team_analytics_snapshots
    WHERE organization_id = :org_id
      AND period_end >= NOW() - INTERVAL '30 days'
)
SELECT
    t.name,
    tas.avg_team_score,
    oa.org_avg,
    (tas.avg_team_score - oa.org_avg) / NULLIF(ts.score_stddev, 0) as z_score,
    PERCENT_RANK() OVER (ORDER BY tas.avg_team_score) as percentile_rank
FROM teams t
JOIN team_analytics_snapshots tas ON tas.team_id = t.id
CROSS JOIN org_avg oa,
     team_stats ts
WHERE tas.period_end >= NOW() - INTERVAL '30 days'
  AND t.id = :team_id;
```

---

## 7. API Design

### 7.1 Analytics Endpoints

```python
@router.get("/api/v1/teams/{team_id}/analytics")
async def get_team_analytics(
    team_id: UUID,
    period: str = "30d",  # 7d, 30d, 90d, 1y
    metrics: List[str] = Query(default=["performance", "engagement", "wellness"]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get comprehensive team analytics

    Returns:
    - Performance trends
    - Engagement metrics
    - Wellness indicators
    - Benchmark comparisons
    """
```

### 7.2 Real-Time Dashboard Endpoint

```python
@router.get("/api/v1/teams/{team_id}/health/realtime")
async def get_team_realtime_health(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    cache: Redis = Depends(get_redis)
):
    """
    Real-time team health dashboard (cached for 60 seconds)

    Returns live data from:
    - Team activity stream
    - Health indicators
    - Active alerts
    """
    cache_key = f"team:{team_id}:health:realtime"
    cached = await cache.get(cache_key)
    if cached:
        return JSONResponse(content=cached)

    # Fetch real-time data
    health = await compute_team_health(team_id)
    await cache.set(cache_key, health.json(), ex=60)
    return health
```

---

## 8. Performance Optimization

### 8.1 Materialized Views

```sql
CREATE MATERIALIZED VIEW mv_team_monthly_stats AS
SELECT
    team_id,
    DATE_TRUNC('month', period_end) as month,
    AVG(avg_team_score) as avg_score,
    AVG(assessment_completion_rate) as completion_rate,
    AVG(wellness_score) as wellness_score,
    SUM(assessments_completed) as total_assessments,
    COUNT(DISTINCT active_members) as unique_members
FROM team_analytics_snapshots
GROUP BY team_id, DATE_TRUNC('month', period_end);

CREATE INDEX ON mv_team_monthly_stats(team_id, month);

-- Refresh strategy
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_team_monthly_stats;
```

### 8.2 Partitioning Strategy

```sql
-- Partition activity stream by month
CREATE TABLE team_activity_stream_2026_01 PARTITION OF team_activity_stream
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE team_activity_stream_2026_02 PARTITION OF team_activity_stream
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Automated partition creation
CREATE INDEX ON team_activity_stream_2026_01 (team_id, timestamp);
CREATE INDEX ON team_activity_stream_2026_02 (team_id, timestamp);
```

---

## 9. Privacy & Security

### 9.1 Data Access Control

```python
def can_view_team_analytics(user: User, team_id: UUID) -> bool:
    """
    Check if user can view team analytics
    - Team members: yes (own team)
    - Team leads: yes (their teams)
    - Org admins: yes (all teams in org)
    - Regular users: no (other teams)
    """
    if user.is_superuser:
        return True

    # Check team membership
    if is_team_member(user.id, team_id):
        return True

    # Check org admin
    team = await get_team(team_id)
    if is_org_admin(user, team.organization_id):
        return True

    return False
```

### 9.2 Anonymous Aggregation

```sql
-- For small teams (<5 members), aggregate at org level to prevent re-identification
CREATE OR REPLACE FUNCTION get_team_analytics_safe(team_id UUID)
RETURNS TABLE (
    metric_name TEXT,
    metric_value FLOAT,
    is_anonymized BOOLEAN
) AS $$
BEGIN
    IF (SELECT COUNT(*) FROM team_members WHERE team_id = team_id) < 5 THEN
        -- Return org-level aggregates
        RETURN QUERY
        SELECT
            am.metric_name,
            AVG(am.metric_value),
            true as is_anonymized
        FROM team_analytics_snapshots tas
        JOIN analytics_metrics am ON am.snapshot_id = tas.id
        WHERE tas.organization_id = (SELECT organization_id FROM teams WHERE id = team_id)
        GROUP BY am.metric_name;
    ELSE
        -- Return team-level aggregates
        RETURN QUERY
        SELECT
            am.metric_name,
            AVG(am.metric_value),
            false as is_anonymized
        FROM team_analytics_snapshots tas
        JOIN analytics_metrics am ON am.snapshot_id = tas.id
        WHERE tas.team_id = team_id
        GROUP BY am.metric_name;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

---

## 10. Success Metrics

- ✅ Query performance: <100ms for team analytics dashboards
- ✅ Real-time data: <5 second latency from event to dashboard
- ✅ Data freshness: Snapshots generated within 1 hour of period end
- ✅ Accuracy: >99% data consistency (via automated validation)
- ✅ Scalability: Support 10,000+ concurrent team analytics queries
- ✅ Privacy: Zero data leakage between teams
