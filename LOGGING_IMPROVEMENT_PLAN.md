# Logging Improvement Plan - Production Debugging Enhancement

**Date:** 2026-01-18
**Status:** Ready for Implementation
**Priority:** Phase 1 (Critical Security), Phase 2 (Performance), Phase 3 (Observability)

---

## Executive Summary

This comprehensive logging improvement plan addresses **1,500+ logging blind spots** identified across the PsychSync codebase. The plan is organized into three phases prioritized by business impact:

- **Phase 1 (Week 1):** Critical security & compliance fixes
- **Phase 2 (Week 2):** Performance monitoring & debugging
- **Phase 3 (Week 3):** Enhanced observability

---

## Current State Analysis

### ✅ Existing Infrastructure (Good Foundation)

1. **StructuredLoggingMiddleware** (`app/middleware/logging.py`)
   - Generates correlation IDs for HTTP requests
   - Logs request/response with timing
   - Client IP tracking

2. **AuditLogger** (`app/core/audit_logger.py`)
   - Security event categorization
   - Structured audit trail
   - Sensitive data redaction

3. **StructuredFormatter** (`app/core/logging_config.py`)
   - JSON formatting for log aggregation
   - IP sanitization for privacy
   - Exception handling

### ❌ Critical Gaps Identified

| Category | Count | Severity | Impact |
|----------|-------|----------|--------|
| Print statements in production code | 852 | CRITICAL | No audit trail, security risk |
| Authentication without structured logging | 12 | HIGH | Cannot detect attacks |
| Database operations without metrics | 200+ | MEDIUM | Cannot detect slow queries |
| Missing correlation ID propagation | 95% | HIGH | Cannot trace requests |
| External API calls without timing | 40+ | MEDIUM | Cannot debug third-party issues |
| Business operations without audit | 150+ | MEDIUM | Compliance risk |

---

## Phase 1: Critical Security & Compliance (Week 1)

### Priority 1.1: Replace print() Statements in Authentication

**Files Affected:**
- `app/api/v1/endpoints/simple_auth.py` (6 print statements)

**Current Code:**
```python
print(f"❌ Login failed: User '{username}' not found in database")
print(f"✅ User found: {user.email}, attempting login...")
print(f"✅ Login successful for: {user.email}")
print(f"Simple login error: {e}")
```

**Problems:**
- Authentication events not logged to structured logger
- No correlation with request IDs
- Stack traces printed to console (may not be captured)
- Cannot track brute force attacks or suspicious patterns

**Implementation:**

```python
from app.core.audit_logger import AuditLogger, SecurityEventType
from app.middleware.request_id import get_request_id
import logging

logger = logging.getLogger(__name__)

@router.post("/simple-login")
async def simple_login(
    username: str = Form(...),
    password: str = Form(...),
    request: Request = None
):
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    correlation_id = get_request_id()

    try:
        # Query user from database
        result = await db.execute(
            text("SELECT id, email, full_name FROM users WHERE email = :email"),
            {"email": username}
        )
        user = result.fetchone()

        if not user:
            # ❌ BEFORE: print(f"❌ Login failed: User '{username}' not found")
            # ✅ AFTER: Structured logging with context
            logger.warning(
                "Authentication failed - user not found",
                extra={
                    "event": "auth_failure",
                    "correlation_id": correlation_id,
                    "username": username,
                    "reason": "user_not_found",
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                }
            )

            # Audit log for security monitoring
            AuditLogger.log_security_event(
                event_type=SecurityEventType.AUTHENTICATION_FAILURE,
                user_id=None,
                details=f"Login attempt with non-existent email: {username}",
                client_ip=client_ip,
                user_agent=user_agent,
                endpoint="/api/v1/auth/simple-login",
                method="POST",
                request_id=correlation_id,
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # ✅ Successful authentication logging
        logger.info(
            "Authentication successful",
            extra={
                "event": "auth_success",
                "correlation_id": correlation_id,
                "user_id": str(user.id),
                "email": user.email,
                "client_ip": client_ip,
            }
        )

        AuditLogger.log_security_event(
            event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
            user_id=str(user.id),
            details=f"Successful login for: {user.email}",
            client_ip=client_ip,
            user_agent=user_agent,
            endpoint="/api/v1/auth/simple-login",
            method="POST",
            request_id=correlation_id,
        )

        # ... rest of login logic

    except HTTPException:
        raise
    except Exception as e:
        # ❌ BEFORE: print(f"Simple login error: {e}"); traceback.print_exc()
        # ✅ AFTER: Structured error logging
        logger.error(
            "Authentication system error",
            exc_info=True,
            extra={
                "event": "auth_error",
                "correlation_id": correlation_id,
                "username": username,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "client_ip": client_ip,
            }
        )

        AuditLogger.log_security_event(
            event_type=SecurityEventType.SYSTEM_ERROR,
            details=f"Authentication system error: {str(e)}",
            client_ip=client_ip,
            endpoint="/api/v1/auth/simple-login",
            method="POST",
            request_id=correlation_id,
            severity="high",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) from e
```

