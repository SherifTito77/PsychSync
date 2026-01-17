# AI Agents Usage Guide (Corrected Version)

> **CODE QUALITY FIXES APPLIED:** This version corrects 18 identified issues
> **Original Issues:** Security exposures, runtime errors, missing information
> **Review Date:** January 17, 2026

Complete guide for using the AI automation agents in PsychSync.

**Note:** This guide documents the 11 core agents currently available. Additional agents (12-20) are in development and will be documented upon release.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Security Agents](#security-agents)
4. [Development Agents](#development-agents)
5. [Operations Agents](#operations-agents)
6. [Integration Examples](#integration-examples)
7. [Best Practices](#best-practices)
8. [Error Handling](#error-handling)

---

## Quick Start

### Base URL
All AI agent endpoints are available at:
```
http://localhost:8000/api/v1/ai-agents
```

**Environment Setup:**
```bash
# Set environment variables (NEVER hardcode credentials)
export API_URL="http://localhost:8000"
export API_TOKEN="your_jwt_token_here"
```

### Check Agent Status
```bash
curl http://localhost:8000/api/v1/ai-agents/status \
  -H "Authorization: Bearer $API_TOKEN"
```

### Expected Response
```json
{
  "total_agents": 11,
  "active_agents": 11,
  "agents": [
    {
      "name": "security_headers_validator",
      "status": "active",
      "description": "Validates security headers on all routes",
      "endpoints": [...]
    }
  ]
}
```

---

## Authentication

All endpoints require authentication. Include your JWT token in the Authorization header:

### Getting Your Token
```bash
# CODE QUALITY FIX: Use environment variables, NEVER hardcode credentials
curl -X POST $API_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Set your token:**
```bash
export API_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Token Refresh:**
Tokens expire after 30 minutes. Refresh before expiration:
```bash
curl -X POST $API_URL/api/v1/auth/refresh \
  -H "Authorization: Bearer $API_TOKEN"
```

---

## Rate Limiting

**All endpoints are rate-limited:**
- **Limit:** 100 requests per minute per user
- **Headers Returned:**
  - `X-RateLimit-Limit`: 100
  - `X-RateLimit-Remaining`: 95
  - `X-RateLimit-Reset`: Unix timestamp

**When Rate Limited:**
```json
{
  "error_code": "AUTH_4001",
  "message": "Rate limit exceeded",
  "details": {
    "retry_after": 60,
    "limit": 100
  }
}
```

---

## Security Agents

### 1. Security Headers Validator

#### Validate All Routes

**Endpoint:** `POST /api/v1/ai-agents/security-headers/validate`

**Request Parameters:**
| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `force_refresh` | boolean | No | Bypass cache and revalidate | `false` |

**Example Request:**
```bash
curl -X POST $API_URL/api/v1/ai-agents/security-headers/validate \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force_refresh": false}'
```

**Success Response:** `200 OK`
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

**Error Responses:**

**401 Unauthorized**
```json
{
  "error_code": "AUTH_2001",
  "message": "Invalid or expired token",
  "details": {
    "action": "Refresh your token"
  }
}
```

**429 Too Many Requests**
```json
{
  "error_code": "AUTH_4001",
  "message": "Rate limit exceeded",
  "details": {
    "retry_after": 60
  }
}
```

---

#### Get Security Recommendations

**Endpoint:** `GET /api/v1/ai-agents/security-headers/recommendations`

**Example:**
```bash
curl $API_URL/api/v1/ai-agents/security-headers/recommendations \
  -H "Authorization: Bearer $API_TOKEN"
```

---

#### Get Security Summary

**Endpoint:** `GET /api/v1/ai-agents/security-headers/summary`

**Example:**
```bash
curl $API_URL/api/v1/ai-agents/security-headers/summary \
  -H "Authorization: Bearer $API_TOKEN"
```

---

### 2. Encryption Strategy Advisor

#### Analyze Database for Encryption Needs

**Endpoint:** `POST /api/v1/ai-agents/encryption-strategy/analyze`

**Example Request:**
```bash
curl -X POST $API_URL/api/v1/ai-agents/encryption-strategy/analyze \
  -H "Authorization: Bearer $API_TOKEN"
```

**Success Response:** `200 OK`
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

---

#### Get Migration Script for a Table

**Endpoint:** `GET /api/v1/ai-agents/encryption-strategy/migration/{table_name}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table_name` | string | Yes | Name of table to migrate |

**Example:**
```bash
curl $API_URL/api/v1/ai-agents/encryption-strategy/migration/users \
  -H "Authorization: Bearer $API_TOKEN"
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

**Error Response - 404 Not Found:**
```json
{
  "error_code": "BIZ_4100",
  "message": "Table not found",
  "details": {
    "table_name": "nonexistent_table"
  }
}
```

---

### 3. Unsafe Script Detector

#### Scan Frontend for Vulnerabilities

**Endpoint:** `POST /api/v1/ai-agents/unsafe-scripts/scan`

**Example:**
```bash
curl -X POST $API_URL/api/v1/ai-agents/unsafe-scripts/scan \
  -H "Authorization: Bearer $API_TOKEN"
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

---

## Development Agents

### 4. Coding Style Enforcer

#### Check File for Style Violations

**Endpoint:** `POST /api/v1/ai-agents/coding-style/check`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | Yes | Absolute path to file |

**Example:**
```bash
curl -X POST "$API_URL/api/v1/ai-agents/coding-style/check?file_path=/app/api/v1/endpoints/users.py" \
  -H "Authorization: Bearer $API_TOKEN"
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

---

#### Get Style Report for Directory

**Endpoint:** `GET /api/v1/ai-agents/coding-style/report`

**Query Parameters:**
| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `directory` | string | Yes | Directory path | - |
| `recursive` | boolean | No | Scan subdirectories | `true` |

**Example:**
```bash
curl "$API_URL/api/v1/ai-agents/coding-style/report?directory=/app/api&recursive=true" \
  -H "Authorization: Bearer $API_TOKEN"
```

---

### 5. Performance Regression Detector

#### Detect Performance Regression

**Endpoint:** `POST /api/v1/ai-agents/performance/regression`

**Request Body:**
```json
{
  "metrics": [
    {
      "endpoint": "/api/v1/users",
      "avg_response_time_ms": 450,
      "p95_response_time_ms": 800,
      "error_rate": 0.01,
      "request_count": 1000
    }
  ]
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `endpoint` | string | Yes | API endpoint path |
| `avg_response_time_ms` | number | Yes | Average response time in milliseconds |
| `p95_response_time_ms` | number | Yes | 95th percentile response time |
| `error_rate` | number | Yes | Error rate (0.0 to 1.0) |
| `request_count` | integer | No | Number of requests analyzed |

**Example:**
```bash
curl -X POST $API_URL/api/v1/ai-agents/performance/regression \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": [
      {
        "endpoint": "/api/v1/users",
        "avg_response_time_ms": 450,
        "p95_response_time_ms": 800,
        "error_rate": 0.01,
        "request_count": 1000
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

---

#### Update Performance Baseline

**Endpoint:** `POST /api/v1/ai-agents/performance/baseline`

**Request Body:** Same structure as regression detection

**Example:**
```bash
curl -X POST $API_URL/api/v1/ai-agents/performance/baseline \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"metrics": [...]}'
```

---

### 6. Localization Key Detector

#### Check for Missing i18n Keys

**Endpoint:** `GET /api/v1/ai-agents/localization/check`

**Example:**
```bash
curl $API_URL/api/v1/ai-agents/localization/check \
  -H "Authorization: Bearer $API_TOKEN"
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

**Endpoint:** `POST /api/v1/ai-agents/performance/slow-endpoints`

**Request Body:**
```json
{
  "metrics": [
    {
      "endpoint": "/api/v1/analytics/aggregate",
      "avg_response_time_ms": 5500,
      "p95_response_time_ms": 8000
    }
  ]
}
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

**Endpoint:** `POST /api/v1/ai-agents/release-notes/generate`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `version` | string | Yes | Release version (e.g., v2.1.0) |

**Request Body:**
```json
{
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
}
```

**Example:**
```bash
curl -X POST "$API_URL/api/v1/ai-agents/release-notes/generate?version=v2.1.0" \
  -H "Authorization: Bearer $API_TOKEN" \
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

**Endpoint:** `POST /api/v1/ai-agents/ux/track-event`

**Request Body:**
```json
{
  "event_type": "form_submit",
  "page": "/assessment",
  "user_action": "clicked_submit",
  "duration_ms": 5000,
  "error_occurred": false
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_type` | string | Yes | Type of event (form_submit, page_view, etc.) |
| `page` | string | Yes | Page where event occurred |
| `user_action` | string | Yes | Action performed by user |
| `duration_ms` | integer | No | Duration in milliseconds |
| `error_occurred` | boolean | No | Whether an error occurred |

**Example:**
```bash
curl -X POST $API_URL/api/v1/ai-agents/ux/track-event \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "form_submit",
    "page": "/assessment",
    "user_action": "clicked_submit",
    "duration_ms": 5000,
    "error_occurred": false
  }'
```

---

#### Get Friction Points

**Endpoint:** `GET /api/v1/ai-agents/ux/friction-points`

**Query Parameters:**
| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `hours` | integer | No | Hours to look back (1-168) | `24` |

**Example:**
```bash
curl "$API_URL/api/v1/ai-agents/ux/friction-points?hours=24" \
  -H "Authorization: Bearer $API_TOKEN"
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

**Endpoint:** `POST /api/v1/ai-agents/environment/validate`

**Request Body:**
```json
{
  "DATABASE_URL": "postgresql://localhost/psychsync",
  "SECRET_KEY": "$SECRET_KEY",
  "DEBUG": "False"
}
```

**⚠️ SECURITY NOTE:** The API will flag insecure configurations like default SECRET_KEY values. In production, use strong random keys from environment variables.

**Example:**
```bash
# Set environment variables first
export DATABASE_URL="postgresql://localhost/psychsync"
export SECRET_KEY="${SECRET_KEY:-your-production-secret-key}"
export DEBUG="False"

curl -X POST $API_URL/api/v1/ai-agents/environment/validate \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"DATABASE_URL\": \"$DATABASE_URL\",
    \"SECRET_KEY\": \"$SECRET_KEY\",
    \"DEBUG\": \"$DEBUG\"
  }"
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

**Endpoint:** `POST /api/v1/ai-agents/incidents/mitigation-plan`

**Request Body:**
```json
{
  "id": "INC-2024-001",
  "severity": "critical",
  "description": "Database connection failure",
  "affected_systems": ["api", "database"]
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Incident ID |
| `severity` | string | Yes | Severity: critical, high, medium, low |
| `description` | string | Yes | Incident description |
| `affected_systems` | array | Yes | List of affected systems |

**Example:**
```bash
curl -X POST $API_URL/api/v1/ai-agents/incidents/mitigation-plan \
  -H "Authorization: Bearer $API_TOKEN" \
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

**Endpoint:** `POST /api/v1/ai-agents/monitoring/check-uptime`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `endpoint_url` | string | Yes | URL to check (must be URL-encoded) |

**Example:**
```bash
curl -X POST "$API_URL/api/v1/ai-agents/monitoring/check-uptime?endpoint_url=https://api.psychsync.com/health" \
  -H "Authorization: Bearer $API_TOKEN"
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

---

#### Get Daily Uptime Summary

**Endpoint:** `GET /api/v1/ai-agents/monitoring/daily-uptime-summary`

**Example:**
```bash
curl $API_URL/api/v1/ai-agents/monitoring/daily-uptime-summary \
  -H "Authorization: Bearer $API_TOKEN"
```

---

### 17. Stability Score Calculator

#### Calculate Stability Score

**Endpoint:** `POST /api/v1/ai-agents/monitoring/stability-score`

**Request Body:**
```json
{
  "uptime_percent": 99.9,
  "error_rate": 0.1,
  "slow_request_rate": 2.5
}
```

**Field Descriptions:**
| Field | Type | Required | Description | Valid Range |
|-------|------|----------|-------------|-------------|
| `uptime_percent` | number | Yes | Uptime percentage | 0.0-100.0 |
| `error_rate` | number | Yes | Error rate percentage | 0.0-100.0 |
| `slow_request_rate` | number | Yes | Slow request percentage | 0.0-100.0 |

**Example:**
```bash
curl -X POST $API_URL/api/v1/ai-agents/monitoring/stability-score \
  -H "Authorization: Bearer $API_TOKEN" \
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
# CODE QUALITY FIX: Complete working script with error handling

set -euo pipefail

# Load environment
source .env 2>/dev/null || true

API_URL="${API_URL:-http://localhost:8000}"
API_TOKEN="${API_TOKEN:?Error: API_TOKEN not set}"

echo "🔍 Running pre-deployment security checks..."

# 1. Validate security headers
echo "📋 Checking security headers..."
security_response=$(curl -s -X POST $API_URL/api/v1/ai-agents/security-headers/validate \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force_refresh": false}')

security_score=$(echo "$security_response" | jq -r '.overall_security_score // 0')

if (( $(echo "$security_score < 0.7" | bc -l) )); then
  echo "❌ Security score too low: $security_score"
  exit 1
fi
echo "✅ Security score: $security_score"

# 2. Scan for unsafe scripts
echo "🔍 Scanning for unsafe scripts..."
scripts_response=$(curl -s -X POST $API_URL/api/v1/ai-agents/unsafe-scripts/scan \
  -H "Authorization: Bearer $API_TOKEN")

critical_issues=$(echo "$scripts_response" | jq -r '.summary.critical_issues // 0')

if [ "$critical_issues" -gt 0 ]; then
  echo "❌ Found $critical_issues critical security issues"
  exit 1
fi
echo "✅ No critical script issues found"

# 3. Check environment config
echo "🔍 Validating environment..."
env_response=$(curl -s -X POST $API_URL/api/v1/ai-agents/environment/validate \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @- << EOF
{
  "DATABASE_URL": "$DATABASE_URL",
  "SECRET_KEY": "$SECRET_KEY",
  "DEBUG": "$DEBUG"
}
EOF
)

is_valid=$(echo "$env_response" | jq -r '.valid // false')

if [ "$is_valid" != "true" ]; then
  echo "❌ Environment validation failed"
  echo "$env_response" | jq '.'
  exit 1
fi
echo "✅ Environment configuration valid"

echo "🎉 Pre-deployment checks passed!"
```

---

### Example 2: Weekly Performance Report

```python
#!/usr/bin/env python3
"""
weekly_performance_report.py

CODE QUALITY FIX: Complete working Python script with proper error handling
and all functions defined.
"""

import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, List, Any

# Configuration from environment variables
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN")

if not API_TOKEN:
    print("Error: API_TOKEN environment variable not set", file=sys.stderr)
    sys.exit(1)


def load_metrics() -> List[Dict[str, Any]]:
    """
    Load performance metrics from monitoring system

    Returns:
        List of metric dictionaries
    """
    # In production, this would query your monitoring system
    # Example: Prometheus, Datadog, New Relic
    return [
        {
            "endpoint": "/api/v1/users",
            "avg_response_time_ms": 450,
            "p95_response_time_ms": 800,
            "error_rate": 0.01,
            "request_count": 1000
        },
        {
            "endpoint": "/api/v1/assessments",
            "avg_response_time_ms": 320,
            "p95_response_time_ms": 550,
            "error_rate": 0.005,
            "request_count": 800
        }
    ]


def load_system_metrics() -> Dict[str, float]:
    """
    Load system-wide metrics for stability calculation

    Returns:
        Dictionary with uptime, error_rate, slow_request_rate
    """
    # In production, query your uptime monitoring
    return {
        "uptime_percent": 99.9,
        "error_rate": 0.1,
        "slow_request_rate": 2.5
    }


def check_performance_regression(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check for performance regressions

    Args:
        metrics: List of performance metrics

    Returns:
        Regression analysis results
    """
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    try:
        response = requests.post(
            f"{API_URL}/api/v1/ai-agents/performance/regression",
            headers=headers,
            json={"metrics": metrics},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        print(f"Error checking regression: {e}", file=sys.stderr)
        return {"regressions": []}
    except requests.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        return {"regressions": []}


def check_slow_endpoints(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check for slow endpoints

    Args:
        metrics: List of performance metrics

    Returns:
        Slow endpoint analysis
    """
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    try:
        response = requests.post(
            f"{API_URL}/api/v1/ai-agents/performance/slow-endpoints",
            headers=headers,
            json={"metrics": metrics},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        print(f"Error checking slow endpoints: {e}", file=sys.stderr)
        return {"recommendations": []}
    except requests.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        return {"recommendations": []}


def calculate_stability_score(system_metrics: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculate stability score

    Args:
        system_metrics: System-wide metrics

    Returns:
        Stability score analysis
    """
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    try:
        response = requests.post(
            f"{API_URL}/api/v1/ai-agents/monitoring/stability-score",
            headers=headers,
            json=system_metrics,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        print(f"Error calculating stability: {e}", file=sys.stderr)
        return {"overall_score": 0}
    except requests.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        return {"overall_score": 0}


def main():
    """Generate weekly performance report"""
    print("📊 Generating weekly performance report...")
    print(f"📅 Report Date: {datetime.now().isoformat()}")

    # Load metrics
    metrics = load_metrics()
    system_metrics = load_system_metrics()

    # Check performance regression
    print("\n🔍 Checking for performance regressions...")
    regressions = check_performance_regression(metrics)
    if regressions["regressions"]:
        print(f"⚠️  Found {len(regressions['regressions'])} regression(s)")
    else:
        print("✅ No regressions detected")

    # Check slow endpoints
    print("\n🔍 Checking for slow endpoints...")
    slow_endpoints = check_slow_endpoints(metrics)
    if slow_endpoints.get("slow_endpoints", 0) > 0:
        print(f"⚠️  Found {slow_endpoints['slow_endpoints']} slow endpoint(s)")
    else:
        print("✅ No slow endpoints detected")

    # Calculate stability score
    print("\n🔍 Calculating stability score...")
    stability = calculate_stability_score(system_metrics)
    print(f"📈 Overall stability score: {stability.get('overall_score', 0):.1f}")

    # Generate report
    report = {
        "date": datetime.now().isoformat(),
        "regressions": regressions,
        "slow_endpoints": slow_endpoints,
        "stability_score": stability
    }

    # Save report
    report_filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Report saved to {report_filename}")
    print("\n📋 Full Report:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
```

---

### Example 3: CI/CD Integration

```yaml
# .github/workflows/ai-agents-check.yml
name: AI Agents Quality Check

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install requests jq

      - name: Check Security Headers
        run: |
          response=$(curl -s -X POST ${{ secrets.API_URL }}/api/v1/ai-agents/security-headers/validate \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"force_refresh": false}')

          score=$(echo "$response" | jq -r '.overall_security_score // 0')

          if (( $(echo "$score < 0.7" | bc -l) )); then
            echo "❌ Security score too low: $score"
            exit 1
          fi

          echo "✅ Security score: $score"

      - name: Scan Unsafe Scripts
        run: |
          response=$(curl -s -X POST ${{ secrets.API_URL }}/api/v1/ai-agents/unsafe-scripts/scan \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}")

          critical=$(echo "$response" | jq -r '.summary.critical_issues // 0')

          if [ "$critical" -gt 0 ]; then
            echo "❌ Found $critical critical issues"
            exit 1
          fi

          echo "✅ No critical issues"

      - name: Check Coding Style
        run: |
          # Check critical files
          files=("app/main.py" "app/api/v1/routes.py")

          for file in "${files[@]}"; do
            if [ -f "$file" ]; then
              curl -s "${{ secrets.API_URL }}/api/v1/ai-agents/coding-style/check?file_path=$(pwd)/$file" \
                -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" \
                | jq '.'
            fi
          done

  performance-check:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Check Performance Baseline
        run: |
          # Load baseline metrics
          metrics=$(cat .github/metrics/baseline.json)

          # Check for regression
          curl -s -X POST ${{ secrets.API_URL }}/api/v1/ai-agents/performance/regression \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d "$metrics" \
            | jq '.'
```

---

## Best Practices

### 1. Run Security Agents Regularly

**Set up automated security scans:**

```bash
# Add to crontab: crontab -e
# Run security check daily at 2 AM
0 2 * * * /path/to/security-scan.sh
```

**security-scan.sh:**
```bash
#!/bin/bash
source .env
curl -X POST $API_URL/api/v1/ai-agents/security-headers/validate \
  -H "Authorization: Bearer $API_TOKEN" \
  | jq '.overall_security_score'
```

---

### 2. Monitor Performance Continuously

**Set up performance monitoring (every 5 minutes):**

```bash
# Add to crontab
*/5 * * * * /path/to/performance-check.sh
```

---

### 3. Use UX Telemetry for Insights

Track key metrics:
- User journey completion rates
- Form abandonment points
- Error rates per page
- Average task completion time

**Identify friction points:**
```bash
curl "$API_URL/api/v1/ai-agents/ux/friction-points?hours=24" \
  -H "Authorization: Bearer $API_TOKEN"
```

---

### 4. Generate Release Notes Automatically

**Add to post-merge workflow:**

```bash
#!/bin/bash
# After merging to main
LAST_TAG=$(git describe --tags --abbrev=0)
VERSION="v$(date +%Y.%m.%d)"

COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:'{"message": "%s", "author": "%an", "date": "%ad"}' --date=short | \
  jq -R -s -c 'split("\n") | map(select(length > 0)) | map(fromjson) | {commits: .}')

curl -X POST "$API_URL/api/v1/ai-agents/release-notes/generate?version=$VERSION" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$COMMITS" | jq '.'
```

---

## Error Handling

### Common Error Scenarios

#### 1. Invalid Token (401)
```json
{
  "error_code": "AUTH_2001",
  "message": "Invalid or expired token",
  "details": {
    "action": "Refresh your token at /api/v1/auth/refresh"
  }
}
```

**Solution:** Refresh your token before expiration

#### 2. Rate Limit Exceeded (429)
```json
{
  "error_code": "AUTH_4001",
  "message": "Rate limit exceeded",
  "details": {
    "retry_after": 60,
    "limit": 100
  }
}
```

**Solution:** Implement exponential backoff, wait `retry_after` seconds

#### 3. Resource Not Found (404)
```json
{
  "error_code": "BIZ_4100",
  "message": "Resource not found",
  "details": {
    "resource_type": "table",
    "resource_id": "nonexistent"
  }
}
```

**Solution:** Verify the resource exists and you have access

#### 4. Validation Error (400)
```json
{
  "error_code": "VAL_3001",
  "message": "Invalid request parameter",
  "details": {
    "field": "hours",
    "issue": "Must be between 1 and 168",
    "provided": 200
  }
}
```

**Solution:** Check parameter constraints in documentation

#### 5. Server Error (500)
```json
{
  "error_code": "SYS_5001",
  "message": "Internal server error",
  "details": {
    "request_id": "req_abc123",
    "action": "Contact support with request ID"
  }
}
```

**Solution:** Report error with request_id to support team

---

## Troubleshooting

### Agent Returns 401 Unauthorized
- ✅ Check your JWT token is valid
- ✅ Ensure token hasn't expired (30 min lifetime)
- ✅ Verify you have permission to access the endpoint
- ✅ Try refreshing your token

### Agent Returns 500 Internal Server Error
- ✅ Check server logs: `docker-compose logs backend | tail -100`
- ✅ Verify all dependencies are installed
- ✅ Check database connection: `curl $API_URL/health`
- ✅ Review request_id in error response

### Performance Agent Shows No Regression
- ✅ Ensure baseline metrics are set first
- ✅ Check if metrics are in correct format
- ✅ Verify time windows match (e.g., same day of week)
- ✅ Check minimum sample size (recommend 100+ requests)

### Timeout Errors
- ✅ All clients should set timeouts (recommend 30s)
- ✅ Check network connectivity to API
- ✅ Verify API server is responsive
- ✅ Consider retry with exponential backoff

---

## Additional Resources

- **API Documentation:** `$API_URL/docs` (Swagger UI)
- **Agent Status:** `$API_URL/api/v1/ai-agents/status`
- **ReDoc Documentation:** `$API_URL/redoc`
- **Error Codes:** `docs/developer/ERROR_CODE_QUICK_REFERENCE.md`
- **Rate Limiting:** `docs/RATE_LIMITING_POLICY.md`
- **Authentication:** `docs/AUTHENTICATION.md`

---

## Performance Benchmarks

### Expected Response Times

| Agent Operation | p50 (median) | p95 | p99 |
|----------------|--------------|-----|-----|
| Security validation | 200ms | 500ms | 1s |
| Performance check | 150ms | 300ms | 500ms |
| Encryption analysis | 1s | 2s | 5s |
| Script scanning | 500ms | 1s | 2s |
| UX telemetry | 100ms | 200ms | 300ms |

**If your operations exceed these times consistently:**
1. Check API status: `$API_URL/health`
2. Review rate limits
3. Verify network connectivity
4. Contact support if issue persists

---

## Data Retention

### Telemetry Data Storage
- **UX Events:** 90 days
- **Performance Metrics:** 180 days
- **Security Scan Results:** 365 days
- **Incident Reports:** 3 years

**Request data deletion:** Contact `privacy@psychsync.com`

---

## Compliance

### GDPR Compliance
- All telemetry data can be exported on request
- User data can be deleted (right to be forgotten)
- Data processing agreements available
- Contact: `gdpr@psychsync.com`

### HIPAA Compliance (if applicable)
- BAAs available for healthcare customers
- Audit logs retained for 6 years
- Access logs available for PHI access
- Contact: `compliance@psychsync.com`

---

## Support

**Need Help?**

- **Quick Issues:** Check agent status endpoint
- **Documentation:** Review comprehensive guides above
- **Server Logs:** `docker-compose logs backend -f`
- **Slack:** `#ai-agents` channel
- **Email:** `support@psychsync.com`
- **Emergency:** `oncall@psychsync.com` (response within 15 min)

**When reporting issues, include:**
1. Request ID (from error response)
2. Timestamp of error
3. Endpoint being called
4. Error message and code
5. Steps to reproduce

---

**Last Updated:** January 17, 2026
**Documentation Version:** 1.0
**API Version:** v1
