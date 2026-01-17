# AI Agents Usage Guide

Complete guide for using the 20 AI automation agents in PsychSync.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Security Agents](#security-agents)
4. [Development Agents](#development-agents)
5. [Operations Agents](#operations-agents)
6. [Integration Examples](#integration-examples)
7. [Best Practices](#best-practices)

---

## Quick Start

### Base URL
All AI agent endpoints are available at:
```
http://localhost:8000/api/v1/ai-agents
```

### Check Agent Status
```bash
curl http://localhost:8000/api/v1/ai-agents/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Expected Response
```json
{
  "total_agents": 20,
  "active_agents": 20,
  "agents": [
    {
      "name": "security_headers_validator",
      "status": "active",
      "description": "Validates security headers on all routes",
      "endpoints": [...]
    },
    ...
  ]
}
```

---

## Authentication

All endpoints require authentication. Include your JWT token in the Authorization header:

```bash
-H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Getting Your Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "yourpassword"}'
```

---

## Security Agents

### 1. Security Headers Validator

#### Validate All Routes
```bash
curl -X POST http://localhost:8000/api/v1/ai-agents/security-headers/validate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force_refresh": false}'
```

**Response:**
```json
{
  "validated_at": "2024-01-17T12:00:00Z",
  "total_routes": 50,
  "routes_with_auth": 35,
  "critical_issues": 2,
  "high_issues": 5,
  "overall_security_score": 0.78,
  "reports": [...]
}
```

#### Get Security Recommendations
```bash
curl http://localhost:8000/api/v1/ai-agents/security-headers/recommendations \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Security Summary
```bash
curl http://localhost:8000/api/v1/ai-agents/security-headers/summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 2. Encryption Strategy Advisor

#### Analyze Database for Encryption Needs
```bash
curl -X POST http://localhost:8000/api/v1/ai-agents/encryption-strategy/analyze \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "analyzed_at": "2024-01-17T12:00:00Z",
  "total_tables": 6,
  "strategies": [
    {
      "table_name": "users",
      "total_fields": 20,
      "sensitive_fields": 8,
      "recommended_encrypted_fields": 6,
      "compliance_score": 0.75,
      "priority": "high",
      "field_recommendations": [...]
    }
  ]
}
```

#### Get Migration Script for a Table
```bash
curl http://localhost:8000/api/v1/ai-agents/encryption-strategy/migration/users \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "table_name": "users",
  "migration_script": "-- Migration script for users...",
  "fields_to_encrypt": 6,
  "estimated_downtime": "3 minutes"
}
```

#### Get Encryption Summary
```bash
curl http://localhost:8000/api/v1/ai-agents/encryption-strategy/summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3. Unsafe Script Detector

#### Scan Frontend for Vulnerabilities
```bash
curl -X POST http://localhost:8000/api/v1/ai-agents/unsafe-scripts/scan \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "scanned_at": "2024-01-17T12:00:00Z",
  "vulnerabilities": [
    {
      "script_source": "https://code.jquery.com/jquery-3.6.0.js",
      "script_type": "cdn",
      "risk_level": "high",
      "issue": "Using potentially unsafe CDN",
      "recommendation": "Host critical libraries locally"
    }
  ],
  "summary": {
    "total_scripts": 15,
    "unsafe_scripts": 5,
    "critical_issues": 1,
    "scripts_with_missing_sri": 3
  }
}
```

#### Get Security Recommendations
```bash
curl http://localhost:8000/api/v1/ai-agents/unsafe-scripts/recommendations \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Development Agents

### 4. Coding Style Enforcer

#### Check File for Style Violations
```bash
curl -X POST "http://localhost:8000/api/v1/ai-agents/coding-style/check?file_path=/app/api/v1/endpoints/users.py" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "file_path": "/app/api/v1/endpoints/users.py",
  "violations": [
    {
      "line": 45,
      "issue": "Line exceeds 100 characters (115 chars)",
      "severity": "low",
      "recommendation": "Break long lines into multiple lines"
    }
  ]
}
```

#### Get Style Report for Directory
```bash
curl "http://localhost:8000/api/v1/ai-agents/coding-style/report?directory=/app/api" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 5. Performance Regression Detector

#### Detect Performance Regression
```bash
curl -X POST http://localhost:8000/api/v1/ai-agents/performance/regression \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": [
      {
        "endpoint": "/api/v1/users",
        "avg_response_time_ms": 450,
        "p95_response_time_ms": 800,
        "error_rate": 0.01
      }
    ]
  }'
```

**Response:**
```json
{
  "regressions": [
    {
      "endpoint": "/api/v1/users",
      "baseline_time_ms": 300,
      "current_time_ms": 450,
      "regression_percent": 50.0,
      "severity": "high",
      "recommendation": "Profile endpoint for bottlenecks"
    }
  ]
}
```

#### Update Performance Baseline
```bash
curl -X POST http://localhost:8000/api/v1/ai-agents/performance/baseline \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"metrics": [...]}'
```

---

### 6. Localization Key Detector

#### Check for Missing i18n Keys
```bash
curl http://localhost:8000/api/v1/ai-agents/localization/check \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total_used": 150,
  "total_defined": 142,
  "missing_keys": ["user.profile.title", "assessment.save"],
  "unused_keys": ["old.feature.key"],
  "coverage_percent": 94.67
}
```

---

### 7. Slow Endpoint Tracker

#### Track Slow Endpoints
```bash
curl -X POST http://localhost:8000/api/v1/ai-agents/performance/slow-endpoints \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": [
      {
        "endpoint": "/api/v1/analytics/aggregate",
        "avg_response_time_ms": 5500,
        "p95_response_time_ms": 8000
      }
    ]
  }'
```

**Response:**
```json
{
  "total_endpoints": 25,
  "slow_endpoints": 3,
  "very_slow_endpoints": 1,
  "recommendations": [
    {
      "endpoint": "/api/v1/analytics/aggregate",
      "response_time_ms": 5500,
      "priority": "critical",
      "recommendations": [
        "Add database indexes",
        "Implement caching",
        "Consider async processing"
      ]
    }
  ]
}
```

---

### 8. Release Notes Generator

#### Generate Release Notes
```bash
curl -X POST "http://localhost:8000/api/v1/ai-agents/release-notes/generate?version=v2.1.0" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "commits": [
      {
        "message": "feat: Add dark mode support",
        "author": "john@example.com",
        "date": "2024-01-17"
      },
      {
        "message": "fix: Resolve login bug",
        "author": "jane@example.com",
        "date": "2024-01-16"
      }
    ]
  }'
```

**Response:**
```json
{
  "version": "v2.1.0",
  "release_date": "2024-01-17T12:00:00Z",
  "summary": "Release v2.1.0 with 2 changes",
  "categories": {
    "features": [...],
    "fixes": [...]
  }
}
```

---

## Operations Agents

### 9. UX Telemetry Tracker

#### Track UX Event
```bash
curl -X POST http://localhost:8000/api/v1/ai-agents/ux/track-event \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "form_submit",
    "page": "/assessment",
    "user_action": "clicked_submit",
    "duration_ms": 5000,
    "error_occurred": false
  }'
```

#### Get Friction Points
```bash
curl "http://localhost:8000/api/v1/ai-agents/ux/friction-points?hours=24" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "analyzed_period_hours": 24,
  "total_events": 1250,
  "friction_points": [
    {
      "page": "/assessment",
      "friction_score": 0.65,
      "error_rate": 15.5,
      "avg_duration_ms": 8500,
      "priority": "high",
      "recommendation": "Review UX for complexity"
    }
  ]
}
```

---

### 10. Environment Config Detector

#### Validate Environment Configuration
```bash
curl -X POST http://localhost:8000/api/v1/ai-agents/environment/validate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "DATABASE_URL": "postgresql://localhost/psychsync",
    "SECRET_KEY": "my-secret-key",
    "DEBUG": "False"
  }'
```

**Response:**
```json
{
  "valid": false,
  "missing_required": ["REDIS_URL"],
  "insecure_configurations": [
    "SECRET_KEY is using default value"
  ],
  "optional_vars_set": []
}
```

---

### 11. Incident Mitigation Planner

#### Create Mitigation Plan
```bash
curl -X POST http://localhost:8000/api/v1/ai-agents/incidents/mitigation-plan \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "INC-2024-001",
    "severity": "critical",
    "description": "Database connection failure",
    "affected_systems": ["api", "database"]
  }'
```

**Response:**
```json
{
  "incident_id": "INC-2024-001",
  "severity": "critical",
  "mitigation_steps": [
    "1. Immediately isolate affected systems",
    "2. Notify on-call engineering team",
    "3. Engage incident commander"
  ],
  "estimated_resolution_time": "1-4 hours"
}
```

---

### 16. Uptime Monitor

#### Check Uptime
```bash
curl -X POST "http://localhost:8000/api/v1/ai-agents/monitoring/check-uptime?endpoint_url=https://api.psychsync.com/health" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "endpoint": "https://api.psychsync.com/health",
  "status": "up",
  "response_time_ms": 45.2,
  "status_code": 200,
  "checked_at": "2024-01-17T12:00:00Z"
}
```

#### Get Daily Uptime Summary
```bash
curl http://localhost:8000/api/v1/ai-agents/monitoring/daily-uptime-summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 17. Stability Score Calculator

#### Calculate Stability Score
```bash
curl -X POST http://localhost:8000/api/v1/ai-agents/monitoring/stability-score \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "uptime_percent": 99.9,
    "error_rate": 0.1,
    "slow_request_rate": 2.5
  }'
