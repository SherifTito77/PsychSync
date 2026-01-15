# app/crud/crud_caching_config.py
"""CRUD operations for Caching Configuration"""
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.caching_config import CacheEntry, CachePerformance, CacheOptimization, CacheConfigurationReport

class CRUDCacheEntry:
    """CRUD operations for cache entries"""
    async def get(self, db: AsyncSession, id: UUID) -> Optional[CacheEntry]:
        result = await db.execute(select(CacheEntry).where(CacheEntry.id == id))
        return result.scalar_one_or_none()
    async def get_by_key(self, db: AsyncSession, *, cache_key: str) -> Optional[CacheEntry]:
        result = await db.execute(select(CacheEntry).where(CacheEntry.cache_key == cache_key))
        return result.scalar_one_or_none()
    async def get_low_hit_rate(self, db: AsyncSession, *, threshold: float = 0.5, skip: int = 0, limit: int = 100) -> list[CacheEntry]:
        result = await db.execute(
            select(CacheEntry).where(CacheEntry.hit_rate < threshold)
            .order_by(CacheEntry.hit_rate.asc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> list[CacheEntry]:
        result = await db.execute(select(CacheEntry).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_recent(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> list[CacheEntry]:
        """Get recent cache entries (alias for get_multi)"""
        return await self.get_multi(db, skip=skip, limit=limit)

    async def create(self, db: AsyncSession, *, obj_in: dict) -> CacheEntry:
        db_obj = CacheEntry(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

class CRUDCachePerformance:
    """CRUD operations for cache performance"""
    async def get(self, db: AsyncSession, id: UUID) -> Optional[CachePerformance]:
        result = await db.execute(select(CachePerformance).where(CachePerformance.id == id))
        return result.scalar_one_or_none()
    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> list[CachePerformance]:
        result = await db.execute(select(CachePerformance).offset(skip).limit(limit))
        return list(result.scalars().all())
    async def create(self, db: AsyncSession, *, obj_in: dict) -> CachePerformance:
        db_obj = CachePerformance(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

class CRUDCacheOptimization:
    """CRUD operations for cache optimizations"""
    async def get(self, db: AsyncSession, id: UUID) -> Optional[CacheOptimization]:
        result = await db.execute(select(CacheOptimization).where(CacheOptimization.id == id))
        return result.scalar_one_or_none()
    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> list[CacheOptimization]:
        result = await db.execute(select(CacheOptimization).offset(skip).limit(limit))
        return list(result.scalars().all())
    async def create(self, db: AsyncSession, *, obj_in: dict) -> CacheOptimization:
        db_obj = CacheOptimization(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

class CRUDCacheConfigurationReport:
    """CRUD operations for cache configuration reports"""
    def calculate_configuration_grade(self, overall_hit_rate, avg_response_time_ms, optimization_opportunities) -> str:
        score = 100
        score -= int((1 - overall_hit_rate) * 70)
        if avg_response_time_ms > 100:
            score -= 10
        if optimization_opportunities > 10:
            score -= 20
        score = max(0, min(100, score))
        if score >= 90: return "A"
        elif score >= 80: return "B"
        elif score >= 70: return "C"
        elif score >= 60: return "D"
        else: return "F"
    async def get_latest(self, db: AsyncSession) -> Optional[CacheConfigurationReport]:
        result = await db.execute(
            select(CacheConfigurationReport).order_by(CacheConfigurationReport.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()
    async def create(self, db: AsyncSession, *, obj_in: dict) -> CacheConfigurationReport:
        db_obj = CacheConfigurationReport(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

cache_entry = CRUDCacheEntry()
cache_performance = CRUDCachePerformance()
cache_optimization = CRUDCacheOptimization()
cache_configuration_report = CRUDCacheConfigurationReport()
