"""
Work Systems Integration Service

Abstraction layer for connecting to external work management platforms:
  - Jira (Atlassian)
  - Azure DevOps
  - Asana
  - Monday.com

Each connector normalizes work items into a common WorkItem schema, enabling
the Behavioral Intelligence Engine to derive signals like:
  - Workload distribution and overcommitment risk
  - Collaboration patterns from shared tasks
  - Cycle time trends (proxy for team friction)
  - Sprint completion rates (proxy for change readiness)

Connectors are designed to be swappable — the behavioral analysis layer
operates on normalized data regardless of the source system.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# NORMALIZED SCHEMA
# ══════════════════════════════════════════════════════════════════


class WorkItemStatus(str, Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


class WorkItemPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class WorkItem:
    """Normalized work item across all platforms."""

    id: str
    external_id: str
    source: str  # "jira", "azure_devops", "asana", "monday"
    title: str
    status: WorkItemStatus
    priority: WorkItemPriority
    assignee_email: Optional[str] = None
    assignee_name: Optional[str] = None
    reporter_email: Optional[str] = None
    project_key: Optional[str] = None
    sprint_name: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    story_points: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    cycle_time_hours: Optional[float] = None


@dataclass
class SprintMetrics:
    """Aggregated sprint/iteration metrics."""

    sprint_name: str
    total_items: int
    completed_items: int
    completion_rate: float
    avg_cycle_time_hours: float
    carry_over_items: int
    total_story_points: float
    completed_story_points: float


@dataclass
class WorkloadSnapshot:
    """Per-person workload at a point in time."""

    user_email: str
    user_name: str
    open_items: int
    in_progress_items: int
    total_story_points: float
    overdue_items: int
    avg_items_per_sprint: float
    overcommitment_score: float  # 0-100, higher = more overcommitted


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class WorkSystemConnector(ABC):
    """Base interface for all work system connectors."""

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Verify connectivity and credentials."""
        ...

    @abstractmethod
    async def fetch_work_items(
        self,
        project_key: str,
        since: Optional[datetime] = None,
    ) -> List[WorkItem]:
        """Fetch and normalize work items from the external system."""
        ...

    @abstractmethod
    async def fetch_sprint_metrics(
        self,
        project_key: str,
        sprint_count: int = 5,
    ) -> List[SprintMetrics]:
        """Fetch recent sprint/iteration metrics."""
        ...


# ══════════════════════════════════════════════════════════════════
# JIRA CONNECTOR
# ══════════════════════════════════════════════════════════════════


