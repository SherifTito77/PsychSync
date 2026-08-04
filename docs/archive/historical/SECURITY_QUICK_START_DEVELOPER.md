# 🔒 Security Quick-Start Guide for Developers

**Last Updated:** December 25, 2025
**Target Audience:** Developers integrating security features
**Reading Time:** 15 minutes

---

## 🎯 Overview

This guide shows you how to quickly integrate all the new security features into your code. Each section includes copy-paste examples.

---

## 📋 Table of Contents

1. [Installation](#installation)
2. [Password Validation](#password-validation)
3. [Rate Limiting](#rate-limiting)
4. [Account Lockout](#account-lockout)
5. [Secure Logging](#secure-logging)
6. [Complete Examples](#complete-examples)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Installation

### Step 1: Verify Dependencies

```bash
# Install security dependencies
pip install redis[hiredis] cryptography

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### Step 2: Initialize Security Modules

```python
# app/main.py
from contextlib import asynccontextmanager
from app.core.account_lockout import init_lockout_manager
from app.core.advanced_rate_limiter import init_rate_limiter
from app.core.secure_logging import configure_secure_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    configure_secure_logging(
        log_level="INFO",
        log_file="logs/app.log"
    )

    redis_url = "redis://localhost:6379"
    await init_lockout_manager(redis_url)
    await init_rate_limiter(redis_url)

    yield

    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)
```

---

## 🔐 Password Validation

### Quick Usage

```python
from app.core.password_validator import password_validator

# Validate password
is_valid, errors = password_validator.validate_password("MyPassword123!")

if not is_valid:
    print(errors)
    # ['Must be at least 12 characters', 'Add special characters']
```

### In API Endpoint

```python
from fastapi import HTTPException
from app.core.password_validator import password_validator

@router.post("/register")
async def register(user_data: UserCreate):
    # Validate password
    is_valid, errors = password_validator.validate_password(user_data.password)

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Password too weak",
                "errors": errors
            }
        )

    # Create user
    user = await create_user(user_data)
    return user
```

### Get Password Strength

```python
result = password_validator.assess_strength("MyPassword123!")

print(f"Score: {result.score}/100")      # 0-100
print(f"Strength: {result.strength}")      # weak, fair, good, strong, excellent
print(f"Entropy: {result.entropy_bits} bits")
print(f"Feedback: {result.feedback}")     # List of improvement suggestions
```

### In Frontend (React)

```typescript
// Check password strength as user types
const checkStrength = async (password: string) => {
  const response = await fetch('/api/v1/auth/check-password-strength', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password })
  });
  return response.json();
};

// Display strength meter
<PasswordStrengthIndicator password={password} />
```

---

## ⚡ Rate Limiting

### Quick Usage

```python
from app.core.advanced_rate_limiter import get_rate_limiter
from fastapi import Request, HTTPException

@router.get("/api/sensitive-operation")
async def sensitive_operation(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    rate_limiter = get_rate_limiter()

    if rate_limiter:
        allowed, reason, limit_info = await rate_limiter.check_rate_limit(
            request=request,
            username=current_user.email,
            endpoint="sensitive_operation"
        )

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "reason": reason,
                    "retry_after": limit_info.get("ip_limit", {}).get("reset", 0)
                }
            )

    # Your code here
    return {"status": "success"}
```

### Custom Rate Limits

```python
# Different limits for different endpoints
endpoint_limits = {
    "login": {"max_requests": 10, "window": 60},       # 10/min
    "upload": {"max_requests": 20, "window": 60},       # 20/min
    "api_call": {"max_requests": 100, "window": 60},   # 100/min
}

@router.post("/api/upload")
async def upload_file(request: Request):
    rate_limiter = get_rate_limiter()

    allowed, reason, _ = await rate_limiter.check_rate_limit(
        request=request,
        endpoint="upload"
    )

    if not allowed:
        raise HTTPException(status_code=429, detail=reason)

    # Upload file
    return {"status": "uploaded"}
```

---

## 🔒 Account Lockout

### Quick Usage

```python
from app.core.account_lockout import get_lockout_manager
from fastapi import Request, HTTPException

@router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    client_ip = request.client.host
    username = form_data.username.lower()

    lockout_manager = get_lockout_manager()

    # Check if account is locked
    if lockout_manager:
        allowed, reason, lockout_info = await lockout_manager.check_login_attempt(
            identifier=username,
            ip_address=client_ip
        )

        if not allowed:
            raise HTTPException(
                status_code=423,  # Locked
                detail={
                    "error": "Account locked",
                    "message": reason,
                    "unlock_time": lockout_info.get("unlock_time")
                }
            )

    # Authenticate user
    user = await authenticate_user(db, username, form_data.password)

    if not user:
        # Record failed attempt
        if lockout_manager:
            attempt_info = await lockout_manager.record_failed_attempt(
                identifier=username,
                ip_address=client_ip
            )

        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Successful login - clear attempts
    if lockout_manager:
        await lockout_manager.record_successful_login(
            identifier=username,
            ip_address=client_ip
        )

    return {"message": "Login successful"}
