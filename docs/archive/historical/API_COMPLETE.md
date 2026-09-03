# PsychSync API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
All endpoints except login and register require a Bearer token:
```
Authorization: Bearer {access_token}
```

## Endpoints

### Authentication

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "SecurePass123"
}
```

#### Login
```http
POST /auth/login/json
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

#### Get Current User
```http
GET /auth/me
Authorization: Bearer {token}
```

### Teams

#### Create Team
```http
POST /teams
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Psychology Team",
  "description": "Clinical psychology team"
}
```

#### List Teams
```http
GET /teams?my_teams=true
Authorization: Bearer {token}
```

#### Add Member
```http
POST /teams/{team_id}/members
Authorization: Bearer {token}
Content-Type: application/json

{
  "user_id": 2,
  "role": "member"
}
```

### Assessments

#### Create Assessment
```http
POST /assessments
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Personality Assessment",
  "description": "Five-factor model",
  "category": "personality",
  "sections": [
    {
      "title": "Section 1",
      "order": 0,
      "questions": [
        {
          "question_type": "likert",
          "question_text": "I am outgoing",
          "order": 0,
          "is_required": true
        }
      ]
    }
  ]
}
```

#### Publish Assessment
```http
POST /assessments/{id}/publish
Authorization: Bearer {token}
```

### Responses

#### Start Response Session
```http
POST /responses/start
Authorization: Bearer {token}
Content-Type: application/json

{
  "assessment_id": 1
}
```

#### Save Progress
```http
PUT /responses/{response_id}/save
Authorization: Bearer {token}
Content-Type: application/json

{
  "responses": {
    "1": 5,
    "2": "My answer"
  },
  "current_section": 0
}
```

#### Submit Response
```http
POST /responses/{response_id}/submit
Authorization: Bearer {token}
Content-Type: application/json

{
  "responses": {
    "1": 5,
    "2": "My answer"
  },
  "time_taken": 300
}
```

### Analytics

#### Get Assessment Analytics
```http
GET /analytics/assessments/{id}
Authorization: Bearer {token}
```

#### Get My Analytics
```http
GET /analytics/users/me
Authorization: Bearer {token}
```

### Templates

#### List Templates
```http
GET /templates?category=personality&is_official=true
```

#### Use Template
```http
POST /templates/{id}/use?team_id=1
Authorization: Bearer {token}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

## Rate Limiting
- 100 requests per minute per user
- 1000 requests per hour per IP

## Pagination
List endpoints support pagination:
```
?skip=0&limit=100
```

## Filtering
Many list endpoints support filtering:
```
?category=personality&status=active
```
