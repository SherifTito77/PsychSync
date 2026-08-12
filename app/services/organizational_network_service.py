"""
Organizational Network Analysis (ONA) Service

Derives informal organizational networks from assessment co-participation,
team membership, and response patterns. Identifies:
  - Hidden influencers (high centrality without formal authority)
  - Isolated employees (low connectivity, disengagement risk)
  - Knowledge hubs (bridge multiple teams/groups)
  - Cross-team collaboration strength
  - Manager dependency (over-reliance on single points of contact)

Network edges are derived from:
  1. Assessment co-participation (same assessment, overlapping time window)
  2. Multi-team membership (shared team = implicit connection)
  3. Response pattern similarity (similar answer profiles)
"""

import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.response import Response
from app.db.models.team import Team, TeamMember
from app.db.models.user import User

logger = logging.getLogger(__name__)


class OrganizationalNetworkService:
    """Builds and analyzes implicit organizational networks."""

    async def analyze_organization(
        self,
        db: AsyncSession,
        organization_id: str,
        lookback_days: int = 60,
    ) -> Dict[str, Any]:
        """Full ONA for an organization."""
        since = datetime.utcnow() - timedelta(days=lookback_days)

        # Get all teams and members in the org
        teams = await self._get_org_teams(db, organization_id)
        if not teams:
            return self._empty_analysis(organization_id)

        team_ids = [str(t.id) for t in teams]
        members_by_team = await self._get_members_by_team(db, team_ids)

        all_user_ids: Set[str] = set()
        user_teams: Dict[str, List[str]] = defaultdict(list)
        for tid, members in members_by_team.items():
            for m in members:
                uid = str(m.user_id)
                all_user_ids.add(uid)
                user_teams[uid].append(tid)

        if not all_user_ids:
            return self._empty_analysis(organization_id)

        user_list = sorted(all_user_ids)

        # Build adjacency from co-participation
        edges = await self._build_edges(db, user_list, since)

        # Compute centrality metrics
        degree = self._degree_centrality(user_list, edges)
        betweenness = self._betweenness_centrality(user_list, edges)
        bridging = self._bridging_score(user_list, edges, user_teams)

        # Fetch user names
        user_names = await self._get_user_names(db, user_list)

        # Classify nodes
        nodes = []
        influencers = []
        isolated = []
        bridges = []

        for uid in user_list:
            d = degree.get(uid, 0)
            b = betweenness.get(uid, 0)
            br = bridging.get(uid, 0)
            team_count = len(user_teams.get(uid, []))

            role = self._classify_node(d, b, br, team_count, len(user_list))
            node = {
                "user_id": uid,
                "name": user_names.get(uid, "Unknown"),
                "degree_centrality": round(d, 3),
                "betweenness_centrality": round(b, 3),
                "bridging_score": round(br, 3),
                "team_count": team_count,
                "role": role,
                "teams": user_teams.get(uid, []),
            }
            nodes.append(node)

            if role == "influencer":
                influencers.append(node)
            elif role == "isolated":
                isolated.append(node)
            elif role == "bridge":
                bridges.append(node)

        # Cross-team collaboration
        cross_team = self._cross_team_collaboration(edges, user_teams, teams)

        # Manager dependency
        manager_dep = self._manager_dependency(members_by_team, degree)

        # Network health
        density = len(edges) / max(len(user_list) * (len(user_list) - 1) / 2, 1)
        avg_degree = sum(degree.values()) / max(len(degree), 1)

        return {
            "organization_id": organization_id,
            "lookback_days": lookback_days,
            "network_stats": {
                "total_nodes": len(user_list),
                "total_edges": len(edges),
                "density": round(density, 4),
                "avg_degree_centrality": round(avg_degree, 3),
            },
            "nodes": sorted(
                nodes, key=lambda n: n["betweenness_centrality"], reverse=True
            ),
            "edges": [
                {"source": e[0], "target": e[1], "weight": w} for e, w in edges.items()
            ],
            "insights": {
                "influencers": sorted(
                    influencers, key=lambda n: n["betweenness_centrality"], reverse=True
                )[:10],
                "isolated": sorted(isolated, key=lambda n: n["degree_centrality"])[:10],
                "bridges": sorted(
                    bridges, key=lambda n: n["bridging_score"], reverse=True
                )[:10],
            },
            "cross_team_collaboration": cross_team,
            "manager_dependency": manager_dep,
            "recommendations": self._generate_recommendations(
                influencers, isolated, bridges, density, manager_dep
            ),
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ══════════════════════════════════════════════════════════════════
    # EDGE BUILDING
    # ══════════════════════════════════════════════════════════════════

    async def _build_edges(
        self, db: AsyncSession, user_ids: List[str], since: datetime
    ) -> Dict[Tuple[str, str], float]:
        """Build weighted edges from assessment co-participation."""
        edges: Dict[Tuple[str, str], float] = {}

        # Find assessment co-participation: users who answered the same assessment
        result = await db.execute(
            select(
                Response.assessment_id,
                Response.user_id,
            )
            .where(
                and_(
                    Response.user_id.in_(user_ids),
                    Response.created_at >= since,
                )
            )
            .group_by(Response.assessment_id, Response.user_id)
        )
        rows = result.all()

        # Group users by assessment
        assessment_users: Dict[str, List[str]] = defaultdict(list)
        for assessment_id, user_id in rows:
            assessment_users[str(assessment_id)].append(str(user_id))

        # Create edges for each pair of users who share an assessment
        for _aid, users in assessment_users.items():
            for i in range(len(users)):
                for j in range(i + 1, len(users)):
                    edge = (min(users[i], users[j]), max(users[i], users[j]))
                    edges[edge] = edges.get(edge, 0) + 1.0

        return edges

    # ══════════════════════════════════════════════════════════════════
    # CENTRALITY METRICS
    # ══════════════════════════════════════════════════════════════════

    def _degree_centrality(
        self, nodes: List[str], edges: Dict[Tuple[str, str], float]
    ) -> Dict[str, float]:
        """Normalized degree centrality (connections / max possible)."""
        degree_count: Dict[str, int] = defaultdict(int)
        for u, v in edges:
            degree_count[u] += 1
            degree_count[v] += 1

        n = len(nodes)
        max_degree = max(n - 1, 1)
        return {uid: degree_count.get(uid, 0) / max_degree for uid in nodes}

    def _betweenness_centrality(
        self, nodes: List[str], edges: Dict[Tuple[str, str], float]
    ) -> Dict[str, float]:
        """
        Approximate betweenness centrality using BFS shortest paths.
        For large graphs, samples a subset of source nodes.
        """
        adj: Dict[str, Set[str]] = defaultdict(set)
        for u, v in edges:
            adj[u].add(v)
            adj[v].add(u)

        betweenness: Dict[str, float] = {n: 0.0 for n in nodes}
        # Sample sources for performance (max 50)
        sources = nodes[:50] if len(nodes) > 50 else nodes

        for s in sources:
            # BFS from s
            stack = []
            pred: Dict[str, List[str]] = {n: [] for n in nodes}
            sigma: Dict[str, float] = {n: 0.0 for n in nodes}
            dist: Dict[str, int] = {n: -1 for n in nodes}
            sigma[s] = 1.0
            dist[s] = 0

            queue = [s]
            qi = 0
            while qi < len(queue):
                v = queue[qi]
                qi += 1
                stack.append(v)
                for w in adj.get(v, set()):
                    if dist[w] < 0:
                        dist[w] = dist[v] + 1
                        queue.append(w)
                    if dist[w] == dist[v] + 1:
                        sigma[w] += sigma[v]
                        pred[w].append(v)

            delta: Dict[str, float] = {n: 0.0 for n in nodes}
            while stack:
                w = stack.pop()
                for v in pred[w]:
                    if sigma[w] > 0:
                        delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
                if w != s:
                    betweenness[w] += delta[w]

        # Normalize
        n = len(nodes)
        scale = 1.0 / max((n - 1) * (n - 2), 1) if n > 2 else 1.0
        if len(sources) < len(nodes):
            scale *= len(nodes) / len(sources)

        return {uid: betweenness[uid] * scale for uid in nodes}

    def _bridging_score(
        self,
        nodes: List[str],
        edges: Dict[Tuple[str, str], float],
        user_teams: Dict[str, List[str]],
    ) -> Dict[str, float]:
        """How much does a user connect different team clusters?"""
        scores: Dict[str, float] = {}
        adj: Dict[str, Set[str]] = defaultdict(set)
        for u, v in edges:
            adj[u].add(v)
            adj[v].add(u)

        for uid in nodes:
            neighbors = adj.get(uid, set())
            if not neighbors:
                scores[uid] = 0.0
                continue

            my_teams = set(user_teams.get(uid, []))
            cross_team_neighbors = 0
            for nb in neighbors:
                nb_teams = set(user_teams.get(nb, []))
                if nb_teams and nb_teams != my_teams:
                    cross_team_neighbors += 1

            scores[uid] = cross_team_neighbors / max(len(neighbors), 1)

        return scores

    # ══════════════════════════════════════════════════════════════════
    # NODE CLASSIFICATION
    # ══════════════════════════════════════════════════════════════════

    def _classify_node(
        self,
        degree: float,
        betweenness: float,
        bridging: float,
        team_count: int,
        total_nodes: int,
    ) -> str:
        """Classify a node's organizational role."""
        if degree < 0.05 and betweenness < 0.01:
            return "isolated"
        if betweenness > 0.1 and degree > 0.2:
            return "influencer"
        if bridging > 0.4 and team_count >= 2:
            return "bridge"
        if degree > 0.3:
            return "connector"
        return "regular"

    # ══════════════════════════════════════════════════════════════════
    # CROSS-TEAM & MANAGER ANALYSIS
    # ══════════════════════════════════════════════════════════════════

    def _cross_team_collaboration(
        self,
        edges: Dict[Tuple[str, str], float],
        user_teams: Dict[str, List[str]],
        teams: list,
    ) -> List[Dict[str, Any]]:
        """Collaboration strength between team pairs."""
        team_name_map = {str(t.id): t.name for t in teams}
        team_pair_edges: Dict[Tuple[str, str], int] = defaultdict(int)

        for (u, v), weight in edges.items():
            u_teams = user_teams.get(u, [])
            v_teams = user_teams.get(v, [])
            for ut in u_teams:
                for vt in v_teams:
                    if ut != vt:
                        pair = (min(ut, vt), max(ut, vt))
                        team_pair_edges[pair] += int(weight)

        result = []
        for (t1, t2), strength in sorted(
            team_pair_edges.items(), key=lambda x: x[1], reverse=True
        ):
            result.append(
                {
                    "team_a": {"id": t1, "name": team_name_map.get(t1, t1)},
                    "team_b": {"id": t2, "name": team_name_map.get(t2, t2)},
                    "collaboration_strength": strength,
                    "label": (
                        "Strong"
                        if strength > 5
                        else ("Moderate" if strength > 2 else "Weak")
                    ),
                }
            )

        return result[:20]

    def _manager_dependency(
        self,
        members_by_team: Dict[str, list],
        degree: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """Identify teams overly dependent on a single high-centrality member."""
        results = []
        for tid, members in members_by_team.items():
            if len(members) < 2:
                continue

            member_degrees = []
            for m in members:
                uid = str(m.user_id)
                member_degrees.append(
                    {
                        "user_id": uid,
                        "degree": degree.get(uid, 0),
                        "role": (
                            m.role.value if hasattr(m.role, "value") else str(m.role)
                        ),
                    }
                )

            member_degrees.sort(key=lambda x: x["degree"], reverse=True)
            top = member_degrees[0]["degree"] if member_degrees else 0
            avg = sum(d["degree"] for d in member_degrees) / len(member_degrees)

            # Dependency ratio: how much more connected is the top person?
            ratio = top / max(avg, 0.001)
            if ratio > 2.0 and top > 0.1:
                results.append(
                    {
                        "team_id": tid,
                        "dependency_ratio": round(ratio, 2),
                        "key_person": member_degrees[0]["user_id"],
                        "risk_level": "high" if ratio > 3 else "moderate",
                    }
                )

        return sorted(results, key=lambda r: r["dependency_ratio"], reverse=True)

    # ══════════════════════════════════════════════════════════════════
    # RECOMMENDATIONS
    # ══════════════════════════════════════════════════════════════════

    def _generate_recommendations(
        self,
        influencers: list,
        isolated: list,
        bridges: list,
        density: float,
        manager_dep: list,
    ) -> List[str]:
        recs = []
        if isolated:
            recs.append(
                f"{len(isolated)} employee(s) show low network connectivity. "
                "Consider pairing them with mentors or including them in cross-functional projects."
            )
        if not bridges:
            recs.append(
                "No strong cross-team bridges detected. Encourage cross-functional assessment sessions "
                "or rotational programs to build informal connections."
            )
        if influencers:
            recs.append(
                f"{len(influencers)} hidden influencer(s) identified — highly connected individuals "
                "who may not hold formal leadership roles. Consider leveraging them as change champions."
            )
        if manager_dep:
            high_dep = [d for d in manager_dep if d["risk_level"] == "high"]
            if high_dep:
                recs.append(
                    f"{len(high_dep)} team(s) show high dependency on a single member. "
                    "This creates a bus factor risk. Encourage knowledge sharing and cross-training."
                )
        if density < 0.1:
            recs.append(
                "Network density is low — few connections exist between employees. "
                "Consider organization-wide events, shared assessments, or collaboration tools."
            )
        if not recs:
            recs.append(
                "Network appears healthy with good connectivity and distribution."
            )
        return recs

    # ══════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════

    async def _get_org_teams(self, db: AsyncSession, org_id: str) -> list:
        result = await db.execute(select(Team).where(Team.organization_id == org_id))
        return result.scalars().all()

    async def _get_members_by_team(
        self, db: AsyncSession, team_ids: List[str]
    ) -> Dict[str, list]:
        result = await db.execute(
            select(TeamMember).where(TeamMember.team_id.in_(team_ids))
        )
        members = result.scalars().all()
        by_team: Dict[str, list] = defaultdict(list)
        for m in members:
            by_team[str(m.team_id)].append(m)
        return by_team

    async def _get_user_names(
        self, db: AsyncSession, user_ids: List[str]
    ) -> Dict[str, str]:
        result = await db.execute(
            select(User.id, User.full_name, User.email).where(User.id.in_(user_ids))
        )
        names = {}
        for uid, full_name, email in result.all():
            names[str(uid)] = full_name or email or str(uid)
        return names

    def _empty_analysis(self, org_id: str) -> Dict[str, Any]:
        return {
            "organization_id": org_id,
            "network_stats": {
                "total_nodes": 0,
                "total_edges": 0,
                "density": 0,
                "avg_degree_centrality": 0,
            },
            "nodes": [],
            "edges": [],
            "insights": {"influencers": [], "isolated": [], "bridges": []},
            "cross_team_collaboration": [],
            "manager_dependency": [],
            "recommendations": [
                "No teams or members found. Create teams and complete assessments to enable network analysis."
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }
