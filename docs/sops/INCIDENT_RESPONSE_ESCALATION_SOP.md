# Incident Response and Escalation SOP - PsychSync

**Document Owner:** SRE Team
**Version:** 1.0.0
**Last Updated:** 2025-12-27
**Target Audience:** On-Call Engineers, Engineering Managers, CTO

---

## Table of Contents
1. [Incident Classification](#incident-classification)
2. [Escalation Paths](#escalation-paths)
3. [Incident Response Process](#incident-response-process)
4. [Role Responsibilities](#role-responsibilities)
5. [Communication Protocols](#communication-protocols)
6. [Post-Incident Procedures](#post-incident-procedures)
7. [Specific Incident Scenarios](#specific-incident-scenarios)
8. [Tools and Resources](#tools-and-resources)

---

## Incident Classification

### Severity Levels

**P0 - CRITICAL (Response Time: ≤15 minutes)**

Definition: Complete service outage or critical security breach affecting all users.

**Examples:**
- All users unable to access the service
- Data breach or exposure of sensitive information
- Complete database failure
- Production cluster down
- Payment processing failure
- Regulatory compliance violation

**Impact:**
- Revenue loss: >$10K/hour
- Users affected: 100%
- SLA breach imminent

**Escalation:** Immediate → CTO, CEO, Customer Support

---

**P1 - HIGH (Response Time: ≤1 hour)**

Definition: Major functionality broken affecting significant user base.

**Examples:**
- Assessment submission failing
- User authentication failing
- Critical API endpoints returning errors
- Significant performance degradation (>50% slowdown)
- Partial data corruption
- Security vulnerability requiring immediate patch

**Impact:**
- Revenue loss: $1K-$10K/hour
- Users affected: 25-100%
- Feature completely unavailable

**Escalation:** Within 15 min → Engineering Manager, Customer Support Lead

---

**P2 - MEDIUM (Response Time: ≤4 hours)**

Definition: Partial degradation affecting smaller user base or non-critical features.

**Examples:**
- Single feature not working (e.g., analytics dashboard)
- Minor performance issues (<50% slowdown)
- Error rate elevated but manageable (<5%)
- Non-critical API endpoints failing
- Intermittent issues

**Impact:**
- Revenue loss: <$1K/hour
- Users affected: 5-25%
- Workaround available

**Escalation:** Within 1 hour → Engineering Manager

---

**P3 - LOW (Response Time: ≤1 business day)**

Definition: Minor issues with minimal impact.

**Examples:**
- UI/UX bugs
- Typos in content
- Non-critical logging errors
- Documentation issues
- Feature requests

**Impact:**
- Revenue loss: Minimal
- Users affected: <5%
- Core functionality intact

**Escalation:** As needed → Team Lead

---

## Escalation Paths

### On-Call Escalation Chain

```
Level 1: On-Call Engineer (Primary)
    ↓ (30 min no response OR severity P0)
Level 2: On-Call Engineer (Backup)
    ↓ (30 min no response OR severity P0/P1)
Level 3: Engineering Manager
    ↓ (15 min no response OR severity P0)
Level 4: DevOps Lead
    ↓ (10 min no response OR severity P0)
Level 5: CTO
    ↓ (5 min no response)
Level 6: CEO
```

### Functional Escalation

**Security Incidents:**
1. On-Call Engineer
2. Security Lead (immediately for P0/P1)
3. CTO
4. Legal Team (if data breach)
5. CEO (if regulatory impact)

**Database Incidents:**
1. On-Call Engineer
2. DBA Lead
3. DevOps Lead
4. Engineering Manager

**Customer-Affecting Incidents:**
1. On-Call Engineer
2. Engineering Manager
3. Customer Support Lead (for customer communication)
4. CTO (if P0/P1)

**Payment/Billing Incidents:**
1. On-Call Engineer
2. Engineering Manager
3. Finance Lead
4. CTO

### Escalation Triggers

**Automatic Escalation (if no response in specified time):**
- P0: Escalate every 15 minutes
- P1: Escalate every 30 minutes
- P2: Escalate every 1 hour
- P3: Manual escalation as needed

**Manual Escalation (if any of these occur):**
- Issue exceeds knowledge/resolution ability
- Estimated resolution time significantly exceeds SLA
- Business impact is greater than initially assessed
- Multiple stakeholders request escalation

---

## Incident Response Process

### Phase 1: Detection & Acknowledgment (5-15 minutes)

**1.1 Detect Incident**

**Detection Methods:**
- Automated alerts (PagerDuty, CloudWatch, Grafana)
- User reports (support tickets, email, Slack)
- Monitoring dashboards (anomaly detection)
- Error tracking (Sentry)

**Detection Checklist:**
```bash
# Verify alert legitimacy
# Check monitoring dashboards
# Check error rates
# Check recent deployments
# Check related systems
```

**1.2 Acknowledge Incident**

**Steps:**
1. Acknowledge PagerDuty alert (stops escalation)
2. Join incident Slack channel: `#incident-YYYY-MM-DD-HHMM`
3. Update status to "Acknowledged"
4. Set status page (if customer-visible)

**Slack Announcement:**
```
🚨 INCIDENT DECLARED

Severity: P1
Summary: Users unable to submit assessments
Impact: ~40% of users
Started: TIMESTAMP
Acked by: @oncall-engineer

Investigation in progress. Next update in 15 minutes.
```

**Status Page Update (if needed):**
```
Service: Assessment Submission
Status: Investigating Issue
Description: We are currently investigating issues with assessment submissions.
Started: TIMESTAMP
```

### Phase 2: Investigation & Diagnosis (15-60 minutes)

**2.1 Gather Information**

**Checklist:**
- [ ] Review error logs (CloudWatch Logs, Sentry)
- [ ] Check metrics (CloudWatch, Grafana)
- [ ] Check recent changes (deployments, config changes)
- [ ] Check dependencies (third-party services)
- [ ] Reproduce issue if possible

**Diagnostic Commands:**
```bash
# Check cluster health
kubectl cluster-info
kubectl get nodes
kubectl top nodes

# Check pod status
kubectl get pods -n psychsync
kubectl describe pods -n psychsync

# Check logs
kubectl logs -f deployment/psychsync-backend -n psychsync --tail=500

# Check metrics
kubectl top pods -n psychsync

# Check recent deployments
kubectl rollout history deployment/psychsync-backend -n psychsync

# Check database
kubectl exec -it postgres-psychsync-0 -n psychsync -- pg_isready
kubectl exec -it postgres-psychsync-0 -n psychsync -- psql -U postgres -d psychsync \
  -c "SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '1 hour';"
```

**2.2 Determine Root Cause**

**Tools:**
- Distributed tracing (if enabled)
- Application Performance Monitoring (APM)
- Database query analysis
- Network analysis

**Root Cause Analysis Techniques:**
1. **5 Whys:** Ask "why" 5 times to find root cause
2. **Timeline Analysis:** Correlate events with incident start
3. **Comparison:** Compare to healthy system state
4. **Isolation:** Isolate affected components

**2.3 Update Status**

**Slack Update (every 15 minutes for P0/P1):**
```
⏳ INCIDENT UPDATE

Severity: P1
Summary: Users unable to submit assessments
Status: Investigating
Progress: Identified potential issue with database connection pool
Impact: ~40% of users
Started: 30 minutes ago
ETR: 45 minutes

Lead: @oncall-engineer
Contributors: @engineer2, @dba
```

### Phase 3: Resolution & Recovery (Variable)

**3.1 Implement Fix**

**Resolution Options:**
1. **Rollback:** If recent deployment caused issue
2. **Scaling:** Add resources if capacity issue
3. **Restart:** Restart affected services
4. **Configuration:** Fix configuration issue
5. **Code Fix:** Deploy hotfix (emergency)

**3.2 Monitor Recovery**

**Post-Fix Verification:**
```bash
# Check error rates dropped
aws cloudwatch get-metric-statistics \
  --namespace PsychSync \
  --metric-name ErrorRate \
  --dimensions Name=Environment,Value=production \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# Check service health
kubectl get pods -n psychsync
kubectl top pods -n psychsync

# Run smoke tests
pytest tests/integration/test_smoke.py -v

# Check for error logs
kubectl logs -l app=psychsync-backend -n psychsync \
  --since=5m | grep -i error
```

**3.3 Verify Normal Operation**

**Verification Checklist:**
- [ ] Error rates back to baseline
- [ ] Latency normal
- [ ] All services healthy
- [ ] Smoke tests passing
- [ ] User reports stopped
- [ ] No new alerts firing

**3.4 Declare Resolved**

**Slack Announcement:**
```
✅ INCIDENT RESOLVED

Severity: P1
Summary: Users unable to submit assessments
Duration: 2 hours 15 minutes
Resolved: TIMESTAMP
Root Cause: Database connection pool exhaustion

Resolution:
- Increased connection pool size
- Added connection pool monitoring
- Implemented connection drain on pod termination

Postmortem scheduled: DATE at TIME
Lead: @oncall-engineer
```

**Status Page Update:**
```
Service: Assessment Submission
Status: Operational
Description: The issue has been resolved. We are monitoring for any recurring problems.
Resolved: TIMESTAMP
```

---

## Role Responsibilities

### Incident Commander (IC)

**Primary Role:** Lead incident response, coordinate resources, make decisions.

**Responsibilities:**
- Declare incident severity
- Assign roles to team members
- Coordinate response efforts
- Make final decisions on resolution
- Communicate with stakeholders
- Authorize incident resolution

**Authority:**
- Can override normal processes
- Can pull in any team member
- Can approve emergency changes
- Can authorize customer communication

### Communications Lead (Comms)

**Primary Role:** Manage all internal and external communication.

**Responsibilities:**
- Provide status updates to team
- Draft customer-facing messages
- Update status page
- Notify stakeholders
- Manage social media (if needed)
- Prepare press release (if P0)

### Operations Lead (Ops)

**Primary Role:** Execute technical resolution steps.

**Responsibilities:**
- Implement fixes and changes
- Coordinate with technical teams
- Verify resolution steps
- Document technical changes
- Monitor system during recovery

### Scribe / Documenter

**Primary Role:** Document incident timeline and actions.

**Responsibilities:**
- Record timeline of events
- Document decisions made
- Capture chat history
- Note commands executed
- Prepare postmortem draft

### Customer Support Liaison

**Primary Role:** Interface with customer support team.

**Responsibilities:**
- Inform support team of issue
- Provide support with talking points
- Gather user reports
- Track customer impact
- Manage customer communications

---

## Communication Protocols

### Internal Communication

**Channels:**
- **Primary:** `#incident-YYYY-MM-DD-HHMM` (created per incident)
- **Secondary:** `#incidents` (all incidents)
- **Updates:** `#engineering` (major updates only)
- **Executive:** `#executive-updates` (P0/P1 only)

**Update Frequency:**
- P0: Every 15 minutes
- P1: Every 15-30 minutes
- P2: Every 1 hour
- P3: As needed

**Update Format:**
```
⏳ INCIDENT UPDATE

Severity: [PX]
Summary: [One-line summary]
Status: [Investigating / Identified / Monitoring / Resolved]
Progress: [What we've done]
Impact: [Users affected]
Started: [X minutes ago]
ETR: [Estimated time to resolution]

Lead: @name
Contributors: @name1, @name2
```

### External Communication

**Customer Communication:**

**Timing:**
- P0: Immediate (within 15 min)
- P1: Within 30 minutes
- P2: Within 2 hours
- P3: No communication (unless requested)

**Channels:**
- Status page: https://status.psychsync.com
- Email: For P0/P1 affecting many customers
- In-app notification: If possible
- Social media: For P0 only

**Email Template:**
```
Subject: Service Issue - [Service Name]

Dear [Customer Name],

We are currently experiencing an issue with [service name].

**What happened:**
[Clear, non-technical explanation]

**Impact:**
[How it affects customers]

**Current status:**
[What we're doing to fix it]

**Next update:**
[When we'll provide next update]

We apologize for any inconvenience and appreciate your patience.

Sincerely,
PsychSync Team
```

### Stakeholder Communication

**Who to Notify:**

| Severity | Engineering Manager | CTO | CEO | Customer Support | Legal |
|----------|---------------------|-----|-----|------------------|-------|
| P0 | Immediate | Immediate | Immediate | Immediate | As needed |
| P1 | Immediate | Within 15 min | Within 30 min | Immediate | If data |
| P2 | Within 1 hour | As needed | As needed | Within 2 hours | No |
| P3 | Next day | No | No | As needed | No |

**Executive Summary Format:**
```
INCIDENT BRIEF

Severity: P1
Status: Resolved
Duration: 2 hours 15 minutes
Root Cause: Database connection pool exhaustion
Impact: 40% of users unable to submit assessments for 90 minutes
Resolution: Increased connection pool size and added monitoring

Financial Impact: $X (estimated)
Customer Impact: Y users affected
Next Steps: Postmortem scheduled for DATE
```

---

## Post-Incident Procedures

### Immediate Post-Incident (First 24 Hours)

**1. Incident Review Meeting (within 24 hours)**

**Attendees:**
- Incident Commander
- All responders
- Engineering Manager
- Relevant stakeholders

**Agenda:**
1. Timeline review
2. Root cause analysis
3. What went well
4. What could be improved
5. Action items

**2. Postmortem Document (within 48 hours)**

**Template:**

```markdown
# Incident Postmortem: [Title]

**Date:** [Incident date]
**Duration:** [Start time] - [End time]
**Severity:** [P0/P1/P2/P3]
**Incident Commander:** [Name]

## Executive Summary

[2-3 sentence summary for executives]

## Impact

**Users Affected:** [Number/percentage]
**Revenue Impact:** [Estimated]
**Services Affected:** [List]
**Duration of Outage:** [Time]

## Timeline

| Time | Event |
|------|-------|
| 00:00 | [Event] |
| 00:15 | [Event] |
| ... | ... |

## Root Cause

[Detailed explanation of what happened and why]

## Resolution

[What we did to fix it]

## Immediate Actions Taken

- [Action 1]
- [Action 2]

## Follow-Up Actions

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| [Action] | [Name] | [Date] | [Open/Done] |

## Lessons Learned

### What Went Well
- [Positive thing 1]
- [Positive thing 2]

### What Could Be Improved
- [Area for improvement 1]
- [Area for improvement 2]

## Action Items to Prevent Recurrence

1. [Action item 1] - [Owner] - [Due date]
2. [Action item 2] - [Owner] - [Due date]

## Appendix

### Logs
[Links to relevant logs]

### Metrics
[Links to relevant metrics]

### Related Incidents
[Links to similar past incidents]
```

**3. Action Item Tracking**

Create GitHub issues for all follow-up actions:
```bash
# Create issue for each action item
gh issue create \
  --title "[Postmortem] Add database connection pool monitoring" \
  --body "From incident P1-20251227-assessment-failure" \
  --label "postmortem,high-priority,database" \
  --assignee @username
```

### Long-Term Improvements

**Postmortem Review (Weekly)**

Engineering leadership reviews:
- All postmortems from the week
- Action item progress
- Recurring issues
- Systematic improvements needed

**Quarterly Incident Review**

Review and improve:
- MTTD (Mean Time To Detect)
- MTTM (Mean Time To Mitigate)
- MTTR (Mean Time To Recovery)
- Incident frequency
- Recurring incident patterns

**Process Improvements:**

Based on incidents, update:
- Runbooks (add new procedures)
- Monitoring (add new alerts)
- Documentation (clarify procedures)
- Training (address knowledge gaps)
- Architecture (eliminate single points of failure)

---

## Specific Incident Scenarios

### Scenario 1: Complete Service Outage (P0)

**Symptoms:**
- All users unable to access service
- All health checks failing
- Error rate: 100%

**Response Steps:**

1. **Immediate (0-5 min):**
   ```bash
   # Check cluster status
   kubectl cluster-info
   kubectl get nodes

   # Check if it's cluster-wide or specific service
   kubectl get pods -A

   # Check load balancer
   kubectl get svc -n psychsync
   ```

2. **Diagnosis (5-15 min):**
   - If cluster down: Contact AWS support
   - If nodes down: Check AWS console, scale up
   - If service down: Check deployment, rollback if needed
   - If DNS issue: Check Route53

3. **Recovery (15-60 min):**
   - Rollback recent deployment (if applicable)
   - Scale up services
   - Restart failed services
   - Restore from backup (if data corruption)

### Scenario 2: Database Failure (P0)

**Symptoms:**
- Database connection errors
- All database-dependent features failing
- Database pods in CrashLoopBackOff

**Response Steps:**

1. **Immediate (0-5 min):**
   ```bash
   # Check database pods
   kubectl get pods -n psychsync -l app=postgres

   # Check database logs
   kubectl logs postgres-psychsync-0 -n psychsync

   # Check database connectivity
   kubectl exec -it postgres-psychsync-0 -n psychsync \
     -- pg_isready -U postgres
   ```

2. **Diagnosis (5-30 min):**
   - Check disk space
   - Check connection limits
   - Check replication status
   - Review recent schema changes

3. **Recovery (30-120 min):**
   - Scale up database resources
   - Restart database pods
   - Failover to standby (if available)
   - Restore from backup (last resort)

### Scenario 3: High Error Rate (P1)

**Symptoms:**
- Error rate elevated >5%
- API endpoints failing intermittently
- User reports of failures

**Response Steps:**

1. **Immediate (0-5 min):**
   - Check Sentry for errors
   - Check error logs
   - Identify error patterns

2. **Diagnosis (5-30 min):**
   - Check recent deployments
   - Check external dependencies
   - Check rate limits
   - Reproduce error

3. **Recovery (30-60 min):**
   - Rollback recent deployment (if cause)
   - Fix configuration issue
   - Scale up services
   - Implement emergency hotfix

### Scenario 4: Performance Degradation (P1/P2)

**Symptoms:**
- High latency (P95 > 1s)
- Slow page loads
- Timeouts

**Response Steps:**

1. **Immediate (0-5 min):**
   - Check resource usage (CPU, memory)
   - Check database query performance
   - Check cache hit rates

2. **Diagnosis (5-30 min):**
   - Identify bottleneck (CPU, memory, I/O, network)
   - Check for N+1 queries
   - Check for memory leaks

3. **Recovery (30-60 min):**
   - Scale up services (horizontal/vertical)
   - Optimize slow queries
   - Restart services (if memory leak)
   - Clear caches

### Scenario 5: Security Incident (P0)

**Symptoms:**
- Suspicious activity detected
- Data breach suspected
- Unauthorized access

**Response Steps:**

1. **Immediate (0-5 min):**
   - Notify Security Lead
   - Notify CTO
   - Assess scope and severity

2. **Containment (5-30 min):**
   - Block malicious IPs
   - Revoke compromised credentials
   - Disable affected services
   - Enable enhanced monitoring

3. **Investigation (30 min - 24 hours):**
   - Preserve evidence (logs, metrics)
   - Identify attack vector
   - Assess data exposure
   - Document timeline

4. **Recovery (Variable):**
   - Patch vulnerabilities
   - Restore from clean backups
   - Implement additional security measures
   - Notify affected users (if data breach)

---

## Tools and Resources

### Monitoring & Alerting

**Tools:**
- **PagerDuty:** On-call management and alerting
- **CloudWatch:** AWS metrics and logs
- **Grafana:** Visualization dashboards
- **Sentry:** Error tracking
- **ElastAlert:** Log-based alerting

**Key Dashboards:**
- System Overview: https://grafana.psychsync.com/d/system-overview
- Application Health: https://grafana.psychsync.com/d/app-health
- Database Metrics: https://grafana.psychsync.com/d/database
- Security Events: https://grafana.psychsync.com/d/security

### Communication Tools

**Slack:**
- **#incidents:** General incident discussion
- **#on-call:** On-call coordination
- **#engineering:** Engineering team updates
- **#executive-updates:** Executive notifications

**Status Page:**
- https://status.psychsync.com

### Documentation

**Internal:**
- Runbooks: `docs/operations/`
- Architecture: `docs/ARCHITECTURE.md`
- Deployment SOP: `docs/sops/PRODUCTION_DEPLOYMENT_SOP.md`

**External:**
- API Documentation: https://docs.psychsync.com/api
- Support: support@psychsync.com

### Emergency Contacts

| Role | Name | Slack | Phone | Hours |
|------|------|-------|-------|-------|
| On-Call (Primary) | | @oncall | +1-XXX-XXX-XXXX | 24/7 |
| On-Call (Backup) | | @oncall-backup | +1-XXX-XXX-XXXX | 24/7 |
| Engineering Manager | | @eng-manager | +1-XXX-XXX-XXXX | 9-5 |
| DevOps Lead | | @devops-lead | +1-XXX-XXX-XXXX | 9-5 |
| Security Lead | | @security-lead | +1-XXX-XXX-XXXX | 9-5 |
| CTO | | @cto | +1-XXX-XXX-XXXX | 24/7 |
| CEO | | @ceo | +1-XXX-XXX-XXXX | 24/7 |

---

## Training & Drills

### On-Call Training

**New On-Call Engineer Checklist:**
- [ ] Read all runbooks
- [ ] Shadow on-call for 1 week
- [ ] Participate in incident drill
- [ ] Complete incident response training
- [ ] Understand escalation paths
- [ ] Set up PagerDuty account
- [ ] Test notification methods
- [ ] Review recent postmortems

### Incident Drills

**Frequency:**
- Team drills: Monthly
- Company-wide drills: Quarterly

**Drill Scenarios:**
1. Complete service outage
2. Database failure
3. Security breach
4. Deployment failure
5. Dependency failure

**Drill Evaluation:**
- MTTD achieved?
- Correct severity assigned?
- Effective communication?
- Proper documentation?
- Safe resolution?

---

## Appendices

### A. Incident Severity Quick Reference

| Severity | Response Time | Escalation | Customer Comms |
|----------|---------------|------------|----------------|
| P0 | ≤15 min | Immediate | Yes (15 min) |
| P1 | ≤1 hour | Within 15 min | Yes (30 min) |
| P2 | ≤4 hours | Within 1 hour | Yes (2 hours) |
| P3 | ≤1 business day | As needed | No |

### B. Command Reference

**Incident Declaration:**
```bash
# Create incident channel
/slack create-channel #incident-$(date +%Y%m%d-%H%M)

# Declare incident in Slack
/postmortem declare --severity P1 --summary "Users unable to submit assessments"

# Update status page
/status-page update --service "Assessment API" --status "investigating"
```

**Common Commands:**
```bash
# Check system health
kubectl get pods -n psychsync
kubectl top nodes
kubectl top pods -n psychsync

# Check logs
kubectl logs -f deployment/psychsync-backend -n psychsync --tail=1000

# Restart service
kubectl rollout restart deployment/psychsync-backend -n psychsync

# Rollback deployment
kubectl rollout undo deployment/psychsync-backend -n psychsync

# Scale up
kubectl scale deployment/psychsync-backend --replicas=10 -n psychsync
```

### C. Postmortem Template Repository

All postmortems stored in: `docs/postmortems/`

Naming convention: `YYYY-MM-DD-severity-title.md`

### D. Related Documentation

- **Rollback Playbooks:** `docs/ROLLBACK_PLAYBOOKS.md`
- **Deployment SOP:** `docs/sops/PRODUCTION_DEPLOYMENT_SOP.md`
- **Security Runbook:** `docs/operations/SECURITY_RUNBOOK.md`
- **Database Runbook:** `docs/operations/DATABASE_RUNBOOK.md`

---

**Document Status:** ✅ Approved

**Next Review Date:** 2026-03-27 (3 months)

**Change Log:**
- Version 1.0.0 (2025-12-27): Initial SOP creation based on SRE best practices
