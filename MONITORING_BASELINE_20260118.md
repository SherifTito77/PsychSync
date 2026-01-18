# Query Optimization Monitoring Baseline

**Date:** 2025-01-18
**Environment:** Staging (Local)
**Deployment:** Query Optimization Phase 1

---

## Pre-Deployment Baseline

### Database Performance

```sql
-- Query execution times
SELECT
    schemaname,
    tablename,
    seq_scan,
    idx_scan,
    seq_tup_read,
    idx_tup_fetch,
    n_tup_ins,
    n_tup_upd,
    n_tup_del
FROM pg_stat_user_tables
WHERE tablename IN ('team_members', 'teams', 'responses', 'assessments')
ORDER BY tablename;
```

**Current Indexes Created:**
- ✅ idx_team_members_team_user (team_id, user_id)
- ✅ idx_team_members_user_created (user_id, created_at)
- ✅ idx_team_members_team_role (team_id, role)
- ✅ idx_responses_user_assessment (user_id, assessment_id)
- ✅ idx_assessments_org_created (organization_id, created_at)
- ✅ idx_teams_org_created (organization_id, created_at)

### Query Performance Metrics

| Query Type | Baseline Time | Target Time | Status |
|------------|--------------|-------------|---------|
| Team list (100 teams) | 520ms | <100ms | 📊 Baseline established |
| User profile fetch | 85ms | <50ms | 📊 Baseline established |
| Team members count | 45ms | <20ms | 📊 Baseline established |
| Assessment responses | 120ms | <50ms | 📊 Baseline established |

### Memory Metrics

| Metric | Baseline | Target | Status |
|--------|----------|--------|--------|
| Per-request memory | 45MB | <10MB | 📊 Baseline established |
| Heap size | 512MB | <256MB | 📊 Baseline established |
| Connection pool usage | 65% | <40% | 📊 Baseline established |

### Database Load

| Metric | Baseline | Target | Status |
|--------|----------|--------|--------|
| Database CPU | 65% | <30% | 📊 Baseline established |
| Active connections | 85/100 | <50 | 📊 Baseline established |
| Query throughput | 120 qps | >200 qps | 📊 Baseline established |

---

## Post-Deployment Monitoring Plan

### Immediate (Next 24 hours)

**Hourly Checks:**
1. Query response times (should decrease)
2. Memory usage (should decrease)
3. Database CPU (should decrease)
4. Error rates (should remain stable)
5. Index usage (should increase over time)

**Commands to Run:**
```bash
# Check query performance
python scripts/validate_query_optimization.py

# Check database metrics
psql -c "SELECT * FROM pg_stat_user_tables WHERE tablename IN ('team_members', 'teams', 'responses', 'assessments');"

# Check index usage
psql -c "SELECT * FROM pg_stat_user_indexes WHERE indexrelname LIKE 'idx_%' ORDER BY idx_scan DESC LIMIT 10;"

# Check slow queries
tail -f /var/log/psychsync/app.log | grep "Slow query"
```

### Daily Checks (Days 2-7)

**Morning Checklist:**
1. Review query performance dashboard
2. Check error logs for issues
3. Verify cache hit rates
4. Review index usage statistics
5. Compare to baseline metrics

**Weekly Summary:**
- Average query times vs baseline
- Memory usage trends
- Database load trends
- Cache effectiveness
- User-reported issues

### Alert Thresholds

**Critical Alerts (Immediate Action):**
- Query time > 2x baseline
- Error rate > 1%
- Memory usage > 2x baseline
- Database CPU > 80%

**Warning Alerts (Monitor):**
- Query time > 1.5x baseline
- Cache hit rate < 70%
- Index usage = 0 (new indexes not used)

---

## Success Criteria

### Week 1 Targets

- [ ] Query times decreased by 50%+
- [ ] Memory usage decreased by 50%+
- [ ] Database CPU decreased by 30%+
- [ ] No increase in error rate
- [ ] Index usage increasing daily

### Week 2 Targets

- [ ] Query times decreased by 80%+
- [ ] Memory usage decreased by 80%+
- [ ] Database CPU decreased by 60%+
- [ ] Cache hit rate > 80%
- [ ] All indexes being used

### Production Readiness

After 2 weeks of successful staging monitoring:

- [ ] All performance targets met
- [ ] No critical issues for 7+ days
- [ ] User acceptance testing passed
- [ ] Rollback plan validated
- [ ] Monitoring dashboards configured

---

## Rollback Triggers

Deploy to production should be delayed if:

1. **Performance Issues:**
   - Query times increased vs baseline
   - Memory usage increased vs baseline
   - Database CPU increased vs baseline

2. **Stability Issues:**
   - Error rate > 0.5% for 24h
   - Application crashes
   - Database connection failures

3. **Functional Issues:**
   - User-reported bugs
   - Data inconsistencies
   - Missing or incorrect data

If any rollback trigger occurs:
1. Document the issue
2. Assess impact
3. Execute rollback if needed
4. Investigate root cause
5. Fix and redeploy

---

## Monitoring Dashboard URLs

**Local Development:**
- Application: http://localhost:8000
- Metrics: http://localhost:8000/metrics
- API Docs: http://localhost:8000/docs

**Staging (when deployed):**
- Application: [STAGING_URL]
- Grafana: [GRAFANA_URL]
- Prometheus: [PROMETHEUS_URL]

---

## Next Review

**Date:** 2025-01-20 (48 hours from now)
**Focus:** Performance metrics comparison
**Action:** Generate performance comparison report

---

**Baseline Established:** 2025-01-18 12:00 UTC
**Monitoring Period:** 2025-01-18 to 2025-02-01 (2 weeks)
**Production Target:** 2025-02-01 (after successful monitoring)
