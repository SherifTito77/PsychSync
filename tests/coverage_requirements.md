# Test Coverage Requirements

## Overview

This document defines the minimum test coverage requirements for the PsychSync platform. Coverage targets are based on risk assessment, regulatory requirements (HIPAA), and industry best practices.

**Coverage Measurement Tools:**
- Backend: `pytest-cov` (Python)
- Frontend: `Vitest coverage` (TypeScript/React)

---

## 1. Overall Coverage Targets

### 1.1 Backend Coverage

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Overall Line Coverage** | >80% | Industry standard for quality software |
| **Overall Branch Coverage** | >75% | Ensures conditional logic is tested |
| **Critical Path Coverage** | >95% | High-risk features need near-complete coverage |
| **Security Module Coverage** | >90% | Security-critical code needs thorough testing |
| **Clinical Module Coverage** | 100% | HIPAA compliance requires complete testing |

### 1.2 Frontend Coverage

| Component Type | Target | Rationale |
|---------------|--------|-----------|
| **Overall Line Coverage** | >75% | Lower than backend due to UI complexity |
| **Context Providers** | >90% | Critical state management logic |
| **Authentication Flows** | >90% | Security-critical user interactions |
| **Assessment Pages** | >85% | Core user-facing functionality |
| **Clinical Assessment Pages** | >95% | HIPAA compliance for clinical features |
| **Form Components** | >85% | Complex user interactions |
| **Dashboard Components** | >80% | Complex UI with many states |
| **Utility Functions** | >90% | Pure functions, easy to test thoroughly |

---

## 2. Backend Module Coverage Breakdown

### 2.1 Authentication & Authorization (Target: >95%)

#### File: `app/services/auth_service.py`
```python
# Coverage requirements
def hash_password():                    # 100% - Security critical
def verify_password():                  # 100% - Security critical
def generate_access_token():            # 100% - Security critical
def generate_refresh_token():           # 100% - Security critical
def verify_token():                     # 100% - Security critical
def authenticate_user():                 # >95% - Core authentication logic
def register_user():                    # >95% - User creation
def logout_user():                      # >90% - Session cleanup
```

**Justification:** Authentication is the security foundation. Any bug here can compromise the entire system.

#### File: `app/services/two_factor_service.py`
```python
def generate_mfa_secret():              # >90%
def verify_mfa_code():                  # 100% - Security critical
def generate_backup_codes():            # >90%
def verify_backup_code():               # >90%
```

#### File: `app/services/session_service.py`
```python
def create_session():                   # >95%
def refresh_session():                  # >95%
def revoke_session():                   # >90%
def revoke_all_sessions():              # >90%
def get_active_sessions():              # >85%
```

### 2.2 Assessment Management (Target: >90%)

#### File: `app/services/assessment_service.py`
```python
def create_assessment():                # >90%
def get_assessment():                   # >90%
def update_assessment():                # >85%
def publish_assessment():               # >95% - Publishing is critical
def archive_assessment():               # >85%
def duplicate_assessment():             # >80%
```

#### File: `app/services/response_service.py`
```python
def start_response():                   # >95%
def save_response():                    # >95%
def submit_response():                  # >95% - Submission is critical
def get_user_responses():              # >85%
```

#### File: `app/services/scoring_service.py`
```python
def calculate_score():                  # >90%
def calculate_mbti_score():             # >95% - Core algorithm
def calculate_big_five_score():         # >95% - Core algorithm
def calculate_enneagram_score():        # >95% - Core algorithm
def normalize_scores():                 # >85%
```

**Justification:** Assessment scoring algorithms are core IP and must work correctly.

### 2.3 Clinical Assessments (Target: 100%)

#### File: `app/services/clinical_scoring_service.py`
```python
def calculate_phq9_score():             # 100% - HIPAA required
def calculate_gad7_score():             # 100% - HIPAA required
def detect_crisis():                    # 100% - Safety critical
def generate_clinical_report():         # 100% - HIPAA required
```

