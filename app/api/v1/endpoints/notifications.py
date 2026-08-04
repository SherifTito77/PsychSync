"""
Clinical Notification System API Endpoints

Manage clinician notification preferences and view notification history.
All endpoints require authentication and clinician/admin role.
"""

import logging
from datetime import datetime, time
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.db.models.notification import Notification, NotificationPreference
from app.db.models.user import User
from app.schemas.clinical import (
    NotificationListResponse,
    NotificationPreferenceCreate,
    NotificationPreferenceResponse,
    NotificationResponse,
    NotificationStatsResponse,
)
from app.services.clinical.notification_service import ClinicianNotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Get current user's notification preferences

    HIPAA: Users can only view their own preferences
    """
    # Check if user has clinician or admin role
    if current_user.role not in ["clinician", "admin"]:
        raise HTTPException(
            403,
            "Notification preferences only available to clinicians and administrators",
        )

    prefs_query = select(NotificationPreference).where(
        NotificationPreference.user_id == current_user.id
    )
    prefs = (await db.execute(prefs_query)).scalar_one_or_none()

    if not prefs:
        # Return default preferences
        return NotificationPreferenceResponse(
            id=None,  # Will be set on first update
            user_id=current_user.id,
            email_enabled=True,
            push_enabled=False,
            sms_enabled=False,
            in_app_enabled=True,
            notify_on_crisis_alert=True,
            notify_on_high_risk=True,
            notify_on_moderate_risk=False,
            notify_on_pending_review=True,
            notify_on_weekly_summary=False,
            min_severity_for_notification="moderate",
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0),
            timezone="America/New_York",
            bypass_quiet_hours_for_critical=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    return prefs


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    preferences: NotificationPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user's notification preferences

    HIPAA: Users can only update their own preferences
    """
    # Check role
    if current_user.role not in ["clinician", "admin"]:
        raise HTTPException(
            403,
            "Notification preferences only available to clinicians and administrators",
        )

    # Get existing preferences
    prefs_query = select(NotificationPreference).where(
        NotificationPreference.user_id == current_user.id
    )
    prefs = (await db.execute(prefs_query)).scalar_one_or_none()

    # Convert time strings to time objects
    try:
        quiet_start = datetime.strptime(preferences.quiet_hours_start, "%H:%M").time()
        quiet_end = datetime.strptime(preferences.quiet_hours_end, "%H:%M").time()
    except ValueError:
        raise HTTPException(
            400, "Invalid time format. Use HH:MM format (e.g., '22:00')"
        )

    if prefs:
        # Update existing
        prefs.email_enabled = preferences.email_enabled
        prefs.push_enabled = preferences.push_enabled
        prefs.sms_enabled = preferences.sms_enabled
        prefs.in_app_enabled = preferences.in_app_enabled
        prefs.notify_on_crisis_alert = preferences.notify_on_crisis_alert
        prefs.notify_on_high_risk = preferences.notify_on_high_risk
        prefs.notify_on_moderate_risk = preferences.notify_on_moderate_risk
        prefs.notify_on_pending_review = preferences.notify_on_pending_review
        prefs.notify_on_weekly_summary = preferences.notify_on_weekly_summary
        prefs.min_severity_for_notification = preferences.min_severity_for_notification
        prefs.quiet_hours_enabled = preferences.quiet_hours_enabled
        prefs.quiet_hours_start = quiet_start
        prefs.quiet_hours_end = quiet_end
        prefs.timezone = preferences.timezone
        prefs.bypass_quiet_hours_for_critical = (
            preferences.bypass_quiet_hours_for_critical
        )
        prefs.updated_at = datetime.utcnow()

    else:
        # Create new
        prefs = NotificationPreference(
            user_id=current_user.id,
            org_id=current_user.org_id,
            email_enabled=preferences.email_enabled,
            push_enabled=preferences.push_enabled,
            sms_enabled=preferences.sms_enabled,
            in_app_enabled=preferences.in_app_enabled,
            notify_on_crisis_alert=preferences.notify_on_crisis_alert,
            notify_on_high_risk=preferences.notify_on_high_risk,
            notify_on_moderate_risk=preferences.notify_on_moderate_risk,
            notify_on_pending_review=preferences.notify_on_pending_review,
            notify_on_weekly_summary=preferences.notify_on_weekly_summary,
            min_severity_for_notification=preferences.min_severity_for_notification,
            quiet_hours_enabled=preferences.quiet_hours_enabled,
            quiet_hours_start=quiet_start,
            quiet_hours_end=quiet_end,
            timezone=preferences.timezone,
            bypass_quiet_hours_for_critical=preferences.bypass_quiet_hours_for_critical,
        )
        db.add(prefs)

    await db.commit()
    await db.refresh(prefs)

    logger.info(f"Updated notification preferences for user {current_user.id}")

    return prefs


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False, description="Filter to only unread notifications"),
    notification_type: Optional[str] = Query(
        None, description="Filter by notification type"
    ),
    limit: int = Query(
        50, ge=1, le=100, description="Number of notifications to return"
    ),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List notifications for current user

    HIPAA: Users can only view their own notifications
    """
    # Check role
    if current_user.role not in ["clinician", "admin"]:
        raise HTTPException(
            403, "Notifications only available to clinicians and administrators"
        )

    # Build base query
    query = select(Notification).where(Notification.recipient_id == current_user.id)

    # Apply filters
    if unread_only:
        query = query.where(Notification.read == False)

    if notification_type:
        query = query.where(Notification.notification_type == notification_type)

    # Get total count
    count_query = select(func.count(Notification.id)).where(
        Notification.recipient_id == current_user.id
    )
    if unread_only:
        count_query = count_query.where(Notification.read == False)
    if notification_type:
        count_query = count_query.where(
            Notification.notification_type == notification_type
        )

    total = (await db.execute(count_query)).scalar()

    # Get unread count
    unread_query = select(func.count(Notification.id)).where(
        and_(Notification.recipient_id == current_user.id, Notification.read == False)
    )
    unread_count = (await db.execute(unread_query)).scalar()

    # Apply pagination and ordering
    query = query.order_by(desc(Notification.created_at)).limit(limit).offset(offset)

    notifications = (await db.execute(query)).scalars().all()

    return NotificationListResponse(
        notifications=notifications, total=total, unread_count=unread_count
    )


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a notification as read

    HIPAA: Users can only mark their own notifications as read
    """
    # Check role
    if current_user.role not in ["clinician", "admin"]:
        raise HTTPException(
            403, "Notifications only available to clinicians and administrators"
        )

    # Get notification
    notification = await db.get(Notification, notification_id)

    if not notification:
        raise HTTPException(404, "Notification not found")

    # Verify ownership
    if notification.recipient_id != current_user.id:
        raise HTTPException(403, "You can only mark your own notifications as read")

    # Mark as read
    notification.read = True
    notification.read_at = datetime.utcnow()
    notification.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(notification)

    logger.info(
        f"Notification {notification_id} marked as read by user {current_user.id}"
    )

    return notification


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Mark all unread notifications as read

    HIPAA: Users can only mark their own notifications as read
    """
    # Check role
    if current_user.role not in ["clinician", "admin"]:
        raise HTTPException(
            403, "Notifications only available to clinicians and administrators"
        )

    # Get all unread notifications
    query = select(Notification).where(
        and_(Notification.recipient_id == current_user.id, Notification.read == False)
    )

    notifications = (await db.execute(query)).scalars().all()

    # Mark all as read
    for notification in notifications:
        notification.read = True
        notification.read_at = datetime.utcnow()
        notification.updated_at = datetime.utcnow()

    await db.commit()

    logger.info(
        f"Marked {len(notifications)} notifications as read for user {current_user.id}"
    )

    return {"marked_as_read": len(notifications)}


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Get notification statistics for current user

    HIPAA: Users can only view their own statistics
    """
    # Check role
    if current_user.role not in ["clinician", "admin"]:
        raise HTTPException(
            403, "Notifications only available to clinicians and administrators"
        )

    # Total sent
    total_sent_query = select(func.count(Notification.id)).where(
        Notification.recipient_id == current_user.id
    )
    total_sent = (await db.execute(total_sent_query)).scalar() or 0

    # Total delivered
    total_delivered_query = select(func.count(Notification.id)).where(
        and_(
            Notification.recipient_id == current_user.id,
            Notification.delivery_status == "sent",
        )
    )
    total_delivered = (await db.execute(total_delivered_query)).scalar() or 0

    # Total failed
    total_failed_query = select(func.count(Notification.id)).where(
        and_(
            Notification.recipient_id == current_user.id,
            Notification.delivery_status == "failed",
        )
    )
    total_failed = (await db.execute(total_failed_query)).scalar() or 0

    # Unread count
    unread_query = select(func.count(Notification.id)).where(
        and_(Notification.recipient_id == current_user.id, Notification.read == False)
    )
    unread_count = (await db.execute(unread_query)).scalar() or 0

    # By type
    by_type_query = (
        select(
            Notification.notification_type, func.count(Notification.id).label("count")
        )
        .where(Notification.recipient_id == current_user.id)
        .group_by(Notification.notification_type)
    )

    by_type_results = (await db.execute(by_type_query)).all()
    by_type = {nt: count for nt, count in by_type_results}

    # By priority
    by_priority_query = (
        select(Notification.priority, func.count(Notification.id).label("count"))
        .where(Notification.recipient_id == current_user.id)
        .group_by(Notification.priority)
    )

    by_priority_results = (await db.execute(by_priority_query)).all()
    by_priority = {p: count for p, count in by_priority_results}

    return NotificationStatsResponse(
        total_sent=total_sent,
        total_delivered=total_delivered,
        total_failed=total_failed,
        unread_count=unread_count,
        by_type=by_type,
        by_priority=by_priority,
    )


@router.post("/test-pending-reviews")
async def trigger_pending_review_notifications(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger pending review notifications for organization

    HIPAA: Requires admin role
    """
    # Admin only
    if current_user.role != "admin":
        raise HTTPException(
            403, "Only administrators can manually trigger notifications"
        )

    if not current_user.org_id:
        raise HTTPException(403, "User must belong to an organization")

    try:
        notification_service = ClinicianNotificationService(db)
        result = await notification_service.notify_of_pending_reviews(
            org_id=str(current_user.org_id), hours_threshold=24
        )

        logger.info(
            f"Pending review notifications triggered by admin {current_user.id}: {result}"
        )

        return result

    except Exception as e:
        logger.error(f"Error triggering pending review notifications: {str(e)}")
        raise HTTPException(500, f"Failed to trigger notifications: {str(e)}")
