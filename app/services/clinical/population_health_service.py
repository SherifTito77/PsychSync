"""
Population Health Analytics Service

Provides aggregated clinical analytics across user populations:
- Aggregate risk scores
- High-risk user identification
- Treatment outcome tracking
- Geographic/demographic breakdowns
- Trend visualization over time

Designed for clinicians, administrators, and researchers.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, text
from sqlalchemy.orm import aliased

from app.db.models.clinical_extended import ClinicalAssessmentExtended
from app.core.logging_config import logger

# =============================================================================
# Data Models for Population Analytics
# =============================================================================


class PopulationMetrics:
    """Container for population-level metrics"""

    def __init__(
        self,
        total_users: int,
        active_assessments: int,
        average_scores: Dict[str, float],
        risk_distribution: Dict[str, int],
        crisis_count: int,
        high_risk_count: int,
        moderate_risk_count: int,
        low_risk_count: int,
    ):
        self.total_users = total_users
        self.active_assessments = active_assessments
        self.average_scores = average_scores
        self.risk_distribution = risk_distribution
        self.crisis_count = crisis_count
        self.high_risk_count = high_risk_count
        self.moderate_risk_count = moderate_risk_count
        self.low_risk_count = low_risk_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_users": self.total_users,
            "active_assessments": self.active_assessments,
            "average_scores": self.average_scores,
            "risk_distribution": self.risk_distribution,
            "crisis_count": self.crisis_count,
            "high_risk_count": self.high_risk_count,
            "moderate_risk_count": self.moderate_risk_count,
            "low_risk_count": self.low_risk_count,
        }


class HighRiskUser:
    """Represents a high-risk user requiring attention"""

    def __init__(
        self,
        user_id: str,
        risk_level: str,
        prediction_type: str,
        current_score: float,
        trend: str,
        last_assessment: datetime,
        factors: Dict[str, Any],
    ):
        self.user_id = user_id
        self.risk_level = risk_level
        self.prediction_type = prediction_type
        self.current_score = current_score
        self.trend = trend
        self.last_assessment = last_assessment
        self.factors = factors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "user_id": self.user_id,
            "risk_level": self.risk_level,
            "prediction_type": self.prediction_type,
            "current_score": float(self.current_score),
            "trend": self.trend,
            "last_assessment": self.last_assessment.isoformat(),
            "factors": self.factors,
        }


class TreatmentOutcome:
    """Treatment outcome statistics"""

    def __init__(
        self,
        outcome_type: str,
        count: int,
        percentage: float,
        avg_score_change: Optional[float] = None,
    ):
        self.outcome_type = outcome_type
        self.count = count
        self.percentage = percentage
        self.avg_score_change = avg_score_change

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "outcome_type": self.outcome_type,
            "count": self.count,
            "percentage": round(self.percentage, 2),
            "avg_score_change": round(self.avg_score_change, 2) if self.avg_score_change else None,
        }


class TimeSeriesData:
    """Time series data for trend visualization"""

    def __init__(
        self,
        period: str,
        avg_score: float,
        assessment_count: int,
        high_risk_count: int,
        crisis_count: int,
    ):
        self.period = period
        self.avg_score = avg_score
        self.assessment_count = assessment_count
        self.high_risk_count = high_risk_count
        self.crisis_count = crisis_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "period": self.period,
            "avg_score": round(self.avg_score, 2),
            "assessment_count": self.assessment_count,
            "high_risk_count": self.high_risk_count,
            "crisis_count": self.crisis_count,
        }


# =============================================================================
# Population Health Service
# =============================================================================


class PopulationHealthService:
    """
    Population Health Analytics Service

    Provides aggregated analytics for:
    - Clinicians monitoring patient populations
    - Administrators tracking program outcomes
    - Researchers analyzing clinical data
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)

    # ========================================================================
    # Overall Population Metrics
    # ========================================================================

    async def get_population_metrics(
        self,
        assessment_types: Optional[List[str]] = None,
        days_back: int = 30,
    ) -> PopulationMetrics:
        """
        Get aggregate population metrics

        Args:
            assessment_types: Filter by assessment types (None = all)
            days_back: Lookback period in days

        Returns:
            PopulationMetrics with aggregate statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Default to all clinical assessment types
            if assessment_types is None:
                assessment_types = ["BDI2", "BAI", "GAD7", "PHQ9", "LSAS", "EAT26", "YBOCS"]

            # Build query
            query = (
                select(ClinicalAssessmentExtended)
                .where(
                    and_(
                        ClinicalAssessmentExtended.assessment_type.in_(assessment_types),
                        ClinicalAssessmentExtended.completed_at >= cutoff_date,
                    )
                )
            )

            result = await self.db.execute(query)
            assessments = result.scalars().all()

            if not assessments:
                return PopulationMetrics(
                    total_users=0,
                    active_assessments=0,
                    average_scores={},
                    risk_distribution={},
                    crisis_count=0,
                    high_risk_count=0,
                    moderate_risk_count=0,
                    low_risk_count=0,
                )

            # Calculate metrics
            total_users = len(set(a.user_id for a in assessments))
            active_assessments = len(assessments)

            # Average scores by type
            avg_scores = {}
            for assess_type in assessment_types:
                type_assessments = [a for a in assessments if a.assessment_type == assess_type]
                if type_assessments:
                    avg_scores[assess_type] = sum(a.total_score for a in type_assessments) / len(
                        type_assessments
                    )

            # Risk distribution
            risk_counts = {"critical": 0, "high": 0, "moderate": 0, "low": 0}
            for assessment in assessments:
                risk_level = assessment.risk_level
                if risk_level in risk_counts:
                    risk_counts[risk_level] += 1

            # Crisis and high risk counts
            crisis_count = sum(1 for a in assessments if a.crisis_alert)
            high_risk_count = risk_counts["critical"] + risk_counts["high"]
            moderate_risk_count = risk_counts["moderate"]
            low_risk_count = risk_counts["low"]

            return PopulationMetrics(
                total_users=total_users,
                active_assessments=active_assessments,
                average_scores=avg_scores,
                risk_distribution=risk_counts,
                crisis_count=crisis_count,
                high_risk_count=high_risk_count,
                moderate_risk_count=moderate_risk_count,
                low_risk_count=low_risk_count,
            )

        except Exception as e:
            self.logger.error(f"Error getting population metrics: {e}")
            raise

    # ========================================================================
    # High-Risk User Identification
    # ========================================================================

    async def identify_high_risk_users(
        self,
        assessment_types: Optional[List[str]] = None,
        days_back: int = 30,
        min_assessments: int = 2,
        limit: int = 50,
    ) -> List[HighRiskUser]:
        """
        Identify high-risk users requiring attention

        Criteria:
        - Crisis alerts in recent assessments
        - High or critical risk levels
        - Worsening trend
        - High scores

        Args:
            assessment_types: Filter by assessment types
            days_back: Lookback period
            min_assessments: Minimum assessments required
            limit: Maximum users to return

        Returns:
            List of HighRiskUser objects sorted by risk level
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            if assessment_types is None:
                assessment_types = ["BDI2", "BAI", "GAD7", "PHQ9"]

            # Get assessments for users with recent activity
            query = (
                select(ClinicalAssessmentExtended)
                .where(
                    and_(
                        ClinicalAssessmentExtended.assessment_type.in_(assessment_types),
                        ClinicalAssessmentExtended.completed_at >= cutoff_date,
                        or_(
                            ClinicalAssessmentExtended.crisis_alert == True,
                            ClinicalAssessmentExtended.risk_level.in_(["high", "critical"]),
                        ),
                    )
                )
                .order_by(ClinicalAssessmentExtended.total_score.desc())
                .limit(limit * 2)  # Get more, will filter and limit
            )

            result = await self.db.execute(query)
            assessments = result.scalars().all()

            # Group by user and get most recent assessment per type
            user_data = {}
            for assessment in assessments:
                user_id = assessment.user_id
                if user_id not in user_data:
                    user_data[user_id] = []
                user_data[user_id].append(assessment)

            # Create high-risk user list
            high_risk_users = []

            for user_id, user_assessments in user_data.items():
                # Filter users with minimum assessments
                if len(user_assessments) < min_assessments:
                    continue

                # Get most recent assessment
                latest = max(user_assessments, key=lambda a: a.completed_at)

                # Calculate trend (compare first and last)
                scores = [a.total_score for a in sorted(user_assessments, key=lambda a: a.completed_at)]
                if len(scores) >= 2:
                    score_change = scores[-1] - scores[0]
                    if score_change > 5:
                        trend = "worsening"
                    elif score_change < -5:
                        trend = "improving"
                    else:
                        trend = "stable"
                else:
                    trend = "unknown"

                # Determine if truly high-risk
                is_high_risk = (
                    latest.crisis_alert
                    or latest.risk_level in ["high", "critical"]
                    or latest.total_score >= 40  # High score threshold
                )

                if is_high_risk:
                    high_risk_user = HighRiskUser(
                        user_id=user_id,
                        risk_level=latest.risk_level,
                        prediction_type=latest.assessment_type,
                        current_score=latest.total_score,
                        trend=trend,
                        last_assessment=latest.completed_at,
                        factors={
                            "crisis_alert": latest.crisis_alert,
                            "risk_flags": latest.risk_flags or [],
                        },
                    )
                    high_risk_users.append(high_risk_user)

            # Sort by risk level and score
            risk_priority = {"critical": 0, "high": 1, "moderate": 2, "low": 3}
            high_risk_users.sort(
                key=lambda u: (
                    risk_priority.get(u.risk_level, 4),
                    -u.current_score,
                )
            )

            return high_risk_users[:limit]

        except Exception as e:
            self.logger.error(f"Error identifying high-risk users: {e}")
            raise

    # ========================================================================
    # Treatment Outcome Tracking
    # ========================================================================

    async def get_treatment_outcomes(
        self,
        assessment_type: str = "BDI2",
        days_back: int = 90,
        min_assessments: int = 4,
    ) -> List[TreatmentOutcome]:
        """
        Analyze treatment outcomes across population

        Classifies outcomes:
        - full_response: ≥50% score reduction
        - partial_response: 25-50% reduction
        - non_response: <25% reduction
        - deterioration: Worsening

        Args:
            assessment_type: Type of assessment to analyze
            days_back: Lookback period
            min_assessments: Minimum assessments per user

        Returns:
            List of TreatmentOutcome with counts and percentages
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Get users with sufficient assessments
            subquery = (
                select(
                    ClinicalAssessmentExtended.user_id,
                    func.count(ClinicalAssessmentExtended.id).label("assessment_count"),
                )
                .where(
                    and_(
                        ClinicalAssessmentExtended.assessment_type == assessment_type,
                        ClinicalAssessmentExtended.completed_at >= cutoff_date,
                    )
                )
                .group_by(ClinicalAssessmentExtended.user_id)
                .having(func.count(ClinicalAssessmentExtended.id) >= min_assessments)
                .subquery()
            )

            # Get first and last assessments for each user
            first_assessment = (
                select(
                    ClinicalAssessmentExtended.user_id,
                    func.min(ClinicalAssessmentExtended.total_score).label("first_score"),
                )
                .where(
                    and_(
                        ClinicalAssessmentExtended.assessment_type == assessment_type,
                        ClinicalAssessmentExtended.completed_at >= cutoff_date,
                    )
                )
                .group_by(ClinicalAssessmentExtended.user_id)
                .subquery()
            )

            last_assessment = (
                select(
                    ClinicalAssessmentExtended.user_id,
                    func.max(ClinicalAssessmentExtended.total_score).label("last_score"),
                )
                .where(
                    and_(
                        ClinicalAssessmentExtended.assessment_type == assessment_type,
                        ClinicalAssessmentExtended.completed_at >= cutoff_date,
                    )
                )
                .group_by(ClinicalAssessmentExtended.user_id)
                .subquery()
            )

            # Combine data
            query = (
                select(
                    subquery.c.user_id,
                    first_assessment.c.first_score,
                    last_assessment.c.last_score,
                )
                .join(first_assessment, subquery.c.user_id == first_assessment.c.user_id)
                .join(last_assessment, subquery.c.user_id == last_assessment.c.user_id)
            )

            result = await self.db.execute(query)
            user_outcomes = result.all()

            if not user_outcomes:
                return []

            # Classify outcomes
            outcomes = {
                "full_response": [],
                "partial_response": [],
                "non_response": [],
                "deterioration": [],
            }

            for user_id, first_score, last_score in user_outcomes:
                if first_score == 0:
                    continue  # Avoid division by zero

                percent_change = ((first_score - last_score) / first_score) * 100

                if percent_change >= 50:
                    outcomes["full_response"].append(percent_change)
                elif percent_change >= 25:
                    outcomes["partial_response"].append(percent_change)
                elif percent_change < -10:
                    outcomes["deterioration"].append(percent_change)
                else:
                    outcomes["non_response"].append(percent_change)

            # Calculate statistics
            total_users = sum(len(users) for users in outcomes.values())
            treatment_outcomes = []

            for outcome_type, changes in outcomes.items():
                count = len(changes)
                percentage = (count / total_users * 100) if total_users > 0 else 0
                avg_change = sum(changes) / len(changes) if changes else None

                treatment_outcomes.append(
                    TreatmentOutcome(
                        outcome_type=outcome_type,
                        count=count,
                        percentage=percentage,
                        avg_score_change=avg_change,
                    )
                )

            return treatment_outcomes

        except Exception as e:
            self.logger.error(f"Error getting treatment outcomes: {e}")
            raise

    # ========================================================================
    # Time Series Trend Data
    # ========================================================================

    async def get_time_series_trends(
        self,
        assessment_type: str = "BDI2",
        days_back: int = 90,
        interval_days: int = 7,
    ) -> List[TimeSeriesData]:
        """
        Get time series data for trend visualization

        Args:
            assessment_type: Type of assessment to analyze
            days_back: Total lookback period
            interval_days: Size of each time bucket

        Returns:
            List of TimeSeriesData ordered by period
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Calculate number of intervals
            num_intervals = days_back // interval_days

            time_series_data = []

            for i in range(num_intervals):
                # Calculate interval dates
                interval_end = datetime.utcnow() - timedelta(days=i * interval_days)
                interval_start = interval_end - timedelta(days=interval_days)

                # Query assessments in this interval
                query = (
                    select(ClinicalAssessmentExtended)
                    .where(
                        and_(
                            ClinicalAssessmentExtended.assessment_type == assessment_type,
                            ClinicalAssessmentExtended.completed_at >= interval_start,
                            ClinicalAssessmentExtended.completed_at < interval_end,
                        )
                    )
                )

                result = await self.db.execute(query)
                assessments = result.scalars().all()

                if not assessments:
                    continue

                # Calculate metrics for this interval
                avg_score = sum(a.total_score for a in assessments) / len(assessments)
                assessment_count = len(assessments)
                high_risk_count = sum(
                    1 for a in assessments if a.risk_level in ["high", "critical"]
                )
                crisis_count = sum(1 for a in assessments if a.crisis_alert)

                # Format period label
                period_label = f"{interval_start.strftime('%Y-%m-%d')} to {interval_end.strftime('%Y-%m-%d')}"

                time_series_data.append(
                    TimeSeriesData(
                        period=period_label,
                        avg_score=avg_score,
                        assessment_count=assessment_count,
                        high_risk_count=high_risk_count,
                        crisis_count=crisis_count,
                    )
                )

            # Reverse to show oldest to newest
            return time_series_data[::-1]

        except Exception as e:
            self.logger.error(f"Error getting time series trends: {e}")
            raise

    # ========================================================================
    # Geographic/Demographic Breakdowns
    # ========================================================================

    async def get_demographic_breakdown(
        self,
        group_by: str = "assessment_type",
        days_back: int = 30,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get breakdown by demographic or assessment type

        Args:
            group_by: Field to group by (assessment_type, risk_level, etc.)
            days_back: Lookback period

        Returns:
            Dictionary with statistics for each group
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Get assessments
            query = (
                select(ClinicalAssessmentExtended)
                .where(ClinicalAssessmentExtended.completed_at >= cutoff_date)
            )

            result = await self.db.execute(query)
            assessments = result.scalars().all()

            if not assessments:
                return {}

            # Group assessments
            groups = {}
            for assessment in assessments:
                if group_by == "assessment_type":
                    group_key = assessment.assessment_type
                elif group_by == "risk_level":
                    group_key = assessment.risk_level
                else:
                    group_key = "unknown"

                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(assessment)

            # Calculate statistics for each group
            breakdown = {}

            for group_key, group_assessments in groups.items():
                scores = [a.total_score for a in group_assessments]
                crisis_count = sum(1 for a in group_assessments if a.crisis_alert)

                breakdown[group_key] = {
                    "count": len(group_assessments),
                    "avg_score": round(sum(scores) / len(scores), 2),
                    "min_score": min(scores),
                    "max_score": max(scores),
                    "crisis_count": crisis_count,
                    "crisis_rate": round(crisis_count / len(group_assessments) * 100, 2),
                }

            return breakdown

        except Exception as e:
            self.logger.error(f"Error getting demographic breakdown: {e}")
            raise

    # ========================================================================
    # Summary Statistics
    # ========================================================================

    async def get_summary_statistics(
        self,
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """
        Get executive summary statistics for dashboard

        Returns:
            Dictionary with key metrics and trends
        """
        try:
            # Get population metrics
            metrics = await self.get_population_metrics(days_back=days_back)

            # Get high-risk users
            high_risk_users = await self.identify_high_risk_users(days_back=days_back, limit=10)

            # Get treatment outcomes
            treatment_outcomes = await self.get_treatment_outcomes(days_back=days_back)

            # Get recent trend
            time_series = await self.get_time_series_trends(days_back=days_back, interval_days=7)

            # Calculate trend direction
            if len(time_series) >= 2:
                recent_avg = time_series[-1].avg_score
                previous_avg = time_series[-2].avg_score
                if recent_avg > previous_avg + 2:
                    trend_direction = "worsening"
                elif recent_avg < previous_avg - 2:
                    trend_direction = "improving"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "unknown"

            return {
                "population_metrics": metrics.to_dict(),
                "high_risk_users": {
                    "count": len(high_risk_users),
                    "users": [u.to_dict() for u in high_risk_users],
                },
                "treatment_outcomes": [o.to_dict() for o in treatment_outcomes],
                "trend_direction": trend_direction,
                "crisis_rate": round(
                    metrics.crisis_count / metrics.active_assessments * 100
                    if metrics.active_assessments > 0
                    else 0,
                    2,
                ),
                "high_risk_rate": round(
                    metrics.high_risk_count / metrics.active_assessments * 100
                    if metrics.active_assessments > 0
                    else 0,
                    2,
                ),
            }

        except Exception as e:
            self.logger.error(f"Error getting summary statistics: {e}")
            raise
