# Team Training Session: Structured Error Handling

> **Duration:** 30 minutes
> **Audience:** Backend developers
> **Prerequisites:** None
> **Materials:** Projector, CODE_QUALITY_START_HERE.md

---

## Training Agenda (30 Minutes)

### Part 1: Introduction (3 minutes)
- Why we're doing this
- What changed
- Impact on your daily work

### Part 2: Quick Start Demo (5 minutes)
- Live code examples
- Before/after comparisons
- See the error response format

### Part 3: Common Patterns (7 minutes)
- 5 most common error scenarios
- Code for each pattern
- When to use each error code

### Part 4: Migration Guide (5 minutes)
- How to migrate existing code
- Tools to help you
- What we've already migrated

### Part 5: Q&A (5 minutes)
- Open questions
- Practice examples
- Next steps

### Part 6: Action Items (5 minutes)
- Install pre-commit hooks
- Your migration assignments
- Resources and documentation

---

## Part 1: Introduction (3 minutes)

### Why Structured Error Handling?

**Before (Generic Errors):**
```python
raise HTTPException(status_code=404, detail="Not found")
```
❌ No error code
❌ Client can't parse errors programmatically
❌ Hard to debug (no context)
❌ Inconsistent error messages

**After (Structured Errors):**
```python
raise TeamNotFoundError(team_id=str(team_id))
```
✅ Error code: BIZ_4300
✅ Client can handle specific errors
✅ Structured details for debugging
✅ Consistent error format

### What Changed Today?

1. **60+ new error codes** added to `app/core/exceptions.py`
2. **10+ new exception classes** for common scenarios
3. **Pre-commit hooks** enhanced with quality checks
4. **Documentation** created for quick reference

### Impact on Your Work

- ✅ **Easier debugging:** Error codes tell you exactly what went wrong
- ✅ **Better client UX:** Apps can show specific error messages
- ✅ **Type-safe:** Can't typo error codes (use exception classes)
- ✅ **Automated:** Pre-commit hooks catch mistakes

---

## Part 2: Quick Start Demo (5 minutes)

### Live Demo: Try the New Exceptions

**Step 1:** Open a Python REPL

```bash
cd /Users/sheriftito/Downloads/psychsync
source .venv/bin/activate
python
```

**Step 2:** Import and try an exception

```python
from app.core.exceptions import TeamNotFoundError

# Raise the exception
try:
    raise TeamNotFoundError(team_id="123")
except TeamNotFoundError as e:
    print(f"Error Code: {e.error_code}")
    print(f"Status Code: {e.status_code}")
    print(f"Message: {e.message}")
    print(f"Details: {e.details}")
```

**Output:**
```
Error Code: BIZ_4300
Status Code: 404
Message: Team 123 not found
Details: {'team_id': '123'}
```

### See the Error Response Format

When an exception is raised in an API endpoint, clients receive:

```json
{
  "error": true,
  "error_code": "BIZ_4300",
  "message": "Team 123 not found",
  "status_code": 404,
  "details": {
    "team_id": "123"
  },
  "timestamp": "2026-01-13T10:30:00.000Z",
  "request_id": "req_abc123",
  "path": "/api/v1/teams/123",
  "documentation_url": "https://docs.psychsync.com/api/errors/BIZ_4300"
}
```

This structured format enables:
- **Programmatic error handling** on clients
- **Better debugging** with request IDs
- **Automatic logging** with context

---

## Part 3: Common Patterns (7 minutes)

### Pattern 1: Resource Not Found

**When:** A requested resource (team, assessment, user) doesn't exist

```python
from app.core.exceptions import TeamNotFoundError, AssessmentNotFoundError

# Team not found
if not team:
    raise TeamNotFoundError(team_id=str(team_id))

# Assessment not found
if not assessment:
    raise AssessmentNotFoundError(assessment_id=str(assessment_id))

# Generic record not found
if not record:
    raise RecordNotFoundError(
        resource="User",
        identifier=user_id
    )
```

