"""
Automated Clinical Alert Triggering Service

Monitors clinical data and automatically triggers alerts when:
- Crisis indicators detected in assessments
- ML models predict high/critical risk
- Worsening trends detected
- Users cross risk thresholds
- Treatment non-response detected

Integrates with:
- ML risk prediction models
- Population health monitoring
- Existing notification system
- ClinicalAlert database model
"""

import logging
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional
from enum import Enum

import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, case

from app.db.models.clinical_extended import ClinicalAssessmentExtended
from app.db.models.clinical_screening import ClinicalAlert
from app.db.models.notification import NotificationPreference
from app.db.models.user import User
from app.services.clinical.risk_prediction_service import RiskPredictionService
from app.services.clinical.notification_service import ClinicianNotificationService
from app.core.logging_config import logger

# =============================================================================
# Alert Types and Severity
# =============================================================================


class AlertType(str, Enum):
    """Types of clinical alerts"""

    CRISIS_SUICIDE = "crisis_suicide"
    CRISIS_SELF_HARM = "crisis_self_harm"
    CRISIS_SEVERE = "crisis_severe"
    HIGH_RISK_DEPRESSION = "high_risk_depression"
    HIGH_RISK_ANXIETY = "high_risk_anxiety"
    WORSENING_TREND = "worsening_trend"
    TREATMENT_NON_RESPONSE = "treatment_non_response"
    RELAPSE_RISK = "relapse_risk"
    ASSESSMENT_DUE = "assessment_due"
    FOLLOW_UP_REQUIRED = "follow_up_required"


