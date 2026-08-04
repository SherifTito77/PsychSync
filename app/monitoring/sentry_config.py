"""
PsychSync Sentry Configuration for FastAPI
Comprehensive error tracking and performance monitoring
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.pydantic import PydanticIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.strawberry import StrawberryIntegration

# Sentry Configuration
SENTRY_DSN = os.getenv("SENTRY_DSN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
RELEASE = os.getenv("APP_VERSION", "unknown")

# Sampling configuration
TRACES_SAMPLE_RATE = float(
    os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")
)  # 10% for production
PROFILES_SAMPLE_RATE = float(
    os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")
)  # 10% for production

# Feature flags
ENABLE_PERFORMANCE_MONITORING = (
    os.getenv("SENTRY_ENABLE_PERFORMANCE", "true").lower() == "true"
)
ENABLE_ERROR_MONITORING = os.getenv("SENTRY_ENABLE_ERRORS", "true").lower() == "true"


def init_sentry() -> None:
    """Initialize Sentry SDK with comprehensive configuration"""

    if not SENTRY_DSN:
        logging.warning("SENTRY_DSN not configured - Sentry disabled")
        return

    if ENVIRONMENT == "development" and not os.getenv("FORCE_SENTRY_DEV"):
        logging.info("Sentry disabled in development environment")
        return

    # Configure logging integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send ERROR logs as events
    )

    integrations = [
        # FastAPI and ASGI
        FastApiIntegration(
            enable_tracing=ENABLE_PERFORMANCE_MONITORING, transaction_style="endpoint"
        ),
        SentryAsgiMiddleware(transaction_style="url"),
        StarletteIntegration(transaction_style="url"),
        # Database and Cache
        SqlalchemyIntegration(enable_spans=True, engine_logging_level=logging.WARNING),
        RedisIntegration(enable_spans=True, enable_breadcrumbs=True),
        # HTTP clients
        HttpxIntegration(
            enable_tracing=ENABLE_PERFORMANCE_MONITORING,
            httpx_capture_all_requests=True,
        ),
        # Background tasks
        CeleryIntegration(
            monitor_beat_tasks=True,
            propagate_traces=True,
            exclude_beat_tasks=["celery.backend_cleanup"],
        ),
        # Schema validation
        PydanticIntegration(),
        # GraphQL (if using)
        StrawberryIntegration(),
        # Logging
        sentry_logging,
    ]

    # Configure before_send to filter sensitive data
    def before_send(
        event: dict[str, Any], hint: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Filter sensitive data and add context"""

        # Remove sensitive data from headers
        if "request" in event and "headers" in event["request"]:
            headers = event["request"]["headers"]
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            for header in sensitive_headers:
                if header in headers:
                    headers[header] = "[FILTERED]"

        # Remove sensitive data from extra
        if "extra" in event:
            sensitive_keys = ["password", "token", "secret", "key", "auth"]
            for key in list(event["extra"].keys()):
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    event["extra"][key] = "[FILTERED]"

        # Add custom tags
        event["tags"] = {
            **event.get("tags", {}),
            "service": "psychsync-api",
            "version": RELEASE,
            "environment": ENVIRONMENT,
        }

        return event

    # Configure before_breadcrumb to add context
    def before_breadcrumb(
        crumb: dict[str, Any], hint: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Filter and enhance breadcrumb data"""

        # Filter sensitive URLs
        if "url" in crumb:
            url = crumb["url"]
            if any(
                sensitive in url.lower()
                for sensitive in ["password", "token", "secret"]
            ):
                crumb["url"] = url.split("?")[0] + "?[FILTERED]"

        return crumb

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # Environment and release
        environment=ENVIRONMENT,
        release=RELEASE,
        # Sampling
        traces_sample_rate=TRACES_SAMPLE_RATE if ENABLE_PERFORMANCE_MONITORING else 0,
        profiles_sample_rate=(
            PROFILES_SAMPLE_RATE if ENABLE_PERFORMANCE_MONITORING else 0
        ),
        # Integrations
        integrations=integrations,
        # Data filtering
        before_send=before_send,
        before_breadcrumb=before_breadcrumb,
        # Error filtering
        ignore_errors=[
            # HTTP errors that are expected
            "HTTPException",
            "starlette.exceptions.HTTPException",
            "fastapi.exceptions.HTTPException",
            # Validation errors (handled in application)
            "pydantic.ValidationError",
            "starlette.validation.ValidationError",
            # Connection timeouts
            "TimeoutError",
            "asyncio.TimeoutError",
        ],
        # Additional configuration
        max_breadcrumbs=100,
        attach_stacktrace=True,
        send_default_pii=False,  # Never send PII
        debug=ENVIRONMENT == "development",
        # Server name for identification
        server_name=os.getenv("SENTRY_SERVER_NAME", "psychsync-api"),
    )

    logging.info(f"Sentry initialized - Environment: {ENVIRONMENT}, Release: {RELEASE}")


@asynccontextmanager
async def sentry_transaction(name: str, op: str = "function"):
    """Context manager for Sentry transaction tracing"""
    if not ENABLE_PERFORMANCE_MONITORING:
        yield
        return

    with sentry_sdk.start_transaction(
        name=name, op=op, auto_finish=True
    ) as transaction:
        try:
            yield transaction
        except Exception as e:
            # Record exception and re-raise
            sentry_sdk.capture_exception(e)
            raise


def set_sentry_user(user_data: dict[str, Any]) -> None:
    """Set user context for Sentry"""
    if not ENABLE_ERROR_MONITORING:
        return

    # Filter sensitive user data
    filtered_user = {
        "id": user_data.get("id"),
        "email": user_data.get("email"),
        "username": user_data.get("username"),
        "organization_id": user_data.get("organization_id"),
        "role": user_data.get("role"),
    }

    # Remove None values
    filtered_user = {k: v for k, v in filtered_user.items() if v is not None}

    sentry_sdk.set_user(filtered_user)


def set_sentry_context(key: str, value: dict[str, Any]) -> None:
    """Set additional context for Sentry"""
    if not ENABLE_ERROR_MONITORING:
        return

    sentry_sdk.set_context(key, value)


def capture_sentry_exception(
    error: Exception,
    level: str = "error",
    extra: dict[str, Any] | None = None,
    tags: dict[str, str] | None = None,
) -> None:
    """Capture exception with additional context"""
    if not ENABLE_ERROR_MONITORING:
        return

    with sentry_sdk.push_scope() as scope:
        scope.set_level(level)

        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)

        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        sentry_sdk.capture_exception(error)


def capture_sentry_message(
    message: str,
    level: str = "info",
    extra: dict[str, Any] | None = None,
    tags: dict[str, str] | None = None,
) -> None:
    """Capture message with context"""
    if not ENABLE_ERROR_MONITORING:
        return

    with sentry_sdk.push_scope() as scope:
        scope.set_level(level)

        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)

        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        sentry_sdk.capture_message(message, level=level)


# Custom middleware for transaction naming
class SentryTransactionMiddleware:
    """FastAPI middleware for automatic transaction naming"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract transaction information
        method = scope.get("method", "")
        path = scope.get("path", "")

        # Clean path for transaction naming
        if path.startswith("/api/v1/"):
            transaction_name = f"{method} /api/v1/{self._extract_endpoint(path)}"
        else:
            transaction_name = f"{method} {path}"

        # Start transaction
        transaction = sentry_sdk.start_transaction(
            name=transaction_name, op="http.server", auto_finish=True
        )

        # Set request data
        request_headers = dict(scope.get("headers", []))
        transaction.set_data("url", path)
        transaction.set_data("method", method)
        transaction.set_tag("http.method", method)
        transaction.set_tag("http.url", path)

        # Wrap send to finish transaction
        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                status = message.get("status", 200)
                transaction.set_http_status(status)
                transaction.set_tag("http.status_code", str(status))

            await send(message)

            # Finish transaction when response is complete
            if message["type"] == "http.response.body" and not message.get(
                "more_body", False
            ):
                transaction.finish()

        try:
            await self.app(scope, receive, wrapped_send)
        except Exception as e:
            transaction.set_status("internal_error")
            sentry_sdk.capture_exception(e)
            raise

    def _extract_endpoint(self, path: str) -> str:
        """Extract clean endpoint name from path"""
        # Remove ID parameters and convert to readable format
        import re

        # Replace numeric IDs with placeholders
        path = re.sub(r"/\d+", "/{id}", path)

        # Extract the main endpoint part
        if path.startswith("/api/v1/"):
            endpoint = path[7:]  # Remove "/api/v1/"
            return endpoint.split("/")[0] if "/" in endpoint else endpoint

        return "unknown"


# Health check for Sentry
def check_sentry_health() -> dict[str, Any]:
    """Check Sentry health and configuration"""
    return {
        "configured": bool(SENTRY_DSN),
        "environment": ENVIRONMENT,
        "release": RELEASE,
        "performance_monitoring": ENABLE_PERFORMANCE_MONITORING,
        "error_monitoring": ENABLE_ERROR_MONITORING,
        "traces_sample_rate": TRACES_SAMPLE_RATE,
        "profiles_sample_rate": PROFILES_SAMPLE_RATE,
    }
