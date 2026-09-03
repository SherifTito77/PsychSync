# app/crud/crud_breaking_changes.py
"""CRUD operations for Breaking Changes Detection"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models.breaking_changes import (
    BreakingChange,
    BreakingChangeReport,
    MigrationGuide,
)


class CRUDBreakingChange:
    """CRUD operations for breaking changes"""

    async def get(self, db: AsyncSession, id: UUID) -> Optional[BreakingChange]:
        result = await db.execute(select(BreakingChange).where(BreakingChange.id == id))
        return result.scalar_one_or_none()

    async def get_unapproved(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[BreakingChange]:
        result = await db.execute(
            select(BreakingChange)
            .where(BreakingChange.is_approved == 0.0)
            .order_by(BreakingChange.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[BreakingChange]:
        result = await db.execute(select(BreakingChange).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_recent(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[BreakingChange]:
        """Get recent breaking changes (alias for get_multi)"""
        return await self.get_multi(db, skip=skip, limit=limit)

    async def create(self, db: AsyncSession, *, obj_in: dict) -> BreakingChange:
        db_obj = BreakingChange(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: BreakingChange, obj_in: dict
    ) -> BreakingChange:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def mark_as_approved(
        self, db: AsyncSession, *, change_id: UUID, approved_by: str
    ) -> Optional[BreakingChange]:
        change = await self.get(db, id=change_id)
        if change:
            change.is_approved = 1.0
            change.approved_by = approved_by
            await db.commit()
            await db.refresh(change)
        return change

    def calculate_risk_grade(self, risk_score: float) -> str:
        if risk_score >= 90:
            return "F"
        elif risk_score >= 80:
            return "D"
        elif risk_score >= 70:
            return "C"
        elif risk_score >= 60:
            return "B"
        else:
            return "A"


class CRUDMigrationGuide:
    """CRUD operations for migration guides"""

    async def get(self, db: AsyncSession, id: UUID) -> Optional[MigrationGuide]:
        result = await db.execute(select(MigrationGuide).where(MigrationGuide.id == id))
        return result.scalar_one_or_none()

    async def get_by_change(
        self, db: AsyncSession, *, breaking_change_id: UUID
    ) -> list[MigrationGuide]:
        result = await db.execute(
            select(MigrationGuide).where(
                MigrationGuide.breaking_change_id == breaking_change_id
            )
        )
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: dict) -> MigrationGuide:
        db_obj = MigrationGuide(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class CRUDBreakingChangeReport:
    """CRUD operations for breaking change reports"""

    async def get_latest(self, db: AsyncSession) -> Optional[BreakingChangeReport]:
        result = await db.execute(
            select(BreakingChangeReport)
            .order_by(BreakingChangeReport.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: dict) -> BreakingChangeReport:
        db_obj = BreakingChangeReport(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


breaking_change = CRUDBreakingChange()
migration_guide = CRUDMigrationGuide()
breaking_change_report = CRUDBreakingChangeReport()
