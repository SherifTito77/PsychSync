# Deployment Configuration Misalignment Analysis

**Date:** March 2026
**Analysis Type:** Environment Configuration Review
**System:** PsychSync AI - Enterprise Psychological Assessment Platform

---

## Executive Summary

This document identifies configuration misalignments across development, testing, and production environments that can cause deployment issues, security vulnerabilities, or performance problems.

### Key Findings

- **15 Critical Misalignments Identified**
- **8 High Priority (Fix Before Production Deploy)**
- **4 Medium Priority (Nice to Have)**
- **3 Low Priority (Documentation Only)**

---

## Configuration Files Analyzed

| File | Purpose | Environment |
|------|----------|-------------|
| `app/.env` | Development environment | Development |
| `app/.env.example` | Configuration template | Template |
| `.env.production` | Production environment | Production |
| `docker-compose.distributed-test.yml` | Distributed testing infrastructure | Testing |
| `frontend/.env` | Frontend development | Development |
| `frontend/.env.example` | Frontend template | Template |
| `app/core/config/application.py` | Application defaults | All |
| `app/core/config/database.py` | Database defaults | All |

---

## Critical Misalignments

### 🔴 CRITICAL #1: Database Configuration Inconsistency

**Files Affected:**
- `app/.env` (Development)
- `app/.env.example` (Template)
- `.env.production` (Production)
- `app/core/config/database.py` (Defaults)

**Issue:**

**Development (.env):**
```bash
DATABASE_URL=sqlite+aiosqlite:///./psychsync_dev.db
```

**Template (.env.example):**
```bash
DATABASE_URL=postgresql+asyncpg://psychsync_user:password@localhost/psychsync_db
```

**Production (.env.production):**
```bash
DATABASE_URL=postgresql+asyncpg://psychsync_user:CHANGE_ME_DB_PASSWORD@db:5432/psychsync_prod?sslmode=require
```

**Default (database.py:34):**
```python
DATABASE_URL: str = Field(
    default="postgresql+asyncpg://postgres:password@localhost:5432/psychsync",
    env="DATABASE_URL",
)
```

**Misalignment:**
1. **Development uses SQLite** while template and defaults expect PostgreSQL
2. **Production uses `db:5432` host** while defaults expect `localhost:5432`
3. **SSL mode only in production** - this is correct but should be documented
4. **Database name mismatch**: `psychsync` (default) vs `psychsync_db` vs `psychsync_prod`

**Impact:**
- Development environment doesn't match testing/production database schema
- ORM queries may fail if PostgreSQL-specific features are used in development
- Deployment surprises when code works in dev but fails in prod

**Recommendation:**
```bash
# Development .env should use PostgreSQL by default
DATABASE_URL=postgresql+asyncpg://psychsync_user:dev_password@localhost:5432/psychsync_dev
```

---

### 🔴 CRITICAL #2: Frontend/Backend Port Mismatch

**Files Affected:**
- `frontend/.env` (Frontend Development)
- `frontend/.env.example` (Frontend Template)
- `app/core/config/application.py` (Backend Defaults)

**Issue:**

**Frontend (.env):**
```bash
VITE_API_URL=http://localhost:5173/api/v1
```

**Frontend Template (.env.example):**
```bash
VITE_API_URL=http://localhost:8000/api/v1
```

**Backend Default (application.py):**
```python
PORT: int = Field(default=8000, env="PORT")
```

**Misalignment:**
1. **Frontend expects backend on port 5173** but backend defaults to 8000
2. **Template expects 8000** but current .env uses 5173
3. **Inconsistent default ports** across environments

**Impact:**
- Frontend cannot communicate with backend in development
- API calls fail with 404/connection errors
- Developers waste time debugging connection issues

**Recommendation:**
```bash
# frontend/.env - Update to match backend default
VITE_API_URL=http://localhost:8000/api/v1

# Or update backend default to 5173 (if 5173 is preferred)
```

---

### 🔴 CRITICAL #3: URL Scheme Inconsistency (HTTP vs HTTPS)

