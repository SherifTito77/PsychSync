# 🔄 Production Rollback Playbooks

**Purpose:** Comprehensive rollback procedures for failed deployments
**Date:** 2025-12-27
**Platform:** Kubernetes with ArgoCD GitOps
**Severity:** CRITICAL (Production Recovery)

---

## 📋 Executive Summary

This document provides **step-by-step rollback procedures** for various failure scenarios in production. These playbooks are designed to:

- **Minimize downtime** (< 5 minutes for critical rollbacks)
- **Preserve data integrity** (no data loss during rollback)
- **Maintain audit trail** (all actions logged)
- **Enable post-mortem analysis** (detailed documentation)

**Target Recovery Time Objective (RTO):** 5 minutes
**Target Recovery Point Objective (RPO):** 0 minutes (no data loss)

---

## 🚨 CRITICAL: Immediate Rollback Procedures

### Scenario 1: Application Deployment Failure (Immediate)

**Severity:** CRITICAL
**Trigger:** Application not responding, high error rates, or health check failures
**Timeline:** Rollback within 5 minutes

#### Detection

```bash
# Health check failing
kubectl get pods -n psychsync
# STATUS: CrashLoopBackOff / Error / ImagePullBackOff

# Application returning errors
curl -f https://psychsync.com/health
# STATUS: HTTP 500 / Connection refused

# Error rate spiking
# Datadog/Grafana shows > 50% error rate
```

#### Rollback Procedure

**Step 1: Assess the Situation (30 seconds)**
```bash
# Check current deployment
kubectl get deployment psychsync-backend -n psychsync -o yaml

# Check pod status
kubectl get pods -n psychsync -l app=psychsync-backend

# Check recent events
kubectl get events -n psychsync --sort-by='.lastTimestamp' | tail -20

# Check logs
kubectl logs -n psychsync -l app=psychsync-backend --tail=100
```

**Step 2: Identify Previous Stable Version (1 minute)**
```bash
# Get rollout history
kubectl rollout history deployment/psychsync-backend -n psychsync

# Get ArgoCD sync history
argocd app history psychsync-backend-production --limit 10

# Check GitOps repo for previous stable commit
git clone https://github.com/psychsync/psychsync-gitops.git
cd psychsync-gitops
git log --oneline -10
```

**Step 3: Execute Rollback (2 minutes)**

**Option A: Rollback via ArgoCD (Recommended)**
```bash
# Rollback to previous revision
argocd app rollback psychsync-backend-production

# Wait for rollback to complete
argocd app wait psychsync-backend-production --health

# Verify rollback
argocd app get psychsync-backend-production
```

**Option B: Rollback via kubectl**
```bash
# Rollback to previous revision
kubectl rollout undo deployment/psychsync-backend -n psychsync

# Watch rollout status
kubectl rollout status deployment/psychsync-backend -n psychsync -w

# Verify pods are healthy
kubectl get pods -n psychsync -l app=psychsync-backend
```

**Option C: Rollback via Git (GitOps)**
```bash
# In GitOps repo
cd psychsync-gitops

# Revert last commit
git revert HEAD

# Push to trigger ArgoCD sync
git push

# Wait for ArgoCD to sync
argocd app wait psychsync-backend-production --health
```

**Step 4: Verify Rollback (1 minute)**
```bash
# Check health endpoint
curl -f https://psychsync.com/health
# Expected: {"status": "ok"}

# Check error rate (should be decreasing)
# Datadog/Grafana dashboard

# Run smoke tests
pytest tests/smoke/production.py --url=https://psychsync.com

# Verify pods are healthy
kubectl get pods -n psychsync
# Expected: All pods Running, READY: 1/1
```

**Step 5: Notify Team (30 seconds)**
```bash
# Slack notification
curl -X POST $SLACK_WEBHOOK \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "🔄 PRODUCTION ROLLBACK EXECUTED",
    "blocks": [
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*Application:* psychsync-backend\n*Status:* Rolled back to previous stable version\n*Time:* $(date -u +%Y-%m-%dT%H:%M:%SZ)\n*Executed by:* $USER\n*Reason:* Deployment failure detected"
        }
      },
      {
        "type": "actions",
        "elements": [
          {
            "type": "button",
            "text": {
              "type": "plain_text",
              "text": "View Logs"
            },
            "url": "https://argocd.psychsync.com/applications/psychsync-backend-production"
          },
          {
            "type": "button",
            "text": {
              "type": "plain_text",
              "text": "Post-Mortem"
            },
            "url": "https://github.com/psychsync/psychsync/issues/new?template=postmortem.md"
          }
        ]
      }
    ]
  }'
```

