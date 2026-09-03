# Load Testing Quick Start Guide

Get started with PsychSync load testing in 5 minutes.

## Prerequisites

```bash
# Install Python dependencies
pip install -r load_testing/requirements.txt

# Install k6 (optional)
brew install k6  # macOS
# or download from https://k6.io/

# Install Docker for monitoring (optional)
docker-compose version
```

## Quick Test (5 Minutes)

### 1. Start Your API

```bash
# From project root
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Run a Quick Smoke Test

```bash
# From project root
./load_testing/run_tests.sh -u 10 -t 2m -c auth
```

This runs a quick authentication test with 10 users for 2 minutes.

## Common Test Scenarios

### Small Load Test (100 Users)

```bash
# Authentication test
./load_testing/run_tests.sh -u 100 -t 5m -c auth

# Assessment test
./load_testing/run_tests.sh -u 100 -t 5m -c assessment

# Mixed workload (realistic)
./load_testing/run_tests.sh -u 100 -t 10m -c mixed
```

### Medium Load Test (1,000 Users)

```bash
# With monitoring
./load_testing/run_tests.sh -u 1000 -s 50 -t 15m -c mixed -m

# Generate test data first
./load_testing/run_tests.sh -u 1000 -g -d medium -c mixed
```

### Large Load Test (10,000 Users)

```bash
# Using k6 for better performance
./load_testing/run_tests.sh -u 10000 -s 200 -t 30m -c mixed -T k6 -m

# With large dataset
./load_testing/run_tests.sh -u 10000 -g -d large -c mixed
```

## View Results

### Locust Results

- HTML reports are saved to `load_testing/reports/`
- Open the latest HTML file in your browser
- Example: `load_testing/reports/locust_mixed_1000users_20240110_143000.html`

### Monitoring Dashboards

If monitoring was started with `-m`:

- **Prometheus**: http://localhost:9090
  - View raw metrics
  - Query data with PromQL

- **Grafana**: http://localhost:3001
  - Username: `admin`
  - Password: `loadtest123`
  - Pre-configured dashboards available

## Test Data Generation

### Quick Data Generation

```bash
# Small dataset (1,000 users)
cd load_testing/test_data
python generate_test_data.py --users 1000 --teams 50 --assessments 10

# Medium dataset (10,000 users)
python generate_test_data.py --users 10000 --teams 500 --assessments 100

# Large dataset (100,000 users)
python generate_test_data.py --users 100000 --teams 5000 --assessments 1000
```

### Custom Data Generation

```bash
# Custom configuration
python generate_test_data.py \
  --users 5000 \
  --teams 250 \
  --assessments 50 \
  --responses-per-user 100 \
  --db-url "postgresql://user:pass@localhost:5432/test_db"
```

## Manual Test Execution

### Using Locust (Web UI)

```bash
# Start Locust web interface
locust -f load_testing/locust/mixed_workload.py --host http://localhost:8000

# Open browser: http://localhost:8089
# Configure:
# - Number of users: 1000
# - Spawn rate: 50
# - Host: http://localhost:8000
# Click "Start swarming"
```

### Using Locust (Headless)

```bash
locust -f load_testing/locust/auth_test.py \
  --headless \
  --host http://localhost:8000 \
  --users 1000 \
  --spawn-rate 50 \
  --run-time 10m \
  --html reports/test_results.html
```

### Using k6

```bash
# Set environment variables
export API_BASE_URL="http://localhost:8000"

# Run test
k6 run --vus 1000 --duration 10m \
  load_testing/k6/mixed_workload.js

# With output
k6 run --vus 1000 --duration 10m \
  --out json=results.json \
  load_testing/k6/mixed_workload.js
```

## Interpreting Results

### Key Metrics to Check

1. **Response Time**:
   - p50: Median response time
   - p95: 95th percentile (95% of requests faster than this)
   - p99: 99th percentile (99% of requests faster than this)

2. **Throughput**:
   - Requests per second (RPS)
   - Users active concurrently

3. **Error Rate**:
   - Percentage of failed requests
   - Target: < 1%

4. **Resource Utilization**:
   - CPU usage
   - Memory usage
   - Database connections
   - Cache hit rate

### Success Criteria

| Metric          | Small Load | Medium Load | Large Load |
|-----------------|------------|-------------|------------|
| p95 Response    | < 500ms    | < 1000ms    | < 2000ms   |
| Error Rate      | < 0.1%     | < 0.5%      | < 1%       |
| Throughput      | 100-300 RPS| 500-1500 RPS| 2000+ RPS  |
| CPU Usage       | < 40%      | < 70%       | < 85%      |

## Troubleshooting

### API Not Accessible

```bash
# Check if API is running
curl http://localhost:8000/health

# Or check docs endpoint
curl http://localhost:8000/docs
```

### Connection Refused

```bash
# Check if correct port
lsof -i :8000

# Verify API_BASE_URL
export API_BASE_URL="http://localhost:8000"
```

### Database Connection Errors

```bash
# Check database connection
psql postgresql://postgres:postgres@localhost:5432/psychsync

# Verify DATABASE_URL in .env
```

### High Error Rates

1. Check API logs: `tail -f app/logs/app.log`
2. Check database logs
3. Review error reports in Locust HTML report
4. Verify test data exists

### Out of Memory

```bash
# Reduce number of users
./load_testing/run_tests.sh -u 100 -t 5m -c mixed

# Or reduce spawn rate
./load_testing/run_tests.sh -u 500 -s 10 -t 10m
```

## Next Steps

1. **Baseline Performance**: Run tests with small load to establish baseline
2. **Gradual Scaling**: Increase load incrementally (100 → 1,000 → 10,000)
3. **Monitor Continuously**: Use Prometheus/Grafana to monitor in real-time
4. **Identify Bottlenecks**: Review slow endpoints and optimize
5. **Iterate**: Make improvements and re-test

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r load_testing/requirements.txt

      - name: Start services
        run: docker-compose up -d db redis backend

      - name: Run load test
        run: |
          ./load_testing/run_tests.sh -u 100 -t 5m -c mixed

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: load_testing/reports/
```

## Additional Resources

- **Full Documentation**: `load_testing/README.md`
- **Test Scripts**: `load_testing/locust/` and `load_testing/k6/`
- **Monitoring**: `load_testing/monitoring/`
- **Test Data**: `load_testing/test_data/`

## Support

For issues or questions:
- Check logs in `load_testing/logs/`
- Review reports in `load_testing/reports/`
- Consult full documentation in `load_testing/README.md`