**Error codes:**
- Team: `BIZ_4300` (404)
- Assessment: `BIZ_4100` (404)
- Generic: `DB_3001` (404)

---

### Pattern 2: Access Denied

**When:** User lacks permission for an action

```python
from app.core.exceptions import ForbiddenError, TeamAccessDeniedError

# Generic access denied
if not has_permission:
    raise ForbiddenError(
        message="You do not have permission to perform this action"
    )

# Team-specific access denied
if not is_team_member(user_id, team_id):
    raise TeamAccessDeniedError(
        team_id=str(team_id),
        user_id=str(user_id)
    )
```

**Error codes:**
- Generic: `AUTH_1001` (403)
- Team: `BIZ_4303` (403)

---

### Pattern 3: Invalid Input

**When:** User provided invalid/missing data

```python
from app.core.exceptions import (
    ValidationError,
    InvalidEmailError,
    MissingFieldError
)

# Missing required field
if not email:
    raise MissingFieldError(field="email")

# Invalid email format
if not is_valid_email(email):
    raise InvalidEmailError(email=email)

# Generic validation error
if not meets_requirements(data):
    raise ValidationError(
        message="Data does not meet requirements",
        error_code=ErrorCode.VALIDATION_ERROR
    )
```

**Error codes:**
- Missing field: `VAL_2002` (422)
- Invalid email: `VAL_2003` (422)
- Generic: `VAL_2000` (422)

---

### Pattern 4: Rate Limiting

**When:** User exceeded rate limit

```python
from app.core.exceptions import RateLimitExceededError

if rate_limit_exceeded():
    raise RateLimitExceededError(
        retry_after=60,  # seconds
        limit=100  # max requests
    )
```

**Error code:** `AUTH_1106` (429)

**Client receives:**
```json
{
  "error_code": "AUTH_1106",
  "retry_after": 60,
  "details": {
    "retry_after": 60,
    "limit": 100
  }
}
```

---

### Pattern 5: Authentication Errors

**When:** Login/auth fails

```python
from app.core.exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    SessionExpiredError
)

# Invalid username/password
if not valid_credentials:
    raise InvalidCredentialsError()

# Account locked
if account.is_locked:
    raise AccountLockedError()

# Session expired
if session.is_expired:
    raise SessionExpiredError()
```

**Error codes:**
- Invalid credentials: `AUTH_1002` (401)
- Account locked: `AUTH_1102` (403)
- Session expired: `AUTH_1104` (401)

---

## Part 4: Migration Guide (5 minutes)

### How to Migrate Existing Code

**Before:**
```python
from fastapi import HTTPException

if not team:
    raise HTTPException(
        status_code=404,
        detail="Team not found"
    )
```

**After (3 steps):**

**Step 1:** Import the exception
```python
from app.core.exceptions import TeamNotFoundError
```

**Step 2:** Replace HTTPException with the specific exception
```python
if not team:
    raise TeamNotFoundError(team_id=str(team_id))
```

**Step 3:** Test it
```bash
# Run pre-commit to check
pre-commit run

# Run tests
pytest tests/api/test_teams.py -v
```

### Tools to Help You

**1. Pre-commit hooks** (catch mistakes)
```bash
# Install (one time)
pre-commit install

# Run manually
pre-commit run --all-files
```

**2. Quick reference guide** (look up error codes)
```bash
# Open the guide
cat docs/developer/ERROR_CODE_QUICK_REFERENCE.md
```

**3. IDE autocomplete** (find exceptions)
```python
from app.core.exceptions import <CTRL+SPACE to see all>
```

### What We've Already Migrated

✅ `app/api/v1/teams.py` - Team errors
✅ `app/services/agent_orchestrator.py` - Tool errors
✅ `app/api/v1/endpoints/auth.py` - Authentication errors

**Total:** 6 endpoints migrated today

---

## Part 5: Q&A (5 minutes)

### Common Questions

