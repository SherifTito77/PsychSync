# Complete Deployment Guide
## Production Monitoring & CI/CD Setup

**Date:** January 6, 2026
**Purpose:** Deploy monitoring stack and verify CI/CD workflows

---

## 📊 MONITORING STACK DEPLOYMENT

### Prerequisites

**Required Software:**
1. **Docker Desktop** (macOS/Windows) or **Docker Engine** (Linux)
   - macOS: https://docs.docker.com/desktop/install/mac-install/
   - Linux: https://docs.docker.com/engine/install/

2. **Docker Compose** (included with Docker Desktop)
   - Verify installation: `docker compose version`

### Quick Start Deployment

**Option 1: Automated Deployment Script**
```bash
# Run the interactive deployment script
./scripts/deploy_monitoring.sh
```

**Option 2: Manual Deployment**
```bash
# Navigate to deploy directory
cd deploy

# Start all services
docker compose -f monitoring-stack.yml up -d

# View logs
docker compose -f monitoring-stack.yml logs -f
```

### Services Deployed

| Service | Port | Purpose | Access Credentials |
|---------|------|---------|-------------------|
| **Grafana** | 3000 | Visualization dashboards | admin/admin |
| **Prometheus** | 9090 | Metrics collection | No auth (local only) |
| **Redis** | 6379 | Caching & metrics | No password (local) |

### Access Points

**Grafana Dashboard:**
```
URL: http://localhost:3000
Username: admin
Password: admin
```

**Prometheus:**
```
URL: http://localhost:9090
Targets: http://localhost:9090/targets
Config: http://localhost:9090/config
Alerts: http://localhost:9090/alerts
```

**Redis:**
```
Port: localhost:6379
CLI: redis-cli ping
```

### Dashboards Available

1. **PsychSync Security Dashboard** (`psychsync-security-dashboard.json`)
   - Security event metrics
   - Authentication/authorization tracking
   - Threat detection visualization

2. **PsychSync Threat Detection Dashboard** (`psychsync-threat-detection-dashboard.json`)
   - Real-time threat monitoring
   - Attack pattern detection
   - Security alert trends

3. **Redis Cache Dashboard** (`redis-cache-dashboard.json`)
   - Cache hit rates
   - Memory usage
   - Key statistics

### Import Dashboards into Grafana

**Method 1: Automatic (Provisioning)**
Dashboards are automatically loaded if provisioning is configured:
```bash
# Dashboards should appear in Grafana at:
# http://localhost:3000/dashboards
```

**Method 2: Manual Import**
1. Open Grafana: http://localhost:3000
2. Click **+ → Import**
3. Upload JSON files from `deploy/grafana/dashboards/`:
   - `psychsync-security-dashboard.json`
   - `psychsync-threat-detection-dashboard.json`
   - `redis-cache-dashboard.json`

### Configure Prometheus Data Source

**Automatic (Provisioned):**
- Already configured in `deploy/grafana/provisioning/datasources/prometheus.yml`
- URL: `http://prometheus:9090`

**Manual Configuration:**
1. Open Grafana: http://localhost:3000
2. Navigate to **Configuration → Data Sources**
3. Click **Add data source → Prometheus**
4. Configure:
   - **Name:** Prometheus
   - **URL:** http://prometheus:9090
   - **Access:** Server (default)
   - Click **Save & Test**

### Verify Monitoring Stack

**Health Checks:**
```bash
# Check Grafana
curl -s http://localhost:3000/api/health

# Check Prometheus
curl -s http://localhost:9090/-/healthy

# Check Redis
redis-cli ping
```

**View Logs:**
```bash
# All services
docker compose -f deploy/monitoring-stack.yml logs -f

# Specific service
docker compose -f deploy/monitoring-stack.yml logs -f grafana
docker compose -f deploy/monitoring-stack.yml logs -f prometheus
docker compose -f deploy/monitoring-stack.yml logs -f redis
```

**Check Status:**
```bash
# Service status
docker compose -f deploy/monitoring-stack.yml ps

# Resource usage
docker stats
```

### Management Commands

**Stop Services:**
```bash
cd deploy
docker compose -f monitoring-stack.yml down
```

**Restart Services:**
```bash
cd deploy
docker compose -f monitoring-stack.yml restart
```

**Update Services:**
```bash
cd deploy
docker compose -f monitoring-stack.yml up -d --force-recreate
```

**View Metrics:**
```bash
# Prometheus targets
curl http://localhost:9090/api/v1/targets

# Prometheus metrics
curl http://localhost:9090/api/v1/label/__name__/values

# Query metrics
curl http://localhost:9090/api/v1/query?query=up
```

---

## 🔄 CI/CD WORKFLOW MONITORING

### GitHub Actions Workflows

**Available Workflows:**
1. **SBOM Generation** - `.github/workflows/sbom.yaml`
2. **Security Scanning** - `.github/workflows/security-scan.yml`
3. **Linting** - `.github/workflows/lint.yml`
4. **Agent Deployment** - `.github/workflows/agents.yml`
5. **AI Security Gate** - `.github/workflows/ai-security-gate.yml`
6. **SLSA Signing** - `.github/workflows/slsa-sign.yaml`

