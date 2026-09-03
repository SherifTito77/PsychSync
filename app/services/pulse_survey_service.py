# app/services/pulse_survey_service.py
"""
Pulse Survey Service — Direct employee voice as ground truth.

This service manages recurring micro-surveys that populate
WellnessMetrics and provide calibration signals to the BI engine.
Without this, all BI scores are personality-based inference.

Key design: pulse responses are aggregated per-team and compared
against inferred BI scores. Divergences (>25pt gap) are flagged as
"confidence: uncertain" so executives know which scores to trust.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.pulse_survey import (
    PulseSurveyCampaign,
    PulseSurveyResponse,
    SurveyCampaignStatus,
)
from app.db.models.wellness_burnout import WellnessMetrics

logger = logging.getLogger(__name__)

# Maps pulse survey fields to BI score names for validation
_PULSE_TO_BI_MAP = {
    "team_health_perception": "team_health",
    "collaboration_effectiveness": "collaboration",
    "manager_support": "manager_health",
    "psychological_safety": "psychological_safety",
    "burnout_felt": "burnout_risk",
    "change_readiness": "change_readiness",
}


class PulseSurveyService:
    """Manages pulse survey campaigns, responses, and BI integration."""

    # ── Campaign Management ───────────────────────────────────────────

    async def create_campaign(
        self,
        db: AsyncSession,
        organization_id: str,
        name: str,
        frequency: str,
        created_by: str,
        question_set: str = "standard",
    ) -> Dict[str, Any]:
        campaign = PulseSurveyCampaign(
            organization_id=organization_id,
            name=name,
            frequency=frequency,
            created_by=created_by,
            question_set=question_set,
            status=SurveyCampaignStatus.ACTIVE.value,
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)

        return {
            "id": str(campaign.id),
            "name": campaign.name,
            "frequency": campaign.frequency,
            "status": campaign.status,
            "question_set": campaign.question_set,
        }

    async def get_active_campaign(
        self, db: AsyncSession, organization_id: str
    ) -> Optional[PulseSurveyCampaign]:
        result = await db.execute(
            select(PulseSurveyCampaign).where(
                and_(
                    PulseSurveyCampaign.organization_id == organization_id,
                    PulseSurveyCampaign.status == SurveyCampaignStatus.ACTIVE.value,
                )
            )
        )
        return result.scalars().first()

    # ── Response Submission ───────────────────────────────────────────

    async def submit_response(
        self,
        db: AsyncSession,
        organization_id: str,
        respondent_id: str,
        responses: Dict[str, Any],
        team_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit a pulse survey response and populate WellnessMetrics."""
        today = date.today()
        year, week, _ = today.isocalendar()
        survey_round = f"{year}-W{week:02d}"

        # Check for duplicate in this round
        existing = await db.execute(
            select(PulseSurveyResponse.id).where(
                and_(
                    PulseSurveyResponse.respondent_id == respondent_id,
                    PulseSurveyResponse.survey_round == survey_round,
                    PulseSurveyResponse.organization_id == organization_id,
                )
            )
        )
        if existing.scalars().first():
            return {
                "success": False,
                "error": "Already submitted for this survey round",
                "survey_round": survey_round,
            }

        response = PulseSurveyResponse(
            organization_id=organization_id,
            campaign_id=campaign_id,
            respondent_id=respondent_id,
            team_id=team_id,
            survey_round=survey_round,
            survey_date=today,
            team_health_perception=responses.get("team_health_perception"),
            collaboration_effectiveness=responses.get("collaboration_effectiveness"),
            manager_support=responses.get("manager_support"),
            psychological_safety=responses.get("psychological_safety"),
            workload_balance=responses.get("workload_balance"),
            engagement_level=responses.get("engagement_level"),
            burnout_felt=responses.get("burnout_felt"),
            change_readiness=responses.get("change_readiness"),
            biggest_challenge=responses.get("biggest_challenge"),
            response_time_seconds=responses.get("response_time_seconds"),
        )
        db.add(response)

        # Populate WellnessMetrics from pulse responses
        await self._sync_to_wellness_metrics(
            db, organization_id, respondent_id, team_id, responses, today
        )

        await db.commit()

        return {
            "success": True,
            "survey_round": survey_round,
            "response_id": str(response.id),
        }

    # ── Aggregation ───────────────────────────────────────────────────

    async def get_team_pulse_summary(
        self,
        db: AsyncSession,
        organization_id: str,
        team_id: Optional[str] = None,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """Aggregate pulse responses per team for BI enrichment.

        Returns averaged scores (0-100 scale) ready for BI blending.
        """
        since = date.today() - timedelta(days=lookback_days)

        query = select(
            PulseSurveyResponse.team_id,
            func.count(PulseSurveyResponse.id).label("response_count"),
            func.avg(PulseSurveyResponse.team_health_perception).label("avg_health"),
            func.avg(PulseSurveyResponse.collaboration_effectiveness).label(
                "avg_collab"
            ),
            func.avg(PulseSurveyResponse.manager_support).label("avg_manager"),
            func.avg(PulseSurveyResponse.psychological_safety).label("avg_safety"),
            func.avg(PulseSurveyResponse.workload_balance).label("avg_workload"),
            func.avg(PulseSurveyResponse.engagement_level).label("avg_engagement"),
            func.avg(PulseSurveyResponse.burnout_felt).label("avg_burnout"),
            func.avg(PulseSurveyResponse.change_readiness).label("avg_change"),
        ).where(
            and_(
                PulseSurveyResponse.organization_id == organization_id,
                PulseSurveyResponse.survey_date >= since,
            )
        )

        if team_id:
            query = query.where(PulseSurveyResponse.team_id == team_id)

        query = query.group_by(PulseSurveyResponse.team_id)
        result = await db.execute(query)
        rows = result.all()

        if not rows:
            return {}

        def _to_100(val):
            """Convert 1-10 scale to 0-100."""
            return round(float(val) * 10, 1) if val is not None else None

        teams_summary = {}
        for row in rows:
            tid = str(row.team_id) if row.team_id else "org_wide"
            teams_summary[tid] = {
                "response_count": row.response_count,
                "team_health": _to_100(row.avg_health),
                "collaboration": _to_100(row.avg_collab),
                "manager_support": _to_100(row.avg_manager),
                "psychological_safety": _to_100(row.avg_safety),
                "workload_balance": _to_100(row.avg_workload),
                "engagement": _to_100(row.avg_engagement),
                "burnout_felt": _to_100(row.avg_burnout),
                "change_readiness": _to_100(row.avg_change),
            }

        return teams_summary

    async def get_org_pulse_summary(
        self,
        db: AsyncSession,
        organization_id: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """Organization-wide pulse summary for enrichment dict."""
        since = date.today() - timedelta(days=lookback_days)

        result = await db.execute(
            select(
                func.count(PulseSurveyResponse.id).label("count"),
                func.avg(PulseSurveyResponse.team_health_perception),
                func.avg(PulseSurveyResponse.collaboration_effectiveness),
                func.avg(PulseSurveyResponse.manager_support),
                func.avg(PulseSurveyResponse.psychological_safety),
                func.avg(PulseSurveyResponse.workload_balance),
                func.avg(PulseSurveyResponse.engagement_level),
                func.avg(PulseSurveyResponse.burnout_felt),
                func.avg(PulseSurveyResponse.change_readiness),
            ).where(
                and_(
                    PulseSurveyResponse.organization_id == organization_id,
                    PulseSurveyResponse.survey_date >= since,
                )
            )
        )
        row = result.one_or_none()

        if not row or not row[0]:
            return {}

        def _to_100(val):
            return round(float(val) * 10, 1) if val is not None else None

        return {
            "response_count": row[0],
            "pulse_team_health": _to_100(row[1]),
            "pulse_collaboration": _to_100(row[2]),
            "pulse_manager_support": _to_100(row[3]),
            "pulse_psych_safety": _to_100(row[4]),
            "pulse_workload_balance": _to_100(row[5]),
            "pulse_engagement": _to_100(row[6]),
            "pulse_burnout_felt": _to_100(row[7]),
            "pulse_change_readiness": _to_100(row[8]),
        }

    # ── Validation Layer ──────────────────────────────────────────────

    async def validate_against_inferred(
        self,
        db: AsyncSession,
        organization_id: str,
        bi_org_scores: Dict[str, Any],
        lookback_days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Compare pulse survey results with inferred BI scores.

        Returns divergences where reported and inferred differ by >25 points.
        These indicate scores where the inference may be wrong.
        """
        pulse_summary = await self.get_org_pulse_summary(
            db, organization_id, lookback_days
        )
        if not pulse_summary or pulse_summary.get("response_count", 0) < 5:
            return []

        divergences = []
        comparisons = {
            "pulse_team_health": "team_health",
            "pulse_collaboration": "collaboration",
            "pulse_manager_support": "manager_health",
            "pulse_psych_safety": "psychological_safety",
            "pulse_burnout_felt": "burnout_risk",
            "pulse_change_readiness": "change_readiness",
        }

        for pulse_key, bi_key in comparisons.items():
            pulse_val = pulse_summary.get(pulse_key)
            bi_val = bi_org_scores.get(bi_key)
            if pulse_val is None or bi_val is None:
                continue

            # For burnout, pulse reports "felt burnout" which is same direction as bi
            gap = abs(pulse_val - bi_val)
            if gap > 25:
                divergences.append(
                    {
                        "metric": bi_key,
                        "inferred_score": bi_val,
                        "reported_score": pulse_val,
                        "gap": round(gap, 1),
                        "direction": (
                            "over_estimated"
                            if bi_val > pulse_val
                            else "under_estimated"
                        ),
                        "confidence": "uncertain",
                        "recommendation": (
                            f"{bi_key.replace('_', ' ').title()} shows a {round(gap)}pt "
                            f"gap between inferred ({bi_val}) and reported ({pulse_val}). "
                            f"The inferred score may be {'too high' if bi_val > pulse_val else 'too low'}."
                        ),
                    }
                )

        return divergences

    # ── Response Trends ───────────────────────────────────────────────

    async def get_pulse_trends(
        self,
        db: AsyncSession,
        organization_id: str,
        days: int = 90,
    ) -> List[Dict[str, Any]]:
        """Weekly pulse trends for charting."""
        since = date.today() - timedelta(days=days)

        result = await db.execute(
            select(
                PulseSurveyResponse.survey_round,
                func.count(PulseSurveyResponse.id),
                func.avg(PulseSurveyResponse.team_health_perception),
                func.avg(PulseSurveyResponse.engagement_level),
                func.avg(PulseSurveyResponse.burnout_felt),
                func.avg(PulseSurveyResponse.psychological_safety),
            )
            .where(
                and_(
                    PulseSurveyResponse.organization_id == organization_id,
                    PulseSurveyResponse.survey_date >= since,
                )
            )
            .group_by(PulseSurveyResponse.survey_round)
            .order_by(PulseSurveyResponse.survey_round)
        )
        rows = result.all()

        def _to_100(v):
            return round(float(v) * 10, 1) if v is not None else None

        return [
            {
                "round": row[0],
                "responses": row[1],
                "team_health": _to_100(row[2]),
                "engagement": _to_100(row[3]),
                "burnout_felt": _to_100(row[4]),
                "psych_safety": _to_100(row[5]),
            }
            for row in rows
        ]

    # ── Private Helpers ───────────────────────────────────────────────

    async def _sync_to_wellness_metrics(
        self,
        db: AsyncSession,
        organization_id: str,
        user_id: str,
        team_id: Optional[str],
        responses: Dict[str, Any],
        today: date,
    ) -> None:
        """Populate WellnessMetrics from pulse survey responses.

        This bridges the gap: WellnessMetrics exists and is already wired
        into the BI burnout_risk calculation (35% weight), but had no
        input mechanism until now.
        """
        burnout = responses.get("burnout_felt")
        engagement = responses.get("engagement_level")
        workload = responses.get("workload_balance")

        if burnout is None and engagement is None:
            return

        # Resilience approximation: inverse of burnout + engagement
        resilience = None
        if burnout is not None and engagement is not None:
            resilience = round((10 - float(burnout) + float(engagement)) / 2, 1)

        wellness = WellnessMetrics(
            organization_id=organization_id,
            user_id=user_id,
            team_id=team_id,
            measurement_date=today,
            overall_wellness_score=engagement or 5.0,
            burnout_risk_score=burnout or 5.0,
            resilience_score=resilience,
            engagement_level=engagement,
            workload_score=workload,
            job_satisfaction=responses.get("engagement_level"),
            data_sources={"source": "pulse_survey", "date": today.isoformat()},
            confidence_level=0.8,
            data_completeness=0.7,
        )
        db.add(wellness)


# Module-level singleton
pulse_survey_service = PulseSurveyService()