**Benefits:**
- ✅ Complete audit trail for authentication events
- ✅ Correlation with request IDs for tracing
- ✅ Security event tracking for threat detection
- ✅ Structured logs for SIEM integration
- ✅ IP and user agent tracking for forensics

---

### Priority 1.2: Implement Correlation ID Propagation

**Problem:** Correlation IDs generated in middleware but not used in 95% of business logic

**Solution:** Create correlation context helper

**File:** `app/core/correlation.py` (NEW)

```python
"""
Correlation ID Context Manager
Propagates correlation IDs across service boundaries
"""

from contextvars import ContextVar
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)

# Context variable for correlation ID (thread-safe, async-safe)
CORRELATION_ID_CONTEXT: ContextVar[Optional[str]] = ContextVar(
    'correlation_id',
    default=None
)

def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in context"""
    CORRELATION_ID_CONTEXT.set(correlation_id)

def get_correlation_id() -> str:
    """Get correlation ID from context or generate new one"""
    correlation_id = CORRELATION_ID_CONTEXT.get()
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
        CORRELATION_ID_CONTEXT.set(correlation_id)
        logger.debug(f"Generated new correlation ID: {correlation_id}")
    return correlation_id

def clear_correlation_id() -> None:
    """Clear correlation ID from context"""
    CORRELATION_ID_CONTEXT.set(None)


# =============================================================================
# Structured Logging Helper
# =============================================================================

def log_with_context(
    logger_instance: logging.Logger,
    level: int,
    message: str,
    **extra
) -> None:
    """
    Log a message with automatic correlation ID injection

    Args:
        logger_instance: Logger instance
        level: Log level (logging.INFO, logging.ERROR, etc.)
        message: Log message
        **extra: Additional structured fields
    """
    # Automatically inject correlation ID
    extra['correlation_id'] = get_correlation_id()

    logger_instance.log(level, message, extra=extra)
```

**Integration with Middleware:**

```python
# app/middleware/logging.py

from app.core.correlation import set_correlation_id

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())

        # Set in context for all downstream code
        set_correlation_id(correlation_id)

        request.state.correlation_id = correlation_id

        # ... rest of middleware logic
```

**Usage in Services:**

```python
# app/services/response_service.py

from app.core.correlation import get_correlation_id, log_with_context

class ResponseService:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        response_in: ResponseCreate
    ) -> Response:
        correlation_id = get_correlation_id()

        # Log with automatic correlation ID injection
        log_with_context(
            logger,
            logging.INFO,
            "Creating assessment response",
            event="response_create_start",
            assessment_id=str(response_in.assessment_id),
            user_id=str(response_in.user_id),
        )

        try:
            response = Response(
                assessment_id=response_in.assessment_id,
                user_id=response_in.user_id,
                # ... other fields
            )

            db.add(response)
            await db.commit()
            await db.refresh(response)

            log_with_context(
                logger,
                logging.INFO,
                "Response created successfully",
                event="response_create_success",
                response_id=str(response.id),
            )

            return response

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to create response",
                event="response_create_error",
                exc_info=True,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise
```

