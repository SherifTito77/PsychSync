"""
Authentication Load Test for PsychSync
Tests login, token refresh, and logout under concurrent load
"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import logging
import random
from datetime import datetime

from locust_config import LoadTestConfig, get_headers, log_response, test_data_manager

logger = logging.getLogger(__name__)


class AuthUser(HttpUser):
    """
    Simulates user authentication flows:
    - Login with credentials
    - Token refresh
    - Logout
    - Concurrent login from multiple devices
    """

    # Wait time between tasks (simulates realistic user behavior)
    wait_time = between(1, 3)

    def on_start(self):
        """Setup: Login and get access token"""
        self.token = None
        self.refresh_token = None
        self.user_credentials = test_data_manager.get_random_user()
        self.device_id = f"device_{random.randint(1, 1000)}"
        self.login()

    def login(self):
        """Perform login and store tokens"""
        credentials = self.user_credentials

        with self.client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": credentials["email"],
                "password": credentials["password"],
            },
            headers=get_headers(),
            catch_response=True,
            name="Auth: Login",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                response.success()
                logger.info(f"User {credentials['email']} logged in successfully")
            else:
                response.failure(f"Login failed: {response.status_code}")
                logger.error(f"Login failed for {credentials['email']}: {response.text[:200]}")

    @task(7)
    def login_with_refresh(self):
        """
        Task: Login with token refresh
        Weight: 7 (most frequent auth operation)
        """
        if not self.token:
            self.login()
            return

        # Try to refresh token
        with self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": self.refresh_token},
            headers=get_headers(),
            catch_response=True,
            name="Auth: Token Refresh",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                response.success()
            elif response.status_code == 401:
                # Token expired, do full login
                self.login()
                response.success()
            else:
                response.failure(f"Token refresh failed: {response.status_code}")

    @task(2)
    def verify_current_user(self):
        """
        Task: Verify current user endpoint
        Weight: 2
        """
        if not self.token:
            self.login()
            return

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

    @task(1)
    def logout(self):
        """
        Task: Logout and login again
        Weight: 1 (least frequent)
        """
        if not self.token:
            return

        with self.client.post(
            "/api/v1/auth/logout",
            headers=get_headers(self.token),
            catch_response=True,
            name="Auth: Logout",
        ) as response:
            if response.status_code in [200, 204]:
                response.success()
                self.token = None
                self.refresh_token = None
                # Login again after logout
                self.login()
            else:
                response.failure(f"Logout failed: {response.status_code}")

    @task(1)
    def concurrent_device_login(self):
        """
        Task: Simulate login from multiple devices
        Weight: 1
        """
        credentials = self.user_credentials

        with self.client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": credentials["email"],
                "password": credentials["password"],
                "device_id": self.device_id,
            },
            headers=get_headers(),
            catch_response=True,
            name="Auth: Concurrent Device Login",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                response.success()
            else:
                response.failure(f"Concurrent login failed: {response.status_code}")


# Performance monitoring hooks
@events.request.add_hook
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    Monitor request performance and log anomalies
    """
    if exception:
        logger.error(f"Request failed: {name} - {exception}")
    elif response_time > LoadTestConfig.THRESHOLDS["p99"]:
        logger.warning(
            f"Slow request: {name} - {response_time}ms "
            f"(threshold: {LoadTestConfig.THRESHOLDS['p99']}ms)"
        )


@events.test_stop.add_hook
def on_test_stop(environment, **kwargs):
    """
    Log test summary when test stops
    """
    if isinstance(environment.runner, MasterRunner):
        logger.info("Master test stopped")
    else:
        logger.info("Worker test stopped")

    logger.info(f"Total requests: {environment.stats.total.num_requests}")
    logger.info(f"Failures: {environment.stats.total.num_failures}")
    logger.info(f"Median response time: {environment.stats.total.median_response_time}ms")
    logger.info(f"Average response time: {environment.stats.total.avg_response_time}ms")


if __name__ == "__main__":
    # Run this file directly for quick testing
    import sys

    if len(sys.argv) > 1:
        users = int(sys.argv[1])
    else:
        users = 100

    print(f"Starting authentication load test with {users} users...")
    print("Target API: ", LoadTestConfig.API_BASE_URL)
    print("\nPress Ctrl+C to stop the test\n")

    from locust import run_single_user

    # For quick debugging, run single user
    # run_single_user(AuthUser)
