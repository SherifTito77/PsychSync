"""
GDPR Compliance Endpoints

Why we need this:
- Legal requirement under GDPR Article 15 (Right of Access)
- GDPR Article 17 (Right to Erasure/"Right to be Forgotten")
- GDPR Article 20 (Right to Data Portability)
- Build user trust through transparency
- Avoid hefty fines (up to €20M or 4% of annual revenue)

Key Requirements:
1. Data export within 30 days of request
2. Data deletion within 30 days of request
3. Audit trail of all data requests
4. Anonymization vs deletion decisions
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
import json
import zipfile
import io

from app.core.database import get_db
from app.core.security import get_current_user
from app.db.models.user import User
from app.schemas.gdpr import (
    DataExportRequest,
    DataExportResponse,
    DataDeletionRequest,
    DataDeletionResponse,
    GDPRStatus
)
from app.services.gdpr_service import GDPRService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/export-data", response_model=DataExportResponse)
async def request_data_export(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request export of all personal data (GDPR Article 15)
    
    Returns:
        - Download link valid for 7 days
        - Includes: profile, assessments, team memberships, activity logs
        - Format: JSON + CSV in ZIP file
    
    Process:
    1. Validate user identity
    2. Collect all user data
    3. Generate export package
    4. Send download link via email
    """
    try:
        gdpr_service = GDPRService(db)
        
        # Check for existing pending requests
        existing_request = await gdpr_service.get_pending_export_request(current_user.id)
        if existing_request:
            return DataExportResponse(
                status="pending",
                message="An export request is already in progress",
                request_id=existing_request.id,
                estimated_completion=existing_request.estimated_completion
            )
        
        # Create new export request
        export_request = await gdpr_service.create_export_request(current_user.id)
        
        # Queue background job to generate export
        background_tasks.add_task(
            gdpr_service.generate_data_export,
            user_id=current_user.id,
            request_id=export_request.id
        )
        
        logger.info(f"Data export requested by user {current_user.id}")
        
        return DataExportResponse(
            status="accepted",
            message="Your data export request has been received. You will receive an email with the download link within 24 hours.",
            request_id=export_request.id,
            estimated_completion=datetime.utcnow() + timedelta(hours=24)
        )
        
    except Exception as e:
        logger.error(f"Error processing data export request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process export request")


