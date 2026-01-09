# Production Deployment SOP - PsychSync

**Document Owner:** DevOps Team
**Version:** 1.0.0
**Last Updated:** 2025-12-27
**Target Audience:** DevOps Engineers, Release Managers, Senior Developers

---

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Prerequisites](#deployment-prerequisites)
3. [Deployment Strategies](#deployment-strategies)
4. [Automated Deployment Procedure](#automated-deployment-procedure)
5. [Manual Deployment Procedure](#manual-deployment-procedure)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Rollback Procedures](#rollback-procedures)
8. [Emergency Deployments](#emergency-deployments)
9. [Deployment Troubleshooting](#deployment-troubleshooting)
10. [Communication Protocol](#communication-protocol)

---

## Pre-Deployment Checklist

### 24 Hours Before Deployment

**Planning:**
- [ ] Create deployment plan with:
  - Feature summary
  - Breaking changes
  - Database migration requirements
  - Estimated downtime (if any)
  - Rollback plan
- [ ] Schedule deployment window with stakeholders
- [ ] Assign deployment roles:
  - Deployment Lead
  - Database Operator
  - Monitoring Lead
  - Communication Lead

**Testing:**
- [ ] All tests passing in staging environment
- [ ] Integration tests completed
- [ ] Performance tests completed (if applicable)
- [ ] Security scans completed (Semgrep, Snyk, Trivy)
- [ ] Load testing completed (for significant changes)

**Documentation:**
- [ ] API documentation updated
- [ ] Changelog updated
- [ ] Migration guide prepared (if needed)
- [ ] Release notes drafted

### 1 Hour Before Deployment

**Final Checks:**
- [ ] Notify stakeholders of upcoming deployment
- [ ] Verify no incidents in progress
- [ ] Check system health metrics are baseline
- [ ] Verify sufficient disk space on all nodes
- [ ] Verify database backup completed successfully
- [ ] Check CI/CD pipeline status

**Team Readiness:**
- [ ] All team members available
- [ ] On-call engineer notified
- [ ] Communication channels prepared
- [ ] Status page ready (if customer-visible)

---

## Deployment Prerequisites

### Access Requirements

**Tools & Access:**
- [ ] AWS CLI configured with production credentials
- [ ] kubectl configured for production EKS cluster
- [ ] GitHub access with appropriate permissions
- [ ] Slack access for team communication
- [ ] Access to monitoring dashboards (Grafana, Datadog)

**Permissions Required:**
- GitHub repository: Write access
- AWS EKS: Cluster admin access
- AWS ECR: Push/pull images
- AWS RDS: No direct access (via migrations only)
- AWS S3: Access to deployment artifacts
- CloudWatch: Access to logs and metrics

### Environment Verification

**Verify Staging Environment:**
```bash
# Set kubectl context to staging
kubectl config use-context psychsync-staging

# Check cluster connectivity
kubectl cluster-info

# Verify all pods are running
kubectl get pods -n psychsync

# Check current deployment
kubectl get deployment -n psychsync
kubectl rollout status deployment/psychsync-backend -n psychsync
```

**Verify Production Environment:**
```bash
# Set kubectl context to production
kubectl config use-context psychsync-production

# Check cluster connectivity
kubectl cluster-info

# Check current state
kubectl get pods -n psychsync
kubectl get deployment -n psychsync
kubectl get hpa -n psychsync
```

---

## Deployment Strategies

### Strategy 1: Blue-Green Deployment (Recommended)

**When to Use:**
- Major releases
- Database schema changes
- High-risk deployments

**Process:**
1. Deploy new version to green environment
2. Run smoke tests in green
3. Switch traffic from blue to green
4. Monitor for issues
5. Keep blue running for rollback capability

**Advantages:**
- Zero downtime
- Instant rollback
- Safe testing before cutover

**Disadvantages:**
- Double resource cost during deployment
- Longer deployment time

### Strategy 2: Rolling Update

**When to Use:**
- Routine deployments
- No breaking changes
- Resource-constrained environments

**Process:**
1. Update deployment with new image
2. Kubernetes gradually replaces pods
3. New pods pass health checks before continuing
4. Old pods terminated after new ones healthy

**Configuration:**
```yaml
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Create 1 extra pod during update
      maxUnavailable: 0  # Never allow unavailable pods
```

**Advantages:**
- Efficient resource usage
- Faster deployment
- Automatic rollback on failure

**Disadvantages:**
- Potential brief traffic to old/new versions simultaneously
- Slower rollback than blue-green

### Strategy 3: Canary Deployment

**When to Use:**
- Experimental features
- Gradual rollout to verify behavior
- High-risk changes

**Process:**
1. Deploy to small percentage of pods (e.g., 10%)
2. Monitor metrics closely
3. Gradually increase percentage (25% → 50% → 100%)
4. Roll back if issues detected

**Advantages:**
- Risk mitigation
- Real user testing
- Quick rollback

**Disadvantages:**
- Longer deployment time
- Complex monitoring required

---

## Automated Deployment Procedure

### Option 1: GitHub Actions CI/CD (Standard)

**Trigger Deployment:**

1. **Merge PR to Main Branch**
   ```bash
   # Ensure PR is approved and all checks pass
   # Merge using GitHub UI or CLI
   gh pr merge 123 --squash
   ```

2. **Monitor CI/CD Pipeline**
   ```bash
   # Watch pipeline progress
   gh run list --limit 5
   gh run view --web
   ```

3. **Staging Deployment (Automatic)**
   - CI/CD automatically deploys to staging
   - Monitor: https://github.com/psychsync/psychsync/actions
   - Verify staging deployment successful

4. **Production Deployment (Manual Approval)**
   - Navigate to: https://github.com/psychsync/psychsync/actions
   - Find workflow run for production deployment
   - Click "Review deployments"
   - Approve production deployment
   - Monitor deployment logs

**Production Deployment Gating:**

The pipeline checks:
- ✅ All tests passing
- ✅ Test coverage ≥ 80%
- ✅ No critical vulnerabilities
- ✅ Staging health checks passing
- ✅ Error rate < 0.1%
- ✅ Uptime ≥ 99%

### Option 2: Deployment Script

**Run Automated Deployment Script:**

```bash
# Navigate to scripts directory
cd /path/to/psychsync/scripts

# Run deployment script
./deploy-production.sh \
  --environment production \
  --version v1.2.3 \
  --strategy rolling \
  --verify \
  --notify
```

**Script Parameters:**
- `--environment`: Target environment (staging/production)
- `--version`: Release version tag
- `--strategy`: Deployment strategy (rolling/blue-green/canary)
- `--verify`: Run post-deployment verification
- `--notify`: Send Slack notifications
- `--dry-run`: Simulate deployment without changes

**Deployment Steps (Automated):**

1. **Pre-Deployment Checks**
   ```bash
   # Verify git tag exists
   git fetch --tags
   git tag -l v1.2.3

   # Verify no uncommitted changes
   git status

   # Run tests
   pytest tests/ -v

   # Check security scan results
   cat security-report.json | jq '.vulnerabilities | length'
   ```

2. **Build Docker Image**
   ```bash
   # Build and push image
   docker build -t psychsync-backend:v1.2.3 .
   docker tag psychsync-backend:v1.2.3 \
     <ECR_REPO_URL>/psychsync-backend:v1.2.3

   # Push to ECR
   aws ecr get-login-password | docker login \
     --username AWS --password-stdin <ECR_REPO_URL>
   docker push <ECR_REPO_URL>/psychsync-backend:v1.2.3
   ```

3. **Database Migrations**
   ```bash
   # Run database migrations
   alembic upgrade head

   # Verify migration success
   alembic current
   psql -h <PROD_DB_HOST> -U postgres -d psychsync \
     -c "SELECT version FROM alembic_version;"
   ```

4. **Kubernetes Deployment**
   ```bash
   # Update deployment image
   kubectl set image deployment/psychsync-backend \
     backend=<ECR_REPO_URL>/psychsync-backend:v1.2.3 \
     -n psychsync

   # Watch rollout status
   kubectl rollout status deployment/psychsync-backend -n psychsync

   # Verify new pods running
   kubectl get pods -n psychsync -l app=psychsync-backend
   ```

5. **Health Verification**
   ```bash
   # Check service health
   kubectl get endpoints -n psychsync

   # Test application health endpoint
   kubectl run -it --rm debug --image=curlimages/curl \
     --restart=Never -- \
     curl http://psychsync-backend:8000/api/v1/health/public

   # Check pod logs
   kubectl logs -f deployment/psychsync-backend -n psychsync --tail=100
   ```

---

## Manual Deployment Procedure

### When Manual Deployment is Required

- Automated deployment failed
- Emergency hotfix needed
- Infrastructure changes required
- Complex multi-step deployment

### Step-by-Step Manual Deployment

#### Phase 1: Preparation (5 minutes)

```bash
# 1. Set environment variables
export ENVIRONMENT="production"
export VERSION="v1.2.3"
export DEPLOYMENT_ID="deploy-$(date +%Y%m%d-%H%M%S)"

# 2. Create deployment log file
mkdir -p logs/deployments
DEPLOY_LOG="logs/deployments/${DEPLOYMENT_ID}.log"
echo "Starting deployment ${DEPLOYMENT_ID}" | tee -a ${DEPLOY_LOG}

# 3. Notify team in Slack
# Post to #engineering channel
curl -X POST ${SLACK_WEBHOOK} \
  -H 'Content-Type: application/json' \
  -d "{
    \"text\": \"🚀 Production deployment starting: ${VERSION}\",
    \"blocks\": [
      {
        \"type\": \"section\",
        \"text\": {
          \"type\": \"mrkdwn\",
          \"text\": \"*Deployment ID:* ${DEPLOYMENT_ID}\n*Version:* ${VERSION}\n*Lead:* ${DEPLOYER}\"
        }
      }
    ]
  }"
```

#### Phase 2: Pre-Deployment Checks (10 minutes)

```bash
# 1. Verify current system health
echo "=== Pre-Deployment Health Check ===" | tee -a ${DEPLOY_LOG}

# Check Kubernetes cluster
kubectl cluster-info | tee -a ${DEPLOY_LOG}

# Check current pods
kubectl get pods -n psychsync | tee -a ${DEPLOY_LOG}

# Check HPA status
kubectl get hpa -n psychsync | tee -a ${DEPLOY_LOG}

# Check database connectivity
kubectl exec -it postgres-psychsync-0 -n psychsync \
  -- pg_isready -U postgres

# 2. Verify backup exists
echo "Checking recent backups..." | tee -a ${DEPLOY_LOG}
aws s3 ls s3://psychsync-postgres-backups/backups/production/ | tail -5

# 3. Run smoke tests
pytest tests/integration/test_smoke.py -v | tee -a ${DEPLOY_LOG}

# 4. Capture baseline metrics
kubectl top pods -n psychsync | tee -a ${DEPLOY_LOG}
```

#### Phase 3: Database Migration (15 minutes)

```bash
# 1. Create pre-migration backup
echo "=== Creating Pre-Migration Backup ===" | tee -a ${DEPLOY_LOG}

./scripts/backup-postgres-production.sh | tee -a ${DEPLOY_LOG}

# 2. Review migration files
echo "=== Reviewing Migrations ===" | tee -a ${DEPLOY_LOG}
alembic heads
alembic current

# 3. Run migrations in test/staging first
echo "=== Running Migration in Staging ===" | tee -a ${DEPLOY_LOG}
kubectl config use-context psychsync-staging
alembic upgrade head

# Verify staging success
# Run smoke tests in staging
pytest tests/integration/ -k staging -v

# 4. Run production migration
echo "=== Running Production Migration ===" | tee -a ${DEPLOY_LOG}
kubectl config use-context psychsync-production

# Execute migration
alembic upgrade head | tee -a ${DEPLOY_LOG}

# 5. Verify migration success
echo "Verifying migration..." | tee -a ${DEPLOY_LOG}
alembic current | tee -a ${DEPLOY_LOG}

# Check database
kubectl exec -it postgres-psychsync-0 -n psychsync \
  -- psql -U postgres -d psychsync \
  -c "SELECT COUNT(*) FROM alembic_version;"
```

#### Phase 4: Application Deployment (20 minutes)

```bash
# 1. Build and push Docker image
echo "=== Building Docker Image ===" | tee -a ${DEPLOY_LOG}
docker build -t psychsync-backend:${VERSION} . | tee -a ${DEPLOY_LOG}

# Tag for ECR
docker tag psychsync-backend:${VERSION} \
  ${ECR_REPO}/psychsync-backend:${VERSION}
docker tag psychsync-backend:${VERSION} \
  ${ECR_REPO}/psychsync-backend:latest

# Push to ECR
echo "=== Pushing to ECR ===" | tee -a ${DEPLOY_LOG}
docker push ${ECR_REPO}/psychsync-backend:${VERSION} | tee -a ${DEPLOY_LOG}
docker push ${ECR_REPO}/psychsync-backend:latest | tee -a ${DEPLOY_LOG}

# 2. Update Kubernetes deployment
echo "=== Updating Kubernetes Deployment ===" | tee -a ${DEPLOY_LOG}

# Apply new image
kubectl set image deployment/psychsync-backend \
  backend=${ECR_REPO}/psychsync-backend:${VERSION} \
  -n psychsync | tee -a ${DEPLOY_LOG}

# 3. Monitor rollout
echo "=== Monitoring Rollout ===" | tee -a ${DEPLOY_LOG}
kubectl rollout status deployment/psychsync-backend \
  -n psychsync -w --timeout=10m | tee -a ${DEPLOY_LOG}

# Watch pod creation
kubectl get pods -n psychsync -w | tee -a ${DEPLOY_LOG}
```

#### Phase 5: Post-Deployment Verification (15 minutes)

```bash
# 1. Health checks
echo "=== Post-Deployment Health Check ===" | tee -a ${DEPLOY_LOG}

# Service health
kubectl get endpoints -n psychsync | tee -a ${DEPLOY_LOG}

# Application health
kubectl run -it --rm curl-debug --image=curlimages/curl \
  --restart=Never -n psychsync -- \
  curl -f http://psychsync-backend:8000/api/v1/health/public | tee -a ${DEPLOY_LOG}

# 2. Smoke tests
echo "=== Running Smoke Tests ===" | tee -a ${DEPLOY_LOG}
pytest tests/integration/test_smoke.py -v | tee -a ${DEPLOY_LOG}

# 3. Check logs for errors
echo "=== Checking Logs for Errors ===" | tee -a ${DEPLOY_LOG}
kubectl logs -l app=psychsync-backend -n psychsync \
  --tail=500 | grep -i error | tee -a ${DEPLOY_LOG}

# 4. Verify metrics
echo "=== Post-Deployment Metrics ===" | tee -a ${DEPLOY_LOG}
kubectl top pods -n psychsync -l app=psychsync-backend | tee -a ${DEPLOY_LOG}

# 5. Load test (if applicable)
# k6 run tests/load/basic.js
```

#### Phase 6: Monitoring & Stabilization (30 minutes)

```bash
# 1. Monitor error rates
echo "=== Monitoring Error Rates ===" | tee -a ${DEPLOY_LOG}

# Watch CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace PsychSync \
  --metric-name ErrorRate \
  --dimensions Name=Environment,Value=production \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# 2. Monitor latency
kubectl logs -l app=psychsync-backend -n psychsync \
  --since=10m | grep "duration_ms"

# 3. Check for anomalies
# Review Grafana dashboard
# https://grafana.psychsync.com/d/production-overview

# 4. Functional testing
# Manually test key features:
# - User login
# - Assessment creation
# - Response submission
# - Analytics generation
```

---

## Post-Deployment Verification

### Automated Health Checks

```bash
#!/bin/bash
# scripts/verify-deployment.sh

echo "Running deployment verification..."

# 1. Health endpoint check
HEALTH_URL="https://api.psychsync.com/api/v1/health/public"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${HEALTH_URL})

if [ ${HEALTH_STATUS} -eq 200 ]; then
  echo "✅ Health check passed"
else
  echo "❌ Health check failed: ${HEALTH_STATUS}"
  exit 1
fi

# 2. API endpoint checks
API_URL="https://api.psychsync.com/api/v1"

# Check public endpoints
curl -s -f ${API_URL}/health/public > /dev/null
if [ $? -eq 0 ]; then
  echo "✅ Public endpoint accessible"
else
  echo "❌ Public endpoint failed"
  exit 1
fi

# 3. Database connectivity check
kubectl exec -it postgres-psychsync-0 -n psychsync \
  -- pg_isready -U postgres

# 4. Redis connectivity check
kubectl exec -it redis-psychsync-0 -n psychsync \
  -- redis-cli ping

# 5. Pod health check
READY_REPLICAS=$(kubectl get deployment psychsync-backend \
  -n psychsync -o jsonpath='{.status.readyReplicas}')

DESIRED_REPLICAS=$(kubectl get deployment psychsync-backend \
  -n psychsync -o jsonpath='{.spec.replicas}')

if [ "${READY_REPLICAS}" -eq "${DESIRED_REPLICAS}" ]; then
  echo "✅ All replicas ready: ${READY_REPLICAS}/${DESIRED_REPLICAS}"
else
  echo "❌ Replicas not ready: ${READY_REPLICAS}/${DESIRED_REPLICAS}"
  exit 1
fi

echo "All verification checks passed! ✅"
```

### Manual Testing Checklist

**User Authentication:**
- [ ] User can log in
- [ ] User can refresh token
- [ ] User can log out
- [ ] 2FA works correctly
- [ ] Password reset works

**Assessments:**
- [ ] List assessments loads
- [ ] Create assessment works
- [ ] View assessment details works
- [ ] Submit assessment response works
- [ ] View assessment results works

**Analytics:**
- [ ] Dashboard loads
- [ ] Charts render correctly
- [ ] Filters work
- [ ] Export data works

**Admin Functions:**
- [ ] Admin dashboard accessible
- [ ] User management works
- [ ] Security analytics loads
- [ ] Audit log search works

### Monitoring Verification

**Metrics to Check:**
- Error rate < 0.1%
- P95 latency < 500ms
- P50 latency < 100ms
- CPU < 70%
- Memory < 80%
- No crash loops

**Alerts to Verify:**
- No critical alerts firing
- No warning alerts (or explain expected warnings)
- Check Grafana dashboards
- Review CloudWatch alarms

**Log Analysis:**
```bash
# Check for errors in last 30 minutes
kubectl logs -l app=psychsync-backend -n psychsync \
  --since=30m | grep -i "error\|exception\|critical" | wc -l

# Check for warnings
kubectl logs -l app=psychsync-backend -n psychsync \
  --since=30m | grep -i "warning" | wc -l

# Review recent logs
kubectl logs -l app=psychsync-backend -n psychsync \
  --since=10m | tail -100
```

---

## Rollback Procedures

### When to Rollback

**Immediate Rollback (< 5 minutes):**
- Critical errors affecting all users
- Data corruption detected
- Security vulnerability identified
- Database migration failed

**Considered Rollback (< 30 minutes):**
- Error rate spike > 1%
- Significant performance degradation
- Critical feature not working
- Unexpected data issues

### Automated Rollback

**Kubernetes Rolling Update Rollback:**
```bash
# 1. Check rollout history
kubectl rollout history deployment/psychsync-backend -n psychsync

# 2. Rollback to previous version
kubectl rollout undo deployment/psychsync-backend -n psychsync

# 3. Watch rollback progress
kubectl rollout status deployment/psychsync-backend -n psychsync -w

# 4. Verify rollback success
kubectl get pods -n psychsync -l app=psychsync-backend
```

**Rollback to Specific Revision:**
```bash
# List revisions
kubectl rollout history deployment/psychsync-backend -n psychsync

# Rollback to specific revision
kubectl rollout undo deployment/psychsync-backend \
  --to-revision=3 -n psychsync
```

### Manual Rollback

**GitOps Rollback (ArgoCD):**
```bash
# 1. Identify previous good commit
git log --oneline -10

# 2. Revert to previous commit
git revert HEAD

# 3. Push to trigger deployment
git push origin main

# 4. ArgoCD will auto-deploy the reverted commit
```

**Database Rollback:**
```bash
# 1. Identify migration to rollback
alembic history

# 2. Rollback migration
alembic downgrade -1

# 3. Verify rollback
alembic current

# 4. If issues persist, restore from backup
./scripts/restore-postgres-production.sh \
  --timestamp 20251227-120000 \
  --force
```

### Rollback Verification

After rollback, verify:

```bash
# 1. Check pods are healthy
kubectl get pods -n psychsync

# 2. Check application health
curl -f https://api.psychsync.com/api/v1/health/public

# 3. Run smoke tests
pytest tests/integration/test_smoke.py -v

# 4. Check error rates dropped
# Review CloudWatch metrics

# 5. Verify data integrity
kubectl exec -it postgres-psychsync-0 -n psychsync \
  -- psql -U postgres -d psychsync \
  -c "SELECT COUNT(*) FROM users;"
```

---

## Emergency Deployments

### Emergency Hotfix Procedure

**When to Use:**
- Critical security fix
- Data loss bug
- Complete service outage
- Compliance issue

**Accelerated Process:**

1. **Skip Some Pre-Checks** (15 minutes)
   - Bypass full staging test
   - Bypass performance testing
   - Keep essential checks (unit tests, security scan)

2. **Fast-Track Review** (10 minutes)
   - Single reviewer approval
   - Focus on critical paths only

3. **Deploy with Monitoring** (20 minutes)
   - Deploy to production
   - Intensive monitoring
   - Ready to rollback immediately

4. **Post-Mortem Required**
   - Document root cause
   - Improve prevention
   - Update runbooks

**Emergency Hotfix Command:**
```bash
./scripts/deploy-production.sh \
  --version v1.2.4-hotfix \
  --skip-staging \
  --skip-performance-tests \
  --monitor-intensive \
  --auto-rollback-on-error
```

---

## Deployment Troubleshooting

### Common Issues

#### Issue 1: Pod Not Starting

**Symptoms:**
```
kubectl get pods -n psychsync
# NAME                                READY   STATUS             RESTARTS   AGE
# psychsync-backend-abc123           0/1     CrashLoopBackOff   5          5m
```

**Diagnosis:**
```bash
# Check pod events
kubectl describe pod psychsync-backend-abc123 -n psychsync

# Check pod logs
kubectl logs psychsync-backend-abc123 -n psychsync

# Check previous container logs
kubectl logs psychsync-backend-abc123 -n psychsync --previous
```

**Common Causes:**
- Application error on startup
- Missing environment variables
- Database connection failure
- Insufficient resources

**Solutions:**
```bash
# Check environment variables
kubectl exec -it psychsync-backend-abc123 -n psychsync -- env

# Check resource limits
kubectl describe pod psychsync-backend-abc123 -n psychsync | grep -A 5 Limits

# Scale up resources if needed
kubectl edit deployment psychsync-backend -n psychsync
# Update resources.limits.memory
```

#### Issue 2: Database Migration Failure

**Symptoms:**
```
alembic upgrade head
# ERROR: Can't execute upgrade command
```

**Diagnosis:**
```bash
# Check current migration version
alembic current

# Check pending migrations
alembic heads

# Check migration file for errors
alembic upgrade head --sql
```

**Solutions:**
```bash
# 1. Stamp current version if DB state is correct
alembic stamp head

# 2. Rollback and retry
alembic downgrade -1
alembic upgrade head

# 3. Manually fix migration
# Edit migration file and re-run
alembic upgrade head
```

#### Issue 3: High Memory/CPU Usage

**Diagnosis:**
```bash
# Check resource usage
kubectl top pods -n psychsync

# Check pod resource limits
kubectl get pod psychsync-backend-xyz -n psychsync \
  -o jsonpath='{.spec.containers[*].resources}'

# Check HPA status
kubectl get hpa -n psychsync
kubectl describe hpa psychsync-backend -n psychsync
```

**Solutions:**
```bash
# 1. Scale up deployment
kubectl scale deployment psychsync-backend --replicas=10 -n psychsync

# 2. Increase resource limits
kubectl edit deployment psychsync-backend -n psychsync

# 3. Adjust HPA thresholds
kubectl edit hpa psychsync-backend -n psychsync
```

#### Issue 4: Image Pull Errors

**Symptoms:**
```
# Failed to pull image "xyz": rpc error: code = Unknown
```

**Diagnosis:**
```bash
# Check image exists in ECR
aws ecr describe-images --repository-name psychsync-backend \
  --image-ids imageTag=v1.2.3

# Check ECR login
aws ecr get-login-password | docker login \
  --username AWS --password-stdin <ECR_REPO_URL>
```

**Solutions:**
```bash
# 1. Re-login to ECR
aws ecr get-login-password --region us-east-1 | docker login \
  --username AWS --password-stdin <ECR_REPO_URL>

# 2. Re-push image
docker push <ECR_REPO>/psychsync-backend:v1.2.3

# 3. Verify image permissions
aws ecr set-repository-policy \
  --repository-name psychsync-backend \
  --policy-text file://ecr-policy.json
```

---

## Communication Protocol

### Pre-Deployment Communication

**24 Hours Before:**
```
Subject: Scheduled Production Deployment - PsychSync v1.2.3

Team,

We will be deploying version 1.2.3 to production on DATE at TIME.

**Deployment Window:** START_TIME - END_TIME (ESTIMATED: 60 min)

**What's Included:**
- Feature 1: Description
- Feature 2: Description
- Database Migration: Description

**Expected Impact:**
- Downtime: None / 5 minutes / etc.
- Breaking Changes: List if any
- User Action Required: Yes/No

**Contact:**
Deployment Lead: NAME
Slack Channel: #deployment-YYYY-MM-DD

Please direct questions to #engineering.
```

### During Deployment Communication

**Start:**
```
🚀 Production deployment STARTING: v1.2.3
Deployment ID: deploy-20251227-143000
Lead: @name
Estimated duration: 60 minutes
```

**Progress Updates (every 15 minutes):**
```
⏳ Deployment UPDATE: Phase 3/5 - Database Migration
Status: In Progress
Next: Application deployment
ETA: 20 minutes
```

**Issues:**
```
⚠️ Deployment ISSUE: Database migration slow
Investigating: @name
Impact: May extend deployment by 15 minutes
Next update: 15 minutes
```

### Post-Deployment Communication

**Success:**
```
✅ Production deployment COMPLETE: v1.2.3

Duration: 45 minutes
Status: SUCCESS
Downtime: 0 minutes

Verification:
- All health checks passed ✅
- Smoke tests passed ✅
- Error rates normal ✅

Thank you for your patience!
Release notes: https://docs.psychsync.com/releases/v1.2.3
```

**Rollback:**
```
🔄 Deployment ROLLBACK: v1.2.3 → v1.2.2

Reason: High error rates detected
Rollback started: TIMESTAMP
Estimated completion: 5 minutes

Investigation ongoing in #incident-YYYY-MM-DD-HHMM
```

### Status Page Updates

**For Customer-Impacting Deployments:**

1. **24 Hours Before:**
   - Post "Scheduled Maintenance" notice
   - Include time window and expected impact

2. **During Deployment (if downtime):**
   - Change status to "Degraded Performance" or "Service Outage"
   - Update every 15 minutes

3. **After Deployment:**
   - Return to "All Systems Operational"
   - Post incident summary if issues occurred

---

## Deployment Metrics

### Track These Metrics

**Deployment Metrics:**
- Deployment frequency (per week/month)
- Lead time for changes (commit to deploy)
- Deployment failure rate
- Mean time to recovery (MTTR)
- Change failure rate

**Success Criteria:**
- Deployment success rate: ≥ 95%
- Rollback rate: ≤ 5%
- Deployment duration: ≤ 60 minutes
- Downtime: ≤ 5 minutes (rolling updates: 0)

**Dashboard:**
Monitor deployment metrics at: https://grafana.psychsync.com/d/deployment-metrics

---

## Appendices

### A. Deployment Script Full Reference

See: `scripts/deploy-production.sh`

Key options:
- `--environment`: staging/production
- `--version`: Version tag
- `--strategy`: rolling/blue-green/canary
- `--verify`: Run verification tests
- `--notify`: Send notifications
- `--dry-run`: Simulate only
- `--auto-rollback`: Auto-rollback on error detection

### B. Useful kubectl Commands

```bash
# Get all resources
kubectl get all -n psychsync

# Watch pod status
kubectl get pods -n psychsync -w

# Get pod logs (all containers)
kubectl logs -f deployment/psychsync-backend -n psychsync --all-containers=true

# Exec into pod
kubectl exec -it <pod-name> -n psychsync -- /bin/bash

# Port forward to local
kubectl port-forward deployment/psychsync-backend 8000:8000 -n psychsync

# Get events
kubectl get events -n psychsync --sort-by='.lastTimestamp'

# Describe resource
kubectl describe deployment psychsync-backend -n psychsync
```

### C. Emergency Contacts

| Role | Name | Slack | Phone |
|------|------|-------|-------|
| DevOps Lead | | @devops-lead | +1-XXX-XXX-XXXX |
| Engineering Manager | | @eng-manager | +1-XXX-XXX-XXXX |
| CTO | | @cto | +1-XXX-XXX-XXXX |
| On-Call Engineer | | @oncall | +1-XXX-XXX-XXXX |

### D. Related Documentation

- **Rollback Playbooks:** `docs/ROLLBACK_PLAYBOOKS.md`
- **Incident Response:** `docs/operations/INCIDENT_RESPONSE_RUNBOOK.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **Kubernetes Security:** `docs/KUBERNETES_CLOUD_SECURITY_SUMMARY.md`

---

**Document Status:** ✅ Approved

**Next Review Date:** 2026-03-27 (3 months)

**Change Log:**
- Version 1.0.0 (2025-12-27): Initial SOP creation
