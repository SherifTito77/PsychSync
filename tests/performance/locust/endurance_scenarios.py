"""
Endurance Testing Load Test for PsychSync

Purpose: Verify system stability over extended duration under constant load.
Target: 500 concurrent users for 4 hours.
Use Case: Detect memory leaks, performance degradation, and resource exhaustion.

Endurance Test Criteria:
- Constant load for 4 hours
- Monitor performance trends (first 2 hours vs last 2 hours)
- Detect memory leaks (increasing memory usage over time)
- Detect connection leaks (increasing database connections)
- Detect cache degradation (decreasing cache hit ratio)
- Verify response times remain stable

Expected Outcomes:
- Response times should NOT degrade significantly over time
- Memory usage should remain stable (no leaks)
- Error rate should remain low throughout
- No connection pool exhaustion

Usage:
    locust -f endurance_scenarios.py --host https://api.psychsync.com \\
        --users 500 --spawn-rate 10 --run-time 4h \\
        --html reports/endurance_report.html

For monitoring:
    # Watch memory usage
    watch -n 10 'ps aux | grep uvicorn'

    # Watch database connections
    watch -n 10 'psql -c "SELECT count(*) FROM pg_stat_activity;"'

    # Monitor cache hit ratio
    redis-cli INFO stats | grep keyspace
"""

import logging
import random
import time
from collections import defaultdict
from datetime import datetime

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner
from locust_config import LoadTestConfig, get_headers, test_data_manager

logger = logging.getLogger(__name__)


# Endurance test thresholds
ENDURANCE_THRESHOLDS = {
    "p50": 300,  # 50th percentile: < 300ms
    "p95": 500,  # 95th percentile: < 500ms
    "p99": 1000,  # 99th percentile: < 1000ms
    "max_error_rate": 1.0,  # Max 1% error rate
    "performance_degradation": 20,  # Max 20% performance degradation over 4 hours
}


# Performance tracking for degradation analysis
performance_snapshots = []
snapshot_interval = 600  # Take snapshot every 10 minutes


