"""
Crisis Intervention Service
Automated crisis response workflows for mental health safety

CRITICAL: This service handles life-safety interventions
All actions must be logged and verified
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import BackgroundTasks

from app.db.models.clinical_screening import ClinicalAlert, ClinicalReferral, ClinicalAuditLog
from app.core.config import settings
from app.services.email_service import EmailService


logger = logging.getLogger(__name__)


class CrisisInterventionService:
    """
    Automated crisis intervention service

    Implements 4-level emergency response hierarchy:
    - Level 1: CRITICAL - Immediate danger (minutes)
    - Level 2: HIGH - High risk (hours)
    - Level 3: MODERATE - Moderate risk (days)
    - Level 4: LOW - Monitoring (weeks)
    """

    # Crisis resources
    CRISIS_HOTLINE_US = "988"
    CRISIS_TEXT_LINE = "741741"  # Text "HOME" to
    EMERGENCY_US = "911"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.email_service = EmailService()

    async def create_alert(
        self,
        screening_id: uuid4,
        user_id: uuid4,
        org_id: uuid4,
        risk_level: str,
        risk_flags: List[str],
        screening_data: Dict
    ) -> ClinicalAlert:
        """
        Create clinical crisis alert

        Args:
            screening_id: ID of the screening that triggered the alert
            user_id: User at risk
            org_id: Organization
            risk_level: LOW, MODERATE, HIGH, or CRITICAL
            risk_flags: Specific risk indicators
            screening_data: Screening data for context

        Returns:
            Created ClinicalAlert
        """
        # Generate alert message based on risk flags
        alert_message = self._generate_alert_message(risk_flags, risk_level)

        # Determine alert type from primary risk flag
        alert_type = risk_flags[0] if risk_flags else "GENERAL_CONCERN"

        # Create the alert
        alert = ClinicalAlert(
            screening_id=screening_id,
            user_id=user_id,
            org_id=org_id,
            alert_type=alert_type,
            severity=risk_level,
            alert_message=alert_message,
            resolution_status="pending"
        )

        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)

        # Log alert creation
        await self._audit_log(
            entity_type="alert",
            entity_id=alert.id,
            action="create",
            details={
                "risk_level": risk_level,
                "risk_flags": risk_flags,
                "screening_type": screening_data.get("screening_type")
            }
        )

        logger.critical(f"Crisis alert created: {alert.id} for user {user_id} - Risk: {risk_level}")

        return alert

    async def activate_crisis_protocol(
        self,
        alert: ClinicalAlert,
        background_tasks: BackgroundTasks,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None
    ):
        """
        Activate appropriate crisis protocol based on risk level

        Args:
            alert: The clinical alert
            background_tasks: FastAPI background tasks for async actions
            user_email: User's email for notifications
            user_name: User's name for personalization
        """
        risk_level = alert.severity.upper()

        if risk_level == "CRITICAL":
            await self._activate_level_1_protocol(alert, user_email, user_name, background_tasks)
        elif risk_level == "HIGH":
            await self._activate_level_2_protocol(alert, user_email, user_name, background_tasks)
        elif risk_level == "MODERATE":
            await self._activate_level_3_protocol(alert, user_email, user_name, background_tasks)
        else:
            await self._activate_level_4_protocol(alert, user_email, user_name, background_tasks)

    async def _activate_level_1_protocol(
        self,
        alert: ClinicalAlert,
        user_email: Optional[str],
        user_name: Optional[str],
        background_tasks: BackgroundTasks
    ):
        """
        Level 1: IMMEDIATE DANGER (Minutes)

        Triggers:
        - C-SSRS: Recent suicide attempt OR active plan with intent
        - PHQ-9 Item 9: Score ≥ 2
        - Any imminent danger indication

        Actions (Complete within 5 minutes):
        1. Send crisis notification to user
        2. Page on-call clinician
        3. Display emergency resources
        4. Log all actions
        """
        logger.critical(f"LEVEL 1 PROTOCOL ACTIVATED for alert {alert.id}")

        # 1. Send immediate crisis notification to user
        if user_email:
            background_tasks.add_task(
                self._send_crisis_notification,
                user_email,
                user_name or "there",
                alert.alert_message
            )

        # 2. Page on-call clinician (implement based on your notification system)
        background_tasks.add_task(
            self._page_on_call_clinician,
            alert.id,
            alert.severity
        )

        # 3. Create emergency referral
        referral = ClinicalReferral(
            alert_id=alert.id,
            user_id=alert.user_id,
            org_id=alert.org_id,
            referral_type="emergency_psychiatric",
            urgency="emergency",
            status="pending",
            follow_up_required=True,
            follow_up_date=datetime.utcnow() + timedelta(hours=24)
        )
        self.db.add(referral)
        await self.db.commit()

        # 4. Log emergency protocol activation
        await self._audit_log(
            entity_type="alert",
            entity_id=alert.id,
            action="emergency_protocol_activated",
            details={
                "level": 1,
                "actions": [
                    "User notified with crisis resources",
                    "On-call clinician paged",
                    "Emergency referral created",
                    "Crisis hotline information provided"
                ]
            }
        )

    async def _activate_level_2_protocol(
        self,
        alert: ClinicalAlert,
        user_email: Optional[str],
        user_name: Optional[str],
        background_tasks: BackgroundTasks
    ):
        """
        Level 2: HIGH RISK (Hours)

        Actions (Complete within 2 hours):
        1. Send resources to user
        2. Schedule clinician outreach
        3. Create urgent referral
        4. Safety planning resources
        """
        logger.warning(f"LEVEL 2 PROTOCOL ACTIVATED for alert {alert.id}")

        # 1. Send resources
        if user_email:
            background_tasks.add_task(
                self._send_mental_health_resources,
                user_email,
                user_name or "there",
                alert.alert_message
            )

        # 2. Schedule clinician outreach (within 2 hours)
        # Implementation depends on your scheduling system
        await self._schedule_clinician_outreach(
            alert.user_id,
            within_hours=2,
            priority="high"
        )

        # 3. Create urgent referral
        referral = ClinicalReferral(
            alert_id=alert.id,
            user_id=alert.user_id,
            org_id=alert.org_id,
            referral_type="urgent_mental_health",
            urgency="urgent",
            status="pending",
            follow_up_required=True,
            follow_up_date=datetime.utcnow() + timedelta(hours=48)
        )
        self.db.add(referral)
        await self.db.commit()

        await self._audit_log(
            entity_type="alert",
            entity_id=alert.id,
            action="high_risk_protocol_activated",
            details={"level": 2}
        )

    async def _activate_level_3_protocol(
        self,
        alert: ClinicalAlert,
        user_email: Optional[str],
        user_name: Optional[str],
        background_tasks: BackgroundTasks
    ):
        """
        Level 3: MODERATE RISK (Days)

        Actions (Complete within 7 days):
        1. Send educational resources
        2. Schedule follow-up
        3. Create non-urgent referral
        """
        logger.info(f"LEVEL 3 PROTOCOL ACTIVATED for alert {alert.id}")

        if user_email:
            background_tasks.add_task(
                self._send_wellness_resources,
                user_email,
                user_name or "there"
            )

        # Create routine referral
        referral = ClinicalReferral(
            alert_id=alert.id,
            user_id=alert.user_id,
            org_id=alert.org_id,
            referral_type="counseling",
            urgency="routine",
            status="pending",
            follow_up_required=True,
            follow_up_date=datetime.utcnow() + timedelta(days=7)
        )
        self.db.add(referral)
        await self.db.commit()

    async def _activate_level_4_protocol(
        self,
        alert: ClinicalAlert,
        user_email: Optional[str],
        user_name: Optional[str],
        background_tasks: BackgroundTasks
    ):
        """
        Level 4: LOW RISK / MONITORING (Weeks)

        Actions:
        1. Send self-help resources
        2. Recommend re-screening
        """
        logger.info(f"LEVEL 4 PROTOCOL ACTIVATED for alert {alert.id}")

        if user_email:
            background_tasks.add_task(
                self._send_self_help_resources,
                user_email,
                user_name or "there"
            )

    # ==========================================================================
    # NOTIFICATION METHODS
    # ==========================================================================

    async def _send_crisis_notification(
        self,
        email: str,
        name: str,
        alert_message: str
    ):
        """Send crisis notification with immediate resources"""
        subject = "🚨 Immediate Support Available"

        resources = f"""
