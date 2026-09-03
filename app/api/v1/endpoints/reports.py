"""
Advanced Reporting API Endpoints
REST API for report generation, templates, scheduling, and management
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db, get_current_active_user, get_current_user, get_db
from app.core.config import settings
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.db.models.reports import (
    ExportFormat,
    ReportStatus,
    ReportType,
    ScheduleFrequency,
)
from app.db.models.user import User
from app.services.reporting_service import (
    ReportGenerationRequest,
    ReportGenerationService,
)

router = APIRouter()


# Pydantic Models for API


class ReportGenerationRequestModel(BaseModel):
    """Request model for report generation"""

    template_id: Optional[UUID] = None
    report_type: ReportType = ReportType.CUSTOM
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=500)
    parameters: Dict[str, Any] = {}
    data_range_start: Optional[datetime] = None
    data_range_end: Optional[datetime] = None
    export_format: ExportFormat = ExportFormat.PDF
    team_id: Optional[UUID] = None
    is_public: bool = False
    shared_with: Optional[List[UUID]] = None
    retention_days: Optional[int] = Field(None, ge=1, le=365)

    @validator("data_range_end")
    def validate_date_range(cls, v, values):
        if v and "data_range_start" in values and values["data_range_start"]:
            if v <= values["data_range_start"]:
                raise ValueError("End date must be after start date")
        return v


class ReportTemplateRequest(BaseModel):
    """Request model for report template creation"""

    name: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=500)
    report_type: ReportType
    template_config: Dict[str, Any] = {}
    layout_config: Dict[str, Any] = {}
    data_config: Dict[str, Any] = {}
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: bool = False


class ReportScheduleRequest(BaseModel):
    """Request model for report scheduling"""

    name: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=500)
    template_id: UUID
    frequency: ScheduleFrequency
    schedule_config: Dict[str, Any] = {}
    delivery_method: str = Field(
        default="download", pattern="^(download|email|webhook)$"
    )
    delivery_config: Dict[str, Any] = {}
    custom_cron: Optional[str] = None
    end_date: Optional[datetime] = None
    default_format: ExportFormat = ExportFormat.PDF

    @validator("end_date")
    def validate_end_date(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError("End date must be in the future")
        return v


# Report Generation Endpoints


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post("/generate", response_model=Dict[str, Any])
async def generate_report(
    report_request: ReportGenerationRequestModel,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Generate a new report

    - **template_id**: Optional template ID to use
    - **report_type**: Type of report to generate
    - **title**: Report title
    - **description**: Report description
    - **parameters**: Report generation parameters
    - **data_range_start**: Start date for report data
    - **data_range_end**: End date for report data
    - **export_format**: Export format (PDF, Excel, CSV, JSON, PowerPoint)
    - **team_id**: Optional team filter
    - **is_public**: Whether report is publicly accessible
    - **shared_with**: List of user IDs to share with
    - **retention_days**: Number of days to retain report
    """
    try:
        reporting_service = ReportGenerationService(db)

        # Create report generation request
        request = ReportGenerationRequest(
            template_id=report_request.template_id,
            report_type=report_request.report_type,
            title=report_request.title,
            description=report_request.description,
            parameters=report_request.parameters,
            data_range_start=report_request.data_range_start,
            data_range_end=report_request.data_range_end,
            export_format=report_request.export_format,
            organization_id=current_user.organization_id,
            team_id=report_request.team_id,
            requested_by_id=current_user.id,
        )

        # Add retention days to parameters
        if report_request.retention_days:
            request.parameters["retention_days"] = report_request.retention_days

        # Generate report
        result = await reporting_service.generate_report(request)

        if result["success"]:
            return {
                "success": True,
                "message": "Report generation started successfully",
                "report_id": result["report_id"],
                "file_url": result.get("file_url"),
                "estimated_completion": "2-5 minutes",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Report generation failed"),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}",
        ) from e


