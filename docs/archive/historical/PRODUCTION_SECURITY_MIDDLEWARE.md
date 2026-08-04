# Production Security Middleware Guide

Complete guide for implementing and using PsychSync's production security middleware.

**Last Updated:** 2025-12-24

---

## 🚀 Quick Start

### 1. Enable Middleware in main.py

```python
# app/main.py

from fastapi import FastAPI
from app.middleware.production_security import configure_production_security

# Create FastAPI app
app = FastAPI(title="PsychSync")

# Apply all security middleware
configure_production_security(app)

# Then add your routes
from app.api.v1.api import api_router
app.include_router(api_router)
```

### 2. Verify Middleware is Active

```bash
# Start the application
uvicorn app.main:app --reload

# Check logs for:
# ✅ Production security middleware configured

# Make a test request
curl -I http://localhost:8000/api/v1/health

# Check for security headers:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# Content-Security-Policy: ...
```

---

## 📚 Middleware Components

### 1. Input Validation Middleware

**Purpose:** Prevents injection attacks (SQL, XSS, command injection)

**Validates:**
- Request size (max 10MB)
- Content-Type (only JSON and multipart/form-data)
- URL patterns (blocks malicious patterns)

**Blocked Patterns:**
```python
# SQL injection
UNION, SELECT, DROP, INSERT, UPDATE, DELETE

# XSS
<script> tags, javascript:, onerror=

# Command injection
|, ;, $(), `

# Path traversal
../
```

**Testing:**
```bash
# Should be blocked
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin"} UNION SELECT * FROM users--'

# Expected: 400 Bad Request
```

---

### 2. Smart Rate Limiting Middleware

**Purpose:** Prevents brute force, DoS, and credential stuffing

**Rate Limits:**
| Endpoint Type | Limit | Period |
|--------------|-------|--------|
| Auth (`/auth/`) | 5 requests | per minute |
| General API | 100 requests | per minute |
| Export | 10 requests | per hour |
| Upload | 20 requests | per hour |

**Features:**
- IP-based tracking
- Exponential backoff for repeat offenders
- Rate limit headers in responses
- Automatic ban escalation

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
Retry-After: 60
```

**Testing:**
```bash
# Make 6 rapid login requests (exceeds limit of 5)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/token \
    -d "username=test&password=test"
done

# 6th request should return: 429 Too Many Requests
```

---

### 3. Security Headers Middleware

**Purpose:** Browser-level security controls

**Headers Added:**

| Header | Value | Purpose |
|--------|-------|---------|
| `Content-Security-Policy` | `default-src 'self'...` | XSS prevention |
| `X-Frame-Options` | `DENY` | Clickjacking prevention |
| `X-Content-Type-Options` | `nosniff` | MIME sniffing prevention |
| `X-XSS-Protection` | `1; mode=block` | XSS protection |
| `Strict-Transport-Security` | `max-age=31536000...` | HTTPS enforcement (prod only) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer control |
| `Permissions-Policy` | `geolocation=(), ...` | Feature control |

**Testing:**
```bash
# Check security headers
curl -I http://localhost:8000/api/v1/health | grep -E "X-|Content-Security"

# Should see all security headers
```

---

### 4. Audit Logging Middleware

**Purpose:** GDPR compliance and incident response

**Logged For:**
- Authentication endpoints (`/auth/`)
- User management (`/users/`)
- Team management (`/teams/`)
- Assessments (`/assessments/`)
- Data export (`/export/`)
- Admin endpoints (`/admin/`)

**Log Data:**
```json
{
  "timestamp": "2025-12-24T12:00:00",
  "request_id": "a1b2c3d4e5f6...",
  "event_type": "api_request",
  "user_id": "user@example.com",
  "ip_address": "192.168.1.100",
  "method": "POST",
  "path": "/api/v1/auth/login",
  "user_agent": "Mozilla/5.0...",
  "status_code": 200,
  "duration_ms": 123.45
}
```

**Request ID:**
Each request gets a unique ID for tracing:
```bash
curl -I http://localhost:8000/api/v1/users/me

# Response header:
# X-Request-ID: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

---

### 5. Request Size Limiting Middleware

**Purpose:** Prevents DoS via large payloads

**Limits:**
- Maximum request size: 10MB
- Applied to all requests
- Checked via Content-Length header

**Testing:**
```bash
# Should be blocked (> 10MB)
curl -X POST http://localhost:8000/api/v1/upload \
  -H "Content-Length: 15000000" \
  -d "$(python -c 'print("A" * 15000000)')"

# Expected: 413 Payload Too Large
```

---

## 🔧 Configuration

### Customizing Rate Limits

```python
# In app/middleware/production_security.py

class SmartRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

        # Customize limits
        self.limits = {
            "auth": ("10", 60),      # Changed: 10/minute
            "api": ("200", 60),      # Changed: 200/minute
            "export": ("20", 3600),  # Changed: 20/hour
            "upload": ("50", 3600),  # Changed: 50/hour
        }
