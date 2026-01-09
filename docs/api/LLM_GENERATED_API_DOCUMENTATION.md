# PsychSync API Documentation

**Auto-generated API Documentation**
**Version:** 1.0.0
**Generated:** January 4, 2026
**Base URL:** `http://localhost:8000/api/v1`

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Assessment Endpoints](#assessment-endpoints)
4. [User Management](#user-management)
5. [Team Management](#team-management)
6. [Analytics & Reporting](#analytics--reporting)
7. [Health & Monitoring](#health--monitoring)
8. [Response Management](#response-management)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)
11. [Best Practices](#best-practices)

---

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Redis for caching
- Valid API credentials

### Making Your First Request

```bash
# Health check (no authentication required)
curl http://localhost:8000/api/v1/health/public

# Expected response
{
  "status": "healthy",
  "timestamp": "2026-01-04T12:00:00",
  "service": "psychsync-api"
}
```

### Authentication Flow

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register-fixed \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=user@example.com&password=SecurePass123!&full_name=John Doe"

# 2. Login to get access token
curl -X POST http://localhost:8000/api/v1/auth/token-fixed \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePass123!"

# 3. Use the access token (stored in httpOnly cookie)
curl http://localhost:8000/api/v1/auth/me-fixed \
  -H "Cookie: access_token=<your_token>"
```

---

## Authentication

### Overview

PsychSync uses JWT (JSON Web Token) based authentication with secure httpOnly cookies to prevent XSS attacks.

**Security Features:**
- JWT tokens stored in httpOnly, secure, SameSite cookies
- CSRF protection via token validation
- Rate limiting on authentication endpoints
- Session management with refresh tokens
- Automatic token invalidation on logout

### Registration

#### POST /auth/register-fixed

Register a new user account.

**Rate Limit:** 3 requests per hour per IP

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register-fixed \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=user@example.com&password=SecurePass123!&full_name=John Doe"
```

**Form Data:**
- `email` (string, required): User's email address
- `password` (string, required): Password (min 8 chars, must contain uppercase, lowercase, number, special character)
- `full_name` (string, required): User's full name

**Success Response (201):**
```json
{
  "message": "Registration successful",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": false
  }
}
```

**Error Responses:**
- `400`: Invalid email format or password doesn't meet requirements
- `409`: Email already registered
- `429`: Too many registration attempts
- `500`: Registration service temporarily unavailable

---

### Login

#### POST /auth/token-fixed

Authenticate and receive session tokens.

**Rate Limit:** 5 requests per minute per IP

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/token-fixed \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePass123!" \
  -c cookies.txt
```

**Form Data (OAuth2 compatible):**
- `username` (string, required): Email address
- `password` (string, required): User password

**Success Response (200):**
Sets httpOnly cookies:
- `access_token`: JWT access token (expires in 30 minutes)
- `refresh_token`: JWT refresh token (expires in 7 days)
- `csrf_token`: CSRF protection token

```json
{
  "message": "Login successful",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

**Error Responses:**
- `400`: Username and password are required
- `401`: Invalid credentials
- `429`: Too many login attempts
- `500`: Authentication service temporarily unavailable

---

### Get Current User

#### GET /auth/me-fixed

Get information about the currently authenticated user.

**Authentication:** Required

**Request:**
```bash
curl http://localhost:8000/api/v1/auth/me-fixed \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": true,
  "role": "user",
  "created_at": "2026-01-01T00:00:00",
  "last_login": "2026-01-04T12:00:00",
  "updated_at": "2026-01-04T12:00:00"
}
```

**Error Responses:**
- `401`: Invalid authentication token
- `404`: User not found
- `500`: User service temporarily unavailable

---

### Logout

#### POST /auth/logout

Invalidate current session and clear cookies.

**Authentication:** Required

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "message": "Logout successful"
}
```

Clears all authentication cookies.

---

### Refresh Token

#### POST /auth/refresh-token-fixed

Refresh access token using refresh token.

**Rate Limit:** 10 requests per minute per IP

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh-token-fixed \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "refresh_token=<your_refresh_token>"
```

**Form Data:**
- `refresh_token` (string, required): Valid refresh token

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "message": "Token refreshed successfully"
}
```

**Error Responses:**
- `401`: Invalid refresh token
- `429`: Too many refresh attempts
- `500`: Token refresh service temporarily unavailable

---

## Assessment Endpoints

### Overview

Assessments are psychological evaluation instruments that can be created, managed, and distributed to users.

**Supported Assessment Types:**
- MBTI (Myers-Briggs Type Indicator)
- Big Five (OCEAN)
- Enneagram
- DISC
- Predictive Index
- Social Styles
- CliftonStrengths (StrengthsFinder)

### List Assessments

#### GET /assessments/

Get a paginated list of assessments with filtering and sorting.

**Authentication:** Required

**Query Parameters:**
- `skip` (integer, default=0): Number of results to skip
- `limit` (integer, default=100, max=1000): Results per page
- `search` (string): Search in title or description
- `category` (string): Filter by assessment category
- `status` (string): Filter by status (draft, active, archived)
- `created_by` (integer): Filter by creator ID
- `created_after` (date): Filter assessments created after date
- `created_before` (date): Filter assessments created before date
- `sort_by` (string): Sort field (created_at, updated_at, title)
- `sort_order` (string): Sort direction (asc, desc)

**Request:**
```bash
curl "http://localhost:8000/api/v1/assessments/?skip=0&limit=20&status=active" \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Assessments retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "Big Five Personality Assessment",
        "description": "Measure the Big Five personality traits",
        "category": "personality",
        "status": "active",
        "created_by_id": "123e4567-e89b-12d3-a456-426614174000",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-04T12:00:00"
      }
    ],
    "total": 45,
    "skip": 0,
    "limit": 20
  },
  "metadata": {
    "response_time_ms": 45.2,
    "cached": true
  }
}
```

---

### Create Assessment

#### POST /assessments/

Create a new assessment template.

**Authentication:** Required

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/assessments/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "title": "Custom Team Assessment",
    "description": "Evaluate team dynamics",
    "category": "team",
    "status": "draft"
  }'
```

**Request Body:**
```json
{
  "title": "string (required, max 200 chars)",
  "description": "string (optional)",
  "category": "string (required)",
  "status": "string (optional, default: draft)",
  "is_public": "boolean (optional, default: false)"
}
```

**Success Response (201):**
```json
{
  "success": true,
  "message": "Assessment created successfully",
  "data": {
    "id": 46,
    "title": "Custom Team Assessment",
    "description": "Evaluate team dynamics",
    "category": "team",
    "status": "draft",
    "created_by_id": "123e4567-e89b-12d3-a456-426614174000",
    "created_at": "2026-01-04T12:00:00"
  }
}
```

**Error Responses:**
- `400`: Validation error
- `403`: Insufficient permissions
- `500`: Creation failed

---

### Get Assessment Details

#### GET /assessments/{assessment_id}

Get detailed assessment information including sections and questions.

**Authentication:** Required

**Parameters:**
- `assessment_id` (integer, required): Assessment ID

**Request:**
```bash
curl http://localhost:8000/api/v1/assessments/1 \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Assessment retrieved successfully",
  "data": {
    "id": 1,
    "title": "Big Five Personality Assessment",
    "description": "Measure the Big Five personality traits",
    "category": "personality",
    "status": "active",
    "sections": [
      {
        "id": 1,
        "title": "Personality Traits",
        "order": 1,
        "questions": [
          {
            "id": 1,
            "question_text": "I am the life of the party",
            "question_type": "likert",
            "options": [
              {"value": 1, "text": "Strongly Disagree"},
              {"value": 2, "text": "Disagree"},
              {"value": 3, "text": "Neutral"},
              {"value": 4, "text": "Agree"},
              {"value": 5, "text": "Strongly Agree"}
            ]
          }
        ]
      }
    ],
    "question_count": 10,
    "created_at": "2026-01-01T00:00:00"
  }
}
```

**Error Responses:**
- `403`: No permission to access assessment
- `404`: Assessment not found

---

### Update Assessment

#### PUT /assessments/{assessment_id}

Update assessment details.

**Authentication:** Required (creator or team admin only)

**Request:**
```bash
curl -X PUT http://localhost:8000/api/v1/assessments/1 \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "title": "Updated Assessment Title",
    "description": "Updated description"
  }'
```

**Success Response (200):**
Returns updated assessment object.

---

### Delete Assessment

#### DELETE /assessments/{assessment_id}

Delete an assessment.

**Authentication:** Required (creator or team admin only)

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/v1/assessments/1 \
  -b cookies.txt
```

**Success Response (204):** No content

---

### Publish Assessment

#### POST /assessments/{assessment_id}/publish

Publish an assessment (change status to active).

**Authentication:** Required (creator or team admin only)

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/assessments/1/publish \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "id": 1,
  "title": "Big Five Assessment",
  "status": "active"
}
```

---

### Archive Assessment

#### POST /assessments/{assessment_id}/archive

Archive an assessment.

**Authentication:** Required (creator or team admin only)

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/assessments/1/archive \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "id": 1,
  "title": "Big Five Assessment",
  "status": "archived"
}
```

---

### Get Assessment Questions

#### GET /assessments/assessment-questions/{type}

Get predefined assessment questions by type.

**Authentication:** Not required

**Available Types:**
- `mbti` - Myers-Briggs Type Indicator
- `big-five` - Big Five (OCEAN)
- `enneagram` - Enneagram Personality
- `disc` - DISC Assessment
- `predictive-index` - Predictive Index Behavioral
- `social-styles` - Social Styles
- `strengthsfinder` - CliftonStrengths

**Request:**
```bash
curl http://localhost:8000/api/v1/assessments/assessment-questions/mbti
```

**Success Response (200):**
```json
{
  "success": true,
  "status": "ok",
  "assessment": {
    "id": "mbti-standard",
    "title": "Myers-Briggs Type Indicator (MBTI) Assessment",
    "description": "Discover your MBTI personality type",
    "instructions": "Choose the option that feels most natural to you",
    "estimated_time": "15-20 minutes",
    "questions": [
      {
        "id": 1,
        "question_text": "At parties, you usually:",
        "dimension": "E-I",
        "options": [
          {"text": "Talk to many people, even strangers", "value": "E"},
          {"text": "Talk to a few people you know well", "value": "I"}
        ]
      }
    ]
  }
}
```

---

## User Management

### Get Current User Profile

#### GET /users/me

Get the authenticated user's profile.

**Authentication:** Required

**Rate Limit:** 100 requests per minute

**Request:**
```bash
curl http://localhost:8000/api/v1/users/me \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "User profile retrieved successfully",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": true,
    "role": "user",
    "organization_id": "org-123",
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-04T12:00:00"
  }
}
```

---

### Update User Profile

#### PUT /users/me

Update the authenticated user's profile.

**Authentication:** Required

**Request:**
```bash
curl -X PUT http://localhost:8000/api/v1/users/me \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "full_name": "John Updated Doe",
    "phone": "+1234567890"
  }'
