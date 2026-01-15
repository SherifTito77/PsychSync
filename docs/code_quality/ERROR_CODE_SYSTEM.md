# Comprehensive Error Code System

> **Analysis Date:** January 12, 2026
> **Purpose:** Standardize error handling across the PsychSync platform
> **Scope:** All API endpoints and services

---

## Executive Summary

The PsychSync codebase has a **solid error handling foundation** but suffers from:
1. **50+ generic HTTPExceptions** without proper error codes
2. **Inconsistent error messages** for the same error types
3. **Missing domain-specific error codes** (assessments, teams, templates)
4. **Lack of structured error responses** with helpful context

**Impact:** Difficult debugging, poor client error handling, security risks from generic error messages.

---

## Current Error Code Structure

The existing system uses a well-designed category-based format:

```
CATEGORY_NUMBER

Categories:
- AUTH: Authentication/Authorization (1000-1099)
- VAL: Validation (2000-2099)
- DB: Database (3000-3099)
- BIZ: Business Logic (4000-4099)
- EXT: External Services (5000-5099)
- SYS: System (6000-6099)
- AI: AI/ML Operations (7000-7099)
```

**Example:** `AUTH_1002` = Invalid credentials

---

## Missing Error Codes to Implement

### 1. Assessment-Specific Codes (BIZ 4100-4199)

```python
class AssessmentErrorCode(str, Enum):
    """Assessment management error codes"""

    ASSESSMENT_NOT_FOUND = "BIZ_4100"
    """Assessment with specified ID does not exist"""

    ASSESSMENT_ALREADY_PUBLISHED = "BIZ_4101"
    """Cannot modify an assessment that is already published"""

    ASSESSMENT_NOT_PUBLISHED = "BIZ_4102"
    """Assessment must be published before it can be taken"""

    INVALID_ASSESSMENT_STATUS = "BIZ_4103"
    """Invalid status transition for current assessment state"""

    ASSESSMENT_EXPIRED = "BIZ_4104"
    """Assessment window has closed"""

    ASSESSMENT_LIMIT_EXCEEDED = "BIZ_4105"
    """User has reached the maximum number of assessments for their tier"""

    INVALID_QUESTION_FORMAT = "BIZ_4106"
    """Question does not match expected schema for assessment type"""

    INVALID_RESPONSE_FORMAT = "BIZ_4107"
    """Response does not match expected question format"""

    RESPONSE_ALREADY_SUBMITTED = "BIZ_4108"
    """User has already submitted a response for this assessment"""

    ASSESSMENT_INCOMPLETE = "BIZ_4109"
    """Cannot generate results for incomplete assessment"""

    INVALID_ASSESSMENT_TYPE = "BIZ_4110"
    """Assessment type not supported (e.g., invalid framework code)"""

    ASSESSMENT_SCORING_FAILED = "BIZ_4111"
    """Failed to calculate assessment scores"""

    ASSESSMENT_LOCKED = "BIZ_4112"
    """Assessment is locked for editing (has active responses)"""

    INVALID_SECTION_ORDER = "BIZ_4113"
    """Section numbers must be sequential and unique"""

    QUESTION_LIMIT_EXCEEDED = "BIZ_4114"
    """Maximum number of questions exceeded for assessment tier"""

    INVALID_SCORING_WEIGHT = "BIZ_4115"
    """Question weight must be between 0 and 1"""
```

**HTTP Status Mappings:**
- 404: ASSESSMENT_NOT_FOUND
- 400: INVALID_ASSESSMENT_STATUS, INVALID_QUESTION_FORMAT, INVALID_RESPONSE_FORMAT
- 409: ASSESSMENT_ALREADY_PUBLISHED, RESPONSE_ALREADY_SUBMITTED, ASSESSMENT_LOCKED
- 403: ASSESSMENT_NOT_PUBLISHED
- 410: ASSESSMENT_EXPIRED
- 429: ASSESSMENT_LIMIT_EXCEEDED, QUESTION_LIMIT_EXCEEDED

---

### 2. Template-Specific Codes (BIZ 4200-4299)

