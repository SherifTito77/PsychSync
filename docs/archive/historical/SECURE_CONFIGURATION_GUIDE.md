# Secure Configuration Guide

Complete guide for using PsychSync's secure configuration system.

**Last Updated:** 2025-12-24

---

## 🚀 Quick Start

### 1. Generate Secure Secrets

```bash
# Generate strong secrets for your deployment
python scripts/generate_secrets.py
```

This will output:
- `SECRET_KEY` - JWT authentication
- `ENCRYPTION_KEY` - Data encryption
- `DATABASE_URL` - Database connection
- `REDIS_PASSWORD` - Redis authentication

### 2. Create Environment File

```bash
# Generate .env file from template
python -c "from app.core.secure_config import generate_secure_env_template; generate_secure_env_template()"

# Copy and fill in your secrets
cp .env.example .env
# Edit .env with your generated secrets
```

### 3. Validate Configuration

```bash
# Test your configuration
python -c "from app.core.secure_config import get_settings; get_settings()"

# Validate production readiness
python -c "from app.core.secure_config import validate_production_readiness; validate_production_readiness()"
```

---

## 📖 Configuration Reference

### Required Environment Variables

#### Core Security
```bash
# Environment (development, staging, production)
ENVIRONMENT=production
DEBUG=false

# JWT Secret (MINIMUM 32 characters, high entropy)
SECRET_KEY=<your-64-character-secret>

# Encryption Key (Fernet format)
ENCRYPTION_KEY=<your-fernet-key>

# Database URL (secure credentials)
DATABASE_URL=postgresql://user:strong_password@host:5432/db

# Redis URL (with password in production)
REDIS_URL=redis://:password@host:6379/0
REDIS_PASSWORD=<strong-redis-password>
```

#### CORS Configuration
```bash
# Comma-separated list of allowed origins
CORS_ORIGINS=https://psychsync.com,https://www.psychsync.com

# NOTE: In production, all origins must use HTTPS
# Never use "*" or "http://*" in production
```

#### Email Configuration
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<app-specific-password>
SMTP_TLS=true  # Required in production
```

#### Third-Party APIs
```bash
SLACK_CLIENT_ID=<your-client-id>
SLACK_CLIENT_SECRET=<your-client-secret>

GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>

OPENAI_API_KEY=<sk-...>
```

---

## 🔒 Security Validations

The secure configuration system automatically validates:

### ✅ DEBUG Mode
- **Check:** `DEBUG` must be `False` in production
- **Error:** "DEBUG cannot be True in production"

### ✅ Secret Key Strength
- **Check:** Minimum 32 characters
- **Check:** High entropy (at least 10 unique characters)
- **Check:** Not using default/example keys
- **Error:** "SECRET_KEY must be at least 32 characters"
- **Error:** "SECRET_KEY has insufficient entropy"
- **Error:** "SECRET_KEY is using a default value"

### ✅ Database Credentials
- **Check:** Not using default credentials (postgres:postgres, root:root, etc.)
- **Error:** "Database URL contains default credentials"

### ✅ CORS Origins
- **Check:** Not wide open (`*`, `http://*`, `https://*`)
- **Check:** HTTPS required in production (except localhost)
- **Error:** "CORS origin is too permissive for production"
- **Error:** "CORS origin must use HTTPS in production"

### ✅ Redis Password
- **Check:** Required in production
- **Error:** "REDIS_PASSWORD is required in production"

### ✅ SMTP TLS
- **Check:** Required in production
- **Error:** "SMTP_TLS must be True in production"

---

## 💻 Usage Examples

### In Application Code

```python
# Import settings
from app.core.secure_config import settings, get_secret

# Access configuration values
app_name = settings.APP_NAME
debug_mode = settings.DEBUG

# Access secrets (automatically decrypted)
database_url = settings.DATABASE_URL.get_secret_value()
secret_key = settings.SECRET_KEY.get_secret_value()

# Get specific secret
openai_key = get_secret("OPENAI_API_KEY")

# Check environment
if settings.ENVIRONMENT == "production":
    # Production-specific logic
    enable_monitoring()
```

### Database Connection

```python
from app.core.secure_config import settings
from sqlalchemy.ext.asyncio import create_async_engine

# Use secure database URL
engine = create_async_engine(
    settings.DATABASE_URL.get_secret_value(),
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
)
```

### JWT Token Generation

```python
from app.core.secure_config import settings
from datetime import timedelta

access_token_expires = timedelta(
    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
)

refresh_token_expires = timedelta(
    days=settings.REFRESH_TOKEN_EXPIRE_DAYS
)
```

