# app/services/response_service.py
"""
Response Service - Cleaned and fixed version
Handles assessment responses with proper async support
"""
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.response import Response, AssessmentResponse
from app.schemas.response import ResponseCreate, ResponseUpdate

class ResponseService:

    @staticmethod
    async def create(db: AsyncSession, *, response_in: ResponseCreate) -> Response:
        """Create a new assessment response."""
        response = Response(
            assessment_id=response_in.assessment_id,
            user_id=response_in.user_id,
            question_id=response_in.question_id,
            answer_text=getattr(response_in, 'answer_text', None),
            answer_value=getattr(response_in, 'answer_value', None),
            answer_data=getattr(response_in, 'answer_data', None),
            response_time_ms=getattr(response_in, 'response_time_ms', None),
            confidence_rating=getattr(response_in, 'confidence_rating', None),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(response)
        await db.commit()
        await db.refresh(response)

        # Calculate initial score if possible
        await ResponseService._calculate_score(db, response)

        return response

    @staticmethod
    async def get_by_id(db: AsyncSession, response_id: UUID) -> Optional[Response]:
        """Get response by ID."""
        result = await db.execute(select(Response).where(Response.id == response_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_assessment(
        db: AsyncSession,
        assessment_id: UUID,
        user_id: Optional[UUID] = None
    ) -> List[Response]:
        """Get responses for an assessment, optionally filtered by user."""
        query = select(Response).where(Response.assessment_id == assessment_id)

        if user_id:
            query = query.where(Response.user_id == user_id)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_user(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 100
    ) -> List[Response]:
        """Get user's responses."""
        result = await db.execute(
            select(Response)
            .where(Response.user_id == user_id)
            .order_by(Response.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def update(
        db: AsyncSession,
        *,
        response_id: UUID,
        response_in: ResponseUpdate
    ) -> Optional[Response]:
        """Update a response."""
        result = await db.execute(select(Response).where(Response.id == response_id))
        response = result.scalar_one_or_none()

        if not response:
            return None

        update_data = response_in.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        for field, value in update_data.items():
            setattr(response, field, value)

        await db.commit()
        await db.refresh(response)

        # Recalculate score if answer changed
        if any(key in update_data for key in ['answer_text', 'answer_value', 'answer_data']):
            await ResponseService._calculate_score(db, response)

        return response

    @staticmethod
    async def delete(db: AsyncSession, *, response_id: UUID) -> bool:
        """Delete a response."""
        result = await db.execute(select(Response).where(Response.id == response_id))
        response = result.scalar_one_or_none()

        if not response:
            return False

        await db.delete(response)
        await db.commit()
        return True

    @staticmethod
    async def get_assessment_completion(
        db: AsyncSession,
        assessment_id: UUID,
        user_id: UUID
    ) -> dict:
        """Get completion status for a user's assessment."""
        total_result = await db.execute(
            select(Response).where(
                Response.assessment_id == assessment_id,
                Response.user_id == user_id
            )
        )
        total_responses = len(total_result.scalars().all())

        scored_result = await db.execute(
            select(Response).where(
                Response.assessment_id == assessment_id,
                Response.user_id == user_id,
                Response.score.isnot(None)
            )
        )
        scored_responses = len(scored_result.scalars().all())

        return {
            "total_questions": total_responses,
            "answered_questions": total_responses,
            "scored_questions": scored_responses,
            "completion_rate": total_responses / max(total_responses, 1),
            "score_rate": scored_responses / max(total_responses, 1)
        }

    @staticmethod
    async def _calculate_score(db: AsyncSession, response: Response) -> None:
        """Internal method to calculate response score."""
        # Simple scoring logic - can be enhanced based on question type
        if response.answer_value is not None:
            # Assuming 1-5 scale, normalize to 0-1
            response.score = min(response.answer_value / 5.0, 1.0)
            response.normalized_score = response.score

        await db.commit()

    @staticmethod
    async def bulk_create(
        db: AsyncSession,
        responses: List[ResponseCreate]
    ) -> List[Response]:
        """Create multiple responses efficiently."""
        created_responses = []

        for response_in in responses:
            response = await ResponseService.create(db=db, response_in=response_in)
            created_responses.append(response)

        return created_responses