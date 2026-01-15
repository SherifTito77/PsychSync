# Executive Reporting Dashboards Setup Guide
**Mixpanel & Amplitude Configuration**

**Date:** January 12, 2025
**Purpose:** Configure analytics dashboards for executive reporting

---

## 🎯 Objective

Configure Mixpanel or Amplitude to track the 7 KPIs defined in the Monthly Executive Product Reports, enabling the CEO to review complete business health in 20 minutes.

---

## 📊 Required Metrics (From Executive Dashboard)

### 1. ARR Growth
- **Metric:** Monthly recurring revenue
- **Calculation:** Sum of all active subscriptions
- **Update Frequency:** Daily
- **Data Source:** Database (subscriptions table)

### 2. Acquisition Metrics
- New Teams: Count of new teams created
- New Users: Count of new users registered
- CAC: Marketing spend / new customers
- Sales Cycle: Days from first touch to closed-won

### 3. Activation Metrics
- Activation Rate: Teams completing first assessment within 5 days
- Time-to-First-Value: Days from sign-up to Team Map view
- Assessment Completion: % of users completing assessment
- Team Map Views: % of teams viewing Team Personality Map

### 4. Engagement Metrics
- DAU/MAU Ratio: Daily active users / Monthly active users
- Teams with ≥3 Users: % of teams with 3+ active users
- Sessions/User/Week: Average sessions per user per week
- Avg Session Duration: Average time per session (in minutes)

### 5. Retention Metrics
- 90-Day Retention: % of teams retained after 90 days
- Net Revenue Retention: (Starting ARR + Expansion - Churn) / Starting ARR
- Logo Churn Rate: % of teams cancelled
- Expansion Revenue: Revenue from upsells/cross-sells

### 6. Product Velocity
- Features Shipped: Count of features deployed
- Sprint Velocity: Story points completed
- Bugs Closed: Count of bugs resolved
- On-Time Delivery: % of sprints delivered on time

### 7. Financials
- MRR Growth: Month-over-month MRR change
- ARPU: Average revenue per user
- Burn Rate: Monthly operating expenses
- Runway: Months of cash remaining

---

## 🔧 Mixpanel Setup

### Step 1: Account Creation
1. Go to https://mixpanel.com
2. Sign up for an account (use Growth plan for $0/month initially)
3. Create a new project: "PsychSync Production"

### Step 2: SDK Installation

**Backend (Python):**
```bash
pip install mixpanel
```

Add to `app/core/analytics.py`:
```python
import mixpanel

mp = mixpanel.Mixpanel(os.getenv("MIXPANEL_TOKEN"))

def track_event(user_id: str, event_name: str, properties: dict):
    mp.track(user_id, event_name, properties)

def set_user_properties(user_id: str, properties: dict):
    mp.people_set(user_id, properties)
```

**Frontend (React):**
```bash
npm install mixpanel-browser
```

Add to `src/main.tsx`:
```typescript
import mixpanel from 'mixpanel-browser';

mixpanel.init(import.meta.env.VITE_MIXPANEL_TOKEN, {
  debug: import.meta.env.DEV,
  track_pageview: true,
  persistence: 'localStorage'
});
```

### Step 3: Event Tracking Implementation

**Critical Events to Track:**

| Event Name | Properties | When to Track |
|------------|------------|---------------|
| `team_created` | team_id, org_id, plan, user_count | On team creation |
| `assessment_completed` | assessment_id, user_id, framework, score | On assessment completion |
| `team_map_viewed` | team_id, user_id, time_to_value | On Team Map view |
| `conflict_alert_viewed` | team_id, user_id, alert_score | On conflict alert view |
| `playbook_started` | playbook_id, team_id, user_id | On playbook start |
| `playbook_completed` | playbook_id, team_id, user_id | On playbook completion |
| `subscription_created` | subscription_id, plan, amount | On subscription |
| `subscription_cancelled` | subscription_id, reason | On cancellation |

**Implementation Example:**
```python
# In teams.py endpoint
@app.post("/")
async def create_team(team_data: TeamCreate, current_user: User = Depends(get_current_active_user)):
    # ... create team logic ...

    # Track event
    track_event(
        user_id=str(current_user.id),
        event_name="team_created",
        properties={
            "team_id": str(new_team.id),
            "org_id": str(new_team.organization_id),
            "plan": "starter",  # or team/enterprise
            "user_count": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    return new_team
```

### Step 4: Create Executive Dashboard

1. Go to Mixpanel → Dashboards → Create Dashboard
2. Name: "Executive Dashboard - CEO"
3. Add these panels:

**Panel 1: ARR Growth (Line Chart)**
- Event: `subscription_created`
- Measure: Total sum of `amount`
- Time range: Last 90 days
- Compare to: Previous period

