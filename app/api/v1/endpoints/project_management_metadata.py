"""
Project Management Metadata Analysis API Endpoints

Privacy-first project management intelligence: analyzes ONLY metadata
(task counts, statuses, cycle times, assignments). Never reads task
descriptions, comments, or attachment content.

Endpoints:
  GET /project-management-metadata/signals/{org_id}  — full behavioral signals
  GET /project-management-metadata/burnout/{org_id}   — burnout risk summary
  GET /project-management-metadata/status             — connector status
"""

import logging

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_current_user, get_db
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/project-management-metadata",
    tags=["Project Management Metadata"],
)


def _get_analyzer():
    from app.services.project_management_metadata_service import (
        ProjectManagementAnalyzer,
    )

    return ProjectManagementAnalyzer()


def _get_registry():
    from app.services.project_management_metadata_service import (
        project_management_registry,
    )

    return project_management_registry


@router.get("/signals/{org_id}")
async def get_project_management_signals(
    org_id: str,
    days: int = Query(14, ge=1, le=90, description="Lookback window in days"),
    current_user: User = Depends(get_current_user),
):
    """Full project management behavioral signals for an organization.

    Returns workload, delivery health, focus, collaboration balance,
    deadline pressure, burnout signals, and recommendations.
    All derived from metadata only — zero task content accessed.
    """
    registry = _get_registry()
    analyzer = _get_analyzer()

    connectors = registry.list_connectors()
    if not connectors:
        result = analyzer.analyze([])
        return {
            "success": True,
            "org_id": org_id,
            "days": days,
            "data_source": "no_connector",
            "data": result,
        }

    all_records = []

    for connector_info in connectors:
        connector = registry.get(connector_info["name"])
        if connector:
            try:
                records = await connector.fetch_task_metadata(
                    org_config={"org_id": org_id},
                    period_days=days,
                )
                all_records.extend(records)
            except Exception as e:
                logger.warning(
                    "PM connector %s failed: %s",
                    connector_info["name"],
                    e,
                )

    result = analyzer.analyze(all_records)

    return {
        "success": True,
        "org_id": org_id,
        "days": days,
        "record_count": len(all_records),
        "data_source": "live" if all_records else "no_data",
        "data": result,
    }


@router.get("/burnout/{org_id}")
async def get_project_management_burnout(
    org_id: str,
    days: int = Query(14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
):
    """Burnout risk signals derived from project management metadata only."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_records = []

    for connector_info in registry.list_connectors():
        connector = registry.get(connector_info["name"])
        if connector:
            try:
                all_records.extend(
                    await connector.fetch_task_metadata(
                        org_config={"org_id": org_id},
                        period_days=days,
                    )
                )
            except Exception:
                pass

    result = analyzer.analyze(all_records)

    return {
        "success": True,
        "org_id": org_id,
        "days": days,
        "burnout": {
            "composite_score": result["burnout_composite"],
            "risk_label": result["risk_label"],
            "workload_score": result["workload_score"],
            "deadline_pressure": result["deadline_pressure"],
            "focus_score": result["focus_score"],
            "signals": result["burnout_signals"],
        },
        "recommendations": result["recommendations"],
    }


@router.get("/status")
async def get_project_management_status(
    current_user: User = Depends(get_current_user),
):
    """Check which project management metadata connectors are registered."""
    registry = _get_registry()
    connectors = registry.list_connectors()

    return {
        "success": True,
        "connectors": connectors,
        "available": len(connectors) > 0,
        "privacy_note": (
            "Only task metadata is accessed. "
            "Descriptions, comments, and attachments are never read."
        ),
    }
