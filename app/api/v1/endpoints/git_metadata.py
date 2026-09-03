"""
Git/GitHub Metadata Analysis API Endpoints

Privacy-first Git intelligence: analyzes ONLY metadata (commit timestamps,
line counts, PR lifecycle). Never reads code, diffs, or commit messages.

Endpoints:
  GET /git-metadata/signals/{org_id}   — full behavioral signals
  GET /git-metadata/burnout/{org_id}   — burnout risk summary only
  GET /git-metadata/status             — connector status
"""

import logging
from dataclasses import asdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_current_user, get_db
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/git-metadata", tags=["Git Metadata Analysis"])


def _get_analyzer():
    from app.services.git_metadata_service import GitMetadataAnalyzer

    return GitMetadataAnalyzer()


def _get_registry():
    from app.services.git_metadata_service import git_metadata_registry

    return git_metadata_registry


@router.get("/signals/{org_id}")
async def get_git_metadata_signals(
    org_id: str,
    days: int = Query(14, ge=1, le=90, description="Lookback window in days"),
    current_user: User = Depends(get_current_user),
):
    """Full Git metadata behavioral signals for an organization.

    Returns commit patterns, PR lifecycle metrics, timing analysis,
    composite scores, and recommendations.
    All derived from metadata only — zero code content accessed.
    """
    registry = _get_registry()
    analyzer = _get_analyzer()

    connectors = registry.list_connectors()
    if not connectors:
        signals = analyzer.analyze([], [], days=days)
        return {
            "success": True,
            "org_id": org_id,
            "days": days,
            "data_source": "no_connector",
            "signals": asdict(signals),
        }

    all_commits = []
    all_prs = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for connector_info in connectors:
        connector = registry.get(connector_info["name"])
        if connector:
            try:
                commits = await connector.fetch_commits(
                    user_id=current_user.email,
                    start=start,
                    end=end,
                )
                all_commits.extend(commits)
                prs = await connector.fetch_prs(
                    user_id=current_user.email,
                    start=start,
                    end=end,
                )
                all_prs.extend(prs)
            except Exception as e:
                logger.warning(
                    "Git connector %s failed: %s",
                    connector_info["name"],
                    e,
                )

    signals = analyzer.analyze(all_commits, all_prs, days=days)

    return {
        "success": True,
        "org_id": org_id,
        "days": days,
        "commit_count": len(all_commits),
        "pr_count": len(all_prs),
        "data_source": "live" if all_commits or all_prs else "no_data",
        "signals": asdict(signals),
    }


@router.get("/burnout/{org_id}")
async def get_git_burnout_signals(
    org_id: str,
    days: int = Query(14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
):
    """Burnout risk signals derived from Git metadata only."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_commits = []
    all_prs = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for connector_info in registry.list_connectors():
        connector = registry.get(connector_info["name"])
        if connector:
            try:
                all_commits.extend(
                    await connector.fetch_commits(
                        user_id=current_user.email,
                        start=start,
                        end=end,
                    )
                )
                all_prs.extend(
                    await connector.fetch_prs(
                        user_id=current_user.email,
                        start=start,
                        end=end,
                    )
                )
            except Exception:
                pass

    signals = analyzer.analyze(all_commits, all_prs, days=days)

    return {
        "success": True,
        "org_id": org_id,
        "days": days,
        "burnout": {
            "risk_score": signals.burnout_risk_score,
            "risk_label": signals.risk_label,
            "work_intensity": signals.work_intensity_score,
            "boundary_erosion": signals.boundary_erosion_score,
            "review_bottleneck": signals.review_bottleneck_score,
            "after_hours_ratio": signals.after_hours_ratio,
            "weekend_ratio": signals.weekend_ratio,
        },
        "recommendations": signals.recommendations,
    }


@router.get("/status")
async def get_git_metadata_status(
    current_user: User = Depends(get_current_user),
):
    """Check which Git metadata connectors are registered."""
    registry = _get_registry()
    connectors = registry.list_connectors()

    return {
        "success": True,
        "connectors": connectors,
        "available": len(connectors) > 0,
        "privacy_note": "Only Git metadata is accessed. Code, diffs, and commit messages are never read.",
    }