```python
class TemplateErrorCode(str, Enum):
    """Assessment template error codes"""

    TEMPLATE_NOT_FOUND = "BIZ_4200"
    """Template with specified ID does not exist"""

    TEMPLATE_ALREADY_EXISTS = "BIZ_4201"
    """Template with this name already exists"""

    INVALID_TEMPLATE_FORMAT = "BIZ_4202"
    """Template structure does not match required schema"""

    TEMPLATE_PUBLISH_FAILED = "BIZ_4203"
    """Template failed validation during publish"""

    TEMPLATE_INVALID_VERSION = "BIZ_4204"
    """Template version number is invalid or conflicts with existing"""

    TEMPLATE_HAS_DEPENDENCIES = "BIZ_4205"
    """Cannot delete template used by active assessments"""

    TEMPLATE_VERSION_CONFLICT = "BIZ_4206"
    """Concurrent modifications detected, please reload"""

    INVALID_TEMPLATE_CATEGORY = "BIZ_4207"
    """Template category not recognized"""

    TEMPLATE_IMPORT_FAILED = "BIZ_4208"
    """Failed to import template from file"""

    TEMPLATE_EXPORT_FAILED = "BIZ_4209"
    """Failed to export template to file"""
```

**HTTP Status Mappings:**
- 404: TEMPLATE_NOT_FOUND
- 400: INVALID_TEMPLATE_FORMAT, TEMPLATE_INVALID_VERSION, INVALID_TEMPLATE_CATEGORY
- 409: TEMPLATE_ALREADY_EXISTS, TEMPLATE_VERSION_CONFLICT
- 422: TEMPLATE_PUBLISH_FAILED
- 423: TEMPLATE_HAS_DEPENDENCIES

---

### 3. Team Management Codes (BIZ 4300-4399)

```python
class TeamErrorCode(str, Enum):
    """Team management error codes"""

    TEAM_NOT_FOUND = "BIZ_4300"
    """Team with specified ID does not exist"""

    TEAM_ALREADY_EXISTS = "BIZ_4301"
    """Team with this name already exists in organization"""

    INVALID_TEAM_SIZE = "BIZ_4302"
    """Team must have between 1 and 1000 members"""

    TEAM_ACCESS_DENIED = "BIZ_4303"
    """User does not have permission to access this team"""

    TEAM_LIMIT_EXCEEDED = "BIZ_4304"
    """Organization has reached maximum number of teams for their tier"""

    INVALID_TEAM_ROLE = "BIZ_4305"
    """Invalid team role specified"""

    TEAM_OWNER_REQUIRED = "BIZ_4306"
    """Team must have at least one owner"""

    LAST_OWNER_CANNOT_LEAVE = "BIZ_4307"
    """Last owner cannot leave or be removed from team"""

    TEAM_MEMBER_EXISTS = "BIZ_4308"
    """User is already a member of this team"""

    TEAM_MEMBER_NOT_FOUND = "BIZ_4309"
    """User is not a member of this team"""

    INVITE_ALREADY_SENT = "BIZ_4310"
    """Invitation already sent to this email address"""

    INVITE_EXPIRED = "BIZ_4311"
    """Team invitation has expired (older than 7 days)"""

    INVITE_ALREADY_ACCEPTED = "BIZ_4312"
    """Invitation has already been accepted"""

    TEAM_ANALYSIS_FAILED = "BIZ_4313"
    """Failed to generate team personality analysis"""

    INSUFFICIENT_DATA_FOR_ANALYSIS = "BIZ_4314"
    """Not enough team member responses to generate analysis"""
```

**HTTP Status Mappings:**
- 404: TEAM_NOT_FOUND, TEAM_MEMBER_NOT_FOUND
- 400: INVALID_TEAM_SIZE, INVALID_TEAM_ROLE
- 403: TEAM_ACCESS_DENIED
- 409: TEAM_ALREADY_EXISTS, TEAM_MEMBER_EXISTS, INVITE_ALREADY_SENT, LAST_OWNER_CANNOT_LEAVE
- 429: TEAM_LIMIT_EXCEEDED
- 410: INVITE_EXPIRED

---

### 4. Response Management Codes (BIZ 4400-4499)