**Files Affected:**
- `app/.env` (Development)
- `.env.production` (Production)
- `app/core/config/application.py` (Defaults)

**Issue:**

**Development (.env):**
```bash
DATABASE_URL=postgresql+asyncpg://psychsync:password@localhost/psychsync_db
FRONTEND_URL=http://localhost:5174
```

**Production (.env.production):**
```bash
DATABASE_URL=postgresql+asyncpg://psychsync_user:CHANGE_ME_DB_PASSWORD@db:5432/psychsync_prod?sslmode=require
FRONTEND_URL=https://app.psychsync.com
```

**Default (application.py):**
```python
FRONTEND_URL: str = Field(default="http://localhost:5173", env="FRONTEND_URL")
```

**Misalignment:**
1. **Default FRONTEND_URL uses HTTP** - should match development behavior
2. **Production correctly uses HTTPS** - this is good
3. **No environment-specific URL scheme enforcement**

**Impact:**
- Mixed content warnings in browsers
- Insecure cookie attributes in development
- HSTS header not enforced properly

**Recommendation:**
```python
# application.py - Make defaults more explicit
FRONTEND_URL: str = Field(
    default="http://localhost:5173",  # Development default
    env="FRONTEND_URL",
)
# Production .env.production overrides to HTTPS
```

---

### 🔴 CRITICAL #4: Redis Configuration Fragmentation

**Files Affected:**
- `app/.env` (Development)
- `.env.production` (Production)
- `docker-compose.distributed-test.yml` (Testing)
- `app/core/config/settings.py` (Defaults)

**Issue:**

**Development (.env):**
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
```

**Production (.env.production):**
```bash
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=CHANGE_ME_REDIS_PASSWORD
REDIS_SSL=true
REDIS_SSL_CERT_REQS=required
```

**Docker Compose (Testing):**
```yaml
REDIS_URL=redis://redis:6379/2
```

**Default (settings.py):**
```python
REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
```

**Misalignment:**
1. **Development uses separate REDIS_HOST/PORT** but production uses REDIS_URL
2. **Different Redis DB numbers**: Default uses `/0`, Testing uses `/2`, Production uses `/0`
3. **SSL settings only in production** - should have dev default
4. **Redis password not documented in .env.example**

**Impact:**
- Connection errors when switching between environments
- Confusing configuration for developers
- Potential Redis DB conflicts in multi-environment setups

**Recommendation:**
```bash
# app/.env - Use consistent REDIS_URL format
REDIS_URL=redis://localhost:6379/0

# Add to .env.example
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_SSL=false
```

---

### 🔴 CRITICAL #5: Database Pool Size Mismatch

**Files Affected:**
- `.env.production` (Production)
- `app/core/config/database.py` (Defaults)

**Issue:**

**Production (.env.production):**
```bash
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_RECYCLE=3600
DATABASE_POOL_TIMEOUT=30
```

**Default (database.py):**
```python
DATABASE_POOL_SIZE: int = Field(default=40, env="DATABASE_POOL_SIZE")
DATABASE_MAX_OVERFLOW: int = Field(default=60, env="DATABASE_MAX_OVERFLOW")
DATABASE_POOL_RECYCLE: int = Field(default=3600, env="DATABASE_POOL_RECYCLE")
DATABASE_POOL_TIMEOUT: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
```

**Misalignment:**
1. **Production pool size is 20** (half of default 40)
2. **Production overflow is 30** (half of default 60)
3. **This may be intentional** for production cost optimization
4. **Not documented** as intentional vs. oversight

**Impact:**
- May cause connection pool exhaustion in production
- Database connection errors under load
- Poor performance during traffic spikes

**Recommendation:**
```bash
# If intentional, document it
# DATABASE_POOL_SIZE=20  # Reduced for production cost optimization