---

### Priority 1.3: Add Database Operation Performance Logging

**Files Affected:**
- `app/services/response_service.py` (create, update, delete)
- `app/services/assessment_service.py` (create, update, delete)
- 200+ other database operations

**Implementation Pattern:**

```python
# app/services/response_service.py

import time
from app.core.correlation import get_correlation_id, log_with_context

class ResponseService:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        response_in: ResponseCreate
    ) -> Response:
        """Create a new assessment response."""
        start_time = time.time()
        correlation_id = get_correlation_id()

        try:
            log_with_context(
                logger,
                logging.INFO,
                "Creating assessment response",
                event="db_create_start",
                operation="create_response",
                table="responses",
                assessment_id=str(response_in.assessment_id),
                user_id=str(response_in.user_id),
            )

            response = Response(
                assessment_id=response_in.assessment_id,
                user_id=response_in.user_id,
                question_id=response_in.question_id,
                answer_text=getattr(response_in, "answer_text", None),
                answer_value=getattr(response_in, "answer_value", None),
                answer_data=getattr(response_in, "answer_data", None),
                response_time_ms=getattr(response_in, "response_time_ms", None),
                confidence_rating=getattr(response_in, "confidence_rating", None),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            db.add(response)
            await db.commit()
            await db.refresh(response)

            # Calculate initial score if possible
            await ResponseService._calculate_score(db, response)

            duration_ms = (time.time() - start_time) * 1000

            log_with_context(
                logger,
                logging.INFO,
                "Database operation completed",
                event="db_create_success",
                operation="create_response",
                table="responses",
                response_id=str(response.id),
                duration_ms=round(duration_ms, 2),
            )

            # Performance warning if slow
            if duration_ms > 500:  # >500ms
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Slow database operation detected",
                    event="db_slow_query",
                    operation="create_response",
                    duration_ms=round(duration_ms, 2),
                    threshold_ms=500,
                )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            log_with_context(
                logger,
                logging.ERROR,
                "Database operation failed",
                event="db_create_error",
                operation="create_response",
                duration_ms=round(duration_ms, 2),
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )

            raise
```

**Benefits:**
- ✅ Query performance tracking
- ✅ Automatic slow query detection (>500ms warning)
- ✅ Correlation with HTTP requests
- ✅ Database operation audit trail

---

## Phase 2: Performance Monitoring & Debugging (Week 2)

### Priority 2.1: External API Call Logging

**Files Affected:**
- `app/services/push_notification_service.py` (FCM API calls)
- `app/services/webhook_manager_secure.py` (webhook deliveries)
- `app/services/slack_integration_service.py` (Slack API)
- 40+ other external API integrations

**Implementation Pattern:**

