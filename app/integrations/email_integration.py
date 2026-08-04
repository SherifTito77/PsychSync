# app/integrations/email_integration.py
"""
Email Metadata Integration
Connects to Gmail/Outlook APIs to extract behavioral signals
PRIVACY-ONLY: No message content stored, only metadata patterns
"""

import base64
import email
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from email.header import decode_header
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class EmailMetadata:
    """Email metadata record (no content stored)"""

    message_id: str
    thread_id: str
    sender: str  # Email address only
    recipients: List[str]  # Email addresses only
    cc_recipients: List[str]
    bcc_recipients: List[str]
    subject_length: int
    sent_at: datetime
    received_at: Optional[datetime]
    has_attachments: bool
    attachment_count: int
    is_external: bool  # Outside organization
    is_urgent: bool  # Urgency keywords in subject
    urgency_level: str  # 'low', 'medium', 'high', 'critical'
    thread_size: int  # Messages in thread
    in_reply_to: Optional[str]
    message_count_in_thread: int
    response_time_seconds: Optional[float]  # Time to respond

    # Behavioral flags
    is_after_hours: bool
    is_weekend: bool
    hour_of_day: int  # 0-23
    day_of_week: int  # 0-6 (Mon-Sun)

    # Organization
    organization_id: int
    user_id: int
    connection_id: int


