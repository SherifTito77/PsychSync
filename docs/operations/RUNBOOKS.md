# Operations Runbooks
## Comprehensive Incident Response Procedures

**Version:** 1.0
**Last Updated:** November 25, 2025
**Maintained by:** Platform Team

---

## 📋 Table of Contents

1. [Incident Response Overview](#incident-response-overview)
2. [Severity Levels](#severity-levels)
3. [Common Incidents](#common-incidents)
4. [Emergency Procedures](#emergency-procedures)
5. [Communication Protocols](#communication-protocols)
6. [Post-Incident Procedures](#post-incident-procedures)

---

## 🚨 Incident Response Overview

### Incident Response Team

| Role | Primary | Backup | Contact |
|------|---------|--------|---------|
| **Incident Commander** | @platform-lead | @senior-devops | Slack @incident-commander |
| **Technical Lead** | @senior-backend | @senior-frontend | Slack @tech-lead |
| **Communications** | @product-manager | @engineering-lead | Slack @communications |
| **Security** | @security-lead | @senior-security | Slack @security-team |

### Response Time Objectives (RTO)

| Severity | Acknowledgment | Resolution |
|----------|----------------|------------|
| **Critical** | 5 minutes | 1 hour |
| **High** | 15 minutes | 4 hours |
| **Medium** | 30 minutes | 24 hours |
| **Low** | 2 hours | 1 week |

---

## 🎯 Severity Levels

### 🚨 SEVERITY 1 - Critical
**Definition**: Production service completely unavailable or security breach

**Examples**:
- Complete application outage
- Data breach or security incident
- Database corruption or complete unavailability
- Payment processing failure

**Response**:
- Immediate incident declaration
- All-hands on deck
- Executive communication required
- Customer communication required

### ⚠️ SEVERITY 2 - High
**Definition**: Significant functionality loss or performance degradation

**Examples**:
- Major feature unavailable (>50% users affected)
- Severe performance degradation (>5x slower response times)
- High error rates (>20% of requests failing)
- Database performance issues

**Response**:
- Incident declaration within 15 minutes
- Core team response
- Internal communication
- Customer notification if service impact

### 📋 SEVERITY 3 - Medium
**Definition**: Limited functionality loss or minor performance issues

**Examples**:
- Minor feature unavailable (<20% users affected)
- Moderate performance degradation (2-5x slower)
- Intermittent errors (5-20% of requests)
- Non-critical bugs

**Response**:
- Standard incident response
- Team-level communication
- Fix in normal release cycle if possible

### ℹ️ SEVERITY 4 - Low
**Definition**: Cosmetic issues or minor improvements

**Examples**:
- UI/UX issues
- Documentation errors
- Minor performance optimizations
- Non-critical feature requests

**Response**:
- Normal development process
- No immediate response required
- Address in next sprint

---

## 🔧 Common Incidents

### 1. Application Down

#### Symptoms
- All HTTP requests returning 5xx errors
- Health check endpoints failing
- Grafana shows application as down
- Customer reports of complete outage

#### Immediate Actions
```bash
# 1. Check application status
curl -f https://app.psychsync.com/health
curl -f https://api.psychsync.com/api/v1/health

# 2. Check application logs
docker-compose logs app --tail=100

# 3. Check system resources
docker stats
free -h
df -h

# 4. Check database connectivity
docker-compose exec db pg_isready
```

#### Troubleshooting Steps

**Step 1: Identify Scope**
- Is it frontend, backend, or both?
- Are all instances affected or just some?
- When did the issue start?

**Step 2: Check Recent Changes**
```bash
# Check recent deployments
kubectl rollout history deployment/psychsync-app  # Kubernetes
# or
docker-compose ps  # Docker Compose

# Check recent code changes
git log --oneline -10
```

**Step 3: Restart Services**
```bash
# Restart application
docker-compose restart app

# If using Kubernetes
kubectl rollout restart deployment/psychsync-app
```

**Step 4: Database Issues**
```bash
# Check database connection
docker-compose exec db psql -U postgres -d psychsync -c "SELECT 1;"

# Check database connections
docker-compose exec db psql -U postgres -d psychsync -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
docker-compose exec db psql -U postgres -d psychsync -c "SELECT pg_size_pretty(pg_database_size('psychsync'));"
```

**Step 5: Memory/CPU Issues**
```bash
# Check memory usage
free -h
docker stats --no-stream

# Check CPU usage
top
htop

# Check processes
ps aux | grep python
```

#### Escalation Criteria
- Issue persists > 15 minutes after restart
- Multiple services affected
- Database connectivity issues

### 2. High Error Rate

#### Symptoms
- Error rate > 5% for > 5 minutes
- Customers report specific errors
- Grafana shows spike in 5xx responses
- Sentry shows increased error volume

#### Immediate Actions
```bash
# 1. Check error rates
curl -s https://api.psychsync.com/metrics | grep 'http_requests_total{status=~"5.."'

# 2. Check recent errors in logs
docker-compose logs app --tail=500 | grep -i error

# 3. Check Sentry dashboard
# https://sentry.psychsync.com

# 4. Check system health
docker-compose exec app python scripts/health_check.py
```

#### Troubleshooting Steps

**Step 1: Identify Error Pattern**
- What errors are occurring?
- Which endpoints are affected?
- When did errors start?

**Step 2: Check Recent Deployments**
```bash
# Check deployment time vs error start time
kubectl get pods --show-labels
# or
docker ps
```

**Step 3: Database Issues**
```bash
# Check for slow queries
docker-compose exec db psql -U postgres -d psychsync -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC LIMIT 10;"

# Check database locks
docker-compose exec db psql -U postgres -d psychsync -c "
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
WHERE NOT blocked_locks.granted;"
```

**Step 4: External Dependencies**
```bash
# Check Redis connectivity
docker-compose exec redis redis-cli ping

# Check external API status
curl -I https://api.stripe.com/v1/
curl -I https://api.sendgrid.com/v3/
```

**Step 5: Resource Constraints**
```bash
# Check memory usage
free -h
docker stats

# Check disk space
df -h

# Check database size
docker-compose exec db psql -U postgres -d psychsync -c "SELECT pg_size_pretty(pg_database_size('psychsync'));"
```

#### Resolution Actions
- **Quick Fix**: Rollback recent deployment
- **Database**: Restart database connection pool
- **Memory**: Scale up application instances
- **External**: Circuit breaker for failing dependencies

### 3. Slow Performance

#### Symptoms
- P95 response time > 2 seconds for > 5 minutes
- Customer reports of slowness
- Database queries timing out
- Frontend loading slowly

#### Immediate Actions
```bash
# 1. Check response times
curl -w "@curl-format.txt" -o /dev/null -s "https://app.psychsync.com/"

# 2. Check database performance
docker-compose exec db psql -U postgres -d psychsync -c "
SELECT query, calls, total_time, mean_time, std_dev_time
FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 10;"

# 3. Check application performance
docker-compose exec app python scripts/performance_check.py
```

#### Troubleshooting Steps

**Step 1: Identify Bottleneck**
- Database queries?
- External API calls?
- Application processing?
- Network latency?

**Step 2: Database Performance**
```bash
# Check slow queries
docker-compose exec db psql -U postgres -d psychsync -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY mean_time DESC;"

# Check missing indexes
docker-compose exec db psql -U postgres -d psychsync -c "
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public';"

# Check table sizes
docker-compose exec db psql -U postgres -d psychsync -c "
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

**Step 3: Application Performance**
```bash
# Profile memory usage
docker-compose exec app python scripts/profile_memory_usage.py

# Check active processes
docker-compose exec app ps aux

# Check connection pool status
docker-compose exec app python scripts/check_connection_pool.py
```

**Step 4: Network Issues**
```bash
# Check network latency
ping app.psychsync.com

# Check DNS resolution
nslookup app.psychsync.com

# Check SSL certificate
openssl s_client -connect app.psychsync.com:443 -servername app.psychsync.com
```

#### Optimization Actions
- **Database**: Add indexes, optimize queries, increase connection pool
- **Application**: Add caching, optimize algorithms, scale instances
- **Network**: Enable compression, use CDN, optimize assets

### 4. Database Issues

#### Symptoms
- Database connection failures
- Slow query performance
- Database out of disk space
- Connection pool exhaustion

#### Immediate Actions
```bash
# 1. Check database status
docker-compose exec db pg_isready

# 2. Check connection count
docker-compose exec db psql -U postgres -d psychsync -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Check disk space
df -h
docker-compose exec db psql -U postgres -d psychsync -c "SELECT pg_size_pretty(pg_database_size('psychsync'));"
```

#### Troubleshooting Steps

**Step 1: Connection Issues**
```bash
# Check max connections
docker-compose exec db psql -U postgres -d psychsync -c "SHOW max_connections;"

# Check active connections
docker-compose exec db psql -U postgres -d psychsync -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"

# Check long-running queries
docker-compose exec db psql -U postgres -d psychsync -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"
```

**Step 2: Performance Issues**
```bash
# Check query statistics
docker-compose exec db psql -U postgres -d psychsync -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Check table bloat
docker-compose exec db psql -U postgres -d psychsync -c "
SELECT schemaname, tablename,
       ROUND(CASE WHEN otta=0 THEN 0.0 ELSE sml.relpages/otta::numeric END,1) AS tbloat,
       CASE WHEN relpages < otta THEN 0 ELSE relpages::bigint - otta END AS wastedpages
FROM (
  SELECT
    schemaname, tablename, cc.reltuples, cc.relpages, bs,
    CEIL((cc.reltuples*((datahdr+ma-
        (CASE WHEN datahdr%ma=0 THEN ma ELSE datahdr%ma END))+nullhdr2+4))/(bs-20::float)) AS otta
  FROM (
    SELECT
      ma,bs,schemaname,tablename,
      (datawidth+(hdr+ma-(CASE WHEN hdr%ma=0 THEN ma ELSE hdr%ma END)))::numeric AS datahdr,
      (maxfracsum*(nullhdr+ma-(CASE WHEN nullhdr%ma=0 THEN ma ELSE nullhdr%ma END))) AS nullhdr2
    FROM (
      SELECT
        schemaname, tablename, hdr, ma, bs,
        SUM((1-null_frac)*avg_width) AS datawidth,
        MAX(null_frac) AS maxfracsum,
        hdr+(
          SELECT 1+COUNT(*)*(8-CASE WHEN hdr%ma=0 THEN ma ELSE hdr%ma END)
          FROM pg_stats s2
          WHERE null_frac<>0 AND s2.schemaname=s.schemaname AND s2.tablename=s.tablename
        ) AS nullhdr
      FROM pg_stats s, (
        SELECT
          (SELECT current_setting('block_size')::numeric) AS bs,
          CASE WHEN substring(v,12,3) IN ('8.0','8.1','8.2') THEN 27 ELSE 23 END AS hdr,
          CASE WHEN v ~ 'mingw32' THEN 8 ELSE 4 END AS ma
        FROM (SELECT version() AS v) AS foo
      ) AS constants
      GROUP BY 1,2,3,4,5
    ) AS foo
  ) AS rs
  JOIN pg_class cc ON cc.relname = rs.tablename
  JOIN pg_namespace nn ON cc.relnamespace = nn.oid AND nn.nspname = rs.schemaname AND nn.nspname <> 'information_schema'
) AS sml
WHERE sml.relpages > otta;"
```

**Step 3: Disk Space Issues**
```bash
# Check available disk space
df -h

# Find large files
find /var/lib/postgresql -type f -size +100M -exec ls -lh {} \;

# Check table sizes
docker-compose exec db psql -U postgres -d psychsync -c "
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

#### Resolution Actions
- **Connections**: Increase max_connections, close idle connections
- **Performance**: Optimize queries, add indexes, VACUUM ANALYZE
- **Disk Space**: Archive old data, increase storage, clean up logs

### 5. Security Incidents

#### Immediate Response
```bash
# 1. Isolate affected systems
docker-compose stop app  # If compromise suspected

# 2. Enable audit logging
docker-compose exec db psql -U postgres -d psychsync -c "ALTER SYSTEM SET log_statement = 'all';"
docker-compose exec db psql -U postgres -d psychsync -c "SELECT pg_reload_conf();"

# 3. Check for suspicious activity
docker-compose logs app | grep -i "failed\|error\|unauthorized"

# 4. Review recent authentication
docker-compose exec db psql -U postgres -d psychsync -c "
SELECT email, last_login_at, failed_login_attempts
FROM users
WHERE last_login_at > NOW() - INTERVAL '24 hours'
  AND failed_login_attempts > 3;"
```

#### Security Response Checklist
- [ ] Contain the incident
- [ ] Preserve evidence
- [ ] Notify security team
- [ ] Assess impact
- [ ] Communicate with stakeholders
- [ ] Document timeline
- [ ] Implement fixes
- [ ] Post-mortem analysis

---

## 🆘 Emergency Procedures

### Immediate Response Checklist

1. **Acknowledge Alert** (within RTO)
2. **Create Incident Channel** (`#incident-TIMESTAMP`)
3. **Assemble Response Team**
4. **Assess Impact** (who/what affected)
5. **Communicate Status** (internal/external)
6. **Implement Fix** (rollback or fix forward)
7. **Verify Resolution**
8. **Document Actions**

### Emergency Contacts

| Service | Contact | Escalation |
|---------|---------|------------|
| **Platform Lead** | +1-555-0101 | @platform-lead |
| **Security** | +1-555-0202 | @security-team |
| **Database** | +1-555-0303 | @dba-team |
| **Infrastructure** | +1-555-0404 | @infra-team |
| **Executive** | +1-555-0505 | @exec-team |

### Emergency Access

#### Production Access
```bash
# SSH to production servers
ssh -i ~/.ssh/psychsync-prod.pem user@prod.psychsync.com

# Database access
psql -h prod-db.psychsync.com -U postgres -d psychsync

# Kubernetes access
kubectl config use-context psychsync-prod
kubectl get pods -n psychsync
```

#### Emergency Rollback
```bash
# Rollback to previous deployment
kubectl rollout undo deployment/psychsync-app

# Or rollback to specific revision
kubectl rollout undo deployment/psychsync-app --to-revision=2

# Verify rollback
kubectl rollout status deployment/psychsync-app
```

### Disaster Recovery

#### Site Recovery
```bash
# 1. Deploy to backup region
kubectl apply -f k8s/backup-region/

# 2. Restore database from backup
python scripts/disaster_recovery.py --restore-from-backup

# 3. Update DNS
# Update Route53 to point to backup region

# 4. Verify services
curl -f https://backup.psychsync.com/health
```

#### Data Recovery
```bash
# Restore from most recent backup
python scripts/restore_database.py --backup-file latest.sql.gz

# Point-in-time recovery
python scripts/restore_database.py --point-in-time "2025-11-25 14:30:00"

# Verify data integrity
python scripts/verify_data_integrity.py
```

---

## 📢 Communication Protocols

### Internal Communication

#### Incident Channel Naming
- Format: `#incident-YYYY-MM-DD-HHMM`
- Example: `#incident-2025-11-25-1430`
- Include severity in topic: `[SEV1]`, `[SEV2]`, etc.

#### Status Updates
- **Every 15 minutes** for SEV1 incidents
- **Every 30 minutes** for SEV2 incidents
- **Every hour** for SEV3 incidents

#### Update Template
```
🚨 STATUS UPDATE
Time: HH:MM UTC
Severity: SEV1/2/3/4
Impact: Description of impact
Actions: What we're doing
ETA: When we expect resolution
Next Update: HH:MM UTC
```

### External Communication

#### Customer Communication
- **SEV1**: Immediate notification
- **SEV2**: Within 30 minutes
- **SEV3**: Within 2 hours

#### Communication Channels
- **Status Page**: https://status.psychsync.com
- **Twitter**: @psychsyncstatus
- **Email**: Customer notifications
- **In-App**: Banner notifications

#### Customer Notification Template
```
🔒 PsychSync Service Update

Issue: [Brief description]
Status: [Investigating/Mitigated/Resolved]
Impact: [What's affected]
Timeline: [Started at HH:MM UTC]
Actions: [What we're doing]
Next Update: [HH:MM UTC]

We apologize for any inconvenience.
```

### Executive Updates

#### For SEV1/SEV2 Incidents
- **Immediate email** to executives
- **Slack notification** in #exec-updates
- **Phone call** if critical customer impact

#### Executive Update Template
```
🚨 EXECUTIVE ALERT

Incident: [Title]
Severity: SEV1/SEV2
Started: HH:MM UTC
Impact: [Revenue/Customer/Operations]
Team: [Who's responding]
Status: [Current status]
ETA: [Resolution estimate]
Customer Impact: [Number of users affected]
Communication: [What we've told customers]
```

---

## 📋 Post-Incident Procedures

### Incident Review Timeline

#### Immediate (0-1 hours after resolution)
- Verify system stability
- Document initial timeline
- Preserve logs and evidence

#### Short-term (1-24 hours)
- Create incident report draft
- Schedule incident review meeting
- Begin root cause analysis

#### Medium-term (1-7 days)
- Complete incident report
- Implement preventive measures
- Update runbooks and procedures

#### Long-term (1-4 weeks)
- Review process improvements
- Update training materials
- Architectural improvements if needed

### Incident Report Template

```markdown
# Incident Report: [Title]

## Executive Summary
[Brief 2-3 sentence summary for executives]

## Incident Details
- **Start Time**: YYYY-MM-DD HH:MM UTC
- **End Time**: YYYY-MM-DD HH:MM UTC
- **Duration**: X hours Y minutes
- **Severity**: SEV1/2/3/4
- **Incident Commander**: [Name]
- **Technical Lead**: [Name]

## Impact Assessment
- **Customers Affected**: [Number/Percentage]
- **Revenue Impact**: [If applicable]
- **Service Impact**: [What was down/degraded]
- **Data Impact**: [Any data loss/corruption]

## Timeline
[Detailed chronological timeline of events]

## Root Cause Analysis
[Technical deep dive of what happened and why]

## Resolution
[What we did to fix it]

## Preventive Measures
[What we'll do to prevent recurrence]

## Lessons Learned
[What we learned from this incident]

## Action Items
- [ ] [Action item 1] - [Owner] - [Due Date]
- [ ] [Action item 2] - [Owner] - [Due Date]
```

### Blameless Post-Mortem Process

#### Principles
1. **Focus on systems, not individuals**
2. **Identify systemic weaknesses**
3. **Encourage honest reporting**
4. **Promote learning culture**

#### Questions to Ask
- What happened?
- Why did it happen?
- What could we have done differently?
- How can we prevent this in the future?
- What do we need to learn?

### Continuous Improvement

#### Monthly Incident Review
- Review all incidents from past month
- Identify patterns and trends
- Update procedures based on learnings

#### Quarterly Process Review
- Evaluate incident response effectiveness
- Review RTO/SLA compliance
- Update runbooks and documentation

#### Annual Architecture Review
- Review systemic issues
- Plan architectural improvements
- Budget for reliability improvements

---

## 📊 Metrics and KPIs

### Incident Response Metrics
- **MTTR** (Mean Time to Resolution)
- **MTTA** (Mean Time to Acknowledge)
- **Incident Frequency**
- **Availability** (Uptime percentage)

### Performance Targets
- **MTTA**: < 5 minutes (SEV1), < 15 minutes (SEV2)
- **MTTR**: < 1 hour (SEV1), < 4 hours (SEV2)
- **Availability**: 99.9% uptime
- **P95 Response Time**: < 2 seconds

### Monitoring Dashboard
- [Incident Metrics Dashboard](https://grafana.psychsync.com/d/incident-metrics)
- [Availability Dashboard](https://grafana.psychsync.com/d/availability)
- [Performance Dashboard](https://grafana.psychsync.com/d/performance)

---

## 📞 Escalation Procedures

### When to Escalate
- Issue persists > 50% of RTO
- Uncertainty about root cause
- Need additional expertise
- Customer impact increases

### Escalation Process
1. **Contact backup** for current role
2. **Escalate to team lead** if backup unavailable
3. **Escalate to management** if team lead unavailable
4. **Activate emergency contacts** for critical incidents

### Escalation Contacts
```
Level 1: Team Members
Level 2: Team Leads
Level 3: Engineering Manager
Level 4: CTO/VP Engineering
Level 5: CEO (SEV1 only)
```

---

## 🔄 Runbook Maintenance

### Regular Updates
- **Monthly**: Review and update procedures
- **Quarterly**: Full runbook audit
- **Annually**: Major review and restructure

### Change Process
1. Create issue for runbook update
2. Draft changes with team input
3. Review with incident commander
4. Test new procedures
5. Update documentation
6. Train team on changes

### Version Control
- All runbooks in Git repository
- Semantic versioning (v1.0.0, v1.0.1, etc.)
- Change log for each update
- Rollback capability for procedures

---

## 📚 Additional Resources

### Training Materials
- [Incident Response Training](../training/incident-response.md)
- [Security Incident Handling](../training/security-incidents.md)
- [Database Troubleshooting](../training/database-troubleshooting.md)

### External References
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Troubleshooting Guide](https://docs.docker.com/config/troubleshooting/)
- [Kubernetes Debugging Guide](https://kubernetes.io/docs/tasks/debug-application-cluster/)

### Tools and Utilities
- [Health Check Script](../scripts/health_check.py)
- [Performance Monitor](../scripts/performance_monitor.py)
- [Database Diagnostics](../scripts/database_diagnostics.py)

---

## 🎯 Success Criteria

A successful incident response includes:
- ✅ Quick acknowledgment within RTO
- ✅ Clear communication throughout
- ✅ Effective resolution of issue
- ✅ Minimal customer impact
- ✅ Thorough documentation
- ✅ Preventive measures implemented
- ✅ Team learns from incident

---

**Remember: Every incident is an opportunity to improve our systems and processes.**

---

*Last Updated: November 25, 2025*
*Next Review: December 25, 2025*
*Maintainer: Platform Team*
