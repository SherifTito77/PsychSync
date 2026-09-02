# app/services/intelligence_events.py
"""
Intelligence Event Dispatcher

Emits domain events from intelligence engine outputs (Pulse, BI, OKR health)
into the webhook system, enabling downstream integrations (Slack, JIRA,
email, third-party HRIS).

Events are fire-and-forget: failures in event dispatch never block the
intelligence engine response.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class IntelligenceEventDispatcher:
    """Evaluates intelligence outputs and dispatches webhook events."""

    async def dispatch_pulse_events(
        self,
        organization_id: str,
        pulse: Dict[str, Any],
    ) -> int:
        """Evaluate a Pulse output and emit relevant events."""
        events_emitted = 0

        questions = pulse.get("questions", {})

        # Flight risk events
        flight_risks = questions.get("flight_risk", {}).get("answer", [])
        for team in flight_risks:
            if team.get("risk_level") == "critical":
                await self._emit(
                    "intelligence.flight_risk_detected",
                    organization_id,
                    {
                        "team_name": team.get("team_name"),
                        "team_id": team.get("team_id"),
                        "flight_risk_score": team.get("flight_risk_score"),
                        "risk_level": "critical",
                        "key_people_at_risk": team.get("key_people_at_risk", 0),
                        "signal": team.get("signal"),
                    },
                )
                events_emitted += 1

        # Manager burnout events
        manager_signals = questions.get("manager_burnout", {}).get("answer", [])
        for signal in manager_signals:
            if signal.get("severity") == "critical":
                await self._emit(
                    "intelligence.manager_health_critical",
                    organization_id,
                    {
                        "team_name": signal.get("team_name"),
                        "team_id": signal.get("team_id"),
                        "severity": "critical",
                    },
                )
                events_emitted += 1

        # Burnout warnings
        for signal in manager_signals:
            burnout = signal.get("burnout_risk", 0)
            if burnout > 70:
                await self._emit(
                    "intelligence.burnout_warning",
                    organization_id,
                    {
                        "team_name": signal.get("team_name"),
                        "burnout_score": burnout,
                    },
                )
                events_emitted += 1

        # Isolation events
        isolated = questions.get("isolated_teams", {}).get("answer", [])
        for team in isolated:
            if team.get("severity") == "critical":
                await self._emit(
                    "intelligence.isolation_detected",
                    organization_id,
                    {
                        "team_name": team.get("team_name"),
                        "team_id": team.get("team_id"),
                        "severity": "critical",
                    },
                )
                events_emitted += 1

        # Friction spike events
        friction = questions.get("friction_trends", {}).get("answer", [])
        for signal in friction:
            if signal.get("severity") == "critical":
                await self._emit(
                    "intelligence.friction_spike",
                    organization_id,
                    {
                        "team_name": signal.get("team_name"),
                        "severity": "critical",
                    },
                )
                events_emitted += 1

        # Pulse score drop
        overall = pulse.get("overall_pulse_score", 50)
        trend = pulse.get("overall_trend", "stable")
        if overall < 40 or trend == "critical":
            await self._emit(
                "intelligence.pulse_score_drop",
                organization_id,
                {
                    "pulse_score": overall,
                    "trend": trend,
                    "teams_at_risk": pulse.get("teams_at_risk", 0),
                },
            )
            events_emitted += 1

        if events_emitted > 0:
            logger.info(
                "Dispatched %d intelligence events for org %s",
                events_emitted,
                organization_id,
            )
        return events_emitted

    async def dispatch_okr_health_events(
        self,
        organization_id: str,
        health_result: Dict[str, Any],
    ) -> int:
        """Emit events for critical OKR health flags."""
        events = 0
        for obj in health_result.get("objectives", []):
            if obj.get("health_risk_flag") == "critical":
                await self._emit(
                    "intelligence.okr_health_critical",
                    organization_id,
                    {
                        "objective_id": obj.get("objective_id"),
                        "title": obj.get("title"),
                        "team": obj.get("team"),
                        "signals": obj.get("signals", []),
                    },
                )
                events += 1
        return events

    async def _emit(
        self,
        event_type: str,
        organization_id: str,
        payload: Dict[str, Any],
    ) -> None:
        """Send event to webhook manager. Fire-and-forget."""
        try:
            from app.services.webhook_manager import WebhookEvent, WebhookManager

            manager = WebhookManager()
            full_payload = {
                "event": event_type,
                "organization_id": organization_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": payload,
            }

            # Find matching event enum
            try:
                event_enum = WebhookEvent(event_type)
            except ValueError:
                logger.debug("No webhook event enum for %s", event_type)
                return

            await manager.send_webhook(event_enum, full_payload)
        except Exception as e:
            # Never block intelligence engines on webhook failures
            logger.debug("Event dispatch failed (non-critical): %s", e)


# Singleton
intelligence_events = IntelligenceEventDispatcher()
