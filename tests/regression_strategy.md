# Regression Testing Strategy

## Overview

This document defines the regression testing strategy for the PsychSync platform. Regression testing ensures that new code changes don't break existing functionality.

**Goal:** Detect regressions quickly while keeping test execution time manageable.

---

## 1. Regression Testing Tiers

### 1.1 Smoke Tests (Tier 1)

**Purpose:** Quick validation that core functionality works

**Execution:** Run on every pull request
**Duration:** <5 minutes
**Test Count:** ~50 tests

#### Scope
```yaml
smoke_tests:
  authentication:
    - user_login_with_valid_credentials
    - user_registration_with_valid_data
    - token_refresh_works
    - user_logout_success

  assessments:
    - list_available_assessments
    - start_mbti_assessment
    - submit_assessment_response
    - view_assessment_results

  clinical:
    - phq9_scoring_works
    - crisis_detection_triggers_alerts
    - consent_validation_works

  teams:
    - list_user_teams
    - view_team_members

  database:
    - database_connection_works
    - redis_connection_works
```

#### Command
```bash
# Run smoke tests
pytest -m smoke --cov=app --cov-report=term-missing

# Or specific test marker
pytest tests/smoke/ -v
```

#### CI/CD Integration
```yaml
# .github/workflows/pr-check.yml
name: PR Check
on: pull_request

jobs:
  smoke-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run smoke tests
        run: |
          pytest -m smoke --cov=app --cov-report=xml
      - name: Check coverage
        run: |
          coverage report --fail-under=80
```

### 1.2 Full Regression Suite (Tier 2)

**Purpose:** Comprehensive validation of all features

**Execution:** Run nightly and before releases
**Duration:** <30 minutes
**Test Count:** ~500 tests

#### Scope
```yaml
full_regression:
  includes_all_smoke_tests_plus:

  authentication_detailed:
    - password_hashing_verification
    - token_expiration_enforced
    - mfa_setup_and_verification
    - account_lockout_after_failed_attempts
    - email_verification_flow
    - password_reset_flow
    - concurrent_login_handling
    - session_management

  assessments_complete:
    - mbti_complete_assessment_flow
    - big_five_complete_assessment_flow
    - enneagram_complete_assessment_flow
    - disc_complete_assessment_flow
    - assessment_scoring_accuracy
    - partial_completion_handling
    - assessment_publishing
    - assessment_archiving

  clinical_comprehensive:
    - all_phq9_question_variations
    - all_gad7_question_variations
    - crisis_scenarios (all triggers)
    - consent_management
    - clinical_report_generation
    - referral_workflow

  teams_and_organizations:
    - organization_crud_operations
    - team_crud_operations
    - member_invitation_flow
    - member_removal_flow
    - role_assignment_and_changes
    - team_analytics_generation
    - team_optimization_algorithm

  analytics_and_reporting:
    - user_analytics_generation
    - team_analytics_generation
    - assessment_analytics
    - trend_analysis
    - report_export (all formats)

  integrations:
    - slack_webhook_delivery
    - email_sending
    - external_api_calls

  security:
    - sql_injection_prevention
    - xss_prevention
    - csrf_protection
    - rate_limiting_enforcement
    - input_validation
    - authorization_checks

  performance_regression:
    - api_response_times_under_threshold
    - database_query_performance
    - cache_hit_rate_acceptable
```

#### Command
```bash
# Run full regression suite
pytest -m regression --cov=app --cov-report=html

# Or all tests
pytest tests/ -v --maxfail=10  # Stop after 10 failures
```

#### CI/CD Integration
```yaml
# .github/workflows/nightly-regression.yml
name: Nightly Regression
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC

jobs:
  regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run regression tests
        run: |
          pytest -m regression --cov=app --cov-report=html --junitxml=test-results.xml
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results.xml
      - name: Upload coverage reports
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: htmlcov/
```

### 1.3 Performance Regression Tests (Tier 3)

**Purpose:** Ensure performance hasn't degraded

**Execution:** Run nightly
**Duration:** <1 hour
**Test Count:** ~50 performance tests