```

### Customizing Security Headers

```python
# In app/middleware/production_security.py

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)

        # Customize CSP for your needs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.example.com; "  # Added CDN
            "img-src 'self' data: https://images.example.com; "  # Added image domain
            # ... more rules
        )

        return response
```

### Customizing Audit Logging

```python
# In app/middleware/production_security.py

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    SENSITIVE_ENDPOINTS = [
        "/auth/",
        "/users/",
        # Add more endpoints to log
        "/payments/",
        "/admin/",
    ]
```

---

## 🧪 Testing

### Unit Tests

```python
# tests/test_middleware.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_input_validation_blocks_sql_injection():
    client = TestClient(app)

    response = client.post("/api/v1/auth/login", json={
        "username": "admin' UNION SELECT * FROM users--",
        "password": "test"
    })

    assert response.status_code == 400
    assert "Invalid request" in response.json()["detail"]

def test_rate_limiting():
    client = TestClient(app)

    # Make 6 rapid requests (limit is 5)
    responses = []
    for i in range(6):
        responses.append(client.post("/api/v1/auth/token", data={
            "username": "test",
            "password": "test"
        }))

    # First 5 should work, 6th should be rate limited
    assert responses[0].status_code != 429
    assert responses[5].status_code == 429

def test_security_headers():
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers
```

### Integration Tests

```bash
# Test all middleware components
pytest tests/test_production_middleware.py -v

# Test specific middleware
pytest tests/test_production_middleware.py::test_input_validation -v
pytest tests/test_production_middleware.py::test_rate_limiting -v
pytest tests/test_production_middleware.py::test_security_headers -v
```

---

## 📊 Monitoring

### Metrics to Track

1. **Rate Limit Blocks**
   ```python
   # Count 429 responses
   from app.middleware.production_security import SmartRateLimitMiddleware

   # Access request_counts to see blocked IPs
   ```

2. **Input Validation Failures**
   ```python
   # Check logs for:
   # "Malicious pattern detected in URL"
   ```

3. **Request Size Rejections**
   ```python
   # Check logs for:
   # "Request too large: X bytes"
   ```

4. **Audit Log Volume**
   ```python
   # Monitor sensitive endpoint usage
   # Check for unusual patterns
   ```

---

## 🚨 Troubleshooting

### Issue: "All requests being rate limited"

**Cause:** Clock synchronization or shared tracking issue

**Solution:**
```python
# Use Redis for production rate limiting
import redis
from redis import asyncio as aioredis

redis_client = await aioredis.from_url("redis://localhost:6379/0")

# Store rate limit data in Redis instead of memory
await redis_client.incr(rate_key)
await redis_client.expire(rate_key, period)
```

### Issue: "CSP blocking legitimate resources"

**Cause:** Content-Security-Policy too strict

**Solution:**
```python
# Add your CDN/domains to CSP
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.example.com https://cdnjs.cloudflare.com; "
    # ... add more sources
)
```

### Issue: "Audit logs too verbose"

**Cause:** Logging too many endpoints

**Solution:**
```python
# Reduce logged endpoints
class AuditLoggingMiddleware(BaseHTTPMiddleware):
    SENSITIVE_ENDPOINTS = [
        "/auth/",  # Keep auth
        "/users/create",  # Only specific user endpoints
        "/admin/",  # Keep admin
    ]
```

---

## 🔐 Best Practices

### 1. Order Matters
Apply middleware in this order:
```
Request Size → Input Validation → Rate Limit → Security Headers → Audit Logging
```

### 2. Tune for Your Load
Adjust rate limits based on:
- Expected traffic
- Server capacity
- Business requirements

### 3. Monitor Regularly
Check logs for:
- Rate limit violations (potential attacks)
- Input validation failures (potential attacks)
- Unusual patterns (legitimate users hitting limits)

### 4. Test Before Deploying
Always test in staging:
```bash
# Load test rate limits
ab -n 1000 -c 10 http://staging.example.com/api/v1/health

# Test input validation
curl -X POST http://staging.example.com/api/v1/auth/login \
  -d '{"username": "admin\x27 OR 1=1--", "password": "test"}'
```

---

## 📚 Related Documentation

- **Security Architecture:** `docs/SECURITY_ARCHITECTURE.md`
- **Secure Configuration:** `docs/SECURE_CONFIGURATION_GUIDE.md`
- **Security Testing:** `tests/test_security_automated.py`

---

## ✅ Production Checklist

Before deploying with middleware:

- [ ] Input validation patterns reviewed
- [ ] Rate limits tuned for expected traffic
- [ ] Security headers tested with your frontend
- [ ] Audit logging configured for your compliance needs
- [ ] Request size limits appropriate for your use case
- [ ] Monitoring set up for middleware metrics
- [ ] Incident response procedure documented
- [ ] Team trained on middleware behavior

---

**Remember:** Security middleware is your first line of defense. Configure it properly, test thoroughly, and monitor continuously.
