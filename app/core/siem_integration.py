# app/core/siem_integration.py
"""
SIEM (Security Information and Event Management) Integration
Sends security events and alerts to external SIEM systems for centralized monitoring

Supported SIEM platforms:
- Splunk (HTTP Event Collector)
- Elasticsearch/ELK Stack
- Sumo Logic
- Azure Sentinel
- Datadog Security Monitoring
- Custom Webhook endpoints
- Syslog

Author: Security Team
Version: 1.0
Date: December 23, 2024
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import logging
from typing import Any

import aiohttp

from app.core.config import settings

logger = logging.getLogger(__name__)


class SIEMPlatform(Enum):
    """Supported SIEM platforms"""

    SPLUNK_HEC = "splunk_hec"
    ELASTICSEARCH = "elasticsearch"
    SUMO_LOGIC = "sumo_logic"
    AZURE_SENTINEL = "azure_sentinel"
    DATADOG = "datadog"
    WEBHOOK = "webhook"
    SYSLOG = "syslog"


@dataclass
class SIEMConfig:
    """SIEM configuration"""

    platform: SIEMPlatform
    enabled: bool = True
    endpoint_url: str | None = None
    token: str | None = None
    index: str | None = None
    source: str | None = "psychsync"
    sourcetype: str | None = "_json"
    headers: dict[str, str] = None
    verify_ssl: bool = True
    timeout_seconds: int = 10
    batch_size: int = 100
    batch_flush_seconds: int = 60

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


@dataclass
class SIEMEvent:
    """Security event for SIEM"""

    event_type: str
    timestamp: datetime
    severity: str  # low, medium, high, critical
    category: str  # authentication, authorization, network, data_access, etc.
    source_ip: str | None = None
    user_id: str | None = None
    username: str | None = None
    action: str | None = None
    outcome: str | None = None  # success, failure, blocked
    details: dict[str, Any] = None
    metadata: dict[str, Any] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, handling datetime serialization"""
        data = {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat()
            if isinstance(self.timestamp, datetime)
            else self.timestamp,
            "severity": self.severity,
            "category": self.category,
            "source": "psychsync",
        }

        if self.source_ip:
            data["source_ip"] = self.source_ip
        if self.user_id:
            data["user_id"] = self.user_id
        if self.username:
            data["username"] = self.username
        if self.action:
            data["action"] = self.action
        if self.outcome:
            data["outcome"] = self.outcome
        if self.details:
            data["details"] = self.details
        if self.metadata:
            data["metadata"] = self.metadata

        return data


