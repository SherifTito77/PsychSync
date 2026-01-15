"""
Enhanced Clinical Analytics Service

Features:
- Trend analysis over time
- Comparative analytics
- Risk stratification
- Outcome measurement
- Longitudinal tracking
- Population health metrics
- Performance monitoring
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
import numpy as np
from scipy import stats

from app.db.models.clinical_screening import ClinicalScreening, ClinicalAlert
from app.services.clinical.scoring_algorithms import PHQ9Scorer, GAD7Scorer
from app.services.clinical.additional_scorers import MDQScorer, DAST10Scorer, AQ10Scorer, ACEScorer


class TrendDirection(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class RiskCategory(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    direction: TrendDirection
    change_percentage: float
    confidence: float
    slope: float
    r_squared: float
    recommendation: str


@dataclass
class ComparativeMetrics:
    """Comparative analytics metrics"""
    user_average: float
    population_average: float
    percentile_rank: float
    z_score: float
    interpretation: str


@dataclass
class OutcomeMetrics:
    """Outcome measurement metrics"""
    baseline_score: float
    current_score: float
    change: float
    clinically_significant: bool
    minimal_important_change: float
    achieved: bool


class EnhancedClinicalAnalytics:
    """
    Advanced analytics for clinical screening data

    Features:
    - Longitudinal trend analysis
    - Comparative analytics
    - Risk stratification
    - Outcome measurement
    - Population health
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_trends(
        self,
        user_id: str,
        screening_type: str,
        weeks: int = 12
    ) -> Optional[TrendAnalysis]:
        """
        Analyze screening score trends over time

        Args:
            user_id: User to analyze
            screening_type: Type of screening (PHQ9, GAD7, etc.)
            weeks: Number of weeks to analyze

        Returns:
            TrendAnalysis with direction and recommendations
        """
        cutoff_date = datetime.utcnow() - timedelta(weeks=weeks)

        # Get historical screenings
        query = select(ClinicalScreening).where(
            and_(
                ClinicalScreening.user_id == user_id,
                ClinicalScreening.screening_type == screening_type,
                ClinicalScreening.completed_at >= cutoff_date,
                ClinicalScreening.completed_at.isnot(None)
            )
        ).order_by(ClinicalScreening.completed_at)

        result = await self.db.execute(query)
        screenings = result.scalars().all()

        if len(screenings) < 2:
            return None

        # Extract scores and dates
        scores = [s.total_score for s in screenings]
        dates = [(s.completed_at - cutoff_date).days for s in screenings]

        # Linear regression for trend
        slope, intercept, r_value, p_value, std_err = stats.linregress(dates, scores)

        # Calculate direction
        if p_value > 0.05:
            direction = TrendDirection.STABLE
        elif slope < 0:
            direction = TrendDirection.IMPROVING
        else:
            direction = TrendDirection.DECLINING

        # Calculate percent change
        if scores[0] > 0:
            change_percentage = ((scores[-1] - scores[0]) / scores[0]) * 100
        else:
            change_percentage = 0

        # Generate recommendation
        recommendation = self._generate_trend_recommendation(
            screening_type, direction, change_percentage, p_value
        )

        return TrendAnalysis(
            direction=direction,
            change_percentage=round(change_percentage, 2),
            confidence=round(1 - p_value, 2),
            slope=round(slope, 4),
            r_squared=round(r_value ** 2, 4),
            recommendation=recommendation
        )

    async def get_comparative_metrics(
        self,
        user_id: str,
        screening_type: str
    ) -> Optional[ComparativeMetrics]:
        """
        Compare user scores to population

        Args:
            user_id: User to analyze
            screening_type: Type of screening

        Returns:
            ComparativeMetrics with population comparison
        """
        # Get user's latest score
        user_query = select(ClinicalScreening).where(
            and_(
                ClinicalScreening.user_id == user_id,
                ClinicalScreening.screening_type == screening_type,
                ClinicalScreening.completed_at.isnot(None)
            )
        ).order_by(ClinicalScreening.completed_at.desc()).limit(1)

        user_result = await self.db.execute(user_query)
        user_screening = user_result.scalar_one_or_none()

        if not user_screening:
            return None

        user_score = user_screening.total_score

        # Get population statistics
        pop_query = select(
            func.avg(ClinicalScreening.total_score).label('mean'),
            func.stddev(ClinicalScreening.total_score).label('stddev')
        ).where(
            and_(
                ClinicalScreening.screening_type == screening_type,
                ClinicalScreening.completed_at.isnot(None)
            )
        )

        pop_result = await self.db.execute(pop_query)
        pop_stats = pop_result.first()

        if not pop_stats or pop_stats.mean is None:
            return None

        pop_mean = float(pop_stats.mean)
        pop_std = float(pop_stats.stddev) if pop_stats.stddev else 1.0

        # Calculate metrics
        z_score = (user_score - pop_mean) / pop_std if pop_std > 0 else 0

        # Percentile rank (using z-score)
        percentile_rank = stats.norm.cdf(z_score) * 100

        # Generate interpretation
        interpretation = self._generate_comparative_interpretation(
            screening_type, percentile_rank, z_score
        )

        return ComparativeMetrics(
            user_average=round(user_score, 2),
            population_average=round(pop_mean, 2),
            percentile_rank=round(percentile_rank, 2),
            z_score=round(z_score, 2),
            interpretation=interpretation
        )

    async def get_outcome_metrics(
        self,
        user_id: str,
        screening_type: str,
        baseline_days: int = 30,
        follow_up_days: int = 90
    ) -> Optional[OutcomeMetrics]:
        """
        Measure clinical outcomes over time

        Args:
            user_id: User to analyze
            screening_type: Type of screening
            baseline_days: Days to look back for baseline
            follow_up_days: Days to measure improvement

        Returns:
            OutcomeMetrics with change and significance
        """
        now = datetime.utcnow()
        baseline_cutoff = now - timedelta(days=baseline_days)
        follow_up_cutoff = now - timedelta(days=follow_up_days)

        # Get baseline and follow-up scores
        baseline_query = select(ClinicalScreening).where(
            and_(
                ClinicalScreening.user_id == user_id,
                ClinicalScreening.screening_type == screening_type,
                ClinicalScreening.completed_at >= baseline_cutoff,
                ClinicalScreening.completed_at < follow_up_cutoff
            )
        ).order_by(ClinicalScreening.completed_at).limit(1)

        baseline_result = await self.db.execute(baseline_query)
        baseline = baseline_result.scalar_one_or_none()

        follow_up_query = select(ClinicalScreening).where(
            and_(
                ClinicalScreening.user_id == user_id,
                ClinicalScreening.screening_type == screening_type,
                ClinicalScreening.completed_at >= follow_up_cutoff
            )
        ).order_by(ClinicalScreening.completed_at.desc()).limit(1)

        follow_up_result = await self.db.execute(follow_up_query)
        follow_up = follow_up_result.scalar_one_or_none()

        if not baseline or not follow_up:
            return None

        baseline_score = baseline.total_score
        current_score = follow_up.total_score
        change = baseline_score - current_score

        # Minimal important change (MIC) values for different tools
        MIC_VALUES = {
            'PHQ9': 5.0,
            'GAD7': 4.0,
            'MDQ': 3.0,
            'DAST10': 2.0,
            'AQ10': 2.0,
            'ACE': 2.0,
            'CSSRS': 1.0
        }

        mic = MIC_VALUES.get(screening_type, 3.0)
        clinically_significant = abs(change) >= mic
        achieved = change > 0 and clinically_significant

        return OutcomeMetrics(
            baseline_score=round(baseline_score, 2),
            current_score=round(current_score, 2),
            change=round(change, 2),
            clinically_significant=clinically_significant,
            minimal_important_change=mic,
            achieved=achieved
        )

    async def get_population_health_metrics(
        self,
        org_id: str,
        screening_type: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Get population health metrics for organization

        Args:
            org_id: Organization ID
            screening_type: Optional filter by type

        Returns:
            Population health metrics
        """
        # Base query
        where_conditions = [ClinicalScreening.org_id == org_id]
        if screening_type:
            where_conditions.append(ClinicalScreening.screening_type == screening_type)

        # Completion rates
        completed_query = select(func.count(ClinicalScreening.id)).where(
            and_(
                *where_conditions,
                ClinicalScreening.completed_at.isnot(None)
            )
        )

        total_query = select(func.count(ClinicalScreening.id)).where(
            and_(*where_conditions)
        )

        completed_result = await self.db.execute(completed_query)
        total_result = await self.db.execute(total_query)

        completed_count = completed_result.scalar() or 0
        total_count = total_result.scalar() or 0
        completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0

        # Risk distribution
        risk_query = select(
            ClinicalScreening.risk_level,
            func.count(ClinicalScreening.id)
        ).where(
            and_(
                *where_conditions,
                ClinicalScreening.completed_at.isnot(None)
            )
        ).group_by(ClinicalScreening.risk_level)

        risk_result = await self.db.execute(risk_query)
        risk_distribution = {row[0]: row[1] for row in risk_result}

        # Crisis alerts
        crisis_query = select(func.count(ClinicalAlert.id)).where(
            and_(
                ClinicalAlert.org_id == org_id,
                ClinicalAlert.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        )

        crisis_result = await self.db.execute(crisis_query)
        crisis_count = crisis_result.scalar() or 0

        return {
            'completion_rate': round(completion_rate, 2),
            'total_screenings': total_count,
            'completed_screenings': completed_count,
            'risk_distribution': risk_distribution,
            'crisis_alerts_last_30_days': crisis_count,
            'high_risk_count': risk_distribution.get('high', 0),
            'moderate_risk_count': risk_distribution.get('moderate', 0),
            'low_risk_count': risk_distribution.get('low', 0),
            'critical_risk_count': risk_distribution.get('critical', 0)
        }

    def _generate_trend_recommendation(
        self,
        screening_type: str,
        direction: TrendDirection,
        change_percentage: float,
        p_value: float
    ) -> str:
        """Generate recommendation based on trend"""

        if direction == TrendDirection.IMPROVING:
            if abs(change_percentage) > 20:
                return f"Significant improvement in {screening_type} scores. Continue current treatment plan."
            else:
                return f"Mild improvement in {screening_type}. Monitor progress."

        elif direction == TrendDirection.DECLINING:
            if abs(change_percentage) > 20:
                return f"Significant worsening of {screening_type} symptoms. Clinical review recommended."
            else:
                return f"Mild worsening of {screening_type}. Consider intervention."

        else:  # Stable
            return f"{screening_type} scores stable. Continue current monitoring."

    def _generate_comparative_interpretation(
        self,
        screening_type: str,
        percentile_rank: float,
        z_score: float
    ) -> str:
        """Generate interpretation of comparative metrics"""

        if percentile_rank >= 90:
            return f"Very high scores compared to population (top 10%). Clinical attention recommended."
        elif percentile_rank >= 75:
            return f"High scores compared to population (top 25%). Monitor closely."
        elif percentile_rank >= 50:
            return f"Scores above population average. Consider support."
        elif percentile_rank >= 25:
            return f"Scores below population average. Positive indicator."
        else:
            return f"Scores well below population average (bottom 25%). Good outcome."

    async def get_screening_analytics_summary(
        self,
        user_id: str,
        org_id: str
    ) -> Dict[str, any]:
        """
        Get comprehensive analytics summary for user

        Args:
            user_id: User ID
            org_id: Organization ID

        Returns:
            Comprehensive analytics summary
        """
        screening_types = ['PHQ9', 'GAD7', 'MDQ', 'DAST10', 'AQ10', 'ACE']

        summary = {
            'user_id': user_id,
            'org_id': org_id,
            'generated_at': datetime.utcnow().isoformat(),
            'screenings': {}
        }

        for screening_type in screening_types:
            # Get trends
            trends = await self.get_user_trends(user_id, screening_type)

            # Get comparative metrics
            comparative = await self.get_comparative_metrics(user_id, screening_type)

            # Get outcome metrics
            outcomes = await self.get_outcome_metrics(user_id, screening_type)

            summary['screenings'][screening_type] = {
                'trends': {
                    'direction': trends.direction.value if trends else None,
                    'change_percentage': trends.change_percentage if trends else None,
                    'recommendation': trends.recommendation if trends else None
                } if trends else None,
                'comparative': {
                    'percentile_rank': comparative.percentile_rank if comparative else None,
                    'interpretation': comparative.interpretation if comparative else None
                } if comparative else None,
                'outcomes': {
                    'change': outcomes.change if outcomes else None,
                    'clinically_significant': outcomes.clinically_significant if outcomes else None,
                    'achieved': outcomes.achieved if outcomes else None
                } if outcomes else None
            }

        return summary


# Analytics API endpoint helpers
async def generate_analytics_report(
    db: AsyncSession,
    user_id: str,
    org_id: str
) -> Dict[str, any]:
    """
    Generate comprehensive analytics report

    This is the main entry point for analytics reporting
    """
    analytics = EnhancedClinicalAnalytics(db)

    report = {
        'summary': await analytics.get_screening_analytics_summary(user_id, org_id),
        'population_health': await analytics.get_population_health_metrics(org_id)
    }

    return report