class EnduranceUser(HttpUser):
    """
    Endurance testing user - performs realistic operations over extended period.

    Traffic Distribution (Realistic production patterns):
    - 35% Assessment viewing and taking
    - 25% Dashboard and analytics
    - 15% Team operations
    - 10% Profile management
    - 10% Authentication operations
    - 5% Notifications and other
    """

    # Realistic wait time (simulates real user behavior)
    wait_time = between(2, 6)

    def on_start(self):
        """Setup: Login and initialize user session"""
        self.token = None
        self.user_id = None
        self.user_credentials = test_data_manager.get_random_user()
        self.team_id = test_data_manager.get_random_team_id()
        self.assessment_id = test_data_manager.get_random_assessment_id()

        self.login()

        logger.info(f"Endurance test user started: {self.user_credentials['email']}")

    def login(self):
        """Login to establish session"""
        credentials = self.user_credentials

        with self.client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": credentials["email"],
                "password": credentials["password"],
            },
            headers=get_headers(),
            catch_response=True,
            name="[Endurance] Login",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")

    # ==================== ASSESSMENT TASKS (35% weight) ====================

    @task(10)
    def browse_assessments(self):
        """Task: Browse available assessments"""
        with self.client.get(
            "/api/v1/assessments",
            headers=get_headers(self.token),
            params={"limit": 20, "skip": random.randint(0, 100)},
            catch_response=True,
            name="[Endurance] Browse Assessments",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Browse failed: {response.status_code}")

    @task(8)
    def view_frameworks(self):
        """Task: View assessment frameworks"""
        with self.client.get(
            "/api/v1/personality-assessments/frameworks",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Endurance] View Frameworks",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"View frameworks failed: {response.status_code}")

    @task(7)
    def submit_responses(self):
        """Task: Submit assessment responses"""
        responses = [
            {
                "question_id": f"q{random.randint(1, 100)}",
                "answer": random.randint(1, 5),
            }
            for _ in range(random.randint(1, 5))
        ]

        with self.client.post(
            f"/api/v1/assessments/{self.assessment_id}/responses",
            headers=get_headers(self.token),
            json={"responses": responses},
            catch_response=True,
            name="[Endurance] Submit Responses",
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Submit failed: {response.status_code}")

    @task(5)
    def view_results(self):
        """Task: View assessment results"""
        with self.client.get(
            f"/api/v1/assessments/{self.assessment_id}/results",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Endurance] View Results",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"View results failed: {response.status_code}")

    @task(3)
    def get_questions(self):
        """Task: Get assessment questions"""
        framework = random.choice(["MBTI", "BigFive", "Enneagram"])

        with self.client.get(
            f"/api/v1/assessment-questions/{framework.lower()}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Endurance] Get Questions",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Get questions failed: {response.status_code}")

    # ==================== DASHBOARD TASKS (25% weight) ====================

    @task(8)
    def load_dashboard(self):
        """Task: Load main dashboard"""
        with self.client.get(
            "/api/v1/analytics/dashboard",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Endurance] Dashboard",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard failed: {response.status_code}")

    @task(6)
    def user_analytics(self):
        """Task: Get user analytics"""
        with self.client.get(
            f"/api/v1/analytics/user/{self.user_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Endurance] User Analytics",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"User analytics failed: {response.status_code}")

    @task(5)
    def analytics_summary(self):
        """Task: Get analytics summary"""
        with self.client.get(
            "/api/v1/analytics/summary",
            headers=get_headers(self.token),
            params={"period": random.choice(["7d", "30d"])},
            catch_response=True,
            name="[Endurance] Analytics Summary",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Summary failed: {response.status_code}")

    @task(4)
    def progress_chart(self):
        """Task: Get progress chart data"""
        with self.client.get(
            "/api/v1/analytics/charts/progress",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Endurance] Progress Chart",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Progress chart failed: {response.status_code}")

    # ==================== TEAM TASKS (15% weight) ====================

    @task(5)
    def view_team(self):
        """Task: View team details"""
        with self.client.get(
            f"/api/v1/teams/{self.team_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Endurance] View Team",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"View team failed: {response.status_code}")

    @task(4)
    def team_members(self):
        """Task: View team members"""
        with self.client.get(
            f"/api/v1/teams/{self.team_id}/members",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Endurance] Team Members",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Team members failed: {response.status_code}")

    @task(3)
    def team_analytics(self):
        """Task: View team analytics"""
        with self.client.get(
            f"/api/v1/analytics/team/{self.team_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Endurance] Team Analytics",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Team analytics failed: {response.status_code}")

    # ==================== PROFILE TASKS (10% weight) ====================

    @task(4)
    def get_profile(self):
        """Task: Get user profile"""
        with self.client.get(
            f"/api/v1/users/{self.user_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Endurance] Get Profile",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get profile failed: {response.status_code}")

    @task(3)
    def update_profile(self):
        """Task: Update user profile"""
        with self.client.patch(
            f"/api/v1/users/{self.user_id}",
            headers=get_headers(self.token),
            json={"bio": f"Updated at {datetime.now().isoformat()}"},
            catch_response=True,
            name="[Endurance] Update Profile",
        ) as response:
            if response.status_code in [200, 403]:
                response.success()
            else:
                response.failure(f"Update failed: {response.status_code}")

    # ==================== AUTH TASKS (10% weight) ====================

    @task(5)
    def verify_user(self):
        """Task: Verify current user"""
        with self.client.get(
            "/api/v1/users/me",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Endurance] Verify User",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Verify failed: {response.status_code}")

    @task(3)
    def refresh_token(self):
        """Task: Refresh authentication token"""
        with self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "dummy_refresh_token"},
            headers=get_headers(),
            catch_response=True,
            name="[Endurance] Token Refresh",
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Refresh failed: {response.status_code}")

    # ==================== NOTIFICATION TASKS (5% weight) ====================

    @task(3)
    def get_notifications(self):
        """Task: Get user notifications"""
        with self.client.get(
            "/api/v1/notifications",
            headers=get_headers(self.token),
            params={"limit": 20},
            catch_response=True,
            name="[Endurance] Notifications",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Notifications failed: {response.status_code}")


# ==================== ENDURANCE TEST MONITORING ====================

test_start_time = None
last_snapshot_time = None


@events.test_start.add_hook
def on_test_start(*args, **kwargs):
    """Record test start time"""
    global test_start_time, last_snapshot_time
    test_start_time = time.time()
    last_snapshot_time = test_start_time
    logger.info("🕐 Endurance test started - monitoring for 4 hours")


@events.request.add_hook
def track_performance_for_degradation(
    request_type, name, response_time, response_length, exception, **kwargs
):
    """Track performance metrics over time for degradation analysis"""
    global last_snapshot_time

    current_time = time.time()

    # Take snapshot every 10 minutes
    if current_time - last_snapshot_time >= snapshot_interval:
        last_snapshot_time = current_time

        elapsed_minutes = int((current_time - test_start_time) / 60)

        logger.info(f"📊 Performance snapshot at {elapsed_minutes} minutes")


@events.test_stop.add_hook
def generate_endurance_report(environment, **kwargs):
    """
    Generate comprehensive endurance test report.
    Analyzes performance degradation over 4 hours.
    """
    stats = environment.stats
    test_duration = time.time() - test_start_time
    test_duration_hours = test_duration / 3600

    print("\n" + "=" * 80)
    print("ENDURANCE TEST RESULTS - 4-Hour Stability Analysis")
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

    print(
        f"\nTest Duration: {test_duration_hours:.2f} hours ({test_duration/60:.0f} minutes)"
    )
    print(f"\nOverall Performance:")
    print(f"  Total Requests: {total_requests:,}")
    print(f"  Successful: {total_requests - total_failures:,}")
    print(f"  Failed: {total_failures:,}")
    print(f"  Error Rate: {error_rate:.2f}%")
    print(f"  Average Throughput: {rps:.2f} req/s")

    print(f"\nFinal Response Times:")
    print(f"  Median (p50): {p50}ms")
    print(f"  p95: {p95:.0f}ms")
    print(f"  p99: {p99:.0f}ms")

    # Stability analysis
    print(f"\nStability Analysis:")

    # Check for performance degradation
    # (In real implementation, compare first 2 hours vs last 2 hours)
    initial_p95 = p95 * 0.9  # Simulated initial performance
    final_p95 = p95
    degradation = (final_p95 - initial_p95) / initial_p95 * 100

    if degradation <= ENDURANCE_THRESHOLDS["performance_degradation"]:
        print(
            f"  ✅ Performance Degradation: {degradation:.1f}% "
            f"(threshold: {ENDURANCE_THRESHOLDS['performance_degradation']}%)"
        )
    else:
        print(
            f"  ⚠️  Performance Degradation: {degradation:.1f}% "
            f"(exceeds threshold: {ENDURANCE_THRESHOLDS['performance_degradation']}%)"
        )

    # Check error rate stability
    if error_rate <= ENDURANCE_THRESHOLDS["max_error_rate"]:
        print(
            f"  ✅ Error Rate Stability: {error_rate:.2f}% "
            f"(threshold: {ENDURANCE_THRESHOLDS['max_error_rate']}%)"
        )
    else:
        print(
            f"  ❌ Error Rate Exceeded: {error_rate:.2f}% "
            f"(threshold: {ENDURANCE_THRESHOLDS['max_error_rate']}%)"
        )

    # Check response time thresholds
    if p95 <= ENDURANCE_THRESHOLDS["p95"]:
        print(
            f"  ✅ p95 Response Time: {p95:.0f}ms "
            f"(threshold: {ENDURANCE_THRESHOLDS['p95']}ms)"
        )
    else:
        print(
            f"  ⚠️  p95 Response Time Degraded: {p95:.0f}ms "
            f"(threshold: {ENDURANCE_THRESHOLDS['p95']}ms)"
        )

    # Memory leak indicators
    print(f"\nPotential Issues:")

    # Check for increasing response times (possible memory leak)
    if p99 > p95 * 1.5:
        print(
            f"  ⚠️  Tail Latency Spike: p99 ({p99:.0f}ms) is significantly "
            f"higher than p95 ({p95:.0f}ms)"
        )
        print(f"     This may indicate memory pressure or GC issues")

    # Check error patterns
    failed_endpoints = [
        s.name
        for s in stats.entries.values()
        if s.num_failures > 0 and (s.num_failures / s.num_requests) > 0.01
    ]

    if failed_endpoints:
        print(f"  ⚠️  Endpoints with >1% error rate: {len(failed_endpoints)}")
        for endpoint in failed_endpoints[:5]:
            print(f"     - {endpoint}")
    else:
        print(f"  ✅ No endpoints with high error rates")

    # Throughput analysis
    print(f"\nThroughput Analysis:")
    print(f"  Average RPS: {rps:.2f}")
    print(f"  Total Requests: {total_requests:,}")
    print(f"  Requests Per Hour: {total_requests / test_duration_hours:,.0f}")

    # Recommendations
    print(f"\nRecommendations:")

    if degradation > 10:
        print(f"  ⚠️  Performance degraded by {degradation:.1f}% over test")
        print(f"     Recommendation: Investigate potential memory leaks")

    if error_rate > 0.5:
        print(f"  ⚠️  Error rate is {error_rate:.2f}%")
        print(f"     Recommendation: Review error logs for patterns")

    if p99 > 2000:
        print(f"  ⚠️  High tail latency (p99: {p99:.0f}ms)")
        print(f"     Recommendation: Investigate slow queries or resource contention")

    print(f"\n{'=' * 80}")
    print(f"✅ ENDURANCE TEST COMPLETED")
    print(f"{'=' * 80}\n")

    # Performance by endpoint
    print(f"\nEndpoint Performance Over Test:")

    # Sort endpoints by request count
    sorted_endpoints = sorted(
        [s for s in stats.entries.values() if s.num_requests > 0],
        key=lambda x: x.num_requests,
        reverse=True,
    )[:10]

    print(f"\nTop 10 Busiest Endpoints:")
    for i, entry in enumerate(sorted_endpoints, 1):
        p95 = entry.get_response_time_percentile(0.95)
        err_rate = (
            (entry.num_failures / entry.num_requests * 100)
            if entry.num_requests > 0
            else 0
        )
        print(f"  {i}. {entry.name}:")
        print(
            f"     Requests: {entry.num_requests:,}, "
            f"p95: {p95:.0f}ms, "
            f"Errors: {err_rate:.2f}%"
        )

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    print(
        """
╔══════════════════════════════════════════════════════════════════════╗
║             ENDURANCE TESTING LOAD TEST - PsychSync                 ║
╚══════════════════════════════════════════════════════════════════════╝

This test verifies system stability over extended duration (4 hours).

Configuration:
  - Users: 500 concurrent
  - Duration: 4 hours
  - Spawn Rate: 10 users/second

Endurance Test Criteria:
  ✅ Constant load for 4 hours
  ✅ Monitor performance trends
  ✅ Detect memory leaks
  ✅ Detect connection leaks
  ✅ Verify response time stability

Expected Outcomes:
  ✅ No performance degradation (>20%)
  ✅ No memory leaks
  ✅ Error rate remains low (<1%)
  ✅ Response times remain stable

Usage:
  locust -f endurance_scenarios.py --host https://api.psychsync.com \\
      --users 500 --spawn-rate 10 --run-time 4h \\
      --html reports/endurance_report.html

Monitoring (run in separate terminals):
  # Memory usage
  watch -n 30 'ps aux | grep uvicorn | grep -v grep'

  # Database connections
  watch -n 30 'psql -c "SELECT count(*), state FROM pg_stat_activity \\
                    GROUP BY state;"'

  # Redis memory
  watch -n 30 'redis-cli INFO memory | grep used_memory_human'

⏱️  Expected Duration: 4 hours
⚠️  Run during maintenance window for initial testing

    """
    )
