"""
File Path: tests/test_scoring_system.py
Tests for assessment scoring system
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.models.assessment import (
    Assessment,
    AssessmentResponse,
    Question,
    AssessmentSection,
    AssessmentCategory,
    AssessmentStatus
)
from app.db.models.user import User


class TestScoringSystem:
    """Test assessment scoring functionality"""
    
    def test_assessment_creation(self, db: Session, test_user: User):
        """Test creating an assessment"""
        assessment = Assessment(
            title="Test Assessment",
            description="Testing assessment creation",
            category=AssessmentCategory.PERSONALITY,
            status=AssessmentStatus.DRAFT,
            created_by_id=test_user.id
        )
        
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        assert assessment.id is not None
        assert assessment.title == "Test Assessment"
        assert assessment.created_by_id == test_user.id
    
    def test_assessment_response_creation(
        self,
        db: Session,
        test_assessment: Assessment,
        test_user: User
    ):
        """Test creating an assessment response"""
        response = AssessmentResponse(
            assessment_id=test_assessment.id,
            respondent_id=test_user.id,
            started_at=datetime.utcnow()
        )
        
        db.add(response)
        db.commit()
        db.refresh(response)
        
        assert response.id is not None
        assert response.assessment_id == test_assessment.id
        assert response.respondent_id == test_user.id
        assert response.completed_at is None
    
    def test_complete_assessment_response(
        self,
        db: Session,
        test_assessment: Assessment,
        test_user: User
    ):
        """Test completing an assessment response"""
        response = AssessmentResponse(
            assessment_id=test_assessment.id,
            respondent_id=test_user.id,
            started_at=datetime.utcnow()
        )
        
        db.add(response)
        db.commit()
        
        # Complete the response
        response.completed_at = datetime.utcnow()
        response.response_data = {
            "question_1": {"answer": "5"},
            "question_2": {"answer": "4"}
        }
        
        db.commit()
        db.refresh(response)
        
        assert response.completed_at is not None
        assert response.response_data is not None
        assert len(response.response_data) == 2
    
    def test_calculate_basic_score(
        self,
        db: Session,
        test_assessment: Assessment,
        test_user: User
    ):
        """Test basic score calculation"""
        # Create completed response
        response = AssessmentResponse(
            assessment_id=test_assessment.id,
            respondent_id=test_user.id,
            started_at=datetime.utcnow() - timedelta(minutes=10),
            completed_at=datetime.utcnow(),
            response_data={
                "question_1": {"answer": "5", "score": 5},
                "question_2": {"answer": "4", "score": 4},
                "question_3": {"answer": "3", "score": 3}
            }
        )
        
        db.add(response)
        db.commit()
        
        # Calculate simple average score
        scores = [
            item['score'] 
            for item in response.response_data.values() 
            if 'score' in item
        ]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        response.score_data = {
            "overall_score": avg_score,
            "total_questions": len(scores),
            "answered_questions": len(scores)
        }
        
        db.commit()
        db.refresh(response)
        
        assert response.score_data is not None
        assert response.score_data['overall_score'] == 4.0
        assert response.score_data['total_questions'] == 3
    
    def test_score_with_weighted_categories(
        self,
        db: Session,
        test_assessment: Assessment,
        test_user: User
    ):
        """Test score calculation with weighted categories"""
        response = AssessmentResponse(
            assessment_id=test_assessment.id,
            respondent_id=test_user.id,
            started_at=datetime.utcnow() - timedelta(minutes=15),
            completed_at=datetime.utcnow(),
            response_data={
                "openness_1": {"answer": "5", "score": 5, "category": "openness"},
                "openness_2": {"answer": "4", "score": 4, "category": "openness"},
                "conscientiousness_1": {"answer": "5", "score": 5, "category": "conscientiousness"},
                "conscientiousness_2": {"answer": "5", "score": 5, "category": "conscientiousness"}
            }
        )
        
        db.add(response)
        db.commit()
        
        # Calculate category scores
        from collections import defaultdict
        category_scores = defaultdict(list)
        
        for item in response.response_data.values():
            if 'category' in item and 'score' in item:
                category_scores[item['category']].append(item['score'])
        
        category_averages = {
            category: sum(scores) / len(scores)
            for category, scores in category_scores.items()
        }
        
        overall_score = sum(category_averages.values()) / len(category_averages)
        
        response.score_data = {
            "overall_score": overall_score,
            "category_scores": category_averages
        }
        
        db.commit()
        db.refresh(response)
        
        assert response.score_data['overall_score'] == 4.75
        assert response.score_data['category_scores']['openness'] == 4.5
        assert response.score_data['category_scores']['conscientiousness'] == 5.0
    
    def test_assessment_expiration(
        self,
        db: Session,
        test_assessment: Assessment,
        test_user: User
    ):
        """Test assessment response expiration"""
        # Create old incomplete response
        old_response = AssessmentResponse(
            assessment_id=test_assessment.id,
            respondent_id=test_user.id,
            started_at=datetime.utcnow() - timedelta(days=35),
            completed_at=None
        )
        
        db.add(old_response)
        db.commit()
        
        # Check if expired (30 days)
        expiry_days = 30
        cutoff = datetime.utcnow() - timedelta(days=expiry_days)
        
        is_expired = (
            old_response.completed_at is None and
            old_response.started_at < cutoff
        )
        
        assert is_expired is True
        
        # Mark as expired
        old_response.status = AssessmentStatus.EXPIRED
        db.commit()
        
        assert old_response.status == AssessmentStatus.EXPIRED
    
    def test_assessment_statistics(
        self,
        db: Session,
        test_assessment: Assessment,
        test_user: User
    ):
        """Test calculating assessment statistics"""
        # Create multiple responses
        scores = [85.5, 90.0, 78.5, 92.0, 88.0]
        
        for score in scores:
            response = AssessmentResponse(
                assessment_id=test_assessment.id,
                respondent_id=test_user.id,
                started_at=datetime.utcnow() - timedelta(minutes=20),
                completed_at=datetime.utcnow(),
                score_data={"overall_score": score}
            )
            db.add(response)
        
        db.commit()
        
        # Calculate statistics
        responses = db.query(AssessmentResponse).filter(
            AssessmentResponse.assessment_id == test_assessment.id,
            AssessmentResponse.completed_at.isnot(None)
        ).all()
        
        response_scores = [
            r.score_data.get('overall_score', 0)
            for r in responses
            if r.score_data
        ]
        
        stats = {
            "total_responses": len(responses),
            "completed_responses": len(response_scores),
            "average_score": sum(response_scores) / len(response_scores),
            "min_score": min(response_scores),
            "max_score": max(response_scores)
        }
        
        assert stats['total_responses'] == 5
        assert stats['average_score'] == 86.8
        assert stats['min_score'] == 78.5
        assert stats['max_score'] == 92.0
    
    def test_score_normalization(self, db: Session):
        """Test score normalization to 0-100 scale"""
        # Simulate raw scores on different scales
        raw_scores = [
            {"raw": 45, "max": 50, "expected": 90.0},
            {"raw": 3.5, "max": 5.0, "expected": 70.0},
            {"raw": 85, "max": 100, "expected": 85.0}
        ]
        
        for score_data in raw_scores:
            normalized = (score_data['raw'] / score_data['max']) * 100
            assert abs(normalized - score_data['expected']) < 0.1
    
    def test_confidence_score_calculation(
        self,
        db: Session,
        test_assessment: Assessment,
        test_user: User
    ):
        """Test confidence score based on response completeness"""
        # Full response
        full_response = AssessmentResponse(
            assessment_id=test_assessment.id,
            respondent_id=test_user.id,
            started_at=datetime.utcnow() - timedelta(minutes=30),
            completed_at=datetime.utcnow(),
            response_data={
                f"q_{i}": {"answer": str(i), "score": i}
                for i in range(1, 11)  # 10 questions
            }
        )
        
        db.add(full_response)
        db.commit()
        
        # Calculate confidence (completeness-based)
        total_questions = 10
        answered_questions = len(full_response.response_data)
        completeness = answered_questions / total_questions
        
        # Time factor (completed in reasonable time)
        time_taken = (
            full_response.completed_at - full_response.started_at
        ).total_seconds() / 60  # minutes
        
        expected_time = 20  # minutes
        time_factor = min(time_taken / expected_time, 1.0)
        
        confidence = (completeness * 0.7 + time_factor * 0.3) * 100
        
        full_response.score_data = {
            "overall_score": 50.0,
            "confidence_score": confidence
        }
        
        db.commit()
        db.refresh(full_response)
        
        assert full_response.score_data['confidence_score'] >= 90.0


class TestScoringEdgeCases:
    """Test edge cases in scoring"""
    
    def test_empty_response_handling(
        self,
        db: Session,
        test_assessment: Assessment,
        test_user: User
    ):
        """Test handling of empty response data"""
        response = AssessmentResponse(
            assessment_id=test_assessment.id,
            respondent_id=test_user.id,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            response_data={}
        )
        
        db.add(response)
        db.commit()
        
        # Should handle gracefully
        scores = [
            item.get('score', 0)
            for item in response.response_data.values()
        ]
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        assert avg_score == 0
        assert len(scores) == 0
    
    def test_partial_response_scoring(
        self,
        db: Session,
        test_assessment: Assessment,
        test_user: User
    ):
        """Test scoring when not all questions are answered"""
        response = AssessmentResponse(
            assessment_id=test_assessment.id,
            respondent_id=test_user.id,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            response_data={
                "q1": {"answer": "5", "score": 5},
                "q2": {"answer": None, "score": None},  # Skipped
                "q3": {"answer": "4", "score": 4}
            }
        )
        
        db.add(response)
        db.commit()
        
        # Calculate only answered questions
        scores = [
            item['score']
            for item in response.response_data.values()
            if item.get('score') is not None
        ]
        
        avg_score = sum(scores) / len(scores) if scores else 0
        completion_rate = len(scores) / len(response.response_data)
        
        assert avg_score == 4.5
        assert completion_rate == pytest.approx(0.667, 0.01)
    
    def test_invalid_score_values(self, db: Session):
        """Test handling of invalid score values"""
        # Test various invalid inputs
        invalid_values = [
            None,
            "",
            "invalid",
            float('inf'),
            -1
        ]
        
        valid_scores = []
        for value in invalid_values:
            try:
                if isinstance(value, (int, float)) and 0 <= value <= 100:
                    valid_scores.append(value)
            except (TypeError, ValueError):
                pass
        
        # Should filter out all invalid values
        assert len(valid_scores) == 0


class TestScoringPerformance:
    """Test scoring performance and optimization"""
    
    def test_bulk_scoring_performance(
        self,
        db: Session,
        test_assessment: Assessment,
        test_user: User
    ):
        """Test performance of bulk score calculations"""
        import time
        
        # Create multiple responses
        num_responses = 50
        responses = []
        
        for i in range(num_responses):
            response = AssessmentResponse(
                assessment_id=test_assessment.id,
                respondent_id=test_user.id,
                started_at=datetime.utcnow() - timedelta(minutes=30),
                completed_at=datetime.utcnow(),
                response_data={
                    f"q_{j}": {"answer": str(j), "score": j % 10}
                    for j in range(20)
                }
            )
            responses.append(response)
        
        db.bulk_save_objects(responses)
        db.commit()
        
        # Measure scoring time
        start_time = time.time()
        
        for response in responses:
            scores = [
                item['score']
                for item in response.response_data.values()
                if 'score' in item
            ]
            avg_score = sum(scores) / len(scores) if scores else 0
        
        elapsed_time = time.time() - start_time
        
        # Should complete quickly (< 1 second for 50 responses)
        assert elapsed_time < 1.0
        assert len(responses) == num_responses