**Step 6: Document Incident (ongoing)**
```bash
# Create incident ticket
# https://github.com/psychsync/psychsync/issues/new

# Template:
## Incident Report: Production Rollback

**Date:** $(date -u +%Y-%m-%d)
**Time:** $(date -u +%H:%M:%SZ)
**Severity:** CRITICAL
**Executed By:** $USER

### What Happened
Deployment failed due to: [describe issue]

### Detection
- Time detected: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- Detected by: [monitoring alert / user report / health check]
- Symptom: [describe symptoms]

### Rollback Actions Taken
1. Assessed situation
2. Identified previous stable version: [version]
3. Executed rollback via [ArgoCD/kubectl/Git]
4. Verified rollback successful
5. Notified team

### Impact Assessment
- Downtime duration: [X minutes]
- Users affected: [estimate]
- Data loss: [yes/no]
- Revenue impact: [estimate]

### Root Cause Analysis
[To be completed in post-mortem]

### Preventive Actions
[To be identified in post-mortem]

### Next Steps
- [ ] Complete root cause analysis
- [ ] Schedule post-mortem meeting
- [ ] Implement preventive actions
- [ ] Update runbooks
```

---

### Scenario 2: Database Migration Failure

**Severity:** CRITICAL
**Trigger:** Database migration fails during deployment, causing application startup issues

#### Rollback Procedure

**Step 1: Stop Deployment (immediate)**
```bash
# Stop rollout if in progress
kubectl rollout pause deployment/psychsync-backend -n psychsync

# Or via ArgoCD
argocd app sync psychsync-backend-production --operation-halt
```

**Step 2: Assess Migration Status**
```bash
# Check migration job logs
kubectl logs -n psychsync job/psychsync-db-migration-XXXXX

# Check database schema version
kubectl run -it --rm psql-client --image=postgres:15 \
  --env="PGPASSWORD=$DATABASE_PASSWORD" \
  --restart=Never -- \
  psql -h postgres.psychsync.svc.cluster.local -U psychsync \
  -d psychsync -c "SELECT version FROM alembic_version;"
```

**Step 3: Rollback Migration**
```bash
# Rollback database migration
kubectl run -it --rm migration-rollback \
  --image=psychsync/db-migration:stable \
  --env="DATABASE_URL=$DATABASE_URL" \
  --restart=Never -- \
  alembic downgrade -1

# Verify rollback
kubectl run -it --rm psql-client --image=postgres:15 \
  --env="PGPASSWORD=$DATABASE_PASSWORD" \
  --restart=Never -- \
  psql -h postgres.psychsync.svc.cluster.local -U psychsync \
  -d psychsync -c "SELECT version FROM alembic_version;"
```

**Step 4: Rollback Application**
```bash
# Rollback application to previous version
kubectl rollout undo deployment/psychsync-backend -n psychsync

# Wait for rollback
kubectl rollout status deployment/psychsync-backend -n psychsync -w
```

**Step 5: Verify System Health**
```bash
# Check application health
curl -f https://psychsync.com/health

# Verify database connectivity
kubectl run -it --rm test-db-connection \
  --image=psychsync/backend:stable \
  --env="DATABASE_URL=$DATABASE_URL" \
  --restart=Never -- \
  python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"

# Run smoke tests
pytest tests/smoke/production.py --url=https://psychsync.com
```

**Step 6: Document and Notify**
```bash
# Document the failed migration
cat > /var/log/incidents/migration-failure-$(date +%Y%m%d).log <<EOF
Migration Rollback: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Migration Version: [FAILED_VERSION]
Previous Version: [STABLE_VERSION]
Root Cause: [INVESTIGATE]
Actions Taken:
  1. Stopped deployment
  2. Assessed migration status
  3. Rolled back database migration
  4. Rolled back application
  5. Verified system health
EOF

# Notify team
curl -X POST $SLACK_WEBHOOK \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "⚠️ DATABASE MIGRATION ROLLBACK",
    "blocks": [{
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Migration Failed:* [FAILED_VERSION]\n*Status:* Rolled back to [STABLE_VERSION]\n*Database:* PostgreSQL psychsync\n*Time:* $(date -u +%Y-%m-%dT%H:%M:%SZ)\n\nAction Required: Investigate migration failure before retrying deployment."
      }
    }]
  }'
```

