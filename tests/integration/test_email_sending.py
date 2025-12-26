"""
Email Sending Integration Tests

This module tests email sending functionality including:
- SMTP and email service integration
- Email templates and personalization
- Email delivery tracking
- Bulk email operations
- Email security and compliance
- Error handling and retry logic
- Email analytics and reporting

Security focus: Email injection prevention, secure template rendering,
and proper handling of sensitive email content.
"""

import pytest
import asyncio
import json
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import io
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.core.config import get_settings
from app.services.email_service import EmailService
from app.services.email_connector_service import EmailConnectorService
from app.db.models.user import User
from app.db.models.organization import Organization
from app.schemas.email import (
    EmailMessage,
    EmailTemplate,
    EmailCampaign,
    EmailAnalytics,
    BulkEmailRequest
)

settings = get_settings()


@pytest.fixture
async def email_service():
    """Create email service instance for testing."""
    return EmailService()


@pytest.fixture
async def email_connector():
    """Create email connector service instance for testing."""
    return EmailConnectorService()


@pytest.fixture
async def sample_email_data():
    """Sample email data for testing."""
    return {
        "to": ["test@example.com", "user2@example.com"],
        "cc": ["manager@example.com"],
        "bcc": ["audit@example.com"],
        "subject": "Test Email Message",
        "html_content": "<h1>Hello {{name}}</h1><p>This is a test email.</p>",
        "text_content": "Hello {{name}}\\nThis is a test email.",
        "template_data": {"name": "Test User"},
        "attachments": [],
        "priority": "normal",
        "track_opens": True,
        "track_clicks": True,
    }


@pytest.fixture
async def email_template_data():
    """Sample email template data for testing."""
    return {
        "name": "Welcome Email",
        "category": "onboarding",
        "subject": "Welcome to {{company_name}}!",
        "html_template": """
        <html>
            <body>
                <h1>Welcome {{user_name}}!</h1>
                <p>Thank you for joining {{company_name}}.</p>
                <p>Your account is now active.</p>
                <a href="{{activation_link}}">Activate Account</a>
            </body>
        </html>
        """,
        "text_template": """
        Welcome {{user_name}}!

        Thank you for joining {{company_name}}.
        Your account is now active.

        Activate Account: {{activation_link}}
        """,
        "variables": ["user_name", "company_name", "activation_link"],
        "is_active": True,
    }


@pytest.fixture
async def bulk_email_data():
    """Sample bulk email campaign data."""
    return {
        "campaign_name": "Monthly Newsletter",
        "template_id": "template_123",
        "recipients": [
            {"email": "user1@example.com", "name": "User One", "company": "Company A"},
            {"email": "user2@example.com", "name": "User Two", "company": "Company B"},
            {"email": "user3@example.com", "name": "User Three", "company": "Company C"},
        ],
        "schedule_time": datetime.now() + timedelta(hours=1),
        "batch_size": 100,
        "track_opens": True,
        "track_clicks": True,
    }


@pytest.fixture
async def email_attachment():
    """Sample email attachment for testing."""
    content = "This is a test attachment content."
    return {
        "filename": "test_document.txt",
        "content": content.encode('utf-8'),
        "content_type": "text/plain",
    }


