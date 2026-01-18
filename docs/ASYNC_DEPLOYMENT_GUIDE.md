# Async Conversion Deployment Guide

**Version**: 1.0
**Date**: 2026-01-18
**Status**: Ready for Production

---

## 📋 Pre-Deployment Checklist

### Code Review
- [x] All type mismatches fixed
- [x] All non-existent methods implemented
- [x] All sync db.query() calls wrapped
- [x] All files compile successfully
- [ ] Code reviewed by senior developer
- [ ] Architecture update documented

### Testing
- [ ] Unit tests pass: `pytest tests/api/test_async_response_endpoints.py -v`
- [ ] Load tests pass: `python tests/load_test_async_endpoints.py`
- [ ] Integration tests pass: `pytest tests/integration/ -v`
- [ ] Manual testing completed on staging
- [ ] Performance benchmarks within acceptable range

### Monitoring
- [ ] Prometheus metrics configured
- [ ] Grafana dashboards created
- [ ] Alert rules configured
- [ ] Health check endpoints deployed
- [ ] Log aggregation configured

### Documentation
- [x] Async conversion complete report generated
- [x] Monitoring guide created
- [x] Deployment checklist created
- [ ] Runbook updated
- [ ] Team notified of changes

---

## 🚀 Deployment Steps

### Phase 1: Preparation (30 minutes before)

```bash
# 1. Create deployment branch
git checkout -b deploy/async-conversion-fixes

# 2. Verify all changes are committed
git status

# 3. Run pre-deployment validation
./scripts/deploy_async_fixes.sh

# 4. Backup current deployment
./scripts/backup_production.sh
```

### Phase 2: Staging Deployment (1 hour before)

```bash
# 1. Deploy to staging
ssh staging-server "cd /app/psychsync && git pull origin deploy/async-conversion-fixes"

# 2. Install dependencies
ssh staging-server "cd /app/psychsync && pip install -r requirements.txt"

# 3. Run database migrations (if any)
ssh staging-server "cd /app/psychsync && alembic upgrade head"

# 4. Restart staging services
ssh staging-server "systemctl restart psychsync-staging"

# 5. Verify staging health
curl http://staging.example.com/api/v1/health/async

# 6. Run smoke tests
./scripts/smoke_tests.sh staging
```

### Phase 3: Load Testing Staging (30 minutes)

```bash
# Run load tests against staging
python tests/load_test_async_endpoints.py http://staging.example.com

# Verify performance is acceptable
# P95 < 500ms, error rate < 1%, no blocking detected
```

### Phase 4: Production Deployment (During low-traffic window)

```bash
# 1. Notify team of deployment
# Post in Slack: "Deploying async conversion fixes in 5 minutes"

# 2. Create deployment point
git tag -a v1.0.0-async-fixes -m "Async conversion fixes"
git push origin v1.0.0-async-fixes

# 3. Deploy to production (blue-green deployment)
./scripts/deploy_production_blue_green.sh

# 4. Or rolling deployment (if using Kubernetes)
kubectl rollout restart deployment/psychsync-api

# 5. Monitor deployment progress
./scripts/monitor_deployment.sh
```

### Phase 5: Verification (15 minutes after)

```bash
# 1. Check production health
curl http://api.example.com/api/v1/health/async

# 2. Monitor error rates
curl -s http://prometheus:9090/api/v1/query?query=rate(async_endpoint_requests_total{status=~"5.."}[5m])

# 3. Check response times
curl -s http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,rate(async_endpoint_duration_seconds_bucket[5m]))

# 4. View Grafana dashboard
open https://grafana.example.com/d/async-endpoints

# 5. Check logs for errors
kubectl logs -f deployment/psychsync-api --tail=100 | grep -i error
```

---

## 📊 Monitoring During Deployment

### First 15 Minutes (Critical Period)

**Watch these metrics**:

1. **Error Rate** (should stay < 1%)
   ```
   rate(async_endpoint_requests_total{status=~"5.."}[5m])
   ```

2. **P95 Latency** (should stay < 500ms)
   ```
   histogram_quantile(0.95, rate(async_endpoint_duration_seconds_bucket[5m]))
   ```

3. **Blocking Detection** (should stay at 0)
   ```
   async_endpoint_blocking_detected
   ```

4. **Active Requests** (should scale with load)
   ```
   async_active_requests
   ```

### Dashboard Alerts

Set up these alerts in Slack:

```
🚨 CRITICAL: Async endpoint error rate > 5%
🟡 WARNING: Async endpoint P95 > 1s
🟡 WARNING: Blocking operations detected
```

---

## 🔄 Rollback Plan

### When to Rollback

- Error rate > 5% for more than 2 minutes
- P95 latency > 2s for more than 5 minutes
- Any 500 errors on critical endpoints
- Database connection failures
- Memory leaks detected

### Rollback Steps

