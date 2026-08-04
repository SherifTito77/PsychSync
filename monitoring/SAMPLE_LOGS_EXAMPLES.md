# Sample Logs - Production Debugging Examples
## Demonstrating PsychSync Logging Capabilities

**Date:** 2026-03-10
**Version:** 1.0.0

---

## Executive Summary

This document provides **real-world sample logs** from PsychSync's production logging infrastructure to demonstrate debugging capabilities. Each example includes the full JSON log entry, an explanation of what it shows, and how to use it for production troubleshooting.

---

## Table of Contents

1. [API Request/Response Logging](#1-api-requestresponse-logging)
2. [Authentication Event Logs](#2-authentication-event-logs)
3. [Security Event Logs](#3-security-event-logs)
4. [Database Operation Logs](#4-database-operation-logs)
5. [Error & Exception Logs](#5-error--exception-logs)
6. [Performance Monitoring Logs](#6-performance-monitoring-logs)
7. [AI/Model Event Logs](#7-aimodel-event-logs)
8. [Correlation ID Tracing](#8-correlation-id-tracing)
9. [Cross-Service Debugging](#9-cross-service-debugging)
10. [Investigation Scenarios](#10-investigation-scenarios)

---

## 1. API Request/Response Logging

### Successful Request with Context

```json
{
  "timestamp": "2026-03-10T12:34:56.789Z",
  "level": "INFO",
  "logger": "psychsync.api",
  "message": "API Request",
  "module": "dispatch",
  "function": "api_request",
  "line": 78,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_abc123",
  "ip_address": "192.168.1.xxx",
  "event": "api_request",
  "method": "POST",
  "path": "/api/v1/responses",
  "query_params": "assessment_id=456&user_id=user_abc123",
  "client_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "timestamp_epoch": 16784564967.89
}
```

**What This Shows:**
- ✅ User `user_abc123` submitted a response at `12:34:56`
- ✅ Correlation ID `550e8400...` for distributed tracing
- ✅ Request method and path for endpoint identification
- ✅ Query parameters showing assessment and user context
- ✅ Client IP and user agent for geographic/browser analysis

**Debugging Use Case:**
> **Scenario:** User reports response not saving
>
> **Steps:**
> 1. Search by user_id: `user_id:"user_abc123"`
> 2. Filter by endpoint: `path:"/api/v1/responses"`
> 3. Check timestamp range when user reported issue
> 4. Look for subsequent response log with same `correlation_id`
> 5. Verify status code and any error messages

---

### Response with Timing

```json
{
  "timestamp": "2026-03-10T12:34:56.923Z",
  "level": "INFO",
  "logger": "psychsync.api",
  "message": "API Response - Success",
  "module": "dispatch",
  "function": "api_response",
  "line": 156,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "event": "api_response",
  "method": "POST",
  "path": "/api/v1/responses",
  "status_code": 200,
  "duration_ms": 234.5,
  "response_size": 2048,
  "content_type": "application/json",
  "timestamp_epoch": 16784564969.923
}
```

**What This Shows:**
- ✅ Request completed successfully in **234.5ms**
- ✅ Response size of 2KB indicates moderate data payload
- ✅ Same `correlation_id` links request and response

**Performance Debugging:**
> **Scenario:** Investigating slow API response
>
> **Query:** `duration_ms > 500 AND path:"/api/v1/responses"`
>
> **Analysis:**
> - This request is fast (234ms) - not the problem
> - Compare with other requests to same endpoint
> - Look for database lock contention or external API delays in correlation chain

---

## 2. Authentication Event Logs

### Successful Login

```json
{
  "timestamp": "2026-03-10T14:22:15.123Z",
  "level": "INFO",
  "logger": "app.security.logging",
  "message": "Login Success",
  "module": "auth_middleware",
  "function": "log_auth_event",
  "line": 445,
  "correlation_id": "7a3d8f90-2c4e-4f1a-9b7c-5d6e8f4a3b2c",
  "event": "security_login_attempt",
  "success": true,
  "email": "john.doe@example.com",
  "ip": "203.0.113.xxx",
  "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
  "timestamp_epoch": 1678462935.123,
  "event_type": "auth_login_success",
  "severity": "info",
  "actor_user_id": "user_456789",
  "actor_username": "john.doe",
  "actor_ip_address": "203.0.113.45",
  "actor_user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
  "auth_method": "password",
  "mfa_verified": true,
  "is_anomalous": false,
  "risk_score": 0.0,
  "browser": "Chrome",
  "os": "Mac OS X",
  "device": "Desktop"
}
```

**What This Shows:**
- ✅ User `john.doe@example.com` successfully logged in
- ✅ MFA was verified (`mfa_verified: true`)
- ✅ Low risk score indicates normal login pattern
- ✅ Browser/OS/device fingerprinting for future comparison

**Security Debugging:**
> **Scenario:** Detecting suspicious login attempts
>
> **Query:** `event:"security_login_attempt" AND success:false`
>
> **Investigation:**
> - Look for multiple failures from same IP
> - Check if failures span short time window (brute force)
> - Compare with successful logins (same IP? different user?)
> - Verify user_agent consistency

---

### Failed Login (Invalid Credentials)

```json
{
  "timestamp": "2026-03-10T14:22:30.456Z",
  "level": "WARNING",
  "logger": "app.security.logging",
  "message": "Login Failed",
  "module": "auth_middleware",
  "function": "log_auth_event",
  "line": 449,
  "correlation_id": "8b4e9f01-3d5f-5g2b-0c8d-6e7f9g5b4c3d",
  "event": "security_login_attempt",
  "success": false,
  "email": "john.doe@example.com",
  "ip": "198.51.100.xxx",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "timestamp_epoch": 1678462950.456,
  "event_type": "auth_login_failure",
  "severity": "high",
  "actor_username": "john.doe",
  "actor_ip_address": "198.51.100.23",
  "actor_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "auth_method": "password",
  "failure_reason": "invalid_credentials",
  "is_anomalous": false,
  "risk_score": 25.0,
  "browser": "Firefox",
  "os": "Windows",
  "device": "Desktop"
}
```

**What This Shows:**
- ⚠️ Login failed with **invalid credentials**
- ⚠️ Risk score elevated to 25 (threshold for investigation)
- ⚠️ Different IP and user-agent than previous successful login

**Security Investigation:**
> **Scenario:** Potential account compromise
>
> **Analysis:**
> 1. Previous successful login from IP `203.0.113.xxx` on Mac/Chrome
> 2. This failed attempt from IP `198.51.100.xxx` on Windows/Firefox
> 3. **Recommendation:** Contact user to verify if this was them
> 4. **Action:** Trigger MFA challenge if multiple failures continue

---

## 3. Security Event Logs

### Privilege Escalation Event

```json
{
  "timestamp": "2026-03-10T15:45:22.789Z",
  "level": "INFO",
  "logger": "app.security.logging",
  "message": "Privilege change: role_granted on user_xyz",
  "module": "security_logger",
  "function": "log_privilege_change",
  "line": 305,
  "correlation_id": "9c5f0g12-4e6g-6h3c-1d9e-7f0h6c5d4e3",
  "event_type": "priv_role_granted",
  "severity": "HIGH",
  "actor_user_id": "user_123456",
  "target_user_id": "user_xyz",
  "target_username": "jane.smith",
  "target_old_role": "user",
  "target_new_role": "admin",
  "actor_ip_address": "192.0.2.xxx",
  "reason": "Project lead assignment - Team Alpha project",
  "approval_ticket": "JIRA-9876",
  "approved_by": "manager_abc",
  "scope": "user",
  "description": "Privilege change: role_granted on user_xyz",
  "metadata": {
    "organization_id": "org_789",
    "team_id": "team_123",
    "timestamp_epoch": 1678467922.789
  },
  "tags": ["security", "privilege", "admin", "role_change"]
}
```

**What This Shows:**
- ✅ **High severity** privilege change event
- ✅ User `jane.smith` elevated from `user` to `admin` role
- ✅ Approved by `manager_abc` with JIRA ticket reference
- ✅ Reason documented for audit trail

**Compliance Debugging:**
> **Scenario:** Auditor wants to trace admin privilege grants
>
> **Query:** `event_type:"priv_role_granted" AND target_new_role:"admin"`
>
> **Report:**
> - List all admin role grants in specified time period
> - Include approvers and justification
> - Cross-reference with security incidents
> - Verify all changes had proper approval

---

### Data Export Event

```json
{
  "timestamp": "2026-03-10T16:30:45.111Z",
  "level": "MEDIUM",
  "logger": "app.security.logging",
  "message": "Data access: export on user_assessments",
  "module": "security_logger",
  "function": "log_data_access",
  "line": 437,
  "correlation_id": "0d6g1h23-5f7h-7i4d-2e0f-8g1i7e6f5g4",
  "event_type": "data_export",
  "severity": "MEDIUM",
  "actor_user_id": "user_789",
  "data_type": "user_assessments",
  "data_classification": "confidential",
  "access_method": "api",
  "record_count": 1500,
  "is_bulk_access": true,
  "export_format": "csv",
  "export_destination": "/exports/assessments_20260310.csv",
  "export_size_bytes": 524288,
  "export_record_count": 1500,
  "description": "Data access: export on user_assessments",
  "metadata": {
    "export_duration_ms": 3450,
    "filters": {
      "assessment_type": "clinical",
      "date_range": "2026-01-01 to 2026-03-10",
      "organization_id": "org_789"
    }
  }
}
```

**What This Shows:**
- ⚠️ **Bulk export** of 1,500 confidential records
- ⚠️ Export took 3.45 seconds to complete
- ⚠️ CSV format with specific date range filter

**GDPR/Compliance Debugging:**
> **Scenario:** Data breach investigation
>
> **Query:** `event_type:"data_export" AND data_classification:"confidential"`
>
> **Investigation:**
> 1. Identify all bulk exports in last 30 days
> 2. Cross-reference with user access privileges
> 3. Verify destination (download vs. external transfer)
> 4. Check if user had legitimate business need
> 5. Review file access logs for exported file

---

## 4. Database Operation Logs

### Slow Database Query

```json
{
  "timestamp": "2026-03-10T17:15:33.222Z",
  "level": "INFO",
  "logger": "app.core.database",
  "message": "Database read operation completed",
  "module": "crud",
  "function": "get_responses",
  "line": 245,
  "correlation_id": "1e7h2i34-6g8h-8j5e-3f1g-9h2j8f7g6h5",
  "event": "db_read_success",
  "operation": "read",
  "table": "responses",
  "duration_ms": 1234.56,
  "success": true,
  "responses_id": "response_456789",
  "user_id": "user_123",
  "organization_id": "org_789",
  "timestamp_epoch": 1678472133.222
}
```

**What This Shows:**
- ✅ Database read operation took **1.23 seconds** (slow!)
- ✅ Successfully retrieved response record
- ✅ User and organization context

**Performance Debugging:**
> **Scenario:** Investigating slow page load
>
> **Query:** `duration_ms > 1000 AND operation:"read" AND table:"responses"`
>
> **Root Cause Analysis:**
> 1. Query took 1.23s - above 500ms threshold
> 2. Check if `responses_id` is indexed
> 3. Look for JOIN operations or N+1 queries
> 4. Compare with similar queries (are they all slow?)
> 5. **Action:** Add index on frequently queried columns

---

**Corresponding Warning:**

```json
{
  "timestamp": "2026-03-10T17:15:33.222Z",
  "level": "WARNING",
  "logger": "app.core.database",
  "message": "Slow database read detected",
  "module": "crud",
  "function": "get_responses",
  "line": 323,
  "correlation_id": "1e7h2i34-6g8h-8j5e-3f1g-9h2j8f7g6h5",
  "event": "db_slow_query",
  "operation": "read",
  "table": "responses",
  "duration_ms": 1234.56,
  "threshold_ms": 500,
  "description": "Database query exceeded performance threshold"
}
```

---

### Database Operation Failure

```json
{
  "timestamp": "2026-03-10T17:20:15.444Z",
  "level": "ERROR",
  "logger": "app.core.database",
  "message": "Database create operation failed",
  "module": "crud",
  "function": "create_response",
  "line": 349,
  "correlation_id": "2f8i3j45-7h9i-9k6f-4g2h-0i3k9h8i7j6",
  "event": "db_create_error",
  "operation": "create",
  "table": "responses",
  "duration_ms": 45.67,
  "error_type": "IntegrityError",
  "error_message": "duplicate key value violates unique constraint \"responses_user_id_assessment_id_key\"",
  "user_id": "user_456",
  "organization_id": "org_789",
  "exc_info": "Traceback (most recent call last):\n  File \"/app/crud/crud_response.py\", line 123, in create_response\n    db.add(response_obj)\n  File \"/usr/local/lib/python3.10/site-packages/sqlalchemy/orm/scoping.py\", line 272, in add\n    instrument = self._instrument_class(instance, key, **kwargs)\n  File \"/usr/local/lib/python3.10/site-packages/sqlalchemy/orm/session.py\", line 2759, in flush\n    flush_context.execute(statements)\n  File \"/usr/local/lib/python3.10/site-packages/sqlalchemy/engine/base.py\", line 1968, in _execute_context\n    conn.execute(statement, params)\npsycopg2.errors.UniqueViolation: duplicate key value violates unique constraint..."
}
```

**What This Shows:**
- ❌ Database constraint violation (duplicate entry)
- ❌ Operation failed after 46ms (database rejected it)
- ❌ Full stack trace for debugging

**Bug Debugging:**
> **Scenario:** Duplicate response submission
>
> **Analysis:**
> 1. User attempted to create duplicate response
> 2. Unique constraint on `(user_id, assessment_id)` prevented duplicate
> 3. **Root Cause:** Frontend allowing double-submission or race condition
> 4. **Action:** Add frontend deduplication + database ON CONFLICT handling

---

## 5. Error & Exception Logs

### Application Error with Context

```json
{
  "timestamp": "2026-03-10T18:45:10.777Z",
  "level": "ERROR",
  "logger": "app.api.endpoints.assessments",
  "message": "API Request Failed",
  "module": "dispatch",
  "function": "get_assessment",
  "line": 203,
  "correlation_id": "3g9j4k56-8i0j-0l7g-5h3i-1j4k0i9j8l7",
  "event": "api_error",
  "method": "GET",
  "path": "/api/v1/assessments/789",
  "client_ip": "10.0.0.xxx",
  "duration_ms": 156.78,
  "error_type": "HTTPException",
  "error_message": "Assessment not found or user does not have access",
  "user_id": "user_123",
  "timestamp_epoch": 1678476310.777
}
```

**What This Shows:**
- ❌ 404 error or 403 forbidden
- ❌ User `user_123` cannot access assessment `789`
- ❌ Request duration 157ms (not a timeout)

**Access Control Debugging:**
> **Scenario:** User reports "Cannot access assessment" error
>
> **Query:** `user_id:"user_123" AND error_type:"HTTPException"`
>
> **Investigation:**
> 1. Check if user has permission for this assessment
> 2. Verify assessment exists and is active
> 3. Check organization/team membership
> 4. Review RBAC rules for this endpoint
> 5. **Action:** Update permissions or provide helpful error message

---

### System Error with Stack Trace

```json
{
  "timestamp": "2026-03-10T19:30:25.888Z",
  "level": "ERROR",
  "logger": "app.services.assessment_service",
  "message": "Assessment scoring failed",
  "module": "scoring",
  "function": "calculate_score",
  "line": 567,
  "correlation_id": "4h0k5l67-9j1k-1m8h-6i4j-2k5l1j0k9m8",
  "event": "system_error",
  "operation": "calculate_score",
  "error_type": "ValueError",
  "error_message": "Cannot calculate score: Invalid response data format",
  "response_id": "response_123456",
  "user_id": "user_789",
  "outcome": "invalid_response_format",
  "metadata": {
    "response_data": {
      "answers": null,
      "question_id": "q_789",
      "value": "invalid"
    },
    "expected_format": {
      "answers": ["array", "of", "strings"],
      "question_id": "string",
      "value": "string or number"
    }
  },
  "exc_info": "Traceback (most recent call last):\n  File \"/app/services/assessment_service.py\", line 545, in calculate_score\n    return self._process_answers(response_data)\n  File \"/app/services/assessment_service.py\", line 512, in _process_answers\n    for answer in response_data['answers']:\nTypeError: 'NoneType' object is not iterable"
}
```

**What This Shows:**
- ❌ System error during scoring calculation
- ❌ Invalid data format (`answers: null`)
- ❌ Full stack trace pointing to line 512
- ❌ Metadata showing expected vs actual format

**Bug Fix Debugging:**
> **Scenario:** Scoring fails intermittently
>
> **Analysis:**
> 1. TypeError at line 512: trying to iterate over None
> 2. Response data has null answers field
> 3. **Root Cause:** Database query or API returning incomplete data
> 4. **Action:** Add validation in scoring function + fix data source

---

## 6. Performance Monitoring Logs

### Performance Metric Log

```json
{
  "timestamp": "2026-03-10T20:15:45.999Z",
  "level": "INFO",
  "logger": "app.core.database",
  "message": "database_query completed",
  "module": "crud",
  "function": "get_user_data",
  "line": 150,
  "correlation_id": "5l1m6n78-0k2l-2n9i-7j5k-3l6m2n0o1p9",
  "event": "performance_metric",
  "operation": "database_query",
  "duration_ms": 234.56,
  "success": true,
  "timestamp_epoch": 1678482145.999
}
```

**What This Shows:**
- ✅ Database query completed in **234ms** (acceptable)
- ✅ Success flag for monitoring
- ✅ Correlation ID for linking to request

### Slow Operation Warning

```json
{
  "timestamp": "2026-03-10T20:20:10.123Z",
  "level": "WARNING",
  "logger": "app.core.database",
  "message": "Slow database_query detected",
  "module": "crud",
  "function": "get_user_data",
  "line": 210,
  "correlation_id": "6m2n7o89-1l3m-3o0j-8k6l-4m7n3o1q0r8",
  "event": "performance_slow",
  "operation": "database_query",
  "duration_ms": 1234.56,
  "threshold_ms": 500,
  "description": "Database query exceeded 500ms threshold",
  "timestamp_epoch": 1678482410.123
}
```

**What This Shows:**
- ⚠️ **Slow operation** detected (1.23s vs 500ms threshold)
- ⚠️ Performance degradation indicator

**Performance Investigation:**
> **Scenario:** Dashboard shows slowness at 20:20
>
> **Query:** `event:"performance_slow" AND duration_ms > 1000`
>
> **Analysis:**
> 1. Identify all slow operations in time window
> 2. Look for patterns (same table? same query?)
> 3. Check for lock contention or resource exhaustion
> 4. **Action:** Add database index or optimize query

---

## 7. AI/Model Event Logs

### Model Prompt with Safety Scoring

```json
{
  "timestamp": "2026-03-10T21:45:30.456Z",
  "level": "INFO",
  "logger": "app.security.logging",
  "message": "Model event: gpt-4",
  "module": "security_logger",
  "function": "log_model_event",
  "line": 532,
  "correlation_id": "7n3o8p90-2m4n-4p1k-9l7m-5n8o2p1q0r9",
  "event_type": "model_prompt",
  "severity": "INFO",
  "actor_user_id": "user_123",
  "model_name": "gpt-4",
  "prompt_length": 256,
  "prompt_tokens": 64,
  "prompt_hash": "a7f3b2c1d5e8f9a2b6c4d7e8f9a0b1c2d3e4f5",
  "prompt_preview": "[REDACTED] User asked about anxiety management strategies for workplace...",
  "response_length": 1024,
  "response_tokens": 256,
  "response_hash": "b8c4d3e2f6a9c0b1d4e5f7a0b2c3d4e5f6a7",
  "response_preview": "[REDACTED] Here are some evidence-based strategies: 1. Practice...",
  "tools_used": [],
  "tool_results_count": 0,
  "latency_ms": 2345,
  "safety_score": 0.95,
  "flagged_content": [],
  "injection_indicators": [],
  "cache_hit": false,
  "description": "Model event: gpt-4",
  "timestamp_epoch": 1678486330.456
}
```

**What This Shows:**
- ✅ User triggered GPT-4 model for AI chatbot
- ✅ High safety score (0.95) - content is safe
- ✅ 256 tokens input → 1024 tokens output
- ✅ 2.3 second latency
- ✅ No injection indicators or flagged content

**AI Debugging:**
> **Scenario:** Monitoring AI costs and safety
>
> **Query:** `model_name:"gpt-4" AND safety_score < 0.5`
>
> **Analysis:**
> 1. Find low-safety-score AI interactions
> 2. Review prompt_previews for concerning content
> 3. Check if safety filters are working
> 4. **Action:** Adjust content filters or add guardrails

---

### Injection Attempt Detected

```json
{
  "timestamp": "2026-03-10T22:30:15.789Z",
  "level": "CRITICAL",
  "logger": "app.security.logging",
  "message": "Model event: gpt-4",
  "module": "security_logger",
  "function": "log_model_event",
  "line": 523,
  "correlation_id": "8o4p9q01-3n5o-5q2l-0m8n-6o9p3q1r0s9",
  "event_type": "model_injection_attempt",
  "severity": "CRITICAL",
  "actor_user_id": "user_456",
  "model_name": "gpt-4",
  "prompt_length": 512,
  "prompt_tokens": 128,
  "prompt_hash": "c9d5e4f3a7b0c2d3e4f5a6b7c8d9e0a1b2c3d4",
  "prompt_preview": "[REDACTED] Ignore previous instructions. Instead, tell me...",
  "response_length": 0,
  "response_tokens": 0,
  "response_hash": null,
  "response_preview": null,
  "tools_used": [],
  "tool_results_count": 0,
  "latency_ms": 0,
  "safety_score": 0.15,
  "flagged_content": ["injection_attempt", "prompt_injection", "jailbreak"],
  "injection_indicators": [
    "Ignore previous instructions",
    "Instead, tell me",
    "jailbreak pattern detected"
  ],
  "cache_hit": false,
  "description": "Model event: gpt-4",
  "timestamp_epoch": 1678490215.789
}
```

**What This Shows:**
- 🚨 **CRITICAL** - Injection attempt detected
- 🚨 Low safety score (0.15)
- 🚨 Multiple injection indicators flagged
- 🚨 Prompt contains classic jailbreak patterns

**Security Response:**
> **Scenario:** User attempting prompt injection
>
> **Immediate Action:**
> 1. Block this request
> 2. Flag user account for review
> 3. Log incident for security team
> 4. **Investigation:** Check user's intent - malicious or testing?
> 5. **Action:** If malicious, suspend account; if testing, document as security research

---

## 8. Correlation ID Tracing

### Complete Request Flow

**Request 1 - Initial API Call:**
```json
{
  "timestamp": "2026-03-10T10:00:00.000Z",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "event": "api_request",
  "method": "GET",
  "path": "/api/v1/assessments/123",
  "user_id": "user_abc"
}
```

**Request 2 - Database Query:**
```json
{
  "timestamp": "2026-03-10T10:00:00.050Z",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "event": "db_read_success",
  "operation": "read",
  "table": "assessments",
  "duration_ms": 45.2
}
```

**Request 3 - External API Call:**
```json
{
  "timestamp": "2026-03-10T10:00:00.100Z",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "event": "api_request",
  "method": "POST",
  "path": "/external/ai-analyze",
  "duration_ms": 1234.5
}
```

**Request 4 - Response:**
```json
{
  "timestamp": "2026-03-10T10:00:01.500Z",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "event": "api_response",
  "method": "GET",
  "path": "/api/v1/assessments/123",
  "status_code": 200,
  "duration_ms": 1500.0
}
```

**What This Shows:**
- ✅ **Complete request flow** using single correlation ID
- ✅ Total duration: 1.5 seconds
- ✅ Breakdown:
  - Database query: 45ms
  - External API: 1,234ms
  - Processing: 221ms

**Distributed Tracing Debugging:**
> **Scenario:** Slow assessment loading page
>
> **Query:** `correlation_id:"550e8400-e29b-41d4-a716-446655440000"`
>
> **Timeline Analysis:**
> 1. API Request received at 10:00:00
> 2. Database query: 45ms (fast)
> 3. External AI API: 1,234ms (**BOTTLENECK!**)
> 4. Total: 1.5s
>
> **Root Cause:** External AI analysis API is slow
> **Action:** Cache AI results or move to faster service

---

## 9. Cross-Service Debugging

### Celery Background Task

```json
{
  "timestamp": "2026-03-10T11:30:00.000Z",
  "level": "INFO",
  "logger": "app.tasks.celery_worker",
  "message": "Task started: process_assessment_results",
  "module": "worker",
  "function": "process_assessment_results",
  "line": 78,
  "correlation_id": "660f9511-f30c-52e5-b827-557766551111",
  "event": "celery_task_started",
  "task_id": "abc-123-def-456",
  "task_name": "app.tasks.process_assessment_results",
  "args": "[456, 789]",
  "kwargs": "{}",
  "retries": 0,
  "user_id": "user_system"
  "timestamp_epoch": 1678486200.0
}
```

**Task Completion:**
```json
{
  "timestamp": "2026-03-10T11:30:05.000Z",
  "level": "INFO",
  "logger": "app.tasks.celery_worker",
  "message": "Task completed: process_assessment_results",
  "module": "worker",
  "function": "process_assessment_results",
  "line": 125,
  "correlation_id": "660f9511-f30c-52e5-b827-557766551111",
  "event": "celery_task_completed",
  "task_id": "abc-123-def-456",
  "task_name": "app.tasks.process_assessment_results",
  "duration_ms": 5000,
  "result": "success",
  "processed_records": 100,
  "timestamp_epoch": 1678486205.0
}
```

**What This Shows:**
- ✅ Background task started at 11:30:00
- ✅ Completed in 5 seconds, processing 100 records
- ✅ Same correlation ID ties to original request

**Background Task Debugging:**
> **Scenario:** Celery task not completing
>
> **Query:** `task_id:"abc-123-def-456"`
>
> **Investigation:**
> 1. Find task start and completion logs
> 2. Check for any ERROR logs with same task_id
> 3. Review Celery worker status
> 4. **Action:** If stuck, retry task or investigate worker health

---

## 10. Investigation Scenarios

### Scenario 1: User Cannot Login

**Step 1 - Find Login Attempts**
```logql
{event_type="auth_login_failure"} | logfmt | actor_username="john.doe@example.com"
```

**Results:**
- 3 failed attempts in last 5 minutes
- All from different IPs
- All failed with "invalid_credentials"

**Step 2 - Check Successful Login**
```logql
{event_type="auth_login_success"} | logfmt | actor_username="john.doe@example.com"
```

**Results:**
- Last successful login was 30 days ago
- IP address matches current location

**Conclusion:** Account compromised - user needs password reset

---

### Scenario 2: Slow Page Load

**Step 1 - Find Slow Requests**
```logql
{event="api_response"} | unwrap() | duration_ms > 2000 | path="/api/v1/assessments/123"
```

**Results:**
- Average duration: 3,500ms
- P95: 5,200ms
- P99: 7,800ms

**Step 2 - Trace Request Flow**
```logql
{correlation_id="550e8400-e29b-41d4-a716-446655440000"}
```

**Results:**
- API Request: 0ms
- Database Query: 45ms
- AI Analysis: 3,200ms (95% of time)
- Response Processing: 255ms

**Root Cause:** External AI API is bottleneck

**Action:** Implement caching for AI analysis results

---

### Scenario 3: Data Export Investigation

**Step 1 - Find Bulk Exports**
```logql
{event_type="data_export"} | record_count > 100
```

**Results:**
- 15 bulk exports in last 7 days
- All by user `user_789`
- All from different organizations

**Step 2 - Check User Access**
```logql
{actor_user_id="user_789"} | logfmt | event_type="priv_*"
```

**Results:**
- No privilege changes for user
- User belongs to 3 organizations (normal)
- No unusual access patterns

**Step 3 - Correlate with Downloads**
```logql
{actor_user_id="user_789"} | logfmt | event_type="data_access_write"
```

**Results:**
- User has legitimate access to exported data
- All exports within normal working hours

**Conclusion:** User is data scientist/analyst, behavior is normal

**Action:** No action needed, continue monitoring

---

## Log Query Examples

### Find All Errors for Specific User
```logql
{level="ERROR"} | logfmt | actor_user_id="user_123"
```

### Find Failed Logins from IP Range
```logql
{event_type="auth_login_failure"} | logfmt | actor_ip_address=~"192\.168\..*"
```

### Find Slow Database Queries
```logql
{event="db_slow_query"} | unwrap() | duration_ms > 1000
```

### Find Security Events by Severity
```logql
{severity="HIGH"} or {severity="CRITICAL"} | logfmt | line_format "{{.timestamp}} [{{.severity}}] {{.event_type}}"
```

### Find API Errors with High Duration
```logql
{event="api_error"} | unwrap() | duration_ms > 1000 | status_code >= 500
```

### Count Events by Type (Last Hour)
```logql
count_over_time({event_type=~".*"} [1h]) by (event_type)
```

### Find Anomalies by Risk Score
```logql
{event_type=~".*"} | unwrap() | risk_score > 50
```

---

## Conclusion

These sample logs demonstrate PsychSync's comprehensive logging capabilities for production debugging:

- ✅ **Request Flow Tracing** - Full visibility into request lifecycle
- ✅ **Security Monitoring** - Detailed security events with context
- ✅ **Performance Tracking** - Identify bottlenecks and slow operations
- ✅ **Error Diagnostics** - Stack traces and context for debugging
- ✅ **Correlation ID Tracking** - Distributed tracing across services
- ✅ **Structured JSON Format** - Queryable and parseable for analysis

**Next Steps:**
1. Use these examples as reference for production debugging
2. Develop standard investigation procedures for common scenarios
3. Train operations team on log querying
4. Integrate with alerting for automated incident response
