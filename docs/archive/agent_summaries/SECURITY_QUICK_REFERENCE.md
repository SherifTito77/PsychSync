# PsychSync Security Quick Reference

**Last Updated:** 2025-12-25
**Status:** ✅ Production Ready

---

## 🚀 Quick Start

### Check Security Status
```bash
# Verify servers running
lsof -i :8000  # Backend
lsof -i :5179  # Frontend

# Run security tests
python3 test_security_middleware.py
python3 test_encryption_service.py

# Check security headers
curl -I http://localhost:8000/health | grep -i "x-\|content-\|strict-"
```

### Start Servers
```bash
# Backend (Terminal 1)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (Terminal 2)
cd frontend && npm run dev
```

---

## 🔐 Security Features

### Active Middleware (in execution order)
1. **ComprehensiveSecurityHeadersMiddleware** - Adds 7 security headers
2. **SecurityValidationMiddleware** - Detects SQLi, XSS, Command Injection
3. **XSSProtectionMiddleware** - Sanitizes HTML output
4. **ContentSecurityPolicyMiddleware** - Restricts resource loading
5. **CSRFProtectionMiddleware** - Validates CSRF tokens
6. **EnterpriseSecurityMiddleware** - Additional security checks

### Encrypted Data Types
- Email addresses (pii_key_v1)
- Social Security Numbers
- Medical records (phi_key_v1)
- Personal addresses (general_key_v1)
- Any sensitive user data

---

## 💡 Common Tasks

### Encrypt PII Data
```python
from app.services.data_encryption_service import encryption_service

# Encrypt
encrypted = encryption_service.encrypt_pii(
    "user@example.com",
    key_id="pii_key_v1"
)
# Store encrypted.encrypted_data in database

# Decrypt
decrypted = encryption_service.decrypt_pii(
    encrypted.encrypted_data,
    key_id=encrypted.key_id
)
```

### Add Security Headers to New Endpoint
```python
from fastapi import APIRouter, Request

@router.get("/secure-endpoint")
async def secure_endpoint(request: Request):
    # Security headers automatically added by middleware
    # CSRF validation automatically performed
    # Input validation automatically done
    return {"message": "This endpoint is protected"}
```

### Exclude Path from CSRF
```python
# Edit app/main.py
csrf_exclude_paths = [
    "/your-new-path",  # Add here
    "/health",
    "/metrics",
    # ... existing paths
]
```

---

## 🧪 Testing

### Run All Security Tests
```bash
# Security middleware tests
python3 test_security_middleware.py

# Encryption service tests
python3 test_encryption_service.py

# Dependency vulnerability scans
cd frontend && npm audit
pip-audit --desc
```

### Test Attack Prevention
```bash
# SQL Injection test
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin'\''OR'\''1'\''='\''1","password":"test"}'

# XSS test
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"<script>alert(1)</script>"}'

# Expected: HTTP 403/404/422 (blocked)
```

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required Security Keys
PSYCHSYNC_ENCRYPTION_KEY=<64-char hex key>
CSRF_SECRET_KEY=<64-char hex key>
SECRET_KEY=<cryptographically random>
ENCRYPTION_MASTER_KEY=<master encryption key>

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname

# Redis (for rate limiting)
REDIS_URL=redis://localhost:6379
```

### Generate New Keys
```bash
# Generate 256-bit hex key (64 hex characters)
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate URL-safe key
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## 📊 Monitoring

### Check Security Logs
```bash
# View recent security events
tail -f logs/security.log

# Search for specific events
grep "AUTH_LOGIN_FAILURE" logs/security.log
grep "SQL_INJECTION" logs/security.log
grep "XSS_ATTEMPT" logs/security.log
```

### Monitor Active Connections
```bash
# Database connections
psql -U psychsync_user -d psychsync_db \
  -c "SELECT * FROM pg_stat_activity;"

# Redis connections
redis-cli CLIENT LIST

# HTTP connections
lsof -i :8000
```

---

## 🚨 Incident Response

### Immediate Actions (If Security Incident Detected)
1. **Isolate Systems**: Block malicious IPs
2. **Preserve Evidence**: Enable additional logging
3. **Rotate Credentials**: Change all secrets
4. **Review Logs**: Check for unauthorized access
5. **Follow Runbook**: See `SECURITY_RUNBOOK.md`

### Emergency Commands
```bash
# Block IP (example - add to firewall/rate limiter)
# Stop all data access
# Enable audit logging
# Check encryption keys
```

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `SECURITY_FINAL_SUMMARY.md` | Complete implementation details |
| `SECURITY_IMPLEMENTATION_COMPLETE.md` | Executive summary |
| `SECURITY_RUNBOOK.md` | Incident response procedures |
| `SECURITY_IMPLEMENTATION_GUIDE.md` | Setup instructions |
| `test_security_middleware.py` | Security test suite |
| `test_encryption_service.py` | Encryption tests |

---

## 🎯 Key Security Principles

1. **Defense in Depth** - Multiple security layers
2. **Zero Trust** - Validate everything
3. **Secure by Default** - Encrypt all PII/PHI
4. **Fail Securely** - Block on uncertainty
5. **Monitor Everything** - Comprehensive logging

---

## 🔍 Troubleshooting

### Security Headers Not Showing
- **Check**: Middleware order in `app/main.py`
- **Solution**: SecurityHeadersMiddleware should be first (outermost)

### CSRF Blocking Legitimate Requests
- **Check**: Is path in `csrf_exclude_paths`?
- **Solution**: Add path to exclusion list in main.py

### Encryption Service Failing
- **Check**: Is `PSYCHSYNC_ENCRYPTION_KEY` set in .env?
- **Solution**: Generate new key and add to .env

### Rate Limiting Too Aggressive
- **Check**: Rate limit tier in `app/core/rate_limit_config.py`
- **Solution**: Adjust limits for your use case

---

## ✅ Pre-Deployment Checklist

- [ ] All security middleware enabled
- [ ] Security keys generated and configured
- [ ] Input validation tested
- [ ] Encryption service verified
- [ ] Dependency scans completed
- [ ] Security headers verified
- [ ] CSRF protection active
- [ ] Rate limiting configured
- [ ] Pre-commit hooks installed
- [ ] Incident response procedures documented

---

## 🎓 Learning Resources

### Security Concepts
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CSP Guide**: https://content-security-policy.com/
- **GDPR**: https://gdpr-info.eu/

### Python Security
- **Cryptography**: https://cryptography.io/
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **Pydantic**: https://docs.pydantic.dev/

### Testing
- **Security Testing**: https://owasp.org/www-project-web-security-testing-guide/

---

**For detailed information, see:** `SECURITY_FINAL_SUMMARY.md`

**For incident response, see:** `SECURITY_RUNBOOK.md`

---

*Quick Reference v1.0 - 2025-12-25*