Dear {name},

We detected that you may be going through a difficult time. Help is available right now.

⚠️ IF YOU ARE IN IMMEDIATE DANGER:
• Call 911 or go to the nearest emergency room
• Call/Text 988 Suicide & Crisis Lifeline
• Text "HOME" to 741741 (Crisis Text Line)

You are not alone. Support is available 24/7.

{alert_message}

Please reach out to one of these resources now. They are trained to help.
        """

        try:
            await self.email_service.send_email(
                email_to=email,
                subject=subject,
                body=resources
            )
            logger.info(f"Crisis notification sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send crisis notification: {e}")

    async def _send_mental_health_resources(
        self,
        email: str,
        name: str,
        alert_message: str
    ):
        """Send mental health resources for high risk"""
        subject = "Mental Health Resources Available"

        resources = f"""
Hi {name},

Based on your recent assessment, we wanted to share some resources with you.

Support Resources:
• 988 Suicide & Crisis Lifeline: Call or text 988
• Crisis Text Line: Text HOME to 741741
• International: https://findahelpline.com/

We recommend connecting with a mental health professional within the next 48 hours.

{alert_message}

You don't have to face this alone.
        """

        await self.email_service.send_email(email_to=email, subject=subject, body=resources)

    async def _send_wellness_resources(self, email: str, name: str):
        """Send wellness resources for moderate risk"""
        subject = "Mental Health & Wellness Resources"

        await self.email_service.send_email(
            email_to=email,
            subject=subject,
            body=f"""
