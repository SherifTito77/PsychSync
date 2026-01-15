# Error Code Quick Reference Guide

> **Last Updated:** January 13, 2026
> **Purpose:** Quick guide for using PsychSync error codes and exceptions
> **Audience:** Backend developers working on the PsychSync platform

---

## Quick Start

### Using Custom Exceptions (Recommended)

```python
from app.core.exceptions import (
    AssessmentNotFoundError,
    TeamAccessDeniedError,
    PaymentFailedError,
    WeakPasswordError,
)

# Assessment not found
if not assessment:
    raise AssessmentNotFoundError(assessment_id="123")

# Team access denied
if not has_permission:
    raise TeamAccessDeniedError(
        team_id="456",
        user_id="789"
    )

# Payment failed
if payment declined:
    raise PaymentFailedError(
        reason="Card declined"
    )

# Weak password
if not meets_requirements:
    raise WeakPasswordError(
        requirements={
            "min_length": 8,
            "requires_uppercase": True,
            "requires_number": True
        }
    )
```

### Using Generic PsychSyncException

```python
from app.core.exceptions import PsychSyncException, ErrorCode

raise PsychSyncException(
    message="Custom error message",
    error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
    status_code=400,
    details={"custom_field": "custom_value"}
)
```

---

## New Error Codes Added

### Security & Compliance (AUTH 1100-1199)

| Error Code | HTTP | Exception Class | Use Case |
|------------|------|-----------------|----------|
| AUTH_1102 | 403 | `AccountLockedError` | Account locked due to security concerns |
| AUTH_1104 | 401 | `SessionExpiredError` | Session expired, user must re-login |
| AUTH_1106 | 429 | `RateLimitExceededError` | Rate limit exceeded (include retry_after) |
| AUTH_1108 | 401 | `MFARRequiredError` | MFA required for this operation |
| AUTH_1111 | 400 | N/A | Password found in data breach |
| AUTH_1112 | 400 | `WeakPasswordError` | Password doesn't meet requirements |
| AUTH_1115 | 403 | N/A | Account suspended by admin |

**Example:**
```python
from app.core.exceptions import RateLimitExceededError

raise RateLimitExceededError(
    retry_after=60,  # seconds
    limit=100  # max requests
)
```

---

### Assessment Errors (BIZ 4100-4199)

| Error Code | HTTP | Exception Class | Use Case |
|------------|------|-----------------|----------|
| BIZ_4100 | 404 | `AssessmentNotFoundError` | Assessment not found |
| BIZ_4104 | 410 | `AssessmentExpiredError` | Assessment window closed |
| BIZ_4105 | 429 | `AssessmentLimitExceededError` | User/org reached assessment limit |
| BIZ_4108 | 409 | `ResponseAlreadySubmittedError` | User already responded |
| BIZ_4112 | 423 | `AssessmentLockedError` | Assessment locked (has responses) |

**Example:**
```python
from app.core.exceptions import (
    AssessmentNotFoundError,
    AssessmentExpiredError
)

# Not found
if not assessment:
    raise AssessmentNotFoundError(assessment_id=str(assessment_id))

# Expired
if assessment.expires_at < datetime.now():
    raise AssessmentExpiredError(
        assessment_id=str(assessment.id),
        expiry_date=assessment.expires_at.isoformat()
    )
```

---

### Team Management Errors (BIZ 4300-4399)

| Error Code | HTTP | Exception Class | Use Case |
|------------|------|-----------------|----------|
| BIZ_4300 | 404 | `TeamNotFoundError` | Team not found |
| BIZ_4303 | 403 | `TeamAccessDeniedError` | User lacks team access |
| BIZ_4304 | 429 | `TeamLimitExceededError` | Org reached team limit |

**Example:**
```python
from app.core.exceptions import TeamAccessDeniedError

if not team_service.user_has_access(user_id, team_id):
    raise TeamAccessDeniedError(
        team_id=str(team_id),
        user_id=str(user_id)
    )
```

---

### Billing Errors (BIZ 4500-4599)

