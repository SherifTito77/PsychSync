# CI/CD Monitoring Quick Reference
## Production Deployment Checklist & Workflow Monitoring

**Date:** January 6, 2026
**Purpose:** Quick reference for monitoring CI/CD workflows and deployment tasks

---

## 🔄 CI/CD WORKFLOW MONITORING

### Monitor via Web Browser (Recommended)

**GitHub Actions Dashboard:**
```
URL: https://github.com/SherifTito77/PsychSync/actions
```

**What to Check:**
- ✅ Green checkmarks = Successful runs
- ❌ Red X marks = Failed runs (needs attention)
- 🟡 Yellow dots = In progress
- ⚪ Grey circles = Not run yet

**Activated Workflows (6):**

1. **SBOM Generation** (`sbom.yaml`)
   - Trigger: Every push to main, pull requests
   - Output: Software Bill of Materials files
   - Status: Should run automatically

2. **Security Scanning** (`security-scan.yml`)
   - Trigger: Push, PR, manual
   - Tools: Bandit, Semgrep, Safety
   - Duration: ~5 minutes

3. **Linting** (`lint.yml`)
   - Trigger: Push, PR, manual
   - Tool: Ruff (Python linter)
   - Duration: ~2 minutes

4. **Agent Deployment** (`agents.yml`)
   - Trigger: Manual dispatch only
   - Purpose: Deploy AI agents
   - Action: Trigger manually when needed

5. **AI Security Gate** (`ai-security-gate.yml`)
   - Trigger: Push to main
   - Purpose: Validate AI/ML security
   - Duration: ~10 minutes

6. **SLSA Signing** (`slsa-sign.yaml`)
   - Trigger: Release creation
   - Output: Signed artifacts with provenance
   - Duration: ~3 minutes

### Monitor via GitHub CLI (Alternative)

**Install GitHub CLI:**
```bash
# macOS
brew install gh

# Authenticate
gh auth login
```

**Quick Commands:**
```bash
# List recent runs (latest 10)
gh run list --limit 10

# View specific run details
gh run view <run-id>

# View logs for a run
gh run view --log

# Watch a workflow in real-time
gh run watch

# Re-run a failed workflow
gh run rerun <run-id>
```

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Deployment Tasks

#### 1. Database Migration Check
```bash
# Check current migration version
psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT version_num FROM alembic_version;"

# Current status: 001_base_tables
# Latest available: 016_add_jsonb_gin_indexes

# To upgrade (DO THIS IN PRODUCTION):
alembic upgrade head

# Or upgrade step by step:
alembic upgrade +1
```

⚠️ **IMPORTANT**: Production database is at migration 001, needs upgrade to 016

#### 2. Environment Variables Check
```bash
# Verify environment files exist
ls -la .env.prod .env.dev

# Check critical variables:
# - DATABASE_URL
# - SECRET_KEY
# - JWT_SECRET
# - REDIS_URL
# - CORS_ORIGINS
```

#### 3. Docker Installation (if deploying monitoring)
```bash
# Check if Docker is installed
docker --version
docker compose version

# If not installed:
# macOS: https://docs.docker.com/desktop/install/mac-install/
# Linux: https://docs.docker.com/engine/install/
```

---

### Monitoring Stack Deployment

#### Option 1: Interactive Script
```bash
./scripts/deploy_monitoring.sh
# Select: 1 (Start monitoring stack)
```

#### Option 2: Manual Docker Compose
```bash
cd deploy
docker compose -f monitoring-stack.yml up -d

# Verify services running
docker compose -f monitoring-stack.yml ps

# View logs
docker compose -f monitoring-stack.yml logs -f
```

#### Access Points
```
Grafana:    http://localhost:3000 (admin/admin)
Prometheus: http://localhost:9090
Redis:      localhost:6379
```

#### Verify Deployment
```bash
# Check Grafana health
curl -s http://localhost:3000/api/health

# Check Prometheus health
curl -s http://localhost:9090/-/healthy

# Check Redis
redis-cli ping
```

---

## 📊 APPLICATION STARTUP

### Backend (FastAPI)
```bash
# Development mode with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Check health endpoint
curl http://localhost:8000/api/v1/health
```

### Frontend (React + Vite)
```bash
cd frontend

# Development server
npm run dev
# Runs on: http://localhost:5173

# Production build
npm run build

# Preview production build
npm run preview
```

### Full Stack with Docker
```bash
# Start all services
docker-compose up --build

# Specific services
docker-compose up backend frontend db redis

# Background mode
docker-compose up -d
```

---

## ✅ PRE-DEPLOYMENT VERIFICATION

