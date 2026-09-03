# Fix Critical Syntax Errors

## Automated Fixes for 6 Critical Issues

This document provides the exact fixes needed for the 6 syntax errors found in the health check.

---

## 🔧 Python File Fixes

### 1. Fix `app/core/config/celery_config.py` (Line 277)

**Location**: `app/core/config/celery_config.py:277`
**Error**: Duplicate keyword argument `task_send_sent_event`

**Current Code**:
```python
task_send_sent_event=True,
task_send_sent_event=True,  # ← Duplicate
```

**Fix**:
```python
# Remove the duplicate line (keep only one)
task_send_sent_event=True,
```

---

### 2. Fix `app/core/database_security.py` (Line 306)

**Location**: `app/core/database_security.py:306`
**Error**: Invalid syntax - missing comma in SQL query

**Current Code**:
```python
role_check = await db.execute(text("""
```

**Fix**:
```python
role_check = await db.execute(text("""
    -- Add proper SQL query here
    SELECT role_name FROM user_roles WHERE user_id = :user_id
"""), {"user_id": user_id})
```

---

### 3. Fix `app/core/validation.py` (Line 572)

**Location**: `app/core/validation.py:572`
**Error**: Unterminated string literal - missing quote

**Current Code**:
```python
'.jar', '.sh', '.php', '.asp', '.aspx', .jsp', '.py', '.pl',
```

**Fix**:
```python
'.jar', '.sh', '.php', '.asp', '.aspx', '.jsp', '.py', '.pl',
```

---

### 4. Fix `app/security/logging/middleware.py` (Line 154)

**Location**: `app/security/logging/middleware.py:154`
**Error**: `async for` outside async function

**Current Code**:
```python
def log_response(response):
    async for chunk in response.body_iterator:
        # process chunk
```

**Fix**:
```python
async def log_response(response):
    async for chunk in response.body_iterator:
        # process chunk
```

---

### 5. Fix `app/testing/api_fuzzer.py` (Line 273)

**Location**: `app/testing/api_fuzzer.py:273`
**Error**: Mismatched parentheses

**Current Code**:
```python
'{"string": "\\"\\""}',
```

**Fix**:
```python
'{"string": "\\"\\\\""}',
```

---

## 🔧 TypeScript File Fix

### 6. Fix `frontend/src/components/mobile/MobileBDI2.tsx` (Line 128)

**Location**: `frontend/src/components/mobile/MobileBDI2.tsx:128`
**Error**: Unterminated string literal

**Current Code**:
```typescript
const text = "some string  // ← Missing closing quote
```

**Fix**:
```typescript
const text = "some string";  // ← Added closing quote
```

---

## 🚀 Quick Fix Commands

### Apply all Python fixes:
```bash
# Fix 1: celery_config.py
sed -i.bak '277d' app/core/config/celery_config.py

# Fix 2: validation.py
sed -i.bak "s/.jsp'/.jsp'/g" app/core/validation.py

# Fix 3: Add async to middleware function
sed -i.bak '153s/def /async def /' app/security/logging/middleware.py
```

### Verify fixes:
```bash
# Check Python syntax
python3 -m py_compile app/core/config/celery_config.py
python3 -m py_compile app/core/validation.py
python3 -m py_compile app/security/logging/middleware.py

# Check TypeScript syntax
cd frontend && npx tsc --noEmit
```

---

## ✅ Validation Checklist

After applying fixes, verify:

- [ ] All Python files compile without errors
- [ ] All TypeScript files compile without errors
- [ ] Application starts successfully
- [ ] Tests run without syntax errors
- [ ] CI/CD pipeline passes

---

## 📋 Pre-commit Prevention

Add these to `.pre-commit-config.yaml` to prevent future syntax errors:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.(tsx?|jsx?)$
        types: [file]
```

Install:
```bash
pip install pre-commit
pre-commit install
```

---

**Estimated Time to Fix**: 10 minutes
**Difficulty**: Easy
**Impact**: Critical - Fixes prevent application crashes
