"""
Production Readiness Load Test for PsychSync

Purpose: Verify system can handle production-level load.
Target: 1,000 concurrent users for 30 minutes.
Use Case: Validate system is ready for production deployment.

Production SLA Thresholds:
- p50 Response Time: < 300ms
- p95 Response Time: < 500ms
- p99 Response Time: < 1000ms
- Error Rate: < 1%
- Throughput: > 500 RPS

User Distribution (matches production demographics):
- 70% Regular users (viewing assessments, basic analytics)
- 20% Team leads (team management, team analytics)
- 10% Admins (user management, system administration)

Usage:
    locust -f production_scenarios.py --host https://api.psychsync.com \\
        --users 1000 --spawn-rate 50 --run-time 30m \\
        --html reports/production_report.html

For distributed testing with multiple workers:
    locust -f production_scenarios.py --master --host https://api.psychsync.com \\
        --users 1000 --spawn-rate 50 --run-time 30m \\
        --expect-workers 4 --html reports/production_report.html

    locust -f production_scenarios.py --worker --host https://api.psychsync.com
"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import logging
import random
from datetime import datetime
from typing import Dict, Any

from locust_config import (
    LoadTestConfig,
    get_headers,
    test_data_manager,
)

logger = logging.getLogger(__name__)


# Production SLA Thresholds
PRODUCTION_SLA = {
    "p50": 300,   # 50th percentile: < 300ms
    "p95": 500,   # 95th percentile: < 500ms
    "p99": 1000,  # 99th percentile: < 1000ms
    "max_error_rate": 1.0,  # Max 1% error rate
    "min_throughput": 500,  # Min 500 requests/second
}


# User type weights
USER_TYPE_WEIGHTS = {
    "regular": 0.70,   # 70% regular users
    "team_lead": 0.20, # 20% team leads
    "admin": 0.10      # 10% admins
}


class ProductionUser(HttpUser):
    """
    Simulates realistic production user behavior with mixed user types.

    Traffic Distribution (Production-grade):
    - Regular Users (70%):
      - 50% Assessment viewing and completion
      - 25% Personal analytics and dashboard
      - 15% Profile management
      - 10% Authentication

    - Team Leads (20%):
      - 35% Team analytics and insights
      - 25% Team member management
      - 20% Assessment assignments
      - 15% Team performance tracking
      - 5% Authentication

    - Admins (10%):
      - 40% User management and administration
      - 25% System-wide analytics
      - 20% Organization management
      - 10% Platform settings
      - 5% Authentication
    """

    # Realistic wait time between tasks (1-5 seconds)
    wait_time = between(1, 5)

    def on_start(self):
        """Setup: Login and initialize user session with role-based context"""
        self.token = None
        self.user_id = None
        self.user_type = self._assign_user_type()
        self.user_credentials = test_data_manager.get_random_user()
        self.team_id = test_data_manager.get_random_team_id()
        self.organization_id = test_data_manager.get_random_organization_id()
        self.assessment_id = test_data_manager.get_random_assessment_id()

        # Login
        self.login()

        # Log user type for debugging
        logger.info(f"Started {self.user_type} user: {self.user_credentials['email']}")

    def _assign_user_type(self) -> str:
        """Assign user type based on production distribution"""
        rand = random.random()
        if rand < USER_TYPE_WEIGHTS["regular"]:
            return "regular"
        elif rand < USER_TYPE_WEIGHTS["regular"] + USER_TYPE_WEIGHTS["team_lead"]:
            return "team_lead"
        else:
            return "admin"

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

    # ==================== REGULAR USER TASKS (70% of users) ====================

    @task(10)
    def regular_view_assessments(self):
        """Task: Regular user viewing their assessments"""
        if self.user_type != "regular":
            return

        with self.client.get(
            "/api/v1/assessments",
            headers=get_headers(self.token),
            params={"limit": 20, "skip": random.randint(0, 100)},
            catch_response=True,
            name="[Regular] View My Assessments",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"View failed: {response.status_code}")

    @task(8)
    def regular_browse_frameworks(self):
        """Task: Regular user browsing assessment frameworks"""
        if self.user_type != "regular":
            return

        with self.client.get(
            "/api/v1/personality-assessments/frameworks",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Regular] Browse Frameworks",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Browse failed: {response.status_code}")

    @task(7)
    def regular_take_assessment(self):
        """Task: Regular user taking/completing assessment"""
        if self.user_type != "regular":
            return

        framework = random.choice(["MBTI", "BigFive", "Enneagram"])

        with self.client.get(
            f"/api/v1/assessment-questions/{framework.lower()}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Regular] Get Assessment Questions",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Get questions failed: {response.status_code}")

    @task(6)
    def regular_view_results(self):
        """Task: Regular user viewing assessment results"""
        if self.user_type != "regular":
            return

        with self.client.get(
            f"/api/v1/assessments/{self.assessment_id}/results",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Regular] View Results",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"View results failed: {response.status_code}")

    @task(5)
    def regular_personal_dashboard(self):
        """Task: Regular user viewing personal dashboard"""
        if self.user_type != "regular":
            return

        with self.client.get(
            "/api/v1/analytics/dashboard",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Regular] Personal Dashboard",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard failed: {response.status_code}")

    @task(3)
    def regular_update_profile(self):
        """Task: Regular user updating profile"""
        if self.user_type != "regular":
            return

        with self.client.patch(
            f"/api/v1/users/{self.user_id}",
            headers=get_headers(self.token),
            json={"bio": f"Updated at {datetime.now().isoformat()}"},
            catch_response=True,
            name="[Regular] Update Profile",
        ) as response:
            if response.status_code in [200, 403]:
                response.success()
            else:
                response.failure(f"Update failed: {response.status_code}")

    # ==================== TEAM LEAD TASKS (20% of users) ====================

    @task(7)
    def team_lead_view_team_analytics(self):
        """Task: Team lead viewing team analytics"""
        if self.user_type != "team_lead":
            return

        with self.client.get(
            f"/api/v1/analytics/team/{self.team_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Team Lead] Team Analytics",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Team analytics failed: {response.status_code}")

    @task(6)
    def team_lead_view_members(self):
        """Task: Team lead viewing team members"""
        if self.user_type != "team_lead":
            return

        with self.client.get(
            f"/api/v1/teams/{self.team_id}/members",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Team Lead] View Members",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"View members failed: {response.status_code}")

    @task(5)
    def team_lead_team_performance(self):
        """Task: Team lead viewing team performance"""
        if self.user_type != "team_lead":
            return

        with self.client.get(
            f"/api/v1/teams/{self.team_id}/performance",
            headers=get_headers(self.token),
            params={"period": random.choice(["7d", "30d", "90d"])},
            catch_response=True,
            name="[Team Lead] Team Performance",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Performance failed: {response.status_code}")

    @task(4)
    def team_lead_assign_assessment(self):
        """Task: Team lead assigning assessment to team"""
        if self.user_type != "team_lead":
            return

        with self.client.post(
            f"/api/v1/teams/{self.team_id}/assessments",
            headers=get_headers(self.token),
            json={
                "assessment_id": self.assessment_id,
                "due_date": "2025-12-31"
            },
            catch_response=True,
            name="[Team Lead] Assign Assessment",
        ) as response:
            if response.status_code in [200, 201, 403]:
                response.success()
            else:
                response.failure(f"Assign failed: {response.status_code}")

    @task(3)
    def team_lead_view_insights(self):
        """Task: Team lead viewing team insights"""
        if self.user_type != "team_lead":
            return

        with self.client.get(
            f"/api/v1/ai/insights/team/{self.team_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Team Lead] Team Insights",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Insights failed: {response.status_code}")

    # ==================== ADMIN TASKS (10% of users) ====================

    @task(6)
    def admin_list_users(self):
        """Task: Admin listing users"""
        if self.user_type != "admin":
            return

        with self.client.get(
            "/api/v1/users/",
            headers=get_headers(self.token),
            params={"limit": 50, "skip": random.randint(0, 200)},
            catch_response=True,
            name="[Admin] List Users",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List users failed: {response.status_code}")

    @task(5)
    def admin_system_analytics(self):
        """Task: Admin viewing system-wide analytics"""
        if self.user_type != "admin":
            return

        with self.client.get(
            "/api/v1/analytics/system",
            headers=get_headers(self.token),
            params={"period": "30d"},
            catch_response=True,
            name="[Admin] System Analytics",
        ) as response:
            if response.status_code in [200, 403]:
                response.success()
            else:
                response.failure(f"System analytics failed: {response.status_code}")

    @task(4)
    def admin_view_organization(self):
        """Task: Admin viewing organization details"""
        if self.user_type != "admin":
            return

        with self.client.get(
            f"/api/v1/organizations/{self.organization_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Admin] View Organization",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"View org failed: {response.status_code}")

    @task(3)
    def admin_user_activity(self):
        """Task: Admin viewing user activity logs"""
        if self.user_type != "admin":
            return

        with self.client.get(
            "/api/v1/analytics/activity",
            headers=get_headers(self.token),
            params={"limit": 100},
            catch_response=True,
            name="[Admin] User Activity",
        ) as response:
            if response.status_code in [200, 403]:
                response.success()
            else:
                response.failure(f"Activity failed: {response.status_code}")

    @task(2)
    def admin_platform_settings(self):
        """Task: Admin viewing platform settings"""
        if self.user_type != "admin":
            return

        with self.client.get(
            "/api/v1/admin/settings",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Admin] Platform Settings",
        ) as response:
            if response.status_code in [200, 403]:
                response.success()
            else:
                response.failure(f"Settings failed: {response.status_code}")

    # ==================== SHARED TASKS (All user types) ====================

    @task(5)
    def refresh_token(self):
        """Task: Token refresh (all users)"""
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

    @task(3)
    def verify_user(self):
        """Task: Verify current user (all users)"""
        with self.client.get(
            "/api/v1/users/me",
            headers=get_headers(self.token),
            catch_response=True,
            name="[Auth] Verify User",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Verify failed: {response.status_code}")

    @task(2)
    def get_notifications(self):
        """Task: Get notifications (all users)"""
        with self.client.get(
            "/api/v1/notifications",
            headers=get_headers(self.token),
            params={"limit": 20},
            catch_response=True,
            name="[Shared] Get Notifications",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Notifications failed: {response.status_code}")


# ==================== PRODUCTION VALIDATION ====================

@events.test_stop.add_hook
def validate_production_sla(environment, **kwargs):
    """
    Validate that production test meets SLA requirements.
    Fails the test if SLA thresholds are exceeded.
    """
    stats = environment.stats

    print("\n" + "=" * 80)
    print("PRODUCTION READINESS TEST RESULTS")
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
    print(f"\nProduction SLA Validation:")

    sla_passed = True

    # Check p50
    if p50 <= PRODUCTION_SLA["p50"]:
        print(f"  ✅ p50 Response Time: {p50}ms <= {PRODUCTION_SLA['p50']}ms")
    else:
        print(f"  ❌ p50 Response Time: {p50}ms > {PRODUCTION_SLA['p50']}ms")
        sla_passed = False

    # Check p95
    if p95 <= PRODUCTION_SLA["p95"]:
        print(f"  ✅ p95 Response Time: {p95:.0f}ms <= {PRODUCTION_SLA['p95']}ms")
    else:
        print(f"  ❌ p95 Response Time: {p95:.0f}ms > {PRODUCTION_SLA['p95']}ms")
        sla_passed = False

    # Check p99
    if p99 <= PRODUCTION_SLA["p99"]:
        print(f"  ✅ p99 Response Time: {p99:.0f}ms <= {PRODUCTION_SLA['p99']}ms")
    else:
        print(f"  ❌ p99 Response Time: {p99:.0f}ms > {PRODUCTION_SLA['p99']}ms")
        sla_passed = False

    # Check error rate
    if error_rate <= PRODUCTION_SLA["max_error_rate"]:
        print(f"  ✅ Error Rate: {error_rate:.2f}% <= {PRODUCTION_SLA['max_error_rate']}%")
    else:
        print(f"  ❌ Error Rate: {error_rate:.2f}% > {PRODUCTION_SLA['max_error_rate']}%")
        sla_passed = False

    # Check throughput
    if rps >= PRODUCTION_SLA["min_throughput"]:
        print(f"  ✅ Throughput: {rps:.2f} req/s >= {PRODUCTION_SLA['min_throughput']} req/s")
    else:
        print(f"  ❌ Throughput: {rps:.2f} req/s < {PRODUCTION_SLA['min_throughput']} req/s")
        sla_passed = False

    # Overall result
    print("\n" + "=" * 80)
    if sla_passed:
        print("✅ PRODUCTION TEST PASSED - System is ready for production")
    else:
        print("❌ PRODUCTION TEST FAILED - System is NOT ready for production")
    print("=" * 80 + "\n")

    # Performance by endpoint type
    print("\nPerformance by Endpoint Type:")

    # Group by user type
    user_types = ["Regular", "Team Lead", "Admin", "Auth", "Shared"]
    for user_type in user_types:
        type_stats = [
            s for s in stats.entries.values()
            if user_type.lower() in s.name.lower()
        ]
        if type_stats:
            total_rps = sum(s.total_rps for s in type_stats)
            avg_resp = sum(s.avg_response_time for s in type_stats) / len(type_stats)
            print(f"  {user_type}: {total_rps:.1f} RPS, Avg {avg_resp:.0f}ms")

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
              f"p95: {entry.get_response_time_percentile(0.95):.0f}ms, "
              f"Count: {entry.num_requests:,}")

    # Top 5 highest throughput endpoints
    print("\nTop 5 Highest Throughput Endpoints:")
    sorted_by_rps = sorted(
        [s for s in stats.entries.values() if s.num_requests > 0],
        key=lambda x: x.total_rps,
        reverse=True,
    )[:5]

    for i, entry in enumerate(sorted_by_rps, 1):
        print(f"  {i}. {entry.name}:")
        print(f"     RPS: {entry.total_rps:.1f}, "
              f"Avg: {entry.avg_response_time:.0f}ms, "
              f"Count: {entry.num_requests:,}")

    print("\n" + "=" * 80 + "\n")


@events.request.add_hook
def log_performance_issues(request_type, name, response_time, response_length, exception, **kwargs):
    """Log performance issues and anomalies"""
    if exception:
        logger.error(f"Request failed: {name} - {exception}")
    elif response_time > PRODUCTION_SLA["p99"]:
        logger.warning(
            f"Slow request detected: {name} - {response_time}ms "
            f"(exceeds p99 threshold: {PRODUCTION_SLA['p99']}ms)"
        )


@events.spawning_complete.add_hook
def on_spawning_complete(user_count, **kwargs):
    """Log when all users have been spawned"""
    logger.info(f"✅ Spawning complete: {user_count} production users are now active")
    logger.info(f"Starting 30-minute production readiness test...")


if __name__ == "__main__":
    import sys

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║        PRODUCTION READINESS LOAD TEST - PsychSync                   ║
╚══════════════════════════════════════════════════════════════════════╝

This test validates production readiness under high load.

Configuration:
  - Users: 1,000 concurrent (simulating production peak)
  - Duration: 30 minutes
  - Spawn Rate: 50 users/second

User Distribution (Production):
  - Regular Users: 70% (assessments, personal analytics)
  - Team Leads: 20% (team management, team analytics)
  - Admins: 10% (user management, system administration)

Production SLA Thresholds:
  - p50 Response Time: < 300ms
  - p95 Response Time: < 500ms
  - p99 Response Time: < 1000ms
  - Error Rate: < 1%
  - Throughput: > 500 RPS

Usage:
  # Single-machine test
  locust -f production_scenarios.py --host https://api.psychsync.com \\
      --users 1000 --spawn-rate 50 --run-time 30m \\
      --html reports/production_report.html

  # Distributed test (1 master + 4 workers)
  # Master:
  locust -f production_scenarios.py --master --host https://api.psychsync.com \\
      --users 1000 --spawn-rate 50 --run-time 30m \\
      --expect-workers 4 --html reports/production_report.html

  # Workers (run on 4 separate machines):
  locust -f production_scenarios.py --worker --host https://api.psychsync.com

    """)

    if len(sys.argv) > 1:
        users = int(sys.argv[1])
    else:
        users = 1000

    print(f"Starting production test with {users} users...")
    print("Target API:", LoadTestConfig.API_BASE_URL)
    print()
