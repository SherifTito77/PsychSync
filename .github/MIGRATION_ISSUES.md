# Bulk Migration Issues: Structured Error Handling

> **Created:** January 13, 2026
> **Purpose:** GitHub issues for migrating to structured error handling
> **Total Files:** 17 files with generic HTTPException

---

## Priority 1: Critical Authentication & Team Files

### Issue #1: Migrate `app/api/v1/endpoints/auth.py` ✅ COMPLETED

**Status:** Already migrated in Phase 1
**Migrations:**
- ✅ Rate limit exceeded → `RateLimitExceededError`
- ✅ Missing fields → `MissingFieldError`
- ✅ Invalid credentials → `InvalidCredentialsError`

---

### Issue #2: Migrate `app/api/v1/teams.py` ✅ COMPLETED

**Status:** Already migrated in Phase 1
**Migrations:**
- ✅ Team not found → `TeamNotFoundError`

---

## Priority 2: High-Traffic Endpoints

### Issue #3: Migrate `app/api/v1/endpoints/personality_assessments.py`

**File:** `app/api/v1/endpoints/personality_assessments.py`
**Estimated:** 2 hours
**Priority:** High

**HTTPExceptions to migrate:**
- 404: Assessment not found → `AssessmentNotFoundError`
- 400: Invalid assessment data → `ValidationError`
- 409: Assessment already submitted → `ResponseAlreadySubmittedError`

**Steps:**
1. Add imports from `app.core.exceptions`
2. Search for all `raise HTTPException` calls
3. Replace with appropriate structured exceptions
4. Test assessment endpoints
5. Update tests

**Acceptance Criteria:**
- [ ] All HTTPException calls replaced
- [ ] Tests pass
- [ ] Manual testing completed

---

### Issue #4: Migrate `app/api/v1/endpoints/feature_requests.py`

**File:** `app/api/v1/endpoints/feature_requests.py`
**Estimated:** 1 hour
**Priority:** Medium

**HTTPExceptions to migrate:**
- 404: Feature request not found → `RecordNotFoundError`
- 403: Access denied → `ForbiddenError`
- 400: Invalid input → `ValidationError`

**Steps:**
1. Add imports
2. Replace HTTPException calls
3. Test feature request endpoints

**Acceptance Criteria:**
- [ ] All HTTPException calls replaced
- [ ] Tests pass

---

### Issue #5: Migrate `app/api/v1/endpoints/monitoring.py`

**File:** `app/api/v1/endpoints/monitoring.py`
**Estimated:** 1.5 hours
**Priority:** Medium

**HTTPExceptions to migrate:**
- 404: Service not found → `RecordNotFoundError`
- 503: Service unavailable → `ServiceUnavailableError`
- 500: Internal error → `InternalServerError`

**Steps:**
1. Add imports
2. Replace HTTPException calls
3. Test monitoring endpoints

**Acceptance Criteria:**
- [ ] All HTTPException calls replaced
- [ ] Tests pass

---

## Priority 3: Data Export & Analytics

### Issue #6: Migrate `app/api/v1/endpoints/data_export.py`

**File:** `app/api/v1/endpoints/data_export.py`
**Estimated:** 1 hour
**Priority:** Medium

**HTTPExceptions to migrate:**
- 400: Invalid export format → `ValidationError`
- 403: Export not allowed → `ForbiddenError`
- 429: Rate limit exceeded → `RateLimitExceededError`

**Steps:**
1. Add imports
2. Replace HTTPException calls
3. Test export endpoints

**Acceptance Criteria:**
- [ ] All HTTPException calls replaced
- [ ] Tests pass

---

### Issue #7: Migrate `app/api/v1/endpoints/query_performance.py`

**File:** `app/api/v1/endpoints/query_performance.py`
**Estimated:** 1 hour
**Priority:** Low

**HTTPExceptions to migrate:**
- 404: Query not found → `RecordNotFoundError`
- 400: Invalid query → `ValidationError`

**Steps:**
1. Add imports
2. Replace HTTPException calls
3. Test query endpoints

**Acceptance Criteria:**
- [ ] All HTTPException calls replaced
- [ ] Tests pass

---

## Priority 4: Integration & Security

### Issue #8: Migrate `app/api/v1/endpoints/intervention_effectiveness.py`

**File:** `app/api/v1/endpoints/intervention_effectiveness.py`
**Estimated:** 1 hour
**Priority:** Medium

**HTTPExceptions to migrate:**
- 404: Intervention not found → `RecordNotFoundError`
- 400: Invalid data → `ValidationError`

**Steps:**
1. Add imports
2. Replace HTTPException calls
3. Test endpoints

**Acceptance Criteria:**
- [ ] All HTTPException calls replaced
- [ ] Tests pass

---