```python
# app/services/push_notification_service.py

import time
from app.core.correlation import get_correlation_id, log_with_context

class PushNotificationService:
    async def _send_to_fcm(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Send notification to FCM servers"""
        start_time = time.time()
        correlation_id = get_correlation_id()

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"key={self.fcm_server_key}",
            }

            log_with_context(
                logger,
                logging.INFO,
                "External API call initiated",
                event="external_api_start",
                api_service="fcm",
                endpoint=self.fcm_api_url,
                request_size=len(json.dumps(payload)),
            )

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.fcm_api_url,
                    json=payload,
                    headers=headers,
                )

                duration_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    result = response.json()

                    log_with_context(
                        logger,
                        logging.INFO,
                        "External API call completed",
                        event="external_api_success",
                        api_service="fcm",
                        duration_ms=round(duration_ms, 2),
                        status_code=response.status_code,
                        response_size=len(response.text),
                    )

                    if "results" in result:
                        return result["results"]

                    return [{"success": True, "message_id": result.get("message_id")}]

                else:
                    log_with_context(
                        logger,
                        logging.ERROR,
                        "External API call failed",
                        event="external_api_error",
                        api_service="fcm",
                        duration_ms=round(duration_ms, 2),
                        status_code=response.status_code,
                        response_text=response.text[:500],  # Truncate
                    )

                    return [{"success": False, "error": "FCM API error"}]

        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000

            log_with_context(
                logger,
                logging.ERROR,
                "External API call timeout",
                event="external_api_timeout",
                api_service="fcm",
                duration_ms=round(duration_ms, 2),
                timeout_seconds=self.timeout,
            )

            return [{"success": False, "error": "Request timeout"}]

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            log_with_context(
                logger,
                logging.ERROR,
                "External API call exception",
                event="external_api_exception",
                api_service="fcm",
                duration_ms=round(duration_ms, 2),
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )

            return [{"success": False, "error": str(e)}]
```

**Benefits:**
- ✅ External API performance tracking
- ✅ Timeout detection
- ✅ Error categorization
- ✅ Third-party integration debugging

---

### Priority 2.2: Background Job Progress Logging

**Files Affected:**
- Celery tasks, data exports, report generation
- 30+ long-running background operations

**Implementation Pattern:**

```python
# app/services/reporting_service.py

import logging
from app.core.correlation import get_correlation_id

logger = logging.getLogger(__name__)

async def generate_report(report_id: str, user_id: str):
    """Generate comprehensive report with progress logging"""
    correlation_id = get_correlation_id()

    log_with_context(
        logger,
        logging.INFO,
        "Report generation started",
        event="task_start",
        task_type="report_generation",
        report_id=report_id,
        user_id=user_id,
    )

    try:
        # Step 1: Data gathering
        log_with_context(
            logger,
            logging.INFO,
            "Gathering data for report",
            event="task_step",
            step=1,
            step_name="data_gathering",
        )

        data = await gather_report_data(report_id)

        log_with_context(
            logger,
            logging.INFO,
            "Data gathering completed",
            event="task_step_complete",
            step=1,
            record_count=len(data),
        )

        # Step 2: Processing
        log_with_context(
            logger,
            logging.INFO,
            "Processing report data",
            event="task_step",
            step=2,
            step_name="data_processing",
        )

        processed = await process_report_data(data)

        log_with_context(
            logger,
            logging.INFO,
            "Data processing completed",
            event="task_step_complete",
            step=2,
        )

        # Step 3: Generation
        log_with_context(
            logger,
            logging.INFO,
            "Generating report document",
            event="task_step",
            step=3,
            step_name="report_generation",
        )

        report = await create_report_document(processed)

        log_with_context(
            logger,
            logging.INFO,
            "Report generation completed successfully",
            event="task_complete",
            task_type="report_generation",
            report_id=report_id,
            document_url=report.url,
        )

        return report

    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Report generation failed",
            event="task_failed",
            task_type="report_generation",
            report_id=report_id,
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True,
        )
        raise
```

---

## Phase 3: Enhanced Observability (Week 3)

### Priority 3.1: Performance Metrics Logging

**Target Operations:**
- Assessment scoring duration
- AI processing time
- Export generation time
- 100+ critical business operations

**Implementation:**

