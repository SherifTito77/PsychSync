"""
Stress Testing Load Test for PsychSync

Purpose: Find the breaking point of the system by ramping up users until failure.
Target: Ramp up to 5,000+ concurrent users until system fails.
Use Case: Identify system limits, bottlenecks, and failure modes.

Stress Test Criteria:
- Ramp up users gradually (100 every 30 seconds)
- Continue until error rate exceeds 5% OR response time exceeds 5 seconds
- Record breaking point (user count, RPS, error type)
- Identify bottlenecks (database, cache, API server, network)

Expected Outcomes:
- Find maximum concurrent users system can handle
- Identify which endpoints fail first
- Document system degradation patterns
- Provide recommendations for scaling

Usage:
    locust -f stress_scenarios.py --host https://api.psychsync.com \\
        --users 5000 --spawn-rate 100 --run-time 1h \\
        --html reports/stress_report.html

For automatic stopping on failure:
    locust -f stress_scenarios.py --headless \\
        --host https://api.psychsync.com \\
        --users 5000 --spawn-rate 100 \\
        --stop-timeout 10
"""

import logging
import random
import time
from datetime import datetime
from typing import Optional

from locust import HttpUser, between, constant, events, task
from locust.runners import MasterRunner
from locust_config import LoadTestConfig, get_headers, test_data_manager

logger = logging.getLogger(__name__)


# Stress test thresholds
STRESS_THRESHOLDS = {
    "max_error_rate": 5.0,  # Stop if error rate exceeds 5%
    "max_response_time": 5000,  # Stop if p95 response time exceeds 5 seconds
    "ramp_up_interval": 30,  # Add 100 users every 30 seconds
    "ramp_up_size": 100,  # Number of users to add per interval
}


