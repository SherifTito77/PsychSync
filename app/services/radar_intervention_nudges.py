"""
Intervention Nudge System for Radar
Provides real-time behavioral nudges and micro-coaching
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class NudgeType(Enum):
    """Types of intervention nudges"""

    COMMUNICATION_GUIDANCE = "communication_guidance"
    CONFLICT_RESOLUTION = "conflict_resolution"
    EMPATHY_BUILDING = "empathy_building"
    ACTIVE_LISTENING = "active_listening"
    STRESS_MANAGEMENT = "stress_management"
    TEAM_DYNAMICS = "team_dynamics"
    BURNOUT_PREVENTION = "burnout_prevention"
    PSYCHOLOGICAL_SAFETY = "psychological_safety"


class NudgePriority(Enum):
    """Priority levels for nudges"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Nudge:
    """Intervention nudge"""

    nudge_id: str
    nudge_type: NudgeType
    priority: NudgePriority
    title: str
    message: str
    suggested_actions: List[str]
    target_audience: str  # 'individual', 'team', 'organization'
    context: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime]
    delivery_channel: str  # 'in_app', 'email', 'slack', 'teams'
    status: str = "pending"  # pending, delivered, acknowledged, dismissed


class InterventionNudgeSystem:
    """
    Intelligent intervention nudge system

    Features:
    - Context-aware nudge generation
    - Multi-channel delivery
    - Behavioral response tracking
    - Effectiveness measurement
    - Adaptive timing
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.nudge_history: Dict[str, List[Nudge]] = {}

    async def generate_nudges_for_zone_change(
        self,
        organization_id: str,
        old_zone: str,
        new_zone: str,
        risk_score: float,
        contributing_factors: List[Dict[str, Any]],
    ) -> List[Nudge]:
        """
        Generate appropriate nudges when zone changes

        Args:
            organization_id: Organization experiencing zone change
            old_zone: Previous zone (green, yellow, red)
            new_zone: New zone
            risk_score: Current risk score
            contributing_factors: Factors contributing to zone change

        Returns:
            List of appropriate nudges
        """
        nudges = []

        try:
            # Zone worsening (green → yellow, yellow → red, green → red)
            if self._is_zone_worsening(old_zone, new_zone):
                critical_nudges = await self._generate_zone_worsening_nudges(
                    organization_id, new_zone, risk_score, contributing_factors
                )
                nudges.extend(critical_nudges)

            # Zone improving (red → yellow, yellow → green, red → green)
            elif self._is_zone_improving(old_zone, new_zone):
                positive_nudges = await self._generate_zone_improvement_nudges(
                    organization_id, new_zone, risk_score
                )
                nudges.extend(positive_nudges)

            # High-risk factors detected
            high_risk_factors = [
                f for f in contributing_factors if f.get("risk", 0) > 0.6
            ]

            if high_risk_factors:
                factor_nudges = await self._generate_factor_specific_nudges(
                    organization_id, high_risk_factors
                )
                nudges.extend(factor_nudges)

            return nudges

        except Exception as e:
            self.logger.error(f"Failed to generate nudges: {e}", exc_info=True)
            return []

    async def _generate_zone_worsening_nudges(
        self,
        organization_id: str,
        zone: str,
        risk_score: float,
        factors: List[Dict[str, Any]],
    ) -> List[Nudge]:
        """Generate nudges for zone worsening"""

        if zone == "yellow":
            return [
                Nudge(
                    nudge_id=f"yellow_zone_alert_{datetime.utcnow().timestamp()}",
                    nudge_type=NudgeType.TEAM_DYNAMICS,
                    priority=NudgePriority.MEDIUM,
                    title="⚠️ Entering Caution Zone",
                    message=(
                        "Your team's health metrics have shifted into the yellow zone. "
                        "This indicates emerging concerns that need attention. "
                        "Early intervention can prevent escalation."
                    ),
                    suggested_actions=[
                        "Schedule team check-in within 48 hours",
                        "Review recent communication patterns",
                        "Assess workload and stress levels",
                        "Consider 1:1 meetings with team members",
                    ],
                    target_audience="team",
                    context={
                        "zone": zone,
                        "risk_score": risk_score,
                        "factors": factors[:3],
                    },
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=7),
                    delivery_channel="in_app",
                ),
                Nudge(
                    nudge_id=f"comm_guidance_yellow_{datetime.utcnow().timestamp()}",
                    nudge_type=NudgeType.COMMUNICATION_GUIDANCE,
                    priority=NudgePriority.MEDIUM,
                    title="💬 Communication Check-in",
                    message=(
                        "Detection of increased tension in communications. "
                        "Consider reviewing meeting dynamics and feedback approaches."
                    ),
                    suggested_actions=[
                        "Use 'I' statements instead of 'you' statements",
                        "Practice active listening techniques",
                        "Schedule regular feedback sessions",
                        "Create safe space for open dialogue",
                    ],
                    target_audience="individual",
                    context={"trigger": "communication_risk_increase"},
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=14),
                    delivery_channel="in_app",
                ),
            ]

        elif zone == "red":
            return [
                Nudge(
                    nudge_id=f"red_zone_critical_{datetime.utcnow().timestamp()}",
                    nudge_type=NudgeType.CONFLICT_RESOLUTION,
                    priority=NudgePriority.CRITICAL,
                    title="🚨 CRITICAL: Immediate Action Required",
                    message=(
                        "Your team has entered the red zone. Critical issues detected "
                        "requiring immediate intervention. HR escalation recommended."
                    ),
                    suggested_actions=[
                        "IMMEDIATE: Contact HR support",
                        "Conduct private individual check-ins",
                        "Pause high-stakes projects if possible",
                        "Document all incidents objectively",
                        "Consider external facilitator",
                    ],
                    target_audience="organization",
                    context={
                        "zone": zone,
                        "risk_score": risk_score,
                        "factors": factors,
                        "escalation_required": True,
                    },
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=3),
                    delivery_channel="email",
                ),
                Nudge(
                    nudge_id=f"crisis_intervention_{datetime.utcnow().timestamp()}",
                    nudge_type=NudgeType.PSYCHOLOGICAL_SAFETY,
                    priority=NudgePriority.HIGH,
                    title="🛡️ Psychological Safety Intervention",
                    message=(
                        "Critical psychological safety concerns detected. "
                        "Team members may feel unsafe speaking up."
                    ),
                    suggested_actions=[
                        "Reiterate non-retaliation policy",
                        "Provide anonymous feedback channels",
                        "Address any public criticisms immediately",
                        "Create safe spaces for concerns",
                    ],
                    target_audience="team",
                    context={"trigger": "psychological_safety_critical"},
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=7),
                    delivery_channel="in_app",
                ),
            ]

        return []

    async def _generate_zone_improvement_nudges(
        self, organization_id: str, zone: str, risk_score: float
    ) -> List[Nudge]:
        """Generate positive reinforcement nudges for zone improvement"""

        nudges = []

        if zone == "green":
            nudges.append(
                Nudge(
                    nudge_id=f"green_zone_success_{datetime.utcnow().timestamp()}",
                    nudge_type=NudgeType.TEAM_DYNAMICS,
                    priority=NudgePriority.LOW,
                    title="✅ Healthy Zone Achieved!",
                    message=(
                        "Congratulations! Your team is in the green zone with positive "
                        "health indicators. Keep up the great work!"
                    ),
                    suggested_actions=[
                        "Share success with team",
                        "Document best practices",
                        "Consider mentorship opportunities",
                        "Celebrate team achievements",
                    ],
                    target_audience="team",
                    context={
                        "zone": zone,
                        "risk_score": risk_score,
                        "improvement": True,
                    },
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=30),
                    delivery_channel="in_app",
                )
            )

        elif zone == "yellow" and risk_score < 0.5:
            nudges.append(
                Nudge(
                    nudge_id=f"improvement_progress_{datetime.utcnow().timestamp()}",
                    nudge_type=NudgeType.BURNOUT_PREVENTION,
                    priority=NudgePriority.LOW,
                    title="📈 Positive Progress Detected",
                    message=(
                        "Your team metrics are showing improvement. Continue current "
                        "practices to maintain positive momentum."
                    ),
                    suggested_actions=[
                        "Maintain current interventions",
                        "Monitor for sustainability",
                        "Share learnings with other teams",
                    ],
                    target_audience="team",
                    context={"trend": "improving"},
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=14),
                    delivery_channel="in_app",
                )
            )

        return nudges

    async def _generate_factor_specific_nudges(
        self, organization_id: str, factors: List[Dict[str, Any]]
    ) -> List[Nudge]:
        """Generate nudges targeting specific high-risk factors"""

        nudges = []

        for factor in factors:
            component = factor.get("component", "")
            risk = factor.get("risk", 0)

            if "toxicity" in component and risk > 0.6:
                nudges.append(
                    Nudge(
                        nudge_id=f"toxicity_nudge_{datetime.utcnow().timestamp()}",
                        nudge_type=NudgeType.CONFLICT_RESOLUTION,
                        priority=NudgePriority.HIGH,
                        title="🛡️ Toxicity Pattern Detected",
                        message="Toxic behavioral patterns detected. Immediate attention needed.",
                        suggested_actions=[
                            "Review specific incidents (check dashboard)",
                            "Address directly but privately",
                            "Set clear behavioral expectations",
                            "Document patterns for HR",
                        ],
                        target_audience="individual",
                        context={"factor": factor},
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=5),
                        delivery_channel="in_app",
                    )
                )

            elif "behavioral" in component and risk > 0.6:
                nudges.append(
                    Nudge(
                        nudge_id=f"behavioral_nudge_{datetime.utcnow().timestamp()}",
                        nudge_type=NudgeType.EMPATHY_BUILDING,
                        priority=NudgePriority.MEDIUM,
                        title="🤝 Behavioral Health Concern",
                        message="Team behavioral health declining. Consider empathy-building exercises.",
                        suggested_actions=[
                            "Schedule team-building activity",
                            "Practice perspective-taking exercises",
                            "Encourage peer recognition",
                            "Promote work-life boundaries",
                        ],
                        target_audience="team",
                        context={"factor": factor},
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=10),
                        delivery_channel="in_app",
                    )
                )

            elif "psychological_safety" in component and risk > 0.6:
                nudges.append(
                    Nudge(
                        nudge_id=f"psych_safety_nudge_{datetime.utcnow().timestamp()}",
                        nudge_type=NudgeType.PSYCHOLOGICAL_SAFETY,
                        priority=NudgePriority.HIGH,
                        title="🔇 Psychological Safety At Risk",
                        message="Team members may not feel safe speaking up. Address immediately.",
                        suggested_actions=[
                            "Model vulnerability as leader",
                            "Reward speaking up behaviors",
                            "Address interruptions quickly",
                            "Normalize asking for help",
                        ],
                        target_audience="organization",
                        context={"factor": factor},
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=7),
                        delivery_channel="email",
                    )
                )

        return nudges

    def _is_zone_worsening(self, old_zone: str, new_zone: str) -> bool:
        """Check if zone change is worsening"""
        zone_rank = {"green": 1, "yellow": 2, "red": 3}
        return zone_rank.get(new_zone, 0) > zone_rank.get(old_zone, 0)

    def _is_zone_improving(self, old_zone: str, new_zone: str) -> bool:
        """Check if zone change is improving"""
        zone_rank = {"green": 1, "yellow": 2, "red": 3}
        return zone_rank.get(new_zone, 0) < zone_rank.get(old_zone, 0)

    async def deliver_nudges(
        self, nudges: List[Nudge], organization_id: str
    ) -> Dict[str, Any]:
        """
        Deliver nudges through appropriate channels

        Returns delivery status for each nudge
        """
        delivery_results = []

        for nudge in nudges:
            try:
                # Store nudge in history
                if organization_id not in self.nudge_history:
                    self.nudge_history[organization_id] = []

                self.nudge_history[organization_id].append(nudge)

                # In production, would deliver via:
                # - Email service
                # - Slack/Teams webhooks
                # - In-app notifications
                # - Push notifications

                delivery_results.append(
                    {
                        "nudge_id": nudge.nudge_id,
                        "status": "delivered",
                        "channel": nudge.delivery_channel,
                        "delivered_at": datetime.utcnow().isoformat(),
                    }
                )

                self.logger.info(f"Nudge delivered: {nudge.nudge_id}")

            except Exception as e:
                self.logger.error(f"Failed to deliver nudge {nudge.nudge_id}: {e}")
                delivery_results.append(
                    {
                        "nudge_id": nudge.nudge_id,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return {
            "total_nudges": len(nudges),
            "delivery_results": delivery_results,
        }

    def get_nudge_history(
        self, organization_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get nudges delivered to an organization"""
        if organization_id not in self.nudge_history:
            return []

        nudges = sorted(
            self.nudge_history[organization_id],
            key=lambda n: n.created_at,
            reverse=True,
        )[:limit]

        return [
            {
                "nudge_id": n.nudge_id,
                "type": n.nudge_type.value,
                "priority": n.priority.value,
                "title": n.title,
                "message": n.message,
                "suggested_actions": n.suggested_actions,
                "target_audience": n.target_audience,
                "created_at": n.created_at.isoformat(),
                "expires_at": n.expires_at.isoformat() if n.expires_at else None,
                "status": n.status,
            }
            for n in nudges
        ]


# Singleton instance
intervention_nudge_system = InterventionNudgeSystem()
