"""
Network Intelligence Engine

Graph-theory-powered organizational analysis that detects 8 structural signals
from relationship metadata. Layers on top of the existing ONA service to elevate
network analysis from a dashboard feature to the structural backbone of PsychSync.

All signals are derived from RELATIONSHIP METADATA — never message content.
Uses pure Python for graph algorithms (no networkx dependency).

Signals detected:
  1. Isolated Employees — low connectivity risk
  2. Collaboration Bottlenecks — high betweenness centrality
  3. Overloaded Connectors — extreme degree + interaction volume
  4. Non-Interacting Teams — silo detection at team level
  5. Excessive Cross-Team Dependency — blurred team boundaries
  6. Communication Concentration — Gini inequality within teams
  7. Emerging Informal Leaders — high eigenvector centrality without title
  8. Organizational Silos — department-level structural separation
"""

import logging
import math
import random
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class NetworkNode:
    id: str
    email: str
    team_id: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None


@dataclass
class NetworkEdge:
    source: str
    target: str
    weight: float
    edge_type: str  # "meeting", "slack", "email", "code_review", "project", ...


@dataclass
class NetworkSignal:
    signal_type: str
    severity: str  # "info", "warning", "critical"
    severity_score: float  # 0-100
    affected_entities: List[Dict[str, Any]]
    description: str
    recommendation: str
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NetworkAnalysis:
    org_id: str
    node_count: int
    edge_count: int
    density: float
    signals: List[NetworkSignal]
    team_interaction_matrix: Dict[str, Dict[str, float]]
    health_score: float  # 0-100


# ---------------------------------------------------------------------------
# Severity helpers
# ---------------------------------------------------------------------------

_SEVERITY_THRESHOLDS = {"critical": 70, "warning": 40, "info": 0}


