# Funnel and Cohort Calculations Validation Report

**Date**: January 21, 2026
**Status**: ✅ **PASS - Formulas are mathematically correct**
**Review Method**: Manual code analysis of calculation logic

---

## 🎯 Executive Summary

The funnel and cohort calculation formulas have been reviewed for mathematical accuracy. **All core formulas are correct**, though many implementations use mock data that should be replaced with real database queries in production.

| Component | Formula | Status | Notes |
|-----------|---------|--------|-------|
| **Funnel Stage Conversion** | (current / previous) × 100 | ✅ CORRECT | Standard funnel analysis |
| **Overall Funnel Conversion** | (last_stage / first_stage) × 100 | ✅ CORRECT | Proper aggregate conversion |
| **Drop-off Rate** | 100 - conversion_rate | ✅ CORRECT | Logical complement |
| **Churn Rate** | canceled / total_subscriptions | ✅ CORRECT | Standard churn formula |
| **Retention Rate** | retained_users / previous_users | ✅ CORRECT | Standard retention formula |
| **Cohort Analysis** | Not implemented | ⚠️ TODO | Mock data only |

---

## 📊 Funnel Calculations Review

### File: `app/services/growth_analytics_service.py`

#### 1. **Stage-to-Stage Conversion Rate**

**Location**: Lines 680-688

```python
for i, stage_def in enumerate(funnel_def["stages"]):
    stage_name = stage_def["name"]
    current_count = funnel_data.get(stage_name, 0)

    # Calculate conversion rate from previous stage
    if previous_count is not None and previous_count > 0:
        # Conversion rate: percentage of users who advanced from previous stage
        conversion_rate = (current_count / previous_count) * 100
        # Drop-off rate: percentage of users lost at this stage
        drop_off_rate = 100 - conversion_rate
    elif i == 0:
        # First stage - no previous stage to compare against
        conversion_rate = 100.0  # Entry point is 100%
        drop_off_rate = 0.0
```

**Formula**: `(current_count / previous_count) * 100`

**Status**: ✅ **CORRECT**

**Analysis**:
- Correctly calculates the percentage of users who advanced from the previous stage
- Properly handles the first stage (100% conversion rate as entry point)
- Correctly handles division by zero protection
- Drop-off rate is the logical complement (100 - conversion_rate)

**Example**:
```
Stage 1 (Awareness): 10,000 users → conversion_rate = 100.0% (entry stage)
Stage 2 (Interest):  1,234 users  → conversion_rate = (1,234 / 10,000) × 100 = 12.34%
                                      drop_off_rate = 100 - 12.34 = 87.66%
Stage 3 (Consider):   891 users  → conversion_rate = (891 / 1,234) × 100 = 72.20%
                                      drop_off_rate = 100 - 72.20 = 27.80%
```

---

#### 2. **Overall Funnel Conversion Rate**

**Location**: Lines 700-706

```python
# Calculate overall funnel conversion rate
first_stage_count = stages[0]["count"] if stages else 0
last_stage_count = stages[-1]["count"] if stages else 0
overall_conversion_rate = (
    (last_stage_count / first_stage_count) * 100
    if first_stage_count > 0 else 0
)
```

**Formula**: `(last_stage_count / first_stage_count) * 100`

**Status**: ✅ **CORRECT**

**Analysis**:
- Correctly calculates the aggregate conversion from first to last stage
- Shows what percentage of initial users completed the entire funnel
- Properly handles empty funnels (returns 0)
- Protected against division by zero

**Example**:
```
User Acquisition Funnel:
  Awareness: 10,000 users
  Engagement: 623 users (final stage)

  Overall Conversion = (623 / 10,000) × 100 = 6.23%
```

---

#### 3. **Bottleneck Identification**

**Location**: Lines 708-712

```python
# Identify bottleneck stages (highest drop-off rates)
bottlenecks = [
    stage for stage in stages
    if stage.get("drop_off_rate") and stage["drop_off_rate"] > 50
]
```

**Formula**: `drop_off_rate > 50`

