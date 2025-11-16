# app/tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

pytestmark = pytest.mark.integration

class TestCompleteUserJourney:
    """Test complete user workflows end-to-end"""
    
    def test_complete_registration_to_assessment_flow(self, client: TestClient, db: Session):
        """Test: Register → Login → Create Team → Create Assessment → Take → View Results"""
        
        # 1. Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "journey@test.com",
                "full_name": "Journey Tester",
                "password": "Test1234"
            }
        )
        assert register_response.status_code == 201
        
        # 2. Login
        login_response = client.post(
            "/api/v1/auth/login/json",
            json={
                "email": "journey@test.com",
                "password": "Test1234"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create Team
        team_response = client.post(
            "/api/v1/teams",
            json={
                "name": "Test Team",
                "description": "Integration test team"
            },
            headers=headers
        )
        assert team_response.status_code == 201
        team_id = team_response.json()["id"]
        
        # 4. Create Assessment
        assessment_response = client.post(
            "/api/v1/assessments",
            json={
                "title": "Integration Test Assessment",
                "category": "personality",
                "team_id": team_id,
                "sections": [
                    {
                        "title": "Section 1",
                        "order": 0,
                        "questions": [
                            {
                                "question_type": "likert",
                                "question_text": "How do you feel?",
                                "order": 0,
                                "is_required": True
                            }
                        ]
                    }
                ]
            },
            headers=headers
        )
        assert assessment_response.status_code == 201
        assessment_id = assessment_response.json()["id"]
        question_id = assessment_response.json()["sections"][0]["questions"][0]["id"]
        
        # 5. Publish Assessment
        publish_response = client.post(
            f"/api/v1/assessments/{assessment_id}/publish",
            headers=headers
        )
        assert publish_response.status_code == 200
        
        # 6. Start Response
        start_response = client.post(
            "/api/v1/responses/start",
            json={"assessment_id": assessment_id},
            headers=headers
        )
        assert start_response.status_code == 201
        response_id = start_response.json()["id"]
        
        # 7. Submit Answer
        answer_response = client.post(
            f"/api/v1/responses/{response_id}/answers",
            json={
                "question_id": question_id,
                "answer_value": "5"
            },
            headers=headers
        )
        assert answer_response.status_code == 201
        
        # 8. Complete Response
        complete_response = client.post(
            f"/api/v1/responses/{response_id}/complete",
            headers=headers
        )
        assert complete_response.status_code == 200
        assert complete_response.json()["status"] == "completed"
        
        # 9. View Results
        results_response = client.get(
            f"/api/v1/responses/{response_id}/results",
            headers=headers
        )
        assert results_response.status_code == 200
        results = results_response.json()
        assert results["assessment_id"] == assessment_id
        assert len(results["answers"]) == 1
    
    def test_team_collaboration_workflow(self, client: TestClient, db: Session):
        """Test: Create Team → Invite Member → Member Accepts → Collaborate on Assessment"""
        
        # 1. Register Owner
        owner_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "owner@test.com",
                "full_name": "Team Owner",
                "password": "Test1234"
            }
        )
        assert owner_response.status_code == 201
        
        # 2. Login Owner
        owner_login = client.post(
            "/api/v1/auth/login/json",
            json={"email": "owner@test.com", "password": "Test1234"}
        )
        owner_token = owner_login.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # 3. Register Member
        member_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "member@test.com",
                "full_name": "Team Member",
                "password": "Test1234"
            }
        )
        assert member_response.status_code == 201
        
        # 4. Login Member
        member_login = client.post(
            "/api/v1/auth/login/json",
            json={"email": "member@test.com", "password": "Test1234"}
        )
        member_token = member_login.json()["access_token"]
        member_headers = {"Authorization": f"Bearer {member_token}"}
        
        # 5. Owner Creates Team
        team_response = client.post(
            "/api/v1/teams",
            json={
                "name": "Collaboration Team",
                "description": "Testing collaboration"
            },
            headers=owner_headers
        )
        assert team_response.status_code == 201
        team_id = team_response.json()["id"]
        
        # 6. Owner Invites Member
        invite_response = client.post(
            f"/api/v1/teams/{team_id}/invite",
            json={
                "email": "member@test.com",
                "role": "member"
            },
            headers=owner_headers
        )
        assert invite_response.status_code == 200
        invite_id = invite_response.json()["invite_id"]
        
        # 7. Member Accepts Invitation
        accept_response = client.post(
            f"/api/v1/teams/invites/{invite_id}/accept",
            headers=member_headers
        )
        assert accept_response.status_code == 200
        
        # 8. Owner Creates Assessment
        assessment_response = client.post(
            "/api/v1/assessments",
            json={
                "title": "Collaborative Assessment",
                "category": "skills",
                "team_id": team_id,
                "sections": [
                    {
                        "title": "Skills Section",
                        "order": 0,
                        "questions": [
                            {
                                "question_type": "multiple_choice",
                                "question_text": "What is your skill level?",
                                "order": 0,
                                "is_required": True,
                                "options": ["Beginner", "Intermediate", "Advanced"]
                            }
                        ]
                    }
                ]
            },
            headers=owner_headers
        )
        assert assessment_response.status_code == 201
        assessment_id = assessment_response.json()["id"]
        
        # 9. Member Can View Assessment
        view_response = client.get(
            f"/api/v1/assessments/{assessment_id}",
            headers=member_headers
        )
        assert view_response.status_code == 200
        assert view_response.json()["title"] == "Collaborative Assessment"
        
        # 10. Member Can Take Assessment
        start_response = client.post(
            "/api/v1/responses/start",
            json={"assessment_id": assessment_id},
            headers=member_headers
        )
        assert start_response.status_code == 201

    def test_assessment_lifecycle(self, client: TestClient, db: Session):
        """Test: Create → Draft → Publish → Archive → Clone"""
        
        # Setup: Register and Login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "lifecycle@test.com",
                "full_name": "Lifecycle Tester",
                "password": "Test1234"
            }
        )
        login_response = client.post(
            "/api/v1/auth/login/json",
            json={"email": "lifecycle@test.com", "password": "Test1234"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Create Assessment (Draft)
        create_response = client.post(
            "/api/v1/assessments",
            json={
                "title": "Lifecycle Assessment",
                "category": "personality",
                "sections": [
                    {
                        "title": "Test Section",
                        "order": 0,
                        "questions": [
                            {
                                "question_type": "text",
                                "question_text": "Test question",
                                "order": 0,
                                "is_required": False
                            }
                        ]
                    }
                ]
            },
            headers=headers
        )
        assert create_response.status_code == 201
        assessment_id = create_response.json()["id"]
        assert create_response.json()["status"] == "draft"
        
        # 2. Update Draft
        update_response = client.put(
            f"/api/v1/assessments/{assessment_id}",
            json={"title": "Updated Lifecycle Assessment"},
            headers=headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated Lifecycle Assessment"
        
        # 3. Publish Assessment
        publish_response = client.post(
            f"/api/v1/assessments/{assessment_id}/publish",
            headers=headers
        )
        assert publish_response.status_code == 200
        assert publish_response.json()["status"] == "published"
        
        # 4. Cannot Edit Published Assessment
        edit_response = client.put(
            f"/api/v1/assessments/{assessment_id}",
            json={"title": "Should Not Work"},
            headers=headers
        )
        assert edit_response.status_code in [400, 403, 422]
        
        # 5. Archive Assessment
        archive_response = client.post(
            f"/api/v1/assessments/{assessment_id}/archive",
            headers=headers
        )
        assert archive_response.status_code == 200
        assert archive_response.json()["status"] == "archived"
        
        # 6. Clone Assessment
        clone_response = client.post(
            f"/api/v1/assessments/{assessment_id}/clone",
            json={"title": "Cloned Assessment"},
            headers=headers
        )
        assert clone_response.status_code == 201
        cloned_id = clone_response.json()["id"]
        assert cloned_id != assessment_id
        assert clone_response.json()["title"] == "Cloned Assessment"
        assert clone_response.json()["status"] == "draft"

    def test_permission_boundaries(self, client: TestClient, db: Session):
        """Test: Verify proper permission enforcement across resources"""
        
        # Setup: Create two users
        client.post("/api/v1/auth/register", json={
            "email": "user1@test.com", "full_name": "User One", "password": "Test1234"
        })
        client.post("/api/v1/auth/register", json={
            "email": "user2@test.com", "full_name": "User Two", "password": "Test1234"
        })
        
        user1_token = client.post("/api/v1/auth/login/json", json={
            "email": "user1@test.com", "password": "Test1234"
        }).json()["access_token"]
        
        user2_token = client.post("/api/v1/auth/login/json", json={
            "email": "user2@test.com", "password": "Test1234"
        }).json()["access_token"]
        
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        # User1 creates team and assessment
        team_response = client.post(
            "/api/v1/teams",
            json={"name": "User1 Team", "description": "Private team"},
            headers=user1_headers
        )
        team_id = team_response.json()["id"]
        
        assessment_response = client.post(
            "/api/v1/assessments",
            json={
                "title": "User1 Assessment",
                "category": "personality",
                "team_id": team_id,
                "sections": [
                    {
                        "title": "Section 1",
                        "order": 0,
                        "questions": [
                            {
                                "question_type": "text",
                                "question_text": "Question",
                                "order": 0,
                                "is_required": False
                            }
                        ]
                    }
                ]
            },
            headers=user1_headers
        )
        assessment_id = assessment_response.json()["id"]
        
        # User2 cannot access User1's team
        user2_team_access = client.get(
            f"/api/v1/teams/{team_id}",
            headers=user2_headers
        )
        assert user2_team_access.status_code in [403, 404]
        
        # User2 cannot edit User1's assessment
        user2_edit_assessment = client.put(
            f"/api/v1/assessments/{assessment_id}",
            json={"title": "Hacked"},
            headers=user2_headers
        )
        assert user2_edit_assessment.status_code in [403, 404]
        
        # User2 cannot delete User1's assessment
        user2_delete_assessment = client.delete(
            f"/api/v1/assessments/{assessment_id}",
            headers=user2_headers
        )
        assert user2_delete_assessment.status_code in [403, 404]
        
        # Verify User1 still has access
        user1_access = client.get(
            f"/api/v1/assessments/{assessment_id}",
            headers=user1_headers
        )
        assert user1_access.status_code == 200


class TestErrorHandling:
    """Test system behavior under error conditions"""
    
    def test_cascade_deletion(self, client: TestClient, db: Session):
        """Test: Deleting parent resources properly cascades"""
        
        # Setup
        client.post("/api/v1/auth/register", json={
            "email": "cascade@test.com", "full_name": "Cascade Test", "password": "Test1234"
        })
        token = client.post("/api/v1/auth/login/json", json={
            "email": "cascade@test.com", "password": "Test1234"
        }).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create team with assessment
        team_response = client.post(
            "/api/v1/teams",
            json={"name": "Cascade Team"},
            headers=headers
        )
        team_id = team_response.json()["id"]
        
        assessment_response = client.post(
            "/api/v1/assessments",
            json={
                "title": "Cascade Assessment",
                "category": "personality",
                "team_id": team_id,
                "sections": [
                    {
                        "title": "Section",
                        "order": 0,
                        "questions": [
                            {
                                "question_type": "text",
                                "question_text": "Q",
                                "order": 0,
                                "is_required": False
                            }
                        ]
                    }
                ]
            },
            headers=headers
        )
        assessment_id = assessment_response.json()["id"]
        
        # Delete team
        delete_response = client.delete(
            f"/api/v1/teams/{team_id}",
            headers=headers
        )
        assert delete_response.status_code in [200, 204]
        
        # Verify assessment is also deleted or orphaned appropriately
        assessment_check = client.get(
            f"/api/v1/assessments/{assessment_id}",
            headers=headers
        )
        assert assessment_check.status_code == 404
    
    def test_concurrent_response_submission(self, client: TestClient, db: Session):
        """Test: Handle concurrent answer submissions gracefully"""
        
        # Setup: Create assessment
        client.post("/api/v1/auth/register", json={
            "email": "concurrent@test.com", "full_name": "Concurrent Test", "password": "Test1234"
        })
        token = client.post("/api/v1/auth/login/json", json={
            "email": "concurrent@test.com", "password": "Test1234"
        }).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        assessment_response = client.post(
            "/api/v1/assessments",
            json={
                "title": "Concurrent Test",
                "category": "personality",
                "sections": [
                    {
                        "title": "Section",
                        "order": 0,
                        "questions": [
                            {
                                "question_type": "text",
                                "question_text": "Q1",
                                "order": 0,
                                "is_required": False
                            }
                        ]
                    }
                ]
            },
            headers=headers
        )
        assessment_id = assessment_response.json()["id"]
        question_id = assessment_response.json()["sections"][0]["questions"][0]["id"]
        
        client.post(f"/api/v1/assessments/{assessment_id}/publish", headers=headers)
        
        # Start response
        response_id = client.post(
            "/api/v1/responses/start",
            json={"assessment_id": assessment_id},
            headers=headers
        ).json()["id"]
        
        # Submit same answer multiple times (simulating concurrent requests)
        results = []
        for i in range(3):
            result = client.post(
                f"/api/v1/responses/{response_id}/answers",
                json={
                    "question_id": question_id,
                    "answer_value": f"Answer {i}"
                },
                headers=headers
            )
            results.append(result.status_code)
        
        # First should succeed, others should either update or fail gracefully
        assert 201 in results or 200 in results
        # Verify we don't have duplicate answers
        response_data = client.get(
            f"/api/v1/responses/{response_id}",
            headers=headers
        ).json()
        assert len(response_data.get("answers", [])) == 1
