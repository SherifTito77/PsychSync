"""
GDPR Compliance API Endpoints
Provides comprehensive endpoints for data export, deletion, consent management, and privacy policy access
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.db.models.user import User
from app.services.compliance_audit_service import AuditAction, ComplianceAuditService
from app.services.consent_service import ConsentManagementService
from app.services.gdpr_service import GDPRService
from app.services.privacy_policy_service import PrivacyPolicyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gdpr", tags=["GDPR Compliance"])

# Initialize services
gdpr_service = GDPRService()
privacy_policy_service = PrivacyPolicyService()
consent_service = ConsentManagementService()
audit_service = ComplianceAuditService()


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post("/data-export")
async def request_data_export(
    request: Request,
    background_tasks: BackgroundTasks,
    format: str = "json",
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Request export of all user data (GDPR Right to Data Portability)

    Args:
        format: Export format (json, csv, zip)
    """
    try:
        # Log the request
        await audit_service.log_action(
            db=db,
            action=AuditAction.GDPR_DATA_EXPORT,
            resource_type="user_data",
            resource_id=str(current_user.id),
            user_id=str(current_user.id),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            audit_metadata={"format": format},
        )

        # Process export in background
        result = await gdpr_service.export_user_data(
            user_id=str(current_user.id), db=db, format=format
        )

        # Schedule cleanup task
        background_tasks.add_task(gdpr_service.schedule_data_export_cleanup)

        return {
            "message": "Data export request processed successfully",
            "export_id": result["export_id"],
            "download_url": result["download_url"],
            "expires_at": result["expires_at"],
            "file_size": result["file_size"],
            "data_categories": result["data_categories"],
        }

    except Exception as e:
        logger.error(f"Data export request failed: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process data export request",
        ) from e


@router.get("/download/{filename}")
async def download_export(
    filename: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Download exported data file"""
    try:
        # Validate filename to prevent directory traversal
        if not filename or ".." in filename or "/" in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename"
            )

        # Check if user has permission to access this file
        if not filename.startswith(str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        file_path = Path("exports") / filename
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found"
            )

        return FileResponse(
            path=file_path, filename=filename, media_type="application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download export failed: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download export file",
        ) from e


@router.delete("/user-data")
async def request_data_deletion(
    request: Request,
    deletion_reason: str = "user_request",
    soft_delete: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Request deletion of user data (GDPR Right to be Forgotten)

    Args:
        deletion_reason: Reason for deletion request
        soft_delete: If True, anonymize data; if False, hard delete
    """
    try:
        # Log the deletion request
        await audit_service.log_action(
            db=db,
            action=AuditAction.GDPR_DATA_DELETE,
            resource_type="user_data",
            resource_id=str(current_user.id),
            user_id=str(current_user.id),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            audit_metadata={
                "deletion_reason": deletion_reason,
                "soft_delete": soft_delete,
            },
            risk_level="high",
        )

        # Process deletion
        result = await gdpr_service.delete_user_data(
            user_id=str(current_user.id),
            db=db,
            deletion_reason=deletion_reason,
            soft_delete=soft_delete,
        )

        return {
            "message": "Data deletion request processed successfully",
            "deletion_id": result["deletion_id"],
            "method": result["method"],
            "deletion_date": result["deletion_date"],
            "data_categories_processed": result["data_categories_processed"],
        }

    except Exception as e:
        logger.error(f"Data deletion request failed: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process data deletion request",
        ) from e


@router.get("/privacy-policy")
async def get_privacy_policy(
    version: str | None = None, db: AsyncSession = Depends(get_db)
):
    """Get current or specific privacy policy version"""
    try:
        if version:
            policy = await privacy_policy_service.get_policy_version(db, version)
        else:
            policy = await privacy_policy_service.get_active_policy(db)

        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Privacy policy not found"
            )

        return policy

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get privacy policy: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve privacy policy",
        ) from e


@router.get("/privacy-policy/versions")
async def list_privacy_policy_versions(
    include_inactive: bool = False, db: AsyncSession = Depends(get_db)
):
    """List all privacy policy versions"""
    try:
        versions = await privacy_policy_service.list_policy_versions(
            db=db, include_inactive=include_inactive
        )

        return {"versions": versions, "total_count": len(versions)}

    except Exception as e:
        logger.error(f"Failed to list privacy policy versions: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve privacy policy versions",
        ) from e


