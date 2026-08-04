"""
Push Notifications API Endpoints

Provides endpoints for managing FCM push notifications:
- Register/unregister device tokens
- Send notifications to users
- Manage notification preferences
- Get notification history

Access: Authenticated users
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.users import get_async_db, get_current_user
from app.db.models.user import User
from app.services.push_notification_service import (
    NotificationType,
    push_notification_service,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/push-notifications", tags=["push-notifications"])


# =============================================================================
# Pydantic Schemas
# =============================================================================


class RegisterTokenRequest(BaseModel):
    """Request schema for registering a device token"""

    token: str = Field(..., min_length=100, description="FCM device token")
    platform: str = Field(..., description="Platform: ios or android")
    device_id: Optional[str] = Field(None, description="Unique device identifier")
    device_model: Optional[str] = Field(
        None, description="Device model (e.g., iPhone 14)"
    )
    os_version: Optional[str] = Field(None, description="OS version (e.g., iOS 16.0)")
    app_version: Optional[str] = Field(None, description="App version (e.g., 1.0.0)")


class UnregisterTokenRequest(BaseModel):
    """Request schema for unregistering a device token"""

    token: str = Field(
        ..., min_length=100, description="FCM device token to unregister"
    )


class SendNotificationRequest(BaseModel):
    """Request schema for sending a notification"""

    user_id: UUID = Field(..., description="Target user ID")
    notification_type: str = Field(..., description="Type of notification")
    data: Optional[Dict] = Field(
        default_factory=dict,
        description="Notification data (variables, deep links, etc.)",
    )


class BulkSendNotificationRequest(BaseModel):
    """Request schema for sending bulk notifications"""

    user_ids: List[UUID] = Field(
        ..., min_items=1, max_items=1000, description="Target user IDs"
    )
    notification_type: str = Field(..., description="Type of notification")
    data: Optional[Dict] = Field(default_factory=dict, description="Notification data")


class TokenResponse(BaseModel):
    """Response schema for token registration"""

    id: UUID
    token: str
    platform: str
    is_active: bool
    created_at: str
    last_used_at: str

    class Config:
        from_attributes = True


class NotificationDeliveryResponse(BaseModel):
    """Response schema for notification delivery"""

    success: bool
    tokens_sent: int
    successful: int
    failed: int
    skipped: Optional[bool] = None
    reason: Optional[str] = None


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/register-token", response_model=TokenResponse)
async def register_device_token(
    request: RegisterTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Register a device's FCM token for push notifications.

    This endpoint should be called when the app starts or when the
    FCM token changes. Tokens are associated with the authenticated user.

    **Request Body:**
    ```json
    {
      "token": "FCM device token string",
      "platform": "ios",
      "device_id": "unique-device-id",
      "device_model": "iPhone 14",
      "os_version": "iOS 16.0",
      "app_version": "1.0.0"
    }
    ```
    """

    try:
        device_info = {
            "platform": request.platform,
            "device_id": request.device_id,
            "device_model": request.device_model,
            "os_version": request.os_version,
            "app_version": request.app_version,
        }

        token_record = await push_notification_service.register_device_token(
            db=db,
            user_id=current_user.id,
            token=request.token,
            device_info=device_info,
        )

        return TokenResponse(
            id=token_record.id,
            token=token_record.token[:20] + "...",  # Truncate for security
            platform=token_record.platform,
            is_active=token_record.is_active,
            created_at=token_record.created_at.isoformat(),
            last_used_at=token_record.last_used_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to register token for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to register device token: {str(e)}"
        )