```python
class ResponseErrorCode(str, Enum):
    """Assessment response error codes"""

    RESPONSE_NOT_FOUND = "BIZ_4400"
    """Response with specified ID does not exist"""

    INVALID_RESPONSE_DATA = "BIZ_4401"
    """Response data does not match expected schema"""

    RESPONSE_SUBMISSION_FAILED = "BIZ_4402"
    """Failed to submit response due to validation error"""

    RESPONSE_ANALYSIS_FAILED = "BIZ_4403"
    """Failed to analyze response or generate insights"""

    INSUFFICIENT_RESPONSES = "BIZ_4404"
    """Not enough responses to generate aggregate statistics"""

    RESPONSE_TOO_LONG = "BIZ_4405"
    """Response exceeds maximum allowed length"""

    RESPONSE_ALREADY_LOCKED = "BIZ_4406"
    """Response has been locked and cannot be modified"""

    RESPONSE_TIMEOUT = "BIZ_4407"
    """Response submission timed out"""

    INVALID_SCORE_VALUE = "BIZ_4408"
    """Score value outside valid range for question type"""

    RESPONSE_EXPORT_FAILED = "BIZ_4409"
    """Failed to export response data"""

    RESPONSE_IMPORT_FAILED = "BIZ_4410"
    """Failed to import response data"""
```

**HTTP Status Mappings:**
- 404: RESPONSE_NOT_FOUND
- 400: INVALID_RESPONSE_DATA, INVALID_SCORE_VALUE, RESPONSE_TOO_LONG
- 422: RESPONSE_SUBMISSION_FAILED, RESPONSE_ANALYSIS_FAILED
- 423: RESPONSE_ALREADY_LOCKED
- 408: RESPONSE_TIMEOUT
- 500: INSUFFICIENT_RESPONSES

---

### 5. Security & Compliance Codes (AUTH 1100-1199)

```python
class SecurityErrorCode(str, Enum):
    """Security and compliance error codes"""

    SECURITY_POLICY_VIOLATION = "AUTH_1100"
    """Action violates security policy"""

    SUSPICIOUS_ACTIVITY_DETECTED = "AUTH_1101"
    """Account flagged for suspicious activity"""

    ACCOUNT_LOCKED = "AUTH_1102"
    """Account has been locked due to security concerns"""

    INVALID_SESSION = "AUTH_1103"
    """Session is invalid or has been tampered with"""

    SESSION_EXPIRED = "AUTH_1104"
    """Session has expired (user must login again)"""

    IP_BLOCKED = "AUTH_1105"
    """IP address has been blocked due to repeated violations"""

    RATE_LIMIT_EXCEEDED = "AUTH_1106"
    """Too many requests from this account or IP"""

    INVALID_CSRF_TOKEN = "AUTH_1107"
    """CSRF token is invalid or missing"""

    MFA_REQUIRED = "AUTH_1108"
    """Multi-factor authentication must be enabled"""

    INVALID_MFA_CODE = "AUTH_1109"
    """MFA code is incorrect or expired"""

    MFA_RATE_LIMITED = "AUTH_1110"
    """Too many incorrect MFA attempts"""

    PASSWORD_COMPROMISED = "AUTH_1111"
    """Password found in data breach (must be changed)"""

    WEAK_PASSWORD = "AUTH_1112"
    """Password does not meet security requirements"""

    PASSWORD_RECENTLY_USED = "AUTH_1113"
    """Password was used recently (must be unique)"""

    EMAIL_NOT_VERIFIED = "AUTH_1114"
    """Email address must be verified before this action"""

    ACCOUNT_SUSPENDED = "AUTH_1115"
    """Account has been suspended by administrator"""

    EMAIL_ALREADY_VERIFIED = "AUTH_1116"
    """Email has already been verified"""

    INVALID_VERIFICATION_TOKEN = "AUTH_1117"
    """Email verification token is invalid or expired"""
```

**HTTP Status Mappings:**
- 401: INVALID_SESSION, SESSION_EXPIRED, INVALID_MFA_CODE, MFA_REQUIRED
- 403: ACCOUNT_LOCKED, IP_BLOCKED, ACCOUNT_SUSPENDED, EMAIL_NOT_VERIFIED
- 429: RATE_LIMIT_EXCEEDED, MFA_RATE_LIMITED
- 400: INVALID_CSRF_TOKEN, WEAK_PASSWORD, PASSWORD_RECENTLY_USED, PASSWORD_COMPROMISED, INVALID_VERIFICATION_TOKEN
- 409: EMAIL_ALREADY_VERIFIED
- 423: SECURITY_POLICY_VIOLATION

---

### 6. Billing & Subscription Codes (BIZ 4500-4599)