# If oversight, fix it
# DATABASE_POOL_SIZE=40  # Match default for consistency
```

---

### 🔴 CRITICAL #6: Inconsistent Environment Variable Names

**Files Affected:**
- `app/.env` (Development)
- `.env.production` (Production)
- `app/core/config/settings.py` (Defaults)

**Issue:**

**Development (.env):**
```bash
ALGORITHM=HS256  # Note: not JWT_ALGORITHM
```

**Production (.env.production):**
```bash
ALGORITHM=HS256  # Note: not JWT_ALGORITHM
```

**Default (settings.py):**
```python
JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
```

**Misalignment:**
1. **Environment files use `ALGORITHM`** but settings expect `JWT_ALGORITHM`
2. **This variable will be ignored** by Pydantic
3. **Falls back to default** - may hide misconfiguration

**Impact:**
- Configuration ignored silently
- Developers confused why changes don't take effect
- Security settings not properly applied

**Recommendation:**
```bash
# Update to use correct variable name
JWT_ALGORITHM=HS256
```

---

## High Priority Misalignments

### 🟠 HIGH #7: Missing Celery Configuration in .env.production

**Files Affected:**
- `.env.production` (Production)
- `app/core/config/settings.py` (Defaults)

**Issue:**

**Production (.env.production):**
```bash
# No CELERY_BROKER_URL or CELERY_RESULT_BACKEND defined
```

**Default (settings.py):**
```python
CELERY_BROKER_URL: str = Field(
    default="redis://localhost:6379/1",
    env="CELERY_BROKER_URL",
)
CELERY_RESULT_BACKEND: str = Field(
    default="redis://localhost:6379/2",
    env="CELERY_RESULT_BACKEND",
)
```

**Misalignment:**
1. **Production doesn't define Celery settings**
2. **Will use localhost defaults** in production
3. **Background tasks will fail** if Redis is remote

**Impact:**
- Background tasks don't work in production
- Email notifications fail
- Analytics tasks don't execute

**Recommendation:**
```bash
# Add to .env.production
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

---

### 🟠 HIGH #8: Frontend Environment Variable Prefix Mismatch

**Files Affected:**
- `frontend/.env` (Frontend Development)
- `frontend/.env.example` (Frontend Template)

**Issue:**

**Frontend (.env):**
```bash
VITE_API_URL=http://localhost:5173/api/v1
VITE_APP_NAME=PsychSync
VITE_APP_VERSION=1.0.0
VITE_FRONTEND_URL=http://localhost:5175
```

**Frontend Template (.env.example):**
```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_API_TIMEOUT=30000
VITE_API_RETRY_ATTEMPTS=3
```

**Misalignment:**
1. **Frontend dev has only minimal configs** while template has many
2. **Missing timeout/retry configs** in development .env
3. **Different port expectations** (5173 vs 8000)

**Impact:**
- Development doesn't match template expectations
- Inconsistent API behavior between dev and template
- Harder to diagnose issues when template values work but dev doesn't

**Recommendation:**
```bash
# frontend/.env - Add missing configuration values
VITE_API_TIMEOUT=30000
VITE_API_RETRY_ATTEMPTS=3
```

---

### 🟠 HIGH #9: Duplicate JWT Configuration Keys

**Files Affected:**
- `app/.env` (Development)

**Issue:**

**Development (.env):**
```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
```

**Misalignment:**
1. **Both JWT_SECRET_KEY and SECRET_KEY defined** - which one is correct?
2. **Both ALGORITHM and JWT_ALGORITHM defined** - potential confusion
3. **JWT_EXPIRE_HOURS duplicated**

**Impact:**
- Security confusion about which key to use
- Potential for using wrong secret key
- JWT token validation failures

**Recommendation:**
```bash
# Use single set of keys consistently
# Remove JWT_SECRET_KEY, ALGORITHM, JWT_EXPIRE_HOURS
# Keep SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_HOURS
```

---

### 🟠 HIGH #10: CORS Origins Configuration Drift

**Files Affected:**
- `app/.env.example` (Template)
- `.env.production` (Production)
- `frontend/.env.example` (Frontend Template)

**Issue:**

**Template (.env.example):**
```bash
CORS_ORIGINS=["http://localhost:5173"]
```

