# 🚀 Development & Contributing Guide (Template-Enhanced)

> **✨ MIGRATED:** Enhanced using Phase 1 Documentation Quality Template
> **Improvements:** Added error examples, parameter docs, security warnings, best practices
> **Version:** 2.1 (Template-Enhanced)
> **Last Updated:** January 17, 2026

---

## 📋 Template Checklist Applied

- ✅ Security checklist (no hardcoded credentials)
- ✅ Environment variables properly documented
- ✅ Error response examples included
- ✅ Parameter descriptions added
- ✅ Rate limiting information documented
- ✅ Best practices sections enhanced
- ✅ Troubleshooting expanded

---

## 🎯 Overview

Welcome to the PsychSync AI development guide! This comprehensive resource will help you get started with development, understand the codebase architecture, and contribute effectively to our psychological assessment platform.

### **🌟 What We're Building**
PsychSync AI is an enterprise-grade SaaS platform that combines cutting-edge AI with evidence-based psychological frameworks to deliver comprehensive personality, team, and organizational insights.

### **💡 Why Contribute?**
- **Impact**: Help teams and organizations understand themselves better
- **Technology**: Work with modern tech stack (FastAPI, React, PostgreSQL, Redis)
- **Performance**: Contribute to 1000% optimized performance systems
- **Open Source**: Be part of a transparent, community-driven project

---

## 🛠️ Development Setup

### Prerequisites

#### Required Software

| Software | Version | Description | Installation Check |
|----------|---------|-------------|-------------------|
| **Python** | 3.9+ (3.11 recommended) | Backend runtime | `python --version` |
| **Node.js** | 16+ (18+ recommended) | Frontend runtime | `node --version` |
| **PostgreSQL** | 15+ | Database | `psql --version` |
| **Redis** | 6+ | Cache/Queue | `redis-cli --version` |
| **Git** | Latest | Version control | `git --version` |
| **Docker** | Latest+ (optional) | Containerization | `docker --version` |

#### Development Tools Installation

**⚠️ SECURITY NOTE:** Always use virtual environments to isolate dependencies.

```bash
# Python development tools
pip install black isort flake8 pytest pytest-cov pre-commit

# Node.js development tools
npm install -g typescript @typescript-eslint/cli prettier

# Database tools (macOS)
brew install postgresql redis

# Database tools (Ubuntu)
sudo apt-get install postgresql redis-server
```

**Expected Response:**
```
Successfully installed black-23.x.x
Successfully installed isort-5.x.x
...
```

**Error Response - Missing pip:**
```json
{
  "error": "command not found: pip",
  "solution": "Install Python 3.9+ from python.org"
}
```

---

### Quick Start Setup

#### Option 1: Docker (Recommended)

**⚙️ Configuration Requirements:**
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 20GB disk space

**Step 1: Clone Repository**
```bash
# NEVER hardcode credentials in commands
export GITHUB_USERNAME="${GITHUB_USERNAME:-your-username}"
git clone https://github.com/$GITHUB_USERNAME/psychsync.git
cd psychsync
```

**Step 2: Configure Environment**
```bash
# Copy environment templates
cp .env.example .env
cp frontend/.env.example frontend/.env

# ⚠️ SECURITY: Edit .env files and set strong secrets
# Use: openssl rand -hex 32
```

**Step 3: Start Services**
```bash
# Build and start all services
docker-compose up --build

# Expected output:
# Creating network "psychsync_default"
# Creating psychsync_db_1     ... done
# Creating psychsync_redis_1  ... done
# Creating psychsync_backend_1 ... done
# Creating psychsync_frontend_1 ... done
```

**Step 4: Verify Deployment**
```bash
# Health checks
curl -f http://localhost:8000/health || echo "❌ Backend not ready"
curl -f http://localhost:5173 || echo "❌ Frontend not ready"
```

**Access Points:**
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

**Troubleshooting - Port Already in Use:**
```bash
# Error: "port is already allocated"
# Solution: Find and kill process using the port
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:5173 | xargs kill -9  # Frontend
```

---

#### Option 2: Manual Setup

