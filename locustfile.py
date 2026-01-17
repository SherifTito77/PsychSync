from locust import HttpUser, task, between
import random
import string

class PsychSyncUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Setup: register and login user"""
        # Generate unique user for this load test
        self.email = f"loadtest_{''.join(random.choices(string.ascii_lowercase, k=8))}@example.com"
        self.password = "LoadTest123!"

        # Register user
        response = self.client.post("/api/v1/register", json={
            "email": self.email,
            "password": self.password,
            "full_name": "Load Test User"
        })

        if response.status_code in [200, 201]:
            # Login to get token
            login_response = self.client.post("/api/v1/token", data={
                "username": self.email,
                "password": self.password
            })

            if login_response.status_code == 200:
                self.token = login_response.json().get("access_token")
            else:
                self.token = None
        else:
            self.token = None

    @task(3)
    def health_check(self):
        """Check API health (most common operation)"""
        self.client.get("/health")

    @task(2)
    def view_profile(self):
        """View user profile"""
        if self.token:
            self.client.get("/api/v1/users/me",
                           headers={"Authorization": f"Bearer {self.token}"})

    @task(1)
    def detailed_health_check(self):
        """Detailed health check"""
        if self.token:
            self.client.get("/api/v1/health/",
                           headers={"Authorization": f"Bearer {self.token}"})

    @task(1)
    def test_teams_list(self):
        """Test teams endpoint (expected to fail, but tests load)"""
        if self.token:
            self.client.get("/api/v1/teams/",
                           headers={"Authorization": f"Bearer {self.token}"})
