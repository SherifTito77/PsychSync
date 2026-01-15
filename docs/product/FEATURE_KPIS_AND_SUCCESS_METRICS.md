# Feature KPIs and Success Metrics

**Document Version:** 1.0
**Last Updated:** January 12, 2026
**Owner:** Product Team
**Audience:** Product Managers, Engineering Managers, Data Analysts, Stakeholders

---

## Overview

This document defines **Key Performance Indicators (KPIs)** and **success metrics** for new features in PsychSync. These metrics enable data-driven decision-making about feature performance, resource allocation, and product strategy.

**Purpose:**
- Standardize how feature success is measured across PsychSync
- Provide clarity on what "success" means before building features
- Enable objective Go/No-Go decisions for feature launches
- Facilitate post-launch analysis and iteration

**Process:**
```
Feature Conceived → Define Success Metrics → Set Targets →
Launch Feature → Measure Performance → Analyze → Iterate or Sunset
```

---

## Part 1: Core Metric Categories

Every feature should be measured across **4 metric categories**:

### 1. Activation Metrics
**Definition:** Did users try the feature?

**Questions to Answer:**
- How many users were exposed to the feature?
- How many users engaged with the feature?
- What percentage of exposed users activated?

**Examples:**
- Feature discovery rate (% of users who saw the feature)
- Feature activation rate (% of users who used the feature at least once)
- Time to first use (days from exposure to activation)

### 2. Engagement Metrics
**Definition:** Are users continuing to use the feature?

**Questions to Answer:**
- How often do users use the feature?
- How deeply do users engage with the feature?
- Do users form habits around the feature?

**Examples:**
- Daily/Weekly/Monthly Active Users (DAU/WAU/MAU)
- Session frequency (avg. sessions per user per week)
- Feature stickiness (MAU who used feature 3+ times)
- Time spent in feature (avg. minutes per session)
- Feature depth (% of users who use advanced features)

### 3. Outcome Metrics
**Definition:** Is the feature delivering value?

**Questions to Answer:**
- Did the feature solve the problem it was meant to solve?
- Did the feature impact business goals (revenue, retention, efficiency)?
- Did user satisfaction improve?

**Examples:**
- Task completion rate (% of users who complete the intended workflow)
- Time savings (reduction in time to complete a task)
- Error reduction (decrease in user mistakes)
- Satisfaction score (CSAT, NPS for the feature)
- Revenue impact (MRR contributed by feature)
- Retention impact (churn reduction attributed to feature)

### 4. Quality Metrics
**Definition:** Is the feature working well?

**Questions to Answer:**
- Is the feature reliable?
- Is the feature fast?
- Is the feature bug-free?

**Examples:**
- Uptime (% of time feature is available)
- Load time (p95 response time)
- Error rate (% of actions that fail)
- Bug reports (number of bugs reported per 1,000 uses)
- Support tickets (number of support requests per 1,000 uses)

---

## Part 2: Feature-Specific KPIs

### Category: Assessment Features

#### Feature 1: Custom Assessment Builder

**Business Objective:** Allow team leads to create customized assessments for their specific needs.

**Metric Framework:**

| Metric Category | Metric | Definition | Target (90 days) | Target (180 days) |
|-----------------|--------|------------|------------------|-------------------|
| **Activation** | Builder Discovery Rate | % of team leads who see the builder | 80% | 90% |
| | Builder Activation Rate | % of team leads who create at least 1 custom assessment | 25% | 40% |
| **Engagement** | Weekly Builder Users | % of team leads who use builder weekly | 15% | 25% |
| | Avg. Questions per Assessment | Avg. number of questions in custom assessments | 15 | 20 |
| | Builder Completion Rate | % of builder sessions that result in published assessment | 60% | 75% |
| **Outcome** | Custom Assessment Adoption Rate | % of team assessments that are custom (not templates) | 20% | 35% |
| | Custom Assessment Completion Rate | % of custom assessments completed by team members | 65% | 75% |
| | Builder Satisfaction | CSAT for builder experience | 4.2/5.0 | 4.5/5.0 |
| **Quality** | Builder Error Rate | % of builder actions that fail | <2% | <1% |
| | Builder Load Time | p95 load time for builder page | <2s | <1s |
| | Bug Reports per 1K Builds | Number of bugs reported per 1,000 assessment builds | <5 | <2 |