| Error Code | HTTP | Exception Class | Use Case |
|------------|------|-----------------|----------|
| BIZ_4503 | 402 | N/A | Payment method required |
| BIZ_4504 | 402 | `PaymentFailedError` | Payment transaction failed |
| BIZ_4507 | 403 | N/A | Plan limit exceeded |
| BIZ_4508 | 402 | `UpgradeRequiredError` | Feature needs higher tier |

**Example:**
```python
from app.core.exceptions import UpgradeRequiredError

if not subscription.has_feature("advanced_analytics"):
    raise UpgradeRequiredError(
        feature="advanced_analytics",
        required_plan="Professional"
    )
```

---

## Migration Guide

### Before (Generic HTTPException)

```python
from fastapi import HTTPException, status

# ❌ Generic error - no error code
if not assessment:
    raise HTTPException(
        status_code=404,
        detail="Assessment not found"
    )

# ❌ Generic validation error
if not user.is_active:
    raise HTTPException(
        status_code=403,
        detail="User account is inactive"
    )
```

### After (Structured Exceptions)

```python
from app.core.exceptions import AssessmentNotFoundError, UserInactiveError

# ✅ Structured error with error code
if not assessment:
    raise AssessmentNotFoundError(assessment_id=str(assessment_id))

# ✅ Structured error with context
if not user.is_active:
    raise UserInactiveError()
```

---

## Error Response Format

All errors now return consistent JSON:

```json
{
  "error": true,
  "error_code": "BIZ_4100",
  "message": "Assessment 123e4567-e89b-12d3-a456-426614174000 not found",
  "status_code": 404,
  "details": {
    "assessment_id": "123e4567-e89b-12d3-a456-426614174000"
  },
  "timestamp": "2026-01-13T10:30:00.000Z",
  "request_id": "req_abc123",
  "path": "/api/v1/assessments/123",
  "documentation_url": "https://docs.psychsync.com/api/errors/BIZ_4100"
}
```

---

## Common Patterns

### 1. Resource Not Found

```python
from app.core.exceptions import RecordNotFoundError

# Generic record not found
if not record:
    raise RecordNotFoundError(
        resource="Assessment",
        identifier=str(assessment_id)
    )

# Specific assessment not found
if not assessment:
    raise AssessmentNotFoundError(assessment_id=str(assessment_id))
```

### 2. Access Denied

```python
from app.core.exceptions import (
    ForbiddenError,
    TeamAccessDeniedError
)

# Generic access denied
if not has_permission:
    raise ForbiddenError(
        message="You do not have permission to perform this action"
    )

# Team-specific access denied
if not has_team_access:
    raise TeamAccessDeniedError(
        team_id=str(team_id),
        user_id=str(user_id)
    )
```

### 3. Validation Errors

```python
from app.core.exceptions import (
    ValidationError,
    InvalidEmailError,
    WeakPasswordError
)

# Generic validation error
if not is_valid(data):
    raise ValidationError(
        message="Invalid data provided",
        error_code=ErrorCode.VALIDATION_ERROR
    )

# Specific email validation
if not is_valid_email(email):
    raise InvalidEmailError(email=email)

# Password requirements
if not meets_password_requirements(password):
    raise WeakPasswordError(
        requirements={
            "min_length": 8,
            "requires_uppercase": True,
            "requires_number": True,
            "requires_special_char": True
        }
    )
```

### 4. Rate Limiting

```python
from app.core.exceptions import RateLimitExceededError

# Check rate limit
if rate_limit_exceeded():
    raise RateLimitExceededError(
        retry_after=60,  # seconds until retry
        limit=100  # max requests per window
    )
```

### 5. Resource Limits

```python
from app.core.exceptions import (
    AssessmentLimitExceededError,
    TeamLimitExceededError
)

# Assessment limit
if user_assessment_count >= user.plan.max_assessments:
    raise AssessmentLimitExceededError(
        limit=user.plan.max_assessments
    )

# Team limit
if org_team_count >= org.plan.max_teams:
    raise TeamLimitExceededError(
        limit=org.plan.max_teams
    )
```

---

## Testing with Error Codes

