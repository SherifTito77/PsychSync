# PsychSync Quick Start Guide
## Deploy to Production in 3 Steps

**Last Updated:** January 7, 2026
**Time to Deploy:** ~5 minutes
**Difficulty:** Beginner

---

## ⚡ 3-MINUTE QUICK START

### Step 1: Verify Prerequisites (1 minute)

```bash
# Check Python version (3.14+ required)
python3 --version

# Check PostgreSQL is running
pg_ctl status

# Check database exists and has tables
psql -h localhost -p 5432 -U sheriftito -d psychsync -c \
  "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';"
# Expected: 38
```

### Step 2: Deploy Application (2 minutes)

```bash
# Run the deployment script
./scripts/deploy_production.sh production

# Watch for success message:
# ✅ Deployment completed successfully!
```

**The script will:**
- ✅ Verify Python, database, and migrations
- ✅ Start application with 4 workers
- ✅ Run health checks
- ✅ Execute smoke tests

### Step 3: Verify Deployment (30 seconds)

```bash
# Quick health check
./scripts/health_check.sh

# Expected output:
# ✓ Application process running
# ✓ Health endpoint responding
# ✓ Database connected (38 tables)
```

**That's it!** Your application is now running at:
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/api/v1/health

---

## 📋 DETAILED DEPLOYMENT (If Quick Start Fails)

### Pre-Deployment Checklist

- [ ] PostgreSQL installed and running
- [ ] Python 3.14+ installed
- [ ] Database `psychsync` created
- [ ] 38 tables in database
- [ ] Migration version: 016_add_jsonb_gin_indexes
- [ ] Dependencies installed (`pip install -r requirements.txt`)

### Step-by-Step Deployment

#### 1. Database Verification

```bash
# Connect to database
psql -h localhost -p 5432 -U sheriftito -d psychsync

# In psql, run:
\dt
# Should show 38 tables

\q
```

**If tables are missing:**
```bash
python3 scripts/create_production_schema.py
alembic stamp 016_add_jsonb_gin_indexes
```

#### 2. Migration Verification

```bash
alembic current
# Expected: 016_add_jsonb_gin_indexes (head)

alembic heads
# Should show latest version
```

#### 3. Application Startup

**Option A: Automated (Recommended)**
```bash
./scripts/deploy_production.sh production
```

**Option B: Manual**
```bash
# Create logs directory
mkdir -p logs

# Start application
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info \
  > logs/application.log 2>&1 &

# Save PID
echo $! > logs/application.pid
```

#### 4. Health Verification

```bash
# Automated health check
./scripts/health_check.sh

# Manual health check
curl http://localhost:8000/api/v1/health

# Expected: {"status":"healthy"} or similar
```

#### 5. Smoke Tests

```bash
# Run regression tests
pytest tests/api/test_regression_assessments.py -v

# Expected: 1 passed
```

---

## 🔍 TROUBLESHOOTING

### Issue: Port 8000 Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use pkill
pkill -f "uvicorn app.main:app"
```

### Issue: Database Connection Failed

**Error:** `Connection refused` or `database does not exist`

**Solution:**
```bash
# Check PostgreSQL is running
pg_ctl status

# If not running, start it
pg_ctl start

# Verify database exists
psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT 1;"

# If database doesn't exist
createdb psychsync
psql -h localhost -p 5432 -U sheriftito -d psychsync \
  -c "CREATE EXTENSION IF NOT EXISTS citext;"
python3 scripts/create_production_schema.py
alembic stamp 016_add_jsonb_gin_indexes
```

### Issue: Import Errors

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
# Make sure you're in project root
cd /Users/sheriftito/Downloads/psychsync

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-ai.txt
```

### Issue: Permission Denied

**Error:** `Permission denied` when running scripts

**Solution:**
```bash
# Make scripts executable
chmod +x scripts/deploy_production.sh
chmod +x scripts/health_check.sh

# Try again
./scripts/deploy_production.sh production
```

### Issue: Health Check Failing

**Error:** Health endpoint returns 500 or times out

**Solution:**
```bash
# Check application logs
tail -100 logs/application.log

# Restart application
pkill -f "uvicorn app.main:app"
./scripts/deploy_production.sh production

# If still failing, check logs for specific errors
tail -f logs/application.log
```

