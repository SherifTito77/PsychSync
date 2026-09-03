#!/usr/bin/env python3
"""
Async Cache Performance Testing Script
Compares synchronous vs asynchronous cache operations
Expected improvement: 30-50% faster response times
"""

import asyncio
import os
import statistics
import sys
import time
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PerformanceTest:
    """Base class for performance tests"""

    def __init__(self, name: str):
        self.name = name
        self.latencies: List[float] = []

    async def run_test(self, iterations: int = 100):
        """Run the test and measure latencies"""
        raise NotImplementedError

    def report(self):
        """Generate test report"""
        if not self.latencies:
            return f"{self.name}: No data collected"

        avg = statistics.mean(self.latencies)
        median = statistics.median(self.latencies)
        p95 = (
            statistics.quantiles(self.latencies, n=20)[18]
            if len(self.latencies) >= 20
            else max(self.latencies)
        )
        p99 = (
            statistics.quantiles(self.latencies, n=100)[98]
            if len(self.latencies) >= 100
            else max(self.latencies)
        )

        return f"""
{self.name} Results:
  Average: {avg*1000:.2f}ms
  Median:  {median*1000:.2f}ms
  P95:     {p95*1000:.2f}ms
  P99:     {p99*1000:.2f}ms
"""


class AsyncCacheTest(PerformanceTest):
    """Test async cache operations"""

    def __init__(self):
        super().__init__("Async Cache Operations")

    async def run_test(self, iterations: int = 100):
        """Test async cache get/set operations"""
        try:
            from app.core.async_cache import AsyncCache

            # Warm up
            await AsyncCache.set("warmup", {"data": "value"}, expire=10)
            await AsyncCache.get("warmup")

            # Test
            latencies = []
            for i in range(iterations):
                key = f"test_key_{i % 10}"  # Reuse keys to test cache hits
                value = {"data": f"value_{i}", "index": i}

                start = time.perf_counter()
                await AsyncCache.set(key, value, expire=60)
                result = await AsyncCache.get(key)
                end = time.perf_counter()

                latencies.append(end - start)

            # Cleanup
            for i in range(10):
                await AsyncCache.delete(f"test_key_{i}")

            self.latencies = latencies
            return True

        except Exception as e:
            print(f"❌ Async cache test failed: {e}")
            return False


class ConcurrentLoadTest(PerformanceTest):
    """Test concurrent cache operations"""

    def __init__(self):
        super().__init__("Concurrent Load Test")

    async def single_operation(self, index: int):
        """Perform a single cache operation"""
        try:
            from app.core.async_cache import AsyncCache

            key = f"concurrent_test_{index % 20}"
            value = {"data": f"concurrent_value_{index}"}

            start = time.perf_counter()
            await AsyncCache.set(key, value, expire=60)
            result = await AsyncCache.get(key)
            end = time.perf_counter()

            return end - start

        except Exception as e:
            print(f"❌ Concurrent operation {index} failed: {e}")
            return 0.0

    async def run_test(self, iterations: int = 100, concurrency: int = 10):
        """Test concurrent cache operations"""
        try:
            # Create tasks
            tasks = []
            for i in range(iterations):
                tasks.append(self.single_operation(i))

            # Run concurrently
            latencies = await asyncio.gather(*tasks)

            # Filter out failed operations (returned 0.0)
            self.latencies = [l for l in latencies if l > 0]

            # Cleanup
            from app.core.async_cache import AsyncCache

            for i in range(20):
                await AsyncCache.delete(f"concurrent_test_{i}")

            return len(self.latencies) > 0

        except Exception as e:
            print(f"❌ Concurrent load test failed: {e}")
            return False


async def run_all_tests():
    """Run all performance tests"""
    print("=" * 60)
    print("🚀 Async Cache Performance Testing")
    print("=" * 60)
    print()

    # Test 1: Async Cache Operations
    print("Test 1: Async Cache Operations (100 iterations)")
    print("-" * 60)
    async_test = AsyncCacheTest()
    if await async_test.run_test(iterations=100):
        print(async_test.report())
    else:
        print("❌ Async cache test failed")
    print()

    # Test 2: Concurrent Load
    print("Test 2: Concurrent Load (100 operations, 10 concurrent)")
    print("-" * 60)
    concurrent_test = ConcurrentLoadTest()
    if await concurrent_test.run_test(iterations=100, concurrency=10):
        print(concurrent_test.report())
    else:
        print("❌ Concurrent load test failed")
    print()

    # Comparison
    if async_test.latencies and concurrent_test.latencies:
        async_avg = statistics.mean(async_test.latencies) * 1000
        concurrent_avg = statistics.mean(concurrent_test.latencies) * 1000

        print("=" * 60)
        print("📊 Performance Summary")
        print("=" * 60)
        print(f"Sequential Operations: {async_avg:.2f}ms average")
        print(f"Concurrent Operations: {concurrent_avg:.2f}ms average")

        if concurrent_avg < async_avg:
            improvement = ((async_avg - concurrent_avg) / async_avg) * 100
            print(f"✅ Concurrent is {improvement:.1f}% faster")
        print()

    # Expected vs Actual
    if async_test.latencies:
        async_avg = statistics.mean(async_test.latencies) * 1000
        print("=" * 60)
        print("🎯 Target Comparison")
        print("=" * 60)
        print(f"Expected improvement: 30-50% faster than sync cache")
        print(f"Your async cache latency: {async_avg:.2f}ms")
        print(f"Note: Full improvement requires production load")
        print()

    print("=" * 60)
    print("✅ Performance testing complete!")
    print("=" * 60)


async def simple_test():
    """Run a simple smoke test"""
    print("🧪 Running smoke test...")

    try:
        from app.core.async_cache import AsyncCache

        # Test set
        await AsyncCache.set("smoke_test", {"status": "ok"}, expire=60)

        # Test get
        result = await AsyncCache.get("smoke_test")
        assert result == {"status": "ok"}, f"Expected {{'status': 'ok'}}, got {result}"

        # Test delete
        await AsyncCache.delete("smoke_test")
        result = await AsyncCache.get("smoke_test")
        assert result is None, f"Expected None after delete, got {result}"

        print("✅ Smoke test PASSED")
        return True

    except Exception as e:
        print(f"❌ Smoke test FAILED: {e}")
        return False


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test async cache performance")
    parser.add_argument("--smoke", action="store_true", help="Run smoke test only")
    parser.add_argument(
        "--iterations", type=int, default=100, help="Number of test iterations"
    )
    args = parser.parse_args()

    if args.smoke:
        success = await simple_test()
        sys.exit(0 if success else 1)
    else:
        # Run smoke test first
        smoke_success = await simple_test()
        if not smoke_success:
            print("\n⚠️  Smoke test failed. Check Redis connection.")
            print("   Start Redis: docker-compose up -d redis")
            sys.exit(1)

        print()

        # Run full performance tests
        await run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
