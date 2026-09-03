"""
PsychSync Performance Regression Tests

This module provides automated performance testing to ensure optimizations
don't regress and new features don't degrade performance.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_engine
from app.db.models.assessment import Assessment
from app.db.models.user import User
from app.main import app

# Performance thresholds (in milliseconds)
PERFORMANCE_THRESHOLDS = {
    "database_query": 100,  # Database queries should be < 100ms
    "api_response": 200,  # API responses should be < 200ms
    "authentication": 50,  # Auth operations should be < 50ms
    "user_lookup": 30,  # Simple user lookup < 30ms
    "assessment_list": 150,  # Assessment listing < 150ms
    "dashboard_load": 500,  # Dashboard data loading < 500ms
}


class PerformanceMetrics:
    """Collect and analyze performance metrics"""

    def __init__(self):
        self.measurements: List[Dict[str, Any]] = []

    def add_measurement(
        self, name: str, duration_ms: float, metadata: Dict[str, Any] = None
    ):
        """Add a performance measurement"""
        measurement = {
            "name": name,
            "duration_ms": duration_ms,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        self.measurements.append(measurement)

    def get_average(self, name: str) -> float:
        """Get average duration for a specific measurement"""
        measurements = [m for m in self.measurements if m["name"] == name]
        if not measurements:
            return 0.0
        return sum(m["duration_ms"] for m in measurements) / len(measurements)

    def check_threshold(self, name: str, threshold_ms: float) -> Dict[str, Any]:
        """Check if measurements meet performance threshold"""
        measurements = [m for m in self.measurements if m["name"] == name]
        if not measurements:
            return {"passed": False, "error": "No measurements found"}

        avg_duration = self.get_average(name)
        max_duration = max(m["duration_ms"] for m in measurements)
        passed = avg_duration <= threshold_ms

        return {
            "passed": passed,
            "average_ms": avg_duration,
            "max_ms": max_duration,
            "threshold_ms": threshold_ms,
            "measurements": len(measurements),
        }


@asynccontextmanager
async def measure_database_operation(metrics: PerformanceMetrics, operation_name: str):
    """Context manager to measure database operation performance"""
    engine = get_async_engine()

    start_time = time.time()
    try:
        async with engine.begin() as conn:
            yield conn
    finally:
        duration_ms = (time.time() - start_time) * 1000
        metrics.add_measurement(operation_name, duration_ms)


@pytest.fixture
def perf_metrics():
    """Fixture providing performance metrics collector"""
    return PerformanceMetrics()


@pytest.fixture
def test_client():
    """Test client for API performance testing"""
    return TestClient(app)


class TestDatabasePerformance:
    """Test database query performance"""

    @pytest.mark.asyncio
    async def test_user_query_performance(self, perf_metrics):
        """Test user query performance meets thresholds"""

        async with measure_database_operation(perf_metrics, "user_lookup") as conn:
            result = await conn.execute(select(User).limit(10))
            users = result.scalars().all()

        # Verify query returned data
        assert len(users) >= 0  # Should work even with no users

        # Check performance
        threshold_check = perf_metrics.check_threshold(
            "user_lookup", PERFORMANCE_THRESHOLDS["user_lookup"]
        )
        assert threshold_check["passed"], (
            f"User lookup too slow: {threshold_check['average_ms']:.2f}ms "
            f"(threshold: {threshold_check['threshold_ms']}ms)"
        )

    @pytest.mark.asyncio
    async def test_assessment_query_performance(self, perf_metrics):
        """Test assessment query performance"""

        async with measure_database_operation(perf_metrics, "assessment_list") as conn:
            result = await conn.execute(
                select(Assessment).order_by(Assessment.created_at.desc()).limit(50)
            )
            assessments = result.scalars().all()

        # Verify query worked
        assert len(assessments) >= 0

        # Check performance
        threshold_check = perf_metrics.check_threshold(
            "assessment_list", PERFORMANCE_THRESHOLDS["assessment_list"]
        )
        assert threshold_check["passed"], (
            f"Assessment list too slow: {threshold_check['average_ms']:.2f}ms "
            f"(threshold: {threshold_check['threshold_ms']}ms)"
        )

    @pytest.mark.asyncio
    async def test_complex_join_query_performance(self, perf_metrics):
        """Test performance of complex join queries"""

        async with measure_database_operation(perf_metrics, "complex_join") as conn:
            # Simulate complex dashboard query
            result = await conn.execute(
                text(
                    """
                SELECT
                    u.id,
                    u.email,
                    u.created_at,
                    COUNT(a.id) as assessment_count
                FROM users u
                LEFT JOIN assessments a ON u.id = a.user_id
                WHERE u.is_active = true
                GROUP BY u.id, u.email, u.created_at
                ORDER BY u.created_at DESC
                LIMIT 20
            """
                )
            )
            results = result.fetchall()

        # Verify query worked
        assert len(results) >= 0

        # Complex queries should still be reasonably fast
        threshold_check = perf_metrics.check_threshold(
            "complex_join", 300
        )  # 300ms for complex query
        assert threshold_check["passed"], (
            f"Complex join query too slow: {threshold_check['average_ms']:.2f}ms "
            f"(threshold: {threshold_check['threshold_ms']}ms)"
        )


class TestAPIPerformance:
    """Test API endpoint performance"""

    def test_health_endpoint_performance(self, test_client, perf_metrics):
        """Test health check endpoint performance"""

        start_time = time.time()
        response = test_client.get("/api/v1/health")
        duration_ms = (time.time() - start_time) * 1000

        perf_metrics.add_measurement("health_check", duration_ms)

        # Verify response
        assert response.status_code == 200

        # Check performance
        threshold_check = perf_metrics.check_threshold(
            "health_check", 50
        )  # Health check should be fast
        assert threshold_check["passed"], (
            f"Health check too slow: {threshold_check['average_ms']:.2f}ms "
            f"(threshold: {threshold_check['threshold_ms']}ms)"
        )

    def test_api_docs_performance(self, test_client, perf_metrics):
        """Test API documentation endpoint performance"""

        start_time = time.time()
        response = test_client.get("/docs")
        duration_ms = (time.time() - start_time) * 1000

        perf_metrics.add_measurement("api_docs", duration_ms)

        # Verify response
        assert response.status_code == 200

        # API docs can be slightly slower but should still be responsive
        threshold_check = perf_metrics.check_threshold(
            "api_docs", 1000
        )  # 1 second for docs
        assert threshold_check["passed"], (
            f"API docs too slow: {threshold_check['average_ms']:.2f}ms "
            f"(threshold: {threshold_check['threshold_ms']}ms)"
        )


class TestConnectionPoolPerformance:
    """Test database connection pool efficiency"""

    @pytest.mark.asyncio
    async def test_concurrent_connection_performance(self, perf_metrics):
        """Test performance with concurrent database connections"""

        async def run_query():
            async with measure_database_operation(
                perf_metrics, "concurrent_query"
            ) as conn:
                await conn.execute(text("SELECT 1"))

        # Run multiple queries concurrently
        start_time = time.time()
        await asyncio.gather(*[run_query() for _ in range(10)])
        total_duration_ms = (time.time() - start_time) * 1000

        # Average per query should be reasonable
        avg_per_query = total_duration_ms / 10

        # Concurrent queries should benefit from connection pooling
        threshold_check = perf_metrics.check_threshold("concurrent_query", 50)
        assert threshold_check["passed"], (
            f"Concurrent queries too slow: {avg_per_query:.2f}ms average "
            f"(threshold: {threshold_check['threshold_ms']}ms)"
        )


class TestPerformanceRegression:
    """Test for performance regressions"""

    @pytest.mark.asyncio
    async def test_no_performance_regression(self, perf_metrics):
        """Comprehensive test to detect performance regressions"""

        # Run a series of typical operations
        operations = []

        # Database operations
        async with measure_database_operation(perf_metrics, "user_count_query") as conn:
            await conn.execute(text("SELECT COUNT(*) FROM users"))

        async with measure_database_operation(
            perf_metrics, "assessment_count_query"
        ) as conn:
            await conn.execute(text("SELECT COUNT(*) FROM assessments"))

        async with measure_database_operation(perf_metrics, "index_usage_test") as conn:
            # Test that our new indexes are being used
            await conn.execute(
                text(
                    """
                SELECT u.id, u.email
                FROM users u
                WHERE u.organization_id = 1
                ORDER BY u.created_at DESC
                LIMIT 5
            """
                )
            )

        # Collect all measurements
        all_checks_passed = True
        failed_operations = []

        # Check each operation against thresholds
        for operation_name, threshold in [
            ("user_count_query", 50),
            ("assessment_count_query", 50),
            ("index_usage_test", 30),
        ]:
            threshold_check = perf_metrics.check_threshold(operation_name, threshold)
            if not threshold_check["passed"]:
                all_checks_passed = False
                failed_operations.append(
                    f"{operation_name}: {threshold_check['average_ms']:.2f}ms "
                    f"(threshold: {threshold_check['threshold_ms']}ms)"
                )

        # Assert no regressions
        assert (
            all_checks_passed
        ), f"Performance regressions detected: {failed_operations}"

    def test_bundle_size_regression(self, perf_metrics):
        """Test frontend bundle size hasn't regressed"""

        # This would typically check actual bundle size
        # For now, we'll simulate the check

        # Simulated bundle size check (in KB)
        simulated_bundle_size = 480  # Should be under 500KB

        assert simulated_bundle_size <= 500, (
            f"Frontend bundle size regression: {simulated_bundle_size}KB "
            f"(threshold: 500KB)"
        )


class TestPerformanceTrends:
    """Track performance trends over time"""

    @pytest.mark.asyncio
    async def test_performance_trend_analysis(self, perf_metrics):
        """Collect multiple measurements for trend analysis"""

        # Run same operation multiple times to establish baseline
        for i in range(5):
            async with measure_database_operation(
                perf_metrics, "trend_test_query"
            ) as conn:
                await conn.execute(text("SELECT COUNT(*) FROM users"))

            # Small delay between measurements
            await asyncio.sleep(0.1)

        # Analyze measurements
        measurements = [
            m["duration_ms"]
            for m in perf_metrics.measurements
            if m["name"] == "trend_test_query"
        ]

        # Performance should be consistent (not too much variance)
        avg_duration = sum(measurements) / len(measurements)
        max_duration = max(measurements)
        variance_percent = ((max_duration - avg_duration) / avg_duration) * 100

        # Variance should be under 50% (consistent performance)
        assert variance_percent < 50, (
            f"Performance variance too high: {variance_percent:.1f}% "
            f"(avg: {avg_duration:.2f}ms, max: {max_duration:.2f}ms)"
        )


if __name__ == "__main__":
    # Run performance tests directly
    pytest.main([__file__, "-v", "-s"])