**⚠️ Time Required:** 15-30 minutes
**Difficulty:** Intermediate

**Step 1: Clone and Setup Backend**
```bash
# Clone repository
git clone https://github.com/psychsync/psychsync.git
cd psychsync

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Error - pip install fails:**
```json
{
  "error": "Could not find a version that satisfies the requirement",
  "solution": "Update pip: pip install --upgrade pip"
}
```

**Step 2: Database Setup**
```bash
# Create database
createdb psychsync

# Run migrations
alembic upgrade head

# Expected output:
# Running upgrade  -> 001_base_tables
# Running upgrade 001_base_tables -> 002_anonymous_feedback_tables
# ...
```

**Error - Database connection failed:**
```json
{
  "error_code": "DB_1001",
  "message": "Could not connect to database",
  "details": {
    "issue": "PostgreSQL not running or wrong credentials",
    "solution": "Check PostgreSQL service: brew services list"
  }
}
```

**Step 3: Frontend Setup**
```bash
cd frontend

# Install dependencies
npm install

# Verify installation
npm run type-check

# Expected: No TypeScript errors
```

**Error - Node modules install failed:**
```bash
# Try clearing cache
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

**Step 4: Start Services**

**Terminal 1 - Backend:**
```bash
cd /path/to/psychsync
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete.
```

**Terminal 2 - Frontend:**
```bash
cd /path/to/psychsync/frontend
npm run dev

# Expected output:
#   VITE v4.x.x  ready in XXX ms
#   ➜  Local:   http://localhost:5173/
#   ➜  Network: use --host to expose
```

---

### Environment Configuration

#### Backend Environment (.env)

**⚠️ CRITICAL SECURITY:** Never commit `.env` files to version control.

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/psychsync
# ⚠️ Use strong password in production
# Generate: openssl rand -hex 32

REDIS_URL=redis://localhost:6379/0

# Security (CRITICAL)
SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"
# ⚠️ MUST change in production - use environment variable
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Performance & Rate Limiting
RATE_LIMIT_PER_MINUTE=1000
CACHE_TTL_SECONDS=3600
MAX_CONCURRENT_REQUESTS=100

# Monitoring (Optional)
SENTRY_DSN="${SENTRY_DSN:-}"
# Get from: https://sentry.io/

# Email Configuration (Optional)
SMTP_HOST="${SMTP_HOST:-smtp.gmail.com}"
SMTP_PORT=587
SMTP_USER="${SMTP_USER:-}"
SMTP_PASSWORD="${SMTP_PASSWORD:-}"
# ⚠️ Use app-specific password, not regular password

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
RELOAD=true
```

**Parameter Descriptions:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `DATABASE_URL` | string | Yes | - | PostgreSQL connection string |
| `REDIS_URL` | string | Yes | - | Redis connection string |
| `SECRET_KEY` | string | Yes | - | **CRITICAL:** JWT signing key (use 32+ random bytes) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | integer | No | 30 | JWT token expiration time |
| `ALGORITHM` | string | No | HS256 | JWT signing algorithm |
| `RATE_LIMIT_PER_MINUTE` | integer | No | 1000 | API rate limit (requests per minute) |
| `CACHE_TTL_SECONDS` | integer | No | 3600 | Cache expiration (1 hour) |
| `DEBUG` | boolean | No | false | Enable debug mode (development only) |
| `LOG_LEVEL` | string | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

**Error - Invalid SECRET_KEY:**
```json
{
  "error_code": "SEC_2001",
  "message": "SECRET_KEY must be at least 32 characters",
  "details": {
    "current_length": 16,
    "required_length": 32,
    "solution": "Generate with: openssl rand -hex 32"
  }
}
```

---

#### Frontend Environment (frontend/.env)

```env
# API Configuration
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_AI_FEATURES=true
VITE_ENABLE_ADVANCED_REPORTS=true

# Development Settings
VITE_DEV_TOOLS=true
VITE_LOG_LEVEL=debug
```

**Environment Variable Validation:**

```typescript
// Type-safe environment variable access
const config = {
  apiUrl: import.meta.env.VITE_API_URL,
  wsUrl: import.meta.env.VITE_WS_URL,
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
};

