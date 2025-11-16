# PsychSync API Reference

This document provides detailed information about the PsychSync REST API endpoints.

## Base URL

```
https://api.psychsync.com/api/v1
```

## Authentication

Most endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## Endpoints

### Authentication

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

#### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "your-refresh-token"
}
```

### Organizations

#### Get Organizations
```http
GET /organizations
Authorization: Bearer <token>
```

#### Create Organization
```http
POST /organizations
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "My Company",
  "description": "A great company to work for"
}
```

#### Get Organization Details
```http
GET /organizations/{organization_id}
Authorization: Bearer <token>
```

### Teams

#### Get Teams
```http
GET /teams
Authorization: Bearer <token>
```

#### Create Team
```http
POST /teams
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Development Team",
  "organization_id": 123,
  "description": "Our awesome dev team"
}
```

#### Get Team Details
```http
GET /teams/{team_id}
Authorization: Bearer <token>
```

#### Add Team Member
```http
POST /teams/{team_id}/members
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": 456,
  "role": "member"
}
```

### Assessments

#### Get Assessments
```http
GET /assessments
Authorization: Bearer <token>
```

#### Create Assessment
```http
POST /assessments
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Big Five Personality Test",
  "description": "Measure Big Five personality traits",
  "framework": "big_five",
  "questions": [
    {
      "text": "I see myself as someone who is talkative",
      "type": "scale",
      "scale_min": 1,
      "scale_max": 5
    }
  ]
}
```

#### Start Assessment
```http
POST /assessments/{assessment_id}/start
Authorization: Bearer <token>
```

#### Submit Assessment Responses
```http
POST /assessments/{assessment_id}/submit
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "session-uuid",
  "responses": [
    {
      "question_id": 1,
      "value": 4
    }
  ]
}
```

#### Get Assessment Results
```http
GET /assessments/{assessment_id}/results
Authorization: Bearer <token>
```

### Team Optimization

#### Optimize Team
```http
POST /team-optimizer/optimize
Authorization: Bearer <token>
Content-Type: application/json

{
  "members": [
    {
      "id": 1,
      "name": "John Doe",
      "role": "Developer",
      "traits": {
        "openness": 0.8,
        "conscientiousness": 0.7,
        "extraversion": 0.6,
        "agreeableness": 0.9,
        "neuroticism": 0.3
      }
    }
  ],
  "objective": "maximize_engagement"
}
```

Response:
```json
{
  "recommended_groups": [[1, 3], [2, 4]],
  "score": 0.85,
  "analysis": {
    "team_compatibility": 0.82,
    "diversity_score": 0.76,
    "potential_conflicts": []
  }
}
```

### Users

#### Get User Profile
```http
GET /users/profile
Authorization: Bearer <token>
```

#### Update User Profile
```http
PUT /users/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "John Smith",
  "title": "Software Engineer",
  "bio": "Passionate about building great software"
}
```

### Notifications

#### Send Event Notification
```http
POST /notifications/send-event
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": 123,
  "event": "assessment_completed",
  "payload": {
    "assessment_id": 456,
    "score": 85
  }
}
```

#### Send Email Notification
```http
POST /notifications/send-email
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "user@example.com",
  "subject": "Assessment Completed",
  "body": "You have successfully completed your assessment."
}
```

## Response Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limits

API requests are rate-limited to prevent abuse:

- **Free Plan**: 100 requests per hour
- **Pro Plan**: 1,000 requests per hour
- **Enterprise Plan**: 10,000 requests per hour

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Time when rate limit resets (Unix timestamp)

## Error Handling

All errors return a JSON response with error details:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "invalid-email"
    }
  }
}
```

## Webhooks

PsychSync supports webhooks for real-time notifications:

### Configure Webhook

```http
POST /webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["assessment.completed", "team.optimized"],
  "secret": "your-webhook-secret"
}
```

### Webhook Payload Example

```json
{
  "event": "assessment.completed",
  "data": {
    "assessment_id": 123,
    "user_id": 456,
    "completed_at": "2024-01-15T10:30:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## SDKs

Official SDKs are available for:
- Python: `pip install psychsync-python`
- JavaScript: `npm install psychsync-js`
- Ruby: `gem install psychsync-ruby`

## Support

For API support:
- Documentation: [https://docs.psychsync.com](https://docs.psychsync.com)
- Email: api-support@psychsync.com
- Status Page: [https://status.psychsync.com](https://status.psychsync.com)

---

Last updated: January 2024