# PsychSync Load Testing Suite

Comprehensive load testing scenarios for the PsychSync psychological assessment platform to validate high-concurrency performance.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Test Scenarios](#test-scenarios)
4. [Performance Metrics](#performance-metrics)
5. [Quick Start](#quick-start)
6. [Test Execution](#test-execution)
7. [Monitoring](#monitoring)
8. [Results Analysis](#results-analysis)
9. [CI/CD Integration](#cicd-integration)

## Overview

This load testing suite validates the PsychSync platform's performance under various concurrency levels:

- **Small Load**: 100 concurrent users
- **Medium Load**: 1,000 concurrent users
- **Large Load**: 10,000+ concurrent users

### Testing Tools

- **Locust** (Primary): Python-based, recommended for FastAPI backends
- **k6** (Alternative): JavaScript-based, modern and lightweight
- **Supporting Tools**: Prometheus, Grafana, PostgreSQL stats

### Key User Journeys Tested

1. **Authentication Flow** (15% weight)
2. **Assessment Taking** (40% weight)
3. **Dashboard & Analytics** (20% weight)
4. **Team Management** (15% weight)
5. **Assessment Management** (5% weight)
6. **AI/NLP Processing** (5% weight)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Test Controller                      │
│                  (Locust/k6 Master Node)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ├──────────────────────────────────────┐
                       │                                      │
┌──────────────────────▼──────────────────┐  ┌───────────────▼──────────────┐
│         PsychSync FastAPI Backend       │  │    PostgreSQL Database        │
│         (Port 8000 - Multiple Workers)  │  │    (Port 5432)                │
└──────────────────────┬──────────────────┘  └───────────────┬──────────────┘
                       │                                    │
┌──────────────────────▼──────────────────┐  ┌───────────────▼──────────────┐
│         Redis Cache Layer               │  │    Monitoring Stack          │
│         (Port 6379)                     │  │    (Prometheus + Grafana)    │
└─────────────────────────────────────────┘  └───────────────────────────────┘
```

## Test Scenarios

### 1. Authentication Flow (15% weight)

**Description**: Simulates user login, token refresh, and logout operations

**Endpoints**:
- `POST /api/v1/auth/token-fixed` - Login
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - Logout

**Load Distribution**:
- Small: 15 concurrent users
- Medium: 150 concurrent users
- Large: 1,500 concurrent users

**Success Criteria**:
- p50 response time: < 200ms
- p95 response time: < 500ms
- p99 response time: < 1000ms
- Error rate: < 0.1%
- Throughput: 50-500 requests/second (depending on load)

### 2. Assessment Taking (40% weight)

**Description**: Users taking psychological assessments with auto-save and final submission

**Endpoints**:
- `GET /api/v1/personality-assessments/frameworks` - List frameworks
- `POST /api/v1/assessments/{id}/start` - Start assessment
- `POST /api/v1/assessments/{id}/responses` - Submit responses (auto-save)
- `POST /api/v1/assessments/{id}/complete` - Final submission
- `GET /api/v1/assessments/{id}/results` - View results

**Load Distribution**:
- Small: 40 concurrent users
- Medium: 400 concurrent users
- Large: 4,000 concurrent users

**Success Criteria**:
- p50 response time: < 300ms
- p95 response time: < 800ms
- p99 response time: < 1500ms
- Error rate: < 0.5%
- Throughput: 100-2000 requests/second

### 3. Dashboard & Analytics (20% weight)

**Description**: Loading dashboards with team analytics, filtering large datasets

**Endpoints**:
- `GET /api/v1/analytics/dashboard` - Dashboard overview
- `GET /api/v1/analytics/team/{id}` - Team analytics
- `GET /api/v1/analytics/export` - Export reports
- `GET /api/v1/analytics/trends` - Historical trends

**Load Distribution**:
- Small: 20 concurrent users
- Medium: 200 concurrent users
- Large: 2,000 concurrent users

**Success Criteria**:
- p50 response time: < 400ms
- p95 response time: < 1000ms
- p99 response time: < 2000ms
- Error rate: < 0.5%
- Cache hit rate: > 80%

### 4. Team Management (15% weight)

**Description**: Managing team members, permissions, and viewing activity

**Endpoints**:
- `GET /api/v1/teams/{id}` - View team
- `POST /api/v1/teams/{id}/members` - Add member
- `DELETE /api/v1/teams/{id}/members/{user_id}` - Remove member
- `PUT /api/v1/teams/{id}/permissions` - Update permissions
- `GET /api/v1/teams/{id}/activity` - View activity

**Load Distribution**:
- Small: 15 concurrent users
- Medium: 150 concurrent users
- Large: 1,500 concurrent users

**Success Criteria**:
- p50 response time: < 250ms
- p95 response time: < 700ms
- p99 response time: < 1500ms
- Error rate: < 0.2%

### 5. Assessment Management (5% weight)

**Description**: Creating, duplicating, and managing assessments

**Endpoints**:
- `POST /api/v1/assessments` - Create assessment
- `POST /api/v1/assessments/{id}/duplicate` - Duplicate assessment
- `PUT /api/v1/assessments/{id}` - Update assessment
- `DELETE /api/v1/assessments/{id}` - Delete assessment

**Load Distribution**:
- Small: 5 concurrent users
- Medium: 50 concurrent users
- Large: 500 concurrent users

**Success Criteria**:
- p50 response time: < 400ms
- p95 response time: < 1000ms
- p99 response time: < 2000ms
- Error rate: < 0.1%

### 6. AI/NLP Processing (5% weight)

**Description**: Submitting text for analysis, processing large documents

**Endpoints**:
- `POST /api/v1/nlp/analyze` - Analyze text
- `POST /api/v1/nlp/batch` - Batch processing
- `GET /api/v1/ai/insights/{id}` - Get insights

**Load Distribution**:
- Small: 5 concurrent users
- Medium: 50 concurrent users
- Large: 500 concurrent users

**Success Criteria**:
- p50 response time: < 1000ms
- p95 response time: < 3000ms
- p99 response time: < 5000ms
- Error rate: < 1%

## Performance Metrics

### Response Time Targets

| Scenario      | p50    | p95    | p99    |
|---------------|--------|--------|--------|
| Auth          | < 200ms| < 500ms| < 1000ms|
| Assessment    | < 300ms| < 800ms| < 1500ms|
| Dashboard     | < 400ms| < 1000ms| < 2000ms|
| Team Mgmt     | < 250ms| < 700ms| < 1500ms|
| Assessment Mgmt| < 400ms| < 1000ms| < 2000ms|
| AI/NLP        | < 1000ms| < 3000ms| < 5000ms|

### Throughput Targets

| Load Level | Requests/Second | Concurrent Users |
|------------|-----------------|------------------|
| Small      | 100-300         | 100              |
| Medium     | 500-1500        | 1,000            |
| Large      | 2000-5000       | 10,000+          |

### Resource Utilization

**CPU**:
- Small: < 40%
- Medium: < 70%
- Large: < 85%

**Memory**:
- Small: < 4GB
- Medium: < 12GB
- Large: < 32GB

**Database Connections**:
- Max connections: 100 per worker
- Connection pool utilization: < 80%
- Query duration: p95 < 100ms

**Cache**:
- Redis hit rate: > 80%
- Redis memory usage: < 70%
- Cache eviction rate: < 5%

### Error Rate Thresholds

| Error Type           | Threshold |
|----------------------|-----------|
| 5xx errors           | < 0.1%    |
| 4xx errors           | < 1%      |
| Timeout errors       | < 0.5%    |
| Connection errors    | < 0.1%    |
| Total error rate     | < 1%      |

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install locust psycopg2-binary redis

# Install k6 (optional)
brew install k6  # macOS
# or download from https://k6.io/

# Install monitoring tools (optional)
pip install prometheus-client grafana-api
```

### Environment Setup

```bash
# Copy environment template
cp .env.example .env.test

# Update test environment variables
# - Set TEST_DATABASE_URL
# - Set TEST_REDIS_URL
# - Set TEST_API_BASE_URL
```

### Generate Test Data

```bash
# Generate test users, assessments, and responses
python load_testing/test_data/generate_test_data.py --users 10000 --assessments 100

# This creates:
# - 10,000 test users
# - 100 assessment templates
# - 1,000,000 historical responses
# - 500 teams with various structures
```

## Test Execution

### Using Locust (Recommended)

#### Single Scenario Tests

```bash
# Authentication load test (100 users)
locust -f load_testing/locust/auth_test.py \
  --host https://api.psychsync.test \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --html reports/auth_test_100users.html

# Assessment taking test (1000 users)
locust -f load_testing/locust/assessment_test.py \
  --host https://api.psychsync.test \
  --users 1000 \
  --spawn-rate 50 \
  --run-time 10m \
  --html reports/assessment_test_1000users.html

# Dashboard analytics test (10000 users)
locust -f load_testing/locust/dashboard_test.py \
  --host https://api.psychsync.test \
  --users 10000 \
  --spawn-rate 200 \
  --run-time 20m \
  --html reports/dashboard_test_10000users.html
```

#### Mixed Workload Tests

```bash
# Mixed workload with realistic user distribution
locust -f load_testing/locust/mixed_workload.py \
  --host https://api.psychsync.test \
  --users 1000 \
  --spawn-rate 50 \
  --run-time 15m \
  --html reports/mixed_workload_1000users.html

# Custom user distribution
locust -f load_testing/locust/mixed_workload.py \
  --host https://api.psychsync.test \
  --users 5000 \
  --spawn-rate 100 \
  --run-time 30m \
  --html reports/mixed_workload_5000users.html \
  --custom-stats
```

#### Distributed Load Testing

```bash
# Master node
locust -f load_testing/locust/mixed_workload.py \
  --master \
  --host https://api.psychsync.test \
  --expect-workers 10 \
  --users 10000 \
  --spawn-rate 200

# Worker nodes (run on 10 different machines)
locust -f load_testing/locust/mixed_workload.py \
  --worker \
  --master-host <master-ip>
```

### Using k6

```bash
# Authentication test
k6 run --vus 100 --duration 5m \
  --out json=reports/auth_k6.json \
  load_testing/k6/auth_test.js

# Assessment test
k6 run --vus 1000 --duration 10m \
  --out json=reports/assessment_k6.json \
  load_testing/k6/assessment_test.js

# Mixed workload
k6 run --vus 5000 --duration 30m \
  --out json=reports/mixed_k6.json \
  load_testing/k6/mixed_workload.js
```

## Monitoring

### Real-time Monitoring Setup

```bash
# Start Prometheus (in monitoring directory)
cd load_testing/monitoring
docker-compose up -d prometheus grafana

# Import Grafana dashboards
# Dashboard files in monitoring/grafana/dashboards/
```

### Key Metrics to Monitor

#### Application Metrics

- Request rate (requests/second)
- Response times (p50, p95, p99)
- Error rates by endpoint
- Active connections
- Queue depth

#### Database Metrics

```sql
-- PostgreSQL connection pool stats
SELECT count(*), state FROM pg_stat_activity GROUP BY state;

-- Slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 10;

-- Table size
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Redis Metrics

```bash
# Redis info
redis-cli INFO stats

# Key patterns
redis-cli --scan --pattern 'user:*' | wc -l

# Memory usage
redis-cli INFO memory
```

#### System Metrics

```bash
# CPU usage
top -o cpu

# Memory usage
vm_stat

# Disk I/O
iostat -d 1

# Network stats
netstat -an | grep ESTABLISHED | wc -l
```

### Monitoring Dashboards

**Grafana Dashboards**:
- `monitoring/grafana/dashboards/api_performance.json` - API performance metrics
- `monitoring/grafana/dashboards/database_performance.json` - Database metrics
- `monitoring/grafana/dashboards/system_metrics.json` - CPU, memory, disk, network

**Prometheus Queries**:
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Response time percentile
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## Results Analysis

### Key Performance Indicators

1. **Throughput**: Requests per second sustained
2. **Latency**: Response time percentiles
3. **Error Rate**: Percentage of failed requests
4. **Resource Utilization**: CPU, memory, database connections
5. **Cache Efficiency**: Hit rates, eviction rates

### Bottleneck Identification

#### Common Bottlenecks

**Database Connection Pool Exhaustion**:
```
Symptoms: p95 response time spikes, connection timeout errors
Solution: Increase pool size, add connection pooling middleware
```

**N+1 Query Problems**:
```
Symptoms: High database CPU, many queries per request
Solution: Add eager loading, optimize ORM queries
```

**Cache Stampede**:
```
Symptoms: High load on cache, many misses, database spikes
Solution: Implement cache warming, use request coalescing
```

**Memory Leaks**:
```
Symptoms: Memory usage grows over time, eventual OOM
Solution: Profile memory usage, check for circular references
```

**Thread/Process Exhaustion**:
```
Symptoms: New connections rejected, high queue depth
Solution: Increase worker count, optimize blocking operations
```

**Network Saturation**:
```
Symptoms: High latency, packet loss, connection timeouts
Solution: Optimize payload sizes, enable compression
```

### Analysis Checklist

- [ ] Response time percentiles meet targets
- [ ] Error rates below thresholds
- [ ] Throughput meets expectations
- [ ] Resource utilization healthy
- [ ] No memory leaks detected
- [ ] Database queries optimized
- [ ] Cache hit rates acceptable
- [ ] No single point of failure
- [ ] Graceful degradation under load
- [ ] Proper error handling and recovery

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/load-testing.yml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        scenario: [auth, assessment, dashboard, mixed]
        load: [small, medium]

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install locust psycopg2-binary redis

      - name: Generate test data
        run: |
          python load_testing/test_data/generate_test_data.py --users 1000

      - name: Start services
        run: |
          docker-compose up -d db redis backend

      - name: Wait for services
        run: sleep 30

      - name: Run Locust tests
        run: |
          locust -f load_testing/locust/${{ matrix.scenario }}_test.py \
            --headless \
            --users ${{ matrix.load == 'small' && 100 || 1000 }} \
            --spawn-rate 10 \
            --run-time 5m \
            --html reports/${{ matrix.scenario }}_${{ matrix.load }}.html

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results-${{ matrix.scenario }}-${{ matrix.load }}
          path: reports/
```

### Pre-deployment Checks

```bash
# Run quick smoke test before deployment
locust -f load_testing/locust/smoke_test.py \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 2m \
  --exit-code-on-error 1
```

### Performance Regression Detection

```bash
# Compare results with baseline
python load_testing/monitoring/compare_results.py \
  --current reports/latest.json \
  --baseline reports/baseline.json \
  --threshold 10  # Alert if 10% degradation
```

## Test Frequency Recommendations

### Continuous Testing
- **Smoke Tests**: Every commit (50 users, 2 minutes)
- **Regression Tests**: Every PR (100 users, 5 minutes)
- **Nightly Builds**: Medium load (1,000 users, 15 minutes)

### Periodic Testing
- **Weekly**: Full test suite (all scenarios, all load levels)
- **Monthly**: Stress testing (find breaking point)
- **Quarterly**: Capacity planning (determine max capacity)

### Event-based Testing
- **Before Major Releases**: Full comprehensive testing
- **After Schema Changes**: Database-focused testing
- **After Infrastructure Changes**: Full infrastructure testing
- **Before High-traffic Events**: Peak load simulation

## Troubleshooting

### Common Issues

**Locust won't start**:
```bash
# Check if port 8089 is available
lsof -i :8089

# Use different port
locust -f test.py --web-port 8090
```

**Database connection errors**:
```bash
# Check connection pool settings
# In app/core/config.py
DATABASE_POOL_SIZE = 20
MAX_OVERFLOW = 40
POOL_TIMEOUT = 30
```

**Redis connection errors**:
```bash
# Check Redis status
redis-cli ping

# Check max connections
redis-cli CONFIG GET maxclients
```

**High memory usage**:
```bash
# Profile memory usage
mprof run locust -f test.py
mprof plot
```

## Best Practices

1. **Always test with realistic data volumes** - Don't test with empty databases
2. **Use distributed testing for large loads** - Single machine can't generate 10k+ users
3. **Monitor during tests** - Don't just collect logs, watch real-time metrics
4. **Test in staging environment** - Never run load tests against production
5. **Ramp up gradually** - Sudden load spikes aren't realistic
6. **Include think time** - Real users don't click instantly
7. **Test failures** - Not just happy path, but error scenarios too
8. **Document baselines** - Track performance over time
9. **Automate analysis** - Use scripts to compare results
10. **Plan for growth** - Test at 2x expected capacity

## Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [k6 Documentation](https://k6.io/docs/)
- [FastAPI Performance Tuning](https://fastapi.tiangolo.com/tutorial/)
- [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance-tips.html)
- [Redis Performance](https://redis.io/topics/admin)

## Support

For issues or questions about load testing, contact:
- DevOps Team: devops@psychsync.com
- Performance Team: performance@psychsync.com
