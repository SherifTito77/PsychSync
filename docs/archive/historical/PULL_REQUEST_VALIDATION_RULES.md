# Pull Request Validation Rules

## Overview

This document defines the comprehensive validation rules that must be satisfied before any pull request can be merged into the PsychSync codebase. These rules ensure code quality, security, performance, and maintainability.

**Last Updated:** 2025-01-09
**Repository:** psychsync/psychsync
**Enforcement:** GitHub Actions CI/CD Pipeline

---

## Table of Contents

1. [Automated Checks](#automated-checks)
2. [Code Quality Standards](#code-quality-standards)
3. [Security Requirements](#security-requirements)
4. [Testing Requirements](#testing-requirements)
5. [Documentation Requirements](#documentation-requirements)
6. [Performance Requirements](#performance-requirements)
7. [Complexity Limits](#complexity-limits)
8. [Review Process](#review-process)

---

## Automated Checks

All pull requests must pass the following automated checks in CI/CD:

### 1. Linting & Formatting

#### Backend (Python)
```bash
# Must pass without errors
ruff check . --output-format=github
ruff format . --check
mypy app/  # Type checking
```

**Rules:**
- ✅ No Ruff errors (warnings allowed with justification)
- ✅ Code formatted with Ruff
- ✅ No mypy type errors
- ✅ Maximum cyclomatic complexity: 15
- ✅ Maximum function arguments: 7
- ✅ Maximum branches: 12
- ✅ Maximum statements: 50

**Failure Actions:**
- Run `ruff check --fix .` for auto-fixable issues
- Manually address remaining issues
- Add `# noqa: <rule-code>` with explanation for exceptions

#### Frontend (TypeScript/React)
```bash
# Must pass without errors
npm run lint
npm run type-check
npm run format:check
```

**Rules:**
- ✅ No ESLint errors (warnings allowed with justification)
- ✅ No TypeScript type errors
- ✅ Code formatted with Prettier
- ✅ No `any` types without `// eslint-disable-next-line` comment
- ✅ All imports properly organized
- ✅ No unused variables or imports

**Failure Actions:**
- Run `npm run lint:fix` for auto-fixable issues
- Manually address remaining issues
- Add `// eslint-disable-next-line` with explanation for exceptions

### 2. Security Scanning

#### Automated Security Checks
```yaml
- Semgrep SAST scan (OWASP rules)
- Bandit Python security linter
- Trivy vulnerability scanner
- Snyk dependency scanning
```

**Failure Criteria:**
- ❌ CRITICAL severity vulnerabilities
- ❌ HIGH severity vulnerabilities (exceptions require security team approval)
- ⚠️ MEDIUM/LOW vulnerabilities (documented in PR description)

**Exemption Process:**
1. Document vulnerability in PR description
2. Justify why it cannot be fixed
3. Get approval from security lead
4. Create issue for remediation

### 3. Build Verification

#### Backend Build
```bash
docker build -t psychsync-backend:test .
```

#### Frontend Build
```bash
cd frontend && npm run build
```

**Requirements:**
- ✅ Docker image builds successfully
- ✅ Frontend production bundle completes
- ✅ No build errors or warnings
- ✅ Bundle size increase < 10% (or justified)

---

## Code Quality Standards

### 1. Code Review Criteria

All PRs must meet these quality standards:

#### Backend Requirements
- ✅ **Function Length:** Maximum 50 lines (excluding docstrings)
- ✅ **Class Length:** Maximum 300 lines
- ✅ **File Length:** Maximum 500 lines (exceptions with approval)
- ✅ **Imports:** Maximum 30 imports per file
- ✅ **Nesting:** Maximum 4 levels deep
- ✅ **Parameters:** Maximum 7 parameters (use dataclasses for more)

#### Frontend Requirements
- ✅ **Component Length:** Maximum 300 lines
- ✅ **Hook Count:** Maximum 10 hooks per component
- ✅ **Props:** Maximum 8 props (use object for more)
- ✅ **Nesting:** Maximum 5 JSX levels deep
- ✅ **Component Files:** One component per file

#### Anti-Pattern Detection
- ❌ Prop drilling > 3 levels (use context)
- ❌ Duplicated code (DRY principle)
- ❌ God objects/files (> 1000 lines requires refactoring)
- ❌ Circular dependencies
- ❌ Hardcoded secrets or credentials
- ❌ Console.log in production code

### 2. Design Pattern Compliance

#### Required Patterns
- ✅ **Backend:** Service → CRUD → Database layer pattern
- ✅ **Frontend:** Component → Service → API pattern
- ✅ **Error Handling:** Consistent exception handling
- ✅ **Validation:** Input validation at API boundaries
- ✅ **State Management:** Appropriate use of Context, hooks, or state management library

#### Prohibited Patterns
- ❌ Tight coupling between layers
- ❌ Business logic in controllers/endpoints
- ❌ Direct database access from API endpoints
- ❌ Mixed concerns (UI + business logic in components)

---

## Security Requirements

### 1. OWASP Compliance

All code must pass OWASP security checks:

#### Critical Rules (BLOCKING)
```python
# ❌ FORBIDDEN
- SQL injection vulnerabilities
- Hardcoded secrets/credentials
- Insecure deserialization
- Weak cryptographic algorithms
- Unvalidated redirects
- Broken authentication
- Sensitive data exposure
```

#### Security Best Practices
```python
# ✅ REQUIRED
- Parameterized queries (SQLAlchemy)
- Environment variables for secrets
- Input validation at boundaries
- Proper error messages (no sensitive data)
- Secure session management
- CSRF protection on state-changing operations
- Rate limiting on authenticated endpoints
```

### 2. Dependency Security

**Requirements:**
- ✅ No dependencies with known CRITICAL vulnerabilities
- ✅ Dependencies with HIGH vulnerabilities documented and approved
- ✅ Regular dependency updates (monthly)

**Process:**
1. Automated scans run on every PR
2. Security team reviews HIGH/CRITICAL findings
3. Exceptions documented in PR description
4. Remediation plan created for all approved exceptions

### 3. Data Protection

**Requirements:**
- ✅ PII encrypted at rest
- ✅ Pseudonymization for analytics
- ✅ Audit logging for data access
- ✅ Proper data retention policies
- ✅ GDPR compliance for user data

---

## Testing Requirements

### 1. Test Coverage

#### Minimum Coverage Thresholds
- **Backend:** 80% line coverage (required)
- **Frontend:** 70% line coverage (required)
- **Critical Paths:** 95% coverage (auth, payments, data export)

#### Coverage Checks
```bash
# Backend
pytest --cov=app --cov-report=term-missing --cov-fail-under=80

# Frontend
npm run test -- --coverage --coverageReporters=text
```

### 2. Test Types Required

#### Backend Tests
- ✅ **Unit Tests:** For all service layer functions
- ✅ **Integration Tests:** For all API endpoints
- ✅ **Regression Tests:** For bug fixes
- ✅ **Edge Cases:** Boundary conditions, error handling

#### Frontend Tests
- ✅ **Component Tests:** For all UI components
- ✅ **Service Tests:** For all API service functions
- ✅ **User Interaction Tests:** For critical user flows
- ✅ **Accessibility Tests:** For all interactive components

### 3. Test Quality Standards

**Requirements:**
- ✅ Tests must be independent (no shared state)
- ✅ Tests must be deterministic (same results every run)
- ✅ Tests must be fast (< 5 seconds per test)
- ✅ Descriptive test names (`test_<function>_<scenario>_<expected_result>`)
- ✅ Proper setup/teardown (pytest fixtures, React testing library)

**Prohibited:**
- ❌ Flaky tests (intermittent failures)
- ❌ Tests depending on execution order
- ❌ Tests with hardcoded sleep/delay
- ❌ Tests depending on external services (use mocks)

---

## Documentation Requirements

### 1. Code Documentation

#### Python Docstrings (Google Style)
```python
def calculate_team_compatibility(team_id: int) -> dict:
    """Calculate team compatibility metrics.

    This function analyzes team member personality assessments
    to generate compatibility scores and identifies potential
    friction points.

    Args:
        team_id: The unique identifier for the team.

    Returns:
        A dictionary containing:
            - compatibility_score: Float from 0-100
            - friction_points: List of potential conflicts
            - recommendations: List of improvement suggestions

    Raises:
        TeamNotFoundError: If team_id doesn't exist
        InsufficientDataError: If fewer than 3 members have assessments

    Example:
        >>> result = calculate_team_compatibility(123)
        >>> print(result['compatibility_score'])
        78.5
    """
```

#### TypeScript Documentation
```typescript
/**
 * Calculate team compatibility metrics.
 *
 * @param teamId - The unique identifier for the team
 * @returns Promise resolving to compatibility data including:
 *   - compatibilityScore: Score from 0-100
 *   - frictionPoints: Array of potential conflicts
 *   - recommendations: Array of improvement suggestions
 * @throws {TeamNotFoundError} If teamId doesn't exist
 * @throws {InsufficientDataError} If fewer than 3 members have assessments
 *
 * @example
 * ```typescript
 * const result = await calculateTeamCompatibility(123);
 * console.log(result.compatibilityScore);
 * // Output: 78.5
 * ```
 */
```

### 2. API Documentation

**Requirements:**
- ✅ All endpoints documented in OpenAPI/Swagger
- ✅ Request/response schemas documented
- ✅ Error responses documented
- ✅ Authentication requirements specified
- ✅ Rate limits documented

### 3. PR Description Template

Every PR must include:

```markdown
## Description
[Brief description of changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing

## Security & Compliance
- [ ] No new vulnerabilities introduced
- [ ] Sensitive data properly handled
- [ ] Audit logging added where required

## Documentation
- [ ] Code documented with docstrings
- [ ] API documentation updated
- [ ] README/CHANGELOG updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added to complex code
- [ ] No hardcoded values/secrets
- [ ] Database migrations included (if applicable)
```

---

## Performance Requirements

### 1. Backend Performance

**API Response Times:**
- ✅ GET requests: < 200ms (p95)
- ✅ POST/PUT: < 500ms (p95)
- ✅ Complex queries: < 2s (p95)

**Database Performance:**
- ✅ No N+1 queries
- ✅ Proper indexing on foreign keys
- ✅ Query result pagination
- ✅ Connection pooling configured

**Caching:**
- ✅ Expensive operations cached (Redis)
- ✅ Cache invalidation strategy documented
- ✅ Cache hit rate > 80%

### 2. Frontend Performance

**Bundle Size:**
- ✅ Initial bundle < 500KB (gzipped)
- ✅ Code splitting implemented for routes
- ✅ Lazy loading for images/components
- ✅ Tree shaking enabled

**Runtime Performance:**
- ✅ No unnecessary re-renders (use React DevTools Profiler)
- ✅ Memoization for expensive computations
- ✅ Virtualization for long lists
- ✅ Optimistic UI updates

**Load Performance:**
- ✅ First Contentful Paint: < 1.5s
- ✅ Time to Interactive: < 3s
- ✅ Cumulative Layout Shift: < 0.1

### 3. Performance Testing

**Required for:**
- New API endpoints
- Database query changes
- Frontend route changes
- Major feature additions

---

## Complexity Limits

### 1. Cyclomatic Complexity

**Maximum Complexity: 15**

Files exceeding this limit must be refactored:

```python
# ❌ TOO COMPLEX (complexity: 25)
def complex_function(data):
    if condition1:
        if condition2:
            if condition3:
                # ... many nested branches
```

```python
# ✅ REFACTORED
complexity = calculate_complexity(data)
if complexity.is_high():
    handle_high_complexity(data)
else:
    handle_normal_complexity(data)
```

### 2. Cognitive Complexity

**Guidelines:**
- ✅ Maximum nesting depth: 4 levels
- ✅ Maximum conditions per function: 5
- ✅ Maximum loops per function: 3

### 3. File Size Limits

**Backend:**
- Maximum 500 lines per file
- Exceptions require team lead approval
- Must include refactoring plan

**Frontend:**
- Maximum 300 lines per component
- Extract to separate files if exceeded
- Use component composition

---

## Review Process

### 1. Required Reviewers

**Based on Changed Files:**
- **Backend changes:** Backend team lead + 1 developer
- **Frontend changes:** Frontend team lead + 1 developer
- **Security changes:** Security lead + 1 team lead
- **Database changes:** DBA + backend lead
- **Infrastructure:** DevOps lead

### 2. Review Checklist

Reviewers must verify:

**Code Quality:**
- [ ] Code is readable and maintainable
- [ ] Follows project patterns and conventions
- [ ] Proper error handling
- [ ] No code duplication
- [ ] Appropriate abstraction level

**Testing:**
- [ ] Tests cover new functionality
- [ ] Tests cover edge cases
- [ ] Tests are well-written
- [ ] No flaky tests introduced

**Security:**
- [ ] No security vulnerabilities
- [ ] Proper input validation
- [ ] Proper authorization checks
- [ ] No sensitive data exposure

**Performance:**
- [ ] No performance regressions
- [ ] Efficient database queries
- [ ] Proper caching strategy
- [ ] No memory leaks

### 3. Approval Workflow

```
1. Author opens PR with template completed
2. Automated checks run (CI/CD)
   ↓
3. All checks must pass
   ↓
4. Code review requested
   ↓
5. Reviewer provides feedback or approves
   ↓
6. Address all review comments
   ↓
7. Get required approvals (minimum 2)
   ↓
8. Pass all automated checks
   ↓
9. Merge to main branch
```

### 4. Merge Blocking Conditions

PR CANNOT be merged if:
- ❌ Any automated check fails
- ❌ Test coverage below threshold
- ❌ Security vulnerabilities present
- ❌ Missing required approvals
- ❌ PR description incomplete
- ❌ No tests for new functionality
- ❌ Performance regression detected
- ❌ Documentation missing

---

## Emergency Exemptions

### Process for Emergency Bypass

In rare emergencies (production hotfix):

1. **Document Justification:**
   ```markdown
   ## EMERGENCY BYPASS
   **Reason:** Production outage affecting all users
   **Impact:** Critical severity
   **Bypassed Rules:** [List]
   **Remediation Plan:** [Link to issue]
   **Approval:** @CTO @TechLead
   ```

2. **Get Approvals:**
   - CTO or VP Engineering
   - Security lead (if security bypassed)

3. **Create Follow-up:**
   - Issue for proper fix
   - Deadline: 7 days
   - Assign to original author

4. **Retrospective:**
   - Document lessons learned
   - Update processes if needed

---

## Metrics & Monitoring

### CI/CD Success Metrics

**Targets:**
- PR validation time: < 15 minutes
- Test suite runtime: < 10 minutes
- False positive rate: < 5%
- PR merge time: < 24 hours (after approval)

**Monitoring:**
- Track failure reasons
- Identify flaky tests
- Monitor build times
- Review exemption requests

---

## Related Documentation

- [CI/CD Pipeline](/.github/workflows/cicd-pipeline.yaml)
- [Code Style Guide](/docs/CODE_STYLE_GUIDE.md)
- [Security Guidelines](/docs/SECURITY_INDEX.md)
- [Testing Guide](/docs/TESTING_REGRESSION_QUICKSTART.md)
- [Pre-commit Hooks](/.pre-commit-config.yaml)

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-01-09 | Initial creation with comprehensive rules | Claude Code |
| - | Add complexity metrics | - |
| - | Add performance baselines | - |
