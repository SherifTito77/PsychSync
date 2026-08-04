"""
External Data Source Integrations for Radar
Integrates with Slack, Microsoft Teams, and Zoom for real-time behavioral signals
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class IntegrationType(Enum):
    """Supported integration types"""

    SLACK = "slack"
    TEAMS = "teams"
    ZOOM = "zoom"


@dataclass
class IntegrationConfig:
    """Configuration for external integration"""

    integration_type: IntegrationType
    api_key: str
    webhook_url: Optional[str] = None
    team_id: Optional[str] = None
    enabled: bool = True
    last_sync: Optional[datetime] = None


@dataclass
class ExternalSignal:
    """Behavioral signal from external source"""

    source: IntegrationType
    signal_type: str
    timestamp: datetime
    user_id: Optional[str]
    team_id: Optional[str]
    severity: float
    metadata: Dict[str, Any]


class ExternalIntegrationManager:
    """
    Manages integrations with external communication platforms

    Features:
    - Slack message analysis (sentiment, timing, patterns)
    - Teams meeting analytics (participation, interruptions)
    - Zoom meeting insights (engagement, fatigue indicators)
    - Real-time signal ingestion
    - Rate limiting and error handling
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.integration_configs: Dict[str, IntegrationConfig] = {}
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize async HTTP session"""
        if not HAS_AIOHTTP:
            logger.warning("aiohttp not installed - external integrations disabled")
            return

        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def shutdown(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

    async def register_integration(
        self, organization_id: str, config: IntegrationConfig
    ):
        """Register a new integration configuration"""
        key = f"{organization_id}:{config.integration_type.value}"
        self.integration_configs[key] = config
        logger.info(
            f"Registered {config.integration_type.value} integration for {organization_id}"
        )

    async def fetch_slack_signals(
        self, organization_id: str, days_back: int = 7
    ) -> List[ExternalSignal]:
        """
        Fetch behavioral signals from Slack

        Analyzes:
        - Message sentiment patterns
        - Communication timing (after-hours, weekend)
        - Response latency
        - Channel participation
        """
        await self.initialize()

        config_key = f"{organization_id}:slack"
        config = self.integration_configs.get(config_key)

        if not config or not config.enabled:
            logger.warning(f"Slack integration not configured for {organization_id}")
            return []

        signals = []

        try:
            # In production, would call Slack API:
            # - conversations.history
            # - reactions.list
            # - team.accessLogs

            # Simulated signal generation for demonstration
            signals = await self._simulate_slack_signals(organization_id, days_back)

            logger.info(
                f"Fetched {len(signals)} signals from Slack for {organization_id}"
            )

        except Exception as e:
            logger.error(f"Failed to fetch Slack signals: {e}", exc_info=True)

        return signals

    async def fetch_teams_signals(
        self, organization_id: str, days_back: int = 7
    ) -> List[ExternalSignal]:
        """
        Fetch behavioral signals from Microsoft Teams

        Analyzes:
        - Meeting participation patterns
        - Chat response times
        - Channel activity
        - After-hours communication
        """
        await self.initialize()

        config_key = f"{organization_id}:teams"
        config = self.integration_configs.get(config_key)

        if not config or not config.enabled:
            logger.warning(f"Teams integration not configured for {organization_id}")
            return []

        signals = []

        try:
            # In production, would call Microsoft Graph API:
            # - /messages
            # - /onlineMeetings
            # - /communications

            # Simulated signal generation
            signals = await self._simulate_teams_signals(organization_id, days_back)

            logger.info(
                f"Fetched {len(signals)} signals from Teams for {organization_id}"
            )

        except Exception as e:
            logger.error(f"Failed to fetch Teams signals: {e}", exc_info=True)

        return signals

    async def fetch_zoom_signals(
        self, organization_id: str, days_back: int = 7
    ) -> List[ExternalSignal]:
        """
        Fetch behavioral signals from Zoom

        Analyzes:
        - Meeting engagement scores
        - Video fatigue indicators
        - Participation patterns
        - Speaking time distribution
        """
        await self.initialize()

        config_key = f"{organization_id}:zoom"
        config = self.integration_configs.get(config_key)

        if not config or not config.enabled:
            logger.warning(f"Zoom integration not configured for {organization_id}")
            return []

        signals = []

        try:
            # In production, would call Zoom API:
            # - /past_meetings
            # - /meeting/{uuid}/participants
            # - /metrics/meetings

            # Simulated signal generation
            signals = await self._simulate_zoom_signals(organization_id, days_back)

            logger.info(
                f"Fetched {len(signals)} signals from Zoom for {organization_id}"
            )

        except Exception as e:
            logger.error(f"Failed to fetch Zoom signals: {e}", exc_info=True)

        return signals

    async def _simulate_slack_signals(
        self, organization_id: str, days_back: int
    ) -> List[ExternalSignal]:
        """Generate simulated Slack signals (demo purposes)"""
        signals = []

        # Simulate various Slack-based signals
        signal_types = [
            ("after_hours_message", 0.3),
            ("weekend_communication", 0.5),
            ("negative_sentiment", 0.6),
            ("slow_response_time", 0.2),
            ("channel_silence", 0.4),
        ]

        for i in range(min(20, days_back * 3)):
            import random

            signal_type, base_severity = random.choice(signal_types)

            # Add some variance
            severity = min(1.0, max(0.0, base_severity + random.uniform(-0.1, 0.1)))

            signal = ExternalSignal(
                source=IntegrationType.SLACK,
                signal_type=signal_type,
                timestamp=datetime.utcnow()
                - timedelta(days=random.randint(0, days_back)),
                user_id=f"user_{random.randint(1, 50)}",
                team_id=f"team_{random.randint(1, 5)}",
                severity=severity,
                metadata={
                    "channel": f"channel_{random.randint(1, 10)}",
                    "message_count": random.randint(1, 50),
                },
            )
            signals.append(signal)

        return signals

    async def _simulate_teams_signals(
        self, organization_id: str, days_back: int
    ) -> List[ExternalSignal]:
        """Generate simulated Teams signals (demo purposes)"""
        signals = []

        signal_types = [
            ("meeting_overload", 0.4),
            ("low_participation", 0.3),
            ("meeting_interruptions", 0.6),
            ("after_hours_meeting", 0.5),
            ("camera_always_off", 0.2),
        ]

        for i in range(min(15, days_back * 2)):
            import random

            signal_type, base_severity = random.choice(signal_types)
            severity = min(1.0, max(0.0, base_severity + random.uniform(-0.1, 0.1)))

            signal = ExternalSignal(
                source=IntegrationType.TEAMS,
                signal_type=signal_type,
                timestamp=datetime.utcnow()
                - timedelta(days=random.randint(0, days_back)),
                user_id=f"user_{random.randint(1, 50)}",
                team_id=f"team_{random.randint(1, 5)}",
                severity=severity,
                metadata={
                    "meeting_duration_minutes": random.randint(15, 120),
                    "participant_count": random.randint(3, 20),
                },
            )
            signals.append(signal)

        return signals

    async def _simulate_zoom_signals(
        self, organization_id: str, days_back: int
    ) -> List[ExternalSignal]:
        """Generate simulated Zoom signals (demo purposes)"""
        signals = []

        signal_types = [
            ("video_fatigue", 0.5),
            ("low_engagement", 0.4),
            ("speaking_time_imbalance", 0.6),
            ("extended_meeting", 0.3),
            ("frequent_disconnections", 0.4),
        ]

        for i in range(min(10, days_back)):
            import random

            signal_type, base_severity = random.choice(signal_types)
            severity = min(1.0, max(0.0, base_severity + random.uniform(-0.1, 0.1)))

            signal = ExternalSignal(
                source=IntegrationType.ZOOM,
                signal_type=signal_type,
                timestamp=datetime.utcnow()
                - timedelta(days=random.randint(0, days_back)),
                user_id=f"user_{random.randint(1, 50)}",
                team_id=f"team_{random.randint(1, 5)}",
                severity=severity,
                metadata={
                    "meeting_duration_minutes": random.randint(30, 180),
                    "attendee_count": random.randint(5, 30),
                    "engagement_score": random.uniform(0.3, 0.9),
                },
            )
            signals.append(signal)

        return signals

    async def fetch_all_signals(
        self, organization_id: str, days_back: int = 7
    ) -> List[ExternalSignal]:
        """Fetch signals from all enabled integrations"""
        all_signals = []

        # Fetch from each integration in parallel
        tasks = [
            self.fetch_slack_signals(organization_id, days_back),
            self.fetch_teams_signals(organization_id, days_back),
            self.fetch_zoom_signals(organization_id, days_back),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_signals.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Integration fetch failed: {result}")

        # Sort by timestamp
        all_signals.sort(key=lambda s: s.timestamp, reverse=True)

        return all_signals


# Singleton instance
external_integration_manager = ExternalIntegrationManager()
