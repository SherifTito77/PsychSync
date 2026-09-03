# app/crud/crud_build_analysis.py
"""
CRUD operations for Build Failure Analysis
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models.build_analysis import (
    BuildAnalysisReport,
    BuildFailure,
    BuildPattern,
    RootCauseAnalysis,
)


class CRUDBuildFailure:
    """CRUD operations for build failures"""

    async def get(self, db: AsyncSession, id: UUID) -> Optional[BuildFailure]:
        """Get build failure by ID"""
        result = await db.execute(select(BuildFailure).where(BuildFailure.id == id))
        return result.scalar_one_or_none()

    async def get_by_build_id(
        self, db: AsyncSession, *, build_id: str
    ) -> Optional[BuildFailure]:
        """Get build failure by build ID"""
        result = await db.execute(
            select(BuildFailure).where(BuildFailure.build_id == build_id)
        )
        return result.scalar_one_or_none()

    async def get_unresolved(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[BuildFailure]:
        """Get unresolved build failures"""
        result = await db.execute(
            select(BuildFailure)
            .where(BuildFailure.is_resolved == 0.0)
            .order_by(BuildFailure.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_priority(
        self, db: AsyncSession, *, priority: str, skip: int = 0, limit: int = 100
    ) -> list[BuildFailure]:
        """Get failures by priority"""
        result = await db.execute(
            select(BuildFailure)
            .where(BuildFailure.priority == priority)
            .where(BuildFailure.is_resolved == 0.0)
            .order_by(BuildFailure.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_failure_type(
        self, db: AsyncSession, *, failure_type: str, skip: int = 0, limit: int = 100
    ) -> list[BuildFailure]:
        """Get failures by type"""
        result = await db.execute(
            select(BuildFailure)
            .where(BuildFailure.failure_type == failure_type)
            .order_by(BuildFailure.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_developer(
        self, db: AsyncSession, *, developer_name: str, skip: int = 0, limit: int = 100
    ) -> list[BuildFailure]:
        """Get failures by developer"""
        result = await db.execute(
            select(BuildFailure)
            .where(BuildFailure.developer_name == developer_name)
            .order_by(BuildFailure.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[BuildFailure]:
        """Get multiple build failures"""
        result = await db.execute(
            select(BuildFailure)
            .order_by(BuildFailure.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[BuildFailure]:
        """Get recent build failures (alias for get_multi)"""
        return await self.get_multi(db, skip=skip, limit=limit)

    async def create(self, db: AsyncSession, *, obj_in: dict) -> BuildFailure:
        """Create new build failure"""
        db_obj = BuildFailure(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: BuildFailure, obj_in: dict
    ) -> BuildFailure:
        """Update build failure"""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: UUID) -> Optional[BuildFailure]:
        """Delete build failure"""
        obj = await self.get(db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def resolve(
        self,
        db: AsyncSession,
        *,
        failure_id: UUID,
        resolution_notes: str,
        fix_commit_hash: str,
        resolution_time_minutes: int
    ) -> Optional[BuildFailure]:
        """Mark build failure as resolved"""
        failure = await self.get(db, id=failure_id)
        if failure:
            failure.is_resolved = 1.0
            failure.resolution_notes = resolution_notes
            failure.fix_commit_hash = fix_commit_hash
            failure.resolution_time_minutes = resolution_time_minutes
            await db.commit()
            await db.refresh(failure)
        return failure

    async def mark_as_resolved(
        self,
        db: AsyncSession,
        *,
        failure_id: UUID,
        resolution_notes: str,
        fix_commit_hash: str,
        resolution_time_minutes: int
    ) -> Optional[BuildFailure]:
        """Mark build failure as resolved (alias for resolve)"""
        return await self.resolve(
            db,
            failure_id=failure_id,
            resolution_notes=resolution_notes,
            fix_commit_hash=fix_commit_hash,
            resolution_time_minutes=resolution_time_minutes,
        )

    def calculate_health_grade(
        self,
        total_failures,
        unresolved_failures,
        critical_failures,
        avg_resolution_time,
    ) -> str:
        """Calculate overall health grade"""
        score = 100

        # Deduct for failures
        score -= min(total_failures * 2, 40)

        # Deduct for unresolved
        unresolved_ratio = unresolved_failures / max(total_failures, 1)
        score -= int(unresolved_ratio * 30)

        # Deduct for critical failures
        score -= min(critical_failures * 10, 30)

        # Adjust for resolution time
        if avg_resolution_time > 480:  # 8 hours
            score -= 10
        elif avg_resolution_time > 1440:  # 24 hours
            score -= 20

        score = max(0, min(100, score))

        # Convert to letter grade
        if score >= 97:
            return "A+"
        elif score >= 93:
            return "A"
        elif score >= 90:
            return "A-"
        elif score >= 87:
            return "B+"
        elif score >= 83:
            return "B"
        elif score >= 80:
            return "B-"
        elif score >= 77:
            return "C+"
        elif score >= 73:
            return "C"
        elif score >= 70:
            return "C-"
        elif score >= 67:
            return "D+"
        elif score >= 63:
            return "D"
        elif score >= 60:
            return "D-"
        else:
            return "F"


class CRUDRootCauseAnalysis:
    """CRUD operations for root cause analyses"""

    async def get(self, db: AsyncSession, id: UUID) -> Optional[RootCauseAnalysis]:
        """Get analysis by ID"""
        result = await db.execute(
            select(RootCauseAnalysis).where(RootCauseAnalysis.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_failure_id(
        self, db: AsyncSession, *, failure_id: UUID
    ) -> Optional[RootCauseAnalysis]:
        """Get analysis by failure ID"""
        result = await db.execute(
            select(RootCauseAnalysis).where(RootCauseAnalysis.failure_id == failure_id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[RootCauseAnalysis]:
        """Get recent analyses"""
        result = await db.execute(
            select(RootCauseAnalysis)
            .order_by(RootCauseAnalysis.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: dict) -> RootCauseAnalysis:
        """Create new root cause analysis"""
        db_obj = RootCauseAnalysis(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class CRUDBuildPattern:
    """CRUD operations for build patterns"""

    async def get(self, db: AsyncSession, id: UUID) -> Optional[BuildPattern]:
        """Get pattern by ID"""
        result = await db.execute(select(BuildPattern).where(BuildPattern.id == id))
        return result.scalar_one_or_none()

    async def get_unresolved(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[BuildPattern]:
        """Get unresolved patterns"""
        result = await db.execute(
            select(BuildPattern)
            .where(BuildPattern.is_resolved == 0.0)
            .order_by(BuildPattern.occurrence_count.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_type(
        self, db: AsyncSession, *, pattern_type: str, skip: int = 0, limit: int = 100
    ) -> list[BuildPattern]:
        """Get patterns by type"""
        result = await db.execute(
            select(BuildPattern)
            .where(BuildPattern.pattern_type == pattern_type)
            .where(BuildPattern.is_resolved == 0.0)
            .order_by(BuildPattern.occurrence_count.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: dict) -> BuildPattern:
        """Create new build pattern"""
        db_obj = BuildPattern(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class CRUDBuildAnalysisReport:
    """CRUD operations for build analysis reports"""

    async def get(self, db: AsyncSession, id: UUID) -> Optional[BuildAnalysisReport]:
        """Get report by ID"""
        result = await db.execute(
            select(BuildAnalysisReport).where(BuildAnalysisReport.id == id)
        )
        return result.scalar_one_or_none()

    async def get_latest(
        self, db: AsyncSession, *, limit: int = 10
    ) -> list[BuildAnalysisReport]:
        """Get recent analysis reports"""
        result = await db.execute(
            select(BuildAnalysisReport)
            .order_by(BuildAnalysisReport.report_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: dict) -> BuildAnalysisReport:
        """Create new build analysis report"""
        db_obj = BuildAnalysisReport(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# Instances
build_failure = CRUDBuildFailure()
root_cause_analysis = CRUDRootCauseAnalysis()
build_pattern = CRUDBuildPattern()
build_analysis_report = CRUDBuildAnalysisReport()
