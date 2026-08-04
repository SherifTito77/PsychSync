# CEO Executive Dashboard Design - Organizational Health Index

## Executive Summary

**Principle:** CEOs don't want metrics. They want answers and risk.

**Framing:** "Systems under strain" NOT "people are stressed"

**Goal:** Future-focused, not blame-focused

---

## 🎯 Dashboard Layout (3 Panels Only)

### Panel 1: Organizational Health Index (OHI)

**Single Number (0-100)**

```
┌─────────────────────────────────┐
│                                 │
│       ORGANIZATIONAL HEALTH      │
│                                 │
│            72.3                 │
│                                 │
│      ▲ 5.2 from last month      │
│                                 │
│        🟢 AMBER / CAUTION        │
│                                 │
└─────────────────────────────────┘
```

**Interpretation:**
- **80-100**: 🟢 GREEN - Healthy
- **60-79**: 🟡 AMBER - Monitor
- **40-59**: 🟠 ORANGE - Action Required
- **0-39**: 🔴 RED - Critical

**Calculation:**
```python
OHI = 100 - weighted_average(
    0.35 × avg_PRI,
    0.25 × avg_early_warning_score,
    0.20 × team_friction_index,
    0.20 × attrition_risk
)
```

**What CEO sees:** "Is the org healthy right now?"
- One glance answer
- Trend direction (↑↓)
• Status color (green/amber/red)

---

### Panel 2: Risk Heatmap

**X-axis: Teams**
**Y-axis: Time (last 30 days)**

```
Risk Level
High │      ██                  ██
    │   ██  ██    ██          ██  ██
Med │   ██  ██    ██    ██   ██  ██    ██
    │██  ██  ██    ██    ██  ██  ██    ██  ██
Low │██  ██  ██    ██    ██  ██  ██    ██  ██
    └───────────────────────────────────────
       Eng  Sales  HR  Marketing  Finance  Ops
```

**Color Coding:**
- 🟢 **Green**: Stable (EW < 50, PRI < 45)
- 🟡 **Yellow**: Rising load (EW 50-70, PRI 45-60)
- 🔴 **Red**: Sustained risk (EW > 70, PRI > 60 for 3+ days)

**What CEO sees:** "Where do I need to act?"

**Interactivity:**
- Hover: See exact scores for each team/day
- Click: Drill down to team details
- Filter: Show only red/yellow teams

---

### Panel 3: Leading Indicator Panel

**Not what happened — what's coming**

```
┌────────────────────────────────────────────────┐
│         🔴 TEAMS WITH RISING EW CURVES         │
├────────────────────────────────────────────────┤
│ 1. Engineering Team 4 (EW: 45→72 in 14 days)  │
│ 2. Sales - West Region (EW: 38→65 in 10 days) │
│ 3. Customer Success (EW: 42→61 in 7 days)     │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│        🔴 PROJECTS DRIVING OVERLOAD            │
├────────────────────────────────────────────────┤
│ 1. Q1 Product Launch (3 teams affected)       │
│ 2. Enterprise Migration (2 teams affected)    │
│ 3. Audit Preparation (1 team affected)        │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│       🔴 LEADERSHIP PRESSURE HOTSPOTS          │
├────────────────────────────────────────────────┤
│ 1. Director of Engineering (6 reports red)    │
│ 2. VP of Sales (4 reports yellow)             │
│ 3. Head of CS (3 reports red)                 │
└────────────────────────────────────────────────┘
```

**What CEO sees:** "What's coming and where should I focus?"

---

## 🚫 What You NEVER Show

### ❌ Individual Emotions
- Don't show: "John is stressed"
- Do show: "Engineering has 3 red zones"

### ❌ Private Messages
- Don't show: Message content
- Do show: Escalation density metrics

### ❌ "This person is stressed"
- Don't show: Individual blame
- Do show: Systems under strain

### ❌ Medical/Psychological Labels
- Don't show: "Depression risk", "Anxiety"
- Do show: "Cognitive load", "Team friction"

---

## ✅ What You ALWAYS Show

### ✅ System-Focused Metrics

**Instead of:** "5 people are burned out"

**Show:** "5 teams have sustained elevation in cognitive load.
           Recommend: Review project timelines and workload distribution."

### ✅ Actionable Insights

**Instead of:** "Team morale is low"

**Show:** "Customer Success team has 67% early warning score.
           Trend: Rising 8 days straight.
           Action: Review caseload distribution and hiring needs."

### ✅ Future-Focused

**Instead of:** "We had 3 people quit last month"

