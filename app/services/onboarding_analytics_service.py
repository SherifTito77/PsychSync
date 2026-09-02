# app/services/onboarding_analytics_service.py
"""
Onboarding Analytics — New hire health composite from existing signals.

Identifies users created within the last N days (proxy for hire date)
and computes an onboarding health score from:
  - Network velocity: how fast they're building connections (ONA)
  - Recognition received: peer validation signals
  - Assessment completion: engagement with the platform
  - Pulse survey participation: active voice
  - Wellness baseline: early burnout/engagement signals
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.team import TeamMember

logger = logging.getLogger(__name__)


class OnboardingAnalyticsService:
    """Computes onboarding health for new hires."""

    async def get_onboarding_dashboard(
        self,
        db: AsyncSession,
        organization_id: str,
        onboarding_window_days: int = 90,
    ) -> Dict[str, Any]:
        """Full onboarding analytics for an organization."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=onboarding_window_days)

        # Find new hires: users on teams in this org, created after cutoff
        new_hires = await self._get_new_hires(db, organization_id, cutoff)

        if not new_hires:
            return {
                "organization_id": organization_id,
                "window_days": onboarding_window_days,
                "new_hire_count": 0,
                "hires": [],
                "summary": {"avg_health": 0, "at_risk": 0, "thriving": 0},
            }

        hire_profiles = []
        for hire in new_hires:
            profile = await self._compute_hire_profile(
                db, hire, organization_id, cutoff
            )
            hire_profiles.append(profile)

        # Sort by health score ascending (worst first)
        hire_profiles.sort(key=lambda p: p["health_score"])

        scores = [p["health_score"] for p in hire_profiles]
        at_risk = sum(1 for s in scores if s < 40)
        thriving = sum(1 for s in scores if s >= 70)

        return {
            "organization_id": organization_id,
            "window_days": onboarding_window_days,
            "new_hire_count": len(hire_profiles),
            "hires": hire_profiles,
            "summary": {
                "avg_health": round(sum(scores) / len(scores), 1),
                "at_risk": at_risk,
                "thriving": thriving,
                "on_track": len(scores) - at_risk - thriving,
            },
        }

    async def _get_new_hires(
        self,
        db: AsyncSession,
        organization_id: str,
        cutoff: datetime,
    ) -> List[Dict[str, Any]]:
        """Find users created after cutoff who belong to teams in this org."""
        from app.db.models.team import Team

        query = (
            select(
                User.id, User.full_name, User.email, User.created_at, TeamMember.team_id
            )
            .join(TeamMember, TeamMember.user_id == User.id)
            .join(Team, Team.id == TeamMember.team_id)
            .where(
                and_(
                    Team.organization_id == organization_id,
                    User.created_at >= cutoff,
                )
            )
        )
        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "user_id": str(row[0]),
                "name": row[1] or row[2] or "Unknown",
                "email": row[2],
                "created_at": row[3],
                "team_id": str(row[4]),
                "days_since_join": (
                    (
                        datetime.now(timezone.utc) - row[3].replace(tzinfo=timezone.utc)
                    ).days
                    if row[3]
                    else 0
                ),
            }
            for row in rows
        ]

    async def _compute_hire_profile(
        self,
        db: AsyncSession,
        hire: Dict[str, Any],
        organization_id: str,
        cutoff: datetime,
    ) -> Dict[str, Any]:
        """Compute onboarding health for a single new hire."""
        uid = hire["user_id"]
        days = hire["days_since_join"]

        # Signal 1: Network velocity (ONA connections built)
        network_score = await self._network_velocity(db, uid)

        # Signal 2: Recognition received
        recognition_score = await self._recognition_received(db, uid, cutoff)

        # Signal 3: Assessment/survey engagement
        engagement_score = await self._platform_engagement(db, uid, cutoff)

        # Signal 4: Wellness baseline
        wellness_score = await self._wellness_baseline(db, uid)

        # Composite: weighted by signal reliability for new hires
        # Network velocity matters most early on (integration signal)
        health = (
            network_score * 0.35
            + recognition_score * 0.20
            + engagement_score * 0.25
            + wellness_score * 0.20
        )

        # Time adjustment: cut slack for very new hires (< 30 days)
        if days < 30:
            health = max(health, 40)  # Floor at 40 for < 30 days

        if health >= 70:
            status = "thriving"
        elif health >= 40:
            status = "on_track"
        else:
            status = "at_risk"

        return {
            "user_id": uid,
            "name": hire["name"],
            "team_id": hire["team_id"],
            "days_since_join": days,
            "health_score": round(health, 1),
            "status": status,
            "signals": {
                "network_velocity": round(network_score, 1),
                "recognition_received": round(recognition_score, 1),
                "platform_engagement": round(engagement_score, 1),
                "wellness_baseline": round(wellness_score, 1),
            },
        }

    async def _network_velocity(self, db: AsyncSession, user_id: str) -> float:
        """How fast is this person building connections?"""
        try:
            from app.db.models.network_analysis import NetworkEdge

            result = await db.execute(
                select(func.count())
                .select_from(NetworkEdge)
                .where(
                    (NetworkEdge.source_user_id == user_id)
                    | (NetworkEdge.target_user_id == user_id)
                )
            )
            edge_count = result.scalar() or 0
            # 5+ connections = full score, 0 = 0
            return min(100, edge_count * 20)
        except Exception:
            return 50.0  # Neutral if ONA unavailable

    async def _recognition_received(
        self, db: AsyncSession, user_id: str, cutoff: datetime
    ) -> float:
        """How much peer recognition has this person received?"""
        try:
            from app.db.models.peer_recognition import PeerRecognition

            result = await db.execute(
                select(func.count())
                .select_from(PeerRecognition)
                .where(
                    and_(
                        PeerRecognition.receiver_id == user_id,
                        PeerRecognition.created_at >= cutoff,
                    )
                )
            )
            count = result.scalar() or 0
            # 3+ recognitions = full score
            return min(100, count * 33)
        except Exception:
            return 50.0

    async def _platform_engagement(
        self, db: AsyncSession, user_id: str, cutoff: datetime
    ) -> float:
        """Has this person completed assessments or pulse surveys?"""
        try:
            from app.db.models.response import Response

            result = await db.execute(
                select(func.count())
                .select_from(Response)
                .where(
                    and_(
                        Response.user_id == user_id,
                        Response.created_at >= cutoff,
                    )
                )
            )
            response_count = result.scalar() or 0

            # Also check pulse survey responses
            pulse_count = 0
            try:
                from app.db.models.pulse_survey import PulseSurveyResponse

                pr = await db.execute(
                    select(func.count())
                    .select_from(PulseSurveyResponse)
                    .where(
                        and_(
                            PulseSurveyResponse.respondent_id == user_id,
                            PulseSurveyResponse.created_at >= cutoff,
                        )
                    )
                )
                pulse_count = pr.scalar() or 0
            except Exception:
                pass

            total = response_count + pulse_count
            # 3+ responses = full engagement
            return min(100, total * 33)
        except Exception:
            return 50.0

    async def _wellness_baseline(self, db: AsyncSession, user_id: str) -> float:
        """Early wellness signals — low burnout + reasonable engagement."""
        try:
            from app.db.models.wellness_burnout import WellnessMetrics

            result = await db.execute(
                select(WellnessMetrics)
                .where(WellnessMetrics.user_id == user_id)
                .order_by(WellnessMetrics.measurement_date.desc())
                .limit(1)
            )
            wm = result.scalar_one_or_none()
            if not wm:
                return 50.0  # Neutral

            burnout = float(wm.burnout_risk_score or 5) * 10  # 0-10 → 0-100
            engagement = float(wm.engagement_level or 5) * 10
            # Good: low burnout + high engagement
            return max(0, min(100, engagement * 0.6 + (100 - burnout) * 0.4))
        except Exception:
            return 50.0


# Singleton
onboarding_analytics_service = OnboardingAnalyticsService()
