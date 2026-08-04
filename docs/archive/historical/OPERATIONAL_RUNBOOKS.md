# Operational Runbooks: System Boundary Resilience

**Version**: 1.0
**Last Updated**: 2026-02-09
**Maintained By**: Platform Engineering Team

---

## Table of Contents

1. [Circuit Breaker Open](#runbook-circuit-breaker-open)
2. [External Service Degradation](#runbook-external-service-degradation)
3. [Cache Layer Failure](#runbook-cache-layer-failure)
4. [OAuth Token Refresh Failures](#runbook-oauth-token-refresh-failures)
5. [Database Connection Pool Exhaustion](#runbook-database-connection-pool-exhaustion)
6. [High Error Rate on External API](#runbook-high-error-rate-on-external-api)
7. [Runbook Testing and Maintenance](#runbook-testing-and-maintenance)

---

<a name="runbook-circuit-breaker-open"></a>
## 🔴 Runbook: Circuit Breaker Open

**Severity**: P1 - Critical
**Escalation**: Platform Lead → Engineering Manager

### Symptoms
- API endpoints returning 503 errors
- High latency on specific operations
- Monitoring dashboard shows circuit breaker in OPEN state
- Alerts: "Circuit breaker '{name}' is OPEN"

### Diagnosis

#### 1. Check Circuit Breaker State
```bash
# Via API
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/circuit-breakers

# Via monitoring dashboard
# Navigate to: /admin/resilience
```

#### 2. Identify Affected Service
```json
{
  "circuit_breakers": [
    {
      "name": "hris_bamboohr",
      "state": "open",
      "failure_count": 5,
      "last_failure_time": "2026-02-09T10:15:30Z"
    }
  ]
}
```

#### 3. Check External Service Status
```bash
# Example: Check HRIS service health
curl -I https://api.bamboohr.com/api/v1/health

# Check service status page
# Example: https://status.bamboohr.com
```

### Resolution Steps

#### Immediate Actions (Minutes 0-5)

1. **Verify External Service Status**
   - Check external service status page
   - Test connectivity to external service
   - Review external service incidents

2. **Check Circuit Breaker Configuration**
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     https://api.psychsync.com/api/v1/resilience/circuit-breakers/hris_bamboohr
   ```

3. **Review Recent Logs**
   ```bash
   # Look for error patterns
   journalctl -u psychsync -n 1000 | grep -i "hris_bamboohr\|circuit breaker"
   ```

#### Short-term Actions (Minutes 5-15)

4. **If External Service is Down**
   - Wait for external service recovery
   - Circuit will automatically attempt recovery after `recovery_timeout` (30-60s)
   - No manual intervention needed

5. **If External Service is Up but Circuit is Still Open**
   - Verify authentication credentials are valid
   - Check for rate limiting on external service
   - Review recent code changes affecting integration

6. **Consider Manual Reset (ONLY if service is verified healthy)**
   ```bash
   # WARNING: Only reset if external service is confirmed healthy
   curl -X POST \
     -H "Authorization: Bearer $TOKEN" \
     https://api.psychsync.com/api/v1/resilience/circuit-breakers/hris_bamboohr/reset
   ```

#### Long-term Actions (Hours 1-24)

7. **Tune Circuit Breaker Settings**
   - If service is legitimately slow: increase `timeout`
   - If service is flaky: adjust `failure_threshold`
   - If recovering too slowly: decrease `recovery_timeout`

8. **Implement Fallback Logic**
   - Add cached data fallback
   - Implement graceful degradation
   - Add user-friendly error messages

9. **Post-Incident Review**
   - Document root cause
   - Update runbook with learnings
   - Create preventive measures

### Prevention

1. **Monitor External Service Health**
   - Set up uptime monitoring for all dependencies
   - Configure alerts for external service degradation

2. **Load Testing**
   - Regular chaos testing of external integrations
   - Validate circuit breaker settings under load

3. **Documentation**
   - Keep external service contact information up to date
   - Document API rate limits and quotas

---

<a name="runbook-external-service-degradation"></a>
## 🟡 Runbook: External Service Degradation

**Severity**: P2 - High
**Escalation**: Service Owner → Platform Lead

### Symptoms
- Increased response times
- Elevated error rates but not total failures
- Circuit breaker in HALF_OPEN or approaching OPEN state
- User complaints about slowness

### Diagnosis

#### 1. Check Service Performance Metrics
```bash
# Get detailed metrics for specific circuit breaker
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/circuit-breakers/email_oauth

# Look at success rate and avg response time
```

#### 2. Check External Service Metrics
```bash
# Example: Check Google API performance
curl https://www.googleapis.com/oauth2/v1/tokeninfo
```

### Resolution Steps

#### Immediate Actions

1. **Verify Service Degradation**
   - Check external service dashboard
   - Review error rates and latency
   - Identify degradation pattern (consistent vs intermittent)

2. **Enable Graceful Degradation**
   - Switch to cached data where possible
   - Implement request queuing for non-critical operations
   - Show user-friendly "experiencing delays" messages

#### Short-term Actions

3. **Adjust Timeout Settings**
   - If service is slow: increase timeout temporarily
   - Monitor for improvement

4. **Reduce Request Rate**
   - Implement client-side rate limiting
   - Batch requests where possible
   - Defer non-critical operations

#### Long-term Actions

5. **Optimize Integration**
   - Reduce number of API calls
   - Implement more aggressive caching
   - Use bulk operations

6. **Service Level Agreement (SLA) Review**
   - Evaluate if external service meets requirements
   - Consider backup providers

---

<a name="runbook-cache-layer-failure"></a>
## 🟡 Runbook: Cache Layer Failure

**Severity**: P2 - High
**Escalation**: Platform Lead

### Symptoms
- Increased database load
- Slower API response times
- Circuit breaker `redis_cache` in OPEN state
- Alert: "Cache circuit breaker is OPEN"

### Diagnosis

#### 1. Check Redis Status
```bash
# Check if Redis is running
systemctl status redis

# Test Redis connection
redis-cli ping

# Check Redis logs
tail -f /var/log/redis/redis.log
```

#### 2. Check Circuit Breaker State
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/circuit-breakers/redis_cache
```

### Resolution Steps

#### Immediate Actions

1. **Verify Redis Health**
   ```bash
   # Check Redis info
   redis-cli INFO

   # Check memory usage
   redis-cli INFO memory

   # Check connection count
   redis-cli CLIENT LIST | wc -l
   ```

2. **If Redis is Down**
   - Start Redis service: `systemctl start redis`
   - Check for configuration errors
   - Verify sufficient memory/disk space

3. **System Continues Operating**
   - Application automatically falls back to database queries
   - No immediate action required
   - Expect higher database load and slower response times

#### Short-term Actions

4. **Restart Redis (if necessary)**
   ```bash
   systemctl restart redis
   ```

5. **Clear Cache (if corruption suspected)**
   ```bash
   redis-cli FLUSHDB
   ```

6. **Circuit Breaker Auto-Recovers**
   - After 30 seconds, circuit transitions to HALF_OPEN
   - Test calls will verify Redis is healthy
   - Circuit closes after successful calls

#### Long-term Actions

7. **Investigate Root Cause**
   - Check for memory exhaustion
   - Review Redis configuration
   - Analyze slow query logs

8. **Scale Redis**
   - Increase memory allocation
   - Consider Redis Cluster for high availability
   - Implement Redis Sentinel for automatic failover

9. **Optimize Cache Usage**
   - Review cache expiration policies
   - Implement cache size limits
   - Add monitoring for cache hit rates

### Prevention

1. **Redis Monitoring**
   - Set up alerts for Redis memory usage
   - Monitor cache hit/miss ratios
   - Track connection pool utilization

2. **High Availability**
   - Deploy Redis in cluster mode
   - Configure automatic failover
   - Regular backup of Redis data

---

<a name="runbook-oauth-token-refresh-failures"></a>
## 🟠 Runbook: OAuth Token Refresh Failures

**Severity**: P2 - High
**Escalation**: Integration Owner

### Symptoms
- Users unable to access email integration
- Alert: "OAuth token refresh failed"
- Circuit breaker `email_oauth` in OPEN state
- Increased authentication errors

### Diagnosis

#### 1. Check Affected Users
```sql
-- Find connections with recent token refresh failures
SELECT user_id, provider, sync_error_message
FROM email_connections
WHERE sync_status = 'error'
  AND sync_error_message LIKE '%token refresh%'
ORDER BY updated_at DESC
LIMIT 10;
```

#### 2. Check Circuit Breaker State
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/circuit-breakers/email_oauth
```

### Resolution Steps

#### Immediate Actions

1. **Verify OAuth Provider Status**
   - Check Google Workspace status: https://www.google.com/appsstatus
   - Check Microsoft 365 status: https://status.office.microsoft.com

2. **Check OAuth Credentials**
   - Verify client ID and secret are valid
   - Check for expired OAuth credentials
   - Review OAuth consent screen configuration

3. **Reset Circuit Breaker (after fixing issue)**
   ```bash
   curl -X POST \
     -H "Authorization: Bearer $TOKEN" \
     https://api.psychsync.com/api/v1/resilience/circuit-breakers/email_oauth/reset
   ```

#### Short-term Actions

4. **Force Token Refresh for Stale Connections**
   ```python
   # Example: Script to refresh tokens for affected users
   # See: app/scripts/refresh_stale_oauth_tokens.py
   ```

5. **Notify Affected Users**
   - Send email about temporary access issues
   - Provide workaround instructions if available
   - Set expectations for resolution time

#### Long-term Actions

6. **Refresh Token Rotation**
   - Implement periodic token refresh
   - Add monitoring for token expiration
   - Automate token refresh before expiration

7. **OAuth Configuration Review**
   - Verify correct OAuth scopes
   - Update redirect URIs if needed
   - Review rate limits on token endpoints

---

<a name="runbook-database-connection-pool-exhaustion"></a>
## 🔴 Runbook: Database Connection Pool Exhaustion

**Severity**: P0 - Critical
**Escalation**: Platform Lead → CTO

### Symptoms
- Application hangs or very slow
- Error: "Connection pool exhausted"
- High number of database connections
- API timeouts

### Diagnosis

#### 1. Check Database Connections
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- Find long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';

-- Check connection pool size
SHOW max_connections;
```

#### 2. Check Application Logs
```bash
# Look for connection pool errors
journalctl -u psychsync -n 1000 | grep -i "pool\|connection"
```

### Resolution Steps

#### Immediate Actions (Minutes 0-5)

1. **Identify Blocking Queries**
   ```sql
   SELECT pid, usename, pg_blocking_pids(pid) as blocked_by,
          query as blocked_query
   FROM pg_stat_activity
   WHERE cardinality(pg_blocking_pids(pid)) > 0;
   ```

2. **Terminate Long-Running Queries (CRITICAL)**
   ```sql
   -- Terminate specific problematic query
   SELECT pg_terminate_backend(pid);

   -- Terminate all queries in a specific database (USE WITH CAUTION)
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE datname = 'psychsync'
     AND pid != pg_backend_pid();
   ```

3. **Scale Application Temporarily**
   - Add more application instances if using connection pooling
   - Reduce traffic if possible (enable maintenance mode)

#### Short-term Actions (Minutes 5-30)

4. **Optimize Connection Pool Configuration**
   ```python
   # In app/core/database.py
   # Increase pool size if needed
   pool_size=30,  # Increase from 20
   max_overflow=50,  # Increase from 40
   ```

5. **Restart Application (if necessary)**
   ```bash
   systemctl restart psychsync
   ```

6. **Monitor Database Performance**
   ```bash
   # Check database metrics
   psql -U postgres -d psychsync -c "SELECT * FROM pg_stat_activity;"
   ```

#### Long-term Actions (Hours 1-24)

7. **Query Optimization**
   - Add database indexes for slow queries
   - Optimize N+1 query problems
   - Implement query result caching

8. **Connection Pool Tuning**
   - Review pool size vs application instances
   - Calculate optimal pool size: (instances × pool_size) < max_connections
   - Consider PgBouncer for connection pooling

9. **Implement Circuit Breaker for Database**
   - Already exists in codebase
   - Ensure it's properly configured

### Prevention

1. **Connection Pool Monitoring**
   - Set up alerts for pool utilization > 80%
   - Monitor average connection wait time
   - Track connection acquisition failures

2. **Query Performance Monitoring**
   - Enable slow query logging
   - Regular query performance reviews
   - Index optimization

3. **Load Testing**
   - Test under expected peak load
   - Validate connection pool configuration
   - Identify bottlenecks before production

---

<a name="runbook-high-error-rate-on-external-api"></a>
## 🟠 Runbook: High Error Rate on External API

**Severity**: P2 - High
**Escalation**: Integration Owner

### Symptoms
- Error rate > 10% on specific external API
- Circuit breaker approaching OPEN state
- User complaints about integration failures
- Monitoring shows elevated failure count

### Diagnosis

#### 1. Check Error Rate and Type
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/circuit-breakers/hris_bamboohr

# Look at success_rate and recent_failures_count
```

#### 2. Analyze Error Patterns
```bash
# Check logs for specific error types
journalctl -u psychsync -n 1000 | grep "hris_bamboohr" | grep -i "error\|exception"

# Categorize errors
# - Network errors (connection refused, timeout)
# - Authentication errors (401, 403)
# - Rate limiting (429)
# - Server errors (5xx)
```

### Resolution Steps

#### Immediate Actions

1. **Identify Error Type**
   - Network errors: Check connectivity, DNS, firewall
   - Auth errors: Verify credentials, API keys
   - Rate limiting: Implement backoff, reduce request rate
   - Server errors: Check external service status

2. **Implement Appropriate Mitigation**
   - Network: Enable retries with exponential backoff
   - Auth: Rotate credentials immediately
   - Rate limiting: Reduce request rate, implement queuing
   - Server errors: Switch to degraded mode, cached data

#### Short-term Actions

3. **Adjust Circuit Breaker Settings**
   - If errors are transient: Increase `failure_threshold`
   - If recovery is slow: Decrease `recovery_timeout`
   - If timeouts are too aggressive: Increase `timeout`

4. **Enable Debug Logging**
   ```python
   # In integration code
   import logging
   logging.getLogger("app.integrations.hris").setLevel(logging.DEBUG)
   ```

5. **Contact External Service Provider**
   - Check if there's a known issue
   - Verify API rate limits haven't changed
   - Confirm no recent API breaking changes

#### Long-term Actions

6. **Implement Retry with Exponential Backoff**
   - Already exists in resilience framework
   - Ensure it's properly configured

7. **Add Request/Response Logging**
   - Log failed requests for analysis
   - Implement structured logging
   - Add correlation IDs

8. **Review API Usage Patterns**
   - Identify inefficient API calls
   - Implement batching where possible
   - Add caching for frequently accessed data

---

<a name="runbook-testing-and-maintenance"></a>
## 📋 Runbook Testing and Maintenance

### Regular Maintenance Tasks

#### Weekly
- Review circuit breaker metrics
- Check external service status pages
- Analyze error patterns in logs
- Validate monitoring dashboards

#### Monthly
- Run chaos tests in staging environment
- Review and update runbooks
- Test manual recovery procedures
- Conduct post-incident reviews

#### Quarterly
- Load test external integrations
- Review and optimize timeout settings
- Update contact information for external services
- Training for on-call engineers

### Runbook Testing Procedure

1. **Simulate Incident**
   ```bash
   # Use toxiproxy to simulate network failures
   # https://github.com/Shopify/toxiproxy

   # Example: Simulate HRIS service failure
   toxiproxy-cli create hris-proxy -l localhost:8080 -u api.bamboohr.com:443
   toxiproxy-cli toxic hris-proxy -t latency -a latency=10000
   ```

2. **Verify Circuit Breaker Behavior**
   - Confirm circuit opens after threshold
   - Verify fast-fail when open
   - Test automatic recovery

3. **Update Runbook**
   - Document any issues found
   - Add new symptoms or resolution steps
   - Improve clarity and accuracy

### Runbook Review Checklist

- [ ] Contact information up to date
- [ ] External service links current
- [ ] Code examples tested
- [ ] Resolution steps validated
- [ ] Prevention measures relevant
- [ ] Last updated date accurate

---

## Appendix

### Useful Commands

```bash
# Check all circuit breaker states
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/circuit-breakers

# Get resilience alerts
curl -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/alerts

# Reset specific circuit breaker
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  https://api.psychsync.com/api/v1/resilience/circuit-breakers/{name}/reset

# View application logs
journalctl -u psychsync -f

# Check database connections
psql -U postgres -d psychsync -c "SELECT count(*) FROM pg_stat_activity;"

# Test Redis connection
redis-cli ping

# Run chaos tests
pytest tests/chaos/test_system_boundary_resilience.py -v
```

### Contact Information

| Role | Name | Email | Slack | On-Call |
|------|------|-------|-------|---------|
| Platform Lead | | | @platform-lead | Primary |
| Engineering Manager | | | @eng-manager | Escalation |
| CTO | | | @cto | Emergency |

### External Services

| Service | Status Page | Support | Documentation |
|---------|-------------|---------|---------------|
| Google Workspace | https://www.google.com/appsstatus | | https://developers.google.com/gmail |
| Microsoft 365 | https://status.office.microsoft.com | | https://docs.microsoft.com/graph |
| BambooHR | https://status.bamboohr.com | | https://www.bamboohr.com/api |
| Redis | https://redis.io | | https://redis.io/documentation |

---

**Document History:**
- v1.0 (2026-02-09): Initial creation - System boundary resilience runbooks

**Next Review Date:** 2026-05-09
