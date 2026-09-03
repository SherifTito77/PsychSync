"""
Automated Health Intervention & Alert System
Provides immediate interventions for work stress and health risks

Integrates with:
- WellnessAlert for storing interventions
- Notification system for multi-channel delivery
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.db.models.notifications import (
    Notification,
    NotificationPriority,
    NotificationStatus,
)
from app.db.models.wellness_burnout import BurnoutIntervention, WellnessResource
from app.services.health.stress_monitoring_service import (
    BurnoutStage,
    HealthRiskIndicators,
    StressLevel,
)

logger = logging.getLogger(__name__)


class InterventionType(Enum):
    """Types of interventions"""

    IMMEDIATE_BREAK = "immediate_break"
    MEDICAL_ALERT = "medical_alert"
    MANAGER_NOTIFICATION = "manager_notification"
    HR_ESCALATION = "hr_escalation"
    WORKLOAD_REDUCTION = "workload_reduction"
    WELLNESS_REMINDER = "wellness_reminder"
    BREAK_ENFORCEMENT = "break_enforcement"
    VACATION_PROMPT = "vacation_prompt"
    BOUNDARY_PROTECTION = "boundary_protection"
    SLEEP_HYGIENE = "sleep_hygiene"
    CRISIS_SUPPORT = "crisis_support"


class InterventionUrgency(Enum):
    """Intervention urgency levels"""

    CRITICAL = "critical"  # Immediate action required (within 1 hour)
    HIGH = "high"  # Action within 24 hours
    MEDIUM = "medium"  # Action within week
    LOW = "low"  # Ongoing monitoring


@dataclass
class InterventionAction:
    """Specific intervention action"""

    intervention_type: InterventionType
    urgency: InterventionUrgency
    title: str
    message: str
    actions_required: List[str]
    notify_user: bool
    notify_manager: bool
    notify_hr: bool
    notify_emergency_contact: bool
    automated_actions: List[str]
    resources: List[Dict[str, str]]
    follow_up_required: bool
    follow_up_days: int
    estimated_duration_weeks: Optional[int] = None


class HealthInterventionSystem:
    """
    Automated intervention system for health risks

    Creates and manages interventions based on health risk analysis.
    Integrates with existing notification and wellness systems.
    """

    def __init__(self, db: Session):
        self.db = db
        self.intervention_history = {}

    async def create_intervention_plan(
        self,
        user_id: str,
        organization_id: str,
        team_id: Optional[str],
        health_risks: HealthRiskIndicators,
        work_patterns: Dict[str, Any],
    ) -> List[InterventionAction]:
        """
        Create comprehensive intervention plan based on risk assessment
        """

        interventions = []

        # Critical interventions (immediate)
        if health_risks.recommend_medical_evaluation:
            interventions.append(
                self._create_medical_alert_intervention(
                    user_id, organization_id, health_risks
                )
            )

        if health_risks.urgent_intervention_needed:
            interventions.append(
                self._create_immediate_break_intervention(
                    user_id, organization_id, health_risks
                )
            )

        # High-priority interventions
        if health_risks.recommend_workload_reduction:
            interventions.append(
                self._create_workload_reduction_intervention(
                    user_id, organization_id, team_id, work_patterns
                )
            )

        if health_risks.recommend_immediate_break:
            interventions.append(
                self._create_break_enforcement_intervention(
                    user_id, organization_id, health_risks
                )
            )

        # Medium-priority interventions
        if health_risks.work_life_imbalance > 0.6:
            interventions.append(
                self._create_boundary_protection_intervention(
                    user_id, organization_id, health_risks
                )
            )

        if health_risks.sleep_disruption_score > 0.6:
            interventions.append(
                self._create_sleep_hygiene_intervention(
                    user_id, organization_id, health_risks
                )
            )

        # Mental health crisis support
        if health_risks.mental_health_risk > 0.7:
            interventions.append(
                self._create_crisis_support_intervention(
                    user_id, organization_id, health_risks
                )
            )

        # Preventive interventions
        if health_risks.stress_level in [StressLevel.ELEVATED, StressLevel.HIGH]:
            interventions.append(
                self._create_wellness_reminder_intervention(
                    user_id, organization_id, health_risks
                )
            )

        # Store interventions in database
        await self._persist_interventions(
            user_id, organization_id, team_id, interventions, health_risks
        )

        # Execute interventions (send notifications)
        await self._execute_interventions(user_id, organization_id, interventions)

        return interventions

    def _create_medical_alert_intervention(
        self, user_id: str, organization_id: str, health_risks: HealthRiskIndicators
    ) -> InterventionAction:
        """Create critical medical alert intervention"""

        risk_factors_text = "\n- ".join(health_risks.primary_risk_factors)

        return InterventionAction(
            intervention_type=InterventionType.MEDICAL_ALERT,
            urgency=InterventionUrgency.CRITICAL,
            title="⚠️ URGENT: Medical Evaluation Recommended",
            message=f"""Your health monitoring data indicates serious risk factors that require immediate medical attention:

