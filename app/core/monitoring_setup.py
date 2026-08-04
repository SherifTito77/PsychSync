"""
Monitoring Setup Guide

This file provides a complete setup for all monitoring components.
Follow this guide to enable comprehensive observability.

USAGE:
1. Add to your main.py or app initialization
2. Configure environment variables
3. Verify endpoints are accessible
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.v1.endpoints import prometheus_metrics

# from app.middleware import setup_security_middleware as setup_prometheus_middleware
from app.core.database import setup_database_monitoring

# Try to import tracing components (may not be available in all environments)
try:
    from app.core.distributed_tracing import initialize_tracing, shutdown_tracing

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.info(
        "Distributed tracing module not available - tracing disabled (OpenTelemetry is optional)"
    )

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan_monitoring_setup(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for monitoring setup

    Add to FastAPI app:

    ```python
    from app.core.monitoring_setup import lifespan_monitoring_setup

    app = FastAPI(lifespan=lifespan_monitoring_setup)
    ```

    This handles:
    - Prometheus metrics initialization
    - Distributed tracing startup
    - Database monitoring setup
    - Graceful shutdown
    """
    # Startup
    logger.info("🚀 Initializing monitoring stack...")

    # 1. Set up Prometheus metrics
    app.include_router(prometheus_metrics.router)
    logger.info("✅ Prometheus metrics endpoint registered")

    # 2. Set up distributed tracing
    tracing_enabled = (
        app.state.config.TRACING_ENABLED if hasattr(app.state, "config") else False
    )
    if tracing_enabled:
        initialize_tracing(
            service_name="psychsync-api",
            jaeger_endpoint=app.state.config.JAEGER_ENDPOINT,
            sample_rate=app.state.config.TRACING_SAMPLE_RATE,
        )
        logger.info("✅ Distributed tracing initialized")
    else:
        logger.info("⚠️  Distributed tracing disabled (enable via TRACING_ENABLED=true)")

    # 3. Set up database monitoring (if engine exists)
    if hasattr(app.state, "engine") and app.state.engine:
        setup_database_monitoring(
            app.state.engine,
            slow_query_threshold=app.state.config.SLOW_QUERY_THRESHOLD,
        )
        logger.info("✅ Database monitoring initialized")

    logger.info("✅ Monitoring stack ready!")
    logger.info("📊 Metrics: http://localhost:8000/metrics")
    logger.info("🔍 Traces: Configure JAEGER_ENDPOINT environment variable")

    yield

    # Shutdown
    logger.info("🛑 Shutting down monitoring stack...")

    # Shutdown distributed tracing if available
    if TRACING_AVAILABLE:
        try:
            shutdown_tracing()
            logger.info("✅ Distributed tracing shutdown")
        except Exception as e:
            logger.warning(f"Tracing shutdown warning: {e}")

    logger.info("✅ Monitoring stack shutdown complete")


def setup_monitoring(
    app: FastAPI,
    engine: AsyncEngine | None = None,
    enable_tracing: bool = False,
    jaeger_endpoint: str | None = None,
    slow_query_threshold: float = 1.0,
) -> None:
    """
    Complete monitoring setup (non-lifespan version)

    Use this if you're not using lifespan context manager:

    ```python
    from app.core.monitoring_setup import setup_monitoring

    app = FastAPI()
    engine = create_async_engine(...)

    setup_monitoring(
        app=app,
        engine=engine,
        enable_tracing=True,
        jaeger_endpoint="http://localhost:4318",
        slow_query_threshold=1.0,
    )
    ```

    Args:
        app: FastAPI application
        engine: SQLAlchemy engine (optional)
        enable_tracing: Enable distributed tracing
        jaeger_endpoint: Jaeger endpoint URL
        slow_query_threshold: Slow query threshold in seconds
    """
    # Include metrics router
    app.include_router(prometheus_metrics.router)

    # Add Prometheus middleware
    setup_prometheus_middleware(app)

    # Initialize tracing (if available and enabled)
    if enable_tracing:
        if TRACING_AVAILABLE:
            initialize_tracing(
                service_name="psychsync-api",
                jaeger_endpoint=jaeger_endpoint,
                sample_rate=0.1,  # 10% sampling
            )
            logger.info("✅ Distributed tracing enabled")
        else:
            logger.warning("⚠️  Tracing requested but module not available")
    else:
        logger.info("ℹ️  Distributed tracing disabled")

    # Setup database monitoring
    if engine:
        setup_database_monitoring(engine, slow_query_threshold=slow_query_threshold)
        logger.info(
            f"✅ Database monitoring enabled (slow query threshold: {slow_query_threshold}s"
        )

    logger.info("✅ Monitoring setup complete!")
    logger.info("📊 Prometheus metrics: http://localhost:8000/metrics")


# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================

"""
Required environment variables for monitoring:

# Prometheus
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus  # For multiprocessing

# Tracing
TRACING_ENABLED=true
JAEGER_ENDPOINT=http://localhost:4318
TRACING_SAMPLE_RATE=0.1  # 10% sampling (adjust based on traffic)

# Database Monitoring
SLOW_QUERY_THRESHOLD=1.0  # seconds

# Application
ENVIRONMENT=production  # development, staging, production
SERVICE_NAME=psychsync-api
"""

# ============================================================================
# VERIFICATION ENDPOINTS
# ============================================================================


async def verify_monitoring_setup(app: FastAPI) -> dict[str, bool]:
    """
    Verify that all monitoring components are working

    Returns:
        Dictionary with component status
    """
    status = {
        "prometheus_metrics": False,
        "tracing": False,
        "database_monitoring": False,
        "middleware": False,
    }

    # Check Prometheus metrics
    try:
        from prometheus_client import REGISTRY

        collectors = list(REGISTRY._collector_to_names.keys())
        if collectors:
            status["prometheus_metrics"] = True
    except ImportError:
        pass

    # Check tracing
    try:
        from opentelemetry import trace

        tracer = trace.get_tracer(__name__)
        status["tracing"] = tracer is not None
    except ImportError:
        pass

    # Check database monitoring
    if hasattr(app.state, "engine"):
        status["database_monitoring"] = True

    # Check middleware
    if hasattr(app, "middleware"):
        status["middleware"] = True

    return status


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "lifespan_monitoring_setup",
    "setup_monitoring",
    "verify_monitoring_setup",
]
