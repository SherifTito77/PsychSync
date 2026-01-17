"""
Advanced Clinical Analytics Service with Trend Analysis

Provides longitudinal tracking, trend detection, and population health insights
for mental health assessments and treatment outcomes.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, text
from sqlalchemy.sql import extract

from app.db.models.clinical import ClinicalAssessmentExtended
from app.db.models.analytics import AssessmentTrend

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Trend classification"""
    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"


@dataclass
class TrendAnalysisResult:
    """Result of trend analysis"""
    trend_direction: str
    slope: float  # Linear regression slope (points per day)
    r_squared: float  # Goodness of fit (0-1)
    confidence: str  # low, moderate, high
    interpretation: str
    recent_scores: List[Tuple[datetime, float]]
    change_30d: Optional[float] = None
    change_90d: Optional[float] = None


@dataclass
class PopulationHealthMetrics:
    """Population-level health statistics"""
    assessment_type: str
    date_range: Tuple[datetime, datetime]
    total_assessments: int
    unique_users: int
    mean_score: float
    median_score: float
    std_dev: float
    score_distribution: Dict[str, int]  # severity level -> count
    crisis_rate: float  # percentage
    high_risk_rate: float  # percentage
    trend_direction: str


class AdvancedAnalyticsService:
    """
    Advanced analytics for longitudinal tracking and population health

    Features:
    - Individual trend analysis (linear regression)
    - Change detection (30d, 90d)
    - Population health statistics
    - Risk stratification
    - Treatment outcome tracking
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_user_trends(
        self,
        user_id: str,
        assessment_type: str,
        min_data_points: int = 3
    ) -> Optional[TrendAnalysisResult]:
        """
        Calculate longitudinal trends for a user's assessments

        Args:
            user_id: User UUID
            assessment_type: Type of assessment (PHQ9, GAD7, LSAS, etc.)
            min_data_points: Minimum number of assessments required for trend analysis

        Returns:
            TrendAnalysisResult with trend direction, slope, statistics
        """
        # Fetch user's assessment history
        query = select(ClinicalAssessmentExtended).where(
            and_(
                ClinicalAssessmentExtended.user_id == user_id,
                ClinicalAssessmentExtended.assessment_type == assessment_type,
                ClinicalAssessmentExtended.deleted_at.is_(None)
            )
        ).order_by(ClinicalAssessmentExtended.completed_at)

        result = await self.db.execute(query)
        assessments = result.scalars().all()

        if len(assessments) < min_data_points:
            logger.info(f"Insufficient data points for trend analysis: {len(assessments)} < {min_data_points}")
            return None

        # Extract scores and dates
        scores_data = [
            (a.completed_at, float(a.total_score))
            for a in assessments
        ]

        # Calculate linear regression
        slope, r_squared = self._linear_regression(scores_data)

        # Determine trend direction
        if slope > 0.1:
            trend_direction = TrendDirection.WORSENING.value
        elif slope < -0.1:
            trend_direction = TrendDirection.IMPROVING.value
        else:
            trend_direction = TrendDirection.STABLE.value

        # Calculate confidence based on R² and data points
        n = len(scores_data)
        if r_squared > 0.7 and n >= 5:
            confidence = "high"
        elif r_squared > 0.4 and n >= 3:
            confidence = "moderate"
        else:
            confidence = "low"

        # Calculate recent changes
        change_30d = await self._calculate_period_change(user_id, assessment_type, 30)
        change_90d = await self._calculate_period_change(user_id, assessment_type, 90)

        # Generate interpretation
        interpretation = self._generate_trend_interpretation(
            trend_direction, slope, r_squared, assessment_type
        )

        # Store/update trend in database
        await self._update_assessment_trend(
            user_id, assessment_type, trend_direction, slope, r_squared,
            scores_data, change_30d, change_90d
        )

        return TrendAnalysisResult(
            trend_direction=trend_direction,
            slope=slope,
            r_squared=r_squared,
            confidence=confidence,
            interpretation=interpretation,
            recent_scores=scores_data[-10:],  # Last 10 assessments
            change_30d=change_30d,
            change_90d=change_90d
        )

    def _linear_regression(
        self,
        data: List[Tuple[datetime, float]]
    ) -> Tuple[float, float]:
        """
        Calculate simple linear regression: y = mx + b

        Returns:
            (slope, r_squared)
        """
        n = len(data)
        if n < 2:
            return 0.0, 0.0

        # Convert dates to numeric (days since first date)
        start_date = data[0][0]
        x = [(date - start_date).days for date, _ in data]
        y = [score for _, score in data]

        # Calculate slope and intercept
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)
        sum_y2 = sum(yi ** 2 for yi in y)

        # Slope (m)
        numerator = n * sum_xy - sum_x * sum_y
        denominator = n * sum_x2 - sum_x ** 2

        if denominator == 0:
            return 0.0, 0.0

        slope = numerator / denominator

        # R² calculation
        y_mean = sum_y / n
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)
        ss_res = sum((y[i] - (slope * x[i] + (sum_y - slope * sum_x) / n)) ** 2 for i in range(n))

        if ss_tot == 0:
            r_squared = 1.0
        else:
            r_squared = 1 - (ss_res / ss_tot)

        return slope, max(0.0, min(1.0, r_squared))

    async def _calculate_period_change(
        self,
        user_id: str,
        assessment_type: str,
        days: int
    ) -> Optional[float]:
        """Calculate average score change over a period"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get earliest score before cutoff
        early_query = select(func.avg(ClinicalAssessmentExtended.total_score)).where(
            and_(
                ClinicalAssessmentExtended.user_id == user_id,
                ClinicalAssessmentExtended.assessment_type == assessment_type,
                ClinicalAssessmentExtended.completed_at < cutoff_date,
                ClinicalAssessmentExtended.deleted_at.is_(None)
            )
        )

        # Get latest score
        recent_query = select(func.avg(ClinicalAssessmentExtended.total_score)).where(
            and_(
                ClinicalAssessmentExtended.user_id == user_id,
                ClinicalAssessmentExtended.assessment_type == assessment_type,
                ClinicalAssessmentExtended.completed_at >= cutoff_date,
                ClinicalAssessmentExtended.deleted_at.is_(None)
            )
        )

        early_result = await self.db.execute(early_query)
        early_avg = early_result.scalar()

        recent_result = await self.db.execute(recent_query)
        recent_avg = recent_result.scalar()

        if early_avg is None or recent_avg is None:
            return None

        return float(recent_avg - early_avg)

    def _generate_trend_interpretation(
        self,
        direction: str,
        slope: float,
        r_squared: float,
        assessment_type: str
    ) -> str:
        """Generate human-readable trend interpretation"""

        if direction == TrendDirection.IMPROVING.value:
            if r_squared > 0.7:
                return f"Strong consistent improvement in {assessment_type} scores over time. Treatment appears highly effective."
            elif r_squared > 0.4:
                return f"Generally improving {assessment_type} scores with some variability. Positive response to treatment."
            else:
                return f"Some improvement in {assessment_type} scores but with significant variability. Continue monitoring."

        elif direction == TrendDirection.WORSENING.value:
            if r_squared > 0.7:
                return f"Significant worsening of {assessment_type} scores over time. Treatment adjustment strongly recommended."
            elif r_squared > 0.4:
                return f"Generally declining {assessment_type} scores. Clinical review and treatment modification needed."
            else:
                return f"Variable {assessment_type} scores with concerning trends. Evaluation recommended."

        else:  # STABLE
            if r_squared > 0.4:
                return f"{assessment_type} scores remain stable over time. Consider treatment intensification if symptoms persist."
            else:
                return f"{assessment_type} scores fluctuating without clear trend. Continue current treatment plan."

    async def _update_assessment_trend(
        self,
        user_id: str,
        assessment_type: str,
        trend_direction: str,
        slope: float,
        r_squared: float,
        scores_data: List[Tuple[datetime, float]],
        change_30d: Optional[float],
        change_90d: Optional[float]
    ):
        """Update or create assessment trend record"""

        # Calculate statistics
        scores = [score for _, score in scores_data]
        mean_score = sum(scores) / len(scores)
        median_score = sorted(scores)[len(scores) // 2]

        # Check if trend exists
        query = select(AssessmentTrend).where(
            and_(
                AssessmentTrend.user_id == user_id,
                AssessmentTrend.assessment_type == assessment_type
            )
        )

        result = await self.db.execute(query)
        trend = result.scalar_one_or_none()

        if trend:
            # Update existing
            trend.trend_direction = trend_direction
            trend.slope = slope
            trend.r_squared = r_squared
            trend.mean_score = mean_score
            trend.median_score = median_score
            trend.total_assessments = len(scores_data)
            trend.score_change_30d = change_30d
            trend.score_change_90d = change_90d
            trend.calculated_at = datetime.utcnow()
            trend.data_points_used = len(scores_data)
            trend.date_range_start = scores_data[0][0]
            trend.date_range_end = scores_data[-1][0]
        else:
            # Create new
            trend = AssessmentTrend(
                user_id=user_id,
                assessment_type=assessment_type,
                trend_direction=trend_direction,
                slope=slope,
                r_squared=r_squared,
                mean_score=mean_score,
                median_score=median_score,
                total_assessments=len(scores_data),
                score_change_30d=change_30d,
                score_change_90d=change_90d,
                data_points_used=len(scores_data),
                date_range_start=scores_data[0][0],
                date_range_end=scores_data[-1][0]
            )
            self.db.add(trend)

        await self.db.commit()

    async def get_population_health_metrics(
        self,
        assessment_type: str,
        start_date: datetime,
        end_date: datetime,
        group_by: str = 'all'  # 'all', 'week', 'month'
    ) -> List[PopulationHealthMetrics]:
        """
        Calculate population health metrics for an assessment type

        Args:
            assessment_type: Type of assessment
            start_date: Start of analysis period
            end_date: End of analysis period
            group_by: Time grouping ('all', 'week', 'month')

        Returns:
            List of PopulationHealthMetrics
        """

        # Build query with optional grouping
        if group_by == 'week':
            date_trunc = func.date_trunc('week', ClinicalAssessmentExtended.completed_at)
        elif group_by == 'month':
            date_trunc = func.date_trunc('month', ClinicalAssessmentExtended.completed_at)
        else:
            date_trunc = func.date_trunc('day', start_date)  # Single group

        query = select(
            date_trunc.label('period'),
            func.count(ClinicalAssessmentExtended.id).label('total'),
            func.count(func.distinct(ClinicalAssessmentExtended.user_id)).label('unique_users'),
            func.avg(ClinicalAssessmentExtended.total_score).label('mean_score'),
            func.percentile_cont(0.5).within_group(ClinicalAssessmentExtended.total_score).label('median_score'),
            func.stddev(ClinicalAssessmentExtended.total_score).label('std_dev'),
            func.count(func.distinct(ClinicalAssessmentExtended.user_id)).filter(
                ClinicalAssessmentExtended.risk_level == 'high'
            ).label('high_risk_count'),
            func.count(func.distinct(ClinicalAssessmentExtended.user_id)).filter(
                ClinicalAssessmentExtended.crisis_alert == True
            ).label('crisis_count')
        ).where(
            and_(
                ClinicalAssessmentExtended.assessment_type == assessment_type,
                ClinicalAssessmentExtended.completed_at >= start_date,
                ClinicalAssessmentExtended.completed_at <= end_date,
                ClinicalAssessmentExtended.deleted_at.is_(None)
            )
        ).group_by(date_trunc).order_by(date_trunc)

        result = await self.db.execute(query)
        rows = result.all()

        metrics = []
        for row in rows:
            period = row.period if group_by != 'all' else start_date

            # Get severity distribution
            severity_dist = await self._get_severity_distribution(
                assessment_type, period, period + timedelta(days=7)
            )

            metrics.append(PopulationHealthMetrics(
                assessment_type=assessment_type,
                date_range=(period, period + timedelta(days=7)),
                total_assessments=row.total,
                unique_users=row.unique_users,
                mean_score=float(row.mean_score or 0),
                median_score=float(row.median_score or 0),
                std_dev=float(row.std_dev or 0),
                score_distribution=severity_dist,
                crisis_rate=float((row.crisis_count or 0) / row.unique_users * 100) if row.unique_users > 0 else 0.0,
                high_risk_rate=float((row.high_risk_count or 0) / row.unique_users * 100) if row.unique_users > 0 else 0.0,
                trend_direction="stable"  # Simplified
            ))

        return metrics

    async def _get_severity_distribution(
        self,
        assessment_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, int]:
        """Get count of assessments by severity level"""

        query = select(
            ClinicalAssessmentExtended.severity_level,
            func.count(ClinicalAssessmentExtended.id)
        ).where(
            and_(
                ClinicalAssessmentExtended.assessment_type == assessment_type,
                ClinicalAssessmentExtended.completed_at >= start_date,
                ClinicalAssessmentExtended.completed_at <= end_date,
                ClinicalAssessmentExtended.deleted_at.is_(None)
            )
        ).group_by(ClinicalAssessmentExtended.severity_level)

        result = await self.db.execute(query)
        return {row.severity_level: row.count for row in result.all()}

    async def identify_high_risk_users(
        self,
        assessment_type: str,
        limit: int = 50
    ) -> List[Dict[str, any]]:
        """
        Identify users with worsening trends or high symptom levels

        Args:
            assessment_type: Type of assessment to analyze
            limit: Maximum number of users to return

        Returns:
            List of user dicts with risk indicators
        """

        # Find users with high recent scores or worsening trends
        query = select(
            AssessmentTrend.user_id,
            AssessmentTrend.trend_direction,
            AssessmentTrend.mean_score,
            AssessmentTrend.score_change_30d,
            AssessmentTrend.high_risk_episodes
        ).where(
            and_(
                AssessmentTrend.assessment_type == assessment_type,
                or_(
                    AssessmentTrend.trend_direction == 'worsening',
                    AssessmentTrend.mean_score > 15,  # Threshold depends on assessment type
                    AssessmentTrend.high_risk_episodes > 0
                )
            )
        ).order_by(
            AssessmentTrend.high_risk_episodes.desc(),
            AssessmentTrend.mean_score.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        trends = result.all()

        return [
            {
                'user_id': str(trend.user_id),
                'trend_direction': trend.trend_direction,
                'mean_score': float(trend.mean_score),
                'change_30d': float(trend.score_change_30d) if trend.score_change_30d else None,
                'high_risk_episodes': trend.high_risk_episodes,
                'risk_level': 'high' if trend.mean_score > 15 or trend.high_risk_episodes > 0 else 'moderate'
            }
            for trend in trends
        ]

    async def refresh_materialized_view(self):
        """Refresh the population_health_stats materialized view"""

        await self.db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY population_health_stats"))
        await self.db.commit()

        logger.info("Refreshed population_health_stats materialized view")


# Helper function for trend calculation
async def calculate_user_trends_task(
    user_id: str,
    assessment_types: List[str]
):
    """
    Background task to calculate trends for a user across all assessment types

    Should be called periodically (e.g., daily/weekly)
    """
    from app.db.session import get_async_db

    async for db in get_async_db():
        analytics = AdvancedAnalyticsService(db)

        for assessment_type in assessment_types:
            try:
                await analytics.calculate_user_trends(user_id, assessment_type)
            except Exception as e:
                logger.error(f"Failed to calculate trends for user {user_id}, assessment {assessment_type}: {e}")

        await analytics.refresh_materialized_view()
