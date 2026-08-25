"""
Organizational Network Analysis (ONA) Service

Derives informal organizational networks from assessment co-participation,
team membership, response patterns, and self-reported collaboration surveys.

Capabilities:
  - Hidden influencers (high centrality without formal authority)
  - Isolated employees (low connectivity, disengagement risk)
  - Knowledge hubs (bridge multiple teams/groups)
  - Cross-team collaboration strength
  - Manager dependency (over-reliance on single points of contact)
  - Community detection (Louvain algorithm)
  - Temporal network evolution (snapshots over time)
  - Personality x network overlay insights

Network edges are derived from:
  1. Assessment co-participation (same assessment, overlapping time window)
  2. Multi-team membership (shared team = implicit connection)
  3. Response pattern similarity (similar answer profiles)
  4. Self-reported collaboration surveys (advice, trust, energy networks)
  5. Work system collaboration (shared sprints/projects via Jira/Azure DevOps)
  6. Communication co-activity (Slack/Teams thread interactions)
"""

import logging
import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import and_, delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.network_analysis import (
    CollaborationSurveyResponse,
    NetworkEdge,
    NetworkSnapshot,
)
from app.db.models.response import Response
from app.db.models.team import Team, TeamMember
from app.db.models.user import User

logger = logging.getLogger(__name__)


