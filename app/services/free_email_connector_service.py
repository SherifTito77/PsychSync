# app/services/free_email_connector_service.py
"""
Free Email Connector Service - IMAP-based email connections
Replaces OAuth with app passwords for free localhost deployment
"""

import email
import imaplib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.header import decode_header
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging_config import logger
from app.db.models.email_connection import EmailConnection
from app.db.models.email_metadata import EmailMetadata


@dataclass
class IMAPConfig:
    """IMAP server configuration for common providers"""

    host: str
    port: int
    use_ssl: bool = True
    use_starttls: bool = False


# Free IMAP configurations for major providers
IMAP_PROVIDERS = {
    "gmail": IMAPConfig("imap.gmail.com", 993, use_ssl=True),
    "outlook": IMAPConfig("outlook.office365.com", 993, use_ssl=True),
    "yahoo": IMAPConfig("imap.mail.yahoo.com", 993, use_ssl=True),
    "icloud": IMAPConfig("imap.mail.me.com", 993, use_ssl=True),
    "aol": IMAPConfig("imap.aol.com", 993, use_ssl=True),
    "hotmail": IMAPConfig("outlook.office365.com", 993, use_ssl=True),
    "custom": None,  # User provides custom IMAP settings
}


class FreeEmailConnectorService:
    """Free IMAP-based email connector service"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_provider_config(self, email_address: str) -> IMAPConfig:
        """Get IMAP config based on email domain"""
        # ✅ FIX: Validate email format before parsing (prevents IndexError)
        if not email_address or "@" not in email_address:
            logger.error(f"Invalid email address (missing @): {email_address}")
            return IMAP_PROVIDERS["custom"]  # Requires manual config

        parts = email_address.split("@")
        if len(parts) != 2:
            logger.error(f"Invalid email address (multiple @): {email_address}")
            return IMAP_PROVIDERS["custom"]

        username, domain = parts
        if not username or not domain:
            logger.error(f"Invalid email address (empty parts): {email_address}")
            return IMAP_PROVIDERS["custom"]

        domain = domain.lower()

        if "gmail.com" in domain:
            return IMAP_PROVIDERS["gmail"]
        if "outlook.com" in domain or "live.com" in domain:
            return IMAP_PROVIDERS["outlook"]
        if "yahoo.com" in domain:
            return IMAP_PROVIDERS["yahoo"]
        if "icloud.com" in domain or "me.com" in domain:
            return IMAP_PROVIDERS["icloud"]
        if "aol.com" in domain:
            return IMAP_PROVIDERS["aol"]
        if "hotmail.com" in domain:
            return IMAP_PROVIDERS["hotmail"]
        return IMAP_PROVIDERS["custom"]  # Requires manual config

    def test_imap_connection(
        self, email_address: str, app_password: str, custom_config: dict | None = None
    ) -> tuple[bool, str]:
        """Test IMAP connection with app password"""
        try:
            config = self.get_provider_config(email_address)

            if custom_config:
                config = IMAPConfig(
                    host=custom_config["host"],
                    port=custom_config["port"],
                    use_ssl=custom_config.get("use_ssl", True),
                    use_starttls=custom_config.get("use_starttls", False),
                )

            if not config:
                return (
                    False,
                    "Unsupported email provider. Please provide custom IMAP settings.",
                )

            # Create IMAP connection
            if config.use_ssl:
                imap = imaplib.IMAP4_SSL(config.host, config.port)
            else:
                imap = imaplib.IMAP4(config.host, config.port)
                if config.use_starttls:
                    imap.starttls()

            # Login with app password
            try:
                imap.login(email_address, app_password)
                imap.logout()
                return True, "Connection successful"
            except imaplib.IMAP4.error as e:
                return False, f"Authentication failed: {e!s}"

        except Exception as e:
            return False, f"Connection failed: {e!s}"

    async def create_free_connection(
        self,
        db: AsyncSession,
        user_id: str,
        email_address: str,
        app_password: str,
        account_name: str | None = None,
        custom_imap_config: dict | None = None,
    ) -> EmailConnection:
        """Create free IMAP email connection"""
        try:
            # Test connection first
            success, message = self.test_imap_connection(
                email_address, app_password, custom_imap_config
            )

            if not success:
                raise ValueError(f"IMAP connection test failed: {message}")

            # Store provider info
            # ✅ FIX: Validate email format before parsing
            if "@" not in email_address:
                raise ValueError(f"Invalid email address format: {email_address}")

            email_parts = email_address.split("@")
            if len(email_parts) != 2:
                raise ValueError(f"Invalid email address format: {email_address}")

            username, domain = email_parts
            if not username or not domain:
                raise ValueError(f"Invalid email address format: {email_address}")

            domain = domain.lower()
            provider = (
                "custom"
                if custom_imap_config
                else domain.split(".")[0] if "." in domain else "custom"
            )

            # Encrypt password for storage
            from cryptography.fernet import Fernet

            cipher = Fernet(settings.EMAIL_ENCRYPTION_KEY.encode())
            encrypted_password = cipher.encrypt(app_password.encode()).decode()

            # Create connection record
            connection = EmailConnection(
                user_id=user_id,
                provider=provider,
                email_address=email_address,
                access_token=encrypted_password,  # Store app password here
                refresh_token=None,  # Not needed for IMAP
                account_name=account_name or username,
                is_active=True,
                connection_type="imap",  # Custom field for connection type
                custom_imap_config=custom_imap_config,  # Store custom config if provided
                privacy_settings={
                    "analyze_internal_only": True,
                    "exclude_domains": ["spam.com", "promotions.com"],
                    "min_email_age_days": 7,
                    "max_emails_per_fetch": 1000,
                },
            )

            db.add(connection)
            await db.commit()
            await db.refresh(connection)

            self.logger.info(f"Created IMAP connection for {email_address}")
            return connection

        except Exception as e:
            self.logger.error(f"Failed to create IMAP connection: {e}")
            await db.rollback()
            raise

    async def fetch_emails_imap(
        self,
        db: AsyncSession,
        connection: EmailConnection,
        max_messages: int = 1000,
        days_back: int = 30,
    ) -> int:
        """Fetch emails using IMAP (free method)"""
        try:
            # Decrypt app password
            from cryptography.fernet import Fernet

            cipher = Fernet(settings.EMAIL_ENCRYPTION_KEY.encode())
            app_password = cipher.decrypt(connection.access_token.encode()).decode()

            # Get IMAP config
            config = self.get_provider_config(connection.email_address)
            if (
                hasattr(connection, "custom_imap_config")
                and connection.custom_imap_config
            ):
                config = IMAPConfig(
                    host=connection.custom_imap_config["host"],
                    port=connection.custom_imap_config["port"],
                    use_ssl=connection.custom_imap_config.get("use_ssl", True),
                    use_starttls=connection.custom_imap_config.get(
                        "use_starttls", False
                    ),
                )

            # Connect to IMAP server
            if config.use_ssl:
                imap = imaplib.IMAP4_SSL(config.host, config.port)
            else:
                imap = imaplib.IMAP4(config.host, config.port)
                if config.use_starttls:
                    imap.starttls()

            # Login
            imap.login(connection.email_address, app_password)

            # Calculate date filter
            date_filter = (datetime.utcnow() - timedelta(days=days_back)).strftime(
                "%d-%b-%Y"
            )

            # Select inbox
            imap.select("INBOX")

            # Search for emails
            search_criteria = f"(SINCE {date_filter})"
            _, message_ids = imap.search(None, search_criteria)

            # ✅ FIX: Check message_ids exists and has content
            if not message_ids or not message_ids[0]:
                imap.logout()
                return 0

            # Limit messages
            message_id_list = message_ids[0].split()[-max_messages:]

            messages_processed = 0

            # Fetch email metadata
            for msg_id in message_id_list:
                try:
                    # Fetch email headers only
                    _, msg_data = imap.fetch(msg_id, "(BODY[HEADER])")

                    # Parse email headers
                    email_message = email.message_from_bytes(msg_data[0][1])

                    # Extract metadata
                    metadata = self._extract_email_metadata(
                        email_message, connection.id
                    )

                    if metadata:
                        # Store in database
                        email_record = EmailMetadata(**metadata)
                        db.add(email_record)
                        messages_processed += 1

                except Exception as e:
                    self.logger.warning(f"Failed to process email {msg_id}: {e}")
                    continue

            await db.commit()
            imap.logout()

            # Update connection
            connection.last_sync_at = datetime.utcnow()
            connection.sync_status = "completed"
            await db.commit()

            self.logger.info(
                f"Fetched {messages_processed} emails for {connection.email_address}"
            )
            return messages_processed

        except Exception as e:
            self.logger.error(f"IMAP fetch failed: {e}")
            connection.sync_status = "error"
            connection.sync_error_message = str(e)
            await db.commit()
            raise

    def _extract_email_metadata(
        self, email_message: email.message.Message, connection_id: str
    ) -> dict[str, Any] | None:
        """Extract metadata from email message headers"""
        try:
            # Basic headers
            subject = self._decode_header(email_message.get("Subject", ""))
            sender = self._decode_header(email_message.get("From", ""))
            recipients = [
                self._decode_header(r) for r in email_message.get_all("To", [])
            ]
            cc_recipients = [
                self._decode_header(r) for r in email_message.get_all("Cc", [])
            ]

            # Date parsing
            date_sent = self._parse_date(email_message.get("Date"))
            date_received = datetime.utcnow()  # IMAP doesn't provide received time

            # Generate unique message ID
            message_id = email_message.get("Message-ID", "")

            # Implement duplicate checking to prevent processing the same email multiple times
            if (
                hasattr(self, "processed_messages")
                and message_id in self.processed_messages
            ):
                logger.debug(f"Skipping duplicate message: {message_id}")
                return None

            # Initialize processed messages set if not exists
            if not hasattr(self, "processed_messages"):
                self.processed_messages = set()

            # Add message ID to processed set (in production, this should be database-backed)
            self.processed_messages.add(message_id)

            # Optional: Clean up old message IDs to prevent memory leaks (keep last 10000)
            if len(self.processed_messages) > 10000:
                # Remove oldest 2000 message IDs
                self.processed_messages = set(list(self.processed_messages)[2000:])

            # Determine if internal email
            is_internal = self._is_internal_email(sender, recipients + cc_recipients)

            # Generate subject hash for analysis
            import hashlib

            subject_hash = hashlib.sha256(subject.encode()).hexdigest()

            return {
                "connection_id": connection_id,
                "message_id": message_id,
                "thread_id": email_message.get("In-Reply-To", "") or message_id,
                "sender": sender,
                "recipients": recipients,
                "cc_recipients": cc_recipients,
                "bcc_recipients": [],  # Not available in headers
                "subject": subject,
                "subject_hash": subject_hash,
                "date_sent": date_sent,
                "date_received": date_received,
                "is_internal": is_internal,
                "folder_labels": ["INBOX"],
                "message_size": len(str(email_message)),
                "has_attachments": "attachment"
                in email_message.get("Content-Type", "").lower(),
            }

        except Exception as e:
            self.logger.warning(f"Failed to extract email metadata: {e}")
            return None

    def _decode_header(self, header: str) -> str:
        """Decode email header"""
        if not header:
            return ""

        try:
            decoded_parts = decode_header(header)
            decoded_str = ""

            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_str += part.decode(encoding)
                    else:
                        decoded_str += part.decode("utf-8", errors="ignore")
                else:
                    decoded_str += part

            return decoded_str.strip()
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            return header.strip()

    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date"""
        try:
            from email.utils import parsedate_to_datetime

            return parsedate_to_datetime(date_str)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            return datetime.utcnow()

    def _is_internal_email(self, sender: str, recipients: list[str]) -> bool:
        """Determine if email is internal based on domains"""
        try:
            # Extract domains
            sender_domain = sender.split("@")[-1].lower() if "@" in sender else ""

            for recipient in recipients:
                recipient_domain = (
                    recipient.split("@")[-1].lower() if "@" in recipient else ""
                )
                if recipient_domain and recipient_domain != sender_domain:
                    return False

            return True if sender_domain else False
        except Exception as e:
            return False


# Singleton instance
free_email_connector_service = FreeEmailConnectorService()
