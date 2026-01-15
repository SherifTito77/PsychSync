"""
Baseline Performance Load Test for PsychSync

Purpose: Establish baseline performance metrics under normal load.
Target: 100 concurrent users for 10 minutes.
Use Case: Verify system meets SLA requirements under typical daily load.

SLA Thresholds:
- p50 Response Time: < 200ms
- p95 Response Time: < 500ms
- p99 Response Time: < 1000ms
- Error Rate: < 1%
- Throughput: > 100 RPS

Usage:
    locust -f baseline_scenarios.py --host=https://api.psychsync.com \\
        --users 100 --spawn-rate 10 --run-time 10m \\
        --html reports/baseline_report.html
"""

from locust import HttpUser, task, between, events
import logging
import random
from datetime import datetime

from locust_config import (
    LoadTestConfig,
    get_headers,
    test_data_manager,
)

logger = logging.getLogger(__name__)


# Baseline SLA Thresholds
BASELINE_SLA = {
    "p50": 200,   # 50th percentile: < 200ms
    "p95": 500,   # 95th percentile: < 500ms
    "p99": 1000,  # 99th percentile: < 1000ms
    "max_error_rate": 1.0,  # Max 1% error rate
    "min_throughput": 100,  # Min 100 requests/second
}


class BaselineUser(HttpUser):
    """
    Simulates typical user behavior under normal load.

    Traffic Distribution (matches production patterns):
    - 40% Assessment browsing and viewing
    - 20% Dashboard and analytics
    - 15% Authentication operations
    - 15% Team management
    - 10% Profile management
    """

    # Realistic wait time between tasks (1-4 seconds)
    wait_time = between(1, 4)

    def on_start(self):
        """Setup: Login and initialize user session"""
        self.token = None
        self.user_id = None
        self.user_credentials = test_data_manager.get_random_user()
        self.team_id = test_data_manager.get_random_team_id()
        self.assessment_id = test_data_manager.get_random_assessment_id()
        self.login()

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
            name="[Auth] Login",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")

    # ==================== ASSESSMENT TASKS (40% weight) ====================

    @task(10)
    def browse_assessment_frameworks(self):
        """Task: Browse available assessment frameworks"""
        with self.client.get(
            "/api/v1/personality-assessments/frameworks",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Assessment] Browse Frameworks",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Browse failed: {response.status_code}")

    @task(8)
    def view_framework_details(self):
        """Task: View details of a specific framework"""
        framework = random.choice(["MBTI", "BigFive", "Enneagram", "DISC"])

        with self.client.get(
            f"/api/v1/personality-assessments/frameworks/{framework}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Assessment] View Framework Details",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"View details failed: {response.status_code}")

    @task(7)
    def list_assessments(self):
        """Task: List user's assessments"""
        with self.client.get(
            "/api/v1/assessments",
            headers=get_headers(self.token),
            params={"limit": 20, "skip": 0},
            catch_response=True,
            name="[Assessment] List Assessments",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List failed: {response.status_code}")

    @task(6)
    def view_assessment_results(self):
        """Task: View assessment results"""
        with self.client.get(
            f"/api/v1/assessments/{self.assessment_id}/results",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Assessment] View Results",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"View results failed: {response.status_code}")

    @task(5)
    def get_assessment_questions(self):
        """Task: Get assessment questions"""
        framework = random.choice(["MBTI", "BigFive", "Enneagram"])

        with self.client.get(
            f"/api/v1/assessment-questions/{framework.lower()}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Assessment] Get Questions",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Get questions failed: {response.status_code}")

    # ==================== DASHBOARD TASKS (20% weight) ====================

    @task(5)
    def load_dashboard(self):
        """Task: Load main dashboard"""
        with self.client.get(
            "/api/v1/analytics/dashboard",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Dashboard] Load Overview",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard load failed: {response.status_code}")

    @task(4)
    def get_user_analytics(self):
        """Task: Get user analytics"""
        with self.client.get(
            f"/api/v1/analytics/user/{self.user_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Dashboard] User Analytics",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"User analytics failed: {response.status_code}")

    @task(3)
    def get_analytics_summary(self):
        """Task: Get analytics summary"""
        with self.client.get(
            "/api/v1/analytics/summary",
            headers=get_headers(self.token),
            params={"period": "30d"},
            catch_response=True,
            name="[Dashboard] Analytics Summary",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Summary failed: {response.status_code}")

    @task(2)
    def get_progress_chart(self):
        """Task: Get progress chart data"""
        with self.client.get(
            "/api/v1/analytics/charts/progress",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Dashboard] Progress Chart",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Progress chart failed: {response.status_code}")

    # ==================== AUTH TASKS (15% weight) ====================

    @task(3)
    def refresh_token(self):
        """Task: Refresh authentication token"""
        with self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "dummy_refresh_token"},
            headers=get_headers(),
            catch_response=True,
            name="[Auth] Token Refresh",
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Refresh failed: {response.status_code}")

    @task(2)
    def verify_current_user(self):
        """Task: Verify current user"""
        with self.client.get(
            "/api/v1/users/me",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Auth] Verify User",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Verify user failed: {response.status_code}")

    @task(1)
    def get_user_profile(self):
        """Task: Get user profile"""
        with self.client.get(
            f"/api/v1/users/{self.user_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Auth] Get Profile",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get profile failed: {response.status_code}")

    # ==================== TEAM TASKS (15% weight) ====================

    @task(4)
    def view_team(self):
        """Task: View team details"""
        with self.client.get(
            f"/api/v1/teams/{self.team_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Team] View Details",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"View team failed: {response.status_code}")

    @task(3)
    def view_team_members(self):
        """Task: View team members"""
        with self.client.get(
            f"/api/v1/teams/{self.team_id}/members",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Team] View Members",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"View members failed: {response.status_code}")

    @task(2)
    def view_team_analytics(self):
        """Task: View team analytics"""
        with self.client.get(
            f"/api/v1/analytics/team/{self.team_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Team] Team Analytics",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Team analytics failed: {response.status_code}")

    # ==================== PROFILE TASKS (10% weight) ====================

    @task(3)
    def update_profile(self):
        """Task: Update user profile (lightweight)"""
        with self.client.patch(
            f"/api/v1/users/{self.user_id}",
            headers=get_headers(self.token),
            json={"bio": f"Updated at {datetime.now().isoformat()}"},
            catch_response=True,
            name="[Profile] Update Profile",
        ) as response:
            if response.status_code in [200, 403]:
                response.success()
            else:
                response.failure(f"Update failed: {response.status_code}")

    @task(2)
    def get_preferences(self):
        """Task: Get user preferences"""
        with self.client.get(
            f"/api/v1/users/{self.user_id}/preferences",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Profile] Get Preferences",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Get preferences failed: {response.status_code}")

    @task(1)
    def get_notifications(self):
        """Task: Get user notifications"""
        with self.client.get(
            "/api/v1/notifications",
            headers=get_headers(self.token),
            params={"limit": 10},
            catch_response=True,
            name="[Profile] Get Notifications",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get notifications failed: {response.status_code}")


# ==================== BASELINE VALIDATION ====================

@events.test_stop.add_hook
def validate_baseline_sla(environment, **kwargs):
    """
    Validate that baseline test meets SLA requirements.
    Fails the test if SLA thresholds are exceeded.
    """
    stats = environment.stats

    print("\n" + "=" * 80)
    print("BASELINE PERFORMANCE TEST RESULTS")
    print("=" * 80)

    # Calculate metrics
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    error_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

    response_times = stats.total
    p50 = response_times.median_response_time
    p95 = response_times.get_response_time_percentile(0.95)
    p99 = response_times.get_response_time_percentile(0.99)
    rps = stats.total.total_rps

    print(f"\nOverall Performance:")
    print(f"  Total Requests: {total_requests:,}")
    print(f"  Successful: {total_requests - total_failures:,}")
    print(f"  Failed: {total_failures:,}")
    print(f"  Error Rate: {error_rate:.2f}%")
    print(f"  Throughput: {rps:.2f} req/s")

    print(f"\nResponse Times:")
    print(f"  Median (p50): {p50}ms")
    print(f"  p95: {p95:.0f}ms")
    print(f"  p99: {p99:.0f}ms")
    print(f"  Min: {response_times.min_response_time}ms")
    print(f"  Max: {response_times.max_response_time}ms")

    # Validate against SLA
    print(f"\nSLA Validation:")

    sla_passed = True

    # Check p50
    if p50 <= BASELINE_SLA["p50"]:
        print(f"  ✅ p50 Response Time: {p50}ms <= {BASELINE_SLA['p50']}ms")
    else:
        print(f"  ❌ p50 Response Time: {p50}ms > {BASELINE_SLA['p50']}ms")
        sla_passed = False

    # Check p95
    if p95 <= BASELINE_SLA["p95"]:
        print(f"  ✅ p95 Response Time: {p95:.0f}ms <= {BASELINE_SLA['p95']}ms")
    else:
        print(f"  ❌ p95 Response Time: {p95:.0f}ms > {BASELINE_SLA['p95']}ms")
        sla_passed = False

    # Check p99
    if p99 <= BASELINE_SLA["p99"]:
        print(f"  ✅ p99 Response Time: {p99:.0f}ms <= {BASELINE_SLA['p99']}ms")
    else:
        print(f"  ❌ p99 Response Time: {p99:.0f}ms > {BASELINE_SLA['p99']}ms")
        sla_passed = False

    # Check error rate
    if error_rate <= BASELINE_SLA["max_error_rate"]:
        print(f"  ✅ Error Rate: {error_rate:.2f}% <= {BASELINE_SLA['max_error_rate']}%")
    else:
        print(f"  ❌ Error Rate: {error_rate:.2f}% > {BASELINE_SLA['max_error_rate']}%")
        sla_passed = False

    # Check throughput
    if rps >= BASELINE_SLA["min_throughput"]:
        print(f"  ✅ Throughput: {rps:.2f} req/s >= {BASELINE_SLA['min_throughput']} req/s")
    else:
        print(f"  ❌ Throughput: {rps:.2f} req/s < {BASELINE_SLA['min_throughput']} req/s")
        sla_passed = False

    # Overall result
    print("\n" + "=" * 80)
    if sla_passed:
        print("✅ BASELINE TEST PASSED - All SLA requirements met")
    else:
        print("❌ BASELINE TEST FAILED - SLA requirements not met")
    print("=" * 80 + "\n")

    # Log top 5 slowest endpoints
    print("\nTop 5 Slowest Endpoints:")
    sorted_stats = sorted(
        [s for s in stats.entries.values() if s.num_requests > 0],
        key=lambda x: x.avg_response_time,
        reverse=True,
    )[:5]

    for i, entry in enumerate(sorted_stats, 1):
        print(f"  {i}. {entry.name}:")
        print(f"     Avg: {entry.avg_response_time:.0f}ms, "
              f"Min: {entry.min_response_time}ms, "
              f"Max: {entry.max_response_time}ms, "
              f"Count: {entry.num_requests}")

    print("\n" + "=" * 80 + "\n")


@events.request.add_hook
def log_slow_requests(request_type, name, response_time, response_length, exception, **kwargs):
    """Log requests that exceed p99 threshold"""
    if exception:
        logger.error(f"Request failed: {name} - {exception}")
    elif response_time > BASELINE_SLA["p99"]:
        logger.warning(
            f"Slow request detected: {name} - {response_time}ms "
            f"(exceeds p99 threshold: {BASELINE_SLA['p99']}ms)"
        )


if __name__ == "__main__":
    import sys

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║          BASELINE PERFORMANCE LOAD TEST - PsychSync                  ║
╚══════════════════════════════════════════════════════════════════════╝

This test establishes baseline performance metrics under normal load.

Configuration:
  - Users: 100 concurrent
  - Duration: 10 minutes
  - Spawn Rate: 10 users/second

Traffic Distribution:
  - Assessment Tasks: 40%
  - Dashboard/Analytics: 20%
  - Authentication: 15%
  - Team Management: 15%
  - Profile Management: 10%

SLA Thresholds:
  - p50 Response Time: < 200ms
  - p95 Response Time: < 500ms
  - p99 Response Time: < 1000ms
  - Error Rate: < 1%
  - Throughput: > 100 RPS

Usage:
  locust -f baseline_scenarios.py --host https://api.psychsync.com \\
      --users 100 --spawn-rate 10 --run-time 10m \\
      --html reports/baseline_report.html

    """)

    if len(sys.argv) > 1:
        users = int(sys.argv[1])
    else:
        users = 100

    print(f"Starting baseline test with {users} users...")
    print("Target API:", LoadTestConfig.API_BASE_URL)
    print()