class EmailMetadataExtractor:
    """
    Extract behavioral signals from email metadata
    PRIVACY-FOCUSED: Never stores message body or content
    """

    # Urgency keywords for subject line analysis
    URGENCY_KEYWORDS = {
        "critical": ["urgent", "asap", "emergency", "critical", "immediate"],
        "high": ["important", "priority", "deadline", "rush", "hurry"],
        "medium": ["please", "kindly", "request", "needed", "review"],
    }

    # Work hours definition
    WORK_HOURS_START = 9  # 9 AM
    WORK_HOURS_END = 18  # 6 PM
    WORK_DAYS = [0, 1, 2, 3, 4]  # Mon-Fri

    def __init__(self, db: AsyncSession, organization_domain: str):
        self.db = db
        self.organization_domain = organization_domain

    def extract_from_gmail_message(
        self,
        message_data: Dict[str, Any],
        user_id: int,
        connection_id: int,
        organization_id: int,
    ) -> EmailMetadata:
        """
        Extract metadata from Gmail API message

        Args:
            message_data: Gmail API message object
            user_id: User ID
            connection_id: Email connection ID
            organization_id: Organization ID

        Returns:
            EmailMetadata object
        """
        try:
            # Extract message headers
            headers = {
                h["name"]: h["value"] for h in message_data["payload"]["headers"]
            }

            # Parse timestamps
            internal_date = int(message_data["internalDate"])
            sent_at = datetime.fromtimestamp(internal_date / 1000)

            # Extract sender
            sender = headers.get("From", "")
            sender_email = self._extract_email(sender)

            # Extract recipients
            to_emails = self._extract_emails(headers.get("To", ""))
            cc_emails = self._extract_emails(headers.get("Cc", ""))
            bcc_emails = self._extract_emails(headers.get("Bcc", ""))

            # Subject analysis
            subject = headers.get("Subject", "")
            subject_length = len(subject)

            # Determine urgency from subject
            urgency_level, is_urgent = self._analyze_urgency(subject)

            # Attachment analysis
            attachments = message_data["payload"].get("parts", [])
            has_attachments = "attachmentId" in str(attachments)
            attachment_count = len([p for p in attachments if p.get("filename")])

            # Thread information
            thread_id = message_data["threadId"]
            thread_size = int(message_data.get("historyId", 1))

            # Reply-to information
            in_reply_to = headers.get("In-Reply-To", "")
            references = headers.get("References", "")

            # Behavioral flags
            is_after_hours = (
                sent_at.hour < self.WORK_HOURS_START
                or sent_at.hour >= self.WORK_HOURS_END
            )
            is_weekend = sent_at.weekday() >= 5

            # External communication check
            is_external = not self._is_internal_domain(sender_email)

            return EmailMetadata(
                message_id=message_data["id"],
                thread_id=thread_id,
                sender=sender_email,
                recipients=to_emails,
                cc_recipients=cc_emails,
                bcc_recipients=bcc_emails,
                subject_length=subject_length,
                sent_at=sent_at,
                received_at=sent_at,  # Gmail doesn't separate receive time
                has_attachments=has_attachments,
                attachment_count=attachment_count,
                is_external=is_external,
                is_urgent=is_urgent,
                urgency_level=urgency_level,
                thread_size=thread_size,
                in_reply_to=in_reply_to,
                message_count_in_thread=1,  # Will be calculated when processing full thread
                response_time_seconds=None,  # Will be calculated in post-processing
                is_after_hours=is_after_hours,
                is_weekend=is_weekend,
                hour_of_day=sent_at.hour,
                day_of_week=sent_at.weekday(),
                organization_id=organization_id,
                user_id=user_id,
                connection_id=connection_id,
            )

        except Exception as e:
            logger.error(f"Error extracting Gmail metadata: {e}")
            raise

    def extract_from_outlook_message(
        self,
        message_data: Dict[str, Any],
        user_id: int,
        connection_id: int,
        organization_id: int,
    ) -> EmailMetadata:
        """
        Extract metadata from Microsoft Graph API (Outlook) message

        Args:
            message_data: Microsoft Graph message object
            user_id: User ID
            connection_id: Email connection ID
            organization_id: Organization ID

        Returns:
            EmailMetadata object
        """
        try:
            # Parse timestamps
            sent_at = datetime.fromisoformat(
                message_data["sentDateTime"].replace("Z", "+00:00")
            )
            received_at = datetime.fromisoformat(
                message_data["receivedDateTime"].replace("Z", "+00:00")
            )

            # Extract sender
            sender_email = message_data["from"]["emailAddress"]["address"]

            # Extract recipients
            to_emails = [
                r["emailAddress"]["address"]
                for r in message_data.get("toRecipients", [])
            ]
            cc_emails = [
                r["emailAddress"]["address"]
                for r in message_data.get("ccRecipients", [])
            ]
            bcc_emails = [
                r["emailAddress"]["address"]
                for r in message_data.get("bccRecipients", [])
            ]

            # Subject analysis
            subject = message_data.get("subject", "")
            subject_length = len(subject)

            # Determine urgency
            urgency_level, is_urgent = self._analyze_urgency(subject)

            # Attachments
            has_attachments = message_data.get("hasAttachments", False)
            attachment_count = len(message_data.get("attachments", []))

            # Thread/conversation information
            thread_id = message_data.get("conversationId", message_data["id"])
            in_reply_to = message_data.get("inReplyTo", "")

            # Behavioral flags
            is_after_hours = (
                sent_at.hour < self.WORK_HOURS_START
                or sent_at.hour >= self.WORK_HOURS_END
            )
            is_weekend = sent_at.weekday() >= 5

            # External communication
            is_external = not self._is_internal_domain(sender_email)

            return EmailMetadata(
                message_id=message_data["id"],
                thread_id=thread_id,
                sender=sender_email,
                recipients=to_emails,
                cc_recipients=cc_emails,
                bcc_recipients=bcc_emails,
                subject_length=subject_length,
                sent_at=sent_at,
                received_at=received_at,
                has_attachments=has_attachments,
                attachment_count=attachment_count,
                is_external=is_external,
                is_urgent=is_urgent,
                urgency_level=urgency_level,
                thread_size=1,
                in_reply_to=in_reply_to,
                message_count_in_thread=1,
                response_time_seconds=None,
                is_after_hours=is_after_hours,
                is_weekend=is_weekend,
                hour_of_day=sent_at.hour,
                day_of_week=sent_at.weekday(),
                organization_id=organization_id,
                user_id=user_id,
                connection_id=connection_id,
            )

        except Exception as e:
            logger.error(f"Error extracting Outlook metadata: {e}")
            raise

    def calculate_behavioral_signals(
        self, emails: List[EmailMetadata], time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate behavioral signals from email metadata

        Args:
            emails: List of email metadata
            time_window_days: Time window for analysis

        Returns:
            Dictionary of behavioral signals
        """
        if not emails:
            return {}

        signals = {
            "communication_frequency": len(emails) / time_window_days,
            "avg_emails_per_day": len(emails) / time_window_days,
            "response_time_avg_hours": 0.0,
            "after_hours_percentage": 0.0,
            "weekend_work_percentage": 0.0,
            "urgent_emails_count": 0,
            "external_communication_percentage": 0.0,
            "thread_length_avg": 0.0,
            "attachment_frequency": 0.0,
            "hourly_distribution": [0] * 24,
            "daily_distribution": [0] * 7,
            "communication_overload": False,
            "work_life_imbalance_score": 0.0,
            "response_latency_distribution": {
                "very_fast": 0,  # < 15 min
                "fast": 0,  # 15-60 min
                "normal": 0,  # 1-4 hours
                "slow": 0,  # 4-24 hours
                "very_slow": 0,  # > 24 hours
            },
        }

        # Calculate various metrics
        after_hours_count = 0
        weekend_count = 0
        urgent_count = 0
        external_count = 0
        total_attachments = 0

        for email in emails:
            # Time-based metrics
            if email.is_after_hours:
                after_hours_count += 1
            if email.is_weekend:
                weekend_count += 1
            if email.is_urgent:
                urgent_count += 1
            if email.is_external:
                external_count += 1

            # Hourly distribution
            signals["hourly_distribution"][email.hour_of_day] += 1

            # Daily distribution
            signals["daily_distribution"][email.day_of_week] += 1

            # Attachments
            if email.has_attachments:
                total_attachments += email.attachment_count

        # Calculate percentages
        total = len(emails)
        signals["after_hours_percentage"] = (after_hours_count / total) * 100
        signals["weekend_work_percentage"] = (weekend_count / total) * 100
        signals["urgent_emails_count"] = urgent_count
        signals["external_communication_percentage"] = (external_count / total) * 100
        signals["attachment_frequency"] = total_attachments / total

        # Work-life imbalance score (0-1, higher is worse)
        imbalance = (
            (signals["after_hours_percentage"] / 100) * 0.4
            + (signals["weekend_work_percentage"] / 100) * 0.3
            + (min(signals["communication_frequency"] / 100, 1) * 0.3)
        )
        signals["work_life_imbalance_score"] = min(imbalance, 1.0)

        # Communication overload (>100 emails/day on average)
        signals["communication_overload"] = signals["avg_emails_per_day"] > 100

        # Thread length
        threads = {}
        for email in emails:
            if email.thread_id not in threads:
                threads[email.thread_id] = []
            threads[email.thread_id].append(email)

        thread_lengths = [len(thread_emails) for thread_emails in threads.values()]
        signals["thread_length_avg"] = (
            sum(thread_lengths) / len(thread_lengths) if thread_lengths else 0
        )

        return signals

    def detect_burnout_indicators(self, signals: Dict[str, Any]) -> List[str]:
        """
        Detect burnout risk indicators from email behavioral signals

        Args:
            signals: Behavioral signals dictionary

        Returns:
            List of detected burnout indicators
        """
        indicators = []

        # Check for excessive communication
        if signals.get("communication_frequency", 0) > 150:
            indicators.append("Excessive email volume (>150/day)")

        # Check for after-hours overload
        if signals.get("after_hours_percentage", 0) > 30:
            indicators.append("High after-hours email activity (>30%)")

        # Check for weekend work
        if signals.get("weekend_work_percentage", 0) > 20:
            indicators.append("Frequent weekend email activity (>20%)")

        # Check for constant urgency
        if signals.get("urgent_emails_count", 0) > 20:
            indicators.append("High urgency email volume (>20 in period)")

        # Check for work-life imbalance
        if signals.get("work_life_imbalance_score", 0) > 0.7:
            indicators.append("Severe work-life imbalance detected")

        # Check for communication overload
        if signals.get("communication_overload", False):
            indicators.append("Communication overload (>100 emails/day)")

        # Check for late-night patterns
        if signals.get("hourly_distribution"):
            late_night = sum(
                signals["hourly_distribution"][22:] + signals["hourly_distribution"][:6]
            )
            total = sum(signals["hourly_distribution"])
            if late_night / total > 0.15:
                indicators.append("Frequent late-night communication (10 PM - 6 AM)")

        return indicators

    def _analyze_urgency(self, subject: str) -> tuple:
        """
        Analyze email subject for urgency indicators

        Args:
            subject: Email subject line

        Returns:
            Tuple of (urgency_level, is_urgent)
        """
        subject_lower = subject.lower()

        # Check for critical urgency
        if any(
            keyword in subject_lower for keyword in self.URGENCY_KEYWORDS["critical"]
        ):
            return "critical", True

        # Check for high urgency
        if any(keyword in subject_lower for keyword in self.URGENCY_KEYWORDS["high"]):
            return "high", True

        # Check for medium urgency
        if any(keyword in subject_lower for keyword in self.URGENCY_KEYWORDS["medium"]):
            return "medium", False

        # Default to low urgency
        return "low", False

    def _extract_email(self, email_string: str) -> str:
        """Extract email address from email string"""
        if "<" in email_string and ">" in email_string:
            return email_string.split("<")[1].split(">")[0].strip()
        return email_string.strip()

    def _extract_emails(self, recipients_string: str) -> List[str]:
        """Extract list of email addresses from recipients string"""
        if not recipients_string:
            return []

        emails = []
        for part in recipients_string.split(","):
            email = self._extract_email(part.strip())
            if email and "@" in email:
                emails.append(email)

        return emails

    def _is_internal_domain(self, email: str) -> bool:
        """Check if email is from internal domain"""
        return email.endswith(f"@{self.organization_domain}")


class GmailAPIIntegration:
    """
    Gmail API integration for fetching email metadata
    """

    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://www.googleapis.com/gmail/v1/users/me"

    async def fetch_recent_emails(
        self, days: int = 7, max_results: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent emails from Gmail

        Args:
            days: Number of days to look back
            max_results: Maximum number of emails to fetch

        Returns:
            List of Gmail message objects
        """
        # Calculate date query
        from datetime import datetime, timedelta

        import httpx

        date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y/%m/%d")
        query = f"after:{date}"

        async with httpx.AsyncClient() as client:
            # Fetch message list
            response = await client.get(
                f"{self.base_url}/messages",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={"q": query, "maxResults": max_results},
            )
            response.raise_for_status()

            messages_data = response.json()
            messages = messages_data.get("messages", [])

            # Fetch full message details for each
            full_messages = []
            for msg in messages[:max_results]:
                response = await client.get(
                    f"{self.base_url}/messages/{msg['id']}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    params={
                        "format": "metadata",
                        "metadataHeaders": [
                            "From",
                            "To",
                            "Cc",
                            "Bcc",
                            "Subject",
                            "Date",
                            "In-Reply-To",
                            "References",
                        ],
                    },
                )
                response.raise_for_status()
                full_messages.append(response.json())

            return full_messages


class OutlookAPIIntegration:
    """
    Microsoft Graph API integration for Outlook email
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0/me"

    async def fetch_recent_emails(
        self, days: int = 7, max_results: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent emails from Outlook

        Args:
            days: Number of days to look back
            max_results: Maximum number of emails to fetch

        Returns:
            List of Outlook message objects
        """
        from datetime import datetime, timedelta

        import httpx

        date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/mailFolders/Inbox/messages",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={
                    "$filter": f"receivedDateTime ge {date}",
                    "$top": max_results,
                    "$select": "id,subject,from,toRecipients,ccRecipients,bccRecipients,sentDateTime,receivedDateTime,hasAttachments,attachments,inReplyTo,conversationId",
                },
            )
            response.raise_for_status()

            data = response.json()
            return data.get("value", [])


# Export
__all__ = [
    "EmailMetadataExtractor",
    "EmailMetadata",
    "GmailAPIIntegration",
    "OutlookAPIIntegration",
]