### Issue #9: Migrate `app/api/v1/endpoints/security_monitoring.py`

**File:** `app/api/v1/endpoints/security_monitoring.py`
**Estimated:** 1.5 hours
**Priority:** High

**HTTPExceptions to migrate:**
- 403: Access denied → `ForbiddenError`
- 404: Security event not found → `RecordNotFoundError`
- 429: Rate limit exceeded → `RateLimitExceededError`

**Steps:**
1. Add imports
2. Replace HTTPException calls
3. Test security endpoints

**Acceptance Criteria:**
- [ ] All HTTPException calls replaced
- [ ] Tests pass

---

## Priority 5: Additional Files

### Issue #10: Migrate `app/api/v1/endpoints/ab_testing.py`

**Estimated:** 1 hour
**Priority:** Low

### Issue #11: Migrate `app/api/v1/endpoints/behavioral_analysis.py`

**Estimated:** 1 hour
**Priority:** Low

### Issue #12: Migrate `app/api/v1/endpoints/behavioral_analytics.py`

**Estimated:** 1 hour
**Priority:** Low

### Issue #13: Migrate `app/api/v1/endpoints/jira_integration.py`

**Estimated:** 1 hour
**Priority:** Low

### Issue #14: Migrate `app/api/v1/endpoints/code_quality.py`

**Estimated:** 1 hour
**Priority:** Low

### Issue #15: Migrate `app/api/v1/endpoints/backups.py`

**Estimated:** 1 hour
**Priority:** Low

### Issue #16: Migrate `app/api/v1/endpoints/data_export_secure.py`

**Estimated:** 1 hour
**Priority:** Medium

### Issue #17: Migrate `app/api/v1/endpoints/sql_audit.py`

**Estimated:** 1 hour
**Priority:** Low

---

## Migration Tracking Dashboard

### Overall Progress

| Priority | Total Files | Completed | In Progress | Pending |
|----------|-------------|-----------|-------------|---------|
| 1 (Critical) | 2 | 2 | 0 | 0 |
| 2 (High) | 3 | 0 | 0 | 3 |
| 3 (Medium) | 3 | 0 | 0 | 3 |
| 4 (Security) | 2 | 0 | 0 | 2 |
| 5 (Low) | 7 | 0 | 0 | 7 |
| **TOTAL** | **17** | **2** | **0** | **15** |

**Completion:** 12% (2/17 files)

### Estimated Effort

- **Completed:** 30 minutes (2 files)
- **Remaining:** ~15 hours (15 files)
- **Total:** ~15.5 hours

### Sprint Allocation

**Sprint 1 (This Week):**
- Issue #3: personality_assessments.py (2 hours)
- Issue #4: feature_requests.py (1 hour)
- Issue #9: security_monitoring.py (1.5 hours)

**Sprint 2 (Next Week):**
- Issue #5: monitoring.py (1.5 hours)
- Issue #6: data_export.py (1 hour)
- Issue #8: intervention_effectiveness.py (1 hour)

**Sprint 3 (Week 3):**
- Remaining 9 files (9 hours)

---

## How to Create GitHub Issues from This

### Option 1: Manual Creation

For each issue above:
1. Go to GitHub Issues
2. Click "New Issue"
3. Use template: `.github/ISSUE_TEMPLATE/MIGRATION_TEMPLATE.md`
4. Fill in the details from the issue description above
5. Assign to developer
6. Add to sprint

### Option 2: Bulk Create (GitHub CLI)

```bash
# Install GitHub CLI
brew install gh

# Login
gh auth login

# Create issues from script
./scripts/create_migration_issues.py
```

### Option 3: Copy-Paste Template

For each file, copy this template:

```markdown
# Migrate [FILE_NAME] to Structured Error Handling

## Goal
Migrate all generic HTTPException calls to use structured exceptions

## File
**Path:** `[FILE_PATH]`
**Lines:** ~[X]
**HTTPExceptions:** [N]

## HTTPExceptions to Migrate
1. Line [XX]: [Description]
2. Line [XX]: [Description]

## Steps
1. Add imports
2. Replace HTTPExceptions
3. Test

## Acceptance Criteria
- [ ] All HTTPException calls replaced
- [ ] Tests pass

**Estimated:** [X] hours
**Priority:** [High/Medium/Low]
**Assigned to:** @[username]
```

---

## Notes

- All issues use the migration template: `.github/ISSUE_TEMPLATE/MIGRATION_TEMPLATE.md`
- Reference documentation: `docs/developer/ERROR_CODE_QUICK_REFERENCE.md`
- Training materials: `docs/training/TEAM_TRAINING_ERROR_HANDLING.md`
- Questions? Ask in #backend-dev

---

**Created:** January 13, 2026
**Next Review:** Weekly standups
**Completion Target:** 3 weeks (by February 3, 2026)
