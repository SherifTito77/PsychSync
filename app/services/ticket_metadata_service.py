"""
Ticket Queue Metadata Service

Detects toxic work patterns from ticket/issue METADATA ONLY:
  - Reassignment chains ("hot potato" — work dumped on one person)
  - Work exclusion (tickets bounced away from specific people)
  - Resolution time asymmetry (some people's tickets deprioritized)
  - Ticket dumping (disproportionate assignment to one team member)

Uses only ticket state changes, assignee fields, and timestamps.
NEVER reads ticket descriptions, comments, or attachments.

Data sources: Jira REST API, ServiceNow API, Linear API
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
class TicketMetadataRecord:
    """One ticket's metadata — no description, comments, or content."""

    ticket_id: str
    ticket_key: str  # e.g., "PROJ-123"
    created_at: datetime
    resolved_at: Optional[datetime]
    status: str  # open, in_progress, resolved, closed
    priority: str  # critical, high, medium, low
    assignee_email: Optional[str]
    reporter_email: Optional[str]
    team_id: Optional[str]
    assignment_history: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {"assignee": str, "timestamp": str, "from": Optional[str]}
    reassignment_count: int = 0
    resolution_hours: Optional[float] = None


@dataclass
class TicketToxicitySignals:
    """Toxicity signals from ticket queue patterns."""

    # Hot potato detection
    avg_reassignments: float
    hot_potato_tickets: int
    hot_potato_score: float

    # Dumping ground detection
    dumping_score: float

    # Resolution asymmetry
    avg_resolution_hours: float
    resolution_asymmetry_score: float

    # Bounce-away (exclusion)
    bounce_away_events: int
    bounce_away_score: float

    # Composite
    toxicity_score: float
    risk_label: str

    # Fields with defaults (must come last)
    dump_targets: List[Dict[str, Any]] = field(default_factory=list)
    slowest_assignee: Optional[Dict[str, Any]] = None
    bounce_targets: List[Dict[str, Any]] = field(default_factory=list)
    signals: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class TicketMetadataConnector(ABC):
    """Base for ticket metadata connectors.

    Must NEVER request ticket descriptions, comments, or attachments.
    Only status changes, assignee fields, and timestamps.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_tickets(
        self,
        project_or_team: str,
        start: datetime,
        end: datetime,
    ) -> List[TicketMetadataRecord]: ...


# ══════════════════════════════════════════════════════════════════
# JIRA CONNECTOR
# ══════════════════════════════════════════════════════════════════


class JiraTicketConnector(TicketMetadataConnector):
    """Jira REST API — ticket metadata only.

    Uses /rest/api/3/search with fields limited to:
    status, assignee, reporter, created, resolutiondate, priority.
    Uses /rest/api/3/issue/{id}/changelog for assignment history.
    """

    def __init__(self, base_url: str = "", email: str = "", api_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.base_url and self.api_token),
            "provider": "jira",
            "note": "Ticket metadata only — no descriptions or comments",
        }

    async def fetch_tickets(
        self,
        project_or_team: str,
        start: datetime,
        end: datetime,
    ) -> List[TicketMetadataRecord]:
        if not self.base_url or not self.api_token:
            return []

        records: List[TicketMetadataRecord] = []
        try:
            import httpx
            from base64 import b64encode

            auth = b64encode(f"{self.email}:{self.api_token}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth}",
                "Accept": "application/json",
            }

            start_str = start.strftime("%Y-%m-%d")
            jql = (
                f"project = {project_or_team} "
                f"AND created >= '{start_str}' "
                f"ORDER BY created DESC"
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                start_at = 0
                while True:
                    resp = await client.get(
                        f"{self.base_url}/rest/api/3/search",
                        headers=headers,
                        params={
                            "jql": jql,
                            "fields": "status,assignee,reporter,created,resolutiondate,priority",
                            "maxResults": 100,
                            "startAt": start_at,
                            "expand": "changelog",
                        },
                    )
                    if resp.status_code != 200:
                        break

                    data = resp.json()
                    issues = data.get("issues", [])
                    if not issues:
                        break

                    for issue in issues:
                        record = self._normalize(issue)
                        if record:
                            records.append(record)

                    if start_at + len(issues) >= data.get("total", 0):
                        break
                    start_at += len(issues)

            logger.info("Jira: fetched %d ticket records", len(records))
        except ImportError:
            logger.warning("httpx not installed — Jira connector disabled")
        except Exception as e:
            logger.error("Jira fetch error: %s", e)
        return records

    def _normalize(self, issue: dict) -> Optional[TicketMetadataRecord]:
        try:
            fields = issue.get("fields", {})
            created = datetime.fromisoformat(fields["created"].replace("Z", "+00:00"))
            resolved = None
            resolution_hours = None
            if fields.get("resolutiondate"):
                resolved = datetime.fromisoformat(
                    fields["resolutiondate"].replace("Z", "+00:00")
                )
                resolution_hours = (resolved - created).total_seconds() / 3600

            assignee = (
                fields.get("assignee", {}).get("emailAddress")
                if fields.get("assignee")
                else None
            )
            reporter = (
                fields.get("reporter", {}).get("emailAddress")
                if fields.get("reporter")
                else None
            )

            # Extract assignment history from changelog
            history = []
            reassignments = 0
            changelog = issue.get("changelog", {}).get("histories", [])
            for change in changelog:
                for item in change.get("items", []):
                    if item.get("field") == "assignee":
                        history.append(
                            {
                                "assignee": item.get("toString", ""),
                                "from": item.get("fromString"),
                                "timestamp": change.get("created", ""),
                            }
                        )
                        reassignments += 1

            return TicketMetadataRecord(
                ticket_id=issue["id"],
                ticket_key=issue["key"],
                created_at=created,
                resolved_at=resolved,
                status=fields.get("status", {}).get("name", "Unknown"),
                priority=fields.get("priority", {}).get("name", "Medium"),
                assignee_email=assignee,
                reporter_email=reporter,
                team_id=None,
                assignment_history=history,
                reassignment_count=reassignments,
                resolution_hours=resolution_hours,
            )
        except Exception as e:
            logger.debug("Skipping Jira issue: %s", e)
            return None


# ══════════════════════════════════════════════════════════════════
# SERVICENOW CONNECTOR
# ══════════════════════════════════════════════════════════════════


class ServiceNowTicketConnector(TicketMetadataConnector):
    """ServiceNow Table API — incident metadata only."""

    def __init__(self, instance: str = "", username: str = "", password: str = ""):
        self.instance = instance  # e.g., "company.service-now.com"
        self.username = username
        self.password = password

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.instance and self.username),
            "provider": "servicenow",
            "note": "Incident metadata — no descriptions or worknotes",
        }

    async def fetch_tickets(
        self,
        project_or_team: str,
        start: datetime,
        end: datetime,
    ) -> List[TicketMetadataRecord]:
        if not self.instance:
            return []

        records: List[TicketMetadataRecord] = []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"https://{self.instance}/api/now/table/incident",
                    auth=(self.username, self.password),
                    headers={"Accept": "application/json"},
                    params={
                        "sysparm_query": (
                            f"assignment_group.name={project_or_team}"
                            f"^sys_created_on>{start.strftime('%Y-%m-%d')}"
                        ),
                        "sysparm_fields": (
                            "sys_id,number,state,priority,assigned_to,"
                            "opened_by,sys_created_on,resolved_at,"
                            "reassignment_count"
                        ),
                        "sysparm_limit": 200,
                    },
                )
                if resp.status_code != 200:
                    return []

                for item in resp.json().get("result", []):
                    created = datetime.fromisoformat(
                        item.get("sys_created_on", "").replace(" ", "T")
                    )
                    resolved = None
                    res_hours = None
                    if item.get("resolved_at"):
                        resolved = datetime.fromisoformat(
                            item["resolved_at"].replace(" ", "T")
                        )
                        res_hours = (resolved - created).total_seconds() / 3600

                    records.append(
                        TicketMetadataRecord(
                            ticket_id=item.get("sys_id", ""),
                            ticket_key=item.get("number", ""),
                            created_at=created,
                            resolved_at=resolved,
                            status=item.get("state", ""),
                            priority=item.get("priority", ""),
                            assignee_email=item.get("assigned_to", {}).get("value", ""),
                            reporter_email=item.get("opened_by", {}).get("value", ""),
                            team_id=project_or_team,
                            reassignment_count=int(item.get("reassignment_count", 0)),
                            resolution_hours=res_hours,
                        )
                    )

            logger.info("ServiceNow: fetched %d tickets", len(records))
        except ImportError:
            logger.warning("httpx not installed — ServiceNow connector disabled")
        except Exception as e:
            logger.error("ServiceNow fetch error: %s", e)
        return records


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER
# ══════════════════════════════════════════════════════════════════


class TicketToxicityAnalyzer:
    """Detects toxic work assignment patterns from ticket metadata.

    Three core signals:
    1. Hot potato — tickets bounced 3+ times before landing
    2. Dumping ground — one person gets disproportionate workload
    3. Bounce-away — work systematically moved away from specific people
    """

    def analyze(
        self,
        tickets: List[TicketMetadataRecord],
        days: int = 30,
    ) -> TicketToxicitySignals:
        if not tickets:
            return self._empty_signals()

        hot_potato = self._analyze_hot_potato(tickets)
        dumping = self._analyze_dumping(tickets)
        resolution = self._analyze_resolution_asymmetry(tickets)
        bounce = self._analyze_bounce_away(tickets)

        toxicity = (
            hot_potato["score"] * 0.25
            + dumping["score"] * 0.30
            + resolution["asymmetry_score"] * 0.20
            + bounce["score"] * 0.25
        )

        signals = []
        if hot_potato["count"] > 0:
            signals.append(
                f"{hot_potato['count']} tickets bounced 3+ times before resolution"
            )
        if dumping["targets"]:
            for t in dumping["targets"][:2]:
                signals.append(
                    f"{t['person']} receives {t['ratio']:.1f}x team average ticket load"
                )
        if resolution["asymmetry_score"] > 40:
            signals.append("Resolution time varies significantly by assignee")
        if bounce["events"] > 0:
            signals.append(
                f"Work systematically reassigned away from {len(bounce['targets'])} people"
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

        recs = self._generate_recommendations(hot_potato, dumping, resolution, bounce)

        return TicketToxicitySignals(
            avg_reassignments=round(hot_potato["avg"], 1),
            hot_potato_tickets=hot_potato["count"],
            hot_potato_score=round(hot_potato["score"], 1),
            dumping_score=round(dumping["score"], 1),
            dump_targets=dumping["targets"],
            avg_resolution_hours=round(resolution["avg_hours"], 1),
            resolution_asymmetry_score=round(resolution["asymmetry_score"], 1),
            slowest_assignee=resolution.get("slowest"),
            bounce_away_events=bounce["events"],
            bounce_away_score=round(bounce["score"], 1),
            bounce_targets=bounce["targets"],
            toxicity_score=round(toxicity, 1),
            risk_label=label,
            signals=signals,
            recommendations=recs,
        )

    def _analyze_hot_potato(
        self, tickets: List[TicketMetadataRecord]
    ) -> Dict[str, Any]:
        """Detect tickets bounced between many assignees."""
        reassignments = [t.reassignment_count for t in tickets]
        avg = sum(reassignments) / len(reassignments) if reassignments else 0
        hot_potatoes = sum(1 for r in reassignments if r >= 3)
        score = min(100, hot_potatoes * 10 + max(0, avg - 1) * 20)

        return {"avg": avg, "count": hot_potatoes, "score": score}

    def _analyze_dumping(self, tickets: List[TicketMetadataRecord]) -> Dict[str, Any]:
        """Detect if one person receives disproportionate ticket load."""
        per_person: Dict[str, int] = defaultdict(int)
        for t in tickets:
            if t.assignee_email:
                per_person[t.assignee_email] += 1

        if len(per_person) < 2:
            return {"score": 0, "targets": []}

        counts = list(per_person.values())
        avg_count = sum(counts) / len(counts)

        targets = []
        for person, count in per_person.items():
            ratio = count / max(avg_count, 1)
            if ratio > 1.8:  # >80% above team average
                targets.append(
                    {
                        "person": person,
                        "assigned_count": count,
                        "team_avg": round(avg_count, 1),
                        "ratio": round(ratio, 2),
                    }
                )

        targets.sort(key=lambda x: x["ratio"], reverse=True)
        score = min(
            100, sum((t["ratio"] - 1.5) * 30 for t in targets if t["ratio"] > 1.5)
        )

        return {"score": score, "targets": targets}

    def _analyze_resolution_asymmetry(
        self, tickets: List[TicketMetadataRecord]
    ) -> Dict[str, Any]:
        """Detect if some people's tickets are deprioritized."""
        per_assignee: Dict[str, List[float]] = defaultdict(list)
        for t in tickets:
            if t.resolution_hours is not None and t.assignee_email:
                per_assignee[t.assignee_email].append(t.resolution_hours)

        if not per_assignee:
            return {"avg_hours": 0, "asymmetry_score": 0}

        all_hours = [h for hours in per_assignee.values() for h in hours]
        avg_hours = sum(all_hours) / len(all_hours) if all_hours else 0

        # Per-person averages
        person_avgs = {
            person: sum(hours) / len(hours)
            for person, hours in per_assignee.items()
            if len(hours) >= 2
        }

        if len(person_avgs) < 2:
            return {"avg_hours": avg_hours, "asymmetry_score": 0}

        avgs = list(person_avgs.values())
        mean_avg = sum(avgs) / len(avgs)
        variance = sum((a - mean_avg) ** 2 for a in avgs) / len(avgs)
        asymmetry = min(100, (variance / max(mean_avg**2, 1)) * 200)

        slowest = max(person_avgs, key=person_avgs.get)
        slowest_info = {
            "person": slowest,
            "avg_hours": round(person_avgs[slowest], 1),
            "team_avg_hours": round(avg_hours, 1),
        }

        return {
            "avg_hours": avg_hours,
            "asymmetry_score": asymmetry,
            "slowest": slowest_info,
        }

    def _analyze_bounce_away(
        self, tickets: List[TicketMetadataRecord]
    ) -> Dict[str, Any]:
        """Detect work being systematically moved away from specific people."""
        bounced_from: Dict[str, int] = defaultdict(int)
        bounced_to: Dict[str, int] = defaultdict(int)

        for t in tickets:
            for change in t.assignment_history:
                from_person = change.get("from")
                to_person = change.get("assignee")
                if from_person:
                    bounced_from[from_person] += 1
                if to_person:
                    bounced_to[to_person] += 1

        # Find people who have work taken away disproportionately
        targets = []
        for person, from_count in bounced_from.items():
            to_count = bounced_to.get(person, 0)
            if from_count > to_count + 2 and from_count >= 3:
                targets.append(
                    {
                        "person": person,
                        "bounced_from": from_count,
                        "bounced_to": to_count,
                        "net_loss": from_count - to_count,
                    }
                )

        targets.sort(key=lambda x: x["net_loss"], reverse=True)
        events = sum(t["net_loss"] for t in targets)
        score = min(100, events * 10 + len(targets) * 15)

        return {"events": events, "score": score, "targets": targets}

    def _generate_recommendations(
        self,
        hot_potato: dict,
        dumping: dict,
        resolution: dict,
        bounce: dict,
    ) -> List[str]:
        recs = []
        if hot_potato["score"] > 30:
            recs.append(
                f"{hot_potato['count']} tickets were bounced 3+ times. "
                "Improve ticket triage process and ownership clarity."
            )
        if dumping["targets"]:
            recs.append(
                "Workload dumping detected — some team members receive "
                "disproportionate ticket volume. Review assignment fairness."
            )
        if resolution["asymmetry_score"] > 40:
            recs.append(
                "Resolution time varies significantly by assignee. "
                "Ensure all team members receive equal support and resources."
            )
        if bounce["events"] > 0:
            recs.append(
                "Work is being systematically reassigned away from specific people. "
                "Investigate whether this reflects exclusion or role mismatch."
            )
        if not recs:
            recs.append("Ticket queue patterns look healthy.")
        return recs

    def _empty_signals(self) -> TicketToxicitySignals:
        return TicketToxicitySignals(
            avg_reassignments=0,
            hot_potato_tickets=0,
            hot_potato_score=0,
            dumping_score=0,
            avg_resolution_hours=0,
            resolution_asymmetry_score=0,
            bounce_away_events=0,
            bounce_away_score=0,
            toxicity_score=0,
            risk_label="No Data",
            signals=["No ticket data available."],
        )


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class TicketToxicityRegistry:
    CONNECTOR_TYPES = {
        "jira": JiraTicketConnector,
        "servicenow": ServiceNowTicketConnector,
    }

    def __init__(self):
        self._connectors: Dict[str, TicketMetadataConnector] = {}

    def register(self, name: str, connector: TicketMetadataConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered ticket metadata connector: %s", name)

    def get(self, name: str) -> Optional[TicketMetadataConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


ticket_toxicity_registry = TicketToxicityRegistry()
