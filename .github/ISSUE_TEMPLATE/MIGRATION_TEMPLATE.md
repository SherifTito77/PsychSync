# Migrate [FILE_NAME] to Structured Error Handling

## 🎯 Goal
Migrate all generic `HTTPException` calls in `[FILE_PATH]` to use structured error exceptions

## 📋 Current State
- **File:** `[FILE_PATH]`
- **Lines:** ~[X] lines
- **Current HTTPExceptions:** [N] occurrences
- **Estimated effort:** [X] hours

## 🔍 Findings

### Generic HTTPException Locations:
1. Line [XX]: `raise HTTPException(status_code=404, detail="...")`
2. Line [XX]: `raise HTTPException(status_code=403, detail="...")`
3. Line [XX]: `raise HTTPException(status_code=400, detail="...")`

## ✅ Migration Plan

### Step 1: Add Imports (5 minutes)
```python
from app.core.exceptions import (
    [Exception1],
    [Exception2],
    [Exception3],
)
```

### Step 2: Replace HTTPExceptions (15-30 minutes)
- Line [XX]: Replace with `[ExceptionName]`
- Line [XX]: Replace with `[ExceptionName]`
- Line [XX]: Replace with `[ExceptionName]`

### Step 3: Test (10 minutes)
```bash
# Run pre-commit
pre-commit run [FILE_NAME]

# Run tests
pytest tests/[TEST_FILE] -v

# Manual test
# [Testing steps]
```

### Step 4: Update Tests (if needed) (15 minutes)
- Update test assertions to check for new error codes
- Verify error response format

## 📚 Reference Documentation

- **Quick Reference:** `docs/developer/ERROR_CODE_QUICK_REFERENCE.md`
- **Complete Guide:** `docs/code_quality/ERROR_CODE_SYSTEM.md`
- **Training:** `docs/training/TEAM_TRAINING_ERROR_HANDLING.md`

## 🧪 Acceptance Criteria

- [ ] All `HTTPException` calls replaced with structured exceptions
- [ ] Pre-commit hooks pass
- [ ] All tests pass
- [ ] Manual testing completed
- [ ] Error responses verified

## 📊 Examples

### Before:
```python
if not team:
    raise HTTPException(status_code=404, detail="Team not found")
```

### After:
```python
if not team:
    raise TeamNotFoundError(team_id=str(team_id))
```

## 🔗 Related Issues

- Parent issue: #XXXX (Structured Error Handling Migration)
- Similar migrations:
  - #XXX (teams.py)
  - #XXX (auth.py)
  - #XXX (agent_orchestrator.py)

## 📝 Notes

[Add any notes about edge cases, dependencies, or special considerations]

## ⏱ Time Tracking

- **Estimated:** [X] hours
- **Actual:** [X] hours

---

**Priority:** [High/Medium/Low]
**Complexity:** [Low/Medium/High]
**Assigned to:** @[username]
**Sprint:** [Sprint name]
**Due date:** [YYYY-MM-DD]
