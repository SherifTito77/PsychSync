# PsychSync Security Monitoring

Comprehensive security monitoring system for PsychSync platform with automated metrics collection, API endpoints, and observability platform integration.

---

## 🎯 Overview

This monitoring system provides:

- **Unified Security Metrics** - Aggregates findings from SAST, DAST, and SCA scans
- **Real-time API** - RESTful endpoints for security data access
- **Prometheus Integration** - Native metrics export for observability platforms
- **Compliance Tracking** - Automated compliance status against major security standards
- **Security Scoring** - Unified 0-100 score with letter grades for easy understanding

---

## 📁 Files

| File | Purpose | Lines |
|------|---------|-------|
| `security_metrics.py` | Main metrics collector | 622 |
| `prometheus_metrics.py` | Prometheus exporter | 207 |
| `__init__.py` | Package initialization | - |

**Integration Points:**
- `app/api/v1/endpoints/monitoring.py` - API endpoints (8 security endpoints added)

---

## 🚀 Quick Start

### 1. Test Metrics Collection

```bash
# Run the metrics collector
python -m app.monitoring.security_metrics

# Run the Prometheus exporter
python -m app.monitoring.prometheus_metrics
```

### 2. Access via API

```bash
# Get security overview
curl http://localhost:8000/api/v1/monitoring/security/overview \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get Prometheus metrics
curl http://localhost:8000/api/v1/monitoring/metrics
```

### 3. View in Grafana

Import `deploy/grafana/dashboards/psychsync-security-dashboard.json` into Grafana.

---

## 📊 Security Score

**Calculation:**
```
Base Score: 100
Deductions:
  - Critical: -50 each
  - High: -20 each
  - Medium: -10 each
  - Low: -0 each

Final Score = max(0, 100 - Deductions)
```

**Grade Scale:**
- **A+**: 90-100 (Excellent)
- **A**: 80-89 (Good)
- **B**: 70-79 (Fair)
- **C**: 60-69 (Poor)
- **F**: 0-59 (Failing)

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/monitoring/security/overview` | GET | Security overview with score, grade, findings |
| `/api/v1/monitoring/security/vulnerabilities` | GET | Get vulnerabilities with filtering |
| `/api/v1/monitoring/security/by-tool` | GET | Vulnerability breakdown by tool |
| `/api/v1/monitoring/security/compliance` | GET | Compliance status |
| `/api/v1/monitoring/security/score` | GET | Current security score and grade |
| `/api/v1/monitoring/security/trend` | GET | Security trend over time |
| `/api/v1/monitoring/security/dashboard` | GET | Complete dashboard data |
| `/api/v1/monitoring/security/scan/trigger` | POST | Trigger security scan |

**Full Documentation:** See `docs/MONITORING_QUICK_START.md`

---

## 📈 Prometheus Metrics

### Metric Names

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `psychsync_security_score` | gauge | | Security score (0-100) |
| `psychsync_security_grade` | gauge | grade | Security grade (1-5) |
| `psychsync_vulnerabilities_total` | gauge | | Total vulnerabilities |
| `psychsync_vulnerabilities_by_severity` | gauge | severity | Count by severity |
| `psychsync_vulnerabilities_by_source` | gauge | source | Count by source (SAST/DAST/SCA) |
| `psychsync_vulnerabilities_by_tool` | gauge | tool, severity | Count by tool and severity |
| `psychsync_compliance_status` | gauge | standard | Compliance (0/1) |
| `psychsync_last_scan_timestamp` | gauge | | Unix timestamp |

### Example Output

```
# HELP psychsync_security_score Security score (0-100)
# TYPE psychsync_security_score gauge
psychsync_security_score 85

# HELP psychsync_vulnerabilities_by_severity Number of vulnerabilities by severity
# TYPE psychsync_vulnerabilities_by_severity gauge
psychsync_vulnerabilities_by_severity{severity="critical"} 0
psychsync_vulnerabilities_by_severity{severity="high"} 2
psychsync_vulnerabilities_by_severity{severity="medium"} 8
psychsync_vulnerabilities_by_severity{severity="low"} 5

# HELP psychsync_compliance_status Compliance status (1=compliant, 0=non-compliant)
# TYPE psychsync_compliance_status gauge
psychsync_compliance_status{standard="owasp_asvs_1_4_1"} 1
psychsync_compliance_status{standard="hipaa_security"} 0
```

---

## 🔔 Prometheus Alerts

### Critical Alerts

| Alert | Trigger | Duration | Action |
|-------|---------|----------|--------|
| `CriticalSecurityVulnerability` | `critical > 0` | 5m | Page on-call |
| `CriticalSecurityScore` | `score < 50` | 5m | Page on-call |

### Warning Alerts

| Alert | Trigger | Duration | Action |
|-------|---------|----------|--------|
| `HighSecurityVulnerability` | `high > 0` | 15m | Email team |
| `LowSecurityScore` | `score < 70` | 15m | Create ticket |
| `ExcessiveMediumVulnerabilities` | `medium > 20` | 1h | Review in standup |

### Info Alerts

| Alert | Trigger | Duration | Action |
|-------|---------|----------|--------|
| `ComplianceViolation` | `compliance == 0` | 1h | Update compliance docs |
| `StaleSecurityScan` | `scan_age > 24h` | 1h | Trigger new scan |

**Full Alert Rules:** See `deploy/prometheus/alerts/psychsync_security_alerts.yml`

---

## ✅ Compliance Standards

### Supported Standards

| Standard | Requirements | Status Metric |
|----------|-------------|---------------|
| **OWASP ASVS v1.4.1** | Static code analysis | `sast_findings == 0` |
| **OWASP ASVS v5.2.1** | Dynamic testing | `dast_findings == 0` |
| **OWASP ASVS v7.1.1** | Vulnerability scanning | `sca_findings == 0` |
| **OWASP A08:2021** | Software verification | `critical_severity == 0` |
| **NIST SP 800-53 CM** | Vulnerability management | `critical_severity == 0` |
| **SOC 2 CC7.2** | Monitoring | `critical_severity == 0` |
| **SOC 2 CC7.5** | Remediation | `high_severity < 5` |
| **HIPAA Security** | Comprehensive security | `critical == 0 and high == 0` |

---

## 🛠️ Architecture

```
Scan Results (SARIF/XML)
        │
        ▼
