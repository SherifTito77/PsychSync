# Schema Consistency Audit Report

**Generated:** 2025-01-19
**Scope:** All schemas in `app/schemas/`
**Total Files Analyzed:** 30+
**Total Lines of Code:** 4,842

---

## 🔍 Critical Issues Found

### 1. ID Type Inconsistencies ❌

**Problem:** Mixed use of `int` and `UUID` for IDs

| Schema | ID Type | Issue |
|--------|---------|-------|
| `user.py` | `UUID` | ✅ Correct |
| `team.py` | `UUID` | ✅ Correct |
| `assessment.py` | `UUID` | ✅ Correct |
| `response.py` | `UUID` (mostly) | ⚠️ `ResponseScore.id` is `int` |
| `organization.py` | `UUID` | ✅ Correct |

**Violations:**
```python
# ❌ response.py line 80-81
class ResponseScore(BaseModel):
    id: int  # Should be UUID
    response_id: int  # Should be UUID
```

### 2. Naming Convention Issues ❌

**Problem:** Multiple conflicting aliases and naming patterns

**Conflicting Names:**
```python
# user.py
UserOut  # Primary schema
UserResponse = UserOut  # Alias

# team.py
TeamResponse  # Primary schema
Team = TeamResponse  # Multiple aliases
TeamSchema = TeamResponse
TeamInDB = TeamResponse
TeamOut = TeamResponse

# response.py
Response  # Name collision with domain concept
ResponseScore  # Inconsistent naming (ResponseScore vs Score)
```

**Issues:**
- Same concept has different names across files
- `_Out`, `_Response`, `_Schema` suffixes used inconsistently
- `Response` is both a schema and a domain concept (confusing)

### 3. Inconsistent Optional Fields ❌

**Problem:** Mixed use of `Optional[T]` vs `T | None`

**Old Style (Pre-Python 3.10):**
```python
from typing import Optional

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
```

**New Style (Python 3.10+):**
```python
class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
```

**Current State:** Mixed usage across files

### 4. Missing Base Classes ❌

**Problem:** Each schema defines its own base pattern, no inheritance hierarchy

**Current Pattern (Inconsistent):**
```python
# user.py
class UserBase(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    role: UserRole = UserRole.USER
    is_active: bool = True

# team.py
class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None

# assessment.py
class AssessmentBase(BaseModel):
    title: str
    description: str | None = None
    category: str
```

**Issues:**
- No shared base class with common configuration
- Each schema reinvents the wheel
- Inconsistent use of `Field()` validators

### 5. Inconsistent Config Usage ❌

**Problem:** Mixed use of `ConfigDict` vs `Config` class

**Pydantic v1 Style (Deprecated):**
```python
class User(BaseModel):
    id: UUID

    class Config:
        from_attributes = True
```

**Pydantic v2 Style (Current):**
```python
class User(BaseModel):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
```

**Current State:** Both patterns exist in codebase

### 6. Validation Inconsistencies ⚠️

**Problem:** Mixed use of `@validator` decorator vs `Field()`

**Old Style:**
```python
class AssessmentCreate(BaseModel):
    title: str

    @validator("title")
    def validate_title(cls, v):
        if len(v) < 3:
            raise ValueError("Title must be at least 3 characters")
        return v
```

**New Style:**
```python
class AssessmentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
```

**Recommendation:** Prefer `Field()` for simple validations, use `@validator` only for complex logic

### 7. Missing model_config ⚠️

**Problem:** Some schemas missing `model_config = ConfigDict(from_attributes=True)`

**Impact:** Cannot create schemas from ORM models:
```python
# ❌ Won't work without model_config
user_schema = UserRead.from_orm(user_model)

# ✅ Works with model_config
user_schema = UserRead.model_validate(user_model)
```

---

## 📊 Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| Total schema classes | ~150 | 100% |
| Using UUID IDs | ~140 | 93% ✅ |
| Using int IDs | ~10 | 7% ❌ |
| With base classes | 0 | 0% ❌ |
| With consistent naming | ~80 | 53% ⚠️ |
| With model_config | ~120 | 80% ⚠️ |
| Using Field() validators | ~60 | 40% |
| Using @validator decorators | ~90 | 60% |

---

## ✅ Recommended Fixes

### Priority 1: Create Base Schema Classes

**Action:** Create `app/schemas/base.py` with:

```python
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )

class EntitySchema(BaseSchema):
    """Base for entities with ID and timestamps"""
    id: UUID
    created_at: datetime
    updated_at: datetime
```

