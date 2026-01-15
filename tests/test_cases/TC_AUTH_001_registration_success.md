# Test Case: TC_AUTH_001 - User Registration Success

**Test ID**: PSYNC-AUTH-001
**Priority**: P0 (Critical)
**Automated**: ✅ Yes
**Test Type**: Functional | Smoke
**Estimated Duration**: 2 seconds
**Tier**: Tier 1 (Smoke Test - runs on every PR)

---

## Description

Verify that a new user can successfully register with valid credentials, receive a verification email, and have their account created in the system.

---

## User Story

As a new user, I want to register an account with email verification so that I can access the PsychSync platform securely.

---

## Acceptance Criteria Reference

See `QA_ACCEPTANCE_CRITERIA.md` Section 1.1 - User Registration

---

## Pre-Conditions

### System State
- [x] Application server is running
- [x] PostgreSQL database is accessible
- [x] Redis cache service is operational
- [x] Email service is configured and operational
- [x] Test database is clean (no duplicate emails)

### Test Data
- **Email**: `newuser@psychsync.test` (not previously registered)
- **Password**: `SecurePass123!`
- **Full Name**: `Test New User`
- **Password Requirements Met**:
  - Minimum 8 characters: ✅ (16 chars)
  - Contains uppercase: ✅ ('S')
  - Contains lowercase: ✅ ('ecure')
  - Contains number: ✅ ('123')
  - Contains special character: ✅ ('!')
  - Not in common password list: ✅

---

## Test Steps

### Step 1: Navigate to Registration Endpoint
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "newuser@psychsync.test",
  "password": "SecurePass123!",
  "full_name": "Test New User"
}
```

### Step 2: Submit Registration Request
Send POST request with valid registration data

### Step 3: Verify Response
Receive and validate HTTP response

### Step 4: Check Database
Query database to confirm user record was created

### Step 5: Verify Email Sent
Check email service logs to confirm verification email was sent

---

## Expected Results

### HTTP Response
```json
{
  "success": true,
  "status": "ok",
  "message": "Registration successful. Please check your email to verify your account.",
  "data": {
    "user_id": "uuid-here",
    "email": "newuser@psychsync.test",
    "full_name": "Test New User",
    "is_active": true,
    "is_verified": false,
    "created_at": "2025-01-10T14:30:00Z"
  }
}
```

### Response Criteria
- [x] **Status Code**: 201 CREATED
- [x] **Response Time**: < 500ms (p95)
- [x] **Success Field**: `true`
- [x] **User ID**: Valid UUID format
- [x] **Email**: Matches request
- [x] **is_verified**: `false` (account pending email verification)

### Database Verification
```sql
SELECT * FROM users WHERE email = 'newuser@psychsync.test';
```

Expected Record:
```json
{
  "id": "uuid-here",
  "email": "newuser@psychsync.test",
  "full_name": "Test New User",
  "hashed_password": "$2b$12$...",  // bcrypt hash
  "is_active": true,
  "is_verified": false,
  "role": "USER",
  "created_at": "2025-01-10T14:30:00Z",
  "updated_at": "2025-01-10T14:30:00Z"
}
```

### Email Verification
Expected email sent to `newuser@psychsync.test`:
- **Subject**: "Verify your PsychSync account"
- **Content**: Contains verification link with token
- **Token Expiry**: 24 hours from creation

---

## Post-Conditions

### Database State
- [x] User record exists in `users` table
- [x] User has `is_verified = false`
- [x] User has `is_active = true`
- [x] User has default role: `USER`
- [x] Password is bcrypt hashed (not plaintext)
- [x] Verification token generated and stored

### Audit Log
- [x] Registration event logged in `audit_logs` table
- [x] Event type: `USER_REGISTRATION`
- [x] Timestamp recorded
- [x] IP address logged (if available)

### Cache State
- [x] No active sessions (user not logged in yet)
- [x] Rate limit counter incremented for email/IP

---

## Edge Cases Tested

This test case validates the happy path. Related edge case tests:

- **TC_AUTH_002**: Registration with duplicate email
- **TC_AUTH_003**: Registration with weak password
- **TC_AUTH_004**: Registration with invalid email format
- **TC_AUTH_005**: Registration with SQL injection payload
- **TC_AUTH_006**: Registration with XSS payload

---

## Error Handling Scenarios

### Expected Behavior for Invalid Input

| Scenario | Expected Status Code | Expected Error Message |
|----------|---------------------|----------------------|
| Duplicate email | 409 CONFLICT | "Email already exists" |
| Weak password | 400 BAD_REQUEST | "Password does not meet requirements" |
| Invalid email format | 400 BAD_REQUEST | "Invalid email format" |
| Missing required field | 400 BAD_REQUEST | "Missing required field: {field_name}" |
| Rate limit exceeded | 429 TOO_MANY_REQUESTS | "Too many registration attempts. Please try again later." |

---

## Test Automation Script

### File: `tests/api/test_auth.py`

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.user import User
from app.core.security import verify_password

@pytest.mark.smoke
@pytest.mark.auth
@pytest.mark.asyncio
async def test_user_registration_success(
    async_client: AsyncClient,
    db_session: AsyncSession
):
    """
    Test Case: TC_AUTH_001 - User Registration Success

    Verify that a new user can successfully register with valid credentials.
    """
    # Arrange
    registration_data = {
        "email": "newuser@psychsync.test",
        "password": "SecurePass123!",
        "full_name": "Test New User"
    }

    # Act
    response = await async_client.post(
        "/api/v1/auth/register",
        json=registration_data
    )

    # Assert - HTTP Response
    assert response.status_code == 201
    data = response.json()

    assert data["success"] is True
    assert data["status"] == "ok"
    assert "user_id" in data["data"]
    assert data["data"]["email"] == registration_data["email"]
    assert data["data"]["full_name"] == registration_data["full_name"]
    assert data["data"]["is_verified"] is False
    assert data["data"]["is_active"] is True

    # Assert - Database Verification
    result = await db_session.execute(
        select(User).where(User.email == registration_data["email"])
    )
    user = result.scalar_one_or_none()

    assert user is not None
    assert user.email == registration_data["email"]
    assert user.full_name == registration_data["full_name"]
    assert user.is_verified is False
    assert user.is_active is True
    assert user.role == "USER"

    # Assert - Password Hashing
    assert user.hashed_password != registration_data["password"]
    assert verify_password(
        registration_data["password"],
        user.hashed_password
    ) is True

    # Assert - Response Time (Performance)
    assert response.elapsed.total_seconds() < 0.5  # < 500ms

    # Assert - Audit Log (if audit logging is enabled)
    # audit_log = await get_audit_log(db_session, user.id, "USER_REGISTRATION")
    # assert audit_log is not None
```

---

## Test Data Cleanup

### Cleanup Procedure
```python
@pytest.fixture(autouse=True)
async def cleanup_test_user(db_session: AsyncSession):
    """Clean up test user after test"""
    yield
    # Delete test user
    await db_session.execute(
        delete(User).where(User.email == "newuser@psychsync.test")
    )
    await db_session.commit()
```

---

## Related Test Cases

- **TC_AUTH_010**: Email verification flow
- **TC_AUTH_011**: Login after registration
- **TC_AUTH_012**: Resend verification email
- **TC_AUTH_020**: Registration rate limiting

---

## History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-01-10 | Initial test case creation | QA Team |

---

## Notes

- This test runs on every PR (smoke test)
- Must complete in < 5 seconds
- Test data uses `@psychsync.test` domain to avoid collisions
- Cleanup is critical to prevent test pollution