```python
class BillingErrorCode(str, Enum):
    """Billing and subscription error codes"""

    SUBSCRIPTION_NOT_FOUND = "BIZ_4500"
    """Subscription does not exist for this organization"""

    SUBSCRIPTION_EXPIRED = "BIZ_4501"
    """Subscription has expired"""

    SUBSCRIPTION_CANCELLED = "BIZ_4502"
    """Subscription has been cancelled"""

    PAYMENT_METHOD_REQUIRED = "BIZ_4503"
    """Payment method must be added to continue"""

    PAYMENT_FAILED = "BIZ_4504"
    """Payment transaction failed"""

    PAYMENT_DECLINED = "BIZ_4505"
    """Payment was declined by payment processor"""

    INSUFFICIENT_CREDITS = "BIZ_4506"
    """Not enough credits for this operation"""

    PLAN_LIMIT_EXCEEDED = "BIZ_4507"
    """Operation exceeds current plan limits"""

    UPGRADE_REQUIRED = "BIZ_4508"
    """Feature requires higher subscription tier"""

    INVOICE_NOT_FOUND = "BIZ_4509"
    """Invoice with specified ID does not exist"""

    INVOICE_OVERDUE = "BIZ_4510"
    """Invoice payment is overdue"""

    TRIAL_EXPIRED = "BIZ_4511"
    """Trial period has expired"""

    ALREADY_SUBSCRIBED = "BIZ_4512"
    """Organization already has an active subscription"""

    COUPON_INVALID = "BIZ_4513"
    """Coupon code is invalid or expired"""

    COUPON_USAGE_LIMIT = "BIZ_4514"
    """Coupon has reached maximum usage"""

    REFUND_PERIOD_EXPIRED = "BIZ_4515"
    """Refund period has passed"""
```

**HTTP Status Mappings:**
- 404: SUBSCRIPTION_NOT_FOUND, INVOICE_NOT_FOUND
- 402: PAYMENT_METHOD_REQUIRED, PAYMENT_FAILED, PAYMENT_DECLINED, UPGRADE_REQUIRED
- 403: PLAN_LIMIT_EXCEEDED, TRIAL_EXPIRED
- 409: ALREADY_SUBSCRIBED
- 400: COUPON_INVALID, COUPON_USAGE_LIMIT

---

### 7. Clinical Assessment Codes (BIZ 4600-4699)

```python
class ClinicalErrorCode(str, Enum):
    """Clinical assessment error codes"""

    CLINICAL_CONSENT_REQUIRED = "BIZ_4600"
    """User must consent before taking clinical assessments"""

    CLINICAL_ACCESS_DENIED = "BIZ_4601"
    """User does not have access to clinical features"""

    CLINICAL_LICENSE_REQUIRED = "BIZ_4602"
    """Clinical features require professional license"""

    CRISIS_RISK_DETECTED = "BIZ_4603"
    """Assessment indicates potential crisis risk"""

    CRISIS_ALERT_FAILED = "BIZ_4604"
    """Failed to send crisis alert"""

    SAFETY_PLAN_REQUIRED = "BIZ_4605"
    """Safety plan must be created before proceeding"""

    CLINICAL_DATA_ACCESS_DENIED = "BIZ_4606"
    """Only licensed professionals can access clinical data"""

    INVALID_CLINICAL_SCORE = "BIZ_4607"
    """Clinical score outside valid range"""

    WELLNESS_PLAN_INCOMPLETE = "BIZ_4608"
    """Wellness plan has missing required sections"""

    TREND_ANALYSIS_FAILED = "BIZ_4609"
    """Failed to analyze mental health trends"""

    INSUFFICIENT_CLINICAL_DATA = "BIZ_4610"
    """Not enough data points for clinical analysis"""
```

**HTTP Status Mappings:**
- 403: CLINICAL_CONSENT_REQUIRED, CLINICAL_ACCESS_DENIED, CLINICAL_LICENSE_REQUIRED, CLINICAL_DATA_ACCESS_DENIED
- 400: INVALID_CLINICAL_SCORE, WELLNESS_PLAN_INCOMPLETE
- 422: CRISIS_ALERT_FAILED, TREND_ANALYSIS_FAILED
- 500: INSUFFICIENT_CLINICAL_DATA
- 423: SAFETY_PLAN_REQUIRED
- 409: CRISIS_RISK_DETECTED

---

## Enhanced Error Response Format

### Standard Error Response Structure