**Success Criteria (Must Meet 3+):**
- ✅ 25%+ activation rate (team leads creating custom assessments)
- ✅ 20%+ of assessments are custom (not templates)
- ✅ 4.0+ CSAT score for builder
- ✅ 75%+ builder completion rate

**Failure Criteria (Meet Any = Sunset Feature):**
- ❌ <10% activation rate after 180 days
- ❌ <10% of assessments are custom after 180 days
- ❌ CSAT <3.5 after 90 days
- ❌ 5%+ error rate after 60 days

---

#### Feature 2: Assessment Reminder System

**Business Objective:** Increase assessment completion rates through automated reminders.

**Metric Framework:**

| Metric Category | Metric | Definition | Target (90 days) | Target (180 days) |
|-----------------|--------|------------|------------------|-------------------|
| **Activation** | Reminder Configuration Rate | % of team leads who configure reminders | 40% | 60% |
| | Reminder Delivery Rate | % of scheduled reminders sent successfully | >99% | >99.5% |
| **Engagement** | Reminder Engagement Rate | % of sent reminders that are opened/clicked | 45% | 55% |
| | Weekly Active Reminders | # of unique users receiving reminders weekly | 500 | 1,000 |
| **Outcome** | Assessment Completion Rate | % of assigned assessments that are completed | 80% | 85% |
| | Time to Completion | Avg. days from assignment to completion | 5 days | 3 days |
| | Reminder Attribution | % of completions that occurred after reminder | 40% | 50% |
| | Team Lead Satisfaction | CSAT for reminder system | 4.0/5.0 | 4.3/5.0 |
| **Quality** | Reminder Opt-Out Rate | % of users who opt out of reminders | <5% | <3% |
| | Reminder Latency | % of reminders sent within 15 min of scheduled time | >95% | >98% |
| | Support Tickets per 1K Reminders | # of support tickets per 1,000 reminders sent | <1 | <0.5 |

**Success Criteria (Must Meet 3+):**
- ✅ Assessment completion rate increases to 80%+ (from 60% baseline)
- ✅ 40%+ of team leads configure reminders
- ✅ 4.0+ CSAT for reminder system
- ✅ 50%+ of completions attributed to reminders

**Failure Criteria (Meet Any = Re-evaluate):**
- ❌ Completion rate doesn't increase to 70%+ after 90 days
- ❌ >10% opt-out rate after 60 days
- ❌ CSAT <3.5 after 60 days
- ❌ <95% reminder delivery rate

---

#### Feature 3: Assessment Results PDF Export

**Business Objective:** Allow team leads to download professional PDF reports of assessment results.

**Metric Framework:**

| Metric Category | Metric | Definition | Target (90 days) | Target (180 days) |
|-----------------|--------|------------|------------------|-------------------|
| **Activation** | Export Discovery Rate | % of users who see export option | 70% | 85% |
| | Export Activation Rate | % of users who export at least 1 PDF | 30% | 50% |
| **Engagement** | Exports per Active User | Avg. # of PDFs exported per active user/month | 2 | 3 |
| | Re-Export Rate | % of users who export the same assessment multiple times | 15% | 25% |
| **Outcome** | Export Success Rate | % of export attempts that succeed | >98% | >99% |
| | Export Satisfaction | CSAT for PDF quality/format | 4.3/5.0 | 4.5/5.0 |
| | Sharing Rate | % of exported PDFs that are shared externally | 20% | 30% |
| **Quality** | Export Generation Time | p95 time to generate PDF | <10s | <5s |
| | PDF Error Rate | % of PDFs with formatting/rendering errors | <1% | <0.5% |
| | File Size | Avg. PDF file size | <500KB | <300KB |

**Success Criteria (Must Meet 2+):**
- ✅ 30%+ of users export at least 1 PDF
- ✅ 4.3+ CSAT for PDF quality
- ✅ >98% export success rate

**Failure Criteria (Meet Any = Sunset Feature):**
- ❌ <15% activation rate after 90 days
- ❌ CSAT <3.5 after 60 days
- ❌ <95% export success rate