```

**Request Body:**
```json
{
  "full_name": "string (optional)",
  "phone": "string (optional)",
  "bio": "string (optional)",
  "avatar_url": "string (optional)"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Updated Doe",
    "phone": "+1234567890"
  }
}
```

---

### Change Password

#### POST /users/change-password

Change user's password.

**Authentication:** Required

**Rate Limit:** 5 attempts per 15 minutes

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/users/change-password \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "current_password": "OldPass123!",
    "new_password": "NewSecurePass456!"
  }'
```

**Request Body:**
```json
{
  "current_password": "string (required)",
  "new_password": "string (required, min 8 chars, uppercase, lowercase, number, special)"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Password updated successfully. All sessions have been invalidated for security.",
  "data": {
    "sessions_invalidated": true
  }
}
```

**Error Responses:**
- `400`: Invalid password format
- `401`: Incorrect current password
- `422`: Password doesn't meet strength requirements
- `429`: Too many attempts

---

### List Users (Admin)

#### GET /users/

Get paginated list of users (admin only).

**Authentication:** Required (admin only)

**Rate Limit:** 30 requests per minute

**Query Parameters:**
- `skip` (integer, default=0)
- `limit` (integer, default=100, max=1000)
- `search` (string): Search by name or email
- `is_active` (boolean)
- `organization_id` (integer)
- `role` (string): admin, user, team_lead