---

### Scenario 3: Infrastructure Failure (Kubernetes Node Issues)

**Severity:** CRITICAL
**Trigger:** Kubernetes nodes failing, cluster not scheduling pods

#### Rollback Procedure

**Step 1: Assess Cluster Health**
```bash
# Check node status
kubectl get nodes

# Check cluster components
kubectl get pods -n kube-system

# Check cluster events
kubectl get events --all-namespaces --sort-by='.lastTimestamp' | tail -50

# Check for NotReady nodes
kubectl get nodes | grep NotReady
```

**Step 2: Identify Issue**
```bash
# Describe problematic node
kubectl describe node <node-name>

# Check node logs (if access)
ssh <node-name> "journalctl -u kubelet -n 100"

# Check resource usage
kubectl top nodes
kubectl top pods -n psychsync
```

**Step 3: Cordone Problematic Node (if needed)**
```bash
# Cordone node to prevent pod scheduling
kubectl cordon <node-name>

# Drain node (moves pods elsewhere)
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# If node is completely broken, mark as unschedulable
kubectl cordon <node-name>
```

**Step 4: Force Rollback to Healthy Region (if multi-region)**
```bash
# If multi-region setup, failover to healthy region
kubectl apply -f deploy/kubernetes/base/ -n psychsync \
  --context=arn:aws:eks:us-west-2:123456789012:cluster/psychsync-production-backup

# Update DNS to point to backup region
# (Route53, Cloudflare, etc.)
```

**Step 5: Verify Cluster Recovery**
```bash
# Wait for nodes to be Ready
kubectl wait --for=condition=Ready nodes --all --timeout=600s

# Verify pods are running
kubectl wait --for=condition=Ready pods -n psychsync -l app=psychsync-backend --timeout=300s

# Verify application health
curl -f https://psychsync.com/health
```

---

### Scenario 4: Secrets/Configuration Corruption

**Severity:** CRITICAL
**Trigger:** Application fails to start due to missing or corrupted secrets

#### Rollback Procedure

**Step 1: Identify Corrupted Secret**
```bash
# Check pod status
kubectl get pods -n psychsync

# Check pod events
kubectl describe pod <pod-name> -n psychsync

# Check if secret exists
kubectl get secret psychsync-secrets -n psychsync

# Check secret contents
kubectl get secret psychsync-secrets -n psychsync -o yaml
```

**Step 2: Restore Secret from Backup**
```bash
# List secret backups in S3
aws s3 ls s3://psychsync-secrets-backup/ | tail -10

# Download previous secret backup
aws s3 cp s3://psychsync-secrets-backup/20251227-020000/psychsync-secrets.json \
  /tmp/psychsync-secrets-restore.json

# Recreate secret from backup
kubectl create secret generic psychsync-secrets-restored \
  -n psychsync \
  --from-file=secrets.json=/tmp/psychsync-secrets-restore.json

# Or using External Secrets Operator, force refresh:
kubectl annotate externalsecret psychsync-database \
  -n psychsync \
  force-sync=$(date +%s) \
  --overwrite
```

**Step 3: Restart Pods with Restored Secret**
```bash
# Restart deployment to pick up restored secret
kubectl rollout restart deployment/psychsync-backend -n psychsync

# Wait for restart
kubectl rollout status deployment/psychsync-backend -n psychsync -w
```

**Step 4: Verify**
```bash
# Check pods are starting successfully
kubectl get pods -n psychsync -l app=psychsync-backend

# Check logs for errors
kubectl logs -n psychsync -l app=psychsync-backend --tail=50

# Verify application health
curl -f https://psychsync.com/health
```

---

### Scenario 5: Performance Degradation (Gradual Rollback)

**Severity:** HIGH
**Trigger:** Latency increases, response times degrade, but application still "up"

#### Rollback Procedure