### Monitor Workflows (Web UI)

**1. Open GitHub Repository**
```
URL: https://github.com/SherifTito77/PsychSync/actions
```

**2. View Workflow Runs**
- Navigate to **Actions** tab
- See all recent workflow runs
- Click on specific workflow for details

**3. Check Workflow Status**
- ✅ **Green checkmark** - Success
- ❌ **Red X** - Failed
- 🟡 **Yellow dot** - In progress
- ⚪ **Grey circle** - Not run

### Monitor Workflows (GitHub CLI)

**Install GitHub CLI:**
```bash
# macOS
brew install gh

# Authenticate
gh auth login
```

**List Recent Runs:**
```bash
gh run list --limit 10
```

**View Specific Run:**
```bash
# View last run details
gh run view

# View specific run
gh run view <run-id>

# View logs
gh run view --log
```

**Watch Workflow in Real-time:**
```bash
# Watch latest run
gh run watch

# Watch specific run
gh run watch <run-id>
```

### Workflow Files Overview

**1. SBOM Generation** (`sbom.yaml`)
- **Purpose:** Generate Software Bill of Materials
- **Trigger:** Push to main, pull request
- **Output:** SBOM JSON files
- **Frequency:** Every commit

**2. Security Scanning** (`security-scan.yml`)
- **Purpose:** Run security scans (Bandit, Semgrep)
- **Trigger:** Push, pull request, manual
- **Tools:** Bandit, Semgrep, Safety
- **Duration:** ~5 minutes

**3. Linting** (`lint.yml`)
- **Purpose:** Code quality checks with Ruff
- **Trigger:** Push, pull request, manual
- **Tool:** Ruff (fast Python linter)
- **Duration:** ~2 minutes

**4. Agent Deployment** (`agents.yml`)
- **Purpose:** Deploy AI agents
- **Trigger:** Manual dispatch
- **Agents:** Code analysis, testing, deployment
- **Duration:** Variable

**5. AI Security Gate** (`ai-security-gate.yml`)
- **Purpose:** Validate AI/ML model security
- **Trigger:** Push to main
- **Checks:** Model scanning, validation
- **Duration:** ~10 minutes

**6. SLSA Signing** (`slsa-sign.yaml`)
- **Purpose:** Generate SLSA provenance
- **Trigger:** Release creation
- **Output:** Signed artifacts
- **Duration:** ~3 minutes

### Workflow Status Interpretation

**Success Indicators:**
- ✅ All checks pass
- 📊 Security scans clean
- 🔍 No vulnerabilities found
- 📝 Linting passes

**Failure Investigation:**
1. Click on failed workflow
2. Expand failed step
3. Review error logs
4. Fix issues
5. Push changes

**Common Issues:**
- **Linting errors:** Fix code style issues
- **Security findings:** Review and remediate
- **Test failures:** Debug and fix tests
- **Dependency issues:** Update requirements

### Configure Workflow Notifications

**Email Notifications:**
```bash
# Go to repository Settings → Notifications
# Add email notification rules
```

**Slack Integration:**
```yaml
# Add to workflow files:
notifications:
  slack:
    webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
```

**Status Badge:**
```markdown
![CI/CD](https://github.com/SherifTito77/PsychSync/actions/workflows/main.yml/badge.svg)
```

---

## 🔧 CONFIGURATION FILES

### Monitoring Stack Configuration

**1. Docker Compose** (`deploy/monitoring-stack.yml`)
- Defines 3 services: Prometheus, Grafana, Redis
- Configures volumes and networks
- Sets environment variables

**2. Prometheus Configuration** (`deploy/prometheus/prometheus.yml`)
- Scrape intervals: 15s default
- Job targets: PsychSync API, health endpoints
- Alert rules: From `alerts/` directory

**3. Grafana Provisioning**
- **Datasource:** `deploy/grafana/provisioning/datasources/prometheus.yml`
- **Dashboards:** `deploy/grafana/provisioning/dashboards/dashboards.yml`
- **Dashboards:** `deploy/grafana/dashboards/*.json` (3 files)

### Customize Configuration

**Add New Scrape Target:**
```yaml
# Edit deploy/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'my_service'
    static_configs:
      - targets: ['localhost:PORT']
```

**Add New Dashboard:**
```bash
# 1. Export dashboard from Grafana as JSON
# 2. Save to deploy/grafana/dashboards/
# 3. Restart monitoring stack
```

**Configure Alerts:**
```yaml
# Edit deploy/prometheus/alerts/*.yml
# Add alerting rules
# Restart Prometheus to apply
```

---

## 📈 MONITORING METRICS

### Key Metrics to Monitor

**Application Metrics:**
- Request rate (requests/second)
- Response time (latency)
- Error rate (5xx errors)
- Database connection pool usage
- Cache hit/miss ratio

**Security Metrics:**
- Authentication failures
- Authorization denials
- Rate limit violations
- CSRF token validation failures
- Suspicious activity patterns

