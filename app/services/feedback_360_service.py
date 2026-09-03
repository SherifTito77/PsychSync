# app/services/feedback_360_service.py
"""
360-Degree Feedback Service

Campaign management, response aggregation, blind spot detection,
and privacy-safe reporting (min raters per category).
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.feedback_360 import (
    FeedbackCompetency,
    FeedbackRequest,
    FeedbackResponse,
    FeedbackRound,
    FeedbackRoundStatus,
    RaterCategory,
)

logger = logging.getLogger(__name__)

# Default competencies if none configured
DEFAULT_COMPETENCIES = [
    {
        "name": "Communication",
        "category": "collaboration",
        "description": "Clarity, listening, written/verbal skills",
    },
    {
        "name": "Leadership",
        "category": "leadership",
        "description": "Vision, decision-making, empowerment",
    },
    {
        "name": "Collaboration",
        "category": "collaboration",
        "description": "Teamwork, cross-functional effectiveness",
    },
    {
        "name": "Execution",
        "category": "execution",
        "description": "Delivery, reliability, problem-solving",
    },
    {
        "name": "Growth Mindset",
        "category": "leadership",
        "description": "Learning, adaptability, feedback receptivity",
    },
    {
        "name": "Emotional Intelligence",
        "category": "communication",
        "description": "Empathy, self-awareness, conflict resolution",
    },
]


class Feedback360Service:
    """Manages 360-degree feedback campaigns."""

    # ------------------------------------------------------------------
    # Campaign management
    # ------------------------------------------------------------------

    async def create_round(
        self,
        db: AsyncSession,
        organization_id: UUID,
        name: str,
        created_by: UUID,
        competency_set: Optional[List[str]] = None,
        min_raters: int = 3,
    ) -> FeedbackRound:
        round_ = FeedbackRound(
            organization_id=organization_id,
            name=name,
            created_by=created_by,
            competency_set=competency_set or [c["name"] for c in DEFAULT_COMPETENCIES],
            min_raters_per_category=min_raters,
            status=FeedbackRoundStatus.DRAFT.value,
        )
        db.add(round_)
        await db.flush()
        return round_

    async def add_feedback_requests(
        self,
        db: AsyncSession,
        round_id: UUID,
        subject_id: UUID,
        raters: List[Dict[str, Any]],
    ) -> List[FeedbackRequest]:
        """Add rater assignments for a subject. Each rater dict: {rater_id, category}."""
        requests = []
        for r in raters:
            req = FeedbackRequest(
                round_id=round_id,
                subject_id=subject_id,
                rater_id=UUID(r["rater_id"]),
                rater_category=r["category"],
            )
            db.add(req)
            requests.append(req)
        await db.flush()
        return requests

    async def activate_round(
        self, db: AsyncSession, round_id: UUID
    ) -> Optional[FeedbackRound]:
        result = await db.execute(
            select(FeedbackRound).where(FeedbackRound.id == round_id)
        )
        round_ = result.scalar_one_or_none()
        if not round_:
            return None
        round_.status = FeedbackRoundStatus.ACTIVE.value
        round_.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return round_

    # ------------------------------------------------------------------
    # Response submission
    # ------------------------------------------------------------------

    async def submit_response(
        self,
        db: AsyncSession,
        request_id: UUID,
        competency_scores: Dict[str, float],
        open_ended: Optional[str] = None,
    ) -> Optional[FeedbackResponse]:
        result = await db.execute(
            select(FeedbackRequest).where(FeedbackRequest.id == request_id)
        )
        req = result.scalar_one_or_none()
        if not req or req.status == "completed":
            return None

        response = FeedbackResponse(
            request_id=request_id,
            round_id=req.round_id,
            subject_id=req.subject_id,
            rater_id=req.rater_id,
            rater_category=req.rater_category,
            competency_scores=competency_scores,
            open_ended=open_ended,
        )
        db.add(response)
        req.status = "completed"
        await db.flush()
        return response

    # ------------------------------------------------------------------
    # Aggregation & reporting
    # ------------------------------------------------------------------

    async def get_subject_report(
        self,
        db: AsyncSession,
        round_id: UUID,
        subject_id: UUID,
    ) -> Dict[str, Any]:
        """Aggregated 360 report for one subject, with privacy guard."""
        # Get the round config
        round_result = await db.execute(
            select(FeedbackRound).where(FeedbackRound.id == round_id)
        )
        round_ = round_result.scalar_one_or_none()
        if not round_:
            return {"error": "Round not found"}

        min_raters = round_.min_raters_per_category

        # Get all responses for this subject
        result = await db.execute(
            select(FeedbackResponse).where(
                and_(
                    FeedbackResponse.round_id == round_id,
                    FeedbackResponse.subject_id == subject_id,
                )
            )
        )
        responses = list(result.scalars().all())

        if not responses:
            return {
                "subject_id": str(subject_id),
                "round_id": str(round_id),
                "total_responses": 0,
                "by_category": {},
                "competency_summary": {},
            }

        # Group by rater category
        by_category: Dict[str, List[FeedbackResponse]] = {}
        for r in responses:
            by_category.setdefault(r.rater_category, []).append(r)

        # Aggregate per category (with privacy guard)
        category_summaries = {}
        for cat, cat_responses in by_category.items():
            if len(cat_responses) < min_raters:
                category_summaries[cat] = {
                    "response_count": len(cat_responses),
                    "suppressed": True,
                    "reason": f"Fewer than {min_raters} raters — results hidden for anonymity",
                }
                continue

            competency_avgs = self._aggregate_competencies(cat_responses)
            category_summaries[cat] = {
                "response_count": len(cat_responses),
                "suppressed": False,
                "competencies": competency_avgs,
            }

        # Overall competency summary (across all categories with enough responses)
        all_safe = [
            r for cat, rs in by_category.items() if len(rs) >= min_raters for r in rs
        ]
        overall = self._aggregate_competencies(all_safe) if all_safe else {}

        # Self-assessment comparison (blind spot detection)
        self_responses = by_category.get(RaterCategory.SELF.value, [])
        blind_spots = []
        if self_responses and overall:
            self_scores = self._aggregate_competencies(self_responses)
            blind_spots = self._detect_blind_spots(self_scores, overall)

        return {
            "subject_id": str(subject_id),
            "round_id": str(round_id),
            "total_responses": len(responses),
            "by_category": category_summaries,
            "competency_summary": overall,
            "blind_spots": blind_spots,
        }

    async def get_round_summary(
        self,
        db: AsyncSession,
        round_id: UUID,
    ) -> Dict[str, Any]:
        """Campaign-level summary: completion rates, subject count."""
        # Count requests and completed
        total_q = await db.execute(
            select(func.count())
            .select_from(FeedbackRequest)
            .where(FeedbackRequest.round_id == round_id)
        )
        total = total_q.scalar() or 0

        completed_q = await db.execute(
            select(func.count())
            .select_from(FeedbackRequest)
            .where(
                and_(
                    FeedbackRequest.round_id == round_id,
                    FeedbackRequest.status == "completed",
                )
            )
        )
        completed = completed_q.scalar() or 0

        subjects_q = await db.execute(
            select(func.count(func.distinct(FeedbackRequest.subject_id))).where(
                FeedbackRequest.round_id == round_id
            )
        )
        subject_count = subjects_q.scalar() or 0

        return {
            "round_id": str(round_id),
            "total_requests": total,
            "completed": completed,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "subject_count": subject_count,
        }

    # ------------------------------------------------------------------
    # Signal export for intelligence engines
    # ------------------------------------------------------------------

    async def get_feedback_signals(
        self,
        db: AsyncSession,
        organization_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Export 360 feedback signals for BI/Digital Twin integration."""
        # Get latest completed round
        result = await db.execute(
            select(FeedbackRound)
            .where(
                and_(
                    FeedbackRound.organization_id == organization_id,
                    FeedbackRound.status.in_(
                        [
                            FeedbackRoundStatus.CLOSED.value,
                            FeedbackRoundStatus.REPORTED.value,
                        ]
                    ),
                )
            )
            .order_by(FeedbackRound.updated_at.desc())
            .limit(1)
        )
        round_ = result.scalar_one_or_none()
        if not round_:
            return None

        # Get responses
        q = select(FeedbackResponse).where(FeedbackResponse.round_id == round_.id)
        if user_id:
            q = q.where(FeedbackResponse.subject_id == user_id)

        result = await db.execute(q)
        responses = list(result.scalars().all())
        if not responses:
            return None

        # Aggregate leadership and collaboration competency scores
        leadership_scores = []
        collaboration_scores = []
        all_scores = []

        for r in responses:
            scores = r.competency_scores or {}
            for comp, score in scores.items():
                all_scores.append(score)
                comp_lower = comp.lower()
                if "leader" in comp_lower or "decision" in comp_lower:
                    leadership_scores.append(score)
                if (
                    "collaborat" in comp_lower
                    or "team" in comp_lower
                    or "communicat" in comp_lower
                ):
                    collaboration_scores.append(score)

        # Convert 1-5 scale to 0-100
        def avg100(vals):
            return round((sum(vals) / len(vals) - 1) * 25, 1) if vals else None

        return {
            "round_id": str(round_.id),
            "response_count": len(responses),
            "leadership_score": avg100(leadership_scores),
            "collaboration_score": avg100(collaboration_scores),
            "overall_score": avg100(all_scores),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _aggregate_competencies(
        self, responses: List[FeedbackResponse]
    ) -> Dict[str, Dict[str, Any]]:
        """Average competency scores across responses."""
        comp_totals: Dict[str, List[float]] = {}
        for r in responses:
            for comp, score in (r.competency_scores or {}).items():
                comp_totals.setdefault(comp, []).append(score)

        return {
            comp: {
                "avg": round(sum(vals) / len(vals), 2),
                "min": round(min(vals), 1),
                "max": round(max(vals), 1),
                "count": len(vals),
            }
            for comp, vals in comp_totals.items()
        }

    def _detect_blind_spots(
        self,
        self_scores: Dict[str, Dict],
        others_scores: Dict[str, Dict],
    ) -> List[Dict[str, Any]]:
        """Find competencies where self-assessment diverges from others."""
        blind_spots = []
        for comp, self_data in self_scores.items():
            others_data = others_scores.get(comp)
            if not others_data:
                continue

            self_avg = self_data["avg"]
            others_avg = others_data["avg"]
            gap = self_avg - others_avg

            if abs(gap) >= 0.75:  # Significant gap on 1-5 scale
                blind_spots.append(
                    {
                        "competency": comp,
                        "self_score": self_avg,
                        "others_score": others_avg,
                        "gap": round(gap, 2),
                        "type": "overestimate" if gap > 0 else "underestimate",
                        "insight": (
                            f"You rate yourself {abs(gap):.1f} points {'higher' if gap > 0 else 'lower'} "
                            f"than others on {comp}."
                        ),
                    }
                )

        blind_spots.sort(key=lambda b: abs(b["gap"]), reverse=True)
        return blind_spots


# Singleton
feedback_360_service = Feedback360Service()