```json
{
  "error": true,
  "error_code": "AUTH_1002",
  "message": "Invalid credentials provided",
  "status_code": 401,
  "details": {
    "field": "email",
    "attempts_remaining": 3,
    "lockout_in_seconds": 900
  },
  "timestamp": "2026-01-13T10:30:00.000Z",
  "request_id": "req_abc123",
  "retry_after": 900,
  "documentation_url": "https://docs.psychsync.com/api/errors/AUTH_1002"
}
```

### Field Definitions

- **error**: Boolean flag indicating error response
- **error_code**: Machine-readable error code for client handling
- **message**: Human-readable error description
- **status_code**: HTTP status code
- **details**: Additional context (field-specific errors, retry info, etc.)
- **timestamp**: ISO 8601 timestamp of error
- **request_id**: Unique request ID for debugging
- **retry_after**: Seconds to wait before retry (if applicable)
- **documentation_url**: Link to error documentation

---

## Implementation Guide

### Step 1: Update ErrorCode Enum

**File:** `app/core/exceptions.py`

```python
from enum import Enum

class ErrorCode(str, Enum):
    """Standardized error codes across the platform"""

    # Existing codes (keep these)
    INVALID_CREDENTIALS = "AUTH_1002"
    RECORD_NOT_FOUND = "VAL_2005"
    # ... existing codes ...

    # Add new assessment codes
    ASSESSMENT_NOT_FOUND = "BIZ_4100"
    ASSESSMENT_ALREADY_PUBLISHED = "BIZ_4101"
    ASSESSMENT_NOT_PUBLISHED = "BIZ_4102"
    INVALID_ASSESSMENT_STATUS = "BIZ_4103"
    ASSESSMENT_EXPIRED = "BIZ_4104"
    ASSESSMENT_LIMIT_EXCEEDED = "BIZ_4105"
    INVALID_QUESTION_FORMAT = "BIZ_4106"
    INVALID_RESPONSE_FORMAT = "BIZ_4107"
    RESPONSE_ALREADY_SUBMITTED = "BIZ_4108"
    ASSESSMENT_INCOMPLETE = "BIZ_4109"

    # Add new team codes
    TEAM_NOT_FOUND = "BIZ_4300"
    TEAM_ALREADY_EXISTS = "BIZ_4301"
    INVALID_TEAM_SIZE = "BIZ_4302"
    TEAM_ACCESS_DENIED = "BIZ_4303"
    TEAM_LIMIT_EXCEEDED = "BIZ_4304"
    INVALID_TEAM_ROLE = "BIZ_4305"

    # Add new security codes
    ACCOUNT_LOCKED = "AUTH_1102"
    SESSION_EXPIRED = "AUTH_1104"
    RATE_LIMIT_EXCEEDED = "AUTH_1106"
    MFA_REQUIRED = "AUTH_1108"
    PASSWORD_COMPROMISED = "AUTH_1111"
    WEAK_PASSWORD = "AUTH_1112"

    # Add new billing codes
    SUBSCRIPTION_EXPIRED = "BIZ_4501"
    PAYMENT_FAILED = "BIZ_4504"
    PLAN_LIMIT_EXCEEDED = "BIZ_4507"
    UPGRADE_REQUIRED = "BIZ_4508"
```

---

### Step 2: Create Custom Exception Classes

**File:** `app/core/exceptions.py`

```python
class PsychSyncException(Exception):
    """Base exception for all PsychSync errors"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = 500,
        details: dict | None = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class AssessmentNotFoundException(PsychSyncException):
    """Raised when assessment is not found"""

    def __init__(self, assessment_id: str | UUID):
        super().__init__(
            message=f"Assessment {assessment_id} not found",
            error_code=ErrorCode.ASSESSMENT_NOT_FOUND,
            status_code=404,
            details={"assessment_id": str(assessment_id)}
        )

class AssessmentExpiredException(PsychSyncException):
    """Raised when attempting to access expired assessment"""

    def __init__(self, assessment_id: str | UUID, expiry_date: datetime):
        super().__init__(
            message=f"Assessment expired on {expiry_date.isoformat()}",
            error_code=ErrorCode.ASSESSMENT_EXPIRED,
            status_code=410,
            details={
                "assessment_id": str(assessment_id),
                "expiry_date": expiry_date.isoformat()
            }
        )

class TeamAccessDeniedException(PsychSyncException):
    """Raised when user lacks team access"""

    def __init__(self, team_id: str | UUID, user_id: str | UUID):
        super().__init__(
            message="You do not have permission to access this team",
            error_code=ErrorCode.TEAM_ACCESS_DENIED,
            status_code=403,
            details={
                "team_id": str(team_id),
                "user_id": str(user_id)
            }
        )

class WeakPasswordException(PsychSyncException):
    """Raised when password doesn't meet security requirements"""

    def __init__(self, requirements: dict):
        super().__init__(
            message="Password does not meet security requirements",
            error_code=ErrorCode.WEAK_PASSWORD,
            status_code=400,
            details={"requirements": requirements}
        )

class RateLimitExceededException(PsychSyncException):
    """Raised when rate limit is exceeded"""

    def __init__(self, retry_after: int, limit: int):
        super().__init__(
            message=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details={
                "retry_after": retry_after,
                "limit": limit
            }
        )
```