---

### Category: Team Management Features

#### Feature 4: Team Comparison Dashboard

**Business Objective:** Enable team leads to compare team members' assessment results side-by-side.

**Metric Framework:**

| Metric Category | Metric | Definition | Target (90 days) | Target (180 days) |
|-----------------|--------|------------|------------------|-------------------|
| **Activation** | Dashboard Discovery Rate | % of team leads who see comparison option | 60% | 75% |
| | Dashboard Activation Rate | % of team leads who use comparison at least once | 35% | 50% |
| **Engagement** | Weekly Comparison Users | % of team leads who use dashboard weekly | 20% | 30% |
| | Avg. Comparisons per Session | Avg. # of team members compared per session | 3 | 4 |
| **Outcome** | Time Savings | Self-reported time savings vs. manual comparison | 60% | 75% |
| | Comparison Satisfaction | CSAT for comparison dashboard | 4.0/5.0 | 4.3/5.0 |
| | Insight Generation Rate | % of comparisons that lead to actionable insights | 40% | 55% |
| **Quality** | Dashboard Load Time | p95 load time for comparison view | <3s | <2s |
| | Data Accuracy Rate | % of comparisons with accurate data | >99% | >99.5% |

**Success Criteria (Must Meet 2+):**
- ✅ 35%+ of team leads use comparison dashboard
- ✅ 60%+ of users report time savings
- ✅ 4.0+ CSAT for dashboard

**Failure Criteria:**
- ❌ <20% activation rate after 90 days
- ❌ CSAT <3.5 after 60 days

---

#### Feature 5: Team Activity Feed

**Business Objective:** Provide team leads with a real-time feed of team assessment activity.

**Metric Framework:**

| Metric Category | Metric | Definition | Target (90 days) | Target (180 days) |
|-----------------|--------|------------|------------------|-------------------|
| **Activation** | Feed Discovery Rate | % of team leads who see activity feed | 80% | 90% |
| | Feed Activation Rate | % of team leads who view feed at least once | 50% | 65% |
| **Engagement** | Daily Feed Viewers | % of team leads who view feed daily | 25% | 40% |
| | Feed Scroll Depth | Avg. % of feed scrolled per session | 40% | 60% |
| | Feed Click-Through Rate | % of feed items clicked | 10% | 15% |
| **Outcome** | Time to Awareness | Reduction in time for team leads to notice completions | 50% | 70% |
| | Feed Satisfaction | CSAT for activity feed | 3.8/5.0 | 4.1/5.0 |
| **Quality** | Feed Freshness | % of feed items <1 hour old | 80% | 90% |
| | Feed Load Time | p95 load time for feed | <2s | <1s |

**Success Criteria (Must Meet 2+):**
- ✅ 50%+ of team leads view feed at least once
- ✅ 50%+ reduction in time to awareness
- ✅ 3.8+ CSAT for feed

**Failure Criteria:**
- ❌ <30% activation rate after 90 days
- ❌ CSAT <3.5 after 60 days

---

### Category: Analytics & Reporting Features

#### Feature 6: Organizational Analytics Dashboard

**Business Objective:** Provide organization admins with high-level analytics across all teams.

**Metric Framework:**

| Metric Category | Metric | Definition | Target (90 days) | Target (180 days) |
|-----------------|--------|------------|------------------|-------------------|
| **Activation** | Dashboard Discovery Rate | % of org admins who see analytics option | 90% | 100% |
| | Dashboard Activation Rate | % of org admins who view dashboard at least once | 70% | 85% |
| **Engagement** | Weekly Dashboard Users | % of org admins who view dashboard weekly | 50% | 65% |
| | Dashboard Session Duration | Avg. time spent per dashboard session | 5 min | 7 min |
| | Filter Usage Rate | % of sessions where filters are applied | 60% | 75% |
| **Outcome** | Decision Impact Rate | % of admins who report dashboard influences decisions | 60% | 75% |
| | Analytics Satisfaction | CSAT for analytics dashboard | 4.2/5.0 | 4.5/5.0 |
| **Quality** | Query Response Time | p95 time for data queries | <3s | <2s |
| | Data Accuracy Rate | % of queries with accurate data | >99% | >99.5% |