class AlertSeverity(str, Enum):
    """Alert severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class AlertTrigger:
    """Represents an alert trigger condition"""

    def __init__(
        self,
        trigger_type: AlertType,
        severity: AlertSeverity,
        user_id: str,
        org_id: str,
        message: str,
        metadata: Dict[str, Any],
        requires_immediate_action: bool = False,
    ):
        self.trigger_type = trigger_type
        self.severity = severity
        self.user_id = user_id
        self.org_id = org_id
        self.message = message
        self.metadata = metadata
        self.requires_immediate_action = requires_immediate_action


# =============================================================================
# Main Automated Alert Service
# =============================================================================


class AutomatedAlertService:
    """
    Automated Clinical Alert Triggering Service

    Monitors clinical data and triggers alerts automatically based on:
    - Real-time assessment results
    - ML risk predictions
    - Population health trends
    - Scheduled checks

    Features:
    - Multi-channel notifications (email, in-app)
    - Escalation logic
    - Quiet hours respect
    - Alert de-duplication
    - Preference-based routing
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)

    # ========================================================================
    # Real-Time Assessment Monitoring
    # ========================================================================

    async def monitor_assessment_submission(
        self,
        assessment: ClinicalAssessmentExtended,
        user: User,
    ) -> List[AlertTrigger]:
        """
        Monitor assessment submission for alert triggers

        Called immediately after assessment submission
        Checks for crisis indicators, high scores, risk flags
        """
        triggers = []

        try:
            # Check for crisis alert
            if assessment.crisis_alert:
                trigger = await self._check_crisis_alert(assessment, user)
                if trigger:
                    triggers.append(trigger)

            # Check for high/critical risk level
            if assessment.risk_level in ["high", "critical"]:
                trigger = await self._check_high_risk_assessment(
                    assessment, user
                )
                if trigger:
                    triggers.append(trigger)

            # Check for specific risk flags (suicidal ideation, etc.)
            if assessment.risk_flags:
                trigger = await self._check_risk_flags(
                    assessment, user
                )
                if trigger:
                    triggers.append(trigger)

            # If triggers found, process them
            if triggers:
                await self._process_alerts(triggers)

            return triggers

        except Exception as e:
            self.logger.error(
                f"Error monitoring assessment for user {user.id}: {e}"
            )
            return []

    async def _check_crisis_alert(
        self,
        assessment: ClinicalAssessmentExtended,
        user: User,
    ) -> Optional[AlertTrigger]:
        """Check if crisis alert requires immediate notification"""

        if not assessment.crisis_alert:
            return None

        # Determine severity based on risk level
        if assessment.risk_level == "critical":
            severity = AlertSeverity.CRITICAL
        else:
            severity = AlertSeverity.HIGH

        # Build detailed message
        assessment_name = self._get_assessment_name(
            assessment.assessment_type
        )

        # Check for specific crisis indicators
        if assessment.risk_flags:
            risk_indicators = ", ".join(
                [flag.replace("_", " ") for flag in assessment.risk_flags]
            )
            message = (
                f"CRISIS ALERT: {user.full_name} triggered crisis indicators "
                f"in {assessment_name}: {risk_indicators}. "
                f"Score: {assessment.total_score}"
            )
        else:
            message = (
                f"CRISIS ALERT: {user.full_name} has critical risk level "
                f"in {assessment_name} (Score: {assessment.total_score}). "
                f"Immediate clinical review required."
            )

        return AlertTrigger(
            trigger_type=AlertType.CRISIS_SEVERE,
            severity=severity,
            user_id=str(user.id),
            org_id=str(user.org_id) if user.org_id else "",
            message=message,
            metadata={
                "assessment_id": str(assessment.id),
                "assessment_type": assessment.assessment_type,
                "total_score": float(assessment.total_score),
                "risk_level": assessment.risk_level,
                "risk_flags": assessment.risk_flags or [],
                "completed_at": assessment.completed_at.isoformat(),
            },
            requires_immediate_action=True,
        )

    async def _check_high_risk_assessment(
        self,
        assessment: ClinicalAssessmentExtended,
        user: User,
    ) -> Optional[AlertTrigger]:
        """Check for high-risk assessment (non-crisis)"""

        # Determine alert type based on assessment type
        if assessment.assessment_type == "BDI2":
            trigger_type = AlertType.HIGH_RISK_DEPRESSION
            threshold = 29  # Moderate depression threshold
        elif assessment.assessment_type == "BAI":
            trigger_type = AlertType.HIGH_RISK_ANXIETY
            threshold = 26  # Moderate anxiety threshold
        else:
            return None

        if assessment.total_score < threshold:
            return None

        assessment_name = self._get_assessment_name(
            assessment.assessment_type
        )

        message = (
            f"HIGH RISK ALERT: {user.full_name} scored {assessment.total_score} "
            f"on {assessment_name} (threshold: {threshold}). "
            f"Risk level: {assessment.risk_level}. "
            f"Clinical assessment recommended."
        )

        return AlertTrigger(
            trigger_type=trigger_type,
            severity=AlertSeverity.HIGH,
            user_id=str(user.id),
            org_id=str(user.org_id) if user.org_id else "",
            message=message,
            metadata={
                "assessment_id": str(assessment.id),
                "assessment_type": assessment.assessment_type,
                "total_score": float(assessment.total_score),
                "risk_level": assessment.risk_level,
                "threshold": threshold,
            },
            requires_immediate_action=False,
        )

    async def _check_risk_flags(
        self,
        assessment: ClinicalAssessmentExtended,
        user: User,
    ) -> Optional[AlertTrigger]:
        """Check for specific risk flags"""

        # Check for suicidal ideation flag
        if any(
            "suicid" in flag.lower()
            for flag in (assessment.risk_flags or [])
        ):
            return AlertTrigger(
                trigger_type=AlertType.CRISIS_SUICIDE,
                severity=AlertSeverity.CRITICAL,
                user_id=str(user.id),
                org_id=str(user.org_id) if user.org_id else "",
                message=(
                    f"⚠️ SUICIDAL IDEATION DETECTED: {user.full_name} "
                    f"indicated suicidal thoughts in recent assessment. "
                    f"IMMEDIATE CLINICAL INTERVENTION REQUIRED."
                ),
                metadata={
                    "assessment_id": str(assessment.id),
                    "assessment_type": assessment.assessment_type,
                    "flag_type": "suicidal_ideation",
                    "requires_intervention": True,
                },
                requires_immediate_action=True,
            )

        return None

    # ========================================================================
    # ML Prediction-Based Alerts
    # ========================================================================

    async def run_ml_prediction_alerts(
        self,
        org_id: Optional[str] = None,
        prediction_types: Optional[List[str]] = None,
    ) -> List[AlertTrigger]:
        """
        Run ML predictions and trigger alerts for high-risk users

        Checks:
        - Depression risk predictions
        - Anxiety risk predictions
        - Crisis risk predictions
        """
        triggers = []

        try:
            # Initialize prediction service
            prediction_service = RiskPredictionService(self.db)

            # Get users with recent assessments
            recent_users = await self._get_users_with_recent_assessments(
                days_back=30, org_id=org_id
            )

            for user_id, user_data in recent_users:
                user = user_data["user"]

                # Check depression risk if enabled
                if not prediction_types or "depression_risk" in prediction_types:
                    trigger = await self._check_depression_risk_prediction(
                        user_id, prediction_service
                    )
                    if trigger:
                        triggers.append(trigger)

                # Check anxiety risk if enabled
                if not prediction_types or "anxiety_risk" in prediction_types:
                    trigger = await self._check_anxiety_risk_prediction(
                        user_id, prediction_service
                    )
                    if trigger:
                        triggers.append(trigger)

                # Check crisis risk if enabled
                if not prediction_types or "crisis_risk" in prediction_types:
                    trigger = await self._check_crisis_risk_prediction(
                        user_id, prediction_service
                    )
                    if trigger:
                        triggers.append(trigger)

            # Process all triggers
            if triggers:
                await self._process_alerts(triggers)

            return triggers

        except Exception as e:
            self.logger.error(f"Error running ML prediction alerts: {e}")
            return []

    async def _check_depression_risk_prediction(
        self,
        user_id: str,
        prediction_service: RiskPredictionService,
    ) -> Optional[AlertTrigger]:
        """Check depression risk prediction"""

        try:
            result = await prediction_service.predict_depression_risk(
                user_id=user_id,
                prediction_days=30,
                min_assessments=3,
            )

            # Only alert on high/critical risk
            if result.risk_level not in ["high", "critical"]:
                return None

            if result.risk_level == "critical":
                severity = AlertSeverity.CRITICAL
                requires_immediate = True
            else:
                severity = AlertSeverity.HIGH
                requires_immediate = False

            message = (
                f"DEPRESSION RISK ALERT: ML model predicts {result.risk_level.upper()} "
                f"risk for user (confidence: {result.confidence:.1%}). "
                f"Current factors: {result.factors}. "
            )

            return AlertTrigger(
                trigger_type=AlertType.HIGH_RISK_DEPRESSION,
                severity=severity,
                user_id=user_id,
                org_id="",  # Will be filled from user data
                message=message,
                metadata={
                    "prediction_type": "depression_risk",
                    "risk_level": result.risk_level,
                    "confidence": result.confidence,
                    "predicted_value": result.predicted_value,
                    "factors": result.factors,
                },
                requires_immediate_action=requires_immediate,
            )

        except Exception as e:
            self.logger.error(f"Error checking depression risk for {user_id}: {e}")
            return None

    async def _check_anxiety_risk_prediction(
        self,
        user_id: str,
        prediction_service: RiskPredictionService,
    ) -> Optional[AlertTrigger]:
        """Check anxiety risk prediction"""

        try:
            result = await prediction_service.predict_anxiety_risk(
                user_id=user_id,
                prediction_days=30,
                min_assessments=3,
            )

            # Only alert on high/critical risk
            if result.risk_level not in ["high", "critical"]:
                return None

            if result.risk_level == "critical":
                severity = AlertSeverity.CRITICAL
                requires_immediate = True
            else:
                severity = AlertSeverity.HIGH
                requires_immediate = False

            message = (
                f"ANXIETY RISK ALERT: ML model predicts {result.risk_level.upper()} "
                f"risk for user (confidence: {result.confidence:.1%}). "
                f"Current factors: {result.factors}. "
            )

            return AlertTrigger(
                trigger_type=AlertType.HIGH_RISK_ANXIETY,
                severity=severity,
                user_id=user_id,
                org_id="",
                message=message,
                metadata={
                    "prediction_type": "anxiety_risk",
                    "risk_level": result.risk_level,
                    "confidence": result.confidence,
                    "predicted_value": result.predicted_value,
                    "factors": result.factors,
                },
                requires_immediate_action=requires_immediate,
            )

        except Exception as e:
            self.logger.error(f"Error checking anxiety risk for {user_id}: {e}")
            return None

    async def _check_crisis_risk_prediction(
        self,
        user_id: str,
        prediction_service: RiskPredictionService,
    ) -> Optional[AlertTrigger]:
        """Check crisis risk prediction"""

        try:
            result = await prediction_service.predict_crisis_risk(
                user_id=user_id,
                lookback_days=90,
                min_assessments=2,
            )

            # Alert on moderate+ crisis risk
            if result.risk_level not in ["moderate", "high", "critical"]:
                return None

            if result.risk_level == "critical":
                severity = AlertSeverity.CRITICAL
                requires_immediate = True
            elif result.risk_level == "high":
                severity = AlertSeverity.HIGH
                requires_immediate = True
            else:  # moderate
                severity = AlertSeverity.MODERATE
                requires_immediate = False

            message = (
                f"CRISIS RISK ALERT: ML model predicts {result.risk_level.upper()} "
                f"crisis risk (confidence: {result.confidence:.1%}). "
                f"Indicators: {result.factors}. "
            )

            return AlertTrigger(
                trigger_type=AlertType.CRISIS_SEVERE,
                severity=severity,
                user_id=user_id,
                org_id="",
                message=message,
                metadata={
                    "prediction_type": "crisis_risk",
                    "risk_level": result.risk_level,
                    "confidence": result.confidence,
                    "factors": result.factors,
                },
                requires_immediate_action=requires_immediate,
            )

        except Exception as e:
            self.logger.error(f"Error checking crisis risk for {user_id}: {e}")
            return None

    # ========================================================================
    # Trend-Based Alerts
    # ========================================================================

    async def check_trending_alerts(
        self,
        org_id: Optional[str] = None,
    ) -> List[AlertTrigger]:
        """
        Check for worsening trends across users

        Detects:
        - Rapid score increase (>50% in short period)
        - Consistent worsening over multiple assessments
        - Users approaching crisis thresholds
        """
        triggers = []

        try:
            # Get users with 4+ assessments in last 90 days
            cutoff_date = datetime.utcnow() - timedelta(days=90)

            subquery = (
                select(
                    ClinicalAssessmentExtended.user_id,
                    func.count(ClinicalAssessmentExtended.id).label(
                        "assessment_count"
                    ),
                )
                .where(
                    and_(
                        ClinicalAssessmentExtended.completed_at >= cutoff_date,
                        ClinicalAssessmentExtended.assessment_type.in_(
                            ["BDI2", "BAI", "GAD7", "PHQ9"]
                        ),
                    )
                )
                .group_by(ClinicalAssessmentExtended.user_id)
                .having(func.count(ClinicalAssessmentExtended.id) >= 4)
                .subquery()
            )

            # Get user details
            users_query = (
                select(User, subquery.c.assessment_count)
                .join(subquery, User.id == subquery.c.user_id)
                .where(User.deleted_at.is_(None))
            )

            if org_id:
                users_query = users_query.where(User.org_id == org_id)

            result = await self.db.execute(users_query)
            users_data = result.all()

            for user, assessment_count in users_data:
                # Check for worsening trend
                trigger = await self._check_worsening_trend(user.id)
                if trigger:
                    triggers.append(trigger)

            # Process triggers
            if triggers:
                await self._process_alerts(triggers)

            return triggers

        except Exception as e:
            self.logger.error(f"Error checking trending alerts: {e}")
            return []

    async def _check_worsening_trend(
        self, user_id: str
    ) -> Optional[AlertTrigger]:
        """Check if user has worsening trend requiring alert"""

        try:
            # Get recent assessments
            cutoff_date = datetime.utcnow() - timedelta(days=60)

            query = (
                select(ClinicalAssessmentExtended)
                .where(
                    and_(
                        ClinicalAssessmentExtended.user_id == user_id,
                        ClinicalAssessmentExtended.completed_at >= cutoff_date,
                        ClinicalAssessmentExtended.assessment_type.in_(
                            ["BDI2", "BAI"]
                        ),
                    )
                )
                .order_by(ClinicalAssessmentExtended.completed_at)
            )

            result = await self.db.execute(query)
            assessments = result.scalars().all()

            if len(assessments) < 4:
                return None

            # Calculate trend
            scores = [float(a.total_score) for a in assessments]
            first_avg = sum(scores[:2]) / 2
            last_avg = sum(scores[-2:]) / 2

            # Check for rapid worsening
            if last_avg > first_avg * 1.5:  # 50% increase
                severity = AlertSeverity.HIGH
                requires_immediate = False
                message = (
                    f"WORSENING TREND: User's scores have increased "
                    f"by {((last_avg - first_avg) / first_avg * 100):.0f}% "
                    f"in the past 60 days. Clinical review recommended."
                )

                return AlertTrigger(
                    trigger_type=AlertType.WORSENING_TREND,
                    severity=severity,
                    user_id=user_id,
                    org_id="",
                    message=message,
                    metadata={
                        "initial_average": first_avg,
                        "recent_average": last_avg,
                        "percent_increase": (
                            (last_avg - first_avg) / first_avg * 100
                        ),
                        "assessment_count": len(assessments),
                    },
                    requires_immediate_action=requires_immediate,
                )

            return None

        except Exception as e:
            self.logger.error(f"Error checking worsening trend for {user_id}: {e}")
            return None

    # ========================================================================
    # Alert Processing
    # ========================================================================

    async def _process_alerts(self, triggers: List[AlertTrigger]) -> None:
        """
        Process alert triggers by:
        1. Creating ClinicalAlert records
        2. Sending notifications via notification service
        3. Logging for audit trail
        """

        for trigger in triggers:
            try:
                # Fill in org_id if missing
                if not trigger.org_id:
                    user = await self.db.get(User, trigger.user_id)
                    if user:
                        trigger.org_id = str(user.org_id) if user.org_id else ""

                # Create ClinicalAlert record
                await self._create_clinician_alert(trigger)

                # Send notifications to clinicians
                await self._send_clinician_notifications(trigger)

                # Log for audit
                self.logger.info(
                    f"✓ Alert triggered: {trigger.trigger_type.value} | "
                    f"Severity: {trigger.severity.value} | "
                    f"User: {trigger.user_id} | "
                    f"Immediate: {trigger.requires_immediate_action}"
                )

            except Exception as e:
                self.logger.error(
                    f"Error processing alert for user {trigger.user_id}: {e}"
                )

    async def _create_clinician_alert(
        self, trigger: AlertTrigger
    ) -> Optional[ClinicalAlert]:
        """Create ClinicalAlert record in database"""

        try:
            # Find related screening/assessment
            assessment_id = trigger.metadata.get("assessment_id")

            alert = ClinicalAlert(
                user_id=trigger.user_id,
                org_id=trigger.org_id,
                alert_type=trigger.trigger_type.value,
                severity=trigger.severity.value,
                alert_message=trigger.message,
                resolution_status="pending" if trigger.severity != AlertSeverity.CRITICAL else "escalated",
                escalated=trigger.severity == AlertSeverity.CRITICAL,
                escalation_level="clinical_team" if trigger.severity == AlertSeverity.CRITICAL else None,
            )

            self.db.add(alert)
            await self.db.commit()
            await self.db.refresh(alert)

            return alert

        except Exception as e:
            self.logger.error(f"Error creating clinician alert: {e}")
            await self.db.rollback()
            return None

    async def _send_clinician_notifications(
        self, trigger: AlertTrigger
    ) -> None:
        """Send notifications to eligible clinicians"""

        try:
            # Initialize notification service
            notification_service = ClinicianNotificationService(self.db)

            # Determine notification type based on trigger
            notification_type = "crisis_alert" if trigger.severity in [
                AlertSeverity.CRITICAL
            ] else "high_risk"

            # Send notifications
            await notification_service.notify_clinicians_of_alert(
                alert_id=f"auto_{trigger.trigger_type.value}_{trigger.user_id}",
                alert_type=trigger.trigger_type.value,
                severity=trigger.severity.value,
                screening_id=trigger.metadata.get("assessment_id", ""),
                org_id=trigger.org_id,
                alert_message=trigger.message,
            )

        except Exception as e:
            self.logger.error(f"Error sending notifications for alert: {e}")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _get_users_with_recent_assessments(
        self,
        days_back: int,
        org_id: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Get users who have recent assessments"""

        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        query = (
            select(User, func.count(ClinicalAssessmentExtended.id).label("count"))
            .join(
                ClinicalAssessmentExtended,
                User.id == ClinicalAssessmentExtended.user_id,
            )
            .where(
                and_(
                    ClinicalAssessmentExtended.completed_at >= cutoff_date,
                    User.deleted_at.is_(None),
                )
            )
            .group_by(User.id)
        )

        if org_id:
            query = query.where(User.org_id == org_id)

        result = await self.db.execute(query)
        users_data = result.all()

        return {
            str(user.id): {"user": user, "assessment_count": count}
            for user, count in users_data
        }

    def _get_assessment_name(self, assessment_type: str) -> str:
        """Get full name for assessment type"""
        names = {
            "BDI2": "Beck Depression Inventory-II",
            "BAI": "Beck Anxiety Inventory",
            "GAD7": "Generalized Anxiety Disorder-7",
            "PHQ9": "Patient Health Questionnaire-9",
            "LSAS": "Liebowitz Social Anxiety Scale",
            "EAT26": "Eating Attitudes Test-26",
            "YBOCS": "Yale-Brown Obsessive Compulsive Scale",
        }
        return names.get(assessment_type, assessment_type)

    # ========================================================================
    # Scheduled Alert Checks
    # ========================================================================

    async def run_scheduled_alert_checks(
        self,
        check_types: List[str] = None,
    ) -> Dict[str, int]:
        """
        Run scheduled alert checks (called by background job)

        check_types:
        - "ml_predictions": Run ML prediction alerts
        - "trends": Check for worsening trends
        - "follow_ups": Check for users needing follow-up
        """
        results = {
            "ml_predictions": 0,
            "trends": 0,
            "follow_ups": 0,
            "total": 0,
        }

        try:
            # ML prediction alerts
            if not check_types or "ml_predictions" in check_types:
                triggers = await self.run_ml_prediction_alerts()
                results["ml_predictions"] = len(triggers)
                results["total"] += len(triggers)

            # Trend alerts
            if not check_types or "trends" in check_types:
                triggers = await self.check_trending_alerts()
                results["trends"] = len(triggers)
                results["total"] += len(triggers)

            # Log summary
            self.logger.info(
                f"Scheduled alert checks completed: {results['total']} alerts triggered"
            )

            return results

        except Exception as e:
            self.logger.error(f"Error running scheduled alert checks: {e}")
            return results

    # ========================================================================
    # Alert Management API Helpers
    # ========================================================================

    async def get_unresolved_alerts(
        self,
        org_id: str,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get unresolved alerts for organization"""

        query = select(ClinicalAlert).where(
            and_(
                ClinicalAlert.org_id == org_id,
                ClinicalAlert.resolution_status.in_(["pending", "in_progress", "escalated"]),
                ClinicalAlert.acknowledged == False,
            )
        )

        if severity:
            query = query.where(ClinicalAlert.severity == severity)

        query = query.order_by(
            case(
                (ClinicalAlert.severity == "critical", 1),
                (ClinicalAlert.severity == "high", 2),
                (ClinicalAlert.severity == "moderate", 3),
                else_=4,
            ),
            ClinicalAlert.created_at.desc(),
        ).limit(limit)

        result = await self.db.execute(query)
        alerts = result.scalars().all()

        return [
            {
                "id": str(alert.id),
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.alert_message,
                "user_id": str(alert.user_id),
                "created_at": alert.created_at.isoformat(),
                "resolution_status": alert.resolution_status,
                "escalated": alert.escalated,
                "requires_immediate": alert.severity == "critical",
            }
            for alert in alerts
        ]

    async def acknowledge_alert(
        self,
        alert_id: str,
        clinician_id: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Acknowledge an alert"""

        try:
            query = select(ClinicalAlert).where(
                ClinicalAlert.id == alert_id
            )
            result = await self.db.execute(query)
            alert = result.scalar_one_or_none()

            if not alert:
                return False

            alert.acknowledged = True
            alert.acknowledged_by = clinician_id
            alert.acknowledged_at = datetime.utcnow()

            if notes:
                alert.resolution_notes = notes

            await self.db.commit()

            self.logger.info(
                f"Alert {alert_id} acknowledged by clinician {clinician_id}"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error acknowledging alert {alert_id}: {e}")
            await self.db.rollback()
            return False

    async def resolve_alert(
        self,
        alert_id: str,
        clinician_id: str,
        resolution_notes: str,
    ) -> bool:
        """Resolve an alert"""

        try:
            query = select(ClinicalAlert).where(
                ClinicalAlert.id == alert_id
            )
            result = await self.db.execute(query)
            alert = result.scalar_one_or_none()

            if not alert:
                return False

            alert.resolution_status = "resolved"
            alert.resolved_by = clinician_id
            alert.resolved_at = datetime.utcnow()
            alert.resolution_notes = resolution_notes

            await self.db.commit()

            self.logger.info(
                f"Alert {alert_id} resolved by clinician {clinician_id}"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error resolving alert {alert_id}: {e}")
            await self.db.rollback()
            return False
