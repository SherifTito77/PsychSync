# app/services/notifications.py
"""
Notification Service
Handles both in-app notifications and email notifications for PsychSync users.
Supports multiple notification channels and templates.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging
from enum import Enum
import asyncio
from email.mime.text import MIMEText
from email.mime.html import MIMEText as MIMEHtml

from app.core.config import settings
from app.core.email import send_email_async

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    """Types of notifications supported"""
    TEAM_INVITATION = "team_invitation"
    TEAM_OPTIMIZATION_COMPLETE = "team_optimization_complete"
    ASSESSMENT_COMPLETED = "assessment_completed"
    ASSESSMENT_REMINDER = "assessment_reminder"
    PROFILE_UPDATE = "profile_update"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    TEAM_RECOMMENDATION = "team_recommendation"
    DEADLINE_REMINDER = "deadline_reminder"

class NotificationChannel(str, Enum):
    """Notification channels"""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"  # Future: mobile push notifications
    WEBHOOK = "webhook"  # Future: external integrations

@dataclass
class Notification:
    """Represents a notification"""
    id: Optional[str] = None
    user_id: int = None
    type: NotificationType = NotificationType.SYSTEM_ANNOUNCEMENT
    title: str = ""
    message: str = ""
    data: Dict[str, Any] = None
    channels: List[NotificationChannel] = None
    priority: str = "normal"  # low, normal, high, urgent
    expires_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.channels is None:
            self.channels = [NotificationChannel.IN_APP]
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class EmailTemplate:
    """Email template configuration"""
    subject: str
    html_body: str
    text_body: str
    from_email: str = None
    reply_to: str = None

class NotificationService:
    """
    Comprehensive notification service for PsychSync

    Features:
    - Multi-channel notifications (in-app, email)
    - Template-based emails
    - Notification scheduling
    - Priority handling
    - Batch processing
    """

    def __init__(self):
        self.email_templates = self._load_email_templates()
        self.notification_queue = []  # In production, use Redis/RabbitMQ

    def _load_email_templates(self) -> Dict[NotificationType, EmailTemplate]:
        """Load email templates for different notification types"""

        return {
            NotificationType.TEAM_INVITATION: EmailTemplate(
                subject="You've been invited to join a team!",
                html_body=self._get_team_invitation_template(),
                text_body="You've been invited to join a team on PsychSync."
            ),

            NotificationType.TEAM_OPTIMIZATION_COMPLETE: EmailTemplate(
                subject="Team Optimization Results Ready",
                html_body=self._get_optimization_complete_template(),
                text_body="Your team optimization analysis is complete."
            ),

            NotificationType.ASSESSMENT_COMPLETED: EmailTemplate(
                subject="Assessment Results Available",
                html_body=self._get_assessment_complete_template(),
                text_body="Your assessment results are now available."
            ),

            NotificationType.ASSESSMENT_REMINDER: EmailTemplate(
                subject="Assessment Reminder",
                html_body=self._get_assessment_reminder_template(),
                text_body="You have an assessment waiting to be completed."
            ),

            NotificationType.PASSWORD_RESET: EmailTemplate(
                subject="Reset Your Password",
                html_body=self._get_password_reset_template(),
                text_body="Use this link to reset your password."
            ),

            NotificationType.EMAIL_VERIFICATION: EmailTemplate(
                subject="Verify Your Email Address",
                html_body=self._get_email_verification_template(),
                text_body="Please verify your email address to activate your account."
            ),

            NotificationType.TEAM_RECOMMENDATION: EmailTemplate(
                subject="New Team Recommendations",
                html_body=self._get_team_recommendation_template(),
                text_body="We have new team recommendations for you."
            ),

            NotificationType.DEADLINE_REMINDER: EmailTemplate(
                subject="Deadline Reminder",
                html_body=self._get_deadline_reminder_template(),
                text_body="You have an upcoming deadline."
            )
        }

    async def send_notification(self, notification: Notification) -> bool:
        """
        Send notification through specified channels

        Args:
            notification: Notification object with all details

        Returns:
            Success status
        """
        try:
            logger.info(f"Sending {notification.type} notification to user {notification.user_id}")

            # Add to queue for processing
            notification.id = self._generate_notification_id()
            self.notification_queue.append(notification)

            # Process each channel
            success = True
            for channel in notification.channels:
                try:
                    if channel == NotificationChannel.IN_APP:
                        await self._send_in_app_notification(notification)
                    elif channel == NotificationChannel.EMAIL:
                        await self._send_email_notification(notification)
                    elif channel == NotificationChannel.PUSH:
                        await self._send_push_notification(notification)
                    elif channel == NotificationChannel.WEBHOOK:
                        await self._send_webhook_notification(notification)
                except Exception as e:
                    logger.error(f"Failed to send {channel} notification: {str(e)}")
                    success = False

            logger.info(f"Notification {notification.id} processed with success: {success}")
            return success

        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}", exc_info=True)
            return False

    async def send_bulk_notifications(self, notifications: List[Notification]) -> Dict[str, int]:
        """
        Send multiple notifications in batch

        Args:
            notifications: List of notifications to send

        Returns:
            Dictionary with success/failure counts
        """
        results = {"success": 0, "failed": 0}

        # Process in batches to avoid overwhelming systems
        batch_size = 50
        for i in range(0, len(notifications), batch_size):
            batch = notifications[i:i + batch_size]

            # Send all notifications in batch concurrently
            tasks = [self.send_notification(notification) for notification in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count results
            for result in batch_results:
                if result is True:
                    results["success"] += 1
                else:
                    results["failed"] += 1

        logger.info(f"Bulk notification complete: {results['success']} success, {results['failed']} failed")
        return results

    def notify_user_email(self, user_email: str, subject: str, body: str,
                         html_body: str = None, from_email: str = None) -> bool:
        """
        Simple email notification wrapper

        Args:
            user_email: Target email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            from_email: From address (optional)

        Returns:
            Success status
        """
        try:
            return send_email_async(
                to=user_email,
                subject=subject,
                body=body,
                html_body=html_body,
                from_email=from_email
            )
        except Exception as e:
            logger.error(f"Failed to send email to {user_email}: {str(e)}")
            return False

    def notify_event(self, user_id: int, event: str, payload: Dict[str, Any]) -> bool:
        """
        Simple in-app event notification

        Args:
            user_id: Target user ID
            event: Event name/type
            payload: Event data

        Returns:
            Success status
        """
        try:
            # Create notification from event
            notification = Notification(
                user_id=user_id,
                type=NotificationType.SYSTEM_ANNOUNCEMENT,
                title=f"Event: {event}",
                message=str(payload),
                data=payload,
                channels=[NotificationChannel.IN_APP]
            )

            # In production, this would be stored in database or cache
            logger.info(f"Event notification for user {user_id}: {event}")
            return True

        except Exception as e:
            logger.error(f"Failed to create event notification: {str(e)}")
            return False

    async def create_team_invitation_notification(self, user_id: int, team_name: str,
                                                inviter_name: str, inviter_email: str,
                                                user_email: str = None) -> Notification:
        """Create team invitation notification"""

        notification = Notification(
            user_id=user_id,
            type=NotificationType.TEAM_INVITATION,
            title=f"Team Invitation: {team_name}",
            message=f"{inviter_name} has invited you to join the '{team_name}' team.",
            data={
                "team_name": team_name,
                "inviter_name": inviter_name,
                "inviter_email": inviter_email
            },
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            priority="high"
        )

        if user_email:
            template = self.email_templates[NotificationType.TEAM_INVITATION]
            html_body = template.html_body.format(
                team_name=team_name,
                inviter_name=inviter_name,
                inviter_email=inviter_email
            )

            await self.send_email_notification(notification, user_email, html_body)

        return notification

    async def create_optimization_complete_notification(self, user_id: int, team_name: str,
                                                       optimization_score: float,
                                                       user_email: str = None) -> Notification:
        """Create optimization complete notification"""

        score_text = "Excellent" if optimization_score > 0.8 else "Good" if optimization_score > 0.6 else "Fair"

        notification = Notification(
            user_id=user_id,
            type=NotificationType.TEAM_OPTIMIZATION_COMPLETE,
            title=f"Team Optimization Complete",
            message=f"Your '{team_name}' team optimization is complete. Score: {score_text} ({optimization_score:.1%})",
            data={
                "team_name": team_name,
                "optimization_score": optimization_score,
                "score_text": score_text
            },
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            priority="normal"
        )

        if user_email:
            template = self.email_templates[NotificationType.TEAM_OPTIMIZATION_COMPLETE]
            html_body = template.html_body.format(
                team_name=team_name,
                score_text=score_text,
                optimization_score=f"{optimization_score:.1%}"
            )

            await self.send_email_notification(notification, user_email, html_body)

        return notification

    async def _send_in_app_notification(self, notification: Notification) -> bool:
        """Send in-app notification (stored in database/cache)"""
        # In production, this would store in database or Redis
        logger.info(f"In-app notification: {notification.title} for user {notification.user_id}")
        return True

    async def _send_email_notification(self, notification: Notification,
                                     user_email: str = None, custom_html: str = None) -> bool:
        """Send email notification"""

        try:
            template = self.email_templates.get(notification.type)

            if custom_html:
                html_body = custom_html
            elif template:
                html_body = template.html_body.format(**notification.data)
            else:
                # Default HTML email
                html_body = f"""
                <html>
                    <body>
                        <h2>{notification.title}</h2>
                        <p>{notification.message}</p>
                        <hr>
                        <p><small>Best regards,<br>The PsychSync Team</small></p>
                    </body>
                </html>
                """

            return send_email_async(
                to=user_email or f"user_{notification.user_id}@example.com",  # Would get real email
                subject=notification.title,
                body=notification.message,
                html_body=html_body
            )

        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            return False

    async def _send_push_notification(self, notification: Notification) -> bool:
        """Send push notification (future implementation)"""
        # Future: Implement mobile push notifications
        logger.info(f"Push notification not yet implemented: {notification.title}")
        return True

    async def _send_webhook_notification(self, notification: Notification) -> bool:
        """Send webhook notification (future implementation)"""
        # Future: Implement webhook notifications for external integrations
        logger.info(f"Webhook notification not yet implemented: {notification.title}")
        return True

    def _generate_notification_id(self) -> str:
        """Generate unique notification ID"""
        import uuid
        return str(uuid.uuid4())

    def _get_team_invitation_template(self) -> str:
        """HTML template for team invitation emails"""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #4F46E5;">You've Been Invited to Join a Team! 🎉</h2>
                <p>Hi there!</p>
                <p><strong>{inviter_name}</strong> has invited you to join the <strong>"{team_name}"</strong> team on PsychSync.</p>

                <div style="background-color: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Why PsychSync?</h3>
                    <ul>
                        <li>AI-powered team optimization</li>
                        <li>Personality-based matching</li>
                        <li>Skill gap analysis</li>
                        <li>Collaboration insights</li>
                    </ul>
                </div>

                <p>Click the button below to view your invitation and get started:</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background-color: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        View Invitation
                    </a>
                </div>

                <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 30px 0;">
                <p style="color: #6B7280; font-size: 14px;">
                    This invitation was sent by {inviter_name} ({inviter_email}).<br>
                    If you didn't expect this invitation, you can safely ignore this email.
                </p>
            </body>
        </html>
        """

    def _get_optimization_complete_template(self) -> str:
        """HTML template for optimization complete emails"""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #10B981;">Team Optimization Complete! ✅</h2>
                <p>Great news!</p>
                <p>Your team optimization analysis for <strong>"{team_name}"</strong> is complete.</p>

                <div style="background-color: #ECFDF5; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                    <h3 style="color: #047857; margin: 0;">Overall Score: {score_text}</h3>
                    <div style="font-size: 36px; font-weight: bold; color: #10B981; margin: 10px 0;">
                        {optimization_score}
                    </div>
                </div>

                <p>Your optimization includes:</p>
                <ul>
                    <li>Team compatibility analysis</li>
                    <li>Skill coverage assessment</li>
                    <li>Diversity metrics</li>
                    <li>Personalized recommendations</li>
                </ul>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background-color: #10B981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        View Results
                    </a>
                </div>

                <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 30px 0;">
                <p style="color: #6B7280; font-size: 14px;">
                    This is an automated notification from PsychSync.
                </p>
            </body>
        </html>
        """

    def _get_assessment_complete_template(self) -> str:
        """HTML template for assessment complete emails"""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #8B5CF6;">Assessment Results Ready! 📊</h2>
                <p>Your assessment has been processed and your results are now available.</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background-color: #8B5CF6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        View Results
                    </a>
                </div>
            </body>
        </html>
        """

    def _get_assessment_reminder_template(self) -> str:
        """HTML template for assessment reminder emails"""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #F59E0B;">Assessment Reminder ⏰</h2>
                <p>You have an assessment waiting to be completed.</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background-color: #F59E0B; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Complete Assessment
                    </a>
                </div>
            </body>
        </html>
        """

    def _get_password_reset_template(self) -> str:
        """HTML template for password reset emails"""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #EF4444;">Reset Your Password 🔒</h2>
                <p>Use the link below to reset your password. This link will expire in 24 hours.</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background-color: #EF4444; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Reset Password
                    </a>
                </div>

                <p style="color: #6B7280; font-size: 14px;">
                    If you didn't request a password reset, you can safely ignore this email.
                </p>
            </body>
        </html>
        """

    def _get_email_verification_template(self) -> str:
        """HTML template for email verification emails"""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #3B82F6;">Verify Your Email Address ✉️</h2>
                <p>Please verify your email address to activate your PsychSync account.</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background-color: #3B82F6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Verify Email
                    </a>
                </div>
            </body>
        </html>
        """

    def _get_team_recommendation_template(self) -> str:
        """HTML template for team recommendation emails"""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #06B6D4;">New Team Recommendations 🎯</h2>
                <p>We've found some great team matches for you based on your profile.</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background-color: #06B6D4; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        View Recommendations
                    </a>
                </div>
            </body>
        </html>
        """

    def _get_deadline_reminder_template(self) -> str:
        """HTML template for deadline reminder emails"""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #DC2626;">Deadline Reminder ⚠️</h2>
                <p>You have an upcoming deadline. Don't forget to complete your task!</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background-color: #DC2626; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        View Task
                    </a>
                </div>
            </body>
        </html>
        """

# Singleton instance
notification_service = NotificationService()

# Convenience functions
def notify_user_email(user_email: str, subject: str, body: str, html_body: str = None, from_email: str = None) -> bool:
    """Simple email notification wrapper"""
    return notification_service.notify_user_email(user_email, subject, body, html_body, from_email)

def notify_event(user_id: int, event: str, payload: Dict[str, Any]) -> bool:
    """Simple in-app event notification"""
    return notification_service.notify_event(user_id, event, payload)

async def send_notification(notification: Notification) -> bool:
    """Send notification through channels"""
    return await notification_service.send_notification(notification)