**Request:**
```bash
curl "http://localhost:8000/api/v1/users/?skip=0&limit=20&is_active=true" \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Users retrieved successfully",
  "data": {
    "items": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "user@example.com",
        "full_name": "John Doe",
        "is_active": true,
        "role": "user"
      }
    ],
    "total": 150,
    "skip": 0,
    "limit": 20
  },
  "security_metadata": {
    "accessed_at": 1704364800,
    "filters_applied": ["is_active"],
    "rate_limit_remaining": 25
  }
}
```

**Error Responses:**
- `403`: Not authorized (non-admin users)
- `400`: Validation errors

---

### Register User

#### POST /users/register

Register a new user account.

**Rate Limit:** 5 registrations per 5 minutes per IP

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "full_name": "Jane Doe"
  }'
```

**Request Body:**
```json
{
  "email": "string (required, valid email)",
  "password": "string (required, strong password)",
  "full_name": "string (required, max 100 chars)",
  "organization_id": "string (optional)"
}
```

**Success Response (201):**
```json
{
  "success": true,
  "message": "User registered successfully. Please check your email for verification.",
  "data": {
    "id": "987fcdeb-51a2-43f1-a456-426614174000",
    "email": "newuser@example.com",
    "full_name": "Jane Doe",
    "is_active": true,
    "is_verified": false,
    "verification_required": true
  }
}
```

**Error Responses:**
- `400`: Validation errors
- `409`: Email already registered
- `429`: Too many registration attempts

---

### Get User by ID

#### GET /users/{user_id}

Get specific user details.

**Authentication:** Required

**Request:**
```bash
curl http://localhost:8000/api/v1/users/123 \
  -b cookies.txt