@router.post("/consent")
async def update_consent(
    request: Request,
    consent_data: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user consent preferences

    Expected format:
    {
        "consents": [
            {
                "consent_type": "analytics",
                "action": "grant",
                "granular_preferences": {"usage_tracking": true, "performance_monitoring": false}
            }
        ]
    }
    """
    try:
        # Extract consent data
        consents = consent_data.get("consents", [])
        if not consents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No consent data provided",
            )

        # Process consent request
        context = {
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "form_version": consent_data.get("form_version", "1.0"),
            "language": consent_data.get("language", "en"),
        }

        result = await consent_service.process_consent_request(
            db=db, user_id=str(current_user.id), consent_data=consents, context=context
        )

        # Log consent updates
        for consent_result in result["results"]:
            await audit_service.log_action(
                db=db,
                action=(
                    AuditAction.GDPR_CONSENT_GRANT
                    if consent_result.get("consent_type")
                    else AuditAction.GDPR_CONSENT_WITHDRAW
                ),
                resource_type="user_consent",
                resource_id=str(current_user.id),
                user_id=str(current_user.id),
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                audit_metadata={
                    "consent_type": consent_result.get("consent_type"),
                    "consent_id": consent_result.get("consent_id"),
                },
            )

        return {
            "message": "Consent preferences updated successfully",
            "processed_count": result["processed_count"],
            "error_count": result["error_count"],
            "results": result["results"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Consent update failed: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update consent preferences",
        ) from e


@router.get("/consent")
async def get_user_consents(
    include_history: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's current consent status and history"""
    try:
        consents = await consent_service.get_user_consents(
            db=db, user_id=str(current_user.id), include_history=include_history
        )

        return consents

    except Exception as e:
        logger.error(f"Failed to get user consents: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve consent information",
        ) from e


@router.get("/consent/check/{consent_type}")
async def check_consent(
    consent_type: str,
    granular_check: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if user has valid consent for a specific purpose"""
    try:
        has_consent = await consent_service.check_consent(
            db=db,
            user_id=str(current_user.id),
            consent_type=consent_type,
            granular_check=granular_check,
        )

        return {
            "consent_type": consent_type,
            "has_consent": has_consent,
            "granular_check": granular_check,
            "user_id": str(current_user.id),
        }

    except Exception as e:
        logger.error(f"Consent check failed: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check consent status",
        ) from e


@router.get("/audit-logs")
async def get_user_audit_logs(
    request: Request,
    page: int = 1,
    limit: int = 50,
    start_date: str | None = None,
    end_date: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's audit logs (GDPR transparency requirement)"""
    try:
        # Parse date filters
        filters = {"user_id": str(current_user.id)}

        if start_date:
            try:
                filters["start_date"] = datetime.fromisoformat(
                    start_date.replace("Z", "+00:00")
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format",
                ) from None

        if end_date:
            try:
                filters["end_date"] = datetime.fromisoformat(
                    end_date.replace("Z", "+00:00")
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format",
                ) from None

        # Search audit logs
        results = await audit_service.search_audit_logs(
            db=db, filters=filters, page=page, limit=limit
        )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs",
        ) from e


@router.get("/data-summary")
async def get_user_data_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary of user's stored data (GDPR transparency requirement)"""
    try:
        # Collect user data summary without exposing actual data
        user_data = await gdpr_service._collect_user_data(str(current_user.id), db)

        summary = {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "data_categories": {
                "user_profile": len(user_data.get("user_profile", {})),
                "team_memberships": len(user_data.get("team_memberships", [])),
                "assessments": len(user_data.get("assessments", [])),
                "responses": len(user_data.get("responses", [])),
                "audit_logs": len(user_data.get("audit_logs", [])),
                "consent_records": len(user_data.get("consent_records", [])),
            },
            "last_updated": datetime.utcnow().isoformat(),
            "data_retention_policy": "Data is retained according to legal requirements and may be deleted upon request",
        }

        return summary

    except Exception as e:
        logger.error(f"Failed to get user data summary: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve data summary",
        ) from e


@router.post("/initiate-compliance-request")
async def initiate_compliance_request(
    request: Request,
    request_data: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate various GDPR compliance requests

    Expected format:
    {
        "request_type": "data_access" | "data_portability" | "data_correction" | "data_deletion" | "restriction_of_processing",
        "details": "Additional request details",
        "contact_method": "email" | "in_app_notification"
    }
    """
    try:
        request_type = request_data.get("request_type")
        details = request_data.get("details", "")
        contact_method = request_data.get("contact_method", "email")

        if not request_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request type is required",
            )

        # Log the compliance request
        await audit_service.log_action(
            db=db,
            action="gdpr_compliance_request",
            resource_type="compliance_request",
            resource_id=str(current_user.id),
            user_id=str(current_user.id),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            audit_metadata={
                "request_type": request_type,
                "details": details,
                "contact_method": contact_method,
            },
            risk_level="medium",
        )

        # Create compliance request record (this would typically go to a compliance system)
        request_id = f"{request_type}_{current_user.id!s}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        return {
            "message": "Compliance request received and is being processed",
            "request_id": request_id,
            "request_type": request_type,
            "status": "received",
            "estimated_processing_time": "30 days",
            "contact_method": contact_method,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compliance request failed: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process compliance request",
        ) from e
