#!/usr/bin/env python3
"""Check if corporate psychology data exists"""
import asyncio
import sys

sys.path.insert(0, "/Users/sheriftito/Downloads/psychsync")

from sqlalchemy import desc, func, select

from app.core.database import AsyncSessionLocal
from app.db.models.corporate_psychology import CorporatePsychologyMetrics


async def check_data():
    """Check if psychology metrics exist"""
    async with AsyncSessionLocal() as db:
        # Count total records
        result = await db.execute(select(func.count(CorporatePsychologyMetrics.id)))
        total = result.scalar()
        print(f"Total psychology metrics in database: {total}")

        if total > 0:
            # Check what organizations have data
            result = await db.execute(
                select(CorporatePsychologyMetrics.organization_id).distinct()
            )
            orgs = result.scalars().all()
            print(f"\n📊 Organizations with psychology metrics:")
            for org in orgs:
                print(f"   - {org}")

            # Check for this organization
            org_id = "9342b324-5bad-4efd-8f57-69e0dabdb15a"
            result = await db.execute(
                select(CorporatePsychologyMetrics)
                .where(CorporatePsychologyMetrics.organization_id == org_id)
                .order_by(desc(CorporatePsychologyMetrics.measurement_period_end))
                .limit(1)
            )
            metrics = result.scalar_one_or_none()

            if metrics:
                print(f"\n✅ Found metrics for organization!")
                print(f"   CLI: {metrics.cognitive_load_index}")
                print(
                    f"   Organizational Health Index: {metrics.organizational_health_index}"
                )
                print(
                    f"   Measurement Period: {metrics.measurement_period_start} to {metrics.measurement_period_end}"
                )
            else:
                print(f"\n❌ No metrics found for this organization")
                print(f"   But {total} total records exist in database")
        else:
            print(f"\n❌ No corporate psychology metrics exist in database")


asyncio.run(check_data())
