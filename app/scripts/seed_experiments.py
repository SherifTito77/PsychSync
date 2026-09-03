# app/scripts/seed_experiments.py
"""Seed initial A/B testing experiments

Run this script to create initial experiments for testing:
python -m app.scripts.seed_experiments
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta

from app.core.database import AsyncSessionLocal
from app.db.models.ab_testing import ABExperiment, ABVariant
from app.db.models.feature_requests import FeatureRequest
from app.db.models.user import User


async def seed_experiments():
    """Perform operation.

    Args:
        **kwargs: Input parameters

    Returns:
        Operation result
    """
    """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
    """
    """Seed initial A/B testing experiments"""
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding A/B testing experiments...")

        # Experiment 1: CTA Button Color Test
        experiment1 = ABExperiment(
            name="cta_button_color_v1",
            description="Test green vs blue vs purple CTA buttons for signup",
            status="running",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            config={
                "hypothesis": "Green CTA button will increase click-through rate by 5%",
                "variants": ["control", "variant_a", "variant_b"],
                "traffic_split": {"control": 0.5, "variant_a": 0.25, "variant_b": 0.25},
            },
        )
        db.add(experiment1)
        await db.flush()

        # Variants for experiment 1
        variant1_control = ABVariant(
            experiment_id=experiment1.id,
            name="control",
            traffic_split=0.5,
            is_control=True,
        )
        variant1_a = ABVariant(
            experiment_id=experiment1.id,
            name="variant_a",
            traffic_split=0.25,
            is_control=False,
        )
        variant1_b = ABVariant(
            experiment_id=experiment1.id,
            name="variant_b",
            traffic_split=0.25,
            is_control=False,
        )
        db.add_all([variant1_control, variant1_a, variant1_b])

        # Experiment 2: Signup Flow Simplification
        experiment2 = ABExperiment(
            name="signup_streamline_v1",
            description="Test reducing signup fields from 5 to 2 vs social auth",
            status="running",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=60),
            config={
                "hypothesis": "Reducing fields will increase email verification rate by 12%",
                "target_metrics": ["email_verification_rate", "time_to_verify"],
                "sample_size": 24000,
            },
        )
        db.add(experiment2)
        await db.flush()

        # Variants for experiment 2
        variant2_control = ABVariant(
            experiment_id=experiment2.id,
            name="control",
            traffic_split=0.5,
            is_control=True,
        )
        variant2_a = ABVariant(
            experiment_id=experiment2.id,
            name="variant_a",
            traffic_split=0.25,
            is_control=False,
        )
        variant2_b = ABVariant(
            experiment_id=experiment2.id,
            name="variant_b",
            traffic_split=0.25,
            is_control=False,
        )
        db.add_all([variant2_control, variant2_a, variant2_b])

        # Commit
        await db.commit()

        print("✅ Successfully seeded 2 experiments:")
        print(f"   1. cta_button_color_v1 (running)")
        print(f"   2. signup_streamline_v1 (running)")
        print()


async def seed_feature_requests():
    """Perform operation.

    Args:
        **kwargs: Input parameters

    Returns:
        Operation result
    """
    """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
    """
    """Seed sample feature requests for testing"""
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding feature requests...")

        # Get or create a user for submitted_by
        result = await db.execute(User.__table__.select().limit(1))
        test_user = result.first()

        # Feature Request 1: Dark Mode
        fr1 = FeatureRequest(
            title="Dark Mode Support",
            description="Add a dark mode theme option for the application to reduce eye strain and improve accessibility in low-light environments.",
            status="backlog",
            theme="UX",
            subcategory="UI",
            request_type="ENH",
            priority="P2",
            effort="M",
            value="V2",
            source_type="internal",
            submitted_by=test_user[0] if test_user else None,
        )
        # Calculate RICE score
        fr1.reach_score = 3.0  # >1000 users would use
        fr1.impact_score = 1.0  # Medium impact
        fr1.confidence_score = 0.8
        fr1.effort_score = 3.0  # 1-2 weeks
        fr1.rice_score = (3.0 * 1.0 * 0.8) / 3.0  # 0.8
        db.add(fr1)

        # Feature Request 2: Mobile Apps
        fr2 = FeatureRequest(
            title="Native Mobile Apps (iOS & Android)",
            description="Build native mobile applications for iOS and Android to enable offline assessment taking and push notifications.",
            status="backlog",
            theme="UX",
            subcategory="MOB",
            request_type="NEW",
            priority="P2",
            effort="XL",
            value="V2",
            source_type="customer",
            submitted_by=test_user[0] if test_user else None,
            opportunity_id="DEAL-001",
        )
        fr2.reach_score = 2.0  # 500-1000 users
        fr2.impact_score = 2.0  # High impact
        fr2.confidence_score = 0.8
        fr2.effort_score = 12.0  # 2-3 months
        fr2.rice_score = (2.0 * 2.0 * 0.8) / 12.0  # 0.27
        db.add(fr2)

        # Feature Request 3: API Access
        fr3 = FeatureRequest(
            title="Public API for Assessment Data",
            description="Provide a REST API to allow programmatic access to assessment results and analytics for enterprise customers.",
            status="planned",
            theme="INTEG",
            subcategory="API",
            request_type="NEW",
            priority="P1",
            effort="L",
            value="V1",
            source_type="customer",
            submitted_by=test_user[0] if test_user else None,
            target_release="Q2 2025",
        )
        fr3.reach_score = 1.0  # <500 users initially
        fr3.impact_score = 3.0  # Massive impact for enterprise
        fr3.confidence_score = 0.9
        fr3.effort_score = 6.0  # 3-6 weeks
        fr3.rice_score = (1.0 * 3.0 * 0.9) / 6.0  # 0.45
        db.add(fr3)

        await db.commit()

        print("✅ Successfully seeded 3 feature requests:")
        print(f"   1. Dark Mode Support (RICE: {fr1.rice_score:.2f})")
        print(f"   2. Native Mobile Apps (RICE: {fr2.rice_score:.2f})")
        print(f"   3. Public API Access (RICE: {fr3.rice_score:.2f})")
        print()


async def main():
    """Perform operation.

    Args:
        **kwargs: Input parameters

    Returns:
        Operation result
    """
    """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
    """
    await seed_experiments()
    await seed_feature_requests()
    print("✨ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
