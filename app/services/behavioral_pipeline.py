# app/services/behavioral_pipeline.py
"""
Unified Behavioral Signal Processing Pipeline
Orchestrates data extraction from all integrations and generates insights
"""

import logging
from typing import Dict, List, Any, Optional, Type
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.email_integration import (
    EmailMetadataExtractor,
    GmailAPIIntegration,
    OutlookAPIIntegration,
    EmailMetadata
)
from app.integrations.calendar_integration import (
    CalendarMetadataExtractor,
    GoogleCalendarAPIIntegration,
    OutlookCalendarAPIIntegration,
    CalendarEvent
)
from app.integrations.slack_integration import (
    SlackMetadataExtractor,
    SlackAPIIntegration,
    SlackMessage
)

logger = logging.getLogger(__name__)


class InsightCategory(Enum):
    """Categories of behavioral insights"""
    BURNOUT = "burnout"
    TOXICITY = "toxicity"
    ENGAGEMENT = "engagement"
    RETENTION = "retention"
    LEADERSHIP = "leadership"
    COLLABORATION = "collaboration"
    WORK_LIFE_BALANCE = "work_life_balance"


class InsightSeverity(Enum):
    """Severity levels for insights"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BehavioralInsight:
    """A behavioral insight derived from data"""
    category: InsightCategory
    severity: InsightSeverity
    title: str
    description: str
    affected_user_id: Optional[int]
    confidence: float  # 0-1
    detected_at: datetime
    data_sources: List[str]
    indicators: List[str]
    recommendations: List[str]
    signal_values: Dict[str, float]


@dataclass
class BehavioralProfile:
    """Comprehensive behavioral profile for a user"""
    user_id: int
    organization_id: int
    profile_date: datetime
    time_window_days: int

    # Risk scores
    burnout_risk_score: float  # 0-1
    toxicity_exposure_score: float  # 0-1
    engagement_score: float  # 0-1
    retention_risk_score: float  # 0-1
    work_life_balance_score: float  # 0-1

    # Behavioral signals by data source
    email_signals: Dict[str, Any]
    calendar_signals: Dict[str, Any]
    slack_signals: Dict[str, Any]

    # Insights generated
    insights: List[BehavioralInsight]

    # Metadata
    data_sources_active: List[str]
    confidence_level: float  # 0-1


class BehavioralPipelineOrchestrator:
    """
    Orchestrates data extraction and analysis across all integrations
    """

    def __init__(self, db: AsyncSession, organization_domain: str):
        self.db = db
        self.organization_domain = organization_domain

        # Initialize extractors
        self.email_extractor = EmailMetadataExtractor(db, organization_domain)
        self.calendar_extractor = CalendarMetadataExtractor(organization_domain)
        self.slack_extractor = SlackMetadataExtractor()

    async def generate_behavioral_profile(
        self,
        user_id: int,
        organization_id: int,
        credentials: Dict[str, Dict[str, str]],
        time_window_days: int = 30
    ) -> BehavioralProfile:
        """
        Generate comprehensive behavioral profile for a user

        Args:
            user_id: User ID
            organization_id: Organization ID
            credentials: Dict mapping service names to their credentials
                e.g., {'gmail': {'access_token': '...'}, 'slack': {'bot_token': '...'}}
            time_window_days: Time window for analysis

        Returns:
            BehavioralProfile object
        """
        logger.info(f"Generating behavioral profile for user {user_id}")

        # Extract data from all available sources
        all_signals = {}
        data_sources_active = []
        insights = []

        # Email integration
        if 'gmail' in credentials or 'outlook' in credentials:
            try:
                email_signals, email_insights = await self._process_email_data(
                    user_id, organization_id, credentials, time_window_days
                )
                all_signals['email'] = email_signals
                insights.extend(email_insights)
                data_sources_active.append('email')
            except Exception as e:
                logger.error(f"Error processing email data: {e}")

        # Calendar integration
        if 'google_calendar' in credentials or 'outlook_calendar' in credentials:
            try:
                calendar_signals, calendar_insights = await self._process_calendar_data(
                    user_id, organization_id, credentials, time_window_days
                )
                all_signals['calendar'] = calendar_signals
                insights.extend(calendar_insights)
                data_sources_active.append('calendar')
            except Exception as e:
                logger.error(f"Error processing calendar data: {e}")

        # Slack integration
        if 'slack' in credentials:
            try:
                slack_signals, slack_insights = await self._process_slack_data(
                    user_id, organization_id, credentials, time_window_days
                )
                all_signals['slack'] = slack_signals
                insights.extend(slack_insights)
                data_sources_active.append('slack')
            except Exception as e:
                logger.error(f"Error processing Slack data: {e}")

        # Calculate aggregate risk scores
        burnout_risk = self._calculate_burnout_risk(all_signals)
        toxicity_exposure = self._calculate_toxicity_exposure(all_signals)
        engagement = self._calculate_engagement(all_signals)
        retention_risk = self._calculate_retention_risk(all_signals)
        work_life_balance = self._calculate_work_life_balance(all_signals)

        # Calculate confidence level based on data sources
        confidence_level = len(data_sources_active) / 3.0  # Max 3 sources

        return BehavioralProfile(
            user_id=user_id,
            organization_id=organization_id,
            profile_date=datetime.utcnow(),
            time_window_days=time_window_days,
            burnout_risk_score=burnout_risk,
            toxicity_exposure_score=toxicity_exposure,
            engagement_score=engagement,
            retention_risk_score=retention_risk,
            work_life_balance_score=work_life_balance,
            email_signals=all_signals.get('email', {}),
            calendar_signals=all_signals.get('calendar', {}),
            slack_signals=all_signals.get('slack', {}),
            insights=insights,
            data_sources_active=data_sources_active,
            confidence_level=confidence_level
        )

    async def _process_email_data(
        self,
        user_id: int,
        organization_id: int,
        credentials: Dict[str, Dict[str, str]],
        time_window_days: int
    ) -> tuple[Dict[str, Any], List[BehavioralInsight]]:
        """Process email data and extract signals"""
        emails = []
        access_token = None
        platform = None

        # Determine platform and get token
        if 'gmail' in credentials:
            access_token = credentials['gmail']['access_token']
            platform = 'gmail'
        elif 'outlook' in credentials:
            access_token = credentials['outlook']['access_token']
            platform = 'outlook'

        if not access_token:
            return {}, []

        # Fetch emails
        if platform == 'gmail':
            gmail_integration = GmailAPIIntegration(access_token)
            raw_emails = await gmail_integration.fetch_recent_emails(days=time_window_days)

            for raw_email in raw_emails:
                email_metadata = self.email_extractor.extract_from_gmail_message(
                    raw_email, user_id, 0, organization_id  # TODO: Get connection_id
                )
                emails.append(email_metadata)

        elif platform == 'outlook':
            outlook_integration = OutlookAPIIntegration(access_token)
            raw_emails = await outlook_integration.fetch_recent_emails(days=time_window_days)

            for raw_email in raw_emails:
                email_metadata = self.email_extractor.extract_from_outlook_message(
                    raw_email, user_id, 0, organization_id
                )
                emails.append(email_metadata)

        # Calculate signals
        signals = self.email_extractor.calculate_behavioral_signals(emails, time_window_days)

        # Generate insights
        insights = []
        burnout_indicators = self.email_extractor.detect_burnout_indicators(signals)

        if burnout_indicators:
            insights.append(BehavioralInsight(
                category=InsightCategory.BURNOUT,
                severity=self._determine_severity(burnout_indicators, 5),
                title="Email-Based Burnout Risk Detected",
                description="Analysis of email patterns reveals potential burnout risk factors",
                affected_user_id=user_id,
                confidence=0.8,
                detected_at=datetime.utcnow(),
                data_sources=['email'],
                indicators=burnout_indicators,
                recommendations=[
                    "Establish clear email communication hours",
                    "Disable email notifications outside work hours",
                    "Take regular breaks from email checking"
                ],
                signal_values=signals
            ))

        return signals, insights

    async def _process_calendar_data(
        self,
        user_id: int,
        organization_id: int,
        credentials: Dict[str, Dict[str, str]],
        time_window_days: int
    ) -> tuple[Dict[str, Any], List[BehavioralInsight]]:
        """Process calendar data and extract signals"""
        events = []
        access_token = None
        platform = None

        if 'google_calendar' in credentials:
            access_token = credentials['google_calendar']['access_token']
            platform = 'google'
        elif 'outlook_calendar' in credentials:
            access_token = credentials['outlook_calendar']['access_token']
            platform = 'outlook'

        if not access_token:
            return {}, []

        # Fetch events
        if platform == 'google':
            calendar_integration = GoogleCalendarAPIIntegration(access_token)
            raw_events = await calendar_integration.fetch_events(days=time_window_days)

            # Get user email (TODO: from database)
            user_email = "user@example.com"

            for raw_event in raw_events:
                event_metadata = self.calendar_extractor.extract_from_google_event(
                    raw_event, user_email, user_id, 0, organization_id
                )
                if event_metadata:
                    events.append(event_metadata)

        elif platform == 'outlook':
            calendar_integration = OutlookCalendarAPIIntegration(access_token)
            raw_events = await calendar_integration.fetch_events(days=time_window_days)

            user_email = "user@example.com"

            for raw_event in raw_events:
                event_metadata = self.calendar_extractor.extract_from_outlook_event(
                    raw_event, user_email, user_id, 0, organization_id
                )
                if event_metadata:
                    events.append(event_metadata)

        # Calculate signals
        signals = self.calendar_extractor.calculate_behavioral_signals(events, time_window_days)

        # Generate insights
        insights = []
        burnout_indicators = self.calendar_extractor.detect_burnout_indicators(signals)

        if burnout_indicators:
            insights.append(BehavioralInsight(
                category=InsightCategory.WORK_LIFE_BALANCE,
                severity=self._determine_severity(burnout_indicators, 4),
                title="Calendar-Based Work-Life Imbalance Detected",
                description="Analysis of calendar patterns reveals work-life balance concerns",
                affected_user_id=user_id,
                confidence=0.85,
                detected_at=datetime.utcnow(),
                data_sources=['calendar'],
                indicators=burnout_indicators,
                recommendations=[
                    "Block focus time in calendar",
                    "Decline non-essential meetings",
                    "Schedule breaks between back-to-back meetings"
                ],
                signal_values=signals
            ))

        return signals, insights

    async def _process_slack_data(
        self,
        user_id: int,
        organization_id: int,
        credentials: Dict[str, Dict[str, str]],
        time_window_days: int
    ) -> tuple[Dict[str, Any], List[BehavioralInsight]]:
        """Process Slack data and extract signals"""
        bot_token = credentials.get('slack', {}).get('bot_token')

        if not bot_token:
            return {}, []

        # Fetch messages
        slack_integration = SlackAPIIntegration(bot_token)
        all_messages = await slack_integration.fetch_all_messages(days=time_window_days)

        # Extract metadata
        messages = []
        for channel_id, channel_messages in all_messages.items():
            channel_name = f"channel_{channel_id}"  # TODO: Get actual channel name
            for raw_msg in channel_messages:
                msg_metadata = self.slack_extractor.extract_from_slack_message(
                    raw_msg, channel_name, str(user_id), 0, organization_id
                )
                if msg_metadata:
                    messages.append(msg_metadata)

        # Filter messages for this user
        user_messages = [m for m in messages if m.user_id == str(user_id)]

        # Calculate signals
        signals = self.slack_extractor.calculate_behavioral_signals(user_messages, time_window_days)

        # Generate insights
        insights = []
        burnout_indicators = self.slack_extractor.detect_burnout_indicators(signals)

        if burnout_indicators:
            insights.append(BehavioralInsight(
                category=InsightCategory.COLLABORATION,
                severity=self._determine_severity(burnout_indicators, 4),
                title="Slack Activity Pattern Concerns",
                description="Analysis of Slack communication patterns reveals potential issues",
                affected_user_id=user_id,
                confidence=0.75,
                detected_at=datetime.utcnow(),
                data_sources=['slack'],
                indicators=burnout_indicators,
                recommendations=[
                    "Set Slack notification boundaries",
                    "Encourage use of status indicators",
                    "Promote digital wellness practices"
                ],
                signal_values=signals
            ))

        return signals, insights

    def _calculate_burnout_risk(self, all_signals: Dict[str, Dict]) -> float:
        """Calculate aggregate burnout risk score (0-1)"""
        risk_factors = []

        email_signals = all_signals.get('email', {})
        if email_signals.get('work_life_imbalance_score', 0) > 0.7:
            risk_factors.append(0.3)
        if email_signals.get('communication_overload', False):
            risk_factors.append(0.2)

        calendar_signals = all_signals.get('calendar', {})
        if calendar_signals.get('meeting_load_percentage', 0) > 80:
            risk_factors.append(0.3)
        if calendar_signals.get('focus_time_hours_per_day', 0) < 1:
            risk_factors.append(0.2)

        slack_signals = all_signals.get('slack', {})
        if slack_signals.get('burnout_risk_score', 0) > 0.5:
            risk_factors.append(0.3)

        return min(sum(risk_factors), 1.0)

    def _calculate_toxicity_exposure(self, all_signals: Dict[str, Dict]) -> float:
        """Calculate aggregate toxicity exposure score (0-1)"""
        # Email conflict indicators
        email_signals = all_signals.get('email', {})
        toxicity_score = 0.0

        if email_signals.get('urgent_emails_count', 0) > 20:
            toxicity_score += 0.3

        # Slack negative sentiment
        slack_signals = all_signals.get('slack', {})
        if slack_signals.get('negative_emoji_percentage', 0) > 30:
            toxicity_score += 0.3

        return min(toxicity_score, 1.0)

    def _calculate_engagement(self, all_signals: Dict[str, Dict]) -> float:
        """Calculate aggregate engagement score (0-1, higher is better)"""
        engagement_score = 0.7  # Base score

        slack_signals = all_signals.get('slack', {})
        if slack_signals.get('social_interaction_score', 0) > 0.6:
            engagement_score += 0.2

        calendar_signals = all_signals.get('calendar', {})
        if calendar_signals.get('one_on_one_frequency', 0) > 0.5:
            engagement_score += 0.1

        return min(engagement_score, 1.0)

    def _calculate_retention_risk(self, all_signals: Dict[str, Dict]) -> float:
        """Calculate aggregate retention risk score (0-1)"""
        risk_score = 0.0

        # Burnout is a major retention risk factor
        burnout_risk = self._calculate_burnout_risk(all_signals)
        risk_score += burnout_risk * 0.5

        # Low engagement increases retention risk
        engagement = self._calculate_engagement(all_signals)
        risk_score += (1.0 - engagement) * 0.3

        # Work-life imbalance
        wlb_score = all_signals.get('calendar', {}).get('meeting_load_percentage', 0) / 100.0
        risk_score += wlb_score * 0.2

        return min(risk_score, 1.0)

    def _calculate_work_life_balance(self, all_signals: Dict[str, Dict]) -> float:
        """Calculate work-life balance score (0-1, higher is better)"""
        balance_score = 0.5  # Base score

        email_signals = all_signals.get('email', {})
        imbalance = email_signals.get('work_life_imbalance_score', 0)
        balance_score -= imbalance * 0.3

        calendar_signals = all_signals.get('calendar', {})
        after_hours = calendar_signals.get('after_hours_meetings_count', 0) / 10.0  # Normalize
        balance_score -= min(after_hours, 0.3)

        weekend_work = calendar_signals.get('weekend_meetings_count', 0) / 10.0
        balance_score -= min(weekend_work, 0.2)

        return max(0.0, min(balance_score, 1.0))

    def _determine_severity(self, indicators: List[str], critical_threshold: int) -> InsightSeverity:
        """Determine insight severity based on number of indicators"""
        count = len(indicators)

        if count >= critical_threshold:
            return InsightSeverity.CRITICAL
        elif count >= critical_threshold - 1:
            return InsightSeverity.HIGH
        elif count >= 2:
            return InsightSeverity.MEDIUM
        else:
            return InsightSeverity.LOW


# Export
__all__ = [
    'BehavioralPipelineOrchestrator',
    'BehavioralProfile',
    'BehavioralInsight',
    'InsightCategory',
    'InsightSeverity'
]