**System Metrics:**
- CPU usage
- Memory usage
- Disk I/O
- Network traffic

### Example Queries

**Request Rate:**
```promql
rate(http_requests_total[5m])
```

**Error Rate:**
```promql
rate(http_requests_total{status=~"5.."}[5m])
```

**Response Time:**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Cache Hit Rate:**
```promql`
rate(redis_cache_hits_total[5m]) / rate(redis_cache_operations_total[5m])
```

---

## 🚨 ALERT CONFIGURATION

### Prometheus Alert Rules

**Available Alert Files:**
- `deploy/prometheus/alerts/psychsync_threat_detection_alerts.yml`

**Example Alert:**
```yaml
groups:
  - name: threat_detection
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
```

### Configure Alert Notifications

**Email Notifications:**
```yaml
# Add to prometheus.yml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

**Slack Notifications:**
```yaml
# Requires Alertmanager configuration
receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: $SLACK_WEBHOOK_URL
```

---

## 🛠️ TROUBLESHOOTING

### Common Issues

**Issue 1: Services Won't Start**
```bash
# Check Docker is running
docker ps

# Check for port conflicts
lsof -i :3000
lsof -i :9090

# View service logs
docker compose -f deploy/monitoring-stack.yml logs
```

**Issue 2: Grafana Can't Connect to Prometheus**
```bash
# Check Prometheus is accessible
curl http://localhost:9090/-/healthy

# Check network
docker network inspect deploy_monitoring

# Restart Grafana
docker compose -f deploy/monitoring-stack.yml restart grafana
```

**Issue 3: Dashboards Not Loading**
```bash
# Check provisioning files exist
ls -la deploy/grafana/provisioning/

# Check dashboard files exist
ls -la deploy/grafana/dashboards/

# Restart Grafana to reload provisioning
docker compose -f deploy/monitoring-stack.yml restart grafana
```

**Issue 4: CI/CD Workflows Not Running**
```bash
# Check workflow files exist
ls -la .github/workflows/

# Verify GitHub Actions is enabled
# Go to: https://github.com/SherifTito77/PsychSync/actions

# Check workflow syntax
# Open each workflow file in GitHub editor
```

**Issue 5: Workflows Failing**
```bash
# View recent runs
gh run list

# View failed run logs
gh run view <run-id> --log-failed

# Re-run workflow
gh run rerun <run-id>
```

### Debug Commands

**Docker Diagnostics:**
```bash
# Container status
docker ps -a

# Container logs
docker logs <container-name>

# Exec into container
docker exec -it <container-name> /bin/sh

# Resource usage
docker stats
```

**Monitoring Diagnostics:**
```bash
# Prometheus targets
curl http://localhost:9090/api/v1/targets

# Prometheus config
curl http://localhost:9090/config

# Prometheus alerts
curl http://localhost:9090/api/v1/rules
```

**Grafana Diagnostics:**
```bash
# Grafana health
curl http://localhost:3000/api/health

# Grafana dashboards
curl http://localhost:3000/api/search

# Grafana datasources
curl http://localhost:3000/api/datasources
```

---

## 📚 REFERENCE DOCUMENTATION

**Helpful Links:**

- **Grafana Docs:** https://grafana.com/docs/
- **Prometheus Docs:** https://prometheus.io/docs/
- **Docker Compose:** https://docs.docker.com/compose/
- **GitHub Actions:** https://docs.github.com/en/actions

**Related Documentation:**
- `docs/SECURITY_MONITORING_GUIDE.md`
- `docs/THREAT_DETECTION_DASHBOARD_GUIDE.md`
- `deploy/grafana/SETUP_CACHE_MONITORING.md`

---

## ✅ DEPLOYMENT CHECKLIST

### Pre-Deployment
- [x] Docker installed
- [ ] Docker Compose available
- [x] Monitoring configuration files created
- [x] Grafana dashboards defined
- [ ] Prometheus alerts configured
- [ ] Firewall ports open (3000, 9090, 6379)

### Deployment Steps
- [ ] Run deployment script: `./scripts/deploy_monitoring.sh`
- [ ] Verify services: `docker compose ps`
- [ ] Check Grafana: http://localhost:3000
- [ ] Check Prometheus: http://localhost:9090
- [ ] Import dashboards (if not auto-loaded)
- [ ] Verify data sources
- [ ] Configure alert notifications

### Post-Deployment
- [ ] Monitor service health
- [ ] Review dashboard metrics
- [ ] Verify alert rules
- [ ] Test alert notifications
- [ ] Configure retention policies
- [ ] Set up backup for Grafana data

### CI/CD Verification
- [ ] Check GitHub Actions tab
- [ ] Verify workflows triggered
- [ ] Review workflow run logs
- [ ] Fix any failed workflows
- [ ] Configure notifications
- [ ] Add status badges to README

---

**Last Updated:** January 6, 2026
**Status:** ✅ Configuration Complete, Deployment Pending Docker Installation
**Next Steps:** Install Docker, run deployment script, verify CI/CD workflows
