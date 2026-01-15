# Team Personality Map API Documentation
**REST API Endpoints for Team Personality Insights**

**Version:** 1.0.0
**Base URL:** `http://localhost:8000/api/v1/teams`
**Last Updated:** January 12, 2025

---

## 📋 Overview

The Team Personality Map API provides endpoints for:
1. **Team Composition** - Get aggregated personality data for a team
2. **AI Insights** - Get actionable recommendations for a team
3. **Team Comparison** - Compare personality across multiple teams

These endpoints analyze individual personality assessments (Big Five model) and calculate team-level insights including strengths, gaps, compatibility, and diversity scores.

---

## 🔐 Authentication

All endpoints require JWT authentication. Include the access token in the request header:

```
Authorization: Bearer <your_access_token>
```

**Get Your Token:**
```bash
curl -X POST "http://localhost:8000/api/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your@email.com&password=yourpassword"
```

---

## 📊 Endpoints

### 1. Get Team Personality Composition

Retrieve aggregated personality data for a specific team, including OCEAN dimension averages, strengths, gaps, and compatibility scores.

```
GET /api/v1/teams/{team_id}/personality
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `team_id` | string | Yes | Team UUID (full or partial) |

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `force_refresh` | boolean | No | false | If true, recalculate from scratch instead of using cached data (also triggers AI insights generation) |

**Response (200 OK):**
```json
{
  "team_id": "123e4567-e89b-12d3-a456-426614174000",
  "team_size": 10,
  "composition_type": "Creative & Social",
  "openness": {
    "avg": 4.2,
    "min": 3.0,
    "max": 5.0,
    "std_dev": 0.6,
    "distribution": [0, 10, 20, 40, 30]
  },
  "conscientiousness": {
    "avg": 3.8,
    "min": 2.5,
    "max": 4.8,
    "std_dev": 0.7,
    "distribution": [0, 10, 30, 40, 20]
  },
  "extraversion": {
    "avg": 4.0,
    "min": 2.8,
    "max": 5.0,
    "std_dev": 0.5,
    "distribution": [0, 0, 20, 50, 30]
  },
  "agreeableness": {
    "avg": 3.5,
    "min": 2.0,
    "max": 4.5,
    "std_dev": 0.8,
    "distribution": [0, 20, 30, 30, 20]
  },
  "neuroticism": {
    "avg": 2.3,
    "min": 1.5,
    "max": 3.5,
    "std_dev": 0.6,
    "distribution": [20, 40, 30, 10, 0]
  },
  "strengths": [
    "Creative problem-solving and innovation",
    "Excellent communication and social engagement",
    "Emotional stability and stress resilience"
  ],
  "gaps": [
    "May struggle with organization and follow-through"
  ],
  "internal_compatibility": 0.85,
  "diversity_score": 0.42,
  "updated_at": "2025-01-12T10:30:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "No personality data found for team: 123e4567-e89b-12d3-a456-426614174000. Ensure team members have completed Big Five assessments."
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/teams/123e4567-e89b-12d3-a456-426614174000/personality" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

### 2. Get AI-Generated Insights

Retrieve AI-powered actionable recommendations for a team based on their personality composition. Uses GPT-4 when available, falls back to rule-based insights.

```
GET /api/v1/teams/{team_id}/insights
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `team_id` | string | Yes | Team UUID |

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `force_refresh` | boolean | No | false | If true, regenerate insights instead of using cached version |

**Response (200 OK):**
```json
{
  "team_id": "123e4567-e89b-12d3-a456-426614174000",
  "insights": [
    {
      "heading": "Leverage Creative Problem-Solving",
      "rationale": "Your team scores high in Openness (avg 4.2/5), which means they thrive on innovation and novel approaches to challenges.",
      "action": "In your next team meeting, introduce a 'wild idea' brainstorming session where no idea is too crazy. Your team will excel at generating creative solutions."
    },
    {
      "heading": "Capitalize on Organizational Strength",
      "rationale": "Your team scores high in Conscientiousness (avg 3.8/5), indicating strong self-discipline and attention to detail.",
      "action": "Assign complex, multi-step projects that require careful planning and follow-through. Your team will execute reliably."
    },
    {
      "heading": "Support Stress Management",
      "rationale": "Your team shows high emotional stability (low Neuroticism: 2.3/5), meaning they handle stress well.",
      "action": "Your team can handle high-pressure situations. Consider them for critical projects or crisis response."
    },
    {
      "heading": "Strengthen Project Management",
      "rationale": "Your team scores lower in Conscientiousness (3.8/5), which may lead to challenges with organization and follow-through.",
      "action": "Implement structured project management tools (Asana, Jira) with clear deadlines and check-ins. Break large projects into smaller, manageable tasks."
    },
    {
      "heading": "Continue Team Development",
      "rationale": "Regular team development and check-ins are essential for maintaining high performance.",
      "action": "Schedule monthly 1-on-1s with each team member to discuss their development goals and how the team can better support them."
    }
  ],
  "generated_at": "2025-01-12T10:30:00Z",
  "insight_count": 5
}
```

**Response (404 Not Found):**
```json
{
  "detail": "No personality data found for team: 123e4567-e89b-12d3-a456-426614174000"
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/teams/123e4567-e89b-12d3-a456-426614174000/insights?force_refresh=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

### 3. Compare Teams (Personality)

Compare personality composition across multiple teams with side-by-side analysis and comparative insights.

```
POST /api/v1/teams/compare-personality
```

**Request Body:**
```json
{
  "team_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "223e4567-e89b-12d3-b456-426614174000",
    "323e4567-e89b-12d3-c456-426614174000"
  ]
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `team_ids` | array of strings | Yes | Array of 2-10 team UUIDs |

**Response (200 OK):**
```json
{
  "teams": [
    {
      "team_id": "123e4567-e89b-12d3-a456-426614174000",
      "composition_type": "Creative & Social",
      "team_size": 10,
      "diversity_score": 0.42,
      "internal_compatibility": 0.85,
      "openness": {
        "avg": 4.2,
        "min": 3.0,
        "max": 5.0,
        "std_dev": 0.6,
        "distribution": [0, 10, 20, 40, 30]
      },
      "conscientiousness": { /* ... */ },
      "extraversion": { /* ... */ },
      "agreeableness": { /* ... */ },
      "neuroticism": { /* ... */ }
    }
    /* ... more teams ... */
  ],
  "insights": [
    "Personality diversity varies significantly across teams (range: 0.30 - 0.55)",
    "Teams show strong internal personality compatibility",
    "Teams have distinct personality profiles: Creative & Social, Strategic Thinkers, Balanced Team"
  ]
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "At least 2 team IDs required for comparison"
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Cannot compare more than 10 teams at once"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/teams/compare-personality" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "team_ids": [
      "123e4567-e89b-12d3-a456-426614174000",
      "223e4567-e89b-12d3-b456-426614174000"
    ]
  }'
```

---

## 📊 Data Models

### DimensionStats
Statistics for a single Big Five personality dimension.

```typescript
interface DimensionStats {
  avg: number;           // Average score (0-5 scale)
  min: number;           // Minimum score
  max: number;           // Maximum score
  std_dev: number;       // Standard deviation
  distribution: number[]; // Distribution across quintiles [very low, low, medium, high, very high] as percentages
}
```

### TeamCompositionResponse
Complete team personality composition data.

```typescript
interface TeamCompositionResponse {
  team_id: string;                      // Team UUID
  team_size: number;                     // Number of team members with assessments
  composition_type: string;              // Overall team personality type
  openness: DimensionStats | null;       // Openness dimension statistics
  conscientiousness: DimensionStats | null; // Conscientiousness dimension statistics
  extraversion: DimensionStats | null;    // Extraversion dimension statistics
  agreeableness: DimensionStats | null;   // Agreeableness dimension statistics
  neuroticism: DimensionStats | null;     // Neuroticism dimension statistics
  strengths: string[];                  // Team strengths
  gaps: string[];                        // Potential areas for development
  internal_compatibility: number | null; // How well personalities complement each other (0-1)
  diversity_score: number | null;        // Personality diversity score (0-1, higher = more diverse)
  updated_at: string;                     // ISO 8601 timestamp
  ai_insights?: Insight[];                // Optional AI-generated insights (if force_refresh=true)
}
```

### Insight
AI-generated actionable recommendation.

```typescript
interface Insight {
  heading: string;     // Section heading
  rationale: string;   // Psychological rationale
  action: string;      // Concrete action for manager
}
```

### TeamComparisonResponse
Comparison of multiple teams.

```typescript
interface TeamComparisonResponse {
  teams: TeamCompositionResponse[];  // Array of team data
  insights: string[];                    // Comparative insights
}
```

---

## 🔒 Error Responses

All endpoints follow standard HTTP status codes:

| Code | Description | Example |
|------|-------------|---------|
| 200 | Success | Data returned successfully |
| 400 | Bad Request | Invalid team ID format, too many teams in comparison |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | User doesn't have access to this team |
| 404 | Not Found | Team not found or no personality data available |
| 500 | Internal Server Error | Server error while processing request |

**Error Response Format:**
```json
{
  "detail": "Error message description"
}
```

---

## 🧪 Testing

### Local Testing

1. **Start the backend server:**
```bash
cd /Users/sheriftito/Downloads/psychsync
.venv/bin/uvicorn app.main:app --reload
```

2. **Get authentication token:**
```bash
curl -X POST "http://localhost:8000/api/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass"
```

3. **Test team composition endpoint:**
```bash
curl -X GET "http://localhost:8000/api/v1/teams/{team_id}/personality" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

4. **Test AI insights endpoint:**
```bash
curl -X GET "http://localhost:8000/api/v1/teams/{team_id}/insights" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

5. **Test comparison endpoint:**
```bash
curl -X POST "http://localhost:8000/api/v1/teams/compare-personality" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "team_ids": ["team1-uuid", "team2-uuid"]
  }'
```

---

## 📈 Performance Considerations

### Caching
- Team composition data is cached for 24 hours
- Set `force_refresh=true` to bypass cache and recalculate
- AI insights are cached separately (24-hour TTL)

### Response Time Targets
- Cached requests: <100ms (p95)
- Uncached requests: <500ms (p95)
- Comparison requests: <2s (p95)

### Rate Limiting
- Default: 100 requests per minute per user
- See app/main.py for rate limiting configuration

---

## 🛠️ Troubleshooting

### Issue: "No personality data found for team"
**Cause:** Team members haven't completed Big Five assessments yet

**Solution:**
1. Ensure team members exist: `GET /api/v1/teams/{team_id}`
2. Ensure assessments exist: `GET /api/v1/assessments?team_id={team_id}`
3. Ensure assessments are completed: Check `completed_at` field
4. Ensure assessments have framework_code="BIG_FIVE"

### Issue: "Invalid team UUID format"
**Cause:** team_id is not a valid UUID

**Solution:** Ensure team_id is a valid UUID (36 characters, including dashes)

### Issue: Insights are generic/rule-based
**Cause:** OpenAI API key not configured or API call failed

**Solution:**
1. Check environment variable: `OPENAI_API_KEY`
2. Check OpenAI API status: https://status.openai.com
3. Check logs for error messages

### Issue: Comparison returns no data
**Cause:** None of the teams have personality data

**Solution:** Ensure all teams in comparison have completed Big Five assessments

---

## 📞 Support

**API Questions:** CTO - [cto@psychsync.io]
**Feature Questions:** CPO - [cpo@psychsync.io]
**Integration Support:** [support@psychsync.io]

---

## 📚 Related Documentation

- `Q1_ENGINEERING_ROADMAP.md` - Sprint 1 implementation details
- `PRICING_STRATEGY_TIERS.md` - Pricing tiers and user limits
- `MONTHLY_EXECUTIVE_PRODUCT_REPORTS.md` - Success metrics and KPIs
- `CROSS_TEAM_COLLABORATION_WORKFLOWS.md` - Product↔Engineering collaboration

---

*Last Updated: January 12, 2025*
*API Version: 1.0.0*
*Base URL: http://localhost:8000/api/v1/teams*