**Justification:** Clinical assessments are HIPAA-regulated. Any error could result in misdiagnosis or missed crisis detection. 100% coverage is non-negotiable.

#### File: `app/services/consent_service.py`
```python
def create_consent_record():            # 100% - HIPAA required
def verify_consent():                   # 100% - HIPAA required
def revoke_consent():                   # 100% - HIPAA required
def get_consent_history():              # >95%
```

**Justification:** HIPAA requires explicit, documented consent. All consent logic must be tested.

### 2.4 Team & Organization Management (Target: >85%)

#### File: `app/services/team_service.py`
```python
def create_team():                      # >90%
def add_member():                       # >90%
def remove_member():                    # >90%
def update_member_role():               # >85%
def get_team_analytics():               # >85%
```

#### File: `app/services/organization_service.py`
```python
def create_organization():              # >90%
def update_organization():              # >85%
def delete_organization():              # >80%
def get_organization_stats():           # >85%
```

### 2.5 AI & NLP Processing (Target: >85%)

#### File: `app/services/nlp_service.py`
```python
def analyze_sentiment():                # >85%
def extract_entities():                 # >85%
def classify_text():                    # >85%
def detect_language():                  # >80%
```

#### File: `app/services/analytics_service.py`
```python
def generate_user_analytics():          # >85%
def generate_team_analytics():          # >85%
def calculate_team_dynamics():          # >80%
def optimize_team_composition():        # >80%
```

### 2.6 Security & Compliance (Target: >90%)

#### File: `app/services/gdpr_service.py`
```python
def export_user_data():                 # 100% - GDPR required
def delete_user_data():                 # 100% - GDPR required
def anonymize_user_data():              # >95% - GDPR required
def get_data_processing_log():         # >90%
```

**Justification:** GDPR violations carry significant fines. All data handling logic must be thoroughly tested.

#### File: `app/core/security.py`
```python
def sanitize_input():                   # 100% - Security critical
def validate_sql_safe():                # 100% - Security critical
def detect_xss():                       # 100% - Security critical
def check_rate_limit():                 # >95%
```

### 2.7 Database CRUD Operations (Target: >90%)

#### File: `app/crud/crud_user.py`
```python
def get():                              # >95%
def get_multi():                        # >90%
def create():                           # >95%
def update():                           # >90%
def delete():                           # >90%
```

**Justification:** CRUD operations are the foundation of data access. Bugs here can lead to data loss or corruption.

### 2.8 API Endpoints (Target: 100%)

#### All API Endpoints
**Requirement:** 100% of all API endpoints must have at least one test

```python
# Minimum test for each endpoint:
def test_endpoint_returns_200():        # Happy path
def test_endpoint_handles_auth():       # Authorization check
def test_endpoint_validates_input():    # Input validation
```

**Justification:** Untested endpoints are potential security vulnerabilities and sources of production bugs.

---

## 3. Frontend Component Coverage Breakdown

### 3.1 Authentication Components (Target: >90%)

#### File: `frontend/src/contexts/AuthContext.tsx`
```typescript
const login():                           # >95% - Security critical
const logout():                          # >95% - Security critical
const register():                        # >95%
const refreshToken():                    # >95% - Security critical
const resetPassword():                   # >90%
```

#### File: `frontend/src/pages/Login.tsx`
```typescript
const render():                          # >85%
const handleSubmit():                    # >90%
const handleValidationErrors():          # >85%
const displayError():                    # >85%
```

### 3.2 Assessment Components (Target: >85%)

#### File: `frontend/src/pages/assessments/MBTIAssessmentPage.tsx`
```typescript
const render():                          # >85%
const startAssessment():                 # >90%
const submitResponse():                  # >90%
const navigateToNext():                  # >85%
const navigateToPrevious():              # >85%
const displayResults():                  # >90%
```

