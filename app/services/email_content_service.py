# app/services/email_content_service.py
"""
Email Content Service - Fetches full email content for sentiment analysis
Includes caching for performance and privacy-first approach
"""

import hashlib
import json
import unicodedata
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import logger
from app.core.redis_client import get_redis_client
from app.db.models.email_connection import EmailConnection, EmailProvider


class EmailContentService:
    """Service for fetching email content with caching"""

    def __init__(self):
        self.cache_ttl = 300  # Cache emails for 5 minutes (was 1 hour)
        self.max_content_length = 10000  # Limit content size for analysis

    async def get_user_emails_for_analysis(
        self,
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """
        Get user's emails with content for sentiment analysis
        Tries to fetch from connected email accounts, falls back to sample data

        Args:
            db: Database session
            user_id: User ID
            page: Page number
            limit: Items per page
            days_back: Number of days to look back

        Returns:
            Dict with emails list and pagination info
        """
        # Try to get user's email connections
        result = await db.execute(
            select(EmailConnection).where(
                EmailConnection.user_id == user_id,
                EmailConnection.connection_status == "ACTIVE",
            )
        )
        connections = result.scalars().all()

        logger.info(
            f"Found {len(connections)} active email connections for user {user_id}"
        )
        for conn in connections:
            logger.info(
                f"Connection: {conn.provider} - {conn.email_address} - Params: {conn.connection_parameters}"
            )

        if not connections:
            logger.info(f"No active email connections found for user {user_id}")
            return await self._get_sample_emails(page, limit)

        # Try to fetch from each connected account
        all_emails = []
        for connection in connections:
            try:
                logger.info(
                    f"Fetching emails from {connection.provider} connection: {connection.email_address}"
                )
                emails = await self._fetch_emails_from_connection(
                    db, connection, limit, days_back
                )
                logger.info(
                    f"Fetched {len(emails)} emails from {connection.email_address}"
                )
                all_emails.extend(emails)
            except Exception as e:
                logger.error(
                    f"Failed to fetch from connection {connection.id}: {e}",
                    exc_info=True,
                )
                continue

        if not all_emails:
            logger.info(f"No emails fetched from connections, using sample data")
            return await self._get_sample_emails(page, limit)

        # Sort by date (newest first)
        all_emails.sort(key=lambda x: x.get("date", ""), reverse=True)

        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_emails = all_emails[start_idx:end_idx]

        return {
            "emails": paginated_emails,
            "total": len(all_emails),
            "page": page,
            "limit": limit,
        }

    async def _fetch_emails_from_connection(
        self, db: AsyncSession, connection: EmailConnection, limit: int, days_back: int
    ) -> List[Dict[str, Any]]:
        """Fetch emails with content from a specific connection"""
        # Check cache first - include limit in cache key
        cache_key = f"emails:{connection.user_id}:{connection.id}:{days_back}:{limit}"
        cached_emails = await self._get_from_cache(cache_key)

        if cached_emails:
            logger.info(f"Returning cached emails for {cache_key}")
            return json.loads(cached_emails)

        # Fetch fresh emails
        try:
            if connection.provider == EmailProvider.GMAIL:
                emails = await self._fetch_gmail_emails_with_content(
                    db, connection, limit, days_back
                )
            elif connection.provider in [EmailProvider.OUTLOOK, EmailProvider.EXCHANGE]:
                emails = await self._fetch_outlook_emails_with_content(
                    db, connection, limit, days_back
                )
            elif connection.provider == EmailProvider.IMAP:
                emails = await self._fetch_imap_emails_with_content(
                    db, connection, limit, days_back
                )
            else:
                logger.warning(f"Unsupported provider: {connection.provider}")
                return []

            # Cache the results
            await self._cache_emails(cache_key, emails)

            return emails

        except Exception as e:
            logger.error(f"Error fetching emails from {connection.provider}: {e}")
            return []

    async def _fetch_gmail_emails_with_content(
        self, db: AsyncSession, connection: EmailConnection, limit: int, days_back: int
    ) -> List[Dict[str, Any]]:
        """Fetch emails with content from Gmail API"""
        from app.services.email_connector_service import email_connector_service

        # Get access token
        access_token = email_connector_service.decrypt_token(
            connection.access_token_encrypted
        )
        credentials = Credentials(access_token)

        service = build("gmail", "v1", credentials=credentials)

        # Calculate date range
        date_since = (datetime.utcnow() - timedelta(days=days_back)).strftime(
            "%Y/%m/%d"
        )

        # Search query - exclude emails with privacy-sensitive keywords
        exclude_keywords = " OR ".join(
            [
                f'-subject:"{kw}"'
                for kw in [
                    "private",
                    "confidential",
                    "password",
                    "secret",
                    "personal",
                    "salary",
                    "ssn",
                    "social security",
                ]
            ]
        )
        query = f"after:{date_since} {exclude_keywords}"

        # Get list of messages
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=limit)
            .execute()
        )

        messages = results.get("messages", [])
        if not messages:
            return []

        emails = []
        for message_ref in messages[:limit]:  # Limit results
            try:
                # Get full message with content
                message = (
                    service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=message_ref["id"],
                        format="full",  # Get full content
                        metadataHeaders=["From", "To", "Cc", "Date", "Subject"],
                    )
                    .execute()
                )

                email_data = self._parse_gmail_email_with_content(message)
                if email_data:
                    emails.append(email_data)

            except Exception as e:
                logger.error(
                    f"Error processing Gmail message {message_ref.get('id')}: {e}"
                )
                continue

        return emails

    def _parse_gmail_email_with_content(
        self, message: dict
    ) -> Optional[Dict[str, Any]]:
        """Parse Gmail message with content"""
        try:
            # Extract headers
            headers = {
                h["name"]: h["value"]
                for h in message.get("payload", {}).get("headers", [])
            }

            # Extract basic info
            message_id = message["id"]
            subject = headers.get("Subject", "(No Subject)")
            sender = headers.get("From", "")
            date_str = headers.get("Date", "")

            # Parse date
            try:
                from dateutil import parser as date_parser

                date_sent = date_parser.parse(date_str)
                date_formatted = date_sent.strftime("%Y-%m-%d")
            except:
                date_formatted = datetime.utcnow().strftime("%Y-%m-%d")

            # Extract email body content
            body_content = self._extract_gmail_body(message.get("payload", {}))

            # Truncate if too long
            if len(body_content) > self.max_content_length:
                body_content = body_content[: self.max_content_length] + "..."

            # Create snippet
            snippet = (
                body_content[:100] + "..." if len(body_content) > 100 else body_content
            )

            # Extract sender email address
            import re

            sender_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", sender)
            sender_email = sender_match.group() if sender_match else sender

            return {
                "id": message_id,
                "subject": subject,
                "from": sender_email,
                "date": date_formatted,
                "snippet": snippet,
                "body": body_content,
            }

        except Exception as e:
            logger.error(f"Error parsing Gmail email: {e}")
            return None

    def _extract_gmail_body(self, payload: dict) -> str:
        """Extract text body from Gmail message payload"""
        body = ""

        def extract_parts(parts):
            nonlocal body
            for part in parts:
                mime_type = part.get("mimeType", "")
                part_body = part.get("body", {})
                data = part_body.get("data")

                # If text/plain, extract content
                if mime_type == "text/plain" and data:
                    import base64

                    # Decode base64 URL-safe encoding
                    body += base64.urlsafe_b64decode(data).decode(
                        "utf-8", errors="ignore"
                    )

                # Recursively process nested parts
                if "parts" in part:
                    extract_parts(part["parts"])

        # Start extraction
        if "parts" in payload:
            extract_parts(payload["parts"])
        elif payload.get("body", {}).get("data"):
            # Single part message
            import base64

            data = payload["body"]["data"]
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        return body.strip()

    async def _fetch_outlook_emails_with_content(
        self, db: AsyncSession, connection: EmailConnection, limit: int, days_back: int
    ) -> List[Dict[str, Any]]:
        """Fetch emails with content from Outlook/Graph API"""
        import httpx

        from app.services.email_connector_service import email_connector_service

        # Get access token
        access_token = email_connector_service.decrypt_token(
            connection.access_token_encrypted
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # Calculate date filter
        date_since = (datetime.utcnow() - timedelta(days=days_back)).isoformat()

        # Get messages with $select to get body content
        url = (
            f"https://graph.microsoft.com/v1.0/me/messages?"
            f"$filter=receivedDateTime ge {date_since} and "
            f"not(subjectAnyOf('private', 'confidential', 'password', 'secret', 'salary'))&"
            f"$top={limit}&"
            f"$orderby=receivedDateTime desc&"
            f"$select=id,subject,from,toRecipients,ccRecipients,receivedDateTime,body"
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            messages = data.get("value", [])

        emails = []
        for message in messages:
            try:
                email_data = self._parse_outlook_email_with_content(message)
                if email_data:
                    emails.append(email_data)
            except Exception as e:
                logger.error(f"Error parsing Outlook message: {e}")
                continue

        return emails

    def _parse_outlook_email_with_content(
        self, message: dict
    ) -> Optional[Dict[str, Any]]:
        """Parse Outlook message with content"""
        try:
            message_id = message["id"]
            subject = message.get("subject", "(No Subject)")

            # Extract sender
            sender_obj = message.get("from", {})
            sender_email = sender_obj.get("emailAddress", {}).get("address", "")

            # Parse date
            date_str = message.get("receivedDateTime")
            try:
                from dateutil import parser as date_parser

                date_sent = date_parser.parse(date_str)
                date_formatted = date_sent.strftime("%Y-%m-%d")
            except:
                date_formatted = datetime.utcnow().strftime("%Y-%m-%d")

            # Extract body content
            body_obj = message.get("body", {})
            body_content = body_obj.get("content", "")

            # Truncate if too long
            if len(body_content) > self.max_content_length:
                body_content = body_content[: self.max_content_length] + "..."

            # Create snippet
            snippet = (
                body_content[:100] + "..." if len(body_content) > 100 else body_content
            )

            return {
                "id": message_id,
                "subject": subject,
                "from": sender_email,
                "date": date_formatted,
                "snippet": snippet,
                "body": body_content,
            }

        except Exception as e:
            logger.error(f"Error parsing Outlook email: {e}")
            return None

    async def _fetch_imap_emails_with_content(
        self, db: AsyncSession, connection: EmailConnection, limit: int, days_back: int
    ) -> List[Dict[str, Any]]:
        """Fetch emails with content from IMAP server"""
        import base64
        import email
        import imaplib
        import json
        from email.header import decode_header

        from app.services.email_connector_service import email_connector_service

        # Get IMAP connection details from connection_parameters JSON
        conn_params = connection.connection_parameters or {}

        # Extract IMAP settings with fallbacks
        imap_server = conn_params.get("server", "imap.gmail.com")
        imap_port = conn_params.get("port", 993)

        # Get password - multiple attempts
        password = None

        # Try 1: access_token_encrypted might be Base64-encoded JSON with credentials
        if connection.access_token_encrypted:
            try:
                decoded = base64.b64decode(connection.access_token_encrypted).decode(
                    "utf-8"
                )
                creds = json.loads(decoded)
                if isinstance(creds, dict) and "password" in creds:
                    password = creds["password"]
                    imap_server = creds.get("server", imap_server)
                    imap_port = creds.get("port", imap_port)
                    logger.info(
                        f"Extracted IMAP credentials from access_token_encrypted"
                    )
            except:
                # Not Base64 JSON, try normal decryption
                try:
                    password = email_connector_service.decrypt_token(
                        connection.access_token_encrypted
                    )
                    logger.info(f"Decrypted IMAP password using cipher_suite")
                except:
                    pass

        # Try 2: connection_parameters
        if not password and conn_params:
            password = conn_params.get("password", "")
            imap_server = conn_params.get("server", imap_server)
            imap_port = conn_params.get("port", imap_port)

        if not password:
            logger.error(
                f"No password found for IMAP connection {connection.email_address}"
            )
            return []

        logger.info(
            f"Connecting to IMAP server {imap_server}:{imap_port} for {connection.email_address}"
        )

        emails = []

        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)

            # Use username from connection_parameters if available, otherwise use email_address
            username = conn_params.get("username", connection.email_address)

            logger.info(f"Attempting IMAP login for {username}")

            # Normalize Unicode characters in credentials to handle non-ASCII characters
            # This fixes issues with passwords containing special characters like \xa0 (non-breaking space)
            normalized_username = unicodedata.normalize("NFKC", username)
            normalized_password = unicodedata.normalize("NFKC", password)

            mail.login(normalized_username, normalized_password)
            mail.select("INBOX")

            # Calculate date filter
            since_date = (datetime.utcnow() - timedelta(days=days_back)).strftime(
                "%d-%b-%Y"
            )

            logger.info(
                f"IMAP login successful, searching for emails since {since_date}"
            )

            # Search for emails since date
            status, messages = mail.search(None, f'(SINCE "{since_date}")')

            if status != "OK":
                logger.error(f"IMAP search failed for {connection.email_address}")
                return []

            # Get message IDs
            email_ids = messages[0].split()

            # Process emails (most recent first)
            for email_id in reversed(email_ids[-limit:]):
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, "(RFC822)")

                    if status != "OK":
                        continue

                    # Parse email
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    # Extract headers
                    subject = ""
                    if msg["Subject"]:
                        decoded_subject = decode_header(msg["Subject"])[0][0]
                        if isinstance(decoded_subject, bytes):
                            subject = decoded_subject.decode("utf-8", errors="ignore")
                        else:
                            subject = decoded_subject

                    # Filter out privacy-sensitive emails
                    privacy_keywords = [
                        "private",
                        "confidential",
                        "password",
                        "secret",
                        "personal",
                        "salary",
                        "ssn",
                        "social security",
                    ]
                    subject_lower = subject.lower()
                    if any(kw in subject_lower for kw in privacy_keywords):
                        continue

                    # Get sender
                    sender = msg.get("From", "")

                    # Get date
                    date_str = msg.get("Date", "")
                    try:
                        from dateutil import parser as date_parser

                        date_sent = date_parser.parse(date_str)
                        date_formatted = date_sent.strftime("%Y-%m-%d")
                    except:
                        date_formatted = datetime.utcnow().strftime("%Y-%m-%d")

                    # Extract email body
                    body_content = self._extract_imap_body(msg)

                    # Truncate if too long
                    if len(body_content) > self.max_content_length:
                        body_content = body_content[: self.max_content_length] + "..."

                    # Create snippet
                    snippet = (
                        body_content[:100] + "..."
                        if len(body_content) > 100
                        else body_content
                    )

                    # Extract sender email address
                    import re

                    sender_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", sender)
                    sender_email = sender_match.group() if sender_match else sender

                    emails.append(
                        {
                            "id": str(email_id.decode()),
                            "subject": subject,
                            "from": sender_email,
                            "date": date_formatted,
                            "snippet": snippet,
                            "body": body_content,
                        }
                    )

                except Exception as e:
                    logger.error(f"Error processing IMAP message {email_id}: {e}")
                    continue

            # Close connection
            mail.close()
            mail.logout()

            logger.info(f"Successfully fetched {len(emails)} emails from IMAP")

        except Exception as e:
            logger.error(
                f"IMAP connection error for {connection.email_address}: {e}",
                exc_info=True,
            )
            return []

        return emails

    def _extract_imap_body(self, msg) -> str:
        """Extract text body from IMAP email message"""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        # Try to decode the payload
                        charset = part.get_content_charset() or "utf-8"
                        body += payload.decode(charset, errors="ignore")
                except:
                    continue
        else:
            # Not multipart - get the payload directly
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="ignore")
            except:
                body = str(msg.get_payload())

        return body.strip()

    async def _get_sample_emails(self, page: int, limit: int) -> Dict[str, Any]:
        """Return sample emails for demonstration/testing"""
        sample_emails = [
            {
                "id": "sample-1",
                "subject": "Quarterly Performance Review",
                "from": "manager@company.com",
                "date": "2025-01-20",
                "snippet": "I wanted to discuss your performance over the last quarter...",
                "body": "I wanted to discuss your performance over the last quarter. You have shown excellent dedication and your team collaboration skills have improved significantly. However, there are some areas where we need to focus on time management and meeting deadlines. Let us schedule a meeting to discuss this further and create an action plan for your development.",
            },
            {
                "id": "sample-2",
                "subject": "Urgent: Project Deadline",
                "from": "client@business.com",
                "date": "2025-01-19",
                "snippet": "We need to move up the deadline by two weeks...",
                "body": "We need to move up the deadline by two weeks due to changing market conditions. I understand this is short notice and may cause stress, but we need your team to prioritize the critical features. Please let me know if this is feasible and what support you need.",
            },
            {
                "id": "sample-3",
                "subject": "Team Appreciation",
                "from": "hr@company.com",
                "date": "2025-01-18",
                "snippet": "Congratulations on the successful project launch!",
                "body": "Congratulations on the successful project launch! The entire team did an outstanding job. Your hard work, dedication, and collaborative spirit made this possible. We are proud to have such an amazing team and look forward to celebrating together at the upcoming team event.",
            },
            {
                "id": "sample-4",
                "subject": "Budget Concerns",
                "from": "finance@company.com",
                "date": "2025-01-17",
                "snippet": "We need to discuss the department budget cuts...",
                "body": "We need to discuss the department budget cuts. Unfortunately, we are facing financial constraints and need to reduce expenses by 15%. This is difficult news and I know it will impact the team. We should explore options together to minimize the impact on critical operations and team morale.",
            },
            {
                "id": "sample-5",
                "subject": "Meeting Request: Strategy Review",
                "from": "director@company.com",
                "date": "2025-01-16",
                "snippet": "Can we schedule a time to review Q1 strategy?",
                "body": "Hi, I'd like to schedule a meeting to review our Q1 strategy and make any necessary adjustments based on recent market changes. Please let me know your availability for this week. I think it's important we align our priorities and ensure everyone is on the same page moving forward.",
            },
            {
                "id": "sample-6",
                "subject": "Feedback on Proposal",
                "from": "stakeholder@partner.com",
                "date": "2025-01-15",
                "snippet": "Thank you for submitting the proposal...",
                "body": "Thank you for submitting the proposal. After reviewing it with our team, we have some questions and suggestions for improvement. Overall, we like the direction, but feel there are some areas that could be strengthened. Would you be available for a call to discuss our feedback?",
            },
            {
                "id": "sample-7",
                "subject": "System Outage Resolution",
                "from": "support@vendor.com",
                "date": "2025-01-14",
                "snippet": "We have resolved the system outage issue...",
                "body": "We have successfully resolved the system outage that affected your services earlier today. Our team identified the root cause and implemented a fix to prevent future occurrences. We sincerely apologize for any inconvenience this may have caused and appreciate your patience during the resolution process.",
            },
            {
                "id": "sample-8",
                "subject": "Project Update: Milestone Achieved",
                "from": "lead@company.com",
                "date": "2025-01-13",
                "snippet": "Great news! We've successfully completed Phase 2...",
                "body": "Great news! We've successfully completed Phase 2 of the project ahead of schedule. The team has put in tremendous effort and the quality of work has been exceptional. I want to personally thank everyone for their dedication. Let's keep this momentum going as we move into Phase 3!",
            },
            {
                "id": "sample-9",
                "subject": "Training Opportunity: Leadership Skills",
                "from": "learning@company.com",
                "date": "2025-01-12",
                "snippet": "New leadership development program starting next month...",
                "body": "We're excited to announce a new leadership development program starting next month. Based on your performance and potential, we think you'd be a great fit. The program includes workshops, mentorship, and hands-on projects to help you grow into leadership roles. Let us know if you're interested!",
            },
            {
                "id": "sample-10",
                "subject": "Customer Complaint Resolution",
                "from": "support@company.com",
                "date": "2025-01-11",
                "snippet": "Regarding the recent customer complaint...",
                "body": "I wanted to follow up on the customer complaint we received yesterday. After investigating the issue, it appears there was a misunderstanding on our end. I've personally reached out to the customer to apologize and resolve the matter. They're satisfied with the outcome and appreciative of our quick response.",
            },
            {
                "id": "sample-11",
                "subject": "Weekly Team Standup Notes",
                "from": "scrum master@company.com",
                "date": "2025-01-10",
                "snippet": "Summary of today's standup meeting...",
                "body": "Great progress on the sprint! Team A completed the backend API integration, Team B is finalizing the UI components, and Team B has started testing. We have two blockers that need attention: the database migration issue and the third-party API delay. Let's address these in tomorrow's planning session.",
            },
            {
                "id": "sample-12",
                "subject": "Invoice Submitted for Q4 Services",
                "from": "billing@vendor.com",
                "date": "2025-01-09",
                "snippet": "Please find attached invoice for services rendered...",
                "body": "Please find attached invoice for the consulting services provided in Q4. The total amount is $15,750 for 120 hours of work. Payment terms are net 30. If you have any questions about the charges or need additional documentation, please don't hesitate to reach out.",
            },
            {
                "id": "sample-13",
                "subject": "Holiday Schedule Announcement",
                "from": "hr@company.com",
                "date": "2025-01-08",
                "snippet": "Upcoming holiday office closure schedule...",
                "body": "Please note that our offices will be closed from December 23rd through January 2nd for the holiday season. All employees will receive paid time off during this period. Please plan your workload accordingly and set up appropriate out-of-office responses. Enjoy the break!",
            },
            {
                "id": "sample-14",
                "subject": "New Product Launch Planning",
                "from": "product@company.com",
                "date": "2025-01-07",
                "snippet": "Initial planning meeting for our spring product launch...",
                "body": "I'm excited to kick off our spring product launch planning! This is going to be our biggest launch yet. We need to coordinate marketing, sales, and customer support efforts. Please review the attached timeline and come prepared to discuss your team's role in making this a success.",
            },
            {
                "id": "sample-15",
                "subject": "Security Update Required",
                "from": "it@company.com",
                "date": "2025-01-06",
                "snippet": "Important: Update your password by end of week...",
                "body": "As part of our ongoing security enhancements, all employees must update their passwords by Friday. Please use the self-service portal to change your password. New requirements: minimum 12 characters, including uppercase, lowercase, numbers, and special characters. Thank you for helping keep our data secure!",
            },
            {
                "id": "sample-16",
                "subject": "Job Referral Bonus Program",
                "from": "recruiting@company.com",
                "date": "2025-01-05",
                "snippet": "Earn $2,000 for successful candidate referrals...",
                "body": "Our employee referral bonus program has been enhanced! You can now earn $2,000 for referring successful candidates for engineering positions, $1,500 for sales roles, and $1,000 for all other positions. Check out our open positions and help us build our amazing team!",
            },
            {
                "id": "sample-17",
                "subject": "Client Meeting Follow-up",
                "from": "account.executive@company.com",
                "date": "2025-01-04",
                "snippet": "Great meeting today! Next steps as discussed...",
                "body": "Thank you for the productive meeting today. As discussed, we'll send over the revised proposal by Wednesday, schedule a technical demo for next Monday, and aim to have the contract ready for review by the following week. I'm confident we can move forward quickly. Please let me know if you need anything else in the meantime.",
            },
            {
                "id": "sample-18",
                "subject": "Office Relocation Update",
                "from": "facilities@company.com",
                "date": "2025-01-03",
                "snippet": "Important updates about our upcoming office move...",
                "body": "I'm writing to share important updates about our office relocation next month. The new space will feature open collaboration areas, private phone booths, and a wellness room. Pack your personal items by January 20th. IT will handle all equipment relocation. We'll have a grand opening party on February 15th!",
            },
            {
                "id": "sample-19",
                "subject": "Performance Bonus Announcement",
                "from": "ceo@company.com",
                "date": "2025-01-02",
                "snippet": "Great news! Performance bonuses have been approved...",
                "body": "I'm thrilled to announce that due to our exceptional Q4 performance, all employees will receive a year-end bonus! Full-time employees will get 15% of their annual salary, part-time employees will receive 8%. Bonuses will be included in your January 31st paycheck. Thank you for your incredible work this year!",
            },
            {
                "id": "sample-20",
                "subject": "Sick Leave Policy Update",
                "from": "hr@company.com",
                "date": "2025-01-01",
                "snippet": "Updated sick leave policy effective immediately...",
                "body": "We're updating our sick leave policy to better support employee wellbeing. Effective immediately, all employees now have 10 paid sick days per year (up from 5). These days can also be used to care for family members. No doctor's note required for absences under 3 days. We value your health!",
            },
            {
                "id": "sample-21",
                "subject": "Team Building Event Next Friday",
                "from": "events@company.com",
                "date": "2024-12-31",
                "snippet": "Join us for an afternoon of fun activities...",
                "body": "You're invited to our team building event next Friday afternoon! We'll have escape rooms, a cooking competition, and games. Food and drinks will be provided. It's a great opportunity to relax and connect with colleagues outside of work. RSVP by Wednesday so we can finalize numbers!",
            },
            {
                "id": "sample-22",
                "subject": "Quarterly Goals Review",
                "from": "manager@company.com",
                "date": "2024-12-30",
                "snippet": "Let's review our Q4 goals and set Q1 objectives...",
                "body": "As we wrap up Q4, I'd like to review our team goals and set objectives for Q1. Please come prepared to share your reflections on what went well, what didn't, and what you'd like to focus on next quarter. I want to ensure everyone feels aligned and supported in their professional growth.",
            },
            {
                "id": "sample-23",
                "subject": "Software License Renewal",
                "from": "procurement@company.com",
                "date": "2024-12-29",
                "snippet": "Action required: Approve software license renewals...",
                "body": "Our annual software license renewals are due for approval. The total cost is $45,000 for various tools including our project management software, design tools, and communication platform. Please review the attached list and confirm which licenses your team still needs. We're looking for opportunities to optimize costs.",
            },
            {
                "id": "sample-24",
                "subject": "New Employee Orientation Schedule",
                "from": "onboarding@company.com",
                "date": "2024-12-28",
                "snippet": "Welcome aboard! Your first week schedule...",
                "body": "Welcome to the team! We're excited to have you join us. Your first week includes: Monday - HR orientation and setup, Tuesday - Team introductions and tool training, Wednesday - Project overview and mentor pairing, Thursday - Shadow sessions, Friday - Check-in with manager. Let's make this a great start!",
            },
            {
                "id": "sample-25",
                "subject": "Remote Work Policy Update",
                "from": "hr@company.com",
                "date": "2024-12-27",
                "snippet": "Updates to our flexible work arrangement policy...",
                "body": "We're enhancing our remote work policy! Starting January 1st, employees can work remotely up to 3 days per week (up from 2). We've also added a $500 home office stipend for equipment. Full details are in the attached policy document. We believe flexibility leads to better work-life balance and productivity.",
            },
            {
                "id": "sample-26",
                "subject": "Customer Testimonial Request",
                "from": "marketing@company.com",
                "date": "2024-12-26",
                "snippet": "Would you be willing to provide a testimonial?",
                "body": "We're updating our website with customer success stories and thought you might have some happy clients who would provide testimonials. If you can identify 2-3 customers who've had great results, please reach out and ask if they'd be willing to share their experience. We'd really appreciate your help!",
            },
            {
                "id": "sample-27",
                "subject": "Year-End Party Planning",
                "from": "social.committee@company.com",
                "date": "2024-12-25",
                "snippet": "Help us plan the annual celebration!",
                "body": "It's time to plan our year-end celebration party! We're looking at a few venues and would love your input. Options include: a rooftop venue with city views, a cozy restaurant with private dining, or a party at a local brewery. Please vote in the attached poll by end of week. Can't wait to celebrate together!",
            },
            {
                "id": "sample-28",
                "subject": "Code Review Required",
                "from": "tech.lead@company.com",
                "date": "2024-12-24",
                "snippet": "PR #1234 ready for review - Features new dashboard...",
                "body": "PR #1234 is ready for your review. This PR implements the new analytics dashboard we've been planning. Key changes include real-time data visualization, customizable widgets, and export functionality. The code is well-documented and tests have been added. Please review by end of week so we can merge before the holidays.",
            },
            {
                "id": "sample-29",
                "subject": "Mentorship Program Enrollment",
                "from": "l&d@company.com",
                "date": "2024-12-23",
                "snippet": "Sign up to be a mentor or mentee this quarter...",
                "body": "Our mentorship program is accepting new enrollments! Whether you want to mentor someone and share your expertise, or you're looking to learn from a senior colleague, this is a great opportunity for growth. The program runs for 3 months with monthly check-ins. Sign up by Friday!",
            },
            {
                "id": "sample-30",
                "subject": "Budget Approval Received",
                "from": "finance@company.com",
                "date": "2024-12-22",
                "snippet": "Great news! Your Q1 budget request has been approved...",
                "body": "I'm pleased to inform you that your budget request for Q1 projects has been fully approved! The $75,000 will support your planned initiatives including the new hire, equipment upgrades, and training programs. Funds will be available starting January 2nd. Please submit your procurement requests accordingly.",
            },
        ]

        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_emails = sample_emails[start_idx:end_idx]

        return {
            "emails": paginated_emails,
            "total": len(sample_emails),
            "page": page,
            "limit": limit,
        }

    async def _get_from_cache(self, key: str) -> Optional[str]:
        """Get emails from Redis cache"""
        try:
            redis = await get_redis_client()
            if redis:
                cached = await redis.get(key)
                if cached:
                    return cached
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        return None

    async def _cache_emails(self, key: str, emails: List[Dict]) -> None:
        """Cache emails in Redis"""
        try:
            redis = await get_redis_client()
            if redis:
                await redis.setex(key, self.cache_ttl, json.dumps(emails))
                logger.info(f"Cached {len(emails)} emails with key {key}")
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")


# Global service instance
email_content_service = EmailContentService()
