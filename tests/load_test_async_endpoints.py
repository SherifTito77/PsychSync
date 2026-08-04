#!/usr/bin/env python3
"""
Load testing script for async endpoints
Tests performance under concurrent load to verify no blocking occurs
"""
import asyncio
import statistics
import time
from dataclasses import dataclass
from typing import Any, Dict, List
from uuid import uuid4

import httpx


@dataclass
class LoadTestResult:
    """Results from a load test"""

    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    median_response_time: float
    p95_response_time: float
    requests_per_second: float


class AsyncLoadTester:
    """Load tester for async endpoints"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[LoadTestResult] = []

    async def test_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        concurrent_users: int = 50,
        total_requests: int = 100,
        json_data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> LoadTestResult:
        """
        Load test an endpoint with concurrent requests

        Args:
            endpoint: API endpoint path
            method: HTTP method
            concurrent_users: Number of concurrent users
            total_requests: Total number of requests to make
            json_data: JSON data for POST requests
            headers: Request headers (auth tokens, etc.)

        Returns:
            LoadTestResult with performance metrics
        """
        url = f"{self.base_url}{endpoint}"
        response_times = []
        successful = 0
        failed = 0

        print(f"\n🧪 Testing: {method} {endpoint}")
        print(f"   Concurrent users: {concurrent_users}")
        print(f"   Total requests: {total_requests}")

        async def make_request(client: httpx.AsyncClient, request_num: int) -> float:
            """Make a single request and return response time"""
            nonlocal successful, failed

            try:
                start = time.time()

                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, json=json_data, headers=headers)
                elif method == "PUT":
                    response = await client.put(url, json=json_data, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                elapsed = time.time() - start

                if response.status_code < 500:
                    successful += 1
                else:
                    failed += 1

                return elapsed

            except Exception as e:
                failed += 1
                if request_num == 1:  # Only print first error
                    print(f"   ❌ Request failed: {e}")
                return 0.0

        async with httpx.AsyncClient(timeout=30.0) as client:
            start_time = time.time()

            # Create batches of concurrent requests
            batch_size = concurrent_users
            num_batches = (total_requests + batch_size - 1) // batch_size

            for batch_num in range(num_batches):
                requests_in_batch = min(
                    batch_size, total_requests - batch_num * batch_size
                )

                # Execute concurrent requests
                tasks = [
                    make_request(client, batch_num * batch_size + i + 1)
                    for i in range(requests_in_batch)
                ]

                batch_times = await asyncio.gather(*tasks)
                response_times.extend([t for t in batch_times if t > 0])

                # Small delay between batches
                if batch_num < num_batches - 1:
                    await asyncio.sleep(0.1)

            total_time = time.time() - start_time

        # Calculate statistics
        valid_times = [t for t in response_times if t > 0]

        if not valid_times:
            print(f"   ⚠️  No successful requests!")
            return LoadTestResult(
                endpoint=endpoint,
                total_requests=total_requests,
                successful_requests=0,
                failed_requests=total_requests,
                total_time=total_time,
                avg_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                median_response_time=0.0,
                p95_response_time=0.0,
                requests_per_second=0.0,
            )

        sorted_times = sorted(valid_times)
        result = LoadTestResult(
            endpoint=endpoint,
            total_requests=total_requests,
            successful_requests=successful,
            failed_requests=failed,
            total_time=total_time,
            avg_response_time=statistics.mean(sorted_times),
            min_response_time=min(sorted_times),
            max_response_time=max(sorted_times),
            median_response_time=statistics.median(sorted_times),
            p95_response_time=sorted_times[int(len(sorted_times) * 0.95)],
            requests_per_second=successful / total_time if total_time > 0 else 0,
        )

        self.results.append(result)

        # Print results
        print(f"   ✅ Successful: {result.successful_requests}")
        print(f"   ❌ Failed: {result.failed_requests}")
        print(f"   ⏱️  Avg response: {result.avg_response_time*1000:.1f}ms")
        print(f"   📊 Median: {result.median_response_time*1000:.1f}ms")
        print(f"   📈 P95: {result.p95_response_time*1000:.1f}ms")
        print(f"   🚀 RPS: {result.requests_per_second:.1f} req/s")

        return result

    async def run_all_tests(self) -> None:
        """Run comprehensive load tests on all modified endpoints"""
        print("\n" + "=" * 70)
        print("ASYNC ENDPOINT LOAD TESTING")
        print("=" * 70)

        # Test 1: Feature Request Endpoints
        print("\n📋 Testing Feature Request Endpoints...")

        await self.test_endpoint(
            "/api/v1/feature-requests/",
            method="GET",
            concurrent_users=20,
            total_requests=50,
        )

        # Test 2: Activation Endpoints
        print("\n📊 Testing Activation Endpoints...")

        await self.test_endpoint(
            "/api/v1/activation/my-activation",
            method="GET",
            concurrent_users=30,
            total_requests=60,
            headers={
                "Authorization": "Bearer test-token"
            },  # Will fail auth but tests async
        )

        # Test 3: Response Endpoints (with invalid UUID, will fail but tests async)
        print("\n💬 Testing Response Endpoints...")

        await self.test_endpoint(
            f"/api/v1/responses/{uuid4()}",
            method="GET",
            concurrent_users=25,
            total_requests=50,
        )

        # Test 4: Health Check (should always work)
        print("\n🏥 Testing Health Endpoints...")

        await self.test_endpoint(
            "/api/v1/health", method="GET", concurrent_users=50, total_requests=100
        )

        # Test 5: Monitoring Endpoints
        print("\n📈 Testing Monitoring Endpoints...")

        await self.test_endpoint(
            "/api/v1/monitoring/metrics",
            method="GET",
            concurrent_users=30,
            total_requests=60,
        )

        self.print_summary()

    def print_summary(self) -> None:
        """Print summary of all load tests"""
        print("\n" + "=" * 70)
        print("LOAD TEST SUMMARY")
        print("=" * 70)

        if not self.results:
            print("No results to display")
            return

        print(f"\n{'Endpoint':<40} {'RPS':<10} {'P95 (ms)':<12} {'Success Rate':<12}")
        print("-" * 74)

        for result in self.results:
            success_rate = (
                (result.successful_requests / result.total_requests * 100)
                if result.total_requests > 0
                else 0
            )
            endpoint_name = result.endpoint[:40]
            print(
                f"{endpoint_name:<40} {result.requests_per_second:<10.1f} {result.p95_response_time*1000:<12.1f} {success_rate:<12.1f}%"
            )

        # Performance checks
        print("\n" + "=" * 70)
        print("PERFORMANCE ANALYSIS")
        print("=" * 70)

        all_passed = True

        for result in self.results:
            issues = []

            # Check for blocking (if P95 is very high)
            if result.p95_response_time > 1.0:  # > 1 second
                issues.append(
                    f"⚠️  High P95: {result.p95_response_time*1000:.1f}ms (possible blocking)"
                )

            # Check success rate
            success_rate = (
                result.successful_requests / result.total_requests * 100
                if result.total_requests > 0
                else 0
            )
            if success_rate < 95:
                issues.append(f"❌ Low success rate: {success_rate:.1f}%")

            # Check RPS
            if result.requests_per_second < 10 and result.successful_requests > 0:
                issues.append(
                    f"⚠️  Low throughput: {result.requests_per_second:.1f} RPS"
                )

            if issues:
                all_passed = False
                print(f"\n{result.endpoint}:")
                for issue in issues:
                    print(f"  {issue}")

        if all_passed:
            print("\n✅ All endpoints passed performance checks!")
            print("   - No blocking operations detected")
            print("   - Response times within acceptable ranges")
            print("   - Good throughput under load")
        else:
            print("\n⚠️  Some endpoints may have performance issues")
            print("   Review the issues above")

        print("\n" + "=" * 70)


async def main():
    """Main entry point for load testing"""
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    print(f"\n🚀 Starting load tests against: {base_url}")
    print("   Make sure the server is running!")

    # Wait a moment for user to see the message
    await asyncio.sleep(1)

    tester = AsyncLoadTester(base_url=base_url)
    await tester.run_all_tests()

    print("\n✅ Load testing complete!")
    print("\nNext steps:")
    print("   1. Review the results above")
    print("   2. Check for any blocking operations (high P95 times)")
    print("   3. Verify success rates are > 95%")
    print("   4. Monitor server logs for errors")


if __name__ == "__main__":
    asyncio.run(main())
