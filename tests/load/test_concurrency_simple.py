"""
SIMPLE CONCURRENCY LOAD TEST
========================

A simplified load test to validate concurrency limits.

Run:
    locust -f tests/load/test_concurrency_simple.py --host http://localhost:8000

Headless:
    locust -f tests/load/test_concurrency_simple.py --headless --users 100 --spawn-rate 10 --run-time 3m
"""

from locust import HttpUser, between, task


class ConcurrencyTestUser(HttpUser):
    """Simulates realistic user behavior for concurrency testing"""

    # Wait 1-3 seconds between tasks (realistic user behavior)
    wait_time = between(1, 3)

    @task(5)
    def health_check(self):
        """Health check - lightweight endpoint"""
        self.client.get("/health")

    @task(3)
    def root_endpoint(self):
        """Root endpoint - public API"""
        self.client.get("/")

    @task(1)
    def api_health(self):
        """API health check - uses database"""
        self.client.get("/api/v1/health")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SIMPLE CONCURRENCY LOAD TEST")
    print("=" * 70)
    print("\nTest Scenarios:")
    print("  Smoke Test:    10 users, 1 min, 1 spawn/sec")
    print("  Normal Load:    100 users, 3 min, 10 spawn/sec")
    print("  Peak Load:     500 users, 5 min, 50 spawn/sec")
    print("\nTo run:")
    print(
        "  locust -f tests/load/test_concurrency_simple.py --host http://localhost:8000"
    )
    print("\nHeadless mode:")
    print(
        "  locust -f tests/load/test_concurrency_simple.py --headless --users 100 --spawn-rate 10 --run-time 3m"
    )
    print("=" * 70 + "\n")
