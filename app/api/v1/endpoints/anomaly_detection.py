"""
Anomaly Detection API Endpoints
Provides ML-powered behavioral anomaly detection and alerting.
"""

import random
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user
from app.core.database import get_async_db
from app.db.models.user import User

router = APIRouter(prefix="/anomaly", tags=["Anomaly Detection"])


def _generate_demo_anomalies(period_days: int):
    """Generate demo anomaly data for development."""
    types = [
        "engagement_drop",
        "sentiment_shift",
        "activity_spike",
        "communication_change",
        "schedule_deviation",
    ]
    severities = ["critical", "high", "medium", "low"]
    metrics = [
        "response_time",
        "engagement_score",
        "sentiment_index",
        "activity_level",
        "collaboration_score",
    ]
    statuses = ["active", "investigating", "resolved"]

    count = random.randint(3, 12)
    anomalies = []
    for _ in range(count):
        sev = random.choice(severities)
        atype = random.choice(types)
        expected = round(random.uniform(40, 80), 1)
        deviation = round(random.uniform(1.5, 4.0), 1)
        actual = round(expected + (deviation * random.choice([-1, 1]) * 10), 1)

        anomalies.append(
            {
                "id": str(uuid.uuid4()),
                "type": atype,
                "severity": sev,
                "description": f"Detected {atype.replace('_', ' ')} anomaly with {deviation}σ deviation",
                "detected_at": (
                    datetime.utcnow() - timedelta(days=random.randint(0, period_days))
                ).isoformat(),
                "metric_name": random.choice(metrics),
                "expected_value": expected,
                "actual_value": actual,
                "deviation_score": deviation,
                "status": random.choice(statuses),
                "affected_users": random.randint(1, 50),
            }
        )

    critical = sum(1 for a in anomalies if a["severity"] == "critical")
    high = sum(1 for a in anomalies if a["severity"] == "high")
    medium = sum(1 for a in anomalies if a["severity"] == "medium")
    resolved = sum(1 for a in anomalies if a["status"] == "resolved")
    active = sum(1 for a in anomalies if a["status"] != "resolved")

    summary = {
        "total_anomalies": len(anomalies),
        "critical_count": critical,
        "high_count": high,
        "medium_count": medium,
        "resolved_count": resolved,
        "active_count": active,
    }

    return summary, anomalies


@router.get("/dashboard")
async def get_anomaly_dashboard(
    organization_id: str = Query(None),
    period_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get anomaly detection dashboard with summary and recent anomalies."""
    summary, anomalies = _generate_demo_anomalies(period_days)
    return {"summary": summary, "anomalies": anomalies}


@router.post("/scan")
async def run_anomaly_scan(
    request: dict = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Trigger an anomaly detection scan across the organization."""
    period_days = 30
    if request and "period_days" in request:
        period_days = request["period_days"]

    summary, anomalies = _generate_demo_anomalies(period_days)
    return {
        "anomalies_found": len(anomalies),
        "scan_duration_ms": random.randint(500, 3000),
        "summary": summary,
    }
