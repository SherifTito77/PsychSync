"""
PsychSync Radar API Endpoints
Quick Win Dashboard - Unified 360° organizational health monitoring
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.core.logging_config import logger
from app.db.models.user import User
from app.services.radar_service import RadarZone, radar_service

router = APIRouter(prefix="/radar", tags=["radar"])


# ============================================
# Pydantic Models
# ============================================


class RadarViewRequest(BaseModel):
    """Request model for radar view"""

    organization_id: str
    team_id: Optional[str] = None
    period_days: int = Field(default=30, ge=1, le=90)


class ConcentricZone(BaseModel):
    """Concentric zone metrics"""

    name: str
    risk_score: float
    zone: str


class ZoneClassification(BaseModel):
    """Zone classification result"""

    zone: str
    zone_label: str
    overall_risk_score: float
    confidence: float
    risk_components: List[Dict[str, Any]]
    recommendation: str


class Hotspot(BaseModel):
    """Identified hotspot"""

    type: str
    severity: float
    description: str
    priority: str


class RadarViewResponse(BaseModel):
    """Response model for radar view"""

    organization_id: str
    team_id: Optional[str]
    analysis_date: str
    period_days: int
    toxicity_analysis: Dict[str, Any]
    early_warnings: Dict[str, Any]
    behavioral_patterns: Dict[str, Any]
    psychological_safety: Dict[str, Any]
    zone_classification: ZoneClassification
    concentric_zones: Dict[str, ConcentricZone]
    active_interventions: Dict[str, Any]
    trends: Dict[str, Any]
    hotspots: List[Hotspot]


class QuickStatsResponse(BaseModel):
    """Quick statistics for dashboard overview"""

    zone: str
    zone_label: str
    overall_risk_score: float
    total_patterns: int
    critical_patterns: int
    active_interventions: int
    psych_safety_score: Optional[float]
    trend_direction: str


# ============================================
# Endpoints
# ============================================


@router.post("/view", response_model=RadarViewResponse)
async def get_radar_view(
    request: RadarViewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get comprehensive 360° radar view of organizational health
    """
    try:
        # Get radar view
        radar_data = await radar_service.get_radar_view(
            db=db,
            organization_id=str(request.organization_id),
            team_id=str(request.team_id) if request.team_id else None,
            period_days=request.period_days,
        )

        # Check for errors
        if "error" in radar_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate radar view: {radar_data['error']}",
            )

        return RadarViewResponse(**radar_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get radar view: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate radar view: {str(e)}",
        )


@router.get("/quick-stats", response_model=QuickStatsResponse)
async def get_quick_stats(
    organization_id: str,
    team_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get quick statistics for dashboard overview
    """
    try:
        # Get radar view with default 30-day period
        radar_data = await radar_service.get_radar_view(
            db=db,
            organization_id=organization_id,
            team_id=team_id,
            period_days=30,
        )

        if "error" in radar_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=radar_data["error"],
            )

        zone_class = radar_data["zone_classification"]
        toxicity = radar_data["toxicity_analysis"]
        interventions = radar_data["active_interventions"]
        psych_safety = radar_data["psychological_safety"]
        trends = radar_data["trends"]

        return QuickStatsResponse(
            zone=zone_class["zone"],
            zone_label=zone_class["zone_label"],
            overall_risk_score=zone_class["overall_risk_score"],
            total_patterns=len(toxicity.get("patterns_detected", [])),
            critical_patterns=len(
                [
                    p
                    for p in toxicity.get("patterns_detected", [])
                    if p.get("severity_score", 0) >= 0.6
                ]
            ),
            active_interventions=interventions.get("active_count", 0),
            psych_safety_score=psych_safety.get("overall_safety_score"),
            trend_direction=(
                trends.get("summary", {}).get("trend_direction", "unknown")
                if isinstance(trends, dict)
                else "unknown"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quick stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quick stats: {str(e)}",
        )


@router.get("/zone-history")
async def get_zone_history(
    organization_id: str,
    team_id: Optional[str] = None,
    days_back: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get historical zone classification history
    """
    try:
        # Get trend data
        radar_data = await radar_service.get_radar_view(
            db=db,
            organization_id=organization_id,
            team_id=team_id,
            period_days=days_back,
        )

        trends = radar_data.get("trends", {}).get("trend_data", [])

        # Calculate historical zones
        zone_history = []
        for trend in trends:
            # Calculate zone from pattern counts
            pattern_count = trend.get("pattern_count", 0)
            critical_count = trend.get("critical_patterns", 0)

            if critical_count > 0 or pattern_count > 5:
                zone = RadarZone.RED
            elif pattern_count > 2:
                zone = RadarZone.YELLOW
            else:
                zone = RadarZone.GREEN

            zone_history.append(
                {
                    "date": trend.get("date"),
                    "zone": zone,
                    "pattern_count": pattern_count,
                    "critical_patterns": critical_count,
                }
            )

        return {
            "organization_id": str(organization_id),
            "team_id": str(team_id) if team_id else None,
            "period_days": days_back,
            "zone_history": zone_history,
            "current_zone": radar_data.get("zone_classification", {}).get("zone"),
            "trend_direction": (
                trends.get("summary", {}).get("trend_direction", "unknown")
                if isinstance(trends, dict)
                else "unknown"
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get zone history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get zone history: {str(e)}",
        )


@router.get("/hotspots")
async def get_hotspots(
    organization_id: str,
    team_id: Optional[str] = None,
    severity_threshold: float = Query(default=0.5, ge=0.0, le=1.0),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get identified hotspots requiring attention
    """
    try:
        # Get radar data
        radar_data = await radar_service.get_radar_view(
            db=db,
            organization_id=organization_id,
            team_id=team_id,
            period_days=30,
        )

        hotspots = radar_data.get("hotspots", [])

        # Filter by severity threshold
        filtered_hotspots = [
            h for h in hotspots if h.get("severity", 0) >= severity_threshold
        ][:limit]

        return {
            "organization_id": str(organization_id),
            "team_id": str(team_id) if team_id else None,
            "total_hotspots": len(hotspots),
            "filtered_hotspots": len(filtered_hotspots),
            "severity_threshold": severity_threshold,
            "hotspots": filtered_hotspots,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get hotspots: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hotspots: {str(e)}",
        )


@router.get("/concentric-zones")
async def get_concentric_zones(
    organization_id: str,
    team_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get concentric zone metrics for radar visualization
    """
    try:
        # Get radar data
        radar_data = await radar_service.get_radar_view(
            db=db,
            organization_id=organization_id,
            team_id=team_id,
            period_days=30,
        )

        return {
            "organization_id": str(organization_id),
            "team_id": str(team_id) if team_id else None,
            "analysis_date": radar_data.get("analysis_date"),
            "concentric_zones": radar_data.get("concentric_zones", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get concentric zones: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get concentric zones: {str(e)}",
        )
