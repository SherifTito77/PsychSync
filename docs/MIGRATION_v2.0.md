# Migration Guide: v2.0 Security Hardening

**Version**: 2.0.0
**Release Date**: 2025-12-27
**Breaking Changes**: Yes

This guide helps you migrate from PsychSync v1.0 to v2.0 with comprehensive security improvements.

---

## Table of Contents

1. [Overview of Changes](#overview-of-changes)
2. [Backend Migration](#backend-migration)
3. [Frontend Migration](#frontend-migration)
4. [Database Migration](#database-migration)
5. [Testing & Verification](#testing--verification)
6. [Rollback Procedure](#rollback-procedure)

---

## Overview of Changes

### Breaking Changes

1. **Authentication Tokens Moved to httpOnly Cookies**
   - JWT tokens no longer returned in JSON response body
   - Tokens now stored in httpOnly cookies (XSS protection)
   - Frontend must remove `Authorization` header usage

2. **Error Messages Genericized**
   - Detailed error information removed from responses
   - Error codes now standardized
   - Frontend must update error handling

3. **CSRF Protection Enabled**
   - State-changing operations require CSRF token
   - Frontend must include CSRF token in requests

### New Security Features

- ✅ Comprehensive audit logging
- ✅ Rate limiting on all endpoints
- ✅ XSS protection via JSON serialization
- ✅ SQL injection prevention
- ✅ IDOR protection
- ✅ SSRF protection

---

## Backend Migration

### Step 1: Update Dependencies

```bash
# Update requirements
pip install --upgrade -r requirements.txt

# Key updates:
# - fastapi >= 0.104.0
# - pydantic >= 2.4.0
# - sqlalchemy >= 2.0.23
```

### Step 2: Database Migration

```bash
# Apply new audit logs migration
alembic upgrade head

# Verify migration
alembic current
```

**New Tables**:
- `audit_logs` - Security event tracking
- `security_events` - Detailed security metadata

### Step 3: Update Environment Variables

Add to `.env`:

```bash
# Security
SECURITY_MIDDLEWARE_ENABLED=true
SPOTLIGHTING_MODE=strict  # or 'permissive' for dev
AUDIT_LOGGING_ENABLED=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Session Management
SESSION_TIMEOUT_SECONDS=1800
REFRESH_TOKEN_EXPIRY_DAYS=7
```

### Step 4: Replace Authentication Endpoints

**OLD** (v1.0):
```python
from app.api.v1.endpoints.auth import router as auth_router
```

**NEW** (v2.0):
```python
from app.api.v1.endpoints.auth_secure import router as auth_router
```

### Step 5: Update Imports

Replace old imports with secure versions:

```python
# OLD
from app.api.v1.endpoints.auth import router

# NEW
from app.api.v1.endpoints.auth_secure import router
```

---

## Frontend Migration

### Step 1: Remove Authorization Header

**OLD** (v1.0):
```typescript
// Set JWT in header
const response = await fetch('/api/v1/users/me', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

**NEW** (v2.0):
```typescript
// No Authorization header needed - httpOnly cookies handle it
const response = await fetch('/api/v1/users/me', {
  headers: {
    'Content-Type': 'application/json'
  },
  credentials: 'include'  // Important: include cookies
});
```

### Step 2: Update Login Flow

**OLD** (v1.0):
```typescript
// Login returns token in response
const response = await fetch('/api/v1/auth/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    username: email,
    password: password
  })
});

const data = await response.json();
localStorage.setItem('token', data.access_token);  // ❌ Vulnerable to XSS
```

**NEW** (v2.0):
```typescript
// Login sets httpOnly cookies automatically
const response = await fetch('/api/v1/auth/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  credentials: 'include',  // Important: receive cookies
  body: new URLSearchParams({
    username: email,
    password: password
  })
});

// No need to store token - cookies handle it automatically
// Just verify login succeeded
if (response.ok) {
  const data = await response.json();
  // data.user contains user info
  // No token storage needed!
}
```

### Step 3: Add CSRF Token to State-Changing Requests

**NEW** (v2.0):
```typescript
// Get CSRF token from cookie
const getCsrfToken = (): string => {
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : '';
};

// Include CSRF token in POST/PUT/DELETE requests
const response = await fetch('/api/v1/users/me', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': getCsrfToken()  // NEW: CSRF protection
  },
  credentials: 'include',
  body: JSON.stringify(updateData)
});
```

### Step 4: Update Error Handling

**OLD** (v1.0):
```typescript
if (response.status === 401) {
  const error = await response.json();
  showMessage(error.detail);  // Detailed error message
}
```

**NEW** (v2.0):
```typescript
if (response.status === 401) {
  // Generic error message - don't leak info
  showMessage('Authentication failed. Please check your credentials.');
} else if (response.status === 403) {
  showMessage('You don\'t have permission to perform this action.');
} else if (response.status === 429) {
  showMessage('Too many requests. Please try again later.');
}
```

### Step 5: Update Axios Configuration (if using Axios)

**OLD** (v1.0):
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});
```

