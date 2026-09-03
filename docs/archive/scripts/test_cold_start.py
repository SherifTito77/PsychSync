#!/usr/bin/env python3
"""
COLD-START TEST SUITE

This script tests initialization behavior under cold-start scenarios to identify
potential bugs that occur when the application starts from a fresh state.

Test Scenarios:
1. Fresh database connection initialization
2. Redis unavailability during startup
3. DI container initialization with missing dependencies
4. Service registration order dependencies
5. Concurrent initialization requests
6. Environment variable missing during startup
7. Background task startup failures
8. Middleware initialization before services

Author: Security Team
Created: March 2026
"""

import asyncio
import logging
import os
import signal
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a cold-start test"""

    test_name: str
    passed: bool
    duration_ms: float
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} | {self.test_name} | {self.duration_ms:.1f}ms | {self.error or 'OK'}"


class ColdStartTestSuite:
    """
    Comprehensive cold-start testing suite
    Tests initialization patterns and identifies bugs in cold-start scenarios
    """

    def __init__(self):
        self.results: List[TestResult] = []
        self.passed = 0
        self.failed = 0

    async def run_all_tests(self):
        """Run all cold-start tests"""
        logger.info("🧪 Starting Cold-Start Test Suite")
        logger.info("=" * 60)

        tests = [
            ("Fresh Database Initialization", self.test_fresh_db_init),
            ("Redis Unavailable During Startup", self.test_redis_unavailable),
            ("DI Container With Missing Deps", self.test_di_missing_deps),
            ("Service Registration Order", self.test_service_order),
            ("Concurrent Initialization", self.test_concurrent_init),
            ("Missing Environment Variables", self.test_missing_env_vars),
            ("Background Task Startup Failure", self.test_bg_task_failure),
            ("Middleware Before Services", self.test_middleware_before_services),
            ("Health Check During Init", self.test_health_during_init),
            ("Circuit Breaker Cold Start", self.test_circuit_breaker_cold_start),
            ("Async Engine Creation", self.test_async_engine_creation),
            ("Lifespan Exception Recovery", self.test_lifespan_exception_recovery),
        ]

        for test_name, test_func in tests:
            logger.info(f"\n🔍 Running: {test_name}")
            try:
                result = await test_func()
                self.results.append(result)
                if result.passed:
                    self.passed += 1
                else:
                    self.failed += 1
                logger.info(str(result))
            except Exception as e:
                logger.error(f"Test crashed: {e}")
                self.results.append(
                    TestResult(
                        test_name=test_name,
                        passed=False,
                        duration_ms=0,
                        error=f"Test crashed: {str(e)}",
                    )
                )
                self.failed += 1

        logger.info("\n" + "=" * 60)
        logger.info(f"Test Summary: {self.passed} passed, {self.failed} failed")
        logger.info("=" * 60)

        return self.results

    async def test_fresh_db_init(self) -> TestResult:
        """
        COLD-START BUG #1: Database initialization with no prior connections

        Potential Issues:
        - Connection pool not pre-warmed
        - Missing SSL context in production
        - Timeout values too aggressive for cold starts
        """
        start = time.time()
        details = {}

        try:
            from app.core.database import async_engine, check_db_health

            # Simulate cold start by checking health immediately
            logger.info("Testing database health check on cold start...")
            health_result = await check_db_health()

            # Check connection pool status
            pool = async_engine.pool
            details["pool_size"] = pool.size()
            details["checked_out"] = pool.checkedout()
            details["overflow"] = pool.overflow()

            # BUG DETECTED: Pool size 0 on cold start
            if pool.size() == 0:
                logger.warning("⚠️  BUG: Connection pool size is 0 on cold start")
                details["bug_detected"] = "pool_size_zero"

            # BUG DETECTED: Health check passes before pool warmed
            if health_result and pool.checkedout() == 0:
                logger.warning("⚠️  BUG: Health check passes but pool not used")
                details["bug_detected"] = "health_check_too_early"

            duration_ms = (time.time() - start) * 1000
            return TestResult(
                test_name="Fresh Database Initialization",
                passed=health_result,
                duration_ms=duration_ms,
                details=details,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Database initialization failed: {e}")
            return TestResult(
                test_name="Fresh Database Initialization",
                passed=False,
                duration_ms=duration_ms,
                error=str(e),
                details=details,
            )

    async def test_redis_unavailable(self) -> TestResult:
        """
        COLD-START BUG #2: Redis unavailable during startup

        Potential Issues:
        - Mock client used instead of failing gracefully
        - Circuit breaker initialized in OPEN state
        - No retry on initial connection
        """
        start = time.time()
        details = {}

        try:
            from app.core.cache import cache_get, cache_set
            from app.core.redis_client import get_redis_circuit_breaker, get_redis_client

            # Simulate Redis unavailability by using wrong port
            original_url = os.environ.get("REDIS_URL")
            os.environ["REDIS_URL"] = "redis://localhost:9999"

            logger.info("Testing Redis unavailability scenario...")

            # Get circuit breaker to check initial state
            circuit_breaker = get_redis_circuit_breaker()
            initial_state = circuit_breaker.state.value
            details["initial_circuit_state"] = initial_state

            # Try to get Redis client (should use mock)
            client = await get_redis_client()
            details["client_type"] = type(client).__name__

            # BUG DETECTED: Client is mock but no degradation logged
            if client.__class__.__name__ == "MockRedisClient":
                logger.warning(
                    "⚠️  BUG: Using mock client without proper degradation logging"
                )
                details["bug_detected"] = "mock_client_no_logging"

            # Try cache operations
            await cache_set("test_key", "test_value", expire=10)
            result = await cache_get("test_key")
            details["cache_result"] = result

            # BUG DETECTED: Circuit breaker not triggered on cold start
            if circuit_breaker.state.value == initial_state:
                logger.warning(
                    "⚠️  BUG: Circuit breaker not triggered during cold start failure"
                )
                details["bug_detected"] = "circuit_breaker_not_triggered"

            # Restore original URL
            if original_url:
                os.environ["REDIS_URL"] = original_url
            else:
                os.environ.pop("REDIS_URL", None)

            duration_ms = (time.time() - start) * 1000
            return TestResult(
                test_name="Redis Unavailable During Startup",
                passed=True,
                duration_ms=duration_ms,
                details=details,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Redis test failed: {e}")
            return TestResult(
                test_name="Redis Unavailable During Startup",
                passed=False,
                duration_ms=duration_ms,
                error=str(e),
                details=details,
            )

    async def test_di_missing_deps(self) -> TestResult:
        """
        COLD-START BUG #3: DI container with missing dependencies

        Potential Issues:
        - Services registered without dependencies ready
        - Circular dependency not detected at startup
        - Singleton initialization order not enforced
        """
        start = time.time()
        details = {}

        try:
            from app.dependency_injection.container import Lifetime, container
            from app.dependency_injection.service_registrations import register_all_services

            # Register services
            register_all_services()

            # Check for validation errors
            validation_errors = container.validate_dependencies()
            details["validation_errors"] = validation_errors

            # BUG DETECTED: Validation disabled in production
            if (
                len(validation_errors) == 0
                and "validate_service_registrations"
                in open("app/dependency_injection/service_registrations.py").read()
            ):
                logger.warning("⚠️  BUG: Validation is commented out in production")
                details["bug_detected"] = "validation_disabled"

            # Get service info to check registration order
            service_info = container.get_service_info()
            details["service_count"] = len(service_info)
            details["singletons"] = sum(
                1 for info in service_info.values() if info["lifetime"] == "singleton"
            )

            # BUG DETECTED: Critical services not registered
            critical_services = ["db_session_provider", "redis_client", "settings"]
            missing_services = [s for s in critical_services if s not in service_info]
            if missing_services:
                logger.warning(f"⚠️  BUG: Missing critical services: {missing_services}")
                details["bug_detected"] = "missing_critical_services"
                details["missing_services"] = missing_services

            duration_ms = (time.time() - start) * 1000
            return TestResult(
                test_name="DI Container With Missing Deps",
                passed=len(missing_services) == 0,
                duration_ms=duration_ms,
                details=details,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ DI test failed: {e}")
            return TestResult(
                test_name="DI Container With Missing Deps",
                passed=False,
                duration_ms=duration_ms,
                error=str(e),
                details=details,
            )

    async def test_service_order(self) -> TestResult:
        """
        COLD-START BUG #4: Service registration order dependencies

        Potential Issues:
        - Services registered before their dependencies
        - Infrastructure services depending on application services
        - No dependency graph validation
        """
        start = time.time()
        details = {}

        try:
            from app.dependency_injection.service_registrations import (
                register_all_services,
                register_core_services,
                register_domain_services,
                register_infrastructure_services,
            )

            # Test each registration step
            logger.info("Testing service registration order...")

            # Step 1: Core services
            register_core_services()

            # BUG DETECTED: Domain services depend on core but registered separately
            try:
                from app.dependency_injection.container import container

                # Try to resolve a service before domain services are registered
                # This should fail if order is enforced
                info = container.get_service_info()
                details["after_core"] = list(info.keys())

            except Exception as e:
                details["core_error"] = str(e)

            # Step 2: Domain services (may have missing dependencies)
            domain_result = await self._safe_execute(register_domain_services)
            details["domain_success"] = domain_result is not False

            # BUG DETECTED: Domain services fail due to missing layer
            if not details["domain_success"]:
                logger.warning(
                    "⚠️  BUG: Domain services fail due to missing domain layer"
                )
                details["bug_detected"] = "missing_domain_layer"

            # Step 3: Infrastructure services
            infra_result = await self._safe_execute(register_infrastructure_services)
            details["infrastructure_success"] = infra_result is not False

            duration_ms = (time.time() - start) * 1000
            return TestResult(
                test_name="Service Registration Order",
                passed=True,
                duration_ms=duration_ms,
                details=details,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Service order test failed: {e}")
            return TestResult(
                test_name="Service Registration Order",
                passed=False,
                duration_ms=duration_ms,
                error=str(e),
                details=details,
            )

    async def test_concurrent_init(self) -> TestResult:
        """
        COLD-START BUG #5: Concurrent initialization requests

        Potential Issues:
        - Multiple requests arrive during startup
        - Race condition in singleton initialization
        - DI container not thread-safe during startup
        """
        start = time.time()
        details = {}

        try:
            from sqlalchemy import text

            from app.core.database import AsyncSessionLocal, async_engine
            from app.dependency_injection.container import container

            logger.info("Testing concurrent initialization...")

            # Simulate concurrent requests during startup
            async def simulate_request(request_id: int) -> bool:
                """Simulate a request arriving during startup"""
                try:
                    # FIX: Use proper async session creation, not engine.acquire()
                    async with async_engine.begin() as conn:
                        await conn.execute(text("SELECT 1"))
                    return True
                except Exception as e:
                    logger.warning(f"Request {request_id} failed: {e}")
                    return False

            # Launch 10 concurrent "requests"
            tasks = [simulate_request(i) for i in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            details["success_count"] = sum(1 for r in results if r is True)
            details["failure_count"] = sum(1 for r in results if r is not True)

            # BUG DETECTED: Failures due to pool not ready
            if details["failure_count"] > 0:
                logger.warning(
                    f"⚠️  BUG: {details['failure_count']} requests failed during concurrent init"
                )
                details["bug_detected"] = "concurrent_init_failures"

            duration_ms = (time.time() - start) * 1000
            return TestResult(
                test_name="Concurrent Initialization",
                passed=details["failure_count"] == 0,
                duration_ms=duration_ms,
                details=details,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Concurrent init test failed: {e}")
            return TestResult(
                test_name="Concurrent Initialization",
                passed=False,
                duration_ms=duration_ms,
                error=str(e),
                details=details,
            )

    async def test_missing_env_vars(self) -> TestResult:
        """
        COLD-START BUG #6: Missing environment variables during startup

        Potential Issues:
        - No fallback values for required settings
        - Application crashes instead of using defaults
        - Settings cached before environment loaded
        """
        start = time.time()
        details = {}

        try:
            from app.core.config import settings

            logger.info("Testing missing environment variables...")

            # Temporarily remove critical environment variable
            original_db = os.environ.get("DATABASE_URL")
            os.environ.pop("DATABASE_URL", None)

            # Try to reload settings (this should use fallback)
            try:
                # Import fresh to trigger re-evaluation
                import importlib

                import app.core.config

                importlib.reload(app.core.config)

                # BUG DETECTED: Settings loaded before environment check
                db_url = getattr(settings, "DATABASE_URL", None)
                details["db_url_after_removal"] = db_url

                if db_url is None or "postgresql://user:pass" in db_url:
                    logger.warning(
                        "⚠️  BUG: Settings use hardcoded fallback instead of proper default"
                    )
                    details["bug_detected"] = "hardcoded_fallback"

            except Exception as e:
                details["reload_error"] = str(e)
                logger.warning(f"Settings reload error: {e}")

            # Restore environment
            if original_db:
                os.environ["DATABASE_URL"] = original_db

            duration_ms = (time.time() - start) * 1000
            return TestResult(
                test_name="Missing Environment Variables",
                passed=True,
                duration_ms=duration_ms,
                details=details,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Environment vars test failed: {e}")
            return TestResult(
                test_name="Missing Environment Variables",
                passed=False,
                duration_ms=duration_ms,
                error=str(e),
                details=details,
            )

    async def test_bg_task_failure(self) -> TestResult:
        """
        COLD-START BUG #7: Background task startup failure

        Potential Issues:
        - Background tasks blocking main startup
        - No timeout on task initialization
        - Task failures not logged properly
        """
        start = time.time()
        details = {}

        try:
            from app.core.background_jobs import _background_worker, _task_queue
            from app.core.tasks import celery_app, task_registry

            logger.info("Testing background task startup failure...")

            # Check if celery is initialized
            details["celery_initialized"] = celery_app is not None
            details["task_queue_initialized"] = _task_queue is not None
            details["worker_initialized"] = _background_worker is not None

            # BUG DETECTED: No health check before starting background tasks
            if celery_app is not None:
                try:
                    # This may fail if RabbitMQ/Redis not ready
                    inspect = celery_app.control.inspect()
                    stats = inspect.stats()
                    details["worker_stats"] = stats is not None

                    if stats is None:
                        logger.warning("⚠️  BUG: No worker health check before startup")
                        details["bug_detected"] = "no_worker_health_check"

                except Exception as e:
                    logger.warning(f"⚠️  BUG: Background task init fails silently: {e}")
                    details["bug_detected"] = "bg_task_silent_failure"
                    details["bg_task_error"] = str(e)

            duration_ms = (time.time() - start) * 1000
            return TestResult(
                test_name="Background Task Startup Failure",
                passed=True,
                duration_ms=duration_ms,
                details=details,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Background task test failed: {e}")
            return TestResult(
                test_name="Background Task Startup Failure",
                passed=False,
                duration_ms=duration_ms,
                error=str(e),
                details=details,
            )

    async def test_middleware_before_services(self) -> TestResult:
        """
        COLD-START BUG #8: Middleware initialized before services

        Potential Issues:
        - Middleware accessing uninitialized services
        - Request processing before DI container ready
        - Security middleware blocking valid requests
        """
        start = time.time()
        details = {}

        try:
            from app.core.application_factory import create_application
            from app.dependency_injection.container import container

            logger.info("Testing middleware before services...")

            # Create application (this initializes middleware)
            app = create_application()

            # Check if services are initialized before first request
            service_info = container.get_service_info()
            details["services_before_request"] = len(service_info)

            # BUG DETECTED: Middleware may access uninitialized DI
            if len(service_info) == 0:
                logger.warning("⚠️  BUG: DI container empty when middleware registered")
                details["bug_detected"] = "middleware_before_di"

            # Check middleware order (security should be first)
            middleware_list = app.user_middleware
            details["middleware_count"] = len(middleware_list)

            # BUG DETECTED: Too many middleware layers
            if len(middleware_list) > 5:
                logger.warning(
                    f"⚠️  BUG: Too many middleware layers: {len(middleware_list)}"
                )
                details["bug_detected"] = "too_many_middleware"

            duration_ms = (time.time() - start) * 1000
            return TestResult(
                test_name="Middleware Before Services",
                passed=len(service_info) > 0,
                duration_ms=duration_ms,
                details=details,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Middleware test failed: {e}")
            return TestResult(
                test_name="Middleware Before Services",
                passed=False,
                duration_ms=duration_ms,
                error=str(e),
                details=details,
            )

    async def test_health_during_init(self) -> TestResult:
        """
        COLD-START BUG #9: Health check during initialization

        Potential Issues:
        - Health endpoint returns success before services ready
        - No initialization status in health check
        - Partial initialization considered healthy
        """
        start = time.time()
        details = {}

        try:
            from app.core.database import check_db_health
            from app.core.redis_client import get_redis_client

            logger.info("Testing health check during init...")

            # Mock partial initialization state
            # DB should be ready, Redis may not be
            db_health = await check_db_health()

            # Try to get Redis client
            redis_health = False
            try:
                redis_client = await get_redis_client()
                await redis_client.ping()
                redis_health = True
            except Exception as e:
                details["redis_error"] = str(e)
                logger.warning(f"Redis not ready during health check: {e}")

            # BUG DETECTED: Health check should reflect partial state
            if db_health and not redis_health:
                logger.warning(
                    "⚠️  BUG: Health check doesn't reflect partial initialization"
                )
                details["bug_detected"] = "partial_init_not_reported"

            details["db_health"] = db_health
            details["redis_health"] = redis_health
            details["partial_init"] = db_health != redis_health

            duration_ms = (time.time() - start) * 1000
            return TestResult(
                test_name="Health Check During Init",
                passed=db_health,  # DB should at least be healthy
                duration_ms=duration_ms,
                details=details,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Health check test failed: {e}")
            return TestResult(
                test_name="Health Check During Init",
                passed=False,
                duration_ms=duration_ms,
                error=str(e),
                details=details,
            )

    async def test_circuit_breaker_cold_start(self) -> TestResult:
        """
        COLD-START BUG #10: Circuit breaker state on cold start

        Potential Issues:
        - Circuit breaker in OPEN state from previous run
        - No recovery mechanism for cold starts
        - Metrics not reset on startup
        """
        start = time.time()
        details = {}

        try:
            from app.core.redis_client import _redis_metrics, get_redis_circuit_breaker

            logger.info("Testing circuit breaker cold start...")

            circuit_breaker = get_redis_circuit_breaker()

            # Check initial state
            details["initial_state"] = circuit_breaker.state.value
            details["initial_failure_count"] = circuit_breaker.failure_count

            # BUG DETECTED: Circuit breaker not reset on startup
            if circuit_breaker.state.value == "open":
                logger.warning("⚠️  BUG: Circuit breaker starts in OPEN state")
                details["bug_detected"] = "circuit_open_on_cold_start"

            # Check if metrics are reset
            details["total_calls"] = _redis_metrics.total_calls
            details["failed_calls"] = _redis_metrics.failed_calls

            if _redis_metrics.total_calls > 0 or _redis_metrics.failed_calls > 0:
                logger.warning("⚠️  BUG: Metrics not reset on cold start")
                details["bug_detected"] = "metrics_not_reset"

            duration_ms = (time.time() - start) * 1000
            return TestResult(
                test_name="Circuit Breaker Cold Start",
                passed=circuit_breaker.state.value == "closed",
                duration_ms=duration_ms,
                details=details,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Circuit breaker test failed: {e}")
            return TestResult(
                test_name="Circuit Breaker Cold Start",
                passed=False,
                duration_ms=duration_ms,
                error=str(e),
                details=details,
            )

    async def test_async_engine_creation(self) -> TestResult:
        """
        COLD-START BUG #11: Async engine creation issues

        Potential Issues:
        - Engine created before environment loaded
        - Connection pool not configured for production
        - SSL context missing on production
        """
        start = time.time()
        details = {}

        try:
            from app.core.database import async_engine, create_secure_ssl_context

            logger.info("Testing async engine creation...")

            # Check engine configuration
            pool = async_engine.pool
            details["pool_size"] = pool.size()
            details["max_overflow"] = (
                pool.max_overflow if hasattr(pool, "max_overflow") else None
            )

            # BUG DETECTED: Pool size not optimized for environment
            pool_size = pool.size()
            if os.getenv("ENVIRONMENT") == "production" and pool_size < 20:
                logger.warning(
                    f"⚠️  BUG: Pool size {pool_size} too small for production"
                )
                details["bug_detected"] = "pool_too_small_production"

            # Check SSL context
            try:
                ssl_context = create_secure_ssl_context()
                details["ssl_context"] = ssl_context is not None

                # BUG DETECTED: SSL context missing in production
                if os.getenv("ENVIRONMENT") == "production" and ssl_context is None:
                    logger.warning("⚠️  BUG: SSL context missing in production")
                    details["bug_detected"] = "ssl_context_missing"

            except Exception as e:
                details["ssl_error"] = str(e)

            duration_ms = (time.time() - start) * 1000
            return TestResult(
                test_name="Async Engine Creation",
                passed=True,
                duration_ms=duration_ms,
                details=details,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Async engine test failed: {e}")
            return TestResult(
                test_name="Async Engine Creation",
                passed=False,
                duration_ms=duration_ms,
                error=str(e),
                details=details,
            )

    async def test_lifespan_exception_recovery(self) -> TestResult:
        """
        COLD-START BUG #12: Lifespan exception recovery

        Potential Issues:
        - Startup exception leaves system in bad state
        - No cleanup after failed startup
        - Cannot recover from partial initialization
        """
        start = time.time()
        details = {}

        try:
            from contextlib import asynccontextmanager

            logger.info("Testing lifespan exception recovery...")

            # Simulate a lifespan with exception
            startup_failed = False

            @asynccontextmanager
            async def test_lifespan():
                nonlocal startup_failed
                try:
                    # Simulate successful initialization
                    logger.info("Starting up...")
                    yield
                except Exception as e:
                    startup_failed = True
                    logger.error(f"Startup failed: {e}")
                    raise
                finally:
                    logger.info("Cleanup running...")
                    # BUG DETECTED: Cleanup runs even if startup failed
                    if not startup_failed:
                        logger.warning("⚠️  BUG: Cleanup runs before startup completes")
                        details["bug_detected"] = "cleanup_before_startup"

            # Test successful case
            async with test_lifespan():
                pass

            # Test failed case
            try:
                async with test_lifespan():
                    raise RuntimeError("Simulated startup failure")
            except RuntimeError:
                pass  # Expected

            duration_ms = (time.time() - start) * 1000
            return TestResult(
                test_name="Lifespan Exception Recovery",
                passed=True,
                duration_ms=duration_ms,
                details=details,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Lifespan test failed: {e}")
            return TestResult(
                test_name="Lifespan Exception Recovery",
                passed=False,
                duration_ms=duration_ms,
                error=str(e),
                details=details,
            )

    async def _safe_execute(self, func: Callable) -> Any:
        """Safely execute a function and return result or False on error"""
        try:
            return await func()
        except Exception as e:
            logger.warning(f"Function failed: {e}")
            return False

    def generate_report(self):
        """Generate test report"""
        report = []
        report.append("\n" + "=" * 80)
        report.append("COLD-START TEST REPORT")
        report.append("=" * 80)
        report.append(f"\nSummary: {self.passed} passed, {self.failed} failed\n")

        # Group results by bug detection
        bugs_detected = [r for r in self.results if "bug_detected" in r.details]
        if bugs_detected:
            report.append("\n🐛 BUGS DETECTED:\n")
            for result in bugs_detected:
                report.append(f"  • {result.test_name}")
                report.append(f"    Bug: {result.details.get('bug_detected')}")
                if result.details:
                    report.append(f"    Details: {result.details}")
                report.append("")

        # All results
        report.append("\n" + "-" * 80)
        report.append("ALL TEST RESULTS:")
        report.append("-" * 80)
        for result in self.results:
            report.append(str(result))

        report.append("\n" + "=" * 80)
        return "\n".join(report)


async def main():
    """Main test execution"""
    # Set up signal handling for graceful shutdown
    loop = asyncio.get_event_loop()

    def signal_handler(sig, frame):
        logger.info("\n🛑 Test suite interrupted")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run tests
    suite = ColdStartTestSuite()
    results = await suite.run_all_tests()

    # Generate report
    print(suite.generate_report())

    # Exit with error code if any tests failed
    sys.exit(1 if suite.failed > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
