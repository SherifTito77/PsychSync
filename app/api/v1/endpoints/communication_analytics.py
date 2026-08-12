"""
Communication Analytics API

Connect Slack or Microsoft Teams to analyze messaging patterns,
response times, after-hours communication, and channel health.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db.models.user import User
from app.services.communication_analytics_service import (
    CommunicationHealthAnalyzer,
    SlackConnector,
    TeamsConnector,
    communication_registry,
)
from app.services.security import get_current_user

router = APIRouter(
    prefix="/communication-analytics",
    tags=["Communication Analytics"],
)

_analyzer = CommunicationHealthAnalyzer()


class CommConnectorConfig(BaseModel):
    type: str  # "slack" or "teams"
    name: str
    bot_token: Optional[str] = None
    workspace_name: Optional[str] = None
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


@router.get("/connectors")
async def list_connectors(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "connectors": communication_registry.list_connectors(),
        "available_types": ["slack", "teams"],
    }


@router.post("/connectors")
async def register_connector(
    config: CommConnectorConfig,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    if config.type == "slack":
        if not config.bot_token:
            raise HTTPException(400, "Slack requires bot_token")
        connector = SlackConnector(config.bot_token, config.workspace_name or "")
    elif config.type == "teams":
        if not config.tenant_id or not config.client_id or not config.client_secret:
            raise HTTPException(
                400, "Teams requires tenant_id, client_id, client_secret"
            )
        connector = TeamsConnector(
            config.tenant_id, config.client_id, config.client_secret
        )
    else:
        raise HTTPException(400, f"Unknown type: {config.type}")

    test = await connector.test_connection()
    if not test.get("connected"):
        return {"success": False, "error": test.get("error", "Connection failed")}

    communication_registry.register(config.name, connector)
    return {"success": True, "name": config.name, "type": config.type}


@router.post("/connectors/{name}/test")
async def test_connector(
    name: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    connector = communication_registry.get(name)
    if not connector:
        raise HTTPException(404, f"Connector '{name}' not found")
    return await connector.test_connection()


@router.get("/connectors/{name}/org-health")
async def org_communication_health(
    name: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Organization-wide communication health analysis."""
    connector = communication_registry.get(name)
    if not connector:
        raise HTTPException(404, f"Connector '{name}' not found")

    org_stats = await connector.fetch_org_stats(days=14)
    channels = await connector.fetch_channel_health(days=14)

    # If no actual data yet, return config status
    if not channels:
        return {
            "connector": name,
            "status": "connected",
            "health": {
                "score": 0,
                "label": "Awaiting Data",
                "recommendations": [
                    "Connector is registered. Once OAuth is configured and data flows, "
                    "communication health metrics will populate automatically."
                ],
            },
            "channels": [],
        }

    health = _analyzer.analyze_org_health([], channels)
    return {
        "connector": name,
        "health": {
            "score": health.score,
            "label": health.label,
            "active_users": health.total_active_users,
            "msg_per_person_day": health.avg_messages_per_person_day,
            "after_hours_rate": health.after_hours_rate,
            "avg_response_time_min": health.avg_response_time_min,
            "sentiment_trend": health.sentiment_trend,
            "engagement_distribution": health.channel_engagement_distribution,
            "recommendations": health.recommendations,
        },
        "channels": [
            {
                "name": c.channel_name,
                "members": c.member_count,
                "active": c.active_members,
                "msgs_per_day": c.messages_per_day,
                "thread_depth": c.avg_thread_depth,
                "response_rate": c.response_rate,
                "healthy": c.is_healthy,
            }
            for c in channels
        ],
    }
