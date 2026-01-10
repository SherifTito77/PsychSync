"""
SIEM (Security Information and Event Management) Integration

Streams security events to external SIEM systems for:
- Centralized log aggregation
- Correlation and analysis
- Alerting and incident response
- Compliance reporting

Supports:
- Splunk (HTTP Event Collector)
- Elasticsearch/ELK Stack
- Microsoft Azure Sentinel (Log Analytics)
- AWS CloudWatch Logs
- Sumo Logic
- Datadog
"""

import json
import logging

logger = logging.getLogger(__name__)
import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp

from app.security.logging.schemas import SecurityEvent


class SIEMType(str, Enum):
    """Supported SIEM systems"""
    SPLUNK = "splunk"
    ELASTICSEARCH = "elasticsearch"
    AZURE_SENTINEL = "azure_sentinel"
    CLOUDWATCH = "cloudwatch"
    SUMO_LOGIC = "sumo_logic"
    DATADOG = "datadog"


@dataclass
class SIEMConfig:
    """Configuration for SIEM endpoint"""
    siem_type: SIEMType
    enabled: bool = True
    endpoint_url: str | None = None
    api_token: str | None = None
    index: str | None = None  # For Splunk/Elasticsearch
    batch_size: int = 100
    batch_timeout_seconds: int = 10
    max_retries: int = 3
    retry_delay_seconds: int = 5
    verify_ssl: bool = True
    custom_headers: dict[str, str] = field(default_factory=dict)


