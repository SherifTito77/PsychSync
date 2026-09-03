# Code Cleanup Guide

## Priority Actions Completed ✅

### 1. Syntax Errors Fixed
- **Fixed:** 11 out of 26 endpoint files with syntax errors
- **Method:** Automated removal of 63 misplaced docstrings
- **Remaining:** 15 files need manual review (different error patterns)

**Fixed Files:**
- ✅ ab_testing.py (2 fixes)
- ✅ build_analysis.py (8 fixes)
- ✅ sql_audit.py (10 fixes)
- ✅ caching_config.py (7 fixes)
- ✅ feature_requests.py (8 fixes)
- ✅ activation.py (5 fixes)
- ✅ jira_integration.py (8 fixes)
- ✅ code_quality.py (9 fixes)
- ✅ breaking_changes.py (6 fixes)
- ✅ predictions.py (1 fix - decorator issue)
- ✅ health.py (1 fix - duplicate kwargs)

**Still Need Manual Fix (15 files):**
```
app/api/v1/endpoints/assessments.py
app/api/v1/endpoints/data_export.py
app/api/v1/endpoints/hris_connector.py
app/api/v1/endpoints/intervention_effectiveness.py
app/api/v1/endpoints/nlp_routes.py
app/api/v1/endpoints/optimizer.py
app/api/v1/endpoints/query_performance.py
app/api/v1/endpoints/reliability_validity.py
app/api/v1/endpoints/security_monitoring.py
app/api/v1/endpoints/skill_gap_analysis.py
app/api/v1/endpoints/slack.py
app/api/v1/endpoints/succession_planning.py
app/api/v1/endpoints/team_optimization.py
app/api/v1/endpoints/templates.py
app/api/v1/endpoints/voice_video_analysis.py
```

**To Fix Remaining Files:**
```bash
# Check specific error for each file
python3 -m py_compile app/api/v1/endpoints/FILENAME.py
```

---

### 2. Test Coverage Generated ✅
- **Generated:** 72 test files
- **Coverage:** Increased from 6% (39 endpoints) to scaffolding for 525 endpoints
- **Status:** Test scaffolding created, needs implementation

**Generated Test Files:**
```bash
ls -lh tests/api/test_*.py
```

**Next Steps:**
1. Implement actual test logic in generated scaffolds
2. Add test data and assertions
3. Run tests: `pytest tests/api/ -v`

---

### 3. Dead Code Analysis ⚠️
- **Status:** Report generated, but **DO NOT auto-remove**
- **Issue:** Agent has false positives (reports used imports as unused)
- **Recommendation:** Manual review only

**Files with "Unused" Imports (Verify Before Removing):**
```bash
# Review specific file
cat reports/dead_code.json | jq '.unused_imports[] | select(.file == "app/core/tasks.py")'

# Manual verification
grep -r "ImportName" app/  # Check if it's actually used
```

**Dead Code Report Location:**
```bash
cat reports/dead_code.json | jq '.'
```

---

## Manual Review Commands

### Check Specific File Syntax
```bash
python3 -m py_compile app/api/v1/endpoints/YOUR_FILE.py
```

### Find All Still-Broken Files
```bash
for file in app/api/v1/endpoints/*.py; do
  if ! python3 -m py_compile "$file" 2>/dev/null; then
    echo "$file"
  fi
done
```

### Verify Import Usage
```bash
# Check if import is used anywhere
grep -r "ImportName" app/

# Count occurrences
grep -c "ImportName" app/core/specific_file.py
```

---

## Summary

| Task | Status | Result |
|------|--------|--------|
| Fix Syntax Errors | 🔄 42% complete | 11/26 files fixed |
| Generate Tests | ✅ Complete | 525 test scaffolds created |
| Clean Dead Code | ⚠️ Review needed | False positives - manual review only |

---

## Next Steps (Recommended Order)

1. **Fix Remaining 15 Syntax Errors** (Blocker)
   - Each file needs individual inspection
   - Run: `python3 -m py_compile app/api/v1/endpoints/FILENAME.py`
   - Fix reported errors manually

2. **Implement Generated Tests** (Quality)
   - 72 test files created with scaffolding
   - Add actual test logic and assertions
   - Run: `pytest tests/api/ -v`

3. **Manual Dead Code Review** (Optional)
   - Do NOT use `--auto-fix`
   - Manually verify each "unused" import
   - Only remove if certain it's unused

---

## Generated Reports

All reports saved to `reports/`:
- `dead_code.json` - Unused code analysis
- `doc_coverage.json` - Documentation: 85.7% coverage ⬆️
- `api_contract_drift.json` - API drifts detected
- `log_anomalies.json` - Error rate analysis

---

## Scripts Created

1. `fix_syntax_errors.py` - Fixes misplaced docstrings
2. `fix_duplicate_kwargs.py` - Fixes duplicate keyword arguments
3. `agents/dead_code_agent.py` - Fixed to track type annotations
4. `agents/auto_test_agent.py` - Generates test scaffolding

Use these scripts for future maintenance!