class TestBasicEmailSending:
    """Test basic email sending functionality."""

    @pytest.mark.integration
    async def test_send_single_email_success(
        self, client: AsyncClient, authenticated_user, sample_email_data, email_service
    ):
        """Test successful single email sending."""
        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = {
                "message_id": "msg_test123456789",
                "status": "sent",
                "provider": "smtp",
                "sent_at": datetime.now().isoformat(),
                "recipients": ["test@example.com"],
            }

            response = await client.post(
                "/api/v1/emails/send",
                json=sample_email_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "sent"
            assert "message_id" in data
            assert data["provider"] == "smtp"

    @pytest.mark.integration
    async def test_send_email_with_template(
        self, client: AsyncClient, authenticated_user, email_template_data, email_service
    ):
        """Test sending email with template rendering."""
        template_request = {
            "template_id": "template_123",
            "to": ["user@example.com"],
            "template_data": {
                "user_name": "John Doe",
                "company_name": "PsychSync",
                "activation_link": "https://example.com/activate/abc123",
            },
        }

        with patch.object(email_service, 'send_template_email') as mock_send:
            mock_send.return_value = {
                "message_id": "msg_template123",
                "status": "sent",
                "rendered_subject": "Welcome to PsychSync!",
                "rendered_content": "Welcome John Doe!",
            }

            response = await client.post(
                "/api/v1/emails/send-template",
                json=template_request,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "sent"
            assert "Welcome to PsychSync!" in data["rendered_subject"]

    @pytest.mark.integration
    async def test_send_email_with_attachments(
        self, client: AsyncClient, authenticated_user, email_attachment, email_service
    ):
        """Test sending email with attachments."""
        email_data = {
            "to": ["recipient@example.com"],
            "subject": "Email with Attachment",
            "text_content": "Please find the attached file.",
            "attachments": [
                {
                    "filename": email_attachment["filename"],
                    "content": email_attachment["content"].decode('utf-8'),
                    "content_type": email_attachment["content_type"],
                }
            ],
        }

        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = {
                "message_id": "msg_attachment123",
                "status": "sent",
                "attachments_count": 1,
            }

            response = await client.post(
                "/api/v1/emails/send",
                json=email_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["attachments_count"] == 1

    @pytest.mark.integration
    async def test_send_email_invalid_recipient(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test sending email to invalid email address."""
        invalid_email_data = {
            "to": ["invalid-email-address"],
            "subject": "Test Email",
            "text_content": "This should fail.",
        }

        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.side_effect = ValueError("Invalid email address format")

            response = await client.post(
                "/api/v1/emails/send",
                json=invalid_email_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 400
            data = response.json()
            assert "invalid email address" in data["detail"].lower()

    @pytest.mark.integration
    async def test_send_email_smtp_error(
        self, client: AsyncClient, authenticated_user, sample_email_data, email_service
    ):
        """Test handling of SMTP server errors."""
        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.side_effect = smtplib.SMTPException("SMTP connection failed")

            response = await client.post(
                "/api/v1/emails/send",
                json=sample_email_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 503
            data = response.json()
            assert "smtp connection" in data["detail"].lower()


class TestEmailTemplates:
    """Test email template management."""

    @pytest.mark.integration
    async def test_create_email_template(
        self, client: AsyncClient, authenticated_user, email_template_data, email_service
    ):
        """Test creating a new email template."""
        with patch.object(email_service, 'create_template') as mock_create:
            mock_create.return_value = {
                "id": "template_test123",
                "name": email_template_data["name"],
                "category": email_template_data["category"],
                "created_at": datetime.now().isoformat(),
                "is_active": True,
            }

            response = await client.post(
                "/api/v1/emails/templates",
                json=email_template_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Welcome Email"
            assert data["category"] == "onboarding"

    @pytest.mark.integration
    async def test_list_email_templates(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test listing email templates."""
        with patch.object(email_service, 'list_templates') as mock_list:
            mock_list.return_value = {
                "templates": [
                    {
                        "id": "template_welcome",
                        "name": "Welcome Email",
                        "category": "onboarding",
                        "is_active": True,
                    },
                    {
                        "id": "template_newsletter",
                        "name": "Monthly Newsletter",
                        "category": "marketing",
                        "is_active": True,
                    },
                ],
                "total": 2,
            }

            response = await client.get(
                "/api/v1/emails/templates",
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["templates"]) == 2
            assert data["total"] == 2

    @pytest.mark.integration
    async def test_update_email_template(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test updating an email template."""
        update_data = {
            "name": "Updated Welcome Email",
            "subject": "Welcome to {{company_name}} - Updated!",
            "html_template": "<h1>Updated content</h1>",
        }

        with patch.object(email_service, 'update_template') as mock_update:
            mock_update.return_value = {
                "id": "template_test123",
                "name": "Updated Welcome Email",
                "updated_at": datetime.now().isoformat(),
            }

            response = await client.put(
                "/api/v1/emails/templates/template_test123",
                json=update_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Welcome Email"

    @pytest.mark.integration
    async def test_delete_email_template(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test deleting an email template."""
        with patch.object(email_service, 'delete_template') as mock_delete:
            mock_delete.return_value = {"deleted": True, "template_id": "template_test123"}

            response = await client.delete(
                "/api/v1/emails/templates/template_test123",
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["deleted"] is True

    @pytest.mark.integration
    async def test_preview_template(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test previewing email template with sample data."""
        preview_request = {
            "template_data": {
                "user_name": "Preview User",
                "company_name": "Preview Company",
                "activation_link": "https://preview.com/activate",
            },
        }

        with patch.object(email_service, 'preview_template') as mock_preview:
            mock_preview.return_value = {
                "subject": "Welcome to Preview Company!",
                "html_content": "<h1>Welcome Preview User!</h1>",
                "text_content": "Welcome Preview User!",
            }

            response = await client.post(
                "/api/v1/emails/templates/template_test123/preview",
                json=preview_request,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert "Preview Company" in data["subject"]
            assert "Preview User" in data["html_content"]


class TestBulkEmailOperations:
    """Test bulk email sending and campaigns."""

    @pytest.mark.integration
    async def test_create_email_campaign(
        self, client: AsyncClient, authenticated_user, bulk_email_data, email_service
    ):
        """Test creating a bulk email campaign."""
        with patch.object(email_service, 'create_campaign') as mock_create:
            mock_create.return_value = {
                "campaign_id": "campaign_test123",
                "name": bulk_email_data["campaign_name"],
                "status": "scheduled",
                "recipient_count": 3,
                "scheduled_for": bulk_email_data["schedule_time"].isoformat(),
            }

            response = await client.post(
                "/api/v1/emails/campaigns",
                json=bulk_email_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 201
            data = response.json()
            assert data["campaign_id"] == "campaign_test123"
            assert data["status"] == "scheduled"
            assert data["recipient_count"] == 3

    @pytest.mark.integration
    async def test_send_bulk_email_immediate(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test sending bulk email immediately."""
        bulk_request = {
            "campaign_name": "Immediate Send Test",
            "template_id": "template_bulk123",
            "recipients": [
                {"email": f"user{i}@example.com", "name": f"User {i}"}
                for i in range(10)
            ],
            "send_immediately": True,
        }

        with patch.object(email_service, 'send_bulk_email') as mock_send:
            mock_send.return_value = {
                "campaign_id": "campaign_bulk123",
                "status": "processing",
                "total_recipients": 10,
                "sent_count": 0,
                "failed_count": 0,
            }

            response = await client.post(
                "/api/v1/emails/bulk-send",
                json=bulk_request,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_recipients"] == 10

    @pytest.mark.integration
    async def test_list_email_campaigns(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test listing email campaigns."""
        with patch.object(email_service, 'list_campaigns') as mock_list:
            mock_list.return_value = {
                "campaigns": [
                    {
                        "id": "campaign_1",
                        "name": "Welcome Series",
                        "status": "active",
                        "sent_count": 150,
                        "open_rate": 0.65,
                    },
                    {
                        "id": "campaign_2",
                        "name": "Monthly Newsletter",
                        "status": "scheduled",
                        "sent_count": 0,
                        "open_rate": 0,
                    },
                ],
                "total": 2,
            }

            response = await client.get(
                "/api/v1/emails/campaigns",
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["campaigns"]) == 2

    @pytest.mark.integration
    async def test_campaign_analytics(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test getting campaign analytics."""
        with patch.object(email_service, 'get_campaign_analytics') as mock_analytics:
            mock_analytics.return_value = {
                "campaign_id": "campaign_test123",
                "total_sent": 1000,
                "delivered": 950,
                "opened": 600,
                "clicked": 120,
                "bounced": 30,
                "unsubscribed": 10,
                "open_rate": 0.632,  # 600/950
                "click_rate": 0.126,  # 120/950
                "bounce_rate": 0.031,  # 30/950
                "unsubscribe_rate": 0.011,  # 10/950
            }

            response = await client.get(
                "/api/v1/emails/campaigns/campaign_test123/analytics",
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_sent"] == 1000
            assert data["open_rate"] == 0.632
            assert data["click_rate"] == 0.126


class TestEmailTracking:
    """Test email delivery tracking and analytics."""

    @pytest.mark.integration
    async def test_email_open_tracking(
        self, client: AsyncClient, email_service
    ):
        """Test email open tracking webhook."""
        tracking_data = {
            "event": "open",
            "message_id": "msg_test123",
            "recipient": "user@example.com",
            "timestamp": datetime.now().isoformat(),
            "user_agent": "Mozilla/5.0...",
            "ip_address": "192.168.1.1",
        }

        with patch.object(email_service, 'track_email_open') as mock_track:
            mock_track.return_value = {"tracked": True, "open_count": 1}

            response = await client.post(
                "/api/v1/emails/tracking/open",
                json=tracking_data
            )

            assert response.status_code == 200

    @pytest.mark.integration
    async def test_email_click_tracking(
        self, client: AsyncClient, email_service
    ):
        """Test email click tracking webhook."""
        tracking_data = {
            "event": "click",
            "message_id": "msg_test123",
            "recipient": "user@example.com",
            "timestamp": datetime.now().isoformat(),
            "url": "https://example.com/clicked-link",
            "link_id": "link_123",
        }

        with patch.object(email_service, 'track_email_click') as mock_track:
            mock_track.return_value = {"tracked": True, "click_count": 1}

            response = await client.post(
                "/api/v1/emails/tracking/click",
                json=tracking_data
            )

            assert response.status_code == 200

    @pytest.mark.integration
    async def test_email_delivery_status(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test checking email delivery status."""
        with patch.object(email_service, 'get_delivery_status') as mock_status:
            mock_status.return_value = {
                "message_id": "msg_test123",
                "status": "delivered",
                "delivered_at": datetime.now().isoformat(),
                "recipient": "user@example.com",
                "attempts": 1,
                "last_attempt": datetime.now().isoformat(),
            }

            response = await client.get(
                "/api/v1/emails/status/msg_test123",
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "delivered"
            assert data["attempts"] == 1

    @pytest.mark.integration
    async def test_email_bounce_handling(
        self, client: AsyncClient, email_service
    ):
        """Test handling email bounce events."""
        bounce_data = {
            "event": "bounce",
            "message_id": "msg_bounce123",
            "recipient": "bounced@example.com",
            "bounce_type": "hard",
            "bounce_reason": "invalid_recipient",
            "timestamp": datetime.now().isoformat(),
        }

        with patch.object(email_service, 'handle_bounce') as mock_handle:
            mock_handle.return_value = {
                "processed": True,
                "recipient_blacklisted": True,
                "bounce_type": "hard",
            }

            response = await client.post(
                "/api/v1/emails/tracking/bounce",
                json=bounce_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["recipient_blacklisted"] is True


class TestEmailSecurity:
    """Test email security and compliance."""

    @pytest.mark.integration
    async def test_email_injection_prevention(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test prevention of email injection attacks."""
        malicious_data = {
            "to": ["user@example.com\\r\\nCc: hacker@malicious.com"],
            "subject": "Test\\r\\nSubject: Injection",
            "text_content": "Content\\r\\nBcc: victim@scam.com",
        }

        with patch.object(email_service, 'send_email') as mock_send:
            # Should not reach actual email sending
            mock_send.side_effect = ValueError("Potential email injection detected")

            response = await client.post(
                "/api/v1/emails/send",
                json=malicious_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 400
            data = response.json()
            assert "email injection" in data["detail"].lower()

    @pytest.mark.integration
    async def test_unsubscribe_handling(
        self, client: AsyncClient, email_service
    ):
        """Test handling unsubscribe requests."""
        unsubscribe_data = {
            "email": "user@example.com",
            "campaign_id": "campaign_test123",
            "reason": "User requested unsubscribe",
        }

        with patch.object(email_service, 'process_unsubscribe') as mock_unsubscribe:
            mock_unsubscribe.return_value = {
                "unsubscribed": True,
                "email": "user@example.com",
                "timestamp": datetime.now().isoformat(),
            }

            response = await client.post(
                "/api/v1/emails/unsubscribe",
                json=unsubscribe_data
            )

            assert response.status_code == 200

    @pytest.mark.integration
    async def test_spam_compliance_headers(
        self, client: AsyncClient, authenticated_user, sample_email_data, email_service
    ):
        """Test that emails include spam compliance headers."""
        compliant_data = {
            **sample_email_data,
            "list_unsubscribe": "<https://example.com/unsubscribe?email=test@example.com>",
            "compliance_headers": {
                "X-Priority": "3",
                "X-MSMail-Priority": "Normal",
                "X-Mailer": "PsychSync Email Service",
            },
        }

        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = {
                "message_id": "msg_compliance123",
                "status": "sent",
                "compliance_headers_added": True,
            }

            response = await client.post(
                "/api/v1/emails/send",
                json=compliant_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200

    @pytest.mark.integration
    async def test_rate_limit_email_sending(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test rate limiting on email sending endpoints."""
        basic_email = {
            "to": ["test@example.com"],
            "subject": "Rate Limit Test",
            "text_content": "Testing rate limits",
        }

        # Make multiple rapid requests
        responses = []
        for i in range(15):  # Should hit rate limit
            response = await client.post(
                "/api/v1/emails/send",
                json={**basic_email, "subject": f"Test {i}"},
                headers=authenticated_user["headers"]
            )
            responses.append(response)
            await asyncio.sleep(0.01)

        # Should have rate limited responses
        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0


class TestEmailProviders:
    """Test integration with different email providers."""

    @pytest.mark.integration
    async def test_smtp_provider_configuration(
        self, client: AsyncClient, authenticated_user, email_connector
    ):
        """Test SMTP provider configuration and connection."""
        smtp_config = {
            "provider": "smtp",
            "host": "smtp.example.com",
            "port": 587,
            "username": "user@example.com",
            "password": "secure_password",
            "use_tls": True,
        }

        with patch.object(email_connector, 'test_connection') as mock_test:
            mock_test.return_value = {
                "connected": True,
                "provider": "smtp",
                "response_time": 0.5,
            }

            response = await client.post(
                "/api/v1/emails/providers/test-connection",
                json=smtp_config,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["connected"] is True

    @pytest.mark.integration
    async def test_sendgrid_provider_integration(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test SendGrid provider integration."""
        email_data = {
            "to": ["recipient@example.com"],
            "subject": "SendGrid Test",
            "content": "Testing SendGrid integration",
            "provider": "sendgrid",
        }

        with patch.object(email_service, 'send_via_sendgrid') as mock_send:
            mock_send.return_value = {
                "message_id": "sendgrid_msg_123",
                "status": "sent",
                "provider": "sendgrid",
            }

            response = await client.post(
                "/api/v1/emails/send-with-provider",
                json=email_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200

    @pytest.mark.integration
    async def test_aws_ses_provider_integration(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test AWS SES provider integration."""
        email_data = {
            "to": ["recipient@example.com"],
            "subject": "AWS SES Test",
            "content": "Testing AWS SES integration",
            "provider": "aws_ses",
        }

        with patch.object(email_service, 'send_via_ses') as mock_send:
            mock_send.return_value = {
                "message_id": "aws_ses_msg_123",
                "status": "sent",
                "provider": "aws_ses",
            }

            response = await client.post(
                "/api/v1/emails/send-with-provider",
                json=email_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200

    @pytest.mark.integration
    async def test_provider_fallback(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test provider fallback when primary fails."""
        email_data = {
            "to": ["recipient@example.com"],
            "subject": "Fallback Test",
            "content": "Testing provider fallback",
            "fallback_providers": ["sendgrid", "smtp"],
        }

        with patch.object(email_service, 'send_with_fallback') as mock_send:
            mock_send.return_value = {
                "message_id": "fallback_msg_123",
                "status": "sent",
                "provider_used": "smtp",
                "primary_failed": True,
            }

            response = await client.post(
                "/api/v1/emails/send-with-fallback",
                json=email_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["primary_failed"] is True


class TestEmailErrorHandling:
    """Test email error handling and retry logic."""

    @pytest.mark.integration
    async def test_email_retry_logic(
        self, client: AsyncClient, authenticated_user, sample_email_data, email_service
    ):
        """Test automatic retry logic for failed emails."""
        with patch.object(email_service, 'send_email_with_retry') as mock_send:
            mock_send.return_value = {
                "message_id": "msg_retry_success",
                "status": "sent",
                "attempts": 3,
                "retry_delays": [1.0, 2.0],
            }

            response = await client.post(
                "/api/v1/emails/send-with-retry",
                json=sample_email_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["attempts"] == 3

    @pytest.mark.integration
    async def test_email_queue_processing(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test email queue processing for bulk operations."""
        with patch.object(email_service, 'process_email_queue') as mock_process:
            mock_process.return_value = {
                "processed": 100,
                "successful": 95,
                "failed": 5,
                "processing_time": 30.5,
            }

            response = await client.post(
                "/api/v1/emails/queue/process",
                json={"batch_size": 100},
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["processed"] == 100
            assert data["successful"] == 95

    @pytest.mark.integration
    async def test_failed_email_notifications(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test notifications for failed email sends."""
        with patch.object(email_service, 'send_failure_notification') as mock_notify:
            mock_notify.return_value = {
                "notification_sent": True,
                "failed_message_id": "msg_failed_123",
                "admin_notified": True,
            }

            response = await client.post(
                "/api/v1/emails/notify-failure",
                json={
                    "message_id": "msg_failed_123",
                    "error_message": "SMTP connection timeout",
                    "recipient": "failed@example.com",
                },
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200


class TestEmailAnalytics:
    """Test email analytics and reporting."""

    @pytest.mark.integration
    async def test_email_performance_metrics(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test email performance metrics."""
        with patch.object(email_service, 'get_performance_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "period": "last_7_days",
                "total_sent": 10000,
                "delivery_rate": 0.95,
                "open_rate": 0.45,
                "click_rate": 0.12,
                "bounce_rate": 0.03,
                "unsubscribe_rate": 0.01,
                "average_delivery_time": 2.5,
            }

            response = await client.get(
                "/api/v1/emails/analytics/performance",
                params={"period": "7d"},
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_sent"] == 10000
            assert data["delivery_rate"] == 0.95

    @pytest.mark.integration
    async def test_email_engagement_report(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test email engagement analytics."""
        with patch.object(email_service, 'get_engagement_report') as mock_report:
            mock_report.return_value = {
                "report_period": "last_30_days",
                "engagement_data": [
                    {
                        "date": "2024-01-01",
                        "sent": 500,
                        "opened": 250,
                        "clicked": 50,
                        "conversion_rate": 0.1,
                    },
                    {
                        "date": "2024-01-02",
                        "sent": 450,
                        "opened": 225,
                        "clicked": 45,
                        "conversion_rate": 0.1,
                    },
                ],
            }

            response = await client.get(
                "/api/v1/emails/analytics/engagement",
                params={"period": "30d"},
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["engagement_data"]) == 2

    @pytest.mark.integration
    async def test_template_performance_comparison(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test comparing performance of different email templates."""
        with patch.object(email_service, 'get_template_comparison') as mock_comparison:
            mock_comparison.return_value = {
                "templates": [
                    {
                        "template_id": "template_welcome",
                        "name": "Welcome Email",
                        "sent_count": 1000,
                        "open_rate": 0.65,
                        "click_rate": 0.15,
                        "conversion_rate": 0.08,
                    },
                    {
                        "template_id": "template_newsletter",
                        "name": "Newsletter",
                        "sent_count": 800,
                        "open_rate": 0.45,
                        "click_rate": 0.08,
                        "conversion_rate": 0.03,
                    },
                ],
                "best_performing": "template_welcome",
            }

            response = await client.get(
                "/api/v1/emails/analytics/template-comparison",
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["best_performing"] == "template_welcome"


class TestEmailPerformance:
    """Test email sending performance and load testing."""

    @pytest.mark.performance
    async def test_bulk_email_performance(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test bulk email sending performance."""
        import time

        bulk_request = {
            "campaign_name": "Performance Test",
            "recipients": [
                {"email": f"user{i}@example.com", "name": f"User {i}"}
                for i in range(1000)
            ],
            "template_id": "template_performance",
            "batch_size": 100,
        }

        with patch.object(email_service, 'send_bulk_email') as mock_send:
            mock_send.return_value = {
                "campaign_id": "perf_test_123",
                "status": "completed",
                "total_recipients": 1000,
                "processing_time": 45.2,
            }

            start_time = time.time()
            response = await client.post(
                "/api/v1/emails/bulk-send",
                json=bulk_request,
                headers=authenticated_user["headers"]
            )
            end_time = time.time()

            response_time = end_time - start_time
            assert response.status_code == 200

            # API response should be quick even for bulk operations
            assert response_time < 5.0

    @pytest.mark.performance
    async def test_template_rendering_performance(
        self, client: AsyncClient, authenticated_user, email_service
    ):
        """Test email template rendering performance."""
        import time

        template_data = {
            "template_id": "template_complex",
            "template_data": {
                "user_name": "Performance Test User",
                "company": "Performance Test Company",
                "products": [{"name": f"Product {i}"} for i in range(100)],
            },
        }

        with patch.object(email_service, 'preview_template') as mock_preview:
            mock_preview.return_value = {
                "subject": "Performance Test",
                "html_content": "<h1>Rendered content</h1>",
            }

            start_time = time.time()
            response = await client.post(
                "/api/v1/emails/templates/template_complex/preview",
                json=template_data,
                headers=authenticated_user["headers"]
            )
            end_time = time.time()

            response_time = end_time - start_time
            assert response.status_code == 200
            # Template rendering should be fast
            assert response_time < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])