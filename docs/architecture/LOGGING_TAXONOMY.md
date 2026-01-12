# Logging Taxonomy & Naming Conventions

**Version:** 1.0
**Date:** 2026-01-10
**Status:** Proposed Standards

---

## Executive Summary

This document establishes comprehensive logging standards for PsychSync to ensure observability, debugging efficiency, security compliance, and operational excellence across the entire platform.

---

## Table of Contents

1. [Logging Philosophy](#1-logging-philosophy)
2. [Log Level Taxonomy](#2-log-level-taxonomy)
3. [Structured Logging Format](#3-structured-logging-format)
4. [Naming Conventions](#4-naming-conventions)
5. [Domain-Specific Guidelines](#5-domain-specific-guidelines)
6. [Security & Compliance Logging](#6-security--compliance-logging)
7. [Performance Logging](#7-performance-logging)
8. [Implementation Examples](#8-implementation-examples)
9. [Log Aggregation Strategy](#9-log-aggregation-strategy)
10. [Alerting & Monitoring](#10-alerting--monitoring)

---

## 1. Logging Philosophy

### Core Principles

```
┌────────────────────────────────────────────────────────────┐
│                    LOGGING PRINCIPLES                      │
├────────────────────────────────────────────────────────────┤
│ 1. Action-Oriented: Logs describe what happened            │
│ 2. Searchable: Structured data enables querying            │
│ 3. Secure: Never log sensitive data (PII, passwords)       │
│ 4. Context-Rich: Include request_id, user_id, tenant_id    │
│ 5. Performance-Conscious: Async logging, sampling          │
└────────────────────────────────────────────────────────────┘
```

### When to Log

| Scenario | Log Level | Example |
|----------|-----------|---------|
| Normal business operations | INFO | User login, assessment created |
| Potential issues | WARNING | High API latency, retry attempt |
| Application errors | ERROR | Database connection failed |
| Critical failures | CRITICAL | Server cannot start |
| Debugging diagnostics | DEBUG | SQL query details (dev only) |

---

## 2. Log Level Taxonomy

### Level Definitions

```python
# Level Hierarchy (from lowest to highest severity)
DEBUG    = 10    # Detailed diagnostic information
INFO     = 20    # Confirmation that things are working as expected
WARNING  = 30    # An indication that something unexpected happened
ERROR    = 40    # Due to a more serious problem, software has not been able to perform
CRITICAL = 50    # A serious error, indicating that the program itself may be unable to run
```

### Usage Guidelines

#### **DEBUG (10)**
**Purpose:** Detailed information for diagnosing problems

**When to Use:**
- Development and troubleshooting only
- SQL queries with execution plans
- Function entry/exit with parameters
- Detailed variable states

**Examples:**
```python
logger.debug(
    "database_query_executed",
    extra={
        "query": "SELECT * FROM users WHERE email = :email",
        "params": {"email": "user@example.com"},
        "execution_time_ms": 15.3
    }
)
```

**Production Behavior:** Disabled (log level >= INFO)

---

#### **INFO (20)**
**Purpose:** Confirmation that things are working as expected

**When to Use:**
- User actions (login, logout, assessment created)
- System lifecycle events (startup, shutdown)
- Business milestones (team created, report generated)
- API requests (successful)

**Examples:**
```python
logger.info(
    "user_authenticated",
    extra={
        "user_id": str(user.id),
        "auth_method": "jwt",
        "ip_address": client_ip,
        "user_agent": request.headers.get("user-agent")
    }
)

logger.info(
    "assessment_created",
    extra={
        "assessment_id": str(assessment.id),
        "organization_id": str(organization.id),
        "template_type": "big_five",
        "created_by": str(user.id)
    }
)
```

---

#### **WARNING (30)**
**Purpose:** Something unexpected happened, but software still works

**When to Use:**
- Deprecated API usage
- Retry attempts (transient failures)
- High resource usage approaching limits
- Missing non-critical data

**Examples:**
```python
logger.warning(
    "high_response_time",
    extra={
        "endpoint": "/api/v1/assessments",
        "duration_ms": 2850,
        "threshold_ms": 2000,
        "request_id": request.state.request_id
    }
)

logger.warning(
    "retry_attempt",
    extra={
        "operation": "send_email",
        "attempt": 2,
        "max_attempts": 3,
        "error": "SMTP timeout"
    }
)
```

---

#### **ERROR (40)**
**Purpose:** Serious problem, software couldn't perform some function

**When to Use:**
- Unhandled exceptions
- Database operation failures
- External API call failures
- Validation failures that block operations

**Examples:**
```python
logger.error(
    "database_operation_failed",
    extra={
        "operation": "create_assessment",
        "error_type": "IntegrityError",
        "error_message": "Duplicate key violation",
        "request_id": request.state.request_id,
        "user_id": str(user.id)
    },
    exc_info=True
)
```

---

#### **CRITICAL (50)**
**Purpose:** Serious error, program may not be able to continue

**When to Use:**
- System cannot start (missing config, cannot connect to DB)
- Out of memory or disk space
- Security breach detected
- All database connections exhausted

**Examples:**
```python
logger.critical(
    "database_connection_exhausted",
    extra={
        "pool_size": 20,
        "active_connections": 20,
        "overflow": 0,
        "checked_out_connections": 20
    }
)

logger.critical(
    "security_breach_detected",
    extra={
        "alert_type": "sql_injection_attempt",
        "ip_address": client_ip,
        "user_input": malicious_input[:100],  # Sanitized
        "request_id": request.state.request_id
    }
)
```

---

## 3. Structured Logging Format

### Standard Log Structure

```json
{
  "timestamp": "2026-01-10T14:30:45.123Z",
  "level": "INFO",
  "logger_name": "app.api.v1.endpoints.assessments",
  "message": "assessment_created",
  "extra": {
    "event_type": "assessment.created",
    "event_id": "evt_01h5x9z2y8x7w6v5u4t3s2r1q",
    "request_id": "req_01h5x9z2y8x7w6v5u4t3s2r1q",
    "tenant_id": "org_01h5x9z2y8x7w6v5u4t3s2r1q",
    "user_id": "usr_01h5x9z2y8x7w6v5u4t3s2r1q",
    "assessment_id": "asm_01h5x9z2y8x7w6v5u4t3s2r1q",
    "organization_id": "org_01h5x9z2y8x7w6v5u4t3s2r1q",
    "template_type": "big_five",
    "created_at": "2026-01-10T14:30:45.120Z"
  }
}
```

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `timestamp` | ISO 8601 | Event timestamp (UTC) | `2026-01-10T14:30:45.123Z` |
| `level` | String | Log level (uppercase) | `INFO`, `ERROR`, `WARNING` |
| `logger_name` | String | Python logger module path | `app.services.assessment` |
| `message` | String | Human-readable event name | `assessment_created` |
| `event_type` | String | Dotted event taxonomy | `assessment.created` |

### Context Fields (Recommended)

| Field | Type | Description | When to Include |
|-------|------|-------------|-----------------|
| `request_id` | UUID | Correlate all logs for a request | Always (middleware injects) |
| `user_id` | UUID | User performing action | When authenticated |
| `tenant_id` | UUID | Organization/tenant context | When in tenant context |
| `trace_id` | UUID | Distributed trace across services | For microservices |
| `span_id` | UUID | Individual operation in trace | For distributed tracing |

### Error Fields (On Exception)

| Field | Type | Description |
|-------|------|-------------|
| `error_type` | String | Exception class name |
| `error_message` | String | Exception message (sanitized) |
| `error_stack_trace` | String | Full stack trace (DEBUG only) |
| `error_code` | String | Application error code |

---

## 4. Naming Conventions

### Logger Naming

**Pattern:** `app.<layer>.<module>.<submodule>`

```python
# API Endpoints
logger = logging.getLogger("app.api.v1.endpoints.auth")

# Business Logic
logger = logging.getLogger("app.services.assessment")

# Database Operations
logger = logging.getLogger("app.crud.user")

# AI Processing
logger = logging.getLogger("app.ai.processors.big_five")
```

**Rules:**
- All lowercase
- Use dots (.) to separate namespaces
- Match Python module structure
- No special characters or spaces

---

### Event Naming

**Pattern:** `<entity>.<action>`

```python
# User Events
"user.created"
"user.updated"
"user.deleted"
"user.authenticated"
"user.logged_out"

# Assessment Events
"assessment.created"
"assessment.started"
"assessment.completed"
"assessment.shared"

# Team Events
"team.created"
"team.member_added"
"team.member_removed"
"team.analytics_generated"

# System Events
"system.started"
"system.shutdown"
"system.error"
"system.config_reloaded"
```

**Rules:**
- Use past tense for completed actions
- Use present tense for ongoing states
- Entity is always singular (assessment, not assessments)
- Action is descriptive verb (created, not create)

**Common Actions:**

| Action | Meaning | Example |
|--------|---------|---------|
| `created` | New resource created | `assessment.created` |
| `updated` | Resource modified | `user.updated` |
| `deleted` | Resource removed | `team.deleted` |
| `started` | Process/workflow began | `assessment.started` |
| `completed` | Process/workflow finished | `assessment.completed` |
| `failed` | Process/workflow errored | `email_sending.failed` |
| `validated` | Validation check passed | `input.validated` |
| `authorized` | Permission granted | `access.authorized` |
| `denied` | Permission rejected | `access.denied` |

---

### Metric Naming

**Pattern:** `<domain>.<entity>.<metric>_<unit>`

```python
# Response Time Metrics
api.assessments.create_response_time_ms
api.auth.login_response_time_ms

# Business Metrics
business.assessments.created_count
business.users.registered_count

# System Metrics
system.database.connection_pool_utilization_percent
system.redis.memory_usage_bytes
```

**Rules:**
- Always include units (ms, count, bytes, percent)
- Use snake_case for multi-word metrics
- Domain prefixes: `api.`, `business.`, `system.`, `db.`

**Standard Units:**

| Metric Type | Unit | Suffix |
|-------------|------|--------|
| Time/Durations | Milliseconds | `_ms` |
| Bytes/Memory | Bytes | `_bytes` |
| Counters | Integer | `_count` |
| Percentages | Percentage (0-100) | `_percent` |
| Ratios | Float | `_ratio` |

---

### Error Code Naming

**Pattern:** `<SERVICE>_<ERROR_TYPE>_<SPECIFIC>`

```python
# Authentication Errors
AUTH_TOKEN_MISSING = "AUTH_TOKEN_001"
AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_002"
AUTH_TOKEN_INVALID = "AUTH_TOKEN_003"

# Assessment Errors
ASSESSMENT_NOT_FOUND = "ASSESSMENT_NOT_FOUND_001"
ASSESSMENT_ALREADY_STARTED = "ASSESSMENT_ALREADY_STARTED_001"

# Database Errors
DB_CONNECTION_FAILED = "DB_CONNECTION_001"
DB_QUERY_TIMEOUT = "DB_QUERY_001"
```

**Benefits:**
- Human-readable
- Searchable in logs
- Can map to HTTP status codes
- Internationalizable

---

## 5. Domain-Specific Guidelines

### Authentication & Authorization

```python
logger.info(
    "user_logged_in",
    extra={
        "user_id": str(user.id),
        "auth_method": "password",  # password, sso, oauth
        "mfa_enabled": user.mfa_enabled,
        "ip_address": client_ip,
        "user_agent": request.headers.get("user-agent"),
        "success": True
    }
)

logger.warning(
    "authentication_failed",
    extra={
        "email": email,  # Never log passwords!
        "reason": "invalid_credentials",
        "ip_address": client_ip,
        "attempt_count": attempt_count
    }
)

logger.error(
    "authorization_denied",
    extra={
        "user_id": str(user.id),
        "resource": "assessment",
        "resource_id": str(assessment_id),
        "action": "delete",
        "required_role": "admin",
        "user_role": user.role
    }
)
```

**Security Rules:**
- ❌ NEVER log passwords, tokens, or API keys
- ❌ NEVER log full request bodies for auth endpoints
- ✅ Always log authentication failures (potential attacks)
- ✅ Always log authorization denials (access control issues)

---

### Database Operations

```python
logger.debug(
    "database_query_executed",
    extra={
        "query": query,  # Only in DEBUG mode
        "params": sanitized_params,
        "execution_time_ms": duration,
        "rows_affected": result.rowcount
    }
)

logger.error(
    "database_operation_failed",
    extra={
        "operation": "insert",
        "table": "assessments",
        "error_type": "IntegrityError",
        "constraint": "assessments_pkey",
        "user_id": str(user.id),
        "request_id": request.state.request_id
    },
    exc_info=True
)
```

**Performance Logging:**
```python
# Log slow queries (>1 second)
if execution_time_ms > 1000:
    logger.warning(
        "slow_database_query",
        extra={
            "query": query[:500],  # Truncate long queries
            "execution_time_ms": execution_time_ms,
            "threshold_ms": 1000
        }
    )
```

---

### External API Calls

```python
logger.info(
    "external_api_call",
    extra={
        "service": "openai",
        "endpoint": "/chat/completions",
        "method": "POST",
        "request_id": request.state.request_id
    }
)

logger.info(
    "external_api_response",
    extra={
        "service": "openai",
        "status_code": response.status_code,
        "duration_ms": duration,
        "request_id": request.state.request_id
    }
)
```

**Never Log:**
- ❌ API keys or secrets
- ❌ Full request/response bodies (may contain PII)
- ❌ Authorization headers

**Always Log:**
- ✅ Service name
- ✅ Status code
- ✅ Duration
- ✅ Success/failure

---

### File Operations

```python
logger.info(
    "file_uploaded",
    extra={
        "user_id": str(user.id),
        "file_name": file.filename,  # Sanitized
        "file_size_bytes": file.size,
        "file_type": file.content_type,
        "storage_path": sanitized_path,
        "request_id": request.state.request_id
    }
)
```

---

## 6. Security & Compliance Logging

### GDPR/Privacy Logging

```python
logger.info(
    "user_data_exported",
    extra={
        "user_id": str(user.id),
        "export_type": "gdpr_request",
        "data_categories": ["profile", "assessments", "responses"],
        "file_size_bytes": export_size,
        "retention_days": 30,
        "request_id": request.state.request_id
    }
)

logger.info(
    "user_data_deleted",
    extra={
        "user_id": str(user.id),  # Before deletion
        "deletion_type": "right_to_be_forgotten",
        "tables_affected": ["users", "responses", "team_members"],
        "anonymized": True,
        "request_id": request.state.request_id
    }
)
```

### Security Events

```python
# Rate Limiting
logger.warning(
    "rate_limit_exceeded",
    extra={
        "ip_address": client_ip,
        "endpoint": "/api/v1/assessments",
        "limit": 100,
        "window_seconds": 60,
        "actual_requests": 150
    }
)

# SQL Injection Attempt
logger.critical(
    "security_threat_detected",
    extra={
        "threat_type": "sql_injection",
        "ip_address": client_ip,
        "user_input": sanitize_input(user_input)[:200],
        "pattern_matched": "union select",
        "request_id": request.state.request_id,
        "blocked": True
    }
)

# Brute Force Attack
logger.warning(
    "brute_force_detected",
    extra={
        "target_email": email,
        "ip_address": client_ip,
        "failed_attempts": 10,
        "time_window_minutes": 5,
        "action_taken": "ip_blocked"
    }
)
```

### Audit Logging

```python
logger.info(
    "audit_log",
    extra={
        "event_type": "assessment.modified",
        "actor_user_id": str(actor.id),
        "actor_role": actor.role,
        "target_resource": "assessment",
        "target_resource_id": str(assessment.id),
        "changes": {
            "fields": ["title", "description"],
            "old_values": {"title": "Old Title"},
            "new_values": {"title": "New Title"}
        },
        "tenant_id": str(organization.id),
        "ip_address": client_ip,
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

---

## 7. Performance Logging

### API Endpoint Performance

```python
# In middleware
@contextmanager
def log_request_duration(request: Request):
    start_time = time.time()
    request_id = request.state.request_id

    logger.info(
        "request_started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host
        }
    )

    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        status_code = getattr(request.state, "status_code", 200)

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2)
            }
        )

        # Alert on slow requests
        if duration_ms > 2000:
            logger.warning(
                "slow_request",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "threshold_ms": 2000
                }
            )
```

### Database Performance

```python
# Connection pool monitoring
logger.info(
    "database_pool_stats",
    extra={
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_in": pool.checkedin()
    }
)

# Query performance
if query_time_ms > 1000:
    logger.warning(
        "slow_query_detected",
        extra={
            "query": query[:500],
            "execution_time_ms": query_time_ms,
            "query_plan": explain_plan  # Only for slow queries
        }
    )
```

### Memory & Resources

```python
import psutil

process = psutil.Process()

logger.info(
    "system_resource_usage",
    extra={
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "cpu_percent": process.cpu_percent(),
        "open_files": len(process.open_files()),
        "threads": process.num_threads()
    }
)
```

---

## 8. Implementation Examples

### Python Logger Setup

```python
# app/core/logging.py
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Structured JSON logging formatter"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger_name": record.name,
            "message": record.message,
            "extra": getattr(record, "extra", {})
        }

        # Add exception info if present
        if record.exc_info:
            log_data["extra"]["error_type"] = record.exc_info[0].__name__
            log_data["extra"]["error_message"] = str(record.exc_info[1])
            if record.levelno >= logging.DEBUG:
                log_data["extra"]["error_stack_trace"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def setup_logging() -> None:
    """Configure application logging"""

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Add request context to logs
class RequestLoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Generate request ID
            request_id = generate_request_id()

            # Add to logging context
            import contextvars
            request_id_var = contextvars.ContextVar("request_id")
            request_id_var.set(request_id)

            # Log request
            logger = logging.getLogger("app.api")
            logger.info(
                "http_request_started",
                extra={
                    "request_id": request_id,
                    "method": scope["method"],
                    "path": scope["path"]
                }
            )

        await self.app(scope, receive, send)
```

### Usage in Services

```python
# app/services/assessment.py
import logging
from typing import Optional

logger = logging.getLogger("app.services.assessment")

class AssessmentService:
    async def create_assessment(
        self,
        title: str,
        organization_id: UUID,
        user_id: UUID
    ) -> Assessment:
        try:
            logger.info(
                "assessment_creation_started",
                extra={
                    "organization_id": str(organization_id),
                    "user_id": str(user_id),
                    "title": title
                }
            )

            assessment = await self.crud.create(
                title=title,
                organization_id=organization_id,
                created_by=user_id
            )

            logger.info(
                "assessment_created",
                extra={
                    "assessment_id": str(assessment.id),
                    "organization_id": str(organization_id),
                    "user_id": str(user_id)
                }
            )

            return assessment

        except Exception as e:
            logger.error(
                "assessment_creation_failed",
                extra={
                    "organization_id": str(organization_id),
                    "user_id": str(user_id),
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise
```

### Request Context Logger

```python
# app/utils/logger.py
import logging
from contextvars import ContextVar
from typing import Dict, Any

_request_context: ContextVar[Dict[str, Any]] = ContextVar("request_context")

class RequestLogger:
    """Logger with automatic request context injection"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _get_context(self) -> Dict[str, Any]:
        """Get current request context"""
        return _request_context.get({})

    def info(self, message: str, **extra):
        """Log info with request context"""
        context = self._get_context()
        self.logger.info(
            message,
            extra={**context, **extra}
        )

    def error(self, message: str, exc_info=False, **extra):
        """Log error with request context"""
        context = self._get_context()
        self.logger.error(
            message,
            extra={**context, **extra},
            exc_info=exc_info
        )

    def warning(self, message: str, **extra):
        """Log warning with request context"""
        context = self._get_context()
        self.logger.warning(
            message,
            extra={**context, **extra}
        )

# Usage
logger = RequestLogger("app.services.assessment")
logger.info(
    "assessment_created",
    assessment_id=str(assessment.id),
    user_id=str(user.id)
    # request_id, tenant_id automatically added from context
)
```

---

## 9. Log Aggregation Strategy

### Log Storage & Retention

| Environment | Storage | Retention | Indexing |
|-------------|---------|-----------|----------|
| Development | Local files | 7 days | None |
| Staging | Cloud storage (S3) | 30 days | Basic |
| Production | ELK Stack / CloudWatch | 1 year (hot), 7 years (cold) | Full |

### Log Destinations

```python
# Development: Local file
LOG_FILE = "logs/psychsync.log"

# Staging: S3 + CloudWatch
LOG_DESTINATIONS = [
    "s3://psychsync-logs/staging/",
    "cloudwatch:/aws/psychsync/staging"
]

# Production: Multiple destinations
LOG_DESTINATIONS = [
    "elasticsearch:log-cluster.psychsync.com",
    "s3://psychsync-logs/production/",
    "cloudwatch:/aws/psychsync/production",
    "slack:#alerts-production"  # CRITICAL only
]
```

### Sampling Strategy (High-Volume Logs)

```python
# Sample high-volume debug logs (10% sample rate)
if random.random() < 0.1:
    logger.debug("high_volume_event", extra={...})

# Always log errors and warnings
if level >= WARNING:
    logger.log(level, message, extra={...})
```

### Log Partitioning

```
psychsync_logs/
├── year=2026/
│   ├── month=01/
│   │   ├── day=10/
│   │   │   ├── level=INFO/
│   │   │   │   ├── app_api_v1_endpoints_auth.log
│   │   │   │   └── app_services_assessment.log
│   │   │   ├── level=ERROR/
│   │   │   └── level=CRITICAL/
```

---

## 10. Alerting & Monitoring

### Alert Rules

```python
# Critical Alerts (Page on-call engineer)
ALERTS_CRITICAL = [
    {
        "name": "Database Connection Exhausted",
        "condition": "database_connection_exhausted",
        "threshold": 1,  # Any occurrence
        "window": "1m",
        "actions": ["pagerduty", "slack"]
    },
    {
        "name": "Security Threat Detected",
        "condition": "security_threat_detected",
        "threshold": 1,
        "window": "1m",
        "actions": ["pagerduty", "slack", "email"]
    },
    {
        "name": "High Error Rate",
        "condition": "error_rate_percent > 5",
        "threshold": 5,
        "window": "5m",
        "actions": ["pagerduty", "slack"]
    }
]

# Warning Alerts (Slack notification)
ALERTS_WARNING = [
    {
        "name": "High Response Time",
        "condition": "response_time_p95_ms > 2000",
        "threshold": 2000,
        "window": "10m",
        "actions": ["slack"]
    },
    {
        "name": "Rate Limit Exceeded",
        "condition": "rate_limit_exceeded",
        "threshold": 10,  # 10 occurrences
        "window": "5m",
        "actions": ["slack"]
    }
]
```

### Dashboard Metrics

```python
DASHBOARD_METRICS = {
    "api_performance": [
        "api_response_time_p50_ms",
        "api_response_time_p95_ms",
        "api_error_rate_percent",
        "api_requests_per_second"
    ],
    "business_metrics": [
        "assessments_created_count",
        "users_registered_count",
        "teams_created_count"
    ],
    "infrastructure": [
        "database_connection_pool_utilization_percent",
        "redis_memory_usage_bytes",
        "disk_usage_percent"
    ],
    "security": [
        "authentication_failures_count",
        "authorization_denials_count",
        "rate_limit_violations_count"
    ]
}
```

### Log Query Examples

```python
# Find all errors for a user
level:ERROR AND user_id:usr_01h5x9z2y8x7w6v5u4t3s2r1q

# Find slow requests
duration_ms:>2000 AND level:WARNING

# Find authentication failures
authentication_failed AND ip_address:"192.168.1.1"

# Find database errors
error_type:*IntegrityError*

# Cross-tenant analysis (admin only)
level:ERROR | stats count by tenant_id
```

---

## Appendix: Quick Reference

### Log Level Decision Tree

```
Is this a critical system failure?
├─ Yes → CRITICAL
└─ No
    └─ Is this an error that prevented an operation?
        ├─ Yes → ERROR
        └─ No
            └─ Is this unexpected but recoverable?
                ├─ Yes → WARNING
                └─ No
                    └─ Is this a normal operation?
                        ├─ Yes → INFO
                        └─ No → DEBUG
```

### Common Event Types

| Category | Events |
|----------|--------|
| **User** | `user.created`, `user.updated`, `user.deleted`, `user.authenticated` |
| **Assessment** | `assessment.created`, `assessment.started`, `assessment.completed` |
| **Team** | `team.created`, `team.member_added`, `team.member_removed` |
| **Auth** | `auth.login`, `auth.logout`, `auth.failed`, `auth.denied` |
| **API** | `api.request`, `api.response`, `api.error`, `api.slow_request` |
| **Database** | `db.query`, `db.slow_query`, `db.connection_failed` |
| **System** | `system.started`, `system.error`, `system.shutdown` |

### Naming Conventions Summary

| Type | Pattern | Example |
|------|---------|---------|
| Logger | `app.<layer>.<module>` | `app.services.assessment` |
| Event | `<entity>.<action>` | `assessment.created` |
| Metric | `<domain>.<entity>.<metric>_<unit>` | `api.assessment.create_response_time_ms` |
| Error Code | `<SERVICE>_<ERROR>_<NUMBER>` | `AUTH_TOKEN_001` |

---

## Success Metrics

- ✅ All logs include `request_id` for request tracing
- ✅ Zero occurrences of sensitive data (passwords, tokens) in logs
- ✅ <5% overhead from logging (performance impact)
- ✅ All errors have associated log entries
- ✅ Average 15 seconds to debug issues using logs
- ✅ 100% of critical security events logged
- ✅ All logs searchable within 1 second

---

**Document Status:** ✅ Ready for Implementation
