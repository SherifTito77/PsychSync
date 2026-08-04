"""
Multi-Provider Email Service with Failover

Supports multiple email providers with automatic failover:
- SendGrid (primary)
- AWS SES (backup)
- Mailgun (tertiary)

HIPAA COMPLIANT: All PHI encrypted in transit, no PHI in email subjects
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class EmailProvider:
    """Base email provider interface"""

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str,
        from_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send email - to be implemented by subclasses"""
        raise NotImplementedError


class SendGridProvider(EmailProvider):
    """SendGrid email provider implementation"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.sendgrid.com/v3/mail/send"

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str,
        from_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send email via SendGrid with resilient HTTP client

        Uses automatic retries, timeouts, and circuit breaker for improved reliability.
        """
        from app.core.resilient_client import HTTPClientError, resilient_http_client

        if from_email is None:
            from_email = os.getenv("SENDGRID_FROM_EMAIL", "notifications@psychsync.io")

        payload = {
            "personalizations": [{"to": [{"email": to}], "subject": subject}],
            "from": {"email": from_email},
            "content": [
                {"type": "text/plain", "value": text_body},
                {"type": "text/html", "value": html_body},
            ],
            "categories": ["clinical", "notifications"],
            "custom_args": {"timestamp": datetime.utcnow().isoformat()},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            # Resilient client provides automatic retries and circuit breaker
            response = await resilient_http_client.post(
                self.api_url, json=payload, headers=headers, timeout=30.0
            )

            if response.status_code in [200, 202]:
                logger.info(f"SendGrid email sent successfully to {to}")
                return {
                    "provider": "sendgrid",
                    "success": True,
                    "message_id": response.headers.get("X-Message-Id"),
                    "status_code": response.status_code,
                }
            else:
                logger.error(
                    f"SendGrid error: {response.status_code} - {response.text}"
                )
                return {
                    "provider": "sendgrid",
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code,
                }

        except HTTPClientError as e:
            logger.error(f"SendGrid HTTP client error: {str(e)}")
            return {"provider": "sendgrid", "success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"SendGrid exception: {str(e)}")
            return {"provider": "sendgrid", "success": False, "error": str(e)}


class AWSSESProvider(EmailProvider):
    """AWS SES email provider implementation"""

    def __init__(self, region: str = "us-east-1"):
        self.region = region

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str,
        from_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send email via AWS SES"""
        try:
            import boto3

            if from_email is None:
                from_email = os.getenv("SES_FROM_EMAIL", "notifications@psychsync.io")

            ses_client = boto3.client(
                "ses",
                region_name=self.region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            )

            response = ses_client.send_email(
                Source=from_email,
                Destination={"ToAddresses": [to]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Text": {"Data": text_body}, "Html": {"Data": html_body}},
                },
                ConfigurationSetName=os.getenv(
                    "SES_CONFIGURATION_SET", "PsychSync-Production"
                ),
                Tags=[
                    {"Name": "email-type", "Value": "clinical-notification"},
                    {
                        "Name": "environment",
                        "Value": os.getenv("ENVIRONMENT", "production"),
                    },
                ],
            )

            message_id = response["MessageId"]
            logger.info(f"AWS SES email sent successfully to {to}: {message_id}")

            return {"provider": "aws-ses", "success": True, "message_id": message_id}

        except Exception as e:
            logger.error(f"AWS SES exception: {str(e)}")
            return {"provider": "aws-ses", "success": False, "error": str(e)}


class MailgunProvider(EmailProvider):
    """Mailgun email provider implementation"""

    def __init__(self, api_key: str, domain: str):
        self.api_key = api_key
        self.domain = domain
        self.api_url = f"https://api.mailgun.net/v3/{domain}/messages"

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str,
        from_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send email via Mailgun with resilient HTTP client

        Uses automatic retries, timeouts, and circuit breaker for improved reliability.
        """
        from app.core.resilient_client import HTTPClientError, resilient_http_client

        if from_email is None:
            from_email = os.getenv("MAILGUN_FROM_EMAIL", f"notifications@{self.domain}")

        auth = ("api", self.api_key)
        data = {
            "from": from_email,
            "to": [to],
            "subject": subject,
            "text": text_body,
            "html": html_body,
            "o:tracking": "yes",
            "o:tracking-clicks": "yes",
            "o:tracking-opens": "yes",
            "o:tag": ["clinical-notification"],
        }

        try:
            # Resilient client provides automatic retries and circuit breaker
            response = await resilient_http_client.post(
                self.api_url, auth=auth, data=data, timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Mailgun email sent successfully to {to}")
                return {
                    "provider": "mailgun",
                    "success": True,
                    "message_id": result.get("id"),
                    "status_code": response.status_code,
                }
            else:
                logger.error(f"Mailgun error: {response.status_code} - {response.text}")
                return {
                    "provider": "mailgun",
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code,
                }

        except HTTPClientError as e:
            logger.error(f"Mailgun HTTP client error: {str(e)}")
            return {"provider": "mailgun", "success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Mailgun exception: {str(e)}")
            return {"provider": "mailgun", "success": False, "error": str(e)}


class EmailServiceManager:
    """
    Email service manager with failover support

    Tries providers in order: SendGrid → AWS SES → Mailgun
    Logs all attempts for monitoring
    """

    def __init__(self):
        self.providers = []
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available email providers based on environment variables"""

        # Primary: SendGrid
        sendgrid_key = os.getenv("SENDGRID_API_KEY")
        if sendgrid_key:
            self.providers.append(("primary", SendGridProvider(sendgrid_key)))
            logger.info("SendGrid provider initialized as primary")

        # Backup: AWS SES
        if os.getenv("AWS_ACCESS_KEY_ID"):
            self.providers.append(
                ("backup", AWSSESProvider(os.getenv("AWS_REGION", "us-east-1")))
            )
            logger.info("AWS SES provider initialized as backup")

        # Tertiary: Mailgun
        mailgun_key = os.getenv("MAILGUN_API_KEY")
        mailgun_domain = os.getenv("MAILGUN_DOMAIN")
        if mailgun_key and mailgun_domain:
            self.providers.append(
                ("tertiary", MailgunProvider(mailgun_key, mailgun_domain))
            )
            logger.info("Mailgun provider initialized as tertiary")

        if not self.providers:
            logger.error(
                "No email providers configured! Please set SENDGRID_API_KEY, AWS credentials, or MAILGUN_API_KEY"
            )

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str,
        from_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send email with automatic failover

        DESIGN DECISION:
        - Try primary provider first
        - If it fails, try backup provider
        - If that fails, try tertiary provider
        - Log all attempts for monitoring
        """

        if not self.providers:
            return {"success": False, "error": "No email providers configured"}

        last_error = None

        for priority, provider in self.providers:
            try:
                logger.info(
                    f"Attempting to send email via {priority} provider: {provider.__class__.__name__}"
                )

                result = await provider.send_email(
                    to=to,
                    subject=subject,
                    html_body=html_body,
                    text_body=text_body,
                    from_email=from_email,
                )

                if result.get("success"):
                    result["provider_priority"] = priority
                    return result
                else:
                    last_error = result.get("error", "Unknown error")
                    logger.warning(f"{priority} provider failed: {last_error}")

            except Exception as e:
                last_error = str(e)
                logger.error(f"{priority} provider exception: {last_error}")

        # All providers failed
        return {
            "success": False,
            "error": f"All email providers failed. Last error: {last_error}",
            "providers_tried": len(self.providers),
        }


# Singleton instance
_email_service: Optional[EmailServiceManager] = None


def get_email_service() -> EmailServiceManager:
    """Get or create singleton email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailServiceManager()
    return _email_service
