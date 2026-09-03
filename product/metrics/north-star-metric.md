# PsychSync North Star Metric

**The primary metric that guides all product decisions**

---

## 📋 Executive Summary

PsychSync's North Star Metric (NSM) is **Weekly Active Teams Receiving Insights**. This metric captures our core value delivery: teams getting actionable psychological insights that improve their performance.

**Definition**: A team is "active" if at least one team member views an insight, dashboard, or report in a 7-day period.
**Current**: [TO BE TRACKED]
**Target**: 10,000 weekly active teams by December 2025
**Why This Metric**: Alights all teams on value delivery, not vanity metrics

---

## 🌟 Why This North Star Metric?

### Criteria for a Great NSM
1. **Customer Value**: Does it measure value delivered to customers?
2. **Alignment**: Does it align all teams (product, engineering, sales, CS)?
3. **Actionability**: Can we break it down into actionable input metrics?
4. **Leading Indicator**: Does it predict long-term business success?
5. **Simplicity**: Is it easy to understand and communicate?

### Why "Weekly Active Teams Receiving Insights"?

✅ **Customer Value**: Teams receive insights, not just log in or click buttons
✅ **Product Alignment**: Every feature should increase insights delivered
✅ **Team Cohesion**: Focuses on teams (our core unit of value), not individual users
✅ **Leading Indicator**: Teams receiving insights correlates with retention and revenue
✅ **Actionable**: Can be broken down into: team acquisition → team activation → team engagement → team retention

### Alternatives Considered (and Rejected)

| Metric | Why Rejected |
|--------|--------------|
| **Weekly Active Users (WAU)** | Too individual-focused, doesn't capture team value |
| **Revenue** | Lagging indicator, too focused on extraction vs. value |
| **Assessments Completed** | Vanity metric - completing ≠ receiving value |
| **NPS Score** | Too infrequent, not actionable week-to-week |
| **Customer Count** | Doesn't measure engagement or value delivery |

---

## 📊 Metric Definition

### Primary Formula

```
Weekly Active Teams Receiving Insights =
Number of unique teams with ≥1 member viewing insights/dashboard/reports in past 7 days
```

### What Counts as "Receiving Insights"?

| Action | Counts? | Why |
|--------|---------|-----|
| View team dashboard | ✅ Yes | Core value moment |
View personal insights | ✅ Yes | Individual value |
Generate team report | ✅ Yes | High-value engagement |
Receive AI insights | ✅ Yes | Advanced value moment |
View assessment results | ✅ Yes | Initial value delivery |
Share insights with team | ✅ Yes | Multiplier effect |
Log in without viewing | ❌ No | No value received |
Admin configuration | ❌ No | Setup, not value |
View billing page | ❌ No | Transactional, not value |

### Technical Implementation

**SQL Definition**:
```sql
SELECT COUNT(DISTINCT team_id)
FROM user_activity
WHERE action IN ('view_dashboard', 'view_insights', 'generate_report', 'view_assessment_results')
AND created_at >= NOW() - INTERVAL '7 days'
AND team_id IS NOT NULL;
```

**Dashboard Display**: Real-time counter on company dashboard, updated hourly

---

## 🎯 Target Trajectory

### 2025 Growth Targets

| Quarter | Target Weekly Active Teams | Growth Rate | Key Initiatives |
|---------|---------------------------|-------------|-----------------|
| **Q1 2025** | 500 | Baseline | Onboarding optimization, quick wins |
| **Q2 2025** | 2,000 | 4x | Team analytics, integrations |
| **Q3 2025** | 5,000 | 2.5x | AI features, enterprise acquisition |
| **Q4 2025** | 10,000 | 2x | Viral growth, retention improvements |

### 2026 Vision
- **Target**: 50,000 weekly active teams
- **Growth Rate**: 5x year-over-year
- **International**: 30% of teams outside North America

---

## 🔄 Input Metrics (Leading Indicators)

The NSM is a lagging metric. These input metrics drive it:

### Acquisition (Teams Created)
- **Weekly New Teams**: Number of teams created
- **Team Viral Coefficient**: Each team creates how many new teams?
- **Conversion Rate**: Free teams → Paid teams

### Activation (Teams Receiving First Insights)
- **7-Day Team Activation**: % of new teams viewing insights within 7 days
- **Time to First Insight**: Average days from team creation to first insight viewed
- **Assessment Completion Rate**: % of team members completing assessments

### Engagement (Insights Depth)
- **Insights per Active Team**: Average insights viewed per team per week
- **Team Member Coverage**: % of team members active in a given week
- **Feature Adoption**: % of teams using advanced features (AI, reports)

### Retention (Teams Returning)
- **Week 4 Team Retention**: % of teams still active after 4 weeks
- **Week 12 Team Retention**: % of teams still active after 12 weeks
- **Resurrection Rate**: % of churned teams who reactivate

### Input Metric Targets

| Metric | Current | Target | Impact on NSM |
|--------|---------|--------|---------------|
| Weekly New Teams | [TBD] | 200 | Directly increases NSM |
| 7-Day Team Activation | [TBD] | 60% | More teams become active |
| Insights per Team | [TBD] | 3 | Deepens engagement (retention) |
| Week 4 Retention | [TBD] | 70% | Reduces churn, compounds NSM |
| Team Viral Coefficient | [TBD] | 0.3 | Exponential growth over time |

---

## 🎯 Team Alignment

### How Each Team Impacts the NSM

#### **Product Team**
- **Focus**: Build features that increase insights delivered
- **Key Projects**: Team analytics, AI insights, onboarding optimization
- **NSM Impact**: +0.8 correlation with feature releases

