"""
Assessment Taking Load Test for PsychSync
Tests the complete assessment flow: start, save responses, complete, view results
"""

from locust import HttpUser, task, between, events
import logging
import random
import json
from datetime import datetime, timedelta

from locust_config import (
    LoadTestConfig,
    get_headers,
    log_response,
    test_data_manager,
)

logger = logging.getLogger(__name__)


class AssessmentUser(HttpUser):
    """
    Simulates users taking psychological assessments:
    - Browse available assessments
    - Start assessment
    - Submit responses (auto-save)
    - Complete assessment
    - View results
    """

    wait_time = between(2, 5)  # Longer wait time for realistic assessment taking

    def on_start(self):
        """Setup: Login and get token"""
        self.token = None
        self.user_credentials = test_data_manager.get_random_user()
        self.current_assessment_id = None
        self.current_framework = None
        self.responses_submitted = 0
        self.total_responses = 0
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
            name="Assessment: Login",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                response.success()
                logger.info(f"User logged in: {credentials['email']}")
            else:
                response.failure(f"Login failed: {response.status_code}")
                logger.error(f"Login failed: {response.text[:200]}")

    @task(5)
    def browse_assessment_frameworks(self):
        """
        Task: Browse available assessment frameworks
        Weight: 5
        """
        with self.client.get(
            "/api/v1/personality-assessments/frameworks",
            headers=get_headers(self.token),
            catch_response=True,
            name="Assessment: Browse Frameworks",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Browse frameworks failed: {response.status_code}")

    @task(10)
    def start_assessment(self):
        """
        Task: Start a new assessment
        Weight: 10
        """
        framework = test_data_manager.get_random_framework()
        self.current_framework = framework

        with self.client.post(
            f"/api/v1/assessments/{test_data_manager.get_random_assessment_id()}/start",
            headers=get_headers(self.token),
            json={
                "framework": framework,
                "started_at": datetime.utcnow().isoformat(),
            },
            catch_response=True,
            name="Assessment: Start",
        ) as response:
            if response.status_code in [200, 201]:
                data = response.json()
                self.current_assessment_id = data.get("assessment_id") or data.get("id")
                self.responses_submitted = 0
                self.total_responses = random.randint(20, 100)
                response.success()
                logger.info(
                    f"Started assessment: {framework} "
                    f"(ID: {self.current_assessment_id})"
                )
            else:
                response.failure(f"Start assessment failed: {response.status_code}")

    @task(20)
    def submit_responses(self):
        """
        Task: Submit assessment responses (auto-save during assessment)
        Weight: 20 (most frequent operation during assessment taking)
        """
        if not self.current_assessment_id:
            self.start_assessment()
            return

        if self.responses_submitted >= self.total_responses:
            # Assessment complete, move to completion
            self.complete_assessment()
            return

        # Submit a batch of responses (simulate auto-save)
        batch_size = random.randint(1, 5)
        responses = [
            {
                "question_id": f"q{self.responses_submitted + i + 1}",
                "answer": random.randint(1, 5),
                "timestamp": datetime.utcnow().isoformat(),
            }
            for i in range(batch_size)
        ]

        with self.client.post(
            f"/api/v1/assessments/{self.current_assessment_id}/responses",
            headers=get_headers(self.token),
            json={"responses": responses},
            catch_response=True,
            name="Assessment: Submit Responses",
        ) as response:
            if response.status_code in [200, 201]:
                self.responses_submitted += batch_size
                response.success()
            else:
                response.failure(f"Submit responses failed: {response.status_code}")

    @task(5)
    def complete_assessment(self):
        """
        Task: Complete assessment and calculate results
        Weight: 5
        """
        if not self.current_assessment_id:
            return

        with self.client.post(
            f"/api/v1/assessments/{self.current_assessment_id}/complete",
            headers=get_headers(self.token),
            json={
                "completed_at": datetime.utcnow().isoformat(),
                "framework": self.current_framework,
            },
            catch_response=True,
            name="Assessment: Complete",
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
                logger.info(
                    f"Completed assessment: {self.current_assessment_id} "
                    f"({self.responses_submitted} responses)"
                )
                # Reset for next assessment
                self.current_assessment_id = None
                self.current_framework = None
                self.responses_submitted = 0
            else:
                response.failure(f"Complete assessment failed: {response.status_code}")

    @task(8)
    def view_results(self):
        """
        Task: View assessment results
        Weight: 8
        """
        # Either view current assessment or a historical one
        assessment_id = self.current_assessment_id or test_data_manager.get_random_assessment_id()

        with self.client.get(
            f"/api/v1/assessments/{assessment_id}/results",
            headers=get_headers(self.token),
            catch_response=True,
            name="Assessment: View Results",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Results not ready yet, that's okay
                response.success()
            else:
                response.failure(f"View results failed: {response.status_code}")

    @task(3)
    def get_assessment_progress(self):
        """
        Task: Get current assessment progress
        Weight: 3
        """
        if not self.current_assessment_id:
            return

        with self.client.get(
            f"/api/v1/assessments/{self.current_assessment_id}/progress",
            headers=get_headers(self.token),
            catch_response=True,
            name="Assessment: Get Progress",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get progress failed: {response.status_code}")

    @task(2)
    def pause_and_resume_assessment(self):
        """
        Task: Pause assessment (simulate user stepping away)
        Weight: 2
        """
        if not self.current_assessment_id:
            return

        # Pause assessment
        with self.client.post(
            f"/api/v1/assessments/{self.current_assessment_id}/pause",
            headers=get_headers(self.token),
            json={
                "paused_at": datetime.utcnow().isoformat(),
                "reason": "user_initiated",
            },
            catch_response=True,
            name="Assessment: Pause",
        ) as response:
            if response.status_code in [200, 201]:
                response.success()

                # Resume after a delay (simulated by next task)
                logger.info(f"Paused assessment: {self.current_assessment_id}")
            else:
                response.failure(f"Pause assessment failed: {response.status_code}")

    @task(2)
    def resume_assessment(self):
        """
        Task: Resume paused assessment
        Weight: 2
        """
        if not self.current_assessment_id:
            return

        with self.client.post(
            f"/api/v1/assessments/{self.current_assessment_id}/resume",
            headers=get_headers(self.token),
            json={
                "resumed_at": datetime.utcnow().isoformat(),
            },
            catch_response=True,
            name="Assessment: Resume",
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
                logger.info(f"Resumed assessment: {self.current_assessment_id}")
            else:
                response.failure(f"Resume assessment failed: {response.status_code}")


# Performance monitoring
@events.request.add_hook
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Monitor performance and log slow requests"""
    if exception:
        logger.error(f"Request exception: {name} - {exception}")
    elif response_time > LoadTestConfig.THRESHOLDS["p99"]:
        logger.warning(
            f"Slow assessment request: {name} - {response_time}ms "
            f"(p99 threshold: {LoadTestConfig.THRESHOLDS['p99']}ms)"
        )


@events.test_stop.add_hook
def on_test_stop(environment, **kwargs):
    """Log test summary"""
    stats = environment.stats
    logger.info("=" * 60)
    logger.info("ASSESSMENT LOAD TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Failures: {stats.total.num_failures}")
    logger.info(f"Failure rate: {(stats.total.num_failures / stats.total.num_requests * 100):.2f}%")
    logger.info(f"Median response time: {stats.total.median_response_time}ms")
    logger.info(f"Average response time: {stats.total.avg_response_time}ms")
    logger.info(f"Min response time: {stats.total.min_response_time}ms")
    logger.info(f"Max response time: {stats.total.max_response_time}ms")
    logger.info("=" * 60)


if __name__ == "__main__":
    import sys

    users = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    print(f"Starting assessment load test with {users} users...")
    print("Target API:", LoadTestConfig.API_BASE_URL)