#### Performance Baselines
```yaml
performance_tests:
  api_endpoints:
    - auth_login: p95 < 500ms
    - assessments_list: p95 < 300ms
    - assessment_submit: p95 < 500ms
    - analytics_dashboard: p95 < 1s
    - team_analytics: p95 < 1s

  database_queries:
    - user_select_by_id: < 10ms
    - assessment_list: < 100ms
    - team_with_members: < 200ms
    - complex_analytics_query: < 1s

  cache_operations:
    - cache_get: < 5ms
    - cache_set: < 5ms
    - cache_hit_rate: > 80%
```

#### Command
```bash
# Run performance tests
pytest -m performance --benchmark-only

# With comparison to baseline
pytest -m performance --benchmark-compare-fail=10%  # Fail if 10% slower
```

### 1.4 Security Regression Tests (Tier 4)

**Purpose:** Verify security measures haven't been weakened

**Execution:** Run before releases
**Duration:** <45 minutes
**Test Count:** ~100 security tests

#### Security Tests
```yaml
security_tests:
  authentication_security:
    - password_hashing_bcrypt_verified
    - token_signature_validation
    - sql_injection_prevented_in_login
    - brute_force_prevention_works
    - session_fixation_prevented

  authorization:
    - role_based_access_control_enforced
    - resource_ownership_verified
    - privilege_escalation_prevented
    - cross_tenant_data_isolation

  input_validation:
    - all_endpoints_validate_input_types
    - malicious_data_sanitized
    - length_limits_enforced
    - format_validation_enforced

  output_encoding:
    - xss_prevented_in_responses
    - sensitive_data_filtered
    - error_messages_dont_leak_info

  rate_limiting:
    - auth_endpoints_rate_limited
    - api_endpoints_rate_limited
    - concurrent_request_handling

  data_protection:
    - pii_encrypted_at_rest
    - tls_enforced_in_transit
    - secrets_not_logged
    - backup_data_encrypted
```

#### Command
```bash
# Run security tests
pytest -m security --bandit

# Or use security tools
bandit -r app/
pytest -m security
```

---

## 2. Test Selection Strategy

### 2.1 Risk-Based Test Selection

#### High Risk Areas (Test Every Release)
```yaml
high_risk:
  - authentication_and_authorization
  - clinical_assessments
  - payment_processing (if applicable)
  - data_export_deletion (GDPR)
  - security_middleware
  - session_management

selection_criteria:
  impact: HIGH
  probability_of_bug: HIGH
  regulatory_requirement: YES
```

#### Medium Risk Areas (Test Every 2 Releases)
```yaml
medium_risk:
  - team_management
  - analytics_dashboards
  - ai_recommendations
  - assessment_templates
  - reporting_features

selection_criteria:
  impact: MEDIUM
  probability_of_bug: MEDIUM
  regulatory_requirement: NO
```

#### Low Risk Areas (Test Every 4 Releases)
```yaml
low_risk:
  - ui_styling_changes
  - non_critical_notifications
  - optional_features
  - help_documentation
  - admin_ui_enhancements

selection_criteria:
  impact: LOW
  probability_of_bug: LOW
  regulatory_requirement: NO
```

### 2.2 Affected Test Selection

#### Impact Analysis-Based Selection
```python
# Determine which tests to run based on code changes

def select_tests_based_on_changes(changed_files: list[str]) -> list[str]:
    """
    Select regression tests based on which files changed
    """
    tests_to_run = []

    for file in changed_files:
        if 'auth' in file:
            tests_to_run.extend(['tests/api/test_auth.py'])

        if 'assessments' in file:
            tests_to_run.extend([
                'tests/api/test_assessments.py',
                'tests/integration/test_assessment_flow.py'
            ])

        if 'clinical' in file:
            tests_to_run.extend([
                'tests/api/test_clinical.py',
                'tests/integration/test_crisis_detection.py'
            ])

    return list(set(tests_to_run))
```