**NEW** (v2.0):
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,  // Important: send cookies
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add CSRF token to state-changing requests
api.interceptors.request.use((config) => {
  if (['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase() || '')) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken;
    }
  }
  return config;
});
```

### Step 6: Remove Token Refresh Logic

**OLD** (v1.0):
```typescript
// Manual token refresh
const refreshToken = async () => {
  const response = await fetch('/api/v1/auth/refresh-token', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('refresh_token')}`
    }
  });
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
};
```

**NEW** (v2.0):
```typescript
// Token refresh automatic via httpOnly cookies
// Just make the request - cookies handle it
const refreshSession = async () => {
  const response = await fetch('/api/v1/auth/refresh-token', {
    method: 'POST',
    credentials: 'include'
  });

  if (response.ok) {
    // New token automatically set in httpOnly cookie
    return true;
  }
  return false;
};
```

---

## Database Migration

### New Tables

#### audit_logs
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    user_id UUID,
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    success BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_user_id (user_id),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
);
```

### Migration Steps

```bash
# 1. Backup database
pg_dump -U postgres psychsync > backup_before_migration.sql

# 2. Run migration
alembic upgrade head

# 3. Verify tables created
psql -U postgres -d psychsync -c "\dt audit_logs"

# 4. Check migration status
alembic current
```

---

## Testing & Verification

### Backend Tests

```bash
# Run security tests
pytest tests/integration/test_owasp_security.py -v

# Run all tests
pytest tests/ -v

# Check coverage
pytest --cov=app --cov-report=html
```

### Frontend Tests

```typescript
// Test: Login without Authorization header
it('should login with cookies', async () => {
  const response = await fetch('/api/v1/auth/token', {
    method: 'POST',
    credentials: 'include',
    body: new URLSearchParams({
      username: 'test@example.com',
      password: 'TestPass123!'
    })
  });

  expect(response.ok).toBe(true);
  // Cookies set automatically
  expect(document.cookie).toContain('access_token');
});

// Test: CSRF token included
it('should include CSRF token in POST requests', async () => {
  const csrfToken = getCsrfToken();

  const response = await fetch('/api/v1/users/me', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrfToken
    },
    credentials: 'include',
    body: JSON.stringify({ full_name: 'Updated Name' })
  });

  expect(response.ok).toBe(true);
});
```

### Manual Testing Checklist

- [ ] Login works without storing tokens in localStorage
- [ ] Cookies are visible in browser DevTools (Application > Cookies)
- [ ] `access_token` cookie has `httpOnly` flag
- [ ] `access_token` cookie has `secure` flag
- [ ] CSRF token is present in non-httpOnly cookie
- [ ] API requests work without Authorization header
- [ ] Logout clears all cookies
- [ ] Error messages are generic

---

## Rollback Procedure

If you need to rollback to v1.0:

### Backend Rollback

```bash
# 1. Revert code
git checkout v1.0.0

# 2. Revert database
alembic downgrade -1

# 3. Restart services
systemctl restart psychsync-backend
```

### Frontend Rollback

```bash
# 1. Revert frontend code
git checkout v1.0.0

# 2. Rebuild
npm run build

# 3. Clear browser cookies
# Users will need to re-login
```

---

## Troubleshooting

### Issue: "CSRF token missing"

**Solution**: Ensure you're reading the `csrf_token` cookie and including it in request headers.

```typescript
const getCsrfToken = (): string => {
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : '';
};
```

### Issue: "401 Unauthorized" after login

**Solution**: Ensure `credentials: 'include'` is set in fetch requests.

### Issue: CORS errors

**Solution**: Update CORS configuration to allow credentials:

```python
# Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,  # Important!
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Performance Considerations

### Additional Latency

- Security checks add ~5-10ms per request
- Audit logging adds ~2-3ms for database writes
- Rate limiting checks add ~1-2ms

### Optimization Tips

1. **Async Audit Logging**: Use message queue (RabbitMQ/Redis)
2. **Cached Results**: Cache frequently accessed data
3. **Connection Pooling**: Reuse database connections

---

## Security Best Practices (Post-Migration)

### Do's ✅

- ✅ Always use `credentials: 'include'` in fetch/axios
- ✅ Include CSRF token in state-changing requests
- ✅ Store CSRF token in memory (not localStorage)
- ✅ Handle generic error messages gracefully
- ✅ Log out users on rate limit errors

### Don'ts ❌

- ❌ Don't store tokens in localStorage/sessionStorage
- ❌ Don't include Authorization header
- ❌ Don't expose detailed error messages to users
- ❌ Don't bypass CSRF protection
- ❌ Don't ignore rate limiting errors

---

## Support

**Documentation**:
- ADR: `docs/ADR/2025-12-27-owasp-security-hardening.md`
- Security Guide: `docs/LLM_SECURITY_POLICY.md`
- API Documentation: `https://api.psychsync.ai/docs`

**Issues**: Report at https://github.com/your-org/psychsync/issues

**Security**: security@psychsync.ai

---

**Last Updated**: 2025-12-27
**Version**: 2.0.0
