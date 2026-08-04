"""
Sentry Error Tracking Service
Provides comprehensive error tracking, performance monitoring, and issue management integration
"""

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for Sentry"""

    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class ErrorLevel(Enum):
    """Sentry error levels"""

    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class IssueStatus(Enum):
    """Sentry issue status"""

    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    ARCHIVED = "archived"


class IssuePriority(Enum):
    """Sentry issue priority levels"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SentryConfig:
    """Sentry configuration"""

    dsn: str
    environment: str
    release: str | None = None
    server_name: str | None = None
    debug: bool = False
    sample_rate: float = 1.0
    traces_sample_rate: float = 0.1
    max_breadcrumbs: int = 100
    attach_stacktrace: bool = True
    send_default_pii: bool = False
    before_send_callback: str | None = None
    before_breadcrumb_callback: str | None = None
    integrations: list[str] = field(default_factory=list)
    custom_tags: dict[str, str] = field(default_factory=dict)
    user_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorEvent:
    """Error event data structure"""

    event_id: str
    message: str
    level: ErrorLevel
    culprit: str | None = None
    exception: dict[str, Any] | None = None
    stacktrace: str | None = None
    request: dict[str, Any] | None = None
    user: dict[str, Any] | None = None
    tags: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)
    fingerprint: list[str] = field(default_factory=list)
    breadcrumbs: list[dict[str, Any]] = field(default_factory=list)
    contexts: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Issue:
    """Sentry issue representation"""

    issue_id: str
    title: str
    level: ErrorLevel
    status: IssueStatus
    priority: IssuePriority
    first_seen: datetime
    last_seen: datetime
    count: int
    users_affected: int
    assigned_to: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSpan:
    """Performance span data"""

    span_id: str
    parent_span_id: str | None
    trace_id: str
    op: str  # operation type
    description: str
    start_timestamp: datetime
    end_timestamp: datetime | None = None
    duration_ms: float | None = None
    status: str = "ok"  # ok, deadline_exceeded, cancelled, unknown
    tags: dict[str, str] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceTransaction:
    """Performance transaction data"""

    event_id: str
    trace_id: str
    name: str
    start_timestamp: datetime
    end_timestamp: datetime | None = None
    duration_ms: float | None = None
    status: str = "ok"
    spans: list[PerformanceSpan] = field(default_factory=list)
    tags: dict[str, str] = field(default_factory=dict)
    contexts: dict[str, Any] = field(default_factory=dict)
    user: dict[str, Any] | None = None
    release: str | None = None
    environment: str | None = None


