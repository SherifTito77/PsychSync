# app/services/organizational_pulse_service.py
"""
Organizational Pulse Engine

The predictive intelligence layer that sits above all PsychSync analytical
engines and continuously answers 7 key questions:

  1. Which teams are becoming isolated?
  2. Which managers are creating burnout?
  3. Which departments are collaborating effectively?
  4. Where is organizational friction increasing?
  5. Which teams are at risk of losing key talent?
  6. Which organizational changes are likely to reduce performance?
  7. What interventions should leaders take before problems become visible?

Architecture:
  BI Service (7 scores) + ONA Service (network) + HRIS Analytics
       |                        |                      |
       └────────────────────────┴──────────────────────┘
                                |
                    Organizational Pulse Engine
                    ├── Early Warning Detector
                    ├── Talent Flight Risk Model
                    └── Proactive Intervention Engine
"""

import logging
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.network_analysis import NetworkSnapshot
from app.db.models.organizational_pulse import PulseSnapshot
from app.db.models.team import Team, TeamMember
from app.db.models.user import User
from app.services.behavioral_intelligence_service import BehavioralIntelligenceService
from app.services.organizational_network_service import OrganizationalNetworkService

logger = logging.getLogger(__name__)

_bi_service = BehavioralIntelligenceService()
_ona_service = OrganizationalNetworkService()