@router.get("/list", response_model=Dict[str, Any])
async def list_reports(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    report_type: Optional[ReportType] = None,
    status: Optional[ReportStatus] = None,
    team_id: Optional[UUID] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get list of reports with filtering options

    - **limit**: Maximum number of reports to return
    - **offset**: Number of reports to skip
    - **report_type**: Filter by report type
    - **status**: Filter by status
    - **team_id**: Filter by team
    - **start_date**: Filter reports after this date
    - **end_date**: Filter reports before this date
    """
    try:
        reporting_service = ReportGenerationService(db)

        # Get date range
        date_range = None
        if start_date or end_date:
            date_range = (
                start_date or datetime.utcnow() - timedelta(days=30),
                end_date or datetime.utcnow(),
            )

        result = await reporting_service.list_reports(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            report_type=report_type,
            team_id=team_id,
            status=status,
            limit=limit,
            offset=offset,
            date_range=date_range,
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(detail=f"Failed to list reports: {str(e)}") from e


@router.get("/{report_id}", response_model=Dict[str, Any])
async def get_report(
    report_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get details of a specific report

    - **report_id**: UUID of the report
    """
    try:
        reporting_service = ReportGenerationService(db)

        report = await reporting_service.get_report(report_id, current_user.id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found or access denied",
            )

        return report

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(detail=f"Failed to get report: {str(e)}") from e


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Download a generated report file

    - **report_id**: UUID of the report to download
    """
    try:
        reporting_service = ReportGenerationService(db)

        # Get report details and verify access
        report = await reporting_service.get_report(report_id, current_user.id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found or access denied",
            )

        # Get file path from database
        from app.db.models.reports import GeneratedReport

        loop = asyncio.get_event_loop()
        report_record = await loop.run_in_executor(
            None,
            lambda: db.query(GeneratedReport)
            .filter(GeneratedReport.id == report_id)
            .first(),
        )

        if not report_record or not report_record.file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found"
            )

        # Return file response (implementation would use FastAPI FileResponse)
        # return FileResponse(
        #     path=report_record.file_path,
        #     filename=report_record.file_name,
        #     media_type='application/octet-stream'
        # )

        return {
            "download_url": f"/api/v1/reports/{report_id}/download",
            "filename": report_record.file_name,
            "file_size": report_record.file_size,
            "format": report_record.file_format.value,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(detail=f"Failed to download report: {str(e)}") from e


# Template Management Endpoints


@router.post("/templates", response_model=Dict[str, Any])
async def create_template(
    template_data: ReportTemplateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new report template

    - **name**: Template name
    - **description**: Template description
    - **report_type**: Type of report this template generates
    - **template_config**: Template configuration
    - **layout_config**: Layout and styling configuration
    - **data_config**: Data sources and filters configuration
    - **category**: Template category
    - **tags**: Template tags
    - **is_public**: Whether template is publicly accessible
    """
    try:
        reporting_service = ReportGenerationService(db)

        result = await reporting_service.create_template(
            name=template_data.name,
            description=template_data.description,
            report_type=template_data.report_type,
            template_config=template_data.template_config,
            layout_config=template_data.layout_config,
            data_config=template_data.data_config,
            created_by_id=current_user.id,
            organization_id=current_user.organization_id,
            category=template_data.category,
            tags=template_data.tags,
        )

        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "template_id": result["template_id"],
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Template creation failed"),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(detail=f"Failed to create template: {str(e)}") from e


@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_templates(
    report_type: Optional[ReportType] = None,
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get available report templates

    - **report_type**: Filter by report type
    - **category**: Filter by category
    - **is_public**: Filter by public status
    """
    try:
        reporting_service = ReportGenerationService(db)

        templates = await reporting_service.get_templates(
            organization_id=current_user.organization_id,
            report_type=report_type,
            category=category,
            is_public=is_public,
        )

        return templates

    except Exception as e:
        raise HTTPException(detail=f"Failed to get templates: {str(e)}") from e


# Scheduling Endpoints


@router.post("/schedules", response_model=Dict[str, Any])
async def create_schedule(
    schedule_data: ReportScheduleRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new report schedule

    - **name**: Schedule name
    - **description**: Schedule description
    - **template_id**: Template to use for scheduled reports
    - **frequency**: How often to generate the report
    - **schedule_config**: Schedule-specific configuration
    - **delivery_method**: How to deliver the report
    - **delivery_config**: Delivery configuration
    - **custom_cron**: Custom cron expression
    - **end_date**: When to stop scheduling
    - **default_format**: Default export format
    """
    try:
        reporting_service = ReportGenerationService(db)

        result = await reporting_service.create_schedule(
            name=schedule_data.name,
            description=schedule_data.description,
            template_id=schedule_data.template_id,
            frequency=schedule_data.frequency,
            schedule_config=schedule_data.schedule_config,
            delivery_method=schedule_data.delivery_method,
            delivery_config=schedule_data.delivery_config,
            created_by_id=current_user.id,
            organization_id=current_user.organization_id,
            custom_cron=schedule_data.custom_cron,
            end_date=schedule_data.end_date,
        )

        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "schedule_id": result["schedule_id"],
                "next_run": result["next_run"],
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Schedule creation failed"),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(detail=f"Failed to create schedule: {str(e)}") from e


@router.get("/schedules", response_model=List[Dict[str, Any]])
async def get_schedules(
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get report schedules

    - **is_active**: Filter by active status
    """
    try:
        reporting_service = ReportGenerationService(db)

        schedules = await reporting_service.get_schedules(
            organization_id=current_user.organization_id, is_active=is_active
        )

        return schedules

    except Exception as e:
        raise HTTPException(detail=f"Failed to get schedules: {str(e)}") from e


# Analytics Endpoints


@router.get("/analytics", response_model=Dict[str, Any])
async def get_report_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get comprehensive report analytics

    - **days**: Number of days to include in analysis
    """
    try:
        reporting_service = ReportGenerationService(db)

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        date_range = (start_date, end_date)

        analytics = await reporting_service.get_report_analytics(
            organization_id=current_user.organization_id, date_range=date_range
        )

        if "error" in analytics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=analytics["error"]
            )

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(detail=f"Failed to get report analytics: {str(e)}") from e


# System Administration Endpoints


@router.post("/execute-scheduled", response_model=Dict[str, Any])
async def execute_scheduled_reports(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Execute all pending scheduled reports (Admin only)
    """
    try:
        # Only admins can execute scheduled reports
        if not current_user.is_admin and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can execute scheduled reports",
            )

        reporting_service = ReportGenerationService(db)

        # Execute scheduled reports in background
        background_tasks.add_task(reporting_service.execute_scheduled_reports)

        return {
            "success": True,
            "message": "Scheduled report execution started",
            "status": "running",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            detail=f"Failed to execute scheduled reports: {str(e)}"
        ) from e


@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_expired_reports(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Clean up expired reports (Admin only)
    """
    try:
        # Only admins can cleanup reports
        if not current_user.is_admin and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can cleanup reports",
            )

        reporting_service = ReportGenerationService(db)

        # Clean up expired reports
        reports_cleaned = await reporting_service.cleanup_expired_reports()
        cache_cleaned = await reporting_service.cleanup_expired_cache()

        return {
            "success": True,
            "message": "Cleanup completed successfully",
            "reports_cleaned": reports_cleaned,
            "cache_cleaned": cache_cleaned,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(detail=f"Failed to cleanup reports: {str(e)}") from e


# Health Check Endpoint


@router.get("/health")
async def health_check():
    """Health check endpoint for reporting service"""
    return {
        "status": "healthy",
        "service": "advanced_reporting",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "PDF generation",
            "Excel export",
            "Report scheduling",
            "Template management",
            "Analytics",
            "Multi-format export",
        ],
    }
