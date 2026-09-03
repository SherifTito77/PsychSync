"""
Communication Toxicity Signal Service

Detects interpersonal toxicity from communication METADATA ONLY:
  - Reaction asymmetry (some people's messages consistently ignored)
  - Response latency asymmetry (fast for some, slow for others)
  - CC escalation patterns (trust breakdown = CC-the-boss chains)
  - Attrition clustering (multiple departures from same manager)

Overlays on existing email/Slack metadata infrastructure.
NEVER reads message content. Only metadata: timestamps, counts,
recipient patterns, and reactions.

Data sources: Slack Events API (reactions), Email routing logs,
HRIS departure data
"""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# NORMALIZED SCHEMA
# ══════════════════════════════════════════════════════════════════


@dataclass
class MessageReactionRecord:
    """Reaction metadata for a message — no content."""

    message_id: str
    author_email: str
    channel_id: str
    timestamp: datetime
    reaction_count: int  # total reactions received
    unique_reactors: int  # distinct people who reacted


@dataclass
class ResponseLatencyRecord:
    """Response time between two specific people — no content."""

    responder_email: str
    sender_email: str
    avg_response_minutes: float
    response_count: int  # number of responses measured
    period_start: datetime
    period_end: datetime


@dataclass
class CCEscalationRecord:
    """CC pattern in email thread — metadata only."""

    thread_id: str
    timestamp: datetime
    sender_email: str
    cc_emails: List[str]
    cc_depth: int  # how many layers of CC
    includes_manager: bool


@dataclass
class DepartureRecord:
    """Employee departure — for attrition clustering."""

    employee_email: str
    manager_email: str
    team_id: str
    departure_date: datetime
    tenure_months: float