**Benefits:**
- Consistent configuration across all schemas
- Single source of truth for common patterns
- Easier to maintain

### Priority 2: Fix ID Types

**Action:** Change all `int` IDs to `UUID`

**Files to update:**
- `response.py`: ResponseScore.id, ResponseScore.response_id
- Any other files with `int` IDs

**Migration:** Coordinate with database migrations (Phase 2.2)

### Priority 3: Standardize Naming

**Action:** Establish naming convention

**Convention:**
- Use `{Entity}Create` for creation schemas
- Use `{Entity}Update` for update schemas
- Use `{Entity}Response` for response schemas
- Use `{Entity}List` for list responses
- Remove aliases (choose one name and use it)

**Example:**
```python
# ✅ Correct
class UserCreate(UserBase): ...
class UserUpdate(BaseModel): ...
class UserResponse(EntitySchema): ...
class UserList(BaseModel): ...

# ❌ Avoid
class UserOut(UserBase): ...  # Use UserResponse
class User = UserResponse     # No aliases
```

### Priority 4: Migrate to Field() Validators

**Action:** Replace simple `@validator` with `Field()`

**Before:**
```python
@validator("title")
def validate_title(cls, v):
    if len(v) < 3:
        raise ValueError("Title must be at least 3 characters")
    return v
```

**After:**
```python
title: str = Field(..., min_length=3, max_length=200)
```

**Keep `@validator` for:**
- Cross-field validation
- Complex business logic
- Conditional validation

### Priority 5: Add Type Hints

**Action:** Ensure all fields have proper type hints

**Before:**
```python
class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
```

**After:**
```python
class TeamUpdate(BaseModel):
    name: Annotated[str | None, Field(min_length=1, max_length=255)] = None
    description: Annotated[str | None, Field(max_length=5000)] = None
```

---

## 🎯 Implementation Plan

### Phase 1: Create Base Classes ✅
- [x] Create `app/schemas/base.py`
- [x] Create `app/schemas/common.py`
- [ ] Update existing schemas to inherit from base classes

### Phase 2: Fix ID Types
- [ ] Audit all schemas for int IDs
- [ ] Convert to UUID
- [ ] Add validation tests

### Phase 3: Standardize Naming
- [ ] Document naming convention
- [ ] Rename schemas according to convention
- [ ] Update all imports
- [ ] Add backward compatibility aliases if needed

### Phase 4: Update Validation
- [ ] Replace simple validators with Field()
- [ ] Keep complex @validator where appropriate
- [ ] Add comprehensive validation tests

### Phase 5: Documentation
- [ ] Create schema style guide
- [ ] Document migration process
- [ ] Update API documentation

---

## 📋 Migration Checklist

For each schema file:

1. **Add imports:**
   ```python
   from app.schemas.base import BaseSchema, EntitySchema
   from app.schemas.common import Status, UserRole
   ```

2. **Update base class:**
   ```python
   class UserCreate(BaseSchema):  # Was: BaseModel
       ...
   ```

3. **Fix ID types:**
   ```python
   id: UUID  # Was: int
   ```

4. **Add model_config if missing:**
   ```python
   model_config = ConfigDict(from_attributes=True)
   ```

5. **Update validators:**
   ```python
   # Replace simple validators with Field()
   email: EmailStr = Field(**ValidationRules.email())
   ```

6. **Test:**
   ```python
   # Verify schema works
   def test_user_schema():
       user = UserCreate(email="test@example.com")
       assert user.email == "test@example.com"
   ```

---

## 🚨 Breaking Changes

### For API Consumers

**Change 1: Response field names**
```diff
- { "user_id": 123 }
+ { "user_id": "uuid-string-here" }
```

**Change 2: Schema names**
```diff
- UserOut
+ UserResponse
```

**Change 3: Required fields**
```diff
- POST /assessments { "title": "" }  # Accepted
+ POST /assessments { "title": "" }  # Returns 400 (min_length=3)
```

### Migration Strategy

1. **Deprecation Period:** Keep old schema names as aliases for 2 versions
2. **API Versioning:** Use `/api/v1/` for old schemas, `/api/v2/` for new
3. **Communication:** Document breaking changes in changelog
4. **Tests:** Ensure all tests pass before deploying

---

## 📚 Resources

- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [Type Hints in Python](https://docs.python.org/3/library/typing.html)
- [FastAPI OpenAPI Documentation](https://fastapi.tiangolo.com/tutorial/schema-extra-example/)
