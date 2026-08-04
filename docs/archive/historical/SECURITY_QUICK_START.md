# PsychSync Security Implementation Guide

Quick reference for developers working with PsychSync security features.

**Last Updated:** 2025-12-24

---

## 🚀 Quick Start

### 1. Access the Security Dashboard

```bash
# Start the backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start the frontend
cd frontend && npm run dev

# Navigate to (admin only):
http://localhost:5173/admin/security
```

**Dashboard Features:**
- Real-time authentication metrics
- Authorization success/failure rates
- CSRF violation tracking
- Suspicious activity alerts
- Top blocked IPs
- Security event timeline (hourly)

### 2. Run Security Tests

```bash
# Run all security tests
./scripts/run_security_tests.sh

# Run specific test category
pytest tests/test_security_automated.py::TestTokenSecurity -v
pytest tests/test_security_automated.py::TestCSRFProtection -v
pytest tests/test_security_automated.py::TestAuthorization -v
pytest tests/test_security_automated.py::TestSecureEndpoints -v

# Run with coverage
pytest tests/test_security_automated.py --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

### 3. Verify Security Measures

```bash
# Check CSRF middleware is enabled
curl -X POST http://localhost:8000/api/v1/assessments \
  -H "Content-Type: application/json" \
  -d '{"title": "test"}'
# Should return 403 Forbidden (CSRF protection)

# Verify test endpoints are disabled
curl http://localhost:8000/api/v1/simple-token
# Should return 400, 404, or 405 (not accessible)
```

---

## 🔒 Key Security Features

### Token Storage (httpOnly Cookies)

**Before (VULNERABLE):**
```typescript
// ❌ Tokens in localStorage - accessible to XSS
localStorage.setItem('access_token', token);
```

**After (SECURE):**
```python
# ✅ Backend sets httpOnly cookies
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,    # NOT accessible to JavaScript
    secure=True,      # HTTPS only
    samesite="lax"    # CSRF protection
)
```

**Frontend Usage:**
```typescript
// Automatic - cookies sent with requests
const response = await apiClient.get('/api/v1/users/me');

// No manual token handling needed!
```

### CSRF Protection

**Backend:** `app/main.py:85-110`
```python
app.add_middleware(
    CSRFMiddleware,
    header_name="X-CSRF-Token",
    exclude_paths=[
        "/health",
        "/api/v1/auth/token-fixed",
        "/api/v1/auth/register",
        # ... public endpoints
    ]
)
```

**Frontend:** `frontend/src/services/api.ts:48-56`
```typescript
// Automatic CSRF token inclusion
api.interceptors.request.use((config) => {
    const dangerousMethods = ['post', 'put', 'delete', 'patch'];
    if (dangerousMethods.includes(config.method?.toLowerCase() || '')) {
        const csrfToken = getCsrfTokenFromCookie();
        if (csrfToken && config.headers) {
            config.headers['X-CSRF-Token'] = csrfToken;
        }
    }
    return config;
});
```

### Authorization (IDOR Prevention)

**Implementation:** `app/api/v1/endpoints/assessments.py:145-180`

```python
async def delete_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    # Fetch assessment
    assessment = await db.get(Assessment, assessment_id)

    # ✅ OWNERSHIP CHECK (prevents IDOR)
    if assessment.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your assessment")

    # Proceed with deletion
