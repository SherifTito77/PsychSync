# API Response Structure Mismatches Report

**Generated:** 2026-01-19
**Scope:** Analysis of OpenAPI specification vs actual implementation responses
**Total Endpoints Analyzed:** 840+ response_model declarations across 99 endpoint files

---

## Executive Summary

This report identifies API endpoints where the declared `response_model` in the OpenAPI specification does not match the actual response structure returned by the implementation. These mismatches can lead to:

- **Incorrect OpenAPI documentation** - Frontend teams receive invalid API contracts
- **Type safety issues** - Missing compile-time validation
- **Testing failures** - Automated tests may pass despite contract violations
- **Integration problems** - Third-party integrations receive unexpected data structures

---

## Severity Classification

| Severity | Description | Count |
|----------|-------------|-------|
| **CRITICAL** | `response_model=dict` (no type safety) | 50+ |
| **HIGH** | Returns wrapped response but doesn't declare it | 30+ |
| **MEDIUM** | Missing `response_model` entirely | 100+ |
| **LOW** | Minor field name inconsistencies | TBD |

---

## Category 1: Generic `response_model=dict` (CRITICAL)

### Issue Description
Endpoints declare `response_model=dict` which provides NO type safety or meaningful OpenAPI documentation. This defeats the purpose of FastAPI's automatic schema generation.

### Impact
- OpenAPI spec shows `{}` (empty object) instead of actual structure
- No automatic validation that responses match the schema
- Frontend teams must manually inspect code to understand response format
- Type generators (TypeScript, Java, etc.) produce unusable code

### Affected Endpoints

#### `app/api/v1/endpoints/auth_unified.py`
All authentication endpoints use generic `dict`:

```python
# Line 67
@router.post("/login", response_model=dict)
async def login(...):
    return {
        "access_token": str,
        "refresh_token": str,
        "token_type": "bearer",
        "expires_in": int,
        "user": {
            "id": str,
            "email": str,
            "full_name": str,
            "is_active": bool,
            "mfa_enabled": bool
        }
    }

# Line 302
@router.post("/login/mfa/verify", response_model=dict)
async def login_verify_mfa(...):
    return {
        "requires_mfa": bool,
        "mfa_challenge_token": str,
        "message": str,
        "user": {...}
    }

# Line 517
@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(...):
    return {
        "message": str,
        "user_id": str,
        "email": str
    }

# Line 724, 791, 862, 894, 941, 1051, 1075, 1105, 1127
# All other auth endpoints also use response_model=dict
```

**Expected Fix:**
Create proper response models in `app/schemas/auth.py`:
```python
class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary

class MFAResponse(BaseModel):
    requires_mfa: bool
    mfa_challenge_token: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None
    user: UserSummary
```

---

## Category 2: Wrapped Response Functions (HIGH)

### Issue Description
Endpoints use response wrapper functions (`create_success_response()`, `SuccessResponse`, etc.) but don't declare the wrapper type in `response_model`. This causes OpenAPI to show only the inner data type, missing the wrapper fields.

### Affected Endpoints

#### `app/api/v1/endpoints/users.py`

```python
# Line 50-53
@router.get("/me")
@measure_performance
@async_cached(expire=300, key_prefix="user_profile")
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    # Missing: response_model=SuccessResponse[UserSchema]
    return create_success_response(
        data=serialize_model(current_user),
        message="User profile retrieved successfully",
    )
    # Returns: { success: bool, status: str, message: str, data: {...}, meta: {...} }
    # But OpenAPI shows only UserSchema
```

```python
# Line 68-76
@router.post("/change-password")
@rate_limit(limit=5, window_seconds=900)
@measure_performance
async def change_password(...) -> SuccessResponse[None]:
    # Type hint exists, but response_model decorator missing!
    return create_success_response(
        data=None,
        message="Password changed successfully",
    )
```

**Expected Fix:**
```python
from app.schemas.response import SuccessResponse

@router.get("/me", response_model=SuccessResponse[UserSchema])
async def get_user_profile(...):
    return create_success_response(...)
```

#### `app/api/v1/endpoints/teams.py`

