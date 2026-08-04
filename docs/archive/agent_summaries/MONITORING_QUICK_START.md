# PsychSync Monitoring Stack - Quick Start Guide

Get your enterprise-grade monitoring up and running in 10 minutes with this comprehensive quick start guide.

## 🚀 Quick Start (10 Minutes)

### Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ with pip
- 4GB+ RAM available
- 50GB+ disk space

### 1. One-Command Setup

```bash
cd /Users/sheriftito/Downloads/psychsync
python scripts/setup_monitoring_stack.py
```

This script will:
- ✅ Check all prerequisites
- ✅ Install Python dependencies
- ✅ Compile monitoring components
- ✅ Create all configuration files
- ✅ Set up directory structure
- ✅ Generate startup scripts

### 2. Configure Environment

Edit the generated environment file:

```bash
cp .env.monitoring.example .env.monitoring
nano .env.monitoring
```

**Required Configuration:**
```bash
# Datadog API Key (optional, for APM)
DD_API_KEY=your_datadog_api_key_here

# Sentry DSN (optional, for error tracking)
SENTRY_DSN=your_sentry_dsn_here

# Grafana Admin Password
GRAFANA_PASSWORD=your_secure_password

# Database Credentials
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=psychsync
```

### 3. Start Monitoring Stack

```bash
./scripts/start_monitoring.sh
```

### 4. Access Your Dashboards

🎉 **Your monitoring is now live!** Access these URLs:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3001 | admin / `[GRAFANA_PASSWORD]` |
| **Prometheus** | http://localhost:9090 | No login required |
| **AlertManager** | http://localhost:9093 | No login required |
| **Sentry** | http://localhost:9000 | Create account |
| **Custom Metrics** | http://localhost:8081/metrics | Raw metrics endpoint |
| **Synthetic Tests** | http://localhost:8082/metrics | Test status endpoint |
| **SLA Monitor** | http://localhost:8083/metrics | SLA compliance endpoint |

---

## 📋 Pre-Built Dashboards

Your Grafana comes with these pre-configured dashboards:

### 1. **FastAPI Overview**
- API response times and error rates
- Request volume and patterns
- Active users and sessions
- System resource usage

### 2. **PostgreSQL Overview**
- Database performance metrics
- Connection pool utilization
- Query performance stats
- Storage and growth trends

### 3. **React Frontend**
- Page load times and user experience
- JavaScript error rates
- User engagement metrics
- Assessment completion rates

### 4. **Stripe Billing**
- Revenue and MRR tracking
- Payment success rates
- Subscription metrics
- Webhook processing status

---

## 🎛️ Advanced Configuration

### Custom Business Metrics

The system automatically tracks these business KPIs:

- **User Metrics**: Registrations, active users, engagement
- **Assessment Metrics**: Completion rates, scores, trends
- **Revenue Metrics**: Daily/monthly revenue, subscriptions
- **Team Metrics**: Organizations, teams, growth

Access at: http://localhost:8081/metrics

### Synthetic Monitoring

Automatically tests critical user journeys:

- User registration flow
- Assessment completion flow
- Team creation and management
- API health and connectivity

Access at: http://localhost:8082

### SLA Monitoring

Tracks compliance with your service level agreements:

- API response time SLAs
- Error rate thresholds
- Availability targets
- Performance baselines

Access at: http://localhost:8083

---

## 🔧 Management Commands

### Start Services
```bash
./scripts/start_monitoring.sh
```

### Stop Services
```bash
./scripts/stop_monitoring.sh
```

### Health Check
```bash
./scripts/health_check.sh
```

### View Logs
```bash
docker-compose -f docker-compose.monitoring.yml logs -f
```

### Rebuild Components
```bash
./scripts/build_monitoring_stack.sh
```

---

## 📊 Key Metrics Available

### Technical Metrics
```yaml
API Performance:
  - Request rate: psychsync:api:request_rate:5m
  - P95 response time: psychsync:api:p95_response_time:5m
  - Error rate: psychsync:api:error_rate:5m

Database Performance:
  - Connection utilization: psychsync:db:connection_utilization:5m
  - Query time: psychsync:db:average_query_time:5m
  - Transaction rate: psychsync:db:transaction_rate:5m

Frontend Performance:
  - Page load time: psychsync:frontend:p95_load_time:5m
  - JavaScript errors: psychsync:frontend:error_rate:5m
  - Bounce rate: psychsync:frontend:bounce_rate:5m
```

### Business Metrics
```yaml
User Metrics:
  - Total users: psychsync_users_registered_total
  - Daily active: psychsync_users_active_daily
  - Weekly active: psychsync_users_active_weekly

Revenue Metrics:
  - Daily revenue: psychsync_revenue_daily_dollars
  - Active subscriptions: psychsync_subscriptions_active_total
  - Monthly recurring revenue: psychsync:stripe:mrr

Assessment Metrics:
  - Completed total: psychsync_assessments_completed_total
  - Completion rate: psychsync_assessment_completion_rate
  - Average score: psychsync_assessment_average_score
```

---

## 🚨 Alert Configuration

Alerts are automatically configured for critical issues:

### Immediate Alerts (PagerDuty)
- Service complete outage
- Database connection failures
- Revenue-critical payment issues

### Warning Alerts (Slack)
- High error rates (>5%)
- Slow response times (>1s)
- Low availability (<99%)

