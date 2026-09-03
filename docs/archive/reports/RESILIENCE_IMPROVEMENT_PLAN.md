# Network Resiliency Improvement Plan

**Date:** 2026-02-11
**Status:** Active
**Priority:** High

## Executive Summary

This document outlines improvements to network resiliency across all integration points in the PsychSync platform. The goal is to ensure graceful degradation under network instability through retry logic, circuit breakers, and comprehensive monitoring.

---

## Current State Analysis

| Integration | Resilience Score | Issues |
|-------------|------------------|--------|
| HTTP Client | 9/10 | Minor: timeout configurations could be per-endpoint |
| Database | 8/10 | Medium: missing exponential backoff in retry logic |
| Redis | 6/10 | Critical: wrapper functions don't retry on failure |
| Email (SendGrid/Mailgun) | 8/10 | Minor: AWS SES uses sync boto3 without async resilience |
| HRIS (Odoo, IceHRM, etc.) | 4/10 | Critical: raw XML-RPC with no retry/circuit breaker |
| Slack | 8/10 | Good: uses resilient_http_client |
| Webhooks | 7/10 | Good: SSRF protection, minor: no unified metrics |

---

## Improvement Plan

### Phase 1: Core Infrastructure (HIGH PRIORITY)

#### 1.1 Redis Wrapper Functions with Retry Logic
**File:** `app/core/redis_client.py`

**Problem:**
- `redis_get()`, `redis_set()`, `redis_delete()` return None/False on first failure
- No exponential backoff
- No circuit breaker

**Solution:**
```python
# Implement retry decorator with exponential backoff
# Add circuit breaker for Redis operations
# Provide timeout configuration
```

**Success Criteria:**
- ✅ Redis operations retry 3 times with exponential backoff
- ✅ Circuit breaker opens after 5 consecutive failures
- ✅ Metrics exported for monitoring

---

#### 1.2 Database Retry Logic Enhancement
**File:** `app/core/database.py`

**Problem:**
- `get_async_db_with_retry()` catches exceptions but doesn't wait between retries
- Could overwhelm struggling database

**Solution:**
```python
# Add exponential backoff with jitter
# Implement per-database circuit breaker
# Add connection health monitoring
```

**Success Criteria:**
- ✅ Retry with 1s → 2s → 4s exponential backoff
- ✅ Jitter to prevent thundering herd
- ✅ Circuit breaker per database instance

---

### Phase 2: HRIS Connector Resilience (HIGH PRIORITY)

#### 2.1 Resilient Adapter Pattern for HRIS
**New File:** `app/integrations/hris/resilient_adapter.py`

**Problem:**
- Odoo connector uses raw `xmlrpc.client.ServerProxy`
- IceHRM and others use raw REST clients
- No retry, timeout, or circuit breaker

**Solution:**
```python
# Create ResilientHRISAdapter base class
# Wrap all external calls with retry logic
# Add circuit breaker per HRIS instance
# Provide timeout configuration
```

**Success Criteria:**
- ✅ All HRIS connectors inherit resilient adapter
- ✅ 3 retries with exponential backoff
- ✅ Circuit breaker per connector instance
- ✅ Configurable timeouts

---

#### 2.2 Update Individual HRIS Connectors
**Files:**
- `app/integrations/hris/odoo_connector.py`
- `app/integrations/hris/icehrm_connector.py`
- `app/integrations/hris/orangehrm_connector.py`
- `app/integrations/hris/frappe_connector.py`
- `app/integrations/hris/sentrifugo_connector.py`
- `app/integrations/hris/quickbooks_workforce_connector.py`

**Changes:**
- Inherit from `ResilientHRISAdapter`
- Wrap XML-RPC/REST calls
- Add timeout configuration

---

### Phase 3: Email Service Enhancement (MEDIUM PRIORITY)

#### 3.1 AWS SES Async Resilient Client
**File:** `app/services/email_providers.py`

**Problem:**
- `AWSSESProvider` uses synchronous boto3
- No async circuit breaker protection

**Solution:**
```python
# Wrap boto3 calls in async executor
# Use resilient_http_client for SES API calls
# Add retry logic for SES throttling
```

**Success Criteria:**
- ✅ AWS SES calls use async pattern
- ✅ Retry on 429 (Throttling) with exponential backoff
- ✅ Circuit breaker for SES API

---

### Phase 4: Unified Monitoring (MEDIUM PRIORITY)

#### 4.1 Integration Metrics Exporter
**New File:** `app/monitoring/integration_metrics.py`

**Problem:**
- Each integration has separate logging
- No unified view of integration health
- Difficult to spot patterns

**Solution:**
```python
# Centralized metrics collection
# Per-integration success/error rates
# Circuit breaker state tracking
# Latency percentiles (p50, p95, p99)
```

**Success Criteria:**
- ✅ Prometheus metrics for all integrations
- ✅ Per-endpoint circuit breaker states
- ✅ Error classification and tracking
- ✅ Alert-ready dashboard metrics

---

## Implementation Order

1. ✅ **Phase 1.1**: Redis retry logic (foundation for caching)
2. ✅ **Phase 1.2**: Database retry enhancement (foundation for all)
3. ✅ **Phase 2.1**: Resilient HRIS adapter (pattern for all connectors)
4. ✅ **Phase 2.2**: Update HRIS connectors (apply pattern)
5. ✅ **Phase 3.1**: AWS SES async wrapper (email reliability)
6. ✅ **Phase 4.1**: Unified monitoring (observability)

---

## Testing Strategy

### Unit Tests
- Retry logic with mock failures
- Circuit breaker state transitions
- Exponential backoff timing

### Integration Tests
- Real network failures (simulate with Toxiproxy)
- Database connection drops
- Redis unavailability

### Chaos Engineering
- Random connection drops
- High latency injection
- Dependency failures

---

## Rollout Plan

1. **Week 1**: Phase 1 (Redis + Database)
2. **Week 2**: Phase 2 (HRIS adapters)
3. **Week 3**: Phase 3 (Email) + Phase 4 (Monitoring)
4. **Week 4**: Testing and validation

---

## Success Metrics

- **99.9% uptime** for integrations under normal conditions
- **< 5s recovery** from transient network failures
- **Zero cascading failures** (circuit breaker effectiveness)
- **< 100ms p99 latency** for healthy integrations

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Retry storms overwhelming services | Add jitter + circuit breakers |
| Stale cache after Redis recovery | Implement cache warming |
| HRIS rate limiting during retries | Per-connector rate limiting |
| Monitoring overhead | Async metrics export |

---

## References

- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Exponential Backoff with Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [ResilientHTTPClient](app/core/resilient_client.py)
- [Circuit Implementation](app/core/resilience.py)
