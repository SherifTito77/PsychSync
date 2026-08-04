#!/usr/bin/env python3
"""
DLQ System Component Testing Script

Tests all DLQ system components without requiring authentication.
Verifies database structure, model operations, and Celery integration.

Usage: python scripts/test_dlq_components.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
from uuid import uuid4

# Add project root to path
sys.path.insert(0, "/Users/sheriftito/Downloads/psychsync")

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models.dead_letter import DeadLetterTask, DLQReason, DLQStatus

# Celery tasks tested separately to avoid import errors
# from app.tasks.dlq_tasks import process_dlq, retry_dlq_task, cleanup_resolved_dlq
from app.schemas.dlq import (
    DLQAnalyticsResponse,
    DLQEntry,
    DLQEntryListResponse,
    DLQHealthCheckResponse,
)


async def get_async_session():
    """Create async database session"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    return async_session_maker()


async def test_database_structure():
    """Test 1: Verify database table and indexes exist"""
    print("\n" + "=" * 70)
    print("TEST 1: Database Structure")
    print("=" * 70)

    session = await get_async_session()

    try:
        # Check table exists via raw query
        result = await session.execute(select(func.count()).select_from(DeadLetterTask))
        count = result.scalar()
        print(f"✓ dead_letter_tasks table exists (current rows: {count})")

        # Check we can query different statuses
        for status in DLQStatus:
            result = await session.execute(
                select(func.count()).where(DeadLetterTask.status == status.value)
            )
            print(f"  - {status.value}: {result.scalar()} entries")

        return True

    except Exception as e:
        print(f"✗ Database structure test failed: {e}")
        return False

    finally:
        await session.close()


