# app/tests/test_analytics_service.py
import pytest
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.assessment import Assessment
from app.services.analytics_service import AnalyticsService
from app.services.response_service import ResponseService

pytestmark = pytest.mark.analytics


class TestAnalyticsService:
    """Test analytics service functionality"""

    def test_get_assessment_analytics(self, db: Session, test_user: User, test_assessment):
        """Test assessment analytics calculation"""
        # Create and submit a response
        question_id = str(test_assessment.sections[0].questions[0].id)
        
        response = ResponseService.create_response_session(
            db,
            assessment_id=test_assessment.id,
            respondent_id=test_user.id
        )
        
        ResponseService.submit_response(
            db,
            response=response,
            responses_data={question_id: 5}
        )
        
        # Get analytics
        analytics = AnalyticsService.get_assessment_analytics(
            db,
            assessment_id=test_assessment.id
        )
        
        assert analytics is not None
        assert analytics["assessment_id"] == test_assessment.id
        assert analytics["total_responses"] == 1
        assert analytics["average_score"] is not None
        assert "score_distribution" in analytics

    def test_get_user_analytics(self, db: Session, test_user: User, test_assessment):
        """Test user analytics calculation"""
        # Create response
        question_id = str(test_assessment.sections[0].questions[0].id)
        
        response = ResponseService.create_response_session(
            db,
            assessment_id=test_assessment.id,
            respondent_id=test_user.id
        )
        
        ResponseService.submit_response(
            db,
            response=response,
            responses_data={question_id: 5}
        )
        
        # Get analytics
        analytics = AnalyticsService.get_user_analytics(
            db,
            user_id=test_user.id
        )
        
        assert analytics is not None
        assert analytics["user_id"] == test_user.id
        assert analytics["total_responses"] >= 1
        assert analytics["completed_responses"] >= 1
        assert "average_score" in analytics

    def test_get_team_analytics(self, db: Session, test_user: User, test_team, test_assessment):
        """Test team analytics calculation"""
        # Associate assessment with team
        test_assessment.team_id = test_team.id
        db.commit()
        
        # Create response
        question_id = str(test_assessment.sections[0].questions[0].id)
        
        response = ResponseService.create_response_session(
            db,
            assessment_id=test_assessment.id,
            respondent_id=test_user.id
        )
        
        ResponseService.submit_response(
            db,
            response=response,
            responses_data={question_id: 5}
        )
        
        # Get analytics
        analytics = AnalyticsService.get_team_analytics(
            db,
            team_id=test_team.id
        )
        
        assert analytics is not None
        assert analytics["team_id"] == test_team.id
        assert analytics["total_members"] >= 1
        assert "member_performance" in analytics

    def test_score_distribution(self, db: Session, test_user: User, test_assessment):
        """Test score distribution calculation"""
        question_id = str(test_assessment.sections[0].questions[0].id)
        
        # Create multiple responses with different scores
        for score in [2, 5, 8, 10]:
            from faker import Faker
            fake = Faker()
            
            # Create new user for each response
            from app.schemas.user import UserCreate
            from app.services.user_service import UserService
            
            user_data = UserCreate(
                email=fake.email(),
                full_name=fake.name(),
                password="Test1234"
            )
            user = UserService.create(db, user_in=user_data)
            
            response = ResponseService.create_response_session(
                db,
                assessment_id=test_assessment.id,
                respondent_id=user.id
            )
            
            ResponseService.submit_response(
                db,
                response=response,
                responses_data={question_id: score}
            )
        
        # Get analytics
        analytics = AnalyticsService.get_assessment_analytics(
            db,
            assessment_id=test_assessment.id
        )
        
        # Check distribution
        distribution = analytics["score_distribution"]
        assert len(distribution) > 0
        total_count = sum(item["count"] for item in distribution)
        assert total_count == 4


class TestAnalyticsEndpoints:
    """Test analytics API endpoints"""

    def test_get_assessment_analytics_endpoint(self, client, auth_headers, test_assessment, db, test_user):
        """Test assessment analytics endpoint"""
        # Create a response first
        question_id = str(test_assessment.sections[0].questions[0].id)
        
        response = ResponseService.create_response_session(
            db,
            assessment_id=test_assessment.id,
            respondent_id=test_user.id
        )
        
        ResponseService.submit_response(
            db,
            response=response,
            responses_data={question_id: 5}
        )
        
        # Get analytics
        response = client.get(
            f"/api/v1/analytics/assessments/{test_assessment.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["assessment_id"] == test_assessment.id

    def test_get_my_analytics_endpoint(self, client, auth_headers):
        """Test user analytics endpoint"""
        response = client.get(
            "/api/v1/analytics/users/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_responses" in data

    def test_analytics_permissions(self, client, auth_headers, test_assessment):
        """Test that non-owners cannot access analytics"""
        from faker import Faker
        fake = Faker()
        
        # Register another user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": fake.email(),
                "full_name": "Other User",
                "password": "Test1234"
            }
        )
        
        # Try to access analytics (should fail - not implemented yet, but test for future)
        # This test documents expected behavior
        pass
    