@router.post("/unregister-token")
async def unregister_device_token(
    request: UnregisterTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Unregister a device token (disable push notifications for that device).

    Call this when the user logs out or disables notifications.
    """

    try:
        success = await push_notification_service.unregister_device_token(
            db=db,
            user_id=current_user.id,
            token=request.token,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Token not found")

        return {"success": True, "message": "Token unregistered successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister token: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to unregister token: {str(e)}"
        )


@router.get("/my-tokens", response_model=List[TokenResponse])
async def get_my_tokens(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get all active FCM tokens for the current user.

    Useful for debugging and managing multiple devices.
    """

    try:
        tokens = await push_notification_service.get_active_tokens(
            db=db,
            user_id=current_user.id,
        )

        return [
            TokenResponse(
                id=t.id,
                token=t.token[:20] + "...",
                platform=t.platform,
                is_active=t.is_active,
                created_at=t.created_at.isoformat(),
                last_used_at=t.last_used_at.isoformat(),
            )
            for t in tokens
        ]

    except Exception as e:
        logger.error(f"Failed to get tokens for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve tokens: {str(e)}"
        )


@router.post("/send", response_model=NotificationDeliveryResponse)
async def send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Send a push notification to a specific user.

    **Note:** This endpoint is typically called by backend services
    (e.g., appointment scheduler, automated alert service). Regular
    users cannot send notifications to others.

    **Request Body:**
    ```json
    {
      "user_id": "user-uuid",
      "notification_type": "appointment_reminder",
      "data": {
        "clinician_name": "Dr. Smith",
        "minutes_until": 15,
        "click_action": "OPEN_APPOINTMENT"
      }
    }
    ```
    """

    # Only clinicians and admins can send notifications
    if current_user.role not in ["clinician", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only clinicians and administrators can send notifications",
        )

    try:
        result = await push_notification_service.send_notification(
            db=db,
            user_id=request.user_id,
            notification_type=request.notification_type,
            data=request.data,
        )

        return NotificationDeliveryResponse(**result)

    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to send notification: {str(e)}"
        )


@router.post("/send-bulk", response_model=NotificationDeliveryResponse)
async def send_bulk_notification(
    request: BulkSendNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Send a notification to multiple users (bulk send).

    Useful for system announcements, mass reminders, etc.

    **Request Body:**
    ```json
    {
      "user_ids": ["uuid1", "uuid2", "uuid3"],
      "notification_type": "system_announcement",
      "data": {
        "title": "Scheduled Maintenance",
        "message": "System will be down for maintenance..."
      }
    }
    ```
    """

    # Only admins can send bulk notifications
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Only administrators can send bulk notifications"
        )

    try:
        result = await push_notification_service.send_bulk_notification(
            db=db,
            user_ids=request.user_ids,
            notification_type=request.notification_type,
            data=request.data,
        )

        return NotificationDeliveryResponse(**result)

    except Exception as e:
        logger.error(f"Failed to send bulk notification: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to send bulk notification: {str(e)}"
        )


@router.get("/test-send")
async def test_send_notification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Send a test notification to the current user.

    Useful for verifying that push notifications are working correctly
    for a specific device.
    """

    try:
        result = await push_notification_service.send_notification(
            db=db,
            user_id=current_user.id,
            notification_type=NotificationType.DAILY_CHECK_IN,
            data={
                "test": True,
                "user_id": str(current_user.id),
                "click_action": "OPEN_APP",
            },
        )

        return NotificationDeliveryResponse(**result)

    except Exception as e:
        logger.error(f"Failed to send test notification: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to send test notification: {str(e)}"
        )


@router.get("/types")
async def list_notification_types():
    """
    List all available notification types and their templates.

    Returns a dictionary of all notification types with their
    default templates, priorities, and usage examples.
    """

    from app.services.push_notification_service import NOTIFICATION_TEMPLATES

    notification_types = {}

    for type_key, template in NOTIFICATION_TEMPLATES.items():
        notification_types[type_key] = {
            "title": template["title"],
            "body": template["body"],
            "icon": template["icon"],
            "color": template["color"],
            "priority": template["priority"],
        }

    return {
        "notification_types": notification_types,
        "total_types": len(notification_types),
    }


@router.get("/status")
async def get_notification_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get notification status for the current user.

    Returns information about:
    - Number of active devices
    - Platform breakdown
    - Last notification sent
    """

    try:
        tokens = await push_notification_service.get_active_tokens(
            db=db,
            user_id=current_user.id,
        )

        ios_count = len([t for t in tokens if t.platform == "ios"])
        android_count = len([t for t in tokens if t.platform == "android"])

        # Get most recent token usage
        last_used = None
        if tokens:
            last_used = max([t.last_used_at for t in tokens])

        return {
            "user_id": str(current_user.id),
            "active_devices": len(tokens),
            "ios_devices": ios_count,
            "android_devices": android_count,
            "last_used": last_used.isoformat() if last_used else None,
            "push_enabled": len(tokens) > 0,
        }

    except Exception as e:
        logger.error(f"Failed to get notification status: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve status: {str(e)}"
        )