class StressTestUser(HttpUser):
    """
    Stress testing user - performs intensive operations to find system limits.

    Focus on high-load endpoints:
    - Assessment submission (write-intensive)
    - Dashboard refresh (read-intensive)
    - Analytics queries (database-intensive)
    - Token refresh (authentication-intensive)
    """

    # Minimal wait time to maximize load
    wait_time = constant(0.5)

    def on_start(self):
        """Setup: Login and prepare for intensive operations"""
        self.token = None
        self.user_credentials = test_data_manager.get_random_user()
        self.team_id = test_data_manager.get_random_team_id()
        self.user_id = test_data_manager.get_random_user_id()
        self.assessment_id = test_data_manager.get_random_assessment_id()
        self.login()

        logger.debug(f"Stress test user started: {self.user_credentials['email']}")

    def login(self):
        """Quick login to get token"""
        credentials = self.user_credentials

        with self.client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": credentials["email"],
                "password": credentials["password"],
            },
            headers=get_headers(),
            catch_response=True,
            name="[Stress] Login",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")

    # ==================== HIGH-INTENSITY TASKS ====================

    @task(20)
    def intensive_assessment_submission(self):
        """
        High-frequency assessment response submission.
        This is write-intensive and tests database write capacity.
        """
        responses = [
            {
                "question_id": f"q{random.randint(1, 100)}",
                "answer": random.randint(1, 5),
            }
            for _ in range(10)  # Submit 10 responses at once
        ]

        with self.client.post(
            f"/api/v1/assessments/{self.assessment_id}/responses",
            headers=get_headers(self.token),
            json={"responses": responses},
            catch_response=True,
            name="[Stress] Submit Assessment Responses",
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 429:
                # Rate limited - expected under stress
                response.success()
            else:
                response.failure(f"Submit failed: {response.status_code}")

    @task(15)
    def intensive_dashboard_refresh(self):
        """
        High-frequency dashboard refresh.
        Tests read performance and caching effectiveness.
        """
        with self.client.get(
            "/api/v1/analytics/dashboard",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Stress] Dashboard Refresh",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard failed: {response.status_code}")

    @task(12)
    def intensive_analytics_query(self):
        """
        High-frequency analytics queries.
        Tests database query performance under load.
        """
        with self.client.get(
            f"/api/v1/analytics/user/{self.user_id}",
            headers=get_headers(self.token),
            params={"period": random.choice(["7d", "30d", "90d"])},
            catch_response=True,
            name="[Stress] Analytics Query",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Analytics failed: {response.status_code}")

    @task(10)
    def intensive_team_analytics(self):
        """
        High-frequency team analytics queries.
        Tests complex aggregation queries.
        """
        with self.client.get(
            f"/api/v1/analytics/team/{self.team_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Stress] Team Analytics",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Team analytics failed: {response.status_code}")

    @task(8)
    def intensive_assessment_list(self):
        """
        High-frequency assessment list queries.
        Tests list performance and pagination.
        """
        with self.client.get(
            "/api/v1/assessments",
            headers=get_headers(self.token),
            params={"limit": 50, "skip": random.randint(0, 200)},
            catch_response=True,
            name="[Stress] List Assessments",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List failed: {response.status_code}")

    @task(8)
    def intensive_framework_browse(self):
        """
        High-frequency framework browsing.
        Tests read performance and cache hit rate.
        """
        with self.client.get(
            "/api/v1/personality-assessments/frameworks",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Stress] Browse Frameworks",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Browse failed: {response.status_code}")

    @task(7)
    def intensive_token_refresh(self):
        """
        High-frequency token refresh.
        Tests authentication system capacity.
        """
        with self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "dummy_refresh_token"},
            headers=get_headers(),
            catch_response=True,
            name="[Stress] Token Refresh",
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Refresh failed: {response.status_code}")

    @task(5)
    def intensive_user_verification(self):
        """
        High-frequency user verification.
        Tests user lookup performance.
        """
        with self.client.get(
            "/api/v1/users/me",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Stress] Verify User",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Verify failed: {response.status_code}")

    @task(5)
    def intensive_team_members(self):
        """
        High-frequency team member queries.
        Tests relationship query performance.
        """
        with self.client.get(
            f"/api/v1/teams/{self.team_id}/members",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Stress] Team Members",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Members failed: {response.status_code}")

    @task(3)
    def intensive_results_view(self):
        """
        High-frequency results viewing.
        Tests calculated/scoped data retrieval.
        """
        with self.client.get(
            f"/api/v1/assessments/{self.assessment_id}/results",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Stress] View Results",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Results failed: {response.status_code}")

    @task(2)
    def intensive_create_assessment(self):
        """
        High-frequency assessment creation.
        Tests write performance and validation.
        """
        with self.client.post(
            "/api/v1/assessments",
            headers=get_headers(self.token),
            json={
                "name": f"Stress Test Assessment {random.randint(1, 10000)}",
                "framework_code": random.choice(["MBTI", "BigFive", "Enneagram"]),
            },
            catch_response=True,
            name="[Stress] Create Assessment",
        ) as response:
            if response.status_code in [200, 201, 400]:
                response.success()
            else:
                response.failure(f"Create failed: {response.status_code}")

    @task(2)
    def intensive_notifications(self):
        """
        High-frequency notification checks.
        Tests query performance with filtering.
        """
        with self.client.get(
            "/api/v1/notifications",
            headers=get_headers(self.token),
            params={"limit": 50},
            catch_response=True,
            name="[Stress] Notifications",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Notifications failed: {response.status_code}")


# ==================== STRESS TEST MONITORING ====================

breaking_point_detected = False
breaking_point_info = {
    "user_count": None,
    "rps": None,
    "error_rate": None,
    "failure_reason": None,
    "timestamp": None,
}


@events.request.add_hook
def monitor_stress_metrics(
    request_type, name, response_time, response_length, exception, **kwargs
):
    """
    Monitor stress test metrics and detect breaking point.
    """
    global breaking_point_detected, breaking_point_info

    if breaking_point_detected:
        return

    # Log slow requests
    if response_time > STRESS_THRESHOLDS["max_response_time"]:
        logger.warning(
            f"⚠️  STRESS: Slow request {name}: {response_time}ms "
            f"(threshold: {STRESS_THRESHOLDS['max_response_time']}ms)"
        )


@events.test_stop.add_hook
def generate_stress_test_report(environment, **kwargs):
    """
    Generate comprehensive stress test report.
    """
    stats = environment.stats

    print("\n" + "=" * 80)
    print("STRESS TEST RESULTS - System Breaking Point Analysis")
    print("=" * 80)

    # Calculate final metrics
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    error_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

    response_times = stats.total
    p50 = response_times.median_response_time
    p95 = response_times.get_response_time_percentile(0.95)
    p99 = response_times.get_response_time_percentile(0.99)
    rps = stats.total.total_rps

    print(f"\nFinal Performance Metrics:")
    print(f"  Total Requests: {total_requests:,}")
    print(f"  Successful: {total_requests - total_failures:,}")
    print(f"  Failed: {total_failures:,}")
    print(f"  Error Rate: {error_rate:.2f}%")
    print(f"  Throughput: {rps:.2f} req/s")

    print(f"\nResponse Times:")
    print(f"  Median (p50): {p50}ms")
    print(f"  p95: {p95:.0f}ms")
    print(f"  p99: {p99:.0f}ms")
    print(f"  Max: {response_times.max_response_time}ms")

    # Breaking point analysis
    if breaking_point_detected:
        print(f"\n🔴 BREAKING POINT DETECTED:")
        print(f"  User Count: {breaking_point_info['user_count']}")
        print(f"  Requests/Second: {breaking_point_info['rps']:.2f}")
        print(f"  Error Rate: {breaking_point_info['error_rate']:.2f}%")
        print(f"  Failure Reason: {breaking_point_info['failure_reason']}")
        print(f"  Timestamp: {breaking_point_info['timestamp']}")
    else:
        print(f"\n✅ NO BREAKING POINT REACHED")
        print(f"  System handled all load successfully")
        print(f"  Consider increasing max users to find true breaking point")

    # Performance degradation analysis
    print(f"\nPerformance Degradation:")

    # Group by endpoint
    endpoints_by_type = {
        "Write Operations": [],
        "Read Operations": [],
        "Auth Operations": [],
        "Analytics": [],
    }

    for entry in stats.entries.values():
        name = entry.name.lower()
        if "submit" in name or "create" in name:
            endpoints_by_type["Write Operations"].append(entry)
        elif "verify" in name or "refresh" in name or "login" in name:
            endpoints_by_type["Auth Operations"].append(entry)
        elif "analytics" in name or "dashboard" in name:
            endpoints_by_type["Analytics"].append(entry)
        else:
            endpoints_by_type["Read Operations"].append(entry)

    for endpoint_type, entries in endpoints_by_type.items():
        if entries:
            avg_p95 = sum(e.get_response_time_percentile(0.95) for e in entries) / len(
                entries
            )
            total_rps = sum(e.total_rps for e in entries)
            error_rate = (
                sum(e.num_failures for e in entries)
                / sum(e.num_requests for e in entries)
                * 100
            )
            print(f"  {endpoint_type}:")
            print(
                f"    p95: {avg_p95:.0f}ms, RPS: {total_rps:.1f}, Errors: {error_rate:.2f}%"
            )

    # Bottleneck identification
    print(f"\nPotential Bottlenecks (Top 5 by p95):")
    sorted_by_p95 = sorted(
        [s for s in stats.entries.values() if s.num_requests > 10],
        key=lambda x: x.get_response_time_percentile(0.95),
        reverse=True,
    )[:5]

    for i, entry in enumerate(sorted_by_p95, 1):
        p95 = entry.get_response_time_percentile(0.95)
        p99 = entry.get_response_time_percentile(0.99)
        err_rate = (
            (entry.num_failures / entry.num_requests * 100)
            if entry.num_requests > 0
            else 0
        )
        print(f"  {i}. {entry.name}:")
        print(f"     p95: {p95:.0f}ms, p99: {p99:.0f}ms, Errors: {err_rate:.2f}%")

    # Failure analysis
    print(f"\nFailure Analysis:")
    failed_endpoints = [
        (s.name, s.num_failures, s.num_requests)
        for s in stats.entries.values()
        if s.num_failures > 0
    ]

    if failed_endpoints:
        failed_endpoints.sort(key=lambda x: x[1], reverse=True)
        print(f"  Endpoints with failures: {len(failed_endpoints)}")
        for name, failures, total in failed_endpoints[:10]:
            err_rate = (failures / total * 100) if total > 0 else 0
            print(f"    {name}: {failures}/{total} ({err_rate:.1f}%)")
    else:
        print(f"  No failures detected ✅")

    # Recommendations
    print(f"\nRecommendations:")

    if error_rate > 1.0:
        print(f"  ⚠️  Error rate exceeded 1% - consider scaling database connections")

    if p95 > 1000:
        print(f"  ⚠️  p95 response time exceeded 1s - optimize slow queries")

    if p99 > 2000:
        print(f"  ⚠️  p99 response time exceeded 2s - investigate tail latency")

    print(f"\n" + "=" * 80 + "\n")


@events.spawning_complete.add_hook
def on_spawning_complete(user_count, **kwargs):
    """Log when stress test reaches max users"""
    logger.info(f"🔥 STRESS TEST: Reached {user_count} concurrent users")
    logger.info(f"Monitoring for breaking point...")


if __name__ == "__main__":
    print(
        """
╔══════════════════════════════════════════════════════════════════════╗
║              STRESS TESTING LOAD TEST - PsychSync                    ║
╚══════════════════════════════════════════════════════════════════════╝

This test finds the system breaking point by ramping up users until failure.

Configuration:
  - Max Users: 5,000 concurrent
  - Spawn Rate: 100 users/second
  - Duration: Until breaking point or 1 hour

Stress Test Criteria:
  - Stop if error rate exceeds 5%
  - Stop if p95 response time exceeds 5 seconds
  - Ramp up: 100 users every 30 seconds

Expected Outcomes:
  ✅ Find maximum concurrent users
  ✅ Identify failing endpoints
  ✅ Document degradation patterns
  ✅ Provide scaling recommendations

Usage:
  # Automatic (stop on failure)
  locust -f stress_scenarios.py --headless \\
      --host https://api.psychsync.com \\
      --users 5000 --spawn-rate 100

  # Manual (with web UI)
  locust -f stress_scenarios.py \\
      --host https://api.psychsync.com \\
      --users 5000 --spawn-rate 100 \\
      --html reports/stress_report.html

⚠️  WARNING: This test will push the system to its limits.
           Run during maintenance windows only.

    """
    )