```

### Get Account Status

```python
lockout_manager = get_lockout_manager()
status = await lockout_manager.get_account_status("user@example.com")

print(status)
# {
#     "identifier": "user@example.com",
#     "failed_attempts": 3,
#     "is_locked": false,
#     "lockout_info": null
# }
```

### Unlock Account (Admin)

```python
lockout_manager = get_lockout_manager()
await lockout_manager.unlock_account(
    identifier="user@example.com",
    admin_user="admin@example.com"
)
```

---

## 📝 Secure Logging

### Quick Setup

```python
from app.core.secure_logging import security_logger, log_context
import logging

logger = logging.getLogger(__name__)

# Log security events
security_logger.log_auth_event(
    user_id="123",
    action="login",
    success=True,
    client_ip="192.168.1.1"
)

# Log authorization events
security_logger.log_authz_event(
    user_id="123",
    resource="admin_panel",
    action="access",
    success=False
)

# Log data access
security_logger.log_data_access(
    user_id="123",
    resource_type="sensitive_data",
    resource_id="456",
    action="read"
)

# Log with context
with log_context(request_id="abc-123", user_id="123"):
    logger.info("Processing request")
    # All logs in this context include request_id and user_id
```

### Auto-Redaction

```python
# Sensitive data is automatically redacted
logger.info(f"User login: password=secret123")
# Logged as: "User login: password=***REDACTED***"

