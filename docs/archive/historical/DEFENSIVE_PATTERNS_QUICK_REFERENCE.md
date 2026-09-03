# 🛡️ Defensive Programming Patterns - Quick Reference

This guide provides copy-paste patterns for the defensive programming techniques applied during the validation audit.

---

## 📋 Table of Contents

1. [Null Check Patterns](#null-check-patterns)
2. [Type Validation Patterns](#type-validation-patterns)
3. [Safe JSON Parsing](#safe-json-parsing)
4. [Error Handling Patterns](#error-handling-patterns)
5. [Schema Validation](#schema-validation)
6. [Rate Limiting](#rate-limiting)

---

## 🔍 NULL CHECK PATTERNS

### Pattern 1: Database Query Result Validation

**Problem:** Query returns None, accessing properties crashes

**Before (UNSAFE):**
```python
# ❌ CRASHES if user is None
result = await db.execute(select(User).where(User.email == email))
user = result.scalar_one_or_none()
return user.id  # AttributeError: 'NoneType' object has no attribute 'id'
```

**After (SAFE):**
```python
# ✅ SAFE - Explicit validation
result = await db.execute(select(User).where(User.email == email))
user = result.scalar_one_or_none()

# Defensive null check before accessing properties
if user is None:
    logger.warning(f"User not found: {email}")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

return user.id
```

### Pattern 2: Nested Property Access Validation

**Problem:** Accessing nested properties without validating parent

**Before (UNSAFE):**
```python
# ❌ CRASHES if assessment is None
assessment = AssessmentService.get_by_id(db, assessment_id)
if assessment.status.value != "active":  # AttributeError!
    raise HTTPException(...)
```

**After (SAFE):**
```python
# ✅ SAFE - Check exists before accessing properties
assessment = AssessmentService.get_by_id(db, assessment_id)

# Defensive null check before accessing nested properties
if assessment is None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Assessment not found"
    )

if assessment.status.value != "active":
    raise HTTPException(...)
```

### Pattern 3: Critical Field Validation

**Problem**: Field exists but is None

**Before (UNSAFE):**
```python
# ❌ CRASHES if user.email is None
user = get_user(user_id)
return user.email.split('@')  # AttributeError!
```

**After (SAFE):**
```python
# ✅ SAFE - Validate critical fields
user = get_user(user_id)

if user is None:
    raise HTTPException(status_code=404, detail="User not found")

# Validate critical fields are not None
if user.email is None:
    logger.error(f"Data integrity error: user.email is None for user_id: {user_id}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="User data integrity error"
    )

return user.email.split('@')
```

---

## 🔐 TYPE VALIDATION PATTERNS

### Pattern 1: UUID vs Integer Type Alignment

**Problem:** Mismatch between schema (int) and database (UUID)

**Before (WRONG):**
```python
# ❌ Type mismatch - database uses UUID
class Assessment(BaseModel):
    id: int  # WRONG!
    created_by_id: int  # WRONG!
```

**After (CORRECT):**
```python
# ✅ Type aligned with database
from uuid import UUID

class Assessment(BaseModel):
    id: UUID  # CORRECT!
    created_by_id: UUID  # CORRECT!
```

### Pattern 2: Frontend-Backend Type Alignment

**Problem:** Frontend expects number, backend sends UUID (string)

**Before (WRONG):**
```typescript
// ❌ Frontend uses number
interface Team {
  id: number;
  created_by_id: number;
}

// Backend sends UUID string
{ "id": "123e4567-e89b-12d3-a456-426614174000" }
// Type error or runtime failure!
```

**After (CORRECT):**
```typescript
// ✅ Frontend uses string (UUID)
interface Team {
  id: string;  // UUID
  created_by_id: string;  // UUID
}

// Backend sends UUID string
{ "id": "123e4567-e89b-12d3-a456-426614174000" }
// Works perfectly!
```

---

## 📦 SAFE JSON PARSING

### Pattern 1: Parse with Fallback

**Problem:** JSON.parse crashes on invalid JSON

**Before (UNSAFE):**
```typescript
// ❌ CRASHES entire app
const events = JSON.parse(localStorage.getItem('events') || '[]');
// If localStorage has invalid JSON, entire app crashes!
```

**After (SAFE):**
```typescript
// ✅ SAFE - Returns fallback on error
import { safeJSONParse } from '@/utils/safeJSON';

const events = safeJSONParse<EventType[]>(
  localStorage.getItem('events'),
  []  // Fallback to empty array
);
// App continues working even with invalid JSON!
```

### Pattern 2: Safe LocalStorage Operations

**Before (UNSAFE):**
```typescript
// ❌ Multiple points of failure
const user = JSON.parse(localStorage.getItem('user') || '{}');
const settings = JSON.parse(localStorage.getItem('settings') || '{}');
```

**After (SAFE):**
```typescript
// ✅ SAFE - Single utility function
import { safeGetLocalStorage } from '@/utils/safeJSON';

const user = safeGetLocalStorage<UserType>('user', null);
const settings = safeGetLocalStorage<SettingsType>('settings', {});
```

---

## ⚠️ ERROR HANDLING PATTERNS

### Pattern 1: Type-Safe Error Handling

**Problem:** Using `any` loses type safety

**Before (UNSAFE):**
```typescript
// ❌ Loses type information
} catch (error: any) {
  if (error.response?.status === 401) {  // No autocomplete!
    // ...
  }
}
```

**After (SAFE):**
```typescript
// ✅ Type-safe with type guard
import axios, { AxiosError } from 'axios';

} catch (error: unknown) {
  if (isAxiosError(error) && error.response?.status === 401) {
    // Full type safety and autocomplete!
  }
}

// Type guard function
function isAxiosError(error: unknown): error is AxiosError {
  return axios.isAxiosError(error);
}
```

### Pattern 2: Explicit HTTP Error Handling

**Before (UNSAFE):**
```python
# ❌ Generic exception handling
try:
    result = some_operation()
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

**After (SAFE):**
```python
# ✅ Specific error handling with context
try:
    result = some_operation()
except ValidationError as e:
    logger.warning(f"Validation failed: {e}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid input: {e}"
    )
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Database operation failed"
    )
```

---

## ✅ SCHEMA VALIDATION

### Pattern 1: Explicit Type Imports

**Before (INCONSISTENT):**
```python
# ❌ Uses int
from pydantic import BaseModel

class Question(BaseModel):
    id: int  # Wrong!
```

**After (CORRECT):**
```python
# ✅ Uses UUID consistently
from uuid import UUID
from pydantic import BaseModel

class Question(BaseModel):
    id: UUID  # Matches database!
```

### Pattern 2: Schema-Model Alignment

**Checklist for alignment:**
```python
# Database Model
class Assessment(Base):
    id = Column(UUID, primary_key=True)
    created_by_id = Column(UUID, ForeignKey('users.id'))
    team_id = Column(UUID, nullable=True)

# Schema (MUST MATCH!)
class AssessmentBase(BaseModel):
    id: UUID  # ✓ Matches
    created_by_id: UUID  # ✓ Matches
    team_id: UUID | None  # ✓ Matches
```

---

## 🚦 RATE LIMITING

### Pattern 1: Correct Import and Usage

**Before (DEPRECATED):**
```python
# ❌ Old pattern
from app.core.rate_limiter_unified import check_rate_limit

@check_rate_limit(identifier="public", limit_name="public")
async def my_endpoint():
    pass
```

**After (CURRENT):**
```python
# ✅ New pattern
from app.core.rate_limiter_unified import rate_limit, RateLimitStrategy

@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
async def my_endpoint():
    pass
```

### Pattern 2: Custom Rate Limits

```python
# Strict rate limit for sensitive operations
@rate_limit(
    limit=5,
    window=300,  # 5 minutes
    strategy=RateLimitStrategy.SLIDING_WINDOW
)
async def login():
    pass

# Lenient rate limit for public endpoints
@rate_limit(
    limit=1000,
    window=60,  # 1 minute
    strategy=RateLimitStrategy.FIXED_WINDOW
)
async def public_data():
    pass
```

---

## 🎯 COMMON PITFALLS TO AVOID

### ❌ DON'T: Trust database query results
```python
user = db.get_user(user_id)
return user.email  # CRASH if user is None!
```

### ✅ DO: Always validate before access
```python
user = db.get_user(user_id)
if user is None:
    raise HTTPException(status_code=404)
return user.email
```

---

### ❌ DON'T: Use `any` type
```typescript
} catch (error: any) {
  // Loses all type safety
}
```

### ✅ DO: Use `unknown` with type guards
```typescript
} catch (error: unknown) {
  if (error instanceof Error) {
    // Type-safe access
  }
}
```

---

### ❌ DON'T: Parse JSON without error handling
```typescript
const data = JSON.parse(input);  // Crashes app!
```

### ✅ DO: Use safe parsing with fallbacks
```typescript
const data = safeJSONParse(input, default_value);
```

---

### ❌ DON'T: Mix int and UUID types
```python
# Schema
id: int
# Model
id = Column(UUID)  # MISMATCH!
```

### ✅ DO: Keep types consistent across layers
```python
# Schema
id: UUID
# Model
id = Column(UUID)  # MATCHES!
```

---

## 📝 CHECKLIST FOR NEW CODE

Before committing new code, verify:

- [ ] All database query results are validated for None
- [ ] All object property accesses are protected by null checks
- [ ] Schema types match database model types
- [ ] Frontend types match backend types
- [ ] All JSON.parse uses safe parsing utility
- [ ] Error handling is specific, not generic
- [ ] Rate limiting is applied to public endpoints
- [ ] Type annotations are specific (avoid `any`)
- [ ] Critical fields are validated for None
- [ ] Logging includes context for debugging

---

## 🔗 RELATED FILES

- **Safe JSON Utility:** `frontend/src/utils/safeJSON.ts`
- **Validation Report:** `VALIDATION_FIXES_DEPLOYMENT_REPORT.md`
- **Pre-Deployment Check:** `scripts/pre_deployment_check.sh`
- **Post-Deployment Monitor:** `scripts/post_deployment_monitor.sh`

---

## 💡 PRO TIPS

1. **Be Explicit:** Use `is None` instead of `if not user:` for clarity
2. **Fail Fast:** Validate early and raise specific errors
3. **Log Context:** Always log what you were trying to do when errors occur
4. **Type Safety:** Let TypeScript/Python catch bugs at compile time
5. **Defensive Programming:** Assume data can be bad and validate accordingly

---

*Remember: A few extra lines of validation now saves hours of debugging later!*