┌────────────────────────────────┐
│  SecurityMetricsCollector      │
│  - Collect from sources        │
│  - Normalize findings          │
│  - Calculate score             │
│  - Check compliance            │
└───────────┬────────────────────┘
            │
    ┌───────┴─────────┐
    ▼                 ▼
┌─────────┐     ┌─────────────┐
│ API     │     │ Prometheus  │
│ Endpoints│    │ Exporter    │
└─────────┘     └──────┬──────┘
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
    ┌────────────┐        ┌────────────┐
    │ Grafana    │        │ Prometheus │
    │ Dashboard  │        │ Alerting   │
    └────────────┘        └────────────┘
```

---

## 🔧 Configuration

### Dependencies

```python
# In requirements.txt
psutil>=5.9.0          # System metrics
prometheus-client>=0.17 # Prometheus integration
```

### Environment Variables

```bash
# Security scan results paths
SAST_RESULTS_PATH=".github/workflows/semgrep-results.json"
DAST_RESULTS_PATH=".github/workflows/zap-results/zap-report.xml"
SCA_RESULTS_PATH=".github/workflows/trivy-results.json"

# Metrics collection
METRICS_RETENTION_DAYS=90
METRICS_COLLECTION_INTERVAL=300  # 5 minutes
```

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'psychsync_security'
    scrape_interval: 5m
    metrics_path: '/api/v1/monitoring/metrics'
    static_configs:
      - targets: ['localhost:8000']
```

---

## 📚 Usage Examples

### Python Code

```python
from app.monitoring.security_metrics import (
    SecurityMetricsCollector,
    collect_security_metrics,
    get_security_score
)

# Collect all metrics
collector = SecurityMetricsCollector()
metrics = await collector.collect_all_metrics()
summary = metrics.get_summary()
print(f"Security Score: {summary['security_score']}")

# Convenience functions
score = await get_security_score()
dashboard_data = await collect_security_metrics()
```

### API Access

```python
import httpx

async def get_security_overview():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/monitoring/security/overview",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()
```

### Prometheus Query

```promql
# Get current security score
psychsync_security_score

# Get vulnerabilities by severity
psychsync_vulnerabilities_by_severity

# Get compliance status
psychsync_compliance_status{standard="owasp_asvs_1_4_1"}

# Get security score trend
rate(psychsync_security_score[5m])

# Alert on critical vulnerabilities
psychsync_vulnerabilities_by_severity{severity="critical"} > 0
```

---

## 🧪 Testing

```bash
# Test metrics collection
python -m pytest tests/test_security_metrics.py -v

# Test API endpoints
pytest tests/api/test_monitoring.py::test_security_overview -v

# Test Prometheus exporter
python -m app.monitoring.prometheus_metrics
```

---

## 🐛 Troubleshooting

### Issue: No Metrics Collected

**Problem:** All findings show 0

**Diagnosis:**
```bash
# Check if scan results exist
ls -la .github/workflows/*results*

# Test collector manually
python -m app.monitoring.security_metrics
```

**Solution:**
1. Ensure GitHub Actions workflows have run
2. Check file paths in collector
3. Verify scan results are in correct format

### Issue: Prometheus Not Scraping

**Problem:** Metrics not appearing in Prometheus

**Diagnosis:**
```bash
# Check if metrics endpoint is accessible
curl http://localhost:8000/api/v1/monitoring/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets
```

**Solution:**
1. Verify FastAPI is running
2. Check Prometheus configuration
3. Ensure network connectivity

### Issue: Score Not Updating

**Problem:** Security score stuck at old value

**Diagnosis:**
```bash
# Check scan timestamp
curl http://localhost:8000/api/v1/monitoring/security/overview | jq '.last_scan'

# Trigger new scan
curl -X POST http://localhost:8000/api/v1/monitoring/security/scan/trigger
```

**Solution:**
1. Trigger new security scan
2. Check for cached results
3. Restart API service if needed

---

## 📖 Documentation

**Detailed Guides:**
- `docs/MONITORING_QUICK_START.md` - Complete setup and usage guide
- `docs/GITHUB_ACTIONS_SECURITY_SUMMARY.md` - Workflow documentation
- `docs/SECURITY_MASTER_INDEX.md` - Master security documentation

**Configuration Files:**
- `deploy/prometheus/prometheus.yml` - Prometheus configuration
- `deploy/prometheus/alerts/psychsync_security_alerts.yml` - Alert rules
- `deploy/grafana/dashboards/psychsync-security-dashboard.json` - Grafana dashboard

---

## 🤝 Contributing

When adding new security metrics:

1. Update `SecurityMetricsCollector` in `security_metrics.py`
2. Add corresponding Prometheus metric in `prometheus_metrics.py`
3. Add API endpoint in `monitoring.py` if needed
4. Update Grafana dashboard
5. Add alert rules if critical
6. Update documentation

---

## 📞 Support

**Questions?**
- Security Team: @security-team
- DevOps: @devops
- Create issue in repository

---

**Status:** ✅ Production Ready
**Last Updated:** 2025-12-26
**Maintained By:** @security-team
