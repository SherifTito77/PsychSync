# app/api/v1/endpoints/corporate_integrations.py
"""
API endpoints for Corporate Data Source Integration Management
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.db.models.user import User
from app.integrations.corporate_data_sources import (
    INTEGRATION_PRIORITY,
    CorporateDataSourceRegistry,
    DataSourceType,
)
from app.schemas.corporate_data_sources import (
    BehavioralAnalysisRequest,
    BehavioralInsight,
    BulkIntegrationRequest,
    CreateIntegrationRequest,
    IntegrationConfig,
    IntegrationHealthMetrics,
    IntegrationInsightsReport,
    IntegrationResponse,
    IntegrationStatus,
    OrganizationIntegrations,
    SyncIntegrationRequest,
    UpdateIntegrationRequest,
)

router = APIRouter(prefix="/integrations/corporate", tags=["corporate-integrations"])


@router.get("/test-auth")
async def test_auth(current_user: User = Depends(get_current_user)):
    """Test authentication is working"""
    return {
        "success": True,
        "user_email": current_user.email,
        "user_id": str(current_user.id),
        "message": "Authentication works!",
    }


@router.get("/organization", response_model=OrganizationIntegrations)
async def get_organization_integrations(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get all integrations for the current user's organization
    """
    # TODO: Implement database lookup for organization integrations
    # For now, return registry data
    all_sources = CorporateDataSourceRegistry.get_all_sources()

    integrations = []
    for source_type, config in all_sources.items():
        # Mock status - in production, fetch from database
        mock_status = IntegrationStatus(
            source_type=source_type,
            status="active" if config.enabled else "disabled",
            last_sync=datetime.utcnow() - timedelta(hours=1),
            next_sync=datetime.utcnow() + timedelta(hours=config.sync_frequency_hours),
            records_processed=0,
            health_score=0.95,
        )

        mock_response = IntegrationResponse(
            config=config,
            status=mock_status,
            behavioral_signals=config.behavioral_signals,
            data_points_count=0,
        )
        integrations.append(mock_response)

    return OrganizationIntegrations(
        organization_id=getattr(current_user, "organization_id", None) or 1,
        integrations=integrations,
        summary={
            "total_integrations": len(integrations),
            "active_integrations": sum(
                1 for i in integrations if i.status.status == "active"
            ),
            "total_data_points": sum(i.data_points_count for i in integrations),
            "coverage_percentage": 75.0,
        },
        recommendations=[
            "Enable email metadata integration for communication pattern analysis",
            "Connect Slack or Teams for real-time team dynamics monitoring",
            "Set up pulse surveys for direct employee feedback",
        ],
    )


@router.get("/available", response_model=List[Dict[str, Any]])
async def get_available_data_sources():
    """
    Get metadata about all available data source types
    """
    all_sources = CorporateDataSourceRegistry.get_all_sources()

    available = []
    for source_type, config in all_sources.items():
        available.append(
            {
                "type": source_type.value,
                "name": source_type.value.replace("_", " ").title(),
                "description": f"Extracts behavioral signals from {source_type.value}",
                "category": _get_category_for_source(source_type),
                "priority": _get_priority_for_source(source_type),
                "requires_consent": config.requires_consent,
                "behavioral_signals": config.behavioral_signals,
            }
        )

    return available


