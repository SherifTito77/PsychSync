# 🚀 Resilience Improvements Deployment Checklist

**Date**: 2026-02-09
**Version**: 1.0
**Purpose**: Step-by-step guide for deploying resilience improvements

---

## ✅ Pre-Deployment Checklist

### Code Review
- [ ] All resilience patterns reviewed
- [ ] Chaos tests passing (19/19)
- [ ] No breaking changes introduced
- [ ] Documentation updated
- [ ] Runbooks reviewed and approved

### Testing
- [ ] Unit tests passing locally
- [ ] Chaos tests passing in staging
- [ ] Load testing completed (if applicable)
- [ ] Integration tests passing
- [ ] Manual testing of monitoring endpoints

### Rollback Plan
- [ ] Git branch tagged for rollback
- [ ] Database migrations reversible
- [ ] Feature flags configured (if needed)
- [ ] Communication plan prepared

---

## 📋 Deployment Steps

### Phase 1: Code Deployment (15 minutes)

#### 1.1 Create Feature Branch
```bash
git checkout -b feature/resilience-improvements
git add .
git commit -m "feat: add system boundary resilience improvements

- Circuit breaker protection for HRIS, Email, Cache layers
- Comprehensive chaos testing suite
- Real-time resilience monitoring API
- Operational runbooks for 6 incident scenarios
- CI/CD automation for chaos testing

See IMPLEMENTATION_SUMMARY_RESILIENCE.md for details"
```

#### 1.2 Run Final Tests
```bash
# Run chaos tests
pytest tests/chaos/test_system_boundary_resilience.py -v

# Run monitoring demo
PYTHONPATH=. python3 tests/chaos/demo_resilience_monitoring.py

# Check for import errors
python -c "from app.api.v1.endpoints.resilience_monitoring import router; print('✓ OK')"
```

#### 1.3 Merge to Main Branch
```bash
git checkout main
git merge feature/resilience-improvements
git push origin main
```

#### 1.4 Deploy to Production
```bash
# Using your deployment tool (Ansible, Docker, Kubernetes, etc.)
./deploy.sh production

# Or if using Docker:
docker-compose -f docker-compose.prod.yml up -d --build

# Or if using Kubernetes:
kubectl apply -f k8s/production/
kubectl rollout status deployment/psychsync-api
```

#### 1.5 Verify Deployment
```bash
# Check service health
curl https://api.psychsync.com/api/v1/health

# Check logs for errors
kubectl logs -f deployment/psychsync-api --tail=100

# Verify no exceptions
journalctl -u psychsync -n 1000 | grep -i error
```

---

### Phase 2: Monitoring Setup (10 minutes)

#### 2.1 Test Monitoring Endpoints
```bash
# Set auth token
TOKEN=$(curl -s https://api.psychsync.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"***"}' \
  | jq -r '.access_token')

# Test health endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/health

# Test circuit breakers endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/circuit-breakers

# Test alerts endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/alerts
```

#### 2.2 Verify Circuit Breakers Created
```bash
# Should show circuit breakers for:
# - hris_<connector_name>
# - email_oauth
# - redis_cache
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/circuit-breakers | jq '.circuit_breakers[].name'
```

#### 2.3 Run Initial Health Check
```bash
# Should show HEALTHY status
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/health | jq '.status'
```

---

### Phase 3: Validation (20 minutes)

#### 3.1 Monitor Circuit Breaker States
```bash
# Watch circuit breaker states for 5 minutes
watch -n 5 'curl -s -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/circuit-breakers | jq ".circuit_breakers[]"'
```

#### 3.2 Verify Error Rates
```bash
# Check for increased errors
# Should see no increase in error rates
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/alerts | jq '.summary'
```

#### 3.3 Test Integration Endpoints
```bash
# Test HRIS integration (if configured)
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/hris/test-connection

# Test email integration
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/email/test-connection
```

#### 3.4 Load Test (Optional)
```bash
# Run load test to verify circuit breakers work under load
# See: tests/chaos/test_system_boundary_resilience.py
pytest tests/chaos/test_system_boundary_resilience.py::TestRealWorldFailureScenarios -v
```

---

### Phase 4: Post-Deployment (15 minutes)

#### 4.1 Monitor Metrics
```bash
# Check circuit breaker metrics after 15 minutes
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/metrics | jq '.circuit_breakers'
```

#### 4.2 Verify Logs
```bash
# Check for circuit breaker events
kubectl logs deployment/psychsync-api --tail=500 | grep -i "circuit breaker"

# Should see:
# - "Circuit breaker X opened after Y failures" (if failures occur)
# - "Circuit breaker X transitioning to HALF_OPEN" (during recovery)
# - "Circuit breaker X reset to CLOSED" (after recovery)
```

#### 4.3 Document Any Issues
```bash
# Create deployment notes
cat > deployment-notes-$(date +%Y%m%d).md << EOF
# Deployment Notes - $(date +%Y-%m-%d)

## Deployment Summary
- **Branch**: feature/resilience-improvements
- **Commit**: $(git rev-parse --short HEAD)
- **Deployed At**: $(date)
- **Deployed By**: $(whoami)

## Status
✅ All systems operational

## Circuit Breakers
- HRIS: CLOSED (Healthy)
- Email OAuth: CLOSED (Healthy)
- Redis Cache: CLOSED (Healthy)

## Issues Encountered
None

## Next Steps
- Monitor for 24 hours
- Review circuit breaker metrics daily
- Update runbooks if needed
EOF
```

---

## 🚨 Rollback Procedure

### If Critical Issues Detected

#### Option 1: Quick Rollback (Git)
```bash
# Revert to previous commit
git revert HEAD
git push origin main

# Redeploy
./deploy.sh production
```

#### Option 2: Feature Flags
```bash
# If using feature flags
kubectl set env deployment/psychsync-api \
  RESILIENCE_ENABLED=false --overwrite

# Restart pods
kubectl rollout restart deployment/psychsync-api
```

#### Option 3: Database Rollback
```bash
# If migrations were applied
alembic downgrade -1

# Verify rollback
alembic current
```

---

## 📊 Post-Deployment Monitoring

### First Hour (Critical)
- Monitor circuit breaker states every 5 minutes
- Check error rates
- Review logs for circuit breaker events
- Verify no increase in latency

### First 24 Hours
- Monitor circuit breaker metrics hourly
- Review alerts and warnings
- Check for any OPEN circuits
- Verify automatic recovery working

### First Week
- Daily circuit breaker health check
- Review chaos test results
- Update runbooks as needed
- Plan next improvements

---

## ✅ Deployment Success Criteria

- [ ] All chaos tests passing
- [ ] No increase in error rate
- [ ] No degradation in response time
- [ ] Circuit breakers in CLOSED state
- [ ] Monitoring endpoints accessible
- [ ] No critical bugs reported
- [ ] Runbooks validated

---

## 📞 Contacts

| Role | Name | Slack | Email |
|------|------|-------|-------|
| Platform Lead | | @platform-lead | |
| Engineering Manager | | @eng-manager | |
| On-Call Engineer | | @on-call | |

---

## 📚 Related Documentation

- **SYSTEM_BOUNDARY_RESILIENCE_REPORT.md** - Technical details
- **OPERATIONAL_RUNBOOKS.md** - Incident procedures
- **IMPLEMENTATION_SUMMARY_RESILIENCE.md** - Executive summary
- **tests/chaos/test_system_boundary_resilience.py** - Test suite
- **.github/workflows/chaos-testing.yml** - CI/CD automation

---

**Deployment Checklist Version**: 1.0
**Last Updated**: 2026-02-09
**Next Review**: After first production deployment