**Success Criteria (Must Meet 2+):**
- ✅ 70%+ of org admins view dashboard
- ✅ 60%+ report dashboard influences decisions
- ✅ 4.2+ CSAT for analytics

**Failure Criteria:**
- ❌ <50% activation rate after 90 days
- ❌ CSAT <3.8 after 60 days

---

#### Feature 7: Trend Analysis Tool

**Business Objective:** Enable team leads to see assessment score trends over time.

**Metric Framework:**

| Metric Category | Metric | Definition | Target (90 days) | Target (180 days) |
|-----------------|--------|------------|------------------|-------------------|
| **Activation** | Tool Discovery Rate | % of team leads with sufficient data who see trend option | 70% | 85% |
| | Tool Activation Rate | % of team leads who use trend analysis at least once | 40% | 55% |
| **Engagement** | Weekly Trend Users | % of team leads who view trends weekly | 25% | 40% |
| | Avg. Time Range Analyzed | Avg. months of data analyzed per session | 3 | 6 |
| **Outcome** | Insight Value | % of users who report trends provide actionable insights | 50% | 65% |
| | Trend Satisfaction | CSAT for trend analysis | 4.0/5.0 | 4.3/5.0 |
| **Quality** | Chart Load Time | p95 time for trend charts to render | <2s | <1s |
| | Data Accuracy Rate | % of trend calculations that are accurate | >99% | >99.5% |

**Success Criteria (Must Meet 2+):**
- ✅ 40%+ of eligible team leads use trend analysis
- ✅ 50%+ report trends provide actionable insights
- ✅ 4.0+ CSAT for trends

**Failure Criteria:**
- ❌ <25% activation rate after 90 days
- ❌ CSAT <3.5 after 60 days

---

### Category: Collaboration Features

#### Feature 8: Team Member Notes

**Business Objective:** Allow team leads to add private notes about team members.

**Metric Framework:**

| Metric Category | Metric | Definition | Target (90 days) | Target (180 days) |
|-----------------|--------|------------|------------------|-------------------|
| **Activation** | Notes Discovery Rate | % of team leads who see notes option | 60% | 75% |
| | Notes Activation Rate | % of team leads who add at least 1 note | 30% | 45% |
| **Engagement** | Weekly Note Writers | % of team leads who write notes weekly | 15% | 25% |
| | Avg. Notes per Member | Avg. # of notes per team member | 2 | 4 |
| | Note Re-View Rate | % of notes that are viewed after creation | 40% | 55% |
| **Outcome** | Note Value | % of team leads who report notes improve management | 55% | 70% |
| | Notes Satisfaction | CSAT for notes feature | 3.9/5.0 | 4.2/5.0 |
| **Quality** | Note Save Success Rate | % of notes saved successfully | >99% | >99.5% |
| | Note Load Time | p95 time to load notes view | <1s | <500ms |

**Success Criteria (Must Meet 2+):**
- ✅ 30%+ of team leads add notes
- ✅ 55%+ report notes improve management
- ✅ 3.9+ CSAT for notes

**Failure Criteria:**
- ❌ <20% activation rate after 90 days
- ❌ CSAT <3.5 after 60 days

---

#### Feature 9: Shared Assessment Annotations

**Business Objective:** Allow team leads to add comments/annotations to assessment results for discussion.

**Metric Framework:**

| Metric Category | Metric | Definition | Target (90 days) | Target (180 days) |
|-----------------|--------|------------|------------------|-------------------|
| **Activation** | Annotation Discovery Rate | % of team leads who see annotation option | 50% | 65% |
| | Annotation Activation Rate | % of team leads who add at least 1 annotation | 20% | 35% |
| **Engagement** | Weekly Annotators | % of team leads who add annotations weekly | 10% | 20% |
| | Avg. Annotations per Result | Avg. # of annotations per assessment result | 1.5 | 2.5 |
| | Annotation Reply Rate | % of annotations that receive replies | 30% | 45% |
| **Outcome** | Discussion Quality | % of users who report annotations improve understanding | 45% | 60% |
| | Annotation Satisfaction | CSAT for annotation feature | 3.8/5.0 | 4.1/5.0 |
| **Quality** | Annotation Save Success Rate | % of annotations saved successfully | >99% | >99.5% |
| | Real-Time Sync Accuracy | % of time annotations sync in <2s | >95% | >98% |