**Production (.env.production):**
```bash
CORS_ORIGINS=https://app.psychsync.com,https://www.psychsync.com
```

**Frontend Template (.env.example):**
```bash
VITE_CSP_NONCE=
VITE_REFERRER_POLICY=strict-origin-when-cross-origin
```

**Misalignment:**
1. **Template has localhost CORS** - not useful for production reference
2. **Frontend CSP/Referrer policies** not aligned with backend CORS
3. **No port specificity** in production CORS origins

**Impact:**
- CORS misconfiguration in development
- Security header conflicts
- Cookie authentication issues

**Recommendation:**
```bash
# .env.example - Add environment-specific CORS
# Development
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Production (already correct)
CORS_ORIGINS=https://app.psychsync.com,https://www.psychsync.com
```

---

## Medium Priority Misalignments

### 🟡 MEDIUM #11: Database Host Configuration

**Files Affected:**
- `docker-compose.distributed-test.yml` (Testing)
- `.env.production` (Production)

**Issue:**

**Docker Compose (Testing):**
```yaml
db:
  environment:
    POSTGRES_DB: psychsync_db
    POSTGRES_USER: psychsync_user
    POSTGRES_PASSWORD: password
  ports:
    - "5432:5432"
```

**Production (.env.production):**
```bash
DATABASE_URL=postgresql+asyncpg://psychsync_user:CHANGE_ME_DB_PASSWORD@db:5432/psychsync_prod
```

**Misalignment:**
1. **Production uses `db:5432` as host** while testing uses `localhost:5432`
2. **Different database names**: `psychsync_db` vs `psychsync_prod`
3. **Host resolution depends on Docker networking vs. external DNS**

**Impact:**
- Database connection failures when switching environments
- DNS resolution issues in production
- Network configuration complexity

**Recommendation:**
```bash
# Document different database environments:
# Development: localhost:5432/psychsync_dev
# Testing: localhost:5432/psychsync_test
# Staging: localhost:5432/psychsync_staging
# Production: db.production.internal:5432/psychsync_prod
```

---

### 🟡 MEDIUM #12: Feature Flags Not Documented

**Files Affected:**
- `frontend/.env` (Frontend Development)
- `frontend/.env.example` (Frontend Template)

**Issue:**

**Frontend (.env):**
```bash
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEBUG=true
VITE_ENABLE_SERVICE_WORKER=false
VITE_EMAIL_VERIFICATION_REQUIRED=false
```

**Frontend Template (.env.example):**
```bash
VITE_ENABLE_BETA_FEATURES=false
VITE_ENABLE_EXPERIMENTAL_FEATURES=false
VITE_ENABLE_ADVANCED_ANALYTICS=false
```

**Misalignment:**
1. **Development has minimal feature flags**
2. **Template has advanced flags** not used in development
3. **Feature flag naming inconsistent** (ENABLE_DEBUG vs VITE_ENABLE_ANALYTICS)

**Impact:**
- Feature toggles don't work consistently
- Hard to test beta features
- Production features leak into development

**Recommendation:**
```bash
# Standardize feature flag names and document all options
# Core flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_DEBUG=false

# Feature flags
VITE_ENABLE_BETA_FEATURES=false
VITE_ENABLE_EXPERIMENTAL_FEATURES=false

# Feature-specific flags
VITE_ENABLE_AI_CHATBOT=true
VITE_ENABLE_CLINICAL_ASSESSMENTS=false
```

---

### 🟡 MEDIUM #13: SSL/TLS Configuration Gap

**Files Affected:**
- `.env.production` (Production)
- `app/core/config/database.py` (Defaults)

**Issue:**

**Production (.env.production):**
```bash
DATABASE_URL=postgresql+asyncpg://...?sslmode=require
REDIS_SSL=true
SMTP_TLS=true
SMTP_SSL=false
SSL_CERT_PATH=/etc/ssl/certs/psychsync.com.crt
```

