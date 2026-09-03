# PsychSync API Reference

**Version:** 2.0.0
**Base URL:** `https://api.psychsync.com/api/v1`
**Documentation:** Interactive docs at `/docs` (Swagger UI)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Users](#users)
3. [Assessments](#assessments)
4. [Organizations](#organizations)
5. [Teams](#teams)
6. [Responses](#responses)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)

---

## Authentication

### Register User

**Endpoint:** `POST /auth/register`

**Description:** Register a new user account

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecureP@ss99!",
  "full_name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "USER",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-01-19T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Validation error
- `409 Conflict`: Email already exists

---

### Login

**Endpoint:** `POST /auth/login`

**Description:** Authenticate user and receive tokens

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecureP@ss99!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials

---

### Refresh Token

**Endpoint:** `POST /auth/refresh`

**Description:** Get new access token using refresh token

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

### Verify Email

**Endpoint:** `POST /auth/verify`

**Description:** Verify user email address

**Query Parameters:**
- `token` (string, required): Verification token

**Response:** `200 OK`
```json
{
  "message": "Email verified successfully"
}
```

---

### Request Password Reset

**Endpoint:** `POST /auth/password-reset/request`

**Description:** Request password reset email

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset email sent"
}
```

---

### Reset Password

**Endpoint:** `POST /auth/password-reset/confirm`

**Description:** Reset password with token

**Request Body:**
```json
{
  "token": "reset_token_here",
  "new_password": "NewSecureP@ss99!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset successfully"
}
```

---

## Users

### Get Current User

**Endpoint:** `GET /users/me`

**Auth Required:** ✅ Yes

**Description:** Get current authenticated user

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "USER",
  "is_active": true,
  "is_verified": true,
  "is_superuser": false,
  "avatar_url": "https://cdn.example.com/avatar.jpg",
  "organization_id": "org-uuid",
  "created_at": "2025-01-19T10:30:00Z",
  "updated_at": "2025-01-19T10:30:00Z"
}
```

---

### Update User Profile

**Endpoint:** `PATCH /users/me`

**Auth Required:** ✅ Yes

**Description:** Update current user profile

**Request Body:**
```json
{
  "full_name": "Jane Doe",
  "avatar_url": "https://example.com/new-avatar.jpg"
}
```

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "avatar_url": "https://example.com/new-avatar.jpg"
}
```

---

### Change Password

**Endpoint:** `POST /users/me/change-password`

**Auth Required:** ✅ Yes

**Description:** Change user password

**Request Body:**
```json
{
  "old_password": "OldP@ss99!",
  "new_password": "NewSecureP@ss99!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

---

### Get User by ID

**Endpoint:** `GET /users/{user_id}`

**Auth Required:** ✅ Yes

**Description:** Get user by ID (admin or team member only)

**Path Parameters:**
- `user_id` (UUID, required): User ID

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "USER"
}
```

---

### List Users

**Endpoint:** `GET /users`

**Auth Required:** ✅ Yes (Admin only)

**Query Parameters:**
- `skip` (integer, default: 0): Pagination offset
- `limit` (integer, default: 100): Max results per page
- `is_active` (boolean, optional): Filter by active status
- `role` (string, optional): Filter by role

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "USER"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

---

## Assessments

### Create Assessment

**Endpoint:** `POST /assessments`

**Auth Required:** ✅ Yes

**Description:** Create a new assessment

**Request Body:**
```json
{
  "title": "Team Personality Assessment",
  "description": "MBTI assessment for team building",
  "category": "mbti",
  "status": "draft",
  "instructions": "Answer all questions honestly",
  "time_limit_minutes": 30
}
```

**Response:** `201 Created`
```json
{
  "id": "assess-uuid",
  "title": "Team Personality Assessment",
  "description": "MBTI assessment for team building",
  "category": "mbti",
  "status": "draft",
  "created_by_id": "user-uuid",
  "organization_id": "org-uuid",
  "created_at": "2025-01-19T10:30:00Z",
  "updated_at": "2025-01-19T10:30:00Z"
}
```

---

### Get Assessment by ID

**Endpoint:** `GET /assessments/{assessment_id}`

**Auth Required:** ✅ Yes

**Path Parameters:**
- `assessment_id` (UUID, required): Assessment ID

**Response:** `200 OK`
```json
{
  "id": "assess-uuid",
  "title": "Team Personality Assessment",
  "description": "MBTI assessment for team building",
  "category": "mbti",
  "status": "published",
  "sections": [
    {
      "id": "section-uuid",
      "title": "Personality Questions",
      "order": 1,
      "questions": [
        {
          "id": "q-uuid",
          "text": "You enjoy social gatherings",
          "type": "multiple_choice",
          "options": [
            {"id": "opt-1", "text": "Strongly Agree", "value": 2},
            {"id": "opt-2", "text": "Agree", "value": 1},
            {"id": "opt-3", "text": "Neutral", "value": 0},
            {"id": "opt-4", "text": "Disagree", "value": -1},
            {"id": "opt-5", "text": "Strongly Disagree", "value": -2}
          ]
        }
      ]
    }
  ]
}
```

---

### List Assessments

**Endpoint:** `GET /assessments`

**Auth Required:** ✅ Yes

**Query Parameters:**
- `skip` (integer, default: 0): Pagination offset
- `limit` (integer, default: 100): Max results per page
- `status` (string, optional): Filter by status (draft, published, archived)
- `category` (string, optional): Filter by category (mbti, big_five, etc.)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "assess-uuid",
      "title": "Team Personality Assessment",
      "category": "mbti",
      "status": "published"
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 100
}
```

---

### Update Assessment

**Endpoint:** `PATCH /assessments/{assessment_id}`

**Auth Required:** ✅ Yes (Owner or Admin)

**Request Body:**
```json
{
  "title": "Updated Assessment Title",
  "status": "published"
}
```

**Response:** `200 OK`
```json
{
  "id": "assess-uuid",
  "title": "Updated Assessment Title",
  "status": "published"
}
```

---

### Delete Assessment

**Endpoint:** `DELETE /assessments/{assessment_id}`

**Auth Required:** ✅ Yes (Owner or Admin)

**Response:** `204 No Content`

---

### Process Assessment

**Endpoint:** `POST /assessments/{assessment_id}/process`

**Auth Required:** ✅ Yes

**Description:** Submit assessment responses and get results

**Request Body:**
```json
{
  "responses": [2, 1, 0, -1, 2, 1, 0, -1]
}
```

**Response:** `200 OK`
```json
{
  "id": "result-uuid",
  "assessment_id": "assess-uuid",
  "user_id": "user-uuid",
  "framework": "mbti",
  "results": {
    "type": "INTJ",
    "dimensions": {
      "EI": {"E": 0.3, "I": 0.7, "dominant": "I"},
      "SN": {"S": 0.4, "N": 0.6, "dominant": "N"},
      "TF": {"T": 0.8, "F": 0.2, "dominant": "T"},
      "JP": {"J": 0.4, "P": 0.6, "dominant": "P"}
    },
    "confidence": 0.95,
    "interpretations": {
      "type": "INTJ - The Architect",
      "description": "Strategic, independent, determined"
    }
  },
  "created_at": "2025-01-19T10:30:00Z"
}
```

---

## Organizations

### Create Organization

**Endpoint:** `POST /organizations`

**Auth Required:** ✅ Yes

**Request Body:**
```json
{
  "name": "Acme Corporation",
  "industry": "Technology",
  "size": "100-500"
}
```

**Response:** `201 Created`
```json
{
  "id": "org-uuid",
  "name": "Acme Corporation",
  "industry": "Technology",
  "size": "100-500",
  "created_at": "2025-01-19T10:30:00Z"
}
```

---

### Get Organization

**Endpoint:** `GET /organizations/{organization_id}`

**Auth Required:** ✅ Yes (Member or Admin)

**Response:** `200 OK`
```json
{
  "id": "org-uuid",
  "name": "Acme Corporation",
  "industry": "Technology",
  "size": "100-500",
  "member_count": 127,
  "team_count": 12,
  "created_at": "2025-01-19T10:30:00Z"
}
```

---

## Teams

### Create Team

**Endpoint:** `POST /teams`

**Auth Required:** ✅ Yes

**Request Body:**
```json
{
  "name": "Engineering Team",
  "organization_id": "org-uuid",
  "description": "Software development team"
}
```

**Response:** `201 Created`
```json
{
  "id": "team-uuid",
  "name": "Engineering Team",
  "organization_id": "org-uuid",
  "member_count": 8,
  "created_at": "2025-01-19T10:30:00Z"
}
```

---

### Add Team Member

**Endpoint:** `POST /teams/{team_id}/members`

**Auth Required:** ✅ Yes (Team Lead or Admin)

**Request Body:**
```json
{
  "user_id": "user-uuid",
  "role": "member"
}
```

**Response:** `200 OK`
```json
{
  "user_id": "user-uuid",
  "team_id": "team-uuid",
  "role": "member",
  "joined_at": "2025-01-19T10:30:00Z"
}
```

---

## Responses

### Submit Assessment Response

**Endpoint:** `POST /responses`

**Auth Required:** ✅ Yes

**Request Body:**
```json
{
  "assessment_id": "assess-uuid",
  "responses": [2, 1, 0, -1, 2, 1, 0, -1]
}
```

**Response:** `201 Created`
```json
{
  "id": "response-uuid",
  "assessment_id": "assess-uuid",
  "user_id": "user-uuid",
  "status": "completed",
  "created_at": "2025-01-19T10:30:00Z"
}
```

---

### Get User Responses

**Endpoint:** `GET /responses`

**Auth Required:** ✅ Yes

**Query Parameters:**
- `assessment_id` (UUID, optional): Filter by assessment
- `skip` (integer, default: 0): Pagination offset
- `limit` (integer, default: 100): Max results per page

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "response-uuid",
      "assessment_id": "assess-uuid",
      "assessment_title": "Team Personality Assessment",
      "status": "completed",
      "created_at": "2025-01-19T10:30:00Z"
    }
  ],
  "total": 5,
  "skip": 0,
  "limit": 100
}
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "timestamp": "2025-01-19T10:30:00Z",
    "request_id": "req-uuid"
  }
}
```

### Common Error Codes

| Status | Code | Description |
|--------|------|-------------|
| 400 | VALIDATION_ERROR | Request validation failed |
| 401 | UNAUTHORIZED | Authentication required |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Resource already exists |
| 422 | UNPROCESSABLE_ENTITY | Semantic errors |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |

### Error Example

**Request:** `POST /auth/login` with invalid credentials

**Response:** `401 Unauthorized`
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password",
    "timestamp": "2025-01-19T10:30:00Z",
    "request_id": "req-123"
  }
}
```