**Success Criteria (Must Meet 2+):**
- ✅ 20%+ of team leads add annotations
- ✅ 45%+ report annotations improve understanding
- ✅ 3.8+ CSAT for annotations

**Failure Criteria:**
- ❌ <15% activation rate after 90 days
- ❌ CSAT <3.5 after 60 days

---

### Category: Integrations Features

#### Feature 10: Slack Integration

**Business Objective:** Allow teams to receive assessment notifications and reminders via Slack.

**Metric Framework:**

| Metric Category | Metric | Definition | Target (90 days) | Target (180 days) |
|-----------------|--------|------------|------------------|-------------------|
| **Activation** | Integration Discovery Rate | % of team leads who see Slack integration option | 60% | 75% |
| | Integration Activation Rate | % of teams who connect Slack | 25% | 40% |
| **Engagement** | Daily Active Slack Users | % of connected users who interact daily | 30% | 45% |
| | Slack Message CTR | % of Slack messages clicked | 15% | 25% |
| | Weekly Slack Commands | Avg. # of Slack commands used per active team/week | 5 | 8 |
| **Outcome** | Assessment Completion Lift | Increase in completion rate for teams with Slack vs. without | 15% | 25% |
| | Slack Satisfaction | CSAT for Slack integration | 4.1/5.0 | 4.4/5.0 |
| **Quality** | Message Delivery Rate | % of Slack messages delivered successfully | >98% | >99% |
| | Integration Uptime | % of time integration is functional | >99% | >99.5% |

**Success Criteria (Must Meet 2+):**
- ✅ 25%+ of teams connect Slack
- ✅ 15%+ lift in completion rate
- ✅ 4.1+ CSAT for integration

**Failure Criteria:**
- ❌ <15% activation rate after 90 days
- ❌ CSAT <3.8 after 60 days
- ❌ <95% message delivery rate

---

## Part 3: Metric Measurement Playbook

### How to Measure Each Category

#### Activation Metrics

**Data Source:** Application analytics (Mixpanel, Amplitude, or custom)

**SQL Query Example:**
```sql
-- Feature Discovery Rate
SELECT
  COUNT(DISTINCT CASE WHEN saw_feature = true THEN user_id END) * 100.0 /
  COUNT(DISTINCT user_id) AS discovery_rate
FROM user_events
WHERE event_date >= NOW() - INTERVAL '30 days'
  AND user_role = 'team_lead';

-- Feature Activation Rate
SELECT
  COUNT(DISTINCT CASE WHEN used_feature = true THEN user_id END) * 100.0 /
  COUNT(DISTINCT CASE WHEN saw_feature = true THEN user_id END) AS activation_rate
FROM user_events
WHERE event_date >= NOW() - INTERVAL '30 days'
  AND user_role = 'team_lead';
```

**Dashboard Visualization:**
- Funnel chart: Exposed → Viewed → Activated
- Time series: Activation rate over time
- Cohort analysis: Activation by user cohort (sign-up month)

---

#### Engagement Metrics

**Data Source:** Application analytics + database queries

**SQL Query Example:**
```sql
-- Weekly Active Users (WAU) for Feature
SELECT
  date_trunc('week', event_date) AS week,
  COUNT(DISTINCT user_id) AS weekly_active_users
FROM user_events
WHERE event_name = 'custom_assessment_builder_used'
  AND event_date >= NOW() - INTERVAL '12 weeks'
GROUP BY 1
ORDER BY 1;

-- Feature Stickiness (MAU who used feature 3+ times)
SELECT
  COUNT(DISTINCT CASE
    WHEN usage_count >= 3 THEN user_id
  END) * 100.0 /
  COUNT(DISTINCT user_id) AS stickiness_rate
FROM (
  SELECT
    user_id,
    COUNT(DISTINCT event_date) AS usage_count
  FROM user_events
  WHERE event_name = 'custom_assessment_builder_used'
    AND event_date >= NOW() - INTERVAL '30 days'
  GROUP BY 1
) usage_counts;
```

