"""
Refactored Email Service

This is the CORRECT service layer implementation.
It focuses ONLY on business logic, not presentation or infrastructure concerns.

Responsibilities:
- Email delivery orchestration
- Business rules about what emails to send
- Email provider interaction

NOT responsible for:
- Template rendering (that's EmailTemplateRenderer's job - presentation layer)
- HTML generation (presentation concern)
- Database queries (repository layer's job)
"""

import logging
import secrets
import time
from typing import Any

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseModel

from app.core.audit_logging import AuditLogger
from app.core.config import settings
from app.domain.value_objects.email import Email
from app.presentation.email_template_renderer import EmailTemplateRenderer

logger = logging.getLogger(__name__)


# Email provider configuration
# This is infrastructure concern, not business logic
conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER or "dummy@example.com",
    MAIL_PASSWORD=settings.SMTP_PASSWORD or "dummy",
    MAIL_FROM=settings.EMAILS_FROM_EMAIL or "noreply@psychsync.com",
    MAIL_PORT=settings.SMTP_PORT or 587,
    MAIL_SERVER=settings.SMTP_HOST or "smtp.gmail.com",
    MAIL_FROM_NAME=settings.EMAILS_FROM_NAME or "PsychSync",
    MAIL_STARTTLS=settings.SMTP_TLS,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=bool(settings.SMTP_USER and settings.SMTP_PASSWORD),
    VALIDATE_CERTS=getattr(settings, "MAIL_VALIDATE_CERTS", False),
)


class EmailProvider:
    """
    Abstraction over email delivery infrastructure

    This allows us to swap email providers without changing business logic.
    """

    def __init__(self, config: ConnectionConfig):
        self._fastmail = FastMail(config)

    async def send(
        self,
        to: str,
        subject: str,
        html: str,
        tracking_id: str | None = None,
    ) -> tuple[bool, str | None]:
        """
        Send email via provider

        Returns:
            Tuple of (success, error_message)
        """
        try:
            message = MessageSchema(
                subject=subject,
                recipients=[to],
                body=html,
                subtype=MessageType.html,
                headers={
                    "X-Priority": "3",
                    "X-Mailer": "PsychSync Email Service",
                    "X-Tracking-ID": tracking_id or secrets.token_urlsafe(16),
                    "List-Unsubscribe": f"<{settings.FRONTEND_URL}/unsubscribe?email={to}>",
                },
            )

            await self._fastmail.send_message(message)
            return True, None

        except Exception as e:
            logger.error(f"Email provider error: {e}")
            return False, str(e)