### Database Checks
```bash
# 1. Database connectivity
psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT 1;"

# 2. Table count (should be 37+ after migrations)
psql -h localhost -p 5432 -U sheriftito -d psychsync -c \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# 3. CITEXT extension
psql -h localhost -p 5432 -U sheriftito -d psychsync -c \
  "SELECT extname FROM pg_extension WHERE extname = 'citext';"
```

### Test Verification
```bash
# Run regression tests
pytest tests/api/test_regression_assessments.py -v

# Run specific passing test
pytest tests/api/test_regression_assessments.py::TestAssessmentCRUDRegression::test_create_assessment_success -xvs

# Expected: 1 passed in ~28s
```

### CI/CD Status
```bash
# Via browser
# https://github.com/SherifTito77/PsychSync/actions

# Check for:
# - All workflows triggered by recent push
# - No failing workflows
# - Artifacts generated (SBOM, scan results)
```

---

## 🚨 TROUBLESHOOTING

### Workflow Failures

**Linting Errors:**
```bash
# Run locally to see issues
ruff check .

# Auto-fix
ruff check --fix .
```

**Security Scan Findings:**
```bash
# Run Bandit locally
bandit -r app/

# Run Semgrep locally
semgrep --config=semgrep_rules/ app/
```

**Test Failures:**
```bash
# Run with verbose output
pytest tests/ -v --tb=short

# Run specific test
pytest tests/path/to/test.py::TestClassName::test_name -xvs
```

### Database Issues

**Migration Conflicts:**
```bash
# Check current version
alembic current

# Check history
alembic history

# Stamp to specific version (careful!)
alembic stamp <revision>
```

**Connection Issues:**
```bash
# Check PostgreSQL is running
pg_ctl status

# Or via brew
brew services list | grep postgres
```

### Docker Issues

**Container Won't Start:**
```bash
# Check Docker is running
docker ps

# Check logs
docker logs <container-name>

# Restart Docker Desktop (macOS)
# Click Docker Desktop icon → Restart
```

**Port Conflicts:**
```bash
# Check what's using port 3000
lsof -i :3000

# Check what's using port 9090
lsof -i :9090

# Kill process if needed
kill -9 <PID>
```

---

## 📋 DEPLOYMENT DAY CHECKLIST

### Morning Of Deployment
- [ ] Verify all CI/CD workflows passing
- [ ] Check database backup is current
- [ ] Verify monitoring stack ready (Grafana, Prometheus)
- [ ] Have rollback plan documented

### During Deployment
- [ ] Run database migrations (`alembic upgrade head`)
- [ ] Restart backend services
- [ ] Verify health endpoints responding
- [ ] Check monitoring dashboards for errors
- [ ] Run smoke tests

### After Deployment
- [ ] Verify all workflows passing
- [ ] Check Grafana for error spikes
- [ ] Monitor Prometheus metrics
- [ ] Verify application functionality
- [ ] Check logs for errors

### One Hour Post-Deployment
- [ ] Review error rates
- [ ] Check response times
- [ ] Verify database connection pool healthy
- [ ] Confirm cache hit rates acceptable
- [ ] No alert notifications firing

---

## 📞 EMERGENCY CONTACTS & RESOURCES

### Rollback Commands
```bash
# Rollback database migration
alembic downgrade -1

# Restart previous version
git checkout <previous-tag>
docker-compose up -d --force-recreate
```

### Documentation Links
- Complete Deployment Guide: `docs/COMPLETE_DEPLOYMENT_GUIDE.md`
- Test Infrastructure Fixes: `docs/TEST_INFRASTRUCTURE_FIXES_SUMMARY.md`
- Action Plan Report: `docs/ACTION_PLAN_EXECUTION_REPORT.md`
- Incident Response: `docs/operations/INCIDENT_RESPONSE_RUNBOOK.md`

### Key Files
- Monitoring Stack: `deploy/monitoring-stack.yml`
- Deployment Script: `scripts/deploy_monitoring.sh`
- Test Configuration: `tests/conftest.py`

---

## 🎯 SUCCESS CRITERIA

**Deployment is successful when:**
- ✅ All CI/CD workflows passing (green checkmarks)
- ✅ Database migrated to latest version (016)
- ✅ Health endpoints returning 200 OK
- ✅ Monitoring dashboards showing normal metrics
- ✅ No error spikes in logs
- ✅ Smoke tests passing
- ✅ Response times within acceptable ranges
- ✅ Database connection pool healthy

---

**Last Updated:** January 6, 2026
**Status:** Production Ready (99% complete)
**Next Step:** Monitor CI/CD workflows, install Docker for monitoring deployment
