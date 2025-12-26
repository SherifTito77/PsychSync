# PsychSync Incident Response Runbook

## 🚨 **CRITICAL INCIDENT PROCEDURES**

### **Severity Levels**
- **CRITICAL** (P0): Service completely down, data loss, security breach
- **HIGH** (P1): Major functionality broken, significant performance degradation
- **MEDIUM** (P2): Partial functionality affected, minor performance issues
- **LOW** (P3): Cosmetic issues, minor bugs

---

## 📋 **INCIDENT CHECKLIST**

### **IMMEDIATE ACTIONS (First 5 Minutes)**

#### ✅ **Step 1: Acknowledge Incident**
- [ ] Create incident in monitoring system
- [ ] Set severity level
- [ ] Notify on-call team via Slack/PagerDuty
- [ ] Create incident channel (#incident-psychsync-YYYY-MM-DD-HHMM)

#### ✅ **Step 2: Initial Assessment**
- [ ] Check application status: `curl -f http://localhost:8000/health`
- [ ] Check database connectivity: `docker exec psychsync pg_isready`
- [ ] Check Redis status: `docker exec psychsync redis-cli ping`
- [ ] Check recent deployments: `git log --oneline -5`
- [ ] Check error logs: `docker logs psychsync --tail 100`

#### ✅ **Step 3: Gather Context**
- [ ] When did the issue start?
- [ ] What changed recently? (deployment, config, etc.)
- [ ] Which users/teams are affected?
- [ ] What's the business impact?

---

## 🔧 **DIAGNOSTIC PROCEDURES**

### **Application Issues**

#### **Application Down/Unresponsive**
```bash
# Check container status
docker ps | grep psychsync

# Check application health
curl -v http://localhost:8000/health

# Check application logs
docker logs psychsync --tail 200 | grep -i error

# Check resource usage
docker stats psychsync

# Restart application if needed
docker restart psychsync
```

#### **High Error Rate**
```bash
# Check recent error rates
curl "http://localhost:9090/api/v1/query_range?query=rate(http_requests_total{status=~'5..'}[5m])&start=$(date -d '10 minutes ago' +%s)&end=$(date +%s)"

# Check application logs for errors
docker logs psychsync --since=10m | grep -i error | tail -20

# Check database query performance
docker exec psychsync psql -U $DB_USER -d $DB_NAME -c "
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"
```

#### **Performance Issues**
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/v1/users/me"

# Check database connections
docker exec psychsync psql -U $DB_USER -d $DB_NAME -c "
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE state = 'active';
"

# Check slow queries
docker exec psychsync psql -U $DB_USER -d $DB_NAME -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC
LIMIT 10;
"
```

### **Database Issues**

#### **Database Connection Problems**
```bash
# Test database connection
docker exec psychsync psql -U $DB_USER -d $DB_NAME -c "SELECT 1;"

# Check connection count
docker exec psychsync psql -U $DB_USER -d $DB_NAME -c "
SELECT count(*) as total_connections,
       count(*) FILTER (WHERE state = 'active') as active_connections,
       count(*) FILTER (WHERE state = 'idle') as idle_connections
FROM pg_stat_activity;
"

# Check database locks
docker exec psychsync psql -U $DB_USER -d $DB_NAME -c "
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
"
```

#### **Database Performance**
```bash
# Check table sizes
docker exec psychsync psql -U $DB_USER -d $DB_NAME -c "
SELECT schemaname,
       tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
"

# Check index usage
docker exec psychsync psql -U $DB_USER -d $DB_NAME -c "
SELECT schemaname,
       tablename,
       indexname,
       idx_scan,
       idx_tup_read,
       idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC
LIMIT 10;
"
```

### **Redis Issues**

#### **Redis Connection Problems**
```bash
# Check Redis status
docker exec psychsync redis-cli ping

# Check Redis memory usage
docker exec psychsync redis-cli info memory

# Check Redis connections
docker exec psychsync redis-cli info clients

# Check Redis slow log
docker exec psychsync redis-cli slowlog get 10
```

---

## 🚀 **RECOVERY PROCEDURES**

### **Application Recovery**

#### **Quick Restart**
```bash
# Graceful shutdown
docker stop psychsync

# Start application
docker start psychsync

# Verify health
sleep 10
curl -f http://localhost:8000/health
```

#### **Full Application Reset**
```bash
# Stop application
docker stop psychsync

# Remove container
docker rm psychsync

# Pull latest image
docker pull psychsync:latest

# Start fresh container
docker run -d \
  --name psychsync \
  --restart unless-stopped \
  -p 8000:8000 \
  -e DATABASE_URL="$DATABASE_URL" \
  -e REDIS_URL="$REDIS_URL" \
  -e SECRET_KEY="$SECRET_KEY" \
  -e ENVIRONMENT="production" \
  --network psychsync-network \
  psychsync:latest
```

### **Database Recovery**

#### **Database Rollback**
```bash
# Check current migration version
docker exec psychsync alembic current

# Rollback to previous version
docker exec psychsync alembic downgrade -1

# Verify rollback
docker exec psychsync alembic current
```

#### **Database Restore from Backup**
```bash
# List available backups
ls -la /backups/database_backup_*.sql

# Restore most recent backup
docker exec -i postgres psql -U $DB_USER -d $DB_NAME < /backups/database_backup_latest.sql

# Verify data integrity
docker exec psychsync psql -U $DB_USER -d $DB_NAME -c "SELECT count(*) FROM users;"
```

---

## 📊 **ESCALATION PROCEDURES**

### **When to Escalate**
- Incident lasts > 30 minutes without resolution
- Multiple systems affected simultaneously
- Security breach suspected
- Data loss or corruption confirmed
- Customer impact > 100 users

### **Escalation Contacts**
- **Team Lead**: [Team Lead Name] - [Phone/Slack]
- **Engineering Manager**: [Manager Name] - [Phone/Slack]
- **CTO**: [CTO Name] - [Phone/Slack]
- **Security Team**: security@psychsync.com

### **Escalation Communication**
```bash
# Slack message template
🚨 ESCALATION REQUIRED 🚨
Incident: [Incident Name]
Severity: [P0/P1/P2/P3]
Duration: [X minutes]
Impact: [Number of users affected]
Team Notified: [@mentions]
```

---

## 📝 **POST-INCIDENT PROCEDURES**

### **Immediate Actions (After Resolution)**
- [ ] Verify fix is stable for 30 minutes
- [ ] Update incident status to "Resolved"
- [ ] Communicate resolution to stakeholders
- [ ] Begin post-mortem process

### **Post-Mortem Requirements**
- [ ] Timeline of events
- [ ] Root cause analysis
- [ ] Impact assessment
- [ ] Resolution details
- [ ] Prevention measures
- [ ] Follow-up actions

### **Post-Mortem Template**
```markdown
# Post-Mortem: [Incident Title]

## Summary
[Brief description of incident and impact]

## Timeline
- [Time]: Event description
- [Time]: Another event
- [Time]: Resolution

## Root Cause
[Detailed analysis of what caused the incident]

## Impact
- Users affected: [Number]
- Downtime: [Duration]
- Revenue impact: [If applicable]

## Resolution
[Steps taken to resolve the incident]

## Prevention
[Measures to prevent recurrence]

## Action Items
- [ ] [Owner] - [Action item 1]
- [ ] [Owner] - [Action item 2]
```

---

## 🔍 **MONITORING COMMANDS**

### **Application Health**
```bash
# Health check
curl -f http://localhost:8000/health

# Metrics check
curl http://localhost:8000/metrics

# Application logs (real-time)
docker logs -f psychsync

# Error logs only
docker logs psychsync 2>&1 | grep -i error
```

### **System Resources**
```bash
# Container resource usage
docker stats psychsync

# Host resource usage
top
htop
iostat -x 1

# Disk space
df -h

# Memory usage
free -h
```

### **Network**
```bash
# Check application port
netstat -tlnp | grep :8000

# Test application connectivity
curl -v http://localhost:8000/api/v1/users/me

# Check for port conflicts
ss -tulpn | grep :8000
```

---

## 🚨 **EMERGENCY COMMANDS**

### **Immediate Application Restart**
```bash
# Force restart application
docker restart psychsync

# If restart fails, recreate container
docker stop psychsync
docker rm psychsync
docker run -d \
  --name psychsync \
  --restart unless-stopped \
  -p 8000:8000 \
  -e DATABASE_URL="$DATABASE_URL" \
  -e REDIS_URL="$REDIS_URL" \
  -e SECRET_KEY="$SECRET_KEY" \
  -e ENVIRONMENT="production" \
  --network psychsync-network \
  psychsync:latest
```

### **Database Emergency Recovery**
```bash
# Check database status
docker exec postgres pg_isready

# Emergency database restart
docker restart postgres

# If database is corrupted, restore from backup
docker exec -i postgres psql -U $DB_USER -d $DB_NAME < /backups/emergency_backup.sql
```

### **Redis Emergency Recovery**
```bash
# Check Redis status
docker exec redis redis-cli ping

# Emergency Redis restart
docker restart redis

# Clear Redis cache if corrupted
docker exec redis redis-cli FLUSHALL
```

---

*This runbook should be reviewed and updated quarterly. All team members should be familiar with these procedures and participate in regular incident response drills.*