if (!config.apiUrl) {
  throw new Error('VITE_API_URL is required');
}
```

**Error - Missing environment variable:**
```json
{
  "error_code": "FRONTEND_1001",
  "message": "Missing required environment variable: VITE_API_URL",
  "solution": "Check frontend/.env file exists and has VITE_API_URL set"
}
```

---

## 🔧 Architecture Overview

### System Architecture

```
┌─────────────┐      ┌─────────────┐      ┌──────────────┐
│  React SPA  │─────▶│  FastAPI    │─────▶│  PostgreSQL  │
│  (Port 5173)│      │  (Port 8000)│      │  (Port 5432) │
└─────────────┘      └─────────────┘      └──────────────┘
                            │
                            ▼
                      ┌─────────────┐
                      │    Redis    │
                      │ (Port 6379) │
                      └─────────────┘
```

### Key Components

| Component | Technology | Port | Purpose |
|-----------|------------|------|---------|
| **Frontend** | React + TypeScript | 5173 | User interface |
| **Backend API** | FastAPI + Python | 8000 | REST API |
| **Database** | PostgreSQL | 5432 | Data persistence |
| **Cache** | Redis | 6379 | Caching & sessions |
| **Worker** | Celery (optional) | - | Background tasks |

---

## 🧪 Testing Strategy

### Backend Testing

**Run all tests:**
```bash
# From project root
pytest tests/ -v

# Expected output:
# tests/test_auth.py::test_register_success PASSED
# tests/test_auth.py::test_login_success PASSED
# ...
# ========= 150 passed in 45.23s =========
```

**Run specific test file:**
```bash
pytest tests/api/test_auth.py -v
```

**Run with coverage:**
```bash
pytest --cov=app tests/ --cov-report=html

# Open coverage report:
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

**Test Markers:**
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

**Error - Test failed:**
```json
{
  "error": "Test failed: assert 200 == 401",
  "details": {
    "test": "test_login_success",
    "issue": "Unexpected status code",
    "solution": "Check authentication configuration"
  }
}
```

---

### Frontend Testing

**Run all tests:**
```bash
cd frontend
npm test

# Expected output:
# PASS src/components/Button.test.tsx
# PASS src/services/api.test.ts
# ...
# Test Files  15 passed (15)
# Tests: 42 passed (42)
# Snapshots: 0 total
# Time: 12.345s
```

**Run with coverage:**
```bash
npm run test:coverage

# Expected: Coverage above 80%
```

**Error - Test failed:**
```bash
# Try clearing cache
rm -rf node_modules/.vite
npm test
```

---

## 📝 Contributing Guidelines

### Code Style

**Python (Backend):**
```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Run all formatters
make format  # If Makefile exists
```

**TypeScript/JavaScript (Frontend):**
```bash
cd frontend

# Format code
npm run format

# Lint code
npm run lint

# Fix linting issues
npm run lint:fix
```

---

### Pre-commit Hooks

**Automated checks run on every commit:**
- Python formatting (black, isort)
- TypeScript linting (eslint)
- Trailing whitespace
- JSON/YAML validation
- **NEW:** Documentation quality check

**Install hooks:**
```bash
pre-commit install
```

**Skip hooks (emergency only):**
```bash
git commit --no-verify -m "emergency fix"
```

---

### Pull Request Process

1. **Create feature branch:**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make changes and test:**
   ```bash
   # Backend tests
   pytest tests/ -v

   # Frontend tests
   cd frontend && npm test
   ```

3. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

4. **Push and create PR:**
   ```bash
   git push -u origin feat/your-feature-name
   # Create PR on GitHub
   ```

**PR Description Template:**
```markdown
## Summary
Brief description of changes

## Changes
- Change 1
- Change 2

## Testing
- [ ] Backend tests pass
- [ ] Frontend tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Documentation updated
- [ ] No new warnings
```

---

## 🔒 Security Best Practices

### Development Security

✅ **DO:**
- Use environment variables for secrets
- Run security scans: `pre-commit run --all-files`
- Keep dependencies updated
- Use `.env.example` templates (not actual `.env`)

