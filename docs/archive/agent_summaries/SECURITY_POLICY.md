# PsychSync Security Policy and Best Practices

This document provides comprehensive security guidelines for all developers working on the PsychSync project.

## Table of Contents

1. [Overview](#overview) - Security posture summary
2. [CORS Policy](#cors-policy) - Cross-Origin Resource Sharing guidelines
3. [Error Handling Policy](#error-handling-policy) - Proper exception handling and fail-safe patterns
4. [Rate Limiting Policy](#rate-limiting-policy) - Rate limiting strategies and implementation
5. [Authentication Security](#authentication-policy) - Password requirements, MFA, session management
6. [Data Protection Policy](#data-protection-policy) - Encryption, PII handling, SQL injection prevention
7. [API Security](#api-security-policy) - Input validation, output encoding, dependency management
8. [Code Review Checklist](#code-review-checklist) - Security code review requirements
9. [CI/CD Pipeline](#cicd-pipeline) - Automated security checks

## Overview

### Security Posture: EXCELLENT

PsychSync implements a defense-in-depth security architecture with multiple independent layers:

- ✅ **CORS**: Environment-aware configuration with origin validation
- ✅ **Rate Limiting**: Unified rate limiter with Redis backend
- ✅ **IP Ban Tracking**: Cumulative failure tracking across endpoints
- ✅ **CAPTCHA Protection**: Adaptive bot detection for suspicious registrations
- ✅ **Request Timeout**: Slow POST attack prevention
- ✅ **File Upload Limits**: Comprehensive abuse prevention
- ✅ **Error Handling**: Structured error responses with context
- ✅ **Monitoring**: Security dashboards for real-time threat detection
- ✅ **Redis Cluster**: Distributed rate limiting support for production

### Security Layers

```
┌────────────────────────────────────────────────────┐
│                   Application Layer │   Security Controls                   │
├────────────────────────────────────────────────────────┤
│  CORS & Headers          │   • Origin validation                    │
│                           │   • Credentials control               │
│                           │   • Protocol enforcement               │
├────────────────────────────────────────────────────────┤
│  Rate Limiting             │   • Per-user tracking                  │
│                           │   • Per-IP tracking                   │
│                           │   • Sliding window algorithm            │
│                           │   • Redis distributed backend          │
├────────────────────────────────────────────────────────┤
│  IP Ban Tracking           │   • Cumulative failures               │
│                           │   • Reputation scoring                 │
│                           │   • Automatic banning                 │
├────────────────────────────────────────────────────────┤
│  CAPTCHA Protection        │   • Suspicion detection              │
│                           │   • Adaptive triggering               │
│                           │   • Score-based verification           │
├────────────────────────────────────────────────────────┤
│  Request Timeout           │   • Slow POST detection               │
│                           │   • Method-specific timeouts            │
│                           │   • Body size limits                │
├────────────────────────────────────────────────────────┤
│  File Upload Limits        │   • Per-user limits                   │
│                           │   • Concurrent upload tracking          │
│                           │   • Bandwidth limits                │
├────────────────────────────────────────────────────────┤
│  Monitoring               │   • Security dashboards              │
│                           │   • Alert management                │
│                           │   • Threat intelligence               │
└────────────────────────────────────────────────────────────┘
```

## CORS Policy

### Configuration Requirements

#### Production Environment

**MUST:**
- Use specific origin list (NO wildcards `*`)
- Set `CORS_ORIGINS` in environment as comma-separated list
- Example: `CORS_ORIGINS=https://app.psychsync.com,https://www.psychsync.com`
- Never enable `allow_credentials=True` with wildcard origins
- Block `localhost`, `127.0.0.1` in production
- Use HTTPS only (`https://`) for all origins

**NEVER:**
- Use `allow_all_origins=True` or `allow_any_origin=True`
- Set `allow_methods=["*"]` without credentials
- Return 200 OK with generic error messages

### Development Environment

**PERMISSIBLE:**
- Can use localhost origins for testing
- Can use `http://localhost:5173` for local development
- Can set `max_age=3600` (1 hour) for easier debugging
- Use `allow_methods=["*"]` for convenience

### Implementation

```python
# app/core/cors.py - ENTERPRISE-GRADE implementation

# Production configuration
CORS_ORIGINS=https://app.psychsync.com,https://www.psychsync.com
ALLOWED_HOSTS=app.psychsync.com,www.psychsync.com
```

### Validation

The EnterpriseCORSManager enforces:
- Origin format validation (must start with http:// or https://)
- Wildcard prevention in production
- Localhost blocking in production
- Exact origins requirement when credentials enabled

### Headers

```python
"allow_headers": [
    "Authorization",
    "Content-Type",
    "Accept",
    "Origin",
    "X-Requested-With",
    "X-CSRF-Token",
    "X-Device-Fingerprint",
    "X-Session-ID",
]
```

### Common Misconfigurations

| Misconfiguration | Severity | Impact | Detection |
|------------------|----------|--------|---------|
| Wildcard origins with credentials | CRITICAL | Allows any site with cookies | CORS audit |
| Wildcard methods/headers | HIGH | Exposes internal APIs | CORS audit |
| Generic 200 on error | CRITICAL | Hides failures from clients | Fallback audit |
| Empty exception handlers | HIGH | Silent failures | Fallback audit |

## Error Handling Policy

### Principles

1. **Never use bare exception handlers**
   ```python
   # BAD
   except Exception:
       pass

   # GOOD
   except Exception as e:
       logger.error(f"Unexpected error: {e}")
       raise HTTPException(
           status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
           detail=str(e)
       )
   ```

2. **Always return appropriate HTTP status codes**
   - `200 OK` - Only for successful operations
   - `400 Bad Request` - Client error (validation, malformed data)
   - `401 Unauthorized` - Authentication/authorization failures
   - `403 Forbidden` - Authorization/resource not allowed
   - `404 Not Found` - Resource not found
   - `429 Too Many Requests` - Rate limiting
   - `500 Internal Server Error` - Server-side failures (with context)
   - `503 Service Unavailable` - External service down
   - `504 Gateway Timeout` - External service timeout

3. **Never suppress errors with 200 OK**
   - When an error occurs, always return an error status code (4xx or 5xx)
   - Never return 200 OK when something goes wrong

4. **Log errors with sufficient context**
   ```python
   logger.error(
       "operation_name": operation_name,
       "error_message": str(e),
       "stack_trace": traceback.format_exc(),
       "request_id": request_id,
       "user_id": user_id,
       "client_ip": client_ip,
   )
   ```

5. **Use structured error responses**
   ```python
   return {
       "error": str(e),
       "error_code": error_code,
       "request_id": request_id,
       "timestamp": datetime.utcnow().isoformat(),
   }
   ```

### Common Anti-Patterns

| Pattern | Why It's Bad | Better Alternative |
|--------|----------------|---------------|------------------|
| `except Exception: pass` | Silent failure | Handle specific exceptions | Log errors properly |
| `return {"error": "default"}` | Generic errors | Use specific error types | Log with context |
| `except:` | Lazy error handling | Catch-all exception | Handle exceptions | Never use bare except |
| Logging and pass | Silent failure | Either log OR raise | Always raise after logging | Never pass |

## Rate Limiting Policy

### Configuration

```python
# app/core/rate_limiter_unified.py

class RateLimitConfig:
    limit: int = 100
    window: int = 60
    strategy: RateLimitStrategy.SLIDING_WINDOW  # Most accurate
    burst: int = int(limit * 1.5)  # Default burst to 1.5x limit
    per_user: bool = False
    per_ip: bool = True
```

### Implementation Strategies

1. **Sliding Window** (Recommended for production)
   - Most accurate rate limiting
   - Uses Redis sorted sets
   - Prevents request bursting at window boundaries
   - Good for API endpoints

2. **Token Bucket** (Good for handling burst traffic)
   - Smooth rate limiting with capacity
   - Allows short bursts within limits
   - Good for preventing spam with intermittent legitimate requests

3. **Fixed Window** (Simple, less accurate)
   - Counter-based rate limiting
   - Resets at fixed intervals
   - Easier to implement but less accurate

### Best Practices

1. **Never rate limit authentication endpoints**
   - Allow legitimate login attempts
   - Rate limit only on failed attempts
   - Use account lockout for brute force protection

2. **Use different limits for different operations**
   - Auth: Stricter limits (5/min, 20/hour)
   - API calls: More permissive (100/min, 1000/hour)
   - File uploads: Very restrictive (10/hour, 50/day)
   - Health checks: Lenient (60/min, 1000/hour)

3. **Implement circuit breakers**
   - Temporarily disable failing services
  - Return 503 Service Unavailable
  - Auto-retry with exponential backoff

4. **Monitor rate limit violations**
   - Track who is being rate limited
  - Alert on suspicious patterns
  - Log to security dashboard

## IP Ban Tracking

### Configuration

```python
# app/services/ip_ban_tracker.py

BAN_THRESHOLD_FAILURES = 100  # Cumulative failures across ALL endpoints
BAN_THRESHOLD_BRUTE_FORCE = 50  # Brute force attempts
BAN_DURATION_MINUTES = 60  # Default ban duration
```

### Ban Reasons

- `BRUTE_FORCE` - High failure rate on auth endpoints
- `CREDENTIAL_STUFFING` - Repeated credential attempts
- `RATE_LIMIT_VIOLATION` - Exceeded rate limits repeatedly
- `AUTOMATED_ATTACK` - Pattern of automated tool usage
- `MALICIOUS_PATTERN` - Suspicious request patterns
- `SYSTEM_ADMIN` - Manual ban by administrator

### Best Practices

1. **Always log before banning**
   - Document reason for ban
   - Include IP, user ID, violation count
   - Track ban expiry and manual unban actions

2. **Implement graduated response**
   - First ban: Warning (rate limit exceeded)
   - Second ban: Temporary (30 min)
   - Third ban: Permanent (or until investigation)

3. **Maintain whitelist**
   - Exclude trusted partners, internal systems
  - Regular review and cleanup

4. **Monitor false positives**
   - Review banned IPs periodically
  - Whitelist legitimate users/IPs if needed

## Code Review Checklist

### Pre-Commit Checklist

- [ ] No hardcoded secrets
- [ ] No API keys or tokens in code
- [ ] No hardcoded URLs or paths
- [ ] No test data or debug endpoints in production
- [ ] No print statements with sensitive data
- [ ] No commented-out debug code
- [ ] SQL queries use parameter binding

### Security Checklist

- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] CSRF protection on state-changing operations
- [ ] File upload validation (type, size, content)
- [ ] Rate limiting on public endpoints
- [ ] Authentication on protected endpoints
- [ ] Authorization checks on sensitive operations
- [ ] Rate limiting on resource-intensive operations

### Authentication Security

- [ ] Strong password requirements (12+ chars, complexity)
- [ ] Secure password hashing (bcrypt/argon2)
- [ ] Never log or store passwords in plaintext
- [ ] Session timeout (30 min default)
- [ ] Token expiration (access: 30min, refresh: 7 days)
- [ ] MFA support (TOTP, recovery codes)

### Data Protection

- [ ] PII encryption at rest (database field encryption)
- [ ] Secure TLS for all connections (1.3+)
- [ ] Audit logging for sensitive operations
- [ ] Data access logging with user attribution
- [ ] Secure backup with encryption
- [ ] GDPR compliance for EU users (right to erasure)

## CI/CD Pipeline

The security workflow in `.github/workflows/security-audit.yml` provides:

### Automatic Security Checks

1. **CORS Security Audit**
   - Validates no wildcard origins in configuration files
   - Checks credentials configuration
   - Blocks deployment on security issues
   - Generates audit reports

2. **Fallback Pattern Audit**
   - Detects bare exception handlers
   - Detects silent exception swallowing
   - Detects fail-open patterns
   - Detects generic 500 fallbacks
   - Blocks deployment on issues found

3. **Pre-Merge Security Checks**
   - Runs before pull requests can be merged
   - Blocks merges with security vulnerabilities
   - Requires all security audits to pass

### Deployment Requirements

**Before Deployment:**
1. Run security audit: `python scripts/security/fallback_audit_simple.py`
2. Review audit report: Check for any issues
3. Fix any critical issues before deploying
4. Update security documentation if patterns change

**Blocked Issues:**
- Wildcard CORS in production: ❌ Block deployment
- Bare exception handlers: ❌ Block deployment
- Fail-open patterns: ❌ Block deployment
- Generic 500 fallbacks: ⚠️ Review and fix before deploy

## Contact

For security questions or issues:
- Security Team: security@psychsync.com
- DevOps Team: devops@psychsync.com

## Quick Reference

### Critical Security Files

| File | Purpose |
|-------|----------|
| `app/core/cors.py` | CORS configuration and validation |
| `app/core/rate_limiter_unified.py` | Unified rate limiting with strategies |
| `app/services/ip_ban_tracker.py` | IP ban tracking and reputation |
| `app/services/captcha_service.py` | CAPTCHA verification and bot detection |
| `app/middleware/request_timeout.py` | Slow POST attack prevention |
| `app/middleware/file_upload_rate_limiting.py` | File upload abuse prevention |
| `app/api/v1/endpoints/security_monitoring.py` | Security dashboards and alerts |
| `scripts/security/cors_security_audit.py` | CORS security audit tool |
| `scripts/security/fallback_audit_simple.py` | Fallback pattern audit tool |

### Security Audit Commands

```bash
# Run CORS audit
python scripts/security/cors_security_audit.py

# Run fallback audit
python scripts/security/fallback_audit_simple.py

# Run full security audit
python scripts/security/cors_security_audit.py && python scripts/security/fallback_audit_simple.py
```

### Key Security Metrics to Monitor

1. **Rate limit violations** - Track via monitoring dashboard
2. **IP bans** - Track via IP ban dashboard
3. **Failed auth attempts** - Monitor for brute force patterns
4. **CAPTCHA verifications** - Track success/failure rates
5. **Timeout occurrences** - Monitor for slow POST attacks
6. **500 error rates** - Alert on sudden increases