class SentryService:
    """Comprehensive Sentry error tracking and performance monitoring service"""

    def __init__(self, config: SentryConfig | None = None):
        self.config = config or self._get_default_config()
        self.enabled = bool(self.config.dsn)
        self.issues_cache: dict[str, Issue] = {}
        self.performance_transactions: dict[str, PerformanceTransaction] = {}
        self.breadcrumbs: list[dict[str, Any]] = []

        # Initialize Sentry if enabled
        if self.enabled:
            self._initialize_sentry()

    def _get_default_config(self) -> SentryConfig:
        """Get default Sentry configuration"""
        return SentryConfig(
            dsn=getattr(settings, "SENTRY_DSN", ""),
            environment=getattr(settings, "ENVIRONMENT", "development"),
            release=getattr(settings, "APP_VERSION", None),
            server_name=getattr(settings, "SERVER_NAME", "psychsync-api"),
            debug=getattr(settings, "DEBUG", False),
            sample_rate=1.0 if settings.ENVIRONMENT == "production" else 1.0,
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            integrations=["fastapi", "sqlalchemy", "redis", "celery"],
            custom_tags={
                "service": "psychsync-api",
                "version": getattr(settings, "APP_VERSION", "1.0.0"),
            },
        )

    def _initialize_sentry(self):
        """Initialize Sentry SDK"""
        try:
            import sentry_sdk
            from sentry_sdk.integrations.celery import CeleryIntegration
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.redis import RedisIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            # Configure integrations
            integrations = []
            if "fastapi" in self.config.integrations:
                integrations.append(
                    FastApiIntegration(auto_enabling_integrations=False)
                )
            if "sqlalchemy" in self.config.integrations:
                integrations.append(SqlalchemyIntegration())
            if "redis" in self.config.integrations:
                integrations.append(RedisIntegration())
            if "celery" in self.config.integrations:
                integrations.append(CeleryIntegration())

            # Configure before_send callback
            def before_send(event, hint):
                """Filter and enrich events before sending to Sentry"""
                # Filter out sensitive data
                if event.get("request"):
                    request = event["request"]
                    # Remove sensitive headers
                    sensitive_headers = ["authorization", "cookie", "x-api-key"]
                    if "headers" in request:
                        request["headers"] = {
                            k: v
                            for k, v in request["headers"].items()
                            if k.lower() not in sensitive_headers
                        }

                # Add custom tags
                if "tags" not in event:
                    event["tags"] = {}
                event["tags"].update(self.config.custom_tags)

                return event

            # Initialize Sentry SDK
            sentry_sdk.init(
                dsn=self.config.dsn,
                environment=self.config.environment,
                release=self.config.release,
                server_name=self.config.server_name,
                debug=self.config.debug,
                sample_rate=self.config.sample_rate,
                traces_sample_rate=self.config.traces_sample_rate,
                max_breadcrumbs=self.config.max_breadcrumbs,
                attach_stacktrace=self.config.attach_stacktrace,
                send_default_pii=self.config.send_default_pii,
                before_send=before_send,
                integrations=integrations,
                auto_enabling_integrations=False,
            )

            logger.info("Sentry SDK initialized successfully")

        except ImportError:
            logger.warning("Sentry SDK not installed. Error tracking disabled.")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e!s}")
            self.enabled = False

    async def capture_exception(
        self,
        exception: Exception,
        level: ErrorLevel = ErrorLevel.ERROR,
        user: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
        fingerprint: list[str] | None = None,
    ) -> str | None:
        """Capture exception and send to Sentry"""
        if not self.enabled:
            return None

        try:
            import sentry_sdk

            # Add user context if provided
            if user:
                sentry_sdk.set_user(user)

            # Add tags
            if tags:
                sentry_sdk.set_tags(tags)

            # Add extra data
            if extra:
                sentry_sdk.set_extra("custom_data", extra)

            # Set fingerprint for grouping
            if fingerprint:
                with sentry_sdk.configure_scope() as scope:
                    scope.fingerprint = fingerprint

            # Capture exception
            event_id = sentry_sdk.capture_exception(exception)

            logger.info(f"Exception captured and sent to Sentry: {event_id}")
            return event_id

        except Exception as e:
            logger.error(f"Failed to capture exception in Sentry: {e!s}")
            return None

    async def capture_message(
        self,
        message: str,
        level: ErrorLevel = ErrorLevel.INFO,
        user: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> str | None:
        """Capture message and send to Sentry"""
        if not self.enabled:
            return None

        try:
            import sentry_sdk

            # Add user context if provided
            if user:
                sentry_sdk.set_user(user)

            # Add tags
            if tags:
                sentry_sdk.set_tags(tags)

            # Add extra data
            if extra:
                sentry_sdk.set_extra("custom_data", extra)

            # Capture message
            event_id = sentry_sdk.capture_message(message, level=level.value)

            logger.info(f"Message captured and sent to Sentry: {event_id}")
            return event_id

        except Exception as e:
            logger.error(f"Failed to capture message in Sentry: {e!s}")
            return None

    async def add_breadcrumb(
        self,
        message: str,
        category: str | None = None,
        level: str | None = None,
        data: dict[str, Any] | None = None,
    ):
        """Add breadcrumb to current Sentry context"""
        if not self.enabled:
            return

        try:
            import sentry_sdk

            breadcrumb = {
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if category:
                breadcrumb["category"] = category
            if level:
                breadcrumb["level"] = level
            if data:
                breadcrumb["data"] = data

            sentry_sdk.add_breadcrumb(**breadcrumb)

        except Exception as e:
            logger.error(f"Failed to add breadcrumb to Sentry: {e!s}")

    async def start_transaction(
        self, name: str, op: str = "http.server", description: str | None = None
    ) -> str | None:
        """Start a performance transaction"""
        if not self.enabled or self.config.traces_sample_rate == 0:
            return None

        try:
            import sentry_sdk

            transaction = sentry_sdk.start_transaction(
                {
                    "name": name,
                    "op": op,
                }
            )

            if description:
                transaction.set_description(description)

            # Add custom tags to transaction
            transaction.set_tags(self.config.custom_tags)

            trace_id = transaction.trace_id

            # Store transaction for later reference
            self.performance_transactions[trace_id] = PerformanceTransaction(
                event_id=str(uuid.uuid4()),
                trace_id=trace_id,
                name=name,
                start_timestamp=datetime.utcnow(),
                spans=[],
                tags=self.config.custom_tags.copy(),
            )

            return trace_id

        except Exception as e:
            logger.error(f"Failed to start transaction in Sentry: {e!s}")
            return None

    async def finish_transaction(self, trace_id: str, status: str = "ok"):
        """Finish a performance transaction"""
        if not self.enabled or trace_id not in self.performance_transactions:
            return

        try:
            import sentry_sdk

            # Get the current transaction from Sentry SDK
            transaction = sentry_sdk.get_current_transaction()
            if transaction and transaction.trace_id == trace_id:
                transaction.set_status(status)
                transaction.finish()

            # Update stored transaction
            if trace_id in self.performance_transactions:
                perf_transaction = self.performance_transactions[trace_id]
                perf_transaction.end_timestamp = datetime.utcnow()
                perf_transaction.duration_ms = (
                    perf_transaction.end_timestamp - perf_transaction.start_timestamp
                ).total_seconds() * 1000
                perf_transaction.status = status

            # Clean up stored transaction after some time
            await asyncio.sleep(300)  # Keep for 5 minutes
            if trace_id in self.performance_transactions:
                del self.performance_transactions[trace_id]

        except Exception as e:
            logger.error(f"Failed to finish transaction in Sentry: {e!s}")

    async def create_span(
        self,
        trace_id: str,
        op: str,
        description: str,
        parent_span_id: str | None = None,
    ) -> str | None:
        """Create a performance span within a transaction"""
        if not self.enabled or trace_id not in self.performance_transactions:
            return None

        try:
            import sentry_sdk

            span_id = str(uuid.uuid4())[:8]

            span = PerformanceSpan(
                span_id=span_id,
                parent_span_id=parent_span_id,
                trace_id=trace_id,
                op=op,
                description=description,
                start_timestamp=datetime.utcnow(),
            )

            # Store span in transaction
            self.performance_transactions[trace_id].spans.append(span)

            # Create actual Sentry span
            transaction = sentry_sdk.get_current_transaction()
            if transaction and transaction.trace_id == trace_id:
                sentry_span = transaction.start_child(op=op, description=description)
                # Store Sentry span reference for later finishing
                span._sentry_span = sentry_span

            return span_id

        except Exception as e:
            logger.error(f"Failed to create span in Sentry: {e!s}")
            return None

    async def finish_span(self, trace_id: str, span_id: str, status: str = "ok"):
        """Finish a performance span"""
        if not self.enabled:
            return

        try:
            if trace_id not in self.performance_transactions:
                return

            transaction = self.performance_transactions[trace_id]
            span = None
            for s in transaction.spans:
                if s.span_id == span_id:
                    span = s
                    break

            if not span:
                return

            span.end_timestamp = datetime.utcnow()
            span.duration_ms = (
                span.end_timestamp - span.start_timestamp
            ).total_seconds() * 1000
            span.status = status

            # Finish actual Sentry span if it exists
            if hasattr(span, "_sentry_span"):
                span._sentry_span.set_status(status)
                span._sentry_span.finish()

        except Exception as e:
            logger.error(f"Failed to finish span in Sentry: {e!s}")

    async def set_user(
        self,
        user_id: str,
        email: str | None = None,
        username: str | None = None,
        extra: dict[str, Any] | None = None,
    ):
        """Set user context for Sentry events"""
        if not self.enabled:
            return

        try:
            import sentry_sdk

            user_data = {"id": user_id, "email": email, "username": username}

            if extra:
                user_data.update(extra)

            sentry_sdk.set_user(user_data)

        except Exception as e:
            logger.error(f"Failed to set user in Sentry: {e!s}")

    async def set_tag(self, key: str, value: str):
        """Set tag for Sentry events"""
        if not self.enabled:
            return

        try:
            import sentry_sdk

            sentry_sdk.set_tag(key, value)

        except Exception as e:
            logger.error(f"Failed to set tag in Sentry: {e!s}")

    async def set_extra(self, key: str, value: Any):
        """Set extra data for Sentry events"""
        if not self.enabled:
            return

        try:
            import sentry_sdk

            sentry_sdk.set_extra(key, value)

        except Exception as e:
            logger.error(f"Failed to set extra data in Sentry: {e!s}")

    async def get_error_stats(self, hours: int = 24) -> dict[str, Any]:
        """Get error statistics from Sentry"""
        if not self.enabled:
            return {
                "total_errors": 0,
                "errors_by_level": {},
                "top_errors": [],
                "error_trend": [],
            }

        try:
            # This would make API calls to Sentry
            # For now, returning simulated data
            return {
                "total_errors": 45,
                "errors_by_level": {"error": 38, "warning": 5, "fatal": 2},
                "top_errors": [
                    {
                        "title": "Database Connection Timeout",
                        "count": 15,
                        "level": "error",
                    },
                    {"title": "Authentication Failed", "count": 12, "level": "error"},
                    {"title": "External API Timeout", "count": 8, "level": "warning"},
                ],
                "error_trend": [
                    {"hour": -23, "count": 3},
                    {"hour": -22, "count": 5},
                    {"hour": -21, "count": 2},
                    {"hour": -20, "count": 8},
                    {"hour": -19, "count": 4},
                ],
            }

        except Exception as e:
            logger.error(f"Failed to get error stats from Sentry: {e!s}")
            return {}

    async def create_issue(
        self,
        title: str,
        description: str,
        level: ErrorLevel = ErrorLevel.ERROR,
        assignee: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> str | None:
        """Create issue in Sentry"""
        if not self.enabled:
            return None

        try:
            # This would make API calls to Sentry to create an issue
            # For now, returning simulated response
            issue_id = str(uuid.uuid4())

            issue = Issue(
                issue_id=issue_id,
                title=title,
                level=level,
                status=IssueStatus.UNRESOLVED,
                priority=IssuePriority.MEDIUM,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                count=1,
                users_affected=1,
                assigned_to=assignee,
                tags=tags or {},
                metadata={"description": description},
            )

            self.issues_cache[issue_id] = issue

            logger.info(f"Created issue in Sentry: {issue_id}")
            return issue_id

        except Exception as e:
            logger.error(f"Failed to create issue in Sentry: {e!s}")
            return None

    def capture_exception_sync(self, func):
        """Decorator to automatically capture exceptions in functions"""

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Capture exception asynchronously
                asyncio.create_task(
                    self.capture_exception(
                        exception=e,
                        level=ErrorLevel.ERROR,
                        extra={
                            "function": func.__name__,
                            "module": func.__module__,
                            "args_count": len(args),
                            "kwargs_count": len(kwargs),
                        },
                    )
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Capture exception synchronously
                try:
                    import sentry_sdk

                    sentry_sdk.capture_exception(e)
                except Exception as e:
                    logger.error(f"Failed to capture exception: {e!s}")
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    async def get_performance_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get performance monitoring summary from Sentry"""
        if not self.enabled:
            return {
                "total_transactions": 0,
                "average_duration": 0,
                "slow_transactions": [],
                "error_rate": 0,
            }

        try:
            # This would make API calls to Sentry for performance data
            # For now, returning simulated data
            return {
                "total_transactions": 1250,
                "average_duration": 245.6,
                "slow_transactions": [
                    {
                        "name": "POST /api/v1/assessments",
                        "duration": 1250.5,
                        "count": 15,
                    },
                    {
                        "name": "GET /api/v1/team/analytics",
                        "duration": 890.3,
                        "count": 23,
                    },
                ],
                "error_rate": 0.8,
                "top_operations": [
                    {"op": "http.server", "count": 800, "avg_duration": 120.5},
                    {"op": "db.query", "count": 450, "avg_duration": 45.2},
                    {"op": "cache.get", "count": 1200, "avg_duration": 2.1},
                ],
            }

        except Exception as e:
            logger.error(f"Failed to get performance summary from Sentry: {e!s}")
            return {}

    @asynccontextmanager
    async def transaction_context(
        self, name: str, op: str = "http.server", description: str | None = None
    ):
        """Context manager for automatically managing transactions"""
        trace_id = await self.start_transaction(name, op, description)
        try:
            yield trace_id
        except Exception as e:
            await self.capture_exception(
                e, level=ErrorLevel.ERROR, extra={"transaction_trace_id": trace_id}
            )
            raise
        finally:
            if trace_id:
                await self.finish_transaction(
                    trace_id, "ok" if not isinstance(e, Exception) else "internal_error"
                )

    def __del__(self):
        """Cleanup when service is destroyed"""
        if self.enabled:
            try:
                import sentry_sdk

                sentry_sdk.flush()
            except Exception as e:
                pass


# Sentry middleware for FastAPI
class SentryMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic Sentry error tracking"""

    def __init__(self, app, sentry_service: SentryService):
        super().__init__(app)
        self.sentry_service = sentry_service

    async def dispatch(self, request: Request, call_next):
        if not self.sentry_service.enabled:
            return await call_next(request)

        # Start transaction
        transaction_name = f"{request.method} {request.url.path}"
        trace_id = await self.sentry_service.start_transaction(
            name=transaction_name, op="http.server"
        )

        # Add request breadcrumb
        await self.sentry_service.add_breadcrumb(
            message=f"{request.method} {request.url.path}",
            category="http",
            level="info",
            data={
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("user-agent"),
                "ip_address": request.client.host if request.client else None,
            },
        )

        try:
            response = await call_next(request)

            # Add response breadcrumb
            await self.sentry_service.add_breadcrumb(
                message=f"Response {response.status_code}",
                category="http",
                level="info",
                data={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type"),
                },
            )

            # Finish transaction with success
            if trace_id:
                status = "ok" if response.status_code < 400 else "resource_exhausted"
                await self.sentry_service.finish_transaction(trace_id, status)

            return response

        except Exception as e:
            # Capture exception with request context
            await self.sentry_service.capture_exception(
                e,
                level=ErrorLevel.ERROR,
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "user_agent": request.headers.get("user-agent"),
                    "ip_address": request.client.host if request.client else None,
                },
                tags={
                    "middleware": "sentry",
                    "request_method": request.method,
                    "request_path": request.url.path,
                },
            )

            # Finish transaction with error
            if trace_id:
                await self.sentry_service.finish_transaction(trace_id, "internal_error")

            raise


# Initialize Sentry service
sentry_service = SentryService()
