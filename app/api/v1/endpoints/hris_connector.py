"""
HRIS Connector & Analytics API Endpoints

Wired to the enterprise HRIS service — manages connector registration,
health checks, data sync, and behavioral analytics from HR platforms.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.db.models.team import Team, TeamMember
from app.db.models.user import User
from app.services.enterprise_hris_service import (
    ADPConnector,
    BambooHRConnector,
    HiBobConnector,
    HRISBehavioralAnalyzer,
    HRISRegistry,
    OracleHCMConnector,
    SAPSuccessFactorsConnector,
    UKGConnector,
    WorkdayConnector,
    hris_registry,
)
from app.services.hris_analytics_service import HRISAnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hris_analytics", tags=["HRIS Analytics"])

_analyzer = HRISBehavioralAnalyzer()
_analytics = HRISAnalyticsService()


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


@router.get("/providers/available")
async def get_available_providers(
    current_user: User = Depends(get_current_user),
):
    return {
        "success": True,
        "providers": {
            name: {
                "name": name.replace("_", " ").title(),
                "connector_class": cls.__name__,
                "setup_difficulty": {
                    "workday": "Intermediate",
                    "sap_successfactors": "Advanced",
                    "bamboohr": "Easy",
                    "hibob": "Easy",
                    "adp": "Advanced",
                    "ukg": "Intermediate",
                    "oracle_hcm": "Intermediate",
                }.get(name, "Intermediate"),
            }
            for name, cls in HRISRegistry.CONNECTOR_TYPES.items()
        },
        "registered_connectors": hris_registry.list_connectors(),
    }


# ---------------------------------------------------------------------------
# Connections
# ---------------------------------------------------------------------------


@router.get("/connections/{organization_id}")
async def get_hris_connections(
    organization_id: str,
    current_user: User = Depends(get_current_user),
):
    connectors = hris_registry.list_connectors()
    connections = []
    for c in connectors:
        connector = hris_registry.get(c["name"])
        if connector:
            health = await connector.test_connection()
            connections.append(
                {
                    "name": c["name"],
                    "type": c["type"],
                    "connected": health.connected,
                    "data_freshness": health.data_freshness,
                    "employee_count": health.employee_count,
                    "error": health.error,
                }
            )

    return {
        "success": True,
        "organization_id": organization_id,
        "total_connections": len(connections),
        "connections": connections,
    }


@router.post("/connection/setup")
async def setup_hris_connection(
    body: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register an HRIS connector with provided credentials."""
    if not body:
        raise HTTPException(status_code=400, detail="Request body required")

    provider = body.get("provider", "").lower()
    name = body.get("name", provider)

    if provider == "workday":
        connector = WorkdayConnector(
            tenant_url=body.get("tenant_url", ""),
            client_id=body.get("client_id", ""),
            client_secret=body.get("client_secret", ""),
            tenant_name=body.get("tenant_name", ""),
        )
    elif provider == "sap_successfactors":
        connector = SAPSuccessFactorsConnector(
            api_url=body.get("api_url", ""),
            company_id=body.get("company_id", ""),
            username=body.get("username", ""),
            password=body.get("password", ""),
        )
    elif provider == "bamboohr":
        connector = BambooHRConnector(
            subdomain=body.get("subdomain", ""),
            api_key=body.get("api_key", ""),
        )
    elif provider == "hibob":
        connector = HiBobConnector(
            api_token=body.get("api_token", ""),
            company_domain=body.get("company_domain", ""),
        )
    elif provider == "adp":
        connector = ADPConnector(
            client_id=body.get("client_id", ""),
            client_secret=body.get("client_secret", ""),
            cert_path=body.get("cert_path"),
            key_path=body.get("key_path"),
        )
    elif provider == "ukg":
        connector = UKGConnector(
            api_url=body.get("api_url", ""),
            customer_api_key=body.get("customer_api_key", ""),
            username=body.get("username", ""),
            password=body.get("password", ""),
            user_api_key=body.get("user_api_key", ""),
        )
    elif provider == "oracle_hcm":
        connector = OracleHCMConnector(
            base_url=body.get("base_url", ""),
            username=body.get("username", ""),
            password=body.get("password", ""),
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {provider}. Available: {list(HRISRegistry.CONNECTOR_TYPES.keys())}",
        )

    # Test connection before registering
    health = await connector.test_connection()
    if not health.connected:
        return {
            "success": False,
            "connection_status": "failed",
            "error_message": health.error or "Connection test failed",
        }

    hris_registry.register(name, connector)

    return {
        "success": True,
        "connection_status": "connected",
        "provider": provider,
        "name": name,
        "data_freshness": health.data_freshness,
        "employee_count": health.employee_count,
        "connected_at": datetime.utcnow().isoformat(),
    }


