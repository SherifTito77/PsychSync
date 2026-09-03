# OpenAPI Documentation Guide

**Status:** ✅ All endpoints have proper response models
**Last Updated:** 2026-01-19
**API Version:** v1

---

## Overview

All API endpoints in the PsychSync application now have **proper response schema validation**. This means:
- ✅ No endpoints use `response_model=dict`
- ✅ All responses are validated against Pydantic models
- ✅ OpenAPI specification is accurate and complete
- ✅ Type generation works correctly

---

## Accessing OpenAPI Documentation

### Swagger UI (Interactive API Documentation)
```bash
# Start the server
uvicorn app.main:app --reload

# Open in browser
open http://localhost:8000/docs
```

**Features:**
- Interactive API testing
- Request/response schema display
- Example values for all fields
- Try-it-out functionality

### ReDoc (Alternative Documentation)
```bash
# Open ReDoc
open http://localhost:8000/redoc
```

### OpenAPI JSON Specification
```bash
# Download the complete OpenAPI spec
curl http://localhost:8000/openapi.json > openapi.json

# Pretty print
cat openapi.json | jq '.' > openapi_formatted.json
```

---

## Response Schema Examples

### Authentication Endpoints

#### POST /api/v1/login
**Response Model:** `LoginResponse`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": true,
    "is_superuser": false
  }
}
```

#### POST /api/v1/register
**Response Model:** `RegisterResponse`

```json
{
  "message": "User registered successfully. Please verify your email.",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "requires_verification": true
}
```

#### GET /api/v1/me
**Response Model:** `UserInfoResponse`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": true,
  "is_superuser": false,
  "two_factor_enabled": false,
  "created_at": "2026-01-19T10:30:00.000Z",
  "updated_at": "2026-01-19T10:30:00.000Z"
}
```

### User Management Endpoints

#### GET /api/v1/users/me
**Response Model:** `UserProfileResponse`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": true,
  "is_superuser": false,
  "two_factor_enabled": false,
  "created_at": "2026-01-19T10:30:00.000Z",
  "updated_at": "2026-01-19T10:30:00.000Z",
  "avatar_url": null
}
```

#### GET /api/v1/users/
**Response Model:** `UserListResponse`

```json
{
  "users": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "user@example.com",
      "full_name": "John Doe",
      "is_active": true,
      "is_verified": true,
      "created_at": "2026-01-19T10:30:00.000Z",
      "updated_at": "2026-01-19T10:30:00.000Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 50
}
```

#### POST /api/v1/users/change-password
**Response Model:** `ChangePasswordResponse`

```json
{
  "message": "Password updated successfully. All sessions have been invalidated for security."
}
```

### Team Management Endpoints

#### GET /api/v1/teams/
**Response Model:** `TeamListWithMetaResponse`

```json
{
  "teams": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Product Team",
      "description": "Product management team",
      "organization_id": "org-123",
      "created_at": "2026-01-19T10:30:00.000Z",
      "updated_at": "2026-01-19T10:30:00.000Z",
      "created_by_id": "user-123",
      "members_count": 5
    }
  ],
  "total": 1,
  "success": true,
  "message": "Teams retrieved successfully"
}
```

### Email Connections Endpoints

#### POST /api/v1/email-connections/{connection_id}/test
**Response Model:** `EmailTestResponse`

```json
{
  "connection_id": "conn-123",
  "provider": "gmail",
  "email_address": "user@gmail.com",
  "is_valid": true,
  "last_tested": "2026-01-19T10:30:00.000Z"
}
```

#### GET /api/v1/email-connections/{connection_id}/stats
**Response Model:** `EmailStatsResponse`

```json
{
  "connection_id": "conn-123",
  "provider": "gmail",
  "email_address": "user@gmail.com",
  "total_emails": 1523,
  "recent_emails_30_days": 234,
  "internal_emails": 89,
  "external_emails": 1434,
  "last_sync": "2026-01-19T10:30:00.000Z",
  "sync_status": "active"
}
```

### MFA Endpoints

#### POST /api/v1/mfa/verify-backup-code
**Response Model:** `BackupCodeVerifyResponse`

```json
{
  "message": "Backup code verified successfully",
  "remaining_codes": 9
}
```

### Anonymous Feedback Endpoints

#### POST /api/v1/anonymous-feedback/submit
**Response Model:** `AnonymousFeedbackSubmitResponse`

```json
{
  "success": true,
  "tracking_id": "FB-2026-ABC123",
  "message": "Your feedback has been submitted. Thank you for speaking up.",
  "severity_notice": "This issue has been marked as high severity and will be prioritized.",
  "estimated_response_days": 3,
  "alternatives": null,
  "error": null
}
```

#### GET /api/v1/anonymous-feedback/status/{tracking_id}
**Response Model:** `FeedbackStatusResponse`

```json
{
  "found": true,
  "status": "investigating",
  "submitted_at": "2026-01-15T10:30:00.000Z",
  "days_since_submission": 4,
  "last_updated": "2026-01-19T09:15:00.000Z",
  "public_resolution_notes": "We are currently investigating this matter.",
  "severity": "high",
  "category": "harassment",
  "estimated_resolution_days": 5,
  "status_explanation": "Your feedback is being actively investigated by HR.",
  "privacy_reminder": "Your identity remains confidential.",
  "next_steps": [
    "HR will review the submission",
    "You may be contacted for additional information",
    "Resolution will be communicated via the tracking system"
  ]
}
```

---

## Generating Type Definitions

### TypeScript
```bash
# Install openapi-typescript
npm install -g openapi-typescript

# Generate TypeScript types
openapi-typescript http://localhost:8000/openapi-json -o src/types/api.ts

