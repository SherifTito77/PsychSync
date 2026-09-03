"""
Email wrapper functions for backward compatibility.

Provides standalone function wrappers around the EmailService class
for code that imports from app.core.email.
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.email_service_refactored_v2 import EmailService

logger = logging.getLogger(__name__)

# Global email service instance
_email_service: Optional[EmailService] = None


def _get_email_service() -> EmailService:
    """Get or create the email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


async def send_email(
    email: str,
    subject: str,
    body: str,
    html: bool = True,
    from_email: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    """
    Send an email using the EmailService.

    Args:
        email: Recipient email address
        subject: Email subject
        body: Email body content
        html: Whether body is HTML (True) or plain text (False)
        from_email: Sender email (optional)
        cc: CC recipients (optional)
        bcc: BCC recipients (optional)
        attachments: List of attachment dictionaries (optional)

    Returns:
        bool: True if email was sent successfully
    """
    try:
        service = _get_email_service()
        await service.send_email(
            to_emails=[email],
            subject=subject,
            body=body,
            html=html,
            from_email=from_email,
            cc=cc or [],
            bcc=bcc or [],
            attachments=attachments or [],
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


async def send_email_async(
    email: str,
    subject: str,
    body: str,
    html: bool = True,
    from_email: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
) -> bool:
    """
    Alias for send_email for backward compatibility.
    """
    return await send_email(
        email=email,
        subject=subject,
        body=body,
        html=html,
        from_email=from_email,
        cc=cc,
        bcc=bcc,
    )


def validate_email(email: str) -> bool:
    """
    Validate an email address.

    Args:
        email: Email address to validate

    Returns:
        bool: True if email is valid
    """
    service = _get_email_service()
    return service._validate_email_address(email)


async def send_batch_emails(
    recipients: List[str],
    subject: str,
    body: str,
    html: bool = True,
) -> Dict[str, Any]:
    """
    Send batch emails to multiple recipients.

    Args:
        recipients: List of recipient email addresses
        subject: Email subject
        body: Email body content
        html: Whether body is HTML

    Returns:
        Dict with success count and failed recipients
    """
    results = {"success": 0, "failed": [], "total": len(recipients)}

    for recipient in recipients:
        try:
            success = await send_email(
                email=recipient,
                subject=subject,
                body=body,
                html=html,
            )
            if success:
                results["success"] += 1
            else:
                results["failed"].append(recipient)
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            results["failed"].append(recipient)

    return results


async def queue_email(
    email: str,
    subject: str,
    body: str,
    html: bool = True,
    delay: int = 0,
) -> bool:
    """
    Queue an email for sending (currently sends immediately).

    Args:
        email: Recipient email
        subject: Email subject
        body: Email body
        html: Whether body is HTML
        delay: Delay in seconds (not implemented, sends immediately)

    Returns:
        bool: True if queued/sent successfully
    """
    # For now, just send immediately. A proper queue would use celery or similar.
    return await send_email(
        email=email,
        subject=subject,
        body=body,
        html=html,
    )


# Additional wrapper functions for common email operations
async def send_verification_email(email: str, token: str, name: str = "") -> bool:
    """Send email verification email."""
    service = _get_email_service()
    try:
        await service.send_verification_email(email=email, token=token, name=name)
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        return False


async def send_password_reset_email(email: str, token: str, name: str = "") -> bool:
    """Send password reset email."""
    service = _get_email_service()
    try:
        await service.send_password_reset_email(email=email, token=token, name=name)
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        return False


async def send_welcome_email(email: str, name: str = "") -> bool:
    """Send welcome email."""
    service = _get_email_service()
    try:
        await service.send_welcome_email_legacy(email=email, name=name)
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        return False


# Stub class for testing
class EmailServiceStub:
    """Stub email service for testing."""

    def __init__(self):
        self.sent_emails = []

    async def send_email(
        self,
        to_emails: list[str],
        subject: str,
        body: str,
        html: bool = True,
        from_email: Optional[str] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        attachments: Optional[list[dict]] = None,
    ) -> bool:
        """Stub send_email that logs instead of sending."""
        self.sent_emails.append(
            {
                "to": to_emails,
                "subject": subject,
                "body": body,
                "html": html,
                "from_email": from_email,
                "cc": cc,
                "bcc": bcc,
                "attachments": attachments,
            }
        )
        logger.info(f"[STUB] Email sent to {to_emails}: {subject}")
        return True