**Step 1: Confirm Performance Degradation**
```bash
# Check application metrics
# Datadog/Grafana dashboard showing:
# - P95 latency > 1s (threshold: 500ms)
# - Error rate > 1% (threshold: 0.1%)
# - CPU/Memory utilization > 90%

# Run synthetic monitoring
curl -w "@curl-format.txt" https://psychsync.com/api/v1/health
# curl-format.txt:
# time_namelookup:  %{time_namelookup}\n
# time_connect:     %{time_connect}\n
# time_appconnect:  %{time_appconnect}\n
# time_pretransfer: %{time_pretransfer}\n
# time_starttransfer: %{time_starttransfer}\n
# time_total:       %{time_total}\n
```

**Step 2: Compare Metrics Before/After Deployment**
```bash
# Get metrics from Prometheus
# Current version metrics
prometheus_query='rate(http_request_duration_seconds_bucket{version="'$NEW_VERSION'"}[5m])'

# Previous version metrics
prometheus_query='rate(http_request_duration_seconds_bucket{version="'$OLD_VERSION'"}[5m])'
```

**Step 3: Decision Point (Canary Analysis)**

**If degradation is severe (> 2x latency):**
```bash
# Immediate rollback
kubectl rollout undo deployment/psychsync-backend -n psychsync
```

**If degradation is moderate (1.5x - 2x latency):**
```bash
# Scale up existing deployment first
kubectl scale deployment/psychsync-backend -n psychsync --replicas=10

# Monitor for 5 minutes to see if scaling helps

# If no improvement, rollback
kubectl rollout undo deployment/psychsync-backend -n psychsync
```

**If degradation is mild (< 1.5x latency):**
```bash
# Continue monitoring, may be temporary load spike
# Set up enhanced monitoring
# Do NOT rollback unless degradation worsens
```

**Step 4: Post-Rollback Verification**
```bash
# Verify metrics have returned to baseline
curl -w "@curl-format.txt" https://psychsync.com/api/v1/health

# Check error rates
# Datadog/Grafana dashboard

# Run performance tests
pytest tests/performance/latency.py --url=https://psychsync.com
```

---

## 📊 Rollback Decision Matrix

| Symptom | Severity | Auto-Rollback? | Time to Rollback |
|---------|----------|-----------------|------------------|
| **Application Down** (503, connection refused) | CRITICAL | ✅ Yes (after 30s) | 2 minutes |
| **High Error Rate** (> 50%) | CRITICAL | ✅ Yes (after 1m) | 3 minutes |
| **Database Migration Failed** | CRITICAL | ❌ No (manual) | 5 minutes |
| **Performance Degradation** (> 2x latency) | HIGH | ⚠️ Conditional | 5 minutes |
| **Moderate Error Rate** (10-50%) | HIGH | ❌ No (manual) | 10 minutes |
| **Secrets Missing** | CRITICAL | ✅ Yes (auto-restore) | 5 minutes |
| **Infrastructure Failure** | CRITICAL | ⚠️ Conditional | 15 minutes |

---

## 🛠️ Rollback Tools and Scripts

### Automated Rollback Script