class OrganizationalNetworkService:
    """Builds and analyzes implicit organizational networks with persistence."""

    # ══════════════════════════════════════════════════════════════════
    # MAIN ANALYSIS (enhanced with communities + persistence)
    # ══════════════════════════════════════════════════════════════════

    async def analyze_organization(
        self,
        db: AsyncSession,
        organization_id: str,
        lookback_days: int = 60,
    ) -> Dict[str, Any]:
        """Full ONA for an organization with community detection."""
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

        # Build adjacency from co-participation + surveys + connectors
        edges = await self._build_edges(db, user_list, since)
        survey_edges = await self._build_survey_edges(db, organization_id, user_list)
        for key, weight in survey_edges.items():
            edges[key] = edges.get(key, 0) + weight

        # Merge edges from work systems + communication connectors
        connector_edges = await self._build_connector_edges(
            organization_id, db, user_list
        )
        for key, weight in connector_edges.items():
            edges[key] = edges.get(key, 0) + weight

        # Persist edges to database
        await self._persist_edges(db, organization_id, edges, user_list, user_teams)

        # Compute centrality metrics
        degree = self._degree_centrality(user_list, edges)
        betweenness = self._betweenness_centrality(user_list, edges)
        bridging = self._bridging_score(user_list, edges, user_teams)

        # Community detection (Louvain)
        communities = self._detect_communities(user_list, edges)

        # Fetch user names
        user_names = await self._get_user_names(db, user_list)

        # Build community membership lookup
        node_community: Dict[str, int] = {}
        for comm in communities:
            for member_id in comm["members"]:
                node_community[member_id] = comm["id"]

        # Classify nodes
        nodes = []
        influencers = []
        isolated = []
        bridges_list = []

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
                "community_id": node_community.get(uid),
            }
            nodes.append(node)

            if role == "influencer":
                influencers.append(node)
            elif role == "isolated":
                isolated.append(node)
            elif role == "bridge":
                bridges_list.append(node)

        # Cross-team collaboration
        cross_team = self._cross_team_collaboration(edges, user_teams, teams)

        # Manager dependency
        manager_dep = self._manager_dependency(members_by_team, degree)

        # Network health
        density = len(edges) / max(len(user_list) * (len(user_list) - 1) / 2, 1)
        avg_degree = sum(degree.values()) / max(len(degree), 1)

        # Save snapshot for temporal tracking
        await self._save_snapshot(
            db,
            organization_id,
            user_list,
            edges,
            density,
            avg_degree,
            betweenness,
            communities,
            cross_team,
            influencers,
            isolated,
            bridges_list,
        )

        return {
            "organization_id": organization_id,
            "lookback_days": lookback_days,
            "network_stats": {
                "total_nodes": len(user_list),
                "total_edges": len(edges),
                "density": round(density, 4),
                "avg_degree_centrality": round(avg_degree, 3),
                "num_communities": len(communities),
            },
            "nodes": sorted(
                nodes, key=lambda n: n["betweenness_centrality"], reverse=True
            ),
            "edges": [
                {"source": e[0], "target": e[1], "weight": w} for e, w in edges.items()
            ],
            "communities": communities,
            "insights": {
                "influencers": sorted(
                    influencers, key=lambda n: n["betweenness_centrality"], reverse=True
                )[:10],
                "isolated": sorted(isolated, key=lambda n: n["degree_centrality"])[:10],
                "bridges": sorted(
                    bridges_list, key=lambda n: n["bridging_score"], reverse=True
                )[:10],
            },
            "cross_team_collaboration": cross_team,
            "manager_dependency": manager_dep,
            "recommendations": self._generate_recommendations(
                influencers, isolated, bridges_list, density, manager_dep
            ),
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ══════════════════════════════════════════════════════════════════
    # COMMUNITY DETECTION (Louvain algorithm)
    # ══════════════════════════════════════════════════════════════════

    def _detect_communities(
        self,
        nodes: List[str],
        edges: Dict[Tuple[str, str], float],
    ) -> List[Dict[str, Any]]:
        """
        Louvain-style community detection.
        Returns list of communities with members, size, and internal density.
        """
        if not edges:
            return [
                {"id": 0, "members": nodes, "size": len(nodes), "internal_density": 0.0}
            ]

        adj: Dict[str, Dict[str, float]] = defaultdict(dict)
        for (u, v), w in edges.items():
            adj[u][v] = w
            adj[v][u] = w

        total_weight = sum(edges.values())
        if total_weight == 0:
            return [
                {"id": 0, "members": nodes, "size": len(nodes), "internal_density": 0.0}
            ]

        # Node degree (weighted)
        k: Dict[str, float] = defaultdict(float)
        for (u, v), w in edges.items():
            k[u] += w
            k[v] += w

        # Start: each node in its own community
        community: Dict[str, int] = {n: i for i, n in enumerate(nodes)}
        improved = True
        max_iterations = 10

        while improved and max_iterations > 0:
            improved = False
            max_iterations -= 1
            for node in nodes:
                current_comm = community[node]
                best_comm = current_comm
                best_gain = 0.0

                # Calculate neighbor community weights
                neighbor_comms: Dict[int, float] = defaultdict(float)
                for nb, w in adj.get(node, {}).items():
                    neighbor_comms[community[nb]] += w

                # Temporarily remove node from its community
                ki = k.get(node, 0)

                for comm_id, w_in in neighbor_comms.items():
                    if comm_id == current_comm:
                        continue
                    # Modularity gain approximation
                    sigma_tot = sum(
                        k.get(n, 0) for n in nodes if community[n] == comm_id
                    )
                    gain = w_in - (sigma_tot * ki) / (2 * total_weight)
                    if gain > best_gain:
                        best_gain = gain
                        best_comm = comm_id

                if best_comm != current_comm:
                    community[node] = best_comm
                    improved = True

        # Build community list
        comm_members: Dict[int, List[str]] = defaultdict(list)
        for node, comm_id in community.items():
            comm_members[comm_id].append(node)

        # Renumber and compute internal density
        result = []
        for new_id, (_, members) in enumerate(
            sorted(comm_members.items(), key=lambda x: -len(x[1]))
        ):
            member_set = set(members)
            internal_edges = sum(
                1 for (u, v) in edges if u in member_set and v in member_set
            )
            max_possible = len(members) * (len(members) - 1) / 2
            density = internal_edges / max_possible if max_possible > 0 else 0.0

            result.append(
                {
                    "id": new_id,
                    "members": members,
                    "size": len(members),
                    "internal_density": round(density, 3),
                    "health_score": self._calculate_community_health(
                        members, member_set, edges, density
                    ),
                }
            )

        return result

    def _calculate_community_health(
        self,
        members: List[str],
        member_set: Set[str],
        edges: Dict[Tuple[str, str], float],
        internal_density: float,
    ) -> float | None:
        """
        Score community health 0-100 by combining four signals:
        cohesion, permeability, size, and weight distribution.
        """
        size = len(members)
        if size < 2:
            return None

        # 1. Cohesion score (0-100) from internal density
        cohesion = min(internal_density * 100, 100.0)

        # 2. Permeability — conductance ratio: external / (internal + external)
        #    Healthy range is 0.2-0.5 (connected but not dissolved)
        internal_count = 0
        external_count = 0
        internal_weights: List[float] = []
        per_member_internal: Dict[str, float] = defaultdict(float)

        for (u, v), w in edges.items():
            u_in = u in member_set
            v_in = v in member_set
            if u_in and v_in:
                internal_count += 1
                internal_weights.append(w)
                per_member_internal[u] += w
                per_member_internal[v] += w
            elif u_in or v_in:
                external_count += 1

        total_incident = internal_count + external_count
        if total_incident == 0:
            return None

        conductance = external_count / total_incident
        # Peak score at conductance ~0.35 (balanced), penalize extremes
        permeability = max(0, 100 - abs(conductance - 0.35) * 200)

        # 3. Size factor — optimal range 3-15 members
        if size < 3:
            size_score = 40.0
        elif size <= 15:
            size_score = 100.0
        elif size <= 25:
            size_score = max(50.0, 100 - (size - 15) * 5)
        else:
            size_score = 30.0

        # 4. Weight distribution — Gini coefficient of internal edge weights
        #    Low Gini = evenly distributed = healthy; High Gini = dependency
        if len(internal_weights) >= 2:
            sorted_w = sorted(internal_weights)
            n = len(sorted_w)
            total_w = sum(sorted_w)
            if total_w > 0:
                cumulative = sum((2 * i - n + 1) * w for i, w in enumerate(sorted_w))
                gini = cumulative / (n * total_w)
            else:
                gini = 0.0
            distribution_score = max(0, (1 - gini) * 100)
        else:
            distribution_score = 50.0  # insufficient data, neutral

        # Weighted combination
        score = (
            cohesion * 0.30
            + permeability * 0.30
            + size_score * 0.15
            + distribution_score * 0.25
        )

        return round(max(0, min(100, score)), 1)

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

    async def _build_survey_edges(
        self,
        db: AsyncSession,
        organization_id: str,
        user_ids: List[str],
    ) -> Dict[Tuple[str, str], float]:
        """Build edges from self-reported collaboration surveys."""
        edges: Dict[Tuple[str, str], float] = {}

        result = await db.execute(
            select(CollaborationSurveyResponse).where(
                and_(
                    CollaborationSurveyResponse.organization_id == organization_id,
                    CollaborationSurveyResponse.respondent_id.in_(user_ids),
                    CollaborationSurveyResponse.nominee_id.in_(user_ids),
                )
            )
        )
        for row in result.scalars().all():
            u, v = str(row.respondent_id), str(row.nominee_id)
            edge = (min(u, v), max(u, v))
            # Survey edges weighted higher (self-reported = high signal)
            edges[edge] = edges.get(edge, 0) + row.strength * 0.5

        return edges

    async def _build_connector_edges(
        self,
        organization_id: str,
        db: AsyncSession,
        user_ids: List[str],
    ) -> Dict[Tuple[str, str], float]:
        """Build edges from work system + communication connectors.

        Uses DataSourceAggregator to gather collaboration edges from
        Jira/Azure DevOps (shared sprints) and Slack/Teams (thread interactions).
        These are email-based edges that need resolving to user IDs.
        """
        try:
            from app.services.data_source_aggregator import data_source_aggregator
        except ImportError:
            return {}

        edges: Dict[Tuple[str, str], float] = {}
        try:
            connector_edges = await data_source_aggregator.gather_ona_edges(
                organization_id
            )
        except Exception as exc:
            logger.warning("Failed to gather connector edges: %s", exc)
            return edges

        if not connector_edges:
            return edges

        # Resolve email → user_id mapping
        from app.db.models.user import User

        email_result = await db.execute(
            select(User.id, User.email).where(User.id.in_(user_ids))
        )
        email_to_uid: Dict[str, str] = {}
        for uid, email in email_result.all():
            if email:
                email_to_uid[email.lower()] = str(uid)

        for edge_data in connector_edges:
            src = email_to_uid.get(edge_data["source_email"].lower())
            tgt = email_to_uid.get(edge_data["target_email"].lower())
            if src and tgt and src != tgt and src in user_ids and tgt in user_ids:
                pair = (min(src, tgt), max(src, tgt))
                edges[pair] = edges.get(pair, 0) + edge_data["weight"]

        logger.info(
            "ONA connector edges: %d resolved from %d raw edges",
            len(edges),
            len(connector_edges),
        )
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
                "num_communities": 0,
            },
            "nodes": [],
            "edges": [],
            "communities": [],
            "insights": {"influencers": [], "isolated": [], "bridges": []},
            "cross_team_collaboration": [],
            "manager_dependency": [],
            "recommendations": [
                "No teams or members found. Create teams and complete assessments to enable network analysis."
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ══════════════════════════════════════════════════════════════════
    # PERSISTENCE — Save edges to database
    # ══════════════════════════════════════════════════════════════════

    async def _persist_edges(
        self,
        db: AsyncSession,
        organization_id: str,
        edges: Dict[Tuple[str, str], float],
        user_list: List[str],
        user_teams: Dict[str, List[str]],
    ) -> None:
        """Upsert computed edges into network_edges table."""
        if not edges:
            return

        now = datetime.utcnow()
        for (u, v), weight in edges.items():
            stmt = (
                pg_insert(NetworkEdge)
                .values(
                    organization_id=organization_id,
                    source_user_id=u,
                    target_user_id=v,
                    edge_type="co_assessment",
                    weight=weight,
                    first_observed_at=now,
                    last_observed_at=now,
                )
                .on_conflict_do_update(
                    constraint="uq_network_edge",
                    set_={
                        "weight": weight,
                        "last_observed_at": now,
                    },
                )
            )
            await db.execute(stmt)

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            logger.warning(
                "Failed to persist network edges, continuing with in-memory analysis"
            )

    # ══════════════════════════════════════════════════════════════════
    # TEMPORAL — Save and retrieve network snapshots
    # ══════════════════════════════════════════════════════════════════

    async def _save_snapshot(
        self,
        db: AsyncSession,
        organization_id: str,
        user_list: List[str],
        edges: Dict[Tuple[str, str], float],
        density: float,
        avg_degree: float,
        betweenness: Dict[str, float],
        communities: List[Dict],
        cross_team: List[Dict],
        influencers: List[Dict],
        isolated: List[Dict],
        bridges: List[Dict],
    ) -> None:
        """Save a point-in-time network snapshot for temporal tracking."""
        today = date.today()
        avg_betweenness = (
            sum(betweenness.values()) / len(betweenness) if betweenness else 0
        )

        # Compact node metrics
        node_metrics = [
            {
                "user_id": uid,
                "degree": round(betweenness.get(uid, 0), 3),
                "community_id": next(
                    (c["id"] for c in communities if uid in c.get("members", [])),
                    None,
                ),
            }
            for uid in user_list[:200]  # Cap to avoid oversized JSON
        ]

        stmt = (
            pg_insert(NetworkSnapshot)
            .values(
                organization_id=organization_id,
                snapshot_date=today,
                total_nodes=len(user_list),
                total_edges=len(edges),
                density=round(density, 4),
                avg_degree_centrality=round(avg_degree, 3),
                avg_betweenness_centrality=round(avg_betweenness, 3),
                num_communities=len(communities),
                num_isolates=len(isolated),
                num_influencers=len(influencers),
                num_bridges=len(bridges),
                node_metrics=node_metrics,
                communities=[
                    {
                        "id": c["id"],
                        "size": c["size"],
                        "internal_density": c["internal_density"],
                    }
                    for c in communities
                ],
                cross_team_density=cross_team[:20],
            )
            .on_conflict_do_update(
                constraint="uq_network_snapshot_date",
                set_={
                    "total_nodes": len(user_list),
                    "total_edges": len(edges),
                    "density": round(density, 4),
                    "avg_degree_centrality": round(avg_degree, 3),
                    "avg_betweenness_centrality": round(avg_betweenness, 3),
                    "num_communities": len(communities),
                    "num_isolates": len(isolated),
                    "num_influencers": len(influencers),
                    "num_bridges": len(bridges),
                    "node_metrics": node_metrics,
                    "communities": [
                        {
                            "id": c["id"],
                            "size": c["size"],
                            "internal_density": c["internal_density"],
                        }
                        for c in communities
                    ],
                    "cross_team_density": cross_team[:20],
                },
            )
        )

        try:
            await db.execute(stmt)
            await db.commit()
        except Exception:
            await db.rollback()
            logger.warning("Failed to save network snapshot")

    async def get_temporal_evolution(
        self,
        db: AsyncSession,
        organization_id: str,
        days: int = 90,
    ) -> List[Dict[str, Any]]:
        """Retrieve network snapshots over time for trend visualization."""
        since = date.today() - timedelta(days=days)
        result = await db.execute(
            select(NetworkSnapshot)
            .where(
                and_(
                    NetworkSnapshot.organization_id == organization_id,
                    NetworkSnapshot.snapshot_date >= since,
                )
            )
            .order_by(NetworkSnapshot.snapshot_date)
        )
        snapshots = result.scalars().all()

        return [
            {
                "date": str(s.snapshot_date),
                "total_nodes": s.total_nodes,
                "total_edges": s.total_edges,
                "density": float(s.density) if s.density else 0,
                "avg_degree_centrality": (
                    float(s.avg_degree_centrality) if s.avg_degree_centrality else 0
                ),
                "num_communities": s.num_communities,
                "num_isolates": s.num_isolates,
                "num_influencers": s.num_influencers,
                "num_bridges": s.num_bridges,
                "communities": s.communities,
            }
            for s in snapshots
        ]

    # ══════════════════════════════════════════════════════════════════
    # COLLABORATION SURVEY
    # ══════════════════════════════════════════════════════════════════

    async def submit_collaboration_survey(
        self,
        db: AsyncSession,
        organization_id: str,
        respondent_id: str,
        nominations: List[Dict[str, Any]],
        survey_round: str | None = None,
    ) -> Dict[str, Any]:
        """
        Submit collaboration survey responses.
        Each nomination: {nominee_id, network_type, strength}
        network_type: advice | trust | energy | collaboration
        """
        saved = 0
        for nom in nominations:
            stmt = (
                pg_insert(CollaborationSurveyResponse)
                .values(
                    organization_id=organization_id,
                    respondent_id=respondent_id,
                    nominee_id=nom["nominee_id"],
                    network_type=nom["network_type"],
                    strength=nom.get("strength", 3),
                    survey_round=survey_round,
                )
                .on_conflict_do_update(
                    constraint="uq_collab_survey_response",
                    set_={
                        "strength": nom.get("strength", 3),
                    },
                )
            )
            await db.execute(stmt)
            saved += 1

            # Also persist as a network edge
            edge_type = f"survey_{nom['network_type']}"
            edge_stmt = (
                pg_insert(NetworkEdge)
                .values(
                    organization_id=organization_id,
                    source_user_id=respondent_id,
                    target_user_id=nom["nominee_id"],
                    edge_type=edge_type,
                    weight=nom.get("strength", 3) * 0.5,
                    first_observed_at=datetime.utcnow(),
                    last_observed_at=datetime.utcnow(),
                )
                .on_conflict_do_update(
                    constraint="uq_network_edge",
                    set_={
                        "weight": nom.get("strength", 3) * 0.5,
                        "last_observed_at": datetime.utcnow(),
                    },
                )
            )
            await db.execute(edge_stmt)

        await db.commit()
        return {
            "saved": saved,
            "respondent_id": respondent_id,
            "survey_round": survey_round,
        }

    async def get_survey_network(
        self,
        db: AsyncSession,
        organization_id: str,
        network_type: str | None = None,
        survey_round: str | None = None,
    ) -> Dict[str, Any]:
        """Get survey-derived network for a specific type (advice/trust/energy)."""
        query = select(CollaborationSurveyResponse).where(
            CollaborationSurveyResponse.organization_id == organization_id
        )
        if network_type:
            query = query.where(
                CollaborationSurveyResponse.network_type == network_type
            )
        if survey_round:
            query = query.where(
                CollaborationSurveyResponse.survey_round == survey_round
            )

        result = await db.execute(query)
        responses = result.scalars().all()

        # Build directed adjacency
        nodes_set: Set[str] = set()
        directed_edges = []
        for r in responses:
            src, tgt = str(r.respondent_id), str(r.nominee_id)
            nodes_set.add(src)
            nodes_set.add(tgt)
            directed_edges.append(
                {
                    "source": src,
                    "target": tgt,
                    "strength": r.strength,
                    "network_type": r.network_type,
                }
            )

        # In-degree (how many people nominated you)
        in_degree: Dict[str, int] = defaultdict(int)
        for e in directed_edges:
            in_degree[e["target"]] += 1

        user_names = await self._get_user_names(db, list(nodes_set))

        return {
            "network_type": network_type or "all",
            "survey_round": survey_round,
            "total_respondents": len({e["source"] for e in directed_edges}),
            "total_nominees": len(nodes_set),
            "edges": directed_edges,
            "top_nominated": sorted(
                [
                    {
                        "user_id": uid,
                        "name": user_names.get(uid, uid),
                        "nominations": count,
                    }
                    for uid, count in in_degree.items()
                ],
                key=lambda x: x["nominations"],
                reverse=True,
            )[:15],
        }

    # ══════════════════════════════════════════════════════════════════
    # PERSONALITY x NETWORK OVERLAY
    # ══════════════════════════════════════════════════════════════════

    async def get_personality_network_insights(
        self,
        db: AsyncSession,
        organization_id: str,
        lookback_days: int = 60,
    ) -> Dict[str, Any]:
        """
        Overlay Big Five personality data onto network positions.
        Identifies patterns like high-centrality introverts, isolated high-performers, etc.
        """
        # Get the full network analysis first
        analysis = await self.analyze_organization(db, organization_id, lookback_days)

        if not analysis["nodes"]:
            return {"insights": [], "node_personality": [], "community_profiles": []}

        # Try to fetch personality scores for network members
        user_ids = [n["user_id"] for n in analysis["nodes"]]
        personality_data = await self._get_personality_scores(db, user_ids)

        # Generate personality-network insights
        insights = []
        node_personality = []

        for node in analysis["nodes"]:
            uid = node["user_id"]
            personality = personality_data.get(uid)
            entry = {
                "user_id": uid,
                "name": node["name"],
                "role": node["role"],
                "degree_centrality": node["degree_centrality"],
                "betweenness_centrality": node["betweenness_centrality"],
                "community_id": node.get("community_id"),
            }

            if personality:
                entry["personality"] = personality

                # Insight: High centrality + low extraversion = quiet connector
                if (
                    node["degree_centrality"] > 0.3
                    and personality.get("extraversion", 50) < 40
                ):
                    insights.append(
                        {
                            "type": "quiet_connector",
                            "user_id": uid,
                            "name": node["name"],
                            "message": f"{node['name']} is highly connected despite low extraversion — a quiet but effective connector who may benefit from reduced meeting load.",
                        }
                    )

                # Insight: Isolated + high conscientiousness = underutilized performer
                if (
                    node["role"] == "isolated"
                    and personality.get("conscientiousness", 50) > 70
                ):
                    insights.append(
                        {
                            "type": "underutilized_performer",
                            "user_id": uid,
                            "name": node["name"],
                            "message": f"{node['name']} scores high on conscientiousness but is isolated in the network — likely a quiet high-performer being underutilized.",
                        }
                    )

                # Insight: Bridge + low agreeableness = friction-prone bridge
                if (
                    node["role"] == "bridge"
                    and personality.get("agreeableness", 50) < 35
                ):
                    insights.append(
                        {
                            "type": "friction_bridge",
                            "user_id": uid,
                            "name": node["name"],
                            "message": f"{node['name']} bridges teams but scores low on agreeableness — effective connector who may create friction.",
                        }
                    )

                # Insight: Influencer + high openness = innovation catalyst
                if (
                    node["role"] == "influencer"
                    and personality.get("openness", 50) > 70
                ):
                    insights.append(
                        {
                            "type": "innovation_catalyst",
                            "user_id": uid,
                            "name": node["name"],
                            "message": f"{node['name']} is a hidden influencer with high openness — ideal candidate for innovation initiatives and change champion roles.",
                        }
                    )

                # Insight: High neuroticism + high centrality = burnout risk
                if (
                    node["degree_centrality"] > 0.3
                    and personality.get("neuroticism", 50) > 70
                ):
                    insights.append(
                        {
                            "type": "burnout_risk",
                            "user_id": uid,
                            "name": node["name"],
                            "message": f"{node['name']} has high network centrality combined with high neuroticism — elevated burnout risk due to social demand.",
                        }
                    )

            node_personality.append(entry)

        # Community personality profiles
        community_profiles = []
        for comm in analysis.get("communities", []):
            members = comm.get("members", [])
            comm_personalities = [
                personality_data[uid] for uid in members if uid in personality_data
            ]
            if comm_personalities:
                profile = {}
                for trait in [
                    "openness",
                    "conscientiousness",
                    "extraversion",
                    "agreeableness",
                    "neuroticism",
                ]:
                    values = [p.get(trait, 50) for p in comm_personalities]
                    profile[trait] = round(sum(values) / len(values), 1)
                community_profiles.append(
                    {
                        "community_id": comm["id"],
                        "size": comm["size"],
                        "avg_personality": profile,
                        "dominant_trait": max(profile, key=lambda t: profile[t]),
                    }
                )

        return {
            "insights": sorted(insights, key=lambda x: x["type"]),
            "node_personality": node_personality,
            "community_profiles": community_profiles,
        }

    async def _get_personality_scores(
        self, db: AsyncSession, user_ids: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Fetch Big Five scores for users from their latest assessment responses."""
        try:
            from app.db.models.score import Score

            result = await db.execute(
                select(Score).where(
                    and_(
                        Score.user_id.in_(user_ids),
                        Score.framework.in_(["big_five", "Big Five", "OCEAN"]),
                    )
                )
            )
            scores = result.scalars().all()

            user_scores: Dict[str, Dict[str, float]] = {}
            for score in scores:
                uid = str(score.user_id)
                if uid not in user_scores and score.scores:
                    # Normalize score keys to lowercase
                    user_scores[uid] = {
                        k.lower(): v
                        for k, v in score.scores.items()
                        if k.lower()
                        in {
                            "openness",
                            "conscientiousness",
                            "extraversion",
                            "agreeableness",
                            "neuroticism",
                        }
                    }
            return user_scores
        except Exception:
            logger.debug(
                "Could not fetch personality scores — Score model may not exist"
            )
            return {}
