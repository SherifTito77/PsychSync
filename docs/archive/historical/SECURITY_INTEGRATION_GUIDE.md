# 🔒 Security Modules Integration Guide

**Last Updated:** December 25, 2025

This guide shows how to integrate the new security modules into your FastAPI application.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Account Lockout Integration](#account-lockout-integration)
3. [Advanced Rate Limiter Integration](#advanced-rate-limiter-integration)
4. [Secure Logging Integration](#secure-logging-integration)
5. [Password Validator Integration](#password-validator-integration)
6. [Complete Example: Auth Endpoint](#complete-example-auth-endpoint)

---

## 🎯 Overview

The new security modules work together to provide defense-in-depth:

```
Request
   ↓
┌─────────────────────────────┐
│  Advanced Rate Limiter       │ ← Check IP, username, device
└─────────────────────────────┘
   ↓
┌─────────────────────────────┐
│  Account Lockout Manager     │ ← Check failed attempts
└─────────────────────────────┘
   ↓
┌─────────────────────────────┐
│  Password Validator          │ ← Validate password strength
└─────────────────────────────┘
   ↓
┌─────────────────────────────┐
│  Secure Logger               │ ← Log all events (sanitized)
└─────────────────────────────┘
```

---

## 🔐 Account Lockout Integration

### Step 1: Initialize in Application Startup

```python
# app/main.py
from app.core.account_lockout import init_lockout_manager
from app.core.advanced_rate_limiter import init_rate_limiter
from app.core.secure_logging import configure_secure_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Configure secure logging
    configure_secure_logging(
        log_level="INFO",
        log_file="logs/app.log"
    )

    # Initialize security modules
    redis_url = "redis://localhost:6379"
    await init_lockout_manager(redis_url)
    await init_rate_limiter(redis_url)

    yield

    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)
```

### Step 2: Use in Login Endpoint

```python
# app/api/v1/endpoints/auth.py
from fastapi import Request, HTTPException, status
from app.core.account_lockout import get_lockout_manager
from app.core.secure_logging import security_logger
from app.core.advanced_rate_limiter import get_rate_limiter

@router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    client_ip = request.client.host if request.client else "unknown"
    username = form_data.username.lower()

    # Get security managers
    lockout_manager = get_lockout_manager()
    rate_limiter = get_rate_limiter()

    # 1. Check rate limits (multi-layered)
    if rate_limiter:
        allowed, reason, limit_info = await rate_limiter.check_rate_limit(
            request=request,
            username=username,
            endpoint="login"
        )

        if not allowed:
            security_logger.log_security_event(
                user_id=username,
                event_type="RATE_LIMIT_EXCEEDED",
                details=reason,
                client_ip=client_ip,
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Too many attempts",
                    "reason": reason,
                    "retry_after": limit_info.get("ip_limit", {}).get("reset", 0)
                }
            )

    # 2. Check account lockout status
    if lockout_manager:
        allowed, lockout_reason, lockout_info = await lockout_manager.check_login_attempt(
            identifier=username,
            ip_address=client_ip
        )

        if not allowed:
            # Account is locked
            security_logger.log_security_event(
                user_id=username,
                event_type="ACCOUNT_LOCKED_LOGIN_ATTEMPT",
                details=lockout_reason,
                client_ip=client_ip,
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail={
                    "error": "Account locked",
                    "message": lockout_reason,
                    "unlock_time": lockout_info.get("unlock_time")
                }
            )

    # 3. Authenticate user
    user = await authenticate_user(db, username, form_data.password)

    if not user:
        # Record failed attempt
        if lockout_manager:
            attempt_info = await lockout_manager.record_failed_attempt(
                identifier=username,
                ip_address=client_ip,
                details="Invalid password"
            )

            security_logger.log_auth_event(
                user_id=username,
                action="login",
                success=False,
                client_ip=client_ip
            )

            # Return attempt count to user
            return {
                "error": "Invalid credentials",
                "attempts_remaining": attempt_info.get("attempts_remaining", 0)
            }

    # 4. Successful login - clear attempt counters
    if lockout_manager:
        await lockout_manager.record_successful_login(
            identifier=username,
            ip_address=client_ip
        )

    security_logger.log_auth_event(
        user_id=str(user.id),
        action="login",
        success=True,
        client_ip=client_ip
    )

    # 5. Create tokens and set httpOnly cookies
    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)

    response = JSONResponse({
        "message": "Login successful",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name
        }
    })

    # Set httpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=1800
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800
    )

    return response
```

---

## ⚡ Advanced Rate Limiter Integration

### Basic Usage

```python
from app.core.advanced_rate_limiter import get_rate_limiter
from fastapi import Request, HTTPException, status

@router.post("/api/sensitive-operation")
async def sensitive_operation(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    rate_limiter = get_rate_limiter()

    if rate_limiter:
        # Check rate limit for this endpoint
        allowed, reason, limit_info = await rate_limiter.check_rate_limit(
            request=request,
            username=current_user.email,
            endpoint="sensitive_operation"
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "reason": reason,
                    "rate_limit_info": limit_info
                }
            )

    # Your endpoint logic here
    return {"status": "success"}
```

### Get Rate Limit Status

```python
@router.get("/api/rate-limit-status")
async def get_rate_limit_status(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    rate_limiter = get_rate_limiter()

    if rate_limiter:
        status = await rate_limiter.get_rate_limit_status(
            request=request,
            username=current_user.email
        )
        return status

    return {"error": "Rate limiter not configured"}
```

---

## 📝 Secure Logging Integration

### Basic Logging

```python
from app.core.secure_logging import security_logger, log_context
import logging

logger = logging.getLogger(__name__)

@router.post("/api/users")
async def create_user(user_data: UserCreate):
    # Log with context
    with log_context(request_id="abc-123", user_id="new-user"):
        logger.info("Creating new user")

        # Security event
        security_logger.log_authz_event(
            user_id="admin",
            resource="user",
            action="create",
            success=True
        )

    return {"status": "created"}
```

### Security Event Categories

```python
# Authentication events
security_logger.log_auth_event(
    user_id="123",
    action="login",
    success=True,
    client_ip="192.168.1.1"
)

# Authorization events
security_logger.log_authz_event(
    user_id="123",
    resource="admin_panel",
    action="access",
    success=False
)

# Data access events
security_logger.log_data_access(
    user_id="123",
    resource_type="sensitive_data",
    resource_id="456",
    action="read"
)

# Generic security events
security_logger.log_security_event(
    user_id="123",
    event_type="SUSPICIOUS_ACTIVITY",
    details="Multiple failed logins from different IPs",
    client_ip="192.168.1.1",
    severity="WARNING"
)
```

---

## 🔑 Password Validator Integration

### In API Endpoint

```python
from app.core.password_validator import password_validator
from fastapi import HTTPException

@router.post("/api/register")
async def register(user_data: UserCreate):
    # Validate password strength
    is_valid, errors = password_validator.validate_password(user_data.password)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Password does not meet requirements",
                "errors": errors
            }
        )

    # Create user with validated password
    user = await create_user(user_data)
    return user
```

### Get Password Strength

```python
@router.post("/api/check-password-strength")
async def check_password_strength(password: str):
    result = password_validator.assess_strength(password)

    return {
        "score": result.score,
        "strength": result.strength,
        "entropy_bits": result.entropy_bits,
        "feedback": result.feedback,
        "is_valid": result.is_valid
    }
```

### In Frontend (React)

```typescript
// frontend/src/components/auth/PasswordStrength.tsx
import { useState } from 'react';

export function PasswordStrengthIndicator({ password }: { password: string }) {
  const [strength, setStrength] = useState<any>(null);

  useEffect(() => {
    if (password) {
      checkStrength(password).then(setStrength);
    }
  }, [password]);

  if (!strength) return null;

  const colors = {
    weak: 'bg-red-500',
    fair: 'bg-orange-500',
    good: 'bg-yellow-500',
    strong: 'bg-green-500',
    excellent: 'bg-green-600'
  };

  return (
    <div className="mt-2">
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${colors[strength.strength]} transition-all`}
          style={{ width: `${strength.score}%` }}
        />
      </div>
      <p className="text-sm mt-1">
        Password strength: <span className="capitalize">{strength.strength}</span>
        ({strength.score}/100)
      </p>
      {strength.feedback.length > 0 && (
        <ul className="text-sm text-gray-600 mt-1">
          {strength.feedback.map((f: string, i: number) => (
            <li key={i}>• {f}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

async function checkStrength(password: string) {
  const response = await fetch('/api/v1/auth/check-password-strength', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password })
  });
  return response.json();
}
```

---

## 🎯 Complete Example: Secure Auth Endpoint

Here's a complete, production-ready authentication endpoint using all security modules:

```python
# app/api/v1/endpoints/auth_secure.py
from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_db
from app.core.account_lockout import get_lockout_manager
from app.core.advanced_rate_limiter import get_rate_limiter
from app.core.secure_logging import security_logger
from app.core.password_validator import password_validator
from app.db.models.user import User

router = APIRouter()

@router.post("/login-secure")
async def login_secure(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Production-ready secure login endpoint.

    Security features:
    - Multi-layered rate limiting
    - Account lockout
    - Secure logging
    - httpOnly cookies
    """
    client_ip = request.client.host if request.client else "unknown"
    username = form_data.username.lower()

    # Get security managers
    lockout_manager = get_lockout_manager()
    rate_limiter = get_rate_limiter()

    # === LAYER 1: Rate Limiting ===
    if rate_limiter:
        allowed, reason, limit_info = await rate_limiter.check_rate_limit(
            request=request,
            username=username,
            endpoint="login"
        )

        if not allowed:
            security_logger.log_security_event(
                user_id=username,
                event_type="RATE_LIMIT_EXCEEDED",
                details=reason,
                client_ip=client_ip,
                severity="WARNING"
            )

            response_headers = {
                "Retry-After": str(limit_info.get("ip_limit", {}).get("reset", 0) - int(time.time())),
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "0",
            }

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Too many attempts",
                    "reason": reason,
                    "retry_after": limit_info.get("ip_limit", {}).get("reset", 0)
                },
                headers=response_headers
            )

    # === LAYER 2: Account Lockout ===
    if lockout_manager:
        allowed, lockout_reason, lockout_info = await lockout_manager.check_login_attempt(
            identifier=username,
            ip_address=client_ip
        )

        if not allowed:
            security_logger.log_security_event(
                user_id=username,
                event_type="LOCKED_ACCOUNT_ATTEMPT",
                details=lockout_reason,
                client_ip=client_ip,
                severity="WARNING"
            )

            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail={
                    "error": "Account locked",
                    "message": lockout_reason,
                    "unlock_time": lockout_info.get("unlock_time")
                }
            )

    # === LAYER 3: Authentication ===
    result = await db.execute(
        select(User).where(User.email == username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        # Record failed attempt
        if lockout_manager:
            attempt_info = await lockout_manager.record_failed_attempt(
                identifier=username,
                ip_address=client_ip,
                details="Invalid credentials"
            )

        security_logger.log_auth_event(
            user_id=username,
            action="login",
            success=False,
            client_ip=client_ip
        )

        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "Invalid credentials",
                "attempts_remaining": attempt_info.get("attempts_remaining", 0) if lockout_manager else 5
            }
        )

    # === LAYER 4: Successful Login ===
    # Clear failed attempt counters
    if lockout_manager:
        await lockout_manager.record_successful_login(
            identifier=username,
            ip_address=client_ip
        )

    # Log successful authentication
    security_logger.log_auth_event(
        user_id=str(user.id),
        action="login",
        success=True,
        client_ip=client_ip
    )

    # Create tokens
    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Build response with httpOnly cookies
    response = JSONResponse({
        "message": "Login successful",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name
        }
    })

    # Set httpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=1800
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800
    )

    return response
```

---

## 🧪 Testing Security Modules

### Test Account Lockout

```python
# tests/test_account_lockout.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_account_lockout(client: AsyncClient):
    """Test that account locks after 5 failed attempts."""

    # Attempt 5 failed logins
    for i in range(5):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrong_password"
            }
        )
        assert response.status_code == 401

    # 6th attempt should be locked
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "wrong_password"
        }
    )
    assert response.status_code == 423  # LOCKED
    assert "locked" in response.json()["detail"].lower()
```

### Test Rate Limiting

```python
@pytest.mark.asyncio
async def test_rate_limiting(client: AsyncClient):
    """Test that rate limiting works."""

    responses = []
    for i in range(101):  # Exceed 100 request limit
        response = await client.get("/api/v1/teams")
        responses.append(response)

    # First 100 should succeed
    assert sum(1 for r in responses[:100] if r.status_code == 200) == 100

    # 101st should be rate limited
    assert responses[100].status_code == 429
```

### Test Password Validation

```python
from app.core.password_validator import password_validator

def test_weak_password():
    """Test that weak passwords are rejected."""
    is_valid, errors = password_validator.validate_password("Password1")

    assert not is_valid
    assert any("12 characters" in e for e in errors)

def test_strong_password():
    """Test that strong passwords are accepted."""
    is_valid, errors = password_validator.validate_password("Tr0ub4dor&3Horse!")

    assert is_valid
    assert len(errors) == 0
```

---

## 📊 Monitoring and Metrics

### Get Security Metrics

```python
@router.get("/api/admin/security-metrics")
async def get_security_metrics(
    current_user: User = Depends(get_current_admin_user)
):
    """Get security metrics for admin dashboard."""

    lockout_manager = get_lockout_manager()
    rate_limiter = get_rate_limiter()

    metrics = {
        "lockout_status": {},
        "rate_limit_status": {},
        "timestamp": datetime.utcnow().isoformat()
    }

    if lockout_manager:
        # Get locked accounts count (would need to be implemented)
        metrics["lockout_status"] = {
            "locked_accounts": 0,
            "total_failed_attempts": 0
        }

    if rate_limiter:
        # Get rate limit stats
        metrics["rate_limit_status"] = {
            "active_rate_limits": 0
        }

    return metrics
```

---

## ✅ Deployment Checklist

Before deploying to production:

- [ ] Redis is configured and running
- [ ] Security modules are initialized in startup
- [ ] Secure logging is configured
- [ ] httpOnly cookies are enabled in production
- [ ] Rate limiting is tested
- [ ] Account lockout is tested
- [ ] Password validation is tested
- [ ] All print statements are replaced with logger
- [ ] CSP headers are configured
- [ ] Monitoring is set up

---

## 🔗 Related Documentation

- [COMPREHENSIVE_SECURITY_AUDIT_REPORT.md](../COMPREHENSIVE_SECURITY_AUDIT_REPORT.md)
- [SECURITY_FIXES_IMPLEMENTATION_SUMMARY.md](../SECURITY_FIXES_IMPLEMENTATION_SUMMARY.md)
- [SECURITY_ARCHITECTURE.md](./SECURITY_ARCHITECTURE.md)
- [SECURITY_QUICK_START.md](./SECURITY_QUICK_START.md)
