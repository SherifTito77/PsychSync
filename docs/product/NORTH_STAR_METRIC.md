# North Star Metric for PsychSync

**Document Version:** 1.0
**Last Updated:** January 12, 2026
**Owner:** Product Team
**Stakeholders:** Entire Company (Product, Engineering, Marketing, Sales, Customer Success, Leadership)

---

## Part 1: What is a North Star Metric?

### Definition

A **North Star Metric (NSM)** is the single metric that best captures the core value your product delivers to customers. It aligns your entire organization around a shared goal, and optimizing it should lead to sustainable business growth.

**Key Characteristics:**
1. **Customer-Centric:** Measures customer value, not business extraction
2. **Leading Indicator:** Predicts long-term success, not just short-term wins
3. **Actionable:** Every team can impact it through their work
4. **Holistic:** Reflects the health of the entire business, not just one function

**What a North Star Metric is NOT:**
- ❌ A vanity metric (e.g., "total registered users" - meaningless if they don't use the product)
- ❌ A revenue metric (e.g., "MRR" - important, but measures extraction, not value)
- ❌ A Silo metric (e.g., "conversion rate" - marketing-only, doesn't reflect product health)

---

## Part 2: PsychSync's North Star Metric

### North Star Metric

**# of Weekly Active Teams with 50%+ Assessment Completion**

**Definition:**
- **Active Team:** A team that has at least 2 members complete an assessment in the past 7 days
- **Assessment Completion:** Percentage of assigned team members who have completed their assessments
- **50%+ Threshold:** At least half of the team has completed assessments

**Why This Metric?**

This metric captures the **core value PsychSync delivers**: helping teams understand themselves through psychological assessments and using those insights to improve team performance.

**Example:**
```
Team A (Marketing Team, 25 members):
- 18 members completed assessments this week
- Completion rate: 18/25 = 72%
- ✅ COUNTS toward NSM (active team with 50%+ completion)

Team B (Sales Team, 10 members):
- 2 members completed assessments this week
- Completion rate: 2/10 = 20%
- ❌ DOES NOT count toward NSM (below 50% threshold)

Team C (Engineering Team, 50 members):
- 28 members completed assessments this week
- Completion rate: 28/50 = 56%
- ✅ COUNTS toward NSM (active team with 50%+ completion)

Weekly Active Teams with 50%+ Completion = 2 (Team A + Team C)
```

---

## Part 3: Why This Metric Matters

### The Logic Chain

```
Weekly Active Teams with 50%+ Completion (NSM)
         ↓
      Teams are actively using PsychSync
         ↓
   Teams are getting value from assessments
         ↓
Teams are deriving insights about their people
         ↓
    Teams are performing better
         ↓
     Teams renew and expand (ARR ↑)
         ↓
         PsychSync grows
```

**This metric represents customer value AND business health:**
- **Customer Value:** Teams are using assessments to understand themselves (product-market fit)
- **Business Health:** Active teams → retention → revenue → growth

---

### Why Not Other Metrics?

| Metric | Why It's NOT the North Star | Why It Still Matters |
|--------|----------------------------|----------------------|
| **Total Registered Users** | Vanity metric. Users can sign up and never use the product. Doesn't reflect value. | Useful for measuring top-of-funnel growth |
| **Monthly Recurring Revenue (MRR)** | Measures extraction, not value. You can increase MRR by raising prices without improving product. | Ultimate business outcome, but lagging indicator |
| **Assessments Completed** | Doesn't capture team usage. One person completing 100 assessments ≠ team value. | Useful for measuring individual engagement |
| **Customer Retention Rate** | Lagging indicator. By the time retention drops, it's too late to fix. | Critical for business health, but reactive |
| **Net Promoter Score (NPS)** | Sentiment metric, not usage metric. Users can love you but not use you. | Useful for measuring customer satisfaction |

---

### The 50% Threshold: Why It Matters

We chose **50%+ completion** as the threshold for a reason:

**Too Low (e.g., 10%+):**
- Easy to game (1 person in a 10-person team completes)
- Doesn't represent team-wide value
- Teams with 10% completion aren't getting value

**Too High (e.g., 90%+):**
- Unrealistic for early-stage teams
- Demotivating for teams with busy schedules
- Excludes teams that are getting value but not fully bought in yet

**Just Right (50%+):**
- Represents meaningful team engagement (half the team)
- Correlates with retention (teams with 50%+ completion have 3x higher retention)
- Achievable but aspirational (requires effort, not automatic)

---

## Part 4: Metric Breakdown and Input Metrics

### North Star Metric Equation

```
Weekly Active Teams with 50%+ Completion =
  COUNT(Teams with ≥2 completions in past 7 days AND ≥50% completion rate)
```

### Input Metrics (What Drives the NSM)

```
                  ┌─────────────────────────────────────┐
                  │   WEEKLY ACTIVE TEAMS (50%+ COMP)   │
                  │            (North Star)             │
                  └─────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│   Team        │       │   Team        │       │   Team        │
│  Acquisition  │       │  Activation   │       │  Engagement   │
└───────────────┘       └───────────────┘       └───────────────┘
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│ # of New      │       │ % of Teams    │       │ Avg.          │
│ Teams Created │       │ That Assign   │       │ Completion    │
│ This Week     │       │ Assessments   │       │ Rate per Team │
└───────────────┘       └───────────────┘       └───────────────┘
```

### Input Metric Definitions

#### 1. Team Acquisition (Top of Funnel)

**Metric:** New Teams Created This Week
**Definition:** Number of new teams that signed up for PsychSync
**Target:** 50 new teams/week
**Owner:** Marketing + Sales

**Sub-Metrics:**
- Trial signups: 100/week
- Trial-to-paid conversion: 50%
- Churned teams: 10/week
- Net new teams: 50/week

**How to Improve:**
- Marketing: Increase trial signups (content marketing, SEO, paid ads)
- Sales: Improve trial-to-paid conversion (demos, POCs, urgency tactics)
- Product: Improve onboarding (reduce time-to-value, increase activation)

---

#### 2. Team Activation (Mid-Funnel)

**Metric:** % of Teams That Assign Assessments
**Definition:** Of teams that signed up, what % assigned at least 1 assessment?
**Target:** 70% of new teams assign assessments within 7 days
**Owner:** Product + Customer Success

**Sub-Metrics:**
- Teams that view assessment library: 90%
- Teams that create an assessment: 80%
- Teams that assign to team: 70%
- Time to first assignment: <3 days

**How to Improve:**
- Product: Improve onboarding flow (make assessment assignment obvious)
- Product: Provide assessment templates (reduce friction)
- CS: Reach out to new teams within 24 hours (help them assign)

---

#### 3. Team Engagement (Bottom of Funnel)

**Metric:** Avg. Completion Rate per Team
**Definition:** Of assigned team members, what % complete assessments?
**Target:** 65% average completion rate
**Owner:** Product + Customer Success

**Sub-Metrics:**
- Teams with 50%+ completion: 60% of teams (this IS our NSM!)
- Teams with 25%+ completion: 80% of teams
- Teams with <25% completion: 20% of teams
- Time to completion: 5 days avg.

**How to Improve:**
- Product: Reminder system (automated nudges)
- Product: Shorter assessments (reduce completion time from 30 min to 15 min)
- Product: Progress tracking (show team members how they compare to teammates)
- CS: Best practices workshops (teach team leads how to drive completion)

---

## Part 5: How Each Team Impacts the NSM

### Product Team

**Focus:** Increase Team Activation and Team Engagement

**Initiatives:**
1. **Onboarding Optimization**
   - Reduce time-to-first-assessment from 7 days to 3 days
   - → More teams activate → Higher NSM

2. **Assessment Templates**
   - Provide 10 pre-built assessments (Big Five, MBTI, Enneagram, etc.)
   - → Easier to assign assessments → Higher activation → Higher NSM

3. **Reminder System**
   - Automated email/in-app reminders for incomplete assessments
   - → Higher completion rates → Higher NSM

4. **Team Dashboard**
   - Visualize team completion rates, nudge team leads
   - → Team leads take action → Higher completion rates → Higher NSM

**Product Team NSM Contribution:** +30% improvement in activation and engagement

---

### Engineering Team

**Focus:** Ensure Reliability and Performance

**Initiatives:**
1. **99.9% Uptime**
   - If system is down, teams can't complete assessments
   - → Higher completion rates → Higher NSM

2. **Fast Load Times**
   - Assessment pages load in <1 second
   - → Better UX → Higher completion rates → Higher NSM

3. **Mobile Optimization**
   - Assessments work on mobile (60% of users are on mobile)
   - → More team members can complete anywhere → Higher NSM

4. **Bug-Free Experience**
   - Zero critical bugs blocking assessment completion
   - → Fewer drop-offs → Higher NSM

**Engineering Team NSM Contribution:** +15% improvement in engagement (through UX)

---

### Marketing Team

**Focus:** Increase Team Acquisition

**Initiatives:**
1. **Content Marketing**
   - Blog posts on "How to Build High-Performing Teams"
   - → 500 trial signups/month → More teams to activate → Higher NSM

2. **SEO Optimization**
   - Rank for "team assessment tool", "personality test for teams"
   - → 1,000 organic trial signups/month → Higher NSM

3. **Paid Ads**
   - Google Ads for "team building assessments"
   - → 200 trial signups/month → Higher NSM

4. **Referral Program**
   - Existing teams refer new teams (10% referral rate)
   - → Higher-quality trial signups → Higher activation → Higher NSM

**Marketing Team NSM Contribution:** +20 new teams/week

---

### Sales Team

**Focus:** Improve Trial-to-Paid Conversion

**Initiatives:**
1. **Fast Follow-Up**
   - Call trial teams within 1 hour of signup
   - → 50% conversion rate → More paid teams → Higher NSM

2. **Demos and POCs**
   - Show teams the value in 30 minutes
   - → Higher conversion → More paid teams → Higher NSM

3. **Enterprise Deals**
   - Close large deals (100+ teams)
   - → Many teams at once → Higher NSM

**Sales Team NSM Contribution:** +15 paid teams/week (from 50 trials)

---

### Customer Success Team

**Focus:** Increase Team Engagement and Retention

**Initiatives:**
1. **New Team Onboarding**
   - Reach out to new teams within 24 hours
   - → Help them assign assessments → Higher activation → Higher NSM

2. **Best Practices Workshops**
   - Monthly webinars on "How to Drive Assessment Completion"
   - → Team leads learn tactics → Higher engagement → Higher NSM

3. **Churn Prevention**
   - Identify teams at risk of canceling (low completion)
   - → Intervene with support/coaching → Save teams → Higher NSM

4. **Success Stories**
   - Showcase teams with high completion and impact
   - → Inspire other teams → Higher engagement → Higher NSM

**CS Team NSM Contribution:** +10% improvement in engagement (through coaching)

---

### Leadership Team

**Focus:** Set Strategy and Remove Blockers

**Initiatives:**
1. **Set NSM as Company Goal**
   - Every all-hands starts with NSM update
   - → Alignment across teams → Everyone focused on NSM

2. **Fund NSM-Impacting Initiatives**
   - Prioritize features that move NSM (e.g., reminder system)
   - → Faster execution → Higher NSM

3. **Remove Cross-Team Blockers**
   - Break down silos (e.g., Marketing + Product on onboarding)
   - → Faster iteration → Higher NSM

**Leadership Team NSM Contribution:** Cultural alignment and resource prioritization

---

## Part 6: Current State and Targets

### Baseline (January 2026)

| Metric | Current Value |
|--------|---------------|
| **North Star Metric** | **120 weekly active teams with 50%+ completion** |
| Total Teams | 500 |
| Active Teams (≥2 completions/week) | 200 |
| Teams with 50%+ Completion | 120 |
| Avg. Completion Rate | 55% |
| New Teams/Week | 15 |
| Team Activation Rate | 60% |
| Team Churn Rate | 5%/month |

### Targets (2026 Roadmap)

| Metric | Q1 2026 | Q2 2026 | Q3 2026 | Q4 2026 |
|--------|---------|---------|---------|---------|
| **North Star Metric** | **150** | **200** | **280** | **400** |
| Total Teams | 600 | 800 | 1,100 | 1,500 |
| Active Teams (≥2 completions/week) | 250 | 340 | 480 | 670 |
| Teams with 50%+ Completion | 150 | 200 | 280 | 400 |
| Avg. Completion Rate | 58% | 61% | 64% | 67% |
| New Teams/Week | 20 | 30 | 40 | 55 |
| Team Activation Rate | 65% | 70% | 75% | 80% |
| Team Churn Rate | 4.5% | 4.0% | 3.5% | 3.0% |

### Growth Strategy

**Q1 2026 (Foundation):**
- Focus: Team Activation (get more teams to assign assessments)
- Launch: Reminder system (automated nudges)
- Launch: Onboarding optimization (reduce time-to-value)
- Target: 150 NSM (up 25%)

**Q2 2026 (Engagement):**
- Focus: Team Engagement (increase completion rates)
- Launch: Team dashboard (visualization, nudge team leads)
- Launch: Assessment templates (easier to assign)
- Target: 200 NSM (up 33%)

**Q3 2026 (Acquisition):**
- Focus: Team Acquisition (more teams signing up)
- Launch: Content marketing + SEO (increase trial signups)
- Launch: Referral program (existing teams refer new teams)
- Target: 280 NSM (up 40%)

**Q4 2026 (Optimization):**
- Focus: All Levers (acquisition, activation, engagement)
- Launch: Advanced analytics (identify at-risk teams)
- Launch: Best practices workshops (teach team leads)
- Target: 400 NSM (up 43%)

---

## Part 7: How to Measure the NSM

### SQL Query

```sql
-- Weekly Active Teams with 50%+ Completion (North Star Metric)

WITH weekly_team_completions AS (
  -- Step 1: Count completions per team this week
  SELECT
    team_id,
    COUNT(DISTINCT user_id) AS members_completed_this_week,
    tm.team_size
  FROM assessment_responses ar
  JOIN teams tm ON ar.team_id = tm.id
  WHERE ar.completed_at >= NOW() - INTERVAL '7 days'
    AND ar.status = 'completed'
  GROUP BY team_id, tm.team_size
),

completion_rates AS (
  -- Step 2: Calculate completion rate per team
  SELECT
    team_id,
    members_completed_this_week,
    team_size,
    members_completed_this_week::FLOAT / NULLIF(team_size, 0) AS completion_rate
  FROM weekly_team_completions
  WHERE members_completed_this_week >= 2  -- At least 2 members completed
)

-- Step 3: Count teams with 50%+ completion
SELECT
  COUNT(*) AS weekly_active_teams_50_plus_completion
FROM completion_rates
WHERE completion_rate >= 0.5;  -- 50%+ threshold
```

### Dashboard Visualization

```
┌─────────────────────────────────────────────────────────────┐
│         NORTH STAR METRIC DASHBOARD                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Weekly Active Teams with 50%+ Completion                   │
│                                                             │
│  ████████████████████ 120                                   │
│                                                             │
│  Current Week: 120 teams                                    │
│  Previous Week: 115 teams (+4.3%)                           │
│  Target: 150 teams                                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  TREND (Last 12 Weeks)                                      │
│                                                             │
│  160│                                                      ╷
│     │                                                   ╷  │
│  140│                                                ╷    │
│     │                                             ╷      │
│  120│   ╭─╮    ╭─╮    ╭─╮    ╭─╮               ╷        │
│     │  ╱  ╲  ╱  ╲  ╱  ╲  ╱  ╲             ╷          │
│  100│ ╱    ╲╱    ╲╱    ╲╱    ╲            ╷            │
│     └──────────────────────────────────────╲─────────────┤
│       W1  W2  W3  W4  W5  W6  W7  W8  W9  W10 W11 W12 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  BREAKDOWN BY SEGMENT                                       │
│                                                             │
│  SMB (1-25 people):      85 teams (71%)                     │
│  Mid-Market (26-100):     30 teams (25%)                    │
│  Enterprise (100+):        5 teams (4%)                     │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  TOP 5 TEAMS BY COMPLETION RATE                             │
│                                                             │
│  1. Marketing Team A       95% (19/20 members)              │
│  2. Sales Team B           92% (12/13 members)              │
│  3. Engineering Team C     88% (22/25 members)              │
│  4. HR Team D              85% (11/13 members)              │
│  5. Customer Success E     82% (9/11 members)               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Alerts and Monitoring

**Daily Alert (9 AM):**
```
North Star Metric Update: Yesterday
- Teams with 50%+ completion: 118 teams
- Previous day: 115 teams (+2.6%)
- Status: ✅ On track for weekly target (120 teams)
```

**Weekly Alert (Monday 9 AM):**
```
North Star Metric Weekly Summary
- This week: 120 teams
- Last week: 115 teams (+4.3%)
- Target: 150 teams (80% of target)
- Status: ⚠️ Below target, need +30 teams to hit goal
- Top contributor: Reminder system (+15 teams)
- Action item: CS team to reach out to 30 at-risk teams
```

**Real-Time Dashboard (Always Available):**
- Current NSM count (live)
- Trend (last 7 days, 4 weeks, 12 weeks)
- Breakdown by segment (SMB, mid-market, enterprise)
- Top/bottom performing teams
- Input metrics (new teams, activation rate, completion rate)

---

## Part 8: NSM in Action: Decision-Making Framework

### Framework: Does This Impact the NSM?

When making any decision (feature prioritization, investment, hiring), ask:

**Question:** Will this increase Weekly Active Teams with 50%+ Completion?

**If YES:** Prioritize it
**If NO:** De-prioritize it (or question why we're doing it)

---

### Example Decisions

#### Decision 1: Should We Build a Mobile App?

**Analysis:**
- **Impact on NSM:** YES - Mobile will make it easier for team members to complete assessments anywhere
- **Expected Impact:** +15% completion rate (from 55% to 63%)
- **Cost:** $200K development cost
- **Timeline:** 6 months

**Decision:** ✅ YES - Build mobile app
**Reasoning:** High impact on NSM, justifies investment

---

#### Decision 2: Should We Build a Team Calendar Integration?

**Analysis:**
- **Impact on NSM:** UNCLEAR - Calendar integration might help schedule assessments, but is it a blocker?
- **Expected Impact:** +5% activation rate (maybe)
- **Cost:** $100K development cost
- **Timeline:** 3 months

**Decision:** ⚠️ MAYBE - Validate demand first
**Reasoning:** Uncertain impact on NSM. Run survey: Ask 100 teams "Would calendar integration make you more likely to assign assessments?" If >50% say yes, build it.

---

#### Decision 3: Should We Sponsor a Industry Conference?

**Analysis:**
- **Impact on NSM:** INDIRECT - Brand awareness, but won't directly drive completions
- **Expected Impact:** +5 new teams/week (maybe)
- **Cost:** $50K sponsorship
- **Timeline:** One-time event

**Decision:** ❌ NO - Don't sponsor
**Reasoning:** Low impact on NSM for the cost. Better to invest in content marketing (higher ROI).

---

#### Decision 4: Should We Hire a Customer Success Manager?

**Analysis:**
- **Impact on NSM:** YES - CS will help teams activate and engage, driving completions
- **Expected Impact:** +10% completion rate (from 55% to 60%)
- **Cost:** $80K/year salary
- **Timeline:** Immediate impact

**Decision:** ✅ YES - Hire CS manager
**Reasoning:** Direct impact on NSM, justifies cost.

---

## Part 9: Common Pitfalls and How to Avoid Them

### Pitfall 1: Vanity Metric Creep

**Mistake:** Focusing on "total registered users" instead of NSM
**Why It's Wrong:** Users can sign up and never use the product. Doesn't reflect value.
**How to Avoid:** Every all-hands starts with NSM update. No vanity metrics on executive dashboards.

---

### Pitfall 2: Silo Optimization

**Mistake:** Marketing optimizes for "trial signups" (their metric) while ignoring activation/engagement
**Why It's Wrong:** Low-quality signups won't activate or engage. Waste of marketing spend.
**How to Avoid:** Marketing's success metric = "New Teams that Reach 50%+ Completion" (not just signups).

---

### Pitfall 3: Gaming the Metric

**Mistake:** Teams find ways to "cheat" the metric (e.g., creating fake teams, completing assessments multiple times)
**Why It's Wrong:** Inflates NSM without creating real value. Misleads decision-making.
**How to Avoid:** Define clear rules (teams must have ≥2 members, completions must be unique, no duplicate assessments).

---

### Pitfall 4: Metric Rigidity

**Mistake:** Refusing to evolve the NSM as the business changes
**Why It's Wrong:** What worked for 100 customers might not work for 10,000 customers.
**How to Avoid:** Review NSM quarterly. Ask: "Does this still represent our core value?" If no, evolve it.

---

### Pitfall 5: Ignoring Input Metrics

**Mistake:** Focusing only on NSM, ignoring the levers that drive it
**Why It's Wrong:** NSM is a lagging indicator. By the time it drops, it's too late to fix.
**How to Avoid:** Monitor input metrics weekly (new teams, activation rate, completion rate). Preempt NSM declines.

---

## Part 10: NSM Evolution: When to Change It

### Signs It's Time to Evolve the NSM

1. **Product Strategy Shift:**
   - Example: We pivot from "team assessments" to "individual coaching"
   - → NSM should evolve to reflect new value prop

2. **Business Model Change:**
   - Example: We shift from "team-based pricing" to "individual usage pricing"
   - → NSM should evolve to "Weekly Active Individuals" (not teams)

3. **Market Maturity:**
   - Example: We reach 10,000 teams and 50%+ completion is automatic
   - → NSM should evolve to "Teams with 80%+ Completion" (raise the bar)

4. **Value Proposition Expansion:**
   - Example: We add new features beyond assessments (e.g., goal-setting, 1:1s)
   - → NSM should evolve to "Teams Using 2+ Features Weekly"

---

### NSM Evolution Framework

**Quarterly NSM Review (Every Q1, April, July, October):**

1. **Analyze Current NSM:**
   - Is it still measuring our core value?
   - Is it still leading indicator (not lagging)?
   - Is it still actionable (every team can impact it)?

2. **Gather Feedback:**
   - Product Team: "Is this still the right goal?"
   - Leadership Team: "Does this align with business strategy?"
   - Customer Interviews: "What value do you get from PsychSync?"

3. **Propose Evolution (If Needed):**
   - Draft new NSM definition
   - Calculate historical performance for new NSM
   - Present to leadership for approval

4. **Communicate Evolution:**
   - Explain WHY we're evolving the NSM
   - Show historical performance (old NSM vs. new NSM)
   - Set new targets
   - Update all dashboards, alerts, reports

---

## Conclusion

The **North Star Metric** is the compass that guides PsychSync. By aligning the entire company around **Weekly Active Teams with 50%+ Assessment Completion**, we ensure:

1. **Customer Value:** Every initiative must drive team engagement (not just vanity metrics)
2. **Business Health:** Teams that engage → retain → pay → grow revenue
3. **Team Alignment:** Every team knows how they impact the NSM
4. **Prioritization:** Every decision is filtered through "Will this move the NSM?"

**The NSM is not just a metric—it's a mindset.**

---

**Next Steps:**
1. ✅ Present NSM to leadership for approval
2. ✅ Update all dashboards to show NSM prominently
3. ✅ Create NSM update slide for all-hands (weekly)
4. ✅ Train every team on how they impact the NSM
5. ✅ Set Q1 2026 target: 150 weekly active teams with 50%+ completion

**Let's make the North Star Metric the heartbeat of PsychSync.** 🌟

---

**Document Owner:** Product Team
**Next Review:** Quarterly (April 2026, July 2026, October 2026)
**Change Log:**
- v1.0 (January 12, 2026): Initial North Star Metric definition