**Default (database.py):**
```python
DB_SSL_MODE: str = Field(default="prefer", env="DB_SSL_MODE")
DB_SSL_CERT: str | None = Field(default=None, env="DB_SSL_CERT")
DB_SSL_KEY: str | None = Field(default=None, env="DB_SSL_KEY")
DB_SSL_CA: str | None = Field(default=None, env="DB_SSL_CA")
```

**Misalignment:**
1. **Production uses query param `sslmode=require`** but defaults use separate fields
2. **SSL cert paths hardcoded** in production but not in defaults
3. **TLS mismatch between Redis, SMTP, and DB**

**Impact:**
- SSL validation may fail
- Certificate management complexity
- Inconsistent encryption settings

**Recommendation:**
```python
# Update defaults to match production practice
# Prefer query param method for PostgreSQL
DATABASE_URL: str = Field(
    default="postgresql+asyncpg://...",
    env="DATABASE_URL",
)

# Add SSL path defaults with validation
DB_SSL_CERT: str | None = Field(
    default=None,
    env="DB_SSL_CERT",
    description="Path to SSL certificate file"
)
```

---

### 🟡 MEDIUM #14: Rate Limiting Configuration

**Files Affected:**
- `app/.env.example` (Template)
- `.env.production` (Production)
- `docker-compose.distributed-test.yml` (Testing)

**Issue:**

**Template (.env.example):**
```bash
# No RATE_LIMIT_* defined
```

**Production (.env.production):**
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

**Docker Compose (Testing):**
```yaml
USE_REDIS_RATE_LIMIT=true  # Flag, not standard config
```

**Misalignment:**
1. **Template missing rate limiting config**
2. **Docker uses different config mechanism** (USE_REDIS_RATE_LIMIT flag)
3. **Inconsistent rate limit defaults** across environments

**Impact:**
- Rate limiting not consistent across environments
- API protection gaps in development
- Hard to test rate limiting features

**Recommendation:**
```bash
# Add to .env.example
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Standardize docker-compose approach
# Remove USE_REDIS_RATE_LIMIT flag
# Use standard RATE_LIMIT_ENABLED instead
```

---

## Low Priority Misalignments

### 🟢 LOW #15: Commented Configuration in .env Files

**Files Affected:**
- `app/.env` (Development)

**Issue:**
```bash
# Database
# DATABASE_URL=postgresql+asyncpg://psychsync:password@localhost/psychsync_db

# # Redis
# REDIS_HOST=localhost
# REDIS_PORT=6379
```

**Misalignment:**
1. **Duplicate commented sections** throughout the file
2. **Makes it hard to parse and maintain**
3. **No clear indication of what's active vs. inactive**

**Impact:**
- Configuration file maintenance complexity
- Easy to accidentally enable wrong settings
- Difficult to review for security issues

**Recommendation:**
```bash
# Remove all commented sections
# Only keep active configuration
# Document defaults in code, not in .env files

# Clean .env structure:
# Database
DATABASE_URL=postgresql+asyncpg://psychsync_user:dev_password@localhost/5432/psychsync_dev

# Redis
REDIS_URL=redis://localhost:6379/0
```

---

## Configuration Alignment Matrix

| Setting | Development (.env) | Production (.env.production) | Template (.env.example) | Default (Code) | Status |
|----------|-------------------|------------------------------|------------------------|------------------|---------|
| DATABASE_URL | SQLite (❌) | PostgreSQL @db:5432 (⚠️) | PostgreSQL @localhost (⚠️) | PostgreSQL @localhost | MISMATCHED |
| DATABASE_POOL_SIZE | - | 20 | - | 40 | LOW VALUE |
| FRONTEND_URL | http://localhost:5174 | https://app.psychsync.com (✅) | http://localhost:5173 | http://localhost:5173 | PORT DIFF |
| REDIS_URL | HOST/PORT format (❌) | redis://redis:6379/0 (✅) | - | redis://localhost:6379 | FORMAT DIFF |
| CELERY_BROKER_URL | - | - | - | redis://localhost:6379/1 | MISSING |
| CORS_ORIGINS | - | https://app.psychsync.com | ["http://localhost:5173"] | - | MISMATCHED |
| API_PORT | 8000 (default) | - | - | 8000 | OK |
| VITE_API_URL | http://localhost:5173 (❌) | - | http://localhost:8000 | - | MISMATCHED |