```

**Success Response (200):**
Returns user object.

**Error Responses:**
- `403`: Not authorized (can only view own profile unless admin)
- `404`: User not found

---

## Team Management

### List Teams

#### GET /teams/

Get list of teams with optional filtering.

**Authentication:** Required

**Query Parameters:**
- `my_teams` (boolean, default=false): Filter to teams user is member of
- `skip` (integer, default=0)
- `limit` (integer, default=100, max=1000)

**Request:**
```bash
curl "http://localhost:8000/api/v1/teams/?my_teams=true" \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "teams": [
    {
      "id": "team-123",
      "name": "Engineering Team",
      "description": "Software development team",
      "organization_id": "org-456",
      "created_at": "2026-01-01T00:00:00",
      "updated_at": "2026-01-04T12:00:00",
      "created_by_id": "user-789",
      "members_count": 12
    }
  ],
  "total": 1,
  "success": true,
  "message": "Teams retrieved successfully"
}
```

---

### Create Team

#### POST /teams/

Create a new team.

**Authentication:** Required

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/teams/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Product Team",
    "description": "Product development team"
  }'
```

**Request Body:**
```json
{
  "name": "string (required, max 100 chars)",
  "description": "string (optional)"
}
```

**Success Response (201):**
```json
{
  "id": "team-456",
  "name": "Product Team",
  "description": "Product development team",
  "organization_id": "org-123",
  "created_by_id": "user-789",
  "created_at": "2026-01-04T12:00:00"
}
```

---

### Get Team Details

#### GET /teams/{team_id}

Get detailed team information including members.

**Authentication:** Required

**Request:**
```bash
curl http://localhost:8000/api/v1/teams/team-123 \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "id": "team-123",
  "name": "Engineering Team",
  "description": "Software development team",
  "organization_id": "org-456",
  "created_at": "2026-01-01T00:00:00",
  "members": [
    {
      "id": "user-789",
      "full_name": "John Doe",
      "email": "john@example.com",
      "role": "admin"
    }
  ]
}
```

**Error Responses:**
- `404`: Team not found
- `400`: Invalid team ID

---

## Analytics & Reporting

### Dashboard Overview

#### GET /analytics/dashboard/overview

Get comprehensive dashboard analytics.

**Authentication:** Required

**Query Parameters:**
- `time_period` (string, default=LAST_30_DAYS): Time period for data
  - LAST_7_DAYS
  - LAST_30_DAYS
  - LAST_90_DAYS
  - LAST_12_MONTHS
- `organization_id` (string, optional): Filter by organization (admin only)
- `team_id` (string, optional): Filter by team

**Request:**
```bash
curl "http://localhost:8000/api/v1/analytics/dashboard/overview?time_period=LAST_30_DAYS" \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "period": "LAST_30_DAYS",
  "generated_at": "2026-01-04T12:00:00",
  "user_metrics": {
    "total_users": 150,
    "active_users": 89,
    "new_users": 15,
    "retention_rate": 85.5
  },
  "assessment_metrics": {
    "total_assessments": 45,
    "completed_assessments": 312,
    "completion_rate": 78.2,
    "average_score": 82.5
  },
  "team_metrics": {
    "total_teams": 12,
    "active_teams": 10,
    "average_team_size": 12.5
  },
  "system_metrics": {
    "uptime_percentage": 99.9,
    "response_time_avg": 145.2,
    "error_rate": 0.02
  },
  "business_metrics": {
    "revenue_mrr": 15000,
    "conversion_rate": 12.5,
    "churn_rate": 2.1
  }
}
```

---

### Time Series Data

#### POST /analytics/dashboard/timeseries

Get time series data for specific metrics.

**Authentication:** Required

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dashboard/timeseries" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "metric": "active_users",
    "time_period": "LAST_30_DAYS",
    "granularity": "day"
  }'
