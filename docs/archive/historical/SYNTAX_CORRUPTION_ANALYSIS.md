# Syntax Corruption Analysis & Fix Strategy

**Date:** 2025-01-08
**Issue:** Widespread syntax corruption blocking 370+ B904 fixes

---

## Problem Analysis

### Corruption Pattern Identified

**Pattern 1: Decorator Insertion in Raise Statements** ✅ FIXED
```python
# CORRUPTED:
except Exception as e:
    raise HTTPException(status_code=500
@check_rate_limit(identifier="public", limit_name="public")
, detail=str(e))

# FIXED:
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=str(e)
    ) from e
```

**Pattern 2: Keyword Split by Decorator**
```python
# CORRUPTED:
    }
e
@check_rate_limit(...)
xcept Exception as e:
    raise HTTPException(...)

# SHOULD BE:
    }
except Exception as e:
    raise HTTPException(...)
```

**Pattern 3: Parameter String Concatenation Corruption**
```python
# CORRUPTED:
detail=f"Error predicting outcome: {str(e, dependencies=[Depends(get_current_user)])}"

# SHOULD BE:
detail=f"Error predicting outcome: {str(e)}"
```

**Pattern 4: Malformed String/Array Literals**
```python
# CORRUPTED:
'{"unicode": "\u00"}'  # Incomplete Unicode escape
'{"string": "\\"\\"'}'  # Malformed string

# These appear to be intentional test cases in api_fuzzer.py
```

---

## Files Affected

### High Priority (Most Corruption)
1. **assessment_results.py** - 157 B904 + 159 syntax errors
   - Multiple corruption patterns
   - Largest file in codebase
   - Critical for assessments

2. **behavioral_patterns.py** - 42 B904 + 42 syntax errors
   - Extensive decorator insertion
   - Complex pattern matching

3. **api_fuzzer.py** - 17 B904 + 17 syntax errors
   - Test file with intentional malformed inputs
   - May not need fixing (could be test cases)

### Medium Priority
4-17. **14 additional endpoint files** - ~150 B904 + syntax errors combined
   - behavioral_analytics.py
   - assessment_routes.py
   - behavioral_analysis.py
   - reports.py
   - templates.py
   - scoring.py
   - anonymous_feedback.py
   - backups.py
   - billing.py
   - clinical_assessments.py
   - communication_analysis.py
   - email_connections.py
   - gdpr.py
   - monitoring.py

**Total Impact:** ~370 B904 errors blocked by syntax corruption

---

## Automated Fix Attempt Results

### Script Created: `scripts/fix_decorator_insertion.py`

**Test Results:**
- ✅ Successfully fixed Pattern 1 (decorator in raise statement)
- ⚠️ Only fixed 1 instance in assessment_results.py
- ⚠️ 158 syntax errors remain

**Limitations:**
1. Pattern complexity requires multiple passes
2. Some corruption may require manual review
3. Risk of breaking legitimate code if patterns aren't precise enough

---

## Recommended Strategy

### Option A: Manual Review with IDE Assistance ⭐ RECOMMENDED

**Pros:**
- Safe and controlled
- Can handle complex patterns
- IDE can help identify issues

**Steps:**
1. Open corrupted file in IDE (VS Code, PyCharm)
2. Use IDE's syntax highlighting to identify errors
3. Search for pattern: `@check_rate_limit` in middle of functions
4. Manually remove decorators from inappropriate locations
5. Verify with `ruff check` after each fix

**Estimated Time:** 2-3 hours for high-priority files

### Option B: Restore from Git History

**Pros:**
- Guaranteed to work if corruption is recent
- Fast rollback

**Cons:**
- May lose legitimate changes
- Need to identify commit that introduced corruption

**Steps:**
1. Use `git log` to find when corruption was introduced
2. `git checkout <commit-before-corruption> -- <file>`
3. Verify and re-apply any legitimate changes

### Option C: Incremental Manual Fixing

**For each corrupted file:**
1. Run `ruff check <file> --output-format=concise`
2. Note first syntax error line number
3. Go to that line in editor
4. Fix the visible corruption
5. Re-run ruff check
6. Repeat until clean
7. Then fix B904 errors

**Estimated Time:** 5-10 minutes per file

---

## Quick Wins (Files to Fix First)

### 1. assessment_routes.py (10 B904 errors)
**Corruption:** Minimal, focused
**Impact:** Unlocks 10 B904 errors quickly
**Time:** 10-15 minutes

### 2. behavioral_analytics.py (4 B904 errors)
**Corruption:** Limited
**Impact:** Quick win
**Time:** 5-10 minutes

### 3. anonymous_feedback.py (8 B904 errors)
**Corruption:** Moderate
**Impact:** Good ROI
**Time:** 15-20 minutes

**Total Quick Wins:** 22 B904 errors in ~45 minutes

---

## Script Usage

### Test on Single File (Dry Run)
```bash
python scripts/fix_decorator_insertion.py --file app/api/v1/endpoints/assessment_routes.py --dry-run
```

### Apply Fix to File
```bash
python scripts/fix_decorator_insertion.py --file app/api/v1/endpoints/assessment_routes.py
```

### Verify Fix
```bash
ruff check app/api/v1/endpoints/assessment_routes.py --select B904
```

---

## Prevention

### Add Pre-Commit Hook

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff (syntax & B904)
        entry: ruff check --select F401,E999,B904
        language: system
```

### Enable in CI/CD

```yaml
# .github/workflows/lint.yml
- name: Check syntax and B904
  run: ruff check --select F401,E999,B904
```

---

## Next Steps

### Immediate
1. ✅ Script created and tested
2. ⚠️ Need to improve script or use manual approach
3. **Recommendation:** Manual fix for high-priority files

### Short Term
1. Fix assessment_routes.py (quick win)
2. Fix behavioral_analytics.py (quick win)
3. Fix anonymous_feedback.py (quick win)
4. Apply B904 fixes to unlocked files (~22 more errors)

### Long Term
1. Develop more sophisticated automated fix
2. Restore corrupted files from git if possible
3. Enable syntax checking in CI/CD

---

## Conclusion

**Current Status:**
- Automated script created ✅
- Limited success (1 pattern fixed) ⚠️
- Manual approach recommended for remaining files ⭐

**Best Path Forward:**
1. Manual fix quick-win files (45 min for 22 B904 errors)
2. Apply B904 fixes (~30 min for 22 errors)
3. **Total: 75 minutes for 52 B904 fixes** (10% reduction!)

**Alternative:** Restore from git history if corruption is recent

---

**Generated:** 2025-01-08
**Status:** Ready for manual fixes or git restore
