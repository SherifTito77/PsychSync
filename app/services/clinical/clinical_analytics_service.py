"""
Clinical Screening Analytics Service

Tracks screening completion rates, severity distributions, and population health trends.
Provides dashboards for clinicians and administrators to monitor mental health metrics.

DESIGN DECISIONS:
- Eligibility: All active users in organization (created within time period, not deleted)
- Repeat Screenings: Count all screenings for trend tracking, plus unique user counts
- Time Granularity: Weekly aggregation (balanced detail and stability)
- Partial Completions: Only count completed screenings (completed_at IS NOT NULL)
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, case, func, literal_column, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class ClinicalScreeningAnalytics:
    """
    Analytics service for clinical screening data

    Provides:
    - Screening completion rates
    - Severity distribution analysis
    - Risk trend monitoring
    - Population health insights
    - Clinician workload metrics
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_screening_completion_stats(
        self,
        org_id: str,
        start_date: datetime,
        end_date: datetime,
        screening_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get screening completion statistics for an organization

        DESIGN DECISIONS:
        - Eligibility: Active users (created within period, not deleted)
        - Counts all screenings (including repeats) + unique users for reach
        - Weekly granularity for trends
        - Only completed screenings (completed_at IS NOT NULL)

        Returns:
            - total_eligible: number of users eligible for screening
            - total_completed: number of screenings completed
            - unique_users_completed: number of unique users who completed at least one screening
            - completion_rate: percentage of eligible users who completed
            - by_screening_type: breakdown by screening type (PHQ9, GAD7, etc.)
            - by_team: completion rates by team
            - trend_over_time: weekly completion rates
        """
        from app.db.models.clinical_screening import ClinicalScreening
        from app.db.models.team import Team
        from app.db.models.user import User

        # Base query for eligible users (active, not deleted, in organization)
        eligible_query = select(func.count(User.id)).where(
            and_(
                User.org_id == org_id,
                User.created_at <= end_date,
                User.deleted_at.is_(None),
            )
        )

        total_eligible_result = await self.db.execute(eligible_query)
        total_eligible = total_eligible_result.scalar() or 0

        # Base query for completed screenings
        screening_base = select(ClinicalScreening).where(
            and_(
                ClinicalScreening.org_id == org_id,
                ClinicalScreening.completed_at >= start_date,
                ClinicalScreening.completed_at <= end_date,
                ClinicalScreening.completed_at.isnot(None),
                ClinicalScreening.deleted_at.is_(None),
            )
        )

        # Apply screening type filter if specified
        if screening_type:
            screening_base = screening_base.where(
                ClinicalScreening.screening_type == screening_type
            )

        # Total completed screenings (including repeats)
        total_completed_query = select(func.count()).select_from(screening_base)
        total_completed_result = await self.db.execute(total_completed_query)
        total_completed = total_completed_result.scalar() or 0

        # Unique users who completed screenings
        unique_users_query = select(
            func.count(func.distinct(ClinicalScreening.user_id))
        ).select_from(screening_base)
        unique_users_result = await self.db.execute(unique_users_query)
        unique_users_completed = unique_users_result.scalar() or 0

        # Calculate completion rate
        completion_rate = round(
            (
                (unique_users_completed / total_eligible * 100)
                if total_eligible > 0
                else 0
            ),
            2,
        )

        # Breakdown by screening type
        by_type_query = (
            select(
                ClinicalScreening.screening_type,
                func.count(ClinicalScreening.id).label("count"),
                func.count(func.distinct(ClinicalScreening.user_id)).label(
                    "unique_users"
                ),
            )
            .where(
                and_(
                    ClinicalScreening.org_id == org_id,
                    ClinicalScreening.completed_at >= start_date,
                    ClinicalScreening.completed_at <= end_date,
                    ClinicalScreening.completed_at.isnot(None),
                    ClinicalScreening.deleted_at.is_(None),
                )
            )
            .group_by(ClinicalScreening.screening_type)
        )

        by_type_result = await self.db.execute(by_type_query)
        by_screening_type = {
            row.screening_type: {
                "total_screenings": row.count,
                "unique_users": row.unique_users,
                "percentage": round(
                    (
                        (row.unique_users / total_eligible * 100)
                        if total_eligible > 0
                        else 0
                    ),
                    2,
                ),
            }
            for row in by_type_result
        }

        # Weekly trend data
        # Using PostgreSQL's date_trunc for weekly aggregation
        weekly_trend_query = (
            select(
                func.date_trunc("week", ClinicalScreening.completed_at).label("week"),
                func.count(ClinicalScreening.id).label("count"),
                func.count(func.distinct(ClinicalScreening.user_id)).label(
                    "unique_users"
                ),
            )
            .where(
                and_(
                    ClinicalScreening.org_id == org_id,
                    ClinicalScreening.completed_at >= start_date,
                    ClinicalScreening.completed_at <= end_date,
                    ClinicalScreening.completed_at.isnot(None),
                    ClinicalScreening.deleted_at.is_(None),
                )
            )
            .group_by(func.date_trunc("week", ClinicalScreening.completed_at))
            .order_by(func.date_trunc("week", ClinicalScreening.completed_at))
        )

        if screening_type:
            weekly_trend_query = weekly_trend_query.where(
                ClinicalScreening.screening_type == screening_type
            )

        weekly_trend_result = await self.db.execute(weekly_trend_query)
        trend_over_time = [
            {
                "week": row.week.isoformat(),
                "total_screenings": row.count,
                "unique_users": row.unique_users,
                "completion_rate": round(
                    (
                        (row.unique_users / total_eligible * 100)
                        if total_eligible > 0
                        else 0
                    ),
                    2,
                ),
            }
            for row in weekly_trend_result
        ]

        # Team-level completion rates
        # Join with team membership (assuming User has team_id)
        by_team_query = (
            select(
                User.team_id,
                func.count(func.distinct(User.id)).label("team_size"),
                func.count(func.distinct(ClinicalScreening.user_id)).label(
                    "completed_users"
                ),
            )
            .select_from(
                User.join(ClinicalScreening, User.id == ClinicalScreening.user_id)
            )
            .where(
                and_(
                    User.org_id == org_id,
                    User.deleted_at.is_(None),
                    ClinicalScreening.completed_at >= start_date,
                    ClinicalScreening.completed_at <= end_date,
                    ClinicalScreening.completed_at.isnot(None),
                    ClinicalScreening.deleted_at.is_(None),
                )
            )
            .group_by(User.team_id)
        )

        if screening_type:
            by_team_query = by_team_query.where(
                ClinicalScreening.screening_type == screening_type
            )

        by_team_result = await self.db.execute(by_team_query)
        by_team = [
            {
                "team_id": str(row.team_id) if row.team_id else "unassigned",
                "team_size": row.team_size,
                "completed_users": row.completed_users,
                "completion_rate": round(
                    (
                        (row.completed_users / row.team_size * 100)
                        if row.team_size > 0
                        else 0
                    ),
                    2,
                ),
            }
            for row in by_team_result
        ]

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "screening_type": screening_type,
            },
            "total_eligible": total_eligible,
            "total_completed": total_completed,
            "unique_users_completed": unique_users_completed,
            "completion_rate": completion_rate,
            "by_screening_type": by_screening_type,
            "by_team": by_team,
            "trend_over_time": trend_over_time,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def get_severity_distribution(
        self,
        org_id: str,
        start_date: datetime,
        end_date: datetime,
        screening_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get distribution of severity levels for completed screenings

        DESIGN DECISIONS:
        - Severity Normalization: Map tool-specific levels to universal scale
        - Repeat Screenings: Include all to track severity changes
        - High-Risk Threshold: Count 'high' and 'critical' risk levels
        - Weekly Trends: Aggregate severity over time

        Returns:
            - severity_counts: count per severity level
            - severity_percentages: percentage distribution
            - by_screening_type: severity breakdown per tool
            - high_risk_count: screenings with high/critical risk
            - trends: weekly severity distribution
        """
        from app.db.models.clinical_screening import ClinicalScreening

        # Base query for screenings
        query = select(ClinicalScreening).where(
            and_(
                ClinicalScreening.org_id == org_id,
                ClinicalScreening.completed_at >= start_date,
                ClinicalScreening.completed_at <= end_date,
                ClinicalScreening.completed_at.isnot(None),
                ClinicalScreening.deleted_at.is_(None),
            )
        )

        if screening_type:
            query = query.where(ClinicalScreening.screening_type == screening_type)

        # Severity counts
        severity_query = (
            select(
                ClinicalScreening.severity_level,
                func.count(ClinicalScreening.id).label("count"),
            )
            .where(
                and_(
                    ClinicalScreening.org_id == org_id,
                    ClinicalScreening.completed_at >= start_date,
                    ClinicalScreening.completed_at <= end_date,
                    ClinicalScreening.completed_at.isnot(None),
                    ClinicalScreening.deleted_at.is_(None),
                )
            )
            .group_by(ClinicalScreening.severity_level)
        )

        if screening_type:
            severity_query = severity_query.where(
                ClinicalScreening.screening_type == screening_type
            )

        severity_result = await self.db.execute(severity_query)
        severity_rows = severity_result.fetchall()

        total_screenings = sum(row.count for row in severity_rows)

        severity_counts = {row.severity_level: row.count for row in severity_rows}
        severity_percentages = {
            level: round(
                (count / total_screenings * 100) if total_screenings > 0 else 0, 2
            )
            for level, count in severity_counts.items()
        }

        # Breakdown by screening type
        by_type_query = (
            select(
                ClinicalScreening.screening_type,
                ClinicalScreening.severity_level,
                func.count(ClinicalScreening.id).label("count"),
            )
            .where(
                and_(
                    ClinicalScreening.org_id == org_id,
                    ClinicalScreening.completed_at >= start_date,
                    ClinicalScreening.completed_at <= end_date,
                    ClinicalScreening.completed_at.isnot(None),
                    ClinicalScreening.deleted_at.is_(None),
                )
            )
            .group_by(
                ClinicalScreening.screening_type, ClinicalScreening.severity_level
            )
        )

        by_type_result = await self.db.execute(by_type_query)
        by_screening_type = {}
        for row in by_type_result.fetchall():
            if row.screening_type not in by_screening_type:
                by_screening_type[row.screening_type] = {}
            by_screening_type[row.screening_type][row.severity_level] = row.count

        # High-risk count (high + critical risk levels)
        high_risk_query = select(func.count(ClinicalScreening.id)).where(
            and_(
                ClinicalScreening.org_id == org_id,
                ClinicalScreening.completed_at >= start_date,
                ClinicalScreening.completed_at <= end_date,
                ClinicalScreening.completed_at.isnot(None),
                ClinicalScreening.deleted_at.is_(None),
                ClinicalScreening.risk_level.in_(["high", "critical"]),
            )
        )

        if screening_type:
            high_risk_query = high_risk_query.where(
                ClinicalScreening.screening_type == screening_type
            )

        high_risk_result = await self.db.execute(high_risk_query)
        high_risk_count = high_risk_result.scalar() or 0

        # Weekly trends
        weekly_trend_query = (
            select(
                func.date_trunc("week", ClinicalScreening.completed_at).label("week"),
                ClinicalScreening.severity_level,
                func.count(ClinicalScreening.id).label("count"),
            )
            .where(
                and_(
                    ClinicalScreening.org_id == org_id,
                    ClinicalScreening.completed_at >= start_date,
                    ClinicalScreening.completed_at <= end_date,
                    ClinicalScreening.completed_at.isnot(None),
                    ClinicalScreening.deleted_at.is_(None),
                )
            )
            .group_by(
                func.date_trunc("week", ClinicalScreening.completed_at),
                ClinicalScreening.severity_level,
            )
            .order_by(func.date_trunc("week", ClinicalScreening.completed_at))
        )

        if screening_type:
            weekly_trend_query = weekly_trend_query.where(
                ClinicalScreening.screening_type == screening_type
            )

        weekly_trend_result = await self.db.execute(weekly_trend_query)
        trends = {}
        for row in weekly_trend_result.fetchall():
            week_str = row.week.isoformat()
            if week_str not in trends:
                trends[week_str] = {}
            trends[week_str][row.severity_level] = row.count

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "screening_type": screening_type,
            },
            "severity_counts": severity_counts,
            "severity_percentages": severity_percentages,
            "total_screenings": total_screenings,
            "by_screening_type": by_screening_type,
            "high_risk_count": high_risk_count,
            "trends": trends,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def get_crisis_alert_metrics(
        self, org_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get crisis alert metrics and response times

        DESIGN DECISIONS:
        - Response Time: Time from alert creation to first acknowledgment
        - Resolution: acknowledged AND resolved_at IS NOT NULL
        - Escalation: Track alerts escalated to higher levels
        - Response Types: Aggregate all response types together

        Returns:
            - total_alerts: number of crisis alerts triggered
            - alerts_by_type: breakdown by alert type
            - average_response_time: time from alert to acknowledgment
            - resolution_rate: percentage of resolved alerts
            - pending_alerts: number of unresolved alerts
        """
        from app.db.models.clinical_screening import ClinicalAlert

        # Total alerts in period
        total_query = select(func.count(ClinicalAlert.id)).where(
            and_(
                ClinicalAlert.org_id == org_id,
                ClinicalAlert.created_at >= start_date,
                ClinicalAlert.created_at <= end_date,
            )
        )

        total_result = await self.db.execute(total_query)
        total_alerts = total_result.scalar() or 0

        # Breakdown by type
        by_type_query = (
            select(
                ClinicalAlert.alert_type, func.count(ClinicalAlert.id).label("count")
            )
            .where(
                and_(
                    ClinicalAlert.org_id == org_id,
                    ClinicalAlert.created_at >= start_date,
                    ClinicalAlert.created_at <= end_date,
                )
            )
            .group_by(ClinicalAlert.alert_type)
        )

        by_type_result = await self.db.execute(by_type_query)
        alerts_by_type = {
            row.alert_type: row.count for row in by_type_result.fetchall()
        }

        # Average response time (created to acknowledged)
        response_time_query = select(
            func.avg(
                func.extract("epoch", ClinicalAlert.acknowledged_at)
                - func.extract("epoch", ClinicalAlert.created_at)
            ).label("avg_seconds")
        ).where(
            and_(
                ClinicalAlert.org_id == org_id,
                ClinicalAlert.created_at >= start_date,
                ClinicalAlert.created_at <= end_date,
                ClinicalAlert.acknowledged_at.isnot(None),
            )
        )

        response_time_result = await self.db.execute(response_time_query)
        avg_seconds = response_time_result.scalar()
        average_response_time = (
            round(avg_seconds / 60, 2) if avg_seconds else None
        )  # Convert to minutes

        # Resolution rate (resolved_at IS NOT NULL)
        resolved_query = select(func.count(ClinicalAlert.id)).where(
            and_(
                ClinicalAlert.org_id == org_id,
                ClinicalAlert.created_at >= start_date,
                ClinicalAlert.created_at <= end_date,
                ClinicalAlert.resolved_at.isnot(None),
            )
        )

        resolved_result = await self.db.execute(resolved_query)
        resolved_count = resolved_result.scalar() or 0
        resolution_rate = round(
            (resolved_count / total_alerts * 100) if total_alerts > 0 else 0, 2
        )

        # Pending alerts (created but not resolved)
        pending_query = select(func.count(ClinicalAlert.id)).where(
            and_(
                ClinicalAlert.org_id == org_id,
                ClinicalAlert.created_at >= start_date,
                ClinicalAlert.created_at <= end_date,
                ClinicalAlert.resolved_at.is_(None),
            )
        )

        pending_result = await self.db.execute(pending_query)
        pending_alerts = pending_result.scalar() or 0

        # Escalation metrics
        escalated_query = select(func.count(ClinicalAlert.id)).where(
            and_(
                ClinicalAlert.org_id == org_id,
                ClinicalAlert.created_at >= start_date,
                ClinicalAlert.created_at <= end_date,
                ClinicalAlert.escalated == True,
            )
        )

        escalated_result = await self.db.execute(escalated_query)
        escalated_count = escalated_result.scalar() or 0

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "total_alerts": total_alerts,
            "alerts_by_type": alerts_by_type,
            "average_response_time_minutes": average_response_time,
            "resolution_rate": resolution_rate,
            "resolved_count": resolved_count,
            "pending_alerts": pending_alerts,
            "escalated_count": escalated_count,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def get_population_health_summary(
        self, org_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get population-level mental health summary

        DESIGN DECISIONS:
        - Score Aggregation: Average scores per screening type (not across types)
        - Risk Distribution: Percentage breakdown of risk levels
        - Top Concerns: Most common high-risk categories
        - Improvement: Compare first vs last month scores
        - Privacy: No individual user data, only aggregates

        Returns:
            - average_scores: mean scores per screening type
            - risk_distribution: percentage of each risk level
            - top_concerns: most frequent high-risk flags
            - improvement_indicators: score changes over time
            - risk_factors: patterns by team or demographic
        """
        from app.db.models.clinical_screening import ClinicalScreening

        # Average scores per screening type
        avg_scores_query = (
            select(
                ClinicalScreening.screening_type,
                func.avg(ClinicalScreening.total_score).label("avg_score"),
                func.count(ClinicalScreening.id).label("count"),
            )
            .where(
                and_(
                    ClinicalScreening.org_id == org_id,
                    ClinicalScreening.completed_at >= start_date,
                    ClinicalScreening.completed_at <= end_date,
                    ClinicalScreening.completed_at.isnot(None),
                    ClinicalScreening.deleted_at.is_(None),
                )
            )
            .group_by(ClinicalScreening.screening_type)
        )

        avg_scores_result = await self.db.execute(avg_scores_query)
        average_scores = {
            row.screening_type: {
                "average_score": round(float(row.avg_score), 2) if row.avg_score else 0,
                "screening_count": row.count,
            }
            for row in avg_scores_result.fetchall()
        }

        # Risk distribution
        risk_query = (
            select(
                ClinicalScreening.risk_level,
                func.count(ClinicalScreening.id).label("count"),
            )
            .where(
                and_(
                    ClinicalScreening.org_id == org_id,
                    ClinicalScreening.completed_at >= start_date,
                    ClinicalScreening.completed_at <= end_date,
                    ClinicalScreening.completed_at.isnot(None),
                    ClinicalScreening.deleted_at.is_(None),
                )
            )
            .group_by(ClinicalScreening.risk_level)
        )

        risk_result = await self.db.execute(risk_query)
        risk_rows = risk_result.fetchall()
        total_count = sum(row.count for row in risk_rows)

        risk_distribution = {
            row.risk_level: {
                "count": row.count,
                "percentage": round(
                    (row.count / total_count * 100) if total_count > 0 else 0, 2
                ),
            }
            for row in risk_rows
        }

        # Top concerns (high-risk flags)
        # Extract risk flags from JSONB and count occurrences
        screenings_with_flags = select(ClinicalScreening).where(
            and_(
                ClinicalScreening.org_id == org_id,
                ClinicalScreening.completed_at >= start_date,
                ClinicalScreening.completed_at <= end_date,
                ClinicalScreening.completed_at.isnot(None),
                ClinicalScreening.deleted_at.is_(None),
                ClinicalScreening.risk_flags.isnot(None),
            )
        )

        screenings_result = await self.db.execute(screenings_with_flags)
        screenings = screenings_result.scalars().all()

        flag_counts = {}
        for screening in screenings:
            if screening.risk_flags:
                for flag in screening.risk_flags:
                    flag_counts[flag] = flag_counts.get(flag, 0) + 1

        # Sort and get top 10
        top_concerns = sorted(flag_counts.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]
        top_concerns_dict = [{flag: count} for flag, count in top_concerns]

        # Team-level risk factors (completion rates and risk levels by team)
        # This is simplified - could be expanded
        team_risk_query = (
            select(
                User.team_id,
                ClinicalScreening.risk_level,
                func.count(ClinicalScreening.id).label("count"),
            )
            .select_from(
                User.join(ClinicalScreening, User.id == ClinicalScreening.user_id)
            )
            .where(
                and_(
                    User.org_id == org_id,
                    ClinicalScreening.completed_at >= start_date,
                    ClinicalScreening.completed_at <= end_date,
                    ClinicalScreening.completed_at.isnot(None),
                    ClinicalScreening.deleted_at.is_(None),
                )
            )
            .group_by(User.team_id, ClinicalScreening.risk_level)
        )

        team_risk_result = await self.db.execute(team_risk_query)
        risk_factors = []
        for row in team_risk_result.fetchall():
            team_id = str(row.team_id) if row.team_id else "unassigned"
            risk_factors.append(
                {"team_id": team_id, "risk_level": row.risk_level, "count": row.count}
            )

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "average_scores": average_scores,
            "risk_distribution": risk_distribution,
            "total_screenings": total_count,
            "top_concerns": top_concerns_dict,
            "risk_factors_by_team": risk_factors,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def get_clinician_workload_metrics(
        self, org_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get clinician workload and productivity metrics

        DESIGN DECISIONS:
        - Reviewed: validated_by IS NOT NULL (clinician reviewed screening)
        - Review Time: completed_at to validated_at (if available)
        - Patient Load: Count of unique users with screenings reviewed by clinician
        - Productivity: Screenings reviewed per clinician

        Returns:
            - screenings_reviewed: number of screenings reviewed per clinician
            - average_review_time: time taken to review screenings
            - alert_responses: alert response statistics
            - patient_load: number of unique patients seen
            - clinician_productivity: productivity metrics per clinician
        """
        from app.db.models.clinical_screening import ClinicalAlert, ClinicalScreening
        from app.db.models.user import User as UserModel

        # Screenings reviewed (validated_by IS NOT NULL)
        reviewed_query = (
            select(
                ClinicalScreening.validated_by,
                func.count(ClinicalScreening.id).label("count"),
                func.count(func.distinct(ClinicalScreening.user_id)).label(
                    "unique_patients"
                ),
            )
            .where(
                and_(
                    ClinicalScreening.org_id == org_id,
                    ClinicalScreening.completed_at >= start_date,
                    ClinicalScreening.completed_at <= end_date,
                    ClinicalScreening.validated_by.isnot(None),
                    ClinicalScreening.deleted_at.is_(None),
                )
            )
            .group_by(ClinicalScreening.validated_by)
        )

        reviewed_result = await self.db.execute(reviewed_query)
        screenings_reviewed = []
        total_reviewed = 0
        total_patients = 0

        for row in reviewed_result.fetchall():
            clinician_id = str(row.validated_by) if row.validated_by else "unknown"
            screenings_reviewed.append(
                {
                    "clinician_id": clinician_id,
                    "screenings_reviewed": row.count,
                    "unique_patients": row.unique_patients,
                }
            )
            total_reviewed += row.count
            total_patients += row.unique_patients

        # Average review time (completed_at to validated_at)
        review_time_query = select(
            func.avg(
                func.extract("epoch", ClinicalScreening.validated_at)
                - func.extract("epoch", ClinicalScreening.completed_at)
            ).label("avg_seconds")
        ).where(
            and_(
                ClinicalScreening.org_id == org_id,
                ClinicalScreening.completed_at >= start_date,
                ClinicalScreening.completed_at <= end_date,
                ClinicalScreening.validated_at.isnot(None),
                ClinicalScreening.deleted_at.is_(None),
            )
        )

        review_time_result = await self.db.execute(review_time_query)
        avg_seconds = review_time_result.scalar()
        average_review_time_hours = (
            round((avg_seconds / 3600), 2) if avg_seconds else None
        )  # Convert to hours

        # Alert response statistics
        alert_responses_query = (
            select(
                ClinicalAlert.acknowledged_by,
                func.count(ClinicalAlert.id).label("count"),
                func.count(ClinicalAlert.id)
                .filter(ClinicalAlert.resolved_at.isnot(None))
                .label("resolved"),
            )
            .where(
                and_(
                    ClinicalAlert.org_id == org_id,
                    ClinicalAlert.created_at >= start_date,
                    ClinicalAlert.created_at <= end_date,
                    ClinicalAlert.acknowledged_by.isnot(None),
                )
            )
            .group_by(ClinicalAlert.acknowledged_by)
        )

        alert_responses_result = await self.db.execute(alert_responses_query)
        alert_responses = []
        total_alerts_responded = 0
        total_resolved = 0

        for row in alert_responses_result.fetchall():
            responder_id = (
                str(row.acknowledged_by) if row.acknowledged_by else "unknown"
            )
            alert_responses.append(
                {
                    "responder_id": responder_id,
                    "alerts_responded": row.count,
                    "alerts_resolved": row.resolved,
                }
            )
            total_alerts_responded += row.count
            total_resolved += row.resolved

        # Get clinician names
        clinician_ids = list(
            set(
                [
                    item["clinician_id"]
                    for item in screenings_reviewed
                    if item["clinician_id"] != "unknown"
                ]
                + [
                    item["responder_id"]
                    for item in alert_responses
                    if item["responder_id"] != "unknown"
                ]
            )
        )

        clinician_names = {}
        if clinician_ids:
            clinician_query = select(UserModel.id, UserModel.full_name).where(
                UserModel.id.in_(clinician_ids)
            )
            clinician_result = await self.db.execute(clinician_query)
            clinician_names = {
                str(row.id): row.full_name for row in clinician_result.fetchall()
            }

        # Add names to results
        for item in screenings_reviewed:
            item["clinician_name"] = clinician_names.get(
                item["clinician_id"], "Unknown Clinician"
            )

        for item in alert_responses:
            item["responder_name"] = clinician_names.get(
                item["responder_id"], "Unknown Clinician"
            )

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "total_screenings_reviewed": total_reviewed,
            "total_unique_patients": total_patients,
            "screenings_reviewed": screenings_reviewed,
            "average_review_time_hours": average_review_time_hours,
            "total_alerts_responded": total_alerts_responded,
            "total_alerts_resolved": total_resolved,
            "alert_responses": alert_responses,
            "generated_at": datetime.utcnow().isoformat(),
        }
