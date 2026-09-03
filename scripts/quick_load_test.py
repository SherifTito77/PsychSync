#!/usr/bin/env python3
"""
Quick Load Test for Async Cache Endpoints
Simple Python script to test endpoint performance
"""

import statistics
import subprocess
import time
from datetime import datetime


def test_endpoint(url, num_requests=100):
    """Test endpoint with multiple requests"""
    print(f"Testing: {url}")
    print(f"Requests: {num_requests}")
    print()

    latencies = []
    success = 0
    errors = 0

    for i in range(num_requests):
        start = time.time()
        try:
            result = subprocess.run(
                ["curl", "-s", "-w", "\n%{http_code}\n%{time_total}", url],
                capture_output=True,
                text=True,
                timeout=10,
            )
            end = time.time()

            output = result.stdout.strip().split("\n")
            if len(output) >= 2:
                http_code = output[-2]
                time_total = output[-1]

                latency = end - start
                latencies.append(latency)

                if http_code in ["200", "401"]:  # 401 is expected (not authenticated)
                    success += 1
                else:
                    errors += 1

            # Progress indicator
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i+1}/{num_requests}")

        except Exception as e:
            errors += 1
            print(f"  Error on request {i+1}: {str(e)[:50]}")

    return latencies, success, errors


def main():
    print("=" * 80)
    print("🚀 ASYNC CACHE LOAD TEST - Quick Version")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test health endpoint
    url = "http://localhost:8000/api/v1/health"
    latencies, success, errors = test_endpoint(url, num_requests=100)

    print()
    print("=" * 80)
    print("📊 RESULTS")
    print("=" * 80)
    print()

    total = success + errors
    success_rate = (success / total * 100) if total > 0 else 0

    print(f"Total Requests: {total}")
    print(f"Successful: {success} ({success_rate:.1f}%)")
    print(f"Errors: {errors}")
    print()

    if latencies:
        avg = statistics.mean(latencies)
        median = statistics.median(latencies)
        p95 = (
            statistics.quantiles(latencies, n=20)[18]
            if len(latencies) >= 20
            else max(latencies)
        )
        p99 = (
            statistics.quantiles(latencies, n=100)[98]
            if len(latencies) >= 100
            else max(latencies)
        )

        print("⏱️  Latency Statistics:")
        print(f"  Average: {avg*1000:.2f}ms")
        print(f"  Median:  {median*1000:.2f}ms")
        print(f"  P95:     {p95*1000:.2f}ms")
        print(f"  P99:     {p99*1000:.2f}ms")
        print()

    print("🎯 Performance Targets:")
    print(
        f"  Success Rate >95%: {'✅' if success_rate >= 95 else '⚠️'} {success_rate:.1f}%"
    )
    if latencies:
        print(
            f"  P95 Latency <500ms: {'✅' if statistics.quantiles(latencies, n=20)[18] < 0.5 else '⚠️'} {p95*1000:.2f}ms"
        )

    print()
    print("=" * 80)
    print("✅ Load Test Complete")
    print("=" * 80)
    print()
    print("💡 Tip: Check Redis cache hit rate:")
    print("   redis-cli INFO stats | grep -E '(keyspace_hits|keyspace_misses)'")


if __name__ == "__main__":
    main()
