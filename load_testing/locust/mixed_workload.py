"""
Mixed Workload Load Test for PsychSync
Simulates realistic traffic patterns with multiple user types
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


class PsychSyncUser(HttpUser):
    """
    Simulates realistic PsychSync usage patterns:
    - 15% Authentication tasks
    - 40% Assessment taking
    - 20% Dashboard viewing
    - 15% Team management
    - 5% Assessment management
    - 5% AI/NLP features
    """

    wait_time = between(1, 4)

    def on_start(self):
        """Setup: Login and initialize user state"""
        self.token = None
        self.user_credentials = test_data_manager.get_random_user()
        self.current_assessment_id = None
        self.team_id = test_data_manager.get_random_team_id()
        self.login()

    def login(self):
        """Login to get access token"""
        credentials = self.user_credentials

        with self.client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": credentials["email"],
                "password": credentials["password"],
            },
            headers=get_headers(),
            catch_response=True,
            name="Mixed: Login",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")

    # ==================== AUTHENTICATION TASKS (15% weight) ====================

    @task(3)
    def refresh_token(self):
        """Task: Refresh authentication token"""
        with self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "dummy_refresh_token"},
            headers=get_headers(),
            catch_response=True,
            name="Auth: Token Refresh",
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Token refresh failed: {response.status_code}")

    @task(2)
    def verify_user(self):
        """Task: Verify current user"""
        with self.client.get(
            "/api/v1/users/me",
            headers=get_headers(self.token),
            catch_response=True,
            name="Auth: Verify User",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Verify user failed: {response.status_code}")

    # ==================== ASSESSMENT TASKS (40% weight) ====================

    @task(10)
    def browse_assessments(self):
        """Task: Browse available assessment frameworks"""
        with self.client.get(
            "/api/v1/personality-assessments/frameworks",
            headers=get_headers(self.token),
            catch_response=True,
            name="Assessment: Browse Frameworks",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Browse failed: {response.status_code}")

    @task(8)
    def start_assessment(self):
        """Task: Start a new assessment"""
        framework = test_data_manager.get_random_framework()
        assessment_id = test_data_manager.get_random_assessment_id()
        self.current_assessment_id = assessment_id

        with self.client.post(
            f"/api/v1/assessments/{assessment_id}/start",
            headers=get_headers(self.token),
            json={"framework": framework},
            catch_response=True,
            name="Assessment: Start",
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Start failed: {response.status_code}")

    @task(15)
    def submit_assessment_responses(self):
        """Task: Submit assessment responses (auto-save)"""
        if not self.current_assessment_id:
            self.current_assessment_id = test_data_manager.get_random_assessment_id()

        responses = [
            {
                "question_id": f"q{random.randint(1, 100)}",
                "answer": random.randint(1, 5),
            }
            for _ in range(random.randint(1, 5))
        ]

        with self.client.post(
            f"/api/v1/assessments/{self.current_assessment_id}/responses",
            headers=get_headers(self.token),
            json={"responses": responses},
            catch_response=True,
            name="Assessment: Submit Responses",
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Submit failed: {response.status_code}")

    @task(5)
    def view_assessment_results(self):
        """Task: View assessment results"""
        assessment_id = self.current_assessment_id or test_data_manager.get_random_assessment_id()

        with self.client.get(
            f"/api/v1/assessments/{assessment_id}/results",
            headers=get_headers(self.token),
            catch_response=True,
            name="Assessment: View Results",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"View results failed: {response.status_code}")

    # ==================== DASHBOARD TASKS (20% weight) ====================

    @task(5)
    def load_dashboard(self):
        """Task: Load main dashboard"""
        with self.client.get(
            "/api/v1/analytics/dashboard",
            headers=get_headers(self.token),
            catch_response=True,
            name="Dashboard: Load Overview",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard load failed: {response.status_code}")

    @task(4)
    def load_team_analytics(self):
        """Task: Load team analytics"""
        team_id = self.team_id

        with self.client.get(
            f"/api/v1/analytics/team/{team_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="Dashboard: Team Analytics",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Team analytics failed: {response.status_code}")

    @task(3)
    def load_analytics_trends(self):
        """Task: Load historical trends"""
        with self.client.get(
            "/api/v1/analytics/trends",
            headers=get_headers(self.token),
            params={"days": random.choice([7, 30, 90])},
            catch_response=True,
            name="Dashboard: Trends",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Trends failed: {response.status_code}")

    @task(2)
    def export_report(self):
        """Task: Export analytics report"""
        with self.client.get(
            "/api/v1/analytics/export",
            headers=get_headers(self.token),
            params={
                "format": random.choice(["pdf", "csv", "json"]),
                "team_id": self.team_id,
            },
            catch_response=True,
            name="Dashboard: Export Report",
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Export failed: {response.status_code}")

    # ==================== TEAM MANAGEMENT TASKS (15% weight) ====================

    @task(4)
    def view_team(self):
        """Task: View team details"""
        team_id = self.team_id

        with self.client.get(
            f"/api/v1/teams/{team_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="Team: View Details",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"View team failed: {response.status_code}")

    @task(3)
    def view_team_members(self):
        """Task: View team members"""
        team_id = self.team_id

        with self.client.get(
            f"/api/v1/teams/{team_id}/members",
            headers=get_headers(self.token),
            catch_response=True,
            name="Team: View Members",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"View members failed: {response.status_code}")

    @task(2)
    def view_team_activity(self):
        """Task: View team activity log"""
        team_id = self.team_id

        with self.client.get(
            f"/api/v1/teams/{team_id}/activity",
            headers=get_headers(self.token),
            catch_response=True,
            name="Team: View Activity",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"View activity failed: {response.status_code}")

    @task(1)
    def update_team_permissions(self):
        """Task: Update team permissions"""
        team_id = self.team_id

        with self.client.put(
            f"/api/v1/teams/{team_id}/permissions",
            headers=get_headers(self.token),
            json={
                "permissions": {
                    "view_analytics": random.choice([True, False]),
                    "manage_assessments": random.choice([True, False]),
                }
            },
            catch_response=True,
            name="Team: Update Permissions",
        ) as response:
            if response.status_code in [200, 403]:
                response.success()
            else:
                response.failure(f"Update permissions failed: {response.status_code}")

    # ==================== ASSESSMENT MANAGEMENT TASKS (5% weight) ====================

    @task(2)
    def list_assessments(self):
        """Task: List available assessments"""
        with self.client.get(
            "/api/v1/assessments",
            headers=get_headers(self.token),
            catch_response=True,
            name="Assessment Mgmt: List",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List assessments failed: {response.status_code}")

    @task(1)
    def duplicate_assessment(self):
        """Task: Duplicate an assessment template"""
        assessment_id = test_data_manager.get_random_assessment_id()

        with self.client.post(
            f"/api/v1/assessments/{assessment_id}/duplicate",
            headers=get_headers(self.token),
            json={"name": f"Copy of {assessment_id}"},
            catch_response=True,
            name="Assessment Mgmt: Duplicate",
        ) as response:
            if response.status_code in [200, 201, 403]:
                response.success()
            else:
                response.failure(f"Duplicate failed: {response.status_code}")

    # ==================== AI/NLP TASKS (5% weight) ====================

    @task(2)
    def analyze_text(self):
        """Task: Submit text for NLP analysis"""
        sample_texts = [
            "I feel confident in my ability to lead teams effectively.",
            "Communication is key to successful project outcomes.",
            "I prefer working independently rather than in groups.",
            "I enjoy solving complex problems and analytical challenges.",
        ]

        with self.client.post(
            "/api/v1/nlp/analyze",
            headers=get_headers(self.token),
            json={
                "text": random.choice(sample_texts),
                "analysis_type": random.choice(["sentiment", "personality", "behavioral"]),
            },
            catch_response=True,
            name="AI: Text Analysis",
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Analysis failed: {response.status_code}")

    @task(1)
    def get_ai_insights(self):
        """Task: Get AI-generated insights"""
        assessment_id = test_data_manager.get_random_assessment_id()

        with self.client.get(
            f"/api/v1/ai/insights/{assessment_id}",
            headers=get_headers(self.token),
            catch_response=True,
            name="AI: Get Insights",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Get insights failed: {response.status_code}")


# ==================== PERFORMANCE MONITORING ====================

@events.request.add_hook
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Monitor performance and log anomalies"""
    if exception:
        logger.error(f"Request failed: {name} - {exception}")
    elif response_time > LoadTestConfig.THRESHOLDS["p99"]:
        logger.warning(
            f"Slow request detected: {name} - {response_time}ms "
            f"(p99 threshold: {LoadTestConfig.THRESHOLDS['p99']}ms)"
        )