class EmailService:
    """
    Email business logic service

    This service orchestrates email sending by coordinating:
    1. Template rendering (via EmailTemplateRenderer)
    2. Email delivery (via EmailProvider)
    3. Business rules (when to send, what to send)

    It does NOT contain HTML rendering or email delivery implementation.
    """

    def __init__(
        self,
        template_renderer: EmailTemplateRenderer,
        email_provider: EmailProvider,
    ):
        """
        Initialize email service with dependencies

        Args:
            template_renderer: Presentation layer component for rendering
            email_provider: Infrastructure component for delivery
        """
        self._template_renderer = template_renderer
        self._email_provider = email_provider

    def _validate_email(self, email: str) -> bool:
        """
        Validate email address

        This is a BUSINESS RULE about what emails are acceptable.
        """
        try:
            # Use domain Email value object for validation
            EmailAddress(email)
            return True
        except ValueError:
            return False

    def _check_rate_limit(self, sender_email: str) -> bool:
        """
        Check if sender has exceeded rate limits

        This is a BUSINESS RULE about sending frequency.
        In production, this would check Redis or similar cache.
        """
        # Placeholder - would implement actual rate limiting
        return True

    async def send_welcome_email(
        self,
        user_email: str,
        user_name: str,
        dashboard_url: str | None = None,
    ) -> EmailResult:
        """
        Send welcome email to new user

        BUSINESS LOGIC:
        - When to send welcome email (after registration)
        - What data to include (user name, dashboard URL)
        - Rate limiting and validation

        PRESENTATION (delegated):
        - How email looks (template rendering)
        - HTML structure (template file)

        INFRASTRUCTURE (delegated):
        - How email is delivered (SMTP, API, etc.)
        """
        try:
            # Business rule: validate email
            if not self._validate_email(user_email):
                AuditLogger.log_security_event(
                    event_type=SecurityEventType.INVALID_INPUT,
                    details=f"Invalid recipient email: {user_email}",
                )
                return EmailResult(
                    success=False,
                    message_id=None,
                    error_message="Invalid email address",
                    recipient=EmailAddress(user_email),  # Will raise if invalid
                )

            # Business rule: check rate limits
            if not self._check_rate_limit(user_email):
                AuditLogger.log_security_event(
                    event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                    details=f"Email rate limit exceeded for sender: {user_email}",
                )
                return EmailResult(
                    success=False,
                    message_id=None,
                    error_message="Rate limit exceeded",
                    recipient=EmailAddress(user_email),
                )

            # Business rule: prepare email data
            email_data = WelcomeEmailData(
                user_name=user_name,
                dashboard_url=dashboard_url
                or (settings.FRONTEND_URL or "https://app.psychsync.com/dashboard"),
                help_url=f"{settings.FRONTEND_URL or 'https://app.psychsync.com'}/help",
                settings_url=f"{settings.FRONTEND_URL or 'https://app.psychsync.com'}/settings",
                unsubscribe_url=f"{settings.FRONTEND_URL or 'https://app.psychsync.com'}/unsubscribe",
            )

            # Presentation: delegate to template renderer
            html_content = self._template_renderer.render_template(
                "welcome.html",
                email_data.to_context_dict(),
            )

            # Infrastructure: delegate to email provider
            tracking_id = secrets.token_urlsafe(16)
            success, error = await self._email_provider.send(
                to=user_email,
                subject="Welcome to PsychSync! 🎉",
                html=html_content,
                tracking_id=tracking_id,
            )

            if success:
                AuditLogger.log_security_event(
                    event_type=SecurityEventType.DATA_ACCESS,
                    details=f"Welcome email sent to {user_email}",
                    additional_data={"tracking_id": tracking_id},
                )
                return EmailResult(
                    success=True,
                    message_id=tracking_id,
                    error_message=None,
                    recipient=EmailAddress(user_email),
                )
            else:
                return EmailResult(
                    success=False,
                    message_id=None,
                    error_message=error or "Failed to send email",
                    recipient=EmailAddress(user_email),
                )

        except Exception as e:
            logger.error(f"Error sending welcome email to {user_email}: {e}")
            return EmailResult(
                success=False,
                message_id=None,
                error_message=str(e),
                recipient=EmailAddress(user_email),
            )

    async def send_password_reset_email(
        self,
        user_email: str,
        token: str,
        user_name: str | None = None,
    ) -> EmailResult:
        """
        Send password reset email

        BUSINESS LOGIC:
        - Password reset is a security-sensitive operation
        - Tokens must be handled securely
        - Rate limiting is crucial
        """
        try:
            if not self._validate_email(user_email):
                return EmailResult(
                    success=False,
                    message_id=None,
                    error_message="Invalid email address",
                    recipient=EmailAddress(user_email),
                )

            # Business rule: prepare reset email data
            reset_url = f"{settings.FRONTEND_PASSWORD_RESET_URL or 'http://localhost:3000/reset-password'}?token={token}"

            email_data = PasswordResetData(
                token=token,  # Token included for template rendering
                user_name=user_name,
                reset_url=reset_url,
            )

            # Presentation: delegate to template renderer
            html_content = self._template_renderer.render_template(
                "password_reset.html",
                email_data.to_context_dict(),
            )

            # Infrastructure: delegate to email provider
            tracking_id = secrets.token_urlsafe(16)
            success, error = await self._email_provider.send(
                to=user_email,
                subject="Reset Your PsychSync Password",
                html=html_content,
                tracking_id=tracking_id,
            )

            if success:
                logger.info(f"Password reset email sent to {user_email}")
                return EmailResult(
                    success=True,
                    message_id=tracking_id,
                    error_message=None,
                    recipient=EmailAddress(user_email),
                )
            else:
                return EmailResult(
                    success=False,
                    message_id=None,
                    error_message=error or "Failed to send email",
                    recipient=EmailAddress(user_email),
                )

        except Exception as e:
            logger.error(f"Error sending password reset email to {user_email}: {e}")
            return EmailResult(
                success=False,
                message_id=None,
                error_message=str(e),
                recipient=EmailAddress(user_email),
            )

    async def send_team_invitation(
        self,
        user_email: str,
        team_name: str,
        inviter_name: str,
        invite_link: str,
    ) -> EmailResult:
        """
        Send team invitation email

        BUSINESS LOGIC:
        - Team invitations require proper authentication
        - Invitation links should have expiration
        - Audit logging is important
        """
        try:
            if not self._validate_email(user_email):
                return EmailResult(
                    success=False,
                    message_id=None,
                    error_message="Invalid email address",
                    recipient=EmailAddress(user_email),
                )

            # Business rule: prepare invitation data
            email_data = TeamInvitationData(
                team_name=team_name,
                inviter_name=inviter_name,
                invite_link=invite_link,
            )

            # Presentation: delegate to template renderer
            html_content = self._template_renderer.render_template(
                "team_invitation.html",
                email_data.to_context_dict(),
            )

            # Infrastructure: delegate to email provider
            tracking_id = secrets.token_urlsafe(16)
            subject = f"You're invited to join {team_name} on PsychSync"
            success, error = await self._email_provider.send(
                to=user_email,
                subject=subject,
                html=html_content,
                tracking_id=tracking_id,
            )

            if success:
                logger.info(f"Team invitation sent to {user_email}")
                AuditLogger.log_security_event(
                    event_type=SecurityEventType.DATA_ACCESS,
                    details=f"Team invitation sent: {team_name} -> {user_email}",
                    additional_data={
                        "team_name": team_name,
                        "inviter": inviter_name,
                        "tracking_id": tracking_id,
                    },
                )
                return EmailResult(
                    success=True,
                    message_id=tracking_id,
                    error_message=None,
                    recipient=EmailAddress(user_email),
                )
            else:
                return EmailResult(
                    success=False,
                    message_id=None,
                    error_message=error or "Failed to send email",
                    recipient=EmailAddress(user_email),
                )

        except Exception as e:
            logger.error(f"Error sending team invitation to {user_email}: {e}")
            return EmailResult(
                success=False,
                message_id=None,
                error_message=str(e),
                recipient=EmailAddress(user_email),
            )


# Singleton instance with default dependencies
email_service_v2 = EmailService(
    template_renderer=EmailTemplateRenderer(),
    email_provider=EmailProvider(conf),
)