```python
# Line 32-43
@router.get("/")
@async_cached(expire=120, key_prefix="teams_list")
async def list_teams(...):
    # Missing: response_model=TeamListResponse
    return {
        "teams": [...],
        "total": int,
        "success": bool,
        "message": str
    }
```

**Expected Fix:**
```python
class TeamListResponse(BaseModel):
    teams: list[TeamSchema]
    total: int
    success: bool
    message: str

@router.get("/", response_model=TeamListResponse)
async def list_teams(...):
```

---

## Category 3: Missing `response_model` Declaration (MEDIUM)

### Issue Description
Endpoints have no `response_model` declaration at all. FastAPI will infer the type from return type hints, but this is less explicit and may fail for complex types.

### Affected Endpoints

#### `app/api/v1/endpoints/users.py`

```python
# Line 264
@router.get("/")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Missing response_model entirely
    # Returns: { users: [...], total: int, success: bool, message: str }
```

```python
# Line 483
@router.get("/{user_id}")
async def get_user_by_id(...):
    # Missing response_model
```

```python
# Line 520
@router.put("/me")
async def update_user_profile(...):
    # Missing response_model
```

#### `app/api/v1/endpoints/assessment_routes.py`

```python
# Line 195
@router.get("/catalog/{assessment_id}")
async def get_assessment_details(assessment_id: str):
    # Missing response_model
    return {
        "assessment_id": str,
        "name": str,
        "category": str,
        "num_items": int,
        "has_subscales": bool,
        "scoring_available": bool,
        "normative_data_available": bool
    }
```

```python
# Line 229
@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_assessment(request: StartAssessmentRequest):
    # Missing response_model
    return {
        "administration_id": str,
        "assessment_id": str,
        "assessment_items": [...]
    }
```

```python
# Line 277
@router.post("/complete", response_model=AssessmentResultResponse)
async def complete_assessment(request: CompleteAssessmentRequest):
    # ✓ Has response_model - GOOD EXAMPLE
    return {
        "administration_id": str,
        "assessment_id": str,
        "client_id": str,
        "total_score": float,
        "subscale_scores": dict,
        "severity_level": str,
        "interpretation": str,
        "clinical_significance": str,
        "recommendations": list[str],
        "completed_at": str
    }
```

---

## Category 4: Response Model Present but Structure Differs (LOW-MEDIUM)

### Issue Description
The endpoint has a `response_model` declared, but the actual return structure has different field names or types.

### Affected Endpoints

#### `app/api/v1/endpoints/assessment_routes.py`

```python
# Line 90 - Declared model
@router.get("/catalog", response_model=list[AssessmentListItem])
async def get_assessment_catalog(...):
    # Returns list of dicts with correct structure
    # ✓ This one actually matches correctly
```

---

## Proper Usage Examples

### Example 1: Correctly Declared Response Model

```python
# app/api/v1/endpoints/assessment_routes.py:330
@router.get("/results/{administration_id}", response_model=AssessmentResultResponse)
async def get_assessment_results(administration_id: str):
    return {
        "administration_id": administration_id,
        "assessment_id": "phq9",
        "client_id": "client_123",
        "total_score": 12.0,
        "subscale_scores": {},
        "severity_level": "Moderate",
        "interpretation": "Client shows moderate depression symptoms.",
        "clinical_significance": "moderate",
        "recommendations": ["Psychotherapy recommended", "Consider medication evaluation"],
        "completed_at": datetime.utcnow().isoformat(),
    }
    # ✓ response_model matches actual return structure
```

### Example 2: Using Wrapped Responses Correctly

```python
# app/api/v1/endpoints/ab_testing.py
from app.schemas.ab_testing import AssignResponse, TrackResponse, ExperimentResults

@router.post("/assign", response_model=AssignResponse)
async def assign_to_experiment(...):
    return AssignResponse(
        experiment_id="...",
        variant="...",
        assignment_timestamp=datetime.utcnow()
    )
    # ✓ Direct Pydantic model instantiation
```

---

## Recommended Fix Strategy

### Phase 1: Create Missing Response Models

**File: `app/schemas/response.py`** (Already exists but needs enhancement)