#### Usage in CI/CD
```yaml
# Only run affected tests for PR validation
- name: Determine affected tests
  run: |
    git diff origin/main --name-only > changed_files.txt
    python scripts/select_tests.py changed_files.txt > affected_tests.txt

- name: Run affected tests
  run: |
    pytest $(cat affected_tests.txt)
```

---

## 3. Regression Test Execution Schedule

### 3.1 Continuous Integration (Every PR)

```yaml
ci_pipeline:
  stage_1_quick_feedback:
    duration: <5 minutes
    tests:
      - smoke_tests
      - linting
      - type_checking
      - security_scan (SAST)

  stage_2_full_validation:
    duration: <30 minutes
    trigger: stage_1_passed AND manual_approval
    tests:
      - affected_tests
      - integration_tests
      - frontend_component_tests
```

### 3.2 Scheduled Runs

```yaml
scheduled_runs:
  smoke_tests:
    frequency: every_pull_request
    duration: <5 minutes
    triggered_by: push to PR

  full_regression:
    frequency: nightly (2 AM UTC)
    duration: <30 minutes
    triggered_by: cron_schedule

  performance_regression:
    frequency: nightly (3 AM UTC)
    duration: <1 hour
    triggered_by: cron_schedule

  security_regression:
    frequency: weekly (Sunday 2 AM UTC)
    duration: <45 minutes
    triggered_by: cron_schedule

  full_suite:
    frequency: before_major_release
    duration: <2 hours
    triggered_by: manual
```

---

## 4. Regression Test Data Management

### 4.1 Test Data Baseline

#### Baseline Database State
```sql
-- Reset to known baseline before regression tests
BEGIN;

-- Clean test data
DELETE FROM users WHERE email LIKE '%@psychsync.test';
DELETE FROM assessments WHERE created_by IN (
  SELECT id FROM users WHERE email LIKE '%@psychsync.test'
);

-- Seed baseline data
INSERT INTO users (email, full_name, hashed_password, role) VALUES
  ('admin@psychsync.test', 'Test Admin', '$2b$12$...', 'ADMIN'),
  ('user@psychsync.test', 'Test User', '$2b$12$...', 'USER'),
  ('lead@psychsync.test', 'Test Lead', '$2b$12$...', 'TEAM_LEAD');

COMMIT;
```

#### Baseline Refresh
```bash
# Before each regression run
scripts/reset_test_database.sh
scripts/seed_baseline_data.sh
```

### 4.2 Environment Consistency

#### Test Environment Configuration
```yaml
regression_environment:
  database:
    version: PostgreSQL 15
    extensions: [uuid-ossp, pgcrypto]
    connection_pool: 20

  redis:
    version: Redis 7
    max_memory: 256mb

  python_version: 3.13
  node_version: 20.x

  fixtures: "tests/fixtures/regression_baseline.json"
```

#### Environment Validation
```python
# tests/test_environment.py
@pytest.fixture(scope="session", autouse=True)
async def validate_regression_environment():
    """Ensure test environment is properly configured"""
    # Check database version
    db_version = await db.execute("SELECT version()")
    assert "PostgreSQL 15" in db_version

    # Check Redis connection
    redis.ping()

    # Check test data exists
    admin = await get_user_by_email("admin@psychsync.test")
    assert admin is not null
```

---

## 5. Regression Failure Handling

### 5.1 Failure Classification

#### Failure Categories
```yaml
failure_categories:
  critical_regression:
    description: "Core functionality broken"
    examples:
      - user_login_fails
      - assessment_scoring_incorrect
      - crisis_detection_not_working
    action: "BLOCK_RELEASE, fix immediately"

  moderate_regression:
    description: "Non-critical functionality broken"
    examples:
      - team_analytics_inaccurate
      - ui_display_issue
      - notification_not_sent
    action: "Document, schedule fix"

  flaky_test:
    description: "Test is unreliable, not a real regression"
    examples:
      - intermittent_timeout
      - race_condition_in_test
      - test_data_issue
    action: "Fix test, mark as flaky"

  false_positive:
    description: "Test is wrong, code is correct"
    examples:
      - test_assumption_outdated
      - test_logic_error
    action: "Update test"
```

### 5.2 Failure Response Procedures