```

**Request Body:**
```json
{
  "metric": "string (required)",
  "time_period": "string (default: LAST_30_DAYS)",
  "granularity": "string (default: day, options: hour, day, week, month)"
}
```

**Valid Metrics:**
- `active_users`
- `completed_assessments`
- `api_requests`
- `revenue_mrr`
- `user_retention_rate`
- `assessment_completion_rate`
- `team_collaboration_score`
- `system_uptime`
- `response_time_avg`
- `error_rate`

**Success Response (200):**
```json
{
  "metric": "active_users",
  "period": "LAST_30_DAYS",
  "granularity": "day",
  "data_points": [
    {
      "date": "2026-01-01",
      "value": 85
    },
    {
      "date": "2026-01-02",
      "value": 92
    }
  ],
  "summary": {
    "average": 89.5,
    "min": 75,
    "max": 105,
    "trend": "upward"
  }
}
```

---

### Analytics Insights

#### GET /analytics/dashboard/insights

Get AI-powered insights and recommendations.

**Authentication:** Required

**Query Parameters:**
- `time_period` (string, default=LAST_30_DAYS)
- `organization_id` (string, optional, admin only)

**Request:**
```bash
curl "http://localhost:8000/api/v1/analytics/dashboard/insights?time_period=LAST_30_DAYS" \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "user_insights": [
    {
      "type": "retention_warning",
      "message": "User retention dropped 5% in the last period",
      "severity": "medium",
      "recommendation": "Review onboarding process"
    }
  ],
  "assessment_insights": [
    {
      "type": "popular_assessment",
      "message": "MBTI assessment has 40% higher completion rate",
      "severity": "info"
    }
  ],
  "recommendations": [
    {
      "action": "Increase assessment variety",
      "priority": "high",
      "expected_impact": "15% increase in engagement"
    }
  ],
  "anomalies": [
    {
      "metric": "api_requests",
      "deviation": "+200%",
      "date": "2026-01-03",
      "possible_cause": "Marketing campaign"
    }
  ],
  "predictions": {
    "next_month_users": 165,
    "confidence": 0.85
  }
}
```

---

### Available Metrics

#### GET /analytics/metrics/available

Get list of all available metrics for analytics.

**Authentication:** Required

**Request:**
```bash
curl http://localhost:8000/api/v1/analytics/metrics/available \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "categories": {
    "user_metrics": {
      "total_users": "Total number of registered users",
      "active_users": "Users with activity in the period",
      "new_users": "New user registrations in the period",
      "user_retention_rate": "Percentage of users retained from previous period"
    },
    "assessment_metrics": {
      "total_assessments": "Total number of assessments created",
      "completed_assessments": "Number of completed assessments",
      "assessment_completion_rate": "Percentage of assessments completed"
    },
    "team_metrics": {
      "total_teams": "Total number of teams",
      "active_teams": "Teams with recent activity",
      "average_team_size": "Average number of members per team"
    },
    "system_metrics": {
      "api_requests": "Total API requests in the period",
      "response_time_avg": "Average API response time in milliseconds",
      "error_rate": "Percentage of requests resulting in errors",
      "uptime_percentage": "System uptime percentage"
    },
    "business_metrics": {
      "revenue_mrr": "Monthly recurring revenue",
      "conversion_rate": "User conversion rate percentage",
      "churn_rate": "Customer churn rate percentage",
      "customer_satisfaction": "Customer satisfaction score (1-10)"
    }
  },
  "time_periods": [
    "LAST_7_DAYS",
    "LAST_30_DAYS",
    "LAST_90_DAYS",
    "LAST_12_MONTHS"
  ],
  "granularities": ["hour", "day", "week", "month"]
}
```

---

## Health & Monitoring

### Public Health Check

#### GET /health/public

Basic health check for load balancers (no authentication).

**Request:**
```bash
curl http://localhost:8000/api/v1/health/public
```

**Success Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-04T12:00:00",
  "service": "psychsync-api"
}
```

---

### Basic Health Check

#### GET /health

Detailed health check with system metrics.

**Authentication:** Required

**Request:**
```bash
curl http://localhost:8000/api/v1/health \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Health check completed",
  "data": {
    "status": "healthy",
    "timestamp": "2026-01-04T12:00:00",
    "uptime": 86400,
    "version": "1.0.0",
    "environment": "production",
    "response_time_ms": 45.2,
    "system": {
      "cpu_percent": 35.5,
      "memory": {
        "total_gb": 16.0,
        "available_gb": 8.5,
        "percent_used": 46.9
      },
      "disk": {
        "total_gb": 256.0,
        "free_gb": 128.0,
        "percent_used": 50.0
      }
    }
  }
}
```

---

### Detailed Health Check

#### GET /health/detailed

Comprehensive health check including database and cache.

**Authentication:** Required

**Request:**
```bash
curl http://localhost:8000/api/v1/health/detailed \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "System status: healthy",
  "data": {
    "status": "healthy",
    "timestamp": "2026-01-04T12:00:00",
    "uptime": 86400,
    "version": "1.0.0",
    "response_time_ms": 125.5,
    "components": {
      "database": {
        "status": "healthy",
        "response_time_ms": 5.2,
        "connection": "established"
      },
      "cache": {
        "status": "healthy",
        "response_time_ms": 1.5,
        "connection": "established"
      }
    },
    "system": {
      "cpu_percent": 35.5,
      "memory": {
        "total_gb": 16.0,
        "available_gb": 8.5,
        "percent_used": 46.9
      },
      "load_average": [1.5, 1.3, 1.2],
      "issues": []
    },
    "application": {
      "memory_mb": 512.5,
      "cpu_percent": 2.5,
      "threads": 8,
      "open_files": 256,
      "connections": 45
    }
  }
}
```

**Degraded Response (503):**
```json
{
  "success": false,
  "message": "System status: degraded",
  "data": {
    "status": "degraded",
    "components": {
      "database": {
        "status": "healthy",
        "response_time_ms": 5.2
      },
      "cache": {
        "status": "unhealthy",
        "error": "Connection timeout"
      }
    },
    "system": {
      "issues": ["Cache service unavailable"]
    }
  }
}
```

