# app/crud/crud_sql_audit.py
"""CRUD operations for SQL Injection Audit"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models.sql_audit import SQLQuery, SQLScanReport, SQLVulnerability


class CRUDSQLQuery:
    """CRUD operations for SQL queries"""

    async def get(self, db: AsyncSession, id: UUID) -> Optional[SQLQuery]:
        result = await db.execute(select(SQLQuery).where(SQLQuery.id == id))
        return result.scalar_one_or_none()

    async def get_by_hash(
        self, db: AsyncSession, *, query_hash: str
    ) -> Optional[SQLQuery]:
        result = await db.execute(
            select(SQLQuery).where(SQLQuery.query_hash == query_hash)
        )
        return result.scalar_one_or_none()

    async def get_unfixed(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[SQLQuery]:
        result = await db.execute(
            select(SQLQuery)
            .where(SQLQuery.is_fixed == 0.0)
            .order_by(SQLQuery.risk_score.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[SQLQuery]:
        result = await db.execute(select(SQLQuery).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_recent(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[SQLQuery]:
        return await self.get_multi(db, skip=skip, limit=limit)

    async def create(self, db: AsyncSession, *, obj_in: dict) -> SQLQuery:
        db_obj = SQLQuery(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: SQLQuery, obj_in: dict
    ) -> SQLQuery:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class CRUDSQLVulnerability:
    """CRUD operations for SQL vulnerabilities"""

    async def get(self, db: AsyncSession, id: UUID) -> Optional[SQLVulnerability]:
        result = await db.execute(
            select(SQLVulnerability).where(SQLVulnerability.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[SQLVulnerability]:
        result = await db.execute(select(SQLVulnerability).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: dict) -> SQLVulnerability:
        db_obj = SQLVulnerability(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class CRUDSQLScanReport:
    """CRUD operations for SQL scan reports"""

    async def get_latest(self, db: AsyncSession) -> Optional[SQLScanReport]:
        result = await db.execute(
            select(SQLScanReport).order_by(SQLScanReport.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: dict) -> SQLScanReport:
        db_obj = SQLScanReport(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


sql_query = CRUDSQLQuery()
sql_vulnerability = CRUDSQLVulnerability()
sql_scan_report = CRUDSQLScanReport()