RISK FACTORS DETECTED:
- {risk_factors_text}

Cardiovascular Risk Score: {health_risks.cardiovascular_risk_score:.1%}
Mental Health Risk: {health_risks.mental_health_risk:.1%}

This is not a diagnosis, but these indicators suggest you should see a healthcare provider TODAY.

If you're experiencing: chest pain, shortness of breath, dizziness, severe headache, or any other concerning symptoms - call emergency services (911) immediately.""".strip(),
            actions_required=[
                "Schedule same-day appointment with primary care physician",
                "If experiencing chest pain, shortness of breath, or dizziness: Call emergency services (911)",
                "Inform your manager you need immediate medical leave",
                "Document all symptoms for medical consultation",
            ],
            notify_user=True,
            notify_manager=True,
            notify_hr=True,
            notify_emergency_contact=False,  # Only if user opts in
            automated_actions=[
                "Block calendar for rest of day",
                "Send auto-reply email about medical leave",
                "Pause all non-critical notifications",
                "Alert HR for immediate leave processing",
            ],
            resources=[
                {
                    "title": "Find Urgent Care Near You",
                    "url": "https://www.urgentcare.com/",
                    "type": "medical",
                },
                {
                    "title": "Recognize Heart Attack Symptoms",
                    "url": "https://www.heart.org/en/health-topics/heart-attack/warning-signs-of-a-heart-attack",
                    "type": "education",
                },
                {"title": "Crisis Support Hotline", "phone": "988", "type": "support"},
            ],
            follow_up_required=True,
            follow_up_days=1,
        )

    def _create_immediate_break_intervention(
        self, user_id: str, organization_id: str, health_risks: HealthRiskIndicators
    ) -> InterventionAction:
        """Create immediate break enforcement"""

        return InterventionAction(
            intervention_type=InterventionType.IMMEDIATE_BREAK,
            urgency=InterventionUrgency.CRITICAL,
            title="🛑 Mandatory Break Required NOW",
            message=f"""Your stress level is CRITICAL. You must take a break immediately.

Current Status:
- Stress Level: {health_risks.stress_level.value.upper()}
- Burnout Stage: {health_risks.burnout_stage.value.replace('_', ' ').title()}
- Mental Health Risk: {health_risks.mental_health_risk:.1%}

Your wellbeing is the top priority. Stop working NOW.""".strip(),
            actions_required=[
                "Close all work applications immediately",
                "Take a 30-minute break away from your desk",
                "Practice deep breathing (guided session provided)",
                "Drink water and have a healthy snack",
                "Consider taking the rest of the day off",
            ],
            notify_user=True,
            notify_manager=True,
            notify_hr=False,
            notify_emergency_contact=False,
            automated_actions=[
                "Block calendar for next 30 minutes",
                "Enable 'Do Not Disturb' mode",
                "Send auto-reply: 'Taking mandatory wellness break'",
                "Launch guided breathing exercise",
            ],
            resources=[
                {
                    "title": "5-Minute Guided Breathing",
                    "url": "/wellness/breathing-exercise",
                    "type": "immediate",
                },
                {"title": "Crisis Support Hotline", "phone": "988", "type": "support"},
            ],
            follow_up_required=True,
            follow_up_days=0,
        )

    def _create_workload_reduction_intervention(
        self,
        user_id: str,
        organization_id: str,
        team_id: Optional[str],
        work_patterns: Dict[str, Any],
    ) -> InterventionAction:
        """Create workload reduction plan"""

        weekly_hours = work_patterns.get("weekly_hours", 0)
        continuous_days = work_patterns.get("continuous_days", 0)

        return InterventionAction(
            intervention_type=InterventionType.WORKLOAD_REDUCTION,
            urgency=InterventionUrgency.HIGH,
            title="📉 Workload Reduction Plan Required",
            message=f"""Your work patterns indicate unsustainable workload:

- Weekly Hours: {weekly_hours:.1f} (Recommended: <45)
- Continuous Work Days: {continuous_days} (Need rest days)

Your manager has been notified to help redistribute work and ensure you can recover.""".strip(),
            actions_required=[
                "Meet with manager within 24 hours to discuss workload",
                "Identify tasks that can be delegated or postponed",
                "Set realistic deadlines with manager input",
                "Schedule mandatory rest days this week",
                "Create 'protected focus time' in calendar",
            ],
            notify_user=True,
            notify_manager=True,
            notify_hr=True,
            notify_emergency_contact=False,
            automated_actions=[
                "Alert manager about workload intervention",
                "Suggest delegation opportunities based on task analysis",
                "Block 2-hour focus blocks in calendar",
                "Pause new task assignments for 1 week",
            ],
            resources=[
                {
                    "title": "Workload Management Guide",
                    "url": "/resources/workload-management",
                    "type": "guide",
                },
                {
                    "title": "Setting Boundaries at Work",
                    "url": "/resources/work-boundaries",
                    "type": "guide",
                },
            ],
            follow_up_required=True,
            follow_up_days=3,
            estimated_duration_weeks=2,
        )

    def _create_break_enforcement_intervention(
        self, user_id: str, organization_id: str, health_risks: HealthRiskIndicators
    ) -> InterventionAction:
        """Create mandatory break schedule"""

        return InterventionAction(
            intervention_type=InterventionType.BREAK_ENFORCEMENT,
            urgency=InterventionUrgency.HIGH,
            title="⏰ Mandatory Break Schedule Activated",
            message="""To protect your health, we're enforcing mandatory breaks:

- 10-minute break every 90 minutes
- 30-minute lunch break (away from desk)
- End work day at 6 PM (no exceptions)
- One full rest day this weekend

Your calendar has been automatically updated.""".strip(),
            actions_required=[
                "Honor all scheduled breaks (non-negotiable)",
                "Leave desk during breaks",
                "No work communication after 6 PM",
                "Plan a restful weekend activity",
            ],
            notify_user=True,
            notify_manager=True,
            notify_hr=False,
            notify_emergency_contact=False,
            automated_actions=[
                "Schedule automatic break reminders",
                "Block calendar: 12-12:30 PM daily (lunch)",
                "Enable 'After Hours' mode at 6 PM",
                "Pause email/Slack notifications after 6 PM",
                "Send daily break compliance report",
            ],
            resources=[
                {
                    "title": "Effective Break Activities",
                    "url": "/wellness/break-activities",
                    "type": "guide",
                },
                {
                    "title": "Micro-Exercise Routines",
                    "url": "/wellness/desk-exercises",
                    "type": "activity",
                },
            ],
            follow_up_required=True,
            follow_up_days=7,
            estimated_duration_weeks=1,
        )

    def _create_boundary_protection_intervention(
        self, user_id: str, organization_id: str, health_risks: HealthRiskIndicators
    ) -> InterventionAction:
        """Create work-life boundary protection"""

        return InterventionAction(
            intervention_type=InterventionType.BOUNDARY_PROTECTION,
            urgency=InterventionUrgency.MEDIUM,
            title="🛡️ Work-Life Boundary Protection Enabled",
            message=f"""Your work-life balance needs improvement:

- Imbalance Score: {health_risks.work_life_imbalance:.1%}

We're activating boundary protection features to help you disconnect.""".strip(),
            actions_required=[
                "Set 'work hours' in your profile (e.g., 9 AM - 6 PM)",
                "Enable automatic after-hours email blocking",
                "Schedule 'personal time' blocks in calendar",
                "Discuss flexible work arrangements with manager if needed",
            ],
            notify_user=True,
            notify_manager=False,
            notify_hr=False,
            notify_emergency_contact=False,
            automated_actions=[
                "Block emails outside work hours",
                "Auto-decline meetings outside hours",
                "Send 'unavailable' auto-reply after hours",
                "Hide work apps from phone after 7 PM",
                "Weekly boundary compliance report",
            ],
            resources=[
                {
                    "title": "Digital Wellbeing Guide",
                    "url": "/wellness/digital-wellbeing",
                    "type": "guide",
                },
                {
                    "title": "Work-Life Integration Strategies",
                    "url": "/resources/work-life-balance",
                    "type": "guide",
                },
            ],
            follow_up_required=True,
            follow_up_days=14,
            estimated_duration_weeks=4,
        )

    def _create_sleep_hygiene_intervention(
        self, user_id: str, organization_id: str, health_risks: HealthRiskIndicators
    ) -> InterventionAction:
        """Create sleep improvement intervention"""

        return InterventionAction(
            intervention_type=InterventionType.SLEEP_HYGIENE,
            urgency=InterventionUrgency.MEDIUM,
            title="😴 Sleep Recovery Program",
            message=f"""Sleep disruption detected:

- Sleep Disruption Score: {health_risks.sleep_disruption_score:.1%}

Poor sleep significantly increases cardiovascular risk. Let's fix this.""".strip(),
            actions_required=[
                "Set consistent sleep schedule (same bedtime daily)",
                "No screens 1 hour before bed",
                "No work communication after 8 PM",
                "Consider sleep tracking for 2 weeks",
            ],
            notify_user=True,
            notify_manager=False,
            notify_hr=False,
            notify_emergency_contact=False,
            automated_actions=[
                "Send bedtime reminder at 10 PM",
                "Block work notifications after 8 PM",
                "Suggest relaxation content before bed",
                "Track sleep patterns if wearable connected",
            ],
            resources=[
                {
                    "title": "Sleep Hygiene Guide",
                    "url": "/wellness/sleep-hygiene",
                    "type": "guide",
                },
                {
                    "title": "Guided Sleep Meditation",
                    "url": "/wellness/sleep-meditation",
                    "type": "audio",
                },
                {
                    "title": "Cognitive Behavioral Therapy for Insomnia (CBT-I)",
                    "url": "/resources/cbt-i",
                    "type": "therapy",
                },
            ],
            follow_up_required=True,
            follow_up_days=14,
            estimated_duration_weeks=4,
        )

    def _create_crisis_support_intervention(
        self, user_id: str, organization_id: str, health_risks: HealthRiskIndicators
    ) -> InterventionAction:
        """Create crisis support intervention"""

        return InterventionAction(
            intervention_type=InterventionType.CRISIS_SUPPORT,
            urgency=InterventionUrgency.CRITICAL,
            title="🆘 Crisis Support Resources",
            message=f"""Your mental health risk score is elevated ({health_risks.mental_health_risk:.1%}).

You're not alone. Help is available 24/7.

IF YOU'RE IN CRISIS:
- Call or text 988 (Suicide & Crisis Lifeline)
- Text HOME to 741741 (Crisis Text Line)
- Go to nearest emergency room

You don't have to face this alone.""".strip(),
            actions_required=[
                "Reach out to a trusted person",
                "Contact crisis support if needed",
                "Schedule appointment with mental health professional",
                "Take immediate mental health day if needed",
            ],
            notify_user=True,
            notify_manager=False,
            notify_hr=True,
            notify_emergency_contact=False,
            automated_actions=[
                "Display crisis resources prominently",
                "Pause non-essential notifications",
                "Send supportive wellness check-in",
            ],
            resources=[
                {
                    "title": "988 Suicide & Crisis Lifeline",
                    "phone": "988",
                    "url": "https://988lifeline.org/",
                    "type": "crisis",
                },
                {
                    "title": "Crisis Text Line",
                    "phone": "Text HOME to 741741",
                    "url": "https://www.crisistextline.org/",
                    "type": "crisis",
                },
                {
                    "title": "Find a Therapist",
                    "url": "/resources/therapy",
                    "type": "resource",
                },
            ],
            follow_up_required=True,
            follow_up_days=1,
        )

    def _create_wellness_reminder_intervention(
        self, user_id: str, organization_id: str, health_risks: HealthRiskIndicators
    ) -> InterventionAction:
        """Create preventive wellness reminders"""

        protective_text = (
            ", ".join(health_risks.protective_factors[:3])
            if health_risks.protective_factors
            else "Building..."
        )

        return InterventionAction(
            intervention_type=InterventionType.WELLNESS_REMINDER,
            urgency=InterventionUrgency.LOW,
            title="💚 Wellness Check-In",
            message=f"""Your stress level is elevated. Let's prevent it from getting worse.

Current Status:
- Stress Level: {health_risks.stress_level.value.title()}
- Protective Factors: {protective_text}

Small actions now prevent big problems later.""".strip(),
            actions_required=[
                "Take 5-minute mindfulness break today",
                "Schedule one social activity this week",
                "Add 30-minute exercise to your schedule",
                "Review and use vacation days",
            ],
            notify_user=True,
            notify_manager=False,
            notify_hr=False,
            notify_emergency_contact=False,
            automated_actions=[
                "Send daily wellness tip",
                "Suggest quick mindfulness exercises",
                "Remind about unused vacation days",
                "Prompt for weekly mood check-in",
            ],
            resources=[
                {
                    "title": "5-Minute Stress Relief Techniques",
                    "url": "/wellness/quick-stress-relief",
                    "type": "guide",
                },
                {
                    "title": "Desk Stretches & Exercises",
                    "url": "/wellness/desk-exercises",
                    "type": "video",
                },
            ],
            follow_up_required=True,
            follow_up_days=7,
        )

    async def _persist_interventions(
        self,
        user_id: str,
        organization_id: str,
        team_id: Optional[str],
        interventions: List[InterventionAction],
        health_risks: HealthRiskIndicators,
    ) -> None:
        """Persist interventions to database"""

        try:
            for intervention in interventions:
                # Create BurnoutIntervention record
                db_intervention = BurnoutIntervention(
                    organization_id=organization_id,
                    user_id=user_id,
                    team_id=team_id,
                    created_date=datetime.utcnow().date(),
                    intervention_type=intervention.intervention_type.value,
                    intervention_category=(
                        "reactive"
                        if intervention.urgency
                        in [InterventionUrgency.CRITICAL, InterventionUrgency.HIGH]
                        else "preventive"
                    ),
                    priority_level=intervention.urgency.value,
                    target_burnout_factors=health_risks.primary_risk_factors,
                    target_wellness_dimensions=[
                        "stress",
                        "work_life_balance",
                        "mental_health",
                    ],
                    severity_level=health_risks.stress_level.value,
                    intervention_description=intervention.message,
                    intervention_goals=intervention.actions_required,
                    success_metrics=[
                        "reduced_stress",
                        "improved_wellness",
                        "sustained_recovery",
                    ],
                    intervention_method="automated_system",
                    start_date=datetime.utcnow().date(),
                    end_date=datetime.utcnow().date()
                    + timedelta(days=intervention.follow_up_days),
                    duration_weeks=intervention.estimated_duration_weeks,
                    status="planned",
                    external_support=intervention.intervention_type
                    in [
                        InterventionType.MEDICAL_ALERT,
                        InterventionType.CRISIS_SUPPORT,
                    ],
                    follow_up_required=intervention.follow_up_required,
                    follow_up_schedule=[
                        {"days": intervention.follow_up_days, "type": "check_in"}
                    ],
                    baseline_metrics={
                        "stress_level": health_risks.stress_level.value,
                        "cardiovascular_risk": health_risks.cardiovascular_risk_score,
                        "mental_health_risk": health_risks.mental_health_risk,
                    },
                )

                self.db.add(db_intervention)

            self.db.commit()
            logger.info(
                f"Persisted {len(interventions)} interventions for user {user_id}"
            )

        except Exception as e:
            logger.error(f"Error persisting interventions: {e}")
            self.db.rollback()

    async def _execute_interventions(
        self,
        user_id: str,
        organization_id: str,
        interventions: List[InterventionAction],
    ) -> None:
        """Execute interventions by creating notifications"""

        try:
            for intervention in interventions:
                # Create notification for user
                if intervention.notify_user:
                    await self._create_notification(
                        user_id=user_id,
                        organization_id=organization_id,
                        intervention=intervention,
                    )

                # TODO: Create notifications for manager, HR, emergency contacts
                # This would require getting their user IDs from relationships

            logger.info(
                f"Executed {len(interventions)} interventions for user {user_id}"
            )

        except Exception as e:
            logger.error(f"Error executing interventions: {e}")

    async def _create_notification(
        self, user_id: str, organization_id: str, intervention: InterventionAction
    ) -> None:
        """Create notification for intervention"""

        # Determine priority
        priority_map = {
            InterventionUrgency.CRITICAL: NotificationPriority.URGENT,
            InterventionUrgency.HIGH: NotificationPriority.HIGH,
            InterventionUrgency.MEDIUM: NotificationPriority.NORMAL,
            InterventionUrgency.LOW: NotificationPriority.LOW,
        }

        notification = Notification(
            user_id=user_id,
            organization_id=organization_id,
            type="in_app",  # Could also be email, push, etc.
            title=intervention.title,
            content=intervention.message,
            notification_metadata={
                "intervention_type": intervention.intervention_type.value,
                "urgency": intervention.urgency.value,
                "actions_required": intervention.actions_required,
                "resources": intervention.resources,
            },
            priority=priority_map[intervention.urgency],
            status=NotificationStatus.PENDING,
        )

        self.db.add(notification)
        self.db.commit()


# Export
__all__ = [
    "HealthInterventionSystem",
    "InterventionAction",
    "InterventionType",
    "InterventionUrgency",
]
