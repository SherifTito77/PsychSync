# app/crud/crud_query_performance.py
"""
CRUD operations for Query Performance Optimization
"""

import hashlib
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models.query_performance import (
    SlowQuery,
    IndexRecommendation,
    QueryPerformanceHistory,
    QueryOptimizationReport,
)
from app.schemas.query_performance import (
    SlowQueryCreate,
    SlowQueryUpdate,
    IndexRecommendationCreate,
    IndexRecommendationUpdate,
)


class CRUDSlowQuery:
    """CRUD operations for slow queries"""

    async def get(self, db: AsyncSession, id: UUID) -> Optional[SlowQuery]:
        """Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
        """
        """Get query by ID"""
        result = await db.execute(select(SlowQuery).where(SlowQuery.id == id))
        return result.scalar_one_or_none()

    async def get_by_hash(self, db: AsyncSession, *, query_hash: str) -> Optional[SlowQuery]:
        """Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
        """
        """Get query by hash"""
        result = await db.execute(select(SlowQuery).where(SlowQuery.query_hash == query_hash))
        return result.scalar_one_or_none()

    async def get_by_performance_tier(
        """Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
        """
        self, db: AsyncSession, *, tier: str, skip: int = 0, limit: int = 100
    ) -> list[SlowQuery]:
        """Get queries by performance tier"""
        result = await db.execute(
            select(SlowQuery)
            .where(SlowQuery.performance_tier == tier)
            .order_by(SlowQuery.impact_score.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_unoptimized(
        """Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
        """
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[SlowQuery]:
        """Get unoptimized queries ordered by impact score"""
        result = await db.execute(
            select(SlowQuery)
            .where(SlowQuery.is_optimized == 0.0)
            .order_by(SlowQuery.impact_score.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_top_slow(
        """Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
        """
        self, db: AsyncSession, *, limit: int = 10
    ) -> list[SlowQuery]:
        """Get top slowest queries"""
        result = await db.execute(
            select(SlowQuery)
            .order_by(SlowQuery.avg_time_ms.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    def calculate_query_hash(self, query_text: str) -> str:
        """Generate hash for query deduplication"""
        return hashlib.sha256(query_text.encode()).hexdigest()

    def calculate_signature(self, query_text: str) -> str:
        """Generate normalized query signature"""
        # Simple signature: normalize whitespace and remove values
        import re
        normalized = re.sub(r"\s+", " ", query_text.strip())
        normalized = re.sub(r"'[^']*'", "?", normalized)  # Replace strings
        normalized = re.sub(r"\b\d+\b", "?", normalized)  # Replace numbers
        return normalized[:200]

    async def mark_as_optimized(
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        self, db: AsyncSession, *, query_id: UUID
    ) -> Optional[SlowQuery]:
        """Mark query as optimized"""
        query = await self.get(db, id=query_id)
        if query:
            query.is_optimized = 1.0
            await db.commit()
            await db.refresh(query)
        return query

    async def update(self, db: AsyncSession, *, db_obj: SlowQuery, obj_in: SlowQueryUpdate | dict[str, Any]) -> SlowQuery:
        """Update an existing resource.

Args:
    db: Database session
    id: Resource ID
    **kwargs: Attributes to update

Returns:
    Updated resource object

Raises:
    NotFoundError: If resource doesn't exist
    ValidationError: If input data is invalid
        """
        """Update query"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class CRUDIndexRecommendation:
    """CRUD operations for index recommendations"""

    async def get(self, db: AsyncSession, id: UUID) -> Optional[IndexRecommendation]:
        """Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
        """
        """Get recommendation by ID"""
        result = await db.execute(select(IndexRecommendation).where(IndexRecommendation.id == id))
        return result.scalar_one_or_none()

    async def get_by_query(
        """Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
        """
        self, db: AsyncSession, *, query_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[IndexRecommendation]:
        """Get recommendations by query ID"""
        result = await db.execute(
            select(IndexRecommendation)
            .where(IndexRecommendation.query_id == query_id)
            .order_by(IndexRecommendation.priority.desc(), IndexRecommendation.estimated_benefit.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_table(
        """Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
        """
        self, db: AsyncSession, *, table_name: str, skip: int = 0, limit: int = 100
    ) -> list[IndexRecommendation]:
        """Get recommendations by table"""
        result = await db.execute(
            select(IndexRecommendation)
            .where(IndexRecommendation.table_name == table_name)
            .where(IndexRecommendation.is_created == 0.0)
            .order_by(IndexRecommendation.priority.desc(), IndexRecommendation.estimated_benefit.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_priority(
        """Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
        """
        self, db: AsyncSession, *, priority: str, skip: int = 0, limit: int = 100
    ) -> list[IndexRecommendation]:
        """Get recommendations by priority"""
        result = await db.execute(
            select(IndexRecommendation)
            .where(IndexRecommendation.priority == priority)
            .where(IndexRecommendation.is_created == 0.0)
            .order_by(IndexRecommendation.estimated_benefit.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_benefit(
        """Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
        """
        self, db: AsyncSession, *, benefit: str, skip: int = 0, limit: int = 100
    ) -> list[IndexRecommendation]:
        """Get recommendations by estimated benefit"""
        result = await db.execute(
            select(IndexRecommendation)
            .where(IndexRecommendation.estimated_benefit == benefit)
            .where(IndexRecommendation.is_created == 0.0)
            .order_by(IndexRecommendation.priority.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


class CRUDQueryOptimizationReport:
    """CRUD operations for optimization reports"""

    async def get_latest(self, db: AsyncSession) -> Optional[QueryOptimizationReport]:
        """Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
        """
        """Get latest optimization report"""
        result = await db.execute(
            select(QueryOptimizationReport).order_by(QueryOptimizationReport.report_date.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_recent(self, db: AsyncSession, *, limit: int = 30) -> list[QueryOptimizationReport]:
        """Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
        """
        """Get recent optimization reports"""
        result = await db.execute(
            select(QueryOptimizationReport).order_by(QueryOptimizationReport.report_date.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def create_report(
        """Create a new resource.

Args:
    db: Database session
    **kwargs: Resource attributes

Returns:
    Created resource object

Raises:
    ValidationError: If input data is invalid
        """
        self,
        db: AsyncSession,
        *,
        report_date,
        total_queries: int,
        slow_queries: int,
        critical_queries: int,
        avg_time: float,
        p95_time: float,
        p99_time: float,
        optimization_potential_ms: float,
        speedup_percentage: float,
        missing_indexes: int,
        n_plus_1: int,
        full_scans: int,
        inefficient_joins: int,
        ai_summary: str,
        ai_insights: dict[str, Any],
        top_slow_queries: list[dict[str, Any]],
    ) -> QueryOptimizationReport:
        """Create optimization report"""
        report = QueryOptimizationReport(
            report_date=report_date,
            total_queries_analyzed=total_queries,
            slow_queries_count=slow_queries,
            critical_queries_count=critical_queries,
            avg_query_time_ms=avg_time,
            p95_query_time_ms=p95_time,
            p99_query_time_ms=p99_time,
            total_optimization_potential_ms=optimization_potential_ms,
            estimated_speedup_percentage=speedup_percentage,
            missing_indexes_count=missing_indexes,
            n_plus_1_count=n_plus_1,
            full_table_scans=full_scans,
            inefficient_joins=inefficient_joins,
            ai_summary=ai_summary,
            ai_insights=ai_insights,
            top_slow_queries=top_slow_queries,
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report


# Create instances
slow_query = CRUDSlowQuery()
index_recommendation = CRUDIndexRecommendation()
query_optimization_report = CRUDQueryOptimizationReport()
