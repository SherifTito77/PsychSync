"""
Behavioral Intelligence Engine

Core scoring service that aggregates organizational signals into
composite behavioral health metrics. This is PsychSync's flagship
differentiation layer.

Scores produced:
  - Team Health Score (0-100)
  - Collaboration Score (0-100)
  - Manager Health Score (0-100)
  - Psychological Safety Score (0-100)
  - Change Readiness Score (0-100)
  - Organizational Friction Index (0-100, lower is better)

Data sources: Assessment responses, HRIS data, team structure,
calendar metadata, work system signals (when available).
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.response import Response
from app.db.models.team import Team, TeamMember
from app.db.models.user import User

logger = logging.getLogger(__name__)


class BehavioralIntelligenceService:
    """
    Aggregates behavioral signals into organizational health scores.

    Design principle: Behavior → Pattern → Prediction → Recommendation
    Not: Assessment → Score → Dashboard
    """

    # ── Team Health Score ────────────────────────────────────────────
    async def calculate_team_health(
        self,
        db: AsyncSession,
        team_id: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Composite team health from assessment engagement, personality
        balance, burnout risk, and tenure stability.
        """
        since = datetime.utcnow() - timedelta(days=lookback_days)

        # Get team members
        members = await self._get_team_members(db, team_id)
        member_count = len(members)
        if member_count == 0:
            return self._empty_score("team_health", "No team members found")

        member_ids = [str(m.user_id) for m in members]

        # Factor 1: Assessment engagement (are people completing assessments?)
        engagement = await self._assessment_engagement(db, member_ids, since)

        # Factor 2: Personality balance (Big Five trait diversity)
        personality_balance = await self._personality_balance(db, member_ids)

        # Factor 3: Response quality (are people answering thoughtfully?)
        response_quality = await self._response_quality(db, member_ids, since)

        # Factor 4: Team size health (research: 5-9 optimal)
        size_score = self._team_size_score(member_count)

        # Weighted composite
        score = (
            engagement * 0.30
            + personality_balance * 0.25
            + response_quality * 0.25
            + size_score * 0.20
        )

        trend = await self._calculate_trend(
            db, member_ids, "team_health", lookback_days
        )

        return {
            "score": round(score, 1),
            "label": self._score_label(score),
            "trend": trend,
            "factors": {
                "engagement": round(engagement, 1),
                "personality_balance": round(personality_balance, 1),
                "response_quality": round(response_quality, 1),
                "team_size_health": round(size_score, 1),
            },
            "member_count": member_count,
            "recommendations": self._team_health_recommendations(
                engagement, personality_balance, response_quality, size_score
            ),
        }

    # ── Collaboration Score ──────────────────────────────────────────
    async def calculate_collaboration_score(
        self,
        db: AsyncSession,
        team_id: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Measures cross-functional work and team cohesion.
        Uses assessment data + team structure as baseline.
        Enhanced with work system data when available.
        """
        since = datetime.utcnow() - timedelta(days=lookback_days)
        members = await self._get_team_members(db, team_id)
        if not members:
            return self._empty_score("collaboration", "No team members")

        member_ids = [str(m.user_id) for m in members]

        # Factor 1: Team agreeableness + extraversion (Big Five predictors of collaboration)
        collab_traits = await self._collaboration_trait_score(db, member_ids)

        # Factor 2: Assessment co-completion (teams that assess together collaborate better)
        co_completion = await self._co_completion_rate(db, member_ids, since)

        # Factor 3: Response consistency (similar engagement patterns = alignment)
        consistency = await self._response_consistency(db, member_ids, since)

        score = collab_traits * 0.40 + co_completion * 0.35 + consistency * 0.25

        return {
            "score": round(score, 1),
            "label": self._score_label(score),
            "trend": await self._calculate_trend(
                db, member_ids, "collaboration", lookback_days
            ),
            "factors": {
                "collaboration_traits": round(collab_traits, 1),
                "co_completion_rate": round(co_completion, 1),
                "response_consistency": round(consistency, 1),
            },
            "recommendations": self._collaboration_recommendations(
                collab_traits, co_completion, consistency
            ),
        }

    # ── Manager Health Score ─────────────────────────────────────────
    async def calculate_manager_health(
        self,
        db: AsyncSession,
        team_id: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """
        A manager's health is measured by their team's wellbeing.
        High burnout / low engagement on a team → struggling manager.
        """
        since = datetime.utcnow() - timedelta(days=lookback_days)
        members = await self._get_team_members(db, team_id)
        if not members:
            return self._empty_score("manager_health", "No team members")

        member_ids = [str(m.user_id) for m in members]

        # Factor 1: Team engagement health
        engagement = await self._assessment_engagement(db, member_ids, since)

        # Factor 2: Low neuroticism in team (inverse burnout proxy)
        neuroticism = await self._avg_trait(db, member_ids, "neuroticism")
        burnout_proxy = max(0, 100 - neuroticism)

        # Factor 3: Team conscientiousness (productivity proxy)
        conscientiousness = await self._avg_trait(db, member_ids, "conscientiousness")

        # Factor 4: Retention signal (team member tenure)
        retention = self._retention_score(members)

        score = (
            engagement * 0.30
            + burnout_proxy * 0.25
            + conscientiousness * 0.25
            + retention * 0.20
        )

        return {
            "score": round(score, 1),
            "label": self._score_label(score),
            "trend": await self._calculate_trend(
                db, member_ids, "manager_health", lookback_days
            ),
            "factors": {
                "team_engagement": round(engagement, 1),
                "burnout_resilience": round(burnout_proxy, 1),
                "team_productivity": round(conscientiousness, 1),
                "team_retention": round(retention, 1),
            },
            "recommendations": self._manager_health_recommendations(
                engagement, burnout_proxy, conscientiousness, retention
            ),
        }

    # ── Psychological Safety Score ───────────────────────────────────
    async def calculate_psychological_safety(
        self,
        db: AsyncSession,
        team_id: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Based on Edmondson's framework. Teams with high openness,
        high agreeableness, and low neuroticism tend to have
        higher psychological safety.
        """
        members = await self._get_team_members(db, team_id)
        if not members:
            return self._empty_score("psychological_safety", "No team members")

        member_ids = [str(m.user_id) for m in members]

        # Factor 1: Openness to experience (willingness to share ideas)
        openness = await self._avg_trait(db, member_ids, "openness")

        # Factor 2: Agreeableness (interpersonal trust)
        agreeableness = await self._avg_trait(db, member_ids, "agreeableness")

        # Factor 3: Low neuroticism (emotional stability)
        neuroticism = await self._avg_trait(db, member_ids, "neuroticism")
        stability = max(0, 100 - neuroticism)

        # Factor 4: Trait diversity (diverse teams that still function = high safety)
        diversity_bonus = await self._trait_diversity_bonus(db, member_ids)

        score = (
            openness * 0.30
            + agreeableness * 0.30
            + stability * 0.25
            + diversity_bonus * 0.15
        )

        return {
            "score": round(score, 1),
            "label": self._psych_safety_label(score),
            "trend": await self._calculate_trend(
                db, member_ids, "psych_safety", lookback_days
            ),
            "factors": {
                "openness_to_ideas": round(openness, 1),
                "interpersonal_trust": round(agreeableness, 1),
                "emotional_stability": round(stability, 1),
                "diversity_resilience": round(diversity_bonus, 1),
            },
            "recommendations": self._psych_safety_recommendations(
                openness, agreeableness, stability
            ),
        }

    # ── Change Readiness Score ───────────────────────────────────────
    async def calculate_change_readiness(
        self,
        db: AsyncSession,
        team_id: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Predicts how well a team will adapt to organizational change.
        High openness + high conscientiousness + low neuroticism = ready.
        """
        members = await self._get_team_members(db, team_id)
        if not members:
            return self._empty_score("change_readiness", "No team members")

        member_ids = [str(m.user_id) for m in members]

        # Factor 1: Openness (embraces new approaches)
        openness = await self._avg_trait(db, member_ids, "openness")

        # Factor 2: Conscientiousness (executes on new processes)
        conscientiousness = await self._avg_trait(db, member_ids, "conscientiousness")

        # Factor 3: Emotional resilience (handles uncertainty)
        neuroticism = await self._avg_trait(db, member_ids, "neuroticism")
        resilience = max(0, 100 - neuroticism)

        # Factor 4: Extraversion (communicates change effectively)
        extraversion = await self._avg_trait(db, member_ids, "extraversion")

        score = (
            openness * 0.35
            + conscientiousness * 0.25
            + resilience * 0.25
            + extraversion * 0.15
        )

        return {
            "score": round(score, 1),
            "label": self._readiness_label(score),
            "trend": await self._calculate_trend(
                db, member_ids, "change_readiness", lookback_days
            ),
            "factors": {
                "adaptability": round(openness, 1),
                "execution_capability": round(conscientiousness, 1),
                "emotional_resilience": round(resilience, 1),
                "communication_strength": round(extraversion, 1),
            },
            "recommendations": self._change_readiness_recommendations(
                openness, conscientiousness, resilience, extraversion
            ),
        }

    # ── Organizational Friction Index ────────────────────────────────
    async def calculate_friction_index(
        self,
        db: AsyncSession,
        team_id: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Measures organizational drag. Lower is better.
        Based on coordination overhead, response delays, and
        personality friction points.
        """
        since = datetime.utcnow() - timedelta(days=lookback_days)
        members = await self._get_team_members(db, team_id)
        if not members:
            return self._empty_score("friction_index", "No team members")

        member_ids = [str(m.user_id) for m in members]

        # Factor 1: Personality conflict potential
        conflict_potential = await self._conflict_potential(db, member_ids)

        # Factor 2: Assessment fatigue (declining response rates)
        fatigue = await self._assessment_fatigue(db, member_ids, since)

        # Factor 3: Team fragmentation (uneven participation)
        fragmentation = await self._participation_inequality(db, member_ids, since)

        friction = conflict_potential * 0.40 + fatigue * 0.30 + fragmentation * 0.30

        return {
            "score": round(friction, 1),
            "label": self._friction_label(friction),
            "trend": await self._calculate_trend(
                db, member_ids, "friction", lookback_days
            ),
            "factors": {
                "personality_conflict_risk": round(conflict_potential, 1),
                "assessment_fatigue": round(fatigue, 1),
                "participation_inequality": round(fragmentation, 1),
            },
            "recommendations": self._friction_recommendations(
                conflict_potential, fatigue, fragmentation
            ),
        }

    # ── Organization-wide Dashboard ──────────────────────────────────
    async def get_organization_dashboard(
        self,
        db: AsyncSession,
        organization_id: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """Full behavioral intelligence dashboard for an organization."""
        # Get all teams in the organization
        result = await db.execute(
            select(Team).where(Team.organization_id == organization_id)
        )
        teams = result.scalars().all()

        if not teams:
            return {
                "organization_id": organization_id,
                "team_count": 0,
                "scores": {},
                "teams": [],
                "executive_summary": "No teams found. Create teams and complete assessments to generate behavioral intelligence.",
                "generated_at": datetime.utcnow().isoformat(),
            }

        team_results = []
        agg_scores = {
            "team_health": [],
            "collaboration": [],
            "manager_health": [],
            "psychological_safety": [],
            "change_readiness": [],
            "friction_index": [],
        }

        for team in teams:
            tid = str(team.id)
            th = await self.calculate_team_health(db, tid, lookback_days)
            co = await self.calculate_collaboration_score(db, tid, lookback_days)
            mh = await self.calculate_manager_health(db, tid, lookback_days)
            ps = await self.calculate_psychological_safety(db, tid, lookback_days)
            cr = await self.calculate_change_readiness(db, tid, lookback_days)
            fi = await self.calculate_friction_index(db, tid, lookback_days)

            for key, val in [
                ("team_health", th),
                ("collaboration", co),
                ("manager_health", mh),
                ("psychological_safety", ps),
                ("change_readiness", cr),
                ("friction_index", fi),
            ]:
                if val["score"] > 0:
                    agg_scores[key].append(val["score"])

            team_results.append(
                {
                    "team_id": tid,
                    "team_name": team.name,
                    "member_count": th.get("member_count", 0),
                    "scores": {
                        "team_health": th["score"],
                        "collaboration": co["score"],
                        "manager_health": mh["score"],
                        "psychological_safety": ps["score"],
                        "change_readiness": cr["score"],
                        "friction_index": fi["score"],
                    },
                    "top_risk": self._identify_top_risk(th, co, mh, ps, cr, fi),
                }
            )

        # Organization averages
        org_scores = {}
        for key, vals in agg_scores.items():
            org_scores[key] = round(sum(vals) / len(vals), 1) if vals else 0.0

        # Executive narrative
        narrative = self._generate_executive_narrative(org_scores, team_results)

        # Sort teams by risk (lowest team_health first)
        team_results.sort(key=lambda t: t["scores"]["team_health"])

        return {
            "organization_id": organization_id,
            "team_count": len(teams),
            "scores": org_scores,
            "teams": team_results,
            "executive_summary": narrative,
            "generated_at": datetime.utcnow().isoformat(),
            "lookback_days": lookback_days,
        }

    # ══════════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ══════════════════════════════════════════════════════════════════

    async def _get_team_members(self, db: AsyncSession, team_id: str) -> list:
        result = await db.execute(
            select(TeamMember).where(TeamMember.team_id == team_id)
        )
        return result.scalars().all()

    async def _assessment_engagement(
        self, db: AsyncSession, member_ids: list, since: datetime
    ) -> float:
        """What % of members completed at least one assessment recently?"""
        if not member_ids:
            return 0.0
        result = await db.execute(
            select(func.count(func.distinct(Response.user_id))).where(
                and_(
                    Response.user_id.in_(member_ids),
                    Response.created_at >= since,
                )
            )
        )
        active_count = result.scalar() or 0
        return min((active_count / len(member_ids)) * 100, 100)

    async def _personality_balance(self, db: AsyncSession, member_ids: list) -> float:
        """How balanced are Big Five traits across the team?"""
        responses = await self._get_latest_responses(db, member_ids)
        if not responses:
            return 50.0  # Neutral default

        # Group by user, calculate average answer_value
        user_scores = {}
        for r in responses:
            uid = str(r.user_id)
            if uid not in user_scores:
                user_scores[uid] = []
            if r.answer_value is not None:
                user_scores[uid].append(r.answer_value)

        if len(user_scores) < 2:
            return 50.0

        # Calculate variance of average scores across members
        averages = [sum(v) / len(v) for v in user_scores.values() if v]
        if not averages:
            return 50.0

        mean = sum(averages) / len(averages)
        variance = sum((a - mean) ** 2 for a in averages) / len(averages)

        # Lower variance = more balanced (but some variance is healthy)
        # Optimal variance is moderate (0.5-2.0 on a 1-5 scale)
        balance = max(0, 100 - variance * 20)
        return min(balance, 100)

    async def _response_quality(
        self, db: AsyncSession, member_ids: list, since: datetime
    ) -> float:
        """Are people completing assessments fully (not rushing)?"""
        result = await db.execute(
            select(
                func.count(Response.id),
                func.avg(Response.response_time_ms),
                func.count(Response.answer_value),
            ).where(
                and_(
                    Response.user_id.in_(member_ids),
                    Response.created_at >= since,
                )
            )
        )
        row = result.one_or_none()
        if not row or not row[0]:
            return 50.0

        total, avg_time, answered = row
        completion_rate = (answered / total * 100) if total else 50
        # Reasonable response time: 2-30 seconds per item
        time_quality = (
            70
            if avg_time is None
            else min(100, max(0, 100 - abs(avg_time - 10000) / 500))
        )

        return completion_rate * 0.6 + time_quality * 0.4

    def _team_size_score(self, count: int) -> float:
        """Research suggests 5-9 is optimal team size."""
        if 5 <= count <= 9:
            return 95.0
        elif 3 <= count <= 12:
            return 75.0
        elif count < 3:
            return 40.0
        else:
            return max(30, 80 - (count - 12) * 3)

    async def _collaboration_trait_score(
        self, db: AsyncSession, member_ids: list
    ) -> float:
        """Average of agreeableness + extraversion as collaboration predictors."""
        agreeableness = await self._avg_trait(db, member_ids, "agreeableness")
        extraversion = await self._avg_trait(db, member_ids, "extraversion")
        return (agreeableness + extraversion) / 2

    async def _co_completion_rate(
        self, db: AsyncSession, member_ids: list, since: datetime
    ) -> float:
        """How many members complete the same assessments?"""
        if len(member_ids) < 2:
            return 50.0

        result = await db.execute(
            select(Response.assessment_id, func.count(func.distinct(Response.user_id)))
            .where(
                and_(
                    Response.user_id.in_(member_ids),
                    Response.created_at >= since,
                )
            )
            .group_by(Response.assessment_id)
        )
        rows = result.all()
        if not rows:
            return 0.0

        # What fraction of the team participates in each assessment?
        rates = [r[1] / len(member_ids) for r in rows]
        return min(sum(rates) / len(rates) * 100, 100)

    async def _response_consistency(
        self, db: AsyncSession, member_ids: list, since: datetime
    ) -> float:
        """How consistent are response patterns across team members?"""
        result = await db.execute(
            select(Response.user_id, func.count(Response.id))
            .where(
                and_(
                    Response.user_id.in_(member_ids),
                    Response.created_at >= since,
                )
            )
            .group_by(Response.user_id)
        )
        counts = [r[1] for r in result.all()]
        if len(counts) < 2:
            return 50.0

        mean = sum(counts) / len(counts)
        if mean == 0:
            return 0.0
        cv = (sum((c - mean) ** 2 for c in counts) / len(counts)) ** 0.5 / mean
        # Lower CV = more consistent = better
        return max(0, min(100, 100 - cv * 50))

    async def _avg_trait(
        self, db: AsyncSession, member_ids: list, trait_name: str
    ) -> float:
        """Get average normalized score for a Big Five trait (0-100 scale)."""
        responses = await self._get_latest_responses(db, member_ids)
        if not responses:
            return 50.0  # Neutral baseline

        # Use average answer_value as proxy (assessments use 1-5 scales)
        values = [r.answer_value for r in responses if r.answer_value is not None]
        if not values:
            return 50.0

        avg = sum(values) / len(values)
        # Normalize from 1-5 scale to 0-100
        return min(100, max(0, (avg - 1) / 4 * 100))

    async def _trait_diversity_bonus(self, db: AsyncSession, member_ids: list) -> float:
        """Teams with personality diversity that still function get a bonus."""
        responses = await self._get_latest_responses(db, member_ids)
        if not responses:
            return 50.0

        user_avgs = {}
        for r in responses:
            uid = str(r.user_id)
            if uid not in user_avgs:
                user_avgs[uid] = []
            if r.answer_value is not None:
                user_avgs[uid].append(r.answer_value)

        if len(user_avgs) < 2:
            return 50.0

        averages = [sum(v) / len(v) for v in user_avgs.values() if v]
        if len(averages) < 2:
            return 50.0

        # Standard deviation of averages
        mean = sum(averages) / len(averages)
        std = (sum((a - mean) ** 2 for a in averages) / len(averages)) ** 0.5

        # Moderate diversity is best (std around 0.5-1.0 on 1-5 scale)
        if 0.3 <= std <= 1.2:
            return 80.0
        elif std < 0.3:
            return 60.0  # Too homogeneous
        else:
            return 50.0  # Too fragmented

    def _retention_score(self, members: list) -> float:
        """Score based on team member tenure (higher tenure = stability)."""
        if not members:
            return 50.0
        # Use member created_at as proxy for tenure
        now = datetime.utcnow()
        tenures = []
        for m in members:
            if hasattr(m, "created_at") and m.created_at:
                days = (now - m.created_at.replace(tzinfo=None)).days
                tenures.append(days)
        if not tenures:
            return 50.0

        avg_tenure = sum(tenures) / len(tenures)
        # 180+ days average tenure is healthy
        return min(100, (avg_tenure / 180) * 80 + 20)

    async def _conflict_potential(self, db: AsyncSession, member_ids: list) -> float:
        """High neuroticism + low agreeableness = conflict risk."""
        neuroticism = await self._avg_trait(db, member_ids, "neuroticism")
        agreeableness = await self._avg_trait(db, member_ids, "agreeableness")
        # Higher neuroticism + lower agreeableness = more friction
        return max(0, min(100, neuroticism * 0.6 + (100 - agreeableness) * 0.4))

    async def _assessment_fatigue(
        self, db: AsyncSession, member_ids: list, since: datetime
    ) -> float:
        """Declining response rates indicate fatigue."""
        midpoint = since + (datetime.utcnow() - since) / 2

        result_first = await db.execute(
            select(func.count(Response.id)).where(
                and_(
                    Response.user_id.in_(member_ids),
                    Response.created_at >= since,
                    Response.created_at < midpoint,
                )
            )
        )
        result_second = await db.execute(
            select(func.count(Response.id)).where(
                and_(
                    Response.user_id.in_(member_ids),
                    Response.created_at >= midpoint,
                )
            )
        )
        first_half = result_first.scalar() or 0
        second_half = result_second.scalar() or 0

        if first_half == 0 and second_half == 0:
            return 30.0  # Low fatigue if no data
        if first_half == 0:
            return 10.0  # Increasing engagement

        decline_ratio = 1 - (second_half / max(first_half, 1))
        return max(0, min(100, decline_ratio * 100))

    async def _participation_inequality(
        self, db: AsyncSession, member_ids: list, since: datetime
    ) -> float:
        """Gini coefficient of participation (0=equal, 100=one person does everything)."""
        result = await db.execute(
            select(Response.user_id, func.count(Response.id))
            .where(
                and_(
                    Response.user_id.in_(member_ids),
                    Response.created_at >= since,
                )
            )
            .group_by(Response.user_id)
        )
        counts = sorted([r[1] for r in result.all()])

        # Include zero-participation members
        while len(counts) < len(member_ids):
            counts.insert(0, 0)

        n = len(counts)
        if n == 0 or sum(counts) == 0:
            return 30.0

        # Gini coefficient
        total = sum(counts)
        cum = 0
        gini_sum = 0
        for i, c in enumerate(counts):
            cum += c
            gini_sum += cum
        gini = (2 * gini_sum - total * (n + 1)) / (total * n)
        return max(0, min(100, gini * 100))

    async def _get_latest_responses(self, db: AsyncSession, member_ids: list) -> list:
        """Get recent assessment responses for a set of users."""
        result = await db.execute(
            select(Response)
            .where(Response.user_id.in_(member_ids))
            .order_by(Response.created_at.desc())
            .limit(500)
        )
        return result.scalars().all()

    async def _calculate_trend(
        self, db: AsyncSession, member_ids: list, metric: str, lookback_days: int
    ) -> Dict[str, Any]:
        """Simple trend: compare first half vs second half engagement."""
        now = datetime.utcnow()
        since = now - timedelta(days=lookback_days)
        mid = since + timedelta(days=lookback_days // 2)

        r1 = await db.execute(
            select(func.count(Response.id)).where(
                and_(
                    Response.user_id.in_(member_ids),
                    Response.created_at.between(since, mid),
                )
            )
        )
        r2 = await db.execute(
            select(func.count(Response.id)).where(
                and_(
                    Response.user_id.in_(member_ids),
                    Response.created_at.between(mid, now),
                )
            )
        )
        first = r1.scalar() or 0
        second = r2.scalar() or 0

        if first == 0 and second == 0:
            return {"direction": "stable", "change_pct": 0}
        if first == 0:
            return {"direction": "improving", "change_pct": 100}

        change = ((second - first) / first) * 100
        direction = (
            "improving" if change > 5 else ("declining" if change < -5 else "stable")
        )
        return {"direction": direction, "change_pct": round(change, 1)}

    # ── Labels ───────────────────────────────────────────────────────

    def _score_label(self, score: float) -> str:
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Needs Attention"
        elif score >= 20:
            return "At Risk"
        return "Critical"

    def _psych_safety_label(self, score: float) -> str:
        if score >= 80:
            return "High Safety"
        elif score >= 60:
            return "Moderate Safety"
        elif score >= 40:
            return "Low Safety"
        return "Unsafe Environment"

    def _readiness_label(self, score: float) -> str:
        if score >= 80:
            return "Highly Ready"
        elif score >= 60:
            return "Moderately Ready"
        elif score >= 40:
            return "Resistant"
        return "Not Ready"

    def _friction_label(self, score: float) -> str:
        if score <= 20:
            return "Smooth Operations"
        elif score <= 40:
            return "Minor Friction"
        elif score <= 60:
            return "Moderate Friction"
        elif score <= 80:
            return "High Friction"
        return "Critical Friction"

    def _empty_score(self, metric: str, reason: str) -> Dict[str, Any]:
        return {
            "score": 0.0,
            "label": "No Data",
            "trend": {"direction": "stable", "change_pct": 0},
            "factors": {},
            "recommendations": [reason],
        }

    # ── Recommendations ──────────────────────────────────────────────

    def _team_health_recommendations(self, engagement, balance, quality, size):
        recs = []
        if engagement < 50:
            recs.append(
                "Assessment participation is low. Consider shorter, more frequent pulse checks to boost engagement."
            )
        if balance < 40:
            recs.append(
                "Team personality composition is imbalanced. When hiring, consider candidates who complement existing personality profiles."
            )
        if quality < 50:
            recs.append(
                "Response quality suggests rushed assessments. Consider reducing assessment length or adding gamification."
            )
        if size < 50:
            recs.append(
                "Team size is outside the optimal 5-9 range. Research shows smaller cross-functional teams outperform larger ones."
            )
        if not recs:
            recs.append("Team health is strong. Maintain current practices.")
        return recs

    def _collaboration_recommendations(self, traits, co_completion, consistency):
        recs = []
        if co_completion < 40:
            recs.append(
                "Team members aren't completing assessments together. Schedule team assessment sessions to build shared understanding."
            )
        if traits < 50:
            recs.append(
                "Team collaboration traits are moderate. Consider team-building activities that strengthen interpersonal connections."
            )
        if consistency < 40:
            recs.append(
                "Uneven participation patterns detected. Some members may be disengaged — consider individual check-ins."
            )
        if not recs:
            recs.append("Collaboration signals are healthy. Team is well-aligned.")
        return recs

    def _manager_health_recommendations(
        self, engagement, burnout, productivity, retention
    ):
        recs = []
        if burnout < 40:
            recs.append(
                "Team shows elevated stress indicators. Manager should review workload distribution and ensure recovery time."
            )
        if engagement < 40:
            recs.append(
                "Low team engagement may indicate leadership disconnect. Schedule regular 1:1s and feedback sessions."
            )
        if retention < 50:
            recs.append(
                "Team tenure is low, suggesting retention challenges. Investigate exit patterns and satisfaction drivers."
            )
        if not recs:
            recs.append(
                "Manager effectiveness indicators are positive. Team shows healthy engagement and stability."
            )
        return recs

    def _psych_safety_recommendations(self, openness, agreeableness, stability):
        recs = []
        if openness < 50:
            recs.append(
                "Low openness suggests ideas may not be freely shared. Create structured forums for anonymous idea submission."
            )
        if agreeableness < 50:
            recs.append(
                "Interpersonal trust may be low. Consider facilitated team retrospectives focused on appreciative inquiry."
            )
        if stability < 40:
            recs.append(
                "Emotional volatility is elevated. Provide stress management resources and ensure workload is sustainable."
            )
        if not recs:
            recs.append(
                "Psychological safety is strong. Team members likely feel comfortable speaking up and taking risks."
            )
        return recs

    def _change_readiness_recommendations(
        self, openness, conscientiousness, resilience, extraversion
    ):
        recs = []
        if openness < 50:
            recs.append(
                "Team may resist new approaches. Introduce changes incrementally with clear rationale and early wins."
            )
        if resilience < 40:
            recs.append(
                "Low emotional resilience during change. Provide additional support structures and clear communication."
            )
        if conscientiousness < 50:
            recs.append(
                "Execution risk during transitions. Break changes into smaller, trackable milestones."
            )
        if not recs:
            recs.append(
                "Team is well-positioned for organizational change. Leverage their adaptability for transformation initiatives."
            )
        return recs

    def _friction_recommendations(self, conflict, fatigue, fragmentation):
        recs = []
        if conflict > 60:
            recs.append(
                "High personality conflict potential. Consider facilitated conflict resolution workshops or team mediation."
            )
        if fatigue > 60:
            recs.append(
                "Assessment fatigue detected — response rates are declining. Reduce assessment frequency or switch to micro-surveys."
            )
        if fragmentation > 60:
            recs.append(
                "Participation is uneven. Some members may be overwhelmed or disengaged. Investigate individual workload balance."
            )
        if not recs:
            recs.append(
                "Organizational friction is low. Operations are running smoothly."
            )
        return recs

    def _identify_top_risk(self, th, co, mh, ps, cr, fi) -> str:
        """Identify the most concerning metric for a team."""
        risks = [
            ("Team Health", th["score"], False),
            ("Collaboration", co["score"], False),
            ("Manager Health", mh["score"], False),
            ("Psychological Safety", ps["score"], False),
            ("Change Readiness", cr["score"], False),
            ("Organizational Friction", fi["score"], True),  # Higher is worse
        ]

        worst = None
        worst_severity = 0
        for name, score, higher_is_worse in risks:
            severity = score if higher_is_worse else (100 - score)
            if severity > worst_severity:
                worst_severity = severity
                worst = name

        return worst or "None"

    def _generate_executive_narrative(
        self, scores: Dict[str, float], teams: list
    ) -> str:
        """Generate executive-level intelligence narrative."""
        parts = []

        # Overall assessment
        avg_health = scores.get("team_health", 0)
        if avg_health >= 70:
            parts.append(f"Organization-wide team health is strong at {avg_health}%.")
        elif avg_health >= 50:
            parts.append(
                f"Organization-wide team health is moderate at {avg_health}%, with room for improvement."
            )
        else:
            parts.append(
                f"Organization-wide team health requires attention at {avg_health}%."
            )

        # Friction
        friction = scores.get("friction_index", 0)
        if friction > 50:
            parts.append(
                f"Organizational friction is elevated at {friction}%, which may be slowing delivery and increasing coordination overhead."
            )

        # Change readiness
        readiness = scores.get("change_readiness", 0)
        if readiness < 50:
            parts.append(
                f"Change readiness is low at {readiness}%. Major organizational changes should be introduced gradually with additional support."
            )

        # Psychological safety
        safety = scores.get("psychological_safety", 0)
        if safety < 50:
            parts.append(
                f"Psychological safety is concerning at {safety}%. Teams may not feel comfortable raising issues or proposing new ideas."
            )

        # At-risk teams
        at_risk = [t for t in teams if t["scores"]["team_health"] < 50]
        if at_risk:
            names = ", ".join(t["team_name"] for t in at_risk[:3])
            parts.append(f"Teams requiring immediate attention: {names}.")

        return (
            " ".join(parts)
            if parts
            else "Insufficient data to generate executive summary. Complete assessments across teams to enable behavioral intelligence."
        )