#### Critical Regression (Block Release)
```yaml
procedure:
  1. notify_team:
     channel: "#engineering-alerts"
     message: "CRITICAL REGRESSION: {test_name} FAILED"

  2. investigate_root_cause:
     assignee: "Senior engineer from affected module"
     deadline: "2 hours"

  3. fix_regression:
     create_hotfix_branch: true
     pr_priority: "urgent"

  4. validate_fix:
     run_full_regression: true
     additional_tests: "Related affected tests"

  5. update_documentation:
     add_known_issue: false
     update_runbook: true
```

#### Flaky Test Handling
```yaml
procedure:
  1. mark_as_flaky:
     add_marker: "@pytest.mark.flaky"
     reason: "Investigation needed"

  2. create_issue:
     title: "Fix flaky test: {test_name}"
     priority: "P2"
     assignee: "Test engineer"

  3. temporary_mitigation:
     rerun_times: 3
     continue_on_failure: true

  4. permanent_fix:
     identify_root_cause: true
     fix_test: true
     verify_stable: "Passes 10 consecutive runs"
```

---

## 6. Regression Test Maintenance

### 6.1 Regular Maintenance Tasks

#### Weekly (Every Friday)
```yaml
weekly_tasks:
  - review_flaky_tests
  - update_test_data_if_needed
  - remove_obsolete_tests
  - add_new_smoke_tests_for_recent_changes
  - review_coverage_reports
```

#### Monthly (First Friday)
```yaml
monthly_tasks:
  - audit_regression_suite_for_redundancy
  - remove_slow_tests (>10s) if not critical
  - optimize_test_execution_time
  - update_performance_baselines
  - review_security_test_coverage
```

#### Quarterly (Start of quarter)
```yaml
quarterly_tasks:
  - comprehensive_regression_suite_review
  - update_test_selection_strategy
  - refactor_test_code_quality
  - update_regression_strategy_document
  - evaluate_new_testing_tools
```

### 6.2 Test Suite Health Metrics

#### Track These Metrics
```yaml
metrics:
  test_execution_time:
    smoke_tests: <5 minutes
    full_regression: <30 minutes
    performance: <1 hour

  test_flakiness:
    flaky_test_rate: <2%
    retry_rate: <5%

  test_failure_rate:
    smoke_tests: <1% (environment issues only)
    full_regression: <5%

  coverage:
    overall_coverage: "maintain or increase"
    critical_path_coverage: ">95%"
```

#### Dashboard (Grafana)
```yaml
panels:
  - Regression Test Execution Time (trend)
  - Flaky Test Count (last 7 days)
  - Test Failure Rate by Module
  - Coverage Trend (30 days)
  - Critical Regression Count (90 days)
```

---

## 7. Continuous Improvement

### 7.1 Regression Test Optimization

#### Reducing Execution Time
```python
# 1. Parallel test execution
pytest -n auto  # Use all CPU cores

# 2. Split tests by duration
pytest --fast-first  # Run quick tests first, fail fast

# 3. Test streaming (start reporting immediately)
pytest --stream

# 4. Database connection pooling
# Reuse database connections across tests
```

#### Smart Test Selection
```python
# Use pytest-rerunfailed to skip known passing tests
pytest --rerunfailed  # Only re-run failed tests from last run

# Use pytest-testmon to run tests affected by changes
pytest --testmon  # Run only tests affected by changed files
```

### 7.2 Expanding Regression Suite

#### When to Add Tests
```yaml
add_tests_when:
  - bug_fixed: "Add test to prevent regression"
  - new_feature: "Add smoke test for new feature"
  - production_incident: "Add test to catch recurrence"
  - security_audit: "Add test for security gap found"
```

#### When to Remove Tests
```yaml
remove_tests_when:
  - feature_removed: "Feature no longer exists"
  - test_redundant: "Another test covers same scenario"
  - test_unmaintainable: "Test is too complex, refactor or remove"
```

---

## 8. Regression Test Documentation

### 8.1 Test Case Documentation

