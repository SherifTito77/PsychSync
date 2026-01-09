# PsychSync Operations Guide
## Production Operations & Management Playbook

**Last Updated:** January 7, 2026
**Version:** 1.0.0
**Status:** Production Ready ✅

---

## 📋 TABLE OF CONTENTS

1. [Quick Start](#quick-start)
2. [Deployment Procedures](#deployment-procedures)
3. [Monitoring & Health Checks](#monitoring--health-checks)
4. [Daily Operations](#daily-operations)
5. [Troubleshooting](#troubleshooting)
6. [Maintenance Procedures](#maintenance-procedures)
7. [Emergency Procedures](#emergency-procedures)

---

## 🚀 QUICK START

### First Time Deployment

```bash
# 1. Run deployment script
./scripts/deploy_production.sh production

# 2. Monitor health
./scripts/health_check.sh --watch

# 3. Check API documentation
open http://localhost:8000/docs
```

### Quick Status Check

```bash
# Check application health
./scripts/health_check.sh

# Check if running
pgrep -f "uvicorn app.main:app"

# Check health endpoint
curl http://localhost:8000/api/v1/health
```

---

## 📦 DEPLOYMENT PROCEDURES

### Initial Deployment

**Prerequisites:**
- PostgreSQL database running
- Python 3.14+ installed
- Database schema created (38 tables)

**Steps:**

1. **Verify Database**
   ```bash
   # Check database connection
   psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT 1;"

   # Check table count
   psql -h localhost -p 5432 -U sheriftito -d psychsync -c \
     "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';"
   # Expected: 38
   ```

2. **Verify Migration Version**
   ```bash
   alembic current
   # Expected: 016_add_jsonb_gin_indexes (head)
   ```

3. **Run Deployment Script**
   ```bash
   ./scripts/deploy_production.sh production
   ```

4. **Verify Deployment**
   ```bash
   ./scripts/health_check.sh
   ```

### Automated Deployment

The deployment script (`deploy_production.sh`) automates:

- ✅ Pre-deployment checks (Python, database, migrations)
- ✅ Database migration verification
- ✅ Application startup (4 workers)
- ✅ Health checks (with retries)
- ✅ Smoke tests (regression tests)

**Output:**
- Application PID: `logs/application.pid`
- Application logs: `logs/application.log`
- Test logs: `logs/smoke_tests.log`

### Manual Deployment (If Script Fails)

```bash
# 1. Create logs directory
mkdir -p logs

# 2. Start application manually
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info \
  > logs/application.log 2>&1 &

# 3. Save PID
echo $! > logs/application.pid

# 4. Monitor startup
tail -f logs/application.log

# 5. Run health check
./scripts/health_check.sh
```

---

## 📊 MONITORING & HEALTH CHECKS

### Health Check Script

**Basic Usage:**
```bash
# Single health check
./scripts/health_check.sh

# Watch mode (continuous monitoring)
./scripts/health_check.sh --watch

# Verbose output
./scripts/health_check.sh --verbose
```

**Health Checks Performed:**
- ✅ Application process running
- ✅ HTTP health endpoint responding
- ✅ Database connection
- ✅ Memory usage
- ✅ Recent log errors

### Manual Health Checks

**Check Application Process:**
```bash
pgrep -f "uvicorn app.main:app"
ps aux | grep "uvicorn app.main:app"
```

**Check HTTP Endpoint:**
```bash
# Basic health check
curl http://localhost:8000/api/v1/health

# Detailed health status
curl -s http://localhost:8000/api/v1/health | jq .

# Response time
time curl http://localhost:8000/api/v1/health
```

**Check Database:**
```bash
# Connection test
psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT 1;"

# Table count
psql -h localhost -p 5432 -U sheriftito -d psychsync -c \
  "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';"

# Active connections
psql -h localhost -p 5432 -U sheriftito -d psychsync -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname = 'psychsync';"
```

### Log Monitoring

**View Application Logs:**
```bash
# Follow logs in real-time
tail -f logs/application.log

# View last 100 lines
tail -100 logs/application.log

# Search for errors
grep -i "error" logs/application.log

# Search for warnings
grep -i "warning" logs/application.log
```

**Log Analysis:**
```bash
# Count errors in last hour
grep "$(date '+%Y-%m-%d %H')" logs/application.log | grep -i "error" | wc -l

# Find recent errors
tail -1000 logs/application.log | grep -i "error" | tail -20

# Check for slow queries
grep "slow query" logs/application.log
```

---

## 🔧 DAILY OPERATIONS

### Morning Checklist

- [ ] Run health check: `./scripts/health_check.sh`
- [ ] Check logs for overnight errors
- [ ] Verify database connection
- [ ] Check disk space
- [ ] Review CI/CD workflow status

### Evening Checklist

- [ ] Run health check
- [ ] Check error counts
- [ ] Backup database (if automated backup not running)
- [ ] Review daily metrics
- [ ] Document any issues

### Regular Maintenance Tasks

**Daily:**
- Health check verification
- Log review for errors
- Disk space check

**Weekly:**
- Database backup verification
- Performance metrics review
- Security scan review
- Log rotation check

**Monthly:**
- Database vacuum/analyze
- Index maintenance
- Security updates review
- Capacity planning review

---

## 🚨 TROUBLESHOOTING

### Common Issues

#### 1. Application Won't Start

**Symptoms:**
- Process not running after deployment
- "Address already in use" error
- Permission denied errors

**Solutions:**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
pkill -f "uvicorn app.main:app"

# Check logs for errors
tail -100 logs/application.log

# Try starting manually
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Database Connection Errors

**Symptoms:**
- "Connection refused" errors
- "Database does not exist" errors
- Authentication failures

**Solutions:**
```bash
# Verify PostgreSQL is running
pg_ctl status
# or
brew services list | grep postgres

# Check database exists
psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT 1;"

# Verify CITEXT extension
psql -h localhost -p 5432 -U sheriftito -d psychsync -c \
  "SELECT extname FROM pg_extension WHERE extname = 'citext';"

# Restart PostgreSQL if needed
pg_ctl restart
# or
brew services restart postgresql
```

#### 3. Health Endpoint Failing

**Symptoms:**
- HTTP 500 errors
- Timeout errors
- Connection refused

**Solutions:**
```bash
# Check if application is running
pgrep -f "uvicorn app.main:app"

# Check logs for errors
tail -100 logs/application.log | grep -i error

# Test endpoint manually
curl -v http://localhost:8000/api/v1/health

# Restart application
pkill -f "uvicorn app.main:app"
./scripts/deploy_production.sh production
```

#### 4. High Memory Usage

**Symptoms:**
- Memory usage > 1GB
- System slowdown
- OOM errors

**Solutions:**
```bash
# Check memory usage
ps aux | grep "uvicorn app.main:app"

# Restart application
pkill -f "uvicorn app.main:app"
./scripts/deploy_production.sh production

# Reduce workers if needed (edit deploy_production.sh)
# Change --workers 4 to --workers 2
```

#### 5. High CPU Usage

**Symptoms:**
- CPU usage > 80%
- Slow response times
- System overload

**Solutions:**
```bash
# Check CPU usage
top -p $(pgrep -f "uvicorn app.main:app" | head -1)

# Check for slow queries
grep "slow query" logs/application.log

# Restart application
pkill -f "uvicorn app.main:app"
./scripts/deploy_production.sh production
```

### Debug Mode

**Enable Debug Logging:**
```bash
# Stop application
pkill -f "uvicorn app.main:app"

# Start with debug logging
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1 \
  --log-level debug \
  --reload
```

### Getting Help

**Check Documentation:**
- Operations Runbook: `docs/operations/DEPLOYMENT_RUNBOOK.md`
- Deployment Guide: `docs/COMPLETE_DEPLOYMENT_GUIDE.md`
- Troubleshooting: `docs/CI_CD_MONITORING_QUICK_REFERENCE.md`

**Useful Commands:**
```bash
# Show system status
./scripts/health_check.sh --verbose

# Check all logs
tail -100 logs/application.log

# Database diagnostics
psql -h localhost -p 5432 -U sheriftito -d psychsync -c \
  "SELECT * FROM pg_stat_activity WHERE datname = 'psychsync';"
```

---

## 🔄 MAINTENANCE PROCEDURES

### Database Maintenance

**Vacuum and Analyze:**
```bash
psql -h localhost -p 5432 -U sheriftito -d psychsync <<EOF
VACUUM ANALYZE;
EOF
```

**Check Table Sizes:**
```bash
psql -h localhost -p 5432 -U sheriftito -d psychsync <<EOF
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
EOF
```

**Check Index Usage:**
```bash
psql -h localhost -p 5432 -U sheriftito -d psychsync <<EOF
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan as index_scans
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC
LIMIT 10;
EOF
```

### Log Rotation

**Set Up Log Rotation:**
```bash
# Create logrotate config
sudo tee /etc/logrotate.d/psychsync <<EOF
/Users/sheriftito/Downloads/psychsync/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 sheriftito staff
}
EOF

# Test logrotate
sudo logrotate -d /etc/logrotate.d/psychsync
```

### Backup Procedures

**Database Backup:**
```bash
# Create backup
pg_dump -h localhost -p 5432 -U sheriftito -d psychsync \
  --clean --if-exists \
  --format=custom \
  -f backups/psychsync_backup_$(date +%Y%m%d_%H%M%S).dump

# List backups
ls -lh backups/

# Restore from backup
pg_restore -h localhost -p 5432 -U sheriftito -d psychsync \
  --clean --if-exists \
  backups/psychsync_backup_YYYYMMDD_HHMMSS.dump
```

**Application Backup:**
```bash
# Backup configuration
tar -czf backups/config_$(date +%Y%m%d).tar.gz .env* app/core/config/

# Backup scripts
tar -czf backups/scripts_$(date +%Y%m%d).tar.gz scripts/
```

---

## 🚨 EMERGENCY PROCEDURES

### Full Application Restart

```bash
# 1. Stop application
pkill -f "uvicorn app.main:app"

# 2. Verify stopped
pgrep -f "uvicorn app.main:app" || echo "Application stopped"

# 3. Check for errors in logs
tail -100 logs/application.log

# 4. Restart application
./scripts/deploy_production.sh production

# 5. Verify health
./scripts/health_check.sh
```

### Emergency Database Rollback

```bash
# 1. Stop application
pkill -f "uvicorn app.main:app"

# 2. Drop and recreate database
dropdb psychsync
createdb psychsync

# 3. Enable extensions
psql -h localhost -p 5432 -U sheriftito -d psychsync \
  -c "CREATE EXTENSION IF NOT EXISTS citext;"

# 4. Recreate schema
python3 scripts/create_production_schema.py

# 5. Stamp migration
alembic stamp 016_add_jsonb_gin_indexes

# 6. Restore data (if backup exists)
pg_restore -h localhost -p 5432 -U sheriftito -d psychsync \
  --clean --if-exists \
  backups/psychsync_backup_YYYYMMDD_HHMMSS.dump

# 7. Restart application
./scripts/deploy_production.sh production

# 8. Verify health
./scripts/health_check.sh
```

### Emergency Contact Procedures

**System Failure:**
1. Check health: `./scripts/health_check.sh --verbose`
2. Review logs: `tail -100 logs/application.log`
3. Attempt restart: `./scripts/deploy_production.sh production`
4. If unresolved, escalate

**Data Corruption:**
1. Stop application immediately
2. Do NOT make any database changes
3. Restore from most recent backup
4. Verify data integrity
5. Restart application

**Security Incident:**
1. Isolate affected systems
2. Preserve logs for investigation
3. Follow security incident response procedures
4. Document all actions taken

---

## 📈 PERFORMANCE OPTIMIZATION

### Application Performance

**Monitor Response Times:**
```bash
# Check average response time
curl -w "@-" -o /dev/null -s http://localhost:8000/api/v1/health <<EOF
    time_namelookup:  %{time_namelookup}\n
       time_connect:  %{time_connect}\n
    time_appconnect:  %{time_appconnect}\n
   time_pretransfer:  %{time_pretransfer}\n
      time_redirect:  %{time_redirect}\n
 time_starttransfer:  %{time_starttransfer}\n
                    ----------\n
         time_total:  %{time_total}\n
EOF
```

**Database Performance:**
```bash
# Check slow queries
psql -h localhost -p 5432 -U sheriftito -d psychsync <<EOF
SELECT
  query,
  calls,
  total_time,
  mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
EOF
```

### Capacity Planning

**Monitor Resources:**
```bash
# Disk space
df -h

# Memory usage
free -h

# CPU usage
top -bn1 | head -20

# Database size
psql -h localhost -p 5432 -U sheriftito -d psychsync -c \
  "SELECT pg_size_pretty(pg_database_size('psychsync'));"
```

---

## 📚 QUICK REFERENCE

### Essential Commands

```bash
# Deploy application
./scripts/deploy_production.sh production

# Check health
./scripts/health_check.sh

# Watch health (continuous)
./scripts/health_check.sh --watch

# View logs
tail -f logs/application.log

# Stop application
pkill -f "uvicorn app.main:app"

# Restart application
./scripts/deploy_production.sh production

# Database backup
pg_dump -h localhost -p 5432 -U sheriftito -d psychsync \
  --format=custom -f backups/backup.dump

# Database connection test
psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT 1;"
```

### File Locations

```
Application:        /Users/sheriftito/Downloads/psychsync
Logs:               logs/application.log
PID file:           logs/application.pid
Test logs:          logs/smoke_tests.log
Backups:            backups/
Deployment script:  scripts/deploy_production.sh
Health check:       scripts/health_check.sh
```

### URLs

```
Application:        http://localhost:8000
API Docs:           http://localhost:8000/docs
Health Check:       http://localhost:8000/api/v1/health
ReDoc:             http://localhost:8000/redoc
```

---

**Operations Guide Last Updated:** January 7, 2026
**Version:** 1.0.0
**Maintained By:** Operations Team