**Show:** "Engineering team 4 has 72% burnout probability.
           Predicted impact: 2-3 attritions in next 30 days if no action.
           Recommended: Immediate workload redistribution."

---

## 📊 Sample CEO Dashboard API

### Endpoint: Organizational Health Index

```python
GET /executive/organizational-health?org_id={id}
```

**Response:**
```json
{
  "organization_id": "acme-corp",
  "analysis_date": "2026-01-31",

  "organizational_health_index": {
    "score": 72.3,
    "trend": "improving",
    "change_from_last_month": +5.2,
    "status": "amber"
  },

  "component_breakdown": {
    "average_pri": 48.5,
    "average_early_warning": 52.3,
    "team_friction_index": 38.7,
    "attrition_risk": 22.1
  },

  "team_count": {
    "total": 12,
    "green": 7,
    "yellow": 3,
    "red": 2
  },

  "priority_actions": [
    "Address 2 red teams (Engineering-4, Sales-West)",
    "Monitor 3 yellow teams for escalation",
    "Review Q1 Product Launch workload"
  ]
}
```

### Endpoint: Risk Heatmap Data

```python
GET /executive/risk-heatmap?org_id={id}&days=30
```

**Response:**
```json
{
  "organization_id": "acme-corp",
  "period": "last_30_days",
  "heatmap_data": [
    {
      "team": "Engineering-4",
      "team_id": "eng-4",
      "daily_scores": [
        {"date": "2026-01-01", "risk_level": "yellow", "pri": 52, "ew": 48},
        {"date": "2026-01-02", "risk_level": "yellow", "pri": 54, "ew": 51},
        ...
        {"date": "2026-01-30", "risk_level": "red", "pri": 72, "ew": 75}
      ],
      "current_status": "red",
      "trend": "worsening",
      "consecutive_red_days": 8
    },
    ...
  ]
}
```

### Endpoint: Leading Indicators

```python
GET /executive/leading-indicators?org_id={id}
```

**Response:**
```json
{
  "organization_id": "acme-corp",
  "analysis_date": "2026-01-31",

  "teams_with_rising_ew": [
    {
      "team": "Engineering Team 4",
      "team_id": "eng-4",
      "ew_start": 45,
      "ew_end": 72,
      "days": 14,
      "slope": 1.9,
      "urgency": "critical"
    },
    ...
  ],

  "projects_driving_overload": [
    {
      "project": "Q1 Product Launch",
      "affected_teams": ["eng-4", "eng-2", "qa-1"],
      "avg_pri_increase": 18.5,
      "deadline": "2026-03-15",
      "recommendation": "Consider extending deadline by 2 weeks"
    },
    ...
  ],

  "leadership_hotspots": [
    {
      "leader": "Director of Engineering",
      "role": "director",
      "direct_reports": 8,
      "red_teams": 3,
      "yellow_teams": 3,
      "recommendation": "Span of control too high. Consider adding managers."
    },
    ...
  ]
}
```

---

## 🎨 Dashboard UI Components

### Component: OHIMeter

```tsx
interface OHIMeterProps {
  score: number;          // 0-100
  trend: 'up' | 'down' | 'stable';
  change: number;        // Change from last period
}

function OHIMeter({ score, trend, change }: OHIMeterProps) {
  const status = score >= 80 ? 'green' :
                score >= 60 ? 'amber' :
                score >= 40 ? 'orange' : 'red';

  return (
    <div className={`ohi-meter ohi-${status}`}>
      <div className="ohi-score">{score.toFixed(1)}</div>
      <div className="ohi-trend">
        {trend === 'up' ? '▲' : trend === 'down' ? '▼' : '─'}
        {change > 0 ? '+' : ''}{change.toFixed(1)}
      </div>
      <div className="ohi-status">{status.toUpperCase()}</div>
    </div>
  );
}
```

### Component: RiskHeatmap

```tsx
interface HeatmapData {
  team: string;
  dailyScores: Array<{
    date: string;
    riskLevel: 'green' | 'yellow' | 'red';
    pri: number;
    ew: number;
  }>;
}

function RiskHeatmap({ data }: { data: HeatmapData[] }) {
  return (
    <div className="risk-heatmap">
      {data.map(team => (
        <div key={team.team} className="heatmap-row">
          <div className="team-name">{team.team}</div>
          {team.dailyScores.map(day => (
            <div
              key={day.date}
              className={`heatmap-cell heatmap-${day.riskLevel}`}
              title={`${day.date}: PRI=${day.pri}, EW=${day.ew}`}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
```

### Component: LeadingIndicators

