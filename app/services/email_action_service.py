"""
Email Action Service
Handles sending replies and forwards via SMTP

ENHANCED: Now includes retry logic for SMTP operations
"""

import asyncio
import os
import random
import smtplib
import ssl
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings

# Retry configuration
SMTP_MAX_RETRIES = 3
SMTP_BASE_DELAY = 1.0
SMTP_MAX_DELAY = 30.0


def _calculate_backoff(attempt: int) -> float:
    """Calculate exponential backoff with jitter."""
    delay = SMTP_BASE_DELAY * (2**attempt)
    delay = min(delay, SMTP_MAX_DELAY)
    jitter = delay * 0.25 * (random.random() * 2 - 1)
    return max(0, delay + jitter)


class EmailActionService:
    """Service for sending email actions (reply, forward, compose) with retry logic"""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str,
        is_html: bool = False,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Send an email via SMTP with retry logic

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            from_email: Sender email address
            is_html: Whether body is HTML
            in_reply_to: Message-ID of email being replied to
            references: References header for threading
            attachments: List of attachment files

        Returns:
            Dict with success status and message
        """
        # Create message (outside retry loop as this is just in-memory)
        msg = MIMEMultipart("mixed")
        msg["From"] = from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

        # Add threading headers if replying
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
        if references:
            msg["References"] = references

        # Create alternative part for plain text and HTML
        alt_msg = MIMEMultipart("alternative")
        msg.attach(alt_msg)

        # Attach body
        if is_html:
            # Attach both plain text and HTML
            plain_text = self._html_to_text(body)
            alt_msg.attach(MIMEText(plain_text, "plain", "utf-8"))
            alt_msg.attach(MIMEText(body, "html", "utf-8"))
        else:
            alt_msg.attach(MIMEText(body, "plain", "utf-8"))

        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                self._add_attachment(msg, attachment)

        # Send with retry logic
        last_error = None
        for attempt in range(SMTP_MAX_RETRIES):
            try:
                # Connect to SMTP server and send
                if self.smtp_port == 465:
                    # SSL connection
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(
                        self.smtp_server, self.smtp_port, context=context
                    ) as server:
                        if self.smtp_username and self.smtp_password:
                            server.login(self.smtp_username, self.smtp_password)
                        server.send_message(msg)
                else:
                    # TLS connection
                    context = ssl.create_default_context()
                    with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                        server.starttls(context=context)
                        if self.smtp_username and self.smtp_password:
                            server.login(self.smtp_username, self.smtp_password)
                        server.send_message(msg)

                return {
                    "success": True,
                    "message": "Email sent successfully",
                    "timestamp": datetime.utcnow().isoformat(),
                    "attempts": attempt + 1,
                }

            except (smtplib.SMTPException, ssl.SSLError, OSError) as e:
                last_error = e
                error_str = str(e).lower()

                # Check if error is retryable
                retryable_errors = [
                    "timeout",
                    "connection",
                    "network",
                    "temporary",
                    "421",
                    "450",
                    "451",
                    "452",
                    "454",
                ]
                is_retryable = any(err in error_str for err in retryable_errors)

                if is_retryable and attempt < SMTP_MAX_RETRIES - 1:
                    backoff = _calculate_backoff(attempt)
                    await asyncio.sleep(backoff)
                    continue
                else:
                    break

            except Exception as e:
                last_error = e
                break

        return {
            "success": False,
            "error": str(last_error),
            "message": f"Failed to send email after {SMTP_MAX_RETRIES} attempts: {str(last_error)}",
            "attempts": SMTP_MAX_RETRIES,
        }

    async def reply_to_email(
        self,
        original_email: Dict[str, Any],
        reply_body: str,
        from_email: str,
        reply_all: bool = False,
    ) -> Dict[str, Any]:
        """
        Reply to an email

        Args:
            original_email: Original email details
            reply_body: Reply message body
            from_email: Sender email address
            reply_all: Whether to reply to all recipients

        Returns:
            Dict with success status
        """
        # Extract original email details
        to = original_email.get("from_email", "")
        subject = original_email.get("subject", "")
        message_id = original_email.get("message_id", "")
        references = original_email.get("references", "")

        # Add Re: to subject if not already present
        if not subject.startswith("Re:"):
            subject = f"Re: {subject}"

        # Build references for threading
        if references:
            references = f"{references} {message_id}"
        else:
            references = message_id

        recipients = [to]
        if reply_all:
            # Add CC recipients
            cc_list = original_email.get("cc", [])
            if cc_list:
                recipients.extend(cc_list)

        # Send to first recipient (SMTP handles multiple recipients)
        return await self.send_email(
            to=recipients[0],
            subject=subject,
            body=reply_body,
            from_email=from_email,
            in_reply_to=message_id,
            references=references,
        )

    async def forward_email(
        self,
        original_email: Dict[str, Any],
        forward_to: str,
        forward_message: str,
        from_email: str,
    ) -> Dict[str, Any]:
        """
        Forward an email

        Args:
            original_email: Original email details
            forward_to: Recipient to forward to
            forward_message: Additional message from sender
            from_email: Sender email address

        Returns:
            Dict with success status
        """
        # Extract original email details
        original_subject = original_email.get("subject", "")
        original_from = original_email.get("from_email", "")
        original_body = original_email.get("body", "")
        original_date = original_email.get("date", "")

        # Add Fwd: to subject
        subject = f"Fwd: {original_subject}"

        # Build forwarded message body
        body = f"""{forward_message}

---------- Forwarded message ----------
From: {original_from}
Date: {original_date}
Subject: {original_subject}

{original_body}
"""

        return await self.send_email(
            to=forward_to, subject=subject, body=body, from_email=from_email
        )

    async def compose_new_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compose and send a new email

        Args:
            to: Primary recipient
            subject: Email subject
            body: Email body
            from_email: Sender email
            cc: CC recipients
            bcc: BCC recipients

        Returns:
            Dict with success status
        """
        # TODO: Handle CC and BCC (currently not supported by send_email)
        return await self.send_email(
            to=to, subject=subject, body=body, from_email=from_email
        )

    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message"""
        part = MIMEBase(
            attachment.get("maintype", "application"),
            attachment.get("subtype", "octet-stream"),
        )

        part.set_payload(attachment["content"])
        encoders.encode_base64(part)

        # Add header
        filename = attachment.get("filename", "attachment")
        part.add_header("Content-Disposition", f"attachment; filename= {filename}")

        msg.attach(part)

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (simple version)"""
        import re

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html)
        # Convert HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")
        return text.strip()


# Singleton instance
email_action_service = EmailActionService()
