"""
Work Systems Integration API

Manage connectors to external work platforms (Jira, Azure DevOps, Asana, Monday.com)
and extract behavioral signals from work item data.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.db.models.user import User
from app.services.security import get_current_user
from app.services.work_systems_integration_service import (
    AsanaConnector,
    AzureDevOpsConnector,
    JiraConnector,
    MondayConnector,
    WorkSystemBehavioralAnalyzer,
    work_systems_registry,
)

router = APIRouter(
    prefix="/work-systems",
    tags=["Work Systems Integration"],
)

_analyzer = WorkSystemBehavioralAnalyzer()


class ConnectorConfig(BaseModel):
    type: str  # "jira", "azure_devops", "asana", "monday"
    name: str
    base_url: Optional[str] = None
    email: Optional[str] = None
    api_token: Optional[str] = None
    organization: Optional[str] = None
    project: Optional[str] = None
    pat: Optional[str] = None
    access_token: Optional[str] = None
    api_key: Optional[str] = None


@router.get("/connectors")
async def list_connectors(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """List all registered work system connectors."""
    return {
        "connectors": work_systems_registry.list_connectors(),
        "available_types": list(work_systems_registry.CONNECTOR_TYPES.keys()),
    }


@router.post("/connectors")
async def register_connector(
    config: ConnectorConfig,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Register a new work system connector."""
    if config.type == "jira":
        if not config.base_url or not config.email or not config.api_token:
            raise HTTPException(400, "Jira requires base_url, email, api_token")
        connector = JiraConnector(config.base_url, config.email, config.api_token)
    elif config.type == "azure_devops":
        if not config.organization or not config.project or not config.pat:
            raise HTTPException(400, "Azure DevOps requires organization, project, pat")
        connector = AzureDevOpsConnector(
            config.organization, config.project, config.pat
        )
    elif config.type == "asana":
        if not config.access_token:
            raise HTTPException(400, "Asana requires access_token")
        connector = AsanaConnector(config.access_token)
    elif config.type == "monday":
        if not config.api_key:
            raise HTTPException(400, "Monday.com requires api_key")
        connector = MondayConnector(config.api_key)
    else:
        raise HTTPException(400, f"Unknown connector type: {config.type}")

    # Test connection first
    test_result = await connector.test_connection()
    if not test_result.get("connected"):
        return {
            "success": False,
            "error": test_result.get("error", "Connection failed"),
        }

    work_systems_registry.register(config.name, connector)
    return {"success": True, "name": config.name, "type": config.type}


@router.post("/connectors/{name}/test")
async def test_connector(
    name: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Test a registered connector's connectivity."""
    connector = work_systems_registry.get(name)
    if not connector:
        raise HTTPException(404, f"Connector '{name}' not found")
    return await connector.test_connection()


@router.get("/connectors/{name}/items")
async def fetch_work_items(
    name: str,
    project_key: str = Query(...),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Fetch normalized work items from a connector."""
    connector = work_systems_registry.get(name)
    if not connector:
        raise HTTPException(404, f"Connector '{name}' not found")

    items = await connector.fetch_work_items(project_key)
    return {
        "connector": name,
        "project_key": project_key,
        "total_items": len(items),
        "items": [
            {
                "id": i.id,
                "external_id": i.external_id,
                "title": i.title,
                "status": i.status.value,
                "priority": i.priority.value,
                "assignee": i.assignee_name or i.assignee_email,
                "story_points": i.story_points,
                "cycle_time_hours": i.cycle_time_hours,
            }
            for i in items[:100]
        ],
    }


@router.get("/connectors/{name}/behavioral-signals")
async def behavioral_signals(
    name: str,
    project_key: str = Query(...),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Extract behavioral signals from work item data."""
    connector = work_systems_registry.get(name)
    if not connector:
        raise HTTPException(404, f"Connector '{name}' not found")

    items = await connector.fetch_work_items(project_key)
    if not items:
        return {"connector": name, "signals": "No work items found"}

    workload = _analyzer.analyze_workload(items)
    cycle_times = _analyzer.analyze_cycle_times(items)
    collaboration = _analyzer.collaboration_from_items(items)

    return {
        "connector": name,
        "project_key": project_key,
        "total_items": len(items),
        "workload": [
            {
                "user": w.user_name,
                "email": w.user_email,
                "open_items": w.open_items,
                "in_progress": w.in_progress_items,
                "story_points": w.total_story_points,
                "overcommitment_score": w.overcommitment_score,
            }
            for w in workload[:20]
        ],
        "cycle_times": cycle_times,
        "collaboration_edges": collaboration[:20],
    }