---

### Application Metrics

#### GET /metrics

Get detailed application metrics.

**Authentication:** Required

**Request:**
```bash
curl http://localhost:8000/api/v1/metrics \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Metrics retrieved successfully",
  "data": {
    "timestamp": "2026-01-04T12:00:00",
    "uptime": 86400,
    "database": {
      "connection_pool": {
        "size": 20,
        "checked_in": 15,
        "checked_out": 5
      },
      "query_performance_ms": 5.2,
      "connection_test": "passed"
    },
    "cache": {
      "hit_rate": 0.85,
      "miss_rate": 0.15,
      "memory_usage_mb": 256.5,
      "evictions": 125
    },
    "application": {
      "memory_mb": 512.5,
      "cpu_percent": 2.5,
      "threads": 8,
      "open_files": 256,
      "connections": 45
    },
    "system": {
      "cpu_percent": 35.5,
      "memory": {
        "total_gb": 16.0,
        "available_gb": 8.5,
        "percent_used": 46.9
      },
      "disk": {
        "total_gb": 256.0,
        "free_gb": 128.0,
        "percent_used": 50.0
      },
      "load_average": [1.5, 1.3, 1.2],
      "boot_time": "2026-01-03T00:00:00"
    }
  }
}
```

---

### Business Metrics

#### GET /metrics/business

Get business-level metrics.

**Authentication:** Required

**Query Parameters:**
- `org_id` (UUID, optional): Filter by organization

**Request:**
```bash
curl "http://localhost:8000/api/v1/metrics/business?org_id=org-123" \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Business metrics retrieved successfully",
  "data": {
    "users": {
      "total": 150,
      "active_last_7_days": 89,
      "new_last_30_days": 15,
      "active_rate": 59.33
    },
    "assessments": {
      "total_assessments": 45,
      "completed_assessments": 312,
      "completion_rate": 693.33
    },
    "org_id": "org-123",
    "period": "last_30_days"
  }
}
```

---

## Response Management

### Start Response Session

#### POST /responses/start

Start a new assessment response session.

**Authentication:** Required

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/responses/start \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "assessment_id": 1
  }'
```

**Request Body:**
```json
{
  "assessment_id": "integer (required)",
  "assignment_id": "integer (optional)"
}
```

**Success Response (201):**
```json
{
  "id": 789,
  "assessment_id": 1,
  "respondent_id": "user-123",
  "status": "in_progress",
  "responses": {},
  "started_at": "2026-01-04T12:00:00"
}
```

**Error Responses:**
- `404`: Assessment not found
- `400`: Assessment is not published

---

### Get My Responses

#### GET /responses/my-responses

Get all responses by current user.

**Authentication:** Required

**Query Parameters:**
- `status_filter` (string, optional): Filter by status (in_progress, completed)

**Request:**
```bash
curl "http://localhost:8000/api/v1/responses/my-responses?status_filter=completed" \
  -b cookies.txt
```

**Success Response (200):**
```json
[
  {
    "id": 789,
    "assessment_id": 1,
    "status": "completed",
    "started_at": "2026-01-01T00:00:00",
    "completed_at": "2026-01-01T00:30:00"
  }
]
```

---

### Get Response Details

#### GET /responses/{response_id}

Get specific response with score.

**Authentication:** Required

**Request:**
```bash
curl http://localhost:8000/api/v1/responses/789 \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "id": 789,
  "assessment_id": 1,
  "respondent_id": "user-123",
  "status": "completed",
  "responses": {
    "question_1": 4,
    "question_2": 3
  },
  "started_at": "2026-01-01T00:00:00",
  "completed_at": "2026-01-01T00:30:00",
  "score": {
    "total_score": 85,
    "max_score": 100,
    "percentage": 85.0,
    "traits": {
      "extroversion": 75,
      "agreeableness": 82,
      "conscientiousness": 90
    }
  }
}
```

**Error Responses:**
- `403`: No permission to view response
- `404`: Response not found

---

### Save Progress

#### PUT /responses/{response_id}/save

Save progress on an in-progress response.

**Authentication:** Required

**Request:**
```bash
curl -X PUT http://localhost:8000/api/v1/responses/789/save \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "responses": {
      "question_1": 4,
      "question_2": 3
    },
    "current_section": 2
  }'
```

**Request Body:**
```json
{
  "responses": "object (required, question_id: answer pairs)",
  "current_section": "integer (optional)"
}
```

**Success Response (200):**
Returns updated response object.

**Error Responses:**
- `400`: Cannot modify completed response
- `403`: Can only save own responses

---

### Submit Response

#### POST /responses/{response_id}/submit

Submit completed assessment response.

**Authentication:** Required

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/responses/789/submit \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "responses": {
      "question_1": 4,
      "question_2": 3
    },
    "time_taken": 1800
  }'
```

