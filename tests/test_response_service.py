# app/tests/test_response_service.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.assessment import Assessment, AssessmentResponse, ResponseStatus
from app.services.response_service import ResponseService

pytestmark = pytest.mark.response


class TestResponseService:
    """Test response service functionality"""

    def test_create_response_session(self, db: Session, test_user: User, test_assessment):
        """Test creating new response session"""
        response = ResponseService.create_response_session(
            db,
            assessment_id=test_assessment.id,
            respondent_id=test_user.id
        )
        
        assert response is not None
        assert response.assessment_id == test_assessment.id
        assert response.respondent_id == test_user.id
        assert response.status == ResponseStatus.IN_PROGRESS
        assert response.progress_percentage == 0.0

    def test_duplicate_session_returns_existing(self, db: Session, test_user: User, test_assessment):
        """Test that duplicate session returns existing session"""
        # Create first session
        session1 = ResponseService.create_response_session(
            db,
            assessment_id=test_assessment.id,
            respondent_id=test_user.id
        )
        
        # Try to create another - should return same session
        session2 = ResponseService.create_response_session(
            db,
            assessment_id=test_assessment.id,
            respondent_id=test_user.id
        )
        
        assert session1.id == session2.id

    def test_save_progress(self, db: Session, test_user: User, test_assessment):
        """Test saving response progress"""
        response = ResponseService.create_response_session(
            db,
            assessment_id=test_assessment.id,
            respondent_id=test_user.id
        )
        
        # Save some answers
        responses_data = {"1": 5, "2": "Test answer"}
        updated = ResponseService.save_progress(
            db,
            response=response,
            responses_data=responses_data,
            current_section=0
        )
        
        assert updated.responses == responses_data
        assert updated.current_section == 0
        assert updated.progress_percentage > 0

    def test_submit_response(self, db: Session, test_user: User, test_assessment):
        """Test submitting completed response"""
        # Get the question ID from the assessment
        question_id = str(test_assessment.sections[0].questions[0].id)
        
        response = ResponseService.create_response_session(
            db,
            assessment_id=test_assessment.id,
            respondent_id=test_user.id
        )
        
        # Submit with answer
        responses_data = {question_id: 5}
        submitted = ResponseService.submit_response(
            db,
            response=response,
            responses_data=responses_data,
            time_taken=300
        )
        
        assert submitted.is_complete is True
        assert submitted.status == ResponseStatus.COMPLETED
        assert submitted.submitted_at is not None
        assert submitted.time_taken == 300
        assert submitted.progress_percentage == 100.0

    def test_calculate_score(self, db: Session, test_user: User, test_assessment):
        """Test score calculation"""
        question_id = str(test_assessment.sections[0].questions[0].id)
        
        response = ResponseService.create_response_session(
            db,
            assessment_id=test_assessment.id,
            respondent_id=test_user.id
        )
        
        # Submit response
        responses_data = {question_id: 5}
        submitted = ResponseService.submit_response(
            db,
            response=response,
            responses_data=responses_data
        )
        
        # Check score was calculated
        score = ResponseService.get_response_score(db, response_id=submitted.id)
        assert score is not None
        assert score.total_score is not None
        assert score.percentage_score is not None

    def test_validate_response_data(self, db: Session, test_assessment):
        """Test response validation"""
        question_id = str(test_assessment.sections[0].questions[0].id)
        
        # Valid response
        is_valid, error = ResponseService.validate_response_data(
            db,
            assessment_id=test_assessment.id,
            responses_data={question_id: 5}
        )
        assert is_valid is True
        assert error is None
        
        # Invalid response (missing required question)
        is_valid, error = ResponseService.validate_response_data(
            db,
            assessment_id=test_assessment.id,
            responses_data={}
        )
        assert is_valid is False
        assert error is not None


class TestResponseEndpoints:
    """Test response API endpoints"""

    def test_start_response_session(self, client: TestClient, auth_headers, test_assessment):
        """Test starting response session"""
        response = client.post(
            "/api/v1/responses/start",
            json={"assessment_id": test_assessment.id},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["assessment_id"] == test_assessment.id
        assert data["status"] == "in_progress"

    def test_save_progress_endpoint(self, client: TestClient, auth_headers, test_assessment):
        """Test save progress endpoint"""
        # Start session
        start_response = client.post(
            "/api/v1/responses/start",
            json={"assessment_id": test_assessment.id},
            headers=auth_headers
        )
        response_id = start_response.json()["id"]
        
        # Save progress
        save_response = client.put(
            f"/api/v1/responses/{response_id}/save",
            json={
                "responses": {"1": 5},
                "current_section": 0
            },
            headers=auth_headers
        )
        
        assert save_response.status_code == 200
        data = save_response.json()
        assert data["responses"] == {"1": 5}

    def test_submit_response_endpoint(self, client: TestClient, auth_headers, test_assessment):
        """Test submit response endpoint"""
        question_id = str(test_assessment.sections[0].questions[0].id)
        
        # Start session
        start_response = client.post(
            "/api/v1/responses/start",
            json={"assessment_id": test_assessment.id},
            headers=auth_headers
        )
        response_id = start_response.json()["id"]
        
        # Submit
        submit_response = client.post(
            f"/api/v1/responses/{response_id}/submit",
            json={
                "responses": {question_id: 5},
                "time_taken": 300
            },
            headers=auth_headers
        )
        
        assert submit_response.status_code == 200
        data = submit_response.json()
        assert data["is_complete"] is True
        assert data["score"] is not None

    def test_get_my_responses(self, client: TestClient, auth_headers, test_assessment):
        """Test getting user's responses"""
        # Create a response
        client.post(
            "/api/v1/responses/start",
            json={"assessment_id": test_assessment.id},
            headers=auth_headers
        )
        
        # Get responses
        response = client.get(
            "/api/v1/responses/my-responses",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_cannot_modify_completed_response(self, client: TestClient, auth_headers, test_assessment):
        """Test that completed responses cannot be modified"""
        question_id = str(test_assessment.sections[0].questions[0].id)
        
        # Start and complete
        start_response = client.post(
            "/api/v1/responses/start",
            json={"assessment_id": test_assessment.id},
            headers=auth_headers
        )
        response_id = start_response.json()["id"]
        
        client.post(
            f"/api/v1/responses/{response_id}/submit",
            json={"responses": {question_id: 5}},
            headers=auth_headers
        )
        
        # Try to save again
        save_response = client.put(
            f"/api/v1/responses/{response_id}/save",
            json={"responses": {"1": 3}},
            headers=auth_headers
        )
        
        assert save_response.status_code == 400
        