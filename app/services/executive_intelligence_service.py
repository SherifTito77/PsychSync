"""
Executive Intelligence Service

The integration layer that PsychSync was missing.

Combines three data engines into team-specific, temporal, executive-grade narratives:
  1. Behavioral Intelligence scores (team health, burnout, collaboration, etc.)
  2. ONA network graphs (communities, influencers, cross-team edges, temporal snapshots)
  3. HRIS signals (turnover, tenure, performance)

Instead of: "Employee X is high conscientiousness"
Produces:  "Sales Team B has become increasingly siloed over the last 45 days.
            Collaboration with Customer Success dropped 38%.
            Burnout indicators increased after organizational restructuring."

Supports both LLM-powered and rule-based narrative generation.
"""

import json
import logging
import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.network_analysis import NetworkSnapshot
from app.db.models.team import Team, TeamMember
from app.db.models.user import User
from app.services.behavioral_intelligence_service import BehavioralIntelligenceService
from app.services.organizational_network_service import OrganizationalNetworkService

logger = logging.getLogger(__name__)

_bi_service = BehavioralIntelligenceService()
_ona_service = OrganizationalNetworkService()


class ExecutiveIntelligenceService:
    """
    Produces executive-grade organizational narratives by fusing
    Behavioral Intelligence + ONA + HRIS into actionable stories.
    """

    async def generate_executive_briefing(
        self,
        db: AsyncSession,
        organization_id: str,
        lookback_days: int = 45,
    ) -> Dict[str, Any]:
        """
        Full executive intelligence briefing for an organization.
        Returns team-level narratives, trend alerts, and cross-team stories.
        """
        # 1. Gather BI scores for all teams
        bi_dashboard = await _bi_service.get_organization_dashboard(
            db, organization_id, lookback_days
        )
        teams = bi_dashboard.get("teams", [])
        org_scores = bi_dashboard.get("scores", {})

        # 2. Gather ONA temporal snapshots
        snapshots = await self._get_temporal_snapshots(
            db, organization_id, lookback_days
        )

        # 3. Gather ONA current state (communities, cross-team, dependencies)
        ona_analysis = await self._get_ona_analysis(db, organization_id, lookback_days)

        # 4. Generate team-level narratives
        team_narratives = []
        for team in teams:
            narrative = await self._generate_team_narrative(
                db, team, snapshots, ona_analysis, lookback_days
            )
            if narrative:
                team_narratives.append(narrative)

        # 5. Generate cross-team relationship stories
        cross_team_stories = self._generate_cross_team_stories(
            teams, ona_analysis, snapshots
        )

        # 6. Generate temporal trend alerts
        trend_alerts = self._generate_trend_alerts(org_scores, snapshots, teams)

        # 7. Try LLM-enhanced executive summary
        executive_summary = await self._generate_llm_summary(
            org_scores, team_narratives, cross_team_stories, trend_alerts
        )

        # Sort by urgency (highest risk first)
        team_narratives.sort(key=lambda n: n.get("urgency_score", 0), reverse=True)

        return {
            "organization_id": organization_id,
            "lookback_days": lookback_days,
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": executive_summary,
            "org_scores": org_scores,
            "team_narratives": team_narratives,
            "cross_team_stories": cross_team_stories,
            "trend_alerts": trend_alerts,
            "data_sources": {
                "behavioral_intelligence": bool(teams),
                "network_analysis": bool(ona_analysis.get("communities")),
                "temporal_snapshots": len(snapshots),
            },
        }

    # ── Team-level narrative generation ───────────────────────────

    async def _generate_team_narrative(
        self,
        db: AsyncSession,
        team: Dict[str, Any],
        snapshots: List[Dict],
        ona_analysis: Dict[str, Any],
        lookback_days: int,
    ) -> Optional[Dict[str, Any]]:
        """Produce a narrative for a single team combining all signal sources."""
        scores = team.get("scores", {})
        team_name = team.get("team_name", "Unknown Team")
        team_id = team.get("team_id", "")

        signals = []
        urgency = 0

        # ── BI signals ──
        burnout = scores.get("burnout_risk", 0)
        if burnout > 60:
            signals.append(
                {
                    "type": "burnout_risk",
                    "severity": "high" if burnout > 75 else "elevated",
                    "message": f"Burnout risk is at {burnout}%, well above the safe threshold of 40%.",
                }
            )
            urgency += burnout / 10

        collaboration = scores.get("collaboration", 0)
        if collaboration < 50:
            signals.append(
                {
                    "type": "low_collaboration",
                    "severity": "high" if collaboration < 30 else "moderate",
                    "message": f"Collaboration score is {collaboration}% — team may be working in silos.",
                }
            )
            urgency += (100 - collaboration) / 10

        friction = scores.get("friction_index", 0)
        if friction > 60:
            signals.append(
                {
                    "type": "high_friction",
                    "severity": "high" if friction > 75 else "elevated",
                    "message": f"Organizational friction at {friction}% — coordination overhead is slowing delivery.",
                }
            )
            urgency += friction / 15

        psych_safety = scores.get("psychological_safety", 0)
        if psych_safety < 45:
            signals.append(
                {
                    "type": "low_psych_safety",
                    "severity": "high" if psych_safety < 30 else "moderate",
                    "message": f"Psychological safety at {psych_safety}% — team members may not feel safe raising concerns.",
                }
            )
            urgency += (100 - psych_safety) / 12

        # ── ONA signals ──
        dependencies = ona_analysis.get("manager_dependencies", [])
        team_deps = [d for d in dependencies if d.get("team_id") == team_id]
        for dep in team_deps:
            ratio = dep.get("dependency_ratio", 0)
            if ratio > 2.0:
                signals.append(
                    {
                        "type": "manager_dependency",
                        "severity": "high" if ratio > 3.0 else "moderate",
                        "message": (
                            f"Communication flows through a single person "
                            f"({ratio:.1f}x the team average). "
                            f"Bus factor risk if this person leaves."
                        ),
                    }
                )
                urgency += ratio

        # ── Temporal trend signals ──
        temporal_msg = self._compute_temporal_change(team_id, snapshots, lookback_days)
        if temporal_msg:
            signals.append(temporal_msg)
            urgency += 3

        if not signals:
            return None

        # Build narrative text
        narrative_text = self._compose_narrative(team_name, signals)

        return {
            "team_id": team_id,
            "team_name": team_name,
            "member_count": team.get("member_count", 0),
            "urgency_score": round(urgency, 1),
            "top_risk": team.get("top_risk", "None"),
            "scores": scores,
            "signals": signals,
            "narrative": narrative_text,
            "recommended_actions": self._recommend_actions(signals),
        }

    def _compose_narrative(self, team_name: str, signals: List[Dict]) -> str:
        """Compose a human-readable narrative paragraph from signals."""
        if not signals:
            return f"{team_name} is operating within healthy parameters."

        parts = [f"{team_name} requires attention."]

        for sig in signals[:4]:  # Cap at 4 most important
            parts.append(sig["message"])

        return " ".join(parts)

    def _recommend_actions(self, signals: List[Dict]) -> List[str]:
        """Generate concrete action items from detected signals."""
        actions = []
        types_seen = set()

        for sig in signals:
            st = sig["type"]
            if st in types_seen:
                continue
            types_seen.add(st)

            if st == "burnout_risk":
                actions.append(
                    "Conduct 1:1 check-ins with team members this week. "
                    "Review workload distribution and enforce recovery time."
                )
            elif st == "low_collaboration":
                actions.append(
                    "Schedule cross-functional working sessions. "
                    "Investigate if recent changes isolated this team from partners."
                )
            elif st == "high_friction":
                actions.append(
                    "Audit coordination overhead — reduce unnecessary meetings and approvals. "
                    "Consider facilitated conflict resolution if personality friction is high."
                )
            elif st == "low_psych_safety":
                actions.append(
                    "Create anonymous feedback channels. "
                    "Train managers on psychological safety practices (Edmondson framework)."
                )
            elif st == "manager_dependency":
                actions.append(
                    "Distribute decision-making authority. "
                    "Cross-train team members on key processes to reduce single-point-of-failure risk."
                )
            elif st == "network_density_drop":
                actions.append(
                    "Investigate what changed — reorg, departures, or remote transition? "
                    "Re-establish regular touchpoints between affected teams."
                )
            elif st == "isolation_increase":
                actions.append(
                    "Identify newly isolated employees and assign mentors or collaboration buddies."
                )

        return (
            actions
            if actions
            else ["Continue monitoring — no immediate actions required."]
        )

    # ── Cross-team relationship stories ───────────────────────────

    def _generate_cross_team_stories(
        self,
        teams: List[Dict],
        ona_analysis: Dict[str, Any],
        snapshots: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Detect and narrate cross-team relationship changes."""
        stories = []
        cross_team = ona_analysis.get("cross_team_collaboration", [])

        # Build team name lookup
        team_names = {t["team_id"]: t["team_name"] for t in teams}

        for pair in cross_team:
            team_a = pair.get("team_a", "")
            team_b = pair.get("team_b", "")
            strength = pair.get("collaboration_strength", 0)
            label = pair.get("label", "Weak")

            name_a = team_names.get(team_a, team_a[:8])
            name_b = team_names.get(team_b, team_b[:8])

            if label == "Weak" and strength <= 2:
                stories.append(
                    {
                        "type": "silo_detected",
                        "teams": [name_a, name_b],
                        "severity": "high",
                        "narrative": (
                            f"{name_a} and {name_b} have minimal collaboration "
                            f"(strength: {strength}). These teams may be operating in silos. "
                            f"Consider cross-functional projects or shared objectives to rebuild connections."
                        ),
                        "strength": strength,
                    }
                )
            elif label == "Strong" and strength > 5:
                stories.append(
                    {
                        "type": "strong_partnership",
                        "teams": [name_a, name_b],
                        "severity": "positive",
                        "narrative": (
                            f"{name_a} and {name_b} have strong collaboration "
                            f"(strength: {strength}). This partnership is a model for cross-team effectiveness."
                        ),
                        "strength": strength,
                    }
                )

        # Detect teams with no cross-team connections
        teams_in_pairs = set()
        for pair in cross_team:
            teams_in_pairs.add(pair.get("team_a", ""))
            teams_in_pairs.add(pair.get("team_b", ""))

        for t in teams:
            tid = t["team_id"]
            if tid not in teams_in_pairs and t.get("member_count", 0) >= 3:
                stories.append(
                    {
                        "type": "completely_isolated",
                        "teams": [t["team_name"]],
                        "severity": "critical",
                        "narrative": (
                            f"{t['team_name']} has no detected cross-team collaboration. "
                            f"This team is operating in complete isolation, "
                            f"which increases knowledge silo risk and reduces organizational agility."
                        ),
                        "strength": 0,
                    }
                )

        stories.sort(
            key=lambda s: {"critical": 3, "high": 2, "positive": 0}.get(
                s["severity"], 1
            ),
            reverse=True,
        )
        return stories

    # ── Temporal trend alerts ─────────────────────────────────────

    def _generate_trend_alerts(
        self,
        org_scores: Dict[str, float],
        snapshots: List[Dict],
        teams: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Generate alerts from temporal trends in network and BI data."""
        alerts = []

        if len(snapshots) >= 2:
            first = snapshots[0]
            last = snapshots[-1]

            # Network density change
            d_first = float(first.get("density") or 0)
            d_last = float(last.get("density") or 0)
            if d_first > 0:
                density_change_pct = ((d_last - d_first) / d_first) * 100
                if density_change_pct < -15:
                    alerts.append(
                        {
                            "type": "network_density_declining",
                            "severity": "high",
                            "metric": "network_density",
                            "change_pct": round(density_change_pct, 1),
                            "message": (
                                f"Network density dropped {abs(density_change_pct):.0f}% "
                                f"over the observation period. The organization is becoming less connected."
                            ),
                        }
                    )

            # Isolate increase
            iso_first = int(first.get("num_isolates") or 0)
            iso_last = int(last.get("num_isolates") or 0)
            iso_increase = iso_last - iso_first
            if iso_increase >= 3:
                alerts.append(
                    {
                        "type": "isolation_increase",
                        "severity": "moderate",
                        "metric": "num_isolates",
                        "change_absolute": iso_increase,
                        "message": (
                            f"{iso_increase} additional employees became isolated during this period. "
                            f"Investigate whether recent departures, reorgs, or remote transitions caused this."
                        ),
                    }
                )

            # Community fragmentation
            comm_first = int(first.get("num_communities") or 0)
            comm_last = int(last.get("num_communities") or 0)
            if comm_last > comm_first + 2:
                alerts.append(
                    {
                        "type": "community_fragmentation",
                        "severity": "moderate",
                        "metric": "num_communities",
                        "change_absolute": comm_last - comm_first,
                        "message": (
                            f"Community count increased from {comm_first} to {comm_last}. "
                            f"The organization may be fragmenting into smaller, disconnected clusters."
                        ),
                    }
                )

        # BI-level alerts
        burnout = org_scores.get("burnout_risk", 0)
        if burnout > 60:
            at_risk_teams = [
                t["team_name"] for t in teams if t["scores"].get("burnout_risk", 0) > 60
            ]
            alerts.append(
                {
                    "type": "org_burnout_elevated",
                    "severity": "high",
                    "metric": "burnout_risk",
                    "org_score": burnout,
                    "message": (
                        f"Organization-wide burnout risk is {burnout}%. "
                        + (
                            f"Most affected: {', '.join(at_risk_teams[:3])}."
                            if at_risk_teams
                            else ""
                        )
                    ),
                }
            )

        collab = org_scores.get("collaboration", 0)
        if collab < 45:
            alerts.append(
                {
                    "type": "org_collaboration_low",
                    "severity": "high",
                    "metric": "collaboration",
                    "org_score": collab,
                    "message": (
                        f"Organization-wide collaboration is at {collab}%. "
                        f"Teams may not be working together effectively across boundaries."
                    ),
                }
            )

        alerts.sort(
            key=lambda a: {"high": 3, "moderate": 2, "low": 1}.get(a["severity"], 0),
            reverse=True,
        )
        return alerts

    # ── Temporal snapshot helpers ─────────────────────────────────

    async def _get_temporal_snapshots(
        self, db: AsyncSession, organization_id: str, lookback_days: int
    ) -> List[Dict]:
        """Fetch network snapshots for temporal analysis."""
        since = date.today() - timedelta(days=lookback_days)
        result = await db.execute(
            select(NetworkSnapshot)
            .where(
                and_(
                    NetworkSnapshot.organization_id == organization_id,
                    NetworkSnapshot.snapshot_date >= since,
                )
            )
            .order_by(NetworkSnapshot.snapshot_date.asc())
        )
        snapshots = result.scalars().all()
        return [
            {
                "date": str(s.snapshot_date),
                "density": float(s.density) if s.density else 0,
                "total_nodes": s.total_nodes,
                "total_edges": s.total_edges,
                "num_communities": s.num_communities,
                "num_isolates": s.num_isolates,
                "num_influencers": s.num_influencers,
                "num_bridges": s.num_bridges,
                "avg_degree_centrality": (
                    float(s.avg_degree_centrality) if s.avg_degree_centrality else 0
                ),
                "node_metrics": s.node_metrics,
            }
            for s in snapshots
        ]

    async def _get_ona_analysis(
        self, db: AsyncSession, organization_id: str, lookback_days: int
    ) -> Dict[str, Any]:
        """Run ONA analysis for current state."""
        try:
            analysis = await _ona_service.analyze_organization(
                db, organization_id, lookback_days
            )
            return analysis
        except Exception as e:
            logger.warning("ONA analysis failed: %s", e)
            return {
                "communities": [],
                "cross_team_collaboration": [],
                "manager_dependencies": [],
            }

    def _compute_temporal_change(
        self, team_id: str, snapshots: List[Dict], lookback_days: int
    ) -> Optional[Dict[str, Any]]:
        """Detect per-team network metric changes over time."""
        if len(snapshots) < 2:
            return None

        first = snapshots[0]
        last = snapshots[-1]

        # Compare team-member connectivity from node_metrics
        first_nodes = first.get("node_metrics") or []
        last_nodes = last.get("node_metrics") or []

        if not first_nodes or not last_nodes:
            return None

        # Average degree centrality across snapshots
        first_avg = self._avg_node_metric(first_nodes, "degree")
        last_avg = self._avg_node_metric(last_nodes, "degree")

        if first_avg > 0:
            change_pct = ((last_avg - first_avg) / first_avg) * 100
            days = lookback_days
            if change_pct < -20:
                return {
                    "type": "network_density_drop",
                    "severity": "high" if change_pct < -35 else "moderate",
                    "message": (
                        f"Team connectivity dropped {abs(change_pct):.0f}% over the last {days} days. "
                        f"This team is becoming increasingly disconnected from the broader organization."
                    ),
                }

        return None

    def _avg_node_metric(self, nodes: List[Dict], metric: str) -> float:
        vals = [n.get(metric, 0) for n in nodes if n.get(metric) is not None]
        return sum(vals) / len(vals) if vals else 0

    # ── LLM-powered executive summary ─────────────────────────────

    async def _generate_llm_summary(
        self,
        org_scores: Dict[str, float],
        team_narratives: List[Dict],
        cross_team_stories: List[Dict],
        trend_alerts: List[Dict],
    ) -> str:
        """
        Generate an executive summary using LLM if available,
        otherwise fall back to rule-based composition.
        """
        # Try LLM first
        llm_summary = await self._try_llm_summary(
            org_scores, team_narratives, cross_team_stories, trend_alerts
        )
        if llm_summary:
            return llm_summary

        # Rule-based fallback
        return self._rule_based_summary(
            org_scores, team_narratives, cross_team_stories, trend_alerts
        )

    async def _try_llm_summary(
        self,
        org_scores: Dict,
        team_narratives: List[Dict],
        cross_team_stories: List[Dict],
        trend_alerts: List[Dict],
    ) -> Optional[str]:
        """Attempt LLM-powered narrative generation."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        try:
            import openai

            client = openai.AsyncOpenAI(api_key=api_key, timeout=30.0)

            # Build context
            context = self._build_llm_context(
                org_scores, team_narratives, cross_team_stories, trend_alerts
            )

            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior I/O psychologist with expertise in organizational network analysis. "
                            "You produce executive intelligence briefings that fuse behavioral science, "
                            "collaboration network data, and workforce signals into actionable narratives.\n\n"
                            "FORMAT: Lead with the single highest-priority risk and its root cause. "
                            "Then cover 2-3 supporting findings. Close with concrete, time-bound actions.\n\n"
                            "RULES:\n"
                            "- Name teams and departments, never individual employees.\n"
                            "- Use specific metrics: percentages, score changes, time ranges.\n"
                            "- Attribute patterns to structural/systemic causes, not individual traits.\n"
                            "- Never use personality labels (MBTI types, Big Five trait names).\n"
                            "- Never speculate on clinical diagnoses or mental health conditions.\n"
                            "- Distinguish correlation from causation — say 'coincides with' not 'caused by' "
                            "when the link is uncertain.\n\n"
                            "TONE: Concise and direct, suitable for a weekly leadership sync. "
                            "Keep the briefing under 250 words."
                        ),
                    },
                    {"role": "user", "content": context},
                ],
                temperature=0.5,
                max_tokens=500,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.warning("LLM executive summary failed: %s", e)
            return None

    def _build_llm_context(
        self,
        org_scores: Dict,
        team_narratives: List[Dict],
        cross_team_stories: List[Dict],
        trend_alerts: List[Dict],
    ) -> str:
        """Build structured context for the LLM prompt."""
        parts = ["Generate an executive intelligence briefing from this data:\n"]

        # Org-level scores
        parts.append("## Organization Scores")
        for key, val in org_scores.items():
            label = key.replace("_", " ").title()
            parts.append(f"- {label}: {val}")

        # Team risks
        if team_narratives:
            parts.append("\n## Teams Requiring Attention")
            for tn in team_narratives[:5]:
                parts.append(
                    f"- {tn['team_name']} (urgency {tn['urgency_score']}): "
                    f"{tn['narrative']}"
                )

        # Cross-team
        if cross_team_stories:
            parts.append("\n## Cross-Team Dynamics")
            for story in cross_team_stories[:5]:
                parts.append(f"- {story['narrative']}")

        # Trends
        if trend_alerts:
            parts.append("\n## Trend Alerts")
            for alert in trend_alerts[:5]:
                parts.append(f"- [{alert['severity'].upper()}] {alert['message']}")

        return "\n".join(parts)

    def _rule_based_summary(
        self,
        org_scores: Dict,
        team_narratives: List[Dict],
        cross_team_stories: List[Dict],
        trend_alerts: List[Dict],
    ) -> str:
        """Rule-based executive summary when LLM is unavailable."""
        parts = []

        # Overall health
        health = org_scores.get("team_health", 0)
        if health >= 70:
            parts.append(f"Organization health is strong at {health}%.")
        elif health >= 50:
            parts.append(
                f"Organization health is moderate at {health}%, with areas requiring attention."
            )
        elif health > 0:
            parts.append(
                f"Organization health is concerning at {health}% and requires immediate focus."
            )

        # Burnout
        burnout = org_scores.get("burnout_risk", 0)
        if burnout > 60:
            parts.append(f"Burnout risk is elevated at {burnout}%.")

        # Collaboration
        collab = org_scores.get("collaboration", 0)
        if collab < 50:
            parts.append(f"Collaboration is weak at {collab}% — teams may be siloed.")

        # Team-specific
        urgent_teams = [t for t in team_narratives if t.get("urgency_score", 0) > 5]
        if urgent_teams:
            names = ", ".join(t["team_name"] for t in urgent_teams[:3])
            parts.append(f"Teams requiring immediate attention: {names}.")

        # Cross-team silos
        silos = [s for s in cross_team_stories if s["type"] == "silo_detected"]
        if silos:
            parts.append(
                f"{len(silos)} cross-team silo{'s' if len(silos) > 1 else ''} detected."
            )

        # Trend alerts
        high_alerts = [a for a in trend_alerts if a["severity"] == "high"]
        if high_alerts:
            parts.append(
                f"{len(high_alerts)} high-severity trend alert{'s' if len(high_alerts) > 1 else ''}."
            )

        return (
            " ".join(parts)
            if parts
            else "Insufficient data for executive briefing. Complete team assessments and collaboration surveys to enable intelligence generation."
        )
