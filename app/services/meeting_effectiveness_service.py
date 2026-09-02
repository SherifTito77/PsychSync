# app/services/meeting_effectiveness_service.py
"""
Meeting Effectiveness Service

Collects post-meeting micro-surveys and produces signals for BI:
- Team-level meeting effectiveness rate
- Organizer effectiveness (manager signal)
- Tag frequency analysis (why meetings fail)
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.meeting_effectiveness import MeetingRating

logger = logging.getLogger(__name__)


class MeetingEffectivenessService:
    """Manages meeting ratings and produces effectiveness signals."""

    async def submit_rating(
        self,
        db: AsyncSession,
        organization_id: UUID,
        rater_id: UUID,
        effectiveness_score: int,
        meeting_date: date,
        *,
        team_id: Optional[UUID] = None,
        meeting_subject: Optional[str] = None,
        organizer_id: Optional[UUID] = None,
        tags: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> MeetingRating:
        if not 1 <= effectiveness_score <= 5:
            raise ValueError("effectiveness_score must be 1-5")

        rating = MeetingRating(
            organization_id=organization_id,
            team_id=team_id,
            rater_id=rater_id,
            meeting_date=meeting_date,
            meeting_subject=meeting_subject,
            organizer_id=organizer_id,
            effectiveness_score=effectiveness_score,
            tags=tags,
            comment=comment,
        )
        db.add(rating)
        await db.flush()
        return rating

    async def get_org_summary(
        self,
        db: AsyncSession,
        organization_id: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """Org-wide meeting effectiveness summary."""
        cutoff = date.today() - timedelta(days=lookback_days)

        result = await db.execute(
            select(
                func.count(MeetingRating.id).label("total"),
                func.avg(MeetingRating.effectiveness_score).label("avg_score"),
            ).where(
                and_(
                    MeetingRating.organization_id == organization_id,
                    MeetingRating.meeting_date >= cutoff,
                )
            )
        )
        row = result.one()
        total = row.total or 0
        avg = float(row.avg_score) if row.avg_score else 0

        # Effectiveness rate: % of meetings rated 4 or 5
        effective_q = await db.execute(
            select(func.count())
            .select_from(MeetingRating)
            .where(
                and_(
                    MeetingRating.organization_id == organization_id,
                    MeetingRating.meeting_date >= cutoff,
                    MeetingRating.effectiveness_score >= 4,
                )
            )
        )
        effective_count = effective_q.scalar() or 0
        effectiveness_rate = round(effective_count / total * 100, 1) if total > 0 else 0

        # Tag frequency
        tag_freq = await self._tag_frequency(db, organization_id, cutoff)

        return {
            "total_ratings": total,
            "avg_score": round(avg, 2),
            "effectiveness_rate": effectiveness_rate,
            "lookback_days": lookback_days,
            "top_issues": tag_freq,
        }

    async def get_team_summary(
        self,
        db: AsyncSession,
        team_id: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """Team-level meeting effectiveness."""
        cutoff = date.today() - timedelta(days=lookback_days)

        result = await db.execute(
            select(
                func.count(MeetingRating.id).label("total"),
                func.avg(MeetingRating.effectiveness_score).label("avg_score"),
            ).where(
                and_(
                    MeetingRating.team_id == team_id,
                    MeetingRating.meeting_date >= cutoff,
                )
            )
        )
        row = result.one()
        total = row.total or 0
        avg = float(row.avg_score) if row.avg_score else 0

        effective_q = await db.execute(
            select(func.count())
            .select_from(MeetingRating)
            .where(
                and_(
                    MeetingRating.team_id == team_id,
                    MeetingRating.meeting_date >= cutoff,
                    MeetingRating.effectiveness_score >= 4,
                )
            )
        )
        effective_count = effective_q.scalar() or 0
        effectiveness_rate = round(effective_count / total * 100, 1) if total > 0 else 0

        return {
            "team_id": team_id,
            "total_ratings": total,
            "avg_score": round(avg, 2),
            "effectiveness_rate": effectiveness_rate,
        }

    async def get_organizer_effectiveness(
        self,
        db: AsyncSession,
        organizer_id: str,
        lookback_days: int = 90,
    ) -> Dict[str, Any]:
        """Effectiveness of meetings organized by a specific person (manager signal)."""
        cutoff = date.today() - timedelta(days=lookback_days)

        result = await db.execute(
            select(
                func.count(MeetingRating.id).label("total"),
                func.avg(MeetingRating.effectiveness_score).label("avg_score"),
            ).where(
                and_(
                    MeetingRating.organizer_id == organizer_id,
                    MeetingRating.meeting_date >= cutoff,
                )
            )
        )
        row = result.one()
        total = row.total or 0
        avg = float(row.avg_score) if row.avg_score else 0

        return {
            "organizer_id": organizer_id,
            "total_meetings_rated": total,
            "avg_score": round(avg, 2),
            "effectiveness_score_100": round((avg - 1) * 25, 1) if avg > 0 else 0,
        }

    async def get_meeting_signals(
        self,
        db: AsyncSession,
        organization_id: str,
        lookback_days: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """Export meeting effectiveness as BI enrichment signal."""
        summary = await self.get_org_summary(db, organization_id, lookback_days)
        if summary["total_ratings"] == 0:
            return None

        return {
            "meeting_effectiveness_rate": summary["effectiveness_rate"],
            "meeting_avg_score": summary["avg_score"],
            "meeting_avg_score_100": round((summary["avg_score"] - 1) * 25, 1),
            "total_ratings": summary["total_ratings"],
            "top_issues": summary["top_issues"],
        }

    async def _tag_frequency(
        self, db: AsyncSession, organization_id: str, cutoff: date
    ) -> List[Dict[str, Any]]:
        """Count tag occurrences across ratings."""
        result = await db.execute(
            select(MeetingRating.tags).where(
                and_(
                    MeetingRating.organization_id == organization_id,
                    MeetingRating.meeting_date >= cutoff,
                    MeetingRating.tags.isnot(None),
                )
            )
        )
        rows = result.scalars().all()

        tag_counts: Dict[str, int] = {}
        for tags_str in rows:
            if not tags_str:
                continue
            for tag in tags_str.split(","):
                tag = tag.strip()
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"tag": t, "count": c} for t, c in sorted_tags[:10]]


# Singleton
meeting_effectiveness_service = MeetingEffectivenessService()
