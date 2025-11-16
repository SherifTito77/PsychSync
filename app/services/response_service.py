# app/services/response_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, joinedload
from datetime import datetime
from fastapi import HTTPException, status

from app.db.models.assessment import (
    Assessment,
    AssessmentResponse,
    AssessmentAssignment,
    ResponseStatus,
    # Response
)
from app.schemas.response import ResponseCreate, ResponseUpdate, ResponseSave, ResponseSubmit
from app.db.models.response_score import ResponseScore

class ResponseService:
    """Response service for database operations"""
    
    @staticmethod
    def create_response_session(
        db: Session,
        assessment_id: int,
        respondent_id: Optional[int],
        assignment_id: Optional[int] = None
    ) -> AssessmentResponse:
        """Create new response session"""
        # Check if active session exists
        existing = result = await db.execute(query)
        return result.scalars().all()
        
        if existing:
            return existing
        
        response = AssessmentResponse(
            assessment_id=assessment_id,
            assignment_id=assignment_id,
            respondent_id=respondent_id,
            responses={},
            status=ResponseStatus.IN_PROGRESS,
            current_section=0,
            progress_percentage=0.0
        )
        db.add(response)
        await db.commit()
        await db.refresh(response)
        return response
    
    @staticmethod
    def get_response(db: Session, response_id: int) -> Optional[AssessmentResponse]:
        """Get response by ID"""
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    def get_user_responses(
        db: Session,
        user_id: int,
        status: Optional[str] = None
    ) -> List[AssessmentResponse]:
        """Get all responses by user"""
        query = db.query(AssessmentResponse).filter(
            AssessmentResponse.respondent_id == user_id
        )
        
        if status:
            query = query.filter(AssessmentResponse.status == ResponseStatus(status))
        
        return query.order_by(AssessmentResponse.started_at.desc()).all()
    
    @staticmethod
    def get_assessment_responses(
        db: Session,
        assessment_id: int,
        completed_only: bool = True
    ) -> List[AssessmentResponse]:
        """Get all responses for an assessment"""
        query = db.query(AssessmentResponse).filter(
            AssessmentResponse.assessment_id == assessment_id
        )
        
        if completed_only:
            query = query.filter(AssessmentResponse.is_complete == True)
        
        return query.all()
    
    @staticmethod
    def save_progress(
        db: Session,
        response: AssessmentResponse,
        responses_data: Dict[str, Any],
        current_section: Optional[int] = None
    ) -> AssessmentResponse:
        """Save response progress"""
        # Merge new responses with existing
        existing_responses = response.responses or {}
        existing_responses.update(responses_data)
        response.responses = existing_responses
        
        if current_section is not None:
            response.current_section = current_section
        
        # Calculate progress
        assessment = db.query(Assessment).options(
            joinedload(Assessment.sections)
        ).filter(Assessment.id == response.assessment_id).first()
        
        if assessment:
            total_questions = sum(len(s.questions) for s in assessment.sections)
            answered_questions = len([k for k in existing_responses.keys() if existing_responses[k] is not None])
            response.progress_percentage = (answered_questions / total_questions * 100) if total_questions > 0 else 0
        
        response.last_saved_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(response)
        return response
    
    @staticmethod
    def submit_response(
        db: Session,
        response: AssessmentResponse,
        responses_data: Dict[str, Any],
        time_taken: Optional[int] = None
    ) -> AssessmentResponse:
        """Submit completed response"""
        # Update responses
        existing_responses = response.responses or {}
        existing_responses.update(responses_data)
        response.responses = existing_responses
        
        # Mark as complete
        response.is_complete = True
        response.status = ResponseStatus.COMPLETED
        response.submitted_at = datetime.utcnow()
        response.progress_percentage = 100.0
        
        if time_taken:
            response.time_taken = time_taken
        else:
            # Calculate time taken
            time_diff = datetime.utcnow() - response.started_at
            response.time_taken = int(time_diff.total_seconds())
        
        # Mark assignment as completed if exists
        if response.assignment_id:
            assignment = result = await db.execute(query)
        return result.scalars().all()
            if assignment:
                assignment.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(response)
        
        # Calculate score
        ResponseService.calculate_score(db, response)
        
        return response
    
    @staticmethod
    def calculate_score(
        db: Session,
        response: AssessmentResponse
    ) -> Optional[ResponseScore]:
        """Calculate score for response (basic implementation)"""
        from app.services.scoring_service import ScoringService
        # Check if score already exists
        existing_score = result = await db.execute(query)
        return result.scalars().all()
        
        if existing_score:
            return existing_score
        
        # Calculate using appropriate algorithm
        scoring_result = ScoringService.calculate_score(db, response)
        
        
        # Get assessment with questions
        assessment = db.query(Assessment).options(
            joinedload(Assessment.sections).joinedload(Assessment.sections[0].questions)
        ).filter(Assessment.id == response.assessment_id).first()
        
        if not assessment:
            return None
        
        # Basic scoring logic
        total_score = 0.0
        max_score = 0.0
        
        for section in assessment.sections:
            for question in section.questions:
                q_id = str(question.id)
                if q_id in response.responses:
                    answer = response.responses[q_id]
                    
                    # Simple scoring based on question type
                    if question.question_type.value == "rating_scale":
                        if question.config and "max" in question.config:
                            max_val = float(question.config["max"])
                            max_score += max_val
                            if answer is not None:
                                total_score += float(answer)
                    
                    elif question.question_type.value == "yes_no":
                        max_score += 1
                        if answer:
                            total_score += 1
        
        # Create score record
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        score = ResponseScore(
            response_id=response.id,
            total_score=total_score,
            max_possible_score=max_score,
            percentage_score=percentage,
            subscale_scores={},
            interpretation=ResponseService._get_interpretation(percentage)
        )
        
        db.add(score)
        await db.commit()
        await db.refresh(score)
        
        return score
    
    @staticmethod
    def _get_interpretation(percentage: float) -> str:
        """Get basic interpretation based on percentage"""
        if percentage >= 80:
            return "High score range"
        elif percentage >= 60:
            return "Above average range"
        elif percentage >= 40:
            return "Average range"
        elif percentage >= 20:
            return "Below average range"
        else:
            return "Low score range"
    
    @staticmethod
    def get_response_score(db: Session, response_id: int) -> Optional[ResponseScore]:
        """Get score for a response"""
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    def delete_response(db: Session, response: AssessmentResponse) -> None:
        """Delete response"""
        db.delete(response)
        await db.commit()
    
    @staticmethod
    def validate_response_data(
        db: Session,
        assessment_id: int,
        responses_data: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Validate response data against assessment structure"""
        assessment = db.query(Assessment).options(
            joinedload(Assessment.sections).joinedload(Assessment.sections[0].questions)
        ).filter(Assessment.id == assessment_id).first()
        
        if not assessment:
            return False, "Assessment not found"
        
        # Check required questions
        for section in assessment.sections:
            for question in section.questions:
                if question.is_required:
                    q_id = str(question.id)
                    if q_id not in responses_data or responses_data[q_id] is None:
                        return False, f"Required question '{question.question_text}' not answered"
        
        return True, None
    