**Dashboard Visualization:**
- Line chart: WAU over time
- Heatmap: Usage by day of week + hour
- Histogram: Distribution of usage frequency (1x, 2x, 3x, 4x+ users)

---

#### Outcome Metrics

**Data Source:** Database queries + surveys + revenue analytics

**SQL Query Example:**
```sql
-- Custom Assessment Adoption Rate
SELECT
  COUNT(DISTINCT CASE
    WHEN is_custom = true THEN assessment_id
  END) * 100.0 /
  COUNT(DISTINCT assessment_id) AS custom_assessment_rate
FROM assessments
WHERE created_at >= NOW() - INTERVAL '90 days';

-- Assessment Completion Rate (Pre/Post Reminder Launch)
SELECT
  CASE
    WHEN created_at >= '2026-04-01' THEN 'Post-Launch'
    ELSE 'Pre-Launch'
  END AS period,
  COUNT(DISTINCT CASE
    WHEN status = 'completed' THEN response_id
  END) * 100.0 /
  COUNT(DISTINCT response_id) AS completion_rate
FROM assessment_responses
WHERE assigned_at >= NOW() - INTERVAL '180 days'
GROUP BY 1;
```

**Survey Approach:**
```typescript
// In-app CSAT survey after feature use
const csatSurvey = {
  trigger: 'after_feature_use',
  feature: 'custom_assessment_builder',
  questions: [
    {
      type: 'rating',
      question: 'How satisfied are you with the Custom Assessment Builder?',
      scale: '1-5',
      labels: ['Very Dissatisfied', 'Dissatisfied', 'Neutral', 'Satisfied', 'Very Satisfied']
    },
    {
      type: 'open_text',
      question: 'What could we improve about the Custom Assessment Builder?',
      optional: true
    }
  ]
};
```

**Dashboard Visualization:**
- Bar chart: Pre/post-launch comparison
- Line chart: Metric trend over time
- Cohort analysis: Metric by user segment (SMB, mid-market, enterprise)

---

#### Quality Metrics

**Data Source:** Application performance monitoring (APM) + error tracking + support ticket system

**SQL Query Example:**
```sql
-- Builder Error Rate
SELECT
  COUNT(DISTINCT CASE
    WHEN event_type = 'error' THEN event_id
  END) * 100.0 /
  COUNT(DISTINCT event_id) AS error_rate
FROM user_events
WHERE feature = 'custom_assessment_builder'
  AND event_date >= NOW() - INTERVAL '7 days';

-- Builder Load Time (p95)
SELECT
  percentile_cont(0.95) WITHIN GROUP (
    ORDER BY load_time_ms
  ) AS p95_load_time_ms
FROM performance_metrics
WHERE feature = 'custom_assessment_builder'
  AND event_date >= NOW() - INTERVAL '7 days';
```

**Monitoring Setup:**
```python
# Example: Datadog monitoring for builder load time
from datadog import statsd

@track_performance(metric_name='custom_assessment_builder.load_time')
def load_builder(user_id):
    """Load custom assessment builder for user"""
    start_time = time.time()

    # ... builder loading logic ...

    load_time_ms = (time.time() - start_time) * 1000
    statsd.histogram('custom_assessment_builder.load_time', load_time_ms)
    statsd.increment('custom_assessment_builder.loaded')

    return builder_state
```

**Dashboard Visualization:**
- Line chart: Error rate over time (with alert threshold)
- Line chart: p95 load time over time
- Heatmap: Error rate by user segment, geography, browser

---

### Setting Targets

**How to Set Realistic Targets:**

**Method 1: Benchmark Against Industry Standards**
```python
# Example: SaaS feature activation rates
INDUSTRY_BENCHMARKS = {
    'feature_activation_rate': {
        'low': 10,      # 10th percentile
        'median': 25,   # 50th percentile
        'high': 40,     # 90th percentile
        'top': 60       # 99th percentile (best-in-class)
    }
}

# Set target based on company ambition
if company_stage == 'early_stage':
    target = INDUSTRY_BENCHMARKS['feature_activation_rate']['median']  # 25%
elif company_stage == 'growth_stage':
    target = INDUSTRY_BENCHMARKS['feature_activation_rate']['high']    # 40%
else:  # mature
    target = INDUSTRY_BENCHMARKS['feature_activation_rate']['top']     # 60%
```