@dataclass
class CommunicationToxicitySignals:
    """Toxicity signals from communication patterns."""

    # Reaction asymmetry
    reaction_gini: float
    zero_reaction_ratio: float
    reaction_asymmetry_score: float

    # Response latency asymmetry
    response_gini: float
    latency_asymmetry_score: float

    # CC escalation
    cc_escalation_rate: float
    cc_escalation_score: float
    frequent_escalators: int

    # Attrition clustering
    cluster_attrition_events: int
    attrition_cluster_score: float

    # Composite
    toxicity_score: float
    risk_label: str

    # Fields with defaults (must come last)
    most_ignored: Optional[str] = None
    worst_pair: Optional[Dict[str, Any]] = None
    toxic_manager_candidates: List[Dict[str, Any]] = field(default_factory=list)
    signals: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class CommunicationToxicityConnector(ABC):
    """Base for communication toxicity connectors.

    Must NEVER read message content. Only reaction counts, response
    timing, CC patterns, and departure metadata.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_reaction_data(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[MessageReactionRecord]: ...

    @abstractmethod
    async def fetch_response_latencies(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[ResponseLatencyRecord]: ...

    async def fetch_cc_patterns(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[CCEscalationRecord]:
        """Optional: CC escalation from email routing logs."""
        return []

    async def fetch_departures(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[DepartureRecord]:
        """Optional: from HRIS connector."""
        return []


# ══════════════════════════════════════════════════════════════════
# SLACK REACTION CONNECTOR
# ══════════════════════════════════════════════════════════════════


class SlackReactionConnector(CommunicationToxicityConnector):
    """Slack API — reaction counts per message author.

    Uses analytics API for aggregate reaction data and
    conversations.list for channel membership. Never reads messages.
    """

    def __init__(self, bot_token: str = ""):
        self.bot_token = bot_token

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.bot_token),
            "provider": "slack_reactions",
            "scopes": ["admin.analytics:read", "reactions:read"],
            "note": "Reaction counts only — no message content",
        }

    async def fetch_reaction_data(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[MessageReactionRecord]:
        if not self.bot_token:
            return []

        records: List[MessageReactionRecord] = []
        try:
            import httpx
            import json

            async with httpx.AsyncClient(timeout=30.0) as client:
                current = start.date()
                end_date = end.date()

                while current <= end_date:
                    resp = await client.get(
                        "https://slack.com/api/admin.analytics.getFile",
                        headers={"Authorization": f"Bearer {self.bot_token}"},
                        params={"type": "member", "date": current.isoformat()},
                    )

                    if resp.status_code == 200:
                        for line in resp.text.strip().split("\n"):
                            try:
                                row = json.loads(line)
                            except json.JSONDecodeError:
                                continue

                            user_id = row.get("user_id", "")
                            msgs = row.get("messages_posted", 0)
                            reactions = row.get("reactions_added", 0)

                            if msgs > 0:
                                records.append(
                                    MessageReactionRecord(
                                        message_id=f"{current}_{user_id}",
                                        author_email=user_id,
                                        channel_id="aggregate",
                                        timestamp=datetime.combine(
                                            current, datetime.min.time()
                                        ),
                                        reaction_count=reactions,
                                        unique_reactors=0,
                                    )
                                )

                    current += timedelta(days=1)

            logger.info("Slack reactions: fetched %d records", len(records))
        except ImportError:
            logger.warning("httpx not installed — Slack reaction connector disabled")
        except Exception as e:
            logger.error("Slack reaction fetch error: %s", e)
        return records

    async def fetch_response_latencies(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[ResponseLatencyRecord]:
        # Slack analytics doesn't directly provide pairwise response times
        # This would need DM metadata which we avoid for privacy
        return []


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER
# ══════════════════════════════════════════════════════════════════


class CommunicationToxicityAnalyzer:
    """Detects interpersonal toxicity from communication metadata.

    Four core signals:
    1. Reaction asymmetry — some people's messages consistently ignored
    2. Response latency asymmetry — favoritism in response speed
    3. CC escalation — trust breakdown causing excessive CC chains
    4. Attrition clustering — multiple departures from same manager
    """

    def analyze(
        self,
        reactions: List[MessageReactionRecord],
        latencies: List[ResponseLatencyRecord],
        cc_patterns: List[CCEscalationRecord],
        departures: List[DepartureRecord],
    ) -> CommunicationToxicitySignals:
        reaction_analysis = self._analyze_reactions(reactions)
        latency_analysis = self._analyze_latencies(latencies)
        cc_analysis = self._analyze_cc_escalation(cc_patterns)
        attrition_analysis = self._analyze_attrition_clustering(departures)

        toxicity = (
            reaction_analysis["score"] * 0.25
            + latency_analysis["score"] * 0.20
            + cc_analysis["score"] * 0.20
            + attrition_analysis["score"] * 0.35  # strongest signal
        )

        signals = []
        if reaction_analysis["score"] > 40:
            signals.append(
                f"Reaction asymmetry: {reaction_analysis['zero_ratio']*100:.0f}% "
                "of messages receive zero reactions (social exclusion indicator)"
            )
        if latency_analysis["score"] > 40:
            signals.append(
                "Response time asymmetry detected — some people consistently "
                "receive slower responses"
            )
        if cc_analysis["score"] > 40:
            signals.append(
                f"CC escalation rate at {cc_analysis['rate']*100:.0f}% — "
                "indicates trust breakdown"
            )
        if attrition_analysis["clusters"] > 0:
            signals.append(
                f"{attrition_analysis['clusters']} teams have cluster attrition "
                "(2+ departures within 90 days)"
            )

        label = (
            "Critical"
            if toxicity >= 60
            else (
                "Elevated"
                if toxicity >= 35
                else "Monitor" if toxicity >= 15 else "Healthy"
            )
        )

        recs = self._generate_recommendations(
            reaction_analysis, latency_analysis, cc_analysis, attrition_analysis
        )

        return CommunicationToxicitySignals(
            reaction_gini=round(reaction_analysis["gini"], 3),
            zero_reaction_ratio=round(reaction_analysis["zero_ratio"], 3),
            reaction_asymmetry_score=round(reaction_analysis["score"], 1),
            most_ignored=reaction_analysis.get("most_ignored"),
            response_gini=round(latency_analysis["gini"], 3),
            latency_asymmetry_score=round(latency_analysis["score"], 1),
            worst_pair=latency_analysis.get("worst_pair"),
            cc_escalation_rate=round(cc_analysis["rate"], 3),
            cc_escalation_score=round(cc_analysis["score"], 1),
            frequent_escalators=cc_analysis["escalators"],
            cluster_attrition_events=attrition_analysis["clusters"],
            attrition_cluster_score=round(attrition_analysis["score"], 1),
            toxic_manager_candidates=attrition_analysis.get("managers", []),
            toxicity_score=round(toxicity, 1),
            risk_label=label,
            signals=signals,
            recommendations=recs,
        )

    def _analyze_reactions(
        self, reactions: List[MessageReactionRecord]
    ) -> Dict[str, Any]:
        if not reactions:
            return {"score": 0, "gini": 0, "zero_ratio": 0}

        # Per-person average reactions
        per_person: Dict[str, List[int]] = defaultdict(list)
        for r in reactions:
            per_person[r.author_email].append(r.reaction_count)

        person_avgs = {p: sum(counts) / len(counts) for p, counts in per_person.items()}

        if len(person_avgs) < 2:
            return {"score": 0, "gini": 0, "zero_ratio": 0}

        values = sorted(person_avgs.values())
        gini = self._gini_coefficient(values)

        # Zero reaction ratio
        total_messages = len(reactions)
        zero_reaction = sum(1 for r in reactions if r.reaction_count == 0)
        zero_ratio = zero_reaction / max(total_messages, 1)

        # Most ignored person
        most_ignored = min(person_avgs, key=person_avgs.get) if person_avgs else None

        score = min(100, gini * 70 + zero_ratio * 30)

        return {
            "score": score,
            "gini": gini,
            "zero_ratio": zero_ratio,
            "most_ignored": most_ignored,
        }

    def _analyze_latencies(
        self, latencies: List[ResponseLatencyRecord]
    ) -> Dict[str, Any]:
        if not latencies:
            return {"score": 0, "gini": 0}

        # Group by responder→sender pair
        pair_avgs: Dict[Tuple[str, str], float] = {}
        for l in latencies:
            if l.response_count >= 3:
                pair_avgs[(l.responder_email, l.sender_email)] = l.avg_response_minutes

        if len(pair_avgs) < 2:
            return {"score": 0, "gini": 0}

        values = sorted(pair_avgs.values())
        gini = self._gini_coefficient(values)

        # Find worst pair (slowest response)
        worst_key = max(pair_avgs, key=pair_avgs.get)
        worst_pair = {
            "responder": worst_key[0],
            "sender": worst_key[1],
            "avg_minutes": round(pair_avgs[worst_key], 1),
        }

        # Asymmetry: compare fastest to slowest per-responder
        per_responder: Dict[str, List[float]] = defaultdict(list)
        for (responder, _), avg in pair_avgs.items():
            per_responder[responder].append(avg)

        max_ratio = 0
        for times in per_responder.values():
            if len(times) >= 2:
                ratio = max(times) / max(min(times), 1)
                max_ratio = max(max_ratio, ratio)

        score = min(100, gini * 50 + max(0, max_ratio - 2) * 15)

        return {
            "score": score,
            "gini": gini,
            "worst_pair": worst_pair,
        }

    def _analyze_cc_escalation(
        self, cc_patterns: List[CCEscalationRecord]
    ) -> Dict[str, Any]:
        if not cc_patterns:
            return {"score": 0, "rate": 0, "escalators": 0}

        escalations = [c for c in cc_patterns if c.includes_manager]
        rate = len(escalations) / max(len(cc_patterns), 1)

        # Frequent escalators
        escalator_counts: Dict[str, int] = defaultdict(int)
        for c in escalations:
            escalator_counts[c.sender_email] += 1

        frequent = sum(1 for count in escalator_counts.values() if count >= 3)

        # Deep CC chains (>3 CCs) are concerning
        deep_chains = sum(1 for c in cc_patterns if c.cc_depth >= 3)
        deep_ratio = deep_chains / max(len(cc_patterns), 1)

        score = min(100, rate * 60 + deep_ratio * 20 + frequent * 10)

        return {
            "score": score,
            "rate": rate,
            "escalators": frequent,
        }

    def _analyze_attrition_clustering(
        self, departures: List[DepartureRecord]
    ) -> Dict[str, Any]:
        """Detect multiple departures from the same manager within 90 days.

        This is the strongest toxicity confirmation signal. People vote
        with their feet — cluster attrition under one manager almost
        always indicates a toxic environment.
        """
        if not departures:
            return {"score": 0, "clusters": 0, "managers": []}

        # Group by manager
        by_manager: Dict[str, List[DepartureRecord]] = defaultdict(list)
        for d in departures:
            by_manager[d.manager_email].append(d)

        clusters = 0
        toxic_managers = []

        for manager, deps in by_manager.items():
            if len(deps) < 2:
                continue

            # Sort by date
            sorted_deps = sorted(deps, key=lambda d: d.departure_date)

            # Check for 2+ departures within 90 days
            for i in range(len(sorted_deps) - 1):
                gap = (
                    sorted_deps[i + 1].departure_date - sorted_deps[i].departure_date
                ).days
                if gap <= 90:
                    clusters += 1
                    avg_tenure = sum(d.tenure_months for d in deps) / len(deps)
                    toxic_managers.append(
                        {
                            "manager": manager,
                            "departures": len(deps),
                            "avg_tenure_months": round(avg_tenure, 1),
                            "cluster_window_days": gap,
                        }
                    )
                    break  # one cluster per manager

        score = min(
            100, clusters * 30 + sum(m["departures"] * 10 for m in toxic_managers)
        )

        return {
            "score": score,
            "clusters": clusters,
            "managers": sorted(
                toxic_managers, key=lambda m: m["departures"], reverse=True
            ),
        }

    def _gini_coefficient(self, values: List[float]) -> float:
        if not values or sum(values) == 0:
            return 0
        n = len(values)
        sorted_vals = sorted(values)
        cumulative = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(sorted_vals))
        return max(0, cumulative / (n * sum(sorted_vals)))

    def _generate_recommendations(
        self,
        reactions: dict,
        latencies: dict,
        cc: dict,
        attrition: dict,
    ) -> List[str]:
        recs = []
        if reactions["score"] > 40:
            recs.append(
                "Reaction asymmetry indicates social exclusion patterns. "
                "Encourage inclusive engagement norms in channels."
            )
        if latencies["score"] > 40:
            recs.append(
                "Response time varies significantly by person. "
                "This may indicate favoritism or deprioritization of certain colleagues."
            )
        if cc["score"] > 40:
            recs.append(
                "CC escalation rate is high — signals trust breakdown. "
                "Address root causes of defensive communication."
            )
        if attrition.get("clusters", 0) > 0:
            recs.append(
                "Cluster attrition detected under specific managers. "
                "Conduct stay interviews and review management effectiveness."
            )
        if not recs:
            recs.append("Communication patterns look healthy.")
        return recs

    def _empty_signals(self) -> CommunicationToxicitySignals:
        return CommunicationToxicitySignals(
            reaction_gini=0,
            zero_reaction_ratio=0,
            reaction_asymmetry_score=0,
            response_gini=0,
            latency_asymmetry_score=0,
            cc_escalation_rate=0,
            cc_escalation_score=0,
            frequent_escalators=0,
            cluster_attrition_events=0,
            attrition_cluster_score=0,
            toxicity_score=0,
            risk_label="No Data",
            signals=["No communication data available."],
        )


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class CommunicationToxicityRegistry:
    CONNECTOR_TYPES = {"slack": SlackReactionConnector}

    def __init__(self):
        self._connectors: Dict[str, CommunicationToxicityConnector] = {}

    def register(self, name: str, connector: CommunicationToxicityConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered communication toxicity connector: %s", name)

    def get(self, name: str) -> Optional[CommunicationToxicityConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


communication_toxicity_registry = CommunicationToxicityRegistry()
