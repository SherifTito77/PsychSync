# Detailed Load Test Scenarios

Comprehensive documentation of all load testing scenarios for PsychSync.

## Table of Contents

1. [Authentication Scenarios](#authentication-scenarios)
2. [Assessment Taking Scenarios](#assessment-taking-scenarios)
3. [Dashboard & Analytics Scenarios](#dashboard--analytics-scenarios)
4. [Team Management Scenarios](#team-management-scenarios)
5. [Assessment Management Scenarios](#assessment-management-scenarios)
6. [AI/NLP Processing Scenarios](#ainlp-processing-scenarios)
7. [Specialized Scenarios](#specialized-scenarios)

---

## Authentication Scenarios

### AUTH-001: Normal Login Flow

**Description**: Standard user login with valid credentials

**Endpoint**: `POST /api/v1/auth/token-fixed`

**Request Rate**:
- Small: 15 requests/second
- Medium: 150 requests/second
- Large: 1,500 requests/second

**Payload**:
```json
{
  "username": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success Criteria**:
- 200 status code
- Response contains `access_token` and `refresh_token`
- Response time < 500ms (p95)

**Failure Points**:
- Invalid credentials (401)
- Rate limit exceeded (429)
- Database timeout (500)

---

### AUTH-002: Token Refresh

**Description**: Refresh expired access token using refresh token

**Endpoint**: `POST /api/v1/auth/refresh`

**Request Rate**:
- Small: 10 requests/second
- Medium: 100 requests/second
- Large: 1,000 requests/second

**Payload**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Criteria**:
- 200 status code
- New access token provided
- Response time < 300ms (p95)

**Failure Points**:
- Invalid refresh token (401)
- Token expired (401)
- Blacklisted token (401)

---

### AUTH-003: Concurrent Device Login

**Description**: Same user logging in from multiple devices simultaneously

**Endpoint**: `POST /api/v1/auth/token-fixed`

**Concurrent Users**: 10-100 users each with 3-5 devices

**Scenario**:
1. User logs in from desktop
2. User logs in from mobile (within 1 second)
3. User logs in from tablet (within 1 second)

**Success Criteria**:
- All logins succeed
- Each device gets unique session
- Previous sessions invalidated if required
- Response time < 500ms (p95)

**Failure Points**:
- Session limit exceeded (429)
- Token collision (409)
- Database lock (500)

---

## Assessment Taking Scenarios

### ASMT-001: Start Assessment

**Description**: User begins a new assessment

**Endpoint**: `POST /api/v1/assessments/{id}/start`

**Request Rate**:
- Small: 20 requests/second
- Medium: 200 requests/second
- Large: 2,000 requests/second

**Payload**:
```json
{
  "framework": "mbti",
  "started_at": "2024-01-10T10:00:00Z"
}
```

**Success Criteria**:
- 201 status code
- Assessment session created
- Session ID returned
- Response time < 400ms (p95)

**Failure Points**:
- Assessment not found (404)
- User already has active assessment (409)
- Database connection pool exhausted (500)

---

### ASMT-002: Submit Responses (Auto-Save)

**Description**: User submits assessment responses in batches (auto-save)

**Endpoint**: `POST /api/v1/assessments/{id}/responses`

**Request Rate**:
- Small: 100 requests/second
- Medium: 1,000 requests/second
- Large: 10,000 requests/second

**Payload**:
```json
{
  "responses": [
    {
      "question_id": "q1",
      "answer": 4,
      "timestamp": "2024-01-10T10:01:00Z"
    },
    {
      "question_id": "q2",
      "answer": 3,
      "timestamp": "2024-01-10T10:01:01Z"
    }
  ]
}
```

**Success Criteria**:
- 200/201 status code
- Responses saved successfully
- Response time < 300ms (p95)
- No data loss

**Failure Points**:
- Invalid assessment ID (404)
- Validation error (400)
- Database write timeout (500)
- Concurrent write conflict (409)

---

### ASMT-003: Complete Assessment

**Description**: User completes assessment and triggers scoring

**Endpoint**: `POST /api/v1/assessments/{id}/complete`

**Request Rate**:
- Small: 15 requests/second
- Medium: 150 requests/second
- Large: 1,500 requests/second

**Payload**:
```json
{
  "completed_at": "2024-01-10T10:30:00Z",
  "framework": "mbti"
}
```

**Success Criteria**:
- 200/201 status code
- Scoring completed
- Results available
- Response time < 2000ms (p95) - scoring is CPU intensive

**Failure Points**:
- Incomplete responses (400)
- Scoring engine error (500)
- AI processor timeout (504)
- Results calculation failure (500)

---

### ASMT-004: View Results

**Description**: User views completed assessment results

**Endpoint**: `GET /api/v1/assessments/{id}/results`

**Request Rate**:
- Small: 30 requests/second
- Medium: 300 requests/second
- Large: 3,000 requests/second

**Success Criteria**:
- 200 status code
- Results data returned
- Response time < 500ms (p95)
- Cache hit rate > 80%

**Failure Points**:
- Results not ready (404)
- Assessment not completed (400)
- Cache miss causing database load

---

## Dashboard & Analytics Scenarios

### DASH-001: Load Dashboard Overview

**Description**: User loads main dashboard with analytics

**Endpoint**: `GET /api/v1/analytics/dashboard`

**Request Rate**:
- Small: 20 requests/second
- Medium: 200 requests/second
- Large: 2,000 requests/second

**Query Parameters**:
```
?organization_id=org_123&date_range=30d
```

**Success Criteria**:
- 200 status code
- Dashboard data returned
- Response time < 1000ms (p95)
- Cache hit rate > 80%

**Failure Points**:
- Insufficient permissions (403)
- Data aggregation timeout (504)
- Cache stampede (multiple simultaneous misses)

---

### DASH-002: Team Analytics

**Description**: Load analytics for specific team

**Endpoint**: `GET /api/v1/analytics/team/{team_id}`

**Request Rate**:
- Small: 15 requests/second
- Medium: 150 requests/second
- Large: 1,500 requests/second

**Success Criteria**:
- 200 status code
- Team analytics returned
- Response time < 800ms (p95)
- Complex aggregations successful

**Failure Points**:
- Team not found (404)
- Not team member (403)
- Large dataset causing timeout (504)
- N+1 query problems

---

### DASH-003: Export Report

**Description**: Export analytics report as PDF/CSV

**Endpoint**: `GET /api/v1/analytics/export`

**Request Rate**:
- Small: 5 requests/second
- Medium: 50 requests/second
- Large: 500 requests/second

**Query Parameters**:
```
?format=pdf&team_id=team_123&date_range=90d
```

**Success Criteria**:
- 200/202 status code
- Report generated successfully
- Response time < 5000ms (p95) - PDF generation is slow
- Downloadable file returned

**Failure Points**:
- Unsupported format (400)
- Generation timeout (504)
- File size too large (500)
- Storage failure (503)

---

### DASH-004: Load Historical Trends

**Description**: Load historical trend data

**Endpoint**: `GET /api/v1/analytics/trends`

**Request Rate**:
- Small: 10 requests/second
- Medium: 100 requests/second
- Large: 1,000 requests/second

**Query Parameters**:
```
?days=365&metrics=engagement,satisfaction,completion_rate
```

**Success Criteria**:
- 200 status code
- Trend data returned
- Response time < 1500ms (p95)
- Efficient time-series queries

**Failure Points**:
- Date range too large (400)
- Time-series query timeout (504)
- Missing metrics (400)
- Data aggregation failure (500)

---

## Team Management Scenarios

### TEAM-001: View Team Details

**Description**: Load team information

**Endpoint**: `GET /api/v1/teams/{team_id}`

**Request Rate**:
- Small: 20 requests/second
- Medium: 200 requests/second
- Large: 2,000 requests/second

**Success Criteria**:
- 200 status code
- Team details returned
- Response time < 400ms (p95)

---

### TEAM-002: Add Team Member

**Description**: Add new member to team

**Endpoint**: `POST /api/v1/teams/{team_id}/members`

**Request Rate**:
- Small: 5 requests/second
- Medium: 50 requests/second
- Large: 500 requests/second

**Payload**:
```json
{
  "user_id": "user_12345",
  "role": "member",
  "permissions": ["view_analytics", "take_assessments"]
}
```

**Success Criteria**:
- 201 status code
- Member added successfully
- Response time < 500ms (p95)
- Notification sent (if applicable)

**Failure Points**:
- User not found (404)
- Already a member (409)
- Team at capacity (429)
- Permission denied (403)

---

### TEAM-003: Remove Team Member

**Description**: Remove member from team

**Endpoint**: `DELETE /api/v1/teams/{team_id}/members/{user_id}`

**Request Rate**:
- Small: 3 requests/second
- Medium: 30 requests/second
- Large: 300 requests/second

**Success Criteria**:
- 200/204 status code
- Member removed successfully
- Response time < 400ms (p95)
- Associated data handled correctly

**Failure Points**:
- User not in team (404)
- Last admin cannot be removed (403)
- Database constraint violation (500)

---

### TEAM-004: Update Team Permissions

**Description**: Update permissions for team role

**Endpoint**: `PUT /api/v1/teams/{team_id}/permissions`

**Request Rate**:
- Small: 2 requests/second
- Medium: 20 requests/second
- Large: 200 requests/second

**Payload**:
```json
{
  "role": "member",
  "permissions": {
    "view_analytics": true,
    "manage_assessments": false
  }
}
```

**Success Criteria**:
- 200 status code
- Permissions updated
- Response time < 500ms (p95)
- Cache invalidated

**Failure Points**:
- Invalid permission (400)
- Insufficient privileges (403)
- Cache update failure (500)

---

## Assessment Management Scenarios

### MGMT-001: Create Assessment

**Description**: Create new custom assessment

**Endpoint**: `POST /api/v1/assessments`

**Request Rate**:
- Small: 2 requests/second
- Medium: 20 requests/second
- Large: 200 requests/second

**Payload**:
```json
{
  "title": "Custom Team Assessment",
  "description": "Assessment for team building",
  "framework": "custom",
  "category": "personality",
  "questions": [
    {
      "id": "q1",
      "text": "I enjoy working in teams",
      "type": "rating",
      "options": [1, 2, 3, 4, 5]
    }
  ]
}
```

**Success Criteria**:
- 201 status code
- Assessment created
- Response time < 1000ms (p95)

**Failure Points**:
- Validation error (400)
- Duplicate title (409)
- Question limit exceeded (400)
- Database error (500)

---

### MGMT-002: Duplicate Assessment

**Description**: Create copy of existing assessment

**Endpoint**: `POST /api/v1/assessments/{id}/duplicate`

**Request Rate**:
- Small: 1 request/second
- Medium: 10 requests/second
- Large: 100 requests/second

**Payload**:
```json
{
  "name": "Copy of MBTI Assessment",
  "organization_id": "org_123"
}
```

**Success Criteria**:
- 201 status code
- Assessment duplicated with all questions
- Response time < 1500ms (p95)

**Failure Points**:
- Original not found (404)
- Permission denied (403)
- Question copy failure (500)

---

## AI/NLP Processing Scenarios

### AI-001: Text Analysis

**Description**: Submit text for AI/NLP analysis

**Endpoint**: `POST /api/v1/nlp/analyze`

**Request Rate**:
- Small: 5 requests/second
- Medium: 50 requests/second
- Large: 500 requests/second

**Payload**:
```json
{
  "text": "I feel confident in my leadership abilities and enjoy helping teams succeed.",
  "analysis_type": "personality",
  "include_insights": true
}
```

**Success Criteria**:
- 200/202 status code
- Analysis completed
- Response time < 3000ms (p95)
- Insights generated

**Failure Points**:
- Invalid text (400)
- Unsupported analysis type (400)
- AI model timeout (504)
- Rate limit exceeded (429)

---

### AI-002: Batch Processing

**Description**: Submit multiple texts for batch analysis

**Endpoint**: `POST /api/v1/nlp/batch`

**Request Rate**:
- Small: 1 request/second
- Medium: 10 requests/second
- Large: 100 requests/second

**Payload**:
```json
{
  "texts": [
    {"id": "text_1", "content": "First text..."},
    {"id": "text_2", "content": "Second text..."},
    {"id": "text_3", "content": "Third text..."}
  ],
  "analysis_type": "sentiment"
}
```

**Success Criteria**:
- 200/202 status code
- All texts processed
- Response time < 10000ms (p95) - 10x single request
- Results array returned

**Failure Points**:
- Batch size exceeded (400)
- Partial processing (207)
- Queue full (503)

---

## Specialized Scenarios

### SPEC-001: Spike Test

**Description**: Sudden increase in load from normal to peak

**Pattern**:
- 0-2 min: 100 users (baseline)
- 2-3 min: Spike to 5000 users (+4900 in 60 seconds)
- 3-10 min: Maintain 5000 users
- 10-12 min: Ramp down to 100 users

**Success Criteria**:
- System handles spike without crashing
- Auto-scaling triggers correctly (if applicable)
- Response times recover after spike
- No data corruption

**Failure Points**:
- Connection pool exhaustion
- Queue overflow
- Database connection limit
- Memory exhaustion

---

### SPEC-002: Soak Test

**Description**: Sustained high load over extended period

**Pattern**:
- Duration: 4-24 hours
- Load: 70-80% of max capacity
- Users: Constant 1000+ users

**Success Criteria**:
- No memory leaks
- Stable response times over duration
- No connection leaks
- Resources stabilize

**Failure Points**:
- Memory leak (gradual increase)
- Connection pool degradation
- Cache saturation
- Disk space exhaustion

---

### SPEC-003: Cache Failure Test

**Description**: System behavior when cache fails

**Scenario**:
1. Run load test at 1000 users
2. After 5 minutes, disable Redis
3. Observe system behavior
4. Re-enable Redis after 5 minutes
5. Verify recovery

**Success Criteria**:
- Requests continue (maybe slower)
- No crashes
- Graceful degradation
- Automatic recovery when cache restored

**Failure Points**:
- Complete system failure
- Database overload
- Timeout cascade

---

### SPEC-004: Database Connection Failover

**Description**: Primary database failure during load test

**Scenario**:
1. Run load test at 500 users
2. After 5 minutes, stop primary database
3. Failover to replica/standby
4. Observe behavior
5. Restore primary

**Success Criteria**:
- Failover completes < 30 seconds
- Minimal request failures during failover
- Automatic reconnection
- No data inconsistency

---

## Test Data Requirements

### Small Load (100 users)
- Users: 1,000
- Teams: 50
- Assessments: 10
- Historical Responses: 50,000
- Database Size: ~500 MB

### Medium Load (1,000 users)
- Users: 10,000
- Teams: 500
- Assessments: 100
- Historical Responses: 500,000
- Database Size: ~5 GB

### Large Load (10,000 users)
- Users: 100,000
- Teams: 5,000
- Assessments: 1,000
- Historical Responses: 5,000,000
- Database Size: ~50 GB

---

## Performance Thresholds Summary

| Scenario Category | Small Load (p95) | Medium Load (p95) | Large Load (p95) |
|-------------------|------------------|-------------------|------------------|
| Authentication    | < 500ms          | < 800ms           | < 1000ms         |
| Assessment Taking | < 800ms          | < 1200ms          | < 2000ms         |
| Dashboard         | < 1000ms         | < 1500ms          | < 2500ms         |
| Team Management   | < 500ms          | < 800ms           | < 1200ms         |
| Assessment Mgmt   | < 1000ms         | < 1500ms          | < 2000ms         |
| AI/NLP            | < 3000ms         | < 5000ms          | < 8000ms         |

---

## Running Specific Scenarios

### Using the test script

```bash
# Authentication scenarios
./load_testing/run_tests.sh -u 100 -t 5m -c auth

# Assessment scenarios
./load_testing/run_tests.sh -u 500 -t 10m -c assessment

# Mixed workload (all scenarios)
./load_testing/run_tests.sh -u 1000 -t 15m -c mixed
```

### Using Locust directly

```bash
# Run specific scenario
locust -f load_testing/locust/auth_test.py \
  --host http://localhost:8000 \
  --users 1000 \
  --spawn-rate 50 \
  --run-time 10m
```

### Using k6

```bash
# Run specific scenario
k6 run --vus 1000 --duration 10m \
  load_testing/k6/mixed_workload.js
```

For more details, see the main README.md.
