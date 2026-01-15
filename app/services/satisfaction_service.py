"""
Satisfaction Scoring Service

Business logic for calculating and managing CSAT, NPS, CES, and CSI scores.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Tuple
from uuid import UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from sqlalchemy.sql import text

from app.db.models.satisfaction import (
    SatisfactionSurvey,
    SatisfactionAggregation,
    CompositeSatisfactionIndex,
    CustomerLifecycleStage,
    SatisfactionFollowUp,
    SurveyType,
    TouchpointType,
    NPSCategory
)


class SatisfactionScoringService:
    """
    Service for calculating and managing satisfaction scores.

    Provides methods for:
    - Recording survey responses
    - Calculating CSAT, NPS, CES metrics
    - Computing Composite Satisfaction Index (CSI)
    - Managing customer lifecycle stages
    - Creating and tracking follow-up actions
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # SURVEY RESPONSE MANAGEMENT
    # ========================================================================

    async def record_survey_response(
        self,
        user_id: UUID,
        survey_type: SurveyType,
        score: int,
        touchpoint_type: Optional[TouchpointType] = None,
        feedback_text: Optional[str] = None,
        follow_up_consent: bool = True,
        survey_channel: str = "in_app",
        context: Optional[Dict] = None,
        organization_id: Optional[UUID] = None,
        sent_at: Optional[datetime] = None
    ) -> SatisfactionSurvey:
        """
        Record a satisfaction survey response.

        Args:
            user_id: User who responded
            survey_type: Type of survey (CSAT, NPS, CES)
            score: Response score (CSAT: 1-5, NPS: 0-10, CES: 1-7)
            touchpoint_type: Type of touchpoint being measured
            feedback_text: Optional open-ended feedback
            follow_up_consent: User consents to follow-up contact
            survey_channel: How the survey was delivered
            context: Additional context (JSON)
            organization_id: User's organization
            sent_at: When the survey was sent

        Returns:
            Created SatisfactionSurvey record
        """
        # Validate score based on survey type
        self._validate_score(survey_type, score)

        # Auto-categorize NPS responses
        nps_category = None
        if survey_type == SurveyType.NPS:
            nps_category = self._categorize_nps_response(score)

        # Create survey response
        survey = SatisfactionSurvey(
            user_id=user_id,
            organization_id=organization_id,
            tenant_id=organization_id,
            survey_type=survey_type,
            touchpoint_type=touchpoint_type,
            score=score,
            feedback_text=feedback_text,
            follow_up_consent=follow_up_consent,
            nps_category=nps_category,
            survey_channel=survey_channel,
            context=context or {},
            sent_at=sent_at or datetime.now(timezone.utc),
            responded_at=datetime.now(timezone.utc)
        )

        self.db.add(survey)
        await self.db.commit()
        await self.db.refresh(survey)

        # Trigger follow-up for low scores
        if self._requires_follow_up(survey_type, score):
            await self._create_follow_up(survey)

        return survey

    def _validate_score(self, survey_type: SurveyType, score: int) -> None:
        """Validate score is within acceptable range for survey type."""
        ranges = {
            SurveyType.CSAT: (1, 5),
            SurveyType.NPS: (0, 10),
            SurveyType.CES: (1, 7)
        }

        min_score, max_score = ranges[survey_type]
        if not (min_score <= score <= max_score):
            raise ValueError(
                f"Invalid score {score} for {survey_type.value}. "
                f"Must be between {min_score} and {max_score}."
            )

    def _categorize_nps_response(self, score: int) -> NPSCategory:
        """Categorize NPS response as Promoter, Passive, or Detractor."""
        if score >= 9:
            return NPSCategory.PROMOTER
        elif score >= 7:
            return NPSCategory.PASSIVE
        else:
            return NPSCategory.DETRACTOR

    def _requires_follow_up(self, survey_type: SurveyType, score: int) -> bool:
        """Determine if response requires follow-up action."""
        if survey_type == SurveyType.CSAT:
            return score <= 2  # Very dissatisfied
        elif survey_type == SurveyType.NPS:
            return score <= 6  # Detractor
        elif survey_type == SurveyType.CES:
            return score <= 3  # Difficult
        return False

    async def _create_follow_up(self, survey: SatisfactionSurvey) -> SatisfactionFollowUp:
        """Create a new resource.

Args:
    db: Database session
    **kwargs: Resource attributes

Returns:
    Created resource object

Raises:
    ValidationError: If input data is invalid
        """
        """Create a follow-up action for low-scoring surveys."""
        # Determine alert level
        if survey.survey_type == SurveyType.NPS and survey.score <= 3:
            alert_level = "red"  # Critical detractor
        elif survey.survey_type == SurveyType.CSAT and survey.score == 1:
            alert_level = "red"  # Very dissatisfied
        else:
            alert_level = "yellow"  # Needs attention

        # Due date: Red alerts within 4 hours, yellow within 24 hours
        if alert_level == "red":
            due_at = datetime.now(timezone.utc) + timedelta(hours=4)
        else:
            due_at = datetime.now(timezone.utc) + timedelta(hours=24)

        follow_up = SatisfactionFollowUp(
            survey_id=survey.id,
            user_id=survey.user_id,
            organization_id=survey.organization_id,
            alert_level=alert_level,
            follow_up_type="email",
            follow_up_status="pending",
            due_at=due_at
        )

        self.db.add(follow_up)
        await self.db.commit()

        return follow_up

    # ========================================================================
    # CSAT CALCULATIONS
    # ========================================================================

    async def calculate_csat(
        self,
        touchpoint_type: Optional[TouchpointType] = None,
        organization_id: Optional[UUID] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> Dict:
        """
        Calculate CSAT (Customer Satisfaction Score).

        CSAT = (Number of satisfied responses / Total responses) × 100
        Satisfied = Rating of 4 or 5

        Args:
            touchpoint_type: Filter by touchpoint
            organization_id: Filter by organization
            period_start: Start of period (default: 30 days ago)
            period_end: End of period (default: now)

        Returns:
            Dict with CSAT metrics
        """
        period_start = period_start or (datetime.now(timezone.utc) - timedelta(days=30))
        period_end = period_end or datetime.now(timezone.utc)

        # Build query
        query = select(SatisfactionSurvey).where(
            and_(
                SatisfactionSurvey.survey_type == SurveyType.CSAT,
                SatisfactionSurvey.responded_at >= period_start,
                SatisfactionSurvey.responded_at <= period_end
            )
        )

        if touchpoint_type:
            query = query.where(SatisfactionSurvey.touchpoint_type == touchpoint_type)
        if organization_id:
            query = query.where(SatisfactionSurvey.organization_id == organization_id)

        result = await self.db.execute(query)
        responses = result.scalars().all()

        if not responses:
            return {
                "csat_percentage": 0.0,
                "total_responses": 0,
                "satisfied_count": 0,
                "average_score": 0.0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

        # Calculate metrics
        total_responses = len(responses)
        satisfied_count = sum(1 for r in responses if r.score >= 4)
        csat_percentage = (satisfied_count / total_responses) * 100
        average_score = sum(r.score for r in responses) / total_responses

        # Rating distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for response in responses:
            distribution[response.score] += 1

        return {
            "csat_percentage": round(csat_percentage, 1),
            "total_responses": total_responses,
            "satisfied_count": satisfied_count,
            "average_score": round(average_score, 2),
            "rating_distribution": distribution,
            "benchmark": self._get_csat_benchmark(csat_percentage)
        }

    def _get_csat_benchmark(self, csat_percentage: float) -> str:
        """Get benchmark classification for CSAT score."""
        if csat_percentage >= 90:
            return "excellent"
        elif csat_percentage >= 80:
            return "good"
        elif csat_percentage >= 70:
            return "average"
        else:
            return "poor"

    # ========================================================================
    # NPS CALCULATIONS
    # ========================================================================

    async def calculate_nps(
        self,
        organization_id: Optional[UUID] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> Dict:
        """
        Calculate NPS (Net Promoter Score).

        NPS = % Promoters - % Detractors
        Promoters = Score 9-10
        Passives = Score 7-8
        Detractors = Score 0-6

        Args:
            organization_id: Filter by organization
            period_start: Start of period (default: 90 days ago)
            period_end: End of period (default: now)

        Returns:
            Dict with NPS metrics
        """
        period_start = period_start or (datetime.now(timezone.utc) - timedelta(days=90))
        period_end = period_end or datetime.now(timezone.utc)

        # Build query
        query = select(SatisfactionSurvey).where(
            and_(
                SatisfactionSurvey.survey_type == SurveyType.NPS,
                SatisfactionSurvey.responded_at >= period_start,
                SatisfactionSurvey.responded_at <= period_end
            )
        )

        if organization_id:
            query = query.where(SatisfactionSurvey.organization_id == organization_id)

        result = await self.db.execute(query)
        responses = result.scalars().all()

        if not responses:
            return {
                "nps_score": 0,
                "total_responses": 0,
                "promoter_count": 0,
                "promoter_percentage": 0.0,
                "passive_count": 0,
                "passive_percentage": 0.0,
                "detractor_count": 0,
                "detractor_percentage": 0.0,
                "benchmark": "no_data"
            }

        # Calculate metrics
        total_responses = len(responses)
        promoters = sum(1 for r in responses if r.score >= 9)
        passives = sum(1 for r in responses if 7 <= r.score <= 8)
        detractors = sum(1 for r in responses if r.score <= 6)

        promoter_pct = (promoters / total_responses) * 100
        detractor_pct = (detractors / total_responses) * 100
        nps_score = int(promoter_pct - detractor_pct)

        return {
            "nps_score": nps_score,
            "total_responses": total_responses,
            "promoter_count": promoters,
            "promoter_percentage": round(promoter_pct, 1),
            "passive_count": passives,
            "passive_percentage": round((passives / total_responses) * 100, 1),
            "detractor_count": detractors,
            "detractor_percentage": round(detractor_pct, 1),
            "benchmark": self._get_nps_benchmark(nps_score)
        }

    def _get_nps_benchmark(self, nps_score: int) -> str:
        """Get benchmark classification for NPS score."""
        if nps_score >= 70:
            return "excellent"
        elif nps_score >= 40:
            return "good"
        elif nps_score >= 10:
            return "average"
        else:
            return "poor"

    # ========================================================================
    # CES CALCULATIONS
    # ========================================================================

    async def calculate_ces(
        self,
        touchpoint_type: Optional[TouchpointType] = None,
        organization_id: Optional[UUID] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> Dict:
        """
        Calculate CES (Customer Effort Score).

        CES = Average of all responses (1-7 scale)
        Higher = Easier = Better

        Args:
            touchpoint_type: Filter by touchpoint
            organization_id: Filter by organization
            period_start: Start of period (default: 30 days ago)
            period_end: End of period (default: now)

        Returns:
            Dict with CES metrics
        """
        period_start = period_start or (datetime.now(timezone.utc) - timedelta(days=30))
        period_end = period_end or datetime.now(timezone.utc)

        # Build query
        query = select(SatisfactionSurvey).where(
            and_(
                SatisfactionSurvey.survey_type == SurveyType.CES,
                SatisfactionSurvey.responded_at >= period_start,
                SatisfactionSurvey.responded_at <= period_end
            )
        )

        if touchpoint_type:
            query = query.where(SatisfactionSurvey.touchpoint_type == touchpoint_type)
        if organization_id:
            query = query.where(SatisfactionSurvey.organization_id == organization_id)

        result = await self.db.execute(query)
        responses = result.scalars().all()

        if not responses:
            return {
                "ces_score": 0.0,
                "total_responses": 0,
                "easy_count": 0,
                "ease_percentage": 0.0,
                "benchmark": "no_data"
            }

        # Calculate metrics
        total_responses = len(responses)
        ces_score = sum(r.score for r in responses) / total_responses
        easy_count = sum(1 for r in responses if r.score >= 5)
        ease_percentage = (easy_count / total_responses) * 100

        return {
            "ces_score": round(ces_score, 2),
            "total_responses": total_responses,
            "easy_count": easy_count,
            "ease_percentage": round(ease_percentage, 1),
            "benchmark": self._get_ces_benchmark(ces_score)
        }

    def _get_ces_benchmark(self, ces_score: float) -> str:
        """Get benchmark classification for CES score."""
        if ces_score >= 6.0:
            return "excellent"
        elif ces_score >= 5.5:
            return "good"
        elif ces_score >= 5.0:
            return "average"
        else:
            return "poor"

    # ========================================================================
    # COMPOSITE SATISFACTION INDEX (CSI)
    # ========================================================================

    async def calculate_csi(
        self,
        organization_id: Optional[UUID] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> Dict:
        """
        Calculate Composite Satisfaction Index (CSI).

        CSI = (CSAT × 0.25) + (NPS_normalized × 0.50) + (CES_normalized × 0.25)

        Where:
        - CSAT: 0-100 scale
        - NPS_normalized: (NPS + 100) / 2 (converts -100..100 to 0..100)
        - CES_normalized: (CES / 7) × 100 (converts 1..7 to 0..100)

        Args:
            organization_id: Filter by organization
            period_start: Start of period
            period_end: End of period

        Returns:
            Dict with CSI metrics
        """
        period_start = period_start or (datetime.now(timezone.utc) - timedelta(days=90))
        period_end = period_end or datetime.now(timezone.utc)

        # Get component scores
        csat_data = await self.calculate_csat(organization_id=organization_id,
                                               period_start=period_start,
                                               period_end=period_end)
        nps_data = await self.calculate_nps(organization_id=organization_id,
                                            period_start=period_start,
                                            period_end=period_end)
        ces_data = await self.calculate_ces(organization_id=organization_id,
                                            period_start=period_start,
                                            period_end=period_end)

        # Normalize scores to 0-100 scale
        csat_normalized = csat_data["csat_percentage"]
        nps_normalized = (nps_data["nps_score"] + 100) / 2
        ces_normalized = (ces_data["ces_score"] / 7) * 100 if ces_data["ces_score"] > 0 else 0

        # Calculate CSI
        csi_score = (csat_normalized * 0.25) + (nps_normalized * 0.50) + (ces_normalized * 0.25)

        # Get previous period for trend analysis
        previous_period_start = period_start - timedelta(days=90)
        previous_period_end = period_start
        previous_csi = await self._get_previous_csi(organization_id,
                                                     previous_period_start,
                                                     previous_period_end)

        # Calculate trend
        change_amount = None
        change_percentage = None
        if previous_csi is not None:
            change_amount = csi_score - previous_csi
            change_percentage = ((csi_score - previous_csi) / previous_csi) * 100 if previous_csi > 0 else 0

        return {
            "csi_score": round(csi_score, 1),
            "csat_score": round(csat_normalized, 1),
            "nps_raw": nps_data["nps_score"],
            "nps_normalized": round(nps_normalized, 1),
            "ces_score": round(ces_normalized, 1),
            "performance_level": self._get_csi_performance_level(csi_score),
            "previous_csi_score": previous_csi,
            "change_amount": round(change_amount, 1) if change_amount is not None else None,
            "change_percentage": round(change_percentage, 1) if change_percentage is not None else None
        }

    async def _get_previous_csi(
        self,
        organization_id: Optional[UUID],
        period_start: datetime,
        period_end: datetime
    ) -> Optional[float]:
        """Get CSI score from previous period for trend comparison."""
        # Get component scores
        csat_data = await self.calculate_csat(organization_id=organization_id,
                                               period_start=period_start,
                                               period_end=period_end)
        nps_data = await self.calculate_nps(organization_id=organization_id,
                                            period_start=period_start,
                                            period_end=period_end)
        ces_data = await self.calculate_ces(organization_id=organization_id,
                                            period_start=period_start,
                                            period_end=period_end)

        # Check if we have data
        if csat_data["total_responses"] == 0:
            return None

        # Calculate CSI
        csat_normalized = csat_data["csat_percentage"]
        nps_normalized = (nps_data["nps_score"] + 100) / 2
        ces_normalized = (ces_data["ces_score"] / 7) * 100 if ces_data["ces_score"] > 0 else 0

        csi_score = (csat_normalized * 0.25) + (nps_normalized * 0.50) + (ces_normalized * 0.25)
        return csi_score

    def _get_csi_performance_level(self, csi_score: float) -> str:
        """Get performance level classification for CSI score."""
        if csi_score >= 90:
            return "exceptional"
        elif csi_score >= 80:
            return "excellent"
        elif csi_score >= 70:
            return "good"
        elif csi_score >= 60:
            return "fair"
        else:
            return "poor"

    # ========================================================================
    # CUSTOMER LIFECYCLE MANAGEMENT
    # ========================================================================

    async def update_lifecycle_stage(
        self,
        user_id: UUID,
        new_stage: str,
        organization_id: Optional[UUID] = None,
        entered_via: Optional[str] = None,
        conversion_source: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> CustomerLifecycleStage:
        """
        Update user's lifecycle stage.

        Stages: awareness, consideration, purchase, adoption, growth, retention, advocacy

        Args:
            user_id: User to update
            new_stage: New lifecycle stage
            organization_id: User's organization
            entered_via: How they entered this stage
            conversion_source: Source of conversion
            context: Additional context (JSON)

        Returns:
            Created CustomerLifecycleStage record
        """
        # Get current stage
        current_stage_query = select(CustomerLifecycleStage).where(
            and_(
                CustomerLifecycleStage.user_id == user_id,
                CustomerLifecycleStage.stage_exit_date.is_(None)
            )
        ).order_by(CustomerLifecycleStage.stage_entry_date.desc())

        result = await self.db.execute(current_stage_query)
        current_stage_record = result.scalar_one_or_none()

        # Close current stage if exists
        if current_stage_record:
            current_stage_record.stage_exit_date = datetime.now(timezone.utc)
            days_in_stage = (datetime.now(timezone.utc) - current_stage_record.stage_entry_date).days
            current_stage_record.days_in_stage = days_in_stage

        # Create new stage record
        new_stage_record = CustomerLifecycleStage(
            user_id=user_id,
            organization_id=organization_id,
            tenant_id=organization_id,
            current_stage=new_stage,
            previous_stage=current_stage_record.current_stage if current_stage_record else None,
            stage_entry_date=datetime.now(timezone.utc),
            entered_via=entered_via,
            conversion_source=conversion_source,
            context=context or {}
        )

        self.db.add(new_stage_record)
        await self.db.commit()
        await self.db.refresh(new_stage_record)

        return new_stage_record

    async def get_lifecycle_summary(
        self,
        organization_id: Optional[UUID] = None
    ) -> Dict:
        """
        Get summary of customers by lifecycle stage.

        Args:
            organization_id: Filter by organization

        Returns:
            Dict with counts and percentages by stage
        """
        query = select(
            CustomerLifecycleStage.current_stage,
            func.count(CustomerLifecycleStage.id).label('count')
        ).where(
            CustomerLifecycleStage.stage_exit_date.is_(None)
        )

        if organization_id:
            query = query.where(CustomerLifecycleStage.organization_id == organization_id)

        query = query.group_by(CustomerLifecycleStage.current_stage)

        result = await self.db.execute(query)
        stages = result.all()

        total_customers = sum(stage.count for stage in stages)

        summary = {}
        for stage in stages:
            summary[stage.current_stage] = {
                "count": stage.count,
                "percentage": round((stage.count / total_customers * 100), 1) if total_customers > 0 else 0
            }

        return summary