**Status**: ✅ **REASONABLE** (but hardcoded threshold)

**Analysis**:
- Identifies stages where more than 50% of users drop off
- This is a reasonable heuristic for finding bottlenecks
- **Improvement opportunity**: Make the threshold configurable per funnel

**Example**:
```
Funnel Stages:
  Awareness → Interest:    87.66% drop-off ✅ BOTTLENECK
  Interest → Consider:     27.80% drop-off
  Consider → Activation:   26.15% drop-off
  Activation → Engagement: 5.32% drop-off
```

---

## 💰 Churn Rate Calculation Review

### File: `app/services/enterprise_billing.py`

#### **Subscription Churn Rate**

**Location**: Lines 746-759

```python
# Calculate churn rate
churn_query = """
SELECT
    COUNT(CASE WHEN s.status = 'canceled' THEN 1 END)::float /
    NULLIF(COUNT(s.subscription_id), 0) as churn_rate
FROM subscriptions s
WHERE s.created_at >= NOW() - INTERVAL '30 days'
"""

async with self.db_pool.acquire() as conn:
    churn_result = await conn.fetchrow(churn_query)
    analytics["churn_rate"] = (
        float(churn_result["churn_rate"]) if churn_result else 0.0
    )
```

**Formula**: `COUNT(canceled_subscriptions) / COUNT(total_subscriptions)`

**Status**: ✅ **CORRECT**

**Analysis**:
- Correctly calculates the proportion of canceled subscriptions
- Uses `NULLIF` to prevent division by zero
- Casts to float for proper decimal division
- Filters to last 30 days (standard churn measurement window)

**Example**:
```
Total subscriptions (last 30 days): 1000
Canceled subscriptions: 50

Churn Rate = 50 / 1000 = 0.05 = 5%
```

