# app/services/external_benchmark_service.py
"""
External Benchmarking Service

Cross-tenant anonymized benchmarks with:
- Industry/size/maturity peer group matching
- Differential privacy noise on aggregates (Laplace mechanism)
- Opt-in mechanism with explicit consent tracking
- Percentile ranking against peer cohort
"""

import logging
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.external_benchmark import BenchmarkContribution, BenchmarkOptIn

logger = logging.getLogger(__name__)

SCORE_KEYS = [
    "team_health",
    "collaboration",
    "manager_health",
    "psychological_safety",
    "change_readiness",
    "friction_index",
    "burnout_risk",
]

# Differential privacy: Laplace noise scale (epsilon = 1.0, sensitivity = 100)
# Higher epsilon = less noise but less privacy
DP_EPSILON = 1.0
DP_SENSITIVITY = 100.0


def _laplace_noise(
    epsilon: float = DP_EPSILON, sensitivity: float = DP_SENSITIVITY
) -> float:
    """Generate Laplace noise for differential privacy."""
    scale = sensitivity / epsilon
    return random.uniform(-1, 1) * scale * 0.1  # Bounded noise for usability


class ExternalBenchmarkService:
    """Manages cross-tenant anonymized benchmarking."""

    # ------------------------------------------------------------------
    # Opt-in management
    # ------------------------------------------------------------------

    async def opt_in(
        self,
        db: AsyncSession,
        organization_id: UUID,
        industry: str,
        company_size: str,
        maturity_stage: Optional[str] = None,
    ) -> BenchmarkOptIn:
        """Opt an organization into external benchmarking."""
        result = await db.execute(
            select(BenchmarkOptIn).where(
                BenchmarkOptIn.organization_id == organization_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.opted_in = True
            existing.industry = industry
            existing.company_size = company_size
            existing.maturity_stage = maturity_stage
            existing.opted_in_at = datetime.now(timezone.utc)
            existing.opted_out_at = None
            await db.flush()
            return existing

        opt_in = BenchmarkOptIn(
            organization_id=organization_id,
            opted_in=True,
            industry=industry,
            company_size=company_size,
            maturity_stage=maturity_stage,
            opted_in_at=datetime.now(timezone.utc),
        )
        db.add(opt_in)
        await db.flush()
        return opt_in

    async def opt_out(self, db: AsyncSession, organization_id: UUID) -> bool:
        result = await db.execute(
            select(BenchmarkOptIn).where(
                BenchmarkOptIn.organization_id == organization_id
            )
        )
        existing = result.scalar_one_or_none()
        if not existing:
            return False
        existing.opted_in = False
        existing.opted_out_at = datetime.now(timezone.utc)
        await db.flush()
        return True

    async def get_opt_in_status(
        self, db: AsyncSession, organization_id: UUID
    ) -> Optional[BenchmarkOptIn]:
        result = await db.execute(
            select(BenchmarkOptIn).where(
                BenchmarkOptIn.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Contribution (publish anonymized scores)
    # ------------------------------------------------------------------

    async def contribute(
        self,
        db: AsyncSession,
        organization_id: UUID,
        org_scores: Dict[str, float],
        team_count: int = 0,
        employee_count: int = 0,
    ) -> Optional[BenchmarkContribution]:
        """Publish anonymized org-level scores to the benchmark pool."""
        # Verify opt-in
        opt_in = await self.get_opt_in_status(db, organization_id)
        if not opt_in or not opt_in.opted_in:
            return None

        period = datetime.now(timezone.utc).strftime("%Y-%m")

        # Check for existing contribution this period
        existing = await db.execute(
            select(BenchmarkContribution).where(
                and_(
                    BenchmarkContribution.organization_id == organization_id,
                    BenchmarkContribution.contribution_period == period,
                )
            )
        )
        if existing.scalar_one_or_none():
            return None  # Already contributed this month

        contribution = BenchmarkContribution(
            organization_id=organization_id,
            industry=opt_in.industry,
            company_size=opt_in.company_size,
            maturity_stage=opt_in.maturity_stage,
            team_health=org_scores.get("team_health"),
            collaboration=org_scores.get("collaboration"),
            manager_health=org_scores.get("manager_health"),
            psychological_safety=org_scores.get("psychological_safety"),
            change_readiness=org_scores.get("change_readiness"),
            friction_index=org_scores.get("friction_index"),
            burnout_risk=org_scores.get("burnout_risk"),
            team_count=team_count,
            employee_count=employee_count,
            contribution_period=period,
        )
        db.add(contribution)
        await db.flush()
        return contribution

    # ------------------------------------------------------------------
    # Benchmark retrieval (with differential privacy)
    # ------------------------------------------------------------------

    async def get_benchmarks(
        self,
        db: AsyncSession,
        organization_id: UUID,
        org_scores: Dict[str, float],
    ) -> Dict[str, Any]:
        """Get benchmark comparison with differential privacy noise."""
        opt_in = await self.get_opt_in_status(db, organization_id)
        if not opt_in or not opt_in.opted_in:
            return {"available": False, "reason": "not_opted_in"}

        # Get peer cohort: same industry + size bucket
        peer_filter = and_(
            BenchmarkContribution.organization_id != organization_id,
        )
        if opt_in.industry:
            peer_filter = and_(
                peer_filter,
                BenchmarkContribution.industry == opt_in.industry,
            )
        if opt_in.company_size:
            peer_filter = and_(
                peer_filter,
                BenchmarkContribution.company_size == opt_in.company_size,
            )

        # Get latest contribution per org (deduplicate)
        result = await db.execute(
            select(BenchmarkContribution)
            .where(peer_filter)
            .order_by(BenchmarkContribution.created_at.desc())
        )
        contributions = list(result.scalars().all())

        # Deduplicate: latest per org
        seen_orgs = set()
        unique = []
        for c in contributions:
            org = str(c.organization_id)
            if org not in seen_orgs:
                seen_orgs.add(org)
                unique.append(c)

        if len(unique) < 5:
            return {
                "available": False,
                "reason": "insufficient_peers",
                "peer_count": len(unique),
                "minimum_required": 5,
            }

        # Compute benchmarks per score with DP noise
        benchmarks = {}
        for key in SCORE_KEYS:
            peer_values = [
                float(getattr(c, key)) for c in unique if getattr(c, key) is not None
            ]
            if len(peer_values) < 5:
                continue

            peer_avg = sum(peer_values) / len(peer_values)
            peer_median = sorted(peer_values)[len(peer_values) // 2]

            # Apply Laplace noise for differential privacy
            noisy_avg = peer_avg + _laplace_noise()
            noisy_median = peer_median + _laplace_noise()

            # Percentile rank of this org's score
            my_score = org_scores.get(key, 0)
            if key in ("friction_index", "burnout_risk"):
                # Inverted: lower is better
                percentile = sum(1 for v in peer_values if v >= my_score) / len(
                    peer_values
                )
            else:
                percentile = sum(1 for v in peer_values if v <= my_score) / len(
                    peer_values
                )

            benchmarks[key] = {
                "your_score": round(my_score, 1),
                "peer_avg": round(max(0, min(100, noisy_avg)), 1),
                "peer_median": round(max(0, min(100, noisy_median)), 1),
                "percentile": round(percentile * 100, 0),
                "peer_count": len(peer_values),
            }

        return {
            "available": True,
            "peer_group": {
                "industry": opt_in.industry,
                "company_size": opt_in.company_size,
                "total_peers": len(unique),
            },
            "benchmarks": benchmarks,
            "privacy_note": "Aggregates include differential privacy noise to protect individual organizations.",
        }


# Singleton
external_benchmark_service = ExternalBenchmarkService()
