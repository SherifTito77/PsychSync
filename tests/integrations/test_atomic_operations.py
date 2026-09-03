"""
Comprehensive Integration Tests for Atomic Operations

Tests race condition prevention and atomic database operations.
These tests ensure that the atomic operations utilities correctly prevent
concurrent modification issues.
"""

import asyncio
from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.atomic_operations import (
    AlreadyExistsError,
    AtomicOperationError,
    InsufficientResourcesError,
    atomic_check_and_update,
    atomic_increment,
    atomic_insert_if_not_exists,
)
from app.db.models.user import User


@pytest.mark.integration
class TestAtomicIncrement:
    """Test atomic increment operations for race condition prevention."""

    async def test_increment_basic(self, db: AsyncSession):
        """Test basic atomic increment."""
        # Create a test user with credits
        user = User(
            email=f"test_{uuid4()}@example.com",
            hashed_password="hash",
            credits=100,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Atomic increment
        new_credits = await atomic_increment(db, User, user.id, "credits", increment=10)

        assert new_credits == 110

    async def test_increment_below_minimum_raises_error(self, db: AsyncSession):
        """Test that decrementing below minimum raises error."""
        user = User(
            email=f"test_{uuid4()}@example.com",
            hashed_password="hash",
            credits=5,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Try to decrement by 10 (would go to -5, below minimum of 0)
        with pytest.raises(InsufficientResourcesError):
            await atomic_increment(
                db, User, user.id, "credits", increment=-10, minimum=0
            )

    async def test_concurrent_increments_are_consistent(self, db: AsyncSession):
        """
        CRITICAL TEST: Verify that concurrent increments don't race.

        This test simulates 10 concurrent requests incrementing the same counter.
        Without atomic operations, this would result in lost updates.
        With atomic operations, all increments should be applied.
        """
        user = User(
            email=f"test_concurrent_{uuid4()}@example.com",
            hashed_password="hash",
            credits=0,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Launch 10 concurrent increments of 10 each
        # Expected final value: 0 + (10 * 10) = 100
        tasks = [
            atomic_increment(db, User, user.id, "credits", increment=10)
            for _ in range(10)
        ]

        results = await asyncio.gather(*tasks)

        # Verify all increments succeeded
        assert all(r == (i + 1) * 10 for i, r in enumerate(sorted(results)))

        # Verify final database state
        await db.refresh(user)
        assert user.credits == 100

    async def test_concurrent_decrements_respect_minimum(self, db: AsyncSession):
        """Test that concurrent decrements cannot go below minimum."""
        user = User(
            email=f"test_decrement_{uuid4()}@example.com",
            hashed_password="hash",
            credits=15,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Try to decrement by 10, three times (would need 30 total, only have 15)
        # First should succeed (15 -> 5)
        # Second should fail (would go to -5)
        # Third should fail
        tasks = [
            atomic_increment(db, User, user.id, "credits", increment=-10, minimum=0)
            for _ in range(3)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes and failures
        successes = sum(1 for r in results if isinstance(r, int))
        failures = sum(1 for r in results if isinstance(r, InsufficientResourcesError))

        # At least one should succeed, at least one should fail
        assert successes >= 1
        assert failures >= 1

    async def test_increment_nonexistent_record_raises_error(self, db: AsyncSession):
        """Test that incrementing non-existent record raises error."""
        fake_id = uuid4()

        with pytest.raises(AtomicOperationError):
            await atomic_increment(db, User, fake_id, "credits")


@pytest.mark.integration
class TestAtomicCheckAndUpdate:
    """Test atomic check-and-update operations."""

    async def test_check_and_update_success(self, db: AsyncSession):
        """Test successful check-and-update."""
        user = User(
            email=f"test_status_{uuid4()}@example.com",
            hashed_password="hash",
            account_status="pending",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Update status from pending to processing
        success = await atomic_check_and_update(
            db=db,
            model=User,
            record_id=user.id,
            check_field="account_status",
            check_value="pending",
            update_fields={"account_status": "processing"},
        )

        assert success is True
        await db.refresh(user)
        assert user.account_status == "processing"

    async def test_check_and_update_fails_when_check_mismatch(self, db: AsyncSession):
        """Test that update fails when check field doesn't match."""
        user = User(
            email=f"test_status_{uuid4()}@example.com",
            hashed_password="hash",
            account_status="active",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Try to update from pending to processing (but user is already active)
        success = await atomic_check_and_update(
            db=db,
            model=User,
            record_id=user.id,
            check_field="account_status",
            check_value="pending",  # Doesn't match!
            update_fields={"account_status": "processing"},
            must_exist=False,
        )

        assert success is False
        await db.refresh(user)
        assert user.account_status == "active"  # Unchanged

    async def test_concurrent_check_and_update_only_one_succeeds(
        self, db: AsyncSession
    ):
        """
        CRITICAL TEST: Verify that only one concurrent request succeeds
        when using check-and-update for idempotent operations.

        This simulates 10 concurrent requests trying to transition a user
        from pending to active. Only one should succeed.
        """
        user = User(
            email=f"test_concurrent_status_{uuid4()}@example.com",
            hashed_password="hash",
            account_status="pending",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # 10 concurrent requests to transition pending -> active
        tasks = [
            atomic_check_and_update(
                db=db,
                model=User,
                record_id=user.id,
                check_field="account_status",
                check_value="pending",
                update_fields={"account_status": "active"},
            )
            for _ in range(10)
        ]

        results = await asyncio.gather(*tasks)

        # Exactly one should succeed
        successes = sum(1 for r in results if r is True)
        failures = sum(1 for r in results if r is False)

        assert successes == 1
        assert failures == 9

        # Verify final state
        await db.refresh(user)
        assert user.account_status == "active"


@pytest.mark.integration
class TestAtomicInsertIfNotExists:
    """Test idempotent insert operations."""

    async def test_insert_succeeds(self, db: AsyncSession):
        """Test successful insert when record doesn't exist."""
        unique_email = f"unique_{uuid4()}@example.com"

        user = await atomic_insert_if_not_exists(
            db=db,
            model=User,
            check_field="email",
            check_value=unique_email,
            fields={
                "email": unique_email,
                "hashed_password": "hash",
            },
        )

        assert user is not None
        assert user.email == unique_email

    async def test_insert_fails_when_exists(self, db: AsyncSession):
        """Test that insert fails when record already exists."""
        unique_email = f"unique_{uuid4()}@example.com"

        # First insert should succeed
        user1 = await atomic_insert_if_not_exists(
            db=db,
            model=User,
            check_field="email",
            check_value=unique_email,
            fields={
                "email": unique_email,
                "hashed_password": "hash",
            },
        )

        assert user1 is not None

        # Second insert should fail
        with pytest.raises(AlreadyExistsError):
            await atomic_insert_if_not_exists(
                db=db,
                model=User,
                check_field="email",
                check_value=unique_email,
                fields={
                    "email": unique_email,
                    "hashed_password": "hash",
                },
            )

    async def test_concurrent_inserts_only_one_succeeds(self, db: AsyncSession):
        """
        CRITICAL TEST: Verify that concurrent inserts of the same unique record
        result in only one success.
        """
        unique_email = f"concurrent_{uuid4()}@example.com"

        # 10 concurrent requests to insert the same email
        tasks = [
            atomic_insert_if_not_exists(
                db=db,
                model=User,
                check_field="email",
                check_value=unique_email,
                fields={
                    "email": unique_email,
                    "hashed_password": "hash",
                },
            )
            for _ in range(10)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Exactly one should succeed
        successes = sum(1 for r in results if not isinstance(r, Exception))
        failures = sum(1 for r in results if isinstance(r, Exception))

        assert successes == 1
        assert failures == 9


@pytest.mark.integration
class TestAtomicOperationsErrorHandling:
    """Test error handling and rollback behavior."""

    async def test_increment_rolls_back_on_error(self, db: AsyncSession):
        """Test that failed increments are properly rolled back."""
        user = User(
            email=f"test_rollback_{uuid4()}@example.com",
            hashed_password="hash",
            credits=10,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        initial_credits = user.credits

        # Try to decrement below minimum (should fail and rollback)
        with pytest.raises(InsufficientResourcesError):
            await atomic_increment(
                db, User, user.id, "credits", increment=-20, minimum=0
            )

        # Verify rollback - credits should be unchanged
        await db.refresh(user)
        assert user.credits == initial_credits

    async def test_check_and_update_rolls_back_on_error(self, db: AsyncSession):
        """Test that failed check-and-update operations are rolled back."""
        user = User(
            email=f"test_rollback_update_{uuid4()}@example.com",
            hashed_password="hash",
            account_status="pending",
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        initial_updated_at = user.updated_at

        # Try to update with mismatched check (should fail and not update)
        success = await atomic_check_and_update(
            db=db,
            model=User,
            record_id=user.id,
            check_field="account_status",
            check_value="active",  # Doesn't match (user is pending)
            update_fields={"updated_at": datetime.utcnow()},
            must_exist=False,
        )

        assert success is False

        # Verify no update occurred
        await db.refresh(user)
        # updated_at should be unchanged (or very close due to timing)
        assert user.updated_at == initial_updated_at


@pytest.mark.integration
class TestAtomicOperationsPerformance:
    """Performance tests for atomic operations."""

    async def test_increment_performance_under_load(
        self, db: AsyncSession, benchmark=False
    ):
        """
        Benchmark atomic increment performance.

        This test is skipped by default. Run with:
            pytest tests/integrations/test_atomic_operations.py::TestAtomicOperationsPerformance::test_increment_performance_under_load --benchmark
        """
        if not benchmark:
            pytest.skip("Enable with --benchmark flag")

        user = User(
            email=f"bench_{uuid4()}@example.com",
            hashed_password="hash",
            credits=0,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Measure time for 1000 atomic increments
        import time

        start = time.time()

        for _ in range(1000):
            await atomic_increment(db, User, user.id, "credits", increment=1)

        elapsed = time.time() - start

        # Should complete 1000 increments in reasonable time (< 10 seconds)
        assert elapsed < 10.0, f"Too slow: {elapsed:.2f}s for 1000 increments"

        print(f"Performance: {1000 / elapsed:.0f} increments/second")