**Request Body:**
```json
{
  "responses": "object (required)",
  "time_taken": "integer (optional, seconds)"
}
```

**Success Response (200):**
Returns completed response with score.

**Error Responses:**
- `400`: Response validation failed or already submitted
- `403`: Can only submit own responses

---

### Delete Response

#### DELETE /responses/{response_id}

Delete an in-progress response.

**Authentication:** Required

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/v1/responses/789 \
  -b cookies.txt
```

**Success Response (204):** No content

**Error Responses:**
- `400`: Cannot delete completed response
- `403`: Can only delete own responses

---

### Get Response Score

#### GET /responses/{response_id}/score

Get score for a completed response.

**Authentication:** Required

**Request:**
```bash
curl http://localhost:8000/api/v1/responses/789/score \
  -b cookies.txt
```

**Success Response (200):**
```json
{
  "total_score": 85,
  "max_score": 100,
  "percentage": 85.0,
  "traits": {
    "extroversion": 75,
    "agreeableness": 82,
    "conscientiousness": 90,
    "neuroticism": 45,
    "openness": 88
  },
  "interpretation": "Your personality shows high conscientiousness and openness, with moderate extroversion."
}
```

**Error Responses:**
- `400`: Response not yet completed
- `403`: No permission to view score
- `404`: Score not available

---

## Error Handling

### Standard Error Response Format

All errors follow this consistent structure:

```json
{
  "success": false,
  "message": "Error message describing what went wrong",
  "error_code": "SPECIFIC_ERROR_CODE",
  "details": {
    "additional": "error context"
  }
}
```

### Common HTTP Status Codes

| Code | Description | Example Scenarios |
|------|-------------|-------------------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful deletion, no content returned |
| 400 | Bad Request | Invalid input, validation errors |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists (e.g., duplicate email) |
| 422 | Unprocessable Entity | Semantic validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Example Error Responses

**Validation Error (400):**
```json
{
  "success": false,
  "message": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "validation_errors": [
      "Email: Invalid email format",
      "Password: Must contain uppercase letter"
    ]
  }
}
```

**Authentication Error (401):**
```json
{
  "success": false,
  "message": "Authentication required",
  "error_code": "AUTH_REQUIRED",
  "details": {
    "hint": "Please login and try again"
  }
}
```

**Rate Limit Error (429):**
```json
{
  "success": false,
  "message": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "retry_after": 60,
    "limit": "5 requests per minute"
  }
}
```

**Server Error (500):**
```json
{
  "success": false,
  "message": "Internal server error",
  "error_code": "INTERNAL_ERROR",
  "details": {
    "request_id": "req_abc123",
    "hint": "Please try again later"
  }
}
```

---

## Rate Limiting

### Overview

The API implements rate limiting to prevent abuse and ensure fair usage.

### Rate Limits by Endpoint

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| POST /auth/token-fixed | 5 | 60 seconds | Per IP |
| POST /auth/register-fixed | 3 | 3600 seconds | Per IP |
| POST /users/register | 5 | 300 seconds | Per IP |
| POST /users/change-password | 5 | 900 seconds | Per user |
| GET /users/ | 30 | 60 seconds | Per user |
| GET /assessments/ | 100 | 60 seconds | Per user |
| POST /assessments/ | 10 | 60 seconds | Per user |
| GET /users/me | 100 | 60 seconds | Per user |

### Rate Limit Headers

Responses include rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704364860
```

### Handling Rate Limits

When rate limited:

```bash
# Check retry-after header
curl -v http://localhost:8000/api/v1/users/ \
  -b cookies.txt

# Response headers include:
# X-RateLimit-Reset: 1704364860
# Retry-After: 45
```

**Best Practices:**
1. Implement exponential backoff on 429 responses
2. Cache responses when possible
3. Use pagination for large result sets
4. Batch requests where supported

---

## Best Practices

### 1. Authentication & Security

**DO:**
- Always use HTTPS in production
- Store tokens securely (use httpOnly cookies)
- Implement proper logout procedures
- Validate tokens before each request
- Handle token expiration gracefully

**DON'T:**
- Never log tokens or passwords
- Don't store tokens in localStorage
- Don't share credentials
- Don't ignore 401/403 errors

### 2. Error Handling

**DO:**
- Always handle errors gracefully
- Display user-friendly error messages
- Log error details for debugging
- Implement retry logic for 5xx errors
- Validate input before sending

**DON'T:**
- Don't expose sensitive error details to users
- Don't ignore error responses
- Don't retry indefinitely on 4xx errors

### 3. Performance

**DO:**
- Use pagination for large lists
- Cache frequently accessed data
- Use compression for large payloads
- Implement request debouncing
- Prefetch likely-needed data