class SIEMStreamer:
    """
    Streams security events to configured SIEM systems.

    Implements:
    - Batching for efficiency
    - Automatic retry with exponential backoff
    - Circuit breaker for failing endpoints
    - Async non-blocking I/O
    """

    def __init__(self):
        self.configs: list[SIEMConfig] = []
        self._batch_queues: dict[SIEMType, deque] = {}
        self._session: aiohttp.ClientSession | None = None
        self._circuit_breakers: dict[SIEMType, dict[str, Any]] = {}
        self._stats: dict[str, int] = {
            "events_sent": 0,
            "events_failed": 0,
            "batches_sent": 0,
            "batches_failed": 0
        }

    def add_config(self, config: SIEMConfig):
        """Add SIEM configuration"""
        if not config.enabled:
            return

        self.configs.append(config)
        self._batch_queues[config.siem_type] = deque()
        self._circuit_breakers[config.siem_type] = {
            "is_open": False,
            "failure_count": 0,
            "last_failure_time": None,
            "success_count": 0
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def send_event(self, event: SecurityEvent) -> bool:
        """
        Send single event to all configured SIEMs.

        Args:
            event: Event to send

        Returns:
            True if sent successfully to all SIEMs
        """
        success = True

        for config in self.configs:
            # Check circuit breaker
            if self._is_circuit_open(config.siem_type):
                continue

            try:
                # Add to batch queue
                self._batch_queues[config.siem_type].append(event)

                # Send batch if full
                if len(self._batch_queues[config.siem_type]) >= config.batch_size:
                    await self._flush_queue(config.siem_type)

            except Exception as e:
                logger.error(f"Error queuing event for {config.siem_type}: {e}")
                success = False
                self._record_failure(config.siem_type)

        return success

    async def send_batch(self, events: list[SecurityEvent]) -> bool:
        """
        Send batch of events to all configured SIEMs.

        Args:
            events: Events to send

        Returns:
            True if sent successfully to all SIEMs
        """
        success = True

        for config in self.configs:
            if self._is_circuit_open(config.siem_type):
                continue

            try:
                await self._send_to_siem(config, events)
                self._record_success(config.siem_type)
            except Exception as e:
                logger.error(f"Error sending batch to {config.siem_type}: {e}")
                success = False
                self._record_failure(config.siem_type)

        return success

    async def flush_all(self):
        """Flush all pending batches"""
        for siem_type in list(self._batch_queues.keys()):
            if self._batch_queues[siem_type]:
                await self._flush_queue(siem_type)

    async def _flush_queue(self, siem_type: SIEMType):
        """Flush batch queue for specific SIEM"""
        queue = self._batch_queues[siem_type]

        if not queue:
            return

        # Convert queue to list
        events = list(queue)
        queue.clear()

        # Find config
        config = next((c for c in self.configs if c.siem_type == siem_type), None)
        if not config:
            return

        try:
            await self._send_to_siem(config, events)
            self._record_success(siem_type)
        except Exception as e:
            logger.error(f"Error flushing to {siem_type}: {e}")
            # Re-queue events for retry
            queue.extendleft(reversed(events))
            self._record_failure(siem_type)

    async def _send_to_siem(self, config: SIEMConfig, events: list[SecurityEvent]):
        """Send events to specific SIEM"""
        if config.siem_type == SIEMType.SPLUNK:
            await self._send_to_splunk(config, events)
        elif config.siem_type == SIEMType.ELASTICSEARCH:
            await self._send_to_elasticsearch(config, events)
        elif config.siem_type == SIEMType.AZURE_SENTINEL:
            await self._send_to_azure_sentinel(config, events)
        elif config.siem_type == SIEMType.CLOUDWATCH:
            await self._send_to_cloudwatch(config, events)
        elif config.siem_type == SIEMType.DATADOG:
            await self._send_to_datadog(config, events)
        else:
            raise ValueError(f"Unsupported SIEM type: {config.siem_type}") from e

        self._stats["events_sent"] += len(events)
        self._stats["batches_sent"] += 1

    async def _send_to_splunk(self, config: SIEMConfig, events: list[SecurityEvent]):
        """Send events to Splunk HTTP Event Collector"""
        url = config.endpoint_url or "https://localhost:8088/services/collector/event"
        headers = {
            "Authorization": f"Splunk {config.api_token}",
            "Content-Type": "application/json"
        }
        headers.update(config.custom_headers)

        session = await self._get_session()

        # Splunk HEC format
        splunk_events = []
        for event in events:
            splunk_events.append({
                "time": int(event.timestamp.timestamp()),
                "host": "psychsync",
                "source": "security_logging",
                "sourcetype": "json",
                "index": config.index or "security_logs",
                "event": event.dict()
            })

        for attempt in range(config.max_retries):
            try:
                async with session.post(url, json=splunk_events, headers=headers, ssl=config.verify_ssl) as response:
                    if response.status == 200:
                        return
                    if response.status >= 500:
                        # Server error, retry
                        if attempt < config.max_retries - 1:
                            await asyncio.sleep(config.retry_delay_seconds * (2 ** attempt))
                            continue
                    raise Exception(f"Splunk returned status {response.status}: {await response.text()}")
            except aiohttp.ClientError as e:
                if attempt < config.max_retries - 1:
                    await asyncio.sleep(config.retry_delay_seconds * (2 ** attempt))
                    continue
                raise e

    async def _send_to_elasticsearch(self, config: SIEMConfig, events: list[SecurityEvent]):
        """Send events to Elasticsearch"""
        url = config.endpoint_url or "http://localhost:9200/security_logs/_bulk"
        headers = {
            "Content-Type": "application/x-ndjson"
        }
        headers.update(config.custom_headers)

        session = await self._get_session()

        # Elasticsearch bulk format
        bulk_data = ""
        index_name = config.index or "security_logs"

        for event in events:
            # Index action
            bulk_data += json.dumps({
                "index": {
                    "_index": index_name,
                    "_id": event.event_id
                }
            }) + "\n"
            # Document data
            bulk_data += json.dumps(event.dict(), default=str) + "\n"

        for attempt in range(config.max_retries):
            try:
                async with session.post(url, data=bulk_data, headers=headers, ssl=config.verify_ssl) as response:
                    if response.status in [200, 201]:
                        return
                    if response.status >= 500:
                        if attempt < config.max_retries - 1:
                            await asyncio.sleep(config.retry_delay_seconds * (2 ** attempt))
                            continue
                    raise Exception(f"Elasticsearch returned status {response.status}: {await response.text()}")
            except aiohttp.ClientError as e:
                if attempt < config.max_retries - 1:
                    await asyncio.sleep(config.retry_delay_seconds * (2 ** attempt))
                    continue
                raise e

    async def _send_to_azure_sentinel(self, config: SIEMConfig, events: list[SecurityEvent]):
        """Send events to Microsoft Azure Sentinel (Log Analytics)"""
        # Azure Sentinel uses Log Analytics REST API
        workspace_id = config.endpoint_url  # Should be workspace ID
        url = f"https://{workspace_id}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01"

        headers = {
            "Content-Type": "application/json",
            "Log-Type": "SecurityLogs",
            "Authorization": f"Bearer {config.api_token}",
            "time-generated-field": "timestamp"
        }
        headers.update(config.custom_headers)

        session = await self._get_session()

        for attempt in range(config.max_retries):
            try:
                async with session.post(url, json=[e.dict() for e in events], headers=headers, ssl=config.verify_ssl) as response:
                    if response.status == 200:
                        return
                    if response.status >= 500:
                        if attempt < config.max_retries - 1:
                            await asyncio.sleep(config.retry_delay_seconds * (2 ** attempt))
                            continue
                    raise Exception(f"Azure Sentinel returned status {response.status}: {await response.text()}")
            except aiohttp.ClientError as e:
                if attempt < config.max_retries - 1:
                    await asyncio.sleep(config.retry_delay_seconds * (2 ** attempt))
                    continue
                raise e

    async def _send_to_cloudwatch(self, config: SIEMConfig, events: list[SecurityEvent]):
        """Send events to AWS CloudWatch Logs"""
        # CloudWatch uses boto3 SDK
        try:
            import boto3
        except ImportError:
            raise Exception("boto3 is required for CloudWatch integration")

        log_group_name = config.index or "/psychsync/security_logs"
        log_stream_name = datetime.utcnow().strftime("%Y/%m/%d/%H")

        client = boto3.client(
            "logs",
            aws_access_key_id=config.endpoint_url,  # Using endpoint_url for access key
            aws_secret_access_key=config.api_token
        )

        # Create log stream if it doesn't exist
        try:
            client.create_log_stream(
                logGroupName=log_group_name,
                logStreamName=log_stream_name
            )
        except client.exceptions.ResourceAlreadyExistsException:
            pass

        # Format events
        cloudwatch_events = []
        for event in events:
            cloudwatch_events.append({
                "timestamp": int(event.timestamp.timestamp() * 1000),
                "message": json.dumps(event.dict(), default=str)
            })

        # Send events
        for attempt in range(config.max_retries):
            try:
                client.put_log_events(
                    logGroupName=log_group_name,
                    logStreamName=log_stream_name,
                    logEvents=cloudwatch_events
                )
                return
            except Exception as e:
                if attempt < config.max_retries - 1:
                    await asyncio.sleep(config.retry_delay_seconds * (2 ** attempt))
                    continue
                raise e

    async def _send_to_datadog(self, config: SIEMConfig, events: list[SecurityEvent]):
        """Send events to Datadog"""
        url = "https://http-intake.logs.datadoghq.com/v1/input/"
        headers = {
            "Content-Type": "application/json",
            "DD-API-KEY": config.api_token
        }
        headers.update(config.custom_headers)

        session = await self._get_session()

        # Datadog format
        datadog_events = []
        for event in events:
            datadog_events.append({
                "ddsource": "psychsync",
                "ddtags": f"event_type:{event.event_type.value},severity:{event.severity.value}",
                "hostname": "psychsync",
                "message": event.dict(),
                "timestamp": int(event.timestamp.timestamp() * 1000)
            })

        for attempt in range(config.max_retries):
            try:
                async with session.post(url, json=datadog_events, headers=headers, ssl=config.verify_ssl) as response:
                    if response.status == 200:
                        return
                    if response.status >= 500:
                        if attempt < config.max_retries - 1:
                            await asyncio.sleep(config.retry_delay_seconds * (2 ** attempt))
                            continue
                    raise Exception(f"Datadog returned status {response.status}: {await response.text()}")
            except aiohttp.ClientError as e:
                if attempt < config.max_retries - 1:
                    await asyncio.sleep(config.retry_delay_seconds * (2 ** attempt))
                    continue
                raise e

    def _is_circuit_open(self, siem_type: SIEMType) -> bool:
        """Check if circuit breaker is open for SIEM"""
        breaker = self._circuit_breakers.get(siem_type, {})
        return breaker.get("is_open", False)

    def _record_success(self, siem_type: SIEMType):
        """Record successful transmission"""
        breaker = self._circuit_breakers.get(siem_type, {})
        breaker["is_open"] = False
        breaker["failure_count"] = 0
        breaker["success_count"] = breaker.get("success_count", 0) + 1

    def _record_failure(self, siem_type: SIEMType):
        """Record failed transmission"""
        breaker = self._circuit_breakers.get(siem_type, {})
        failure_count = breaker.get("failure_count", 0) + 1
        breaker["failure_count"] = failure_count
        breaker["last_failure_time"] = datetime.utcnow()

        # Open circuit after 5 consecutive failures
        if failure_count >= 5:
            breaker["is_open"] = True

    def get_stats(self) -> dict[str, Any]:
        """Get streaming statistics"""
        return {
            **self._stats,
            "pending_events": {
                siem_type.value: len(queue)
                for siem_type, queue in self._batch_queues.items()
            },
            "circuit_breakers": {
                siem_type.value: {
                    "is_open": breaker["is_open"],
                    "failure_count": breaker["failure_count"],
                    "success_count": breaker.get("success_count", 0)
                }
                for siem_type, breaker in self._circuit_breakers.items()
            }
        }


# Singleton instance
_default_siem_streamer = None


def get_siem_streamer() -> SIEMStreamer:
    """Get default SIEM streamer instance"""
    global _default_siem_streamer
    if _default_siem_streamer is None:
        _default_siem_streamer = SIEMStreamer()
    return _default_siem_streamer