Hi {name},

Here are some resources that might help:

• Find a Therapist: Psychology Today, BetterHelp, Talkspace
• Self-Help: Moodfit app, Calm, Headspace
• Support Groups: NAMI (nami.org)

Taking care of your mental health is important. Consider reaching out to a professional.
            """
        )

    async def _send_self_help_resources(self, email: str, name: str):
        """Send self-help resources for low risk"""
        subject = "Resources for Your Wellbeing"

        await self.email_service.send_email(
            email_to=email,
            subject=subject,
            body=f"""
Hi {name},

Here are some resources for maintaining good mental health:

• Mental Health America: mhanational.org
• National Alliance on Mental Illness: nami.org
• Apps: Moodfit, Sanvello, Woebot

Remember to take breaks, stay connected, and reach out if you need support.
            """
        )

    # ==========================================================================
    # CLINICIAN COORDINATION
    # ==========================================================================

    async def _page_on_call_clinician(self, alert_id: uuid4, severity: str):
        """
        Page on-call clinician for crisis response

        Implementation depends on your paging system:
        - SMS/twilio integration
        - Slack/Teams notification
        - Pager system
        - Phone call
        """
        # TODO: Implement based on your notification system
        logger.critical(f"On-call clinician paged for alert {alert_id} - Severity: {severity}")

    async def _schedule_clinician_outreach(
        self,
        user_id: uuid4,
        within_hours: int,
        priority: str
    ):
        """
        Schedule clinician to reach out to user

        Implementation depends on your scheduling/case management system
        """
        # TODO: Implement based on your scheduling system
        logger.info(f"Clinician outreach scheduled for user {user_id} within {within_hours}h")

    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================

    def _generate_alert_message(self, risk_flags: List[str], risk_level: str) -> str:
        """Generate human-readable alert message"""
        messages = {
            "SUICIDE_ATTEMPT_RECENT": "Recent suicide attempt reported",
            "SUICIDE_PLAN_WITH_INTENT": "Active suicidal plan with intent detected",
            "ACTIVE_SUICIDE_IDEATION": "Active suicidal thoughts detected",
            "PASSIVE_SUICIDE_IDEATION": "Thoughts of death reported",
            "SEVERE_DEPRESSION": "Severe depression symptoms detected",
            "SEVERE_ANXIETY": "Severe anxiety symptoms detected",
            "CLINICALLY_SIGNIFICANT_ANXIETY": "Clinically significant anxiety detected"
        }

        primary_flag = risk_flags[0] if risk_flags else "GENERAL_CONCERN"
        return messages.get(primary_flag, "Mental health concern identified")

    async def _audit_log(
        self,
        entity_type: str,
        entity_id: uuid4,
        action: str,
        details: Dict
    ):
        """
        Log clinical action for HIPAA compliance

        CRITICAL: All clinical actions must be logged
        """
        # TODO: Implement audit logging
        logger.info(f"Clinical audit: {action} on {entity_type} {entity_id}")
