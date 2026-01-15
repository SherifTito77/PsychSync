# Structured Exceptions Refactoring Guide

## Overview

This guide demonstrates how to replace generic `HTTPException` with PsychSync's structured exception system. The structured exceptions provide better error context, standardized error codes, and improved debugging capabilities.

## Why Use Structured Exceptions?

### Benefits Over HTTPException

1. **Automatic Error Context**: Each exception carries relevant details (resource type, identifiers, etc.)
2. **Standardized Error Codes**: Clients receive actionable codes like `AUTH_1005` instead of generic "Not Found"
3. **Structured Logging**: All exceptions log with consistent format including timestamps, error codes, and details
4. **Better API Responses**: Predictable response format with error metadata
5. **Easier Testing**: Specific exception types make test assertions more reliable

### Example Comparison

**Before (HTTPException):**
```python
if not team:
    raise HTTPException(
        status_code=404,
        detail=f"Team not found with ID: {team_id}"
    )
```

**After (Structured Exception):**
```python
if not team:
    raise TeamNotFoundError(
        team_id=team_id,
        details={
            "searched_id": team_id,
            "user_id": str(current_user.id),
            "search_type": "uuid_or_prefix",
        },
    )
```

## Available Exception Types

### Authentication & Authorization (401, 403)
- `UnauthorizedError` - User not authenticated
- `ForbiddenError` - User lacks permission
- `InvalidCredentialsError` - Invalid email/password
- `UserNotFoundError` - User account doesn't exist
- `UserAlreadyExistsError` - Duplicate user registration
- `UserInactiveError` - Account not active
- `AccountLockedError` - Security lockout
- `SessionExpiredError` - Token/session expired

### Validation (400, 422)
- `InvalidInputError` - General input validation failure
- `MissingFieldError` - Required field omitted
- `InvalidEmailError` - Email format validation
- `InvalidPasswordError` - Password doesn't meet requirements
- `WeakPasswordError` - Password security policy violation

### Database (404, 409, 500)
- `RecordNotFoundError` - Generic record not found
- `DuplicateRecordError` - Unique constraint violation
- `DatabaseError` - General database errors

### Business Logic (400, 402, 403, 429)
- `InvalidOperationError` - Business rule violation
- `ResourceLimitExceededError` - Quota/limit reached
- `UpgradeRequiredError` - Feature needs higher tier

### Team-Specific (403, 404, 429)
- `TeamNotFoundError` - Team doesn't exist
- `TeamAccessDeniedError` - No permission to access team
- `TeamLimitExceededError` - Organization team quota exceeded

### Assessment-Specific (404, 409, 423, 429)
- `AssessmentNotFoundError` - Assessment doesn't exist
- `AssessmentExpiredError` - Assessment past deadline
- `AssessmentLockedError` - Assessment frozen for editing
- `ResponseAlreadySubmittedError` - Duplicate response

### AI/ML Processing (500, 504)
- `AIProcessingError` - General AI processing failure
- `ModelNotFoundError` - AI model missing
- `ProcessingTimeoutError` - Operation exceeded timeout

## Refactoring Patterns

### Pattern 1: Resource Not Found (404)

**Before:**
```python
from fastapi import HTTPException, status

if not team:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Team not found with ID: {team_id}"
    )
```

**After:**
```python
from app.core.exceptions import TeamNotFoundError

if not team:
    raise TeamNotFoundError(
        team_id=team_id,
        details={
            "searched_id": team_id,
            "user_id": str(current_user.id),
            "search_type": "uuid_or_prefix",
        },
    )
```

### Pattern 2: Invalid Input (400)

**Before:**
```python
if not team_id or team_id.strip() == "":
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid team ID: {team_id}"
    )
```

**After:**
```python
from app.core.exceptions import InvalidInputError

if not team_id or team_id.strip() == "":
    raise InvalidInputError(
        message=f"Invalid team ID: {team_id}",
        details={"team_id": team_id, "reason": "empty_or_invalid"},
    )
```

### Pattern 3: Access Denied (403)

**Before:**
```python
if not current_user.is_admin:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required"
    )
```

**After:**
```python
from app.core.exceptions import ForbiddenError

if not current_user.is_admin:
    raise ForbiddenError(
        message="Admin access required for this operation",
        details={
            "user_id": str(current_user.id),
            "user_role": current_user.role,
            "required_role": "admin",
        },
    )
```

### Pattern 4: Generic Errors (500)

**Before:**
```python
except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to create team: {str(e)}"
    ) from e
```

**After:**
```python
from app.core.exceptions import PsychSyncException

except Exception as e:
    raise PsychSyncException(
        message="Failed to create team",
        details={
            "original_error": str(e),
            "user_id": str(current_user.id),
        },
        cause=e,
    ) from e
```

### Pattern 5: Handling Multiple Exception Types

**Best Practice:**
```python
try:
    # Business logic here
    pass

except ValueError as e:
    # Re-raise as structured validation error
    raise InvalidInputError(
        message=f"Invalid data: {e!s}",
        details={"field": "team_data", "error": str(e)},
    ) from e

except (InvalidInputError, TeamNotFoundError, TeamAccessDeniedError):
    # Re-raise structured exceptions as-is
    raise

except Exception as e:
    # Catch-all for unexpected errors
    raise PsychSyncException(
        message="Operation failed",
        details={"original_error": str(e)},
        cause=e,
    ) from e
```

## Complete Example: Refactored Endpoint

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user
from app.core.database import get_async_db
from app.core.exceptions import (
    InvalidInputError,
    PsychSyncException,
    TeamAccessDeniedError,
    TeamNotFoundError,
)
from app.db.models.user import User