#### File: `frontend/src/contexts/AssessmentContext.tsx`
```typescript
const loadAssessment():                  # >90%
const saveResponse():                    # >90%
const submitAssessment():                # >95%
```

### 3.3 Clinical Assessment Components (Target: >95%)

#### File: `frontend/src/pages/clinical/ClinicalAssessment.tsx`
```typescript
const render():                          # >95%
const displayCrisisResources():         # 100% - Safety critical
const handleCrisisDetection():          # 100% - Safety critical
const validateConsent():                 # 100% - HIPAA required
```

**Justification:** Clinical assessments must display crisis resources correctly and handle consent properly. Any error is a safety/HIPAA issue.

### 3.4 Team Management Components (Target: >85%)

#### File: `frontend/src/contexts/TeamContext.tsx`
```typescript
const loadTeam():                        # >90%
const addMember():                       # >90%
const removeMember():                    # >90%
const updateMemberRole():                # >85%
```

### 3.5 Dashboard Components (Target: >80%)

#### File: `frontend/src/pages/Dashboard.tsx`
```typescript
const render():                          # >80%
const loadUserData():                    # >85%
const displayAnalytics():                # >80%
```

### 3.6 Utility Functions (Target: >90%)

#### File: `frontend/src/utils/apiClient.ts`
```typescript
const request():                         # >95%
const handleResponse():                  # >90%
const handleError():                     # >90%
```

#### File: `frontend/src/utils/validators.ts`
```typescript
const validateEmail():                   # >95%
const validatePassword():                # >95%
const validatePhoneNumber():             # >90%
```

---

## 4. Coverage Exclusions

### 4.1 Files That Should NOT Be Coverage-Measured

#### Generated Code
- Database migrations (`alembic/versions/*.py`)
- Auto-generated OpenAPI schemas
- Protocol buffer definitions
- GraphQL schema definitions

#### Configuration Files
- `app/core/config.py` (settings are loaded, not executed logic)
- `.env` files
- Configuration YAML/JSON files

#### Test Code
- All files in `tests/` directory
- Test fixtures and factories
- Mock objects

#### Third-Party Libraries
- `node_modules/`
- Virtual environment packages
- External dependencies

#### Development Tools
- Build scripts
- Development server configurations
- Hot module replacement code

### 4.2 Justification for Exclusions

**Generated Code:** Not written by humans, changes automatically. Testing it provides no value.

**Configuration:** Loaded at startup, not executable logic. Value comes from manual review, not coverage.

**Test Code:** Testing your tests provides diminishing returns. Focus coverage on production code.

**Third-Party:** Should be tested by their maintainers, not by your team.

---

## 5. Coverage Measurement & Reporting

### 5.1 Backend Coverage Measurement

#### Running Coverage with pytest
```bash
# Run all tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Generate HTML report
pytest --cov=app --cov-report=html

# Generate specific module coverage
pytest --cov=app.services.auth_service --cov-report=term-missing

# Generate branch coverage
pytest --cov=app --cov-branch --cov-report=term
```

#### Coverage Configuration (`.coveragerc` or `setup.cfg`)
```ini
[coverage:run]
source = app
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*
    */.venv/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False

[coverage:html]
directory = htmlcov

[coverage:xml]
output = coverage.xml
```

#### CI/CD Integration
```yaml
# .github/workflows/test.yml
- name: Run tests with coverage
  run: |
    pytest --cov=app --cov-report=xml --cov-report=term

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
    flags: unittests
    name: codecov-umbrella

- name: Check coverage thresholds
  run: |
    coverage report --fail-under=80
```

### 5.2 Frontend Coverage Measurement

#### Running Coverage with Vitest
```bash
# Run all tests with coverage
npm run test:coverage

# Run specific file coverage
npm run test:coverage -- src/components/Button.test.tsx

# Generate HTML report
npm run test:coverage -- --reporter=html
```

