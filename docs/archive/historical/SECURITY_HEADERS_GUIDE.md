# Security Headers Implementation Guide for PsychSync

## Overview
This document provides comprehensive security headers for all FastAPI responses in the PsychSync application.

## Implementation

### 1. Security Headers Middleware

```python
from fastapi import FastAPI, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds comprehensive security headers to all API responses.

    Security Headers Included:
    - X-Content-Type-Options: Prevents MIME sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: XSS protection
    - Content-Security-Policy: Controls resource loading
    - Strict-Transport-Security: HTTPS enforcement
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    - Cross-Origin-Opener-Policy: Window control
    - Cross-Origin-Resource-Policy: Resource sharing
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "img-src 'self' data: https: blob:",
            "font-src 'self' https://fonts.gstatic.com",
            "connect-src 'self' https://*.github.com https://api.github.com",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-src 'none'",
            "object-src 'none'",
            "manifest-src 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # HTTPS enforcement (only in production)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        permissions_policy = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_policy)

        # Cross-Origin policies
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # Cache control for sensitive endpoints
        if request.url.path in ["/auth/login", "/auth/register", "/auth/refresh"]:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        # Remove server information
        response.headers.pop("Server", None)

        return response
```

### 2. Integration with FastAPI App

```python
from app.core.config import settings

app = FastAPI()

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)

# Custom server header
@app.middleware("http")
async def remove_server_header(request: Request, call_next):
    response = await call_next(request)
    # Remove server info
    response.headers.pop("Server", None)
    # Add custom server header (optional)
    response.headers["Server"] = "PsychSync"
    return response
```

### 3. CORS Configuration (app/core/config.py)

```python
from fastapi.middleware.cors import CORSMiddleware

# CORS settings
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "https://psychsync.example.com",  # Production
    "https://www.psychsync.example.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-CSRF-Token",
        "X-Requested-With",
    ],
    expose_headers=["X-Total-Count", "X-Request-ID"],
    max_age=600,  # 10 minutes
)
```

### 4. Rate Limiting Headers

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    response = JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"}
    )
    response.headers["Retry-After"] = str(exc.retry_after)
    response.headers["X-RateLimit-Limit"] = str(exc.detail.limit)
    response.headers["X-RateLimit-Remaining"] = "0"
    response.headers["X-RateLimit-Reset"] = str(exc.reset_time)
    return response
```

## Header Reference Table

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME type sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS protection |
| `Content-Security-Policy` | *see above* | Controls resource loading |
| `Strict-Transport-Security` | `max-age=31536000` | HTTPS enforcement (prod only) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controls referrer info |
| `Permissions-Policy` | *see above* | Controls browser features |
| `Cross-Origin-Opener-Policy` | `same-origin` | Window control |
| `Cross-Origin-Resource-Policy` | `same-origin` | Resource sharing |
| `Cache-Control` | `no-store` | For auth endpoints |

## Testing Security Headers

### Using curl:
```bash
curl -I https://api.psychsync.com/health

# Expected output includes:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Strict-Transport-Security: max-age=31536000
# Content-Security-Policy: default-src 'self'...
```

### Python Test:
```python
import requests

def test_security_headers():
    response = requests.get("https://api.psychsync.com/health")

    required_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Content-Security-Policy",
        "Referrer-Policy",
        "Permissions-Policy",
    ]

    for header in required_headers:
        assert header in response.headers, f"Missing {header}"

    print("✅ All security headers present")
```

## Environment-Specific Configuration

```python
# Development (allow localhost, no HSTS)
DEBUG = True
CORS_ORIGINS = ["http://localhost:*"]

# Staging (strict but allow testing)
DEBUG = False
CORS_ORIGINS = ["https://staging.psychsync.com"]
HSTS_MAX_AGE = 3600  # 1 hour

# Production (maximum security)
DEBUG = False
CORS_ORIGINS = ["https://psychsync.com", "https://www.psychsync.com"]
HSTS_MAX_AGE = 31536000  # 1 year
HSTS_INCLUDE_SUBDOMAINS = True
HSTS_PRELOAD = True
```

## Monitoring & Alerts

```python
# Add to monitoring/metrics.py
from prometheus_client import Counter

security_header_missing = Counter(
    'security_header_missing_total',
    'Total missing security headers',
    ['header_name']
)

def check_security_headers(response: Response):
    required_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Content-Security-Policy",
    ]

    for header in required_headers:
        if header not in response.headers:
            security_header_missing.labels(header_name=header).inc()
```

## Compliance Notes

- **OWASP**: Meets OWASP security header recommendations
- **PCI-DSS**: Suitable for payment processing (when implemented with HTTPS)
- **GDPR**: Helps with data protection (no tracking without consent)
- **SOC 2**: Demonstrates security controls

## Maintenance

- Review CSP directives quarterly
- Update CORS origins when adding new domains
- Test headers after every deployment
- Monitor security header bypass attempts
- Keep dependencies updated for latest security patches

---

**Status**: ✅ Complete
**Next**: Zero-Downtime Deployment Plan
