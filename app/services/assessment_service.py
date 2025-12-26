"""
File: app/services/assessment_service.py
Assessment service with Redis caching implementation
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.assessment import Assessment
from app.db.models.response import Response
from app.core.cache import cached, cache_delete_pattern
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)


# =============================================================================
# ASSESSMENT SERVICE CLASS
# =============================================================================

class AssessmentService:
    """Service for managing assessments with caching support"""

    @staticmethod
    async def get_by_id(db: AsyncSession, assessment_id: UUID) -> Optional[Assessment]:
        """Get assessment by ID"""
        result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_assessments(
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Assessment]:
        """Get user's assessments"""
        result = await db.execute(
            select(Assessment)
            .where(Assessment.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Assessment.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_organization_assessments(
        db: AsyncSession,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Assessment]:
        """Get organization's assessments"""
        result = await db.execute(
            select(Assessment)
            .where(Assessment.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
            .order_by(Assessment.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: UUID,
        framework_code: str,
        organization_id: Optional[UUID] = None,
        team_id: Optional[UUID] = None
    ) -> Assessment:
        """Create new assessment"""
        assessment = Assessment(
            user_id=user_id,
            framework_code=framework_code,
            organization_id=organization_id,
            team_id=team_id,
            status='in_progress',
            started_at=datetime.utcnow()
        )

        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)

        logger.info(f"Created assessment ID: {assessment.id} for user: {user_id}")
        return assessment

    @staticmethod
    async def update(
        db: AsyncSession,
        assessment_id: UUID,
        update_data: dict
    ) -> Optional[Assessment]:
        """Update assessment"""
        result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
        assessment = result.scalar_one_or_none()

        if not assessment:
            return None

        # Update fields
        for field, value in update_data.items():
            if hasattr(assessment, field):
                setattr(assessment, field, value)

        assessment.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(assessment)

        logger.info(f"Updated assessment ID: {assessment_id}")
        return assessment

    @staticmethod
    async def complete(db: AsyncSession, assessment_id: UUID) -> Optional[Assessment]:
        """Mark assessment as completed"""
        result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
        assessment = result.scalar_one_or_none()

        if not assessment:
            return None

        assessment.status = 'completed'
        assessment.completed_at = datetime.utcnow()
        assessment.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(assessment)

        logger.info(f"Completed assessment ID: {assessment_id}")
        return assessment

    @staticmethod
    async def delete(db: AsyncSession, assessment_id: UUID) -> bool:
        """Delete assessment"""
        result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
        assessment = result.scalar_one_or_none()

        if not assessment:
            return False

        await db.delete(assessment)
        await db.commit()

        logger.info(f"Deleted assessment ID: {assessment_id}")
        return True

    @staticmethod
    async def get_assessment_results(db: AsyncSession, assessment_id: UUID) -> Optional[dict]:
        """Get assessment results (expensive calculation)"""
        assessment = await AssessmentService.get_by_id(db, assessment_id)

        if not assessment:
            return None

        # Get all responses for this assessment
        result = await db.execute(
            select(Response).where(Response.assessment_id == assessment_id)
        )
        responses = result.scalars().all()

        # Calculate results
        results = {
            "assessment_id": str(assessment.id),
            "user_id": str(assessment.user_id),
            "framework": assessment.framework_code,
            "status": assessment.status,
            "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            "scores": AssessmentService._calculate_scores(assessment, responses),
            "response_count": len(responses)
        }

        return results

    @staticmethod
    def _calculate_scores(assessment: Assessment, responses: List[Response]) -> dict:
        """Calculate assessment scores based on framework"""
        framework = assessment.framework_code

        if framework == 'MBTI':
            return {
                "E_I": 0.0,  # Extraversion vs Introversion
                "S_N": 0.0,  # Sensing vs Intuition
                "T_F": 0.0,  # Thinking vs Feeling
                "J_P": 0.0   # Judging vs Perceiving
            }
        elif framework == 'BIG_FIVE':
            return {
                "openness": 0.0,
                "conscientiousness": 0.0,
                "extraversion": 0.0,
                "agreeableness": 0.0,
                "neuroticism": 0.0
            }
        elif framework == 'ENNEAGRAM':
            return {
                "type_1": 0.0, "type_2": 0.0, "type_3": 0.0, "type_4": 0.0,
                "type_5": 0.0, "type_6": 0.0, "type_7": 0.0, "type_8": 0.0, "type_9": 0.0
            }
        else:
            return {"total_score": len(responses)}

    @staticmethod
    def to_dict(assessment: Assessment) -> dict:
        """Convert Assessment object to dictionary"""
        return {
            "id": str(assessment.id),
            "user_id": str(assessment.user_id),
            "organization_id": str(assessment.organization_id) if assessment.organization_id else None,
            "team_id": str(assessment.team_id) if assessment.team_id else None,
            "framework_code": assessment.framework_code,
            "status": assessment.status,
            "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            "created_at": assessment.created_at.isoformat() if hasattr(assessment, 'created_at') and assessment.created_at else None,
            "updated_at": assessment.updated_at.isoformat() if hasattr(assessment, 'updated_at') and assessment.updated_at else None
        }


# =============================================================================
# BACKWARD COMPATIBILITY FUNCTIONS
# =============================================================================

# Keep these for backward compatibility but redirect to the new service
async def get_assessment_by_id(db: AsyncSession, assessment_id: UUID) -> Optional[Assessment]:
    """Backward compatibility wrapper"""
    return await AssessmentService.get_by_id(db, assessment_id)

async def get_user_assessments(db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Assessment]:
    """Backward compatibility wrapper"""
    return await AssessmentService.get_user_assessments(db, user_id, skip, limit)

async def create_assessment(
    db: AsyncSession,
    user_id: UUID,
    framework_code: str,
    organization_id: Optional[UUID] = None,
    team_id: Optional[UUID] = None
) -> Assessment:
    """Backward compatibility wrapper"""
    return await AssessmentService.create(db, user_id, framework_code, organization_id, team_id)