#### **Engineering Team**
- **Focus**: Improve performance, reliability, and user experience
- **Key Projects**: Reduce page load time, improve assessment UX
- **NSM Impact**: +10% engagement from performance improvements

#### **Growth / Marketing**
- **Focus**: Drive team creation and activation
- **Key Projects**: Content marketing, referral programs, paid acquisition
- **NSM Impact**: Directly increases weekly new teams

#### **Sales Team**
- **Focus**: Close enterprise deals with many teams
- **Key Projects**: Enterprise outreach, consultant partnerships
- **NSM Impact**: High-value teams (multiple teams per organization)

#### **Customer Success**
- **Focus**: Ensure teams activate and retain
- **Key Projects**: Onboarding calls, health monitoring, churn prevention
- **NSM Impact**: +15% retention from proactive outreach

#### **Design Team**
- **Focus**: Make insights delightful and easy to access
- **Key Projects**: Dashboard UX, mobile experience, onboarding flow
- **NSM Impact**: +20% engagement from UX improvements

---

## 📈 Dashboard & Reporting

### Weekly NSM Report Template

```markdown
# Weekly North Star Metric Report
Week of [Date]

## Headline Numbers
- **Weekly Active Teams**: [Current] ([change] vs. last week)
- **Growth Rate**: [X]% week-over-week
- **YTD Growth**: [X]% since Jan 1

## Input Metrics
- **Weekly New Teams**: [X] (Target: [Y])
- **7-Day Activation**: [X]% (Target: 60%)
- **Week 4 Retention**: [X]% (Target: 70%)
- **Insights per Team**: [X] (Target: 3)

## Key Drivers (What moved the metric this week?)
- [Positive driver: e.g., Team Analytics feature launch]
- [Negative driver: e.g., Performance degradation on Tuesday]

## Forecast
- **Next Week Prediction**: [X] teams
- **Quarter Predictions**: On track / At risk / Behind

## Action Items
- [ ] [Owner] - [Action to improve NSM]
- [ ] [Owner] - [Action to improve NSM]
```

### Company Dashboard Display

**Real-time NSM Counter**:
```
🌟 WEEKLY ACTIVE TEAMS

[ 7,842 ]

↑ 12% from last week
Goal: 10,000 by Dec 2025
```

**Trend Chart**: 12-week rolling NSM graph
**Input Metrics**: Small sparklines for new teams, activation, retention

---

## 🎯 Decision Framework

### NSM-Based Product Decisions

**Question**: Should we build [Feature X]?

**Decision Tree**:
1. **Will Feature X increase NSM?**
   - Yes → Prioritize based on impact magnitude
   - No → Why build it?

2. **How will Feature X increase NSM?**
   - Acquisition? (More teams created)
   - Activation? (More teams viewing insights)
   - Engagement? (More insights per team)
   - Retention? (Teams staying active longer)

3. **What's the expected NSM impact?**
   - High impact (>10% lift) → Strategic bet, prioritize
   - Medium impact (3-10% lift) → Quick win, ship soon
   - Low impact (<3% lift) → Backlog, deprioritize

### Example Decisions

| Feature | NSM Impact | Decision |
|---------|------------|----------|
| **Team Analytics** | High (engagement + retention) | ✅ P0 - Q2 Priority |
| **Dark Mode** | Low (nice-to-have, minimal NSM impact) | ⏸️ Backlog |
| **Assessment Reminders** | Medium (activation) | ✅ P0 - Q1 Priority |
| **Mobile App** | High (engagement + accessibility) | ✅ P1 - Q3 Priority |
| **Custom Fonts** | Very low (no NSM impact) | ❌ Reject |

---

## 🔄 NSM Health & Diagnostics

### When NSM is Growing (Green Light 🟢)

**Do More Of**:
- Double down on features/programs driving growth
- Share learnings across teams
- Expand successful experiments
- Reinvest in growth channels

**Monitor**:
- Input metric balance (don't over-optimize one at expense of others)
- Quality vs. quantity (are teams actually getting value?)
- Retention health (growth + churn = sustainability)

### When NSM is Flat (Yellow Light 🟡)

**Investigate**:
- Which input metric is lagging? (Acquisition, activation, engagement, retention)
- Any recent changes that impacted NSM? (Product launches, bugs, seasonality)
- Competitive landscape (did competitor launch something?)

**Actions**:
- A/B test interventions
- Focus on worst-performing input metric
- Talk to customers (qualitative feedback)
- Review feature usage (what's driving value?)

### When NSM is Declining (Red Light 🔴)

**Immediate Actions**:
- Root cause analysis (product, marketing, or market issue?)
- Customer outreach (talk to 10 churned teams)
- Fix critical bugs or UX issues
- Pause initiatives that might be harming NSM

**Recovery Plan**:
1. Stabilize NSM (stop the decline)
2. Return to previous level (recovery)
3. Resume growth (exceed previous peak)

---

## 📚 Supporting Documentation

- [Product KPI Dashboard](./product-kpis.md) - Full metrics suite
- [Activation Milestones](./activation-milestones.md) - Activation metrics
- [Churn Prediction](./churn-prediction.md) - Retention metrics
- [Executive Product Reports](./executive-reports.md) - Reporting templates

---

**🧠 PsychSync AI - North Star Metric**

*Version: 1.0*
*Last Updated: January 2025*
*Owner: Product Team*
*Reviewed by: CEO, Leadership Team*
*Next Review: Monthly (in company all-hands)*
