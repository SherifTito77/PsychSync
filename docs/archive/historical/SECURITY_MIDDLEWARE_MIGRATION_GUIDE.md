# Security Middleware Consolidation - Migration Guide

## Overview

The codebase had **15+ duplicate security middleware implementations** across ~8,000 lines of code. These have been consolidated into a single, modular system using composition over inheritance.

## What Changed

### Old Files (TO BE DELETED)

**Middleware files** (~2,961 lines):
- `app/middleware/security.py` (571 lines)
- `app/middleware/security_middleware.py` (441 lines)
- `app/middleware/enterprise_security_middleware.py`
- `app/middleware/comprehensive_security_headers.py`
- `app/middleware/security_headers.py`
- `app/middleware/csrf_xss_protection.py`
- `app/middleware/production_security.py`

**Core files** (~5,096 lines):
- `app/core/security_advanced.py` (SecurityMiddleware class)
- `app/core/security_middleware.py`
- Plus duplicate code in 6 other security files

### New Files

**Unified Security Middleware Package**:
```
app/middleware/security_unified/
├── __init__.py          # Package exports
├── utils.py             # Common utilities (get_client_ip, etc.)
└── middleware.py        # Main UnifiedSecurityMiddleware class
```

**Total**: ~800 lines (vs. 8,000+ old lines) = **90% reduction**

## Key Features

### 1. Modular Design
Each security feature is independent and can be enabled/disabled:
- Security headers (OWASP compliant)
- CSRF protection
- IP blocking
- Attack tool detection
- Request logging

### 2. Single Source of Truth
- `get_client_ip()` - ONE implementation (was duplicated in 14 files)
- CSP templates - ONE set of templates
- Attack tool signatures - ONE list
- Security headers - ONE implementation

### 3. Configuration-Driven
All features controlled via `SecurityConfig` dataclass:
```python
config = SecurityConfig(
    csrf_protection_enabled=True,
    ip_blocking_enabled=True,
    csp_level="high",  # low, medium, high, strict
    exclude_paths={"/health", "/metrics"},
)
```

## Migration Steps

### Step 1: Update Imports

**Before:**
```python
from app.middleware.security import SecurityMiddleware, SecurityConfig
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.csrf_xss_protection import CSRFProtectionMiddleware
from app.middleware.comprehensive_security_headers import ComprehensiveSecurityHeadersMiddleware
```

**After:**
```python
from app.middleware.security_unified import (
    UnifiedSecurityMiddleware,
    SecurityConfig,
)
```

### Step 2: Update Middleware Registration

**Before:**
```python
from app.middleware.security import SecurityMiddleware
from app.middleware.comprehensive_security_headers import ComprehensiveSecurityHeadersMiddleware
from app.middleware.csrf_xss_protection import CSRFProtectionMiddleware

app.add_middleware(SecurityMiddleware, config=security_config)
app.add_middleware(ComprehensiveSecurityHeadersMiddleware)
app.add_middleware(CSRFProtectionMiddleware, secret_key=settings.SECRET_KEY)
```

**After:**
```python
from app.middleware.security_unified import UnifiedSecurityMiddleware, SecurityConfig

config = SecurityConfig(
    csrf_protection_enabled=True,
    ip_blocking_enabled=True,
    attack_detection_enabled=True,
    security_headers_enabled=True,
    csp_level="high",
)

app.add_middleware(UnifiedSecurityMiddleware, config=config)
```

### Step 3: Update Utility Function Calls

**Before:**
```python
# Multiple implementations across different files
from app.middleware.security import SecurityMiddleware
middleware = SecurityMiddleware(app)
client_ip = middleware._get_client_ip(request)  # Private method
```

**After:**
```python
from app.middleware.security_unified import get_client_ip

client_ip = get_client_ip(request)  # Public utility function
```

### Step 4: Update Security Configuration

**Before:**
```python
@dataclass
class SecurityConfig:
    csrf_protect: bool = True
    csrf_token_expiry: int = 3600
    security_headers: bool = True
    csp_enabled: bool = True
    # ... 20+ more fields
```

**After:**
```python
from app.middleware.security_unified import SecurityConfig

config = SecurityConfig(
    # Feature toggles
    csrf_protection_enabled=True,
    security_headers_enabled=True,
    ip_blocking_enabled=True,

    # CSP configuration
    csp_level="high",  # low, medium, high, strict

    # Exclusions
    exclude_paths={"/health", "/metrics", "/docs"},
)
```

## Configuration Reference

### SecurityConfig Options

```python
@dataclass
class SecurityConfig:
    # Feature Toggles
    security_headers_enabled: bool = True
    csrf_protection_enabled: bool = True
    ip_blocking_enabled: bool = True
    attack_detection_enabled: bool = True
    request_logging_enabled: bool = False

    # Security Headers
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    csp_level: str = "medium"  # low, medium, high, strict

    # CSRF
    csrf_cookie_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"
    csrf_token_expiry: int = 3600
    csrf_safe_methods: set = {"GET", "HEAD", "OPTIONS", "TRACE"}

    # IP Blocking
    failed_login_threshold: int = 5
    ip_block_duration: int = 900  # 15 minutes
    max_requests_per_minute: int = 60

    # Attack Detection
    block_known_attack_tools: bool = True
    log_suspicious_paths: bool = True

    # Exclusions
    exclude_paths: set = {"/health", "/metrics", "/docs", "/redoc"}
    exclude_ips: set = set()  # IPs to skip security checks
```

