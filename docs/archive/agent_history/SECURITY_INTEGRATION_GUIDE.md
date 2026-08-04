# Security Middleware Integration Guide

**Purpose:** Step-by-step guide to integrate security enhancements into PsychSync application

---

## Table of Contents
1. [Host Header Validation Middleware](#1-host-header-validation-middleware)
2. [Security Testing Integration](#2-security-testing-integration)
3. [Automated Security Monitoring](#3-automated-security-monitoring)
4. [CI/CD Security Pipeline](#4-cicd-security-pipeline)

---

## 1. Host Header Validation Middleware

### Overview
The Host header validation middleware prevents DNS rebinding and host injection attacks by validating that incoming requests come from allowed hosts.

### Integration Steps

#### Step 1: Environment Configuration

Add to `.env`:
```bash
# Development
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Production
ALLOWED_HOSTS=api.psychsync.com,psychsync.com,www.psychsync.com
```

#### Step 2: Update Configuration

Add to `app/core/config/settings.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Host validation
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"],
        description="Allowed hosts for Host header validation"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True
```

#### Step 3: Integrate Middleware

Add to `app/main.py` around line 504 (after Enterprise Security Middleware):

```python
# Import the middleware
from app.middleware.host_validation import create_host_validation_middleware

# Add middleware with strict mode for production
app.add_middleware(
    create_host_validation_middleware(
        app,
        strict=settings.ENVIRONMENT == "production"
    )
)
```

**Complete integration context:**

```python
# --- ENTERPRISE SECURITY MIDDLEWARE CONFIGURATION ---

# 1. Add enterprise security middleware FIRST (highest priority)
app.add_middleware(EnterpriseSecurityMiddleware)

# 2. Add Host header validation (NEW)
app.add_middleware(
    create_host_validation_middleware(
        app,
        strict=settings.ENVIRONMENT == "production"
    )
)
logger.info("Host header validation middleware configured")

# 3. Rate limiting middleware
app.state.limiter = limiter
# ... rest of middleware configuration
```

#### Step 4: Testing

Test the integration:

```bash
# Test with valid host
curl -H "Host: localhost:8000" http://localhost:8000/health

# Test with invalid host (should return 400)
curl -H "Host: evil.com" http://localhost:8000/health

# Run automated tests
python3 test_host_header_validation.py --url http://localhost:8000
```

### Troubleshooting

**Issue:** All requests returning 400
- **Cause:** ALLOWED_HOSTS not configured or contains wildcard in production
- **Fix:** Set ALLOWED_HOSTS in environment with actual domain names

**Issue:** Health checks failing
- **Cause:** Strict mode blocking all requests
- **Fix:** Use non-strict mode in development, or add health check domains to ALLOWED_HOSTS

**Issue:** CORS errors after enabling
- **Cause:** CORS origins not matching allowed hosts
- **Fix:** Ensure CORS_ORIGINS and ALLOWED_HOSTS are aligned

---

## 2. Security Testing Integration

### Overview
Integrate security testing into your development workflow.

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo "🔒 Running security checks..."

# Run type checks
echo "Checking types..."
npm run type-check || exit 1

# Run security audit
echo "Running security audit..."
python3 network_layer_security_audit.py --host localhost --port 8000 --output /tmp/security_audit.json

# Check for critical findings
if grep -q '"severity": "CRITICAL"' /tmp/security_audit.json 2>/dev/null; then
    echo "❌ Critical security findings detected! Commit aborted."
    cat /tmp/security_audit.json
    exit 1
fi

echo "✅ Security checks passed"
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

### Pytest Integration

Add to `tests/conftest.py`:

```python
import pytest
from network_layer_security_audit import NetworkSecurityAuditor

@pytest.fixture(scope="session")
def security_audit_result():
    """Run security audit once per test session"""
    auditor = NetworkSecurityAuditor("localhost", 8000)
    results = auditor.run_all_audits()
    return results

@pytest.mark.security
def test_no_critical_vulnerabilities(security_audit_result):
    """Ensure no critical security vulnerabilities"""
    findings = security_audit_result.get("audits", {}).get("tls_configuration", {}).get("findings", [])
    critical = [f for f in findings if f.get("severity") == "CRITICAL"]
    assert len(critical) == 0, f"Critical vulnerabilities found: {critical}"

@pytest.mark.security
def test_security_headers_present(security_audit_result):
    """Ensure security headers are configured"""
    # Add specific header checks
    pass
```

Run security tests:
```bash
# Run all security tests
pytest -m security

# Run specific test
pytest tests/test_security.py::test_no_critical_vulnerabilities -v
```

### GitHub Actions Integration

Create `.github/workflows/security-scan.yml`:

```yaml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * 1'  # Weekly at 2 AM Monday

jobs:
  security-scan:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install requests

      - name: Start application
        run: |
          python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 10

      - name: Run security audit
        run: |
          python3 network_layer_security_audit.py \
            --host localhost \
            --port 8000 \
            --output security_audit.json

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: security-audit-results
          path: security_audit.json

      - name: Check for critical vulnerabilities
        run: |
          if grep -q '"severity": "CRITICAL"' security_audit.json; then
            echo "Critical vulnerabilities found!"
            exit 1
          fi
```

---

## 3. Automated Security Monitoring

### Overview
Set up continuous security monitoring for your production environment.

### Prometheus Metrics

Add to `app/main.py`:

```python
from prometheus_client import Counter, Histogram, make_asgi_app

# Security metrics
security_violations = Counter(
    'security_violations_total',
    'Total security violations detected',
    ['violation_type', 'severity']
)

host_header_rejections = Counter(
    'host_header_rejections_total',
    'Total rejected Host headers',
    ['host', 'reason']
)

ssl_handshake_failures = Counter(
    'ssl_handshake_failures_total',
    'Total SSL handshake failures'
)

# Expose metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### Grafana Dashboard

Create `monitoring/grafana/security-dashboard.json`:

```json
{
  "dashboard": {
    "title": "Security Monitoring",
    "panels": [
      {
        "title": "Security Violations by Type",
        "type": "graph",
        "targets": [{
          "expr": "rate(security_violations_total[5m])",
          "legendFormat": "{{violation_type}}"
        }]
      },
      {
        "title": "Host Header Rejections",
        "type": "graph",
        "targets": [{
          "expr": "rate(host_header_rejections_total[5m])",
          "legendFormat": "{{host}}"
        }]
      },
      {
        "title": "SSL Handshake Failures",
        "type": "graph",
        "targets": [{
          "expr": "rate(ssl_handshake_failures_total[5m])"
        }]
      }
    ]
  }
}
```

### Alert Rules

Create `monitoring/prometheus/security-alerts.yml`:

```yaml
groups:
  - name: security_alerts
    interval: 30s
    rules:
      - alert: HighRateOfSecurityViolations
        expr: rate(security_violations_total[5m]) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High rate of security violations detected"
          description: "More than 10 security violations per second"

      - alert: HostHeaderRejectionSpike
        expr: rate(host_header_rejections_total[5m]) > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Spike in Host header rejections"
          description: "Possible DNS rebinding attack"

      - alert: SSLFailuresDetected
        expr: rate(ssl_handshake_failures_total[5m]) > 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "SSL handshake failures detected"
          description: "Possible SSL configuration issue or attack"
```

### Slack Integration

Add to `app/core/notifications.py`:

```python
import requests
import os

SLACK_WEBHOOK_URL = os.getenv("SLACK_SECURITY_WEBHOOK")

def send_security_alert(
    severity: str,
    title: str,
    details: str,
    metadata: dict = None
):
    """Send security alert to Slack"""

    if not SLACK_WEBHOOK_URL:
        return

    colors = {
        "CRITICAL": "#ff0000",
        "HIGH": "#ff6600",
        "MEDIUM": "#ffcc00",
        "LOW": "#00ccff"
    }

    emoji = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🔵"
    }

    attachment = {
        "color": colors.get(severity, "#cccccc"),
        "title": f"{emoji.get(severity, '⚪')} Security Alert: {title}",
        "text": details,
        "fields": [],
        "footer": "PsychSync Security",
        "ts": int(time.time())
    }

    if metadata:
        for key, value in metadata.items():
            attachment["fields"].append({
                "title": key,
                "value": str(value),
                "short": True
            })

    requests.post(SLACK_WEBHOOK_URL, json={"attachments": [attachment]})
```

Use in middleware:
```python
from app.core.notifications import send_security_alert

# When blocking a request
send_security_alert(
    severity="HIGH",
    title="Invalid Host Header",
    details=f"Blocked request with Host header: {host}",
    metadata={
        "Client IP": client_ip,
        "Path": request.url.path,
        "User Agent": user_agent
    }
)
```

---

## 4. CI/CD Security Pipeline

### Overview
Integrate security checks into your CI/CD pipeline.

### GitLab CI Example

Create `.gitlab-ci.yml`:

```yaml
stages:
  - security-scan
  - test
  - deploy

security_scan:
  stage: security-scan
  script:
    - pip install -r requirements.txt
    - python network_layer_security_audit.py --host $CI_ENVIRONMENT_URL --output security_report.json
  artifacts:
    paths:
      - security_report.json
    expire_in: 1 week
  only:
    - main
    - develop

security_gate:
  stage: security-scan
  script:
    - |
      if grep -q '"severity": "CRITICAL"' security_report.json; then
        echo "Critical vulnerabilities detected!"
        exit 1
      fi
  needs:
    - security_scan
  only:
    - main

deploy_production:
  stage: deploy
  script:
    - ./scripts/deploy-production.sh
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: manual
```

### AWS CodePipeline Example

Create `pipeline/security-check.sh`:

```bash
#!/bin/bash

# Run security audit
python3 network_layer_security_audit.py \
  --host $APPLICATION_URL \
  --output security_audit.json

# Check results
CRITICAL_COUNT=$(jq '[.audits[].findings[] | select(.severity=="CRITICAL")] | length' security_audit.json)

if [ "$CRITICAL_COUNT" -gt 0 ]; then
  echo "Critical vulnerabilities found: $CRITICAL_COUNT"
  exit 1
fi

# Continue with deployment
echo "Security checks passed"
exit 0
```

---

## Testing Your Integration

### Integration Test Script

Create `scripts/test_security_integration.sh`:

```bash
#!/bin/bash

echo "🧪 Testing Security Integration"
echo "================================"

# Test 1: Host header validation
echo "Testing Host header validation..."
curl -H "Host: evil.com" http://localhost:8000/health
if [ $? -eq 400 ]; then
  echo "✅ Host validation working"
else
  echo "❌ Host validation failed"
fi

# Test 2: Valid host accepted
echo "Testing valid host..."
curl -H "Host: localhost:8000" http://localhost:8000/health
if [ $? -eq 200 ]; then
  echo "✅ Valid host accepted"
else
  echo "❌ Valid host rejected"
fi

# Test 3: Security headers
echo "Testing security headers..."
HEADERS=$(curl -I http://localhost:8000/health)
if echo "$HEADERS" | grep -q "X-Frame-Options"; then
  echo "✅ Security headers present"
else
  echo "❌ Security headers missing"
fi

echo "================================"
echo "Integration tests complete"
```

---

## Monitoring Checklist

### Daily (Automated)
- [ ] Security metrics collected
- [ ] Alerts checked
- [ ] Critical violations reviewed

### Weekly
- [ ] Security audit results reviewed
- [ ] New vulnerabilities assessed
- [ ] Security trends analyzed

### Monthly
- [ ] Full security assessment
- [ ] Penetration testing
- [ ] Security documentation updated
- [ ] Team security training

### Quarterly
- [ ] Architecture review
- [ ] Compliance audit
- [ ] Third-party security review
- [ ] Incident response drill

---

## Quick Reference

### Environment Variables
```bash
# Host validation
ALLOWED_HOSTS=api.psychsync.com,psychsync.com

# Security notifications
SLACK_SECURITY_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_DASHBOARD=security-monitoring
```

### Key Files
- `app/middleware/host_validation.py` - Host validation middleware
- `app/core/notifications.py` - Security alert notifications
- `network_layer_security_audit.py` - Security audit tool
- `test_host_header_validation.py` - Host validation tests

### Common Commands
```bash
# Run security audit
python3 network_layer_security_audit.py

# Test host validation
python3 test_host_header_validation.py

# Check application security headers
curl -I http://localhost:8000/health

# View security metrics
curl http://localhost:8000/metrics
```

---

**Last Updated:** 2025-12-23
**Version:** 1.0.0
