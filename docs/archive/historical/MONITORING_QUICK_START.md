# Security Monitoring Quick Start Guide

**Last Updated:** 2025-12-26
**Status:** ✅ Production Ready

---

## Overview

PsychSync provides comprehensive security monitoring with automated metrics collection, API endpoints, and Prometheus integration for observability platforms.

### What's Included

- **Security Metrics Collector** - Aggregates findings from SAST, DAST, and SCA scans
- **API Endpoints** - RESTful endpoints for real-time security data
- **Prometheus Exporter** - Metrics in Prometheus format for scraping
- **Compliance Tracking** - Status against OWASP, NIST, SOC 2, HIPAA standards
- **Security Scoring** - Unified 0-100 score with letter grades

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Security Monitoring                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────┐│
│  │   SAST       │    │   DAST       │    │    SCA      ││
│  │  (Semgrep)   │    │  (OWASP ZAP) │    │ (Trivy/Snyk)││
│  └──────┬───────┘    └──────┬───────┘    └──────┬──────┘│
│         │                   │                    │        │
│         └───────────────────┴────────────────────┘        │
│                         │                                 │
│                         ▼                                 │
│         ┌─────────────────────────────┐                  │
│         │  SecurityMetricsCollector   │                  │
│         │  - Normalizes findings      │                  │
│         │  - Calculates score         │                  │
│         │  - Checks compliance        │                  │
│         └───────────┬─────────────────┘                  │
│                     │                                     │
│         ┌───────────┴─────────────────┐                  │
│         ▼                             ▼                  │
│  ┌──────────────┐          ┌────────────────┐            │
│  │ API Endpoints│          │  Prometheus    │            │
│  │ /monitoring/ │          │  Exporter      │            │
│  │  security/*  │          │  /metrics      │            │
│  └──────────────┘          └────────────────┘            │
│                                                             │
└───────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Test the Security Metrics

Run the security metrics CLI to see current status:

```bash
# From project root
python -m app.monitoring.security_metrics
```

**Expected Output:**
```
============================================================
🔒 PSYCHSYNC SECURITY METRICS
============================================================

📅 Scan Date: 2025-12-26T10:30:00
📊 Security Score: 85/100 (A)

📈 Total Findings: 15
   🔴 Critical: 0
   🟠 High:     2
   🟡 Medium:   8
   🟢 Low:      5

------------------------------------------------------------
Breakdown by Source:
------------------------------------------------------------
SAST (Semgrep): 5
DAST (OWASP ZAP): 3
SCA (Dependencies): 7

------------------------------------------------------------
Top 10 Vulnerabilities:
------------------------------------------------------------

1. SQL Injection in user_service.py
   Severity: HIGH
   Location: app/services/user_service.py:127

...
```

### 2. Access API Endpoints

All endpoints require authentication and `monitoring:read` permission.

#### Get Security Overview

```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/security/overview" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "security_score": 85,
    "security_grade": "A",
    "total_findings": 15,
    "last_scan": "2025-12-26T10:30:00",
    "severity_breakdown": {
      "critical": 0,
      "high": 2,
      "medium": 8,
      "low": 5
    },
    "by_source": {
      "sast": 5,
      "dast": 3,
      "sca": 7
    },
    "compliance_status": {
      "owasp_asvs_1_4_1": true,
      "owasp_asvs_5_2_1": false,
      "owasp_asvs_7_1_1": false,
      "owasp_a08_2021": true,
      "nist_800_53_cm": true,
      "soc_2_cc7_2": true,
      "hipaa_security": false
    }
  }
}
```

#### Get Vulnerabilities

```bash
# Get all vulnerabilities
curl -X GET "http://localhost:8000/api/v1/monitoring/security/vulnerabilities?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by severity
curl -X GET "http://localhost:8000/api/v1/monitoring/security/vulnerabilities?severity=high&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by source
curl -X GET "http://localhost:8000/api/v1/monitoring/security/vulnerabilities?source=SAST&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Tool Breakdown

```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/security/by-tool" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "semgrep": {
      "critical": 0,
      "high": 1,
      "medium": 3,
      "low": 1,
      "total": 5
    },
    "zap": {
      "critical": 0,
      "high": 0,
      "medium": 2,
      "low": 1,
      "total": 3
    },
    "trivy": {
      "critical": 0,
      "high": 1,
      "medium": 3,
      "low": 3,
      "total": 7
    },
    "snyk": {
      "critical": 0,
      "high": 0,
      "medium": 0,
      "low": 0,
      "total": 0
    }
  }
}
```

#### Get Compliance Status

```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/security/compliance" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Security Score

```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/security/score" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Security Trend

```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/security/trend?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Complete Dashboard

```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/security/dashboard" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Trigger Security Scan

```bash
# Requires monitoring:write permission
curl -X POST "http://localhost:8000/api/v1/monitoring/security/scan/trigger?scan_type=all" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Trigger specific scan type
curl -X POST "http://localhost:8000/api/v1/monitoring/security/scan/trigger?scan_type=sast" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Prometheus Metrics

Run the Prometheus exporter to generate metrics:

```bash
python -m app.monitoring.prometheus_metrics
```

**Output:**
```
============================================================
📊 PSYCHSYNC SECURITY METRICS (PROMETHEUS FORMAT)
============================================================

# HELP psychsync_security_score Security score (0-100)
# TYPE psychsync_security_score gauge
psychsync_security_score 85

# HELP psychsync_security_grade Security grade (A+, A, B, C, F)
# TYPE psychsync_security_grade gauge
psychsync_security_score{grade="A"} 4

# HELP psychsync_vulnerabilities_total Total number of vulnerabilities
# TYPE psychsync_vulnerabilities_total gauge
psychsync_vulnerabilities_total 15

# HELP psychsync_vulnerabilities_by_severity Number of vulnerabilities by severity
# TYPE psychsync_vulnerabilities_by_severity gauge
psychsync_vulnerabilities_by_severity{severity="critical"} 0
psychsync_vulnerabilities_by_severity{severity="high"} 2
psychsync_vulnerabilities_by_severity{severity="medium"} 8
psychsync_vulnerabilities_by_severity{severity="low"} 5

# HELP psychsync_vulnerabilities_by_source Number of vulnerabilities by source
# TYPE psychsync_vulnerabilities_by_source gauge
psychsync_vulnerabilities_by_source{source="SAST"} 5
psychsync_vulnerabilities_by_source{source="DAST"} 3
psychsync_vulnerabilities_by_source{source="SCA"} 7

# HELP psychsync_vulnerabilities_by_tool Number of vulnerabilities by tool
# TYPE psychsync_vulnerabilities_by_tool gauge
psychsync_vulnerabilities_by_tool{tool="semgrep"} 5
psychsync_vulnerabilities_by_tool{tool="zap"} 3
psychsync_vulnerabilities_by_tool{tool="trivy"} 7

# HELP psychsync_compliance_status Compliance status (1=compliant, 0=non-compliant)
# TYPE psychsync_compliance_status gauge
psychsync_compliance_status{standard="owasp_asvs_1_4_1"} 1
psychsync_compliance_status{standard="owasp_asvs_5_2_1"} 0
psychsync_compliance_status{standard="owasp_asvs_7_1_1"} 0
psychsync_compliance_status{standard="owasp_a08_2021"} 1
psychsync_compliance_status{standard="nist_800_53_cm"} 1
psychsync_compliance_status{standard="soc_2_cc7_2"} 1
psychsync_compliance_status{standard="hipaa_security"} 0

# HELP psychsync_last_scan_timestamp Unix timestamp of last security scan
# TYPE psychsync_last_scan_timestamp gauge
psychsync_last_scan_timestamp 1735210200
```

---

## API Endpoint Reference

### Security Monitoring Endpoints

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/v1/monitoring/security/overview` | GET | Security overview with score, grade, findings | `monitoring:read` |
| `/api/v1/monitoring/security/vulnerabilities` | GET | Get vulnerabilities with filtering | `monitoring:read` |
| `/api/v1/monitoring/security/by-tool` | GET | Vulnerability breakdown by tool | `monitoring:read` |
| `/api/v1/monitoring/security/compliance` | GET | Compliance status | `monitoring:read` |
| `/api/v1/monitoring/security/score` | GET | Current security score and grade | `monitoring:read` |
| `/api/v1/monitoring/security/trend` | GET | Security trend over time | `monitoring:read` |
| `/api/v1/monitoring/security/dashboard` | GET | Complete dashboard data | `monitoring:read` |
| `/api/v1/monitoring/security/scan/trigger` | POST | Trigger security scan | `monitoring:write` |

### Query Parameters

**Vulnerabilities Endpoint:**
- `severity` - Filter by severity: `critical`, `high`, `medium`, `low`
- `source` - Filter by source: `SAST`, `DAST`, `SCA`
- `limit` - Max results (1-500, default: 100)

**Trend Endpoint:**
- `days` - Number of days to analyze (1-90, default: 30)

**Scan Trigger Endpoint:**
- `scan_type` - Type of scan: `sast`, `dast`, `sca`, `all` (default: `all`)

---

## Prometheus Integration

### Option 1: Manual Export

```bash
# Generate metrics
python -m app.monitoring.prometheus_metrics > /tmp/security_metrics.txt

# Make available to Prometheus
mv /tmp/security_metrics.txt /var/lib/prometheus/textfile_collector/psychsync_security.prom
```

### Option 2: API Endpoint

Add to your FastAPI application:

```python
from fastapi import Response
from app.monitoring.prometheus_metrics import generate_prometheus_metrics

@router.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    metrics_text = await generate_prometheus_metrics()
    return Response(content=metrics_text, media_type="text/plain")
```

Configure Prometheus to scrape:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'psychsync_security'
    scrape_interval: 5m
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/monitoring/metrics'
```

### Option 3: Grafana Dashboard

Import the provided Grafana dashboard JSON (see `deploy/grafana/psychsync-security-dashboard.json`).

**Metrics to Visualize:**
- `psychsync_security_score` - Gauge panel
- `psychsync_vulnerabilities_by_severity` - Bar chart
- `psychsync_vulnerabilities_by_tool` - Pie chart
- `psychsync_compliance_status` - Stat panel
- Trend over time - Time series graph

---

## Security Score Calculation

The security score is calculated as follows:

```
Base Score: 100
Deductions:
  - Critical severity: -50 each
  - High severity: -20 each
  - Medium severity: -10 each
  - Low severity: -0 each

Final Score = max(0, Base Score - Deductions)
```

**Grade Scale:**
- **A+**: 90-100
- **A**: 80-89
- **B**: 70-79
- **C**: 60-69
- **F**: 0-59

**Example:**
```
Findings: 0 Critical, 2 High, 8 Medium, 5 Low
Score = 100 - (0 * 50) - (2 * 20) - (8 * 10) - (5 * 0)
      = 100 - 0 - 40 - 80 - 0
      = -20 → max(0, -20) = 0
Grade = F
```

---

## Compliance Standards

### OWASP ASVS v3.2.1

| Requirement | Implementation | Status Metric |
|-------------|----------------|---------------|
| v1.4.1 - Static Code Analysis | Semgrep on every PR | `sast_findings == 0` |
| v5.2.1 - Dynamic Testing | ZAP scans on staging | `dast_findings == 0` |
| v7.1.1 - Vulnerability Scanning | Trivy, Snyk, Safety | `sca_findings == 0` |

### OWASP Top 10 (2021)

| Risk | Mitigation | Status Metric |
|------|------------|---------------|
| A08: Software Verification | Dependency scanning | `critical_severity == 0` |

### NIST SP 800-53

| Control | Implementation | Status Metric |
|---------|----------------|---------------|
| CM - Vulnerability Management | Automated SCA | `critical_severity == 0` |

### SOC 2 Type II

| Criteria | Implementation | Status Metric |
|----------|----------------|---------------|
| CC7.2 - Monitoring | Continuous security scanning | `critical_severity == 0` |
| CC7.5 - Vulnerability Remediation | Automated blocking | `high_severity < 5` |

### HIPAA Security Rule

| Requirement | Implementation | Status Metric |
|-------------|----------------|---------------|
| §164.308(a) - Security Management | Comprehensive security testing | `critical_severity == 0 and high_severity == 0` |

---

## File Locations

```
app/monitoring/
├── security_metrics.py      # Main metrics collector
├── prometheus_metrics.py    # Prometheus exporter
└── __init__.py

app/api/v1/endpoints/
└── monitoring.py            # API endpoints (includes security section)

docs/
├── MONITORING_QUICK_START.md      # This file
├── GITHUB_ACTIONS_SECURITY_SUMMARY.md
└── SECURITY_MASTER_INDEX.md
```

---

## Troubleshooting

### Issue: Metrics Not Collecting

**Problem:** API returns 0 findings or errors

**Solutions:**
1. Check scan results exist in `.github/workflows/` directory
2. Verify file paths in `security_metrics.py`
3. Check file permissions

```bash
# Check if scan results exist
ls -la .github/workflows/*results*

# Test collector manually
python -m app.monitoring.security_metrics
```

### Issue: Score Always 0 or 100

**Problem:** Security score not calculating correctly

**Solutions:**
1. Verify severity mapping in collector
2. Check finding counts by severity
3. Review calculation logic in `calculate_security_score()`

### Issue: Prometheus Metrics Not Updating

**Problem:** Metrics showing stale data

**Solutions:**
1. Check scan timestamps
2. Verify Prometheus scrape interval
3. Trigger new security scan

```bash
# Trigger new scan
curl -X POST "http://localhost:8000/api/v1/monitoring/security/scan/trigger" \
  -H "Authorization: Bearer $TOKEN"
```

### Issue: Compliance Status Incorrect

**Problem:** Compliance showing wrong status

**Solutions:**
1. Review compliance logic in `get_compliance_status()`
2. Check severity thresholds
3. Verify standard requirements

---

## Best Practices

### For Developers

1. **Run scans locally** before pushing
   ```bash
   semgrep --config=auto
   trivy fs .
   npm audit
   ```

2. **Fix high-severity findings** immediately

3. **Keep dependencies updated** to reduce SCA findings

4. **Review security dashboard** weekly

### For Security Team

1. **Review metrics daily** via dashboard or API

2. **Tune scanning rules** to reduce false positives

3. **Monitor trends** to catch deteriorating security posture

4. **Set up alerts** for critical vulnerabilities

5. **Update compliance requirements** as standards evolve

### For DevOps

1. **Configure Prometheus scraping** every 5 minutes

2. **Set up Grafana dashboards** for visualization

3. **Create alerting rules** in Prometheus
   ```yaml
   # Example: Alert on critical vulnerabilities
   - alert: CriticalSecurityVulnerability
     expr: psychsync_vulnerabilities_by_severity{severity="critical"} > 0
     for: 5m
     labels:
       severity: critical
     annotations:
       summary: "Critical security vulnerability detected"
   ```

4. **Monitor scan execution times** to ensure workflows complete

---

## Next Steps

1. **Configure secrets** in GitHub repository for workflow execution
2. **Test workflows** by pushing code or triggering manually
3. **Set up monitoring** dashboard with Grafana or similar
4. **Configure alerts** for critical/high vulnerabilities
5. **Review and tune** scanning rules to reduce false positives
6. **Document team processes** for security review workflows

---

## Additional Resources

**Internal Documentation:**
- `docs/GITHUB_ACTIONS_SECURITY_SUMMARY.md` - Complete workflow documentation
- `docs/SECURITY_MASTER_INDEX.md` - Master security documentation
- `.github/workflows/README.md` - Workflow quick reference

**External Tools:**
- [Semgrep Documentation](https://semgrep.dev/docs/)
- [OWASP ZAP Documentation](https://www.zaproxy.org/docs/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Prometheus Documentation](https://prometheus.io/docs/)

**Support:**
- Security Team: @security-team
- DevOps: @devops
- Create issue in repository

---

**Status:** ✅ Production Ready
**Last Updated:** 2025-12-26
**Maintained By:** @security-team