@router.delete("/connection/{connection_id}")
async def disconnect_hris(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    connector = hris_registry.get(connection_id)
    if not connector:
        raise HTTPException(
            status_code=404, detail=f"Connection '{connection_id}' not found"
        )

    # Remove from registry (re-create without this connector)
    hris_registry._connectors.pop(connection_id, None)

    return {
        "success": True,
        "connection_id": connection_id,
        "disconnected_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


@router.post("/sync/manual")
async def trigger_manual_sync(
    body: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a manual data sync from all registered connectors."""
    connectors = hris_registry.list_connectors()
    if not connectors:
        return {"success": False, "sync_status": "no_connections"}

    results = []
    for c in connectors:
        connector = hris_registry.get(c["name"])
        if connector:
            try:
                employees = await connector.fetch_employees()
                results.append(
                    {
                        "connector": c["name"],
                        "status": "synced",
                        "employees_fetched": len(employees),
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "connector": c["name"],
                        "status": "error",
                        "error": str(e),
                    }
                )

    return {
        "success": True,
        "sync_status": "completed",
        "results": results,
        "synced_at": datetime.utcnow().isoformat(),
    }


@router.get("/sync/status/{connection_id}")
async def get_sync_status(
    connection_id: str,
    current_user: User = Depends(get_current_user),
):
    connector = hris_registry.get(connection_id)
    if not connector:
        return {
            "success": False,
            "connection_id": connection_id,
            "sync_status": {"status": "not_found"},
        }

    health = await connector.test_connection()
    return {
        "success": True,
        "connection_id": connection_id,
        "sync_status": {
            "status": "connected" if health.connected else "disconnected",
            "last_sync": health.last_sync,
            "data_freshness": health.data_freshness,
            "employee_count": health.employee_count,
        },
    }


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@router.post("/configuration/update")
async def update_configuration(
    body: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return {"success": True, "updated_configuration": body or {}}


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


@router.get("/analytics/dashboard/{organization_id}")
async def get_analytics_dashboard(
    organization_id: str,
    time_period: str = Query(default="90d"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard combining HRIS connector data with DB team/member counts."""
    connectors = hris_registry.list_connectors()

    # Get org member count from DB
    member_result = await db.execute(
        select(func.count(func.distinct(TeamMember.user_id)))
        .join(Team, Team.id == TeamMember.team_id)
        .where(Team.organization_id == organization_id)
    )
    member_count = member_result.scalar() or 0

    # Get team count
    team_result = await db.execute(
        select(func.count(Team.id)).where(Team.organization_id == organization_id)
    )
    team_count = team_result.scalar() or 0

    # If connectors are registered, fetch and analyze employee data
    hris_employees = []
    for c in connectors:
        connector = hris_registry.get(c["name"])
        if connector:
            try:
                emps = await connector.fetch_employees()
                hris_employees.extend(emps)
            except Exception:
                pass

    behavioral_signals = (
        _analyzer.analyze(hris_employees)
        if hris_employees
        else {"status": "no_hris_data", "signals": []}
    )

    # Serialize employee data for analytics service
    employee_dicts = [
        {
            "department": e.department,
            "job_title": e.job_title,
            "status": e.status.value,
            "location": e.location,
            "tenure_days": e.tenure_days,
            "hire_date": e.hire_date.isoformat() if e.hire_date else None,
            "last_performance_score": e.last_performance_score,
            "leave_days_used": e.leave_days_used,
            "leave_days_total": e.leave_days_total,
        }
        for e in hris_employees
    ]
    hris_data = {"employees": employee_dicts}

    # Run real analytics when employee data is available
    analytics = {}
    if employee_dicts:
        analytics = await _analytics.get_dashboard_data(
            organization_id=0,
            time_period=time_period,
            hris_data=hris_data,
        )

    return {
        "success": True,
        "organization_id": organization_id,
        "time_period": time_period,
        "dashboard_data": {
            "total_employees": max(member_count, len(hris_employees)),
            "active_employees": member_count,
            "departments": list(
                behavioral_signals.get("department_distribution", {}).keys()
            ),
            "workforce_metrics": {
                "avg_tenure_days": behavioral_signals.get("avg_tenure_days", 0),
                "avg_leave_utilization": behavioral_signals.get(
                    "avg_leave_utilization_pct", 0
                ),
                "avg_performance_score": behavioral_signals.get(
                    "avg_performance_score"
                ),
                "teams": team_count,
            },
            "behavioral_signals": behavioral_signals.get("signals", []),
            "hris_connectors": len(connectors),
            "analytics": analytics,
        },
    }


@router.post("/analytics/workforce")
async def analyze_workforce(
    body: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run behavioral analysis on HRIS employee data."""
    connectors = hris_registry.list_connectors()
    all_employees = []
    for c in connectors:
        connector = hris_registry.get(c["name"])
        if connector:
            try:
                emps = await connector.fetch_employees()
                all_employees.extend(emps)
            except Exception:
                pass

    analysis = _analyzer.analyze(all_employees)

    # Serialize for analytics service
    employee_dicts = [
        {
            "department": e.department,
            "job_title": e.job_title,
            "status": e.status.value,
            "location": e.location,
            "tenure_days": e.tenure_days,
            "hire_date": e.hire_date.isoformat() if e.hire_date else None,
            "last_performance_score": e.last_performance_score,
            "leave_days_used": e.leave_days_used,
            "leave_days_total": e.leave_days_total,
        }
        for e in all_employees
    ]
    hris_data = {"employees": employee_dicts}

    # Run full analytics suite
    analytics_type = (body or {}).get("analytics_type", "demographics")
    analytics_results = {}
    if employee_dicts:
        if analytics_type == "demographics":
            analytics_results = await _analytics.analyze_workforce_demographics(
                hris_data
            )
        elif analytics_type == "performance":
            analytics_results = await _analytics.analyze_employee_performance(hris_data)
        elif analytics_type == "turnover":
            analytics_results = await _analytics.analyze_turnover_patterns(hris_data)
        elif analytics_type == "engagement":
            analytics_results = await _analytics.analyze_employee_engagement(hris_data)
        elif analytics_type == "compensation":
            analytics_results = await _analytics.analyze_compensation_equity(hris_data)
        elif analytics_type == "learning_development":
            analytics_results = await _analytics.analyze_learning_development(hris_data)
        elif analytics_type == "succession":
            analytics_results = await _analytics.analyze_succession_readiness(hris_data)

    insights = await _analytics.generate_workforce_insights(
        analytics_results, analytics_type
    )

    return {
        "success": True,
        "analytics_type": analytics_type,
        "analytics_results": analytics_results,
        "behavioral_signals": analysis,
        "workforce_insights": insights,
        "workforce_metrics": {
            "total_employees": analysis.get("total_employees", 0),
            "avg_tenure_days": analysis.get("avg_tenure_days", 0),
        },
    }


@router.post("/employees/data")
async def get_employee_data(
    body: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch normalized employee data from all registered HRIS connectors."""
    connectors = hris_registry.list_connectors()
    all_employees = []
    for c in connectors:
        connector = hris_registry.get(c["name"])
        if connector:
            try:
                emps = await connector.fetch_employees()
                all_employees.extend(emps)
            except Exception:
                pass

    # Serialize dataclass instances
    employee_data = [
        {
            "id": e.id,
            "source": e.source,
            "email": e.email,
            "department": e.department,
            "job_title": e.job_title,
            "status": e.status.value,
            "location": e.location,
            "tenure_days": e.tenure_days,
            "last_performance_score": e.last_performance_score,
        }
        for e in all_employees
    ]

    return {
        "success": True,
        "total_employees": len(employee_data),
        "employee_data": {"employees": employee_data},
    }


# ---------------------------------------------------------------------------
# Engagement
# ---------------------------------------------------------------------------


@router.get("/engagement/individual-scores")
async def get_engagement_scores(
    organization_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Engagement scores derived from assessment response activity."""
    from app.db.models.response import Response
    from sqlalchemy import and_
    from datetime import timedelta

    if not organization_id:
        return {"success": True, "scores": [], "organization_id": organization_id}

    # Get org members
    member_result = await db.execute(
        select(TeamMember.user_id)
        .join(Team, Team.id == TeamMember.team_id)
        .where(Team.organization_id == organization_id)
        .distinct()
    )
    member_ids = [str(r[0]) for r in member_result.all()]

    if not member_ids:
        return {"success": True, "scores": [], "organization_id": organization_id}

    since = datetime.utcnow() - timedelta(days=30)

    # Per-user response count and avg score as engagement proxy
    result = await db.execute(
        select(
            Response.user_id,
            func.count(Response.id),
            func.avg(Response.answer_value),
        )
        .where(
            and_(
                Response.user_id.in_(member_ids),
                Response.created_at >= since,
            )
        )
        .group_by(Response.user_id)
    )

    scores = []
    for user_id, count, avg_val in result.all():
        # Engagement score: response frequency (0-50) + avg satisfaction (0-50)
        freq_score = min(50, count * 5)
        sat_score = min(50, (float(avg_val or 3) / 5) * 50)
        engagement = round(freq_score + sat_score, 1)
        scores.append(
            {
                "user_id": str(user_id),
                "engagement_score": engagement,
                "response_count": count,
                "avg_satisfaction": round(float(avg_val or 0), 2),
            }
        )

    return {
        "success": True,
        "scores": sorted(scores, key=lambda s: s["engagement_score"], reverse=True),
        "organization_id": organization_id,
    }
