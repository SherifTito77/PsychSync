# app/repositories/response_repository.py

"""
ENTERPRISE-GRADE RESPONSE REPOSITORY
Response-specific data access operations for assessment responses

RESPONSE REPOSITORY FEATURES:
- Response CRUD operations
- User and assessment-based queries
- Response analytics
- Scoring data access
"""

import logging
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.assessment import Assessment
from app.db.models.response import Response
from app.db.models.user import User
from app.repositories.base_repository import BaseRepository
from app.schemas.response import ResponseCreate, ResponseUpdate

# Initialize response repository logger
response_repo_logger = logging.getLogger("app.repositories.response")


class ResponseRepository(BaseRepository[Response, ResponseCreate, ResponseUpdate]):
    """
    Response-specific repository with comprehensive response management operations
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize response repository

        Args:
            db: Database session
        """
        super().__init__(db, Response)

    async def get_by_user(
        self,
        user_id: Any,
        skip: int = 0,
        limit: int = 1000,
        include_assessment: bool = False,
    ) -> list[Response]:
        """
        Get responses by user

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_assessment: Whether to include assessment data

        Returns:
            List of Response instances
        """
        try:
            query = select(Response).where(Response.user_id == user_id)

            if include_assessment:
                query = query.options(selectinload(Response.assessment))

            query = query.order_by(Response.created_at.desc()).offset(skip).limit(limit)

            result = await self.db.execute(query)
            responses = result.scalars().all()

            response_repo_logger.debug(
                f"Retrieved {len(responses)} responses for user {user_id}",
                extra={"user_id": user_id, "count": len(responses)},
            )

            return responses

        except Exception as e:
            response_repo_logger.error(
                f"Error getting responses by user {user_id}: {e}"
            )
            raise

    async def get_by_assessment(
        self,
        assessment_id: Any,
        skip: int = 0,
        limit: int = 1000,
        include_user: bool = False,
    ) -> list[Response]:
        """
        Get responses by assessment

        Args:
            assessment_id: Assessment ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_user: Whether to include user data

        Returns:
            List of Response instances
        """
        try:
            query = select(Response).where(Response.assessment_id == assessment_id)

            if include_user:
                query = query.options(selectinload(Response.user))

            query = query.order_by(Response.created_at.desc()).offset(skip).limit(limit)

            result = await self.db.execute(query)
            responses = result.scalars().all()

            response_repo_logger.debug(
                f"Retrieved {len(responses)} responses for assessment {assessment_id}",
                extra={"assessment_id": assessment_id, "count": len(responses)},
            )

            return responses

        except Exception as e:
            response_repo_logger.error(
                f"Error getting responses by assessment {assessment_id}: {e}"
            )
            raise

    async def get_completed(
        self,
        user_id: Any = None,
        assessment_id: Any = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Response]:
        """
        Get completed responses with optional filtering

        Args:
            user_id: Optional user filter
            assessment_id: Optional assessment filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of completed Response instances
        """
        try:
            query = select(Response).where(
                and_(
                    Response.submitted_at.isnot(None),
                    Response.deleted_at.is_(None),
                )
            )

            if user_id:
                query = query.where(Response.user_id == user_id)
            if assessment_id:
                query = query.where(Response.assessment_id == assessment_id)

            query = (
                query.order_by(Response.submitted_at.desc()).offset(skip).limit(limit)
            )

            result = await self.db.execute(query)
            responses = result.scalars().all()

            response_repo_logger.debug(
                f"Retrieved {len(responses)} completed responses",
                extra={"user_id": user_id, "assessment_id": assessment_id},
            )

            return responses

        except Exception as e:
            response_repo_logger.error("Error getting completed responses: {e}")
            raise

    async def get_in_progress(
        self,
        user_id: Any = None,
        assessment_id: Any = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Response]:
        """
        Get in-progress responses with optional filtering

        Args:
            user_id: Optional user filter
            assessment_id: Optional assessment filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of in-progress Response instances
        """
        try:
            query = select(Response).where(
                and_(
                    Response.submitted_at.is_(None),
                    Response.deleted_at.is_(None),
                )
            )

            if user_id:
                query = query.where(Response.user_id == user_id)
            if assessment_id:
                query = query.where(Response.assessment_id == assessment_id)

            query = query.order_by(Response.created_at.desc()).offset(skip).limit(limit)

            result = await self.db.execute(query)
            responses = result.scalars().all()

            response_repo_logger.debug(
                f"Retrieved {len(responses)} in-progress responses",
                extra={"user_id": user_id, "assessment_id": assessment_id},
            )

            return responses

        except Exception as e:
            response_repo_logger.error("Error getting in-progress responses: {e}")
            raise

    async def get_response_statistics(
        self, user_id: Any = None, assessment_id: Any = None
    ) -> dict[str, Any]:
        """
        Get response statistics

        Args:
            user_id: Optional user filter
            assessment_id: Optional assessment filter

        Returns:
            Dictionary with response statistics
        """
        try:
            base_filters = [Response.deleted_at.is_(None)]
            if user_id:
                base_filters.append(Response.user_id == user_id)
            if assessment_id:
                base_filters.append(Response.assessment_id == assessment_id)

            # Total responses
            total_query = select(func.count(Response.id)).where(and_(*base_filters))
            total_result = await self.db.execute(total_query)
            total_responses = total_result.scalar()

            # Completed responses
            completed_filters = base_filters + [Response.submitted_at.isnot(None)]
            completed_query = select(func.count(Response.id)).where(
                and_(*completed_filters)
            )
            completed_result = await self.db.execute(completed_query)
            completed_responses = completed_result.scalar()

            # In-progress responses
            in_progress_filters = base_filters + [Response.submitted_at.is_(None)]
            in_progress_query = select(func.count(Response.id)).where(
                and_(*in_progress_filters)
            )
            in_progress_result = await self.db.execute(in_progress_query)
            in_progress_responses = in_progress_result.scalar()

            # Average score (for completed responses)
            score_query = (
                select(func.avg(Response.score))
                .where(and_(*completed_filters))
                .where(Response.score.isnot(None))
            )
            score_result = await self.db.execute(score_query)
            average_score = score_result.scalar()

            # Average completion time
            time_query = (
                select(func.avg(Response.time_taken))
                .where(and_(*completed_filters))
                .where(Response.time_taken.isnot(None))
            )
            time_result = await self.db.execute(time_query)
            average_time = time_result.scalar()

            statistics = {
                "total_responses": total_responses,
                "completed_responses": completed_responses,
                "in_progress_responses": in_progress_responses,
                "completion_rate": (
                    (completed_responses / total_responses * 100)
                    if total_responses > 0
                    else 0
                ),
                "average_score": float(average_score) if average_score else None,
                "average_time": float(average_time) if average_time else None,
            }

            response_repo_logger.debug(
                "Response statistics retrieved",
                extra={
                    "user_id": user_id,
                    "assessment_id": assessment_id,
                    "statistics": statistics,
                },
            )

            return statistics

        except Exception as e:
            response_repo_logger.error("Error getting response statistics: {e}")
            raise

    async def get_user_latest_response(
        self, user_id: Any, assessment_id: Any
    ) -> Response | None:
        """
        Get user's latest response for an assessment

        Args:
            user_id: User ID
            assessment_id: Assessment ID

        Returns:
            Latest Response instance or None
        """
        try:
            query = (
                select(Response)
                .where(
                    and_(
                        Response.user_id == user_id,
                        Response.assessment_id == assessment_id,
                        Response.deleted_at.is_(None),
                    )
                )
                .order_by(Response.created_at.desc())
                .limit(1)
            )

            result = await self.db.execute(query)
            response = result.scalar_one_or_none()

            if response:
                response_repo_logger.debug(
                    f"Latest response found for user {user_id}, assessment {assessment_id}",
                    extra={"response_id": response.id},
                )

            return response

        except Exception as e:
            response_repo_logger.error(
                f"Error getting latest response for user {user_id}, assessment {assessment_id}: {e}"
            )
            raise