class OrganizationalPulseService:
    """
    Predictive intelligence engine that fuses all PsychSync analytical
    signals into proactive early warnings and actionable interventions.

    This is what makes PsychSync an Organizational Behavioral Intelligence
    Platform rather than just another HR dashboard.
    """

    # ── Main Entry Point ─────────────────────────────────────────────

    async def generate_pulse(
        self,
        db: AsyncSession,
        organization_id: str,
        lookback_days: int = 45,
        enrichment: Optional[Dict[str, Any]] = None,
        hris_signals: Optional[Dict[str, Any]] = None,
        feedback_signals: Optional[Dict[str, Any]] = None,
        culture_signals: Optional[Dict[str, Any]] = None,
        recognition_signals: Optional[Dict[str, Any]] = None,
        okr_signals: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate the full organizational pulse — answers all 7 key questions.

        When enrichment is provided (from DataSourceAggregator), BI scores
        incorporate work system and calendar signals. HRIS signals feed
        directly into flight risk and intervention calculations.

        When feedback_signals/culture_signals/recognition_signals are provided,
        previously unwired assets enrich BI scores and directly inform
        friction (Q4) and change impact (Q6) detection.
        """
        start_ms = time.time()

        # Gather raw signals from existing engines
        bi_dashboard = await _bi_service.get_organization_dashboard(
            db,
            organization_id,
            lookback_days,
            enrichment=enrichment,
            culture_signals=culture_signals,
            feedback_signals=feedback_signals,
            recognition_signals=recognition_signals,
        )
        ona_analysis = await _ona_service.analyze_organization(
            db, organization_id, lookback_days
        )
        temporal_snapshots = await _ona_service.get_temporal_evolution(
            db, organization_id, days=lookback_days
        )

        teams = bi_dashboard.get("teams", [])
        org_scores = bi_dashboard.get("organization_scores", {})

        # Answer each of the 7 questions
        q1_isolated = self._detect_team_isolation(
            teams, ona_analysis, temporal_snapshots
        )
        q2_manager_burnout = self._detect_manager_burnout_attribution(teams)
        q3_collaboration = self._rank_collaboration_effectiveness(teams, ona_analysis)
        q4_friction = self._detect_friction_trends(
            teams, temporal_snapshots, feedback_signals=feedback_signals
        )
        q5_flight_risk = self._calculate_flight_risk(
            teams, ona_analysis, hris_signals, okr_signals=okr_signals
        )
        q6_change_impact = self._predict_change_impact(
            teams, org_scores, ona_analysis, feedback_signals=feedback_signals
        )
        q7_interventions = self._generate_proactive_interventions(
            q1_isolated,
            q2_manager_burnout,
            q3_collaboration,
            q4_friction,
            q5_flight_risk,
            q6_change_impact,
        )

        # Compute overall pulse
        early_warnings = self._compile_early_warnings(
            q1_isolated, q2_manager_burnout, q4_friction, q5_flight_risk
        )
        overall_pulse = self._compute_overall_pulse(org_scores, early_warnings)
        overall_trend = self._determine_trend(temporal_snapshots, org_scores)

        teams_at_risk = sum(
            1 for t in q5_flight_risk if t.get("risk_level") in ("high", "critical")
        )

        # Generate executive narrative
        narrative = self._generate_pulse_narrative(
            overall_pulse,
            overall_trend,
            len(teams),
            teams_at_risk,
            early_warnings,
            q5_flight_risk,
            q7_interventions,
        )

        computation_time = int((time.time() - start_ms) * 1000)

        pulse = {
            "organization_id": organization_id,
            "computed_at": datetime.utcnow().isoformat(),
            "narrative": narrative,
            "overall_pulse_score": overall_pulse,
            "overall_trend": overall_trend,
            "total_teams_analyzed": len(teams),
            "teams_at_risk": teams_at_risk,
            "active_alerts": len(early_warnings),
            "interventions_recommended": len(q7_interventions),
            # The 7 key questions
            "questions": {
                "isolated_teams": {
                    "question": "Which teams are becoming isolated?",
                    "answer": q1_isolated,
                    "count": len(q1_isolated),
                },
                "manager_burnout": {
                    "question": "Which managers are creating burnout?",
                    "answer": q2_manager_burnout,
                    "count": len(q2_manager_burnout),
                },
                "collaboration_effectiveness": {
                    "question": "Which departments are collaborating effectively?",
                    "answer": q3_collaboration,
                    "count": len(q3_collaboration),
                },
                "friction_trends": {
                    "question": "Where is organizational friction increasing?",
                    "answer": q4_friction,
                    "count": len(q4_friction),
                },
                "flight_risk": {
                    "question": "Which teams are at risk of losing key talent?",
                    "answer": q5_flight_risk,
                    "count": len(q5_flight_risk),
                },
                "change_impact": {
                    "question": "Which organizational changes are likely to reduce performance?",
                    "answer": q6_change_impact,
                    "count": len(q6_change_impact),
                },
                "interventions": {
                    "question": "What interventions should leaders take before problems become visible?",
                    "answer": q7_interventions,
                    "count": len(q7_interventions),
                },
            },
            "early_warnings": early_warnings,
            "computation_time_ms": computation_time,
            "data_sources": {
                "behavioral_intelligence": bool(teams),
                "network_analysis": bool(ona_analysis.get("nodes")),
                "temporal_snapshots": bool(temporal_snapshots),
                "anonymous_feedback": bool(feedback_signals),
                "culture_metrics": bool(culture_signals),
                "peer_recognition": bool(recognition_signals),
                "okr_signals": bool(okr_signals),
            },
        }

        # Add OKR health context if available
        if okr_signals:
            pulse["okr_context"] = {
                "active_objectives": okr_signals.get("active_objectives", 0),
                "critical_health_flags": okr_signals.get("critical_health", 0),
                "capacity_pressure": okr_signals.get("capacity_pressure", 0),
                "achievement_rate": okr_signals.get("achievement_rate", 0),
            }

        # Persist snapshot
        await self._persist_snapshot(db, organization_id, pulse)

        return pulse

    # ── Q1: Team Isolation Detection ─────────────────────────────────

    def _detect_team_isolation(
        self,
        teams: List[Dict],
        ona: Dict[str, Any],
        temporal: List[Dict],
    ) -> List[Dict[str, Any]]:
        """
        Detect teams becoming isolated by combining ONA cross-team
        collaboration weakness with temporal trend degradation.
        """
        isolated = []

        cross_team = ona.get("cross_team_collaboration", [])
        # Build a map of team collaboration strength
        team_collab_strength: Dict[str, float] = {}
        for edge in cross_team:
            for team_key in ("team_a_name", "team_b_name"):
                name = edge.get(team_key, "")
                strength = edge.get("strength", 0)
                team_collab_strength[name] = (
                    team_collab_strength.get(name, 0) + strength
                )

        # Check temporal density decline
        density_declining = False
        if len(temporal) >= 2:
            recent_density = temporal[-1].get("density", 0)
            older_density = temporal[0].get("density", 0)
            if older_density > 0:
                density_change = (recent_density - older_density) / older_density
                density_declining = density_change < -0.10

        for team_data in teams:
            team_name = team_data.get("team_name", "Unknown")
            collab_score = team_data.get("scores", {}).get("collaboration", {})
            collab_value = collab_score.get("score", 50)

            # Low collaboration + weak cross-team connections
            cross_strength = team_collab_strength.get(team_name, 0)
            is_isolating = collab_value < 40 or cross_strength <= 2

            if is_isolating:
                severity = (
                    "critical"
                    if collab_value < 25
                    else "high" if collab_value < 35 else "moderate"
                )
                isolated.append(
                    {
                        "team_name": team_name,
                        "team_id": team_data.get("team_id"),
                        "collaboration_score": collab_value,
                        "cross_team_strength": cross_strength,
                        "density_declining": density_declining,
                        "severity": severity,
                        "signal": (
                            f"{team_name} has a collaboration score of {collab_value}/100 "
                            f"with only {cross_strength} cross-team connections. "
                            f"{'Network density is also declining.' if density_declining else ''}"
                        ).strip(),
                    }
                )

        return sorted(isolated, key=lambda x: x["collaboration_score"])

    # ── Q2: Manager Burnout Attribution ──────────────────────────────

    def _detect_manager_burnout_attribution(
        self, teams: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Attribute team burnout to manager behavior by correlating
        manager health scores with team burnout risk.

        Low manager health + high team burnout = manager-attributed burnout.
        """
        signals = []

        for team_data in teams:
            scores = team_data.get("scores", {})
            manager_health = scores.get("manager_health", {}).get("score", 50)
            burnout_risk = scores.get("burnout_risk", {}).get("score", 50)
            team_name = team_data.get("team_name", "Unknown")

            # Manager health below 40 AND team burnout above 60 = attribution
            if manager_health < 40 and burnout_risk > 60:
                severity = (
                    "critical" if manager_health < 25 and burnout_risk > 75 else "high"
                )
                signals.append(
                    {
                        "team_name": team_name,
                        "team_id": team_data.get("team_id"),
                        "manager_health_score": manager_health,
                        "team_burnout_risk": burnout_risk,
                        "severity": severity,
                        "signal": (
                            f"{team_name}'s manager health is {manager_health}/100 while "
                            f"team burnout risk is {burnout_risk}/100. "
                            f"This correlation suggests management practices are contributing to burnout."
                        ),
                        "contributing_factors": scores.get("manager_health", {}).get(
                            "factors", []
                        ),
                    }
                )
            elif manager_health < 50 and burnout_risk > 50:
                signals.append(
                    {
                        "team_name": team_name,
                        "team_id": team_data.get("team_id"),
                        "manager_health_score": manager_health,
                        "team_burnout_risk": burnout_risk,
                        "severity": "moderate",
                        "signal": (
                            f"{team_name} shows early signs: manager health at {manager_health}/100 "
                            f"with rising burnout risk ({burnout_risk}/100)."
                        ),
                        "contributing_factors": scores.get("manager_health", {}).get(
                            "factors", []
                        ),
                    }
                )

        return sorted(signals, key=lambda x: x["manager_health_score"])

    # ── Q3: Collaboration Effectiveness ──────────────────────────────

    def _rank_collaboration_effectiveness(
        self, teams: List[Dict], ona: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Rank departments/teams by collaboration effectiveness,
        combining BI collaboration score with ONA cross-team density.
        """
        rankings = []
        cross_team = ona.get("cross_team_collaboration", [])

        # Build cross-team connection counts per team
        team_connections: Dict[str, int] = {}
        for edge in cross_team:
            for key in ("team_a_name", "team_b_name"):
                name = edge.get(key, "")
                team_connections[name] = team_connections.get(name, 0) + 1

        for team_data in teams:
            team_name = team_data.get("team_name", "Unknown")
            collab_score = (
                team_data.get("scores", {}).get("collaboration", {}).get("score", 50)
            )
            connections = team_connections.get(team_name, 0)

            # Composite: 70% BI collaboration + 30% cross-team connectivity
            connectivity_score = min(
                100, connections * 15
            )  # Scale: 7+ connections = 100
            composite = collab_score * 0.70 + connectivity_score * 0.30

            if composite >= 70:
                status = "strong"
            elif composite >= 50:
                status = "moderate"
            else:
                status = "weak"

            rankings.append(
                {
                    "team_name": team_name,
                    "team_id": team_data.get("team_id"),
                    "collaboration_score": collab_score,
                    "cross_team_connections": connections,
                    "composite_score": round(composite, 1),
                    "status": status,
                }
            )

        return sorted(rankings, key=lambda x: x["composite_score"], reverse=True)

    # ── Q4: Friction Trend Detection ─────────────────────────────────

    def _detect_friction_trends(
        self,
        teams: List[Dict],
        temporal: List[Dict],
        feedback_signals: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect where organizational friction is increasing by comparing
        current friction index with historical trajectory.

        When feedback_signals are provided, anonymous feedback patterns
        (toxic behavior, team dynamics, leadership concerns) amplify
        friction detection for earlier warning.
        """
        # Detect org-wide network fragmentation trend
        fragmentation_increasing = False
        if len(temporal) >= 2:
            recent_communities = temporal[-1].get("num_communities", 0)
            older_communities = temporal[0].get("num_communities", 0)
            fragmentation_increasing = recent_communities > older_communities + 1

        # Anonymous feedback amplifier: high concern ratio lowers thresholds
        feedback_amplifier = 0
        if feedback_signals and feedback_signals.get("concern_ratio", 0) > 0.3:
            feedback_amplifier = 10  # Lower detection threshold

        friction_signals = []
        for team_data in teams:
            team_name = team_data.get("team_name", "Unknown")
            friction = team_data.get("scores", {}).get("friction_index", {})
            friction_score = friction.get("score", 50)
            trend = friction.get("trend", "stable")

            detection_threshold = 50 - feedback_amplifier
            if friction_score > detection_threshold or trend == "increasing":
                severity = (
                    "critical"
                    if friction_score > 75
                    else "high" if friction_score > 60 else "moderate"
                )
                signal_parts = [
                    f"{team_name} friction index is {friction_score}/100 "
                    f"(trend: {trend}).",
                ]
                if fragmentation_increasing:
                    signal_parts.append(
                        "Organizational fragmentation is also increasing."
                    )
                if feedback_amplifier > 0:
                    signal_parts.append(
                        f"Anonymous feedback shows elevated concern ratio "
                        f"({feedback_signals['concern_ratio']:.0%}) — "
                        f"{feedback_signals.get('friction_reports', 0)} friction-related reports."
                    )

                friction_signals.append(
                    {
                        "team_name": team_name,
                        "team_id": team_data.get("team_id"),
                        "friction_score": friction_score,
                        "trend": trend,
                        "fragmentation_increasing": fragmentation_increasing,
                        "feedback_amplified": feedback_amplifier > 0,
                        "severity": severity,
                        "signal": " ".join(signal_parts),
                        "factors": friction.get("factors", []),
                    }
                )

        return sorted(friction_signals, key=lambda x: x["friction_score"], reverse=True)

    # ── Q5: Talent Flight Risk ───────────────────────────────────────

    def _calculate_flight_risk(
        self,
        teams: List[Dict],
        ona: Dict[str, Any],
        hris_signals: Optional[Dict[str, Any]] = None,
        okr_signals: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculate talent flight risk per team by fusing:
          - Burnout risk (from BI)
          - Network position (isolated high-performers are flight risks)
          - Engagement trajectory (declining = risk)
          - Manager health (poor management drives attrition)
          - HRIS signals: low tenure, high leave utilization (when available)
          - OKR signals: high capacity pressure amplifies burnout-driven flight risk
        """
        flight_risks = []
        nodes = ona.get("nodes", [])

        # HRIS amplifiers: org-wide signals that raise baseline risk
        hris_tenure_risk = 0
        hris_leave_risk = 0
        if hris_signals and hris_signals.get("total_employees", 0) > 0:
            avg_tenure = hris_signals.get("avg_tenure_days", 999)
            if avg_tenure < 180:
                hris_tenure_risk = 15  # New workforce, high churn baseline
            elif avg_tenure < 365:
                hris_tenure_risk = 8
            leave_pct = hris_signals.get("avg_leave_utilization_pct", 0)
            if leave_pct > 80:
                hris_leave_risk = 10  # Leave exhaustion signals burnout

        # Map node roles by team for network position analysis
        team_isolated_count: Dict[str, int] = {}
        team_influencer_count: Dict[str, int] = {}
        for node in nodes:
            team_name = node.get("team_name", "")
            role = node.get("role", "Regular")
            if role == "Isolated":
                team_isolated_count[team_name] = (
                    team_isolated_count.get(team_name, 0) + 1
                )
            elif role in ("Hidden Influencer", "Knowledge Bridge"):
                team_influencer_count[team_name] = (
                    team_influencer_count.get(team_name, 0) + 1
                )

        for team_data in teams:
            team_name = team_data.get("team_name", "Unknown")
            scores = team_data.get("scores", {})

            burnout = scores.get("burnout_risk", {}).get("score", 50)
            manager_health = scores.get("manager_health", {}).get("score", 50)
            engagement_trend = scores.get("team_health", {}).get("trend", "stable")
            psych_safety = scores.get("psychological_safety", {}).get("score", 50)

            isolated_members = team_isolated_count.get(team_name, 0)
            key_people = team_influencer_count.get(team_name, 0)

            flight_score = _compute_flight_risk_score(
                burnout_risk=burnout,
                manager_health=manager_health,
                engagement_trend=engagement_trend,
                psych_safety=psych_safety,
                isolated_members=isolated_members,
                key_people_count=key_people,
            )
            # HRIS amplifiers: tenure churn + leave exhaustion
            flight_score = min(100, flight_score + hris_tenure_risk + hris_leave_risk)

            # OKR capacity pressure: overloaded teams with high burnout flee faster
            if okr_signals and okr_signals.get("capacity_pressure", 0) > 40:
                okr_amplifier = min(12, okr_signals["capacity_pressure"] * 0.15)
                flight_score = min(100, flight_score + okr_amplifier)

            if flight_score >= 30:
                risk_level = (
                    "critical"
                    if flight_score >= 75
                    else "high" if flight_score >= 55 else "moderate"
                )
                flight_risks.append(
                    {
                        "team_name": team_name,
                        "team_id": team_data.get("team_id"),
                        "flight_risk_score": round(flight_score, 1),
                        "risk_level": risk_level,
                        "burnout_risk": burnout,
                        "manager_health": manager_health,
                        "psych_safety": psych_safety,
                        "isolated_members": isolated_members,
                        "key_people_at_risk": key_people if burnout > 60 else 0,
                        "signal": (
                            f"{team_name} flight risk: {round(flight_score)}/100. "
                            f"{'High burnout (' + str(burnout) + '). ' if burnout > 60 else ''}"
                            f"{'Poor management (' + str(manager_health) + '). ' if manager_health < 40 else ''}"
                            f"{str(key_people) + ' key people at risk. ' if key_people > 0 and burnout > 60 else ''}"
                        ).strip(),
                    }
                )

        return sorted(flight_risks, key=lambda x: x["flight_risk_score"], reverse=True)

    # ── Q6: Change Impact Prediction ─────────────────────────────────

    def _predict_change_impact(
        self,
        teams: List[Dict],
        org_scores: Dict[str, Any],
        ona: Dict[str, Any],
        feedback_signals: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Predict which organizational changes would reduce performance
        based on current change readiness, network dependencies, and
        psychological safety levels.

        When feedback_signals are provided, workplace_environment reports
        (stress, burnout, culture) increase vulnerability scores.
        """
        predictions = []

        # Anonymous feedback amplifier for change vulnerability
        feedback_change_amplifier = 0
        if feedback_signals and feedback_signals.get("change_reports", 0) > 0:
            # Each workplace environment report adds vulnerability
            feedback_change_amplifier = min(10, feedback_signals["change_reports"] * 2)

        # Identify teams not ready for change
        for team_data in teams:
            team_name = team_data.get("team_name", "Unknown")
            scores = team_data.get("scores", {})
            change_readiness = scores.get("change_readiness", {}).get("score", 50)
            psych_safety = scores.get("psychological_safety", {}).get("score", 50)
            friction = scores.get("friction_index", {}).get("score", 50)

            # Teams with low change readiness + low psych safety are vulnerable
            vulnerability = (
                (100 - change_readiness) * 0.5
                + (100 - psych_safety) * 0.3
                + friction * 0.2
                + feedback_change_amplifier
            )

            if vulnerability > 50:
                predictions.append(
                    {
                        "team_name": team_name,
                        "team_id": team_data.get("team_id"),
                        "vulnerability_score": round(vulnerability, 1),
                        "change_readiness": change_readiness,
                        "psych_safety": psych_safety,
                        "friction": friction,
                        "risk_scenarios": self._generate_risk_scenarios(
                            team_name, change_readiness, psych_safety, friction
                        ),
                    }
                )

        # Detect manager dependency risks from ONA — merge into existing team entries
        existing_teams = {p["team_name"]: p for p in predictions}
        dependencies = ona.get("manager_dependencies", [])
        for dep in dependencies:
            if dep.get("risk_level") in ("high", "moderate"):
                dep_scenario = {
                    "scenario": "Key person departure",
                    "impact": (
                        f"Removing {dep.get('member_name', 'this person')} "
                        f"(dependency ratio: {dep.get('dependency_ratio', 0):.1f}x) "
                        f"would severely disrupt team operations."
                    ),
                    "confidence": "high" if dep["risk_level"] == "high" else "moderate",
                }
                team_name = dep.get("team_name", "Unknown")
                if team_name in existing_teams:
                    existing_teams[team_name]["risk_scenarios"].append(dep_scenario)
                    dep_vuln = 70 if dep["risk_level"] == "high" else 55
                    existing_teams[team_name]["vulnerability_score"] = max(
                        existing_teams[team_name]["vulnerability_score"], dep_vuln
                    )
                else:
                    predictions.append(
                        {
                            "team_name": team_name,
                            "vulnerability_score": (
                                70 if dep["risk_level"] == "high" else 55
                            ),
                            "change_readiness": None,
                            "risk_scenarios": [dep_scenario],
                        }
                    )

        return sorted(predictions, key=lambda x: x["vulnerability_score"], reverse=True)

    # ── Q7: Proactive Interventions ──────────────────────────────────

    def _generate_proactive_interventions(
        self,
        isolated: List[Dict],
        manager_burnout: List[Dict],
        collaboration: List[Dict],
        friction: List[Dict],
        flight_risk: List[Dict],
        change_impact: List[Dict],
    ) -> List[Dict[str, Any]]:
        """
        Generate prioritized intervention recommendations based on
        all detected signals — acting on leading indicators before
        problems become visible.
        """
        interventions = []

        # Isolation interventions
        for team in isolated:
            if team["severity"] in ("critical", "high"):
                interventions.append(
                    {
                        "priority": 1 if team["severity"] == "critical" else 2,
                        "category": "isolation",
                        "team_name": team["team_name"],
                        "team_id": team.get("team_id"),
                        "action": f"Initiate cross-team collaboration program for {team['team_name']}",
                        "details": (
                            "Schedule joint stand-ups or project pairing with adjacent teams. "
                            "Consider rotating 1-2 members into cross-functional initiatives."
                        ),
                        "expected_impact": "Increase cross-team connections within 30 days",
                        "urgency": (
                            "immediate"
                            if team["severity"] == "critical"
                            else "this_week"
                        ),
                    }
                )

        # Manager burnout interventions
        for signal in manager_burnout:
            if signal["severity"] in ("critical", "high"):
                interventions.append(
                    {
                        "priority": 1 if signal["severity"] == "critical" else 2,
                        "category": "manager_effectiveness",
                        "team_name": signal["team_name"],
                        "team_id": signal.get("team_id"),
                        "action": f"Manager coaching intervention for {signal['team_name']}",
                        "details": (
                            "Provide manager with 1:1 executive coaching focused on team wellbeing. "
                            "Review workload distribution and delegation patterns. "
                            "Consider skip-level meetings to understand team perspective."
                        ),
                        "expected_impact": "Reduce team burnout risk within 45 days",
                        "urgency": (
                            "immediate"
                            if signal["severity"] == "critical"
                            else "this_week"
                        ),
                    }
                )

        # Flight risk interventions
        for team in flight_risk:
            if team["risk_level"] in ("critical", "high"):
                interventions.append(
                    {
                        "priority": 1 if team["risk_level"] == "critical" else 2,
                        "category": "retention",
                        "team_name": team["team_name"],
                        "team_id": team.get("team_id"),
                        "action": f"Retention risk mitigation for {team['team_name']}",
                        "details": (
                            f"{'Key influencers at risk — prioritize stay interviews. ' if team.get('key_people_at_risk', 0) > 0 else ''}"
                            "Conduct confidential engagement pulse survey. "
                            "Review compensation competitiveness and growth opportunities. "
                            "Address burnout drivers identified in behavioral intelligence."
                        ),
                        "expected_impact": "Reduce flight risk signals within 60 days",
                        "urgency": (
                            "immediate"
                            if team["risk_level"] == "critical"
                            else "this_week"
                        ),
                    }
                )

        # Friction interventions
        for signal in friction:
            if signal["severity"] in ("critical", "high"):
                interventions.append(
                    {
                        "priority": 2,
                        "category": "friction_reduction",
                        "team_name": signal["team_name"],
                        "team_id": signal.get("team_id"),
                        "action": f"Friction reduction program for {signal['team_name']}",
                        "details": (
                            "Facilitate team retrospective focused on process pain points. "
                            "Review meeting load and communication overhead. "
                            "Consider personality-based conflict resolution workshops."
                        ),
                        "expected_impact": "Reduce friction index by 15+ points within 30 days",
                        "urgency": "this_week",
                    }
                )

        # Change readiness interventions
        vulnerable = [c for c in change_impact if c.get("vulnerability_score", 0) > 65]
        if vulnerable:
            interventions.append(
                {
                    "priority": 3,
                    "category": "change_readiness",
                    "team_name": "Organization-wide",
                    "action": "Strengthen change readiness before major transitions",
                    "details": (
                        f"{len(vulnerable)} teams are vulnerable to organizational changes. "
                        "Build psychological safety through transparent communication. "
                        "Increase manager-team trust before announcing changes. "
                        "Consider phased rollouts starting with change-ready teams."
                    ),
                    "expected_impact": "Reduce change resistance and performance dips",
                    "urgency": "this_month",
                }
            )

        return sorted(interventions, key=lambda x: x["priority"])

    # ── Supporting Methods ───────────────────────────────────────────

    def _generate_risk_scenarios(
        self, team_name: str, readiness: float, safety: float, friction: float
    ) -> List[Dict[str, Any]]:
        """Generate specific risk scenarios for a vulnerable team."""
        scenarios = []

        if readiness < 35:
            scenarios.append(
                {
                    "scenario": "Restructuring or reorganization",
                    "impact": f"Team would likely resist and productivity could drop 20-40%",
                    "confidence": "high",
                }
            )

        if safety < 40:
            scenarios.append(
                {
                    "scenario": "New leadership introduction",
                    "impact": f"Low psychological safety ({safety}/100) means team won't voice concerns, leading to silent disengagement",
                    "confidence": "high",
                }
            )

        if friction > 65:
            scenarios.append(
                {
                    "scenario": "Process or tooling changes",
                    "impact": f"Existing friction ({friction}/100) would compound, risking team breakdown",
                    "confidence": "moderate",
                }
            )

        if not scenarios:
            scenarios.append(
                {
                    "scenario": "Major organizational change",
                    "impact": "Team shows moderate vulnerability — changes should be communicated with extra care",
                    "confidence": "moderate",
                }
            )

        return scenarios

    def _generate_pulse_narrative(
        self,
        pulse_score: float,
        trend: str,
        total_teams: int,
        teams_at_risk: int,
        warnings: List[Dict],
        flight_risks: List[Dict],
        interventions: List[Dict],
    ) -> str:
        """
        Generate a concise executive narrative summarizing the organizational pulse.
        Rule-based — no LLM dependency, always available.
        """
        parts = []

        # Overall health assessment
        if pulse_score >= 75:
            parts.append(
                f"Organization is healthy at {round(pulse_score)}/100 pulse score."
            )
        elif pulse_score >= 55:
            parts.append(
                f"Organization is stable at {round(pulse_score)}/100 but has areas needing attention."
            )
        elif pulse_score >= 35:
            parts.append(
                f"Organization is at risk with a {round(pulse_score)}/100 pulse score. Action recommended."
            )
        else:
            parts.append(
                f"Organization is in critical state at {round(pulse_score)}/100. Immediate intervention required."
            )

        # Trend
        if trend == "critical":
            parts.append("Multiple indicators are declining simultaneously.")
        elif trend == "declining":
            parts.append("Key metrics are trending downward.")
        elif trend == "improving":
            parts.append("Metrics are trending in a positive direction.")

        # Teams at risk
        if teams_at_risk > 0:
            parts.append(
                f"{teams_at_risk} of {total_teams} team{'s' if teams_at_risk > 1 else ''} "
                f"{'are' if teams_at_risk > 1 else 'is'} at elevated flight risk."
            )

        # Critical warnings
        critical_warnings = [w for w in warnings if w.get("severity") == "critical"]
        if critical_warnings:
            types = set(w["type"] for w in critical_warnings)
            type_labels = {
                "isolation": "team isolation",
                "manager_burnout": "manager-attributed burnout",
                "friction": "organizational friction",
                "flight_risk": "talent flight risk",
            }
            labels = [type_labels.get(t, t) for t in types]
            parts.append(f"Critical signals detected: {', '.join(labels)}.")

        # Key flight risks
        critical_flight = [f for f in flight_risks if f.get("risk_level") == "critical"]
        if critical_flight:
            names = ", ".join(f["team_name"] for f in critical_flight[:3])
            parts.append(f"Highest retention risk: {names}.")

        # Intervention count
        immediate = [i for i in interventions if i.get("urgency") == "immediate"]
        if immediate:
            parts.append(
                f"{len(immediate)} intervention{'s' if len(immediate) > 1 else ''} require{'s' if len(immediate) == 1 else ''} immediate action."
            )

        return (
            " ".join(parts)
            if parts
            else "Insufficient data to generate pulse narrative."
        )

    def _compile_early_warnings(
        self,
        isolated: List[Dict],
        manager_burnout: List[Dict],
        friction: List[Dict],
        flight_risk: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Compile all signals into a unified early warning list."""
        warnings = []

        for team in isolated:
            if team["severity"] in ("critical", "high"):
                warnings.append(
                    {
                        "type": "isolation",
                        "severity": team["severity"],
                        "team_name": team["team_name"],
                        "message": team["signal"],
                    }
                )

        for signal in manager_burnout:
            if signal["severity"] in ("critical", "high"):
                warnings.append(
                    {
                        "type": "manager_burnout",
                        "severity": signal["severity"],
                        "team_name": signal["team_name"],
                        "message": signal["signal"],
                    }
                )

        for signal in friction:
            if signal["severity"] in ("critical", "high"):
                warnings.append(
                    {
                        "type": "friction",
                        "severity": signal["severity"],
                        "team_name": signal["team_name"],
                        "message": signal["signal"],
                    }
                )

        for team in flight_risk:
            if team["risk_level"] in ("critical", "high"):
                warnings.append(
                    {
                        "type": "flight_risk",
                        "severity": team["risk_level"],
                        "team_name": team["team_name"],
                        "message": team["signal"],
                    }
                )

        # Sort: critical first, then high
        severity_order = {"critical": 0, "high": 1}
        return sorted(warnings, key=lambda x: severity_order.get(x["severity"], 2))

    def _compute_overall_pulse(
        self, org_scores: Dict[str, Any], warnings: List[Dict]
    ) -> float:
        """
        Compute overall organizational pulse score (0-100).
        Weighted average of org scores penalized by warning severity.
        """
        # Start from org BI scores average
        score_values = []
        for key in (
            "team_health",
            "collaboration",
            "psychological_safety",
            "change_readiness",
        ):
            val = org_scores.get(key, {}).get("score")
            if val is not None:
                score_values.append(val)

        # Inverse scores (lower is better) — flip for pulse calculation
        for key in ("friction_index", "burnout_risk"):
            val = org_scores.get(key, {}).get("score")
            if val is not None:
                score_values.append(100 - val)

        if not score_values:
            return 50.0

        base_pulse = sum(score_values) / len(score_values)

        # Penalty for warnings
        critical_count = sum(1 for w in warnings if w["severity"] == "critical")
        high_count = sum(1 for w in warnings if w["severity"] == "high")
        penalty = critical_count * 8 + high_count * 3

        return max(0, min(100, round(base_pulse - penalty, 1)))

    def _determine_trend(self, temporal: List[Dict], org_scores: Dict[str, Any]) -> str:
        """Determine overall organizational trend."""
        if not temporal or len(temporal) < 2:
            return "stable"

        # Compare network density trend
        recent = temporal[-1]
        older = temporal[0]
        density_change = (recent.get("density", 0) or 0) - (
            older.get("density", 0) or 0
        )
        isolates_change = (recent.get("num_isolates", 0) or 0) - (
            older.get("num_isolates", 0) or 0
        )

        # Check BI trend signals
        burnout_trend = org_scores.get("burnout_risk", {}).get("trend", "stable")
        health_trend = org_scores.get("team_health", {}).get("trend", "stable")

        negative_signals = 0
        positive_signals = 0

        if density_change < -0.05:
            negative_signals += 1
        elif density_change > 0.05:
            positive_signals += 1

        if isolates_change > 2:
            negative_signals += 1
        elif isolates_change < -1:
            positive_signals += 1

        if burnout_trend == "increasing":
            negative_signals += 1
        if health_trend == "decreasing":
            negative_signals += 1
        elif health_trend == "increasing":
            positive_signals += 1

        if negative_signals >= 3:
            return "critical"
        elif negative_signals >= 2:
            return "declining"
        elif positive_signals >= 2:
            return "improving"
        return "stable"

    # ── History & Trending ─────────────────────────────────────────

    async def get_pulse_history(
        self,
        db: AsyncSession,
        organization_id: str,
        days: int = 90,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical pulse snapshots for temporal trending.
        Returns summary-level data (scores, counts, trend) per snapshot date.
        """
        since = date.today() - timedelta(days=days)
        result = await db.execute(
            select(PulseSnapshot)
            .where(
                and_(
                    PulseSnapshot.organization_id == organization_id,
                    PulseSnapshot.snapshot_date >= since,
                )
            )
            .order_by(PulseSnapshot.snapshot_date.asc())
        )
        snapshots = result.scalars().all()

        history = []
        for snap in snapshots:
            history.append(
                {
                    "date": snap.snapshot_date.isoformat(),
                    "pulse_score": snap.overall_pulse_score,
                    "trend": snap.overall_trend,
                    "teams_analyzed": snap.total_teams_analyzed,
                    "teams_at_risk": snap.teams_at_risk,
                    "active_alerts": snap.active_alerts,
                    "interventions": snap.interventions_recommended,
                }
            )

        return history

    # ── Persistence ──────────────────────────────────────────────────

    async def _persist_snapshot(
        self,
        db: AsyncSession,
        organization_id: str,
        pulse: Dict[str, Any],
    ) -> None:
        """Persist pulse snapshot for temporal tracking."""
        try:
            today = date.today()
            questions = pulse.get("questions", {})

            stmt = (
                pg_insert(PulseSnapshot)
                .values(
                    organization_id=organization_id,
                    snapshot_date=today,
                    overall_pulse_score=pulse["overall_pulse_score"],
                    overall_trend=pulse["overall_trend"],
                    total_teams_analyzed=pulse["total_teams_analyzed"],
                    teams_at_risk=pulse["teams_at_risk"],
                    active_alerts=pulse["active_alerts"],
                    interventions_recommended=pulse["interventions_recommended"],
                    isolated_teams=questions.get("isolated_teams", {}).get("answer"),
                    manager_burnout_signals=questions.get("manager_burnout", {}).get(
                        "answer"
                    ),
                    collaboration_effectiveness=questions.get(
                        "collaboration_effectiveness", {}
                    ).get("answer"),
                    friction_trends=questions.get("friction_trends", {}).get("answer"),
                    flight_risk_teams=questions.get("flight_risk", {}).get("answer"),
                    change_impact_predictions=questions.get("change_impact", {}).get(
                        "answer"
                    ),
                    proactive_interventions=questions.get("interventions", {}).get(
                        "answer"
                    ),
                    early_warnings=pulse.get("early_warnings"),
                    predictions=None,
                    computation_time_ms=pulse.get("computation_time_ms"),
                    data_sources_used=pulse.get("data_sources"),
                )
                .on_conflict_do_update(
                    constraint="uq_pulse_snapshot_date",
                    set_={
                        "overall_pulse_score": pulse["overall_pulse_score"],
                        "overall_trend": pulse["overall_trend"],
                        "total_teams_analyzed": pulse["total_teams_analyzed"],
                        "teams_at_risk": pulse["teams_at_risk"],
                        "active_alerts": pulse["active_alerts"],
                        "interventions_recommended": pulse["interventions_recommended"],
                        "isolated_teams": questions.get("isolated_teams", {}).get(
                            "answer"
                        ),
                        "manager_burnout_signals": questions.get(
                            "manager_burnout", {}
                        ).get("answer"),
                        "collaboration_effectiveness": questions.get(
                            "collaboration_effectiveness", {}
                        ).get("answer"),
                        "friction_trends": questions.get("friction_trends", {}).get(
                            "answer"
                        ),
                        "flight_risk_teams": questions.get("flight_risk", {}).get(
                            "answer"
                        ),
                        "change_impact_predictions": questions.get(
                            "change_impact", {}
                        ).get("answer"),
                        "proactive_interventions": questions.get(
                            "interventions", {}
                        ).get("answer"),
                        "early_warnings": pulse.get("early_warnings"),
                        "computation_time_ms": pulse.get("computation_time_ms"),
                        "data_sources_used": pulse.get("data_sources"),
                    },
                )
            )
            await db.execute(stmt)
            await db.commit()
            logger.info(
                "Pulse snapshot persisted for org=%s date=%s", organization_id, today
            )
        except Exception as exc:
            logger.error("Failed to persist pulse snapshot: %s", exc)
            await db.rollback()


# ── Flight Risk Scoring (module-level for human contribution) ────────


def _compute_flight_risk_score(
    burnout_risk: float,
    manager_health: float,
    engagement_trend: str,
    psych_safety: float,
    isolated_members: int,
    key_people_count: int,
) -> float:
    """
    Compute a team's talent flight risk score (0-100).

    Weights reflect turnover research: poor management is the #1 driver,
    burnout is #2, and psych safety acts as a multiplier (cluster exits).
    Network isolation and key-person counts amplify the base score.
    """
    # Base score: manager quality (35%) + burnout (25%) + psych safety (20%) + trend (20%)
    manager_risk = (100 - manager_health) * 0.35
    burnout_component = burnout_risk * 0.25
    safety_component = (100 - psych_safety) * 0.20
    trend_score = {"decreasing": 80, "stable": 30, "increasing": 5}.get(
        engagement_trend, 30
    )
    trend_component = trend_score * 0.20

    base = manager_risk + burnout_component + safety_component + trend_component

    # Amplifiers: isolated members add +4 each, key people at burnout risk add +6 each
    amplifier = min(
        20, isolated_members * 4 + (key_people_count * 6 if burnout_risk > 60 else 0)
    )

    # Psych safety below 30 acts as a cluster-exit multiplier (1.0x - 1.3x)
    multiplier = 1.0 + max(0, (30 - psych_safety) / 100)

    return min(100, base * multiplier + amplifier)