---

### Step 3: Update API Endpoints

**Before (Generic Error):**
```python
# app/api/v1/endpoints/assessments.py
@router.get("/{assessment_id}")
async def get_assessment(assessment_id: str, db: AsyncSession = Depends(get_db)):
    assessment = await assessment_service.get_by_id(db, assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found"
        )
    return assessment
```

**After (Structured Error):**
```python
# app/api/v1/endpoints/assessments.py
from app.core.exceptions import AssessmentNotFoundException

@router.get("/{assessment_id}")
async def get_assessment(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        assessment = await assessment_service.get_by_id(
            db,
            UUID(assessment_id),
            current_user.id
        )
        if not assessment:
            raise AssessmentNotFoundException(assessment_id)
        return assessment
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid assessment ID format"
        )
```

---

### Step 4: Create Error Handler Middleware

**File:** `app/middleware/error_handling.py`

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import PsychSyncException

async def psychsync_exception_handler(
    request: Request,
    exc: PsychSyncException
) -> JSONResponse:
    """Handle PsychSync custom exceptions"""

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.error_code.value,
            "message": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else None,
            "documentation_url": f"https://docs.psychsync.com/api/errors/{exc.error_code.value}"
        }
    )

async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """Handle standard HTTP exceptions with error codes"""

    # Map common HTTP exceptions to error codes
    error_code_map = {
        401: ErrorCode.INVALID_CREDENTIALS,
        403: ErrorCode.INVALID_PERMISSIONS,
        404: ErrorCode.RECORD_NOT_FOUND,
        422: ErrorCode.VALIDATION_ERROR,
    }

    error_code = error_code_map.get(exc.status_code, ErrorCode.GENERIC_ERROR)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": error_code.value,
            "message": str(exc.detail),
            "status_code": exc.status_code,
            "details": {},
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else None,
        }
    )
```

---

### Step 5: Register Error Handlers

**File:** `app/main.py`

```python
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import PsychSyncException
from app.middleware.error_handling import (
    psychsync_exception_handler,
    http_exception_handler,
    validation_exception_handler
)

app = FastAPI()