```bash
#!/bin/bash
################################################################################
# Automated Rollback Script for PsychSync Production
# Usage: ./scripts/rollback-production.sh [previous_version]
################################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

NAMESPACE="psychsync"
DEPLOYMENT="psychsync-backend"
ARGOCD_APP="psychsync-backend-production"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

notify_slack() {
    local message="$1"
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -X POST "$SLACK_WEBHOOK" \
          -H 'Content-Type: application/json' \
          -d "{\"text\": \"$message\"}"
    fi
}

main() {
    log_info "Starting production rollback..."
    notify_slack "🔄 *Rollback Initiated* for ${DEPLOYMENT}"

    # Check if previous version provided
    PREV_VERSION="${1:-}"

    # Get current deployment status
    log_info "Current deployment status:"
    kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE"

    # Get rollout history
    log_info "Rollout history:"
    kubectl rollout history deployment/"$DEPLOYMENT" -n "$NAMESPACE"

    # Confirm rollback
    echo ""
    log_warning "This will rollback ${DEPLOYMENT} to previous version"
    read -p "Continue? (yes/no): " confirm

    if [[ "$confirm" != "yes" ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi

    # Execute rollback
    log_info "Executing rollback..."

    if [[ -n "$PREV_VERSION" ]]; then
        # Rollback to specific version via GitOps
        log_info "Rolling back to version: $PREV_VERSION"

        # Clone GitOps repo
        TMPDIR=$(mktemp -d)
        git clone https://github.com/psychsync/psychsync-gitops.git "$TMPDIR"
        cd "$TMPDIR"

        # Update kustomization
        yq eval '.images[0].newTag = strenv(PREV_VERSION)' \
          -i "apps/${DEPLOYMENT}/overlays/production/kustomization.yaml"

        # Commit and push
        git config user.name "Automation"
        git config user.email "automation@psychsync.com"
        git commit -am "Rollback to $PREV_VERSION"
        git push

        # Wait for ArgoCD sync
        log_info "Waiting for ArgoCD sync..."
        argocd app wait "$ARGOCD_APP" --health --timeout 900

        rm -rf "$TMPDIR"
    else
        # Rollback to previous revision via kubectl
        log_info "Rolling back to previous revision..."
        kubectl rollout undo deployment/"$DEPLOYMENT" -n "$NAMESPACE"

        # Wait for rollout
        log_info "Waiting for rollout to complete..."
        kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE" -w
    fi

    # Verify rollback
    log_info "Verifying rollback..."
    kubectl get pods -n "$NAMESPACE" -l app="$DEPLOYMENT"

    # Health check
    log_info "Running health checks..."
    if curl -f https://psychsync.com/health > /dev/null 2>&1; then
        log_info "✅ Health check passed"
        HEALTH_STATUS="passed"
    else
        log_error "❌ Health check failed"
        HEALTH_STATUS="failed"
    fi

    # Final status
    echo ""
    log_info "═══════════════════════════════════════════"
    log_info "       ROLLBACK COMPLETE"
    log_info "═══════════════════════════════════════════"
    log_info "Deployment: $DEPLOYMENT"
    log_info "Health Check: $HEALTH_STATUS"
    log_info "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    log_info "Executed by: $USER"
    log_info "═══════════════════════════════════════════"

    # Notify
    if [[ "$HEALTH_STATUS" == "passed" ]]; then
        notify_slack "✅ *Rollback Complete* for ${DEPLOYMENT}\nHealth: PASSED\nTime: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    else
        notify_slack "❌ *Rollback Failed* for ${DEPLOYMENT}\nHealth: FAILED\nTime: $(date -u +%Y-%m-%dT%H:%M:%SZ)\nRequires immediate attention!"
    fi
}

main "$@"
```

### ArgoCD Rollback Script

```bash
#!/bin/bash
################################################################################
# ArgoCD Rollback Script
# Usage: ./scripts/argocd-rollback.sh <application-name>
################################################################################

set -euo pipefail

APP_NAME="${1:?Application name required}"
NAMESPACE="${2:-argocd}"

log_info "Rolling back $APP_NAME via ArgoCD..."

# Rollback to previous healthy revision
argocd app rollback "$APP_NAME" --timeout 900

# Wait for rollback to complete
argocd app wait "$APP_NAME" --health --timeout 900

# Get current status
argocd app get "$APP_NAME"

log_info "Rollback complete"
```

---

## 📋 Post-Rollback Checklist

### Immediate Actions (First 15 minutes)

- [ ] **Verify application health** (all health checks passing)
- [ ] **Check error rates** (returned to baseline)
- [ ] **Verify data integrity** (no data corruption)
- [ ] **Check database connectivity** (all connections healthy)
- [ ] **Verify cache connectivity** (Redis connections working)
- [ ] **Check external integrations** (API keys, webhooks working)
- [ ] **Review logs** (no critical errors)
- [ ] **Notify team** (Slack, email, on-call)

### Short-Term Actions (Within 1 hour)

- [ ] **Document rollback** (incident report created)
- [ ] **Preserve logs** (logs from failed deployment saved)
- [ ] **Root cause analysis started** (team assembled)
- [ ] **Monitor metrics closely** (enhanced monitoring active)
- [ ] **Prepare hotfix** (if issue identified)
- [ ] **Communicate with stakeholders** (users notified if affected)
- [ ] **Review deployment process** (what went wrong?)

### Long-Term Actions (Within 24 hours)