**DON'T:**
- Don't fetch unnecessary fields
- Don't make redundant requests
- Don't poll excessively

### 4. Data Validation

**DO:**
- Validate input on client side
- Sanitize user input
- Use schema validation
- Check for null/undefined values
- Validate data types

**DON'T:**
- Don't trust client-side validation only
- Don't skip server-side validation

### 5. API Versioning

**DO:**
- Always use the API version in URLs (/api/v1/)
- Handle version deprecation gracefully
- Test new API versions before migration

**DON'T:**
- Don't hardcode API versions (make it configurable)

### 6. Monitoring & Debugging

**DO:**
- Log API requests and responses
- Track response times
- Monitor error rates
- Use request IDs for tracing
- Implement health checks

**Example Request Logging:**
```bash
# Include request ID in your requests
curl -H "X-Request-ID: my-custom-request-123" \
  http://localhost:8000/api/v1/users/me \
  -b cookies.txt
```

---

## Common Workflows

### Workflow 1: Complete Assessment

```bash
# 1. Login
curl -X POST http://localhost:8000/api/v1/auth/token-fixed \
  -d "username=user@example.com&password=pass123" \
  -c cookies.txt

# 2. Get assessment questions
curl http://localhost:8000/api/v1/assessments/assessment-questions/mbti \
  -b cookies.txt

# 3. Start response session
curl -X POST http://localhost:8000/api/v1/responses/start \
  -H "Content-Type: application/json" \
  -d '{"assessment_id": 1}' \
  -b cookies.txt

# 4. Save progress periodically
curl -X PUT http://localhost:8000/api/v1/responses/789/save \
  -H "Content-Type: application/json" \
  -d '{"responses":{"q1": 4},"current_section": 1}' \
  -b cookies.txt

# 5. Submit completed assessment
curl -X POST http://localhost:8000/api/v1/responses/789/submit \
  -H "Content-Type: application/json" \
  -d '{"responses":{"q1": 4,"q2": 3},"time_taken": 1800}' \
  -b cookies.txt

# 6. Get results
curl http://localhost:8000/api/v1/responses/789/score \
  -b cookies.txt
```

### Workflow 2: Team Management

```bash
# 1. Create team
curl -X POST http://localhost:8000/api/v1/teams/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Engineering Team","description":"Software dev"}' \
  -b cookies.txt

# 2. Get team analytics
curl "http://localhost:8000/api/v1/analytics/dashboard/overview?team_id=team-123" \
  -b cookies.txt
```

### Workflow 3: Admin User Management

```bash
# 1. List all users (admin)
curl "http://localhost:8000/api/v1/users/?skip=0&limit=50" \
  -b cookies.txt

# 2. View system health
curl http://localhost:8000/api/v1/health/detailed \
  -b cookies.txt

# 3. Get business metrics
curl http://localhost:8000/api/v1/metrics/business \
  -b cookies.txt
```

---

## SDK & Client Libraries

### JavaScript/TypeScript

```typescript
// Example API client setup
class PsychSyncAPI {
  private baseURL: string;
  private cookies: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    this.cookies = '';
  }

  async login(email: string, password: string) {
    const response = await fetch(`${this.baseURL}/auth/token-fixed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `username=${email}&password=${password}`
    });
    // Store cookies from response
    return response.json();
  }

  async getAssessments() {
    const response = await fetch(`${this.baseURL}/assessments/`, {
      headers: { 'Cookie': this.cookies }
    });
    return response.json();
  }
}
```

### Python

```python
import requests

class PsychSyncAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

    def login(self, email, password):
        response = self.session.post(
            f"{self.base_url}/auth/token-fixed",
            data={"username": email, "password": password}
        )
        response.raise_for_status()
        return response.json()

    def get_assessments(self):
        response = self.session.get(f"{self.base_url}/assessments/")
        response.raise_for_status()
        return response.json()
```

---

## Support & Resources

- **API Base URL:** `http://localhost:8000/api/v1`
- **Interactive Documentation:** `http://localhost:8000/docs` (Swagger UI)
- **Alternative Documentation:** `http://localhost:8000/redoc` (ReDoc)
- **Support Email:** support@psychsync.com
- **Status Page:** `http://status.psychsync.com`

### Additional Documentation

- [Authentication Guide](./AUTHENTICATION_GUIDE.md)
- [Rate Limiting Details](./RATE_LIMITING.md)
- [Webhook Integration](./WEBHOOKS.md)
- [SDK Documentation](./SDK_REFERENCE.md)

---

## Changelog

### Version 1.0.0 (2026-01-04)
- Initial API release
- Authentication endpoints
- Assessment management
- User and team management
- Analytics and reporting
- Health monitoring
- Response management

---

**Note:** This documentation is auto-generated and may not reflect the most recent API changes. Always refer to the interactive API documentation (`/docs`) for the most up-to-date information.
