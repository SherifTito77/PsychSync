"""
Push Notification Service

Manages Firebase Cloud Messaging (FCM) push notifications for mobile apps.
Supports both iOS (APNS via FCM) and Android platforms.

Features:
- Multi-device token management
- Scheduled notifications
- Notification templates
- User preferences
- Delivery tracking
- Error handling and retry logic
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import httpx

from app.db.models.user import User
from app.db.models.notification import NotificationPreference, PushNotificationToken
from app.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Notification Types and Templates
# =============================================================================

class NotificationType(str):
    """Enumeration of notification types"""

    # Assessment reminders
    ASSESSMENT_REMINDER = "assessment_reminder"
    ASSESSMENT_DUE = "assessment_due"
    ASSESSMENT_OVERDUE = "assessment_overdue"

    # Appointment notifications
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_CANCELED = "appointment_canceled"
    APPOINTMENT_RESCHEDULED = "appointment_rescheduled"

    # Clinical alerts (for clinicians)
    CLINICAL_ALERT = "clinical_alert"
    CRISIS_ALERT = "crisis_alert"
    HIGH_RISK_ALERT = "high_risk_alert"

    # Messages and communication
    NEW_MESSAGE = "new_message"
    CLINICIAN_MESSAGE = "clinician_message"
    SYSTEM_ANNOUNCEMENT = "system_announcement"

    # Wellness and tracking
    DAILY_CHECK_IN = "daily_check_in"
    WELLNESS_REMINDER = "wellness_reminder"
    PROGRESS_UPDATE = "progress_update"

    # Account and settings
    ACCOUNT_UPDATE = "account_update"
    PRIVACY_UPDATE = "privacy_update"
    SECURITY_ALERT = "security_alert"


class NotificationPriority(str):
    """FCM notification priority levels"""

    NORMAL = "normal"  # Priority 5 - Delivery may be delayed for power saving
    HIGH = "high"  # Priority 10 - Delivered immediately


# Notification templates
NOTIFICATION_TEMPLATES = {
    NotificationType.ASSESSMENT_REMINDER: {
        "title": "Assessment Reminder",
        "body": "You have a pending assessment to complete.",
        "icon": "assessment",
        "color": "#6366F1",
        "priority": NotificationPriority.NORMAL,
    },
    NotificationType.ASSESSMENT_DUE: {
        "title": "Assessment Due Soon",
        "body": "Your {assessment_name} is due in {hours_until_due} hours.",
        "icon": "clock",
        "color": "#F59E0B",
        "priority": NotificationPriority.NORMAL,
    },
    NotificationType.ASSESSMENT_OVERDUE: {
        "title": "Overdue Assessment",
        "body": "Your {assessment_name} is {days_overdue} days overdue. Please complete it soon.",
        "icon": "alert",
        "color": "#EF4444",
        "priority": NotificationPriority.HIGH,
    },
    NotificationType.APPOINTMENT_SCHEDULED: {
        "title": "Appointment Scheduled",
        "body": "Your appointment with {clinician_name} is scheduled for {appointment_time}.",
        "icon": "calendar",
        "color": "#10B981",
        "priority": NotificationPriority.NORMAL,
    },
    NotificationType.APPOINTMENT_REMINDER: {
        "title": "Appointment Reminder",
        "body": "Reminder: Appointment with {clinician_name} in {minutes_until} minutes.",
        "icon": "bell",
        "color": "#6366F1",
        "priority": NotificationPriority.HIGH,
    },
    NotificationType.APPOINTMENT_CANCELED: {
        "title": "Appointment Canceled",
        "body": "Your appointment scheduled for {appointment_time} has been canceled.",
        "icon": "x-circle",
        "color": "#EF4444",
        "priority": NotificationPriority.HIGH,
    },
    NotificationType.APPOINTMENT_RESCHEDULED: {
        "title": "Appointment Rescheduled",
        "body": "Your appointment has been rescheduled to {new_appointment_time}.",
        "icon": "refresh",
        "color": "#F59E0B",
        "priority": NotificationPriority.HIGH,
    },
    NotificationType.CLINICAL_ALERT: {
        "title": "Clinical Alert",
        "body": "{alert_type} requires attention for {patient_name}.",
        "icon": "alert-triangle",
        "color": "#F59E0B",
        "priority": NotificationPriority.HIGH,
    },
    NotificationType.CRISIS_ALERT: {
        "title": "🚨 CRISIS ALERT",
        "body": "{patient_name} has triggered crisis indicators. Immediate action required.",
        "icon": "alert-octagon",
        "color": "#EF4444",
        "priority": NotificationPriority.HIGH,
    },
    NotificationType.HIGH_RISK_ALERT: {
        "title": "High Risk Alert",
        "body": "{patient_name} has been flagged as high risk based on recent assessment.",
        "icon": "flag",
        "color": "#F59E0B",
        "priority": NotificationPriority.HIGH,
    },
    NotificationType.NEW_MESSAGE: {
        "title": "New Message",
        "body": "{sender_name} sent you a message.",
        "icon": "message",
        "color": "#6366F1",
        "priority": NotificationPriority.NORMAL,
    },
    NotificationType.CLINICIAN_MESSAGE: {
        "title": "Message from {clinician_name}",
        "body": "{message_preview}",
        "icon": "user-md",
        "color": "#10B981",
        "priority": NotificationPriority.HIGH,
    },
    NotificationType.DAILY_CHECK_IN: {
        "title": "Daily Check-In",
        "body": "How are you feeling today? Take a moment to check in.",
        "icon": "heart",
        "color": "#EC4899",
        "priority": NotificationPriority.NORMAL,
    },
    NotificationType.WELLNESS_REMINDER: {
        "title": "Wellness Reminder",
        "body": "Time for your wellness check-in. Your mental health matters.",
        "icon": "sparkles",
        "color": "#8B5CF6",
        "priority": NotificationPriority.NORMAL,
    },
    NotificationType.PROGRESS_UPDATE: {
        "title": "Progress Update",
        "body": "You've made progress! View your wellness journey.",
        "icon": "trending-up",
        "color": "#10B981",
        "priority": NotificationPriority.NORMAL,
    },
    NotificationType.SECURITY_ALERT: {
        "title": "Security Alert",
        "body": "{alert_message}",
        "icon": "shield",
        "color": "#EF4444",
        "priority": NotificationPriority.HIGH,
    },
}


# =============================================================================
# Main Service Class
# =============================================================================

class PushNotificationService:
    """
    Service for managing Firebase Cloud Messaging (FCM) push notifications.
    Handles token registration, notification sending, and delivery tracking.
    """

    def __init__(self):
        self.fcm_server_key = settings.FCM_SERVER_KEY
        self.fcm_api_url = "https://fcm.googleapis.com/fcm/send"
        self.timeout = 20.0  # Increased from 10s to 20s for better reliability

    # -------------------------------------------------------------------------
    # Token Management
    # -------------------------------------------------------------------------

    async def register_device_token(
        self,
        db: AsyncSession,
        user_id: UUID,
        token: str,
        device_info: Dict[str, Any],
    ) -> PushNotificationToken:
        """
        Register or update a device's FCM token.

        Args:
            db: Database session
            user_id: User UUID
            token: FCM device token
            device_info: Device information (platform, model, os_version, app_version)

        Returns:
            PushNotificationToken: Created or updated token record
        """
        try:
            # Check if token already exists for this user
            query = select(PushNotificationToken).where(
                and_(
                    PushNotificationToken.user_id == user_id,
                    PushNotificationToken.token == token,
                )
            )
            result = await db.execute(query)
            existing_token = result.scalar_one_or_none()

            if existing_token:
                # Update existing token
                existing_token.device_info = device_info
                existing_token.last_used_at = datetime.utcnow()
                existing_token.is_active = True
                await db.commit()
                await db.refresh(existing_token)

                logger.info(f"Updated FCM token for user {user_id}: {token[:20]}...")
                return existing_token
            else:
                # Create new token record
                new_token = PushNotificationToken(
                    id=uuid4(),
                    user_id=user_id,
                    token=token,
                    platform=device_info.get("platform", "unknown"),
                    device_info=device_info,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    last_used_at=datetime.utcnow(),
                )

                db.add(new_token)
                await db.commit()
                await db.refresh(new_token)

                logger.info(f"Registered new FCM token for user {user_id}: {token[:20]}...")
                return new_token

        except Exception as e:
            logger.error(f"Failed to register device token: {str(e)}")
            await db.rollback()
            raise

    async def unregister_device_token(
        self,
        db: AsyncSession,
        user_id: UUID,
        token: str,
    ) -> bool:
        """
        Unregister a device token (deactivate it).

        Args:
            db: Database session
            user_id: User UUID
            token: FCM device token

        Returns:
            bool: True if successfully unregistered
        """
        try:
            query = select(PushNotificationToken).where(
                and_(
                    PushNotificationToken.user_id == user_id,
                    PushNotificationToken.token == token,
                )
            )
            result = await db.execute(query)
            token_record = result.scalar_one_or_none()

            if token_record:
                token_record.is_active = False
                token_record.deactivated_at = datetime.utcnow()
                await db.commit()

                logger.info(f"Unregistered FCM token for user {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to unregister device token: {str(e)}")
            await db.rollback()
            return False

    async def get_active_tokens(
        self,
        db: AsyncSession,
        user_id: UUID,
        platform: Optional[str] = None,
    ) -> List[PushNotificationToken]:
        """
        Get all active FCM tokens for a user.

        Args:
            db: Database session
            user_id: User UUID
            platform: Optional platform filter (ios, android)

        Returns:
            List of active PushNotificationToken records
        """
        try:
            query = select(PushNotificationToken).where(
                and_(
                    PushNotificationToken.user_id == user_id,
                    PushNotificationToken.is_active == True,
                )
            )

            if platform:
                query = query.where(PushNotificationToken.platform == platform)

            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Failed to get active tokens: {str(e)}")
            return []

    # -------------------------------------------------------------------------
    # Notification Sending
    # -------------------------------------------------------------------------

    async def send_notification(
        self,
        db: AsyncSession,
        user_id: UUID,
        notification_type: str,
        data: Optional[Dict[str, Any]] = None,
        tokens: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send a push notification to a user.

        Args:
            db: Database session
            user_id: User UUID
            notification_type: Type of notification (from NotificationType)
            data: Additional data for notification (variables, deep link, etc.)
            tokens: Specific tokens to send to (optional, gets all active if not provided)

        Returns:
            Dict with success status, delivery report, and error details
        """
        try:
            # Get notification template
            template = NOTIFICATION_TEMPLATES.get(notification_type)
            if not template:
                logger.error(f"Unknown notification type: {notification_type}")
                return {"success": False, "error": "Unknown notification type"}

            # Check user preferences
            if not await self._check_user_preferences(db, user_id, notification_type):
                logger.info(f"User {user_id} has disabled {notification_type} notifications")
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "User preferences",
                    "tokens_sent": 0,
                }

            # Get tokens to send to
            if not tokens:
                tokens_records = await self.get_active_tokens(db, user_id)
                tokens = [t.token for t in tokens_records]

            if not tokens:
                logger.info(f"No active tokens found for user {user_id}")
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "No active tokens",
                    "tokens_sent": 0,
                }

            # Build notification payload
            payload = await self._build_notification_payload(
                notification_type=notification_type,
                template=template,
                data=data or {},
                tokens=tokens,
            )

            # Send to FCM
            results = await self._send_to_fcm(payload)

            # Update token usage
            await self._update_token_usage(db, tokens)

            # Log delivery
            await self._log_notification_delivery(
                db=db,
                user_id=user_id,
                notification_type=notification_type,
                tokens_sent=len(tokens),
                results=results,
            )

            return {
                "success": True,
                "tokens_sent": len(tokens),
                "successful": len([r for r in results if r.get("success")]),
                "failed": len([r for r in results if not r.get("success")]),
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tokens_sent": 0,
            }

    async def send_bulk_notification(
        self,
        db: AsyncSession,
        user_ids: List[UUID],
        notification_type: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a notification to multiple users (batch send).

        Args:
            db: Database session
            user_ids: List of user UUIDs
            notification_type: Type of notification
            data: Additional notification data

        Returns:
            Dict with bulk send results
        """
        try:
            # Get all active tokens for all users
            all_tokens = []
            for user_id in user_ids:
                user_tokens = await self.get_active_tokens(db, user_id)
                all_tokens.extend([t.token for t in user_tokens])

            if not all_tokens:
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "No active tokens",
                    "users_reached": 0,
                }

            # Build notification payload
            template = NOTIFICATION_TEMPLATES.get(notification_type, {})
            payload = await self._build_notification_payload(
                notification_type=notification_type,
                template=template,
                data=data or {},
                tokens=all_tokens,
            )

            # Send to FCM
            results = await self._send_to_fcm(payload)

            return {
                "success": True,
                "users_reached": len(user_ids),
                "tokens_sent": len(all_tokens),
                "successful": len([r for r in results if r.get("success")]),
                "failed": len([r for r in results if not r.get("success")]),
            }

        except Exception as e:
            logger.error(f"Failed to send bulk notification: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "users_reached": 0,
            }

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    async def _check_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        notification_type: str,
    ) -> bool:
        """Check if user has enabled this notification type"""

        try:
            query = select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
            result = await db.execute(query)
            preferences = result.scalar_one_or_none()

            if not preferences:
                # Default preferences - allow most notifications
                return True

            # Check based on notification type
            if "assessment" in notification_type:
                return preferences.assessment_reminders != False

            if "appointment" in notification_type:
                return preferences.appointment_reminders != False

            if "alert" in notification_type and "crisis" not in notification_type:
                return preferences.general_notifications != False

            if "crisis" in notification_type:
                # Always send crisis alerts regardless of preferences
                return True

            if "message" in notification_type:
                return preferences.message_notifications != False

            # Default to True
            return True

        except Exception as e:
            logger.error(f"Failed to check user preferences: {str(e)}")
            return True  # Default to sending if check fails

    async def _build_notification_payload(
        self,
        notification_type: str,
        template: Dict[str, Any],
        data: Dict[str, Any],
        tokens: List[str],
    ) -> Dict[str, Any]:
        """Build FCM notification payload"""

        # Personalize title and body with data
        title = template.get("title", "")
        body = template.get("body", "")

        for key, value in data.items():
            title = title.replace(f"{{{key}}}", str(value))
            body = body.replace(f"{{{key}}}", str(value))

        # Build base payload
        payload = {
            "registration_ids": tokens,
            "notification": {
                "title": title,
                "body": body,
                "sound": "default",
                "badge": 1,
                "icon": template.get("icon", "ic_notification"),
                "color": template.get("color", "#6366F1"),
                "click_action": data.get("click_action", "FCM_PLUGIN_ACTIVITY"),
            },
            "data": {
                "type": notification_type,
                "user_id": str(data.get("user_id", "")),
                "title": title,
                "body": body,
                **{k: v for k, v in data.items() if k != "user_id"},
            },
            "priority": template.get("priority", NotificationPriority.NORMAL),
        }

        # Android-specific settings
        payload["android"] = {
            "notification": {
                "notification_count": 1,
                "channel_id": notification_type,
            }
        }

        # iOS-specific settings
        payload["apns"] = {
            "payload": {
                "aps": {
                    "alert": {
                        "title": title,
                        "body": body,
                    },
                    "sound": "default",
                    "badge": 1,
                },
            }
        }

        return payload

    async def _send_to_fcm(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Send notification to FCM servers using resilient HTTP client.

        Features:
        - Automatic retry with exponential backoff
        - Circuit breaker to prevent cascading failures
        - 20-second timeout
        - Connection pooling for better performance
        """

        try:
            from app.core.resilient_client import resilient_http_client, HTTPClientError

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"key={self.fcm_server_key}",
            }

            try:
                # Use resilient HTTP client with automatic retry
                response = await resilient_http_client.post(
                    self.fcm_api_url,
                    json=payload,
                    headers=headers,
                )

                if response.status_code == 200:
                    result = response.json()

                    # FCM returns results for each token
                    if "results" in result:
                        return result["results"]

                    return [{"success": True, "message_id": result.get("message_id")}]

                else:
                    logger.error(f"FCM API error: {response.status_code} - {response.text}")
                    return [{"success": False, "error": "FCM API error"}]

            except HTTPClientError as e:
                logger.error(f"FCM HTTP client error after retries: {str(e)}")
                return [{"success": False, "error": f"Request failed: {str(e)}"}]

        except Exception as e:
            logger.error(f"Failed to send to FCM: {str(e)}")
            return [{"success": False, "error": str(e)}]

    async def _update_token_usage(self, db: AsyncSession, tokens: List[str]):
        """Update last_used_at for sent tokens"""

        try:
            for token in tokens:
                query = select(PushNotificationToken).where(
                    PushNotificationToken.token == token
                )
                result = await db.execute(query)
                token_record = result.scalar_one_or_none()

                if token_record:
                    token_record.last_used_at = datetime.utcnow()

            await db.commit()

        except Exception as e:
            logger.error(f"Failed to update token usage: {str(e)}")
            await db.rollback()

    async def _log_notification_delivery(
        self,
        db: AsyncSession,
        user_id: UUID,
        notification_type: str,
        tokens_sent: int,
        results: List[Dict[str, Any]],
    ):
        """Log notification delivery for analytics"""

        try:
            successful = len([r for r in results if r.get("success")])

            logger.info(
                f"Notification delivery report: "
                f"user={user_id}, type={notification_type}, "
                f"sent={tokens_sent}, successful={successful}, "
                f"failed={tokens_sent - successful}"
            )

            # TODO: Store in notification_logs table if needed

        except Exception as e:
            logger.error(f"Failed to log delivery: {str(e)}")


# =============================================================================
# Service Instance
# =============================================================================

push_notification_service = PushNotificationService()