- [ ] **Complete post-mortem** (document prepared)
- [ ] **Schedule post-mortem meeting** (team review)
- [ ] **Implement preventive actions** (fixes deployed)
- [ ] **Update runbooks** (procedures improved)
- [ ] **Add automated tests** (prevent recurrence)
- [ ] **Review CI/CD pipeline** (gates improved)
- [ ] **Team training** (lessons learned shared)

---

## 📝 Post-Mortem Template

```markdown
# Incident Post-Mortem: Production Rollback

**Date:** YYYY-MM-DD
**Incident ID:** INC-YYYY-MM-DD-001
**Severity:** CRITICAL/HIGH/MEDIUM/LOW
**Duration:** X hours
**Root Cause Owner:** [Name]

## Executive Summary
[2-3 sentence summary of what happened, impact, and resolution]

## Timeline
| Time (UTC) | Event | Duration |
|------------|-------|----------|
| 14:30 | Deployment initiated | - |
| 14:35 | Health checks failing | 5 min |
| 14:37 | Alert triggered | 2 min |
| 14:40 | Rollback initiated | 3 min |
| 14:45 | Rollback complete, system healthy | 5 min |

**Total Downtime:** 15 minutes

## Impact Assessment
- **Users Affected:** [number/percentage]
- **Revenue Impact:** [estimate]
- **Data Loss:** [yes/no]
- **Customer Complaints:** [number]

## Root Cause Analysis

### What Happened
[Detailed description of events]

### Why It Happened
[Root cause analysis - 5 Whys]

### Contributing Factors
- [ ] Human error
- [ ] Process failure
- [ ] Technical failure
- [ ] Communication breakdown
- [ ] Monitoring gap
- [ ] Testing gap
- [ ] Documentation gap

## Resolution Steps

### Immediate Actions
1. [Action 1]
2. [Action 2]
3. [Action 3]

### Rollback Procedure
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Verification
- [Health checks passed]
- [Error rates returned to baseline]
- [Smoke tests passed]

## Lessons Learned

### What Went Well
- [Monitoring detected issue quickly]
- [Rollback procedure worked smoothly]
- [Team responded rapidly]

### What Could Be Improved
- [Detection time could be faster]
- [Testing should have caught this]
- [Documentation was unclear]

### Action Items
- [ ] [Action item 1] - Owner: [Name] - Due: [Date]
- [ ] [Action item 2] - Owner: [Name] - Due: [Date]
- [ ] [Action item 3] - Owner: [Name] - Due: [Date]

## Preventive Measures

### Short-Term (This Week)
- [ ] [Measure 1]
- [ ] [Measure 2]

### Long-Term (This Month)
- [ ] [Measure 1]
- [ ] [Measure 2]

### Process Improvements
- [ ] Add automated testing for [specific scenario]
- [ ] Implement pre-production canary deployment
- [ ] Enhance monitoring with [specific metric]
- [ ] Update runbooks with [specific procedure]

## Appendix

### Logs
[Link to logs]

### Metrics
[Link to metrics dashboard]

### Screenshots
[Relevant screenshots]

---

**Post-Mortem Completed By:** [Name]
**Date:** YYYY-MM-DD
**Approved By:** [Name]
**Next Review Date:** YYYY-MM-DD
```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-27
**Maintained By:** DevOps Team
**Next Review:** Quarterly

## 📞 Emergency Contacts

| Role | Name | Contact | Hours |
|------|------|---------|-------|
| **On-Call Engineer** | [Name] | +1-XXX-XXX-XXXX | 24/7 |
| **DevOps Lead** | [Name] | +1-XXX-XXX-XXXX | Business hours |
| **CTO** | [Name] | +1-XXX-XXX-XXXX | Emergency |
| **Platform Owner** | [Name] | +1-XXX-XXX-XXXX | Business hours |

---

## 🎯 Key Takeaways

1. **Speed Matters** - Rollback within 5 minutes for critical issues
2. **Automation Wins** - Use ArgoCD rollback, not manual pod manipulation
3. **GitOps is Truth** - Rollback via Git, preserve audit trail
4. **Test After Rollback** - Always verify health checks and smoke tests
5. **Document Everything** - Create incident reports for learning
6. **Communicate Early** - Notify team immediately when issues detected
7. **Post-Mortem is Key** - Learn from every rollback to prevent recurrence
