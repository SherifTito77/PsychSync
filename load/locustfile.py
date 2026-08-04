import random

from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a simulated user starts"""
        # Try to login or register
        self.login()

    def login(self):
        """Simulate user login"""
        login_data = {
            "email": f"test{secrets.randbelow(999) + 1}@example.com",
            "password": "TestPassword123!",
        }

        response = self.client.post("/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # Try to register if login fails
            register_data = {
                "email": login_data["email"],
                "password": login_data["password"],
                "full_name": f"Test User {secrets.randbelow(999) + 1}",
            }
            self.client.post("/api/v1/auth/register", json=register_data)

    @task(3)
    def optimize_team(self):
        """Simulate team optimization requests"""
        # Generate random team data
        num_members = secrets.randbelow(6) + 2
        members = []

        for i in range(num_members):
            member = {
                "id": i + 1,
                "name": f"Team Member {i + 1}",
                "role": secrets.choice(["Developer", "Designer", "Manager", "Analyst"]),
                "traits": {
                    "openness": round(random.uniform(0.1, 1.0), 2),
                    "conscientiousness": round(random.uniform(0.1, 1.0), 2),
                    "extraversion": round(random.uniform(0.1, 1.0), 2),
                    "agreeableness": round(random.uniform(0.1, 1.0), 2),
                    "neuroticism": round(random.uniform(0.1, 1.0), 2),
                },
            }
            members.append(member)

        optimization_data = {
            "members": members,
            "objective": secrets.choice(
                ["maximize_engagement", "balance_traits", "complementary_skills"]
            ),
        }

        headers = getattr(self, "headers", {})
        self.client.post(
            "/api/v1/team-optimizer/optimize", json=optimization_data, headers=headers
        )

    @task(2)
    def view_profile(self):
        """Simulate viewing user profile"""
        if hasattr(self, "headers"):
            self.client.get("/api/v1/users/profile", headers=self.headers)

    @task(1)
    def view_health(self):
        """Simulate health check requests"""
        self.client.get("/api/v1/health")

    @task(1)
    def create_assessment(self):
        """Simulate creating assessments"""
        if hasattr(self, "headers"):
            assessment_data = {
                "title": f"Test Assessment {secrets.randbelow(999) + 1}",
                "description": "Performance test assessment",
                "framework": secrets.choice(["big_five", "mbti", "enneagram"]),
                "questions": [
                    {
                        "text": f"Question {i + 1}",
                        "type": "scale",
                        "scale_min": 1,
                        "scale_max": 5,
                    }
                    for i in range(5)
                ],
            }

            self.client.post(
                "/api/v1/assessments", json=assessment_data, headers=self.headers
            )

    @task(1)
    def send_notification(self):
        """Simulate sending notifications"""
        if hasattr(self, "headers"):
            notification_data = {
                "user_id": secrets.randbelow(999) + 1,
                "event": secrets.choice(
                    ["assessment_completed", "team_created", "optimization_finished"]
                ),
                "payload": {"test": True},
            }

            self.client.post(
                "/api/v1/notifications/send-event",
                json=notification_data,
                headers=self.headers,
            )