@router.get("/{team_id}")
async def get_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a specific team by ID

    Raises:
        InvalidInputError: If team_id is invalid
        TeamNotFoundError: If team doesn't exist
        TeamAccessDeniedError: If user lacks permission
        PsychSyncException: For unexpected errors
    """
    try:
        # Validate input
        if not team_id or team_id.strip() == "":
            raise InvalidInputError(
                message=f"Invalid team ID: {team_id}",
                details={"team_id": team_id, "reason": "empty"},
            )

        # Business logic
        team = await fetch_team(db, team_id)

        if not team:
            raise TeamNotFoundError(
                team_id=team_id,
                details={
                    "searched_id": team_id,
                    "user_id": str(current_user.id),
                },
            )

        # Check permissions
        if not can_access_team(current_user, team):
            raise TeamAccessDeniedError(
                team_id=team_id,
                user_id=str(current_user.id),
                details={"team_name": team.name},
            )

        return team

    except (InvalidInputError, TeamNotFoundError, TeamAccessDeniedError):
        # Re-raise structured exceptions as-is
        raise

    except Exception as e:
        raise PsychSyncException(
            message="Failed to retrieve team",
            details={
                "team_id": team_id,
                "user_id": str(current_user.id),
                "original_error": str(e),
            },
            cause=e,
        ) from e
```

## Error Response Format

Structured exceptions produce standardized JSON responses:

```json
{
  "error": true,
  "error_code": "BIZ_4300",
  "message": "Team abc123 not found",
  "details": {
    "team_id": "abc123",
    "user_id": "uuid-here",
    "search_type": "uuid_or_prefix"
  },
  "timestamp": "2025-01-13T10:30:45.123456",
  "status_code": 404
}
```

### Error Code Reference

- `AUTH_1XXX` - Authentication & Authorization
- `VAL_2XXX` - Validation errors
- `DB_3XXX` - Database errors
- `BIZ_4XXX` - Business logic errors
- `EXT_5XXX` - External service errors
- `SYS_6XXX` - System errors
- `AI_7XXX` - AI/ML processing errors

See `app/core/exceptions.py` for complete error code definitions.

## Testing Structured Exceptions

### Unit Tests

```python
import pytest
from app.core.exceptions import TeamNotFoundError
from app.api.v1.endpoints.teams import get_team

async def test_get_team_not_found(db_session):
    with pytest.raises(TeamNotFoundError) as exc_info:
        await get_team("non-existent-id", db_session, test_user)

    # Assert specific exception properties
    assert exc_info.value.error_code.value == "BIZ_4300"
    assert "non-existent-id" in exc_info.value.details["team_id"]
    assert exc_info.value.status_code == 404
```

### Integration Tests

```python
async def test_get_team_returns_404(client):
    response = await client.get("/api/v1/teams/non-existent")

    assert response.status_code == 404
    data = response.json()
    assert data["error"] == True
    assert data["error_code"] == "BIZ_4300"
    assert "team_id" in data["details"]
```

## Migration Checklist

For each endpoint file:

1. ✅ Update imports to include structured exceptions
2. ✅ Remove `HTTPException` from imports (keep `status` if needed)
3. ✅ Replace `raise HTTPException(...)` with appropriate structured exceptions
4. ✅ Add helpful details to exception constructors
5. ✅ Update docstrings to document raised exceptions
6. ✅ Ensure exception chaining with `from e`
7. ✅ Group re-raises of structured exceptions
8. ✅ Test endpoints with new exception handling

## Files Refactored

- ✅ `app/core/error_handling.py` - Updated middleware to support structured exceptions
- ✅ `app/api/v1/endpoints/teams.py` - Refactored 3 endpoints (create_team, get_team, get_team_personality_composition)

## Files Requiring Refactoring

### High Priority (Core Endpoints)
- `app/api/v1/endpoints/auth.py` - Authentication endpoints
- `app/api/v1/endpoints/users.py` - User management
- `app/api/v1/endpoints/assessments.py` - Assessment CRUD
- `app/api/v1/endpoints/responses.py` - Response submission

### Medium Priority (Business Logic)
- `app/api/v1/endpoints/analytics.py` - Analytics endpoints
- `app/api/v1/endpoints/reports.py` - Report generation
- `app/api/v1/endpoints/admin.py` - Admin operations

### Lower Priority (Feature Endpoints)
- `app/api/v1/endpoints/hris_connector.py` - HRIS integration
- `app/api/v1/endpoints/slack.py` - Slack integration
- `app/api/v1/endpoints/nlp_routes.py` - NLP features
- All other endpoint files (90+ remaining)

## Best Practices

### DO ✅
- Always include relevant details in exception constructors
- Use specific exception types when available
- Document raised exceptions in docstrings
- Chain exceptions with `from e` for debugging
- Group structured exception re-raises
- Log important context in exception details

### DON'T ❌
- Don't use generic `HTTPException` for business logic errors
- Don't include sensitive data in exception details
- Don't swallow exceptions without re-raising
- Don't forget to update imports
- Don't use bare `except:` clauses
- Don't create duplicate exception classes

## Next Steps

1. **Review refactored examples** in `teams.py`
2. **Apply patterns** to your assigned endpoints
3. **Run tests** to ensure proper error handling
4. **Update API documentation** with new error codes
5. **Monitor logs** for structured exception output

## Questions?

Refer to:
- `app/core/exceptions.py` - Complete exception definitions
- `app/api/v1/endpoints/teams.py` - Refactoring examples
- `app/core/error_handling.py` - Global exception handler
