# 🚀 Deployment Guide - External Integration Retry Logic

## ✅ Pre-Deployment Checklist

### 1. Code Review
- [x] All modified files reviewed
- [x] Retry logic implementation verified
- [x] Timeout configurations validated
- [x] Tests passing
- [x] Git commit created

### 2. Testing
```bash
# Run validation script
python validate_retry_improvements.py

# Run integration tests (if environment supports)
pytest tests/integrations/test_external_service_retry.py -v

# Verify imports
python -c "from app.core.monitoring.retry_metrics import retry_tracker; print('✓ OK')"
```

### 3. Configuration
Add to `.env` or `.env.prod` (optional - defaults are good):

```bash
# Retry Configuration
RETRY_MAX_ATTEMPTS=3
RETRY_TIMEOUT_SHORT=10
RETRY_TIMEOUT_MEDIUM=30
RETRY_TIMEOUT_LONG=300
RETRY_MULTIPLIER=1.0
RETRY_MIN_WAIT=1.0
RETRY_MAX_WAIT=10.0
RETRY_BACKOFF_BASE=2
```

## 📋 Deployment Steps

### Step 1: Backup Current State
```bash
# Create backup branch
git branch backup-before-retry-logic

# Or create a tag
git tag pre-retry-logic-implementation
```

### Step 2: Review the Commit
```bash
# View commit details
git log -1 --stat

# View the diff
git show HEAD --stat
```

### Step 3: Deploy to Staging
```bash
# Merge to staging branch
git checkout staging
git merge feature/security-service-migration

# Push to remote
git push origin staging
```

### Step 4: Monitor Staging (1-2 hours)
```python
# In Python shell or monitoring script:
from app.core.monitoring.retry_metrics import get_retry_summary

summary = get_retry_summary(hours=1)
print(f"Overall retry rate: {summary['overall_retry_rate']:.2f}%")
print(f"Overall failure rate: {summary['overall_failure_rate']:.2f}%")
print(f"High retry integrations: {summary['integrations_with_high_retry_rate']}")
```

**Expected results in staging:**
- Overall retry rate: < 20%
- Failure rate: < 5%
- No circuit breaker activations > 5/hour

### Step 5: Deploy to Production
```bash
# Merge to main
git checkout main
git merge feature/security-service-migration

# Push to remote
git push origin main

# Or use your deployment pipeline
# kubectl apply -f deployment.yaml
# ansible-playbook deploy.yml
```

## 📊 Post-Deployment Monitoring

### Immediate Monitoring (First Hour)

```python
from app.core.monitoring.retry_metrics import (
    retry_tracker,
    get_retry_summary,
    get_retry_metrics
)

# Check overall health
summary = get_retry_summary(hours=1)
alerts = await retry_tracker.check_and_alert()

for alert in alerts:
    print(f"⚠️ {alert}")
```

### Metrics to Watch

1. **Overall Retry Rate**
   - Green: < 20%
   - Yellow: 20-30%
   - Red: > 30%

2. **Failure Rate**
   - Green: < 5%
   - Yellow: 5-10%
   - Red: > 10%

3. **Individual Integration Health**
   ```python
   integrations = ["openai", "fcm", "splunk", "s3", "sendgrid"]

   for integration in integrations:
       metrics = get_retry_metrics(integration, hours=1)
       print(f"{integration}:")
       print(f"  Retry rate: {metrics.retry_rate:.2f}%")
       print(f"  Failure rate: {metrics.failure_rate:.2f}%")
       print(f"  Avg duration: {metrics.avg_duration_ms:.0f}ms")
   ```

### Prometheus Metrics Setup

Add to your metrics exporter:

```python
from fastapi import Response
from app.core.monitoring.retry_metrics import retry_tracker

@app.get("/metrics/retry")
async def retry_metrics():
    """Export retry metrics for Prometheus"""
    return Response(
        content=retry_tracker.export_prometheus_metrics(),
        media_type="text/plain"
    )
```

Grafana dashboard queries:
```promql
# Overall retry rate
rate(external_integration_retry_attempts_total[5m])

# Per-integration retry rates
rate(external_integration_retry_rate{integration="openai"}[5m])

# Failure rates
rate(external_integration_failure_rate[5m])
```

## 🚨 Rollback Procedure

If critical issues detected:

### Option 1: Disable Retries (Quick)
```bash
# Set environment variable
export RETRY_MAX_ATTEMPTS=0

# Or add to .env
echo "RETRY_MAX_ATTEMPTS=0" >> .env

# Restart services
systemctl restart psychsync
# or
kubectl rollout restart deployment/psychsync
```

### Option 2: Increase Timeouts (If timeouts too aggressive)
```bash
export RETRY_TIMEOUT_MEDIUM=60
export RETRY_TIMEOUT_LONG=600
```

### Option 3: Full Rollback
```bash
# Revert to backup
git revert HEAD

# Or checkout previous commit
git checkout <previous-commit-hash>

# Redeploy
git push origin main
```

## 📈 Success Criteria

### Day 1 (First 24 hours)
- ✅ No increase in error rate
- ✅ No service degradation
- ✅ Retry rate < 25%
- ✅ Failure rate < 8%

### Week 1
- ✅ Retry rate stabilizes < 20%
- ✅ Failure rate < 5%
- ✅ No circuit breaker activations > 5/hour
- ✅ User-reported issues decreased

### Month 1
- ✅ Improved external service reliability
- ✅ Reduced support tickets for transient failures
- ✅ Better observability into external dependencies

## 🔧 Troubleshooting

### Issue: High Retry Rate (> 30%)

**Diagnosis:**
```python
summary = get_retry_summary(hours=1)
print(summary['high_retry_integrations'])
```

**Solutions:**
- Check if external service is degraded
- Verify network connectivity
- Consider increasing timeout
- Contact external service provider

### Issue: High Failure Rate (> 10%)

**Diagnosis:**
```python
metrics = get_retry_metrics("problematic-service", hours=1)
print(f"Failed attempts: {metrics.failed_attempts}")
print(f"Total attempts: {metrics.total_attempts}")
```

**Solutions:**
- Check API keys/credentials
- Verify service configuration
- Review external service status page
- Consider fallback mechanisms

### Issue: Circuit Breaker Activations

**Diagnosis:**
```python
metrics = get_retry_metrics("affected-service", hours=1)
print(f"Circuit opens: {metrics.circuit_breaker_opens}")
```

**Solutions:**
- Temporary: Increase circuit breaker threshold
- Long-term: Fix underlying service issues
- Implement better fallback mechanisms

## 📞 Support Contacts

For issues or questions:
1. Check logs: `tail -f logs/psychsync.log | grep retry`
2. Review metrics in monitoring dashboard
3. Check external service status pages
4. Contact team lead for critical issues

## 📚 Additional Resources

- Code Review: `git show HEAD`
- Test Coverage: `tests/integrations/test_external_service_retry.py`
- Documentation: `IMPLEMENTATION_COMPLETE.md`
- PR Description: `RETRY_LOGIC_IMPROVEMENTS.md`
- Technical Details: `RETRY_IMPROVEMENTS_SUMMARY.md`

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Review Status**: ✅ Approved / ⏳ Pending / ❌ Rejected
