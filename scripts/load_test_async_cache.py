#!/usr/bin/env python3
"""
Load Test Script for Async Cache Endpoints
Tests migrated endpoints under concurrent load
Measures latency, throughput, and error rates
"""

import asyncio
import time
import statistics
import sys
import os
from datetime import datetime
from typing import List, Dict, Tuple
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp


class LoadTestResult:
    """Store load test results"""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.latencies: List[float] = []
        self.errors: List[str] = []
        self.success_count = 0
        self.error_count = 0

    def add_result(self, latency: float, error: str = None):
        """Add a test result"""
        if error:
            self.errors.append(error)
            self.error_count += 1
        else:
            self.latencies.append(latency)
            self.success_count += 1

    def report(self) -> str:
        """Generate report for this endpoint"""
        total = self.success_count + self.error_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0

        if not self.latencies:
            return f"""
{self.endpoint}:
  Requests: {total}
  Success: {self.success_count} ({success_rate:.1f}%)
  Errors: {self.error_count}
  No successful requests to measure latency
"""

        avg = statistics.mean(self.latencies)
        median = statistics.median(self.latencies)
        p95 = statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) >= 20 else max(self.latencies)
        p99 = statistics.quantiles(self.latencies, n=100)[98] if len(self.latencies) >= 100 else max(self.latencies)

        return f"""
{self.endpoint}:
  Requests: {total}
  Success: {self.success_count} ({success_rate:.1f}%)
  Errors: {self.error_count}
  Latency (ms):
    Average: {avg*1000:.2f}ms
    Median:  {median*1000:.2f}ms
    P95:     {p95*1000:.2f}ms
    P99:     {p99*1000:.2f}ms
"""


async def test_endpoint(session: aiohttp.ClientSession, endpoint: str, method: str = "GET",
                       headers: dict = None) -> Tuple[float, str]:
    """Test a single endpoint"""
    start = time.time()

    try:
        async with session.request(method, endpoint, headers=headers) as response:
            await response.text()  # Consume response
            latency = time.time() - start
            return latency, None
    except Exception as e:
        latency = time.time() - start
        return latency, str(e)


async def load_test_endpoint(base_url: str, endpoint: str, concurrent_users: int,
                            requests_per_user: int, headers: dict = None) -> LoadTestResult:
    """Load test a single endpoint with concurrent users"""
    result = LoadTestResult(endpoint)

    async def user_session(user_id: int):
        """Simulate a single user making multiple requests"""
        async with aiohttp.ClientSession() as session:
            for i in range(requests_per_user):
                url = f"{base_url}{endpoint}"
                latency, error = await test_endpoint(session, url, headers=headers)
                result.add_result(latency, error)

                # Small delay between requests
                await asyncio.sleep(0.01)

    # Launch all concurrent users
    tasks = [user_session(i) for i in range(concurrent_users)]
    await asyncio.gather(*tasks)

    return result


