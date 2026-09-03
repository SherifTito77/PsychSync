# app/integrations/slack_integration.py
"""
Slack Integration
Connects to Slack API to extract team communication behavioral signals
PRIVACY-FOCUSED: Analyzes patterns, not message content
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SlackMessage:
    """Slack message metadata (no content stored)"""
    message_id: str
    channel_id: str
    channel_name: str
    user_id: str
    timestamp: datetime
    message_type: str  # 'message', 'reply', 'thread_starter'
    reply_count: int  # Number of replies in thread
    reaction_count: int  # Number of reactions
    has_mentions: bool
    has_links: bool
    has_attachments: bool
    word_count: int
    emoji_count: int

    # Behavioral flags
    is_after_hours: bool
    is_weekend: bool
    hour_of_day: int
    day_of_week: int

    # User metadata
    organization_id: int
    connection_id: int


@dataclass
class SlackReaction:
    """Slack reaction metadata"""
    reaction_name: str  # e.g., 'thumbsup', 'joy', 'heart'
    count: int
    users: List[str]


class SlackMetadataExtractor:
    """
    Extract behavioral signals from Slack metadata
    PRIVACY-FOCUSED: Never stores message content, only patterns
    """

    # Work hours definition
    WORK_HOURS_START = 9
    WORK_HOURS_END = 18
    WORK_DAYS = [0, 1, 2, 3, 4]

    # Emoji categories for sentiment analysis
    POSITIVE_EMOJIS = [
        'thumbsup', 'thumbsup_all', 'thumbs_all', '+1', 'heavy_check_mark',
        'white_check_mark', 'joy', 'smile', 'smiley', 'grin', 'laughing',
        'heart', 'heart_eyes', 'star', 'clap', 'tada', 'raised_hands',
        '100', 'ok_hand', 'muscle', 'fire', 'rocket', 'sparkles'
    ]

    NEGATIVE_EMOJIS = [
        'thumbsdown', 'thumbsdown_all', '-1', 'x', 'heavy_multiplication_x',
        'cry', 'sob', 'disappointed', 'worried', 'frowning', 'angry',
        'rage', 'sick', 'face_with_thermometer', 'warning', 'no_entry'
    ]

    STRESS_INDICATOR_EMOJIS = [
        'scream', 'exploding_head', 'dizzy_face', 'cold_sweat', 'anxious',
        'sweat', 'tired_face', 'weary', 'sleeping', 'zzz', 'hourglass',
        'alarm_clock', 'exclamation', 'grey_exclamation', 'bangbang'
    ]

    def __init__(self):
        pass

    def extract_from_slack_message(
        self,
        message_data: Dict[str, Any],
        channel_name: str,
        user_id: str,
        connection_id: int,
        organization_id: int
    ) -> Optional[SlackMessage]:
        """
        Extract metadata from Slack API message

        Args:
            message_data: Slack API message object
            channel_name: Channel name
            user_id: User ID
            connection_id: Slack connection ID
            organization_id: Organization ID

        Returns:
            SlackMessage object or None (if not a user message)
        """
        try:
            # Skip bot messages and messages without user
            if message_data.get('subtype') in ['bot_message', 'message_changed']:
                return None

            if 'user' not in message_data:
                return None

            # Parse timestamp
            timestamp = datetime.fromtimestamp(float(message_data['ts']))

            # Determine message type
            thread_ts = message_data.get('thread_ts')
            message_type = 'thread_starter' if thread_ts == message_data['ts'] else 'reply'
            if not thread_ts:
                message_type = 'message'

            # Extract reactions
            reactions = message_data.get('reactions', [])
            reaction_count = sum(r.get('count', 0) for r in reactions)

            # Check for mentions
            text = message_data.get('text', '')
            has_mentions = bool(re.search(r'<@[A-Z0-9]+>', text))

            # Check for links and attachments
            has_links = 'blocks' in message_data or '<http' in text
            has_attachments = 'files' in message_data

            # Count words and emojis
            word_count = len(text.split())
            emoji_count = len(re.findall(r':[a-zA-Z0-9_+-]+:', text))

            # Reply count (if thread starter)
            reply_count = message_data.get('reply_count', 0)

            # Behavioral flags
            is_after_hours = timestamp.hour < self.WORK_HOURS_START or timestamp.hour >= self.WORK_HOURS_END
            is_weekend = timestamp.weekday() >= 5

            return SlackMessage(
                message_id=message_data['ts'],
                channel_id=message_data.get('channel', ''),
                channel_name=channel_name,
                user_id=message_data['user'],
                timestamp=timestamp,
                message_type=message_type,
                reply_count=reply_count,
                reaction_count=reaction_count,
                has_mentions=has_mentions,
                has_links=has_links,
                has_attachments=has_attachments,
                word_count=word_count,
                emoji_count=emoji_count,
                is_after_hours=is_after_hours,
                is_weekend=is_weekend,
                hour_of_day=timestamp.hour,
                day_of_week=timestamp.weekday(),
                organization_id=organization_id,
                connection_id=connection_id
            )

        except Exception as e:
            logger.error(f"Error extracting Slack message metadata: {e}")
            return None

    def calculate_behavioral_signals(
        self,
        messages: List[SlackMessage],
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate behavioral signals from Slack metadata

        Args:
            messages: List of Slack messages
            time_window_days: Time window for analysis

        Returns:
            Dictionary of behavioral signals
        """
        if not messages:
            return {}

        signals = {
            'message_frequency_per_day': len(messages) / time_window_days,
            'avg_messages_per_day': len(messages) / time_window_days,
            'response_time_avg_minutes': 0.0,
            'after_hours_message_percentage': 0.0,
            'weekend_message_percentage': 0.0,
            'channel_diversity_score': 0.0,  # Number of unique channels
            'emoji_usage_rate': 0.0,
            'positive_emoji_percentage': 0.0,
            'negative_emoji_percentage': 0.0,
            'stress_emoji_percentage': 0.0,
            'thread_participation_rate': 0.0,
            'mention_rate': 0.0,
            'attachment_rate': 0.0,
            'avg_word_count': 0.0,
            'communication_volatility': 0.0,  # Variance in message frequency
            'hourly_distribution': [0] * 24,
            'daily_distribution': [0] * 7,
            'channel_activity_distribution': {},
            'reply_rate': 0.0,
            'reaction_rate': 0.0,
            'social_interaction_score': 0.0,  # 0-1, based on reactions, mentions, threads
            'communication_overload': False,
            'burnout_risk_score': 0.0
        }

        # Calculate metrics
        after_hours_count = 0
        weekend_count = 0
        total_emojis = 0
        positive_emojis = 0
        negative_emojis = 0
        stress_emojis = 0
        mention_count = 0
        attachment_count = 0
        total_words = 0
        threads_started = 0
        total_replies = 0
        total_reactions = 0

        channels = set()
        channel_message_counts = defaultdict(int)

        for msg in messages:
            # Time-based metrics
            if msg.is_after_hours:
                after_hours_count += 1
            if msg.is_weekend:
                weekend_count += 1

            # Channel diversity
            channels.add(msg.channel_name)
            channel_message_counts[msg.channel_name] += 1

            # Emoji analysis
            total_emojis += msg.emoji_count
            # Note: Actual emoji type analysis would need full message data
            # For now, we count total emojis

            # Mentions and attachments
            if msg.has_mentions:
                mention_count += 1
            if msg.has_attachments:
                attachment_count += 1

            # Word count
            total_words += msg.word_count

            # Thread analysis
            if msg.message_type == 'thread_starter':
                threads_started += 1
                total_replies += msg.reply_count

            # Reactions
            total_reactions += msg.reaction_count

            # Hourly and daily distribution
            signals['hourly_distribution'][msg.hour_of_day] += 1
            signals['daily_distribution'][msg.day_of_week] += 1

        # Calculate percentages and rates
        total = len(messages)
        signals['after_hours_message_percentage'] = (after_hours_count / total) * 100
        signals['weekend_message_percentage'] = (weekend_count / total) * 100
        signals['channel_diversity_score'] = len(channels)
        signals['emoji_usage_rate'] = total_emojis / total if total > 0 else 0
        signals['mention_rate'] = mention_count / total if total > 0 else 0
        signals['attachment_rate'] = attachment_count / total if total > 0 else 0
        signals['avg_word_count'] = total_words / total if total > 0 else 0

        # Emoji percentages (would need actual reaction data for accuracy)
        signals['positive_emoji_percentage'] = (positive_emojis / total_emojis * 100) if total_emojis > 0 else 0
        signals['negative_emoji_percentage'] = (negative_emojis / total_emojis * 100) if total_emojis > 0 else 0
        signals['stress_emoji_percentage'] = (stress_emojis / total_emojis * 100) if total_emojis > 0 else 0

        # Thread participation
        signals['thread_participation_rate'] = (total_replies / threads_started) if threads_started > 0 else 0
        signals['reply_rate'] = total_replies / total if total > 0 else 0
        signals['reaction_rate'] = total_reactions / total if total > 0 else 0

        # Social interaction score (0-1)
        social_signals = [
            signals['mention_rate'],
            min(signals['thread_participation_rate'] / 5, 1.0),  # Normalize
            min(signals['reaction_rate'] * 5, 1.0),  # Scale up
            min(len(channels) / 20, 1.0)  # Channel diversity
        ]
        signals['social_interaction_score'] = sum(social_signals) / len(social_signals)

        # Channel activity distribution
        signals['channel_activity_distribution'] = dict(channel_message_counts)

        # Communication overload (>200 messages/day)
        signals['communication_overload'] = signals['avg_messages_per_day'] > 200

        # Burnout risk score (0-1)
        burnout_factors = []
        if signals['after_hours_message_percentage'] > 25:
            burnout_factors.append(0.3)
        if signals['weekend_message_percentage'] > 15:
            burnout_factors.append(0.3)
        if signals['avg_messages_per_day'] > 150:
            burnout_factors.append(0.2)
        if signals['stress_emoji_percentage'] > 20:
            burnout_factors.append(0.2)
        signals['burnout_risk_score'] = sum(burnout_factors)

        return signals

    def detect_burnout_indicators(self, signals: Dict[str, Any]) -> List[str]:
        """
        Detect burnout risk indicators from Slack behavioral signals

        Args:
            signals: Behavioral signals dictionary

        Returns:
            List of detected burnout indicators
        """
        indicators = []

        # Check for excessive communication
        if signals.get('message_frequency_per_day', 0) > 200:
            indicators.append("Excessive Slack messaging (>200/day)")

        # Check for after-hours overload
        if signals.get('after_hours_message_percentage', 0) > 30:
            indicators.append("High after-hours Slack activity (>30%)")

        # Check for weekend work
        if signals.get('weekend_message_percentage', 0) > 20:
            indicators.append("Frequent weekend Slack activity (>20%)")

        # Check for stress emoji usage
        if signals.get('stress_emoji_percentage', 0) > 25:
            indicators.append("High stress indicator emoji usage (>25%)")

        # Check for low social interaction (isolation)
        if signals.get('social_interaction_score', 1.0) < 0.3:
            indicators.append("Low social interaction (potential isolation)")

        # Check for communication overload
        if signals.get('communication_overload', False):
            indicators.append("Communication overload (>200 messages/day)")

        # Check for negative sentiment
        if signals.get('negative_emoji_percentage', 0) > 30:
            indicators.append("High negative emoji usage (>30%)")

        # Check for low channel diversity (silos)
        if signals.get('channel_diversity_score', 0) < 3:
            indicators.append("Limited channel diversity (<3 channels)")

        return indicators

    def analyze_team_dynamics(
        self,
        messages_by_user: Dict[str, List[SlackMessage]],
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze team-wide communication patterns

        Args:
            messages_by_user: Dictionary mapping user_id to their messages
            time_window_days: Time window for analysis

        Returns:
            Dictionary of team dynamics metrics
        """
        team_signals = {
            'total_users': len(messages_by_user),
            'total_messages': sum(len(msgs) for msgs in messages_by_user.values()),
            'avg_messages_per_user': 0.0,
            'communication_distribution_evenness': 0.0,  # Gini coefficient
            'cross_channel_collaboration_score': 0.0,
            'response_time_avg_minutes': 0.0,
            'most_active_hour': 0,
            'most_active_day': 0,
            'user_activity_levels': {},
            'channel_usage_patterns': {},
            'team_health_score': 0.0
        }

        total_messages = sum(len(msgs) for msgs in messages_by_user.values())
        team_signals['avg_messages_per_user'] = total_messages / len(messages_by_user) if messages_by_user else 0

        # User activity levels
        for user_id, messages in messages_by_user.items():
            team_signals['user_activity_levels'][user_id] = len(messages)

        # Calculate activity distribution evenness (0 = very uneven, 1 = very even)
        if messages_by_user:
            avg_activity = total_messages / len(messages_by_user)
            max_activity = max(len(msgs) for msgs in messages_by_user.values())
            min_activity = min(len(msgs) for msgs in messages_by_user.values())
            range_activity = max_activity - min_activity
            team_signals['communication_distribution_evenness'] = 1.0 - (range_activity / max_activity) if max_activity > 0 else 1.0

        # Team health score (0-1)
        health_factors = []
        if team_signals['communication_distribution_evenness'] > 0.6:
            health_factors.append(0.2)
        if team_signals['avg_messages_per_user'] > 10:
            health_factors.append(0.2)
        if team_signals['communication_distribution_evenness'] > 0.7:
            health_factors.append(0.3)
        # Add more health factors as needed

        team_signals['team_health_score'] = min(sum(health_factors), 1.0)

        return team_signals


class SlackAPIIntegration:
    """Slack API integration for fetching message metadata"""

    SCOPES = [
        'channels:history',
        'groups:history',
        'ims:history',
        'mpim:history',
        'channels:read',
        'groups:read',
        'users:read'
    ]

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = 'https://slack.com/api'

    async def fetch_conversations(self) -> List[Dict[str, Any]]:
        """Fetch list of conversations (channels, DMs, etc.)

        Uses resilient HTTP client with automatic retries, timeouts, and circuit breaker.
        """
        from app.core.resilient_client import resilient_http_client

        # Resilient client provides: 30s timeout, 3 retries with exponential backoff,
        # circuit breaker to prevent cascading failures, connection pooling
        response = await resilient_http_client.get(
            f'{self.base_url}/conversations.list',
            headers={'Authorization': f'Bearer {self.bot_token}'},
            params={'types': 'public_channel,private_channel,mpim,im'}
        )
        response.raise_for_status()

            data = response.json()
            if not data.get('ok'):
                logger.error(f"Slack API error: {data.get('error')}")
                return []

            return data.get('channels', [])

    async def fetch_messages_from_conversation(
        self,
        conversation_id: str,
        days: int = 30,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Fetch messages from a specific conversation

        Uses resilient HTTP client for improved reliability.
        """
        from datetime import datetime, timedelta

        from app.core.resilient_client import resilient_http_client
        oldest_ts = (datetime.utcnow() - timedelta(days=days)).timestamp()

        # TODO(human): If you want to add custom error handling for Slack-specific errors,
        # add it here. For example, you might want to handle 'rate_limited' errors
        # by implementing a custom retry delay based on the Retry-After header.
        # See app/core/resilient_client.py for available exception types.

        response = await resilient_http_client.get(
            f'{self.base_url}/conversations.history',
            headers={'Authorization': f'Bearer {self.bot_token}'},
            params={
                'channel': conversation_id,
                'oldest': oldest_ts,
                'limit': limit,
                'inclusive': 'true'
            }
        )
        response.raise_for_status()

            data = response.json()
            if not data.get('ok'):
                logger.error(f"Slack API error: {data.get('error')}")
                return []

            return data.get('messages', [])

    async def fetch_all_messages(
        self,
        days: int = 30,
        exclude_archived: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch all messages from all accessible conversations"""
        conversations = await self.fetch_conversations()

        if exclude_archived:
            conversations = [c for c in conversations if not c.get('is_archived', False)]

        all_messages = {}
        for conv in conversations:
            conv_id = conv['id']
            messages = await self.fetch_messages_from_conversation(conv_id, days)
            all_messages[conv_id] = messages

        return all_messages

    async def fetch_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user information

        Uses resilient HTTP client for improved reliability.
        """
        from app.core.resilient_client import resilient_http_client

        response = await resilient_http_client.get(
            f'{self.base_url}/users.info',
            headers={'Authorization': f'Bearer {self.bot_token}'},
            params={'user': user_id}
        )
        response.raise_for_status()

            data = response.json()
            if not data.get('ok'):
                logger.error(f"Slack API error: {data.get('error')}")
                return None

            return data.get('user')


# Export
__all__ = [
    'SlackMetadataExtractor',
    'SlackMessage',
    'SlackReaction',
    'SlackAPIIntegration'
]
