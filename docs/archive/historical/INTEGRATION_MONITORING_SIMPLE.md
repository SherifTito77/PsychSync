# Integration Monitoring Setup (No Docker Required)

**Simple setup for integration resilience monitoring using free tools**

---

## Quick Start

### 1. Test Your Endpoints

```bash
# Health check (no auth required)
curl http://localhost:8000/api/v1/monitoring/integration-health

# Detailed metrics (no auth required)
curl http://localhost:8000/api/v1/monitoring/integration-metrics

# Prometheus format (no auth required)
curl http://localhost:8000/api/v1/monitoring/integration-metrics/prometheus

# HTML Dashboard (no auth required)
# Open in browser: http://localhost:8000/api/v1/monitoring/integration-dashboard
curl http://localhost:8000/api/v1/monitoring/integration-dashboard
```

### 2. Available Endpoints

| Endpoint | Auth Required | Usage |
|----------|---------------|-------|
| `/api/v1/monitoring/integration-health` | No | Quick health checks |
| `/api/v1/monitoring/integration-metrics` | No | Detailed JSON metrics |
| `/api/v1/monitoring/integration-metrics/prometheus` | No | Prometheus scraping |
| `/api/v1/monitoring/integration-dashboard` | No | HTML dashboard with auto-refresh |

---

## Free Monitoring Options

### Option 1: Built-in HTML Dashboard (Easiest)

Just use your existing dashboard at `/dashboard` - the integration health data is already included!

### Option 2: Simple Shell Script Monitoring

Create `check_integrations.sh`:

```bash
#!/bin/bash
# Simple health check script

echo "Checking PsychSync integration health..."
echo

HEALTH=$(curl -s http://localhost:8000/api/v1/monitoring/integration-health)
STATUS=$(echo $HEALTH | jq -r '.status')

echo "Overall Status: $STATUS"
echo

# Check individual components
echo "Components:"
echo $HEALTH | jq -r '.checks | to_entries[] | "  \(.key): \(.value)"'

# Alert if not healthy
if [ "$STATUS" != "healthy" ]; then
    echo
    echo "⚠️  WARNING: Integration health is $STATUS"
    # You could add email/Slack notification here
fi
```

Run with:
```bash
chmod +x check_integrations.sh
./check_integrations.sh
```

### Option 3: Prometheus (Binary, No Docker)

#### Download Prometheus (Free)

```bash
# Download latest version
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.darwin-arm64.tar.gz
tar xvfz prometheus-2.45.0.darwin-arm64.tar.gz
cd prometheus-2.45.0.darwin-arm64
```

#### Create Simple Config

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 30s

scrape_configs:
  - job_name: 'psychsync'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/monitoring/integration-metrics/prometheus'
```

#### Start Prometheus

```bash
./prometheus --config.file=prometheus.yml
```

#### Access Prometheus UI

Open http://localhost:9090

Try these queries:
```promql
# Database circuit breaker (1=open, 0=closed)
psychsync_db_circuit_breaker_open

# Database success rate
psychsync_db_success_rate

# Overall health
psychsync_integration_healthy_count / psychsync_integration_total_count
```

---

## Simple Alerting (No Tools Required)

### Bash Script Alert

Create `alert_on_failure.sh`:

```bash
#!/bin/bash

HEALTH=$(curl -s http://localhost:8000/api/v1/monitoring/integration-health)
STATUS=$(echo $HEALTH | jq -r '.status')

if [ "$STATUS" != "healthy" ]; then
    echo "🚨 INTEGRATION FAILURE DETECTED"
    echo "Status: $STATUS"
    echo

    # Send to Slack (optional)
    # curl -X POST -H 'Content-type: application/json' \
    #   --data "{\"text\":\"PsychSync integration failure: $STATUS\"}" \
    #   YOUR_SLACK_WEBHOOK_URL

    # Or send email (optional)
    # echo "Integration failed" | mail -s "PsychSync Alert" you@example.com
fi
```

Add to crontab for periodic checks:
```bash
# Check every 5 minutes
*/5 * * * * /path/to/alert_on_failure.sh
```

---

## Metrics Reference

### Key Metrics to Monitor

```bash
# 1. Database Health
curl -s http://localhost:8000/api/v1/monitoring/integration-metrics | jq '.database'

# 2. Redis Health
curl -s http://localhost:8000/api/v1/monitoring/integration-metrics | jq '.redis'

# 3. Overall Summary
curl -s http://localhost:8000/api/v1/monitoring/integration-metrics | jq '.summary'
```

### What the Metrics Mean

| Metric | Good Value | Bad Value | Action |
|--------|-----------|-----------|--------|
| `circuit_breaker_state` | "closed" | "open" | Check underlying service |
| `success_rate` | > 95% | < 90% | Investigate errors |
| `avg_response_time_ms` | < 100ms | > 500ms | Check performance |
| `failed_calls` | Low | Increasing | Check logs |

---

## Integration with Existing Dashboard

Your resilience metrics are now available in your existing `/dashboard` route. The data is automatically included in the monitoring section.

### Frontend Integration Example

```typescript
// Fetch integration health in your React app
const fetchIntegrationHealth = async () => {
  const response = await fetch('/api/v1/monitoring/integration-health');
  const health = await response.json();
  return health;
};

// Use in your dashboard
const Dashboard = () => {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetchIntegrationHealth().then(setHealth);
    // Poll every 30 seconds
    const interval = setInterval(() => {
      fetchIntegrationHealth().then(setHealth);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h2>Integration Health: {health?.status}</h2>
      {health?.checks && (
        <ul>
          <li>Database: {health.checks.database}</li>
          <li>Redis: {health.checks.redis}</li>
        </ul>
      )}
    </div>
  );
};
```

---

## Files Modified

| File | Purpose |
|------|---------|
| `app/core/redis_client.py` | Added retry, circuit breaker, metrics |
| `app/core/database.py` | Added retry, circuit breaker, metrics |
| `app/integrations/hris/resilient_adapter.py` | New: Resilient HRIS base class |
| `app/integrations/hris/odoo_connector.py` | Updated: Uses resilient wrapper |
| `app/services/email_providers.py` | Updated: AWS SES with async retry |
| `app/monitoring/integration_metrics.py` | New: Unified metrics collection |
| `app/api/v1/endpoints/monitoring.py` | **Updated: Added integration endpoints** |

---

## What Was NOT Created (Docker-related)

- ❌ No Docker containers
- ❌ No docker-compose files for monitoring
- ❌ No Grafana dashboards
- ❌ No Alertmanager setup

---

## What You Got Instead

- ✅ **Simple HTTP endpoints** that work with your existing API
- ✅ **Prometheus-compatible** metrics (if you want them)
- ✅ **JSON metrics** for easy consumption
- ✅ **Health check** for load balancers
- ✅ **No additional infrastructure** required

The resilience features (retry, circuit breakers, metrics) work **without** any monitoring setup - they're built into the application itself. The monitoring endpoints just let you **observe** what's happening.