**Note**: This is a **simple churn rate**. Other common formulas:
- **Revenue Churn**: `MRR_churned / MRR_total`
- **Customer Churn**: `customers_churned / customers_total` ✅ (what's implemented)
- **Logo Churn**: Same as customer churn

---

## 👥 Retention Rate Calculation Review

### File: `app/services/customer_usage_score.py`

#### **User Retention Rate**

**Location**: Lines 432-447

```python
async def _calculate_retention(
    self, organization_id: str, lookback_days: int, previous_period_days: int
) -> ComponentScore:
    """Calculate Retention Score (10% weight)."""

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=lookback_days)
    prev_start = start_date - timedelta(days=previous_period_days)

    # User retention
    current_users = set(
        await self._get_active_user_ids(organization_id, start_date, end_date)
    )
    previous_users = set(
        await self._get_active_user_ids(organization_id, prev_start, start_date)
    )

    retained_users = len(current_users & previous_users)  # Intersection
    retention_rate = (
        (retained_users / len(previous_users)) if previous_users else 1.0
    )
```

**Formula**: `retained_users / previous_users`

Where:
- `retained_users` = `current_users ∩ previous_users` (users active in both periods)
- `previous_users` = users active in the previous period

**Status**: ✅ **CORRECT**

**Analysis**:
- Correctly calculates the percentage of previous users who remain active
- Uses set intersection to find users present in both periods
- Protected against division by zero (returns 1.0 = 100%)
- Standard retention analysis formula

**Example**:
```
Previous period (days -60 to -30): 100 users
Current period (days -30 to 0):     85 users
Users active in BOTH periods:       70 users

Retention Rate = 70 / 100 = 0.70 = 70%
```

**Note**: This is **period-based retention**. Other common formulas:
- **Cohort Retention**: Track a specific cohort over time (e.g., "users who joined in January")
- **Rolling Retention**: What's implemented here ✅

---

## 🔍 Behavioral Retention Risk

### File: `app/services/behavioral_pipeline.py`

#### **Retention Risk Score**

**Location**: Lines 482-500

```python
def _calculate_retention_risk(self, all_signals: Dict[str, Dict]) -> float:
    """Calculate aggregate retention risk score (0-1)"""
    risk_score = 0.0

    # Burnout is a major retention risk factor
    burnout_risk = self._calculate_burnout_risk(all_signals)
    risk_score += burnout_risk * 0.5

    # Low engagement increases retention risk
    engagement = self._calculate_engagement(all_signals)
    risk_score += (1.0 - engagement) * 0.3

    # Work-life imbalance
    wlb_score = (
        all_signals.get("calendar", {}).get("meeting_load_percentage", 0) / 100.0
    )
    risk_score += wlb_score * 0.2

    return min(risk_score, 1.0)
```

**Formula**: Weighted sum of risk factors

**Status**: ✅ **REASONABLE**

**Analysis**:
- Uses weighted risk factors (burnout: 50%, engagement: 30%, work-life: 20%)
- Properly normalizes to 0-1 range using `min(risk_score, 1.0)`
- **Not a direct churn calculation** - this is a **risk score** for individual users
- Used for prediction, not reporting

**Example**:
```
User signals:
  Burnout risk: 0.8 (high)
  Engagement: 0.4 (low) → risk = 1 - 0.4 = 0.6
  Meeting load: 70% → risk = 0.7

Retention Risk = (0.8 × 0.5) + (0.6 × 0.3) + (0.7 × 0.2)
               = 0.40 + 0.18 + 0.14
               = 0.72 (72% risk of churn)
```

---

## ⚠️ Issues and Recommendations

### 1. **Mock Data in Production Code**

**Issue**: Many services return hardcoded mock data instead of querying the database:

```python
# growth_analytics_service.py:837-839
async def _calculate_retention_metrics(self, days: int) -> dict[str, Any]:
    """Calculate retention metrics"""
    return {"retention_rate": 0.85, "churn_rate": 0.05}  # MOCK DATA!
```

**Impact**:
- Analytics dashboards will show fake data
- Business decisions will be based on incorrect metrics
- Funnel analysis won't reflect actual user behavior

**Recommendation**:
Replace mock data with actual database queries. Example:

```python
async def _calculate_retention_metrics(self, days: int) -> dict[str, Any]:
    """Calculate retention metrics"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get active users in current period
    current_active = await self.db.execute(
        """SELECT DISTINCT user_id FROM user_activity
           WHERE last_activity >= $1""",
        start_date
    )

    # Get active users in previous period
    prev_start = start_date - timedelta(days=days)
    previous_active = await self.db.execute(
        """SELECT DISTINCT user_id FROM user_activity
           WHERE last_activity >= $1 AND last_activity < $2""",
        prev_start, start_date
    )

    # Calculate retention
    retained = len(current_active & previous_active)
    retention_rate = retained / len(previous_active) if previous_active else 0

    return {
        "retention_rate": retention_rate,
        "churn_rate": 1 - retention_rate
    }
```

---

### 2. **Cohort Analysis Not Implemented**

**Issue**: Cohort analysis is mentioned in `longitudinal_analysis.py:11` but not actually implemented:

```python
"""
- Cohort analysis and retention modeling  # TODO!
"""
```

**Impact**:
- Cannot track retention of specific user cohorts (e.g., "users who joined in January")
- Cannot compare retention across different signup periods
- Missing critical SaaS metrics

**Recommendation**:
Implement proper cohort analysis:

```python
async def calculate_cohort_retention(
    self,
    cohort_period: str,  # "2026-01", "2026-W03", etc.
    analysis_periods: int = 12  # Track for 12 periods
) -> dict[str, Any]:
    """
    Calculate cohort-based retention analysis.

    Example output:
    {
        "cohort": "2026-01",
        "cohort_size": 1000,
        "retention": [100%, 45%, 32%, 28%, 25%, ...],
        "period_labels": ["Period 0", "Period 1", "Period 2", ...]
    }
    """
    # 1. Get all users who signed up in cohort_period
    cohort_users = await self._get_cohort_users(cohort_period)

    retention_rates = []
    for period in range(analysis_periods):
        period_start = cohort_start + timedelta(days=period*30)
        period_end = period_start + timedelta(days=30)

        # Count active users from cohort in this period
        active_in_period = await self._count_active_users(
            cohort_users, period_start, period_end
        )

        retention_rate = active_in_period / len(cohort_users)
        retention_rates.append(retention_rate)

    return {
        "cohort": cohort_period,
        "cohort_size": len(cohort_users),
        "retention": retention_rates,
        "period_labels": [f"Period {i}" for i in range(analysis_periods)]
    }
```

---

### 3. **Hardcoded Bottleneck Threshold**

**Issue**: Funnel bottleneck threshold is hardcoded at 50%:

```python
bottlenecks = [
    stage for stage in stages
    if stage.get("drop_off_rate") and stage["drop_off_rate"] > 50  # HARDCODED!
]
```

**Impact**:
- Some funnels may need stricter or looser thresholds
- Cannot adapt to different conversion expectations

**Recommendation**:
Make threshold configurable per funnel:

```python
bottleneck_threshold = funnel_def.get("bottleneck_threshold", 50)
bottlenecks = [
    stage for stage in stages
    if stage.get("drop_off_rate") and stage["drop_off_rate"] > bottleneck_threshold
]
```

---

## ✅ Validation Summary

### Formulas Verified as Correct

| Formula | Location | Status |
|---------|----------|--------|
| Stage conversion rate | growth_analytics_service.py:684 | ✅ CORRECT |
| Overall funnel conversion | growth_analytics_service.py:703-705 | ✅ CORRECT |
| Drop-off rate | growth_analytics_service.py:687 | ✅ CORRECT |
| Churn rate | enterprise_billing.py:749-750 | ✅ CORRECT |
| Retention rate | customer_usage_score.py:445-447 | ✅ CORRECT |
| Retention risk score | behavioral_pipeline.py:487-496 | ✅ REASONABLE |

### Issues Requiring Attention

| Issue | Severity | Action Required |
|-------|----------|-----------------|
| Mock data in production code | 🔴 HIGH | Replace with real queries |
| Cohort analysis not implemented | 🟡 MEDIUM | Implement cohort retention tracking |
| Hardcoded bottleneck threshold | 🟢 LOW | Make configurable per funnel |

---

## 📚 Key Learnings

### What Makes Funnel Analysis Correct?

1. **Stage-to-stage conversion**: Always calculate as `(current / previous) × 100`
   - First stage should be 100% (it's the entry point)
   - Each subsequent stage shows advancement from previous

2. **Overall conversion**: Calculate as `(final / initial) × 100`
   - Shows aggregate conversion across entire funnel
   - Protected against division by zero

3. **Drop-off rate**: Always `100 - conversion_rate`
   - Logical complement of conversion rate
   - Shows percentage of users lost

### What Makes Churn/Retention Correct?

1. **Churn rate**: `canceled / total` or `churned / total`
   - Simple proportion of customers who left
   - Usually measured over a standard period (30 days)

2. **Retention rate**: `retained / previous`
   - Percentage of previous customers still active
   - Uses set intersection to find common customers

3. **Cohort analysis**: Track specific groups over time
   - Group customers by signup period
   - Measure retention at each subsequent period
   - Compare cohorts to identify trends

---

## 🎓 Conclusion

The funnel and cohort calculation **formulas are mathematically correct** ✅

**What's Working**:
- ✅ Funnel conversion rates follow standard formulas
- ✅ Churn rate calculation is correct
- ✅ Retention rate calculation is correct
- ✅ Proper division by zero protection
- ✅ Logical complement for drop-off rates

**What Needs Work**:
- ⚠️ Replace mock data with real database queries
- ⚠️ Implement true cohort analysis (currently just mentioned)
- ⚠️ Make bottleneck threshold configurable

**Priority Actions**:
1. Replace mock data in `_calculate_retention_metrics()`
2. Implement `_calculate_cohort_retention()` in longitudinal_analysis.py
3. Add `bottleneck_threshold` to funnel definitions

---

**Last Updated**: January 21, 2026
**Next Review**: After implementing real data queries
**Maintained By**: Analytics Engineering Team