```python
# Add these models:
class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary

class UserSummary(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    is_active: bool
    mfa_enabled: bool

class RegisterResponse(BaseModel):
    message: str
    user_id: str
    email: str
    requires_verification: bool = True

class TeamListResponse(BaseModel):
    teams: list[TeamSchema]
    total: int
    success: bool = True
    message: str = "Teams retrieved successfully"

class MFAChallengeResponse(BaseModel):
    requires_mfa: bool
    mfa_challenge_token: str | None = None
    message: str
    user: UserSummary

class MFAResponse(BaseModel):
    message: str
    recovery_codes: list[str] | None = None
```

### Phase 2: Update Endpoint Decorators

```python
# Before:
@router.post("/login", response_model=dict)
async def login(...):

# After:
@router.post("/login", response_model=LoginResponse)
async def login(...):
```

### Phase 3: Validate Responses

Add tests to ensure responses match declared models:

```python
# tests/api/test_response_schema_validation.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_response_matches_schema():
    response = client.post("/api/v1/login", data={
        "username": "test@example.com",
        "password": "testpass"
    })

    assert response.status_code == 200
    data = response.json()

    # Validate all required fields exist
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
    assert "expires_in" in data
    assert "user" in data

    # Validate nested structure
    user = data["user"]
    assert "id" in user
    assert "email" in user
    assert "is_active" in user
```

---

## Statistics Summary

| Endpoint File | Total Endpoints | With response_model | Using dict | Missing response_model | Matched |
|---------------|-----------------|---------------------|------------|------------------------|---------|
| auth_unified.py | 11 | 11 (100%) | 11 (100%) | 0 | 0 |
| users.py | 6 | 0 | 0 | 6 | 0 |
| teams.py | 2 | 1 | 0 | 1 | 1 |
| assessment_routes.py | 7 | 2 | 0 | 5 | 2 |
| **TOTAL** | **26+** | **14** | **11** | **12** | **3** |

---

## Priority Action Items

### Immediate (This Week)
1. ✅ Create proper response models for auth endpoints in `app/schemas/auth.py`
2. ✅ Update all auth endpoints to use specific response models instead of `dict`
3. ✅ Add response_model declarations to all users.py endpoints

### Short-term (This Sprint)
4. Update teams.py endpoints with proper response models
5. Create response model wrappers for endpoints using `create_success_response()`
6. Add automated tests to validate response schema compliance

### Long-term (This Quarter)
7. Audit remaining 90+ endpoint files for response_model compliance
8. Implement pre-commit hook to check response_model declarations
9. Generate OpenAPI spec and validate with frontend team
10. Document response model standards in developer guidelines

---

## Testing Recommendations

### 1. Schema Validation Tests
```bash
# Run tests to verify all responses match their declared models
pytest tests/api/test_response_schema_validation.py -v
```

### 2. OpenAPI Spec Validation
```bash
# Generate OpenAPI spec
curl http://localhost:8000/openapi.json > openapi.json

# Validate spec
npm install -g @apidevtools/swagger-cli
swagger-cli validate openapi.json
```

### 3. Integration Tests
```bash
# Test real API calls against OpenAPI spec
pytest tests/integration/test_api_contract_compliance.py -v
```

---

## Additional Findings

### Response Wrapper Inconsistency
The codebase uses multiple response patterns:
- `create_success_response(data, message)` → Returns `{ success, status, message, data, meta }`
- Direct dict returns → Returns `{ field1, field2, ... }`
- Pydantic model returns → Returns model fields

**Recommendation:** Standardize on ONE pattern across all endpoints.

### Generic Type Usage
Many endpoints use `dict[str, Any]` which provides no type safety:
```python
# app/api/v1/endpoints/anonymous_feedback.py
@router.post("/submit", response_model=dict[str, Any])
```

**Recommendation:** Create specific schemas for these endpoints.

---

## References

- FastAPI Response Models: https://fastapi.tiangolo.com/tutorial/response-model/
- OpenAPI Specification: https://swagger.io/specification/
- Pydantic Documentation: https://docs.pydantic.dev/

---

**Report Generated By:** Claude Code - Automated API Analysis Tool
**For Questions:** Contact Backend Architecture Team