**Q: Do I have to migrate all my code today?**
A: No! Start with new code you write. Migrate old code incrementally.

**Q: What if there's no exception for my error?**
A: Use `PsychSyncException` with a custom error code, or add a new exception class.

**Q: Will this break existing clients?**
A: No! The response format is backward compatible. Clients get more information now.

**Q: Can I still use HTTPException?**
A: You can, but we strongly recommend using the structured exceptions for consistency.

**Q: How do I know which error code to use?**
A: Check the quick reference guide (`docs/developer/ERROR_CODE_QUICK_REFERENCE.md`)

### Practice Examples

**Example 1:** You're checking if a user exists

**Solution:**
```python
if not user:
    raise UserNotFoundError(identifier=user_id)
```

**Example 2:** User tries to access a feature they don't have

**Solution:**
```python
if not user.has_feature("advanced_analytics"):
    raise UpgradeRequiredError(
        feature="advanced_analytics",
        required_plan="Professional"
    )
```

**Example 3:** Password doesn't meet requirements

**Solution:**
```python
if not is_strong_password(password):
    raise WeakPasswordError(
        requirements={
            "min_length": 8,
            "requires_uppercase": True,
            "requires_number": True
        }
    )
```

---

## Part 6: Action Items (5 minutes)

### Immediate Actions (Do Now!)

**Action 1: Install pre-commit hooks** (1 minute)
```bash
cd /Users/sheriftito/Downloads/psychsync
source .venv/bin/activate
pre-commit install
```

**Action 2: Open the quick reference** (30 seconds)
```bash
open docs/developer/ERROR_CODE_QUICK_REFERENCE.md
```

**Action 3: Try an example** (2 minutes)
```python
# Create a test file
from app.core.exceptions import AssessmentNotFoundError

try:
    raise AssessmentNotFoundError(assessment_id="123")
except AssessmentNotFoundError as e:
    print(f"✅ Error code: {e.error_code}")
    print(f"✅ Status: {e.status_code}")
```

### This Week

**Action 4:** Use structured exceptions in **new code** you write

**Action 5:** Migrate **1-2 endpoints** you're working on

**Action 6:** Review the quick reference guide when unsure

### Next Week

**Action 7:** Team will create GitHub issues for bulk migration

**Action 8:** We'll track migration progress in standups

---

## Resources

### Documentation (Read These!)

1. **Quick Reference** - Daily use
   - `docs/developer/ERROR_CODE_QUICK_REFERENCE.md`

2. **Complete Guide** - Deep dive
   - `docs/code_quality/ERROR_CODE_SYSTEM.md`

3. **Phase 1 Summary** - Project status
   - `docs/code_quality/PHASE1_COMPLETION_SUMMARY.md`

### Code Reference

**Exception definitions:** `app/core/exceptions.py`
**Error codes:** See `ErrorCode` enum in the file above

**Migrated examples:**
- `app/api/v1/teams.py`
- `app/services/agent_orchestrator.py`
- `app/api/v1/endpoints/auth.py`

### Getting Help

**Questions?**
- Check the quick reference guide first
- Ask in #backend-dev channel
- Create an issue for bugs/suggestions

---

## Summary

### Key Takeaways

1. ✅ **Use structured exceptions** instead of `HTTPException`
2. ✅ **Include helpful details** (IDs, counts, limits)
3. ✅ **Check the quick reference** for error codes
4. ✅ **Run pre-commit** to catch mistakes
5. ✅ **Migrate incrementally** - don't try to do it all at once

### What Changed Today

- 60+ new error codes
- 10+ exception classes
- 6 endpoints migrated
- Pre-commit hooks enhanced
- Documentation created

### Your Next Steps

1. Install pre-commit: `pre-commit install`
2. Read quick reference (10 min)
3. Use in new code you write
4. Migrate 1-2 endpoints this week

---

> **"Code quality is not a destination, it's a journey."**
>
> **Let's make our error handling exceptional! 🚀**
