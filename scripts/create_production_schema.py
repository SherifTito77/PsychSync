#!/usr/bin/env python3
"""
Create production database schema from SQLAlchemy models.
This script imports all models and creates the complete schema.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import Base

# MUST import models before anything else so they register with Base.metadata
from app.db.models import (
    Analytics,
    AnalyticsEvent,
    Assessment,
    AssessmentResponse,
    ComparativeEffectiveness,
    Framework,
    GrowthMilestone,
    GrowthPotentialAnalysis,
    GrowthTrajectory,
    Intervention,
    InterventionEffectiveness,
    InterventionOutcomes,
    InterventionParticipant,
    Organization,
    PostInterventionMeasurement,
    PreInterventionMeasurement,
    Question,
    Response,
    SafetyFollowUpAction,
    SafetyIncident,
    SafetyResource,
    SafetyTraining,
    SafetyTrainingCompletion,
    Team,
    TeamMember,
    TrajectoryBenchmark,
    TrajectoryPrediction,
    TrajectorySimulation,
    User,
    WellnessAlert,
    WellnessAssessment,
)


async def create_schema():
    """Create all tables from SQLAlchemy models."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    print("=" * 70)
    print("CREATING PRODUCTION DATABASE SCHEMA")
    print("=" * 70)
    print(f"Database: {settings.DATABASE_URL.split('@')[-1]}")
    print()

    # Get table count before
    async with engine.begin() as conn:
        from sqlalchemy import text

        result = await conn.execute(
            text("SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';")
        )
        before_count = result.scalar()
        print(f"Tables before: {before_count}")

    print()
    print("Creating all tables from model definitions...")
    print("-" * 70)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("-" * 70)
    print("✅ Schema creation complete!")
    print()

    # List created tables
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename NOT IN ('alembic_version', 'spatial_ref_sys') ORDER BY tablename;"
            )
        )
        tables = [row[0] for row in result.fetchall()]
        print(f"Total tables created: {len(tables)}")
        print()
        print("Tables:")
        for i, table in enumerate(tables, 1):
            print(f"  {i:2d}. {table}")

    print()
    print("=" * 70)
    print("✅ PRODUCTION SCHEMA CREATION COMPLETE")
    print("=" * 70)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_schema())
