"""
OKR (Objectives and Key Results) Service

Business logic for managing OKRs, tracking progress, and calculating
achievement rates. Implements the OKR framework defined in the quarterly
product team OKRs document.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.okr import (
    Initiative,
    KeyResult,
    KRProgressUpdate,
    KRStatus,
    Objective,
    OKRCheckIn,
    OKRPeriod,
    OKRRetrospective,
    OKRStatus,
)


class OKRService:
    """
    Service for managing Objectives and Key Results.

    Provides methods for:
    - Creating and updating objectives and key results
    - Tracking progress and calculating achievement
    - Managing initiatives and check-ins
    - Running retrospectives
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # OBJECTIVE MANAGEMENT
    # ========================================================================

    async def create_objective(
        self,
        title: str,
        owner_id: UUID,
        period: OKRPeriod,
        year: int,
        start_date: datetime,
        end_date: datetime,
        objective_type: str,
        organization_id: Optional[UUID] = None,
        team: Optional[str] = None,
        description: Optional[str] = None,
        strategic_priority: Optional[str] = None,
        parent_objective_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> Objective:
        """
        Create a new Objective.

        Args:
            title: Objective title (what we want to achieve)
            owner_id: User responsible for this objective
            period: Time period (Q1, Q2, Q3, Q4, H1, H2, annual)
            year: Year (e.g., 2025)
            start_date: Start date
            end_date: End date
            objective_type: Type (growth, excellence, innovation, enterprise)
            organization_id: Organization (optional)
            team: Team name (Product, Engineering, etc.)
            description: Detailed description
            strategic_priority: Strategic priority (revenue, satisfaction, etc.)
            parent_objective_id: Parent objective (for cascading OKRs)
            tags: Tags for categorization
            context: Additional context (JSON)

        Returns:
            Created Objective
        """
        objective = Objective(
            title=title,
            owner_id=owner_id,
            organization_id=organization_id,
            tenant_id=organization_id,
            period=period,
            year=year,
            start_date=start_date,
            end_date=end_date,
            objective_type=objective_type,
            team=team,
            description=description,
            strategic_priority=strategic_priority,
            parent_objective_id=parent_objective_id,
            status=OKRStatus.DRAFT,
            progress_percentage=0.0,
            tags=tags or [],
            context=context or {},
        )

        self.db.add(objective)
        await self.db.commit()
        await self.db.refresh(objective)

        return objective

    async def activate_objective(self, objective_id: UUID) -> Objective:
        """Activate an objective (change status from DRAFT to ACTIVE)."""
        query = select(Objective).where(Objective.id == objective_id)
        result = await self.db.execute(query)
        objective = result.scalar_one_or_none()

        if not objective:
            raise ValueError(f"Objective {objective_id} not found")

        if objective.status != OKRStatus.DRAFT:
            raise ValueError(
                f"Objective must be in DRAFT status to activate. Current: {objective.status}"
            )

        # Check if all KRs are defined
        if not objective.key_results:
            raise ValueError(
                "Cannot activate objective without key results. Add at least one key result first."
            )

        objective.status = OKRStatus.ACTIVE
        await self.db.commit()
        await self.db.refresh(objective)

        return objective

    async def update_objective_progress(self, objective_id: UUID) -> Objective:
        """Update an existing resource.

        Args:
            db: Database session
            id: Resource ID
            **kwargs: Attributes to update

        Returns:
            Updated resource object

        Raises:
            NotFoundError: If resource doesn't exist
            ValidationError: If input data is invalid
        """
        """
        Recalculate objective progress based on weighted average of key results.

        Progress = Σ(KR_progress × KR_weight) / Σ(KR_weights)
        """
        query = (
            select(Objective)
            .options(selectinload(Objective.key_results))
            .where(Objective.id == objective_id)
        )

        result = await self.db.execute(query)
        objective = result.scalar_one_or_none()

        if not objective:
            raise ValueError(f"Objective {objective_id} not found")

        if not objective.key_results:
            objective.progress_percentage = 0.0
        else:
            total_weight = sum(kr.weight for kr in objective.key_results)
            weighted_progress = sum(
                kr.progress_percentage * kr.weight for kr in objective.key_results
            )
            objective.progress_percentage = (
                weighted_progress / total_weight if total_weight > 0 else 0.0
            )

        # Auto-complete objective if progress >= 100% and all KRs achieved
        if objective.progress_percentage >= 100.0:
            all_krs_achieved = all(
                kr.status in [KRStatus.ACHIEVED, KRStatus.ON_TRACK]
                for kr in objective.key_results
            )
            if all_krs_achieved:
                objective.status = OKRStatus.COMPLETED
                objective.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(objective)

        return objective

    # ========================================================================
    # KEY RESULT MANAGEMENT
    # ========================================================================

    async def create_key_result(
        self,
        objective_id: UUID,
        title: str,
        owner_id: UUID,
        target_value: float,
        unit_of_measure: str,
        start_date: datetime,
        end_date: datetime,
        baseline_value: Optional[float] = None,
        description: Optional[str] = None,
        weight: float = 1.0,
        depends_on_kr_ids: Optional[List[UUID]] = None,
        tags: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> KeyResult:
        """
        Create a new Key Result.

        Args:
            objective_id: Parent objective
            title: KR title
            owner_id: User responsible
            target_value: Target to achieve
            unit_of_measure: Unit (percentage, currency, count, score)
            start_date: Start date
            end_date: End date
            baseline_value: Starting value
            description: Detailed description
            weight: Weight within objective (default: 1.0)
            depends_on_kr_ids: KRs that must complete first
            tags: Tags for categorization
            context: Additional context

        Returns:
            Created KeyResult
        """
        # Validate objective exists
        objective_query = select(Objective).where(Objective.id == objective_id)
        result = await self.db.execute(objective_query)
        objective = result.scalar_one_or_none()

        if not objective:
            raise ValueError(f"Objective {objective_id} not found")

        # Calculate initial progress
        current_value = baseline_value or 0.0
        progress_percentage = self._calculate_kr_progress(
            current_value, baseline_value or 0.0, target_value
        )

        # Determine initial status
        status = KRStatus.NOT_STARTED
        if progress_percentage > 0:
            status = KRStatus.ON_TRACK

        key_result = KeyResult(
            objective_id=objective_id,
            owner_id=owner_id,
            title=title,
            description=description,
            target_value=target_value,
            current_value=current_value,
            baseline_value=baseline_value,
            unit_of_measure=unit_of_measure,
            start_date=start_date,
            end_date=end_date,
            weight=weight,
            progress_percentage=progress_percentage,
            status=status,
            depends_on_kr_ids=depends_on_kr_ids or [],
            tags=tags or [],
            context=context or {},
        )

        self.db.add(key_result)
        await self.db.commit()
        await self.db.refresh(key_result)

        # Update objective progress
        await self.update_objective_progress(objective_id)

        return key_result

    async def update_key_result_progress(
        self,
        key_result_id: UUID,
        current_value: float,
        updated_by: UUID,
        notes: Optional[str] = None,
        blockers: Optional[str] = None,
        next_steps: Optional[str] = None,
        confidence_level: Optional[str] = None,
        sentiment: Optional[str] = None,
    ) -> KeyResult:
        """
        Update key result progress and create progress update record.

        Args:
            key_result_id: KR to update
            current_value: New current value
            updated_by: User making the update
            notes: Progress notes
            blockers: Current blockers
            next_steps: Planned next steps
            confidence_level: Confidence (high, medium, low)
            sentiment: Sentiment (positive, neutral, negative)

        Returns:
            Updated KeyResult
        """
        # Get KR
        query = select(KeyResult).where(KeyResult.id == key_result_id)
        result = await self.db.execute(query)
        kr = result.scalar_one_or_none()

        if not kr:
            raise ValueError(f"KeyResult {key_result_id} not found")

        # Update values
        kr.current_value = current_value
        kr.progress_percentage = self._calculate_kr_progress(
            current_value, kr.baseline_value or 0.0, kr.target_value
        )

        # Update status based on progress
        kr.status = self._determine_kr_status(
            kr.progress_percentage, kr.end_date, confidence_level
        )
        kr.confidence_level = confidence_level or kr.confidence_level

        # Mark as achieved if 100%+
        if kr.progress_percentage >= 100.0 and kr.status != KRStatus.ACHIEVED:
            kr.status = KRStatus.ACHIEVED
            kr.achieved_at = datetime.now(timezone.utc)
            kr.final_value = current_value

        # Create progress update
        progress_update = KRProgressUpdate(
            key_result_id=key_result_id,
            updated_by=updated_by,
            current_value=current_value,
            progress_percentage=kr.progress_percentage,
            status=kr.status,
            notes=notes,
            blockers=blockers,
            next_steps=next_steps,
            confidence_level=confidence_level,
            sentiment=sentiment,
            update_date=datetime.now(timezone.utc),
        )

        self.db.add(progress_update)
        await self.db.commit()
        await self.db.refresh(kr)

        # Update objective progress
        await self.update_objective_progress(kr.objective_id)

        return kr

    def _calculate_kr_progress(
        self, current_value: float, baseline_value: float, target_value: float
    ) -> float:
        """
        Calculate KR progress percentage.

        Formula: ((current - baseline) / (target - baseline)) × 100
        """
        if target_value == baseline_value:
            return 100.0 if current_value >= target_value else 0.0

        progress = (
            (current_value - baseline_value) / (target_value - baseline_value)
        ) * 100
        return max(0.0, min(100.0, progress))  # Clamp between 0-100

    def _determine_kr_status(
        self,
        progress_percentage: float,
        end_date: datetime,
        confidence_level: Optional[str] = None,
    ) -> KRStatus:
        """
        Determine KR health status based on progress and timeline.

        Rules:
        - 100%+ = ACHIEVED
        - On track with high/medium confidence = ON_TRACK
        - Behind schedule or low confidence = AT_RISK
        - Far behind or no progress = OFF_TRACK
        """
        if progress_percentage >= 100.0:
            return KRStatus.ACHIEVED

        days_remaining = (end_date - datetime.now(timezone.utc)).days

        # Use confidence level if provided
        if confidence_level == "low" and progress_percentage < 50:
            return KRStatus.AT_RISK

        # Time-based assessment
        if days_remaining < 0:
            # Past due date
            return KRStatus.OFF_TRACK if progress_percentage < 90 else KRStatus.ON_TRACK
        elif days_remaining < 7:
            # Less than 1 week
            if progress_percentage < 80:
                return KRStatus.OFF_TRACK
            elif progress_percentage < 90:
                return KRStatus.AT_RISK
            else:
                return KRStatus.ON_TRACK
        elif days_remaining < 30:
            # Less than 1 month
            expected_progress = ((30 - days_remaining) / 30) * 100
            if progress_percentage < expected_progress - 20:
                return KRStatus.OFF_TRACK
            elif progress_percentage < expected_progress:
                return KRStatus.AT_RISK
            else:
                return KRStatus.ON_TRACK
        else:
            # More than 1 month remaining
            if progress_percentage < 10:
                return KRStatus.NOT_STARTED
            else:
                return KRStatus.ON_TRACK

    # ========================================================================
    # INITIATIVE MANAGEMENT
    # ========================================================================

    async def create_initiative(
        self,
        key_result_id: UUID,
        title: str,
        owner_id: UUID,
        planned_start_date: datetime,
        planned_end_date: datetime,
        description: Optional[str] = None,
        estimated_hours: Optional[int] = None,
        depends_on_initiative_ids: Optional[List[UUID]] = None,
        tags: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> Initiative:
        """
        Create a new Initiative.

        Initiatives are the specific projects/tasks that drive Key Results.
        """
        # Validate KR exists
        kr_query = select(KeyResult).where(KeyResult.id == key_result_id)
        result = await self.db.execute(kr_query)
        kr = result.scalar_one_or_none()

        if not kr:
            raise ValueError(f"KeyResult {key_result_id} not found")

        initiative = Initiative(
            key_result_id=key_result_id,
            owner_id=owner_id,
            title=title,
            description=description,
            planned_start_date=planned_start_date,
            planned_end_date=planned_end_date,
            estimated_hours=estimated_hours,
            depends_on_initiative_ids=depends_on_initiative_ids or [],
            status="not_started",
            completion_percentage=0,
            tags=tags or [],
            context=context or {},
        )

        self.db.add(initiative)
        await self.db.commit()
        await self.db.refresh(initiative)

        return initiative

    async def update_initiative_status(
        self,
        initiative_id: UUID,
        status: str,
        completion_percentage: int,
        actual_hours: Optional[int] = None,
        outcome_summary: Optional[str] = None,
    ) -> Initiative:
        """Update initiative status and completion."""
        query = select(Initiative).where(Initiative.id == initiative_id)
        result = await self.db.execute(query)
        initiative = result.scalar_one_or_none()

        if not initiative:
            raise ValueError(f"Initiative {initiative_id} not found")

        initiative.status = status
        initiative.completion_percentage = completion_percentage

        if actual_hours is not None:
            initiative.actual_hours = actual_hours

        if outcome_summary:
            initiative.outcome_summary = outcome_summary

        # Set completion date if completed
        if status == "completed" and not initiative.completed_at:
            initiative.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(initiative)

        return initiative

    # ========================================================================
    # CHECK-IN MANAGEMENT
    # ========================================================================

    async def create_check_in(
        self,
        team: str,
        meeting_date: datetime,
        meeting_type: str,
        attendee_ids: List[UUID],
        organization_id: Optional[UUID] = None,
        agenda_items: Optional[List[str]] = None,
        objectives_reviewed: Optional[List[Dict]] = None,
        overall_health: Optional[str] = None,
        action_items: Optional[List[Dict]] = None,
        decisions_made: Optional[str] = None,
        discussions: Optional[str] = None,
        next_check_in_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> OKRCheckIn:
        """Create an OKR check-in meeting record."""
        check_in = OKRCheckIn(
            organization_id=organization_id,
            team=team,
            meeting_date=meeting_date,
            meeting_type=meeting_type,
            attendee_ids=attendee_ids,
            agenda_items=agenda_items or [],
            objectives_reviewed=objectives_reviewed or [],
            overall_health=overall_health,
            action_items=action_items or [],
            decisions_made=decisions_made,
            discussions=discussions,
            next_check_in_date=next_check_in_date,
            notes=notes,
        )

        self.db.add(check_in)
        await self.db.commit()
        await self.db.refresh(check_in)

        return check_in

    # ========================================================================
    # REPORTING AND ANALYTICS
    # ========================================================================

    async def get_okr_summary(
        self,
        period: OKRPeriod,
        year: int,
        organization_id: Optional[UUID] = None,
        team: Optional[str] = None,
    ) -> Dict:
        """
        Get OKR summary for a period.

        Returns:
            Dict with objectives, KRs, initiatives, and overall health
        """
        # Build query
        query = (
            select(Objective)
            .options(selectinload(Objective.key_results))
            .where(
                and_(
                    Objective.period == period,
                    Objective.year == year,
                    Objective.status.in_([OKRStatus.ACTIVE, OKRStatus.COMPLETED]),
                )
            )
        )

        if organization_id:
            query = query.where(Objective.organization_id == organization_id)
        if team:
            query = query.where(Objective.team == team)

        result = await self.db.execute(query)
        objectives = result.scalars().all()

        # Calculate metrics
        total_objectives = len(objectives)
        completed_objectives = sum(
            1 for o in objectives if o.status == OKRStatus.COMPLETED
        )

        total_krs = sum(len(o.key_results) for o in objectives)
        achieved_krs = sum(
            sum(1 for kr in o.key_results if kr.status == KRStatus.ACHIEVED)
            for o in objectives
        )
        on_track_krs = sum(
            sum(1 for kr in o.key_results if kr.status == KRStatus.ON_TRACK)
            for o in objectives
        )
        at_risk_krs = sum(
            sum(1 for kr in o.key_results if kr.status == KRStatus.AT_RISK)
            for o in objectives
        )
        off_track_krs = sum(
            sum(1 for kr in o.key_results if kr.status == KRStatus.OFF_TRACK)
            for o in objectives
        )

        # Calculate overall health
        success_rate = (achieved_krs / total_krs * 100) if total_krs > 0 else 0
        if success_rate >= 83:
            overall_health = "green"
        elif success_rate >= 67:
            overall_health = "yellow"
        else:
            overall_health = "red"

        return {
            "period": period.value,
            "year": year,
            "team": team,
            "overall_health": overall_health,
            "objectives": {
                "total": total_objectives,
                "completed": completed_objectives,
                "completion_rate": (
                    round((completed_objectives / total_objectives * 100), 1)
                    if total_objectives > 0
                    else 0
                ),
            },
            "key_results": {
                "total": total_krs,
                "achieved": achieved_krs,
                "on_track": on_track_krs,
                "at_risk": at_risk_krs,
                "off_track": off_track_krs,
                "achievement_rate": round(success_rate, 1),
            },
            "objectives_list": [
                {
                    "id": str(obj.id),
                    "title": obj.title,
                    "progress": round(obj.progress_percentage, 1),
                    "status": obj.status.value,
                    "key_results_count": len(obj.key_results),
                }
                for obj in objectives
            ],
        }
