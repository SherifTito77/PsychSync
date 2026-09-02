"""
Project Management Metadata Analysis Service

Analyzes project management METADATA ONLY — task counts, status transitions,
cycle times, assignment patterns. Never reads task descriptions, comments,
or attachment content.

Input signals (per user):
  - assigned / completed / overdue / blocked / in-progress task counts
  - avg cycle time (start → done) and lead time (created → done)
  - active project count (context-switching proxy)
  - priority distribution (critical/high/medium/low)
  - collaboration: tasks assigned by/to others, comment counts
  - sprint velocity and commitment ratio (optional)

Output behavioral signals:
  - workload_score (overload risk)
  - delivery_health (completion vs assignment)
  - focus_score (project sprawl)
  - collaboration_balance (give vs take)
  - deadline_pressure (overdue + blocked)
  - burnout_signals composite

Privacy guarantees:
  - No task titles, descriptions, or comment content
  - No attachment content or linked documents
  - Only aggregate counts, timestamps, and status transitions
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ==================================================================
# NORMALIZED SCHEMA — counts and durations only
# ==================================================================


@dataclass
class ProjectMetadataRecord:
    """One user's project management metadata for a time window."""

    user_email: str
    period_start: datetime
    period_end: datetime
    # Workload signals
    assigned_tasks: int
    completed_tasks: int
    overdue_tasks: int
    blocked_tasks: int
    in_progress_tasks: int
    # Cycle time signals
    avg_cycle_time_hours: float  # time from start to done
    avg_lead_time_hours: float  # time from created to done
    # Focus signals
    projects_active: int  # how many projects simultaneously
    priority_distribution: Dict[str, int] = field(
        default_factory=dict
    )  # critical/high/medium/low
    # Collaboration signals
    tasks_assigned_by_others: int = 0
    tasks_assigned_to_others: int = 0
    comments_given: int = 0
    comments_received: int = 0
    # Sprint/iteration signals (optional)
    sprint_velocity: Optional[float] = None
    sprint_commitment_ratio: Optional[float] = None  # completed / committed
    story_points_completed: Optional[float] = None


# ==================================================================
# ABSTRACT CONNECTOR
# ==================================================================


