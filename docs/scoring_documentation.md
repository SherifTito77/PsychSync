# Psychological Assessment Scoring System - Complete Documentation

## Overview

The PsychSync Scoring System provides comprehensive psychological analytics using multi-dimensional assessment approaches. The system calculates scores across key psychological dimensions and generates overall wellness and performance insights on a 0-100 scale.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Scoring Methodology](#scoring-methodology)
3. [API Reference](#api-reference)
4. [Database Schema](#database-schema)
5. [Automated Tasks](#automated-tasks)
6. [Frontend Integration](#frontend-integration)
7. [Deployment](#deployment)
8. [Testing](#testing)

---

## System Architecture

### Components

```
┌─────────────────┐
│   Frontend      │  React Dashboard with Recharts
│   (React)       │  - Assessment results
└────────┬────────┘  - Progress tracking
         │           - Wellness insights
         ↓
┌─────────────────┐
│   API Layer     │  FastAPI Endpoints
│   (FastAPI)     │  - /api/scoring/assessment/{id}
└────────┬────────┘  - /api/scoring/psychometric-profile
         │           - /api/scoring/team-analysis
         ↓
┌─────────────────┐
│ Scoring Engine  │  Python Service
│   (Python)      │  - Category calculations
└────────┬────────┘  - Trend analysis
         │           - Insight generation
         ↓
┌─────────────────┐
│   Database      │  PostgreSQL
│  (PostgreSQL)   │  - assessment_scores
└────────┬────────┘  - score_history
         │           - wellness_insights
         ↓
┌─────────────────┐
│   AI Engine     │  PsychSync AI
│    (PsychSync)  │  - Pattern recognition
└─────────────────┘  - Predictive analytics
                     - Recommendation engine
```

---

## Scoring Methodology

### Assessment Framework Categories

The overall psychological wellness score is calculated as a weighted average of multiple dimensions:

| Category        | Weight | Description |
|-----------------|--------|-------------|
| Cognitive       | 20%    | Mental clarity, problem-solving, memory |
| Emotional       | 25%    | Emotional regulation, resilience, stability |
| Social          | 15%    | Interpersonal skills, communication, teamwork |
| Behavioral      | 15%    | Work patterns, habits, productivity |
| Professional    | 15%    | Performance, engagement, satisfaction |
| Physical        | 10%    | Stress indicators, energy levels, wellness |

### Scoring Formulas

#### 1. Cognitive Category (0-100)
```
Cognitive Score = (Mental_Clarity × 0.3) + (Problem_Solving × 0.4) + (Memory_Focus × 0.3)

Where:
- Mental_Clarity = Self-rated mental clarity score
- Problem_Solving = Assessment-based problem solving ability
- Memory_Focus = Concentration and memory performance metrics
```

#### 2. Emotional Category (0-100)
```
Emotional Score = (Emotional_Regulation × 0.4) + (Resilience × 0.3) + (Stress_Management × 0.3)

Where:
- Emotional_Regulation = Ability to manage emotions effectively
- Resilience = Bounce-back ability from setbacks
- Stress_Management = Coping mechanisms and stress levels
```

#### 3. Social Category (0-100)
```
Social Score = (Communication × 0.4) + (Teamwork × 0.3) + (Leadership × 0.3)

Where:
- Communication = Interpersonal communication effectiveness
- Teamwork = Collaborative skills and team integration
- Leadership = Influence and guidance capabilities
```

#### 4. Behavioral Category (0-100)
```
Behavioral Score = (Productivity × 0.4) + (Work_Habits × 0.3) + (Time_Management × 0.3)

Where:
- Productivity = Output and efficiency metrics
- Work_Habits = Consistency and quality of work patterns
- Time_Management = Prioritization and scheduling effectiveness
```

#### 5. Professional Category (0-100)
```
Professional Score = (Job_Satisfaction × 0.3) + (Engagement × 0.4) + (Performance × 0.3)

Where:
- Job_Satisfaction = Overall career and role satisfaction
- Engagement = Work involvement and commitment levels
- Performance = Goal achievement and contribution metrics
```

#### 6. Physical Category (0-100)
```
Physical Score = (Energy_Levels × 0.4) + (Stress_Indicators × 0.3) + (Wellness_Habits × 0.3)

Where:
- Energy_Levels = Daily energy and vitality
- Stress_Indicators = Physical manifestations of stress (inverted)
- Wellness_Habits = Sleep, nutrition, exercise patterns
```

---

## API Reference

### Assessment Scoring Endpoints

#### Get Assessment Score
```http
GET /api/v1/scoring/assessment/{assessment_id}
```

**Parameters:**
- `assessment_id` (path, required): Assessment identifier

**Response:**
```json
{
  "assessment_id": "uuid",
  "user_id": "uuid",
  "overall_score": 78.5,
  "category_scores": {
    "cognitive": 82.0,
    "emotional": 75.0,
    "social": 80.0,
    "behavioral": 76.0,
    "professional": 79.0,
    "physical": 74.0
  },
  "insights": [
    "Strong problem-solving skills demonstrated",
    "Consider stress management techniques",
    "Excellent team collaboration patterns"
  ],
  "recommendations": [
    "Practice mindfulness exercises",
    "Schedule regular breaks during work",
    "Continue developing leadership skills"
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Get Psychometric Profile
```http
GET /api/v1/scoring/psychometric-profile/{user_id}
```

**Parameters:**
- `user_id` (path, required): User identifier
- `period_days` (query, optional): Analysis period in days (default: 30)

**Response:**
```json
{
  "user_id": "uuid",
  "analysis_period_days": 30,
  "baseline_score": 75.0,
  "current_score": 78.5,
  "improvement_trend": 0.12,
  "category_trends": {
    "cognitive": 0.08,
    "emotional": 0.15,
    "social": 0.10,
    "behavioral": 0.05,
    "professional": 0.18,
    "physical": 0.12
  },
  "risk_factors": [
    "High stress levels detected",
    "Irregular sleep patterns"
  ],
  "strengths": [
    "Strong analytical thinking",
    "Effective communication skills",
    "Consistent work performance"
  ]
}
```

#### Team Analysis
```http
GET /api/v1/scoring/team-analysis/{team_id}
```

**Parameters:**
- `team_id` (path, required): Team identifier

**Response:**
```json
{
  "team_id": "uuid",
  "team_size": 8,
  "average_score": 76.2,
  "cohesion_score": 82.0,
  "communication_effectiveness": 79.0,
  "collaboration_score": 81.0,
  "individual_profiles": [
    {
      "user_id": "uuid",
      "score": 78.5,
      "role": "Team Lead",
      "strengths": ["Leadership", "Communication"]
    }
  ],
  "team_insights": [
    "Strong collaborative dynamics",
    "Good balance of skills and perspectives",
    "Consider cross-training opportunities"
  ],
  "recommendations": [
    "Schedule regular team check-ins",
    "Implement peer recognition program",
    "Provide professional development resources"
  ]
}
```

---

## Database Schema

### Core Tables

#### assessment_scores
```sql
CREATE TABLE assessment_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES assessments(id),
    user_id UUID NOT NULL REFERENCES users(id),
    overall_score DECIMAL(5,2) NOT NULL,
    cognitive_score DECIMAL(5,2),
    emotional_score DECIMAL(5,2),
    social_score DECIMAL(5,2),
    behavioral_score DECIMAL(5,2),
    professional_score DECIMAL(5,2),
    physical_score DECIMAL(5,2),
    insights JSONB,
    recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### score_history
```sql
CREATE TABLE score_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    score_date DATE NOT NULL,
    overall_score DECIMAL(5,2) NOT NULL,
    category_scores JSONB,
    assessment_type VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### wellness_insights
```sql
CREATE TABLE wellness_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    insight_type VARCHAR(50) NOT NULL,
    insight_text TEXT NOT NULL,
    priority_level INTEGER DEFAULT 3,
    is_actioned BOOLEAN DEFAULT FALSE,
    valid_until DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Automated Tasks

### Scheduled Analyses

#### Daily Score Updates
```python
# Runs daily at 2 AM
async def update_daily_scores():
    """Update assessment scores and generate insights"""
    users = await get_active_users()
    for user in users:
        scores = await calculate_latest_scores(user.id)
        insights = await generate_insights(user.id, scores)
        await save_scores_and_insights(user.id, scores, insights)
```

#### Weekly Trend Analysis
```python
# Runs every Sunday at 6 PM
async def weekly_trend_analysis():
    """Analyze weekly trends and generate reports"""
    teams = await get_active_teams()
    for team in teams:
        team_analysis = await analyze_team_dynamics(team.id)
        await generate_team_report(team.id, team_analysis)
```

#### Monthly Wellness Reports
```python
# Runs on 1st of each month
async def monthly_wellness_report():
    """Generate comprehensive monthly wellness reports"""
    users = await get_all_users()
    for user in users:
        monthly_data = await compile_monthly_data(user.id)
        report = await generate_wellness_report(user.id, monthly_data)
        await deliver_report(user.id, report)
```

---

## Frontend Integration

### React Components

#### AssessmentScoreCard
```typescript
interface AssessmentScoreCardProps {
  score: AssessmentScore;
  showDetails?: boolean;
  onInsightClick?: (insight: string) => void;
}

const AssessmentScoreCard: React.FC<AssessmentScoreCardProps> = ({
  score,
  showDetails = false,
  onInsightClick
}) => {
  return (
    <Card className="assessment-score-card">
      <div className="overall-score">
        <CircularProgress value={score.overall_score} />
        <h3>Overall Wellness: {score.overall_score}</h3>
      </div>

      {showDetails && (
        <div className="category-breakdown">
          {Object.entries(score.category_scores).map(([category, value]) => (
            <div key={category} className="category-score">
              <span>{category}</span>
              <ProgressBar value={value} />
            </div>
          ))}
        </div>
      )}

      <div className="insights">
        {score.insights.map((insight, index) => (
          <InsightTag
            key={index}
            insight={insight}
            onClick={() => onInsightClick?.(insight)}
          />
        ))}
      </div>
    </Card>
  );
};
```

#### TeamAnalyticsDashboard
```typescript
interface TeamAnalyticsProps {
  teamId: string;
  dateRange: DateRange;
}

const TeamAnalyticsDashboard: React.FC<TeamAnalyticsProps> = ({
  teamId,
  dateRange
}) => {
  const [teamData, setTeamData] = useState<TeamAnalysis | null>(null);

  useEffect(() => {
    fetchTeamAnalysis(teamId, dateRange).then(setTeamData);
  }, [teamId, dateRange]);

  if (!teamData) return <LoadingSpinner />;

  return (
    <div className="team-analytics">
      <TeamOverviewCard teamData={teamData} />
      <TeamTrendsChart trends={teamData.trend_data} />
      <IndividualComparisonGrid members={teamData.individual_profiles} />
      <TeamInsightsPanel insights={teamData.team_insights} />
    </div>
  );
};
```

---

## Testing

### Unit Tests
```python
async def test_assessment_scoring_calculation():
    """Test psychological assessment scoring algorithm"""
    user = create_test_user()
    assessment = create_test_assessment()

    # Mock assessment responses
    responses = {
        'cognitive': [4, 5, 3, 4, 5],  # Scale 1-5
        'emotional': [3, 4, 4, 5, 3],
        'social': [5, 4, 4, 4, 5],
        'behavioral': [4, 4, 5, 3, 4],
        'professional': [5, 5, 4, 4, 4],
        'physical': [3, 4, 3, 4, 3]
    }

    score = await calculate_assessment_score(user.id, assessment.id, responses)

    assert score.overall_score >= 0
    assert score.overall_score <= 100
    assert len(score.category_scores) == 6
    assert score.insights is not None
```

### Integration Tests
```python
async def test_scoring_api_integration():
    """Test scoring API endpoints"""
    client = AsyncClient(app=app, base_url="http://test")

    # Create test user and assessment
    user_response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert user_response.status_code == 201

    # Create assessment
    assessment_response = await client.post(
        "/api/v1/assessments",
        json=test_assessment_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert assessment_response.status_code == 201

    # Get assessment score
    score_response = await client.get(
        f"/api/v1/scoring/assessment/{assessment_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert score_response.status_code == 200
    score_data = score_response.json()
    assert "overall_score" in score_data
    assert "category_scores" in score_data
```

---

## Deployment

### Production Configuration
```yaml
# docker-compose.prod.yml
services:
  psychsync-api:
    image: psychsync/api:latest
    environment:
      - DATABASE_URL=postgresql://psychsync_user:${DB_PASSWORD}@postgres:5432/psychsync_db
      - REDIS_URL=redis://redis:6379/0
      - SCORING_ALGORITHM_VERSION=2.1
      - INSIGHT_GENERATION_ENABLED=true
    depends_on:
      - postgres
      - redis
      - celery-worker

  celery-worker:
    image: psychsync/api:latest
    command: celery -A app.core.celery_worker worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://psychsync_user:${DB_PASSWORD}@postgres:5432/psychsync_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  celery-beat:
    image: psychsync/api:latest
    command: celery -A app.core.celery_worker beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://psychsync_user:${DB_PASSWORD}@postgres:5432/psychsync_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
```

### Environment Variables
```bash
# .env.prod
DATABASE_URL=postgresql://psychsync_user:secure_password@postgres:5432/psychsync_db
REDIS_URL=redis://redis:6379/0

# Scoring Configuration
SCORING_ALGORITHM_VERSION=2.1
INSIGHT_GENERATION_ENABLED=true
WELLNESS_ALERT_THRESHOLD=65
TEAM_COHESION_WEIGHT=0.3

# Performance Tuning
SCORING_CACHE_TTL=3600
INSIGHT_GENERATION_TIMEOUT=30
MAX_CONCURRENT_SCORING_JOBS=10
```

---

This Psychological Assessment Scoring System provides comprehensive mental wellness and performance analytics for organizations and individuals, replacing the previous basketball analytics with domain-appropriate psychological assessment capabilities.