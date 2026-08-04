"""
Diagnostic Script for GAD-7 Assessment and Analytics Dashboard Issue

This script helps diagnose why recent GAD-7 assessments are not appearing
in the Clinical Analytics Dashboard.
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.screening import SKIP_CONSENT_CHECK
from app.core.config.settings import get_settings
from app.db.models.clinical_screening import ClinicalScreening
from app.db.models.user import User


async def diagnose():
    """Run diagnostic checks for GAD-7 assessment issue"""

    print("=" * 60)
    print("GAD-7 ASSESSMENT DIAGNOSTIC")
    print("=" * 60)
    print()

    # Check 1: Environment configuration
    print("1. ENVIRONMENT CONFIGURATION")
    print("-" * 60)
    print(f"SKIP_CONSENT_CHECK: {SKIP_CONSENT_CHECK}")

    try:
        settings = get_settings()
        print(
            f"Database URL: {settings.get_database_url()[:50]}..."
            if len(settings.get_database_url()) > 50
            else f"Database URL: {settings.get_database_url()}"
        )
    except Exception as e:
        print(f"  ✗ Failed to get database URL: {e}")
        return

    print()

    # Check 2: Create database connection
    print("2. DATABASE CONNECTION")
    print("-" * 60)
    try:
        settings = get_settings()
        engine = create_async_engine(settings.get_database_url(), echo=False)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        print("✓ Database connection successful")
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        return

    async with async_session() as db:
        try:
            # Check 3: Recent GAD-7 assessments
            print("\n3. RECENT GAD-7 ASSESSMENTS")
            print("-" * 60)

            now_utc = datetime.now(timezone.utc)
            thirty_days_ago = now_utc - timedelta(days=30)

            gad7_query = (
                select(ClinicalScreening)
                .where(
                    and_(
                        ClinicalScreening.screening_type == "GAD7",
                        ClinicalScreening.completed_at >= thirty_days_ago,
                    )
                )
                .order_by(ClinicalScreening.completed_at.desc())
            )

            result = await db.execute(gad7_query)
            screenings = result.scalars().all()

            print(f"Total GAD-7 assessments in last 30 days: {len(screenings)}")
            print()

            if screenings:
                for idx, screening in enumerate(screenings[:5], 1):
                    print(f"  {idx}. ID: {screening.id}")
                    print(f"     User ID: {screening.user_id}")
                    print(f"     Org ID: {screening.org_id}")
                    print(f"     Total Score: {screening.total_score}")
                    print(f"     Severity: {screening.severity_level}")
                    print(f"     Risk Level: {screening.risk_level}")
                    print(f"     Completed At: {screening.completed_at}")
                    print(
                        f"     Completed At (UTC): {screening.completed_at.astimezone(timezone.utc) if screening.completed_at.tzinfo else screening.completed_at}"
                    )
                    print(f"     Timezone Info: {screening.completed_at.tzinfo}")
                    print()
            else:
                print("  ✗ No GAD-7 assessments found in last 30 days")

            # Check 4: Analytics query simulation with timezone-aware datetimes
            print("\n4. ANALYTICS QUERY SIMULATION")
            print("-" * 60)

            start_date = now_utc - timedelta(days=30)
            end_date = now_utc

            analytics_query = (
                select(func.count())
                .select_from(ClinicalScreening)
                .where(
                    and_(
                        ClinicalScreening.completed_at >= start_date,
                        ClinicalScreening.completed_at <= end_date,
                        ClinicalScreening.completed_at.isnot(None),
                    )
                )
            )

            count_result = await db.execute(analytics_query)
            total_count = count_result.scalar() or 0

            print(f"Total assessments (analytics query): {total_count}")
            print(f"Query start_date: {start_date}")
            print(f"Query end_date: {end_date}")
            print(f"Query start_date (timezone): {start_date.tzinfo}")
            print(f"Query end_date (timezone): {end_date.tzinfo}")

            # Check 5: Timezone scenario test
            print("\n5. TIMEZONE SCENARIO TEST")
            print("-" * 60)

            naive_start = datetime.utcnow() - timedelta(days=30)
            naive_end = datetime.utcnow()

            naive_query = (
                select(func.count())
                .select_from(ClinicalScreening)
                .where(
                    and_(
                        ClinicalScreening.completed_at >= naive_start,
                        ClinicalScreening.completed_at <= naive_end,
                    )
                )
            )

            naive_count_result = await db.execute(naive_query)
            naive_count = naive_count_result.scalar() or 0

            print(f"Count with naive datetime: {naive_count}")
            print(f"Count with timezone-aware datetime: {total_count}")
            print(f"Difference: {total_count - naive_count}")

            if naive_count != total_count:
                print("\n  ⚠️  TIMEZONE ISSUE DETECTED!")
                print(
                    "  The difference in counts indicates timezone-related filtering issues."
                )
                print("  This is why assessments may not appear in the dashboard.")
            else:
                print("\n  ✓ Timezone handling is correct - counts match")

        except Exception as e:
            print(f"\n✗ Diagnostic error: {e}")
            import traceback

            traceback.print_exc()

    print()
    print("=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(diagnose())