#### Vitest Configuration (`vitest.config.ts`)
```typescript
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.test.ts',
        '**/*.test.tsx',
        '**/*.config.ts',
        '**/dist/**',
      ],
      thresholds: {
        lines: 75,
        functions: 75,
        branches: 70,
        statements: 75
      },
      // Fail CI if below thresholds
      perFile: false
    }
  }
})
```

#### CI/CD Integration
```yaml
- name: Run frontend tests with coverage
  run: |
    npm run test:coverage

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage/lcov.info
    flags: frontend

- name: Comment PR with coverage
  uses: romeovs/lcov-reporter-action@v0.3.1
  with:
    lcov-file: ./coverage/lcov.info
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

---

## 6. Coverage Gates & Quality Thresholds

### 6.1 Pull Request Requirements

#### Coverage Thresholds
```yaml
coverage_checks:
  backend:
    min_line_coverage: 80%
    max_line_decrease: 1%  # Can decrease by 1% with approval
    new_features: 85%      # New code must have higher coverage

  frontend:
    min_line_coverage: 75%
    max_line_decrease: 1%
    new_features: 80%
```

#### Enforcement
- **Below threshold**: Block PR merge
- **Threshold-1% decrease**: Require reviewer approval
- **New features**: Must meet higher threshold (85% backend, 80% frontend)

### 6.2 Coverage Quality Checks

#### Beyond Just Line Coverage
- **Branch coverage**: Must also measure conditional logic
- **Mutation testing**: Use `mutmut` (Python) or `stryker` (TypeScript) to verify test quality
- **CRAP score**: Complexity, Risk, and Analysis Precision (lower is better)

#### Example CRAP Score Calculation
```
CRAP = complexity^2 * (1 - coverage/100)

Good: CRAP < 30
Acceptable: CRAP 30-60
Poor: CRAP > 60
```

---

## 7. Coverage Trend Analysis

### 7.1 Tracking Coverage Over Time

#### Metrics to Monitor
```yaml
weekly_reports:
  - overall_coverage_percentage
  - modules_with_improving_coverage
  - modules_with_declining_coverage
  - new_uncovered_code
  - test_execution_time
  - flaky_test_count
```

#### Coverage Dashboard (Grafana/Metabase)
- Overall coverage trend (last 30 days)
- Coverage by module (heatmap)
- Coverage growth rate
- Untested code hotspots

### 7.2 Coverage Goals & Milestones

#### Phase 1: Foundation (Week 1-4)
- Achieve 70% overall coverage
- All critical paths covered
- All API endpoints have tests

#### Phase 2: Improvement (Week 5-8)
- Achieve 75% overall coverage
- Clinical modules at 100%
- Authentication at 95%

#### Phase 3: Excellence (Week 9-12)
- Achieve 80% overall coverage
- All security modules at 90%+
- Maintain coverage on new code

---

## 8. Coverage Best Practices

### 8.1 Writing Testable Code

#### Principles
1. **Single Responsibility**: One function, one purpose
2. **Dependency Injection**: Pass dependencies, don't instantiate inside
3. **Pure Functions**: No side effects, easy to test
4. **Small Functions**: Under 50 lines if possible
5. **Avoid God Objects**: Break large classes into smaller ones

#### Example: Untestable vs Testable

**Untestable:**
```python
# Bad: Hard to test due to database dependency
class UserService:
    def get_user(self, user_id):
        db = Database()  # Hard-coded dependency
        return db.query(User).get(user_id)
```

**Testable:**
```python
# Good: Dependencies injected, easy to mock
class UserService:
    def __init__(self, db: Database):
        self.db = db

    def get_user(self, user_id):
        return self.db.query(User).get(user_id)

# Test can inject mock database
def test_get_user():
    mock_db = Mock(spec=Database)
    service = UserService(mock_db)
    # ... test logic
