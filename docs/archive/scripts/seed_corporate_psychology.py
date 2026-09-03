#!/usr/bin/env python3
"""Seed corporate psychology metrics for an organization"""
import asyncio
import sys
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, "/Users/sheriftito/Downloads/psychsync")

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.db.models.corporate_psychology import CorporatePsychologyMetrics


async def seed_corporate_psychology():
    """Create sample psychology metrics for organization"""
    org_id = "9342b324-5bad-4efd-8f57-69e0dabdb15a"

    async with AsyncSessionLocal() as db:
        # Check if data already exists
        result = await db.execute(
            select(CorporatePsychologyMetrics).where(
                CorporatePsychologyMetrics.organization_id == org_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"✅ Metrics already exist for organization {org_id}")
            print(f"   Health Index: {existing.organizational_health_index}")
            print(f"   Risk Score: {existing.overall_risk_score}")
            return

        # Create sample metrics with realistic values
        # Using a mix of good and concerning metrics to show the dashboard capabilities
        today = datetime.now().date()
        period_start = today - timedelta(days=30)

        metrics = CorporatePsychologyMetrics(
            organization_id=org_id,
            team_id=None,  # Organization-level metrics
            measurement_period_start=period_start,
            measurement_period_end=today,
            # Core Psychology Encodings (0-100 scale)
            # 1. Cognitive Load Index - moderate load
            cognitive_load_index=Decimal("62.50"),
            cli_trend="stable",
            cli_slope=Decimal("0.120"),
            cli_acceleration=Decimal("-0.050"),
            cli_drivers=Decimal("45.00"),  # Workload is main driver
            # 2. Trust Stability - good trust levels
            trust_stability_score=Decimal("71.25"),
            tsc_trend="strengthening",
            tsc_volatility=Decimal("15.30"),
            tsc_cross_team_trust=Decimal("68.50"),
            tsc_leadership_trust=Decimal("74.00"),
            # 3. Emotional Volatility - moderate volatility
            emotional_volatility_score=Decimal("45.80"),
            evs_trend="stable",
            evs_triggers=Decimal("35.00"),  # Deadline pressure
            evs_recovery_time=Decimal("2.50"),  # Days
            # 4. Coordination Friction - some friction points
            coordination_friction_score=Decimal("58.30"),
            cfs_bottlenecks=Decimal("42.00"),
            cfs_handoff_efficiency=Decimal("65.00"),
            cfs_dependency_loops=3,
            # 5. Psychological Debt - moderate debt accumulation
            psychological_debt_score=Decimal("55.20"),
            pda_rate=Decimal("2.100"),
            pda_debt_categories=Decimal("50.00"),  # Workload debt
            pda_paydown_capacity=Decimal("60.00"),
            # 6. Recovery & Resilience - good resilience
            recovery_resilience_score=Decimal("68.75"),
            rrc_buffer=Decimal("25.00"),
            rrc_adaptation_speed=Decimal("72.50"),
            rrc_learning_rate=Decimal("65.00"),
            # Derived System Metrics
            organizational_health_index=Decimal("63.85"),  # Good overall health
            health_trajectory="improving",
            # Risk Indicators
            overall_risk_score=Decimal("42.30"),  # Moderate risk
            risk_horizon="emerging",  # 15-45 day horizon
            risk_probability_range="35-50%",
            # Operational Impact Scores
            execution_risk_score=Decimal("38.50"),
            innovation_risk_score=Decimal("45.00"),
            retention_risk_score=Decimal("40.20"),
            collaboration_risk_score=Decimal("48.75"),
            # Contextual Data
            data_quality_score=Decimal("85.00"),
            confidence_level=Decimal("78.50"),
            sample_size=150,  # 150 data points analyzed
            seasonality_factor=Decimal("1.05"),
            organizational_events=Decimal("2.00"),  # 2 major events
            baseline_comparison=Decimal("5.20"),  # 5.2% above baseline
        )

        db.add(metrics)
        await db.commit()
        await db.refresh(metrics)

        print(f"✅ Successfully created corporate psychology metrics!")
        print(f"\n📊 Key Metrics:")
        print(
            f"   Organization Health Index: {metrics.organizational_health_index}/100"
        )
        print(f"   Overall Risk Score: {metrics.overall_risk_score}/100")
        print(f"   Risk Horizon: {metrics.risk_horizon}")
        print(f"\n🧠 Psychology Encodings:")
        print(
            f"   Cognitive Load Index: {metrics.cognitive_load_index}/100 ({metrics.cli_trend})"
        )
        print(
            f"   Trust Stability: {metrics.trust_stability_score}/100 ({metrics.tsc_trend})"
        )
        print(
            f"   Emotional Volatility: {metrics.emotional_volatility_score}/100 ({metrics.evs_trend})"
        )
        print(f"   Coordination Friction: {metrics.coordination_friction_score}/100")
        print(f"   Psychological Debt: {metrics.psychological_debt_score}/100")
        print(f"   Recovery Resilience: {metrics.recovery_resilience_score}/100")
        print(f"\n📅 Measurement Period:")
        print(f"   From: {metrics.measurement_period_start}")
        print(f"   To: {metrics.measurement_period_end}")
        print(f"\n🎯 Operational Risks:")
        print(f"   Execution Risk: {metrics.execution_risk_score}/100")
        print(f"   Innovation Risk: {metrics.innovation_risk_score}/100")
        print(f"   Retention Risk: {metrics.retention_risk_score}/100")
        print(f"   Collaboration Risk: {metrics.collaboration_risk_score}/100")


asyncio.run(seed_corporate_psychology())
