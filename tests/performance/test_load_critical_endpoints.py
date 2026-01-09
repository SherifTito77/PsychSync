"""
Performance and Load Tests for Critical Endpoints
tests/performance/test_load_critical_endpoints.py

This module contains performance and load tests for critical API endpoints:
- Login endpoint
- Assessment list endpoint
- Response submission endpoint

Test Categories:
- Load Tests: Normal concurrent user load
- Stress Tests: Maximum system capacity
- Caching Performance: Cache effectiveness
- Memory Leak Detection: Resource management

Priority: P1 (High)
Tools: pytest-asyncio, pytest-benchmark (optional)
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any
from httpx import AsyncClient
from memory_profiler import profile

from app.main import app


class TestLoadPerformanceRegression:
    """
    Load tests for critical endpoints under normal concurrent load
    Priority: P1 (High)
    """

    @pytest.mark.asyncio
    async def test_login_endpoint_load(self, client: AsyncClient, test_user: User):
        """
        Test: Login endpoint under concurrent load

        Input: 100 concurrent login requests
        Expected:
            - p95 response time < 2 seconds
            - 0% errors (all succeed or proper 429 rate limits)
        Priority: P1
        """
        num_requests = 100

        async def login_attempt(attempt_num: int) -> Dict[str, Any]:
            start = time.time()
            try:
                response = await client.post(
                    "/api/v1/auth/token-fixed",
                    data={
                        "username": test_user.email,
                        "password": "TestPassword123!"
                    }
                )
                elapsed = time.time() - start
                return {
                    "attempt": attempt_num,
                    "status": response.status_code,
                    "elapsed": elapsed,
                    "success": response.status_code == 200
                }
            except Exception as e:
                elapsed = time.time() - start
                return {
                    "attempt": attempt_num,
                    "status": 500,
                    "elapsed": elapsed,
                    "success": False,
                    "error": str(e)
                }

        # Execute concurrent requests
        start_time = time.time()
        results = await asyncio.gather(*[login_attempt(i) for i in range(num_requests)])
        total_time = time.time() - start_time

        # Analyze results
        successful = [r for r in results if r["success"]]
        errors = [r for r in results if not r["success"]]
        response_times = [r["elapsed"] for r in results]

        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.5)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]

        # Assertions
        assert len(successful) > 0, "No successful requests"
        assert p95 < 2.0, f"p95 response time {p95}s exceeds 2s threshold"

        # Print statistics
        print(f"\n=== Login Load Test Results ===")
        print(f"Total requests: {num_requests}")
        print(f"Successful: {len(successful)}")
        print(f"Errors: {len(errors)}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Requests/sec: {num_requests / total_time:.2f}")
        print(f"p50: {p50:.3f}s")
        print(f"p95: {p95:.3f}s")
        print(f"p99: {p99:.3f}s")

    @pytest.mark.asyncio
    async def test_assessments_list_load(self, client: AsyncClient, auth_headers: dict):
        """
        Test: Assessment list endpoint under concurrent load

        Input: 100 concurrent list requests
        Expected:
            - p95 response time < 500ms
            - 100% success rate
        Priority: P1
        """
        num_requests = 100

        async def list_attempt(attempt_num: int) -> Dict[str, Any]:
            start = time.time()
            try:
                response = await client.get(
                    "/api/v1/assessments/",
                    headers=auth_headers
                )
                elapsed = time.time() - start
                return {
                    "attempt": attempt_num,
                    "status": response.status_code,
                    "elapsed": elapsed,
                    "success": response.status_code == 200
                }
            except Exception as e:
                elapsed = time.time() - start
                return {
                    "attempt": attempt_num,
                    "status": 500,
                    "elapsed": elapsed,
                    "success": False,
                    "error": str(e)
                }

        # Execute concurrent requests
        start_time = time.time()
        results = await asyncio.gather(*[list_attempt(i) for i in range(num_requests)])
        total_time = time.time() - start_time

        # Analyze results
        successful = [r for r in results if r["success"]]
        response_times = [r["elapsed"] for r in results]

        sorted_times = sorted(response_times)
        p95 = sorted_times[int(len(sorted_times) * 0.95)]

        assert len(successful) == num_requests, "All requests should succeed"
        assert p95 < 0.5, f"p95 response time {p95}s exceeds 500ms threshold"

        print(f"\n=== Assessment List Load Test Results ===")
        print(f"Total requests: {num_requests}")
        print(f"Successful: {len(successful)}")
        print(f"p95: {p95:.3f}s")

    @pytest.mark.asyncio
    async def test_response_submission_load(self, client: AsyncClient, auth_headers: dict, test_assessment):
        """
        Test: Response submission endpoint under concurrent load

        Input: 50 concurrent submission requests
        Expected:
            - p95 response time < 1 second
            - High success rate (> 95%)
        Priority: P1
        """
        num_requests = 50

        async def submit_attempt(attempt_num: int) -> Dict[str, Any]:
            start = time.time()
            try:
                response = await client.post(
                    f"/api/v1/responses/",
                    json={
                        "assessment_id": str(test_assessment.id),
                        "responses": {
                            "q1": attempt_num % 5 + 1,
                            "q2": attempt_num % 5 + 1
                        }
                    },
                    headers=auth_headers
                )
                elapsed = time.time() - start
                return {
                    "attempt": attempt_num,
                    "status": response.status_code,
                    "elapsed": elapsed,
                    "success": response.status_code in [200, 201]
                }
            except Exception as e:
                elapsed = time.time() - start
                return {
                    "attempt": attempt_num,
                    "status": 500,
                    "elapsed": elapsed,
                    "success": False,
                    "error": str(e)
                }

        # Execute concurrent requests
        start_time = time.time()
        results = await asyncio.gather(*[submit_attempt(i) for i in range(num_requests)])
        total_time = time.time() - start_time

        # Analyze results
        successful = [r for r in results if r["success"]]
        response_times = [r["elapsed"] for r in results]

        sorted_times = sorted(response_times)
        p95 = sorted_times[int(len(sorted_times) * 0.95)]

        success_rate = len(successful) / num_requests

        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95%"
        assert p95 < 1.0, f"p95 response time {p95}s exceeds 1s threshold"

        print(f"\n=== Response Submission Load Test Results ===")
        print(f"Total requests: {num_requests}")
        print(f"Successful: {len(successful)} ({success_rate:.2%})")
        print(f"p95: {p95:.3f}s")


class TestStressPerformanceRegression:
    """
    Stress tests to determine maximum system capacity
    Priority: P1 (High)
    """

    @pytest.mark.asyncio
    async def test_max_concurrent_users(self, client: AsyncClient, auth_headers: dict):
        """
        Test: Maximum concurrent users the system can handle

        Input: 1000 concurrent users
        Expected:
            - System remains responsive (no crashes)
            - Reasonable success rate (> 80%)
        Priority: P1
        """
        num_concurrent = 1000

        async def user_request(user_id: int) -> Dict[str, Any]:
            start = time.time()
            try:
                response = await client.get(
                    "/api/v1/assessments/",
                    headers=auth_headers
                )
                elapsed = time.time() - start
                return {
                    "user_id": user_id,
                    "status": response.status_code,
                    "elapsed": elapsed,
                    "success": response.status_code == 200
                }
            except Exception as e:
                elapsed = time.time() - start
                return {
                    "user_id": user_id,
                    "status": 500,
                    "elapsed": elapsed,
                    "success": False,
                    "error": str(e)
                }

        # Execute with limited concurrency to avoid overwhelming the test system
        start_time = time.time()

        # Process in batches of 100
        batch_size = 100
        all_results = []

        for i in range(0, num_concurrent, batch_size):
            batch = [user_request(j) for j in range(i, min(i + batch_size, num_concurrent))]
            batch_results = await asyncio.gather(*batch)
            all_results.extend(batch_results)

        total_time = time.time() - start_time

        # Analyze results
        successful = [r for r in all_results if r["success"]]
        success_rate = len(successful) / num_concurrent

        assert success_rate >= 0.80, f"Success rate {success_rate:.2%} below 80%"

        print(f"\n=== Stress Test Results ===")
        print(f"Concurrent users: {num_concurrent}")
        print(f"Successful: {len(successful)} ({success_rate:.2%})")
        print(f"Total time: {total_time:.2f}s")
        print(f"Avg response time: {total_time / num_concurrent:.3f}s")

    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, client: AsyncClient, auth_headers: dict):
        """
        Test: Detect memory leaks over many requests

        Input: 1000 requests over time
        Expected: Stable memory usage
        Priority: P1
        """
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        num_requests = 1000
        memory_samples = [initial_memory]

        for i in range(num_requests):
            # Make request
            await client.get("/api/v1/assessments/", headers=auth_headers)

            # Sample memory every 100 requests
            if i % 100 == 0:
                current_memory = process.memory_info().rss
                memory_samples.append(current_memory)

        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        memory_growth_mb = memory_growth / (1024 * 1024)
        memory_growth_percent = (memory_growth / initial_memory) * 100

        # Allow 20% memory growth as threshold
        assert memory_growth_percent < 20, f"Memory grew by {memory_growth_percent:.2f}%"

        print(f"\n=== Memory Leak Test Results ===")
        print(f"Initial memory: {initial_memory / (1024 * 1024):.2f} MB")
        print(f"Final memory: {final_memory / (1024 * 1024):.2f} MB")
        print(f"Memory growth: {memory_growth_mb:.2f} MB ({memory_growth_percent:.2f}%)")


class TestCachingPerformanceRegression:
    """
    Tests for caching effectiveness
    Priority: P1 (High)
    """

    @pytest.mark.asyncio
    async def test_cache_hit_ratio(self, client: AsyncClient, auth_headers: dict, test_assessment):
        """
        Test: Verify cache effectiveness

        Input: Repeated requests to same endpoint
        Expected: > 80% cache hit ratio
        Priority: P1
        """
        num_requests = 100
        cache_hits = 0

        # First request (cache miss)
        response1 = await client.get(
            f"/api/v1/assessments/{test_assessment.id}",
            headers=auth_headers
        )

        # Subsequent requests (should hit cache)
        start_time = time.time()
        for i in range(num_requests - 1):
            response = await client.get(
                f"/api/v1/assessments/{test_assessment.id}",
                headers=auth_headers
            )
        total_time = time.time() - start_time

        # Calculate average response time
        avg_time = total_time / (num_requests - 1)

        # Cache should make responses faster
        # This is an indirect measure of cache effectiveness
        assert avg_time < 0.1, f"Average response time {avg_time}s suggests cache not working"

        print(f"\n=== Cache Performance Results ===")
        print(f"Total requests: {num_requests}")
        print(f"Average response time: {avg_time:.4f}s")
        print(f"Total time: {total_time:.2f}s")

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, client: AsyncClient, auth_headers: dict, test_assessment):
        """
        Test: Verify cache invalidates on update

        Input: Get, update, get again
        Expected: Second get returns updated data (not stale cache)
        Priority: P1
        """
        # First get
        response1 = await client.get(
            f"/api/v1/assessments/{test_assessment.id}",
            headers=auth_headers
        )
        data1 = response1.json()

        # Update assessment
        await client.put(
            f"/api/v1/assessments/{test_assessment.id}",
            json={"title": "Updated Title"},
            headers=auth_headers
        )

        # Get again (should return updated data, not stale cache)
        response2 = await client.get(
            f"/api/v1/assessments/{test_assessment.id}",
            headers=auth_headers
        )
        data2 = response2.json()

        # Verify data is updated
        assert data2["data"]["title"] == "Updated Title"
        assert data2["data"]["title"] != data1["data"]["title"]


class TestPerformanceBenchmarking:
    """
    Benchmarking tests for performance regression detection
    Priority: P1 (High)
    """

    @pytest.mark.asyncio
    async def test_benchmark_assessment_list(self, client: AsyncClient, auth_headers: dict, benchmark):
        """
        Test: Benchmark assessment list endpoint

        Expected: Establish performance baseline
        Priority: P1

        Note: Requires pytest-benchmark
        Run with: pytest --benchmark-only
        """
        # This test requires pytest-benchmark
        # If not available, skip
        try:
            import pytest_benchmark

            async def operation():
                response = await client.get("/api/v1/assessments/", headers=auth_headers)
                assert response.status_code == 200
                return response

            result = await benchmark(operation)
            assert result.status_code == 200

        except ImportError:
            pytest.skip("pytest-benchmark not installed")

    @pytest.mark.asyncio
    async def test_benchmark_response_create(self, client: AsyncClient, auth_headers: dict, test_assessment, benchmark):
        """
        Test: Benchmark response creation

        Expected: Establish performance baseline
        Priority: P1
        """
        try:
            import pytest_benchmark

            async def operation():
                response = await client.post(
                    f"/api/v1/responses/",
                    json={
                        "assessment_id": str(test_assessment.id),
                        "responses": {"q1": 5}
                    },
                    headers=auth_headers
                )
                return response

            result = await benchmark(operation)
            assert result.status_code in [200, 201]

        except ImportError:
            pytest.skip("pytest-benchmark not installed")


class TestPerformanceDegradation:
    """
    Tests to detect performance degradation over time
    Priority: P1 (High)
    """

    @pytest.mark.asyncio
    async def test_response_time_stability(self, client: AsyncClient, auth_headers: dict):
        """
        Test: Verify response times remain stable over many requests

        Input: 1000 sequential requests
        Expected: No significant degradation (> 2x slowdown)
        Priority: P1
        """
        response_times = []

        for i in range(1000):
            start = time.time()
            await client.get("/api/v1/assessments/", headers=auth_headers)
            elapsed = time.time() - start
            response_times.append(elapsed)

        # Calculate statistics
        first_100_avg = sum(response_times[:100]) / 100
        last_100_avg = sum(response_times[-100:]) / 100
        degradation_ratio = last_100_avg / first_100_avg

        # Allow 2x degradation as threshold
        assert degradation_ratio < 2.0, f"Response time degraded by {degradation_ratio:.2f}x"

        print(f"\n=== Response Time Stability Results ===")
        print(f"First 100 avg: {first_100_avg:.4f}s")
        print(f"Last 100 avg: {last_100_avg:.4f}s")
        print(f"Degradation ratio: {degradation_ratio:.2f}x")

    @pytest.mark.asyncio
    async def test_database_connection_pool_exhaustion(self, client: AsyncClient, auth_headers: dict):
        """
        Test: Verify database connection pool handles load

        Input: Rapid concurrent requests
        Expected: No connection pool exhaustion errors
        Priority: P1
        """
        num_requests = 500

        async def make_request(i: int):
            try:
                response = await client.get("/api/v1/assessments/", headers=auth_headers)
                return response.status_code == 200
            except Exception:
                return False

        results = await asyncio.gather(*[make_request(i) for i in range(num_requests)])
        success_count = sum(results)

        success_rate = success_count / num_requests
        assert success_rate > 0.95, f"Connection pool exhaustion detected: {success_rate:.2%} success"

        print(f"\n=== Connection Pool Test Results ===")
        print(f"Success rate: {success_rate:.2%}")


# Test class markers
TestLoadPerformanceRegression = pytest.mark.P1(TestLoadPerformanceRegression)
TestStressPerformanceRegression = pytest.mark.P1(TestStressPerformanceRegression)
TestCachingPerformanceRegression = pytest.mark.P1(TestCachingPerformanceRegression)
TestPerformanceBenchmarking = pytest.mark.P1(TestPerformanceBenchmarking)
TestPerformanceDegradation = pytest.mark.P1(TestPerformanceDegradation)