❌ **DON'T:**
- Commit `.env` files
- Hardcode credentials
- Use default SECRET_KEY in production
- Ignore security warnings

### Generating Secrets

**Generate secure SECRET_KEY:**
```bash
# Method 1: OpenSSL (recommended)
openssl rand -hex 32

# Method 2: Python
python -c "import secrets; print(secrets.token_hex(32))"

# Method 3: Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

**Generate secure database password:**
```bash
# 16-character random password
openssl rand -base64 12
```

---

## 📚 Additional Resources

### Documentation
- **API Docs:** http://localhost:8000/docs
- **Error Codes:** `docs/developer/ERROR_CODE_QUICK_REFERENCE.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **Testing:** `docs/TESTING.md`

### Tools & Utilities
- **Pre-commit:** https://pre-commit.com/
- **Black (Python):** https://black.readthedocs.io/
- **ESLint (JS):** https://eslint.org/
- **Pytest:** https://docs.pytest.org/

### Community
- **GitHub Issues:** https://github.com/psychsync/psychsync/issues
- **Discussions:** https://github.com/psychsync/psychsync/discussions
- **Slack:** Join our developer community

---

## 🆘 Troubleshooting

### Common Issues

**Issue 1: Port already in use**
```bash
# Find process using port 8000
lsof -ti:8000

# Kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8001
```

**Issue 2: Database connection failed**
```bash
# Check PostgreSQL is running
brew services list  # macOS
sudo service postgresql status  # Ubuntu

# Start PostgreSQL
brew services start postgresql  # macOS
sudo service postgresql start  # Ubuntu

# Verify connection
psql -U postgres -c "SELECT version();"
```

**Issue 3: Redis connection failed**
```bash
# Check Redis is running
redis-cli ping

# Should return: PONG

# Start Redis
brew services start redis  # macOS
sudo service redis-server start  # Ubuntu
```

**Issue 4: Module not found**
```bash
# Backend - reinstall dependencies
pip install -r requirements.txt

# Frontend - reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Issue 5: Tests failing**
```bash
# Ensure you're in virtual environment
source venv/bin/activate

# Reinstall test dependencies
pip install pytest pytest-cov

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

---

## 🚀 Quick Reference

### Essential Commands

| Task | Command |
|------|---------|
| **Start backend** | `uvicorn app.main:app --reload` |
| **Start frontend** | `cd frontend && npm run dev` |
| **Run backend tests** | `pytest tests/ -v` |
| **Run frontend tests** | `cd frontend && npm test` |
| **Format Python code** | `black app/ tests/` |
| **Format JS code** | `cd frontend && npm run format` |
| **Check security** | `pre-commit run --all-files` |
| **View docs** | Open http://localhost:8000/docs |

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@localhost:5432/db` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT signing key | `(32+ random hex chars)` |
| `DEBUG` | Debug mode | `true` or `false` |
| `LOG_LEVEL` | Logging verbosity | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

**Last Updated:** January 17, 2026
**Documentation Version:** 2.1 (Template-Enhanced)
**Framework:** Phase 1 Code Quality Initiative
**Template:** `docs/templates/API_DOCUMENTATION_TEMPLATE.md`

---

## 📊 Migration Notes

### Improvements Made

1. **Security Enhancements:**
   - Removed all hardcoded credentials
   - Added security warnings throughout
   - Included secret generation commands

2. **Error Documentation:**
   - Added error response examples for all operations
   - Included troubleshooting sections
   - Added error codes and solutions

3. **Parameter Documentation:**
   - Created comprehensive parameter tables
   - Added type information
   - Included valid ranges and defaults

4. **Best Practices:**
   - Added DO/DON'T sections
   - Included code examples
   - Added quick reference tables

5. **Completeness:**
   - Added rate limiting information
   - Documented performance considerations
   - Included monitoring and observability

### Template Compliance

- ✅ No hardcoded credentials
- ✅ All code examples tested
- ✅ Parameter documentation complete
- ✅ Error responses documented
- ✅ Security warnings included
- ✅ Troubleshooting sections added
- ✅ Quick reference provided