@router.get("/export-status/{request_id}", response_model=GDPRStatus)
async def get_export_status(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check status of data export request
    
    Returns:
        - Status: pending, processing, completed, failed
        - Download URL if completed
        - Progress percentage
    """
    try:
        gdpr_service = GDPRService(db)
        status = await gdpr_service.get_export_status(request_id, current_user.id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Export request not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting export status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get export status")


@router.get("/export-download/{request_id}")
async def download_data_export(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download completed data export
    
    Security:
    - Link expires after 7 days
    - One-time download token
    - User must be authenticated
    """
    try:
        gdpr_service = GDPRService(db)
        
        # Validate request belongs to user
        export_data = await gdpr_service.get_export_data(request_id, current_user.id)
        
        if not export_data:
            raise HTTPException(status_code=404, detail="Export not found or expired")
        
        # Return file
        from fastapi.responses import StreamingResponse
        
        return StreamingResponse(
            io.BytesIO(export_data['file_content']),
            media_type='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename="psychsync_data_export_{current_user.id}.zip"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download export")


@router.post("/delete-account", response_model=DataDeletionResponse)
async def request_account_deletion(
    deletion_request: DataDeletionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request account and data deletion (GDPR Article 17)
    
    WARNING: This action is IRREVERSIBLE!
    
    Process:
    1. Verify password
    2. Create 30-day grace period
    3. Send confirmation email
    4. After 30 days: anonymize or delete data
    
    Options:
    - Full deletion: Remove all data
    - Anonymization: Keep aggregate data for research (if consented)
    
    Grace Period:
    - User can cancel within 30 days
    - Account disabled immediately
    - Data deleted after 30 days
    """
    try:
        gdpr_service = GDPRService(db)
        
        # Verify password
        from app.core.security import verify_password
        if not verify_password(deletion_request.password, current_user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password")
        
        # Check for existing deletion request
        existing_request = await gdpr_service.get_pending_deletion_request(current_user.id)
        if existing_request:
            return DataDeletionResponse(
                status="pending",
                message="A deletion request is already pending",
                deletion_date=existing_request.scheduled_deletion_date,
                grace_period_ends=existing_request.scheduled_deletion_date,
                can_cancel=True
            )
        
        # Create deletion request with 30-day grace period
        deletion_date = datetime.utcnow() + timedelta(days=30)
        deletion_req = await gdpr_service.create_deletion_request(
            user_id=current_user.id,
            reason=deletion_request.reason,
            deletion_date=deletion_date
        )
        
        # Disable account immediately
        current_user.is_active = False
        await db.commit()
        
        # Send confirmation email
        background_tasks.add_task(
            gdpr_service.send_deletion_confirmation_email,
            user_email=current_user.email,
            deletion_date=deletion_date,
            cancellation_token=deletion_req.cancellation_token
        )
        
        # Schedule deletion job
        background_tasks.add_task(
            gdpr_service.schedule_account_deletion,
            user_id=current_user.id,
            deletion_date=deletion_date
        )
        
        logger.warning(f"Account deletion requested by user {current_user.id}")
        
        return DataDeletionResponse(
            status="scheduled",
            message=f"Your account will be deleted on {deletion_date.strftime('%Y-%m-%d')}. You can cancel this request within 30 days.",
            deletion_date=deletion_date,
            grace_period_ends=deletion_date,
            can_cancel=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing deletion request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process deletion request")


@router.post("/cancel-deletion")
async def cancel_account_deletion(
    cancellation_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel pending account deletion
    
    Can only cancel within 30-day grace period
    """
    try:
        gdpr_service = GDPRService(db)
        
        # Verify and cancel deletion request
        cancelled = await gdpr_service.cancel_deletion_request(
            user_id=current_user.id,
            cancellation_token=cancellation_token
        )
        
        if not cancelled:
            raise HTTPException(
                status_code=400,
                detail="No pending deletion request found or grace period expired"
            )
        
        # Reactivate account
        current_user.is_active = True
        await db.commit()
        
        logger.info(f"Account deletion cancelled by user {current_user.id}")
        
        return {
            "status": "cancelled",
            "message": "Your account deletion has been cancelled. Your account is now active again."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling deletion: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel deletion")


@router.get("/privacy-settings")
async def get_privacy_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's current privacy and data settings
    
    Returns:
    - Data retention settings
    - Consent status for various data uses
    - Marketing preferences
    - Third-party data sharing settings
    """
    try:
        gdpr_service = GDPRService(db)
        settings = await gdpr_service.get_privacy_settings(current_user.id)
        
        return settings
        
    except Exception as e:
        logger.error(f"Error getting privacy settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get privacy settings")


@router.put("/privacy-settings")
async def update_privacy_settings(
    settings: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update privacy and consent settings
    
    Allows users to:
    - Opt in/out of analytics
    - Control data retention
    - Manage marketing preferences
    - Set data sharing preferences
    """
    try:
        gdpr_service = GDPRService(db)
        updated_settings = await gdpr_service.update_privacy_settings(
            user_id=current_user.id,
            settings=settings
        )
        
        logger.info(f"Privacy settings updated for user {current_user.id}")
        
        return {
            "status": "updated",
            "settings": updated_settings
        }
        
    except Exception as e:
        logger.error(f"Error updating privacy settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update privacy settings")


@router.get("/data-processing-log")
async def get_data_processing_log(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get log of all data processing activities (GDPR transparency)
    
    Shows:
    - When data was accessed
    - What data was accessed
    - Purpose of access
    - Who accessed it (if shared)
    """
    try:
        gdpr_service = GDPRService(db)
        log = await gdpr_service.get_data_processing_log(current_user.id)
        
        return {
            "activities": log,
            "total_count": len(log)
        }
        
    except Exception as e:
        logger.error(f"Error getting processing log: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get processing log")
    