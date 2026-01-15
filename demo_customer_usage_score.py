#!/usr/bin/env python
"""
Customer Usage Score Demonstration

Shows how to calculate CUS for organizations to predict churn.

This demo works with the existing schema (no migration required).
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_async_db
from app.services.customer_usage_score import CustomerUsageScoreService, ScoreTier
from app.db.models.user import User
from app.db.models.organization import Organization


async def demo_customer_usage_score():
    """Demonstrate CUS calculation for all organizations."""

    print("\n" + "="*80)
    print("CUSTOMER USAGE SCORE DEMONSTRATION")
    print("="*80)

    # Get database session
    async for db in get_async_db():
        service = CustomerUsageScoreService(db)

        # Get all organizations
        result = await db.execute(select(Organization).limit(5))
        organizations = result.scalars().all()

        print(f"\nFound {len(organizations)} organizations to analyze\n")

        # Calculate CUS for each organization
        for org in organizations:
            print(f"\n{'─'*80}")
            print(f"Organization: {org.name}")
            print(f"{'─'*80}")

            try:
                # Calculate customer usage score
                cus = await service.calculate_score(
                    organization_id=str(org.id),
                    lookback_days=30,
                    previous_period_days=30
                )

                # Display results
                print(f"\n📊 CUSTOMER USAGE SCORE: {cus.score:.1f}/100")
                print(f"   Health Tier: {cus.tier.value.upper()}")
                print(f"   Churn Probability: {cus.churn_probability*100:.1f}%")
                print(f"   Trend: {cus.trend or 'N/A'}")

                # Component breakdown
                print(f"\n📈 Component Breakdown:")
                for component_name, component in cus.components.items():
                    trend_icon = {
                        "improving": "📈",
                        "stable": "➡️",
                        "declining": "📉",
                        "growing": "🚀"
                    }.get(component.trend, "•")

                    print(f"   {trend_icon} {component_name.title():15} {component.score:5.1f}/100 "
                          f"(weight: {component.weight*100:.0f}%) → {component.weighted_score:.1f} points")

                # Metrics
                print(f"\n📋 Key Metrics:")
                if "engagement" in cus.components:
                    eng = cus.components["engagement"]
                    print(f"   • DAU/MAU Ratio: {eng.metrics.get('dau_mau_ratio', 0):.2f}")
                    print(f"   • Session Frequency: {eng.metrics.get('session_frequency', 0):.1f} assessments/user")
                    print(f"   • Feature Breadth: {eng.metrics.get('feature_breadth', 0):.1%}")

                if "adoption" in cus.components:
                    ado = cus.components["adoption"]
                    print(f"   • Activation Rate: {ado.metrics.get('activation_rate', 0):.1%}")
                    print(f"   • Team Adoption: {ado.metrics.get('team_adoption_rate', 0):.1%}")
                    print(f"   • Seat Utilization: {ado.metrics.get('seat_utilization', 0):.1%}")

                # Insights
                if cus.insights:
                    print(f"\n💡 Insights:")
                    for insight in cus.insights:
                        print(f"   • {insight}")

                # Recommendations
                if cus.recommendations:
                    print(f"\n🎯 Recommendations:")
                    for rec in cus.recommendations:
                        print(f"   • {rec}")

                # Health indicator
                health_bar = "█" * int(cus.score / 10) + "░" * (10 - int(cus.score / 10))
                health_emoji = {
                    ScoreTier.THRIVING: "🌟",
                    ScoreTier.HEALTHY: "✅",
                    ScoreTier.AT_RISK: "⚠️",
                    ScoreTier.CRITICAL: "🔴"
                }.get(cus.tier, "•")

                print(f"\n{health_emoji} Health: [{health_bar}] {cus.score:.0f}/100")

            except Exception as e:
                print(f"\n❌ Error calculating score: {e}")
                import traceback
                traceback.print_exc()

        print(f"\n{'='*80}\n")

        # Identify at-risk customers
        print("\n🔍 AT-RISK CUSTOMERS (Score < 40)")
        print("="*80)

        at_risk_customers = await service.get_at_risk_customers(
            score_threshold=40.0,
            limit=5
        )

        if at_risk_customers:
            for cus in at_risk_customers:
                print(f"\n⚠️  Organization: {cus.organization_id}")
                print(f"   Score: {cus.score:.1f}/100")
                print(f"   Churn Risk: {cus.churn_probability*100:.1f}%")
                print(f"   Top Issues:")
                for component_name, component in cus.components.items():
                    if component.score < 50:
                        print(f"      • {component_name}: {component.score:.1f}/100")
        else:
            print("\n✅ No at-risk customers found!")

        print(f"\n{'='*80}\n")

        break  # Only use first DB session


async def demo_score_calculation_steps():
    """Show detailed steps of CUS calculation."""

    print("\n" + "="*80)
    print("CUS CALCULATION DETAILS")
    print("="*80)

    async for db in get_async_db():
        service = CustomerUsageScoreService(db)

        # Get first organization
        result = await db.execute(select(Organization).limit(1))
        org = result.scalar_one_or_none()

        if not org:
            print("\n❌ No organizations found in database")
            return

        print(f"\nAnalyzing: {org.name}")
        print("="*80)

        # Get user count
        user_count = await service._get_user_count(str(org.id))
        print(f"\n📊 Total Users: {user_count}")

        # Get active users (DAU/MAU)
        dau = await service._get_active_user_count(str(org.id), days=1)
        mau = await service._get_active_user_count(str(org.id), days=30)
        dau_mau_ratio = (dau / mau) if mau > 0 else 0
        print(f"📊 DAU: {dau}, MAU: {mau}")
        print(f"📊 DAU/MAU Ratio: {dau_mau_ratio:.2%}")

        # Get assessment completions
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        assessments = await service._get_assessment_count(str(org.id), start_date, end_date)
        print(f"📊 Assessments (30d): {assessments}")

        # Calculate engagement score
        session_frequency = assessments / user_count if user_count > 0 else 0
        print(f"📊 Session Frequency: {session_frequency:.1f} per user")

        engagement_score = (dau_mau_ratio * 40) + (min(session_frequency / 4, 1.0) * 30) + 30
        print(f"\n✅ Engagement Score: {engagement_score:.1f}/100")

        print(f"\n{'='*80}\n")

        break


if __name__ == "__main__":
    print("\n🚀 Customer Usage Score Demonstration")
    print("="*80)
    print("\nThis demo shows how to:")
    print("  1. Calculate Customer Usage Score for organizations")
    print("  2. Identify at-risk customers")
    print("  3. Generate churn predictions")
    print("  4. Provide actionable insights")

    # Run demonstrations
    asyncio.run(demo_score_calculation_steps())
    asyncio.run(demo_customer_usage_score())

    print("\n✅ Demo complete!")
    print("\nNext Steps:")
    print("  • Integrate CUS calculation into daily batch jobs")
    print("  • Set up alerts for at-risk customers")
    print("  • Use insights for customer success outreach")
    print("  • Track CUS trends over time")
    print()