---

## 🧪 Testing Configuration

### Validate Development Setup

```bash
# Set environment
export ENVIRONMENT=development
export DEBUG=true
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
export DATABASE_URL="postgresql://test:test@localhost:5432/test"
export REDIS_URL="redis://localhost:6379/0"

# Test configuration
python -c "
from app.core.secure_config import get_settings
settings = get_settings()
print('✅ Configuration loaded successfully')
print(f'Environment: {settings.ENVIRONMENT}')
print(f'Debug: {settings.DEBUG}')
"
```

### Validate Production Setup

```bash
# Set production environment
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY=<your-strong-secret>
export DATABASE_URL=<secure-database-url>
export REDIS_URL=<secure-redis-url>
export REDIS_PASSWORD=<redis-password>

# Test configuration
python -c "
from app.core.secure_config import get_settings, validate_production_readiness
settings = get_settings()
validate_production_readiness()
print('✅ Production-ready configuration validated')
"
```

---

## 🔧 Troubleshooting

### Error: "SECRET_KEY must be at least 32 characters"

**Solution:** Generate a stronger secret
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Error: "SECRET_KEY has insufficient entropy"

**Solution:** Your secret has too many repeated characters
```bash
# Bad: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
# Good: use generator
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Error: "Database URL contains default credentials"

**Solution:** Change default username/password
```bash
# Bad: postgresql://postgres:postgres@localhost/db
# Good: postgresql://appuser:strong_random_pass@localhost/db
```

### Error: "CORS origin must use HTTPS in production"

**Solution:** Use HTTPS URLs (except localhost)
```bash
# Bad: http://example.com
# Good: https://example.com
```

---

## 📊 Production Readiness Checklist

Before deploying to production, verify:

- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] Strong `SECRET_KEY` (64+ characters, high entropy)
- [ ] Valid `ENCRYPTION_KEY` (Fernet format)
- [ ] Secure database credentials (not default)
- [ ] `REDIS_PASSWORD` set
- [ ] CORS origins use HTTPS (except localhost)
- [ ] `SMTP_TLS=true`
- [ ] `SECURE_COOKIES=true`
- [ ] `SENTRY_DSN` configured for error tracking
- [ ] All secrets stored in vault (not .env)

---

## 🔐 Secrets Management Best Practices

### Development
- Use `.env` file (never commit)
- Different secrets for each developer
- Rotate secrets monthly

### Staging
- Use environment variables
- Shared secrets team access
- Rotate before production deployment

### Production
- Use AWS Secrets Manager or HashiCorp Vault
- No `.env` files
- Rotate secrets every 90 days
- Enable secret rotation automation
- Monitor for secret leaks

---

## 📝 Environment Files

### .env.example (Template)
```bash
# Copy this to .env and fill in real values
ENVIRONMENT=development
DEBUG=false
SECRET_KEY=GENERATE_WITH_SCRIPT
DATABASE_URL=postgresql://user:password@localhost:5432/db
REDIS_URL=redis://localhost:6379/0
```

### .env (NEVER COMMIT)
```bash
# Your actual secrets
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=5odrlpy9kOm9KtwWZDkTqT8IWmmZBR8Z7WoHW_GmGvsKsve-P8X...
DATABASE_URL=postgresql://appuser:sTr0ngP@ssw0rd@localhost:5432/psychsync
REDIS_URL=redis://:r3d1sp@ss@localhost:6379/0
```

---

## 🚀 Deployment Configuration

### Docker Compose
```yaml
services:
  backend:
    environment:
      - ENVIRONMENT=production
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
```

### Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: psychsync-secrets
type: Opaque
stringData:
  SECRET_KEY: <base64-encoded>
  DATABASE_URL: <base64-encoded>
  REDIS_URL: <base64-encoded>
```

---

## 📚 Related Documentation

- **Security Architecture:** `docs/SECURITY_ARCHITECTURE.md`
- **Quick Start:** `docs/SECURITY_QUICK_START.md`
- **Main Config:** `app/core/config.py`

---

## 🆘 Getting Help

### Generate New Secrets
```bash
python scripts/generate_secrets.py
```

### Validate Current Configuration
```bash
python -c "from app.core.secure_config import get_settings, validate_production_readiness; get_settings(); validate_production_readiness()"
```

### Debug Configuration Issues
```bash
# Enable debug output
export LOG_LEVEL=DEBUG

# Check what's being loaded
python -c "from app.core.secure_config import settings; print(settings.dict())"
```

---

**Remember:** Never commit secrets to git! Use environment-specific secrets and rotate them regularly.