```tsx
interface LeadingIndicatorsProps {
  risingTeams: Array<{
    team: string;
    ewStart: number;
    ewEnd: number;
    days: number;
  }>;
  projects: Array<{
    name: string;
    affectedTeams: string[];
    deadline: string;
  }>;
  leadership: Array<{
    name: string;
    role: string;
    redTeams: number;
  }>;
}

function LeadingIndicators({
  risingTeams,
  projects,
  leadership
}: LeadingIndicatorsProps) {
  return (
    <div className="leading-indicators">
      <section>
        <h3>🔴 Teams with Rising EW Curves</h3>
        {risingTeams.map(team => (
          <div key={team.team}>
            {team.team}: {team.ewStart}→{team.ewEnd} in {team.days} days
          </div>
        ))}
      </section>

      <section>
        <h3>🔴 Projects Driving Overload</h3>
        {projects.map(project => (
          <div key={project.name}>
            {project.name} ({project.affectedTeams.length} teams affected)
          </div>
        ))}
      </section>

      <section>
        <h3>🔴 Leadership Pressure Hotspots</h3>
        {leadership.map(leader => (
          <div key={leader.name}>
            {leader.name} ({leader.redTeams} red teams)
          </div>
        ))}
      </section>
    </div>
  );
}
```

---

## 🔑 Access Control

**Who can access CEO Dashboard?**
- Roles: `admin`, `super_admin`, `executive`
- Or: Explicit permission: `view_executive_dashboard`

**API Authentication:**
```python
@router.get("/executive/organizational-health")
async def get_organizational_health(
    org_id: str,
    current_user: User = Depends(get_current_active_user)
):
    # Check permissions
    if not has_executive_access(current_user):
        raise HTTPException(403, "Executive access required")

    # Return data
    ...
```

---

## 📈 Sample CEO Alerts

### Alert 1: Red Team Detected

```
🔴 URGENT: Engineering Team 4 Risk Level Elevated

Team: Engineering Team 4
Current Status: RED (8 consecutive days)
PRI: 72.3 (↑24 from last month)
Early Warning Score: 75.8 (↑31 from last month)

Trend: Rapidly escalating
Predicted Impact: 2-3 attritions within 30 days if no action

Recommended Actions:
1. Immediate: Review workload distribution
2. Short-term: Add 1-2 engineers to team
3. Long-term: Assess project pipeline and deadlines

Cost of Inaction: ~$450K (recruiting + lost productivity)
Cost of Intervention: ~$80K (contractors + overtime)
ROI: 462% → STRONGLY RECOMMENDED
```

### Alert 2: Project Driving Overload

```
🟠 WARNING: Q1 Product Launch Causing Team Overload

Project: Q1 Product Launch
Affected Teams: 3 (Engineering-4, QA-1, DevOps)
Average PRI Increase: +18.5 points
Deadline: March 15, 2026 (45 days)

Risk: If current pace continues, 2 teams likely to burnout before launch

Recommended Actions:
1. Assess critical vs. nice-to-have features
2. Consider extending deadline by 2 weeks
3. Add contract resources for sprint 4-6

Impact: Extending deadline costs $120K
         Burnout costs $600K+ per team
         → Extension is 5x cheaper than replacement
```

---

## 🎯 Key Design Principles

### 1. Single Source of Truth
- OHI is the ONE number that matters
- Everything else explains OHI

### 2. Action-First Design
- Every data point has a clear action
- No metrics without recommendations

### 3. Future-Focused
- Leading indicators, not lagging
- Predictions, not just history

### 4. System-Focused
- "Teams under strain" not "people stressed"
- "Workload distribution" not "individual failure"

### 5. Executive Simplicity
- 3 panels only
- One glance answers
- Drill down available but not required

---

## ✅ Implementation Checklist

- [ ] OHI calculation algorithm
- [ ] Risk heatmap data aggregation
- [ ] Leading indicator detection
- [ ] API endpoints (OHI, Heatmap, Indicators)
- [ ] React components (OHIMeter, Heatmap, Indicators)
- [ ] Access control (executive role)
- [ ] Alert system with recommendations
- [ ] Cost-benefit analysis
- [ ] Drill-down capability
- [ ] Mobile-responsive design

---

## 📞 Next Steps

1. **Backend:** Implement OHI calculation
2. **API:** Create executive endpoints
3. **Frontend:** Build 3-panel dashboard
4. **Testing:** Validate with executive users
5. **Iteration:** Refine based on feedback

**Target:** CEO can understand org health in 5 seconds.