class SIEMIntegration:
    """
    Centralized SIEM integration for sending security events
    """

    def __init__(self, config: SIEMConfig | None = None):
        """
        Initialize SIEM integration

        Args:
            config: SIEMConfig object. If None, will load from settings
        """
        self.config = config or self._load_config()
        self.event_queue: list[SIEMEvent] = []
        self._batch_timer_task: asyncio.Task | None = None
        self._session: aiohttp.ClientSession | None = None

        if self.config.enabled:
            logger.info(f"SIEM integration enabled: {self.config.platform.value}")
            # Start batch flush timer
            self._start_batch_timer()

    def _load_config(self) -> SIEMConfig:
        """Load SIEM configuration from settings"""
        platform_str = getattr(settings, "SIEM_PLATFORM", "webhook").lower()
        try:
            platform = SIEMPlatform(platform_str)
        except ValueError:
            logger.warning(f"Unknown SIEM platform: {platform_str}, using webhook")
            platform = SIEMPlatform.WEBHOOK

        return SIEMConfig(
            platform=platform,
            enabled=getattr(settings, "SIEM_ENABLED", False),
            endpoint_url=getattr(settings, "SIEM_ENDPOINT_URL", None),
            token=getattr(settings, "SIEM_TOKEN", None),
            index=getattr(settings, "SIEM_INDEX", None),
            source=getattr(settings, "SIEM_SOURCE", "psychsync"),
            headers=getattr(settings, "SIEM_HEADERS", {}),
            verify_ssl=getattr(settings, "SIEM_VERIFY_SSL", True),
        )

    def _start_batch_timer(self):
        """Start background task to periodically flush event queue"""
        if self._batch_timer_task is None or self._batch_timer_task.done():
            self._batch_timer_task = asyncio.create_task(self._batch_flush_loop())

    async def _batch_flush_loop(self):
        """Background loop to periodically flush events"""
        while self.config.enabled:
            try:
                await asyncio.sleep(self.config.batch_flush_seconds)
                if self.event_queue:
                    await self.flush_events()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch flush loop: {e}")

    async def send_event(self, event: SIEMEvent) -> bool:
        """
        Send a security event to SIEM

        Args:
            event: SIEMEvent to send

        Returns:
            True if sent successfully
        """
        if not self.config.enabled:
            return False

        try:
            # Add to queue for batch sending
            self.event_queue.append(event)

            # Flush if queue is full
            if len(self.event_queue) >= self.config.batch_size:
                await self.flush_events()

            return True

        except Exception as e:
            logger.error(f"Error queueing SIEM event: {e}")
            return False

    async def send_alert(self, alert: "SecurityAlert") -> bool:
        """
        Send security alert to SIEM

        Args:
            alert: SecurityAlert from security_monitoring.py

        Returns:
            True if sent successfully
        """
        if not self.config.enabled:
            return False

        try:
            event = SIEMEvent(
                event_type="security_alert",
                timestamp=alert.timestamp,
                severity=alert.severity.value,
                category="security",
                user_id=alert.user_id,
                action=alert.anomaly_type.value,
                outcome="detected",
                details={
                    "alert_id": alert.id,
                    "description": alert.description,
                    "risk_score": alert.risk_score,
                    "alert_details": alert.details,
                },
                metadata=alert.metadata,
            )

            return await self.send_event(event)

        except Exception as e:
            logger.error(f"Error sending SIEM alert: {e}")
            return False

    async def flush_events(self) -> bool:
        """
        Flush all queued events to SIEM

        Returns:
            True if all events sent successfully
        """
        if not self.event_queue:
            return True

        events_to_send = self.event_queue.copy()
        self.event_queue.clear()

        try:
            success = await self._send_to_platform(events_to_send)

            if success:
                logger.debug(f"Sent {len(events_to_send)} events to SIEM")
            else:
                # Re-queue failed events
                self.event_queue.extend(events_to_send)

            return success

        except Exception as e:
            logger.error(f"Error flushing SIEM events: {e}")
            # Re-queue failed events
            self.event_queue.extend(events_to_send)
            return False

    async def _send_to_platform(self, events: list[SIEMEvent]) -> bool:
        """Send events to specific SIEM platform"""
        if self._session is None:
            self._session = aiohttp.ClientSession()

        try:
            if self.config.platform == SIEMPlatform.SPLUNK_HEC:
                return await self._send_to_splunk(events)
            if self.config.platform == SIEMPlatform.ELASTICSEARCH:
                return await self._send_to_elasticsearch(events)
            if self.config.platform == SIEMPlatform.WEBHOOK:
                return await self._send_to_webhook(events)
            logger.warning(
                f"SIEM platform {self.config.platform.value} not fully implemented, using webhook"
            )
            return await self._send_to_webhook(events)

        except Exception as e:
            logger.error(f"Error sending to SIEM platform: {e}")
            return False

    async def _send_to_splunk(self, events: list[SIEMEvent]) -> bool:
        """Send events to Splunk HTTP Event Collector"""
        try:
            if not self.config.endpoint_url or not self.config.token:
                logger.error("Splunk HEC requires endpoint_url and token")
                return False

            url = self.config.endpoint_url.rstrip("/") + "/services/collector/event"
            headers = {
                "Authorization": f"Splunk {self.config.token}",
                "Content-Type": "application/json",
            }

            # Send events as batch
            events_data = []
            for event in events:
                event_dict = event.to_dict()
                splunk_event = {
                    "time": int(datetime.timestamp(event.timestamp)),
                    "host": "psychsync",
                    "source": self.config.source,
                    "sourcetype": self.config.sourcetype,
                    "index": self.config.index,
                    "event": event_dict,
                }
                events_data.append(splunk_event)

            # For Splunk, we need to send events individually or with proper newline delimiter
            # Using newline-delimited JSON
            payload = "\n".join(json.dumps(e) for e in events_data)

            async with self._session.post(
                url,
                headers=headers,
                data=payload,
                ssl=self.config.verify_ssl,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
            ) as response:
                if response.status in [200, 201]:
                    return True
                text = await response.text()
                logger.error(f"Splunk HEC error: {response.status} - {text}")
                return False

        except Exception as e:
            logger.error(f"Error sending to Splunk: {e}")
            return False

    async def _send_to_elasticsearch(self, events: list[SIEMEvent]) -> bool:
        """Send events to Elasticsearch"""
        try:
            if not self.config.endpoint_url:
                logger.error("Elasticsearch requires endpoint_url")
                return False

            index = self.config.index or f"psychsync-security-{datetime.now().strftime('%Y.%m')}"

            url = f"{self.config.endpoint_url.rstrip('/')}/{index}/_bulk"
            headers = {"Content-Type": "application/x-ndjson"}

            if self.config.token:
                headers["Authorization"] = f"Bearer {self.config.token}"

            # Build bulk payload
            bulk_lines = []
            for event in events:
                event_dict = event.to_dict()

                # Add index action line
                action_line = json.dumps({"index": {"_index": index}})
                bulk_lines.append(action_line)

                # Add data line
                data_line = json.dumps(event_dict)
                bulk_lines.append(data_line)

            payload = "\n".join(bulk_lines) + "\n"

            async with self._session.post(
                url,
                headers=headers,
                data=payload,
                ssl=self.config.verify_ssl,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
            ) as response:
                if response.status in [200, 201]:
                    return True
                text = await response.text()
                logger.error(f"Elasticsearch error: {response.status} - {text}")
                return False

        except Exception as e:
            logger.error(f"Error sending to Elasticsearch: {e}")
            return False

    async def _send_to_webhook(self, events: list[SIEMEvent]) -> bool:
        """Send events to generic webhook endpoint"""
        try:
            if not self.config.endpoint_url:
                logger.error("Webhook requires endpoint_url")
                return False

            headers = {"Content-Type": "application/json"}

            # Add custom headers
            headers.update(self.config.headers)

            # Add auth header if token provided
            if self.config.token:
                headers["Authorization"] = f"Bearer {self.config.token}"

            payload = {
                "source": "psychsync",
                "platform": "security_monitoring",
                "timestamp": datetime.utcnow().isoformat(),
                "events": [e.to_dict() for e in events],
                "event_count": len(events),
            }

            async with self._session.post(
                self.config.endpoint_url,
                headers=headers,
                data=json.dumps(payload),
                ssl=self.config.verify_ssl,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
            ) as response:
                if response.status in [200, 201, 202, 204]:
                    return True
                text = await response.text()
                logger.error(f"Webhook error: {response.status} - {text}")
                return False

        except Exception as e:
            logger.error(f"Error sending to webhook: {e}")
            return False

    async def test_connection(self) -> dict[str, Any]:
        """
        Test SIEM connection

        Returns:
            Dict with test results
        """
        if not self.config.enabled:
            return {"success": False, "message": "SIEM integration is disabled"}

        test_event = SIEMEvent(
            event_type="connection_test",
            timestamp=datetime.utcnow(),
            severity="info",
            category="system",
            details={"message": "SIEM connection test"},
        )

        try:
            # Send test event directly (bypass queue)
            events_to_send = [test_event]
            success = await self._send_to_platform(events_to_send)

            return {
                "success": success,
                "platform": self.config.platform.value,
                "endpoint_url": self.config.endpoint_url,
                "message": "Connection successful" if success else "Connection failed",
            }

        except Exception as e:
            return {"success": False, "platform": self.config.platform.value, "error": str(e)}

    async def shutdown(self):
        """Cleanup and close connections"""
        # Flush any remaining events
        if self.event_queue:
            await self.flush_events()

        # Cancel batch timer
        if self._batch_timer_task and not self._batch_timer_task.done():
            self._batch_timer_task.cancel()
            try:
                await self._batch_timer_task
            except asyncio.CancelledError:
                pass

        # Close HTTP session
        if self._session:
            await self._session.close()
            self._session = None


# Global instance
siem_integration = SIEMIntegration()


# Convenience functions
async def send_security_event(
    event_type: str,
    severity: str,
    category: str,
    user_id: str | None = None,
    source_ip: str | None = None,
    action: str | None = None,
    outcome: str | None = None,
    details: dict[str, Any] | None = None,
) -> bool:
    """
    Convenience function to send security event to SIEM

    Args:
        event_type: Type of event (e.g., "login_attempt", "api_call")
        severity: Event severity (low, medium, high, critical)
        category: Event category (authentication, authorization, network, etc.)
        user_id: User ID (optional)
        source_ip: Source IP address (optional)
        action: Action performed (optional)
        outcome: Outcome (success, failure, blocked) (optional)
        details: Additional event details (optional)

    Returns:
        True if sent successfully
    """
    event = SIEMEvent(
        event_type=event_type,
        timestamp=datetime.utcnow(),
        severity=severity,
        category=category,
        user_id=user_id,
        source_ip=source_ip,
        action=action,
        outcome=outcome,
        details=details or {},
    )

    return await siem_integration.send_event(event)