---

## 📊 MONITORING YOUR DEPLOYMENT

### Health Monitoring

**Watch Mode (Continuous):**
```bash
./scripts/health_check.sh --watch
```
Press Ctrl+C to exit

**One-Time Check:**
```bash
./scripts/health_check.sh
```

**Verbose Output:**
```bash
./scripts/health_check.sh --verbose
```

### Log Monitoring

**Real-time Logs:**
```bash
tail -f logs/application.log
```

**Recent Errors:**
```bash
tail -100 logs/application.log | grep -i error
```

**Recent Warnings:**
```bash
tail -100 logs/application.log | grep -i warning
```

### Application Status

**Check Process:**
```bash
pgrep -f "uvicorn app.main:app"
ps aux | grep "uvicorn app.main:app"
```

**Check HTTP Endpoint:**
```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/docs
```

**Check Database:**
```bash
psql -h localhost -p 5432 -U sheriftito -d psychsync -c \
  "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';"
```

---

## 🔄 DAILY OPERATIONS

### Morning Startup

```bash
# 1. Check health
./scripts/health_check.sh

# 2. If not running, start it
./scripts/deploy_production.sh production

# 3. Verify API is accessible
curl http://localhost:8000/api/v1/health
```

### Evening Shutdown

```bash
# Graceful shutdown
pkill -f "uvicorn app.main:app"

# Verify stopped
pgrep -f "uvicorn app.main:app" || echo "Application stopped"
```

### Restart Application

```bash
# Full restart
pkill -f "uvicorn app.main:app"
./scripts/deploy_production.sh production

# Quick restart (keeps PID)
./scripts/deploy_production.sh production
```

---

## 📚 NEXT STEPS

### After Successful Deployment

1. **Set up monitoring** (optional)
   ```bash
   ./scripts/deploy_monitoring.sh
   ```
   Requires Docker Desktop

2. **Configure CI/CD monitoring**
   Visit: https://github.com/SherifTito77/PsychSync/actions

3. **Review documentation**
   - [Operations Guide](docs/operations/OPERATIONS_GUIDE.md)
   - [Deployment Guide](docs/COMPLETE_DEPLOYMENT_GUIDE.md)
   - [Production Summary](docs/PRODUCTION_READINESS_FINAL_SUMMARY.md)

4. **Configure backups**
   ```bash
   # Manual backup
   pg_dump -h localhost -p 5432 -U sheriftito -d psychsync \
     --format=custom -f backups/backup_$(date +%Y%m%d).dump
   ```

### Advanced Configuration

**Change Workers:**
Edit `scripts/deploy_production.sh` and modify `--workers 4` to desired number.

**Change Port:**
Edit `scripts/deploy_production.sh` and modify `--port 8000` to desired port.

**Enable Debug Mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

---

## 🎯 SUCCESS CRITERIA

Your deployment is successful when:

- ✅ `./scripts/health_check.sh` shows all green
- ✅ `curl http://localhost:8000/api/v1/health` returns 200 OK
- ✅ API docs accessible at http://localhost:8000/docs
- ✅ No errors in `logs/application.log`
- ✅ Tests passing: `pytest tests/api/test_regression_assessments.py -v`

---

## 📞 GETTING HELP

### Documentation

- **Quick Start:** This file
- **Operations:** [docs/operations/OPERATIONS_GUIDE.md](docs/operations/OPERATIONS_GUIDE.md)
- **Deployment:** [docs/COMPLETE_DEPLOYMENT_GUIDE.md](docs/COMPLETE_DEPLOYMENT_GUIDE.md)
- **Production Summary:** [docs/PRODUCTION_READINESS_FINAL_SUMMARY.md](docs/PRODUCTION_READINESS_FINAL_SUMMARY.md)
- **Documentation Index:** [docs/README_INDEX.md](docs/README_INDEX.md)

### Quick Commands

```bash
# Get help
./scripts/deploy_production.sh --help

# Check status
./scripts/health_check.sh --verbose

# View logs
tail -f logs/application.log

# Database connection test
psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT 1;"
```

---

**Quick Start Guide Last Updated:** January 7, 2026
**Deployment Time:** 3-5 minutes
**Status:** Production Ready ✅