**Panel 2: New Teams (Line Chart)**
- Event: `team_created`
- Measure: Unique `team_id`
- Time range: Last 30 days

**Panel 3: Activation Rate (Funnel)**
- Steps: `team_created` → `assessment_completed` → `team_map_viewed`
- Time range: Last 30 days

**Panel 4: DAU/MAU Ratio (Line Chart)**
- Event: `session_started`
- Measure: Unique `user_id`
- Time range: Last 90 days
- Calculation: DAU / MAU

**Panel 5: 90-Day Retention (Retention Curve)**
- Cohort: `team_created`
- Return action: `assessment_completed`
- Intervals: Days 1, 7, 14, 30, 60, 90

### Step 5: Schedule Reports
1. Go to Mixpanel → Reports
2. Create report: "Weekly Executive Report"
3. Schedule: Every Monday 8 AM PT
4. Email to: ceo@psychsync.io, cpo@psychsync.io
5. Include: Executive dashboard PDF

---

## 🔧 Amplitude Setup (Alternative)

### Step 1: Account Creation
1. Go to https://amplitude.com
2. Sign up for Growth plan (free up to 1M events/month)
3. Create a new project: "PsychSync Production"

### Step 2: SDK Installation

**Backend:**
```bash
pip install amplitude-analytics
```

Add to `app/core/analytics.py`:
```python
from amplitude import Amplitude, BaseEvent

client = Amplitude(os.getenv("AMPLITUDE_API_KEY"))

def track_event(user_id: str, event_name: str, properties: dict):
    event = BaseEvent(user_id=user_id, event_type=event_name, event_properties=properties)
    client.track(event)
```

**Frontend:**
```bash
npm install @amplitude/analytics-browser
```

Add to `src/main.tsx`:
```typescript
import * as amplitude from '@amplitude/analytics-browser';

amplitude.init(import.meta.env.VITE_AMPLITUDE_API_KEY, {
  defaultTracking: true
});
```

### Step 3: Event Tracking
Use the same event schema as Mixpanel (see above)

### Step 4: Create Executive Dashboard

1. Go to Amplitude → Dashboards → New Dashboard
2. Name: "Executive Dashboard"
3. Add charts:

**Chart 1: Revenue (Line Chart)**
- Metric: Revenue (custom property from `subscription_created`)
- Time range: Last 90 days

**Chart 2: Active Teams (Line Chart)**
- Metric: Active teams (performed `team_created` event in last 30 days)
- Time range: Last 90 days

**Chart 3: Conversion Funnel**
- Steps: Sign up → Team created → Assessment completed → Team map viewed
- Time range: Last 30 days

**Chart 4: Retention (Retention Analysis)**
- Cohort: Sign up
- Return action: Any event
- Days: 1, 7, 14, 30, 60, 90

### Step 5: Schedule Reports
1. Go to Amplitude → Reports → Schedule
2. Create weekly report
3. Email to: ceo@psychsync.io, cpo@psychsync.io

---

## 🎨 Dashboard Design Best Practices

### Color Scheme
- 🟢 Green: On track (>100% of target)
- 🟡 Yellow: At risk (80-99% of target)
- 🔴 Red: Off track (<80% of target)

### Layout
- **Top Row:** ARR Growth, New Teams, Activation Rate (3 columns)
- **Middle Row:** Engagement Metrics (4 columns)
- **Bottom Row:** Retention, Financials, Product Velocity (3 columns)

### Annotations
- Mark product launches (Team Map, Slack Integration, etc.)
- Mark marketing campaigns
- Mark outages/incidents

---

## ✅ Setup Checklist

### Mixpanel
- [ ] Account created
- [ ] Project created
- [ ] SDK installed (backend + frontend)
- [ ] Events tracked (all 8 critical events)
- [ ] Dashboard created (all 5 panels)
- [ ] Report scheduled (weekly)
- [ ] Email recipients configured

### Amplitude (Alternative)
- [ ] Account created
- [ ] Project created
- [ ] SDK installed (backend + frontend)
- [ ] Events tracked (all 8 critical events)
- [ ] Dashboard created (all 4 charts)
- [ ] Report scheduled (weekly)
- [ ] Email recipients configured

### Verification
- [ ] Test event tracking (send test events)
- [ ] Verify dashboard populates with data
- [ ] Test email delivery
- [ ] Train CEO on dashboard usage

---

## 📞 Support

**Mixpanel Documentation:** https://docs.mixpanel.com
**Amplitude Documentation:** https://amplitude.com/docs
**Internal Contact:** [Data Engineer Name] - [Email]

---

*Last Updated: January 12, 2025*
*Next Review: Monthly (ensure metrics align to business goals)*
