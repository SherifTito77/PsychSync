"""
Locust Load Testing Script for Rate Limiting Validation

This file defines realistic user behavior patterns for load testing the API.
Run with: locust -f tests/load/locustfile.py --host=http://localhost:8000

Features:
- Multiple user types (anonymous, basic, premium, admin)
- Realistic request patterns (browsing, authentication, API calls)
- Ramp-up and sustained load testing
- Rate limit validation
"""

import random
import time

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner


class AnonymousUser(HttpUser):
    """
    Simulates anonymous user behavior before authentication.
    Rate limit: 50 requests/minute
    """

    wait_time = between(1, 3)
    weight = 1

    @task(3)
    def view_health(self):
        """Check API health - lenient rate limits"""
        with self.client.get("/api/v1/health", catch_response=True) as response:
            if response.status_code == 429:
                response.failure("Rate limited on health endpoint")

    @task(2)
    def view_public_docs(self):
        """View public API documentation"""
        self.client.get("/docs")

    @task(1)
    def attempt_login(self):
        """Attempt login - triggers stricter auth rate limits"""
        # Use different emails to avoid account lockout
        email = f"anon{random.randint(1000, 9999)}@test.com"
        with self.client.post(
            "/api/v1/auth/token",
            json={"username": email, "password": "wrongpass"},
            catch_response=True,
        ) as response:
            if response.status_code == 429:
                # Expected for auth endpoints
                response.success()


class BasicUser(HttpUser):
    """
    Simulates BASIC tier authenticated user.
    Rate limit: 200 requests/minute
    """

    wait_time = between(0.5, 2)
    weight = 2

    def on_start(self):
        """Login on start"""
        response = self.client.post(
            "/api/v1/auth/test-login",
            json={"email": "basic_user@test.com", "tier": "basic"},
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(5)
    def view_teams(self):
        """Browse teams - common operation"""
        if self.token:
            with self.client.get(
                "/api/v1/teams", headers=self.headers, catch_response=True
            ) as response:
                if response.status_code == 429:
                    response.failure("Rate limited on teams endpoint")

    @task(3)
    def view_analytics(self):
        """View analytics - has stricter multiplier (0.5x)"""
        if self.token:
            with self.client.get(
                "/api/v1/analytics", headers=self.headers, catch_response=True
            ) as response:
                if response.status_code == 429:
                    # Expected due to stricter limits
                    response.success()

    @task(2)
    def create_assessment(self):
        """Create assessment - very strict multiplier (0.3x)"""
        if self.token:
            with self.client.post(
                "/api/v1/assessments",
                headers=self.headers,
                json={
                    "title": f"Test Assessment {random.randint(1, 1000)}",
                    "type": "personality",
                },
                catch_response=True,
            ) as response:
                if response.status_code == 429:
                    response.success()

    @task(1)
    def refresh_token(self):
        """Refresh access token"""
        if self.token:
            self.client.post(
                "/api/v1/auth/refresh", headers=self.headers, catch_response=True
            )


class PremiumUser(HttpUser):
    """
    Simulates PREMIUM tier user with higher limits.
    Rate limit: 500 requests/minute
    """

    wait_time = between(0.3, 1)
    weight = 1

    def on_start(self):
        """Login on start"""
        response = self.client.post(
            "/api/v1/auth/test-login",
            json={"email": "premium_user@test.com", "tier": "premium"},
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(4)
    def intensive_analytics(self):
        """Run intensive analytics operations"""
        if self.token:
            self.client.get("/api/v1/analytics/advanced", headers=self.headers)

    @task(3)
    def batch_operations(self):
        """Perform batch operations"""
        if self.token:
            # Multiple requests in quick succession
            for i in range(5):
                self.client.get(f"/api/v1/teams/{i}", headers=self.headers)

    @task(2)
    def export_data(self):
        """Export large datasets"""
        if self.token:
            self.client.post(
                "/api/v1/data-export",
                headers=self.headers,
                json={"format": "csv", "include_all": True},
            )

    @task(1)
    def ai_analysis(self):
        """Run AI-powered analysis"""
        if self.token:
            self.client.post(
                "/api/v1/ai/analyze",
                headers=self.headers,
                json={"assessment_id": random.randint(1, 100)},
            )


class AdminUser(HttpUser):
    """
    Simulates ADMIN user with highest limits.
    Rate limit: 2000 requests/minute
    """

    wait_time = between(0.1, 0.5)
    weight = 1

    def on_start(self):
        """Login on start"""
        response = self.client.post(
            "/api/v1/auth/test-login", json={"email": "admin@test.com", "tier": "admin"}
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(3)
    def admin_monitoring(self):
        """Admin monitoring dashboard"""
        if self.token:
            self.client.get("/api/v1/admin/monitoring", headers=self.headers)

    @task(2)
    def admin_users(self):
        """Manage users"""
        if self.token:
            self.client.get("/api/v1/admin/users", headers=self.headers)

    @task(1)
    def system_health(self):
        """Check system health"""
        if self.token:
            self.client.get("/api/v1/admin/system-health", headers=self.headers)


# Rate limit validation event handlers
@events.request.add_hook
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    Track rate limit violations during load test
    """
    if exception:
        print(f"Request exception: {exception}")
    elif hasattr(response_time, "context"):
        # Check if response was rate limited
        if response_time.status_code == 429:
            print(f"⚠️  Rate limit hit: {name} (wait time: {response_time}s)")


@events.test_stop.add_hook
def on_test_stop(environment, **kwargs):
    """
    Print summary statistics after test completes
    """
    if isinstance(environment.runner, MasterRunner):
        return

    print("\n" + "=" * 60)
    print("RATE LIMITING LOAD TEST SUMMARY")
    print("=" * 60)

    stats = environment.stats
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Failed requests: {stats.total.num_failures}")
    print(f"Success rate: {(1 - stats.total.fail_ratio) * 100:.1f}%")
    print(f"Response times:")
    print(f"  - Median: {stats.total.median_response_time}ms")
    print(f"  - Average: {stats.total.avg_response_time:.0f}ms")
    print(
        f"  - 95th percentile: {stats.total.get_response_time_percentile(0.95):.0f}ms"
    )
    print(
        f"  - 99th percentile: {stats.total.get_response_time_percentile(0.99):.0f}ms"
    )
    print(f"Requests per second: {stats.total.total_rps:.2f}")
    print("\n" + "=" * 60)


class StresstestUser(HttpUser):
    """
    Stress test user that sends requests as fast as possible.
    Use to validate rate limiting under extreme load.
    """

    wait_time = between(0.01, 0.05)  # Very fast, almost no delay
    weight = 0  # Disabled by default

    def on_start(self):
        response = self.client.post(
            "/api/v1/auth/test-login",
            json={"email": "stress@test.com", "tier": "basic"},
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task
    def rapid_requests(self):
        """Send requests as fast as possible"""
        if self.token:
            endpoint = random.choice(
                ["/api/v1/teams", "/api/v1/analytics", "/api/v1/users"]
            )
            self.client.get(endpoint, headers=self.headers)