class JiraConnector(WorkSystemConnector):
    """Atlassian Jira Cloud/Server connector."""

    STATUS_MAP = {
        "backlog": WorkItemStatus.BACKLOG,
        "to do": WorkItemStatus.TODO,
        "open": WorkItemStatus.TODO,
        "in progress": WorkItemStatus.IN_PROGRESS,
        "in review": WorkItemStatus.REVIEW,
        "code review": WorkItemStatus.REVIEW,
        "done": WorkItemStatus.DONE,
        "closed": WorkItemStatus.DONE,
        "resolved": WorkItemStatus.DONE,
        "cancelled": WorkItemStatus.CANCELLED,
        "won't do": WorkItemStatus.CANCELLED,
    }

    PRIORITY_MAP = {
        "highest": WorkItemPriority.CRITICAL,
        "critical": WorkItemPriority.CRITICAL,
        "blocker": WorkItemPriority.CRITICAL,
        "high": WorkItemPriority.HIGH,
        "medium": WorkItemPriority.MEDIUM,
        "low": WorkItemPriority.LOW,
        "lowest": WorkItemPriority.LOW,
    }

    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token

    async def test_connection(self) -> Dict[str, Any]:
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/rest/api/3/myself",
                    auth=(self.email, self.api_token),
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "connected": True,
                        "user": data.get("displayName", self.email),
                    }
                return {"connected": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def fetch_work_items(
        self,
        project_key: str,
        since: Optional[datetime] = None,
    ) -> List[WorkItem]:
        items = []
        try:
            import httpx

            jql = f'project = "{project_key}"'
            if since:
                jql += f' AND updated >= "{since.strftime("%Y-%m-%d")}"'
            jql += " ORDER BY updated DESC"

            async with httpx.AsyncClient() as client:
                start_at = 0
                while True:
                    resp = await client.get(
                        f"{self.base_url}/rest/api/3/search",
                        params={"jql": jql, "startAt": start_at, "maxResults": 100},
                        auth=(self.email, self.api_token),
                        timeout=30,
                    )
                    if resp.status_code != 200:
                        logger.error("Jira search failed: %s", resp.text)
                        break

                    data = resp.json()
                    for issue in data.get("issues", []):
                        items.append(self._normalize_issue(issue))

                    if start_at + 100 >= data.get("total", 0):
                        break
                    start_at += 100

        except ImportError:
            logger.warning("httpx not installed — Jira connector disabled")
        except Exception as e:
            logger.error("Jira fetch error: %s", e)

        return items

    async def fetch_sprint_metrics(
        self,
        project_key: str,
        sprint_count: int = 5,
    ) -> List[SprintMetrics]:
        # Would require Jira Agile API (/rest/agile/1.0/board/.../sprint)
        # Returning empty for now — full implementation requires board ID lookup
        return []

    def _normalize_issue(self, issue: dict) -> WorkItem:
        fields = issue.get("fields", {})
        status_name = (fields.get("status", {}).get("name", "")).lower()
        priority_name = (fields.get("priority", {}).get("name", "")).lower()

        assignee = fields.get("assignee") or {}
        reporter = fields.get("reporter") or {}

        created = fields.get("created")
        updated = fields.get("updated")
        resolved = fields.get("resolutiondate")

        cycle_time = None
        if created and resolved:
            try:
                c = datetime.fromisoformat(created.replace("Z", "+00:00"))
                r = datetime.fromisoformat(resolved.replace("Z", "+00:00"))
                cycle_time = (r - c).total_seconds() / 3600
            except (ValueError, TypeError):
                pass

        return WorkItem(
            id=issue.get("id", ""),
            external_id=issue.get("key", ""),
            source="jira",
            title=fields.get("summary", ""),
            status=self.STATUS_MAP.get(status_name, WorkItemStatus.TODO),
            priority=self.PRIORITY_MAP.get(priority_name, WorkItemPriority.MEDIUM),
            assignee_email=assignee.get("emailAddress"),
            assignee_name=assignee.get("displayName"),
            reporter_email=reporter.get("emailAddress"),
            project_key=(
                issue.get("key", "").split("-")[0] if issue.get("key") else None
            ),
            labels=fields.get("labels", []),
            story_points=fields.get("customfield_10016"),  # Common story points field
            created_at=(
                datetime.fromisoformat(created.replace("Z", "+00:00"))
                if created
                else None
            ),
            updated_at=(
                datetime.fromisoformat(updated.replace("Z", "+00:00"))
                if updated
                else None
            ),
            resolved_at=(
                datetime.fromisoformat(resolved.replace("Z", "+00:00"))
                if resolved
                else None
            ),
            cycle_time_hours=cycle_time,
        )


# ══════════════════════════════════════════════════════════════════
# AZURE DEVOPS CONNECTOR
# ══════════════════════════════════════════════════════════════════


class AzureDevOpsConnector(WorkSystemConnector):
    """Azure DevOps connector."""

    STATUS_MAP = {
        "new": WorkItemStatus.TODO,
        "active": WorkItemStatus.IN_PROGRESS,
        "resolved": WorkItemStatus.REVIEW,
        "closed": WorkItemStatus.DONE,
        "removed": WorkItemStatus.CANCELLED,
    }

    def __init__(self, organization: str, project: str, pat: str):
        self.base_url = f"https://dev.azure.com/{organization}/{project}"
        self.pat = pat

    async def test_connection(self) -> Dict[str, Any]:
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/_apis/projects?api-version=7.0",
                    headers={"Authorization": f"Basic {self.pat}"},
                    timeout=10,
                )
                return {"connected": resp.status_code == 200}
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def fetch_work_items(
        self,
        project_key: str,
        since: Optional[datetime] = None,
    ) -> List[WorkItem]:
        # Would use WIQL query API
        return []

    async def fetch_sprint_metrics(
        self,
        project_key: str,
        sprint_count: int = 5,
    ) -> List[SprintMetrics]:
        return []


# ══════════════════════════════════════════════════════════════════
# ASANA CONNECTOR
# ══════════════════════════════════════════════════════════════════


