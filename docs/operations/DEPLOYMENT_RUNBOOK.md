# 🚀 PsychSync Deployment Runbook

**Version**: 1.0
**Date**: 2025-12-27
**Environment**: Production

---

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Standard Deployment Procedure](#standard-deployment-procedure)
3. [Zero-Downtime Deployment](#zero-downtime-deployment)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Rollback Procedure](#rollback-procedure)
6. [Troubleshooting](#troubleshooting)

---

## ✅ Pre-Deployment Checklist

### Security Verification

- [ ] **Image Signature Verified**
  ```bash
  cosign verify \
    --certificate-identity "https://github.com/your-org/psychsync/.github/workflows/slsa-sign.yaml@refs/tags/${TAG}" \
    --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
    ghcr.io/your-org/psychsync:${TAG}
  ```

- [ ] **SLSA Provenance Verified**
  ```bash
  slsa-verifier verify-image \
    --source-uri github.com/your-org/psychsync \
    ghcr.io/your-org/psychsync:${TAG}
  ```

- [ ] **SBOM Downloaded and Reviewed**
  ```bash
  cosign download sbom ghcr.io/your-org/psychsync:${TAG} > sbom.spdx.json
  ```

### Infrastructure Readiness

- [ ] **Kubernetes Cluster Accessible**
  ```bash
  kubectl cluster-info
  kubectl get nodes
  ```

- [ ] **Namespace Exists**
  ```bash
  kubectl get namespace psychsync
  ```

- [ ] **Secrets Configured**
  ```bash
  kubectl get secrets -n psychsync
  kubectl describe secret psychsync-secrets -n psychsync
  ```

- [ ] **Database Migrations Ready**
  ```bash
  alembic current
  alembic history | head -20
  ```

### Monitoring Setup

- [ ] **Prometheus Targets Configured**
  ```bash
  kubectl get servicemonitor -n psychsync
  ```

- [ ] **Alerting Rules Loaded**
  ```bash
  kubectl get prometheusrule -n monitoring
  ```

- [ ] **Grafana Dashboards Imported**

- [ ] **Loki Logging Configured**

---

## 🚀 Standard Deployment Procedure

### Step 1: Prepare Release

```bash
# Set version
export TAG="v1.0.0"
export IMAGE="ghcr.io/your-org/psychsync:${TAG}"

# Verify image signature
./scripts/verify-quick.sh ${IMAGE}

# Pull image locally (optional, for testing)
docker pull ${IMAGE}
docker inspect ${IMAGE}
```

`★ Insight ─────────────────────────────────────`
Image verification before deployment is crucial for supply chain security. The Cosign verification ensures the image was built by your GitHub Actions workflow and hasn't been tampered with. This prevents supply chain attacks where malicious images could be substituted.
`─────────────────────────────────────────────────`

### Step 2: Run Database Migrations

```bash
# Backup database first
kubectl exec -n psychsync postgres-0 -- pg_dump -U postgres psychsync > backup-$(date +%Y%m%d).sql

# Run migrations
alembic upgrade head

# Verify migration status
alembic current
```

### Step 3: Update Kubernetes Deployment

```bash
# Update image tag in deployment
kubectl set image deployment/psychsync psychsync=${IMAGE} -n psychsync

# Or apply updated manifest
kubectl apply -f deploy/kubernetes/psychsync-deployment.yaml

# Watch rollout status
kubectl rollout status deployment/psychsync -n psychsync
```

### Step 4: Monitor Rollout

```bash
# Watch pods starting
kubectl get pods -n psychsync -l app=psychsync -w

# Check pod logs
kubectl logs -f -n psychsync -l app=psychsync --tail=100

# Check pod events
kubectl get events -n psychsync --field-selector involvedObject.kind=Pod
```

### Step 5: Verify Health

```bash
# Check pod readiness
kubectl get pods -n psychsync -l app=psychsync

# Check service endpoints
kubectl get endpoints psychsync -n psychsync

# Test health endpoint
kubectl exec -n psychsync deployment/psychsync -- curl -f http://localhost:8000/health

# Check application metrics
kubectl exec -n psychsync deployment/psychsync -- curl -f http://localhost:8000/metrics
```

---

## 🔄 Zero-Downtime Deployment

### Rolling Update Strategy

The deployment uses Kubernetes rolling updates with the following strategy:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # One extra pod during update
    maxUnavailable: 0  # No pods unavailable during update
```

### Execution Steps

```bash
# 1. Check current replicas
kubectl get deployment psychsync -n psychsync

# 2. Initiate rolling update
kubectl set image deployment/psychsync psychsync=${IMAGE} -n psychsync

# 3. Monitor the rollout in real-time
watch kubectl get pods -n psychsync -l app=psychsync

# 4. Watch application logs during transition
stern psychsync -n psychsync --tail 50

# 5. Verify no connection errors
kubectl logs -n psychsync -l app=psychsync --since=5m | grep -i error
```

### Health Check Configuration

The deployment includes probes to ensure readiness:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 3
```

### Verification During Rollout

```bash
# Monitor HTTP 5xx errors
kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/namespaces/psychsync/pods/*/http_requests_total{status="5xx"} | jq .

# Check response times
kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/namespaces/psychsync/pods/*/http_request_duration_seconds | jq .

# Verify database connection pool
kubectl exec -n psychsync deployment/psychsync -- curl -s http://localhost:8000/metrics | grep db_pool
```

`★ Insight ─────────────────────────────────────`
Zero-downtime deployments rely on Kubernetes gradually replacing pods. The `maxUnavailable: 0` setting ensures all old pods remain healthy until new ones pass readiness checks. The `maxSurge: 1` allows one extra pod temporarily to maintain capacity during the transition.
`─────────────────────────────────────────────────`

---

## ✅ Post-Deployment Verification

### Health Checks

```bash
# 1. All pods ready
kubectl get pods -n psychsync -l app=psychsync

# Expected output: All pods Running and Ready
# NAME                         READY   STATUS    RESTARTS   AGE
# psychsync-7d9f8c5b6-xhv2g   1/1     Running   0          2m
# psychsync-7d9f8c5b6-xkp8m   1/1     Running   0          3m
# psychsync-7d9f8c5b6-xqz9p   1/1     Running   0          4m

# 2. Service endpoints ready
kubectl get endpoints psychsync -n psychsync

# Expected: At least 3 ready addresses
# NAME         ENDPOINTS                                   AGE
# psychsync    10.244.1.5:8000,10.244.2.7:8000,...        30d

# 3. HPA metrics
kubectl get hpa psychsync -n psychsync

# Expected: Target metrics at normal levels
# NAME         REFERENCE                       TARGETS         MINPODS   MAXPODS   REPLICAS
# psychsync    Deployment/psychsync            50%/80%         3         10        3
```

### Application Verification

```bash
# 1. Test health endpoint
curl -f https://api.psychsync.ai/health
# Expected: {"status": "healthy"}

# 2. Test API endpoint
curl -f https://api.psychsync.ai/api/v1/health
# Expected: {"status": "ok", "version": "v1.0.0"}

# 3. Check authentication
curl -f https://api.psychsync.ai/api/v1/auth/test
# Expected: 401 Unauthorized (working correctly)

# 4. Check metrics endpoint (secured)
kubectl exec -n psychsync deployment/psychsync -- curl -f http://localhost:8000/metrics | head -20
```

### Smoke Tests

```bash
# Run integration tests
pytest tests/integration/ -v -m smoke

# Test critical endpoints
./scripts/smoke-test.sh https://api.psychsync.ai

# Verify database connectivity
kubectl exec -n psychsync deployment/psychsync -- python -c "
from app.core.database import engine
print('Database connection:', 'OK' if engine else 'FAILED')
"
```

### Monitoring Verification

```bash
# 1. Check Prometheus targets
curl -s http://prometheus.monitoring:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="psychsync") | .health'

# Expected: "up"

# 2. Verify metrics being scraped
curl -s http://prometheus.monitoring:9090/api/v1/query?query=up{job="psychsync"} | jq .

# 3. Check Grafana dashboards
curl -s http://grafana.monitoring:3000/api/search | jq '.[] | select(.type=="dash-db") | .title'

# 4. Verify alert rules
kubectl get prometheusrule -n monitoring -l app=psychsync
```

### Performance Baseline

```bash
# Check response times
kubectl logs -n psychsync -l app=psychsync --since=5m | grep "duration_ms" | awk '{print $NF}' | sort -n | tail -10

# Check error rate
kubectl logs -n psychsync -l app=psychsync --since=5m | grep -c "ERROR"

# Check database query performance
kubectl logs -n psychsync -l app=psychsync --since=5m | grep "db_query_time" | awk '{sum+=$NF; count++} END {print "Avg:", sum/count, "ms"}'
```

---

## 🔄 Rollback Procedure

### Immediate Rollback (Quick)

```bash
# 1. Check previous revisions
kubectl rollout history deployment/psychsync -n psychsync

# 2. Rollback to previous version
kubectl rollout undo deployment/psychsync -n psychsync

# 3. Watch rollback
kubectl rollout status deployment/psychsync -n psychsync

# 4. Verify rollback
kubectl get pods -n psychsync -l app=psychsync
kubectl logs -f -n psychsync -l app=psychsync --tail=50
```

### Rollback to Specific Revision

```bash
# 1. View revision history
kubectl rollout history deployment/psychsync -n psychsync

# REVISION  CHANGE-CAUSE
# 15        Upgrade to v1.0.1
# 14        Upgrade to v1.0.0
# 13        Initial deployment

# 2. Rollback to specific revision
kubectl rollout undo deployment/psychsync -n psychsync --to-revision=14

# 3. Verify
kubectl get pods -n psychsync -l app=psychsync
kubectl describe deployment psychsync -n psychsync | grep Image
```

### Database Rollback (if needed)

```bash
# 1. Check current migration version
alembic current

# 2. View migration history
alembic history

# 3. Downgrade to specific version
alembic downgrade <previous_revision>

# 4. Verify schema
alembic check
```

### Emergency Rollback (Full Restoration)

```bash
# 1. Scale down current deployment
kubectl scale deployment psychsync -n psychsync --replicas=0

# 2. Restore previous image from backup
export PREVIOUS_IMAGE="ghcr.io/your-org/psychsync:v0.9.0"
kubectl set image deployment/psychsync psychsync=${PREVIOUS_IMAGE} -n psychsync

# 3. Restore database from backup
kubectl exec -i -n psychsync postgres-0 -- psql -U postgres psychsync < backup-20251227.sql

# 4. Scale up
kubectl scale deployment psychsync -n psychsync --replicas=3

# 5. Verify
kubectl rollout status deployment/psychsync -n psychsync
```

### Post-Rollback Verification

```bash
# 1. Verify image version
kubectl describe deployment psychsync -n psychsync | grep Image

# 2. Test health endpoints
curl -f https://api.psychsync.ai/health

# 3. Run smoke tests
pytest tests/integration/ -v -m smoke

# 4. Check error logs
kubectl logs -n psychsync -l app=psychsync --since=5m | grep -i error
```

---

## 🔧 Troubleshooting

### Pods Not Starting

**Symptoms**: Pods stuck in Pending or CrashLoopBackOff

**Diagnosis**:
```bash
# 1. Check pod status
kubectl get pods -n psychsync -l app=psychsync

# 2. Describe pod
kubectl describe pod <pod-name> -n psychsync

# 3. Check logs
kubectl logs <pod-name> -n psychsync

# 4. Check events
kubectl get events -n psychsync --sort-by='.lastTimestamp'
```

**Common Solutions**:

- **Image pull error**: Check image tag and registry credentials
  ```bash
  kubectl get secret psychsync-secrets -n psychsync -o jsonpath="{.data\.dockerconfigjson}" | base64 -d
  ```

- **Resource limits**: Check node capacity
  ```bash
  kubectl describe nodes | grep -A 5 "Allocated resources"
  ```

- **ConfigMap missing**: Verify configuration
  ```bash
  kubectl get configmap -n psychsync
  kubectl describe configmap psychsync-config -n psychsync
  ```

### Health Check Failures

**Symptoms**: Pods marked Unhealthy

**Diagnosis**:
```bash
# 1. Check probe configuration
kubectl describe pod <pod-name> -n psychsync | grep -A 10 Liveness

# 2. Test health endpoint manually
kubectl exec <pod-name> -n psychsync -- curl -v http://localhost:8000/health

# 3. Check application logs
kubectl logs <pod-name> -n psychsync | grep -i health
```

**Common Solutions**:

- **Startup timeout**: Increase `initialDelaySeconds`
- **Database connection**: Verify database connectivity
- **Port binding**: Ensure application listens on 0.0.0.0

### High Memory/CPU Usage

**Diagnosis**:
```bash
# 1. Check resource usage
kubectl top pods -n psychsync -l app=psychsync

# 2. Check resource limits
kubectl describe deployment psychsync -n psychsync | grep -A 10 Resources

# 3. Check VPA recommendations
kubectl get vpa psychsync-vpa -n psychsync -o yaml
```

**Solutions**:

- **Adjust limits**: Update resource limits in deployment
- **Scale horizontally**: HPA will auto-scale if needed
- **Profile memory**: Use memory profiler to identify leaks

### Image Verification Failures

**Symptoms**: Init container fails during image verification

**Diagnosis**:
```bash
# 1. Check init container logs
kubectl logs <pod-name> -n psychsync -c verify-image

# 2. Manually verify image
cosign verify \
  --certificate-identity "https://github.com/your-org/psychsync/.github/workflows/slsa-sign.yaml@refs/tags/${TAG}" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/your-org/psychsync:${TAG}
```

**Solutions**:

- **Wrong identity**: Update certificate-identity in ConfigMap
- **Expired signature**: Rebuild and sign image
- **Network issue**: Check connectivity to sigstore

---

## 📞 Escalation

### Contact Information

| Role | Contact | Availability |
|------|---------|--------------|
| **On-Call Engineer** | oncall@psychsync.ai | 24/7 |
| **Tech Lead** | techlead@psychsync.ai | Business hours |
| **CTO** | cto@psychsync.ai | Emergency only |

### Severity Levels

**P0 - Critical**: Production down, total outage
- Response time: 15 minutes
- Examples: All pods crashed, database down, complete API failure

**P1 - High**: Major functionality broken
- Response time: 1 hour
- Examples: API errors > 50%, authentication failing, critical features down

**P2 - Medium**: Partial degradation
- Response time: 4 hours
- Examples: Elevated error rates, performance degradation, non-critical features broken

**P3 - Low**: Minor issues
- Response time: 1 business day
- Examples: UI bugs, documentation errors, minor performance issues

---

## 📚 Related Documentation

- **Supply Chain Security**: `/docs/SUPPLY_CHAIN_SECURITY.md`
- **SLSA Quick Start**: `/docs/SUPPLY_CHAIN_QUICKSTART.md`
- **Kubernetes Manifests**: `/deploy/kubernetes/psychsync-deployment.yaml`
- **Incident Response**: `/docs/operations/INCIDENT_RESPONSE_RUNBOOK.md`

---

**Last Updated**: 2025-12-27
**Maintained By**: DevOps Team <devops@psychsync.ai>
