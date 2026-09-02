# app/services/benchmark_service.py
"""
Benchmarking Service

Aggregates anonymized BI scores across enrolled organizations
into percentile distributions. Provides cross-org comparison
with k-anonymity protection (k=20 minimum orgs per cohort).
"""

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.benchmarks import (
    BenchmarkCohort,
    BenchmarkSnapshot,
    OrganizationBenchmarkEnrollment,
)

logger = logging.getLogger(__name__)

K_ANONYMITY_THRESHOLD = 20  # Minimum orgs required for benchmark
BI_METRICS = [
    "team_health",
    "collaboration",
    "manager_health",
    "psychological_safety",
    "change_readiness",
    "friction_index",
    "burnout_risk",
]


class BenchmarkService:
    """Manages benchmarking cohorts, aggregation, and comparison."""

    async def get_percentile(
        self,
        db: AsyncSession,
        org_id: UUID,
        metric: str,
        cohort_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get an organization's percentile rank for a metric within its cohort.

        Returns percentile (0-100), cohort distribution, and label.
        """
        if metric not in BI_METRICS:
            return {"error": f"Unknown metric: {metric}"}

        # Find the org's cohort
        if not cohort_id:
            cohort_id = await self._get_org_cohort(db, org_id)
            if not cohort_id:
                return {"error": "Organization not enrolled in benchmarking"}

        # Get latest benchmark snapshot for this cohort+metric
        result = await db.execute(
            select(BenchmarkSnapshot)
            .where(
                and_(
                    BenchmarkSnapshot.cohort_id == cohort_id,
                    BenchmarkSnapshot.metric_name == metric,
                )
            )
            .order_by(desc(BenchmarkSnapshot.snapshot_date))
            .limit(1)
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            return {"error": "No benchmark data available for this cohort"}

        # Get org's current score
        org_score = await self._get_org_metric(db, org_id, metric)
        if org_score is None:
            return {"error": f"No {metric} score available for this organization"}

        # Calculate percentile
        percentile = self._calculate_percentile(
            org_score,
            snapshot.p10,
            snapshot.p25,
            snapshot.p50,
            snapshot.p75,
            snapshot.p90,
        )

        # Label
        if percentile >= 75:
            label = "Top Quartile"
        elif percentile >= 50:
            label = "Above Median"
        elif percentile >= 25:
            label = "Below Median"
        else:
            label = "Bottom Quartile"

        return {
            "metric": metric,
            "org_score": round(org_score, 1),
            "percentile": round(percentile, 1),
            "label": label,
            "cohort_distribution": {
                "p10": round(snapshot.p10, 1) if snapshot.p10 else None,
                "p25": round(snapshot.p25, 1) if snapshot.p25 else None,
                "p50": round(snapshot.p50, 1) if snapshot.p50 else None,
                "p75": round(snapshot.p75, 1) if snapshot.p75 else None,
                "p90": round(snapshot.p90, 1) if snapshot.p90 else None,
                "mean": round(snapshot.mean, 1) if snapshot.mean else None,
            },
            "sample_size": snapshot.sample_size,
        }

    async def get_all_percentiles(
        self, db: AsyncSession, org_id: UUID
    ) -> Dict[str, Any]:
        """Get percentile ranks for all BI metrics."""
        cohort_id = await self._get_org_cohort(db, org_id)
        if not cohort_id:
            return {"error": "Organization not enrolled in benchmarking", "metrics": {}}

        metrics = {}
        for metric in BI_METRICS:
            result = await self.get_percentile(db, org_id, metric, cohort_id)
            if "error" not in result:
                metrics[metric] = result

        return {
            "organization_id": str(org_id),
            "cohort_id": str(cohort_id),
            "metrics": metrics,
        }

    async def aggregate_cohort(
        self, db: AsyncSession, cohort_id: UUID
    ) -> Dict[str, Any]:
        """
        Aggregate scores across all enrolled orgs in a cohort.
        Only produces output if k-anonymity threshold (20 orgs) is met.
        """
        # Get enrolled orgs
        result = await db.execute(
            select(OrganizationBenchmarkEnrollment.organization_id).where(
                and_(
                    OrganizationBenchmarkEnrollment.cohort_id == cohort_id,
                    OrganizationBenchmarkEnrollment.is_active == 1,
                )
            )
        )
        org_ids = [row[0] for row in result.all()]

        if len(org_ids) < K_ANONYMITY_THRESHOLD:
            logger.info(
                "Cohort %s has %d orgs (need %d) — skipping aggregation",
                cohort_id,
                len(org_ids),
                K_ANONYMITY_THRESHOLD,
            )
            return {
                "status": "insufficient_orgs",
                "count": len(org_ids),
                "required": K_ANONYMITY_THRESHOLD,
            }

        now = datetime.now(timezone.utc)
        snapshots_created = 0

        for metric in BI_METRICS:
            scores = []
            for org_id in org_ids:
                score = await self._get_org_metric(db, org_id, metric)
                if score is not None and score > 0:
                    scores.append(score)

            if len(scores) < K_ANONYMITY_THRESHOLD:
                continue

            scores.sort()
            n = len(scores)

            snapshot = BenchmarkSnapshot(
                cohort_id=cohort_id,
                snapshot_date=now,
                metric_name=metric,
                p10=scores[int(n * 0.10)],
                p25=scores[int(n * 0.25)],
                p50=scores[int(n * 0.50)],
                p75=scores[int(n * 0.75)],
                p90=scores[min(int(n * 0.90), n - 1)],
                mean=sum(scores) / n,
                std_dev=self._std_dev(scores),
                sample_size=n,
            )
            db.add(snapshot)
            snapshots_created += 1

        await db.commit()
        return {
            "status": "aggregated",
            "metrics": snapshots_created,
            "orgs": len(org_ids),
        }

    async def enroll_organization(
        self, db: AsyncSession, org_id: UUID, cohort_id: UUID
    ) -> Dict[str, Any]:
        """Enroll an organization in a benchmark cohort."""
        enrollment = OrganizationBenchmarkEnrollment(
            organization_id=org_id,
            cohort_id=cohort_id,
        )
        db.add(enrollment)

        # Update cohort org count
        result = await db.execute(
            select(func.count())
            .select_from(OrganizationBenchmarkEnrollment)
            .where(
                and_(
                    OrganizationBenchmarkEnrollment.cohort_id == cohort_id,
                    OrganizationBenchmarkEnrollment.is_active == 1,
                )
            )
        )
        count = result.scalar()

        await db.execute(select(BenchmarkCohort).where(BenchmarkCohort.id == cohort_id))
        # Update count via direct update
        from sqlalchemy import update

        await db.execute(
            update(BenchmarkCohort)
            .where(BenchmarkCohort.id == cohort_id)
            .values(org_count=count + 1)
        )

        await db.commit()
        return {"enrolled": True, "cohort_id": str(cohort_id)}

    # --- Helpers ---

    async def _get_org_cohort(self, db: AsyncSession, org_id: UUID) -> Optional[UUID]:
        result = await db.execute(
            select(OrganizationBenchmarkEnrollment.cohort_id)
            .where(
                and_(
                    OrganizationBenchmarkEnrollment.organization_id == org_id,
                    OrganizationBenchmarkEnrollment.is_active == 1,
                )
            )
            .limit(1)
        )
        row = result.first()
        return row[0] if row else None

    async def _get_org_metric(
        self, db: AsyncSession, org_id: UUID, metric: str
    ) -> Optional[float]:
        """Get an org's current BI score for a metric."""
        try:
            from app.services.behavioral_intelligence_service import (
                BehavioralIntelligenceService,
            )

            bi = BehavioralIntelligenceService()
            dashboard = await bi.get_organization_dashboard(db, str(org_id))
            return dashboard.get("scores", {}).get(metric)
        except Exception:
            return None

    def _calculate_percentile(
        self, score: float, p10: float, p25: float, p50: float, p75: float, p90: float
    ) -> float:
        """Estimate percentile from known distribution points via linear interpolation."""
        points = [(10, p10), (25, p25), (50, p50), (75, p75), (90, p90)]
        points = [(p, v) for p, v in points if v is not None]

        if not points:
            return 50.0

        # Below lowest known point
        if score <= points[0][1]:
            return max(1.0, points[0][0] * (score / max(points[0][1], 1)))

        # Above highest known point
        if score >= points[-1][1]:
            return min(99.0, points[-1][0] + (100 - points[-1][0]) * 0.5)

        # Interpolate between known points
        for i in range(len(points) - 1):
            p_low, v_low = points[i]
            p_high, v_high = points[i + 1]
            if v_low <= score <= v_high:
                if v_high == v_low:
                    return (p_low + p_high) / 2
                ratio = (score - v_low) / (v_high - v_low)
                return p_low + ratio * (p_high - p_low)

        return 50.0

    def _std_dev(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
        return math.sqrt(variance)


# Singleton
benchmark_service = BenchmarkService()