def _severity_label(score: float) -> str:
    if score >= _SEVERITY_THRESHOLDS["critical"]:
        return "critical"
    if score >= _SEVERITY_THRESHOLDS["warning"]:
        return "warning"
    return "info"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class NetworkIntelligenceEngine:
    """Detects structural organizational signals from relationship metadata."""

    # ── Public entry point ────────────────────────────────────────────

    def analyze(
        self,
        nodes: List[NetworkNode],
        edges: List[NetworkEdge],
    ) -> NetworkAnalysis:
        """Run all 8 signal detectors and return comprehensive analysis."""
        if not nodes:
            return NetworkAnalysis(
                org_id="",
                node_count=0,
                edge_count=0,
                density=0.0,
                signals=[],
                team_interaction_matrix={},
                health_score=100.0,
            )

        node_map: Dict[str, NetworkNode] = {n.id: n for n in nodes}
        adj = self._build_adjacency(edges)

        # Pre-compute centrality metrics once for reuse across detectors
        degree = self._degree_centrality(adj, len(nodes))
        betweenness = self._betweenness_centrality_sample(adj, sample_size=50)
        eigenvector = self._eigenvector_centrality(adj, iterations=100)

        # Run all 8 signal detectors
        signals: List[NetworkSignal] = []
        detectors = [
            self._detect_isolation,
            self._detect_bottlenecks,
            self._detect_overloaded_connectors,
            self._detect_team_silos,
            self._detect_excessive_cross_team,
            self._detect_communication_concentration,
            self._detect_informal_leaders,
            self._detect_org_silos,
        ]
        for detector in detectors:
            try:
                signal = detector(
                    adj=adj,
                    nodes=node_map,
                    degree=degree,
                    betweenness=betweenness,
                    eigenvector=eigenvector,
                    edges=edges,
                )
                if signal is not None:
                    signals.append(signal)
            except Exception:
                logger.exception("Signal detector %s failed", detector.__name__)

        # Network-wide metrics
        n = len(nodes)
        max_edges = n * (n - 1) / 2
        density = len(edges) / max_edges if max_edges > 0 else 0.0
        team_matrix = self._build_team_interaction_matrix(adj, node_map)
        health = self._network_health_score(signals)

        return NetworkAnalysis(
            org_id="",
            node_count=n,
            edge_count=len(edges),
            density=round(density, 4),
            signals=signals,
            team_interaction_matrix=team_matrix,
            health_score=health,
        )

    # ══════════════════════════════════════════════════════════════════
    # SIGNAL 1: Isolated Employees
    # ══════════════════════════════════════════════════════════════════

    def _detect_isolation(
        self,
        adj: Dict[str, Dict[str, float]],
        nodes: Dict[str, NetworkNode],
        degree: Dict[str, float],
        **_kw: Any,
    ) -> Optional[NetworkSignal]:
        """Find employees with degree centrality < 0.1 (connected to < 10% of their team).

        Critical if 0 connections. Warning if < 3 connections.
        """
        # Build per-team member lists
        teams: Dict[str, List[str]] = defaultdict(list)
        for nid, node in nodes.items():
            tid = node.team_id or "__no_team__"
            teams[tid].append(nid)

        isolated: List[Dict[str, Any]] = []
        for nid, node in nodes.items():
            tid = node.team_id or "__no_team__"
            team_size = len(teams[tid])
            neighbor_count = len(adj.get(nid, {}))

            # Team-relative threshold: connected to < 10% of team
            threshold = max(team_size * 0.1, 1)
            if neighbor_count < threshold:
                if neighbor_count == 0:
                    sev = 90.0
                elif neighbor_count < 3:
                    sev = 65.0
                else:
                    sev = 45.0

                isolated.append(
                    {
                        "id": nid,
                        "email": node.email,
                        "team": node.team_id,
                        "department": node.department,
                        "metrics": {
                            "connections": neighbor_count,
                            "team_size": team_size,
                            "degree_centrality": round(degree.get(nid, 0), 4),
                        },
                    }
                )

        if not isolated:
            return None

        worst = max(e["metrics"]["connections"] == 0 for e in isolated)
        overall_severity = 85.0 if worst else 55.0

        return NetworkSignal(
            signal_type="isolated_employees",
            severity=_severity_label(overall_severity),
            severity_score=round(overall_severity, 1),
            affected_entities=sorted(
                isolated, key=lambda e: e["metrics"]["connections"]
            ),
            description=(
                f"{len(isolated)} employee(s) have very few connections relative to "
                f"their team size. "
                f"{sum(1 for e in isolated if e['metrics']['connections'] == 0)} "
                f"have zero connections."
            ),
            recommendation=(
                "Pair isolated employees with mentors or include them in cross-functional "
                "projects. For zero-connection employees, investigate whether they are "
                "new hires (expected) or disengaging (risk)."
            ),
            evidence={
                "total_isolated": len(isolated),
                "zero_connection_count": sum(
                    1 for e in isolated if e["metrics"]["connections"] == 0
                ),
                "threshold": "< 10% of team size",
            },
        )

    # ══════════════════════════════════════════════════════════════════
    # SIGNAL 2: Collaboration Bottlenecks
    # ══════════════════════════════════════════════════════════════════

    def _detect_bottlenecks(
        self,
        adj: Dict[str, Dict[str, float]],
        nodes: Dict[str, NetworkNode],
        betweenness: Dict[str, float],
        **_kw: Any,
    ) -> Optional[NetworkSignal]:
        """Find employees with high betweenness centrality — they sit on many
        shortest paths between other pairs.

        If a node appears on > 30% of shortest paths, it is a bottleneck.
        """
        if not betweenness:
            return None

        threshold = 0.30
        bottlenecks: List[Dict[str, Any]] = []
        for nid, bc in betweenness.items():
            if bc > threshold and nid in nodes:
                node = nodes[nid]
                bottlenecks.append(
                    {
                        "id": nid,
                        "email": node.email,
                        "team": node.team_id,
                        "department": node.department,
                        "metrics": {
                            "betweenness_centrality": round(bc, 4),
                            "connections": len(adj.get(nid, {})),
                        },
                    }
                )

        if not bottlenecks:
            return None

        peak_bc = max(e["metrics"]["betweenness_centrality"] for e in bottlenecks)
        severity = min(100, peak_bc * 150)  # 0.30 -> 45, 0.66 -> ~100

        return NetworkSignal(
            signal_type="collaboration_bottlenecks",
            severity=_severity_label(severity),
            severity_score=round(severity, 1),
            affected_entities=sorted(
                bottlenecks,
                key=lambda e: e["metrics"]["betweenness_centrality"],
                reverse=True,
            ),
            description=(
                f"{len(bottlenecks)} employee(s) sit on a disproportionate number of "
                f"communication paths. Removing any of them would fragment collaboration "
                f"flows significantly."
            ),
            recommendation=(
                "Reduce single-point-of-failure risk by creating redundant communication "
                "channels. Pair bottleneck employees with deputies who can handle the same "
                "cross-team coordination. Review whether organizational structure forces "
                "all decisions through these individuals."
            ),
            evidence={
                "threshold": f"betweenness > {threshold}",
                "peak_betweenness": round(peak_bc, 4),
                "count": len(bottlenecks),
            },
        )

    # ══════════════════════════════════════════════════════════════════
    # SIGNAL 3: Overloaded Connectors
    # ══════════════════════════════════════════════════════════════════

    def _detect_overloaded_connectors(
        self,
        adj: Dict[str, Dict[str, float]],
        nodes: Dict[str, NetworkNode],
        degree: Dict[str, float],
        **_kw: Any,
    ) -> Optional[NetworkSignal]:
        """Find employees with extremely high degree centrality AND high edge
        weight sum.

        Different from bottleneck: this is about volume, not structural position.
        Threshold: connections to > 40% of org AND total interaction weight in top 5%.
        """
        n = len(nodes)
        if n < 5:
            return None

        degree_threshold = 0.40

        # Compute total interaction weight per node
        weight_sums: Dict[str, float] = {}
        for nid in nodes:
            weight_sums[nid] = sum(adj.get(nid, {}).values())

        if not weight_sums:
            return None

        sorted_weights = sorted(weight_sums.values(), reverse=True)
        top5_cutoff_idx = max(1, int(len(sorted_weights) * 0.05))
        weight_threshold = sorted_weights[min(top5_cutoff_idx, len(sorted_weights) - 1)]

        overloaded: List[Dict[str, Any]] = []
        for nid, node in nodes.items():
            dc = degree.get(nid, 0)
            ws = weight_sums.get(nid, 0)
            if dc > degree_threshold and ws >= weight_threshold:
                overloaded.append(
                    {
                        "id": nid,
                        "email": node.email,
                        "team": node.team_id,
                        "department": node.department,
                        "metrics": {
                            "degree_centrality": round(dc, 4),
                            "total_interaction_weight": round(ws, 2),
                            "connection_count": len(adj.get(nid, {})),
                            "org_size": n,
                        },
                    }
                )

        if not overloaded:
            return None

        peak_degree = max(e["metrics"]["degree_centrality"] for e in overloaded)
        severity = min(100, peak_degree * 120 + len(overloaded) * 5)

        return NetworkSignal(
            signal_type="overloaded_connectors",
            severity=_severity_label(severity),
            severity_score=round(severity, 1),
            affected_entities=sorted(
                overloaded,
                key=lambda e: e["metrics"]["total_interaction_weight"],
                reverse=True,
            ),
            description=(
                f"{len(overloaded)} employee(s) are connected to over 40% of the "
                f"organization AND carry extremely high interaction volume. "
                f"Risk: burnout and single point of failure."
            ),
            recommendation=(
                "Redistribute coordination responsibilities. Audit whether these "
                "individuals are pulled into meetings/threads by necessity or habit. "
                "Assign communication deputies and establish direct channels between "
                "teams that currently route through overloaded connectors."
            ),
            evidence={
                "degree_threshold": degree_threshold,
                "weight_percentile_cutoff": "top 5%",
                "peak_degree": round(peak_degree, 4),
                "count": len(overloaded),
            },
        )

    # ══════════════════════════════════════════════════════════════════
    # SIGNAL 4: Non-Interacting Teams (Silos)
    # ══════════════════════════════════════════════════════════════════

    def _detect_team_silos(
        self,
        adj: Dict[str, Dict[str, float]],
        nodes: Dict[str, NetworkNode],
        **_kw: Any,
    ) -> Optional[NetworkSignal]:
        """Find team pairs with zero or near-zero cross-team edges.

        For each team pair, compute:
        cross_edges / (team_a_size * team_b_size) = interaction density.
        Flag if density < 0.02 for teams in the same department.
        """
        teams: Dict[str, List[str]] = defaultdict(list)
        team_dept: Dict[str, Optional[str]] = {}
        for nid, node in nodes.items():
            if node.team_id:
                teams[node.team_id].append(nid)
                if node.team_id not in team_dept:
                    team_dept[node.team_id] = node.department

        team_ids = list(teams.keys())
        if len(team_ids) < 2:
            return None

        silo_pairs: List[Dict[str, Any]] = []
        for i in range(len(team_ids)):
            for j in range(i + 1, len(team_ids)):
                ta, tb = team_ids[i], team_ids[j]
                members_a = set(teams[ta])
                members_b = set(teams[tb])

                # Count cross-team edges
                cross_edges = 0
                cross_weight = 0.0
                for nid in members_a:
                    for neighbor, w in adj.get(nid, {}).items():
                        if neighbor in members_b:
                            cross_edges += 1
                            cross_weight += w

                max_possible = len(members_a) * len(members_b)
                density = cross_edges / max_possible if max_possible > 0 else 0.0

                # Flag low-density pairs, especially same-department
                same_dept = team_dept.get(ta) is not None and team_dept.get(
                    ta
                ) == team_dept.get(tb)
                threshold = 0.02 if same_dept else 0.01

                if density < threshold:
                    silo_pairs.append(
                        {
                            "id": f"{ta}--{tb}",
                            "team_a": ta,
                            "team_b": tb,
                            "metrics": {
                                "cross_edge_count": cross_edges,
                                "interaction_density": round(density, 4),
                                "team_a_size": len(members_a),
                                "team_b_size": len(members_b),
                                "same_department": same_dept,
                                "cross_weight": round(cross_weight, 2),
                            },
                        }
                    )

        if not silo_pairs:
            return None

        same_dept_silos = sum(1 for p in silo_pairs if p["metrics"]["same_department"])
        severity = min(
            100,
            30 + same_dept_silos * 20 + len(silo_pairs) * 3,
        )

        return NetworkSignal(
            signal_type="non_interacting_teams",
            severity=_severity_label(severity),
            severity_score=round(severity, 1),
            affected_entities=sorted(
                silo_pairs,
                key=lambda e: (
                    e["metrics"]["same_department"],
                    -e["metrics"]["interaction_density"],
                ),
                reverse=True,
            ),
            description=(
                f"{len(silo_pairs)} team pair(s) have near-zero cross-team interaction. "
                f"{same_dept_silos} of these are within the same department, suggesting "
                f"structural silos that may impede knowledge sharing."
            ),
            recommendation=(
                "Introduce cross-team rituals: shared standups, joint retrospectives, "
                "or rotation programs. For same-department silos, investigate whether "
                "teams have redundant responsibilities or competing priorities."
            ),
            evidence={
                "silo_pair_count": len(silo_pairs),
                "same_department_silos": same_dept_silos,
                "density_threshold": 0.02,
            },
        )

    # ══════════════════════════════════════════════════════════════════
    # SIGNAL 5: Excessive Cross-Team Dependency
    # ══════════════════════════════════════════════════════════════════

    def _detect_excessive_cross_team(
        self,
        adj: Dict[str, Dict[str, float]],
        nodes: Dict[str, NetworkNode],
        **_kw: Any,
    ) -> Optional[NetworkSignal]:
        """Find teams where > 60% of edges go outside the team boundary.

        This suggests unclear team boundaries or misaligned responsibilities.
        """
        teams: Dict[str, Set[str]] = defaultdict(set)
        for nid, node in nodes.items():
            if node.team_id:
                teams[node.team_id].add(nid)

        if not teams:
            return None

        excessive: List[Dict[str, Any]] = []
        for tid, members in teams.items():
            if len(members) < 2:
                continue

            internal_edges = 0
            external_edges = 0
            for nid in members:
                for neighbor in adj.get(nid, {}):
                    if neighbor in members:
                        internal_edges += 1
                    else:
                        external_edges += 1

            # Each internal edge counted twice (both endpoints in set)
            internal_edges //= 2
            total = internal_edges + external_edges
            if total == 0:
                continue

            external_ratio = external_edges / total
            if external_ratio > 0.60:
                excessive.append(
                    {
                        "id": tid,
                        "team": tid,
                        "metrics": {
                            "external_edge_ratio": round(external_ratio, 3),
                            "internal_edges": internal_edges,
                            "external_edges": external_edges,
                            "team_size": len(members),
                        },
                    }
                )

        if not excessive:
            return None

        peak_ratio = max(e["metrics"]["external_edge_ratio"] for e in excessive)
        severity = min(100, peak_ratio * 100 + len(excessive) * 5)

        return NetworkSignal(
            signal_type="excessive_cross_team_dependency",
            severity=_severity_label(severity),
            severity_score=round(severity, 1),
            affected_entities=sorted(
                excessive,
                key=lambda e: e["metrics"]["external_edge_ratio"],
                reverse=True,
            ),
            description=(
                f"{len(excessive)} team(s) have more than 60% of their collaboration "
                f"edges going outside the team boundary. This may indicate misaligned "
                f"team structure or unclear ownership."
            ),
            recommendation=(
                "Review team charters and responsibility boundaries. Consider whether "
                "heavily cross-dependent teams should be merged, restructured, or given "
                "explicit shared ownership. Excessive external dependency erodes team "
                "identity and slows decision-making."
            ),
            evidence={
                "threshold": "external_ratio > 0.60",
                "peak_external_ratio": round(peak_ratio, 3),
                "count": len(excessive),
            },
        )

    # ══════════════════════════════════════════════════════════════════
    # SIGNAL 6: Communication Concentration
    # ══════════════════════════════════════════════════════════════════

    def _detect_communication_concentration(
        self,
        adj: Dict[str, Dict[str, float]],
        nodes: Dict[str, NetworkNode],
        edges: List[NetworkEdge],
        **_kw: Any,
    ) -> Optional[NetworkSignal]:
        """Measure Gini coefficient of edge weights within each team.

        If Gini > 0.6, communication is highly concentrated among a few members.
        Risk: knowledge loss if key communicators leave, exclusion of quieter members.
        """
        teams: Dict[str, Set[str]] = defaultdict(set)
        for nid, node in nodes.items():
            if node.team_id:
                teams[node.team_id].add(nid)

        concentrated: List[Dict[str, Any]] = []
        for tid, members in teams.items():
            if len(members) < 3:
                continue

            # Collect per-member total interaction weight within the team
            member_weights: List[float] = []
            for nid in members:
                w = 0.0
                for neighbor, edge_w in adj.get(nid, {}).items():
                    if neighbor in members:
                        w += edge_w
                member_weights.append(w)

            if sum(member_weights) == 0:
                continue

            gini = self._gini_coefficient(member_weights)
            if gini > 0.6:
                # Find the top communicator
                member_list = list(members)
                sorted_by_weight = sorted(
                    zip(member_list, member_weights),
                    key=lambda x: x[1],
                    reverse=True,
                )
                top_id, top_weight = sorted_by_weight[0]
                total_weight = sum(member_weights)
                concentrated.append(
                    {
                        "id": tid,
                        "team": tid,
                        "metrics": {
                            "gini_coefficient": round(gini, 3),
                            "team_size": len(members),
                            "top_communicator": top_id,
                            "top_share": round(
                                top_weight / total_weight if total_weight else 0, 3
                            ),
                        },
                    }
                )

        if not concentrated:
            return None

        peak_gini = max(e["metrics"]["gini_coefficient"] for e in concentrated)
        severity = min(100, peak_gini * 100 + len(concentrated) * 5)

        return NetworkSignal(
            signal_type="communication_concentration",
            severity=_severity_label(severity),
            severity_score=round(severity, 1),
            affected_entities=sorted(
                concentrated,
                key=lambda e: e["metrics"]["gini_coefficient"],
                reverse=True,
            ),
            description=(
                f"{len(concentrated)} team(s) show highly concentrated communication "
                f"patterns (Gini > 0.6). A small number of members carry most of the "
                f"interaction load, creating knowledge-loss and inclusion risks."
            ),
            recommendation=(
                "Rotate meeting facilitation and documentation duties. Create structured "
                "round-robin formats (e.g., each team member leads a weekly update). "
                "Investigate whether quieter members are excluded or self-selecting out."
            ),
            evidence={
                "gini_threshold": 0.6,
                "peak_gini": round(peak_gini, 3),
                "count": len(concentrated),
            },
        )

    # ══════════════════════════════════════════════════════════════════
    # SIGNAL 7: Emerging Informal Leaders
    # ══════════════════════════════════════════════════════════════════

    def _detect_informal_leaders(
        self,
        adj: Dict[str, Dict[str, float]],
        nodes: Dict[str, NetworkNode],
        eigenvector: Dict[str, float],
        **_kw: Any,
    ) -> Optional[NetworkSignal]:
        """Find non-managers with high eigenvector centrality.

        Eigenvector centrality measures connection to other well-connected people.
        Non-managers in the top 10% are informal leaders — a positive signal
        useful for succession planning.
        """
        if not eigenvector:
            return None

        sorted_ev = sorted(eigenvector.values(), reverse=True)
        if not sorted_ev:
            return None

        top10_idx = max(1, int(len(sorted_ev) * 0.10))
        top10_threshold = sorted_ev[min(top10_idx, len(sorted_ev) - 1)]

        # Treat "member" / "regular" roles as non-manager
        manager_roles = {"owner", "admin", "manager", "lead", "director", "vp"}

        leaders: List[Dict[str, Any]] = []
        for nid, node in nodes.items():
            ev = eigenvector.get(nid, 0)
            role_lower = (node.role or "").lower()
            is_manager = role_lower in manager_roles
            if ev >= top10_threshold and not is_manager:
                leaders.append(
                    {
                        "id": nid,
                        "email": node.email,
                        "team": node.team_id,
                        "department": node.department,
                        "role": node.role,
                        "metrics": {
                            "eigenvector_centrality": round(ev, 4),
                            "connections": len(adj.get(nid, {})),
                        },
                    }
                )

        if not leaders:
            return None

        # This is an INFO-level signal — positive insight, not a problem
        severity = 25.0  # always "info"

        return NetworkSignal(
            signal_type="emerging_informal_leaders",
            severity="info",
            severity_score=round(severity, 1),
            affected_entities=sorted(
                leaders,
                key=lambda e: e["metrics"]["eigenvector_centrality"],
                reverse=True,
            ),
            description=(
                f"{len(leaders)} non-manager employee(s) have high eigenvector centrality "
                f"— they are well-connected to other well-connected people. These are "
                f"informal organizational leaders."
            ),
            recommendation=(
                "Leverage these individuals as change champions, mentors, or candidates "
                "for leadership development programs. Their influence is organic and "
                "authentic — formalizing it can amplify positive culture."
            ),
            evidence={
                "percentile_threshold": "top 10%",
                "centrality_cutoff": round(top10_threshold, 4),
                "count": len(leaders),
            },
        )

    # ══════════════════════════════════════════════════════════════════
    # SIGNAL 8: Organizational Silos
    # ══════════════════════════════════════════════════════════════════

    def _detect_org_silos(
        self,
        adj: Dict[str, Dict[str, float]],
        nodes: Dict[str, NetworkNode],
        **_kw: Any,
    ) -> Optional[NetworkSignal]:
        """Detect department-level silos using community detection.

        Run label propagation to find emergent communities. Compare with actual
        department boundaries. If detected communities match departments with
        > 80% overlap AND inter-department edge density < 0.05, the org has
        structural silos.
        """
        # Need departments for comparison
        dept_members: Dict[str, Set[str]] = defaultdict(set)
        for nid, node in nodes.items():
            dept = node.department or "__unknown__"
            dept_members[dept].append(nid) if False else dept_members[dept].add(nid)

        known_depts = {d for d in dept_members if d != "__unknown__"}
        if len(known_depts) < 2:
            return None

        # Run label propagation community detection
        communities = self._label_propagation(adj)
        if not communities:
            return None

        # Group by detected community
        comm_members: Dict[int, Set[str]] = defaultdict(set)
        for nid, comm_id in communities.items():
            comm_members[comm_id].add(nid)

        # Measure overlap: for each community, find best-matching department
        high_overlap_count = 0
        silo_details: List[Dict[str, Any]] = []

        for comm_id, c_members in comm_members.items():
            if len(c_members) < 2:
                continue
            best_dept = None
            best_overlap = 0.0
            for dept, d_members in dept_members.items():
                if dept == "__unknown__":
                    continue
                intersection = len(c_members & d_members)
                union = len(c_members | d_members)
                jaccard = intersection / union if union > 0 else 0
                if jaccard > best_overlap:
                    best_overlap = jaccard
                    best_dept = dept

            if best_overlap > 0.80:
                high_overlap_count += 1

        # Inter-department edge density
        dept_list = list(known_depts)
        low_density_pairs: List[Dict[str, Any]] = []
        for i in range(len(dept_list)):
            for j in range(i + 1, len(dept_list)):
                da, db = dept_list[i], dept_list[j]
                ma, mb = dept_members[da], dept_members[db]
                cross = 0
                for nid in ma:
                    for neighbor in adj.get(nid, {}):
                        if neighbor in mb:
                            cross += 1
                max_possible = len(ma) * len(mb)
                density = cross / max_possible if max_possible > 0 else 0.0
                if density < 0.05:
                    low_density_pairs.append(
                        {
                            "department_a": da,
                            "department_b": db,
                            "interaction_density": round(density, 4),
                            "cross_edges": cross,
                        }
                    )

        # Determine if org-level silos exist
        total_communities = len([c for c in comm_members.values() if len(c) >= 2])
        overlap_ratio = (
            high_overlap_count / total_communities if total_communities > 0 else 0
        )
        has_silos = overlap_ratio > 0.80 and len(low_density_pairs) > 0

        if not has_silos:
            return None

        severity = min(100, 40 + len(low_density_pairs) * 10 + overlap_ratio * 20)

        affected = [
            {
                "id": pair["department_a"] + "--" + pair["department_b"],
                "department_a": pair["department_a"],
                "department_b": pair["department_b"],
                "metrics": {
                    "interaction_density": pair["interaction_density"],
                    "cross_edges": pair["cross_edges"],
                },
            }
            for pair in low_density_pairs
        ]

        return NetworkSignal(
            signal_type="organizational_silos",
            severity=_severity_label(severity),
            severity_score=round(severity, 1),
            affected_entities=affected,
            description=(
                f"Detected communities align closely with department boundaries "
                f"({round(overlap_ratio * 100)}% overlap), and {len(low_density_pairs)} "
                f"department pair(s) have inter-department edge density below 5%. "
                f"This indicates structural organizational silos."
            ),
            recommendation=(
                "Create cross-department initiatives: guilds, communities of practice, "
                "or rotation programs. Evaluate whether leadership incentives reward "
                "department-level metrics over organization-level outcomes. Consider "
                "cross-functional product/project teams."
            ),
            evidence={
                "community_department_overlap": round(overlap_ratio, 3),
                "low_density_pair_count": len(low_density_pairs),
                "density_threshold": 0.05,
                "department_pairs": low_density_pairs,
            },
        )

    # ══════════════════════════════════════════════════════════════════
    # GRAPH UTILITIES (pure Python, no networkx)
    # ══════════════════════════════════════════════════════════════════

    def _build_adjacency(self, edges: List[NetworkEdge]) -> Dict[str, Dict[str, float]]:
        """Build weighted adjacency dict from edges. Undirected: both directions stored."""
        adj: Dict[str, Dict[str, float]] = defaultdict(dict)
        for e in edges:
            # Accumulate weights for multi-edges between same pair
            adj[e.source][e.target] = adj[e.source].get(e.target, 0) + e.weight
            adj[e.target][e.source] = adj[e.target].get(e.source, 0) + e.weight
        return dict(adj)

    def _degree_centrality(
        self, adj: Dict[str, Dict[str, float]], n: int
    ) -> Dict[str, float]:
        """Compute normalized degree centrality for all nodes."""
        max_degree = max(n - 1, 1)
        return {nid: len(neighbors) / max_degree for nid, neighbors in adj.items()}

    def _betweenness_centrality_sample(
        self,
        adj: Dict[str, Dict[str, float]],
        sample_size: int = 50,
    ) -> Dict[str, float]:
        """Approximate betweenness centrality using BFS from sampled source nodes.

        Uses Brandes' algorithm with optional sampling for large graphs.
        """
        all_nodes = list(adj.keys())
        n = len(all_nodes)
        if n < 3:
            return {nid: 0.0 for nid in all_nodes}

        betweenness: Dict[str, float] = {nid: 0.0 for nid in all_nodes}

        # Sample sources for performance
        if n > sample_size:
            sources = random.sample(all_nodes, sample_size)
        else:
            sources = all_nodes

        for s in sources:
            # BFS (Brandes)
            stack: List[str] = []
            pred: Dict[str, List[str]] = {nid: [] for nid in all_nodes}
            sigma: Dict[str, float] = {nid: 0.0 for nid in all_nodes}
            dist: Dict[str, int] = {nid: -1 for nid in all_nodes}
            sigma[s] = 1.0
            dist[s] = 0

            queue: deque[str] = deque([s])
            while queue:
                v = queue.popleft()
                stack.append(v)
                for w in adj.get(v, {}):
                    if dist[w] < 0:
                        dist[w] = dist[v] + 1
                        queue.append(w)
                    if dist[w] == dist[v] + 1:
                        sigma[w] += sigma[v]
                        pred[w].append(v)

            # Back-propagation
            delta: Dict[str, float] = {nid: 0.0 for nid in all_nodes}
            while stack:
                w = stack.pop()
                for v in pred[w]:
                    if sigma[w] > 0:
                        delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
                if w != s:
                    betweenness[w] += delta[w]

        # Normalize
        scale = 1.0 / max((n - 1) * (n - 2), 1) if n > 2 else 1.0
        if len(sources) < n:
            scale *= n / len(sources)

        return {nid: betweenness[nid] * scale for nid in all_nodes}

    def _eigenvector_centrality(
        self,
        adj: Dict[str, Dict[str, float]],
        iterations: int = 100,
        tol: float = 1e-6,
    ) -> Dict[str, float]:
        """Power iteration for eigenvector centrality.

        Nodes connected to other high-centrality nodes get higher scores.
        """
        all_nodes = list(adj.keys())
        n = len(all_nodes)
        if n == 0:
            return {}

        # Initialize uniformly
        x: Dict[str, float] = {nid: 1.0 / n for nid in all_nodes}

        for _ in range(iterations):
            x_new: Dict[str, float] = {nid: 0.0 for nid in all_nodes}
            for nid in all_nodes:
                for neighbor, weight in adj.get(nid, {}).items():
                    if neighbor in x_new:
                        x_new[neighbor] += x[nid] * weight

            # Normalize to unit vector
            norm = math.sqrt(sum(v * v for v in x_new.values()))
            if norm == 0:
                return {nid: 0.0 for nid in all_nodes}
            x_new = {nid: v / norm for nid, v in x_new.items()}

            # Check convergence
            diff = sum(abs(x_new[nid] - x.get(nid, 0)) for nid in all_nodes)
            x = x_new
            if diff < tol:
                break

        return x

    def _gini_coefficient(self, values: List[float]) -> float:
        """Compute Gini coefficient. 0 = perfectly equal, 1 = maximally concentrated."""
        if not values or len(values) < 2:
            return 0.0

        sorted_vals = sorted(values)
        n = len(sorted_vals)
        total = sum(sorted_vals)
        if total == 0:
            return 0.0

        cumulative = sum((2 * i - n + 1) * v for i, v in enumerate(sorted_vals))
        return max(0.0, min(1.0, cumulative / (n * total)))

    def _label_propagation(self, adj: Dict[str, Dict[str, float]]) -> Dict[str, int]:
        """Simple label propagation community detection.

        Each node starts with its own label. Iteratively, each node adopts the
        most common label among its neighbors (weighted). Converges when no
        labels change.
        """
        all_nodes = list(adj.keys())
        if not all_nodes:
            return {}

        # Initialize: each node is its own community
        labels: Dict[str, int] = {nid: i for i, nid in enumerate(all_nodes)}

        max_iterations = 30
        for _ in range(max_iterations):
            changed = False
            # Process nodes in random order to avoid ordering bias
            order = list(all_nodes)
            random.shuffle(order)

            for nid in order:
                neighbors = adj.get(nid, {})
                if not neighbors:
                    continue

                # Weighted vote from neighbors
                label_weights: Dict[int, float] = defaultdict(float)
                for neighbor, weight in neighbors.items():
                    label_weights[labels[neighbor]] += weight

                if not label_weights:
                    continue

                best_label = max(label_weights, key=lambda lbl: label_weights[lbl])
                if labels[nid] != best_label:
                    labels[nid] = best_label
                    changed = True

            if not changed:
                break

        return labels

    def _build_team_interaction_matrix(
        self,
        adj: Dict[str, Dict[str, float]],
        nodes: Dict[str, NetworkNode],
    ) -> Dict[str, Dict[str, float]]:
        """Compute cross-team interaction density matrix.

        Returns: {team_a: {team_b: normalized_interaction_strength}}
        """
        teams: Dict[str, Set[str]] = defaultdict(set)
        for nid, node in nodes.items():
            if node.team_id:
                teams[node.team_id].add(nid)

        team_ids = list(teams.keys())
        matrix: Dict[str, Dict[str, float]] = {
            t: {t2: 0.0 for t2 in team_ids} for t in team_ids
        }

        for nid, neighbors in adj.items():
            node = nodes.get(nid)
            if not node or not node.team_id:
                continue
            src_team = node.team_id
            for neighbor, weight in neighbors.items():
                nb_node = nodes.get(neighbor)
                if not nb_node or not nb_node.team_id:
                    continue
                tgt_team = nb_node.team_id
                if src_team in matrix and tgt_team in matrix.get(src_team, {}):
                    matrix[src_team][tgt_team] += weight

        # Normalize by team size product
        for ta in team_ids:
            for tb in team_ids:
                size_product = len(teams[ta]) * len(teams[tb])
                if size_product > 0 and ta != tb:
                    matrix[ta][tb] = round(matrix[ta][tb] / size_product, 4)
                elif ta == tb and len(teams[ta]) > 1:
                    max_internal = len(teams[ta]) * (len(teams[ta]) - 1)
                    matrix[ta][tb] = (
                        round(matrix[ta][tb] / max_internal, 4)
                        if max_internal > 0
                        else 0.0
                    )

        return matrix

    def _network_health_score(self, signals: List[NetworkSignal]) -> float:
        """Composite health score: 100 - weighted severity of all signals.

        Each signal type has a maximum contribution to the penalty.
        Info signals barely penalize; critical signals penalize heavily.
        """
        if not signals:
            return 100.0

        severity_weights = {
            "critical": 1.0,
            "warning": 0.5,
            "info": 0.05,
        }

        # Cap total penalty from any single signal type at 20 points
        per_signal_cap = 20.0
        total_penalty = 0.0

        for signal in signals:
            weight = severity_weights.get(signal.severity, 0.3)
            raw_penalty = signal.severity_score * weight * 0.2
            total_penalty += min(raw_penalty, per_signal_cap)

        return round(max(0.0, min(100.0, 100.0 - total_penalty)), 1)
