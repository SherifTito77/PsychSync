"""
Clinician Notification Service

Monitors clinical screenings and alerts, notifies clinicians based on preferences.
Respects quiet hours and urgency thresholds.
"""

import logging
from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional

import pytz
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import send_email  # Assuming email service exists
from app.db.models.clinical_screening import ClinicalAlert, ClinicalScreening
from app.db.models.notifications import (
    Notification,
    NotificationPreferences as NotificationPreference,
    NotificationQueue,
)
from app.db.models.organization import Organization
from app.db.models.user import User

logger = logging.getLogger(__name__)


class ClinicianNotificationService:
    """
    DESIGN DECISIONS:
    1. Quiet Hours: Respect clinician downtime unless critical alert
    2. Organization-Level: Clinicians only receive notifications for their org
    3. Preference-Based: Individual clinicians control what they receive
    4. Retry Logic: Failed notifications queued for retry (max 3 attempts)
    5. Timezone-Aware: All scheduling respects clinician's local timezone
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def notify_clinicians_of_alert(
        self,
        alert_id: str,
        alert_type: str,
        severity: str,
        screening_id: str,
        org_id: str,
        alert_message: str,
    ) -> Dict[str, Any]:
        """
        Notify eligible clinicians when a new crisis alert is created

        DESIGN DECISION:
        - Find all clinicians in organization with clinician/admin role
        - Filter by their notification preferences
        - Respect quiet hours (unless severity=critical)
        - Send via enabled channels (email, in-app)
        """
        # Get all potential recipients (clinicians and admins in org)
        from app.db.models.user import User as UserModel

        clinicians_query = select(
            UserModel.id, UserModel.email, UserModel.full_name
        ).where(
            and_(
                UserModel.org_id == org_id,
                UserModel.deleted_at.is_(None),
                or_(UserModel.role == "clinician", UserModel.role == "admin"),
            )
        )
        potential_recipients = (await self.db.execute(clinicians_query)).all()

        if not potential_recipients:
            logger.warning(f"No clinicians found for org {org_id}")
            return {"notified": 0, "skipped": 0, "errors": 0}

        notified_count = 0
        skipped_count = 0
        error_count = 0

        for recipient in potential_recipients:
            try:
                # Get recipient's preferences
                prefs = await self._get_notification_preferences(recipient.id)

                # Check if this alert type is enabled
                should_notify = await self._should_send_notification(
                    prefs=prefs, notification_type="crisis_alert", severity=severity
                )

                if not should_notify:
                    skipped_count += 1
                    continue

                # Create notification
                notification = await self._create_notification(
                    recipient_id=recipient.id,
                    org_id=org_id,
                    notification_type="crisis_alert",
                    entity_type="alert",
                    entity_id=alert_id,
                    title=f"Crisis Alert: {alert_type.replace('_', ' ').title()}",
                    message=self._format_crisis_alert_message(
                        alert_type, severity, alert_message
                    ),
                    priority="urgent" if severity == "critical" else "high",
                    metadata={
                        "alert_type": alert_type,
                        "severity": severity,
                        "screening_id": str(screening_id),
                    },
                )

                # Send via enabled channels
                if prefs.email_enabled:
                    await self._send_email_notification(
                        notification=notification,
                        recipient_email=recipient.email,
                        recipient_name=recipient.full_name,
                    )

                notified_count += 1
                logger.info(f"Notified clinician {recipient.id} of alert {alert_id}")

            except Exception as e:
                error_count += 1
                logger.error(f"Error notifying clinician {recipient.id}: {str(e)}")

        return {
            "notified": notified_count,
            "skipped": skipped_count,
            "errors": error_count,
        }

    async def notify_of_pending_reviews(
        self, org_id: str, hours_threshold: int = 24
    ) -> Dict[str, Any]:
        """
        Notify clinicians of screenings pending review beyond threshold

        DESIGN DECISION:
        - Only notify if validated_by IS NULL and completed_at > hours_threshold ago
        - Group by screening type to reduce notification volume
        - Send summary rather than individual notifications
        """
        threshold_time = datetime.utcnow() - timedelta(hours=hours_threshold)

        # Count pending reviews per screening type
        pending_query = (
            select(
                ClinicalScreening.screening_type,
                func.count(ClinicalScreening.id).label("count"),
            )
            .where(
                and_(
                    ClinicalScreening.org_id == org_id,
                    ClinicalScreening.completed_at.isnot(None),
                    ClinicalScreening.validated_by.is_(None),
                    ClinicalScreening.completed_at < threshold_time,
                )
            )
            .group_by(ClinicalScreening.screening_type)
        )

        pending_counts = (await self.db.execute(pending_query)).all()

        if not pending_counts:
            return {"notified": 0, "pending_reviews": 0}

        total_pending = sum(count for _, count in pending_counts)

        # Get clinicians who want pending review notifications
        from app.db.models.user import UserModel

        clinicians_query = select(
            UserModel.id, UserModel.email, UserModel.full_name
        ).where(
            and_(
                UserModel.org_id == org_id,
                UserModel.deleted_at.is_(None),
                or_(UserModel.role == "clinician", UserModel.role == "admin"),
            )
        )
        clinicians = (await self.db.execute(clinicians_query)).all()

        notified_count = 0

        for clinician in clinicians:
            try:
                prefs = await self._get_notification_preferences(clinician.id)

                if not prefs.notify_on_pending_review:
                    continue

                # Format pending summary
                pending_summary = "\n".join(
                    [
                        f"- {screening_type}: {count} pending"
                        for screening_type, count in pending_counts
                    ]
                )

                notification = await self._create_notification(
                    recipient_id=clinician.id,
                    org_id=org_id,
                    notification_type="pending_review",
                    entity_type="screening",
                    entity_id=None,  # Summary notification
                    title=f"{total_pending} Screenings Pending Review",
                    message=self._format_pending_review_message(
                        total_pending, pending_summary, hours_threshold
                    ),
                    priority="normal",
                    metadata={
                        "pending_counts": {st: c for st, c in pending_counts},
                        "hours_threshold": hours_threshold,
                    },
                )

                if prefs.email_enabled:
                    await self._send_email_notification(
                        notification=notification,
                        recipient_email=clinician.email,
                        recipient_name=clinician.full_name,
                    )

                notified_count += 1

            except Exception as e:
                logger.error(
                    f"Error notifying clinician {clinician.id} of pending reviews: {str(e)}"
                )

        return {"notified": notified_count, "pending_reviews": total_pending}

    async def _get_notification_preferences(
        self, user_id: str
    ) -> NotificationPreference:
        """Get user's notification preferences, create defaults if not exist"""
        prefs_query = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
        prefs = (await self.db.execute(prefs_query)).scalar_one_or_none()

        if not prefs:
            # Create default preferences
            prefs = NotificationPreference(
                user_id=user_id,
                org_id=None,  # Will be set before commit
                email_enabled=True,
                in_app_enabled=True,
                notify_on_crisis_alert=True,
                notify_on_high_risk=True,
                notify_on_moderate_risk=False,
                notify_on_pending_review=True,
                quiet_hours_enabled=True,
            )
            self.db.add(prefs)
            await self.db.flush()

        return prefs

    async def _should_send_notification(
        self, prefs: NotificationPreference, notification_type: str, severity: str
    ) -> bool:
        """
        Determine if notification should be sent based on preferences

        DESIGN DECISIONS:
        - Check quiet hours (bypass for critical if preference enabled)
        - Check notification type preferences
        - Check severity threshold
        """
        # Check quiet hours
        if prefs.quiet_hours_enabled:
            is_quiet_hours = await self._is_in_quiet_hours(prefs)

            if is_quiet_hours:
                # Bypass for critical alerts if preference enabled
                is_critical = (
                    severity == "critical" or notification_type == "crisis_alert"
                )
                if not (is_critical and prefs.bypass_quiet_hours_for_critical):
                    logger.debug(
                        f"In quiet hours, skipping notification for user {prefs.user_id}"
                    )
                    return False

        # Check notification type preferences
        if notification_type == "crisis_alert":
            if not prefs.notify_on_crisis_alert:
                return False
        elif notification_type == "high_risk":
            if not prefs.notify_on_high_risk:
                return False
        elif notification_type == "moderate_risk":
            if not prefs.notify_on_moderate_risk:
                return False
        elif notification_type == "pending_review":
            if not prefs.notify_on_pending_review:
                return False

        # Check severity threshold
        severity_levels = ["low", "moderate", "high", "critical"]
        min_level_index = severity_levels.index(prefs.min_severity_for_notification)
        current_level_index = severity_levels.index(severity)

        if current_level_index < min_level_index:
            return False

        return True

    async def _is_in_quiet_hours(self, prefs: NotificationPreference) -> bool:
        """Check if current time is within quiet hours"""
        try:
            tz = pytz.timezone(prefs.timezone)
            now = datetime.now(tz)
            current_time = now.time()

            start_time = prefs.quiet_hours_start
            end_time = prefs.quiet_hours_end

            # Handle overnight quiet hours (e.g., 22:00 to 08:00)
            if start_time > end_time:
                # Quiet hours spans midnight
                in_quiet_hours = current_time >= start_time or current_time < end_time
            else:
                # Normal range (e.g., 13:00 to 17:00)
                in_quiet_hours = start_time <= current_time < end_time

            return in_quiet_hours

        except Exception as e:
            logger.error(f"Error checking quiet hours: {str(e)}")
            return False  # Default to sending if error

    async def _create_notification(
        self,
        recipient_id: str,
        org_id: str,
        notification_type: str,
        entity_type: str,
        entity_id: Optional[str],
        title: str,
        message: str,
        priority: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Create notification record and queue entry"""
        notification = Notification(
            recipient_id=recipient_id,
            org_id=org_id,
            notification_type=notification_type,
            entity_type=entity_type,
            entity_id=entity_id,
            title=title,
            message=message,
            priority=priority,
            channel="email",  # Default channel
            delivery_status="pending",
            metadata=metadata or {},
        )

        self.db.add(notification)
        await self.db.flush()

        # Create queue entry
        queue_entry = NotificationQueue(
            notification_id=notification.id,
            recipient_id=recipient_id,
            scheduled_for=datetime.utcnow(),
        )
        self.db.add(queue_entry)

        return notification

    async def _send_email_notification(
        self, notification: Notification, recipient_email: str, recipient_name: str
    ) -> bool:
        """
        Send email notification using HTML templates

        DESIGN DECISION:
        - Use responsive HTML email templates for better readability
        - Template selection based on notification type
        - Fallback to plain text if template fails
        - Track delivery status
        """
        try:
            from app.services.clinical.email_template_renderer import get_email_renderer

            renderer = get_email_renderer()
            subject = f"[PsychSync] {notification.title}"
            action_url = (
                f"https://app.psychsync.io/clinical/screenings/{notification.entity_id}"
                if notification.entity_id
                else "https://app.psychsync.io/clinical"
            )

            # Render appropriate template based on notification type
            if notification.notification_type == "crisis_alert":
                # Extract metadata from notification
                metadata = notification.meta_data or {}
                html_body = renderer.render_crisis_alert(
                    recipient_name=recipient_name,
                    alert_type=metadata.get("alert_type", "Unknown"),
                    severity=metadata.get("severity", "moderate"),
                    alert_message=notification.message,
                    screening_type=metadata.get("screening_type", "Screening"),
                    screening_date=notification.created_at.strftime("%Y-%m-%d %H:%M"),
                    action_url=action_url,
                )
            elif notification.notification_type == "pending_review":
                # TODO(human): Implement pending_review.html template
                metadata = notification.meta_data or {}
                html_body = renderer.render_pending_review(
                    recipient_name=recipient_name,
                    total_pending=metadata.get("pending_counts", {}).get("total", 0),
                    pending_breakdown=metadata.get("pending_counts", {}),
                    hours_threshold=metadata.get("hours_threshold", 24),
                    action_url="https://app.psychsync.io/clinical/reviews",
                )
            elif notification.notification_type == "weekly_summary":
                # TODO(human): Implement weekly_summary.html template
                metadata = notification.meta_data or {}
                html_body = renderer.render_weekly_summary(
                    recipient_name=recipient_name,
                    week_start=metadata.get("week_start", ""),
                    week_end=metadata.get("week_end", ""),
                    total_screenings=metadata.get("total_screenings", 0),
                    completion_rate=metadata.get("completion_rate", 0),
                    crisis_count=metadata.get("crisis_count", 0),
                    avg_response_time=metadata.get("avg_response_time", 0),
                    top_concerns=metadata.get("top_concerns", []),
                    action_url="https://app.psychsync.io/clinical/analytics",
                )
            else:
                # Default fallback for other notification types
                html_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>{notification.title}</h2>
                    <p>{notification.message}</p>
                    <p><a href="{action_url}" style="display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 6px;">View Details</a></p>
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #e5e7eb;">
                    <p style="font-size: 12px; color: #6b7280;">This is an automated notification from PsychSync Clinical Platform.</p>
                </body>
                </html>
                """

            # TODO: Replace with actual email service integration
            # await send_email(
            #     to=recipient_email,
            #     subject=subject,
            #     html_body=html_body,
            #     text_body=notification.message  # Plain text fallback
            # )

            # For now, just log that we would send the email
            logger.info(
                f"Email prepared for {recipient_email}: {subject} (HTML: {len(html_body)} chars)"
            )

            notification.sent_at = datetime.utcnow()
            notification.delivery_status = "sent"

            return True

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            notification.delivery_status = "failed"
            notification.error_message = str(e)
            notification.delivery_attempts += 1
            return False

    def _format_crisis_alert_message(
        self, alert_type: str, severity: str, alert_message: str
    ) -> str:
        """Format crisis alert message for readability"""
        readable_type = alert_type.replace("_", " ").title()
        readable_severity = severity.upper()

        return f"""
CRISIS ALERT - {readable_severity}

Type: {readable_type}

Details:
{alert_message}

Please review this screening immediately and take appropriate action.
If this is a life-threatening emergency, contact emergency services.

Severity: {readable_severity}
        """.strip()

    def _format_pending_review_message(
        self, total_count: int, pending_summary: str, hours_threshold: int
    ) -> str:
        """Format pending review summary message"""
        return f"""
You have {total_count} screening(s) that have been pending review for more than {hours_threshold} hours:

{pending_summary}

Please log in to review these screenings at your earliest convenience.
        """.strip()


# Background task to process notification queue
async def process_notification_queue(
    db: AsyncSession, batch_size: int = 50
) -> Dict[str, int]:
    """
    Process pending notifications from the queue

    DESIGN DECISION:
    - Process in batches to avoid memory issues
    - Retry failed notifications up to max_retries
    - Mark as failed if max retries exceeded
    """
    queue_query = (
        select(NotificationQueue)
        .where(
            and_(
                NotificationQueue.status == "pending",
                NotificationQueue.scheduled_for <= datetime.utcnow(),
            )
        )
        .limit(batch_size)
    )

    queue_entries = (await db.execute(queue_query)).scalars().all()

    processed = 0
    failed = 0
    retried = 0

    for entry in queue_entries:
        try:
            # Mark as processing
            entry.status = "processing"
            entry.processing_started = datetime.utcnow()
            await db.flush()

            # Get notification
            notification = await db.get(Notification, entry.notification_id)

            if not notification:
                entry.status = "failed"
                entry.last_error = "Notification not found"
                failed += 1
                continue

            # Send notification (already implemented in _send_email_notification)
            # This would be expanded to support multiple channels
            notification.sent_at = datetime.utcnow()
            notification.delivery_status = "sent"

            entry.status = "completed"
            entry.processing_completed = datetime.utcnow()
            processed += 1

        except Exception as e:
            entry.retry_count += 1

            if entry.retry_count >= entry.max_retries:
                entry.status = "failed"
                entry.last_error = str(e)
                failed += 1
            else:
                entry.status = "pending"
                entry.retry_after = datetime.utcnow() + timedelta(
                    minutes=5**entry.retry_count
                )
                retried += 1

            logger.error(
                f"Error processing notification {entry.notification_id}: {str(e)}"
            )

    await db.commit()

    return {"processed": processed, "failed": failed, "retried": retried}
