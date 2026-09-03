# app/services/organizational_chat_service.py
"""
Organizational Chat Service — Conversational AI Coach

Takes natural language questions about organizational health and returns
data-grounded answers by querying PsychSync's intelligence engines
(BI, ONA, Pulse, Digital Twin, OKR) and synthesizing responses via Claude.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

AVAILABLE_ENGINES = [
    "bi_dashboard",
    "ona_analysis",
    "pulse",
    "digital_twin",
    "okr_summary",
    "intervention_history",
]


class OrganizationalChatService:
    """
    Conversational interface over PsychSync intelligence engines.

    Flow:
    1. User asks a question
    2. _select_data_sources() determines which engines to query
    3. _gather_context() calls those engines and formats results
    4. _generate_response() sends context + question to Claude API
    5. Returns structured answer with evidence citations
    """

    async def ask(
        self,
        db: AsyncSession,
        org_id: UUID,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Answer an organizational intelligence question.

        Args:
            db: Database session
            org_id: Organization to query
            question: Natural language question
            conversation_history: Previous messages for multi-turn context

        Returns:
            {answer, evidence, sources_queried, confidence}
        """
        # Step 1: Determine which engines to query
        sources = self._select_data_sources(question)

        # Step 2: Gather context from selected engines
        context = await self._gather_context(db, org_id, sources)

        # Step 3: Generate response via Claude
        response = await self._generate_response(
            question, context, conversation_history or []
        )

        return {
            "answer": response.get("answer", ""),
            "evidence": response.get("evidence", []),
            "sources_queried": sources,
            "suggested_actions": response.get("suggested_actions", []),
            "confidence": response.get("confidence", 0.0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _select_data_sources(self, question: str) -> list[str]:
        """
        Route questions to the right intelligence engines via keyword matching.
        Returns 1-4 engine names to query. Always includes bi_dashboard as
        baseline context unless the question is clearly about OKRs or interventions only.
        """
        q = question.lower()
        sources = set()

        # ONA signals: network, collaboration patterns, isolation, bridges
        ona_keywords = {
            "collaborat",
            "isolat",
            "silo",
            "network",
            "bridge",
            "connect",
            "influencer",
            "community",
            "fragment",
            "cross-team",
            "who ",
            "hidden",
            "bottleneck",
        }
        if any(kw in q for kw in ona_keywords):
            sources.add("ona_analysis")

        # Pulse signals: predictions, warnings, flight risk, interventions
        pulse_keywords = {
            "predict",
            "warning",
            "flight",
            "risk",
            "early",
            "proactive",
            "pulse",
            "trend",
            "declining",
            "improving",
            "isolation",
            "friction",
            "change impact",
        }
        if any(kw in q for kw in pulse_keywords):
            sources.add("pulse")

        # Digital Twin: structure, simulation, what-if, dimensions
        twin_keywords = {
            "structure",
            "twin",
            "dimension",
            "what if",
            "what-if",
            "simulate",
            "reorg",
            "restructur",
            "merge",
            "split",
            "departure",
            "scenario",
            "culture",
            "turnover",
        }
        if any(kw in q for kw in twin_keywords):
            sources.add("digital_twin")

        # OKR: goals, objectives, progress, performance
        okr_keywords = {
            "okr",
            "objective",
            "key result",
            "goal",
            "target",
            "progress",
            "quarter",
            "achievement",
            "kr ",
        }
        if any(kw in q for kw in okr_keywords):
            sources.add("okr_summary")

        # Interventions: actions taken, what worked, past efforts
        intervention_keywords = {
            "intervention",
            "action plan",
            "what worked",
            "resolved",
            "improvement",
            "addressed",
            "follow-up",
            "measure",
        }
        if any(kw in q for kw in intervention_keywords):
            sources.add("intervention_history")

        # BI is baseline for most health/score questions
        bi_keywords = {
            "health",
            "score",
            "burnout",
            "manager",
            "safety",
            "engagement",
            "team",
            "how is",
            "how are",
            "status",
            "wellness",
            "psychological",
        }
        if any(kw in q for kw in bi_keywords):
            sources.add("bi_dashboard")

        # Default: if nothing matched or question is generic, query BI + Pulse
        if not sources:
            sources = {"bi_dashboard", "pulse"}

        # Always include BI if we're querying 2+ engines (provides baseline context)
        if len(sources) >= 2 and "bi_dashboard" not in sources:
            sources.add("bi_dashboard")

        # Cap at 4 engines for latency
        return list(sources)[:4]

    async def _gather_context(
        self, db: AsyncSession, org_id: UUID, sources: List[str]
    ) -> Dict[str, Any]:
        """Query selected engines and format results as context."""
        context = {}

        if "bi_dashboard" in sources:
            try:
                from app.services.behavioral_intelligence_service import (
                    BehavioralIntelligenceService,
                )

                bi = BehavioralIntelligenceService()
                dashboard = await bi.get_organization_dashboard(db, str(org_id))
                context["bi_dashboard"] = {
                    "scores": dashboard.get("scores", {}),
                    "teams": [
                        {
                            "team_name": t.get("team_name"),
                            "scores": t.get("scores", {}),
                            "top_risk": t.get("top_risk"),
                        }
                        for t in dashboard.get("teams", [])[:10]
                    ],
                    "executive_summary": dashboard.get("executive_summary", ""),
                }
            except Exception as e:
                logger.warning("Failed to gather BI context: %s", e)

        if "ona_analysis" in sources:
            try:
                from app.services.organizational_network_service import (
                    OrganizationalNetworkService,
                )

                ona = OrganizationalNetworkService()
                network = await ona.analyze_organization(db, str(org_id))
                context["ona_analysis"] = {
                    "network_stats": network.get("network_stats", {}),
                    "insights": {
                        k: v
                        for k, v in network.get("insights", {}).items()
                        if k
                        in (
                            "isolated",
                            "influencers",
                            "bridges",
                            "manager_dependency",
                            "cross_team_collaboration",
                        )
                    },
                }
            except Exception as e:
                logger.warning("Failed to gather ONA context: %s", e)

        if "pulse" in sources:
            try:
                from app.services.organizational_pulse_service import (
                    OrganizationalPulseService,
                )

                pulse_svc = OrganizationalPulseService()
                pulse = await pulse_svc.generate_pulse(db, str(org_id))
                context["pulse"] = {
                    "overall_score": pulse.get("overall_pulse", {}).get("score"),
                    "trend": pulse.get("overall_pulse", {}).get("trend"),
                    "early_warnings": pulse.get("early_warnings", [])[:5],
                    "questions_summary": {
                        q.get("question", ""): q.get("answer", "")[:200]
                        for q in pulse.get("questions", [])
                    },
                }
            except Exception as e:
                logger.warning("Failed to gather Pulse context: %s", e)

        if "digital_twin" in sources:
            try:
                from app.services.org_digital_twin_service import (
                    OrganizationalDigitalTwinService,
                )

                twin = OrganizationalDigitalTwinService()
                state = await twin.get_current_state(db, str(org_id))
                context["digital_twin"] = {
                    "overall_health": state.get("overall_health"),
                    "dimensions": {
                        k: {
                            "score": v.get("score"),
                            "highlights": v.get("highlights", []),
                        }
                        for k, v in state.get("dimensions", {}).items()
                    },
                }
            except Exception as e:
                logger.warning("Failed to gather Digital Twin context: %s", e)

        if "okr_summary" in sources:
            try:
                from app.services.okr_service import OKRService

                okr = OKRService(db)
                from app.db.models.okr import OKRPeriod

                now = datetime.now(timezone.utc)
                quarter = f"q{(now.month - 1) // 3 + 1}"
                period = OKRPeriod(quarter)
                summary = await okr.get_okr_summary(
                    period, now.year, organization_id=org_id
                )
                context["okr_summary"] = summary
            except Exception as e:
                logger.warning("Failed to gather OKR context: %s", e)

        if "intervention_history" in sources:
            try:
                from app.services.intervention_service import intervention_service

                interventions = (
                    await intervention_service.get_organization_interventions(
                        db, org_id, limit=10
                    )
                )
                context["intervention_history"] = {
                    "total": interventions.get("total", 0),
                    "improvement_rate": interventions.get("improvement_rate", 0),
                    "by_status": interventions.get("by_status", {}),
                    "recent": [
                        {
                            "title": i["title"],
                            "signal": i["source_signal"],
                            "status": i["status"],
                            "outcome": i.get("outcome_result"),
                        }
                        for i in interventions.get("interventions", [])[:5]
                    ],
                }
            except Exception as e:
                logger.warning("Failed to gather intervention context: %s", e)

        return context

    async def _generate_response(
        self,
        question: str,
        context: Dict[str, Any],
        history: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Generate a grounded response using Claude API."""
        try:
            import anthropic
            import json

            client = anthropic.AsyncAnthropic()

            system_prompt = (
                "You are PsychSync's organizational intelligence assistant. "
                "You answer questions about organizational health using ONLY the data provided. "
                "Never speculate beyond what the data shows. "
                "Always cite specific metrics and scores as evidence. "
                "If the data doesn't contain enough information to answer, say so.\n\n"
                "Respond in JSON format with keys: "
                '"answer" (string, 2-4 sentences), '
                '"evidence" (list of {metric, value, context} dicts), '
                '"suggested_actions" (list of strings, max 3), '
                '"confidence" (float 0-1, based on data completeness).'
            )

            messages = []
            for msg in history[-5:]:  # Last 5 messages for context
                messages.append(
                    {
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    }
                )

            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Question: {question}\n\n"
                        f"Available data:\n{json.dumps(context, indent=2, default=str)}"
                    ),
                }
            )

            response = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
            )

            answer_text = response.content[0].text

            # Parse JSON response
            try:
                parsed = json.loads(answer_text)
                return parsed
            except json.JSONDecodeError:
                return {
                    "answer": answer_text,
                    "evidence": [],
                    "suggested_actions": [],
                    "confidence": 0.5,
                }

        except ImportError:
            logger.warning("anthropic package not installed — using fallback response")
            return self._fallback_response(question, context)
        except Exception as e:
            logger.error("Claude API error: %s", e)
            return self._fallback_response(question, context)

    def _fallback_response(
        self, question: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a basic response without LLM when Claude is unavailable."""
        # Extract key metrics from context
        evidence = []
        if "bi_dashboard" in context:
            scores = context["bi_dashboard"].get("scores", {})
            for metric, value in scores.items():
                if isinstance(value, (int, float)) and value > 0:
                    evidence.append(
                        {
                            "metric": metric,
                            "value": round(value, 1),
                            "context": "organization-wide",
                        }
                    )

        summary = context.get("bi_dashboard", {}).get("executive_summary", "")

        return {
            "answer": summary
            or "I have the data but need the Claude API to synthesize a response. Please check your API key configuration.",
            "evidence": evidence[:5],
            "suggested_actions": [],
            "confidence": 0.3,
        }


# Singleton
organizational_chat_service = OrganizationalChatService()
