"""
GDPR User Data Export and Deletion Endpoints

Simple, easy-to-use routes for GDPR compliance:
- GET /api/v1/users/export - Export user data
- DELETE /api/v1/users/delete - Request account deletion

These are simplified versions of the full GDPR endpoints,
designed for quick implementation and easy integration.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user, verify_password
from app.db.models.user import User
from app.services.user_service import UserService
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class UserDeleteRequest(BaseModel):
    """Request model for account deletion"""
    password: str
    reason: str | None = None
    confirm: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "password": "your_password",
                "reason": "No longer need the service",
                "confirm": True
            }
        }


class UserExportResponse(BaseModel):
    """Response model for data export"""
    status: str
    message: str
    download_url: str | None = None
    expires_at: datetime | None = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "processing",
                "message": "Your data export is being prepared",
                "download_url": None,
                "expires_at": None
            }
        }


class UserDeleteResponse(BaseModel):
    """Response model for account deletion"""
    status: str
    message: str
    deletion_date: datetime | None = None
    cancellation_url: str | None = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "scheduled",
                "message": "Account scheduled for deletion",
                "deletion_date": "2024-12-01T00:00:00Z",
                "cancellation_url": "https://app.psychsync.com/cancel-deletion?token=abc123"
            }
        }


# ============================================
# EXPORT ENDPOINT
# ============================================

@router.get("/export", response_model=UserExportResponse)
async def export_user_data(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export all user data (GDPR Article 15 - Right of Access)
    
    Returns a ZIP file containing:
    - profile.json: User profile information
    - assessments.json: All assessment results
    - teams.json: Team memberships
    - activity.csv: Activity logs
    
    The download link expires after 7 days for security.
    
    Example:
        GET /api/v1/users/export
        Authorization: Bearer <your-token>
        
        Response:
        {
            "status": "processing",
            "message": "Your data export is being prepared...",
            "download_url": null
        }
    
    Usage:
        1. Call this endpoint
        2. Check email for download link
        3. Download within 7 days
    """
    try:
        user_service = UserService(db)
        
        # Check if export already in progress
        existing_export = await user_service.get_pending_export(current_user.id)
        
        if existing_export:
            return UserExportResponse(
                status="processing",
                message="Your previous export request is still being processed. Check your email.",
                download_url=None,
                expires_at=existing_export.get("expires_at")
            )
        
        # Create export request
        export_request = await user_service.create_export_request(current_user.id)
        
        # Queue background task to generate export
        background_tasks.add_task(
            user_service.generate_export,
            user_id=current_user.id,
            email=current_user.email,
            request_id=export_request["id"]
        )
        
        logger.info(f"Data export requested by user {current_user.id}")
        
        return UserExportResponse(
            status="accepted",
            message="Your data export request has been received. You will receive an email with the download link within 24 hours.",
            download_url=None,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
    except Exception as e:
        logger.error(f"Error in export_user_data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process export request. Please try again later."
        )


@router.get("/export/status")
async def get_export_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check status of data export request
    
    Returns:
    - pending: Export is being generated
    - ready: Export is ready for download
    - expired: Download link has expired
    - none: No export request found
    
    Example:
        GET /api/v1/users/export/status
        
        Response:
        {
            "status": "ready",
            "download_url": "https://app.psychsync.com/downloads/export_123.zip",
            "expires_at": "2024-11-08T10:00:00Z"
        }
    """
    try:
        user_service = UserService(db)
        export_status = await user_service.get_export_status(current_user.id)
        
        if not export_status:
            return {
                "status": "none",
                "message": "No export request found"
            }
        
        return export_status
        
    except Exception as e:
        logger.error(f"Error getting export status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get export status")


# ============================================
# DELETE ENDPOINT
# ============================================

@router.delete("/delete", response_model=UserDeleteResponse)
async def delete_user_account(
    delete_request: UserDeleteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request account deletion (GDPR Article 17 - Right to Erasure)
    
    ⚠️ WARNING: This action is IRREVERSIBLE after 30-day grace period!
    
    Process:
    1. Verify password
    2. Disable account immediately
    3. 30-day grace period (can cancel)
    4. Permanent deletion after 30 days
    
    What gets deleted:
    - User profile and authentication
    - All assessment results
    - Team memberships
    - Activity logs
    - Uploaded files
    
    What is preserved (anonymized):
    - Aggregate statistics (if consented for research)
    
    Example:
        DELETE /api/v1/users/delete
        Authorization: Bearer <your-token>
        Body: {
            "password": "your_password",
            "reason": "No longer need the service",
            "confirm": true
        }
        
        Response:
        {
            "status": "scheduled",
            "message": "Account scheduled for deletion",
            "deletion_date": "2024-12-01T00:00:00Z",
            "cancellation_url": "https://app.psychsync.com/cancel?token=abc123"
        }
    
    To cancel deletion:
        Click the cancellation link in the email
        Or call: POST /api/v1/users/cancel-deletion
    """
    try:
        # Verify confirmation
        if not delete_request.confirm:
            raise HTTPException(
                status_code=400,
                detail="You must confirm account deletion by setting 'confirm' to true"
            )
        
        # Verify password
        if not verify_password(delete_request.password, current_user.password_hash):
            logger.warning(f"Failed deletion attempt for user {current_user.id} - invalid password")
            raise HTTPException(
                status_code=401,
                detail="Invalid password. Please verify your password and try again."
            )
        
        user_service = UserService(db)
        
        # Check for existing deletion request
        existing_deletion = await user_service.get_pending_deletion(current_user.id)
        
        if existing_deletion:
            return UserDeleteResponse(
                status="pending",
                message="Your account is already scheduled for deletion.",
                deletion_date=existing_deletion["deletion_date"],
                cancellation_url=existing_deletion.get("cancellation_url")
            )
        
        # Create deletion request with 30-day grace period
        deletion_date = datetime.utcnow() + timedelta(days=30)
        
        deletion_request = await user_service.create_deletion_request(
            user_id=current_user.id,
            reason=delete_request.reason,
            deletion_date=deletion_date
        )
        
        # Disable account immediately
        await user_service.disable_account(current_user.id)
        
        # Send confirmation email with cancellation link
        background_tasks.add_task(
            user_service.send_deletion_confirmation,
            email=current_user.email,
            deletion_date=deletion_date,
            cancellation_token=deletion_request["cancellation_token"]
        )
        
        # Schedule deletion job
        background_tasks.add_task(
            user_service.schedule_deletion,
            user_id=current_user.id,
            deletion_date=deletion_date
        )
        
        logger.warning(f"Account deletion scheduled for user {current_user.id}")
        
        return UserDeleteResponse(
            status="scheduled",
            message=f"Your account has been disabled and will be permanently deleted on {deletion_date.strftime('%Y-%m-%d')}. "
                   f"You can cancel this request within 30 days using the link sent to your email.",
            deletion_date=deletion_date,
            cancellation_url=f"https://app.psychsync.com/cancel-deletion?token={deletion_request['cancellation_token']}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_user_account: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process deletion request. Please contact support."
        )


@router.post("/cancel-deletion")
async def cancel_account_deletion(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel pending account deletion
    
    Use the cancellation token from the deletion confirmation email.
    Can only cancel within 30-day grace period.
    
    Example:
        POST /api/v1/users/cancel-deletion?token=abc123xyz
        Authorization: Bearer <your-token>
        
        Response:
        {
            "status": "cancelled",
            "message": "Account deletion cancelled. Your account is now active."
        }
    """
    try:
        if not token:
            raise HTTPException(
                status_code=400,
                detail="Cancellation token is required"
            )
        
        user_service = UserService(db)
        
        # Verify and cancel deletion request
        cancelled = await user_service.cancel_deletion(
            user_id=current_user.id,
            cancellation_token=token
        )
        
        if not cancelled:
            raise HTTPException(
                status_code=400,
                detail="Invalid cancellation token or grace period has expired"
            )
        
        # Reactivate account
        await user_service.reactivate_account(current_user.id)
        
        logger.info(f"Account deletion cancelled for user {current_user.id}")
        
        return {
            "status": "cancelled",
            "message": "Your account deletion has been cancelled successfully. Your account is now active again."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling deletion: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel deletion")


# ============================================
# PRIVACY SETTINGS
# ============================================

@router.get("/privacy-settings")
async def get_privacy_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's privacy and data settings
    
    Returns current consent status for:
    - Analytics data collection
    - Marketing communications
    - Research participation (anonymized data)
    - Data sharing with team leaders
    
    Example:
        GET /api/v1/users/privacy-settings
        
        Response:
        {
            "analytics_consent": true,
            "marketing_consent": false,
            "research_consent": true,
            "share_with_team_leaders": true,
            "email_notifications": true,
            "push_notifications": true
        }
    """
    try:
        user_service = UserService(db)
        settings = await user_service.get_privacy_settings(current_user.id)
        
        return settings
        
    except Exception as e:
        logger.error(f"Error getting privacy settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get privacy settings")


@router.put("/privacy-settings")
async def update_privacy_settings(
    settings: Dict[str, bool],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update privacy and consent settings
    
    Allows users to control:
    - What data is collected
    - How data is used
    - Who can see their data
    - Communication preferences
    
    Example:
        PUT /api/v1/users/privacy-settings
        Body: {
            "analytics_consent": true,
            "marketing_consent": false,
            "research_consent": true,
            "email_notifications": true
        }
        
        Response:
        {
            "status": "updated",
            "settings": { ... }
        }
    """
    try:
        user_service = UserService(db)
        
        updated_settings = await user_service.update_privacy_settings(
            user_id=current_user.id,
            settings=settings
        )
        
        logger.info(f"Privacy settings updated for user {current_user.id}")
        
        return {
            "status": "updated",
            "message": "Privacy settings updated successfully",
            "settings": updated_settings
        }
        
    except Exception as e:
        logger.error(f"Error updating privacy settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update privacy settings")


# ============================================
# USAGE EXAMPLES
# ============================================

"""
Frontend Integration Examples
==============================

1. Export User Data:

   const exportData = async () => {
       const response = await fetch('/api/v1/users/export', {
           method: 'GET',
           headers: {
               'Authorization': `Bearer ${token}`
           }
       });
       const data = await response.json();
       
       if (data.status === 'accepted') {
           alert('Export requested! Check your email.');
       }
   };


2. Delete Account:

   const deleteAccount = async (password) => {
       if (!confirm('Are you sure? This cannot be undone after 30 days!')) {
           return;
       }
       
       const response = await fetch('/api/v1/users/delete', {
           method: 'DELETE',
           headers: {
               'Authorization': `Bearer ${token}`,
               'Content-Type': 'application/json'
           },
           body: JSON.stringify({
               password: password,
               reason: 'No longer need the service',
               confirm: true
           })
       });
       
       const data = await response.json();
       
       if (data.status === 'scheduled') {
           alert(`Account will be deleted on ${data.deletion_date}`);
           // Log out user
           logout();
       }
   };


3. Check Export Status:

   const checkExportStatus = async () => {
       const response = await fetch('/api/v1/users/export/status', {
           headers: {
               'Authorization': `Bearer ${token}`
           }
       });
       const data = await response.json();
       
       if (data.status === 'ready') {
           window.open(data.download_url, '_blank');
       } else if (data.status === 'pending') {
           alert('Export is still being generated...');
       }
   };


4. Cancel Deletion:

   const cancelDeletion = async (token) => {
       const response = await fetch(
           `/api/v1/users/cancel-deletion?token=${token}`,
           {
               method: 'POST',
               headers: {
                   'Authorization': `Bearer ${authToken}`
               }
           }
       );
       
       if (response.ok) {
           alert('Deletion cancelled! Account reactivated.');
           window.location.href = '/dashboard';
       }
   };


5. Update Privacy Settings:

   const updatePrivacy = async (settings) => {
       const response = await fetch('/api/v1/users/privacy-settings', {
           method: 'PUT',
           headers: {
               'Authorization': `Bearer ${token}`,
               'Content-Type': 'application/json'
           },
           body: JSON.stringify(settings)
       });
       
       if (response.ok) {
           alert('Privacy settings updated!');
       }
   };
"""