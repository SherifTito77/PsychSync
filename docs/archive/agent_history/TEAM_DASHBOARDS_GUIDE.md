# 👥 Team Dashboards - Complete Guide

## ✅ Team Analytics Complete!

Managers can now view **aggregate email analytics** across teams and organizations.

---

## 🚀 Quick Start

### 1. Backend API

```python
# Service: app/services/team_analytics_service.py
# Endpoints: app/api/v1/endpoints/team_analytics.py
# API Routes: /api/v1/team-analytics/*
```

### 2. Get Team Analytics

```bash
curl http://localhost:8000/api/v1/team-analytics/team/1?days=30 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Compare Multiple Teams

```bash
curl -X POST http://localhost:8000/api/v1/team-analytics/compare-teams \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "team_ids": [1, 2, 3],
    "days": 30
  }'
```

---

## 📊 Features Overview

| Feature | Description |
|---------|-------------|
| **Team Analytics** | Aggregate metrics for entire team |
| **Member Breakdown** | Individual performance within team |
| **Team Comparison** | Compare metrics across teams |
| **Organization Analytics** | Company-wide analytics |
| **Leaderboards** | Top performers identification |
| **Trend Analysis** | Productivity/sentiment over time |
| **Actionable Insights** | Recommendations for improvement |

---

## 🎯 API Endpoints

### Get Team Analytics

**Endpoint:** `GET /api/v1/team-analytics/team/{team_id}`

**Query Parameters:**
- `days`: Number of days to analyze (1-365, default: 30)

**Response:**
```json
{
  "success": true,
  "analytics": {
    "team_id": 1,
    "period_days": 30,
    "team_size": 5,
    "member_analytics": [
      {
        "member_id": 1,
        "member_name": "John Doe",
        "member_email": "john@example.com",
        "analytics": {
          "total_emails": 1250,
          "emails_last_period": 87,
          "daily_average": 42,
          "categories": {...},
          "response_time": {"avg_minutes": 45},
          "sentiment": {"positive": 65, "neutral": 25, "negative": 10},
          "stress_level": "moderate",
          "productivity_score": 78
        }
      }
    ],
    "team_metrics": {
      "total_emails": 6250,
      "emails_this_period": 435,
      "daily_average_per_member": 38.5,
      "category_breakdown": {...},
      "average_response_time_minutes": 42.3,
      "sentiment_distribution": {...},
      "stress_distribution": {"moderate": 3, "low": 2},
      "average_productivity_score": 76.8,
      "top_performers": [
        {"name": "Jane Smith", "score": 92},
        {"name": "John Doe", "score": 85}
      ]
    },
    "insights": [
      "Team productivity is good - room for improvement",
      "Team maintains highly positive communication tone"
    ]
  }
}
```

### Compare Teams

**Endpoint:** `POST /api/v1/team-analytics/compare-teams`

**Request:**
```json
{
  "team_ids": [1, 2, 3],
  "days": 30
}
```

**Response:**
```json
{
  "success": true,
  "comparison": {
    "period_days": 30,
    "teams_compared": 3,
    "team_rankings": [
      {
        "rank": 1,
        "team_id": 2,
        "productivity_score": 84.5,
        "total_emails": 5200,
        "avg_response_time": 35.2
      },
      {"rank": 2, "team_id": 1, ...},
      {"rank": 3, "team_id": 3, ...}
    ],
    "improvement_areas": [
      "Response times across all teams could be improved"
    ]
  }
}
```

### Get Organization Analytics

**Endpoint:** `GET /api/v1/team-analytics/organization/{org_id}`

**Response:**
```json
{
  "success": true,
  "analytics": {
    "organization_id": 1,
    "total_teams": 3,
    "total_members": 15,
    "organization_metrics": {
      "total_emails": 18750,
      "average_productivity_score": 74.2,
      "best_performing_team": {
        "team_id": 2,
        "team_name": "Engineering",
        "productivity_score": 84.5
      }
    }
  }
}
```

---

## 📈 Metrics Explained

### Team Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| **Total Emails** | All emails sent/received by team | Volume analysis |
| **Daily Average per Member** | Average emails per person | Workload balance |
| **Category Breakdown** | Email types (security, financial, etc.) | Focus areas |
| **Average Response Time** | Minutes to respond | Efficiency |
| **Sentiment Distribution** | Positive/neutral/negative ratio | Team morale |
| **Stress Distribution** | Stress levels across team | Wellbeing |
| **Productivity Score** | Composite performance metric (0-100) | Overall performance |

### Productivity Score Calculation

```
Productivity Score = (
  (Email Volume * 0.3) +
  (Response Speed * 0.3) +
  (Positive Sentiment * 0.2) +
  (Low Stress * 0.2)
) * 100
```

---

## 🎨 Use Cases

### 1. Manager Dashboard

View team performance at a glance:

```tsx
function TeamManagerDashboard({ teamId }) {
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    fetch(`/api/v1/team-analytics/team/${teamId}`)
      .then(r => r.json())
      .then(data => setAnalytics(data.analytics));
  }, [teamId]);

  return (
    <div>
      <h2>Team Performance</h2>
      <MetricCard
        title="Productivity Score"
        value={analytics?.team_metrics.average_productivity_score}
        target={80}
      />
      <MemberTable members={analytics?.member_analytics} />
      <InsightsList insights={analytics?.insights} />
    </div>
  );
}
```

### 2. Team Comparison

Compare multiple teams side-by-side:

```tsx
function TeamComparison() {
  const [comparison, setComparison] = useState(null);

  const compareTeams = (teamIds) => {
    fetch('/api/v1/team-analytics/compare-teams', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({team_ids: teamIds})
    })
    .then(r => r.json())
    .then(data => setComparison(data.comparison));
  };

  return (
    <div>
      <TeamSelector onSelect={compareTeams} />
      {comparison && (
        <Leaderboard rankings={comparison.team_rankings} />
      )}
    </div>
  );
}
```

### 3. Organization Overview

Executive view of all teams:

```tsx
function OrganizationDashboard({ orgId }) {
  const [orgAnalytics, setOrgAnalytics] = useState(null);

  useEffect(() => {
    fetch(`/api/v1/team-analytics/organization/${orgId}`)
      .then(r => r.json())
      .then(data => setOrgAnalytics(data.analytics));
  }, [orgId]);

  return (
    <div>
      <h2>Organization Overview</h2>
      <StatGrid
        totalTeams={orgAnalytics?.total_teams}
        totalMembers={orgAnalytics?.total_members}
        avgProductivity={orgAnalytics?.organization_metrics.average_productivity_score}
      />
      <BestTeam team={orgAnalytics?.organization_metrics.best_performing_team} />
    </div>
  );
}
```

---

## 💡 Insights Generated

### Productivity Insights

- Score ≥ 80: "Team productivity is excellent - maintain current practices"
- Score 60-79: "Team productivity is good - room for improvement"
- Score < 60: "Team productivity needs attention - consider workflow optimization"

### Stress Insights

- High stress > 50%: "More than half the team shows high stress - consider workload rebalancing"
- Multiple stress levels: "Varied stress levels - investigate individual workloads"

### Sentiment Insights

- Positive > 70%: "Team maintains highly positive communication tone"
- Positive < 40%: "Team communication tone is concerning - address team morale"

### Response Time Insights

- > 60 minutes: "Average response time is over 1 hour - consider improving communication efficiency"
- < 30 minutes: "Excellent response time - team is highly responsive"

---

## 🎯 Implementation Roadmap

### Phase 1: Core ✅ (Complete)
- ✅ Team aggregation
- ✅ Member breakdown
- ✅ Basic metrics
- ✅ Team comparison
- ✅ Organization analytics

### Phase 2: Enhanced (Ready to Implement)
- ⏳ Historical trend charts
- ⏳ Goal setting and tracking
- ⏳ Performance benchmarks
- ⏳ Automated reports

### Phase 3: Advanced
- ⏳ Predictive analytics
- ⏳ Team optimization recommendations
- ⏳ Skill gap analysis
- ⏳ Workload balancing suggestions

---

## ✨ Summary

**Status:** ✅ **COMPLETE & FUNCTIONAL**

Team Dashboards provide:
- ✅ Aggregate team metrics
- ✅ Individual member breakdowns
- ✅ Cross-team comparison
- ✅ Organization-wide analytics
- ✅ Top performer identification
- ✅ Actionable insights
- ✅ REST API ready for integration

**Ready to visualize:** Use API endpoints to build team analytics dashboards!

---

*Generated: 2026-01-22*
*PsychSync Email Monitoring System v1.0*
*Status: ✅ Team Dashboards Operational*
