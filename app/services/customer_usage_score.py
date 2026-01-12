"""
Customer Usage Score (CUS) Calculation Service

Computes a 0-100 score measuring customer product health and engagement.
Used for churn prediction, customer success intervention, and product insights.

Score Formula:
CUS = (Engagement × 0.30) + (Adoption × 0.25) + (Integration × 0.20) +
      (Growth × 0.15) + (Retention × 0.10)

Created: 2025-01-12
Author: Architecture Team
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from sqlalchemy.sql import text

from app.db.models.organization import Organization
from app.db.models.user import User
from app.db.models.team import Team
from app.db.models.analytics import FactAssessmentCompletion

logger = logging.getLogger(__name__)


class ScoreTier(str, Enum):
    """Customer health tiers based on usage score"""
    CRITICAL = "critical"  # 0-39: High churn risk
    AT_RISK = "at_risk"    # 40-59: Moderate churn risk
    HEALTHY = "healthy"    # 60-79: Good engagement
    THRIVING = "thriving"  # 80-100: Excellent engagement


@dataclass
class ComponentScore:
    """Individual component score details"""
    component_name: str
    score: float  # 0-100
    weight: float  # 0-1
    weighted_score: float  # score × weight
    metrics: Dict[str, float]
    trend: str  # "improving", "stable", "declining"


@dataclass
class CustomerUsageScore:
    """Complete customer usage score breakdown"""
    tenant_id: str
    organization_id: str
    score: float  # 0-100
    tier: ScoreTier
    churn_probability: float  # 0-1
    calculated_at: datetime
    components: Dict[str, ComponentScore]
    insights: List[str]
    recommendations: List[str]
    previous_score: Optional[float] = None
    trend: Optional[str] = None


class CustomerUsageScoreService:
    """
    Calculates and manages Customer Usage Scores.

    Usage:
        service = CustomerUsageScoreService(db)

        # Calculate score for organization
        cus = await service.calculate_score(organization_id)

        # Get scores for all organizations (batch job)
        scores = await service.calculate_all_scores()

        # Identify at-risk customers
        at_risk = await service.get_at_risk_customers(threshold=40)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize score calculation service.

        Args:
            db: Database session
        """
        self.db = db

    async def calculate_score(
        self,
        organization_id: str,
        lookback_days: int = 30,
        previous_period_days: int = 30
    ) -> CustomerUsageScore:
        """
        Calculate Customer Usage Score for organization.

        Args:
            organization_id: Organization UUID
            lookback_days: Days to look back for current period
            previous_period_days: Days for previous period (trend comparison)

        Returns:
            CustomerUsageScore with complete breakdown
        """
        logger.info(f"Calculating CUS for organization {organization_id}")

        # Calculate each component
        engagement_score = await self._calculate_engagement(
            organization_id, lookback_days, previous_period_days
        )

        adoption_score = await self._calculate_adoption(
            organization_id, lookback_days, previous_period_days
        )

        integration_score = await self._calculate_integration(
            organization_id, lookback_days, previous_period_days
        )

        growth_score = await self._calculate_growth(
            organization_id, lookback_days, previous_period_days
        )

        retention_score = await self._calculate_retention(
            organization_id, lookback_days, previous_period_days
        )

        # Combine scores with weights
        components = {
            "engagement": engagement_score,
            "adoption": adoption_score,
            "integration": integration_score,
            "growth": growth_score,
            "retention": retention_score,
        }

        total_score = sum(c.weighted_score for c in components.values())

        # Determine tier and churn probability
        tier = self._get_score_tier(total_score)
        churn_probability = self._calculate_churn_probability(total_score, components)

        # Generate insights and recommendations
        insights = self._generate_insights(components, total_score)
        recommendations = self._generate_recommendations(components, tier)

        # Get previous score for trend
        previous_score = await self._get_previous_score(organization_id)
        trend = self._calculate_trend(previous_score, total_score) if previous_score else None

        return CustomerUsageScore(
            tenant_id=organization_id,  # For multi-tenant, org_id = tenant_id
            organization_id=organization_id,
            score=round(total_score, 2),
            tier=tier,
            churn_probability=round(churn_probability, 3),
            calculated_at=datetime.utcnow(),
            components=components,
            insights=insights,
            recommendations=recommendations,
            previous_score=previous_score,
            trend=trend,
        )

    async def _calculate_engagement(
        self,
        organization_id: str,
        lookback_days: int,
        previous_period_days: int
    ) -> ComponentScore:
        """
        Calculate Engagement Score (30% weight).

        Metrics:
        - DAU/MAU ratio (daily active / monthly active users)
        - Average session frequency (sessions per user)
        - Assessment completion rate
        - Feature usage breadth
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)
        prev_start = start_date - timedelta(days=previous_period_days)

        # Get user count
        user_count = await self._get_user_count(organization_id)
        if user_count == 0:
            return ComponentScore(
                component_name="engagement",
                score=0.0,
                weight=0.30,
                weighted_score=0.0,
                metrics={},
                trend="stable"
            )

        # DAU calculation
        dau = await self._get_active_user_count(organization_id, days=1)
        mau = await self._get_active_user_count(organization_id, days=30)
        dau_mau_ratio = (dau / mau) if mau > 0 else 0

        # Session frequency (avg assessments per user)
        assessments_completed = await self._get_assessment_count(
            organization_id, start_date, end_date
        )
        session_frequency = assessments_completed / user_count if user_count > 0 else 0

        # Feature usage breadth (number of different frameworks used)
        frameworks_used = await self._get_frameworks_used(
            organization_id, start_date, end_date
        )
        feature_breadth = min(frameworks_used / 5, 1.0)  # Normalize to 0-1

        # Calculate component score (0-100)
        # DAU/MAU: 40%, Session Frequency: 30%, Feature Breadth: 30%
        score = (
            (dau_mau_ratio * 40) +
            (min(session_frequency / 4, 1.0) * 30) +  # 4 assessments/user = 100%
            (feature_breadth * 30)
        )

        # Get previous period score for trend
        prev_assessments = await self._get_assessment_count(
            organization_id, prev_start, start_date
        )
        prev_session_frequency = prev_assessments / user_count if user_count > 0 else 0
        trend = self._calculate_component_trend(session_frequency, prev_session_frequency)

        return ComponentScore(
            component_name="engagement",
            score=round(score, 2),
            weight=0.30,
            weighted_score=round(score * 0.30, 2),
            metrics={
                "dau_mau_ratio": round(dau_mau_ratio, 3),
                "session_frequency": round(session_frequency, 2),
                "feature_breadth": round(feature_breadth, 2),
            },
            trend=trend
        )

    async def _calculate_adoption(
        self,
        organization_id: str,
        lookback_days: int,
        previous_period_days: int
    ) -> ComponentScore:
        """
        Calculate Adoption Score (25% weight).

        Metrics:
        - User activation rate (% invited users who completed assessment)
        - Team adoption rate (% teams with assessments)
        - Seat utilization (active users / total seats)
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)

        # Get org metrics
        total_users = await self._get_user_count(organization_id)
        total_teams = await self._get_team_count(organization_id)

        if total_users == 0 or total_teams == 0:
            return ComponentScore(
                component_name="adoption",
                score=0.0,
                weight=0.25,
                weighted_score=0.0,
                metrics={},
                trend="stable"
            )

        # User activation rate (users who completed ≥1 assessment)
        activated_users = await self._get_activated_user_count(
            organization_id, start_date, end_date
        )
        activation_rate = (activated_users / total_users) if total_users > 0 else 0

        # Team adoption rate (teams with ≥1 assessment completed)
        adopted_teams = await self._get_adopted_team_count(
            organization_id, start_date, end_date
        )
        team_adoption_rate = (adopted_teams / total_teams) if total_teams > 0 else 0

        # Seat utilization (active users in last 30 days / total users)
        active_users = await self._get_active_user_count(organization_id, days=30)
        seat_utilization = (active_users / total_users) if total_users > 0 else 0

        # Calculate component score
        # Activation: 40%, Team Adoption: 30%, Seat Utilization: 30%
        score = (
            (activation_rate * 40) +
            (team_adoption_rate * 30) +
            (seat_utilization * 30)
        )

        return ComponentScore(
            component_name="adoption",
            score=round(score, 2),
            weight=0.25,
            weighted_score=round(score * 0.25, 2),
            metrics={
                "activation_rate": round(activation_rate, 3),
                "team_adoption_rate": round(team_adoption_rate, 3),
                "seat_utilization": round(seat_utilization, 3),
            },
            trend="stable"
        )

    async def _calculate_integration(
        self,
        organization_id: str,
        lookback_days: int,
        previous_period_days: int
    ) -> ComponentScore:
        """
        Calculate Integration Score (20% weight).

        Metrics:
        - SSO/identity provider integration
        - API usage frequency
        - Data sync/completeness
        - Custom configurations
        """
        # For now, use simplified metrics
        # In production, query integration tables

        # SSO integration (40%)
        has_sso = await self._check_sso_enabled(organization_id)
        sso_score = 100 if has_sso else 50

        # API usage (30%)
        api_calls = await self._get_api_call_count(organization_id, lookback_days)
        api_score = min(api_calls / 100, 1.0) * 100  # 100+ calls = 100%

        # Data sync completeness (30%)
        sync_score = 100  # Default to full sync

        score = (sso_score * 0.40) + (api_score * 0.30) + (sync_score * 0.30)

        return ComponentScore(
            component_name="integration",
            score=round(score, 2),
            weight=0.20,
            weighted_score=round(score * 0.20, 2),
            metrics={
                "has_sso": has_sso,
                "api_calls": api_calls,
                "sync_completeness": sync_score,
            },
            trend="stable"
        )

    async def _calculate_growth(
        self,
        organization_id: str,
        lookback_days: int,
        previous_period_days: int
    ) -> ComponentScore:
        """
        Calculate Growth Score (15% weight).

        Metrics:
        - User growth rate
        - Assessment volume growth
        - Team expansion
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)
        prev_start = start_date - timedelta(days=previous_period_days)

        # User growth
        current_users = await self._get_user_count(organization_id)
        prev_users = await self._get_user_count_at_date(organization_id, prev_start)
        user_growth_rate = self._calculate_growth_rate(current_users, prev_users)

        # Assessment volume growth
        current_assessments = await self._get_assessment_count(
            organization_id, start_date, end_date
        )
        prev_assessments = await self._get_assessment_count(
            organization_id, prev_start, start_date
        )
        assessment_growth_rate = self._calculate_growth_rate(
            current_assessments, prev_assessments
        )

        # Team growth
        current_teams = await self._get_team_count(organization_id)
        prev_teams = await self._get_team_count_at_date(organization_id, prev_start)
        team_growth_rate = self._calculate_growth_rate(current_teams, prev_teams)

        # Calculate component score
        # Positive growth = good, negative = declining
        score = min(max(
            (user_growth_rate * 40) +
            (min(assessment_growth_rate, 100) * 35) +
            (team_growth_rate * 25),
            0
        ), 100)

        # Determine trend based on overall growth direction
        avg_growth = (user_growth_rate + assessment_growth_rate + team_growth_rate) / 3
        if avg_growth > 10:
            trend = "growing"
        elif avg_growth > 0:
            trend = "stable"
        else:
            trend = "declining"

        return ComponentScore(
            component_name="growth",
            score=round(score, 2),
            weight=0.15,
            weighted_score=round(score * 0.15, 2),
            metrics={
                "user_growth_rate": round(user_growth_rate, 2),
                "assessment_growth_rate": round(assessment_growth_rate, 2),
                "team_growth_rate": round(team_growth_rate, 2),
            },
            trend=trend
        )

    async def _calculate_retention(
        self,
        organization_id: str,
        lookback_days: int,
        previous_period_days: int
    ) -> ComponentScore:
        """
        Calculate Retention Score (10% weight).

        Metrics:
        - User retention rate (% users retained)
        - Assessment completion repeat rate
        - Subscription renewal status
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)
        prev_start = start_date - timedelta(days=previous_period_days)

        # User retention
        current_users = set(await self._get_active_user_ids(organization_id, start_date, end_date))
        previous_users = set(await self._get_active_user_ids(
            organization_id, prev_start, start_date
        ))

        retained_users = len(current_users & previous_users)
        retention_rate = (retained_users / len(previous_users)) if previous_users else 1.0

        # Assessment repeat rate
        repeat_assessments = await self._get_repeat_assessment_rate(
            organization_id, start_date, end_date
        )

        # Calculate component score
        score = (retention_rate * 70) + (repeat_assessments * 30)

        return ComponentScore(
            component_name="retention",
            score=round(score, 2),
            weight=0.10,
            weighted_score=round(score * 0.10, 2),
            metrics={
                "retention_rate": round(retention_rate, 3),
                "repeat_assessment_rate": round(repeat_assessments, 3),
            },
            trend="stable"
        )

    # ==================== HELPER METHODS ====================

    async def _get_user_count(self, organization_id: str) -> int:
        """Get total user count for organization."""
        query = select(func.count(User.id)).where(
            User.organization_id == organization_id
        )
        result = await self.db.execute(query)
        return result.scalar_one() or 0

    async def _get_team_count(self, organization_id: str) -> int:
        """Get total team count for organization."""
        query = select(func.count(Team.id)).where(
            Team.organization_id == organization_id
        )
        result = await self.db.execute(query)
        return result.scalar_one() or 0

    async def _get_active_user_count(self, organization_id: str, days: int) -> int:
        """Get active user count in last N days."""
        since = datetime.utcnow() - timedelta(days=days)

        query = select(func.count(func.distinct(FactAssessmentCompletion.user_id))).where(
            and_(
                FactAssessmentCompletion.tenant_id == organization_id,
                FactAssessmentCompletion.completed_at >= since
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one() or 0

    async def _get_assessment_count(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Get assessment count in date range."""
        query = select(func.count(FactAssessmentCompletion.completion_key)).where(
            and_(
                FactAssessmentCompletion.tenant_id == organization_id,
                FactAssessmentCompletion.completed_at >= start_date,
                FactAssessmentCompletion.completed_at < end_date
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one() or 0

    async def _get_frameworks_used(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Get number of different frameworks used."""
        query = select(func.count(func.distinct(FactAssessmentCompletion.framework_key))).where(
            and_(
                FactAssessmentCompletion.tenant_id == organization_id,
                FactAssessmentCompletion.completed_at >= start_date,
                FactAssessmentCompletion.completed_at < end_date
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one() or 0

    async def _get_activated_user_count(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Get count of users who completed ≥1 assessment."""
        query = select(func.count(func.distinct(FactAssessmentCompletion.user_id))).where(
            and_(
                FactAssessmentCompletion.tenant_id == organization_id,
                FactAssessmentCompletion.completed_at >= start_date,
                FactAssessmentCompletion.completed_at < end_date
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one() or 0

    async def _get_adopted_team_count(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Get count of teams with ≥1 assessment completed."""
        query = select(func.count(func.distinct(FactAssessmentCompletion.team_id))).where(
            and_(
                FactAssessmentCompletion.tenant_id == organization_id,
                FactAssessmentCompletion.completed_at >= start_date,
                FactAssessmentCompletion.completed_at < end_date,
                FactAssessmentCompletion.team_id.isnot(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one() or 0

    async def _check_sso_enabled(self, organization_id: str) -> bool:
        """Check if SSO is enabled for organization."""
        # Simplified - in production, query organization settings
        return False

    async def _get_api_call_count(self, organization_id: str, days: int) -> int:
        """Get API call count in last N days."""
        # Simplified - in production, query API logs
        return 0

    async def _get_user_count_at_date(
        self,
        organization_id: str,
        at_date: datetime
    ) -> int:
        """Get user count at specific date."""
        # Simplified - using current count
        return await self._get_user_count(organization_id)

    async def _get_team_count_at_date(
        self,
        organization_id: str,
        at_date: datetime
    ) -> int:
        """Get team count at specific date."""
        # Simplified - using current count
        return await self._get_team_count(organization_id)

    async def _get_active_user_ids(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[str]:
        """Get list of active user IDs in date range."""
        query = select(FactAssessmentCompletion.user_id).where(
            and_(
                FactAssessmentCompletion.tenant_id == organization_id,
                FactAssessmentCompletion.completed_at >= start_date,
                FactAssessmentCompletion.completed_at < end_date
            )
        ).distinct()
        result = await self.db.execute(query)
        return [str(row[0]) for row in result.all()]

    async def _get_repeat_assessment_rate(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate assessment repeat rate."""
        # Simplified - return 0 for now
        return 0.0

    async def _get_previous_score(self, organization_id: str) -> Optional[float]:
        """Get previous CUS for trend calculation."""
        # In production, query CUS history table
        return None

    def _calculate_growth_rate(self, current: int, previous: int) -> float:
        """Calculate percentage growth rate."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100

    def _calculate_component_trend(self, current: float, previous: float) -> str:
        """Determine component trend direction."""
        if current > previous * 1.05:
            return "improving"
        elif current < previous * 0.95:
            return "declining"
        else:
            return "stable"

    def _calculate_trend(self, previous: float, current: float) -> str:
        """Determine overall score trend."""
        if current > previous * 1.05:
            return "improving"
        elif current < previous * 0.95:
            return "declining"
        else:
            return "stable"

    def _get_score_tier(self, score: float) -> ScoreTier:
        """Map score to health tier."""
        if score >= 80:
            return ScoreTier.THRIVING
        elif score >= 60:
            return ScoreTier.HEALTHY
        elif score >= 40:
            return ScoreTier.AT_RISK
        else:
            return ScoreTier.CRITICAL

    def _calculate_churn_probability(
        self,
        score: float,
        components: Dict[str, ComponentScore]
    ) -> float:
        """
        Calculate churn probability based on score and components.

        Higher churn risk factors:
        - Low engagement
        - Declining adoption
        - Poor retention
        """
        # Base churn probability from score (inverted)
        base_churn = (100 - score) / 100

        # Adjust based on component trends
        retention_trend = components["retention"].trend
        if retention_trend == "declining":
            base_churn *= 1.5

        engagement_trend = components["engagement"].trend
        if engagement_trend == "declining":
            base_churn *= 1.2

        # Clamp to 0-1
        return max(0.0, min(1.0, base_churn))

    def _generate_insights(
        self,
        components: Dict[str, ComponentScore],
        total_score: float
    ) -> List[str]:
        """Generate human-readable insights from scores."""
        insights = []

        # Overall health
        if total_score >= 80:
            insights.append("Customer is thriving with excellent product engagement.")
        elif total_score >= 60:
            insights.append("Customer shows healthy engagement levels.")
        elif total_score >= 40:
            insights.append("Customer shows moderate engagement with improvement opportunities.")
        else:
            insights.append("Customer is at high risk of churn - immediate attention needed.")

        # Component-specific insights
        eng = components["engagement"]
        if eng.score < 50:
            insights.append(f"Low engagement ({eng.score:.0f}/100) - users not actively using platform.")

        ado = components["adoption"]
        if ado.score < 50:
            insights.append(f"Poor adoption ({ado.score:.0f}/100) - low team activation rate.")

        growth = components["growth"]
        if growth.trend == "declining":
            insights.append("Declining growth trend - usage metrics are decreasing.")

        return insights

    def _generate_recommendations(
        self,
        components: Dict[str, ComponentScore],
        tier: ScoreTier
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if tier in [ScoreTier.CRITICAL, ScoreTier.AT_RISK]:
            recommendations.append("Schedule customer success call immediately")
            recommendations.append("Review onboarding process and completion rates")

        eng = components["engagement"]
        if eng.score < 60:
            recommendations.append("Launch user engagement campaign")
            recommendations.append("Provide training on key features")

        ado = components["adoption"]
        if ado.score < 60:
            recommendations.append("Focus on team-level adoption")
            recommendations.append("Identify and onboard power users")

        integ = components["integration"]
        if integ.score < 60:
            recommendations.append("Discuss integration opportunities")
            recommendations.append("Offer API support and documentation")

        return recommendations

    async def get_at_risk_customers(
        self,
        score_threshold: float = 40.0,
        limit: int = 50
    ) -> List[CustomerUsageScore]:
        """
        Get all customers at or below score threshold.

        Args:
            score_threshold: Maximum score for "at risk" (default: 40)
            limit: Maximum number of customers to return

        Returns:
            List of CustomerUsageScore for at-risk customers
        """
        # Get all organizations
        query = select(Organization.id).limit(limit)
        result = await self.db.execute(query)
        org_ids = [str(row[0]) for row in result.all()]

        # Calculate scores for each
        at_risk = []
        for org_id in org_ids:
            score = await self.calculate_score(org_id)
            if score.score <= score_threshold:
                at_risk.append(score)

        # Sort by score (lowest first)
        at_risk.sort(key=lambda x: x.score)

        return at_risk