class AsanaConnector(WorkSystemConnector):
    """Asana connector."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://app.asana.com/api/1.0"

    async def test_connection(self) -> Dict[str, Any]:
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/users/me",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10,
                )
                if resp.status_code == 200:
                    return {
                        "connected": True,
                        "user": resp.json().get("data", {}).get("name"),
                    }
                return {"connected": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def fetch_work_items(
        self,
        project_key: str,
        since: Optional[datetime] = None,
    ) -> List[WorkItem]:
        return []

    async def fetch_sprint_metrics(
        self,
        project_key: str,
        sprint_count: int = 5,
    ) -> List[SprintMetrics]:
        return []


# ══════════════════════════════════════════════════════════════════
# MONDAY.COM CONNECTOR
# ══════════════════════════════════════════════════════════════════


class MondayConnector(WorkSystemConnector):
    """Monday.com connector."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.monday.com/v2"

    async def test_connection(self) -> Dict[str, Any]:
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.base_url,
                    json={"query": "{ me { name email } }"},
                    headers={"Authorization": self.api_key},
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {}).get("me", {})
                    return {"connected": True, "user": data.get("name")}
                return {"connected": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def fetch_work_items(
        self,
        project_key: str,
        since: Optional[datetime] = None,
    ) -> List[WorkItem]:
        return []

    async def fetch_sprint_metrics(
        self,
        project_key: str,
        sprint_count: int = 5,
    ) -> List[SprintMetrics]:
        return []


# ══════════════════════════════════════════════════════════════════
# CONNECTOR REGISTRY
# ══════════════════════════════════════════════════════════════════


class WorkSystemsRegistry:
    """Manages configured work system connectors."""

    CONNECTOR_TYPES = {
        "jira": JiraConnector,
        "azure_devops": AzureDevOpsConnector,
        "asana": AsanaConnector,
        "monday": MondayConnector,
    }

    def __init__(self):
        self._connectors: Dict[str, WorkSystemConnector] = {}

    def register(self, name: str, connector: WorkSystemConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered work system connector: %s", name)

    def get(self, name: str) -> Optional[WorkSystemConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, Any]]:
        return [
            {"name": name, "type": type(conn).__name__, "source": name}
            for name, conn in self._connectors.items()
        ]

    async def test_all(self) -> Dict[str, Dict[str, Any]]:
        results = {}
        for name, conn in self._connectors.items():
            results[name] = await conn.test_connection()
        return results


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL SIGNAL EXTRACTION
# ══════════════════════════════════════════════════════════════════


class WorkSystemBehavioralAnalyzer:
    """Extracts behavioral signals from normalized work items."""

    def analyze_workload(self, items: List[WorkItem]) -> List[WorkloadSnapshot]:
        """Calculate per-person workload metrics."""
        by_person: Dict[str, List[WorkItem]] = {}
        for item in items:
            key = item.assignee_email or item.assignee_name or "unassigned"
            if key not in by_person:
                by_person[key] = []
            by_person[key].append(item)

        snapshots = []
        for email, person_items in by_person.items():
            if email == "unassigned":
                continue

            open_items = [
                i
                for i in person_items
                if i.status in (WorkItemStatus.TODO, WorkItemStatus.BACKLOG)
            ]
            in_progress = [
                i for i in person_items if i.status == WorkItemStatus.IN_PROGRESS
            ]
            total_sp = sum(
                i.story_points or 0
                for i in person_items
                if i.status != WorkItemStatus.DONE
            )

            # Overcommitment: > 10 open items or > 30 story points is high
            overcommitment = min(
                100, (len(open_items) / 10) * 50 + (total_sp / 30) * 50
            )

            snapshots.append(
                WorkloadSnapshot(
                    user_email=email,
                    user_name=person_items[0].assignee_name or email,
                    open_items=len(open_items),
                    in_progress_items=len(in_progress),
                    total_story_points=total_sp,
                    overdue_items=0,
                    avg_items_per_sprint=len(person_items) / 4,  # Approximate
                    overcommitment_score=round(overcommitment, 1),
                )
            )

        return sorted(snapshots, key=lambda s: s.overcommitment_score, reverse=True)

    def analyze_cycle_times(self, items: List[WorkItem]) -> Dict[str, Any]:
        """Analyze cycle time trends as a proxy for team friction."""
        resolved = [
            i for i in items if i.cycle_time_hours is not None and i.resolved_at
        ]
        if not resolved:
            return {"avg_hours": 0, "median_hours": 0, "trend": "stable", "count": 0}

        times = sorted([i.cycle_time_hours for i in resolved])
        avg = sum(times) / len(times)
        median = times[len(times) // 2]

        # Trend: compare first half vs second half
        mid = len(resolved) // 2
        if mid > 0:
            first = sum(t.cycle_time_hours for t in resolved[:mid]) / mid
            second = sum(t.cycle_time_hours for t in resolved[mid:]) / (
                len(resolved) - mid
            )
            if second > first * 1.1:
                trend = "slowing"
            elif second < first * 0.9:
                trend = "improving"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "avg_hours": round(avg, 1),
            "median_hours": round(median, 1),
            "trend": trend,
            "count": len(resolved),
        }

    def collaboration_from_items(self, items: List[WorkItem]) -> List[Dict[str, Any]]:
        """Derive collaboration edges from shared project/sprint work."""
        sprint_people: Dict[str, set] = {}
        for item in items:
            key = item.sprint_name or item.project_key or "default"
            email = item.assignee_email or item.assignee_name
            if email:
                if key not in sprint_people:
                    sprint_people[key] = set()
                sprint_people[key].add(email)

        edges: Dict[tuple, int] = {}
        for _sprint, people in sprint_people.items():
            people_list = sorted(people)
            for i in range(len(people_list)):
                for j in range(i + 1, len(people_list)):
                    pair = (people_list[i], people_list[j])
                    edges[pair] = edges.get(pair, 0) + 1

        return [
            {"person_a": a, "person_b": b, "shared_contexts": w}
            for (a, b), w in sorted(edges.items(), key=lambda x: x[1], reverse=True)[
                :50
            ]
        ]


# Singleton registry
work_systems_registry = WorkSystemsRegistry()