**Method 2: Analyze Historical Performance**
```sql
-- Analyze similar features launched in the past
SELECT
  feature_name,
  activation_rate_30_days,
  engagement_rate_30_days,
  outcome_metric_30_days
FROM feature_launch_history
WHERE launch_date >= NOW() - INTERVAL '2 years'
  AND feature_category = 'assessment_features'
ORDER BY launch_date;

-- Use median as target for new feature
-- Example: If median activation rate for assessment features is 28%,
-- set target for new assessment feature at 30-35% (slightly higher)
```

**Method 3: Run A/B Test Before Full Launch**
```python
# Launch feature to 10% of users (treatment), keep 90% as control
# Measure outcomes after 30 days
# If treatment shows positive lift, roll out to 100%
# Use treatment performance as target for 90-day goal

# Example: Reminder system A/B test
treatment_completion_rate = 82%  # users with reminders
control_completion_rate = 60%    # users without reminders
lift = (82 - 60) / 60 = 36.7%

# Set 90-day target: 80% completion rate (conservative vs. 82% A/B result)
# Set 180-day target: 85% completion rate (optimistic as optimization continues)
```

**Method 4: Reverse-Engineer from Business Goals**
```python
# Example: Business goal is $1M ARR from new feature
# Pricing: $100/month per team
# Teams needed: $1M / ($100 * 12 months) = 833 teams
# Current customer base: 5,000 teams
# Activation rate needed: 833 / 5,000 = 16.7%

# Set targets:
# 90-day target: 15% activation (conservative)
# 180-day target: 20% activation (stretch goal)
```

---

## Part 4: Go/No-Go Decision Framework

### Pre-Launch Decision (Gate Review)

**Question:** Should we launch this feature to all users?

**Criteria:**

| Criterion | Threshold | Decision |
|-----------|-----------|----------|
| **P0 Bugs** | Zero critical bugs blocking launch | ✅ Pass |
| **Performance** | Meets all NFRs (load time, uptime, etc.) | ✅ Pass |
| **Beta Testing** | 20+ beta users, 3.5+ CSAT | ✅ Pass |
| **Documentation** | Help center article, in-app tooltips ready | ✅ Pass |
| **Support Readiness** | Support team trained, escalation process defined | ✅ Pass |
| **Legal/Compliance** | Legal review complete, no blockers | ✅ Pass |
| **Success Metrics Defined** | All success metrics baselined and tracked | ✅ Pass |

**Decision Rules:**
- ✅ **GO:** All criteria pass
- ⚠️ **GO WITH CONDITIONS:** 1-2 criteria fail, but have mitigation plan
- ❌ **NO-GO:** 3+ criteria fail, or any critical criterion fails

---

### Post-Launch Review (30, 60, 90 Days)

**Question:** Is this feature successful? Continue, iterate, or sunset?

**30-Day Review (Early Indicators)**

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Activation Rate | >20% | __% | ⬜ Pass ⬜ Fail |
| Weekly Engagement | >15% | __% | ⬜ Pass ⬜ Fail |
| Error Rate | <5% | __% | ⬜ Pass ⬜ Fail |
| CSAT | >3.8 | __% | ⬜ Pass ⬜ Fail |

**Decision:**
- ✅ **Continue:** 3+ metrics passing
- ⚠️ **Monitor Closely:** 2 metrics passing, 2 metrics close to target
- ❌ **Fix or Sunset:** 2+ metrics failing significantly

---

**60-Day Review (Trending Analysis)**

**Questions to Answer:**
1. Are metrics trending toward 90-day targets?
2. Are users providing positive feedback?
3. Are there unexpected use cases?
4. Are there technical issues?

**Decision:**
- ✅ **Continue:** Metrics trending positive, on track for 90-day targets
- ⚠️ **Pivot:** Metrics flat/declining, but user feedback suggests opportunity (e.g., "love the concept, but workflow is clunky")
- ❌ **Sunset:** Metrics declining, negative feedback, no path to success

