# app/services/nudge_bot_service.py
"""
Nudge Bot Service — Proactive outbound nudges via Slack/Teams.

Generates and sends contextual nudges based on intelligence engine outputs:
  - Pulse survey delivery reminders
  - Meeting effectiveness micro-surveys
  - Recognition prompts (for managers with low recognition investment)
  - Burnout nudges (for at-risk individuals)
  - Action plan reminders (overdue/upcoming)
  - OKR check-in reminders

Nudges are fire-and-forget: delivery failures are logged but never
block the calling service.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class NudgeBotService:
    """Generates and sends proactive nudges via messaging platforms."""

    # ------------------------------------------------------------------
    # Nudge generators
    # ------------------------------------------------------------------

    async def send_pulse_survey_reminders(
        self,
        db: AsyncSession,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Remind users who haven't submitted their pulse survey this round."""
        try:
            from app.db.models.pulse_survey import (
                PulseSurveyCampaign,
                PulseSurveyResponse,
            )
            from app.db.models.team import Team, TeamMember

            # Find active campaigns
            result = await db.execute(
                select(PulseSurveyCampaign).where(
                    and_(
                        PulseSurveyCampaign.organization_id == organization_id,
                        PulseSurveyCampaign.status == "active",
                    )
                )
            )
            campaigns = list(result.scalars().all())
            if not campaigns:
                return {"sent": 0, "reason": "no_active_campaigns"}

            # Find users who haven't responded in the last 14 days
            cutoff = date.today() - timedelta(days=14)
            responded = await db.execute(
                select(PulseSurveyResponse.respondent_id).where(
                    and_(
                        PulseSurveyResponse.organization_id == organization_id,
                        PulseSurveyResponse.survey_date >= cutoff,
                    )
                )
            )
            responded_ids = {str(r[0]) for r in responded.all()}

            # Get all users in org teams
            all_members = await db.execute(
                select(TeamMember.user_id)
                .join(Team, Team.id == TeamMember.team_id)
                .where(Team.organization_id == organization_id)
            )
            all_ids = {str(r[0]) for r in all_members.all()}

            missing = all_ids - responded_ids
            sent = 0
            for user_id in missing:
                await self._send_nudge(
                    user_id,
                    nudge_type="pulse_survey",
                    message="Your team's pulse survey is waiting. It takes <30 seconds and helps us understand how things are really going.",
                    action_url="/pulse-survey",
                )
                sent += 1

            return {
                "sent": sent,
                "total_users": len(all_ids),
                "already_responded": len(responded_ids),
            }

        except Exception as e:
            logger.warning("Pulse survey reminders failed: %s", e)
            return {"sent": 0, "error": str(e)}

    async def send_burnout_nudges(
        self,
        db: AsyncSession,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Send gentle nudges to users showing elevated burnout signals."""
        try:
            from app.db.models.wellness_burnout import WellnessMetrics
            from app.db.models.team import Team, TeamMember

            cutoff = date.today() - timedelta(days=30)

            # Find users with recent high burnout scores
            result = await db.execute(
                select(
                    WellnessMetrics.user_id,
                    func.max(WellnessMetrics.burnout_risk_score),
                )
                .join(TeamMember, TeamMember.user_id == WellnessMetrics.user_id)
                .join(Team, Team.id == TeamMember.team_id)
                .where(
                    and_(
                        Team.organization_id == organization_id,
                        WellnessMetrics.measurement_date >= cutoff,
                    )
                )
                .group_by(WellnessMetrics.user_id)
                .having(func.max(WellnessMetrics.burnout_risk_score) > 7)
            )
            at_risk = result.all()

            sent = 0
            for user_id, score in at_risk:
                await self._send_nudge(
                    str(user_id),
                    nudge_type="burnout_wellness",
                    message="We noticed some signals that suggest you might be stretched thin. Remember: it's okay to take a break or talk to someone. Your wellness resources are available anytime.",
                    action_url="/wellness",
                )
                sent += 1

            return {"sent": sent}

        except Exception as e:
            logger.warning("Burnout nudges failed: %s", e)
            return {"sent": 0, "error": str(e)}

    async def send_action_plan_reminders(
        self,
        db: AsyncSession,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Remind owners of upcoming/overdue action plans."""
        try:
            from app.db.models.action_plan import ActionPlan, ActionPlanStatus

            today = date.today()
            upcoming = today + timedelta(days=3)

            # Overdue plans
            result = await db.execute(
                select(ActionPlan).where(
                    and_(
                        ActionPlan.organization_id == organization_id,
                        ActionPlan.due_date < today,
                        ActionPlan.status.in_(
                            [
                                ActionPlanStatus.ACCEPTED.value,
                                ActionPlanStatus.IN_PROGRESS.value,
                            ]
                        ),
                    )
                )
            )
            overdue = list(result.scalars().all())

            # Upcoming (due within 3 days)
            result2 = await db.execute(
                select(ActionPlan).where(
                    and_(
                        ActionPlan.organization_id == organization_id,
                        ActionPlan.due_date >= today,
                        ActionPlan.due_date <= upcoming,
                        ActionPlan.status.in_(
                            [
                                ActionPlanStatus.ACCEPTED.value,
                                ActionPlanStatus.IN_PROGRESS.value,
                            ]
                        ),
                    )
                )
            )
            upcoming_plans = list(result2.scalars().all())

            sent = 0
            for plan in overdue:
                await self._send_nudge(
                    str(plan.owner_id),
                    nudge_type="action_plan_overdue",
                    message=f'Action plan overdue: "{plan.title}" (was due {plan.due_date.isoformat()}). Can you update or complete it?',
                    action_url="/action-plans",
                )
                sent += 1

            for plan in upcoming_plans:
                await self._send_nudge(
                    str(plan.owner_id),
                    nudge_type="action_plan_upcoming",
                    message=f'Reminder: "{plan.title}" is due {plan.due_date.isoformat()}.',
                    action_url="/action-plans",
                )
                sent += 1

            return {
                "sent": sent,
                "overdue": len(overdue),
                "upcoming": len(upcoming_plans),
            }

        except Exception as e:
            logger.warning("Action plan reminders failed: %s", e)
            return {"sent": 0, "error": str(e)}

    async def send_recognition_prompts(
        self,
        db: AsyncSession,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Prompt managers who haven't given recognition recently."""
        try:
            from app.db.models.peer_recognition import PeerRecognition
            from app.db.models.team import Team, TeamMember

            cutoff = datetime.now(timezone.utc) - timedelta(days=30)

            # Get all managers (team members — simplified: all members)
            members_q = await db.execute(
                select(TeamMember.user_id)
                .join(Team, Team.id == TeamMember.team_id)
                .where(Team.organization_id == organization_id)
                .distinct()
            )
            all_members = {str(r[0]) for r in members_q.all()}

            # Get users who gave recognition recently
            givers_q = await db.execute(
                select(PeerRecognition.giver_id)
                .where(
                    and_(
                        PeerRecognition.organization_id == organization_id,
                        PeerRecognition.created_at >= cutoff,
                    )
                )
                .distinct()
            )
            recent_givers = {str(r[0]) for r in givers_q.all()}

            non_givers = all_members - recent_givers
            sent = 0
            for user_id in list(non_givers)[:50]:  # Cap at 50 per run
                await self._send_nudge(
                    user_id,
                    nudge_type="recognition_prompt",
                    message="It's been a while since you recognized a colleague. A quick shoutout can make someone's day and strengthens team culture.",
                    action_url="/peer-recognition",
                )
                sent += 1

            return {"sent": sent, "non_givers": len(non_givers)}

        except Exception as e:
            logger.warning("Recognition prompts failed: %s", e)
            return {"sent": 0, "error": str(e)}

    async def send_okr_checkin_reminders(
        self,
        db: AsyncSession,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Remind OKR owners to update their key results."""
        try:
            from app.db.models.okr import Objective, OKRStatus

            result = await db.execute(
                select(Objective).where(
                    and_(
                        Objective.organization_id == organization_id,
                        Objective.status == OKRStatus.ACTIVE,
                    )
                )
            )
            objectives = list(result.scalars().all())

            sent = 0
            for obj in objectives:
                await self._send_nudge(
                    str(obj.owner_id),
                    nudge_type="okr_checkin",
                    message=f'Time for an OKR check-in on "{obj.title}". How are your key results tracking?',
                    action_url="/okr",
                )
                sent += 1

            return {"sent": sent}

        except Exception as e:
            logger.warning("OKR check-in reminders failed: %s", e)
            return {"sent": 0, "error": str(e)}

    # ------------------------------------------------------------------
    # Batch run (all nudge types)
    # ------------------------------------------------------------------

    async def run_all_nudges(
        self,
        db: AsyncSession,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Run all nudge types for an organization."""
        results = {}
        results["pulse_survey"] = await self.send_pulse_survey_reminders(
            db, organization_id
        )
        results["burnout"] = await self.send_burnout_nudges(db, organization_id)
        results["action_plans"] = await self.send_action_plan_reminders(
            db, organization_id
        )
        results["recognition"] = await self.send_recognition_prompts(
            db, organization_id
        )
        results["okr_checkin"] = await self.send_okr_checkin_reminders(
            db, organization_id
        )

        total = sum(r.get("sent", 0) for r in results.values())
        return {"total_nudges_sent": total, "by_type": results}

    # ------------------------------------------------------------------
    # Delivery
    # ------------------------------------------------------------------

    async def _send_nudge(
        self,
        user_id: str,
        nudge_type: str,
        message: str,
        action_url: Optional[str] = None,
    ) -> bool:
        """Send a nudge via Slack DM. Falls back to logging in test mode."""
        try:
            from app.services.slack_service import slack_service

            blocks = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": message},
                },
            ]
            if action_url:
                blocks.append(
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Take Action"},
                                "url": action_url,
                                "action_id": f"nudge_{nudge_type}",
                            }
                        ],
                    }
                )

            await slack_service.send_direct_message(
                user_id=user_id,
                message=message,
                blocks=blocks,
            )
            return True
        except Exception as e:
            logger.debug(
                "Nudge delivery failed for %s (%s): %s", user_id, nudge_type, e
            )
            return False


# Singleton
nudge_bot_service = NudgeBotService()