```

**Pattern for All Protected Endpoints:**
```python
async def update_resource(
    resource_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    # 1. Fetch resource
    resource = await db.get(Model, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Not found")

    # 2. Check ownership
    if resource.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 3. Proceed with operation
```

---

## 🛠️ Common Security Tasks

### Adding a New Protected Endpoint

```python
from app.api.v1.deps import get_current_active_user
from app.db.models.user import User

@router.post("/api/v1/protected-resource")
async def create_protected_resource(
    resource_data: ResourceCreate,
    current_user: User = Depends(get_current_active_user),  # ✅ Auth required
    db: AsyncSession = Depends(get_async_db)
):
    # Automatic CSRF protection (via middleware)
    # Automatic authorization (via dependency)

    # Create resource with current user as owner
    new_resource = Model(
        **resource_data.dict(),
        owner_id=current_user.id  # ✅ Track ownership
    )
    db.add(new_resource)
    await db.commit()
    return new_resource
```

### Adding Admin-Only Endpoints

```python
from app.api.v1.deps import get_current_admin_user

@router.get("/api/v1/admin/metrics")
async def get_admin_metrics(
    current_admin: User = Depends(get_current_admin_user),  # ✅ Admin required
    db: AsyncSession = Depends(get_async_db)
):
    # Only accessible by users with role="admin"
    return {"sensitive": "metrics"}
```

### Creating Security Tests

```python
# tests/test_security_automated.py

class TestMyFeatureSecurity:
    def test_unauthorized_access_blocked(self, client: TestClient):
        """Test that unauthorized users cannot access the feature"""
        response = client.get("/api/v1/protected-resource")
        assert response.status_code in [401, 403]

    def test_idor_prevented(self, client: TestClient):
        """Test users cannot access other users' resources"""
        # Login as user1
        client.post("/api/v1/auth/token-fixed", data={
            "username": "user1@example.com",
            "password": "password123"
        })

        # Try to access user2's resource
        response = client.get("/api/v1/resources/999")  # user2's resource
        assert response.status_code in [403, 404]
```

---

## 📊 Security Metrics Reference

### Dashboard API Endpoints

```typescript
import { getSecurityMetrics, getSecurityEvents, getSecurityTimeline } from '@/services/securityService';

// Get overall metrics (last 24 hours)
const metrics = await getSecurityMetrics(24);

// Get security events with filtering
const events = await getSecurityEvents(50, 'failed_login');

// Get timeline data
const timeline = await getSecurityTimeline(24);

// Send test alert
await sendTestAlert('suspicious_activity');
```

**Response Structure:**
```typescript
{
  "authentication": {
    "total_login_attempts": 1523,
    "successful_logins": 1487,
    "failed_logins": 36,
    "blocked_by_rate_limit": 8
  },
  "authorization": {
    "total_requests": 8542,
    "authorized_requests": 8398,
    "unauthorized_requests": 144,
    "idor_attempts_prevented": 3
  },
  "csrf": {
    "csrf_violations": 15,
    "blocked_requests": 15
  },
  "top_blocked_ips": [
    {"ip": "192.168.1.100", "attempts": 45, "reason": "Rate limit exceeded"}
  ],
  "recent_events": [...]
}
```

---

## 🔐 Security Checklist

### Pre-Commit Checklist

- [ ] No tokens in localStorage (use cookies)
- [ ] No `dangerouslySetInnerHTML` (use React JSX)
- [ ] All protected endpoints use `get_current_active_user`
- [ ] All resources have ownership checks
- [ ] Input validation on all user inputs
- [ ] Parameterized queries (no string concatenation)
- [ ] Error messages don't leak sensitive info

### Pre-Deployment Checklist

- [ ] Test endpoints removed/disabled
- [ ] Admin user account created
- [ ] Test users removed
- [ ] CSRF middleware enabled
- [ ] Rate limiting configured
- [ ] Security headers set
- [ ] TLS certificates valid
- [ ] CORS restricted to production domains
- [ ] Environment variables secured
- [ ] Audit logging enabled
- [ ] Security tests passing
- [ ] Dependencies scanned for vulnerabilities

---

## 🚨 Security Incident Response

### Detecting Suspicious Activity

```bash
# Check the dashboard for:
- Multiple failed logins from same IP
- Rapid requests from single user
- CSRF violations
- Authorization failures
- IDOR attempts prevented

# Or query logs directly:
grep "failed_login" logs/app.log | tail -20
grep "csrf_violation" logs/app.log | tail -20
grep "authorization_failed" logs/app.log | tail -20
```

### Responding to Incidents

**1. Brute Force Attack Detected:**
```bash
# Block IP (via firewall or application)
# Example: Add to blocked IPs list
# See: app/core/security_middleware.py
```

**2. CSRF Violation Spike:**
```bash
# Check if CSRF token generation is working
curl -c cookies.txt -X POST http://localhost:8000/api/v1/auth/token-fixed \
  -d "username=admin@psychsync.com&password=xxx"

# Verify csrf_token cookie exists
cat cookies.txt
```

**3. Unauthorized Access Attempt:**
```python
# Review audit logs
from app.core.audit_logging import audit_logger

# Get recent failed authorization attempts
failed_attempts = await audit_logger.get_recent_events(
    event_type="authorization_failed",
    limit=50
)
```

---

## 📚 Important Files Reference

| File | Purpose |
|------|---------|
| `app/core/security.py` | Password hashing, JWT tokens |
| `app/core/audit_logging.py` | Security event logging |
| `app/core/simple_rate_limiter.py` | Rate limiting |
| `app/api/v1/deps.py` | Auth dependencies (get_current_user, etc.) |
| `app/api/v1/endpoints/auth.py` | Login/logout/token refresh |
| `app/api/v1/endpoints/security_monitoring_public.py` | Security metrics API |
| `frontend/src/services/api.ts` | API client (CSRF, cookies) |
| `frontend/src/services/securityService.ts` | Security dashboard API calls |
| `frontend/src/components/admin/SecurityDashboard.tsx` | Security dashboard UI |
| `tests/test_security_automated.py` | Security test suite |
| `docs/SECURITY_ARCHITECTURE.md` | Detailed security documentation |

---

## 🧪 Testing Security Features

### Manual Testing CSRF Protection

```bash
# 1. Login to get CSRF token
curl -c cookies.txt -X POST http://localhost:8000/api/v1/auth/token-fixed \
  -d "username=admin@psychsync.com&password=xxx"

# 2. Try POST without CSRF token (should fail)
curl -b cookies.txt -X POST http://localhost:8000/api/v1/assessments \
  -H "Content-Type: application/json" \
  -d '{"title": "test"}'
# Expected: 403 Forbidden

# 3. Try POST with CSRF token (should succeed if authenticated)
CSRF_TOKEN=$(grep csrf_token cookies.txt | cut -f7)
curl -b cookies.txt -X POST http://localhost:8000/api/v1/assessments \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" \
  -d '{"title": "test"}'
# Expected: 200 OK or 422 validation error
```

### Manual Testing Authorization

```bash
# 1. Login as regular user
curl -c user_cookies.txt -X POST http://localhost:8000/api/v1/auth/token-fixed \
  -d "username=user@example.com&password=xxx"

# 2. Try to access admin endpoint (should fail)
curl -b user_cookies.txt http://localhost:8000/api/v1/dashboard/metrics
# Expected: 403 Forbidden

# 3. Try to access another user's resource (should fail)
curl -b user_cookies.txt http://localhost:8000/api/v1/assessments/999
# Expected: 403 Forbidden or 404 Not Found
```

---

## 💡 Security Best Practices

### DO ✅

- Use httpOnly cookies for tokens
- Include CSRF tokens in state-changing requests
- Verify ownership before resource access
- Use parameterized queries
- Validate all user input
- Log security events
- Use rate limiting on auth endpoints
- Encrypt sensitive data
- Keep dependencies updated
- Run security tests regularly

### DON'T ❌

- Store tokens in localStorage
- Use `dangerouslySetInnerHTML`
- Trust client-side input
- Concatenate SQL strings
- Expose sensitive data in errors
- Disable CSRF middleware
- Hardcode credentials
- Use weak passwords
- Ignore security warnings
- Skip security tests

---

## 🔗 Related Documentation

- **Full Security Architecture:** `docs/SECURITY_ARCHITECTURE.md`
- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Test Documentation:** `tests/README.md`
- **Deployment Guide:** `docs/DEPLOYMENT.md`

---

## 🆘 Getting Help

### Security Questions?
- Review `docs/SECURITY_ARCHITECTURE.md`
- Check the security dashboard: `/admin/security`
- Run security tests: `./scripts/run_security_tests.sh`

### Found a Security Issue?
- Email: security@psychsync.com
- See: `docs/SECURITY_BOUNTY_PROGRAM.md`

**Remember:** Security is everyone's responsibility! Always follow secure coding practices.