```bash
# Option 1: Git revert (fastest)
git revert <async-conversion-commit>
git push origin main
kubectl rollout restart deployment/psychsync-api

# Option 2: Blue-green switch (if using blue-green)
kubectl patch service psychsync-api -p '{"spec":{"selector":{"version":"old"}}}'

# Option 3: Feature flag (if implemented)
curl -X POST http://api.example.com/api/v1/admin/features/async-conversion/disable

# Verify rollback
curl http://api.example.com/api/v1/health
```

### Post-Rollback

1. Investigate root cause
2. Fix issue in staging
3. Re-test thoroughly
4. Schedule new deployment attempt
5. Document lessons learned

---

## 📈 Post-Deployment Validation

### First Hour Checklist

- [ ] Error rate < 1%
- [ ] P95 latency < 500ms
- [ ] No blocking operations detected
- [ ] Request rate stable (no drops)
- [ ] Memory usage stable (no leaks)
- [ ] CPU usage normal
- [ ] Database connection pool healthy
- [ ] No unexpected log entries

### First Day Monitoring

Assign on-call engineer to monitor:

**Hour 1-2**: Check every 10 minutes
**Hour 3-6**: Check every 30 minutes
**Hour 7-24**: Check hourly

### Automated Checks

```bash
# Run automated validation every hour
cron: 0 * * * * /app/psychsync/scripts/hourly_health_check.sh
```

---

## 🐛 Troubleshooting

### Issue: High Error Rate After Deployment

**Diagnosis**:
```bash
# Check error types
kubectl logs deployment/psychsync-api --tail=500 | grep ERROR | sort | uniq -c

# Check specific endpoint
curl -v http://api.example.com/api/v1/responses/test-id
```

**Common Causes**:
1. Missing environment variables
2. Database migration not run
3. Dependency version mismatch
4. Feature flag not enabled

**Fix**: Address root cause, then redeploy

### Issue: Slow Response Times

**Diagnosis**:
```bash
# Check P95 latency
curl -s http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,rate(async_endpoint_duration_seconds_bucket[5m])) | jq .

# Check for blocking
curl -s http://prometheus:9090/api/v1/query?query=async_endpoint_blocking_detected | jq .
```

**Common Causes**:
1. Database queries not optimized
2. External API slow
3. Network latency
4. Insufficient resources

**Fix**: Add caching, optimize queries, scale up

### Issue: Memory Leaks

**Diagnosis**:
```bash
# Check memory usage
kubectl top pod -l app=psychsync-api

# Check for growing memory
kubectl exec -it deployment/psychsync-api -- memory_profiler
```

**Common Causes**:
1. Unclosed connections
2. Large objects not released
3. Event loop issues

**Fix**: Restart services, investigate memory profile

---

## 📞 Communication Plan

### Pre-Deployment (1 day before)

```
Subject: Scheduled Deployment: Async Conversion Fixes

Team,

We will be deploying critical async conversion fixes tomorrow at 2 AM UTC.

What's changing:
- Fixed type mismatches in helper functions
- Added missing service methods
- Wrapped all blocking database operations

Impact:
- Zero downtime expected
- No API contract changes
- Performance should improve

Monitoring:
- Watch Slack alerts for any issues
- On-call: @engineer-name

Questions? Reply all.
```

### Post-Deployment (after successful deploy)

```
Subject: ✅ Deployment Complete: Async Conversion Fixes

Team,

Async conversion fixes have been successfully deployed to production.

Results:
- All health checks passing
- Error rate: 0.1% (baseline: 0.2%)
- P95 latency: 120ms (baseline: 180ms)
- No blocking operations detected

Monitoring continues for next 24 hours.

Great work team! 🎉
```

### Post-Rollback (if needed)

```
Subject: ⚠️ Rollback Executed: Async Conversion Fixes

Team,

Async conversion fixes have been rolled back due to:
[REASON]

Root cause under investigation.

New deployment scheduled for:
[DATE/TIME]

On-call: @engineer-name
```

---

## ✅ Final Sign-Off

### Approval Required

- [ ] Tech Lead: _______________
- [ ] QA Lead: _______________
- [ ] DevOps Lead: _____________
- [ ] Product Owner: ___________

### Deployment Sign-Off

**Deployed by**: _______________
**Deployment time**: _______________
**Version**: v1.0.0-async-fixes
**Status**: [ ] Success [ ] Rolled Back

### Post-Deployment Review

**Scheduled**: [ ] Yes [ ] No
**Date**: _______________
**Attendees**: _______________

---

## 📚 Related Documents

- [Async Conversion Complete Report](../ASYNC_CONVERSION_COMPLETE.md)
- [Monitoring Guide](./ASYNC_MONITORING_GUIDE.md)
- [Runbook](../RUNBOOK.md)
- [Architecture Diagrams](../ARCHITECTURE.md)

---

**Questions? Contact**: #engineering-deployments
**Emergency Page**: @on-call-engineer
