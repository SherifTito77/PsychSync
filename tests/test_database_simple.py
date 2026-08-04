"""Simple database integration test without API router dependencies"""

import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_async_db
from app.db.models.user import User, UserRole


@pytest.fixture
async def test_db() -> AsyncSession:
    """Create test database session"""
    # Create async test engine
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.core.config import get_database_url

    test_engine = create_async_engine(
        get_database_url(async_driver=True, test_mode=True),
        echo=False,
        pool_size=1,
        max_overflow=0,
    )

    # Drop all tables first to ensure clean state
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    # Clean up - drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncClient:
    """Create test client"""
    from app.core.database import get_async_db
    from app.main import app

    app.dependency_overrides[get_async_db] = lambda: test_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestDatabaseSimple:
    """Simple database tests without API router"""

    async def test_create_user(self, test_db: AsyncSession):
        """Test basic user creation"""
        from app.db.models.user import User, UserRole

        user = User(
            email="test@example.com",
            password_hash="test_hash_123",
            full_name="Test User",
            role=UserRole.USER.value,
            is_active=True,
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        assert user.id is not None, "User should have ID"
        assert user.email == "test@example.com"
        print(f"✅ Created user: {user.email}")

    async def test_organization(self, test_db: AsyncSession):
        """Test organization creation"""
        from app.db.models.organization import Organization

        org = Organization(name="Test Organization")
        test_db.add(org)
        await test_db.commit()
        await test_db.refresh(org)

        assert org.id is not None, "Organization should have ID"
        assert org.name == "Test Organization"
        print(f"✅ Created organization: {org.name}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
