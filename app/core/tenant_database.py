"""
Tenant Database Router

Routes database queries to appropriate database instances based on tenant tier.
Supports hybrid multi-tenancy: shared database for SMB, dedicated databases for enterprise.

Created: 2025-01-12
Author: Architecture Team
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import Optional, Dict
from enum import Enum
import logging
from contextlib import asynccontextmanager

from app.core.config import settings

logger = logging.getLogger(__name__)


class TenantTier(str, Enum):
    """Tenant subscription tiers"""
    SMB = "smb"              # Shared database
    ENTERPRISE = "enterprise"  # Dedicated database
    TRIAL = "trial"           # Shared database


class TenantDatabaseRouter:
    """
    Routes database connections based on tenant tier.

    Architecture:
    - SMB/Trial tenants → Shared database (cost-efficient)
    - Enterprise tenants → Dedicated database (performance + compliance)

    Usage:
        router = TenantDatabaseRouter()

        # In request handler
        async with router.get_session(tenant_id) as db:
            result = await db.execute(query)

    Database Connection Pooling:
    - Shared DB: 50 connections max (serves all SMB tenants)
    - Each Enterprise DB: 20 connections max (dedicated pool)
    """

    def __init__(
        self,
        shared_db_url: Optional[str] = None,
        pool_size: int = 20,
        max_overflow: int = 30,
    ):
        """
        Initialize tenant database router.

        Args:
            shared_db_url: Connection URL for shared database
            pool_size: Base connection pool size per database
            max_overflow: Max overflow connections per database
        """
        self.shared_db_url = shared_db_url or settings.DATABASE_URL
        self.pool_size = pool_size
        self.max_overflow = max_overflow

        # Database engines cache (tenant_id → engine)
        self._engines: Dict[str, AsyncEngine] = {}
        self._session_makers: Dict[str, async_sessionmaker] = {}

        # Shared database engine (for SMB/trial tenants)
        self._shared_engine: Optional[AsyncEngine] = None
        self._shared_session_maker: Optional[async_sessionmaker] = None

        logger.info("TenantDatabaseRouter initialized")

    async def initialize(self):
        """Initialize shared database connection pool."""
        try:
            # Create shared database engine
            self._shared_engine = create_async_engine(
                self.shared_db_url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,   # Recycle connections after 1 hour
                echo=settings.SQL_DEBUG,
            )

            # Create session maker
            self._shared_session_maker = async_sessionmaker(
                self._shared_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            logger.info(f"✅ Shared database engine initialized: {self.shared_db_url}")

        except Exception as e:
            logger.error(f"Failed to initialize shared database engine: {e}")
            raise

    async def get_or_create_enterprise_engine(
        self,
        tenant_id: str,
        database_url: str,
    ):
        """
        Get or create database engine for enterprise tenant.

        Args:
            tenant_id: Tenant UUID
            database_url: Database connection URL

        Returns:
            AsyncEngine for tenant's dedicated database
        """
        # Return cached engine if exists
        if tenant_id in self._engines:
            return self._engines[tenant_id]

        try:
            # Create new engine for this tenant
            engine = create_async_engine(
                database_url,
                pool_size=10,  # Enterprise gets dedicated pool
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=settings.SQL_DEBUG,
            )

            # Create session maker
            session_maker = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            # Cache engine and session maker
            self._engines[tenant_id] = engine
            self._session_makers[tenant_id] = session_maker

            logger.info(f"✅ Created enterprise database engine for tenant {tenant_id}")

            return engine

        except Exception as e:
            logger.error(f"Failed to create enterprise engine for {tenant_id}: {e}")
            raise

    async def get_session(self, tenant_id: str, tenant_tier: TenantTier):
        """
        Get database session for tenant based on tier.

        Args:
            tenant_id: Tenant UUID
            tenant_tier: Tenant tier (smb, enterprise, trial)

        Returns:
            AsyncSession for appropriate database

        Example:
            session = await router.get_session(tenant_id, TenantTier.SMB)
            result = await session.execute(query)
            await session.close()
        """
        if tenant_tier in [TenantTier.SMB, TenantTier.TRIAL]:
            # Use shared database
            if not self._shared_session_maker:
                await self.initialize()

            return self._shared_session_maker()

        elif tenant_tier == TenantTier.ENTERPRISE:
            # Use dedicated database
            if tenant_id not in self._session_makers:
                # Get enterprise database URL from tenant record
                # In real implementation, this would query the database
                database_url = await self._get_enterprise_db_url(tenant_id)

                # Create engine
                await self.get_or_create_enterprise_engine(tenant_id, database_url)

            return self._session_makers[tenant_id]()

        else:
            raise ValueError(f"Unknown tenant tier: {tenant_tier}")

    @asynccontextmanager
    async def get_session_context(self, tenant_id: str, tenant_tier: TenantTier):
        """
        Context manager for database session.

        Args:
            tenant_id: Tenant UUID
            tenant_tier: Tenant tier

        Yields:
            AsyncSession for tenant's database

        Example:
            async with router.get_session_context(tenant_id, TenantTier.SMB) as db:
                result = await db.execute(query)
            # Session automatically closed
        """
        session = await self.get_session(tenant_id, tenant_tier)

        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

    async def _get_enterprise_db_url(self, tenant_id: str) -> str:
        """
        Get database URL for enterprise tenant.

        In production, this would:
        1. Query tenant database configuration
        2. Retrieve connection details from secure storage
        3. Return formatted database URL

        For now, returns placeholder.
        """
        # TODO: Implement tenant database configuration lookup
        # In real implementation:
        # tenant_config = await db.get(TenantDatabaseConfig, tenant_id)
        # return tenant_config.database_url

        # Placeholder - enterprise database naming convention
        # e.g., postgresql://user:pass@localhost:5432/psychsync_tenant_{tenant_id}
        database_name = f"psychsync_tenant_{tenant_id.replace('-', '_')}"
        return f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{database_name}"

    async def close_tenant_connection(self, tenant_id: str):
        """
        Close database connection for specific tenant.

        Used when tenant is deleted or database is migrated.

        Args:
            tenant_id: Tenant UUID
        """
        if tenant_id in self._engines:
            engine = self._engines[tenant_id]

            try:
                await engine.dispose()
                del self._engines[tenant_id]
                del self._session_makers[tenant_id]

                logger.info(f"Closed database connection for tenant {tenant_id}")

            except Exception as e:
                logger.error(f"Failed to close connection for {tenant_id}: {e}")

    async def close_all_connections(self):
        """Close all database connections (for graceful shutdown)."""
        try:
            # Close shared database engine
            if self._shared_engine:
                await self._shared_engine.dispose()
                logger.info("Closed shared database engine")

            # Close all enterprise tenant engines
            for tenant_id, engine in self._engines.items():
                await engine.dispose()
                logger.info(f"Closed enterprise database engine for {tenant_id}")

            self._engines.clear()
            self._session_makers.clear()

            logger.info("✅ All database connections closed")

        except Exception as e:
            logger.error(f"Error closing database connections: {e}")

    def get_connection_stats(self) -> Dict:
        """
        Get connection pool statistics.

        Returns:
            Dict with connection stats for each database
        """
        stats = {
            "shared_database": {
                "status": "active" if self._shared_engine else "inactive",
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow,
            },
            "enterprise_tenants": len(self._engines),
            "total_engines": len(self._engines) + (1 if self._shared_engine else 0),
        }

        # Add per-tenant stats
        for tenant_id, engine in self._engines.items():
            pool = engine.pool
            stats[f"tenant_{tenant_id}"] = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            }

        return stats


# Global router instance
_tenant_router: Optional[TenantDatabaseRouter] = None


def get_tenant_router() -> TenantDatabaseRouter:
    """
    Get global tenant database router instance.

    Returns:
        TenantDatabaseRouter singleton

    Usage:
        router = get_tenant_router()
        async with router.get_session_context(tenant_id, tenant_tier) as db:
            result = await db.execute(query)
    """
    global _tenant_router

    if _tenant_router is None:
        _tenant_router = TenantDatabaseRouter()

    return _tenant_router


async def init_tenant_router():
    """Initialize tenant database router on application startup."""
    router = get_tenant_router()
    await router.initialize()
    logger.info("✅ Tenant database router initialized")


async def close_tenant_router():
    """Close tenant database router on application shutdown."""
    global _tenant_router

    if _tenant_router:
        await _tenant_router.close_all_connections()
        _tenant_router = None
        logger.info("✅ Tenant database router closed")


# Dependency for FastAPI
async def get_tenant_db(
    tenant_id: str,
    tenant_tier: TenantTier,
):
    """
    FastAPI dependency for tenant-scoped database session.

    Usage in endpoint:
        @router.get("/api/v1/assessments")
        async def list_assessments(
            tenant_id: str = Depends(get_current_tenant_id),
            tenant_tier: str = Depends(get_current_tenant_tier),
            db: AsyncSession = Depends(get_tenant_db)
        ):
            # Database session is automatically scoped to tenant's database
            result = await db.execute(query)
            return result.scalars().all()
    """
    router = get_tenant_router()

    async with router.get_session_context(tenant_id, tenant_tier) as session:
        yield session