class ProjectManagementConnector(ABC):
    """Base interface for project management metadata connectors.

    Implementations must NEVER fetch task descriptions, comment content,
    or attachments. Only task lifecycle metadata (counts, statuses,
    timestamps, assignments).
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_task_metadata(
        self,
        org_config: Dict,
        period_days: int,
    ) -> List[ProjectMetadataRecord]:
        """Fetch task/issue metadata for the organization."""


# ==================================================================
# JIRA CLOUD CONNECTOR
# ==================================================================


class JiraCloudConnector(ProjectManagementConnector):
    """Jira Cloud API connector — task lifecycle metadata only.

    Uses:
      POST /rest/api/3/search — JQL search for issue metadata
      GET  /rest/api/3/issue/{key}/changelog — status transitions

    Never uses:
      GET /rest/api/3/issue/{key} with body/description fields
      GET /rest/api/3/issue/{key}/comment — would expose content

    Required scopes: read:jira-work (metadata only)
    """

    def __init__(
        self,
        base_url: str = "",
        email: str = "",
        api_token: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.api_token and self.base_url),
            "provider": "jira_cloud",
            "scopes": ["read:jira-work (metadata only)"],
            "note": "Fetches task counts, statuses, and cycle times — never reads descriptions or comments",
        }

    def _auth(self) -> tuple:
        return (self.email, self.api_token)

    async def fetch_task_metadata(
        self,
        org_config: Dict,
        period_days: int,
    ) -> List[ProjectMetadataRecord]:
        if not self.api_token or not self.base_url:
            return []

        records: List[ProjectMetadataRecord] = []
        try:
            import httpx
            from datetime import timedelta

            end = datetime.utcnow()
            start = end - timedelta(days=period_days)
            start_str = start.strftime("%Y-%m-%d")

            jql = f"updated >= '{start_str}' ORDER BY assignee ASC"
            project = org_config.get("project_key")
            if project:
                jql = f"project = {project} AND {jql}"

            user_tasks: Dict[str, Dict] = {}
            start_at = 0
            max_results = 100

            async with httpx.AsyncClient(timeout=30.0) as client:
                while True:
                    resp = await client.post(
                        f"{self.base_url}/rest/api/3/search",
                        auth=self._auth(),
                        json={
                            "jql": jql,
                            "startAt": start_at,
                            "maxResults": max_results,
                            "fields": [
                                "assignee",
                                "status",
                                "priority",
                                "created",
                                "resolutiondate",
                                "project",
                                "issuetype",
                                "statuscategorychangedate",
                            ],
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    issues = data.get("issues", [])
                    if not issues:
                        break

                    for issue in issues:
                        fields = issue.get("fields", {})
                        assignee = fields.get("assignee") or {}
                        email = assignee.get("emailAddress", "")
                        if not email:
                            continue

                        if email not in user_tasks:
                            user_tasks[email] = {
                                "assigned": 0,
                                "completed": 0,
                                "overdue": 0,
                                "blocked": 0,
                                "in_progress": 0,
                                "cycle_times": [],
                                "lead_times": [],
                                "projects": set(),
                                "priorities": {},
                                "comments_given": 0,
                                "comments_received": 0,
                                "assigned_by_others": 0,
                                "assigned_to_others": 0,
                            }

                        ut = user_tasks[email]
                        ut["assigned"] += 1

                        status_cat = (
                            fields.get("status", {})
                            .get("statusCategory", {})
                            .get("key", "")
                        )
                        priority_name = (
                            fields.get("priority", {}).get("name", "medium").lower()
                        )

                        if status_cat == "done":
                            ut["completed"] += 1
                        elif status_cat == "indeterminate":
                            ut["in_progress"] += 1

                        # Blocked detection via status name
                        status_name = fields.get("status", {}).get("name", "").lower()
                        if "block" in status_name or "impediment" in status_name:
                            ut["blocked"] += 1

                        # Overdue: resolved after due or still open past due
                        # (simplified — Jira doesn't always have duedate)

                        # Priority
                        bucket = self._priority_bucket(priority_name)
                        ut["priorities"][bucket] = ut["priorities"].get(bucket, 0) + 1

                        # Project tracking
                        proj_key = fields.get("project", {}).get("key", "")
                        if proj_key:
                            ut["projects"].add(proj_key)

                        # Cycle/lead time
                        created = fields.get("created")
                        resolved = fields.get("resolutiondate")
                        if created and resolved:
                            try:
                                c = datetime.fromisoformat(
                                    created.replace("Z", "+00:00")
                                )
                                r = datetime.fromisoformat(
                                    resolved.replace("Z", "+00:00")
                                )
                                lead_h = (r - c).total_seconds() / 3600
                                ut["lead_times"].append(lead_h)
                                # Cycle time approximated from status change date
                                scd = fields.get("statuscategorychangedate")
                                if scd:
                                    s = datetime.fromisoformat(
                                        scd.replace("Z", "+00:00")
                                    )
                                    cycle_h = (r - s).total_seconds() / 3600
                                    ut["cycle_times"].append(max(0, cycle_h))
                                else:
                                    ut["cycle_times"].append(lead_h)
                            except (ValueError, TypeError):
                                pass

                    start_at += max_results
                    if start_at >= data.get("total", 0):
                        break

            # Build records
            for email, ut in user_tasks.items():
                avg_cycle = (
                    sum(ut["cycle_times"]) / len(ut["cycle_times"])
                    if ut["cycle_times"]
                    else 0
                )
                avg_lead = (
                    sum(ut["lead_times"]) / len(ut["lead_times"])
                    if ut["lead_times"]
                    else 0
                )
                records.append(
                    ProjectMetadataRecord(
                        user_email=email,
                        period_start=start,
                        period_end=end,
                        assigned_tasks=ut["assigned"],
                        completed_tasks=ut["completed"],
                        overdue_tasks=ut["overdue"],
                        blocked_tasks=ut["blocked"],
                        in_progress_tasks=ut["in_progress"],
                        avg_cycle_time_hours=round(avg_cycle, 1),
                        avg_lead_time_hours=round(avg_lead, 1),
                        projects_active=len(ut["projects"]),
                        priority_distribution=ut["priorities"],
                        tasks_assigned_by_others=ut["assigned_by_others"],
                        tasks_assigned_to_others=ut["assigned_to_others"],
                        comments_given=ut["comments_given"],
                        comments_received=ut["comments_received"],
                    )
                )

            logger.info("Jira: fetched metadata for %d users", len(records))
        except ImportError:
            logger.warning("httpx not installed — Jira connector disabled")
        except Exception as e:
            logger.error("Jira metadata fetch error: %s", e)
        return records

    @staticmethod
    def _priority_bucket(name: str) -> str:
        name = name.lower()
        if name in ("highest", "critical", "blocker"):
            return "critical"
        if name in ("high"):
            return "high"
        if name in ("low", "lowest", "trivial"):
            return "low"
        return "medium"


# ==================================================================
# ASANA CONNECTOR
# ==================================================================


class AsanaConnector(ProjectManagementConnector):
    """Asana API connector — task lifecycle metadata only.

    Uses:
      GET /api/1.0/tasks — task metadata with project filter
      GET /api/1.0/projects — project listing

    Never uses:
      Task notes/descriptions or attachment content

    Auth: Personal Access Token or OAuth 2.0
    """

    def __init__(self, access_token: str = ""):
        self.access_token = access_token

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.access_token),
            "provider": "asana",
            "scopes": ["default (metadata only)"],
            "note": "Fetches task counts and completion times — never reads task notes or descriptions",
        }

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    async def fetch_task_metadata(
        self,
        org_config: Dict,
        period_days: int,
    ) -> List[ProjectMetadataRecord]:
        if not self.access_token:
            return []

        records: List[ProjectMetadataRecord] = []
        try:
            import httpx
            from datetime import timedelta

            end = datetime.utcnow()
            start = end - timedelta(days=period_days)
            workspace = org_config.get("workspace_gid", "")
            if not workspace:
                return []

            user_tasks: Dict[str, Dict] = {}

            async with httpx.AsyncClient(timeout=30.0) as client:
                # List projects in workspace
                proj_resp = await client.get(
                    "https://app.asana.com/api/1.0/projects",
                    headers=self._headers(),
                    params={
                        "workspace": workspace,
                        "opt_fields": "gid,name",
                        "limit": 100,
                    },
                )
                proj_resp.raise_for_status()
                projects = proj_resp.json().get("data", [])

                for project in projects:
                    project_gid = project.get("gid", "")
                    offset = None

                    while True:
                        params: Dict[str, Any] = {
                            "project": project_gid,
                            "opt_fields": (
                                "assignee.email,completed,completed_at,"
                                "created_at,due_on,custom_fields.name,"
                                "custom_fields.display_value,memberships.project.gid,"
                                "num_subtasks"
                            ),
                            "completed_since": start.isoformat() + "Z",
                            "limit": 100,
                        }
                        if offset:
                            params["offset"] = offset

                        resp = await client.get(
                            "https://app.asana.com/api/1.0/tasks",
                            headers=self._headers(),
                            params=params,
                        )
                        resp.raise_for_status()
                        body = resp.json()
                        tasks = body.get("data", [])
                        if not tasks:
                            break

                        for task in tasks:
                            assignee = task.get("assignee") or {}
                            email = assignee.get("email", "")
                            if not email:
                                continue

                            if email not in user_tasks:
                                user_tasks[email] = {
                                    "assigned": 0,
                                    "completed": 0,
                                    "overdue": 0,
                                    "blocked": 0,
                                    "in_progress": 0,
                                    "cycle_times": [],
                                    "lead_times": [],
                                    "projects": set(),
                                    "priorities": {},
                                }

                            ut = user_tasks[email]
                            ut["assigned"] += 1
                            ut["projects"].add(project_gid)

                            is_completed = task.get("completed", False)
                            if is_completed:
                                ut["completed"] += 1
                            else:
                                ut["in_progress"] += 1

                            # Overdue check
                            due_on = task.get("due_on")
                            if due_on and not is_completed:
                                try:
                                    due = datetime.strptime(due_on, "%Y-%m-%d")
                                    if due < end:
                                        ut["overdue"] += 1
                                except ValueError:
                                    pass

                            # Lead time
                            created_at = task.get("created_at")
                            completed_at = task.get("completed_at")
                            if created_at and completed_at:
                                try:
                                    c = datetime.fromisoformat(
                                        created_at.replace("Z", "+00:00")
                                    )
                                    d = datetime.fromisoformat(
                                        completed_at.replace("Z", "+00:00")
                                    )
                                    lead_h = (d - c).total_seconds() / 3600
                                    ut["lead_times"].append(lead_h)
                                    ut["cycle_times"].append(lead_h)
                                except (ValueError, TypeError):
                                    pass

                            # Priority from custom fields
                            for cf in task.get("custom_fields", []):
                                if cf.get("name", "").lower() == "priority":
                                    val = (cf.get("display_value") or "medium").lower()
                                    bucket = (
                                        "critical"
                                        if val in ("critical", "urgent")
                                        else (
                                            "high"
                                            if val == "high"
                                            else "low" if val == "low" else "medium"
                                        )
                                    )
                                    ut["priorities"][bucket] = (
                                        ut["priorities"].get(bucket, 0) + 1
                                    )

                        next_page = body.get("next_page")
                        offset = next_page.get("offset") if next_page else None
                        if not offset:
                            break

            for email, ut in user_tasks.items():
                avg_cycle = (
                    sum(ut["cycle_times"]) / len(ut["cycle_times"])
                    if ut["cycle_times"]
                    else 0
                )
                avg_lead = (
                    sum(ut["lead_times"]) / len(ut["lead_times"])
                    if ut["lead_times"]
                    else 0
                )
                records.append(
                    ProjectMetadataRecord(
                        user_email=email,
                        period_start=start,
                        period_end=end,
                        assigned_tasks=ut["assigned"],
                        completed_tasks=ut["completed"],
                        overdue_tasks=ut["overdue"],
                        blocked_tasks=ut["blocked"],
                        in_progress_tasks=ut["in_progress"],
                        avg_cycle_time_hours=round(avg_cycle, 1),
                        avg_lead_time_hours=round(avg_lead, 1),
                        projects_active=len(ut["projects"]),
                        priority_distribution=ut["priorities"],
                    )
                )

            logger.info("Asana: fetched metadata for %d users", len(records))
        except ImportError:
            logger.warning("httpx not installed — Asana connector disabled")
        except Exception as e:
            logger.error("Asana metadata fetch error: %s", e)
        return records


# ==================================================================
# LINEAR CONNECTOR
# ==================================================================


class LinearConnector(ProjectManagementConnector):
    """Linear GraphQL API connector — issue lifecycle metadata only.

    Uses:
      POST /graphql — issues query with state, assignee, priority, cycle

    Never uses:
      Issue description or comment body fields

    Auth: API key
    """

    GRAPHQL_URL = "https://api.linear.app/graphql"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.api_key),
            "provider": "linear",
            "scopes": ["read (metadata only)"],
            "note": "Fetches issue counts, states, and cycle data — never reads descriptions or comments",
        }

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

    async def fetch_task_metadata(
        self,
        org_config: Dict,
        period_days: int,
    ) -> List[ProjectMetadataRecord]:
        if not self.api_key:
            return []

        records: List[ProjectMetadataRecord] = []
        try:
            import httpx
            from datetime import timedelta

            end = datetime.utcnow()
            start = end - timedelta(days=period_days)

            query = (
                """
            query($after: String) {
              issues(
                first: 100
                after: $after
                filter: { updatedAt: { gte: "%s" } }
              ) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  assignee { email }
                  state { name type }
                  priority
                  createdAt
                  completedAt
                  startedAt
                  dueDate
                  project { id }
                  cycle { id }
                  estimate
                }
              }
            }
            """
                % start.isoformat()
            )

            user_tasks: Dict[str, Dict] = {}
            cursor = None

            async with httpx.AsyncClient(timeout=30.0) as client:
                while True:
                    resp = await client.post(
                        self.GRAPHQL_URL,
                        headers=self._headers(),
                        json={
                            "query": query,
                            "variables": {"after": cursor},
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json().get("data", {}).get("issues", {})
                    nodes = data.get("nodes", [])
                    if not nodes:
                        break

                    for issue in nodes:
                        assignee = issue.get("assignee") or {}
                        email = assignee.get("email", "")
                        if not email:
                            continue

                        if email not in user_tasks:
                            user_tasks[email] = {
                                "assigned": 0,
                                "completed": 0,
                                "overdue": 0,
                                "blocked": 0,
                                "in_progress": 0,
                                "cycle_times": [],
                                "lead_times": [],
                                "projects": set(),
                                "priorities": {},
                                "velocity_points": [],
                                "committed": 0,
                                "completed_in_cycle": 0,
                            }

                        ut = user_tasks[email]
                        ut["assigned"] += 1

                        state_type = (issue.get("state") or {}).get("type", "")
                        state_name = (issue.get("state") or {}).get("name", "").lower()

                        if state_type == "completed":
                            ut["completed"] += 1
                        elif state_type == "started":
                            ut["in_progress"] += 1

                        if "block" in state_name:
                            ut["blocked"] += 1

                        # Priority: Linear uses 0(none) 1(urgent) 2(high) 3(medium) 4(low)
                        pri = issue.get("priority", 0)
                        bucket = (
                            "critical"
                            if pri == 1
                            else "high" if pri == 2 else "low" if pri == 4 else "medium"
                        )
                        ut["priorities"][bucket] = ut["priorities"].get(bucket, 0) + 1

                        # Project
                        proj = issue.get("project") or {}
                        if proj.get("id"):
                            ut["projects"].add(proj["id"])

                        # Cycle/lead times
                        created = issue.get("createdAt")
                        completed = issue.get("completedAt")
                        started = issue.get("startedAt")
                        if created and completed:
                            try:
                                c = datetime.fromisoformat(
                                    created.replace("Z", "+00:00")
                                )
                                d = datetime.fromisoformat(
                                    completed.replace("Z", "+00:00")
                                )
                                ut["lead_times"].append((d - c).total_seconds() / 3600)
                                if started:
                                    s = datetime.fromisoformat(
                                        started.replace("Z", "+00:00")
                                    )
                                    ut["cycle_times"].append(
                                        max(0, (d - s).total_seconds() / 3600)
                                    )
                                else:
                                    ut["cycle_times"].append(
                                        (d - c).total_seconds() / 3600
                                    )
                            except (ValueError, TypeError):
                                pass

                        # Sprint/cycle data
                        if issue.get("cycle"):
                            ut["committed"] += 1
                            estimate = issue.get("estimate")
                            if state_type == "completed" and estimate:
                                ut["velocity_points"].append(estimate)
                                ut["completed_in_cycle"] += 1

                        # Overdue
                        due = issue.get("dueDate")
                        if due and state_type != "completed":
                            try:
                                d = datetime.strptime(due, "%Y-%m-%d")
                                if d < end:
                                    ut["overdue"] += 1
                            except ValueError:
                                pass

                    page_info = data.get("pageInfo", {})
                    if not page_info.get("hasNextPage"):
                        break
                    cursor = page_info.get("endCursor")

            for email, ut in user_tasks.items():
                avg_cycle = (
                    sum(ut["cycle_times"]) / len(ut["cycle_times"])
                    if ut["cycle_times"]
                    else 0
                )
                avg_lead = (
                    sum(ut["lead_times"]) / len(ut["lead_times"])
                    if ut["lead_times"]
                    else 0
                )
                velocity = sum(ut["velocity_points"]) if ut["velocity_points"] else None
                commitment = (
                    ut["completed_in_cycle"] / ut["committed"]
                    if ut["committed"] > 0
                    else None
                )
                records.append(
                    ProjectMetadataRecord(
                        user_email=email,
                        period_start=start,
                        period_end=end,
                        assigned_tasks=ut["assigned"],
                        completed_tasks=ut["completed"],
                        overdue_tasks=ut["overdue"],
                        blocked_tasks=ut["blocked"],
                        in_progress_tasks=ut["in_progress"],
                        avg_cycle_time_hours=round(avg_cycle, 1),
                        avg_lead_time_hours=round(avg_lead, 1),
                        projects_active=len(ut["projects"]),
                        priority_distribution=ut["priorities"],
                        sprint_velocity=velocity,
                        sprint_commitment_ratio=(
                            round(commitment, 2) if commitment is not None else None
                        ),
                        story_points_completed=(
                            sum(ut["velocity_points"])
                            if ut["velocity_points"]
                            else None
                        ),
                    )
                )

            logger.info("Linear: fetched metadata for %d users", len(records))
        except ImportError:
            logger.warning("httpx not installed — Linear connector disabled")
        except Exception as e:
            logger.error("Linear metadata fetch error: %s", e)
        return records


# ==================================================================
# BEHAVIORAL ANALYZER
# ==================================================================


class ProjectManagementAnalyzer:
    """Extracts behavioral signals from project management metadata.

    Never sees task descriptions, comment content, or attachments.
    Works only with counts, statuses, and lifecycle durations.
    """

    def analyze(self, records: List[ProjectMetadataRecord]) -> Dict[str, Any]:
        if not records:
            return self._empty_result()

        # Aggregate across all records
        total_assigned = sum(r.assigned_tasks for r in records)
        total_completed = sum(r.completed_tasks for r in records)
        total_overdue = sum(r.overdue_tasks for r in records)
        total_blocked = sum(r.blocked_tasks for r in records)
        total_in_progress = sum(r.in_progress_tasks for r in records)

        # Averages
        avg_cycle = sum(
            r.avg_cycle_time_hours for r in records if r.avg_cycle_time_hours > 0
        ) / max(sum(1 for r in records if r.avg_cycle_time_hours > 0), 1)
        avg_lead = sum(
            r.avg_lead_time_hours for r in records if r.avg_lead_time_hours > 0
        ) / max(sum(1 for r in records if r.avg_lead_time_hours > 0), 1)

        avg_projects = sum(r.projects_active for r in records) / len(records)

        # Priority aggregation
        priority_totals: Dict[str, int] = {}
        for r in records:
            for k, v in r.priority_distribution.items():
                priority_totals[k] = priority_totals.get(k, 0) + v

        # Collaboration
        total_comments_given = sum(r.comments_given for r in records)
        total_comments_received = sum(r.comments_received for r in records)
        total_assigned_by_others = sum(r.tasks_assigned_by_others for r in records)
        total_assigned_to_others = sum(r.tasks_assigned_to_others for r in records)

        # Sprint data (from records that have it)
        sprint_records = [r for r in records if r.sprint_velocity is not None]
        avg_velocity = (
            sum(r.sprint_velocity for r in sprint_records)  # type: ignore[arg-type]
            / len(sprint_records)
            if sprint_records
            else None
        )
        avg_commitment = (
            sum(
                r.sprint_commitment_ratio
                for r in sprint_records  # type: ignore[arg-type]
                if r.sprint_commitment_ratio is not None
            )
            / max(
                sum(1 for r in sprint_records if r.sprint_commitment_ratio is not None),
                1,
            )
            if sprint_records
            else None
        )

        # -- Scores --

        workload = self._workload_score(
            total_assigned,
            total_completed,
            total_overdue,
            total_in_progress,
        )
        delivery = self._delivery_health(
            total_assigned,
            total_completed,
            avg_cycle,
        )
        focus = self._focus_score(avg_projects)
        collab = self._collaboration_balance(
            total_comments_given,
            total_comments_received,
            total_assigned_by_others,
            total_assigned_to_others,
        )
        deadline = self._deadline_pressure(
            total_assigned,
            total_overdue,
            total_blocked,
        )

        # Burnout signals
        overdue_ratio = total_overdue / max(total_assigned, 1)
        multitasking_idx = min(100, avg_projects * 15)
        blocked_ratio = total_blocked / max(total_assigned, 1)
        velocity_decline = self._velocity_decline(sprint_records)

        burnout_composite = (
            workload * 0.30
            + deadline * 0.25
            + multitasking_idx * 0.20
            + (100 - delivery) * 0.15
            + (velocity_decline * 100) * 0.10
        )
        burnout_composite = min(100, round(burnout_composite, 1))

        if burnout_composite >= 70:
            risk_label = "Critical"
        elif burnout_composite >= 45:
            risk_label = "Elevated"
        elif burnout_composite >= 25:
            risk_label = "Monitor"
        else:
            risk_label = "Healthy"

        recommendations = self._generate_recommendations(
            workload,
            delivery,
            focus,
            deadline,
            overdue_ratio,
            avg_projects,
            avg_commitment,
        )

        return {
            "workload_score": round(workload, 1),
            "delivery_health": round(delivery, 1),
            "focus_score": round(focus, 1),
            "collaboration_balance": round(collab, 1),
            "deadline_pressure": round(deadline, 1),
            "burnout_composite": burnout_composite,
            "risk_label": risk_label,
            "burnout_signals": {
                "overdue_ratio": round(overdue_ratio, 3),
                "multitasking_index": round(multitasking_idx, 1),
                "velocity_decline": round(velocity_decline, 3),
                "blocked_ratio": round(blocked_ratio, 3),
            },
            "signals": {
                "workload": {
                    "assigned": total_assigned,
                    "completed": total_completed,
                    "overdue": total_overdue,
                    "blocked": total_blocked,
                    "in_progress": total_in_progress,
                },
                "cycle_time": {
                    "avg_cycle_hours": round(avg_cycle, 1),
                    "avg_lead_hours": round(avg_lead, 1),
                },
                "completion_rate": {
                    "rate": round(total_completed / max(total_assigned, 1), 3),
                    "priority_distribution": priority_totals,
                },
                "sprint_health": {
                    "avg_velocity": round(avg_velocity, 1) if avg_velocity else None,
                    "avg_commitment_ratio": (
                        round(avg_commitment, 2) if avg_commitment else None
                    ),
                },
                "collaboration": {
                    "comments_given": total_comments_given,
                    "comments_received": total_comments_received,
                    "tasks_assigned_by_others": total_assigned_by_others,
                    "tasks_assigned_to_others": total_assigned_to_others,
                },
                "focus": {
                    "avg_active_projects": round(avg_projects, 1),
                },
            },
            "recommendations": recommendations,
        }

    # -- Component scores --

    def _workload_score(
        self,
        assigned: int,
        completed: int,
        overdue: int,
        in_progress: int,
    ) -> float:
        """0-100: higher = more overloaded."""
        backlog_ratio = (assigned - completed) / max(assigned, 1)
        base = min(100, backlog_ratio * 100)
        overdue_penalty = min(30, (overdue / max(assigned, 1)) * 60)
        wip_pressure = min(20, max(0, in_progress - 5) * 4)
        return min(100, base + overdue_penalty + wip_pressure)

    def _delivery_health(
        self,
        assigned: int,
        completed: int,
        avg_cycle: float,
    ) -> float:
        """0-100: higher = healthier delivery."""
        completion_rate = completed / max(assigned, 1)
        base = completion_rate * 100
        # Penalize long cycle times: >72h starts hurting
        cycle_penalty = min(30, max(0, (avg_cycle - 72) / 72) * 30)
        return max(0, min(100, base - cycle_penalty))

    def _focus_score(self, avg_projects: float) -> float:
        """0-100: higher = more focused. 1 project = 100, 6+ = 0."""
        return max(0, 100 - min(100, (avg_projects - 1) * 20))

    def _collaboration_balance(
        self,
        comments_given: int,
        comments_received: int,
        assigned_by: int,
        assigned_to: int,
    ) -> float:
        """0-100: 50 = balanced give/take. <50 = more taking, >50 = more giving."""
        total_give = comments_given + assigned_to
        total_take = comments_received + assigned_by
        total = total_give + total_take
        if total == 0:
            return 50.0
        return round((total_give / total) * 100, 1)

    def _deadline_pressure(
        self,
        assigned: int,
        overdue: int,
        blocked: int,
    ) -> float:
        """0-100: higher = more deadline pressure."""
        overdue_component = (overdue / max(assigned, 1)) * 100
        blocked_penalty = min(30, (blocked / max(assigned, 1)) * 60)
        return min(100, overdue_component + blocked_penalty)

    def _velocity_decline(
        self,
        sprint_records: List[ProjectMetadataRecord],
    ) -> float:
        """0-1: fraction of velocity decline across available sprint data."""
        velocities = [
            r.sprint_velocity for r in sprint_records if r.sprint_velocity is not None
        ]
        if len(velocities) < 2:
            return 0.0
        mid = len(velocities) // 2
        first_avg = sum(velocities[:mid]) / mid
        second_avg = sum(velocities[mid:]) / max(len(velocities) - mid, 1)
        if first_avg == 0:
            return 0.0
        decline = (first_avg - second_avg) / first_avg
        return max(0, min(1, decline))

    def _generate_recommendations(
        self,
        workload: float,
        delivery: float,
        focus: float,
        deadline: float,
        overdue_ratio: float,
        avg_projects: float,
        avg_commitment: Optional[float],
    ) -> List[str]:
        recs = []
        if workload > 60:
            recs.append(
                f"Workload score is {workload:.0f}/100. "
                "Task backlog is growing faster than completion. "
                "Consider re-prioritizing or redistributing work."
            )
        if overdue_ratio > 0.20:
            recs.append(
                f"{overdue_ratio*100:.0f}% of tasks are overdue. "
                "Chronic overdue work erodes predictability and increases stress."
            )
        if avg_projects > 4:
            recs.append(
                f"Averaging {avg_projects:.1f} active projects. "
                "Context-switching across many projects reduces deep work capacity."
            )
        if delivery < 40:
            recs.append(
                f"Delivery health is low ({delivery:.0f}/100). "
                "Completion rate relative to assignments suggests capacity issues."
            )
        if deadline > 50:
            recs.append(
                "High deadline pressure from overdue and blocked tasks. "
                "Review blockers and deadline realism with the team."
            )
        if avg_commitment is not None and avg_commitment < 0.7:
            recs.append(
                f"Sprint commitment ratio is {avg_commitment:.0%}. "
                "Teams committing more than they deliver face morale erosion. "
                "Consider right-sizing sprint scope."
            )
        if not recs:
            recs.append(
                "Project management patterns look healthy. "
                "Workload and delivery are well-balanced."
            )
        return recs

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "workload_score": 0,
            "delivery_health": 0,
            "focus_score": 0,
            "collaboration_balance": 50,
            "deadline_pressure": 0,
            "burnout_composite": 0,
            "risk_label": "No Data",
            "burnout_signals": {
                "overdue_ratio": 0,
                "multitasking_index": 0,
                "velocity_decline": 0,
                "blocked_ratio": 0,
            },
            "signals": {
                "workload": {
                    "assigned": 0,
                    "completed": 0,
                    "overdue": 0,
                    "blocked": 0,
                    "in_progress": 0,
                },
                "cycle_time": {"avg_cycle_hours": 0, "avg_lead_hours": 0},
                "completion_rate": {"rate": 0, "priority_distribution": {}},
                "sprint_health": {
                    "avg_velocity": None,
                    "avg_commitment_ratio": None,
                },
                "collaboration": {
                    "comments_given": 0,
                    "comments_received": 0,
                    "tasks_assigned_by_others": 0,
                    "tasks_assigned_to_others": 0,
                },
                "focus": {"avg_active_projects": 0},
            },
            "recommendations": [
                "No project management data available. "
                "Connect Jira, Asana, or Linear to enable analysis."
            ],
        }


# ==================================================================
# REGISTRY
# ==================================================================


class ProjectManagementRegistry:
    CONNECTOR_TYPES = {
        "jira": JiraCloudConnector,
        "asana": AsanaConnector,
        "linear": LinearConnector,
    }

    def __init__(self):
        self._connectors: Dict[str, ProjectManagementConnector] = {}

    def register(self, name: str, connector: ProjectManagementConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered project management connector: %s", name)

    def get(self, name: str) -> Optional[ProjectManagementConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


project_management_registry = ProjectManagementRegistry()
# Register default connectors
project_management_registry.register("jira", JiraCloudConnector())
project_management_registry.register("asana", AsanaConnector())
project_management_registry.register("linear", LinearConnector())
