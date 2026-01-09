# ADR: OWASP Top 10 Security Hardening

**Date**: 2025-12-27
**Status**: Accepted
**Author**: Security Team
**Deciders**: Security Team, Engineering Leadership

---

## Context

A comprehensive security review of the PsychSync platform identified multiple OWASP Top 10 (2021) vulnerabilities across authentication, user management, and assessment endpoints. The review covered:

- `app/api/v1/endpoints/auth.py`
- `app/api/v1/endpoints/users.py`
- `app/api/v1/endpoints/assessments.py`
- `app/api/v1/endpoints/ai_secure.py`

### Critical Findings

1. **A01 - Broken Access Control**:
   - Hardcoded admin credentials in token refresh endpoint (CRITICAL)
   - Missing role validation allowing potential privilege escalation
   - Insecure IDOR patterns in user/assessment access
   - TODO comments indicating unimplemented audit logging

2. **A03 - Injection**:
   - XSS vulnerability via string concatenation in JSON responses
   - Raw SQL queries with `text()` function (risky pattern)
   - Unsanitized user input in search queries

3. **A05 - Security Misconfiguration**:
   - Using `print()` for security-sensitive events (information disclosure)
   - Caching user data without access control consideration
   - Stack traces potentially exposed in error responses

4. **A07 - Authentication Failures**:
   - Placeholder implementations for critical security functions
   - Missing password strength requirements in some flows

5. **A09 - Security Logging Failures**:
   - TODO comments for audit logging throughout codebase
   - Inconsistent logging of security events

---

## Decision

We will implement comprehensive security improvements across all identified vulnerability categories:

### 1. Create Secure Authentication Module

**File**: `app/api/v1/endpoints/auth_secure.py`

**Changes**:
- Replace hardcoded credentials with database lookup
- Implement proper JSON serialization to prevent XSS
- Use structured logging instead of `print()`
- Add comprehensive audit logging for all auth events
- Secure error handling without information leakage
- Proper token validation with database checks

```python
# Before (INSECURE):
if token_validator:
    new_token = create_secure_token_for_user("admin", "admin@example.com")

# After (SECURE):
user = await get_user_from_database(user_id)
new_token = create_secure_token_for_user(str(user.id), user.email)
```

### 2. Implement Comprehensive Security Tests

**File**: `tests/integration/test_owasp_security.py`

**Coverage**:
- A01: IDOR, privilege escalation, unauthorized access
- A03: SQL injection, XSS, command injection, LDAP injection
- A05: Stack traces, debug info, secure defaults
- A07: Password security, session management
- A09: Audit logging for all security events
- A10: SSRF via URL parameters

**Test Count**: 40+ comprehensive security tests

### 3. Create Semgrep Rules for Regression Prevention

**File**: `semgrep_rules/owasp-python.yaml`

**Rules**:
- 20+ security patterns detected automatically
- Covers all OWASP Top 10 categories
- Integrated into CI/CD pipeline
- Fails build on critical security issues

**Examples**:
```yaml
- id: hardcoded-admin-credentials
  patterns:
    - pattern: create_secure_token_for_user("admin", ...)
  severity: ERROR

- id: xss-string-concatenation-json
  patterns:
    - pattern: Response(content='{' ... $VAR ... '}')
  severity: ERROR
```

### 4. Security Documentation

**Files**:
- This ADR
- `CHANGELOG.md` (detailed changes)
- Implementation guides for each fix

---

## Consequences

### Positive

1. **Security Posture Improved**:
   - All critical vulnerabilities addressed
   - Defense in depth implemented
   - Continuous security monitoring via Semgrep

2. **Compliance**:
   - OWASP Top 10 (2021) compliance
   - SOC 2 readiness improved
   - Audit trail completeness

3. **Developer Experience**:
   - Automated security testing
   - Clear patterns for secure code
   - Fast feedback via Semgrep in CI/CD

4. **Incident Prevention**:
   - XSS attacks prevented via JSON serialization
   - SQL injection prevented via parameterized queries
   - IDOR attacks prevented via access control checks

### Negative

1. **Migration Effort**:
   - Existing endpoints need updates
   - Frontend changes for httpOnly cookie authentication
   - Breaking changes in some API responses

2. **Performance**:
   - Additional security checks add latency (~5-10ms per request)
   - Audit logging requires additional I/O
   - Caching complexity increased

3. **Testing Overhead**:
   - 40+ new tests to maintain
   - Security test suite adds ~2-3 minutes to CI/CD
   - Semgrep scanning adds ~30 seconds

### Neutral

1. **API Changes**:
   - Auth endpoints now use httpOnly cookies (breaking change)
   - Error messages genericized (may affect UX)
   - Audit logging async (non-blocking)

2. **Deployment**:
   - Requires database migration for audit logs
   - Semgrep must be added to CI/CD pipeline
   - Monitoring must be configured for security events

---

## Implementation Plan

### Phase 1: Critical Fixes (Week 1)
- [x] Create secure authentication module
- [x] Replace hardcoded credentials
- [x] Fix XSS vulnerabilities
- [ ] Deploy to staging

### Phase 2: Testing & Validation (Week 2)
- [x] Implement security test suite
- [x] Create Semgrep rules
- [ ] Run all tests and fix failures
- [ ] Penetration testing

### Phase 3: Production Deployment (Week 3)
- [ ] Database migration for audit logs
- [ ] Frontend changes for cookie auth
- [ ] Gradual rollout with feature flags
- [ ] Monitor security metrics

### Phase 4: Monitoring & Iteration (Ongoing)
- [ ] Track security events in SIEM
- [ ] Review failed authentication attempts
- [ ] Update Semgrep rules as needed
- [ ] Quarterly security reviews

---

## Alternatives Considered

### Alternative 1: Web Application Firewall (WAF)
**Pros**:
- Fast to deploy
- Covers many attack types

**Cons**:
- Expensive
- False positives
- Doesn't fix root cause

**Decision**: Rejected - WAF is complementary, not a replacement for secure coding

### Alternative 2: Rewrite in Rust/Go
**Pros**:
- Memory safety
- Performance benefits

**Cons**:
- Massive rewrite effort
- Team expertise gap
- High risk

**Decision**: Rejected - Cost/benefit doesn't justify rewrite

### Alternative 3: Minimal Fixes Only
**Pros**:
- Faster implementation
- Less risk

**Cons**:
- Vulnerabilities remain
- Technical debt accumulates

**Decision**: Rejected - Security is non-negotiable

---

## Related Decisions

- [ADR-001] LLM Security Integration (Spotlighting Middleware)
- [ADR-002] SLSA Supply Chain Security
- [ADR-003] Kubernetes Deployment with Image Verification

---

## References

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [OWASP ASVS 4.0](https://owasp.org/www-project-application-security-verification-standard/)
- [Semgrep Rules Documentation](https://semgrep.dev/docs/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)

---

**Approval**: Security Team Lead
**Review Date**: 2025-12-27
**Next Review**: 2026-03-27