### Unit Tests

```python
import pytest
from app.core.exceptions import AssessmentNotFoundError, ErrorCode

def test_get_assessment_not_found():
    """Test AssessmentNotFoundError is raised"""
    with pytest.raises(AssessmentNotFoundError) as exc_info:
        raise AssessmentNotFoundError(assessment_id="123")

    # Verify error code
    assert exc_info.value.error_code == ErrorCode.ASSESSMENT_NOT_FOUND
    assert exc_info.value.status_code == 404
    assert exc_info.value.details["assessment_id"] == "123"
```

### Integration Tests

```python
from fastapi.testclient import TestClient

def test_get_assessment_returns_404(client: TestClient):
    """Test GET /assessments/{id} returns 404 with error code"""
    response = client.get("/api/v1/assessments/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"] == True
    assert response.json()["error_code"] == "BIZ_4100"
    assert "timestamp" in response.json()
    assert "request_id" in response.json()
```

---

## Adding New Error Codes

If you need a new error code:

1. **Add to ErrorCode enum** in `app/core/exceptions.py`:
```python
class ErrorCode(str, Enum):
    # ... existing codes ...
    YOUR_NEW_ERROR = "CATEGORY_XXXX"
```

2. **Create exception class** (if reusable):
```python
class YourNewError(PsychSyncException):
    """Description of error"""

    def __init__(self, param: str, details: dict | None = None):
        message = f"Error message with {param}"
        if details is None:
            details = {"param": param}
        super().__init__(message, ErrorCode.YOUR_NEW_ERROR, status_code=400, details=details)
```

3. **Document in this guide** with:
   - Error code
   - HTTP status
   - Exception class
   - Use case description
   - Example usage

---

## Best Practices

### ✅ DO

- **Use specific exceptions** (`AssessmentNotFoundError` vs generic `RecordNotFoundError`)
- **Include helpful details** in the `details` dict (IDs, counts, limits)
- **Log before raising** in production (exception handlers will log)
- **Use appropriate HTTP status codes** (404, 403, 429, etc.)
- **Provide context** that helps debugging without exposing sensitive data

### ❌ DON'T

- **Don't expose internal details** in error messages (file paths, stack traces in production)
- **Don't use generic HTTPException** anymore (use structured exceptions)
- **Don't forget to test** error scenarios
- **Don't hardcode error codes** (use `ErrorCode.ERROR_NAME` enum)
- **Don't include sensitive data** in `details` (passwords, tokens, PII)

---

## Quick Reference Card

### Print this for your desk:

```
ASSESSMENT ERRORS:
  AssessmentNotFoundError(assessment_id) → 404
  AssessmentExpiredError(id, expiry_date) → 410
  AssessmentLimitExceededError(limit) → 429

TEAM ERRORS:
  TeamNotFoundError(team_id) → 404
  TeamAccessDeniedError(team_id, user_id) → 403

SECURITY ERRORS:
  AccountLockedError() → 403
  SessionExpiredError() → 401
  RateLimitExceededError(retry_after, limit) → 429
  WeakPasswordError(requirements) → 400

BILLING ERRORS:
  PaymentFailedError(reason) → 402
  UpgradeRequiredError(feature, plan) → 402
```

---

## Need Help?

- **Full Error Code List:** See `app/core/exceptions.py`
- **Error Documentation:** https://docs.psychsync.com/api/errors
- **Architecture Docs:** `/Users/sheriftito/Downloads/psychsync/docs/code_quality/ERROR_CODE_SYSTEM.md`
- **Examples:** Check `tests/` directory for test examples

---

## Summary

**What Changed:**
- ✅ Added 60+ new error codes
- ✅ Created custom exception classes for common errors
- ✅ Structured error responses with helpful metadata
- ✅ Existing handlers already support new codes

**What You Need to Do:**
1. **Replace generic HTTPException** with structured exceptions
2. **Include helpful details** in exception constructors
3. **Test error scenarios** in your unit tests
4. **Reference this guide** when unsure which error code to use

**Questions?** Ask in #backend-dev channel or create an issue!
