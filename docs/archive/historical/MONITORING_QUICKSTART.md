# 🎯 Monitoring Quick Start Guide

## ✅ Step 1: Enable Monitoring (COMPLETE)

Monitoring has been successfully integrated into `app/main.py`!

### What Was Added:
- ✅ Prometheus metrics endpoint (`/metrics`)
- ✅ SLO/SLI tracking
- ✅ Database query monitoring
- ✅ Distributed tracing support (optional)
- ✅ Automatic request tracking middleware

---

## 🚀 Step 2: Start the Application

```bash
# Navigate to project directory
cd /Users/sheriftito/Downloads/psychsync

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see monitoring initialization logs:
```
✅ Prometheus metrics router registered at /metrics
✅ Comprehensive monitoring stack initialized
   → Prometheus metrics: http://localhost:8000/metrics
   → SLO/SLI tracking: Active
```

---

## 🧪 Step 3: Verify Monitoring is Working

### Option A: Automatic Verification Script

```bash
# Run the verification script
./verify_monitoring.sh
```

### Option B: Manual Verification

```bash
# Check metrics endpoint
curl http://localhost:8000/metrics

# You should see Prometheus metrics like:
# psychsync_http_requests_total{method="GET",endpoint="/health",status="200"} 42.0
# psychsync_http_request_duration_seconds_bucket{le="0.5"} 38.0
# psychsync_slo_compliance{slo_name="API_AVAILABILITY"} 0.998
```

---

## 📊 Step 4: Generate Some Metrics

```bash
# Send some requests to populate metrics
curl http://localhost:8000/health
curl http://localhost:8000/
curl http://localhost:8000/docs

# Check metrics again
curl http://localhost:8000/metrics | grep psychsync
```

---

## 🔧 Step 5: (Optional) Enable Distributed Tracing

### Start Jaeger locally:
```bash
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 4318:4318 \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest
```

### Enable tracing in environment:
```bash
# Add to .env or set as environment variable
export TRACING_ENABLED=true
export JAEGER_ENDPOINT=http://localhost:4318

# Restart the application
uvicorn app.main:app --reload
```

### View traces:
Open http://localhost:16686 in your browser

---

## 📈 Step 6: Deploy Prometheus (Recommended)

### Create `docker-compose.yml` for monitoring:
```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/prometheus/alert_rules.yml:/etc/prometheus/alert_rules.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  grafana-storage:
```

### Start monitoring stack:
```bash
docker-compose up -d prometheus grafana
```

### Access:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (login: admin/admin)

---

## ✅ Verification Checklist

- [ ] Application starts without errors
- [ ] `/metrics` endpoint returns Prometheus format
- [ ] Metrics include `psychsync_http_requests_total`
- [ ] `/health` endpoint returns system status
- [ ] Logs show "✅ Comprehensive monitoring stack initialized"
- [ ] (Optional) Jaeger UI shows traces
- [ ] (Optional) Prometheus targets are up

---

## 📝 Configuration Options

Add these to your `.env` file:

```bash
# Monitoring Configuration
TRACING_ENABLED=false                          # Enable distributed tracing
JAEGER_ENDPOINT=http://jaeger:4318            # Jaeger collector endpoint
SLOW_QUERY_THRESHOLD=1.0                      # Slow query threshold (seconds)

# Prometheus (optional)
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus      # For multiprocessing
```

---

## 🐛 Troubleshooting

### Problem: `/metrics` endpoint returns 404

**Solution**: Make sure the app is running with `uvicorn app.main:app --reload`

### Problem: No metrics appearing

**Solution**: Send some requests first to populate metrics:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/
```

### Problem: Import errors

**Solution**: Install required dependencies:
```bash
pip install prometheus-client opentelemetry-api opentelemetry-sdk
```

### Problem: Metrics not visible in Prometheus

**Solution**: Check Prometheus is configured to scrape `http://localhost:8000/metrics`

---

## 🎓 What's Being Monitored

### HTTP Metrics (RED Method)
- **Rate**: Request count by endpoint, method, status
- **Errors**: Error rate tracking
- **Duration**: Request latency (P50, P95, P99)

### Database Metrics
- Query duration by operation and table
- Connection pool usage
- Slow query detection

### Business Metrics
- User registrations
- Assessment completions
- Team operations

### SLO/SLI Metrics
- API availability (99.9% target)
- API latency (P95 < 500ms)
- Error rate (< 1%)
- Error budget remaining

---

## 📚 Next Steps

1. ✅ **DONE** - Enable monitoring in main.py
2. ✅ **DONE** - Create verification script
3. 📋 **TODO** - Deploy Prometheus
4. 📋 **TODO** - Create Grafana dashboards
5. 📋 **TODO** - Set up alerting
6. 📋 **TODO** - Enable log aggregation (Loki/ELK)

---

## 📖 Additional Resources

- **Complete Analysis**: `monitoring/MONITORING_BLIND_SPOTS_REPORT.md`
- **Metrics Code**: `app/api/v1/endpoints/prometheus_metrics.py`
- **SLO Tracking**: `app/monitoring/slo_tracking.py`
- **Database Monitoring**: `app/core/database_monitoring.py`

---

**Questions?** The monitoring stack is now fully integrated and ready to use! 🎉
