"""
Integration tests for full user workflows
Tests multiple API endpoints working together
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestUserWorkflow:
    """Test complete user registration and authentication workflow"""

    def test_user_registration_and_login_flow(self):
        """Test user registration, email verification, and login"""

        # 1. Register new user
        register_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }

        register_response = client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code in [200, 201]  # Accept both success codes

        # 2. Login with registered user
        login_data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }

        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200

        login_result = login_response.json()
        assert "access_token" in login_result
        assert "refresh_token" in login_result

        # 3. Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {login_result['access_token']}"}

        profile_response = client.get("/api/v1/users/profile", headers=headers)
        assert profile_response.status_code == 200

        profile_data = profile_response.json()
        assert profile_data["email"] == "test@example.com"

    def test_team_creation_and_optimization_flow(self):
        """Test creating a team and running optimization"""

        # First login to get token
        login_data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }

        login_response = client.post("/api/v1/auth/login", json=login_data)
        if login_response.status_code != 200:
            pytest.skip("Need valid authentication token")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create organization
        org_data = {
            "name": "Test Organization",
            "description": "Test organization for integration tests"
        }

        org_response = client.post("/api/v1/organizations", json=org_data, headers=headers)
        assert org_response.status_code in [200, 201]

        org_id = org_response.json().get("id")

        # 2. Create team under organization
        team_data = {
            "name": "Development Team",
            "organization_id": org_id,
            "description": "Team for testing optimization"
        }

        team_response = client.post("/api/v1/teams", json=team_data, headers=headers)
        assert team_response.status_code in [200, 201]

        team_id = team_response.json().get("id")

        # 3. Run team optimization
        optimization_data = {
            "members": [
                {
                    "id": 1,
                    "name": "John Doe",
                    "role": "Developer",
                    "traits": {"openness": 0.8, "conscientiousness": 0.7}
                },
                {
                    "id": 2,
                    "name": "Jane Smith",
                    "role": "Designer",
                    "traits": {"openness": 0.9, "conscientiousness": 0.6}
                }
            ],
            "objective": "maximize_engagement"
        }

        opt_response = client.post(
            "/api/v1/team-optimizer/optimize",
            json=optimization_data,
            headers=headers
        )

        assert opt_response.status_code == 200
        result = opt_response.json()
        assert "recommended_groups" in result
        assert "score" in result

    def test_assessment_creation_and_completion_flow(self):
        """Test creating an assessment and completing it"""

        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })

        if login_response.status_code != 200:
            pytest.skip("Need valid authentication token")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create assessment
        assessment_data = {
            "title": "Big Five Personality Test",
            "description": "Test Big Five traits",
            "framework": "big_five",
            "questions": [
                {
                    "text": "I see myself as someone who is talkative",
                    "type": "scale",
                    "scale_min": 1,
                    "scale_max": 5
                },
                {
                    "text": "I see myself as someone who is critical",
                    "type": "scale",
                    "scale_min": 1,
                    "scale_max": 5
                }
            ]
        }

        assessment_response = client.post(
            "/api/v1/assessments",
            json=assessment_data,
            headers=headers
        )

        assert assessment_response.status_code in [200, 201]
        assessment_id = assessment_response.json().get("id")

        # 2. Start assessment
        start_response = client.post(
            f"/api/v1/assessments/{assessment_id}/start",
            headers=headers
        )

        assert start_response.status_code == 200
        session_id = start_response.json().get("session_id")

        # 3. Submit assessment responses
        responses_data = {
            "session_id": session_id,
            "responses": [
                {"question_id": 1, "value": 4},
                {"question_id": 2, "value": 2}
            ]
        }

        submit_response = client.post(
            f"/api/v1/assessments/{assessment_id}/submit",
            json=responses_data,
            headers=headers
        )

        assert submit_response.status_code == 200
        result = submit_response.json()
        assert "scores" in result or "message" in result

    def test_notification_workflow(self):
        """Test notification sending and receiving"""

        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })

        if login_response.status_code != 200:
            pytest.skip("Need valid authentication token")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Send event notification
        notification_data = {
            "user_id": 1,
            "event": "assessment_completed",
            "payload": {"assessment_id": 123, "score": 85}
        }

        event_response = client.post(
            "/api/v1/notifications/send-event",
            json=notification_data,
            headers=headers
        )

        assert event_response.status_code == 200

        # Send email notification
        email_data = {
            "email": "test@example.com",
            "subject": "Assessment Completed",
            "body": "You have successfully completed your assessment."
        }

        email_response = client.post(
            "/api/v1/notifications/send-email",
            json=email_data,
            headers=headers
        )

        assert email_response.status_code == 200


class TestErrorHandling:
    """Test error handling across integrated workflows"""

    def test_unauthorized_access_protection(self):
        """Test that unauthorized access is properly blocked"""

        # Try to access protected endpoint without token
        response = client.get("/api/v1/users/profile")
        assert response.status_code == 401

        # Try to access team optimization without token
        response = client.post("/api/v1/team-optimizer/optimize", json={
            "members": [{"id": 1, "name": "Test", "role": "dev", "traits": {}}]
        })
        assert response.status_code == 401

    def test_invalid_data_handling(self):
        """Test how the system handles invalid data"""

        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })

        if login_response.status_code != 200:
            pytest.skip("Need valid authentication token")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Send invalid team optimization data
        invalid_data = {
            "members": "not_a_list",  # Should be a list
            "objective": 123  # Should be a string
        }

        response = client.post(
            "/api/v1/team-optimizer/optimize",
            json=invalid_data,
            headers=headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_resource_not_found_handling(self):
        """Test handling of non-existent resources"""

        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })

        if login_response.status_code != 200:
            pytest.skip("Need valid authentication token")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to access non-existent assessment
        response = client.get("/api/v1/assessments/99999", headers=headers)
        assert response.status_code == 404

        # Try to start non-existent assessment
        response = client.post("/api/v1/assessments/99999/start", headers=headers)
        assert response.status_code == 404


class TestPerformanceWorkflow:
    """Test performance characteristics of integrated workflows"""

    def test_concurrent_user_simulation(self):
        """Test system behavior with simulated concurrent users"""
        import threading
        import time

        results = []

        def simulate_user_request():
            start_time = time.time()
            response = client.get("/api/v1/health")
            end_time = time.time()

            results.append({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })

        # Create 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=simulate_user_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all requests succeeded
        assert len(results) == 10
        assert all(r["status_code"] == 200 for r in results)

        # Verify reasonable response times
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        assert avg_response_time < 2.0  # Should respond within 2 seconds on average


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