# Or using the downloaded file
openapi-typescript openapi.json -o src/types/api.ts
```

### Python
```bash
# Install openapi-python-client
pip install openapi-python-client

# Generate Python client
openapi-python-client generate openapi.json
```

### Java/Kotlin
```bash
# Install openapi-generator
npm install -g @openapitools/openapi-generator-cli

# Generate Java client
openapi-generator-cli generate -i openapi.json -g java -o ./client/java

# Generate Kotlin client
openapi-generator-cli generate -i openapi.json -g kotlin -o ./client/kotlin
```

---

## Response Schema Files

### Authentication Schemas
**File:** `app/schemas/auth.py`

Classes:
- `LoginResponse`
- `MFAChallengeResponse`
- `MFALoginResponse`
- `RegisterResponse`
- `VerifyEmailResponse`
- `UserInfoResponse`
- `LogoutResponse`
- `RefreshTokenResponse`
- `MFAResponse`
- `MFAVerifyResponse`
- `MFADisableResponse`
- `HealthCheckResponse`
- `UserSummary`

### User Schemas
**File:** `app/schemas/user.py`

Classes:
- `UserListResponse`
- `UserProfileResponse`
- `ChangePasswordResponse`
- `UpdateUserProfileResponse`
- `CreateUserResponse`

### Team Schemas
**File:** `app/schemas/team.py`

Classes:
- `TeamListWithMetaResponse`
- `TeamItemResponse`

### Email Connection Schemas
**File:** `app/api/v1/endpoints/email_connections.py`

Classes:
- `EmailTestResponse`
- `EmailStatsResponse`

### MFA Schemas
**File:** `app/api/v1/endpoints/mfa.py`

Classes:
- `BackupCodeVerifyResponse`

### Anonymous Feedback Schemas
**File:** `app/api/v1/endpoints/anonymous_feedback.py`

Classes:
- `AnonymousFeedbackSubmitResponse`
- `FeedbackStatusResponse`

---

## Validation

### Run Validation Script
```bash
python scripts/validate_response_schemas.py
```

Expected output:
```
======================================================================
Response Schema Validation Report
======================================================================

1. Checking for response_model=dict usage...
----------------------------------------------------------------------
   ✅ No endpoints using response_model=dict

2. Validating auth response schemas...
----------------------------------------------------------------------
   ✅ All 8 auth schemas defined

3. Validating user response schemas...
----------------------------------------------------------------------
   ✅ All 3 user schemas defined

4. Validating team response schemas...
----------------------------------------------------------------------
   ✅ All 1 team schemas defined

======================================================================
Validation Complete
======================================================================
```

### Run Test Suite
```bash
# Run all response schema validation tests
pytest tests/api/test_response_schema_validation.py -v

# Run specific test class
pytest tests/api/test_response_schema_validation.py::TestOpenAPISpecGeneration -v

# Run with coverage
pytest tests/api/test_response_schema_validation.py --cov=app.api.v1.endpoints -v
```

---

## Best Practices

### When Creating New Endpoints

1. **Define Response Schema First**
   ```python
   # In app/schemas/your_feature.py
   class YourResponse(BaseModel):
       """Response for your endpoint"""
       field1: str
       field2: int
       optional_field: str | None = None
   ```

2. **Use Response Model in Decorator**
   ```python
   @router.get("/your-endpoint", response_model=YourResponse)
   async def your_endpoint():
       return YourResponse(field1="value", field2=42)
   ```

3. **Never Use response_model=dict**
   - ❌ `@router.get("/endpoint", response_model=dict)`
   - ✅ `@router.get("/endpoint", response_model=YourResponse)`

4. **Test Response Validation**
   ```bash
   python scripts/validate_response_schemas.py
   ```

---

## Troubleshooting

### Issue: "Field required" Error
**Cause:** Response model expects a field but it's missing from the return value

**Solution:**
```python
# Check response model definition
class MyResponse(BaseModel):
    required_field: str
    optional_field: str | None = None

# Ensure all required fields are present
return MyResponse(
    required_field="value",  # Required
    optional_field="value",  # Optional
)
```

### Issue: OpenAPI Spec Shows Empty Object
**Cause:** Using `response_model=dict` or `response_model=dict[str, Any]`

**Solution:** Create a proper Pydantic model and use it instead

### Issue: Swagger UI Not Loading
**Cause:** CSP headers blocking Swagger UI resources

**Solution:** Ensure CSP middleware allows Swagger UI
```python
csp_directives = {
    "default-src": "'self'",
    "script-src": "'self' https://cdn.jsdelivr.net",
    "style-src": "'self' https://fonts.googleapis.com https://cdn.jsdelivr.net",
    # ... other directives
}
```

---

## Migration from Old Response Format

If you have existing code returning raw dicts:

**Before:**
```python
@router.get("/endpoint", response_model=dict)
async def get_data():
    return {"field1": "value", "field2": 123}
```

**After:**
```python
# 1. Create response model
class DataResponse(BaseModel):
    field1: str
    field2: int

# 2. Update decorator
@router.get("/endpoint", response_model=DataResponse)

# 3. Update return statement
async def get_data():
    return DataResponse(field1="value", field2=123)
```

---

## Additional Resources

- **FastAPI Response Models:** https://fastapi.tiangolo.com/tutorial/response-model/
- **Pydantic Documentation:** https://docs.pydantic.dev/
- **OpenAPI Specification:** https://swagger.io/specification/
- **TypeScript Type Generation:** https://openapi-ts.pages.dev/

---

**Last Updated:** 2026-01-19
**Maintained By:** Backend Architecture Team
