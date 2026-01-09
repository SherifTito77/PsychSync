# 🚨 PsychSync Incident Response Runbook

**Version**: 1.0
**Date**: 2025-12-27
**Purpose**: Operational procedures for incident detection, response, and recovery

---

## 📋 Table of Contents

1. [Incident Classification](#incident-classification)
2. [Immediate Response Procedures](#immediate-response-procedures)
3. [Security Incidents](#security-incidents)
4. [Application Incidents](#application-incidents)
5. [Infrastructure Incidents](#infrastructure-incidents)
6. [Data Incidents](#data-incidents)
7. [Post-Incident Procedures](#post-incident-procedures)
8. [Communication Templates](#communication-templates)

---

## 🎯 Incident Classification

### Severity Levels

#### P0 - CRITICAL (Total Outage)
**Definition**: Complete system outage, all users affected

**Examples**:
- All application pods crashed
- Database completely unavailable
- Complete API failure (500 errors for all endpoints)
- Security breach with confirmed data exfiltration

**Response Time**: ≤ 15 minutes
**Escalation**: Immediate to CTO, CEO

#### P1 - HIGH (Major Impact)
**Definition**: Critical functionality broken, significant user impact

**Examples**:
- Authentication/authorization failure
- API error rate > 50%
- Database performance degraded (queries timing out)
- Security incident with potential impact

**Response Time**: ≤ 1 hour
**Escalation**: Tech Lead, On-Call

#### P2 - MEDIUM (Partial Degradation)
**Definition**: Partial system degradation, some users affected

**Examples**:
- API error rate 10-50%
- Non-critical features unavailable
- Elevated response times (> 2x baseline)
- Performance degradation

**Response Time**: ≤ 4 hours
**Escalation**: On-Call Engineer

#### P3 - LOW (Minor Issue)
**Definition**: Minor issues, limited user impact

**Examples**:
- API error rate < 10%
- UI bugs, cosmetic issues
- Documentation errors
- Minor performance issues

**Response Time**: ≤ 1 business day
**Escalation**: Team Lead

---

## ⚡ Immediate Response Procedures

### Step 1: Detection and Acknowledgment (0-5 min)

```bash
# Check alerting dashboard
# Verify incident scope and impact

# Create incident channel
# (Slack/Teams: #incident-psychsync-YYYY-MM-DD)

# Assign incident commander
# Declare severity level
```

**Initial Assessment Checklist**:
- [ ] What is the primary symptom?
- [ ] When did it start?
- [ ] How many users affected?
- [ ] Is this a regression or new issue?
- [ ] Any recent deployments?

### Step 2: Gather Initial Data (5-15 min)

```bash
# 1. Check system status
kubectl get pods -n psychsync
kubectl get nodes
kubectl top pods -n psychsync

# 2. Check recent deployments
kubectl rollout history deployment/psychsync -n psychsync
kubectl get events -n psychsync --sort-by='.lastTimestamp' | tail -50

# 3. Check application logs
kubectl logs -n psychsync -l app=psychsync --since=15m | grep -i error

# 4. Check metrics
kubectl exec -n psychsync deployment/psychsync -- curl -s http://localhost:8000/metrics | grep error

# 5. Check database
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "SELECT count(*) FROM users;"
```

`★ Insight ─────────────────────────────────────`
The first 15 minutes of an incident are critical. Establishing a consistent initial data gathering process prevents diagnostic thrashing and ensures all responders have the same baseline information. The `--since=15m` flag is specifically chosen to capture logs from before the incident started.
`─────────────────────────────────────────────────`

### Step 3: Establish Impact Scope (15-30 min)

**Metrics to Check**:

```bash
# Request rate
kubectl exec -n psychsync deployment/psychsync -- curl -s http://localhost:8000/metrics | grep http_requests_total

# Error rate
kubectl exec -n psychsync deployment/psychsync -- curl -s http://localhost:8000/metrics | grep http_errors_total

# Latency
kubectl exec -n psychsync deployment/psychsync -- curl -s http://localhost:8000/metrics | grep http_request_duration_seconds

# Database performance
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  SELECT query, calls, total_time, mean_time
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT 10;
"
```

### Step 4: Mitigation (30+ min)

Based on incident type, follow specific procedures in sections below.

---

## 🔒 Security Incidents

### Confirmed Data Breach

**Immediate Actions**:

```bash
# 1. Isolate affected systems
kubectl scale deployment psychsync -n psychsync --replicas=0

# 2. Enable maintenance mode
kubectl annotate ingress psychsync-ingress -n psychsync nginx.ingress.kubernetes.io/maintenance-mode="true"

# 3. Preserve evidence
kubectl logs -n psychsync -l app=psychsync > incident-$(date +%Y%m%d-%H%M%S).log
kubectl get pods -n psychsync -o yaml > incident-pods-$(date +%Y%m%d-%H%M%S).yaml

# 4. Enable audit logging
kubectl apply -f deploy/audit-logging-enable.yaml
```

**Investigation Steps**:

```bash
# 1. Check authentication logs
kubectl logs -n psychsync -l app=psychsync --since=24h | grep -i "auth\|login\|token"

# 2. Check database access
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  SELECT * FROM audit_logs
  WHERE action IN ('SELECT', 'UPDATE', 'DELETE')
  ORDER BY timestamp DESC
  LIMIT 100;
"

# 3. Check for suspicious patterns
kubectl logs -n psychsync -l app=psychsync --since=24h | grep -E "(sql injection|xss|path traversal|command injection)"

# 4. Export audit logs
kubectl exec -n psychsync postgres-0 -- pg_dump -U postgres psychsync -t audit_logs > audit-export-$(date +%Y%m%d).sql
```

**Recovery Steps**:

```bash
# 1. Rotate all secrets
kubectl delete secret psychsync-secrets -n psychsync
./scripts/rotate-secrets.sh

# 2. Force password reset for all users
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  UPDATE users SET password_reset_required = true;
"

# 3. Rebuild and redeploy with clean image
git tag v$(date +%Y%m%d)-security-fix
git push origin v$(date +%Y%m%d)-security-fix

# 4. Verify image integrity
./scripts/verify-quick.sh ghcr.io/your-org/psychsync:v$(date +%Y%m%d)-security-fix

# 5. Gradual rollout
kubectl set image deployment/psychsync psychsync=ghcr.io/your-org/psychsync:v$(date +%Y%m%d)-security-fix -n psychsync
kubectl rollout status deployment/psychsync -n psychsync
```

### Suspected Attack Pattern

**Detection Commands**:

```bash
# 1. Check for SQL injection attempts
kubectl logs -n psychsync -l app=psychsync --since=1h | grep -iE "(drop table|union select|' or 1=1|; delete)"

# 2. Check for XSS attempts
kubectl logs -n psychsync -l app=psychsync --since=1h | grep -iE "<script|javascript:|onerror="

# 3. Check for path traversal
kubectl logs -n psychsync -l app=psychsync --since=1h | grep -iE "\.\./|\.\.\|%2e%2e"

# 4. Check rate limiting violations
kubectl logs -n psychsync -l app=psychsync --since=1h | grep -i "rate limit"

# 5. Check spotlighting alerts
kubectl logs -n psychsync -l app=psychsync --since=1h | grep -iE "spotlight|untrusted content|blocked"
```

**Leveraging Spotlighting Middleware**:

```python
# Check if spotlighting detected attacks
kubectl exec -n psychsync deployment/psychsync -- python -c "
from app.middleware.spotlighting import SpotlightingEngine
engine = SpotlightingEngine()
# Review blocked operations and flagged content
print('Attack detection enabled:', engine.mode)
"
```

---

## 💥 Application Incidents

### High Error Rate (> 50%)

**Diagnosis**:

```bash
# 1. Check error rate by endpoint
kubectl exec -n psychsync deployment/psychsync -- curl -s http://localhost:8000/metrics | \
  grep "http_errors_total" | sort -t: -k2 -n

# 2. Check recent errors
kubectl logs -n psychsync -l app=psychsync --since=10m | grep -i "error\|exception" | tail -100

# 3. Check database connections
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  SELECT count(*), state
  FROM pg_stat_activity
  WHERE datname = 'psychsync'
  GROUP BY state;
"
```

**Common Causes and Fixes**:

**Database Connection Pool Exhausted**:
```bash
# 1. Check pool size
kubectl exec -n psychsync deployment/psychsync -- curl -s http://localhost:8000/metrics | grep db_pool

# 2. Scale up deployment
kubectl scale deployment psychsync -n psychsync --replicas=5

# 3. Restart pods to reset connections
kubectl rollout restart deployment/psychsync -n psychsync
```

**Recent Deployment Regression**:
```bash
# 1. Check recent deployments
kubectl rollout history deployment/psychsync -n psychsync | head -10

# 2. Rollback if needed
kubectl rollout undo deployment/psychsync -n psychsync

# 3. Verify fix
kubectl rollout status deployment/psychsync -n psychsync
kubectl logs -f -n psychsync -l app=psychsync --tail=50
```

### Memory Leak (Pod OOMKilled)

**Detection**:

```bash
# 1. Check pod events for OOM
kubectl get events -n psychsync --field-selector reason=OOMKilling

# 2. Check pod memory usage
kubectl top pods -n psychsync -l app=psychsync

# 3. Check memory trends
kubectl exec -n psychsync deployment/psychsync -- curl -s http://localhost:8000/metrics | grep memory_usage
```

**Mitigation**:

```bash
# 1. Immediate: Scale up to distribute load
kubectl scale deployment psychsync -n psychsync --replicas=10

# 2. Increase memory limits
kubectl set resources deployment psychsync -n psychsync \
  --limits=memory=2Gi \
  --requests=memory=512Mi

# 3. Enable VPA auto-tuning
kubectl apply -f deploy/kubernetes/psychsync-deployment.yaml  # Includes VPA

# 4. Restart pods to reclaim memory
kubectl rollout restart deployment/psychsync -n psychsync
```

### Database Performance Degradation

**Detection**:

```bash
# 1. Check slow queries
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  SELECT query, calls, total_time, mean_time, max_time
  FROM pg_stat_statements
  WHERE mean_time > 1000
  ORDER BY mean_time DESC
  LIMIT 20;
"

# 2. Check database connections
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  SELECT count(*), state
  FROM pg_stat_activity
  WHERE datname = 'psychsync'
  GROUP BY state;
"

# 3. Check table locks
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  SELECT relname, locktype, mode
  FROM pg_locks l
  JOIN pg_class c ON l.relation = c.oid
  WHERE NOT granted;
"
```

**Mitigation**:

```bash
# 1. Kill long-running queries
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE datname = 'psychsync'
  AND state = 'active'
  AND query_start < now() - interval '5 minutes';
"

# 2. Vacuum and analyze tables
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "VACUUM ANALYZE;"

# 3. Restart database pods if needed
kubectl rollout restart statefulset postgres -n database
```

---

## 🏗️ Infrastructure Incidents

### Node Failure

**Detection**:

```bash
# 1. Check node status
kubectl get nodes

# 2. Check pods on problematic node
kubectl get pods -n psychsync -o wide | grep <node-name>

# 3. Check node events
kubectl describe node <node-name>
```

**Mitigation**:

```bash
# 1. Cordon the node to prevent new pods
kubectl cordon <node-name>

# 2. Drain existing pods
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# 3. Monitor rescheduling
kubectl get pods -n psychsync -w

# 4. If node needs replacement, delete it
# (Cloud provider will provision new node)
kubectl delete node <node-name>
```

### Pod Stuck in Pending State

**Diagnosis**:

```bash
# 1. Check pod events
kubectl describe pod <pod-name> -n psychsync | grep -A 20 Events

# 2. Check resource availability
kubectl describe nodes | grep -A 5 "Allocated resources"

# 3. Check for taints/tolerations
kubectl describe pod <pod-name> -n psychsync | grep -A 10 Tolerations
```

**Common Fixes**:

**Insufficient Resources**:
```bash
# Scale down other workloads or add nodes
kubectl autoscale status
# Or manually scale up cluster (cloud-specific)
```

**Image Pull Error**:
```bash
# Check registry credentials
kubectl get secret psychsync-secrets -n psychsync -o jsonpath="{.data\.dockerconfigjson}" | base64 -d

# Create/update secret
kubectl create secret docker-registry psychsync-secrets \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token> \
  -n psychsync
```

---

## 💾 Data Incidents

### Accidental Data Deletion

**Immediate Actions**:

```bash
# 1. Stop all writes
kubectl scale deployment psychsync -n psychsync --replicas=0

# 2. Enable read-only mode
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "ALTER DATABASE psychsync SET default_transaction_read_only = on;"
```

**Recovery**:

```bash
# 1. Identify when data was deleted
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  SELECT * FROM audit_logs
  WHERE action = 'DELETE'
  ORDER BY timestamp DESC
  LIMIT 100;
"

# 2. Restore from backup
# Find appropriate backup
kubectl exec -n psychsync postgres-0 -- ls -lh /backups/

# Restore to point-in-time
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  SELECT pg_restore(
    '/backups/psychsync-backup-$(date +%Y%m%d).sql'
  );
"

# 3. Verify restored data
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  SELECT count(*) FROM users;
  SELECT count(*) FROM assessments;
"

# 4. Bring application back
kubectl scale deployment psychsync -n psychsync --replicas=3
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "ALTER DATABASE psychsync SET default_transaction_read_only = off;"
```

`★ Insight ─────────────────────────────────────`
Point-in-time recovery (PITR) is PostgreSQL's mechanism for restoring to a specific moment. Combined with the audit logs, you can identify the exact moment data was lost and restore to just before that time, minimizing data loss while maximizing recovery speed.
`─────────────────────────────────────────────────`

### Data Corruption

**Detection**:

```bash
# 1. Check database integrity
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  SELECT schemaname, tablename, n_live_tup, n_dead_tup
  FROM pg_stat_user_tables
  ORDER BY n_dead_tup DESC;
"

# 2. Check for orphaned rows
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  SELECT COUNT(*) FROM responses
  WHERE user_id NOT IN (SELECT id FROM users);
"

# 3. Check constraint violations
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "
  SELECT * FROM (
    SELECT conname, conrelid::regclass AS table
    FROM pg_constraint
    WHERE contype = 'f'
  ) checks
  LEFT JOIN LATERAL (
    SELECT 1 FROM pg_attribute WHERE attrelid = checks.conrelid LIMIT 1
  ) attrs ON true;
"
```

**Recovery**:

```bash
# 1. Rebuild indexes
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "REINDEX DATABASE psychsync;"

# 2. Vacuum full
kubectl exec -n psychsync postgres-0 -- psql -U postgres -c "VACUUM FULL ANALYZE;"

# 3. If corruption persists, restore from backup
# (See "Accidental Data Deletion" section)
```

---

## 📊 Post-Incident Procedures

### Incident Timeline Documentation

**Template**:

```markdown
# Incident Report: [Title]

**Date**: [YYYY-MM-DD]
**Severity**: [P0/P1/P2/P3]
**Duration**: [Start time - End time]
**Incident Commander**: [Name]

## Timeline

- **[HH:MM]**: Incident detected via [alerting source]
- **[HH:MM]**: Initial assessment completed
- **[HH:MM]**: Mitigation action taken
- **[HH:MM]**: Service restored
- **[HH:MM]**: Incident closed

## Impact

- **Users Affected**: [Number/Percentage]
- **Revenue Impact**: [If applicable]
- **Data Loss**: [Yes/No + details]

## Root Cause

[Technical explanation of what happened]

## Resolution

[What was done to fix it]

## Prevention

[What will be done to prevent recurrence]
```

### Post-Mortem Meeting

**Agenda**:

1. **Timeline Review** (15 min)
   - Walk through incident chronologically
   - Identify decision points
   - Discuss what information was available

2. **Root Cause Analysis** (30 min)
   - Use "5 Whys" technique
   - Map contributing factors
   - Identify process vs. technical issues

3. **Action Items** (30 min)
   - Specific improvements
   - Assign owners and due dates
   - Prioritize by impact

4. **Documentation Updates** (15 min)
   - Update runbooks
   - Add new alerting rules
   - Create knowledge base articles

### Continuous Improvement

**Metrics to Track**:

```bash
# Mean Time to Detect (MTTD)
# Time from incident start to detection

# Mean Time to Mitigate (MTTM)
# Time from detection to mitigation

# Mean Time to Resolution (MTTR)
# Time from detection to full resolution

# Incident frequency
# Count per month

# Incident recurrence
# Same root cause within 6 months
```

**Review Cadence**:
- Weekly: Review P0/P1 incidents
- Monthly: Review all incidents, trend analysis
- Quarterly: Review post-mortem completion, process improvements

---

## 📢 Communication Templates

### Internal Notification (Slack/Teams)

```
🚨 INCIDENT DECLARED 🚨

**Service**: PsychSync
**Severity**: [P0/P1/P2/P3]
**Impact**: [Brief description]

**Current Status**: [Investigating/Mitigating/Monitoring]
**Started**: [HH:MM UTC]
**Incident Commander**: [@mention]

**Latest Update**: [What's happening]

**Next Update**: [HH:MM UTC or As needed]

#incident-psychsync-[date]
```

### Customer Communication (Email)

**Subject**: Service Issue - [Brief Description]

```
Dear PsychSync Users,

We are currently experiencing [issue description]. Our team is actively working to resolve this issue.

**Impact**: [What users are experiencing]
**Started**: [Time]
**Current Status**: [What we're doing]

We will provide updates every [30 minutes] until resolved.

Thank you for your patience.

The PsychSync Team
```

### Post-Incident Summary (Internal)

```
📋 POST-MORTEM: [Incident Title]

**Severity**: [P0/P1/P2/P3]
**Duration**: [X hours Y minutes]
**Downtime**: [X minutes]

**What Happened**:
[Brief description]

**Root Cause**:
[Technical root cause]

**Impact**:
- Users affected: [X]
- Revenue impact: [$X if applicable]
- Data loss: [Yes/No]

**Timeline**:
[Key timestamps and actions]

**Resolution**:
[What was fixed]

**Preventive Measures**:
1. [Action item] - Owner: @mention - Due: [Date]
2. [Action item] - Owner: @mention - Due: [Date]

**Runbook Updates**:
- [Link to updated runbook]

**Related Incidents**:
- [Link to similar past incidents if any]
```

---

## 🔗 Related Resources

- **Deployment Runbook**: `/docs/operations/DEPLOYMENT_RUNBOOK.md`
- **Security Policy**: `/docs/LLM_SECURITY_POLICY.md`
- **Supply Chain Security**: `/docs/SUPPLY_CHAIN_SECURITY.md`
- **Monitoring Setup**: `/docs/MONITORING_SETUP.md`

---

**Last Updated**: 2025-12-27
**Maintained By**: SRE Team <sre@psychsync.ai>
