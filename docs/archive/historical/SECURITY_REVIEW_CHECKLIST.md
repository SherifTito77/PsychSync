# PsychSync Code Review Checklist

Use this checklist when reviewing code changes or performing security reviews.

## Code Review Categories

### 🔒 Authentication & Authorization

- [ ] No hardcoded credentials (API keys, tokens)
- [ ] No hardcoded passwords or secrets
- [ ] Proper password hashing (bcrypt/argon2)
- [ ] Secure session management (JWT with expiration)
- [ ] Token rotation implemented
- [ ] MFA support available
- [ ] Account lockout after failed attempts
- [ ] Never log passwords in plaintext
- [ ] Rate limiting on auth endpoints
- [ ] Device fingerprinting for sensitive operations

### 🔒 Data Protection

- [ ] PII fields encrypted at rest
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] CSRF protection on state changes
- [ ] Sensitive data logging redaction
- [ ] File upload validation (type, size, content)
- [ ] Secure database connection (TLS)
- [ ] Regular security audits of data access
- [ ] GDPR compliance for EU users
- [ ] Data retention policies implemented

### 🔒 Input Validation

- [ ] All user input validated (Pydantic schemas)
- [ ] Length and format validation
- [ ] SQL injection prevention on all inputs
- [ ] Path traversal prevention
- [ ] Command injection prevention
- [ ] XXE and SSRF prevention
- [ ] File upload validation (MIME type, size)
- [ ] JSON schema validation
- [ ] Type conversion where appropriate
- [ ] Never trust client-side input

### 🔒 API Security

- [ ] CORS properly configured (no wildcards in production)
- [ ] Security headers set (CSP, X-Frame-Options)
- [ ] Rate limiting on all public endpoints
- [ ] Authentication required for sensitive endpoints
- [ ] API versioning implemented
- [ ] OpenAPI/Swagger documentation available
- [ ] Dependency management for security updates
- [ ] Audit logging for security events

### 🔒 Error Handling

- [ ] No bare exception handlers (except:)
- [ ] Specific exceptions caught and logged
- [ ] Appropriate HTTP status codes (4xx, 5xx)
- [ ] Structured error responses
- [ ] Never return 200 OK on error
- [ ] Stack traces logged for errors
- [ ] Circuit breakers for external services
- [ ] Retry logic with exponential backoff
- [ ] Error monitoring with alerting
- [ ] No silent exception swallowing

### 🔒 Logging & Monitoring

- [ ] Security events logged to dedicated audit log
- [ ] PII redaction in all logs
- [ ] Request ID correlation for tracing
- [ ] User attribution in security events
- [ ] Error logging with sufficient context
- [ ] Performance metrics collected
- [ ] Anomaly detection monitoring
- [ ] Log retention policy defined
- [ ] Log access controls implemented

### 🔒 Rate Limiting & Abuse Prevention

- [ ] Unified rate limiting implemented
- [ ] Per-user and per-IP tracking
- [ ] Sliding window algorithm for accuracy
- [ ] Redis backend for distributed tracking
- [ ] IP ban tracking with cumulative failures
- [ ] IP reputation scoring
- [ ] File upload rate limiting
- [ ] CAPTCHA integration for suspicious attempts
- [ ] Request timeout middleware

### 🔒 File Security

- [ ] File upload validation (type, size, content)
- [ ] Virus scanning capability if applicable
- [ ] Secure file storage with encryption
- [ ] File access controls (authorization)
- [ ] Quarantine for suspicious files

### 🔒 Infrastructure Security

- [ ] TLS enabled for all connections
- [ ] Database connection pooling configured
- [ ] Redis password protection
- [ ] SSL certificate validation
- [ ] Network security groups implemented
- [ ] DDoS protection infrastructure
- [ ] Failover mechanisms implemented

### 🔒 Testing & Quality Assurance

- [ ] Security tests in test suite
- [ ] Integration tests for security controls
- [ ] Code review checklist implemented
- [ ] Dependency scanning in CI/CD
- [ ] Security audit scripts available
- [ ] Penetration testing before releases

## Review Process

1. **Self-Review** - Developer completes checklist first
2. **Peer Review** - At least one other developer reviews
3. **Security Review** - Security team reviews critical changes
4. **Automated Scan** - Run security audit scripts
5. **Approval** - All checks must pass before merge

## Scoring

- ✅ All items checked: Code passes security review
- ⚠️ Items requiring attention: None
- ❌ Critical issues: None

## Notes

- Focus on actual production code, not test files
- Prioritize security over convenience
- Always consider security implications of changes
- Document security decisions for future reference

## Approval Criteria

- **MUST PASS**: Zero critical issues
- **CAN PASS**: All high-priority items addressed or documented
- **SHOULD PASS**: All medium-priority items addressed or documented

---

Last Updated: 2026-03-11