@router.get("/recommendations")
async def get_integration_recommendations(
    organization_size: int = Query(..., description="Number of employees"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get recommended integrations based on organization size
    """
    recommended_types = CorporateDataSourceRegistry.get_recommended_sources_by_org_size(
        organization_size
    )

    # Generate reasons for each recommendation
    reasons = {}
    for source_type in recommended_types:
        reasons[source_type] = _get_recommendation_reason(
            source_type, organization_size
        )

    return {
        "recommended": [t.value for t in recommended_types],
        "reasons": {k.value: v for k, v in reasons.items()},
    }


@router.post("/bulk-setup")
async def setup_bulk_integrations(
    request: BulkIntegrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Setup multiple integrations at once based on organization size and preferences
    """
    # Get recommended sources
    recommended_types = CorporateDataSourceRegistry.get_recommended_sources_by_org_size(
        request.organization_size
    )

    # Filter by privacy preference
    if request.privacy_preference == "minimal":
        filtered_types = [
            t
            for t in recommended_types
            if not CorporateDataSourceRegistry.get_all_sources()[t].requires_consent
        ]
    elif request.privacy_preference == "comprehensive":
        filtered_types = recommended_types
    else:  # balanced
        filtered_types = recommended_types[:8]  # Top 8

    # TODO: Create integrations in database
    created_count = len(filtered_types)

    # Mock response
    all_sources = CorporateDataSourceRegistry.get_all_sources()
    integrations = []
    for source_type in filtered_types:
        config = all_sources[source_type]
        mock_status = IntegrationStatus(
            source_type=source_type,
            status="active" if request.auto_enable_recommended else "pending",
            records_processed=0,
            health_score=1.0,
        )
        integrations.append(
            IntegrationResponse(
                config=config,
                status=mock_status,
                behavioral_signals=config.behavioral_signals,
                data_points_count=0,
            )
        )

    return {"created": created_count, "integrations": integrations}


@router.get("/{source_type}", response_model=IntegrationResponse)
async def get_integration(
    source_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get details of a specific integration
    """
    # Validate source type
    try:
        data_source_type = DataSourceType(source_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source type: {source_type}",
        )

    # Get config from registry
    all_sources = CorporateDataSourceRegistry.get_all_sources()
    if data_source_type not in all_sources:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration not found: {source_type}",
        )

    config = all_sources[data_source_type]

    # TODO: Fetch actual integration status from database
    mock_status = IntegrationStatus(
        source_type=data_source_type,
        status="active",
        last_sync=datetime.utcnow() - timedelta(hours=1),
        next_sync=datetime.utcnow() + timedelta(hours=config.sync_frequency_hours),
        records_processed=1000,
        health_score=0.95,
    )

    return IntegrationResponse(
        config=config,
        status=mock_status,
        behavioral_signals=config.behavioral_signals,
        data_points_count=1000,
    )


@router.post(
    "", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED
)
async def create_integration(
    request: CreateIntegrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new integration
    """
    # TODO: Validate API credentials
    # TODO: Store integration in database

    all_sources = CorporateDataSourceRegistry.get_all_sources()
    config = all_sources.get(request.source_type)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown source type: {request.source_type}",
        )

    # Create integration config from request
    integration_config = IntegrationConfig(
        source_type=request.source_type,
        enabled=True,
        privacy_level=request.privacy_level,
        sync_frequency_hours=request.sync_frequency_hours,
        data_retention_days=request.data_retention_days,
        requires_consent=config.requires_consent,
        api_credentials=request.api_credentials,
        custom_settings=request.custom_settings,
    )

    mock_status = IntegrationStatus(
        source_type=request.source_type,
        status="pending",
        records_processed=0,
        health_score=1.0,
    )

    return IntegrationResponse(
        config=integration_config,
        status=mock_status,
        behavioral_signals=config.behavioral_signals,
        data_points_count=0,
    )


@router.put("/{source_type}", response_model=IntegrationResponse)
async def update_integration(
    source_type: str,
    request: UpdateIntegrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing integration
    """
    # TODO: Update integration in database

    all_sources = CorporateDataSourceRegistry.get_all_sources()
    config = all_sources.get(DataSourceType(source_type))

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration not found: {source_type}",
        )

    mock_status = IntegrationStatus(
        source_type=DataSourceType(source_type),
        status="active",
        records_processed=1000,
        health_score=0.95,
    )

    return IntegrationResponse(
        config=config,
        status=mock_status,
        behavioral_signals=config.behavioral_signals,
        data_points_count=1000,
    )


@router.delete("/{source_type}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    source_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an integration
    """
    # TODO: Delete integration from database
    return None


@router.post("/{source_type}/sync")
async def trigger_sync(
    source_type: str,
    options: Optional[SyncIntegrationRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger manual sync for an integration
    """
    # TODO: Trigger async sync job
    # TODO: Return sync job ID for tracking

    return {
        "message": f"Sync initiated for {source_type}",
        "sync_id": f"sync_{source_type}_{datetime.utcnow().timestamp()}",
    }


@router.get("/health", response_model=IntegrationHealthMetrics)
async def get_health_metrics(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get health metrics for all integrations
    """
    # TODO: Calculate actual metrics from database

    return IntegrationHealthMetrics(
        total_integrations=10,
        active_integrations=8,
        error_integrations=1,
        total_data_points=50000,
        last_24h_ingestion_count=2500,
        avg_sync_latency_minutes=15.5,
        data_quality_score=0.92,
    )


@router.post("/analyze", response_model=List[BehavioralInsight])
async def analyze_behavioral_data(
    request: BehavioralAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze behavioral data across integrations
    """
    # TODO: Implement behavioral analysis engine
    # TODO: Query data from specified sources
    # TODO: Apply ML models for insight generation

    # Mock insights
    insights = [
        BehavioralInsight(
            category="burnout",
            severity="high",
            title="High Overtime Detected in Engineering Team",
            description="Analysis of time tracking and calendar data reveals 40% of engineers "
            "are consistently working >50 hours/week with insufficient recovery time.",
            affected_employees=[1, 2, 3, 4, 5],
            confidence=0.87,
            recommendations=[
                "Implement maximum weekly hour cap",
                "Add mandatory break reminders",
                "Review workload distribution",
                "Consider hiring additional resources",
            ],
            data_sources=[DataSourceType.TIME_TRACKING, DataSourceType.CALENDAR_EVENTS],
            detected_at=datetime.utcnow(),
        ),
        BehavioralInsight(
            category="toxicity",
            severity="medium",
            title="Conflict Patterns in Marketing Team",
            description="Email metadata analysis shows increased conflict language and "
            "decreased collaborative communication in marketing department.",
            affected_employees=[6, 7, 8],
            confidence=0.72,
            recommendations=[
                "Schedule team mediation session",
                "Review management practices",
                "Conduct anonymous pulse survey",
                "Provide conflict resolution training",
            ],
            data_sources=[DataSourceType.EMAIL_METADATA, DataSourceType.SLACK_MESSAGES],
            detected_at=datetime.utcnow(),
        ),
    ]

    return insights


@router.post("/reports/generate", response_model=IntegrationInsightsReport)
async def generate_insights_report(
    date_range: Dict[str, datetime],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate comprehensive insights report
    """
    date_range.get("start")
    date_range.get("end")

    # TODO: Generate actual report

    return IntegrationInsightsReport(
        report_id=f"report_{datetime.utcnow().timestamp()}",
        generated_at=datetime.utcnow(),
        date_range=date_range,
        organization_id=getattr(current_user, "organization_id", None) or 1,
        insights=[],  # Populate with actual insights
        health_metrics=IntegrationHealthMetrics(
            total_integrations=10,
            active_integrations=8,
            error_integrations=1,
            total_data_points=50000,
            last_24h_ingestion_count=2500,
            avg_sync_latency_minutes=15.5,
            data_quality_score=0.92,
        ),
        summary={
            "total_insights": 15,
            "critical_insights": 2,
            "high_insights": 5,
            "medium_insights": 6,
            "low_insights": 2,
        },
        recommendations=[
            "Address burnout risk in engineering team immediately",
            "Investigate communication patterns in marketing",
            "Consider implementing wellness program",
        ],
    )


@router.get("/reports/latest", response_model=IntegrationInsightsReport)
async def get_latest_report(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get the most recent insights report
    """
    # TODO: Fetch latest report from database
    # For now, return mock data

    return IntegrationInsightsReport(
        report_id=f"report_{datetime.utcnow().timestamp()}",
        generated_at=datetime.utcnow(),
        date_range={
            "start": datetime.utcnow() - timedelta(days=30),
            "end": datetime.utcnow(),
        },
        organization_id=getattr(current_user, "organization_id", None) or 1,
        insights=[],
        health_metrics=IntegrationHealthMetrics(
            total_integrations=10,
            active_integrations=8,
            error_integrations=1,
            total_data_points=50000,
            last_24h_ingestion_count=2500,
            avg_sync_latency_minutes=15.5,
            data_quality_score=0.92,
        ),
        summary={
            "total_insights": 15,
            "critical_insights": 2,
            "high_insights": 5,
            "medium_insights": 6,
            "low_insights": 2,
        },
        recommendations=[],
    )


# Helper functions


def _get_category_for_source(source_type: DataSourceType) -> str:
    """Map data source type to category"""
    communication_sources = [
        DataSourceType.EMAIL_METADATA,
        DataSourceType.SLACK_MESSAGES,
        DataSourceType.TEAMS_MESSAGES,
        DataSourceType.ZOOM_TRANSCRIPTS,
    ]

    productivity_sources = [
        DataSourceType.CALENDAR_EVENTS,
        DataSourceType.JIRA_ACTIVITY,
        DataSourceType.GITHUB_COMMITS,
        DataSourceType.CONFLUENCE_EDITS,
    ]

    hr_sources = [
        DataSourceType.WORKDAY_DATA,
        DataSourceType.BAMBOO_HR,
        DataSourceType.PERFORMANCE_REVIEWS,
        DataSourceType.TIME_TRACKING,
    ]

    if source_type in communication_sources:
        return "communication"
    elif source_type in productivity_sources:
        return "productivity"
    elif source_type in hr_sources:
        return "hr"
    else:
        return "other"


def _get_priority_for_source(source_type: DataSourceType) -> str:
    """Get priority level for a source"""
    for priority, sources in INTEGRATION_PRIORITY.items():
        if source_type in sources:
            return priority
    return "medium"


def _get_recommendation_reason(source_type: DataSourceType, org_size: int) -> str:
    """Get recommendation reason for a source"""
    reasons = {
        DataSourceType.EMAIL_METADATA: "Essential for communication pattern analysis",
        DataSourceType.CALENDAR_EVENTS: "Tracks meeting load and focus time",
        DataSourceType.PULSE_SURVEYS: "Direct feedback from employees",
        DataSourceType.SLACK_MESSAGES: "Real-time team dynamics monitoring",
        DataSourceType.JIRA_ACTIVITY: "Workload and deadline stress indicators",
    }
    return reasons.get(source_type, f"Valuable for {org_size} employee organizations")