---

**90-Day Review (Success/Failure Determination)**

**Success Criteria:** Meet pre-defined success criteria (usually 2-4 metrics)

**If Successful:**
- Celebrate win! Communicate to company/stakeholders
- Scale feature (more marketing, training, optimization)
- Plan Phase 2 features (based on user feedback)
- Document learnings for future features

**If Unsuccessful:**
- Conduct root cause analysis (why did it fail?)
- Decide: Iterate (fixable) or Sunset (fundamentally flawed)
- If Sunset:
  - Communicate to users (give 30-day notice)
  - Migrate data (if applicable)
  - Turn off feature
  - Document learnings (what went wrong?)

---

### Sunset Criteria

**When to Sunset a Feature:**

1. **Low Adoption:** Activation rate <10% after 180 days
2. **Poor Retention:** <20% of activated users still using after 90 days
3. **Negative Feedback:** CSAT <3.5 after 60 days
4. **High Cost:** Feature costs more to maintain than value it provides
5. **Technical Debt:** Feature is too complex to maintain, inhibits other improvements
6. **Strategic Shift:** Company strategy changed, feature no longer aligns

**Sunset Process:**
1. **Decision:** Product Manager proposes sunset, reviews with stakeholders
2. **Communication:** Notify users 30-60 days in advance
3. **Migration:** Help users migrate to alternatives (if applicable)
4. **Decommission:** Turn off feature, remove from UI, delete code
5. **Retrospective:** Document why feature failed, learnings for future

---

## Part 5: Feature KPI Template

**Use this template when defining KPIs for new features:**

```markdown
# [Feature Name] - KPIs and Success Metrics

## Business Objective
[What problem does this feature solve? Why does it matter?]

## Metric Framework

| Category | Metric | Definition | Target (90 days) | Target (180 days) |
|----------|--------|------------|------------------|-------------------|
| **Activation** | [Metric 1] | [Definition] | [Target] | [Target] |
| | [Metric 2] | [Definition] | [Target] | [Target] |
| **Engagement** | [Metric 3] | [Definition] | [Target] | [Target] |
| | [Metric 4] | [Definition] | [Target] | [Target] |
| **Outcome** | [Metric 5] | [Definition] | [Target] | [Target] |
| | [Metric 6] | [Definition] | [Target] | [Target] |
| **Quality** | [Metric 7] | [Definition] | [Target] | [Target] |
| | [Metric 8] | [Definition] | [Target] | [Target] |

## Success Criteria
- ✅ [Success criterion 1]
- ✅ [Success criterion 2]
- ✅ [Success criterion 3]

## Failure Criteria (Meet Any = Sunset)
- ❌ [Failure criterion 1]
- ❌ [Failure criterion 2]
- ❌ [Failure criterion 3]

## Measurement Plan
**Data Sources:** [Where will we get this data?]
**SQL Queries:** [Key queries to measure metrics]
**Dashboards:** [Which dashboards will display these metrics?]
**Alerts:** [What alerts will notify us of issues?]

## Go/No-Go Review
**30-Day Review:**
- Activation: [Target] → Actual: __
- Engagement: [Target] → Actual: __
- Outcome: [Target] → Actual: __
- Quality: [Target] → Actual: __

**Decision:** ⬜ Continue ⬜ Monitor ⬜ Fix/Sunset

**90-Day Review:**
- Success Criteria Met: ⬜ Yes ⬜ No
- User Feedback: [Summary of feedback]
- Iteration Plan: [What's next for this feature?]
```

---

## Conclusion

Feature KPIs and success metrics are the **compass for product development**. They:

1. **Align teams** on what success looks like before building
2. **Enable data-driven decisions** about feature continuation
3. **Prevent feature bloat** by sunset underperforming features
4. **Create accountability** for product and engineering teams

**Remember:** What gets measured gets managed. Define success upfront, measure relentlessly, and act on the data.

---

**Document Owner:** Product Team
**Next Review:** Quarterly (add new feature KPIs as features launch)
**Change Log:**
- v1.0 (January 12, 2026): Initial version with 10 feature KPI frameworks