### Info Alerts (Email)
- Metric collection issues
- Performance degradation
- Low disk space

**Configure alerts in:** `monitoring/prometheus/alert_rules.yml`

---

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  React Frontend │    │   PostgreSQL    │
│   • Metrics     │    │  • Errors       │    │  • Query Stats  │
│   • Tracing     │    │  • Performance  │    │  • Connections  │
│   • Logging     │    │  • User Actions  │    │  • Replication  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                             │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Prometheus    │     Grafana     │         Sentry              │
│                 │                 │                             │
│  • Metrics      │  • Dashboards   │  • Error Aggregation       │
│  • Storage      │  • Alerts       │  • Issue Tracking          │
│  • Alerting     │  • Visualization│  • User Feedback           │
└─────────────────┴─────────────────┴─────────────────────────────┘
          │                      │
          ▼                      ▼
┌─────────────────┬─────────────────────────────────────────────────┐
│   Custom Exporters│                Alertmanager                    │
│                 │                                             │
│  • Business KPIs │  • Multi-channel alerts                     │
│  • Synthetic Tests│  • Escalation policies                      │
│  • SLA Monitoring │  • Integration with PagerDuty/Slack        │
└─────────────────┴─────────────────────────────────────────────────┘
```

---

## 💡 Pro Tips

### 1. Optimize Costs
```bash
# Check current usage
docker stats

# Reduce data retention
# Edit monitoring/prometheus/prometheus.yml
# Set retention.time to 15d (from 30d)
```

### 2. Customize Dashboards
```bash
# Access Grafana at http://localhost:3001
# Login with admin/[GRAFANA_PASSWORD]
# Click "+" → "Import" to add dashboards
# Upload JSON files from monitoring/grafana/dashboards/
```

### 3. Add Custom Metrics
```python
# Add to your FastAPI app
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('requests_total', 'Total requests')
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')

# Use in your endpoints
REQUEST_COUNT.inc()
REQUEST_DURATION.observe(0.123)
```

### 4. Set Up External Monitoring
```bash
# Enable Datadog APM
export DD_API_KEY=your_key
pip install ddtrace
ddtrace-run python app/main.py
```

---

## 🔍 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check Docker logs
docker-compose -f docker-compose.monitoring.yml logs

# Check port conflicts
netstat -tulpn | grep :3001
netstat -tulpn | grep :9090
```

**Prometheus not collecting data:**
```bash
# Check targets
curl http://localhost:9090/api/v1/targets

# Check configuration
docker exec -it psychsync-prometheus cat /etc/prometheus/prometheus.yml
```

**Grafana can't connect to Prometheus:**
```bash
# Test connectivity
docker exec -it psychsync-grafana wget -qO- http://prometheus:9090/api/v1/query?query=up

# Check datasource configuration
docker exec -it psychsync-grafana cat /etc/grafana/provisioning/datasources/datasources.yml
```

**High memory usage:**
```bash
# Check resource usage
docker stats

# Optimize Prometheus retention
# Edit monitoring/prometheus/prometheus.yml
# Reduce retention.size to 20GB
```

### Get Help

**Documentation:**
- 📖 [Complete Setup Guide](./docs/MONITORING_SETUP_GUIDE.md)
- 📊 [Cost Optimization Guide](./docs/MONITORING_COST_OPTIMIZATION.md)
- 🚨 [Incident Response Playbook](./docs/incidents/INCIDENT_RESPONSE_PLAYBOOK.md)

**Support:**
- 💬 Slack: `#monitoring` channel
- 📧 Email: devops@psychsync.com
- 🐛 Issues: Create issue in repository

---

## 🎯 Next Steps

### Immediate (After Setup)
1. **Configure alerts** - Set up your Slack/PagerDuty webhooks
2. **Customize dashboards** - Add your business-specific metrics
3. **Set up backups** - Configure data backup for Prometheus
4. **Review costs** - Optimize retention policies

### Week 1
1. **Monitor baseline** - Establish performance baselines
2. **Set up SLAs** - Define and configure service level agreements
3. **Test alerts** - Verify alerting works correctly
4. **Train team** - Onboard team to monitoring tools

### Month 1
1. **Optimize costs** - Implement retention policies and filtering
2. **Add custom metrics** - Track business-specific KPIs
3. **Integrate with CI/CD** - Add monitoring to deployment pipeline
4. **Review performance** - Analyze and optimize based on data

---

## 📈 Success Metrics

Your monitoring is successful when:

**Technical Metrics:**
- ✅ All services are healthy and collecting data
- ✅ Dashboard load time < 3 seconds
- ✅ Alert response time < 2 minutes
- ✅ False positive rate < 5%

**Business Value:**
- ✅ MTTR reduced by 60% or more
- ✅ 99%+ uptime visibility
- ✅ Revenue impact monitoring active
- ✅ Customer experience tracking enabled

**Operational Excellence:**
- ✅ Automated incident response
- ✅ Cost monitoring in place
- ✅ Team trained and empowered
- ✅ Documentation complete and current

---

**🎉 Congratulations!** You now have enterprise-grade monitoring that will help you:

- **Detect issues before users notice**
- **Respond to incidents 10x faster**
- **Make data-driven decisions**
- **Maintain 99.9%+ reliability**
- **Scale confidently with full visibility**

For additional support or questions, reach out to the DevOps team!
