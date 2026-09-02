# app/services/narrative_intelligence_service.py
"""
Narrative Intelligence Service — Executive Storytelling

Generates publication-quality narrative reports from BI, Pulse, ONA,
and Digital Twin data. Turns dashboards into boardroom-ready stories.

Outputs: structured narrative sections that can be rendered as
PDF reports, email digests, or Slack summaries.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class NarrativeIntelligenceService:
    """Generates narrative reports from organizational intelligence data."""

    async def generate_report(
        self,
        db: AsyncSession,
        org_id: UUID,
        period: str = "weekly",  # weekly, monthly, quarterly
    ) -> Dict[str, Any]:
        """
        Generate a full narrative report for an organization.

        Returns structured sections ready for rendering.
        """
        # Gather data from all engines
        data = await self._gather_report_data(db, org_id, period)

        # Build narrative sections
        report = {
            "organization_id": str(org_id),
            "period": period,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sections": {
                "executive_summary": self._build_executive_summary(data),
                "what_improved": self._build_improvements(data),
                "what_declined": self._build_declines(data),
                "team_spotlight": self._build_team_spotlight(data),
                "risk_outlook": self._build_risk_outlook(data),
                "recommended_actions": self._build_recommendations(data),
            },
            "key_metrics": self._build_key_metrics(data),
        }

        # Optionally use Claude for narrative polish
        report["sections"] = await self._polish_with_llm(report["sections"], data)

        return report

    async def _gather_report_data(
        self, db: AsyncSession, org_id: UUID, period: str
    ) -> Dict[str, Any]:
        """Gather data from all intelligence engines."""
        data = {}

        # BI Dashboard
        try:
            from app.services.behavioral_intelligence_service import (
                BehavioralIntelligenceService,
            )

            bi = BehavioralIntelligenceService()
            data["bi"] = await bi.get_organization_dashboard(db, str(org_id))
        except Exception as e:
            logger.warning("BI data unavailable: %s", e)
            data["bi"] = {}

        # Pulse history for trends
        try:
            from app.db.models.organizational_pulse import PulseSnapshot

            days_map = {"weekly": 7, "monthly": 30, "quarterly": 90}
            lookback = days_map.get(period, 30)
            cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback)).date()

            result = await db.execute(
                select(PulseSnapshot)
                .where(
                    PulseSnapshot.organization_id == org_id,
                    PulseSnapshot.snapshot_date >= cutoff,
                )
                .order_by(desc(PulseSnapshot.snapshot_date))
            )
            snapshots = result.scalars().all()
            data["pulse_history"] = [
                {
                    "date": str(s.snapshot_date),
                    "score": (
                        float(s.overall_pulse_score) if s.overall_pulse_score else None
                    ),
                    "trend": s.trend,
                    "warning_count": s.warning_count,
                    "intervention_count": s.intervention_count,
                }
                for s in snapshots
            ]
        except Exception as e:
            logger.warning("Pulse history unavailable: %s", e)
            data["pulse_history"] = []

        # ONA for network health
        try:
            from app.services.organizational_network_service import (
                OrganizationalNetworkService,
            )

            ona = OrganizationalNetworkService()
            data["ona"] = await ona.analyze_organization(db, str(org_id))
        except Exception as e:
            logger.warning("ONA data unavailable: %s", e)
            data["ona"] = {}

        # Digital Twin
        try:
            from app.services.org_digital_twin_service import (
                OrganizationalDigitalTwinService,
            )

            twin = OrganizationalDigitalTwinService()
            data["digital_twin"] = await twin.get_current_state(db, str(org_id))
        except Exception as e:
            logger.warning("Digital Twin data unavailable: %s", e)
            data["digital_twin"] = {}

        # Interventions
        try:
            from app.services.intervention_service import intervention_service

            data["interventions"] = (
                await intervention_service.get_organization_interventions(
                    db, org_id, limit=20
                )
            )
        except Exception as e:
            logger.warning("Intervention data unavailable: %s", e)
            data["interventions"] = {}

        return data

    def _build_executive_summary(self, data: Dict) -> Dict[str, Any]:
        """3-sentence executive summary: overall health, biggest change, focus area."""
        bi = data.get("bi", {})
        scores = bi.get("scores", {})
        pulse_history = data.get("pulse_history", [])

        # Overall health
        health = scores.get("team_health", 0)
        if health >= 70:
            health_status = "healthy"
        elif health >= 50:
            health_status = "moderate with areas of concern"
        else:
            health_status = "at risk and requires attention"

        # Biggest change (from pulse trend)
        trend = "stable"
        if len(pulse_history) >= 2:
            latest = pulse_history[0].get("score") or 0
            earliest = pulse_history[-1].get("score") or 0
            delta = latest - earliest
            if delta > 5:
                trend = f"improving (+{delta:.0f} points)"
            elif delta < -5:
                trend = f"declining ({delta:.0f} points)"

        # Top risk
        risk_metrics = {
            "burnout_risk": scores.get("burnout_risk", 0),
            "friction_index": scores.get("friction_index", 0),
        }
        top_risk = max(risk_metrics, key=risk_metrics.get) if risk_metrics else "none"
        top_risk_value = risk_metrics.get(top_risk, 0)

        sentences = [
            f"The organization's overall health is {health_status} (score: {health:.0f}/100).",
            f"The trend over this period is {trend}.",
        ]
        if top_risk_value > 50:
            sentences.append(
                f"The primary area of concern is {top_risk.replace('_', ' ')} "
                f"at {top_risk_value:.0f}/100, which warrants focused intervention."
            )
        else:
            sentences.append("No critical risk areas require immediate attention.")

        return {
            "narrative": " ".join(sentences),
            "health_score": round(health, 1),
            "trend": trend,
            "top_risk": top_risk if top_risk_value > 50 else None,
        }

    def _build_improvements(self, data: Dict) -> Dict[str, Any]:
        """Identify metrics that improved over the period."""
        improvements = []
        bi = data.get("bi", {})
        teams = bi.get("teams", [])

        # Find teams with strong scores
        for team in teams:
            scores = team.get("scores", {})
            for metric, value in scores.items():
                if isinstance(value, (int, float)):
                    # Good: high health/collaboration/safety, low burnout/friction
                    if (
                        metric
                        in ("team_health", "collaboration", "psychological_safety")
                        and value >= 75
                    ):
                        improvements.append(
                            {
                                "team": team.get("team_name", "Unknown"),
                                "metric": metric.replace("_", " ").title(),
                                "value": round(value, 1),
                                "context": f"Strong {metric.replace('_', ' ')} indicating good team dynamics",
                            }
                        )
                    elif metric in ("burnout_risk", "friction_index") and value <= 25:
                        improvements.append(
                            {
                                "team": team.get("team_name", "Unknown"),
                                "metric": metric.replace("_", " ").title(),
                                "value": round(value, 1),
                                "context": f"Low {metric.replace('_', ' ')} — team is operating sustainably",
                            }
                        )

        # Sort by value (best first)
        improvements.sort(key=lambda x: x["value"], reverse=True)

        narrative = ""
        if improvements:
            top = improvements[0]
            narrative = (
                f"{top['team']} leads in {top['metric']} ({top['value']}/100). "
                f"{len(improvements)} positive signals detected across the organization."
            )
        else:
            narrative = "No standout improvements identified in this period."

        return {"narrative": narrative, "items": improvements[:5]}

    def _build_declines(self, data: Dict) -> Dict[str, Any]:
        """Identify metrics that declined or are concerning."""
        concerns = []
        bi = data.get("bi", {})
        teams = bi.get("teams", [])

        for team in teams:
            scores = team.get("scores", {})
            top_risk = team.get("top_risk")
            for metric, value in scores.items():
                if isinstance(value, (int, float)):
                    if (
                        metric
                        in ("team_health", "collaboration", "psychological_safety")
                        and value < 40
                    ):
                        concerns.append(
                            {
                                "team": team.get("team_name", "Unknown"),
                                "metric": metric.replace("_", " ").title(),
                                "value": round(value, 1),
                                "severity": "critical" if value < 25 else "warning",
                                "context": f"Low {metric.replace('_', ' ')} requires investigation",
                            }
                        )
                    elif metric in ("burnout_risk", "friction_index") and value > 60:
                        concerns.append(
                            {
                                "team": team.get("team_name", "Unknown"),
                                "metric": metric.replace("_", " ").title(),
                                "value": round(value, 1),
                                "severity": "critical" if value > 75 else "warning",
                                "context": f"Elevated {metric.replace('_', ' ')} — team may be under strain",
                            }
                        )

        concerns.sort(
            key=lambda x: (
                x["value"] if x["severity"] == "critical" else x["value"] - 100
            )
        )

        narrative = ""
        if concerns:
            critical = [c for c in concerns if c["severity"] == "critical"]
            narrative = (
                f"{len(concerns)} areas of concern detected, "
                f"{len(critical)} at critical severity. "
            )
            if critical:
                c = critical[0]
                narrative += (
                    f"Most urgent: {c['team']}'s {c['metric']} at {c['value']}/100."
                )
        else:
            narrative = "No significant declines detected in this period."

        return {"narrative": narrative, "items": concerns[:5]}

    def _build_team_spotlight(self, data: Dict) -> Dict[str, Any]:
        """Highlight 1-2 teams with notable changes."""
        bi = data.get("bi", {})
        teams = bi.get("teams", [])

        if not teams:
            return {"narrative": "Insufficient team data for spotlight.", "teams": []}

        # Find most notable teams (highest risk and highest performing)
        spotlights = []

        # Highest risk team
        risk_teams = sorted(
            teams, key=lambda t: t.get("scores", {}).get("team_health", 100)
        )
        if risk_teams and risk_teams[0].get("scores", {}).get("team_health", 100) < 50:
            team = risk_teams[0]
            spotlights.append(
                {
                    "team": team.get("team_name"),
                    "type": "concern",
                    "headline": f"{team.get('team_name')} needs attention",
                    "detail": f"Team health at {team['scores'].get('team_health', 0):.0f}/100. "
                    f"Top risk: {team.get('top_risk', 'unknown').replace('_', ' ')}.",
                }
            )

        # Highest performing team
        if len(risk_teams) > 1:
            best = risk_teams[-1]
            if best.get("scores", {}).get("team_health", 0) > 70:
                spotlights.append(
                    {
                        "team": best.get("team_name"),
                        "type": "positive",
                        "headline": f"{best.get('team_name')} is thriving",
                        "detail": f"Team health at {best['scores'].get('team_health', 0):.0f}/100 "
                        f"with strong collaboration and low burnout.",
                    }
                )

        narrative = " ".join(s["headline"] + ". " + s["detail"] for s in spotlights[:2])
        return {
            "narrative": narrative or "No standout teams in this period.",
            "teams": spotlights[:2],
        }

    def _build_risk_outlook(self, data: Dict) -> Dict[str, Any]:
        """Forward-looking risk assessment based on trends."""
        pulse_history = data.get("pulse_history", [])
        ona = data.get("ona", {})

        risks = []

        # Pulse trend
        if len(pulse_history) >= 3:
            recent_scores = [p["score"] for p in pulse_history[:3] if p.get("score")]
            if recent_scores and all(s < recent_scores[-1] for s in recent_scores[:-1]):
                risks.append(
                    "Organizational pulse is on a downward trend — early intervention recommended."
                )

        # ONA isolation
        isolated = ona.get("insights", {}).get("isolated", [])
        if len(isolated) > 3:
            risks.append(
                f"{len(isolated)} employees are isolated in the network — flight risk increases."
            )

        # Warning accumulation
        if pulse_history and pulse_history[0].get("warning_count", 0) > 3:
            risks.append(
                f"{pulse_history[0]['warning_count']} active early warnings require attention."
            )

        narrative = (
            " ".join(risks)
            if risks
            else "No significant forward-looking risks identified."
        )
        return {"narrative": narrative, "risks": risks}

    def _build_recommendations(self, data: Dict) -> Dict[str, Any]:
        """Top 3 recommended actions based on data."""
        actions = []
        bi = data.get("bi", {})
        scores = bi.get("scores", {})

        if scores.get("burnout_risk", 0) > 60:
            actions.append(
                {
                    "priority": 1,
                    "action": "Launch burnout mitigation program",
                    "rationale": f"Org-wide burnout risk at {scores['burnout_risk']:.0f}/100",
                    "metric_to_track": "burnout_risk",
                }
            )

        if scores.get("collaboration", 0) < 45:
            actions.append(
                {
                    "priority": 2,
                    "action": "Initiate cross-team collaboration program",
                    "rationale": f"Collaboration score at {scores['collaboration']:.0f}/100",
                    "metric_to_track": "collaboration",
                }
            )

        if scores.get("manager_health", 0) < 45:
            actions.append(
                {
                    "priority": 2,
                    "action": "Provide executive coaching for managers",
                    "rationale": f"Manager health at {scores['manager_health']:.0f}/100",
                    "metric_to_track": "manager_health",
                }
            )

        if scores.get("friction_index", 0) > 55:
            actions.append(
                {
                    "priority": 3,
                    "action": "Run friction reduction retrospectives",
                    "rationale": f"Friction index at {scores['friction_index']:.0f}/100",
                    "metric_to_track": "friction_index",
                }
            )

        if scores.get("psychological_safety", 0) < 40:
            actions.append(
                {
                    "priority": 1,
                    "action": "Psychological safety workshops for all teams",
                    "rationale": f"Psych safety at {scores['psychological_safety']:.0f}/100",
                    "metric_to_track": "psychological_safety",
                }
            )

        # Intervention effectiveness
        interventions = data.get("interventions", {})
        if interventions.get("improvement_rate", 0) > 0:
            rate = interventions["improvement_rate"]
            actions.append(
                {
                    "priority": 3,
                    "action": f"Continue current intervention programs ({rate:.0f}% improvement rate)",
                    "rationale": "Data shows interventions are working",
                    "metric_to_track": "intervention_effectiveness",
                }
            )

        actions.sort(key=lambda x: x["priority"])
        narrative = "; ".join(f"({a['priority']}) {a['action']}" for a in actions[:3])
        return {
            "narrative": narrative or "No specific actions recommended.",
            "actions": actions[:3],
        }

    def _build_key_metrics(self, data: Dict) -> Dict[str, Any]:
        """Summary metrics card for the report header."""
        bi = data.get("bi", {})
        scores = bi.get("scores", {})
        pulse = data.get("pulse_history", [])

        return {
            "team_health": round(scores.get("team_health", 0), 1),
            "collaboration": round(scores.get("collaboration", 0), 1),
            "burnout_risk": round(scores.get("burnout_risk", 0), 1),
            "psychological_safety": round(scores.get("psychological_safety", 0), 1),
            "pulse_score": (
                round(pulse[0]["score"], 1) if pulse and pulse[0].get("score") else None
            ),
            "team_count": bi.get("team_count", 0),
            "active_warnings": pulse[0].get("warning_count", 0) if pulse else 0,
        }

    async def _polish_with_llm(
        self, sections: Dict[str, Any], data: Dict
    ) -> Dict[str, Any]:
        """Optionally polish narratives with Claude for publication quality."""
        try:
            import anthropic
            import json

            client = anthropic.AsyncAnthropic()

            narratives = {
                k: v.get("narrative", "")
                for k, v in sections.items()
                if isinstance(v, dict)
            }

            response = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=(
                    "You are an executive report writer. Rewrite the following section narratives "
                    "to be more polished and professional while preserving all data points and numbers. "
                    "Keep each section to 2-3 sentences max. Return JSON with the same keys."
                ),
                messages=[
                    {
                        "role": "user",
                        "content": json.dumps(narratives),
                    }
                ],
            )

            polished = json.loads(response.content[0].text)
            for key, narrative in polished.items():
                if key in sections and isinstance(sections[key], dict):
                    sections[key]["narrative"] = narrative

        except Exception as e:
            logger.debug("LLM polish skipped: %s", e)

        return sections


# Singleton
narrative_intelligence_service = NarrativeIntelligenceService()