```

**Response:**
```json
{
  "overall_score": 95.8,
  "uptime_score": 99.9,
  "error_score": 99.9,
  "performance_score": 97.5,
  "grade": "A",
  "calculated_at": "2024-01-17T12:00:00Z"
}
```

---

## Integration Examples

### Example 1: Pre-Deployment Security Check

```bash
#!/bin/bash
# pre-deploy-check.sh

echo "Running pre-deployment security checks..."

# 1. Validate security headers
echo "Checking security headers..."
curl -X POST http://localhost:8000/api/v1/ai-agents/security-headers/validate \
  -H "Authorization: Bearer $TOKEN" | jq '.overall_security_score'

# 2. Scan for unsafe scripts
echo "Scanning for unsafe scripts..."
curl -X POST http://localhost:8000/api/v1/ai-agents/unsafe-scripts/scan \
  -H "Authorization: Bearer $TOKEN" | jq '.summary.critical_issues'

# 3. Check environment config
echo "Validating environment..."
curl -X POST http://localhost:8000/api/v1/ai-agents/environment/validate \
  -H "Authorization: Bearer $TOKEN" \
  -d @env.json | jq '.valid'

echo "Pre-deployment checks complete!"
```

### Example 2: Weekly Performance Report

```python
# weekly_performance_report.py
import requests
import json
from datetime import datetime