logger.info(f"Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
# Logged as: "Token: ***JWT***"

logger.info(f"Card: 4111-1111-1111-1111")
# Logged as: "Card: ***CARD***"
```

---

## 💡 Complete Examples

### Example 1: Protected Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.advanced_rate_limiter import get_rate_limiter
from app.core.account_lockout import get_lockout_manager
from app.core.secure_logging import security_logger

router = APIRouter()

@router.post("/api/sensitive-action")
async def sensitive_action(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    client_ip = request.client.host

    # 1. Check rate limits
    rate_limiter = get_rate_limiter()
    if rate_limiter:
        allowed, reason, _ = await rate_limiter.check_rate_limit(
            request=request,
            username=current_user.email,
            endpoint="sensitive_action"
        )
        if not allowed:
            security_logger.log_security_event(
                user_id=str(current_user.id),
                event_type="RATE_LIMIT_EXCEEDED",
                details=reason,
                client_ip=client_ip,
                severity="WARNING"
            )
            raise HTTPException(status_code=429, detail=reason)

    # 2. Your business logic here
    result = await perform_sensitive_action(current_user)

    # 3. Log successful action
    security_logger.log_data_access(
        user_id=str(current_user.id),
        resource_type="sensitive_data",
        resource_id=result.id,
        action="create",
        client_ip=client_ip
    )

    return result
```

### Example 2: User Registration

```python
from app.core.password_validator import password_validator
from app.core.secure_logging import security_logger

@router.post("/register")
async def register(user_data: UserCreate, request: Request):
    client_ip = request.client.host

    # 1. Validate password strength
    is_valid, errors = password_validator.validate_password(user_data.password)

    if not is_valid:
        security_logger.log_security_event(
            user_id=user_data.email,
            event_type="WEAK_PASSWORD_ATTEMPT",
            details=f"Weak password: {', '.join(errors)}",
            client_ip=client_ip,
            severity="WARNING"
        )

        raise HTTPException(
            status_code=400,
            detail={"error": "Password too weak", "errors": errors}
        )

    # 2. Check password strength for feedback
    strength_result = password_validator.assess_strength(user_data.password)

    if strength_result.score < 60:
        # Provide feedback
        return {
            "error": "Password should be stronger",
            "feedback": strength_result.feedback,
            "strength": strength_result.strength
        }

    # 3. Create user
    user = await create_user(user_data)

    # 4. Log security event
    security_logger.log_security_event(
        user_id=str(user.id),
        event_type="USER_REGISTRATION",
        details="New user account created",
        client_ip=client_ip,
        severity="INFO"
    )

    return {
        "message": "Registration successful",
        "user_id": str(user.id)
    }
```

---

## 🧪 Testing

### Run Security Tests

```bash
# Run all security tests
pytest tests/test_security_comprehensive.py -v

# Run specific test class
pytest tests/test_security_comprehensive.py::TestPasswordValidation -v

# Run with coverage
pytest tests/test_security_comprehensive.py \
    --cov=app/core \
    --cov-report=html \
    --cov-report=term
```

### Manual Testing

#### Test httpOnly Cookies

```javascript
// Open browser DevTools Console
localStorage.getItem('access_token')
// Expected: null (should not exist)

document.cookie
// Expected: Contains access_token and refresh_token
```

#### Test Rate Limiting

```bash
# Make 101 requests (exceeds 100 limit)
for i in {1..101}; do
  curl -X GET http://localhost:8000/api/v1/teams
done

# Expected: Last request returns HTTP 429
```

#### Test Account Lockout

```python
# Attempt 5 failed logins
for i in range(5):
    response = await client.post("/login", json={
        "username": "test@example.com",
        "password": "wrong"
    })
    print(response.status_code)

# Expected: After 5th attempt, returns 423 (Locked)
```

#### Test Password Validation

```python
from app.core.password_validator import password_validator

# Test weak password
is_valid, errors = password_validator.validate_password("Password1")
assert not is_valid
assert any("12 characters" in e for e in errors)

# Test strong password
is_valid, errors = password_validator.validate_password("Tr0ub4dor&3Horse!")
assert is_valid
```

---

## 🔧 Troubleshooting

### Issue: "Redis connection refused"

**Solution:**
```bash
# Start Redis
sudo systemctl start redis

# Or using Homebrew
brew services start redis

# Verify connection
redis-cli ping
```

### Issue: "Security module not found"

**Solution:**
```python
# Verify modules are initialized
python -c "
from app.core.password_validator import password_validator
from app.core.advanced_rate_limiter import get_rate_limiter
from app.core.account_lockout import get_lockout_manager
print('✓ All modules imported successfully')
"
```

### Issue: "Account lockout not working"

**Solution:**
```python
# Check if lockout manager is initialized
from app.core.account_lockout import get_lockout_manager
lockout_manager = get_lockout_manager()

if lockout_manager is None:
    print("Lockout manager not initialized!")
    print("Check app/main.py lifespan function")
```

### Issue: "Logs still showing sensitive data"

**Solution:**
```python
# Verify secure logging is configured
from app.core.secure_logging import configure_secure_logging

import logging
configure_secure_logging(log_level="INFO")

# Test redaction
logger = logging.getLogger(__name__)
logger.info("Test: password=secret123")
# Should log: password=***REDACTED***
```

---

## 📊 Monitoring

### View Security Metrics

```python
# Check rate limit status
rate_limiter = get_rate_limiter()
status = await rate_limiter.get_rate_limit_status(
    request=request,
    username="user@example.com"
)

# Check account lockout status
lockout_manager = get_lockout_manager()
status = await lockout_manager.get_account_status("user@example.com")

# View security logs
tail -f /var/log/psychsync/app.log
```

### Security Dashboard

Navigate to: `http://localhost:3000/admin/security`

Shows:
- Authentication metrics
- Authorization metrics
- Rate limiting status
- Failed login attempts
- Suspicious activity alerts
- Security event timeline

---

## 🎓 Best Practices

### DO's ✅

- ✅ Always use `get_rate_limiter()` to check rate limits
- ✅ Always use `password_validator.validate_password()` for passwords
- ✅ Always use `security_logger` for security events
- ✅ Always include `client_ip` in security logs
- ✅ Always log security events for sensitive operations

### DON'Ts ❌

- ❌ Don't use print() for sensitive data
- ❌ Don't store passwords in variables longer than needed
- ❌ Don't log tokens, passwords, or secrets
- ❌ Don't bypass rate limiting
- ❌ Don't ignore lockout status

---

## 📚 Additional Resources

- [Full Security Integration Guide](./SECURITY_INTEGRATION_GUIDE.md)
- [Comprehensive Security Audit Report](../COMPREHENSIVE_SECURITY_AUDIT_REPORT.md)
- [Security Architecture Documentation](./SECURITY_ARCHITECTURE.md)

---

## 🚀 Quick Start Commands

```bash
# Install dependencies
pip install redis[hiredis] cryptography

# Start Redis
redis-server

# Run tests
pytest tests/test_security_comprehensive.py -v

# Deploy security modules
./scripts/deploy_security_modules.sh

# View logs
tail -f logs/app.log

# Check security status
redis-cli
> GET account_locked:user@example.com
> GET rate_limit:ip:192.168.1.1
```

---

## 💡 Tips

1. **Start Simple**: Begin with password validation, then add other features
2. **Test Locally**: Run security tests before deploying
3. **Monitor Logs**: Check logs for any security issues
4. **Ask Questions**: Don't hesitate to ask the security team

---

**Need Help?** Contact security@psychsync.com or check the [Integration Guide](./SECURITY_INTEGRATION_GUIDE.md)