Legend:
- ✅ Correct
- ❌ Critical Issue
- ⚠️ Potential Issue
- - Not Applicable

---

## Recommended Actions

### Immediate Actions (Before Next Production Deploy)

1. ✅ **Fix Development Database** - Change from SQLite to PostgreSQL
2. ✅ **Fix Frontend Port** - Align with backend (8000 or 5173)
3. ✅ **Unify Redis Configuration** - Use REDIS_URL format everywhere
4. ✅ **Add Celery Config** - Define CELERY_BROKER_URL in production
5. ✅ **Fix JWT Key Duplication** - Remove duplicate SECRET_KEY/JWT_SECRET_KEY

### Short-term Actions

6. ✅ **Update CORS Configuration** - Add environment-specific origins to template
7. ✅ **Add Rate Limiting to Template** - Document all rate limiting options
8. ✅ **Standardize Feature Flags** - Consistent naming across all files
9. ✅ **Align Database Pool Sizes** - Document if 20 is intentional

### Long-term Actions

10. ✅ **Implement Environment Validation** - Add startup validation for config
11. ✅ **Create Environment Matrix** - Document all environment differences
12. ✅ **Configuration Sync** - Add script to verify config alignment

---

## Configuration Validation Script

Create a script to validate configuration alignment:

```python
#!/usr/bin/env python3
"""
Configuration Alignment Validator
Checks for misalignment between environment files and code defaults
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environments
load_dotenv('.env')  # Development
load_dotenv('.env.production')  # Production

def check_setting(name, expected_default, actual_value):
    """Check if setting matches expected default"""
    if actual_value is None or actual_value == expected_default:
        return "OK"
    return f"MISMATCH: expected {expected_default}, got {actual_value}"

def validate_database():
    """Validate database configuration"""
    issues = []

    # Check for SQLite in non-test environments
    db_url = os.getenv('DATABASE_URL', '')
    if 'sqlite' in db_url and os.getenv('ENVIRONMENT') == 'development':
        issues.append("CRITICAL: SQLite in development - should use PostgreSQL")

    return issues

def validate_frontend_backend():
    """Validate frontend/backend connectivity"""
    issues = []

    backend_port = os.getenv('PORT', '8000')
    frontend_url = os.getenv('VITE_API_URL', '')

    # Extract port from frontend URL
    if 'localhost:' in frontend_url:
        frontend_port = frontend_url.split(':')[2].split('/')[0]
        if frontend_port != backend_port:
            issues.append(f"CRITICAL: Frontend port {frontend_port} != backend port {backend_port}")

    return issues

def main():
    """Run all validations"""
    print("🔍 Validating Configuration Alignment...\n")

    all_issues = []

    # Run validations
    all_issues.extend(validate_database())
    all_issues.extend(validate_frontend_backend())

    # Report results
    if all_issues:
        print("❌ Configuration Issues Found:\n")
        for issue in all_issues:
            print(f"  • {issue}")
        sys.exit(1)
    else:
        print("✅ All configurations aligned")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

---

`★ Insight ─────────────────────────────────────`
The most critical misalignment is the **database configuration divergence** - development uses SQLite while production expects PostgreSQL. This is a classic "works on my machine" bug that will cause deployment failures because SQLite doesn't support PostgreSQL features like `RETURNING` clauses, complex joins, and has different transaction isolation levels.

The second most critical issue is the **Redis configuration fragmentation** - mixing REDIS_HOST/REDIS_PORT format with REDIS_URL format makes it impossible to have consistent configuration management across environments.
`─────────────────────────────────────────────────`

---

**End of Deployment Configuration Misalignment Analysis**

For questions or updates, contact the DevOps team.