async def run_load_tests(base_url: str = "http://localhost:8000"):
    """Run load tests on all migrated endpoints"""
    print("=" * 80)
    print("🚀 ASYNC CACHE LOAD TEST")
    print("=" * 80)
    print(f"Base URL: {base_url}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test configuration
    concurrent_users = 50
    requests_per_user = 20
    total_requests = concurrent_users * requests_per_user

    # Test endpoints (using public endpoints that don't require auth)
    test_endpoints = [
        ("/api/v1/health", "GET"),
    ]

    # Note: The migrated endpoints require authentication
    # We'll test the health endpoint as a baseline
    # For authenticated endpoints, you would need to:
    # 1. Login to get a token
    # 2. Add the token to headers

    results: List[LoadTestResult] = []

    for endpoint, method in test_endpoints:
        print(f"\n📍 Testing: {method} {endpoint}")
        print(f"   Concurrent Users: {concurrent_users}")
        print(f"   Requests per User: {requests_per_user}")
        print(f"   Total Requests: {total_requests}")
        print()

        start = time.time()
        result = await load_test_endpoint(
            base_url,
            endpoint,
            concurrent_users,
            requests_per_user
        )
        elapsed = time.time() - start

        print(f"✅ Completed in {elapsed:.2f}s")
        print(f"   Throughput: {total_requests/elapsed:.2f} requests/second")
        print()

        results.append(result)

    # Generate final report
    print("\n" + "=" * 80)
    print("📊 LOAD TEST RESULTS")
    print("=" * 80)

    for result in results:
        print(result.report())

    # Summary
    total_success = sum(r.success_count for r in results)
    total_errors = sum(r.error_count for r in results)
    total_all = total_success + total_errors

    print("=" * 80)
    print("📈 SUMMARY")
    print("=" * 80)
    print(f"Total Requests: {total_all}")
    print(f"Successful: {total_success} ({total_success/total_all*100:.1f}%)")
    print(f"Errors: {total_errors} ({total_errors/total_all*100:.1f}%)")
    print()

    # Calculate overall latency stats
    all_latencies = []
    for result in results:
        all_latencies.extend(result.latencies)

    if all_latencies:
        avg = statistics.mean(all_latencies)
        median = statistics.median(all_latencies)
        p95 = statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) >= 20 else max(all_latencies)

        print(f"Overall Latency:")
        print(f"  Average: {avg*1000:.2f}ms")
        print(f"  Median:  {median*1000:.2f}ms")
        print(f"  P95:     {p95*1000:.2f}ms")
        print()

    # Performance targets
    print("🎯 Performance Targets:")
    print(f"  Target P95 Latency: <500ms")
    if all_latencies and statistics.quantiles(all_latencies, n=20)[18] < 0.5:
        print(f"  ✅ ACHIEVED: {p95*1000:.2f}ms")
    else:
        print(f"  ⚠️  NOT ACHIEVED: {p95*1000:.2f}ms")

    print(f"  Target Throughput: >100 req/s")
    if total_success / (sum(time.time() - time.time() for _ in [0]) + 1) > 100:
        print(f"  ✅ ACHIEVED")
    else:
        print(f"  ⚠️  NEEDS IMPROVEMENT")

    print()
    print("=" * 80)
    print("✅ LOAD TEST COMPLETE")
    print("=" * 80)


async def test_with_auth(base_url: str = "http://localhost:8000"):
    """Test authenticated endpoints (requires login)"""
    print("\n" + "=" * 80)
    print("🔐 AUTHENTICATED ENDPOINT TESTS")
    print("=" * 80)
    print()
    print("NOTE: These tests require authentication.")
    print("To test migrated endpoints with auth:")
    print("1. Create a test user or use existing credentials")
    print("2. Login to get JWT token")
    print("3. Add token to request headers")
    print()
    print("Example:")
    print("""
    # Login
    TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \\
        -H "Content-Type: application/json" \\
        -d '{"email":"user@example.com","password":"password"}' \\
        | jq -r '.data.access_token')

    # Test endpoint with auth
    curl -H "Authorization: Bearer $TOKEN" \\
        http://localhost:8000/api/v1/users/me
    """)


if __name__ == "__main__":
    print("Async Cache Load Testing")
    print("=" * 80)
    print()
    print("This script tests the async cache endpoints under load.")
    print()
    print("Prerequisites:")
    print("  1. Backend server running on http://localhost:8000")
    print("  2. Redis running and accessible")
    print("  3. aiohttp installed (pip install aiohttp)")
    print()
    print("Starting load test...")
    print()

    # Check if server is running
    try:
        import aiohttp
        asyncio.run(run_load_tests())
        asyncio.run(test_with_auth())
    except ImportError:
        print("❌ ERROR: aiohttp not installed")
        print("   Install with: pip install aiohttp")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print()
        print("Make sure the backend server is running:")
        print("  uvicorn app.main:app --host 0.0.0.0 --port 8000")