```

### 8.2 Test Maintenance

#### Keeping Coverage High
1. **Write tests first** (TDD) - guarantees coverage
2. **Add tests for every bug fix** - prevent regressions
3. **Refactor test code** - keep tests maintainable
4. **Delete obsolete tests** - don't test removed features
5. **Review coverage reports weekly** - catch gaps early

### 8.3 Coverage Anti-Patterns

#### What NOT to Do

❌ **Coverage for Coverage's Sake**
```python
# Bad: Test adds no value
def test_function_returns_true():
    result = function_that_always_returns_true()
    assert result is True  # Meaningless assertion
```

✅ **Meaningful Tests**
```python
# Good: Test verifies behavior
def test_login_with_valid_credentials_returns_token():
    response = client.post("/auth/token", data=valid_credentials)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert jwt.decode(response.json()["access_token"])["sub"] == "user@test.com"
```

❌ **Asserting Implementation Details**
```python
# Bad: Tests private method
def test_private_method():
    obj = MyClass()
    assert obj._private_method() == "expected"  # Fragile!
```

✅ **Testing Public API**
```python
# Good: Tests public interface
def test_public_api():
    obj = MyClass()
    result = obj.public_method()  # Tests contract, not implementation
    assert result == "expected"
```

---

## 9. Coverage by Risk Level

### 9.1 High-Risk Modules (>95% coverage required)

#### Criteria
- Security-critical code (auth, sessions, tokens)
- Clinical assessments (PHQ-9, GAD-7, crisis detection)
- Payment processing (if applicable)
- Data encryption/decryption
- Compliance features (GDPR, HIPAA)

#### Justification
Bugs in high-risk modules can lead to:
- Security breaches
- Regulatory fines
- Patient safety issues
- Legal liability

### 9.2 Medium-Risk Modules (>85% coverage required)

#### Criteria
- Core business logic (assessments, scoring)
- Team management
- Analytics and reporting
- Email/Slack integrations
- API endpoints

### 9.3 Low-Risk Modules (>75% coverage required)

#### Criteria
- UI components (non-critical paths)
- Utility functions (well-understood, low complexity)
- Logging/debugging code
- Static data retrieval

---

## 10. Coverage Reporting & Visualization

### 10.1 HTML Coverage Reports

#### Backend Coverage Report
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

**What to Look For:**
- Red files (low coverage) - prioritize these
- Yellow lines (partial branch coverage) - add missing test cases
- Complex functions with low coverage - refactor or test

#### Frontend Coverage Report
```bash
npm run test:coverage
open coverage/index.html
```

### 10.2 Coverage Badges

#### README.md Badges
```markdown
![Backend Coverage](https://img.shields.io/badge/coverage-82%25-brightgreen)
![Frontend Coverage](https://img.shields.io/badge/coverage-78%25-green)
```

#### Auto-Updating Badges
```yaml
# GitHub Actions
- name: Generate coverage badge
  run: |
    coverage=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
    echo "![Coverage](https://img.shields.io/badge/coverage-${coverage}%25-brightgreen)" >> README.md
```

---

## Appendix: Coverage Commands Reference

### Backend Coverage Commands

```bash
# Quick coverage check
pytest --cov=app --cov-report=term-missing

# Full HTML report
pytest --cov=app --cov-report=html

# Filter by module
pytest --cov=app.services.auth_service

# Branch coverage
pytest --cov=app --cov-branch

# Combine with markers
pytest -m unit --cov=app

# Exclude files
pytest --cov=app --omit=*/migrations/*
```

### Frontend Coverage Commands

```bash
# Run all tests with coverage
npm run test:coverage

# Watch mode with coverage
npm run test:watch -- --coverage

# Specific file coverage
npm run test:coverage src/components/Button.test.tsx

# Open HTML report
open coverage/index.html
```

---

**Document Version:** 1.0
**Last Updated:** 2025-01-10
**Next Review:** 2025-02-10
