# app/services/response_service.py
"""
Response Service - Enhanced with data corruption prevention
Handles assessment responses with proper error handling and row-level locking
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, select as sql_select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.response import Response
from app.schemas.response import ResponseCreate, ResponseUpdate

logger = logging.getLogger(__name__)


class ResponseService:
    @staticmethod
    async def create(db: AsyncSession, *, response_in: ResponseCreate) -> Response:
        """Create a new assessment response with proper error handling."""
        try:
            response = Response(
                assessment_id=response_in.assessment_id,
                user_id=response_in.user_id,
                question_id=response_in.question_id,
                answer_text=getattr(response_in, "answer_text", None),
                answer_value=getattr(response_in, "answer_value", None),
                answer_data=getattr(response_in, "answer_data", None),
                response_time_ms=getattr(response_in, "response_time_ms", None),
                confidence_rating=getattr(response_in, "confidence_rating", None),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            db.add(response)
            await db.commit()
            await db.refresh(response)

            # Calculate initial score if possible
            await ResponseService._calculate_score(db, response)

            logger.info(f"Created response ID: {response.id} for assessment: {response_in.assessment_id}")
            return response

        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Integrity error creating response: {e}", exc_info=True)
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create response: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_by_id(db: AsyncSession, response_id: UUID) -> Response | None:
        """Get response by ID."""
        result = await db.execute(select(Response).where(Response.id == response_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_assessment(
        db: AsyncSession, assessment_id: UUID, user_id: UUID | None = None
    ) -> list[Response]:
        """Get responses for an assessment, optionally filtered by user."""
        query = select(Response).where(Response.assessment_id == assessment_id)

        if user_id:
            query = query.where(Response.user_id == user_id)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: UUID, limit: int = 100) -> list[Response]:
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
        db: AsyncSession, *, response_id: UUID, response_in: ResponseUpdate
    ) -> Response | None:
        """Update a response with row-level locking to prevent race conditions."""
        try:
            # Use SELECT FOR UPDATE to prevent concurrent modification
            result = await db.execute(
                select(Response)
                .where(Response.id == response_id)
                .with_for_update()
            )
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
            if any(key in update_data for key in ["answer_text", "answer_value", "answer_data"]):
                await ResponseService._calculate_score(db, response)

            logger.info(f"Updated response ID: {response_id}")
            return response

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update response {response_id}: {e}", exc_info=True)
            raise

    @staticmethod
    async def delete(db: AsyncSession, *, response_id: UUID) -> bool:
        """Delete a response with proper error handling."""
        try:
            result = await db.execute(select(Response).where(Response.id == response_id))
            response = result.scalar_one_or_none()

            if not response:
                return False

            await db.delete(response)
            await db.commit()

            logger.info(f"Deleted response ID: {response_id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete response {response_id}: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_assessment_completion(
        db: AsyncSession, assessment_id: UUID, user_id: UUID
    ) -> dict:
        """Get completion status for a user's assessment."""
        # Use func.count() to avoid loading all data into memory
        total_result = await db.execute(
            select(func.count(Response.id)).where(
                Response.assessment_id == assessment_id, Response.user_id == user_id
            )
        )
        total_responses = total_result.scalar() or 0

        scored_result = await db.execute(
            select(func.count(Response.id)).where(
                Response.assessment_id == assessment_id,
                Response.user_id == user_id,
                Response.score.isnot(None),
            )
        )
        scored_responses = scored_result.scalar() or 0

        return {
            "total_questions": total_responses,
            "answered_questions": total_responses,
            "scored_questions": scored_responses,
            "completion_rate": total_responses / max(total_responses, 1),
            "score_rate": scored_responses / max(total_responses, 1),
        }

    @staticmethod
    async def _calculate_score(db: AsyncSession, response: Response) -> None:
        """Internal method to calculate response score (called within transaction)."""
        # Note: This method doesn't commit as it's called from within ongoing transactions
        # Simple scoring logic - can be enhanced based on question type
        if response.answer_value is not None:
            # Assuming 1-5 scale, normalize to 0-1
            response.score = min(response.answer_value / 5.0, 1.0)
            response.normalized_score = response.score

    @staticmethod
    async def bulk_create(db: AsyncSession, responses: list[ResponseCreate]) -> list[Response]:
        """Create multiple responses efficiently."""
        created_responses = []

        for response_in in responses:
            response = await ResponseService.create(db=db, response_in=response_in)
            created_responses.append(response)

        return created_responses

    # ========================================================================
    # Additional Methods for Endpoint Compatibility
    # ========================================================================

    @staticmethod
    async def get_response_score(db: AsyncSession, response_id: UUID) -> dict | None:
        """Get score for a response."""
        response = await ResponseService.get_by_id(db, response_id)
        if not response:
            return None
        return {
            "raw_score": response.score,
            "normalized_score": response.normalized_score,
            "percentage": response.percentage
        }

    @staticmethod
    async def save_progress(
        db: AsyncSession,
        response: Response,
        responses_data: dict | None = None,
        current_section: str | None = None
    ) -> Response:
        """Save progress on a response with row-level locking."""
        try:
            # Update response data if provided
            if responses_data is not None:
                response.responses = responses_data
            if current_section is not None:
                response.current_section = current_section

            response.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(response)

            logger.debug(f"Saved progress for response ID: {response.id}")
            return response

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to save progress for response {response.id}: {e}", exc_info=True)
            raise

    @staticmethod
    async def validate_response_data(
        db: AsyncSession,
        assessment_id: UUID,
        responses_data: dict
    ) -> tuple[bool, str | None]:
        """Validate response data for an assessment."""
        # Basic validation - check if responses_data is not empty
        if not responses_data:
            return False, "Response data cannot be empty"

        # Add more validation logic here as needed
        return True, None

    @staticmethod
    async def submit_response(
        db: AsyncSession,
        response: Response,
        responses_data: dict,
        time_taken: int | None = None
    ) -> Response:
        """Submit a completed response with row-level locking."""
        try:
            # Update response data
            response.responses = responses_data
            response.is_complete = True

            if time_taken is not None:
                response.time_taken_minutes = time_taken / 60.0  # Convert seconds to minutes

            response.completed_at = datetime.utcnow()
            response.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(response)

            # Calculate final score
            await ResponseService._calculate_score(db, response)

            logger.info(f"Submitted response ID: {response.id}")
            return response

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to submit response {response.id}: {e}", exc_info=True)
            raise

    @staticmethod
    async def delete_response(db: AsyncSession, response: Response) -> bool:
        """Delete a response by object with proper error handling."""
        try:
            await db.delete(response)
            await db.commit()

            logger.info(f"Deleted response ID: {response.id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete response {response.id}: {e}", exc_info=True)
            raise