TOKEN = "YOUR_JWT_TOKEN"
BASE_URL = "http://localhost:8000/api/v1/ai-agents"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Check performance regression
response = requests.post(
    f"{BASE_URL}/performance/regression",
    headers=headers,
    json={"metrics": load_metrics()}
)
regressions = response.json()

# Check slow endpoints
response = requests.post(
    f"{BASE_URL}/performance/slow-endpoints",
    headers=headers,
    json={"metrics": load_metrics()}
)
slow_endpoints = response.json()

# Calculate stability score
response = requests.post(
    f"{BASE_URL}/monitoring/stability-score",
    headers=headers,
    json={"metrics": load_system_metrics()}
)
stability = response.json()

# Generate report
report = {
    "date": datetime.now().isoformat(),
    "regressions": regressions,
    "slow_endpoints": slow_endpoints,
    "stability_score": stability
}

print(json.dumps(report, indent=2))
```

### Example 3: CI/CD Integration

```yaml
# .github/workflows/ai-agents-check.yml
name: AI Agents Check

on: [pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Check Security Headers
        run: |
          curl -X POST ${{ secrets.API_URL }}/ai-agents/security-headers/validate \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}"

      - name: Scan Unsafe Scripts
        run: |
          curl -X POST ${{ secrets.API_URL }}/ai-agents/unsafe-scripts/scan \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}"

      - name: Check Coding Style
        run: |
          curl -X POST "${{ secrets.API_URL }}/ai-agents/coding-style/check?file_path=app/main.py" \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}"
```

---

## Best Practices

### 1. Run Security Agents Regularly
```bash
# Add to crontab
0 2 * * * /path/to/security-scan.sh
```

### 2. Monitor Performance Continuously
```bash
# Every 5 minutes
*/5 * * * * /path/to/performance-check.sh
```

### 3. Use UX Telemetry for Insights
- Track user journeys
- Identify friction points
- Measure form completion rates
- Monitor error rates

### 4. Generate Release Notes Automatically
```bash
# Run after every merge to main
git log $(git describe --tags --abbrev=0)..HEAD --pretty=format:"%s" | \
  xargs -I {} curl -X POST "$API/ai-agents/release-notes/generate?version=$VERSION" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"commits": [{"message": "'{}'"}, ...]}'
```

### 5. Check Architecture Drift
```bash
# Weekly architecture review
curl -X POST $API/ai-agents/architecture/check-drift \
  -H "Authorization: Bearer $TOKEN"
```

---

## Troubleshooting

### Agent Returns 401 Unauthorized
- Check your JWT token is valid
- Ensure token hasn't expired
- Verify you have permission to access the endpoint

### Agent Returns 500 Internal Server Error
- Check server logs: `docker-compose logs backend`
- Verify all dependencies are installed
- Check database connection

### Performance Agent Shows No Regression
- Ensure baseline metrics are set
- Check if metrics are in correct format
- Verify time windows match

---

## Additional Resources

- API Documentation: http://localhost:8000/docs
- Agent Status: http://localhost:8000/api/v1/ai-agents/status
- ReDoc: http://localhost:8000/redoc

---

**Need Help?**
- Check the agent status endpoint for current agent availability
- Review server logs for detailed error messages
- Consult the API documentation for request/response formats