---

## Rate Limiting

### Rate Limit Headers

All API responses include rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642600800
```

### Rate Limits by Endpoint

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /auth/login` | 5 requests | 1 minute |
| `POST /auth/register` | 3 requests | 1 hour |
| `POST /assessments` | 10 requests | 1 minute |
| `GET /assessments` | 100 requests | 1 minute |
| `POST /responses` | 20 requests | 1 minute |

### Rate Limit Exceeded

**Response:** `429 Too Many Requests`
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60
  }
}
```

---

## Authentication in Requests

### Bearer Token

Include the access token in the `Authorization` header:

```bash
curl -X GET https://api.psychsync.com/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Example with Python

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(
    "https://api.psychsync.com/api/v1/users/me",
    headers=headers
)

user = response.json()
```

### Example with JavaScript

```javascript
const headers = {
  'Authorization': `Bearer ${accessToken}`
};

fetch('https://api.psychsync.com/api/v1/users/me', { headers })
  .then(response => response.json())
  .then(user => console.log(user));
```

---

## Pagination

### Pagination Format

List endpoints return paginated responses:

```json
{
  "items": [...],
  "total": 250,
  "skip": 0,
  "limit": 100
}
```

### Pagination Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of items to skip |
| `limit` | integer | 100 | Number of items to return (max: 100) |

### Pagination Example

```bash
# Get first page
GET /assessments?skip=0&limit=20