```python
import time
from functools import wraps
from app.core.correlation import log_with_context

def log_performance(operation_name: str, warning_threshold_ms: float = 5000):
    """
    Decorator to log operation performance metrics

    Args:
        operation_name: Name of the operation for logging
        warning_threshold_ms: Threshold in ms for performance warning
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                duration_ms = (time.time() - start_time) * 1000

                log_with_context(
                    logger,
                    logging.INFO,
                    f"{operation_name} completed",
                    event="performance_metric",
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2),
                    success=True,
                )

                # Warning if slow
                if duration_ms > warning_threshold_ms:
                    log_with_context(
                        logger,
                        logging.WARNING,
                        f"Slow {operation_name} detected",
                        event="performance_slow",
                        operation=operation_name,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=warning_threshold_ms,
                    )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                log_with_context(
                    logger,
                    logging.ERROR,
                    f"{operation_name} failed",
                    event="performance_error",
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

                raise

        return wrapper
    return decorator


# Usage:
@log_performance("assessment_scoring", warning_threshold_ms=3000)
async def score_assessment(assessment_id: str):
    # Scoring logic here
    pass
```

---

### Priority 3.2: Business Logic Audit Trails

**Target Operations:**
- Template creation/modification
- Assessment creation/completion
- User role changes
- 150+ business operations

**Implementation:**

```python
# app/services/template_service.py

from app.core.audit_logger import AuditLogger, SecurityEventType
from app.core.correlation import get_correlation_id, log_with_context

async def create_template(
    db: AsyncSession,
    template_in: TemplateCreate,
    creator_id: UUID | None = None
):
    correlation_id = get_correlation_id()

    log_with_context(
        logger,
        logging.INFO,
        "Template creation started",
        event="template_create_start",
        creator_id=str(creator_id),
        template_name=template_in.name,
        template_type=template_in.template_type,
    )

    try:
        template = await TemplateService.create(db, template_in, creator_id)

        log_with_context(
            logger,
            logging.INFO,
            "Template created successfully",
            event="template_create_success",
            template_id=str(template.id),
            template_name=template.name,
        )

        # Audit log for compliance
        AuditLogger.log_security_event(
            user_id=str(creator_id),
            event_type=SecurityEventType.DATA_MODIFICATION,
            details=f"Created template: {template.name} (ID: {template.id})",
            endpoint="/api/v1/templates",
            method="POST",
            request_id=correlation_id,
            additional_data={
                "template_id": str(template.id),
                "template_name": template.name,
                "template_type": template.template_type,
            },
        )

        return template

    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Template creation failed",
            event="template_create_error",
            creator_id=str(creator_id),
            template_name=template_in.name,
            error_type=type(e).__name__,
            exc_info=True,
        )

        AuditLogger.log_security_event(
            user_id=str(creator_id),
            event_type=SecurityEventType.SYSTEM_ERROR,
            details=f"Failed to create template: {str(e)}",
            endpoint="/api/v1/templates",
            method="POST",
            request_id=correlation_id,
            severity="medium",
        )

        raise
```

---

## Implementation Checklist

### Week 1: Critical Security & Compliance
- [ ] Replace all print() statements in `simple_auth.py` with structured logging
- [ ] Create `app/core/correlation.py` with correlation context helper
- [ ] Update `StructuredLoggingMiddleware` to set correlation context
- [ ] Add correlation ID propagation to top 10 critical services
- [ ] Implement database performance logging for CRUD operations
- [ ] Test authentication logging with security scenarios

### Week 2: Performance Monitoring & Debugging
- [ ] Add external API call logging to all third-party integrations
- [ ] Implement progress logging for background jobs
- [ ] Add performance metrics to critical operations
- [ ] Create slow query detection dashboard queries
- [ ] Test external API timeout scenarios

### Week 3: Enhanced Observability
- [ ] Implement performance decorator for automatic timing
- [ ] Add audit trails to all business operations
- [ ] Create log aggregation queries for common debugging tasks
- [ ] Set up alerts for critical log patterns
- [ ] Document logging standards and best practices

---

## Testing Strategy

