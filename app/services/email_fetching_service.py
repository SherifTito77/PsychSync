# app/services/email_fetching_service.py
"""
Email Fetching Service - Retrieves email metadata for analysis
Privacy-first approach: only fetches headers, never content
"""

import hashlib
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import re
from dateutil import parser as date_parser
from sqlalchemy.ext.asyncio import AsyncSession
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import requests
import base64

from app.db.models.email_connection import EmailConnection, EmailProvider
from app.db.models.email_metadata import EmailMetadata
from app.services.email_connector_service import email_connector_service
from app.core.logging_config import logger


class EmailFetchingService:
    """Service for fetching email metadata from various providers"""

    def __init__(self):
        self.connector_service = email_connector_service

    async def fetch_emails_batch(
        self,
        db: Session,
        connection: EmailConnection,
        max_messages: int = 1000,
        days_back: int = 30
    ) -> int:
        """Fetch batch of email metadata for analysis"""

        logger.info(f"Starting email fetch for connection {connection.id}")

        # Check if connection needs token refresh
        if connection.token_expires_at and connection.token_expires_at <= datetime.utcnow():
            if not await self.connector_service.refresh_access_token(db, connection):
                raise Exception("Failed to refresh access token")

        try:
            if connection.provider == EmailProvider.GMAIL:
                return await self._fetch_gmail_emails(db, connection, max_messages, days_back)
            elif connection.provider in [EmailProvider.OUTLOOK, EmailProvider.OFFICE365]:
                return await self._fetch_outlook_emails(db, connection, max_messages, days_back)
            elif connection.provider == EmailProvider.IMAP:
                return await self._fetch_imap_emails(db, connection, max_messages, days_back)
            else:
                raise ValueError(f"Unsupported provider: {connection.provider}")

        except Exception as e:
            logger.error(f"Email fetch failed for connection {connection.id}: {e}")
            connection.sync_status = "error"
            connection.sync_error_message = str(e)
            connection.last_sync_at = datetime.utcnow()
            await db.commit()
            raise

    async def _fetch_gmail_emails(
        self,
        db: Session,
        connection: EmailConnection,
        max_messages: int,
        days_back: int
    ) -> int:
        """Fetch emails from Gmail API"""

        access_token = self.connector_service.decrypt_token(connection.access_token_encrypted)
        credentials = Credentials(access_token)

        service = build('gmail', 'v1', credentials=credentials)

        # Calculate date range
        date_since = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y/%m/%d')

        # Search query for messages
        query = f'after:{date_since}'

        # Get list of messages
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_messages
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            logger.info(f"No messages found for Gmail connection {connection.id}")
            return 0

        logger.info(f"Found {len(messages)} messages to process")

        processed_count = 0
        for message_ref in messages:
            try:
                # Get full message details
                message = service.users().messages().get(
                    userId='me',
                    id=message_ref['id'],
                    format='metadata',
                    metadataHeaders=['From', 'To', 'Cc', 'Bcc', 'Date', 'Subject', 'Message-ID', 'Thread-ID', 'References']
                ).execute()

                email_metadata = self._parse_gmail_message(message, connection)
                if email_metadata:
                    await self._save_email_metadata(db, email_metadata)
                    processed_count += 1

            except Exception as e:
                logger.error(f"Error processing Gmail message {message_ref['id']}: {e}")
                continue

        # Update connection status
        connection.sync_status = "completed"
        connection.last_sync_at = datetime.utcnow()
        connection.sync_error_message = None
        await db.commit()

        logger.info(f"Successfully processed {processed_count} emails from Gmail")
        return processed_count

    def _parse_gmail_message(self, message: Dict, connection: EmailConnection) -> Optional[EmailMetadata]:
        """Parse Gmail API message into EmailMetadata"""

        try:
            headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}

            # Extract basic info
            message_id = message['id']
            subject = headers.get('Subject', '')
            date_sent_str = headers.get('Date', '')
            sender = headers.get('From', '')
            thread_id = message.get('threadId')

            # Parse date
            date_sent = None
            date_received = datetime.utcnow()  # Use current time as fallback
            if date_sent_str:
                try:
                    date_sent = date_parser.parse(date_sent_str)
                    date_received = date_sent
                except:
                    logger.warning(f"Could not parse date: {date_sent_str}")

            # Create subject hash for deduplication
            subject_hash = hashlib.sha256(subject.encode('utf-8')).hexdigest()

            # Extract participants
            all_participants = set()
            participants = []

            # Add sender
            if sender:
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender)
                if email_match:
                    all_participants.add(email_match.group())

            # Add recipients
            for field in ['To', 'Cc', 'Bcc']:
                recipients = headers.get(field, '')
                if recipients:
                    for email_match in re.finditer(r'[\w\.-]+@[\w\.-]+\.\w+', recipients):
                        all_participants.add(email_match.group())

            participants = list(all_participants)

            # Determine if internal (all from same domain)
            user_domain = connection.email_address.split('@')[-1]
            is_internal = all(
                '@' in email and email.split('@')[-1] == user_domain
                for email in participants
            )

            # Calculate participant count
            participant_count = len(participants)

            # Extract thread information
            thread_id = thread_id or message_id

            # Determine email direction
            email_direction = self._determine_email_direction(sender, connection.email_address)

            return EmailMetadata(
                message_id=message_id,
                connection_id=connection.id,
                user_id=connection.user_id,
                thread_id=thread_id,
                subject_hash=subject_hash,
                date_sent=date_sent,
                date_received=date_received,
                sender_address=sender,
                all_participants=participants,
                participant_count=participant_count,
                is_internal=is_internal,
                email_direction=email_direction,
                size_bytes=len(str(message)),  # Approximate size
                attachment_count=self._count_gmail_attachments(message),
            )

        except Exception as e:
            logger.error(f"Error parsing Gmail message {message.get('id', 'unknown')}: {e}")
            return None

    def _count_gmail_attachments(self, message: Dict) -> int:
        """Count attachments in Gmail message"""
        try:
            payload = message.get('payload', {})
            parts = payload.get('parts', [])

            def count_parts_recursive(parts):
                count = 0
                for part in parts:
                    if part.get('filename'):
                        count += 1
                    if part.get('parts'):
                        count += count_parts_recursive(part.get('parts'))
                return count

            return count_parts_recursive(parts)
        except:
            return 0

    async def _fetch_outlook_emails(
        self,
        db: Session,
        connection: EmailConnection,
        max_messages: int,
        days_back: int
    ) -> int:
        """Fetch emails from Outlook/Graph API"""

        access_token = self.connector_service.decrypt_token(connection.access_token_encrypted)

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Calculate date filter
        date_since = (datetime.utcnow() - timedelta(days=days_back)).isoformat()

        # Get messages
        url = f"https://graph.microsoft.com/v1.0/me/messages?$filter=receivedDateTime ge {date_since}&$top={max_messages}&$orderby=receivedDateTime desc"

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        messages = data.get('value', [])

        if not messages:
            logger.info(f"No messages found for Outlook connection {connection.id}")
            return 0

        logger.info(f"Found {len(messages)} messages to process")

        processed_count = 0
        for message in messages:
            try:
                email_metadata = self._parse_outlook_message(message, connection)
                if email_metadata:
                    await self._save_email_metadata(db, email_metadata)
                    processed_count += 1

            except Exception as e:
                logger.error(f"Error processing Outlook message {message.get('id', 'unknown')}: {e}")
                continue

        # Update connection status
        connection.sync_status = "completed"
        connection.last_sync_at = datetime.utcnow()
        connection.sync_error_message = None
        await db.commit()

        logger.info(f"Successfully processed {processed_count} emails from Outlook")
        return processed_count

    def _parse_outlook_message(self, message: Dict, connection: EmailConnection) -> Optional[EmailMetadata]:
        """Parse Outlook message into EmailMetadata"""

        try:
            message_id = message['id']
            subject = message.get('subject', '')
            date_sent_str = message.get('receivedDateTime')
            sender = message.get('from', {}).get('emailAddress', {}).get('address', '')
            thread_id = message.get('conversationId')

            # Parse date
            date_sent = None
            date_received = datetime.utcnow()
            if date_sent_str:
                try:
                    date_sent = date_parser.parse(date_sent_str)
                    date_received = date_sent
                except:
                    logger.warning(f"Could not parse date: {date_sent_str}")

            # Create subject hash
            subject_hash = hashlib.sha256(subject.encode('utf-8')).hexdigest()

            # Extract participants
            all_participants = set()

            # Add sender
            if sender:
                all_participants.add(sender)

            # Add recipients
            for recipient_field in ['toRecipients', 'ccRecipients', 'bccRecipients']:
                recipients = message.get(recipient_field, [])
                for recipient in recipients:
                    email_addr = recipient.get('emailAddress', {}).get('address')
                    if email_addr:
                        all_participants.add(email_addr)

            participants = list(all_participants)

            # Determine if internal
            user_domain = connection.email_address.split('@')[-1]
            is_internal = all(
                '@' in email and email.split('@')[-1] == user_domain
                for email in participants
            )

            participant_count = len(participants)

            # Determine email direction
            email_direction = self._determine_email_direction(sender, connection.email_address)

            return EmailMetadata(
                message_id=message_id,
                connection_id=connection.id,
                user_id=connection.user_id,
                thread_id=thread_id,
                subject_hash=subject_hash,
                date_sent=date_sent,
                date_received=date_received,
                sender_address=sender,
                all_participants=participants,
                participant_count=participant_count,
                is_internal=is_internal,
                email_direction=email_direction,
                size_bytes=message.get('bodySize', 0),
                attachment_count=len(message.get('attachments', [])),
            )

        except Exception as e:
            logger.error(f"Error parsing Outlook message {message.get('id', 'unknown')}: {e}")
            return None

    async def _fetch_imap_emails(
        self,
        db: Session,
        connection: EmailConnection,
        max_messages: int,
        days_back: int
    ) -> int:
        """Fetch emails from IMAP server (basic implementation)"""

        # This is a placeholder for IMAP implementation
        # In practice, you'd need server configuration, credentials, etc.
        logger.warning(f"IMAP fetching not fully implemented for connection {connection.id}")

        # Update connection status
        connection.sync_status = "completed"
        connection.last_sync_at = datetime.utcnow()
        connection.sync_error_message = "IMAP fetching not yet implemented"
        await db.commit()

        return 0

    def _determine_email_direction(self, sender: str, user_email: str) -> str:
        """Determine if email is incoming, outgoing, or internal"""
        if not sender or not user_email:
            return "unknown"

        # Extract email addresses
        sender_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender)
        if not sender_match:
            return "unknown"

        sender_email = sender_match.group()

        if sender_email.lower() == user_email.lower():
            return "outgoing"
        else:
            return "incoming"

    async def _save_email_metadata(...db: AsyncSession...):
        """Save email metadata to database, avoiding duplicates"""

        # Check if already exists
        existing = result = await db.execute(query)
        return result.scalars().all()

        if existing:
            logger.debug(f"Email {email_metadata.message_id} already exists, skipping")
            return

        try:
            db.add(email_metadata)
        await db.commit()
            logger.debug(f"Saved email metadata for {email_metadata.message_id}")
        except Exception as e:
            logger.error(f"Error saving email metadata: {e}")
            await db.rollback()
            raise

    async def calculate_response_times(...db: AsyncSession...):
        """Calculate response times for emails by analyzing thread patterns"""

        # Get all emails for the user
        emails = db.query(EmailMetadata).filter(
            EmailMetadata.user_id == user_id
        ).order_by(EmailMetadata.date_received).all()

        # Group by thread
        threads = {}
        for email in emails:
            if email.thread_id not in threads:
                threads[email.thread_id] = []
            threads[email.thread_id].append(email)

        # Calculate response times
        response_times = []

        for thread_id, thread_emails in threads.items():
            thread_emails.sort(key=lambda x: x.date_received or datetime.min)

            for i in range(1, len(thread_emails)):
                current_email = thread_emails[i]
                previous_email = thread_emails[i-1]

                # Only calculate if there's a time gap and different senders
                if (current_email.date_received and previous_email.date_received and
                    current_email.sender_address != previous_email.sender_address):

                    time_diff = current_email.date_received - previous_email.date_received
                    response_minutes = int(time_diff.total_seconds() / 60)

                    # Only consider reasonable response times (within 30 days)
                    if 0 < response_minutes <= 30 * 24 * 60:  # 30 days in minutes
                        response_times.append(response_minutes)

        # Update emails with response times
        # This is a simplified approach - in practice you'd want more sophisticated analysis
        return response_times


# Global service instance
email_fetching_service = EmailFetchingService()