# Get second page
GET /assessments?skip=20&limit=20
```

---

## Webhooks

### Webhook Configuration

Webhooks can be configured to receive notifications about events:

**Supported Events:**
- `assessment.completed`: User completed assessment
- `user.registered`: New user registered
- `team.member_added`: Member added to team

### Webhook Payload Example

```json
{
  "event": "assessment.completed",
  "timestamp": "2025-01-19T10:30:00Z",
  "data": {
    "user_id": "user-uuid",
    "assessment_id": "assess-uuid",
    "result_id": "result-uuid"
  }
}
```

---

## SDKs and Libraries

### Python SDK

```python
from psychsync import PsychSyncClient

client = PsychSyncClient(
    api_key="your-api-key",
    base_url="https://api.psychsync.com"
)

# Get current user
user = client.users.get_me()

# Create assessment
assessment = client.assessments.create(
    title="My Assessment",
    category="mbti"
)
```

### JavaScript SDK

```javascript
import { PsychSyncClient } from '@psychsync/sdk';

const client = new PsychSyncClient({
  apiKey: 'your-api-key',
  baseURL: 'https://api.psychsync.com'
});

// Get current user
const user = await client.users.getMe();

// Create assessment
const assessment = await client.assessments.create({
  title: 'My Assessment',
  category: 'mbti'
});
```

---

## Changelog

### Version 2.0.0 (2025-01-19)

**Breaking Changes:**
- Migrated to UUID-based identifiers
- Updated authentication flow with refresh tokens
- Changed error response format

**New Features:**
- Assessment processing endpoint
- Team management endpoints
- Enhanced rate limiting
- Webhook support

**Improvements:**
- Better error messages
- Consistent pagination
- Performance optimizations

---

**Interactive Documentation:** https://api.psychsync.com/docs
**Support:** api-support@psychsync.com
**Status Page:** https://status.psychsync.com
