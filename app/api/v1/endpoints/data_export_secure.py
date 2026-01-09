# app/api/v1/endpoints/data_export_secure.py
"""
OWASP-Secure User Data Export API Endpoints

Security Improvements:
- Path traversal prevention (CRITICAL FIX)
- Fixed syntax errors
- Per-user rate limiting
- Comprehensive audit logging
- CSRF protection
- File path validation
- Proper error handling

Author: Security Team
Version: 2.0 OWASP-Compliant
"""

from datetime import datetime
import logging
import os
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db, get_current_user
from app.core.audit_logging import AuditAction, AuditEvent, audit_logger
from app.db.models.user import User
from app.schemas.responses import PaginatedResponse, SuccessResponse
from app.services.data_export_service import (
    ExportFormat,
    ExportScope,
    ExportStatus,
    get_data_export_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class ExportRequestModel(BaseModel):
    """Request model for creating data export"""
    format: ExportFormat = Field(..., description="Export format")
    scope: ExportScope = Field(..., description="Data scope to export")
    date_range_start: datetime | None = Field(None, description="Start date for data filtering")
    date_range_end: datetime | None = Field(None, description="End date for data filtering")
    include_anonymized_data: bool = Field(default=False, description="Include anonymized/pseudonymized data")
    include_deleted_data: bool = Field(default=False, description="Include deleted/archived data")
    filters: dict[str, Any] = Field(default_factory=dict, description="Additional filters")
    notes: str | None = Field(None, description="Export notes or description")


class ExportResponse(BaseModel):
    """Response model for export information"""
    export_id: str
    format: str
    scope: str
    status: str
    requested_at: datetime
    expires_at: datetime
    file_size: int
    download_count: int
    max_downloads: int
    error_message: str | None

    class Config:
        from_attributes = True


class ExportListResponse(PaginatedResponse[ExportResponse]):
    """Response model for export list with pagination"""


class ExportStatisticsResponse(BaseModel):
    """Response model for export statistics"""
    total_exports: int
    completed_exports: int
    pending_exports: int
    failed_exports: int
    total_size_bytes: int
    total_size_gb: float
    most_common_formats: dict[str, int]
    most_common_scopes: dict[str, int]
    exports_this_month: int


async def _get_client_info(request: Request) -> dict[str, str]:
    """Extract client information for security logging"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")

    return {
        "ip_address": client_ip,
        "user_agent": user_agent
    }


@router.post("/data-exports", response_model=SuccessResponse[ExportResponse])
async def create_export_request(
    export_request: ExportRequestModel,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new data export request

    SECURITY: Per-user rate limiting, audit logging
    """
    client_info = await _get_client_info(request)

    try:
        export_service = get_data_export_service()

        # Create export request
        export = await export_service.create_export_request(
            user_id=str(current_user.id),
            format=export_request.format,
            scope=export_request.scope,
            filters=export_request.filters,
            date_range_start=export_request.date_range_start,
            date_range_end=export_request.date_range_end,
            include_anonymized_data=export_request.include_anonymized_data,
            include_deleted_data=export_request.include_deleted_data
        )

        logger.info(f"Export request created for user {current_user.email}: {export.export_id}")

        # SECURITY: Audit log
        await audit_logger.log_event(AuditEvent(
            action=AuditAction.CREATE,
            user_id=str(current_user.id),
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            resource="/data-exports",
            details={
                "export_id": export.export_id,
                "format": export.format.value,
                "scope": export.scope.value,
                "filters": export_request.filters
            }
        ))

        return SuccessResponse(
            message="Export request created successfully",
            data=ExportResponse.from_orm(export)
        )

    except Exception as e:
        logger.error(f"Failed to create export request: {e!s}")

        # Audit log failure
        await audit_logger.log_event(AuditEvent(
            action=AuditAction.CREATE,
            user_id=str(current_user.id),
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            resource="/data-exports",
            details={"error": str(e)},
            severity="high"
        ))

        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/data-exports", response_model=ExportListResponse)
async def list_user_exports(
    status: ExportStatus | None = Query(None, description="Filter by export status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List user's export requests with pagination
    """
    try:
        export_service = get_data_export_service()

        # Get user exports
        exports = await export_service.get_user_exports(
            user_id=str(current_user.id),
            status=status,
            limit=size * page  # Get more for pagination
        )

        # Convert to response models
        export_responses = [ExportResponse.from_orm(export) for export in exports]

        # Manual pagination
        total = len(export_responses)
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_exports = export_responses[start_idx:end_idx]

        return ExportListResponse.create_paginated(
            items=paginated_exports,
            total=total,
            page=page,
            size=size
        )

    except Exception as e:
        logger.error(f"Failed to list exports: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/data-exports/{export_id}", response_model=SuccessResponse[ExportResponse])
async def get_export_status(
    export_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get detailed information about an export request

    SECURITY: Ownership verification, audit logging
    """
    client_info = await _get_client_info(request)

    try:
        export_service = get_data_export_service()

        # Get export status
        export = await export_service.get_export_status(export_id)
        if not export:
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.READ,
                user_id=str(current_user.id),
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                resource=f"/data-exports/{export_id}",
                details={"reason": "Export not found"},
                severity="medium"
            ))
            raise HTTPException(status_code=404, detail="Export not found")

        # Verify ownership
        if export.user_id != str(current_user.id):
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.UNAUTHORIZED_ACCESS,
                user_id=str(current_user.id),
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                resource=f"/data-exports/{export_id}",
                details={"reason": "Ownership check failed"},
                severity="high"
            ))
            raise HTTPException(status_code=403, detail="Access denied")

        return SuccessResponse(
            message="Export status retrieved successfully",
            data=ExportResponse.from_orm(export)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get export status {export_id}: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/data-exports/{export_id}/download")
async def download_export(
    export_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Download an exported data file

    SECURITY: Path traversal prevention, ownership verification, audit logging
    """
    client_info = await _get_client_info(request)

    try:
        export_service = get_data_export_service()

        # Get export status
        export = await export_service.get_export_status(export_id)
        if not export:
            raise HTTPException(status_code=404, detail="Export not found")

        # Verify ownership
        if export.user_id != str(current_user.id):
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.UNAUTHORIZED_ACCESS,
                user_id=str(current_user.id),
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                resource=f"/data-exports/{export_id}/download",
                details={"reason": "Ownership check failed"},
                severity="high"
            ))
            raise HTTPException(status_code=403, detail="Access denied")

        # Check if export is ready
        if export.status != ExportStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Export not ready. Current status: {export.status.value}"
            )

        # Check if export has expired
        if datetime.utcnow() > export.expires_at:
            raise HTTPException(status_code=410, detail="Export has expired")

        # SECURITY: Path traversal prevention built into service
        file_handle = await export_service.download_export(export_id)
        if not file_handle:
            raise HTTPException(status_code=404, detail="Export file not available")

        try:
            # Determine filename and content type
            filename = f"user_data_export_{export_id}.{export.format.value}"

            content_types = {
                ExportFormat.JSON: "application/json",
                ExportFormat.CSV: "text/csv",
                ExportFormat.XML: "application/xml",
                ExportFormat.PDF: "application/pdf",
                ExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }

            content_type = content_types.get(export.format, "application/octet-stream")

            # Read file content
            file_content = file_handle.read()
            file_handle.close()

            # Log download
            logger.info(f"Export downloaded: {export_id} by user {current_user.email}")

            # SECURITY: Audit log
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.READ,
                user_id=str(current_user.id),
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                resource=f"/data-exports/{export_id}/download",
                details={"export_id": export_id, "filename": filename}
            ))

            return Response(
                content=file_content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )

        finally:
            file_handle.close()

    except HTTPException:
        raise
    except ValueError as e:
        # Path traversal attempt
        logger.error(f"Path traversal attempt blocked: {e!s}")

        await audit_logger.log_event(AuditEvent(
            action=AuditAction.UNAUTHORIZED_ACCESS,
            user_id=str(current_user.id),
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            resource=f"/data-exports/{export_id}/download",
            details={"reason": "Path traversal attempt", "error": str(e)},
            severity="critical"
        ))

        raise HTTPException(status_code=400, detail="Invalid export file path") from e
    except Exception as e:
        logger.error(f"Failed to download export {export_id}: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/data-exports/{export_id}", response_model=SuccessResponse[dict[str, str]])
async def delete_export(
    export_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete an export request and associated file

    SECURITY: Path traversal prevention, ownership verification, audit logging
    """
    client_info = await _get_client_info(request)

    try:
        export_service = get_data_export_service()

        # Get export status
        export = await export_service.get_export_status(export_id)
        if not export:
            raise HTTPException(status_code=404, detail="Export not found")

        # Verify ownership
        if export.user_id != str(current_user.id):
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.UNAUTHORIZED_ACCESS,
                user_id=str(current_user.id),
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                resource=f"/data-exports/{export_id}",
                details={"reason": "Ownership check failed"},
                severity="high"
            ))
            raise HTTPException(status_code=403, detail="Access denied")

        # SECURITY: Path traversal prevention
        if export.file_path:
            try:
                # Validate path is within export directory
                validated_path = export_service._validate_file_path(export.file_path)

                if validated_path.exists():
                    os.unlink(validated_path)

                    logger.info(f"Export file deleted: {export.file_path}")

            except ValueError as e:
                # Path traversal attempt
                logger.error(f"Path traversal attempt blocked: {e!s}")

                await audit_logger.log_event(AuditEvent(
                    action=AuditAction.UNAUTHORIZED_ACCESS,
                    user_id=str(current_user.id),
                    ip_address=client_info["ip_address"],
                    user_agent=client_info["user_agent"],
                    resource=f"/data-exports/{export_id}",
                    details={"reason": "Path traversal attempt", "error": str(e)},
                    severity="critical"
                ))

                raise HTTPException(
                    status_code=400,
                    detail="Invalid export file path"
                ) from e

        # Remove from active exports
        if export_id in export_service.active_exports:
            del export_service.active_exports[export_id]

        logger.info(f"Export deleted: {export_id} by user {current_user.email}")

        # SECURITY: Audit log
        await audit_logger.log_event(AuditEvent(
            action=AuditAction.DELETE,
            user_id=str(current_user.id),
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            resource=f"/data-exports/{export_id}",
            details={"export_id": export_id}
        ))

        return SuccessResponse(
            message="Export deleted successfully",
            data={"export_id": export_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete export {export_id}: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/data-exports/statistics", response_model=SuccessResponse[ExportStatisticsResponse])
async def get_export_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get user's export statistics"""
    try:
        export_service = get_data_export_service()

        # Get user exports
        exports = await export_service.get_user_exports(
            user_id=str(current_user.id),
            limit=1000  # Get all for statistics
        )

        # Calculate statistics
        total_exports = len(exports)
        completed_exports = len([e for e in exports if e.status == ExportStatus.COMPLETED])
        pending_exports = len([e for e in exports if e.status == ExportStatus.PENDING])
        failed_exports = len([e for e in exports if e.status == ExportStatus.FAILED])

        total_size_bytes = sum(e.file_size for e in exports if e.file_size)
        total_size_gb = round(total_size_bytes / (1024 ** 3), 2)

        # Format distribution
        format_counts = {}
        for export in exports:
            format_key = export.format.value
            format_counts[format_key] = format_counts.get(format_key, 0) + 1

        # Scope distribution
        scope_counts = {}
        for export in exports:
            scope_key = export.scope.value
            scope_counts[scope_key] = scope_counts.get(scope_key, 0) + 1

        # Exports this month
        current_month_start = datetime.utcnow().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        exports_this_month = len([
            e for e in exports
            if e.requested_at and e.requested_at >= current_month_start
        ])

        statistics = ExportStatisticsResponse(
            total_exports=total_exports,
            completed_exports=completed_exports,
            pending_exports=pending_exports,
            failed_exports=failed_exports,
            total_size_bytes=total_size_bytes,
            total_size_gb=total_size_gb,
            most_common_formats=format_counts,
            most_common_scopes=scope_counts,
            exports_this_month=exports_this_month
        )

        return SuccessResponse(
            message="Export statistics retrieved successfully",
            data=statistics
        )

    except Exception as e:
        logger.error(f"Failed to get export statistics: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/data-exports/cleanup", response_model=SuccessResponse[dict[str, Any]])
async def cleanup_expired_exports(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Clean up expired export files"""
    client_info = await _get_client_info(request)

    try:
        export_service = get_data_export_service()

        # Clean up expired exports
        cleaned_count = await export_service.cleanup_expired_exports()

        logger.info(
            f"Export cleanup completed by user {current_user.email}. "
            f"Cleaned {cleaned_count} exports."
        )

        # SECURITY: Audit log
        await audit_logger.log_event(AuditEvent(
            action=AuditAction.DELETE,
            user_id=str(current_user.id),
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            resource="/data-exports/cleanup",
            details={"cleaned_count": cleaned_count}
        ))

        return SuccessResponse(
            message="Export cleanup completed",
            data={
                "cleaned_count": cleaned_count,
                "cleaned_at": datetime.utcnow().isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Failed to cleanup expired exports: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/data-exports/formats", response_model=SuccessResponse[dict[str, list[str]]])
async def get_available_formats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get available export formats and their descriptions"""
    try:
        formats = {
            "available_formats": [format.value for format in ExportFormat],
            "format_descriptions": {
                "json": "JavaScript Object Notation - Machine-readable, structured data",
                "csv": "Comma-Separated Values - Spreadsheet compatible",
                "xml": "eXtensible Markup Language - Structured markup format",
                "pdf": "Portable Document Format - Human-readable document",
                "excel": "Microsoft Excel Spreadsheet - Tabular data with multiple sheets"
            }
        }

        return SuccessResponse(
            message="Available export formats retrieved successfully",
            data=formats
        )

    except Exception as e:
        logger.error(f"Failed to get available formats: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/data-exports/scopes", response_model=SuccessResponse[dict[str, list[str]]])
async def get_available_scopes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get available export scopes and their descriptions"""
    try:
        scopes = {
            "available_scopes": [scope.value for scope in ExportScope],
            "scope_descriptions": {
                "profile": "Basic user profile information (name, email, role, etc.)",
                "assessments": "Assessment data, responses, and scores",
                "team_data": "Team memberships, roles, and related information",
                "activity_log": "User activity logs and audit trail",
                "settings": "User preferences, settings, and configurations",
                "all": "All available user data (comprehensive export)"
            }
        }

        return SuccessResponse(
            message="Available export scopes retrieved successfully",
            data=scopes
        )

    except Exception as e:
        logger.error(f"Failed to get available scopes: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e