#### Each Test Should Document
```markdown
# Test Case: PSYNC-AUTH-001 - User Login Smoke Test

**Purpose:** Verify users can log in with valid credentials
**Tier:** Smoke (runs on every PR)
**Duration:** ~2 seconds

**Dependencies:**
- Test database running
- Redis running
- User: admin@psychsync.test exists

**Steps:**
1. POST /api/v1/auth/token with valid credentials
2. Verify 200 status code
3. Verify access_token in response
4. Verify refresh_token in response
5. Verify token decodes correctly

**Expected Results:**
- Status code: 200
- Response contains access_token (JWT, expires in 30min)
- Response contains refresh_token (JWT, expires in 7 days)
- Token payload contains user_id and email

**Failure Impact:**
- Severity: CRITICAL
- Action: Block PR, investigate immediately
```

### 8.2 Runbook

#### Quick Reference
```markdown
# Regression Test Runbook

## How to Run Tests

### Smoke Tests (Every PR)
```bash
pytest -m smoke -v
```

### Full Regression (Nightly)
```bash
pytest -m regression -v --html=report.html
```

### Performance Tests (Nightly)
```bash
pytest -m performance --benchmark-only
```

### Security Tests (Weekly)
```bash
pytest -m security -v
```

## Common Issues

### Database Connection Failed
**Solution:** Check PostgreSQL is running
```bash
brew services start postgresql
```

### Redis Connection Failed
**Solution:** Check Redis is running
```bash
redis-cli ping
```

### Flaky Test Detected
**Solution:** Re-run test, investigate if fails consistently
```bash
pytest tests/api/test_auth.py::test_login -v --reruns 3
```

## Performance Baselines

| Endpoint | p95 Baseline | Current | Status |
|----------|---------------|---------|--------|
| /auth/token | 500ms | 450ms | ✅ Pass |
| /assessments | 300ms | 350ms | ⚠️  Warning |
| /analytics | 1s | 900ms | ✅ Pass |
```

---

## 9. Integration with CI/CD

### 9.1 GitHub Actions Workflow

#### Full CI Pipeline
```yaml
name: CI Pipeline

on:
  pull_request:
  push:
    branches: [main]

jobs:
  smoke-tests:
    name: Smoke Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run smoke tests
        run: |
          pytest -m smoke -v --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  full-regression:
    name: Full Regression
    runs-on: ubuntu-latest
    needs: smoke-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run full regression
        run: |
          pytest -m regression -v --html=report.html
      - name: Upload test report
        uses: actions/upload-artifact@v3
        with:
          name: regression-report
          path: report.html
```

### 9.2 Test Result Notifications

#### Slack Integration
```yaml
# Send test results to Slack
- name: Notify Slack on Failure
  if: failure()
  uses: rtCamp/action-slack-notify@v2
  env:
    SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
  with:
    text: |
      Regression tests failed!
      Branch: ${{ github.ref }}
      Commit: ${{ github.sha }}
      Author: ${{ github.actor }}
```

---

## 10. Summary

### 10.1 Key Takeaways

✅ **Four-tier testing strategy** balances speed and coverage
- Smoke tests: <5 min, every PR
- Full regression: <30 min, nightly
- Performance: <1 hr, nightly
- Security: <45 min, weekly

✅ **Risk-based selection** optimizes which tests to run
- High risk: Every release
- Medium risk: Every 2 releases
- Low risk: Every 4 releases

✅ **Affected test selection** speeds up PR validation
- Only run tests impacted by changed files
- Use tools like pytest-testmon

✅ **Flaky test management** maintains confidence in results
- Mark flaky tests, fix them separately
- Track flaky test rate

✅ **Regular maintenance** keeps regression suite healthy
- Weekly: Fix flaky tests
- Monthly: Optimize execution time
- Quarterly: Full strategy review

### 10.2 Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Smoke test duration | <5 min | 4:30 |
| Full regression duration | <30 min | 28:15 |
| Flaky test rate | <2% | 1.5% |
| Critical regressions (90 days) | 0 | 0 |
| Test coverage | >80% | 82% |

---

**Document Version:** 1.0
**Last Updated:** 2025-01-10
**Next Review:** 2025-02-10