# Register custom exception handlers
app.add_exception_handler(PsychSyncException, psychsync_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
```

---

## Error Code Quick Reference

### Authentication Errors (AUTH)

| Error Code | HTTP | Description |
|------------|------|-------------|
| AUTH_1000 | 401 | Not authenticated |
| AUTH_1002 | 401 | Invalid credentials |
| AUTH_1003 | 403 | Insufficient permissions |
| AUTH_1102 | 403 | Account locked |
| AUTH_1104 | 401 | Session expired |
| AUTH_1106 | 429 | Rate limit exceeded |
| AUTH_1108 | 401 | MFA required |
| AUTH_1111 | 400 | Password compromised |
| AUTH_1112 | 400 | Weak password |
| AUTH_1114 | 403 | Email not verified |

### Validation Errors (VAL)

| Error Code | HTTP | Description |
|------------|------|-------------|
| VAL_2001 | 400 | Missing required field |
| VAL_2002 | 400 | Invalid email format |
| VAL_2003 | 400 | Invalid UUID format |
| VAL_2004 | 400 | Invalid date format |
| VAL_2005 | 404 | Record not found |

### Business Logic Errors (BIZ)

| Error Code | HTTP | Description |
|------------|------|-------------|
| BIZ_4100 | 404 | Assessment not found |
| BIZ_4104 | 410 | Assessment expired |
| BIZ_4105 | 429 | Assessment limit exceeded |
| BIZ_4200 | 404 | Template not found |
| BIZ_4300 | 404 | Team not found |
| BIZ_4303 | 403 | Team access denied |
| BIZ_4400 | 404 | Response not found |
| BIZ_4501 | 403 | Subscription expired |
| BIZ_4504 | 402 | Payment failed |
| BIZ_4507 | 403 | Plan limit exceeded |
| BIZ_4508 | 402 | Upgrade required |

---

## Testing Error Codes

### Unit Test Example

```python
import pytest
from app.core.exceptions import AssessmentNotFoundException, ErrorCode

def test_assessment_not_found():
    """Test AssessmentNotFoundException"""

    exc = AssessmentNotFoundException("123e4567-e89b-12d3-a456-426614174000")

    assert exc.error_code == ErrorCode.ASSESSMENT_NOT_FOUND
    assert exc.status_code == 404
    assert exc.details["assessment_id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert "Assessment 123e4567-e89b-12d3-a456-426614174000 not found" in exc.message
```

### Integration Test Example

```python
import pytest
from fastapi.testclient import TestClient

def test_get_assessment_not_found(client: TestClient):
    """Test GET /assessments/{id} with invalid ID"""

    response = client.get("/api/v1/assessments/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"] == True
    assert response.json()["error_code"] == "BIZ_4100"
    assert "Assessment" in response.json()["message"]
    assert "timestamp" in response.json()
```

---

## Client-Side Error Handling

### JavaScript/TypeScript Example

```typescript
interface ErrorResponse {
  error: boolean;
  error_code: string;
  message: string;
  status_code: number;
  details: Record<string, any>;
  timestamp: string;
  request_id: string;
}

async function handleApiCall() {
  try {
    const response = await fetch('/api/v1/assessments/123', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) {
      const error: ErrorResponse = await response.json();

      // Handle specific error codes
      switch (error.error_code) {
        case 'BIZ_4100': // Assessment not found
          showNotification('Assessment not found', 'error');
          break;

        case 'AUTH_1104': // Session expired
          redirectToLogin();
          break;

        case 'AUTH_1106': // Rate limit exceeded
          const retryAfter = error.details.retry_after;
          showNotification(`Try again in ${retryAfter} seconds`, 'warning');
          break;

        case 'BIZ_4303': // Team access denied
          showNotification('You do not have permission to access this team', 'error');
          break;

        default:
          showNotification(error.message, 'error');
      }
    }
  } catch (err) {
    console.error('Unexpected error:', err);
  }
}
```

---

## Documentation Strategy

### Auto-Generate Error Documentation

```bash
# Script to extract error codes from codebase
# scripts/generate_error_docs.py

import re
from app.core.exceptions import ErrorCode

def generate_error_documentation():
    """Generate Markdown documentation from ErrorCode enum"""

    with open('docs/api/errors.md', 'w') as f:
        f.write('# API Error Codes\n\n')

        for code in ErrorCode:
            f.write(f'## {code.value}\n\n')
            f.write(f'**Description:** {code.value}\n\n')
            f.write(f'**Category:** {code.value.split("_")[0]}\n\n')
            f.write(f'**Documentation:** https://docs.psychsync.com/api/errors/{code.value}\n\n')
            f.write('---\n\n')

if __name__ == '__main__':
    generate_error_documentation()
```

---

## Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Add missing error codes to ErrorCode enum
- [ ] Create custom exception classes for common errors
- [ ] Set up error handler middleware
- [ ] Write unit tests for new exceptions

### Phase 2: Migration (Weeks 2-3)
- [ ] Replace generic 404s with specific error codes
- [ ] Replace generic 403s with specific error codes
- [ ] Replace generic 400s with validation error codes
- [ ] Update all API endpoints to use custom exceptions

### Phase 3: Enhancement (Week 4)
- [ ] Add detailed error context to responses
- [ ] Implement retry_after headers for rate limits
- [ ] Add request_id tracking
- [ ] Create error documentation

### Phase 4: Testing & Documentation (Week 5)
- [ ] Write integration tests for error scenarios
- [ ] Generate error code documentation
- [ ] Create client-side error handling guide
- [ ] Team training on error handling

---

## Conclusion

Implementing a comprehensive error code system will:
1. **Improve debugging** (clear error identification)
2. **Enhance client error handling** (machine-readable codes)
3. **Increase security** (no information leakage from generic errors)
4. **Better user experience** (actionable error messages)
5. **Simplify maintenance** (consistent error handling)

**Estimated Effort:** 5 weeks
**Impact:** High (critical for production readiness)
**Priority:** High (blocks beta launch)