## Utility Functions

### Available Utilities

```python
from app.middleware.security_unified import (
    # IP extraction
    get_client_ip,           # Extract IP from request (handles proxies)
    get_client_info,         # Get comprehensive client info dict

    # Detection
    detect_attack_tool,      # Detect sqlmap, nikto, etc.
    is_suspicious_path,      # Check for attack patterns in path
    is_sensitive_endpoint,   # Check if endpoint needs extra security

    # Headers
    get_security_headers_default,  # OWASP default headers
    get_csp_template,        # Get CSP by security level
)
```

### Example Usage

```python
from app.middleware.security_unified import get_client_ip, detect_attack_tool

# Get client IP (handles all proxy headers correctly)
ip = get_client_ip(request)

# Detect attack tools
tool = detect_attack_tool(request.headers.get("User-Agent"))
if tool:
    logger.warning(f"Attack tool detected: {tool}")
```

## Management Methods

The `UnifiedSecurityMiddleware` provides management methods:

```python
middleware = UnifiedSecurityMiddleware(app, config)

# Manual IP management
middleware.block_ip("192.168.1.100", duration=3600, reason="manual_block")
middleware.unblock_ip("192.168.1.100")
middleware.get_blocked_ips()  # Get all blocked IPs

# Clear failed attempts
middleware.clear_failed_attempts("192.168.1.100")

# Get statistics
stats = middleware.get_security_stats()
```

## Testing

### Unit Testing

```python
import pytest
from app.middleware.security_unified import (
    UnifiedSecurityMiddleware,
    SecurityConfig,
    get_client_ip,
)

def test_client_ip_extraction():
    from fastapi import Request

    # Test with proxy headers
    request = Request(scope={
        "type": "http",
        "headers": [(b"x-forwarded-for", b"203.0.113.1")],
        "client": ("192.168.1.1", 12345),
    })

    ip = get_client_ip(request)
    assert ip == "203.0.113.1"  # Should use X-Forwarded-For

def test_attack_tool_detection():
    from app.middleware.security_unified import detect_attack_tool

    tool = detect_attack_tool("sqlmap/1.0")
    assert tool == "sqlmap"
```

### Integration Testing

```python
import pytest
from httpx import AsyncClient
from fastapi import FastAPI

from app.middleware.security_unified import UnifiedSecurityMiddleware, SecurityConfig

@pytest.mark.asyncio
async def test_security_headers():
    app = FastAPI()
    config = SecurityConfig(security_headers_enabled=True)
    app.add_middleware(UnifiedSecurityMiddleware, config=config)

    @app.get("/test")
    async def test():
        return {"message": "test"}

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/test")

        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
```

## Files to Delete (After Migration)

Once all imports are updated and tests pass, delete:

```bash
# Middleware files
rm app/middleware/security.py
rm app/middleware/security_middleware.py
rm app/middleware/enterprise_security_middleware.py
rm app/middleware/enterprise_security_middleware_v2.py
rm app/middleware/comprehensive_security_headers.py
rm app/middleware/security_headers.py
rm app/middleware/csrf_xss_protection.py
rm app/middleware/production_security.py

# Core security files with duplicate middleware
# (Carefully review these first - they may have other functions)
# app/core/security_advanced.py
# app/core/security_middleware.py
```

## Benefits of Consolidation

1. **Security**: Single implementation = easier to audit and patch
2. **Consistency**: All endpoints get same security level
3. **Maintainability**: 90% less code to maintain
4. **Testability**: Smaller, focused modules
5. **Flexibility**: Feature toggles for different environments
6. **Performance**: Less middleware overhead

## Rollback Plan

If issues occur:
1. Restore old files from git
2. Comment out unified middleware imports
3. Re-add old middleware registrations

## Common Migration Patterns

### Pattern 1: SecurityMiddleware class usage

**Before:**
```python
from app.middleware.security import SecurityMiddleware, SecurityConfig

@app.on_event("startup")
async def init_security():
    global security_middleware
    security_middleware = SecurityMiddleware(app, config=SecurityConfig())
```

**After:**
```python
from app.middleware.security_unified import UnifiedSecurityMiddleware, SecurityConfig

# Register directly on app
config = SecurityConfig(csrf_protection_enabled=True)
app.add_middleware(UnifiedSecurityMiddleware, config=config)
```

### Pattern 2: IP blocking calls

**Before:**
```python
if await security_middleware._is_ip_blocked(client_ip):
    return JSONResponse(status_code=429, content={"detail": "Blocked"})
```

**After:**
```python
from app.middleware.security_unified import UnifiedSecurityMiddleware

# Get middleware instance (if needed)
# The middleware handles blocking automatically
# No manual checks needed
```

## Support

For questions:
- See inline docstrings in `app/middleware/security_unified/`
- See `docs/SECURITY_MIDDLEWARE_MIGRATION_GUIDE.md`
- Check test files for examples
