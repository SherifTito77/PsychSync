# app/infrastructure/repositories/assessment_repository.py
"""
Assessment Repository Implementation

Handles all data access operations for Assessment entities.
Follows the Repository Pattern to separate data access from business logic.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.assessment import Assessment as AssessmentModel
from app.domain.entities.assessment import AssessmentStatus
from app.infrastructure.repositories.base import BaseRepository
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate


class AssessmentRepository(
    BaseRepository[AssessmentModel, AssessmentCreate, AssessmentUpdate]
):
    """
    Repository for Assessment entity.

    Provides data access methods for Assessment operations.
    All database queries for Assessment should go through this repository.

    Example:
        repo = AssessmentRepository(db_session)
        assessment = await repo.get_published_by_id(assessment_id)
        assessments = await repo.list_by_category("personality")
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize assessment repository.

        Args:
            db: Async database session
        """
        super().__init__(AssessmentModel, db)

    # ========================================================================
    # FIND BY STATUS
    # ========================================================================

    async def get_published_by_id(
        self, assessment_id: UUID
    ) -> Optional[AssessmentModel]:
        """
        Get published assessment by ID.

        Args:
            assessment_id: Assessment ID

        Returns:
            Assessment model or None if not found or not published

        Example:
            >>> assessment = await assessment_repo.get_published_by_id(assessment_id)
            >>> if assessment:
            ...     print(f"Found: {assessment.title}")
        """
        result = await self._db.execute(
            select(AssessmentModel).where(
                and_(
                    AssessmentModel.id == assessment_id,
                    AssessmentModel.status == AssessmentStatus.PUBLISHED.value,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 100,
        team_id: Optional[UUID] = None,
    ) -> tuple[list[AssessmentModel], int]:
        """
        List assessments by status.

        Args:
            status: Assessment status (draft, published, archived)
            skip: Pagination offset
            limit: Pagination limit
            team_id: Optional team filter

        Returns:
            Tuple of (assessments, total count)

        Example:
            >>> published, total = await assessment_repo.list_by_status("published")
        """
        query = select(AssessmentModel).where(AssessmentModel.status == status)

        if team_id:
            query = query.where(
                or_(
                    AssessmentModel.team_id == team_id,
                    AssessmentModel.team_id.is_(None),  # Public assessments
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self._db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.offset(skip).limit(limit)
        query = query.order_by(AssessmentModel.created_at.desc())

        result = await self._db.execute(query)
        assessments = result.scalars().all()

        return list(assessments), total

    # ========================================================================
    # FIND BY CATEGORY
    # ========================================================================

    async def list_by_category(
        self,
        category: str,
        skip: int = 0,
        limit: int = 100,
        only_published: bool = True,
    ) -> tuple[list[AssessmentModel], int]:
        """
        List assessments by category.

        Args:
            category: Assessment category
            skip: Pagination offset
            limit: Pagination limit
            only_published: Only show published assessments

        Returns:
            Tuple of (assessments, total count)

        Example:
            >>> personality, total = await assessment_repo.list_by_category("personality")
        """
        query = select(AssessmentModel).where(AssessmentModel.category == category)

        if only_published:
            query = query.where(
                AssessmentModel.status == AssessmentStatus.PUBLISHED.value
            )

        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self._db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        query = query.offset(skip).limit(limit)
        query = query.order_by(AssessmentModel.created_at.desc())

        result = await self._db.execute(query)
        assessments = result.scalars().all()

        return list(assessments), total

    # ========================================================================
    # TEAM ASSESSMENTS
    # ========================================================================

    async def list_by_team(
        self,
        team_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_public: bool = False,
    ) -> tuple[list[AssessmentModel], int]:
        """
        List assessments for a team.

        Args:
            team_id: Team ID
            skip: Pagination offset
            limit: Pagination limit
            include_public: Include public assessments in results

        Returns:
            Tuple of (assessments, total count)
        """
        if include_public:
            query = select(AssessmentModel).where(
                or_(
                    AssessmentModel.team_id == team_id,
                    AssessmentModel.is_public == True,
                )
            )
        else:
            query = select(AssessmentModel).where(AssessmentModel.team_id == team_id)

        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self._db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        query = query.offset(skip).limit(limit)
        query = query.order_by(AssessmentModel.created_at.desc())

        result = await self._db.execute(query)
        assessments = result.scalars().all()

        return list(assessments), total

    # ========================================================================
    # SEARCH
    # ========================================================================

    async def search(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        only_published: bool = True,
    ) -> tuple[list[AssessmentModel], int]:
        """
        Search assessments by title or description.

        Args:
            search_term: Search query
            skip: Pagination offset
            limit: Pagination limit
            only_published: Only search published assessments

        Returns:
            Tuple of (assessments, total count)

        Example:
            >>> assessments, total = await assessment_repo.search("personality")
        """
        search_pattern = f"%{search_term.lower()}%"

        query = select(AssessmentModel).where(
            or_(
                AssessmentModel.title.ilike(search_pattern),
                AssessmentModel.description.ilike(search_pattern),
            )
        )

        if only_published:
            query = query.where(
                AssessmentModel.status == AssessmentStatus.PUBLISHED.value
            )

        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self._db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        query = query.offset(skip).limit(limit)
        query = query.order_by(AssessmentModel.created_at.desc())

        result = await self._db.execute(query)
        assessments = result.scalars().all()

        return list(assessments), total

    # ========================================================================
    # WITH RELATIONSHIPS
    # ========================================================================

    async def get_with_sections(self, assessment_id: UUID) -> Optional[AssessmentModel]:
        """
        Get assessment with sections eager loaded.

        Args:
            assessment_id: Assessment ID

        Returns:
            Assessment with sections or None

        Example:
            >>> assessment = await assessment_repo.get_with_sections(assessment_id)
            >>> for section in assessment.sections:
            ...     print(section.title)
        """
        result = await self._db.execute(
            select(AssessmentModel)
            .options(selectinload(AssessmentModel.sections))
            .where(AssessmentModel.id == assessment_id)
        )
        return result.scalar_one_or_none()

    async def get_with_all_relations(
        self, assessment_id: UUID
    ) -> Optional[AssessmentModel]:
        """
        Get assessment with all relationships eager loaded.

        Args:
            assessment_id: Assessment ID

        Returns:
            Assessment with all relations or None

        Example:
            >>> assessment = await assessment_repo.get_with_all_relations(assessment_id)
            >>> # Has sections, questions, etc. pre-loaded
        """
        result = await self._db.execute(
            select(AssessmentModel)
            .options(
                selectinload(AssessmentModel.sections).selectinload(
                    "sections.questions"
                )
            )
            .where(AssessmentModel.id == assessment_id)
        )
        return result.scalar_one_or_none()

    # ========================================================================
    # STATUS OPERATIONS
    # ========================================================================

    async def publish(self, assessment_id: UUID) -> Optional[AssessmentModel]:
        """
        Publish an assessment.

        Args:
            assessment_id: Assessment ID

        Returns:
            Updated assessment or None if not found

        Example:
            >>> assessment = await assessment_repo.publish(assessment_id)
            >>> assert assessment.status == "published"
        """
        assessment = await self.get(assessment_id)
        if assessment:
            from datetime import datetime

            assessment.status = AssessmentStatus.PUBLISHED.value
            assessment.published_at = datetime.utcnow()
            await self._db.flush()
        return assessment

    async def archive(self, assessment_id: UUID) -> Optional[AssessmentModel]:
        """
        Archive an assessment.

        Args:
            assessment_id: Assessment ID

        Returns:
            Updated assessment or None if not found
        """
        assessment = await self.get(assessment_id)
        if assessment:
            assessment.status = AssessmentStatus.ARCHIVED.value
            await self._db.flush()
        return assessment

    # ========================================================================
    # STATISTICS
    # ========================================================================

    async def count_by_status(self) -> dict[str, int]:
        """
        Count assessments grouped by status.

        Returns:
            Dictionary mapping status to count

        Example:
            >>> counts = await assessment_repo.count_by_status()
            >>> print(counts)
            {'draft': 15, 'published': 42, 'archived': 8}
        """
        result = await self._db.execute(
            select(AssessmentModel.status, func.count(AssessmentModel.id)).group_by(
                AssessmentModel.status
            )
        )

        return {row[0]: row[1] for row in result.all()}

    async def count_by_category(self) -> dict[str, int]:
        """
        Count assessments grouped by category.

        Returns:
            Dictionary mapping category to count

        Example:
            >>> counts = await assessment_repo.count_by_category()
            >>> print(counts)
            {'personality': 20, 'clinical': 15, 'cognitive': 10}
        """
        result = await self._db.execute(
            select(AssessmentModel.category, func.count(AssessmentModel.id)).group_by(
                AssessmentModel.category
            )
        )

        return {row[0]: row[1] for row in result.all()}

    async def get_popular(self, limit: int = 10) -> list[AssessmentModel]:
        """
        Get most popular assessments (by response count).

        Args:
            limit: Maximum number to return

        Returns:
            List of popular assessments

        Example:
            >>> popular = await assessment_repo.get_popular(limit=5)
        """
        # This would require a responses table with response counts
        # For now, return most recently created
        result = await self._db.execute(
            select(AssessmentModel)
            .where(AssessmentModel.status == AssessmentStatus.PUBLISHED.value)
            .order_by(AssessmentModel.created_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())