### Unit Testing
```python
# tests/test_correlation_logging.py

def test_correlation_id_propagation():
    """Test that correlation IDs propagate through service calls"""
    from app.core.correlation import set_correlation_id, get_correlation_id

    # Set correlation ID
    set_correlation_id("test-correlation-123")

    # Verify it's available downstream
    assert get_correlation_id() == "test-correlation-123"


def test_structured_logging_with_context():
    """Test that structured logging includes correlation IDs"""
    import logging
    from app.core.correlation import log_with_context

    logger = logging.getLogger("test")

    # Mock log handler to capture output
    handler = MockLogHandler()
    logger.addHandler(handler)

    set_correlation_id("test-123")
    log_with_context(logger, logging.INFO, "Test message", user_id="user-456")

    # Verify correlation ID was injected
    assert "correlation_id" in handler.records[0]
    assert handler.records[0]["correlation_id"] == "test-123"
    assert handler.records[0]["user_id"] == "user-456"
```

### Integration Testing
- Simulate failed login attempts → verify audit logs created
- Execute database operations → verify performance metrics logged
- Call external APIs → verify timing logged
- Test slow operations → verify warnings triggered

---

## Success Metrics

### Quantitative Metrics
- **Print statements:** 852 → 0 (100% elimination)
- **Correlation ID usage:** 5% → 95% (90% increase)
- **Database operations with metrics:** 0% → 100% (all CRUD operations)
- **External API calls with logging:** 0% → 100% (all integrations)
- **Business operations with audit trails:** 0% → 80% (critical operations)

### Qualitative Improvements
- ✅ Can trace single request across all database operations
- ✅ Can detect and debug slow queries in production
- ✅ Has complete audit trail for compliance
- ✅ Can debug third-party integration issues
- ✅ Can track authentication events for security monitoring
- ✅ Can monitor background job progress

---

## Rollout Strategy

### Phase 1: Non-Breaking Changes
- All changes are additive (no breaking changes)
- Existing print() statements remain functional during transition
- Correlation context gracefully falls back to new IDs if not set

### Phase 2: Gradual Migration
- Start with high-risk services (auth, payments, assessments)
- Migrate remaining services based on priority
- Remove print() statements after verifying structured logs work

### Phase 3: Monitoring & Optimization
- Monitor log volume and performance impact
- Tune slow query thresholds based on production data
- Create dashboards for common debugging queries

---

## Risk Mitigation

### Risk 1: Log Volume Explosion
**Mitigation:** Use log levels appropriately (INFO for normal, WARNING for slow, ERROR for failures)

### Risk 2: Performance Overhead
**Mitigation:** Async logging, batch writes, measure impact before deployment

### Risk 3: Sensitive Data Leakage
**Mitigation:** Existing SensitiveDataFilter sanitizes logs, verify with security review

---

## Documentation Requirements

1. **Developer Guide:** How to use correlation context and log_with_context helper
2. **Runbook:** Common debugging queries and log patterns
3. **Standards:** When to use each log level, what fields to include
4. **Onboarding:** Add logging training to developer onboarding checklist

---

## Dependencies

### Required Packages (Already Installed)
- ✅ logging (Python stdlib)
- ✅ contextvars (Python stdlib)
- ✅ pydantic-settings (for structured log data)

### Optional Enhancements
- Python-json-logger (for structured JSON output)
- Sentry (for error tracking integration)
- ELK Stack (for log aggregation and visualization)

---

## Support & Maintenance

### Log Rotation
- Configure logrotate for `/var/log/psychsync/*.log`
- Retain logs for 90 days (compliance requirement)
- Archive older logs to cold storage

### Monitoring
- Set up alerts for:
  - ERROR logs exceeding threshold (>100/min)
  - Authentication failures (>5/min from same IP)
  - Slow database queries (>5s)
  - External API timeouts (>10/min)

---

**Plan Status:** ✅ Ready for Implementation
**Estimated Effort:** 3 weeks (1 week per phase)
**Business Impact:** High (security, compliance, debugging capability)
**Risk Level:** Low (additive changes, no breaking modifications)

---

*Generated: 2026-01-18*
*Author: Claude Code (Anthropic)*
*Version: 1.0*
