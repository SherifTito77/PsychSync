"""
Manager Intelligence Service

Dedicated view for managers — combines Behavioral Intelligence scores,
ONA network insights, burnout risk signals, and AI coaching into a
single actionable dashboard for the manager's team.

Inspired by: Microsoft Viva (manager dashboards), Lattice (manager
coaching), Culture Amp (manager action plans).

Key difference from the org-wide BI dashboard: this is personal to
the manager.  It shows THEIR team, THEIR action items, and coaching
prompts specific to their leadership context.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.team import Team, TeamMember
from app.db.models.user import User

logger = logging.getLogger(__name__)


class ManagerIntelligenceService:
    """
    Produces a manager-specific intelligence briefing for a single team.
    """

    async def get_manager_briefing(
        self,
        db: AsyncSession,
        team_id: str,
        manager_user_id: str,
    ) -> Dict[str, Any]:
        """Full manager intelligence briefing for one team."""

        # Verify team exists
        team = await self._get_team(db, team_id)
        if not team:
            return {"error": "Team not found", "team_id": team_id}

        members = await self._get_members_with_names(db, team_id)
        if not members:
            return {
                "team_id": team_id,
                "team_name": team.name,
                "member_count": 0,
                "message": "No team members found.",
            }

        # Gather all intelligence layers
        bi_scores = await self._get_bi_scores(db, team_id)
        member_risks = await self._get_member_risk_profiles(db, team_id, members)
        network_insights = await self._get_network_insights(
            db, team_id, team.organization_id, members
        )
        action_items = self._generate_action_items(
            bi_scores, member_risks, network_insights
        )
        coaching_prompts = self._generate_coaching_prompts(bi_scores, network_insights)
        team_pulse = self._compute_team_pulse(bi_scores)
        effectiveness = self._compute_manager_effectiveness(
            bi_scores, member_risks, network_insights
        )

        return {
            "team_id": team_id,
            "team_name": team.name,
            "organization_id": str(team.organization_id),
            "member_count": len(members),
            "generated_at": datetime.utcnow().isoformat(),
            "team_pulse": team_pulse,
            "manager_effectiveness": effectiveness,
            "bi_scores": bi_scores,
            "members": member_risks,
            "network_insights": network_insights,
            "action_items": action_items,
            "coaching_prompts": coaching_prompts,
        }

    async def get_manager_teams(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """List all teams a user manages (for team selector)."""
        # Get teams where user is a member with manager/lead role
        query = (
            select(Team, TeamMember)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .where(TeamMember.user_id == user_id)
        )
        result = await db.execute(query)
        rows = result.all()

        teams = []
        for team, membership in rows:
            # Count members
            count_q = (
                select(func.count())
                .select_from(TeamMember)
                .where(TeamMember.team_id == team.id)
            )
            count_result = await db.execute(count_q)
            member_count = count_result.scalar() or 0

            teams.append(
                {
                    "team_id": str(team.id),
                    "team_name": team.name,
                    "member_count": member_count,
                    "organization_id": str(team.organization_id),
                }
            )

        return teams

    # ------------------------------------------------------------------
    # Behavioral Intelligence Layer
    # ------------------------------------------------------------------

    async def _get_bi_scores(self, db: AsyncSession, team_id: str) -> Dict[str, Any]:
        """Fetch all 7 BI scores for this team."""
        try:
            from app.services.behavioral_intelligence_service import (
                BehavioralIntelligenceService,
            )

            bi = BehavioralIntelligenceService()
            th = await bi.calculate_team_health(db, team_id)
            co = await bi.calculate_collaboration_score(db, team_id)
            mh = await bi.calculate_manager_health(db, team_id)
            ps = await bi.calculate_psychological_safety(db, team_id)
            cr = await bi.calculate_change_readiness(db, team_id)
            fi = await bi.calculate_friction_index(db, team_id)
            br = await bi.calculate_burnout_risk(db, team_id)

            return {
                "team_health": th,
                "collaboration": co,
                "manager_health": mh,
                "psychological_safety": ps,
                "change_readiness": cr,
                "friction_index": fi,
                "burnout_risk": br,
            }
        except Exception as e:
            logger.warning("BI scores unavailable for team %s: %s", team_id, e)
            return {}

    # ------------------------------------------------------------------
    # Member Risk Profiles
    # ------------------------------------------------------------------

    async def _get_member_risk_profiles(
        self,
        db: AsyncSession,
        team_id: str,
        members: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Per-member risk signals: burnout, engagement, churn, network position."""
        profiles = []

        for member in members:
            uid = member["user_id"]
            profile: Dict[str, Any] = {
                "user_id": uid,
                "name": member["name"],
                "risk_level": "low",
                "signals": [],
            }

            # Burnout risk from wellness
            burnout = await self._get_member_burnout(db, uid)
            if burnout is not None:
                profile["burnout_risk"] = burnout
                if burnout > 7:
                    profile["signals"].append(
                        {
                            "type": "burnout",
                            "severity": "critical",
                            "message": f"Burnout risk score {burnout:.1f}/10 — needs immediate attention",
                        }
                    )
                    profile["risk_level"] = "critical"
                elif burnout > 5:
                    profile["signals"].append(
                        {
                            "type": "burnout",
                            "severity": "elevated",
                            "message": f"Burnout risk score {burnout:.1f}/10 — monitor closely",
                        }
                    )
                    if profile["risk_level"] == "low":
                        profile["risk_level"] = "elevated"

            # Engagement from wellness
            engagement = await self._get_member_engagement(db, uid)
            if engagement is not None:
                profile["engagement"] = engagement
                if engagement < 4:
                    profile["signals"].append(
                        {
                            "type": "disengagement",
                            "severity": "elevated",
                            "message": f"Engagement {engagement:.1f}/10 — consider 1:1 conversation",
                        }
                    )
                    if profile["risk_level"] == "low":
                        profile["risk_level"] = "elevated"

            # Churn risk
            churn = await self._get_member_churn(db, uid)
            if churn is not None:
                profile["churn_risk"] = churn
                if churn > 70:
                    profile["signals"].append(
                        {
                            "type": "churn",
                            "severity": "high",
                            "message": f"Churn risk {churn}/100 — retention intervention recommended",
                        }
                    )
                    profile["risk_level"] = "critical"

            # Network position
            network_role = await self._get_member_network_role(db, uid)
            if network_role:
                profile["network_role"] = network_role
                if network_role["role"] == "isolated":
                    profile["signals"].append(
                        {
                            "type": "isolation",
                            "severity": "moderate",
                            "message": "Low network connectivity — may need collaboration opportunities",
                        }
                    )
                    if profile["risk_level"] == "low":
                        profile["risk_level"] = "moderate"

            profiles.append(profile)

        # Sort: critical first, then elevated, then moderate
        risk_order = {"critical": 0, "elevated": 1, "moderate": 2, "low": 3}
        profiles.sort(key=lambda p: risk_order.get(p["risk_level"], 3))

        return profiles

    # ------------------------------------------------------------------
    # Network Insights
    # ------------------------------------------------------------------

    async def _get_network_insights(
        self,
        db: AsyncSession,
        team_id: str,
        org_id: str,
        members: List[Dict],
    ) -> Dict[str, Any]:
        """ONA-derived insights specific to this team."""
        try:
            from app.services.organizational_network_service import (
                OrganizationalNetworkService,
            )

            ona = OrganizationalNetworkService()
            network = await ona.analyze_network(db, str(org_id))

            if not network or "insights" not in network:
                return {"available": False}

            insights = network["insights"]
            member_ids = {m["user_id"] for m in members}

            # Find team members in network roles
            team_influencers = [
                n for n in insights.get("influencers", []) if n["user_id"] in member_ids
            ]
            team_isolated = [
                n for n in insights.get("isolated", []) if n["user_id"] in member_ids
            ]
            team_bridges = [
                n for n in insights.get("bridges", []) if n["user_id"] in member_ids
            ]

            # Manager dependency for this team
            manager_dep = insights.get("manager_dependency", {})

            # Cross-team connections
            cross_team = insights.get("cross_team_collaboration", {})
            team_connections = []
            for pair in cross_team.get("team_pairs", []):
                teams_in_pair = pair.get("teams", [])
                if team_id in [str(t) for t in teams_in_pair]:
                    team_connections.append(pair)

            return {
                "available": True,
                "influencers": team_influencers[:5],
                "isolated": team_isolated,
                "bridges": team_bridges[:5],
                "manager_dependency": manager_dep,
                "cross_team_connections": team_connections[:5],
                "network_density": network.get("network_stats", {}).get("density", 0),
            }

        except Exception as e:
            logger.warning("Network insights unavailable: %s", e)
            return {"available": False}

    # ------------------------------------------------------------------
    # Action Items
    # ------------------------------------------------------------------

    def _generate_action_items(
        self,
        bi_scores: Dict,
        member_risks: List[Dict],
        network: Dict,
    ) -> List[Dict[str, Any]]:
        """Generate prioritized, concrete action items for the manager."""
        actions: List[Dict[str, Any]] = []

        # Critical member risks
        critical_members = [m for m in member_risks if m["risk_level"] == "critical"]
        elevated_members = [m for m in member_risks if m["risk_level"] == "elevated"]

        if critical_members:
            names = ", ".join(m["name"] for m in critical_members[:3])
            actions.append(
                {
                    "priority": "urgent",
                    "category": "people",
                    "action": f"Schedule 1:1 check-ins with {names}",
                    "reason": "Critical risk signals detected (burnout/churn/disengagement)",
                    "timeframe": "This week",
                }
            )

        if elevated_members:
            actions.append(
                {
                    "priority": "high",
                    "category": "people",
                    "action": f"Monitor {len(elevated_members)} team member(s) with elevated risk",
                    "reason": "Early warning signals — intervene before escalation",
                    "timeframe": "Next 2 weeks",
                }
            )

        # BI-driven actions
        if bi_scores:
            burnout = bi_scores.get("burnout_risk", {})
            if burnout.get("score", 0) > 65:
                actions.append(
                    {
                        "priority": "urgent",
                        "category": "wellness",
                        "action": "Review workload distribution and meeting load",
                        "reason": f"Team burnout risk at {burnout['score']:.0f}/100",
                        "timeframe": "This week",
                    }
                )

            psych_safety = bi_scores.get("psychological_safety", {})
            if psych_safety.get("score", 100) < 45:
                actions.append(
                    {
                        "priority": "high",
                        "category": "culture",
                        "action": "Introduce anonymous feedback mechanisms and model vulnerability in meetings",
                        "reason": f"Psychological safety at {psych_safety['score']:.0f}/100",
                        "timeframe": "Next 2 weeks",
                    }
                )

            collab = bi_scores.get("collaboration", {})
            if collab.get("score", 100) < 50:
                actions.append(
                    {
                        "priority": "medium",
                        "category": "collaboration",
                        "action": "Create cross-functional pairing opportunities or joint projects",
                        "reason": f"Collaboration score at {collab['score']:.0f}/100",
                        "timeframe": "Next sprint",
                    }
                )

            friction = bi_scores.get("friction_index", {})
            if friction.get("score", 0) > 60:
                actions.append(
                    {
                        "priority": "high",
                        "category": "process",
                        "action": "Identify and remove coordination bottlenecks — review handoff processes",
                        "reason": f"Friction index at {friction['score']:.0f}/100 (lower is better)",
                        "timeframe": "Next 2 weeks",
                    }
                )

            change = bi_scores.get("change_readiness", {})
            if change.get("score", 100) < 40:
                actions.append(
                    {
                        "priority": "medium",
                        "category": "change",
                        "action": "Increase transparency about upcoming changes — hold town halls",
                        "reason": f"Change readiness at {change['score']:.0f}/100",
                        "timeframe": "Next month",
                    }
                )

        # Network-driven actions
        if network.get("available"):
            isolated = network.get("isolated", [])
            if isolated:
                names = ", ".join(n.get("name", "?") for n in isolated[:3])
                actions.append(
                    {
                        "priority": "medium",
                        "category": "network",
                        "action": f"Connect isolated team members ({names}) with collaboration partners",
                        "reason": "Low network connectivity correlates with disengagement risk",
                        "timeframe": "Next 2 weeks",
                    }
                )

        # Sort by priority
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        actions.sort(key=lambda a: priority_order.get(a["priority"], 3))

        return actions

    # ------------------------------------------------------------------
    # Coaching Prompts (for the manager themselves)
    # ------------------------------------------------------------------

    def _generate_coaching_prompts(
        self,
        bi_scores: Dict,
        network: Dict,
    ) -> List[Dict[str, Any]]:
        """Leadership coaching prompts based on team state."""
        prompts: List[Dict[str, Any]] = []

        if not bi_scores:
            return [
                {
                    "theme": "Getting Started",
                    "prompt": "Complete team assessments to unlock behavioral intelligence insights.",
                    "source": "system",
                }
            ]

        # Manager health reflection
        mh = bi_scores.get("manager_health", {})
        if mh.get("score", 100) < 50:
            prompts.append(
                {
                    "theme": "Leadership Impact",
                    "prompt": (
                        "Your team's manager health score suggests opportunities to strengthen "
                        "your leadership presence. Consider: Are you providing enough autonomy? "
                        "Do team members feel supported in their growth? "
                        "Try asking each person: 'What's one thing I could do differently to help you succeed?'"
                    ),
                    "source": "behavioral_intelligence",
                }
            )

        # Psychological safety coaching
        ps = bi_scores.get("psychological_safety", {})
        if ps.get("score", 100) < 55:
            prompts.append(
                {
                    "theme": "Building Psychological Safety",
                    "prompt": (
                        "Research (Edmondson, 1999) shows psychological safety is the #1 predictor "
                        "of team performance. Start your next meeting by sharing a recent mistake "
                        "you made and what you learned. This models vulnerability and signals "
                        "that speaking up is safe."
                    ),
                    "source": "behavioral_intelligence",
                }
            )

        # Burnout coaching
        br = bi_scores.get("burnout_risk", {})
        if br.get("score", 0) > 55:
            prompts.append(
                {
                    "theme": "Preventing Burnout",
                    "prompt": (
                        "Your team is showing elevated burnout signals. "
                        "Review: Are there meetings that could be async? "
                        "Is anyone consistently working after hours? "
                        "Consider implementing 'no-meeting' blocks and checking in on workload "
                        "balance during your next 1:1s."
                    ),
                    "source": "behavioral_intelligence",
                }
            )

        # Network-aware coaching
        if network.get("available"):
            dep = network.get("manager_dependency", {})
            if dep.get("avg_dependency_ratio", 0) > 0.6:
                prompts.append(
                    {
                        "theme": "Reducing Dependency",
                        "prompt": (
                            "Your team has high manager dependency — team members route too much "
                            "through you. Empower direct collaboration by designating peer leads "
                            "for specific domains, and gradually step back from being the default "
                            "decision point."
                        ),
                        "source": "network_analysis",
                    }
                )

            if network.get("isolated"):
                prompts.append(
                    {
                        "theme": "Inclusion & Connection",
                        "prompt": (
                            "Some team members have low network connectivity. "
                            "Pair them with well-connected colleagues on cross-functional tasks. "
                            "Isolation is an early signal of disengagement — a simple 'How can "
                            "I help you connect with the broader team?' can make a difference."
                        ),
                        "source": "network_analysis",
                    }
                )

        # Always include a positive prompt if team is healthy
        th = bi_scores.get("team_health", {})
        if th.get("score", 0) > 70:
            prompts.append(
                {
                    "theme": "Sustaining Excellence",
                    "prompt": (
                        "Your team's health score is strong. Protect this by maintaining "
                        "regular 1:1 cadence, celebrating wins publicly, and watching for "
                        "early signs of complacency. Strong teams can coast — help them "
                        "find their next growth challenge."
                    ),
                    "source": "behavioral_intelligence",
                }
            )

        return prompts

    # ------------------------------------------------------------------
    # Team Pulse (summary metric)
    # ------------------------------------------------------------------

    def _compute_team_pulse(self, bi_scores: Dict) -> Dict[str, Any]:
        """Single composite 'pulse' score with status."""
        if not bi_scores:
            return {"score": 0, "status": "no_data", "label": "Awaiting Data"}

        # Weighted pulse: team_health and burnout risk matter most
        weights = {
            "team_health": 0.25,
            "collaboration": 0.15,
            "manager_health": 0.10,
            "psychological_safety": 0.20,
            "burnout_risk": 0.15,
            "change_readiness": 0.05,
            "friction_index": 0.10,
        }

        total = 0.0
        weight_sum = 0.0
        for key, weight in weights.items():
            score_data = bi_scores.get(key, {})
            score = score_data.get("score", 0)
            if score > 0:
                # Invert friction and burnout (high = bad)
                if key in ("friction_index", "burnout_risk"):
                    score = 100 - score
                total += score * weight
                weight_sum += weight

        pulse = total / weight_sum if weight_sum > 0 else 0

        if pulse >= 75:
            status, label = "healthy", "Healthy"
        elif pulse >= 55:
            status, label = "moderate", "Moderate"
        elif pulse >= 35:
            status, label = "at_risk", "At Risk"
        else:
            status, label = "critical", "Critical"

        return {
            "score": round(pulse, 1),
            "status": status,
            "label": label,
        }

    # ------------------------------------------------------------------
    # Manager Effectiveness Composite
    # ------------------------------------------------------------------

    def _compute_manager_effectiveness(
        self,
        bi_scores: Dict,
        member_risks: List[Dict],
        network: Dict,
    ) -> Dict[str, Any]:
        """Multi-dimensional manager effectiveness score.

        Dimensions:
          - Team outcomes (40%): BI team_health + collaboration + low burnout
          - People development (25%): member risk profile health
          - Network leadership (15%): low dependency ratio, connected team
          - Manager support (20%): manager_health BI score (includes pulse survey)
        """
        if not bi_scores:
            return {"score": 0, "grade": "N/A", "dimensions": {}}

        # Dimension 1: Team outcomes
        th = bi_scores.get("team_health", {}).get("score", 50)
        co = bi_scores.get("collaboration", {}).get("score", 50)
        br = bi_scores.get("burnout_risk", {}).get("score", 50)
        team_outcomes = th * 0.4 + co * 0.3 + (100 - br) * 0.3

        # Dimension 2: People development (% of team not at elevated/critical risk)
        if member_risks:
            healthy = sum(1 for m in member_risks if m["risk_level"] == "low")
            people_dev = (healthy / len(member_risks)) * 100
        else:
            people_dev = 50.0

        # Dimension 3: Network leadership
        network_score = 50.0
        if network.get("available"):
            dep = network.get("manager_dependency", {})
            dep_ratio = dep.get("avg_dependency_ratio", 0.5)
            # Lower dependency = better distributed leadership
            network_score = max(0, min(100, (1 - dep_ratio) * 100))
            # Bonus for having bridges (cross-team connectors)
            bridges = len(network.get("bridges", []))
            if bridges > 0:
                network_score = min(100, network_score + bridges * 5)

        # Dimension 4: Manager support (from BI manager_health which includes pulse survey)
        mgr_support = bi_scores.get("manager_health", {}).get("score", 50)

        composite = (
            team_outcomes * 0.40
            + people_dev * 0.25
            + network_score * 0.15
            + mgr_support * 0.20
        )

        # Grade
        if composite >= 80:
            grade = "A"
        elif composite >= 65:
            grade = "B"
        elif composite >= 50:
            grade = "C"
        elif composite >= 35:
            grade = "D"
        else:
            grade = "F"

        return {
            "score": round(composite, 1),
            "grade": grade,
            "dimensions": {
                "team_outcomes": round(team_outcomes, 1),
                "people_development": round(people_dev, 1),
                "network_leadership": round(network_score, 1),
                "manager_support": round(mgr_support, 1),
            },
        }

    # ------------------------------------------------------------------
    # Data Fetchers
    # ------------------------------------------------------------------

    async def _get_team(self, db: AsyncSession, team_id: str) -> Optional[Team]:
        result = await db.execute(select(Team).where(Team.id == team_id))
        return result.scalar_one_or_none()

    async def _get_members_with_names(
        self, db: AsyncSession, team_id: str
    ) -> List[Dict[str, Any]]:
        query = (
            select(TeamMember.user_id, User.full_name, User.email)
            .join(User, User.id == TeamMember.user_id)
            .where(TeamMember.team_id == team_id)
        )
        result = await db.execute(query)
        return [
            {
                "user_id": str(row[0]),
                "name": row[1] or row[2] or "Unknown",
            }
            for row in result.all()
        ]

    async def _get_member_burnout(
        self, db: AsyncSession, user_id: str
    ) -> Optional[float]:
        try:
            from app.db.models.wellness_burnout import WellnessMetrics

            query = (
                select(WellnessMetrics.burnout_risk_score)
                .where(WellnessMetrics.user_id == user_id)
                .where(
                    WellnessMetrics.measurement_date
                    >= date.today() - timedelta(days=90)
                )
                .order_by(desc(WellnessMetrics.measurement_date))
                .limit(1)
            )
            result = await db.execute(query)
            val = result.scalar_one_or_none()
            return float(val) if val is not None else None
        except Exception:
            return None

    async def _get_member_engagement(
        self, db: AsyncSession, user_id: str
    ) -> Optional[float]:
        try:
            from app.db.models.wellness_burnout import WellnessMetrics

            query = (
                select(WellnessMetrics.engagement_level)
                .where(WellnessMetrics.user_id == user_id)
                .where(
                    WellnessMetrics.measurement_date
                    >= date.today() - timedelta(days=90)
                )
                .order_by(desc(WellnessMetrics.measurement_date))
                .limit(1)
            )
            result = await db.execute(query)
            val = result.scalar_one_or_none()
            return float(val) if val is not None else None
        except Exception:
            return None

    async def _get_member_churn(self, db: AsyncSession, user_id: str) -> Optional[int]:
        try:
            from app.db.models.churn_prediction import ChurnRiskScore

            query = (
                select(ChurnRiskScore.overall_score)
                .where(ChurnRiskScore.user_id == user_id)
                .order_by(desc(ChurnRiskScore.calculated_at))
                .limit(1)
            )
            result = await db.execute(query)
            val = result.scalar_one_or_none()
            return int(val) if val is not None else None
        except Exception:
            return None

    async def _get_member_network_role(
        self, db: AsyncSession, user_id: str
    ) -> Optional[Dict]:
        try:
            from app.db.models.network_analysis import NetworkSnapshot

            query = (
                select(NetworkSnapshot.node_metrics)
                .order_by(desc(NetworkSnapshot.snapshot_date))
                .limit(1)
            )
            result = await db.execute(query)
            node_metrics = result.scalar_one_or_none()

            if not node_metrics or not isinstance(node_metrics, dict):
                return None

            user_data = node_metrics.get(user_id)
            if not user_data:
                return None

            return {
                "role": user_data.get("role", "member"),
                "degree": user_data.get("degree_centrality", 0),
                "betweenness": user_data.get("betweenness_centrality", 0),
            }
        except Exception:
            return None