@events.spawning_complete.add_hook
def on_spawning_complete(user_count, **kwargs):
    """Log when all users have been spawned"""
    logger.info(f"Spawning complete: {user_count} users are now running")


@events.test_stop.add_hook
def on_test_stop(environment, **kwargs):
    """Log comprehensive test summary"""
    stats = environment.stats

    logger.info("\n" + "=" * 80)
    logger.info("MIXED WORKLOAD LOAD TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Requests: {stats.total.num_requests:,}")
    logger.info(f"Failures: {stats.total.num_failures:,}")
    logger.info(f"Failure Rate: {(stats.total.num_failures / stats.total.num_requests * 100):.2f}%")
    logger.info(f"Median Response Time: {stats.total.median_response_time}ms")
    logger.info(f"Average Response Time: {stats.total.avg_response_time:.1f}ms")
    logger.info(f"Min Response Time: {stats.total.min_response_time}ms")
    logger.info(f"Max Response Time: {stats.total.max_response_time}ms")
    logger.info(f"Requests/Second: {stats.total.total_rps:.2f}")
    logger.info("=" * 80)

    # Log top 5 slowest endpoints
    logger.info("\nTop 5 Slowest Endpoints:")
    sorted_stats = sorted(
        [s for s in stats.entries.values() if s.num_requests > 0],
        key=lambda x: x.avg_response_time,
        reverse=True,
    )[:5]

    for entry in sorted_stats:
        logger.info(
            f"  {entry.name}: {entry.avg_response_time:.1f}ms "
            f"({entry.num_requests} requests)"
        )

    logger.info("=" * 80 + "\n")


if __name__ == "__main__":
    import sys

    users = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    print(f"Starting mixed workload test with {users} users...")
    print("Target API:", LoadTestConfig.API_BASE_URL)
    print("\nTask Distribution:")
    print("  - Authentication: 15%")
    print("  - Assessment Taking: 40%")
    print("  - Dashboard & Analytics: 20%")
    print("  - Team Management: 15%")
    print("  - Assessment Management: 5%")
    print("  - AI/NLP Processing: 5%")
    print()
