# PsychSync Code Style Implementation Guide

**Version:** 1.0.0  
**Last Updated:** January 8, 2026  
**Status:** Active

---

## Executive Summary

PsychSync uses automated linting to maintain code quality:
- **Python:** Ruff (14,306 issues → 23% auto-fixable)
- **TypeScript:** ESLint (frontend)
- **Pre-commit:** Automated checks on git commit

---

## Quick Start

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Activate hooks
pre-commit install

# Run on all files (one-time setup)
pre-commit run --all-files
```

### Daily Usage

```bash
# Auto-fix Python code
ruff check . --fix

# Format Python code  
ruff format .

# Check TypeScript
cd frontend && npm run lint
```

---

## Current State

### Python Issues Summary

```
Total Issues:    14,306
Auto-Fixable:      3,134 (23%)
Manual Fixes:     11,172 (77%)
```

### Top 5 Issues

| Rule | Count | Description | Fix Complexity |
|------|-------|-------------|----------------|
| ERA001 | 2,500+ | Commented-out code | Low |
| E501 | 2,000+ | Line too long (>100) | Medium |
| G004 | 1,500+ | Logging f-strings | Low |
| TRY400 | 800+ | Use logger.exception | Low |
| DTZ003 | 500+ | datetime.utcnow() | Low |

**Estimated Fix Time:** 8-12 hours for all manual fixes

---

## Fixing Strategy

### Phase 1: Auto-Fix (5 minutes)

```bash
ruff check . --fix
```

**Result:** 3,134 issues fixed automatically

### Phase 2: Manual Priority Fixes (4-6 hours)

**Priority 1: Commented Code (1 hour)**
```bash
# Find all commented code
ruff check . --select ERA001

# Manual: Remove commented lines
```

**Priority 2: Logging (1-2 hours)**
```python
# Before
logger.error(f"Error: {error}")

# After  
logger.error("Error: %s", error)
```

**Priority 3: Exceptions (1 hour)**
```python
# Before
except Error as e:
    raise HTTPException(...)

# After
except Error as e:
    raise HTTPException(...) from e
```

**Priority 4: Datetimes (30 min)**
```python
# Before
datetime.utcnow()

# After
datetime.now(UTC)
```

### Phase 3: Lower Priority (2-4 hours)

- Fix long lines
- Simplify complex code
- Remove unused imports
- Organize imports

---

## Pre-Commit Hooks

### What's Checked

1. ✅ Python style (ruff)
2. ✅ Python formatting (ruff format)
3. ✅ TypeScript style (eslint)
4. ✅ Trailing whitespace
5. ✅ Line endings
6. ✅ YAML/JSON validity
7. ✅ No large files (>1MB)
8. ✅ No private keys

### Usage

**Automatic:** Runs on `git commit`

**Skip (not recommended):**
```bash
git commit --no-verify -m "WIP"
```

---

## Configuration Files

- **Ruff:** `ruff.toml` (Python linting)
- **Pre-commit:** `.pre-commit-config.yaml`
- **ESLint:** `frontend/eslint.config.js`

---

## Best Practices

### Development Workflow

1. Write code
2. Run `ruff check . --fix`
3. Fix remaining issues manually
4. Commit (pre-commit hooks verify)
5. Push (CI verifies again)

### Code Review Checklist

- [ ] No commented-out code
- [ ] Logging uses `%s` not f-strings
- [ ] Exceptions use `raise ... from err`
- [ ] Datetimes are timezone-aware
- [ ] Line length ≤ 100 chars
- [ ] No unused imports/variables

---

## CI/CD Integration

**File:** `.github/workflows/lint.yml`

Runs on every pull request:
```yaml
- Python lint check (ruff)
- TypeScript lint check (eslint)
- Pre-commit hooks validation
```

---

## Resources

- [Ruff Docs](https://docs.astral.sh/ruff/)
- [Pre-Commit](https://pre-commit.com/)
- [ESLint](https://eslint.org/)

---

**Questions?** Open an issue or contact the dev team.