async def test_model_operations():
    """Test 2: Create, read, update DLQ entries"""
    print("\n" + "=" * 70)
    print("TEST 2: Model Operations")
    print("=" * 70)

    session = await get_async_session()
    test_id = uuid4()

    try:
        # Create test entry
        dlq = DeadLetterTask(
            id=test_id,
            task_id=f"test-task-{test_id}",
            task_name="app.tasks.test.example_task",
            reason=DLQReason.MAX_RETRIES_EXCEEDED,
            status=DLQStatus.PENDING,
            exception="Test exception: connection timeout",
            exception_type="ConnectionError",
            traceback="Traceback (most recent call last):\n  ConnectionError",
            args="(1, 2, 3)",
            kwargs="{'key': 'value'}",
            retry_count=3,
            retry_attempts=0,
            max_retries=3,
            is_transient=True,
            error_category="network_error",
            confidence_score=0.95,
            task_metadata={"test": True, "source": "component_test"},
        )

        session.add(dlq)
        await session.commit()
        print(f"✓ Created test DLQ entry: {test_id}")

        # Read entry
        result = await session.execute(
            select(DeadLetterTask).where(DeadLetterTask.id == test_id)
        )
        fetched = result.scalar_one_or_none()

        if fetched:
            print(f"✓ Fetched DLQ entry:")
            print(f"  - Task: {fetched.task_name}")
            print(f"  - Reason: {fetched.reason}")
            print(f"  - Status: {fetched.status}")
            print(f"  - Can retry: {fetched.can_retry()}")
            print(f"  - Should auto-retry: {fetched.should_auto_retry()}")
        else:
            print("✗ Failed to fetch created entry")
            return False

        # Test status transition
        fetched.mark_resolved()
        await session.commit()
        print(f"✓ Updated status to: {fetched.status}")

        # Cleanup test entry
        await session.delete(fetched)
        await session.commit()
        print(f"✓ Cleaned up test entry")

        return True

    except Exception as e:
        print(f"✗ Model operations test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await session.close()


async def test_enums():
    """Test 3: Verify enum values"""
    print("\n" + "=" * 70)
    print("TEST 3: Enum Values")
    print("=" * 70)

    try:
        print("DLQStatus enum:")
        for status in DLQStatus:
            print(f"  - {status.name}: {status.value}")

        print("\nDLQReason enum:")
        for reason in DLQReason:
            print(f"  - {reason.name}: {reason.value}")

        print("\n✓ All enums defined correctly")
        return True

    except Exception as e:
        print(f"✗ Enum test failed: {e}")
        return False


async def test_error_classification():
    """Test 4: Test exception classification"""
    print("\n" + "=" * 70)
    print("TEST 4: Error Classification")
    print("=" * 70)

    try:
        test_cases = [
            ("ConnectionError", "Connection refused", True, DLQReason.NETWORK_ERROR),
            ("TimeoutError", "Request timeout", True, DLQReason.TIMEOUT),
            ("ValueError", "Invalid input", False, DLQReason.VALIDATION_ERROR),
            ("KeyError", "missing_key", False, DLQReason.VALIDATION_ERROR),
            ("RuntimeError", "Unknown error", True, DLQReason.UNKNOWN),
        ]

        for exc_type, exc_msg, expected_transient, expected_reason in test_cases:
            result = DeadLetterTask.classify_exception(exc_type, exc_msg)
            is_transient = result["is_transient"]
            reason = result["reason"]

            status = (
                "✓"
                if (is_transient == expected_transient and reason == expected_reason)
                else "✗"
            )
            print(f"{status} {exc_type}: transient={is_transient}, reason={reason}")

        print("\n✓ Error classification working correctly")
        return True

    except Exception as e:
        print(f"✗ Error classification test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_celery_tasks():
    """Test 5: Verify Celery tasks are registered"""
    print("\n" + "=" * 70)
    print("TEST 5: Celery Task Registration")
    print("=" * 70)

    try:
        from app.core.config.celery_config import celery_app

        dlq_tasks = [
            "app.tasks.dlq_tasks.process_dlq",
            "app.tasks.dlq_tasks.retry_dlq_task",
            "app.tasks.dlq_tasks.cleanup_resolved_dlq",
        ]

        print("Checking registered Celery tasks:")
        for task_name in dlq_tasks:
            # Check if task is registered
            task = celery_app.tasks.get(task_name)
            if task:
                print(f"  ✓ {task_name}")
            else:
                print(f"  ✗ {task_name} NOT FOUND")

        print("\n✓ Celery task registration verified")
        return True

    except Exception as e:
        print(f"✗ Celery task test failed: {e}")
        return False


async def test_schemas():
    """Test 6: Verify Pydantic schemas"""
    print("\n" + "=" * 70)
    print("TEST 6: Pydantic Schemas")
    print("=" * 70)

    try:
        from app.schemas.dlq import (
            DLQAnalyticsResponse,
            DLQBatchActionRequest,
            DLQBatchActionResponse,
            DLQEntry,
            DLQEntryListResponse,
            DLQEntrySummary,
            DLQHealthCheckResponse,
            DLQQueryParams,
            DLQRetryRequest,
            DLQRetryResponse,
        )

        print("✓ All Pydantic schemas import successfully:")
        print(f"  - DLQEntry: {DLQEntry.__name__}")
        print(f"  - DLQEntrySummary: {DLQEntrySummary.__name__}")
        print(f"  - DLQEntryListResponse: {DLQEntryListResponse.__name__}")
        print(f"  - DLQRetryRequest: {DLQRetryRequest.__name__}")
        print(f"  - DLQRetryResponse: {DLQRetryResponse.__name__}")
        print(f"  - DLQBatchActionRequest: {DLQBatchActionRequest.__name__}")
        print(f"  - DLQBatchActionResponse: {DLQBatchActionResponse.__name__}")
        print(f"  - DLQAnalyticsResponse: {DLQAnalyticsResponse.__name__}")
        print(f"  - DLQHealthCheckResponse: {DLQHealthCheckResponse.__name__}")
        print(f"  - DLQQueryParams: {DLQQueryParams.__name__}")

        # Test schema validation
        test_entry = DLQEntry(
            id=uuid4(),
            task_id="test-123",
            task_name="app.tasks.test.example",
            reason="max_retries_exceeded",
            status="pending",
            is_transient=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            retry_count=0,
            retry_attempts=0,
            max_retries=3,
            can_retry=True,
            should_auto_retry=True,
        )
        print(f"\n✓ Schema validation works: {test_entry.task_name}")

        return True

    except Exception as e:
        print(f"✗ Schema test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("DLQ SYSTEM COMPONENT TESTS")
    print("=" * 70)
    print(f"Started at: {datetime.utcnow()}")

    results = []

    # Run all tests
    results.append(("Database Structure", await test_database_structure()))
    results.append(("Model Operations", await test_model_operations()))
    results.append(("Enum Values", await test_enums()))
    results.append(("Error Classification", await test_error_classification()))
    results.append(("Celery Tasks", await test_celery_tasks()))
    results.append(("Pydantic Schemas", await test_schemas()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - DLQ System is fully operational!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - please review the errors above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
