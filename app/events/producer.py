"""
Kafka Event Producer

Publishes events to Kafka topics for distributed event streaming.
Supports reliable delivery, batching, and error handling.

Created: 2025-01-12
Author: Architecture Team
"""

import asyncio
import json
import logging
import random
from asyncio import Queue
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.core.config import settings
from app.events.schemas import CloudEvent, EventType

logger = logging.getLogger(__name__)

# ✅ NEW: Persistent buffer configuration
PERSISTENT_BUFFER_KEY_PREFIX = "kafka:buffer:"
BUFFER_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days


class KafkaEventProducer:
    """
    Kafka producer for publishing events.

    Features:
    - Async event publishing
    - Automatic serialization
    - Batching for efficiency
    - Error handling and retries
    - Callbacks for delivery confirmation

    Usage:
        producer = KafkaEventProducer()
        await producer.start()

        # Publish event
        await producer.publish(
            topic="assessment-events",
            event=assessment_completed_event
        )

        await producer.stop()
    """

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        client_id: Optional[str] = None,
        compression_type: str = "snappy",
        max_batch_size: int = 16384,  # 16KB
        linger_ms: int = 10,  # Wait up to 10ms for batching
        acks: str = "all",  # Wait for all replicas
        max_retries: int = 3,  # Application-level retries
    ):
        """
        Initialize Kafka producer.

        Args:
            bootstrap_servers: Kafka servers (default: from settings)
            client_id: Client ID for tracking
            compression_type: Compression (snappy, gzip, lz4, none)
            max_batch_size: Max batch size in bytes
            linger_ms: Milliseconds to wait for batching
            acks: Acknowledgment level (0, 1, all)
            max_retries: Application-level retry attempts
        """
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self.client_id = client_id or "psychsync-producer"
        self.compression_type = compression_type
        self.max_batch_size = max_batch_size
        self.linger_ms = linger_ms
        self.acks = acks
        self.max_retries = max_retries  # Store for application-level retry logic

        self.producer: Optional[AIOKafkaProducer] = None
        self._event_queue: Optional[Queue] = None

        logger.info(f"KafkaEventProducer initialized: {self.bootstrap_servers}")

    async def start(self):
        """Start the Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                compression_type=self.compression_type,
                max_batch_size=self.max_batch_size,
                linger_ms=self.linger_ms,
                # retries parameter removed - handled at application level
                acks=self.acks,
                # Serialization
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                # Reliability
                enable_idempotence=True,  # Exactly-once semantics
                max_in_flight_requests_per_connection=5,
            )

            await self.producer.start()
            logger.info("✅ Kafka producer started")

        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise

    async def stop(self):
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def publish(
        self,
        topic: str,
        event: CloudEvent,
        key: Optional[str] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        max_retries: int = 3,  # ✅ NEW: Retry configuration
    ) -> Optional[Dict[str, Any]]:
        """
        Publish event to Kafka topic with retry logic.

        Args:
            topic: Kafka topic
            event: CloudEvent to publish
            key: Partition key (optional)
            partition: Specific partition (optional)
            timestamp_ms: Event timestamp (optional)
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            Record metadata (topic, partition, offset) if successful

        Raises:
            KafkaError: If publish fails after all retries
        """
        if not self.producer:
            raise RuntimeError("Producer not started. Call start() first.")

        # Serialize event to dict
        event_dict = event.dict()

        # Determine partition key
        # Use tenant_id for consistent hashing (same tenant → same partition)
        partition_key = key or event.tenant_id or event.id

        # ✅ NEW: Retry logic with exponential backoff
        last_exception = None
        for attempt in range(max_retries):
            try:
                # Send event
                record_metadata = await self.producer.send_and_wait(
                    topic=topic,
                    value=event_dict,
                    key=partition_key,
                    partition=partition,
                    timestamp_ms=timestamp_ms,
                )

                # Log success
                logger.info(
                    f"Event published: {event.type.value} → {topic} "
                    f"(partition={record_metadata.partition}, offset={record_metadata.offset})"
                )

                return {
                    "topic": record_metadata.topic,
                    "partition": record_metadata.partition,
                    "offset": record_metadata.offset,
                    "timestamp": record_metadata.timestamp,
                }

            except KafkaError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    # Calculate backoff delay with jitter
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        f"Publish attempt {attempt + 1}/{max_retries} failed for "
                        f"event {event.type.value}: {e}. Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Failed to publish event {event.type.value} after {max_retries} attempts: {e}"
                    )

        # ✅ NEW: All retries failed, store in persistent buffer
        logger.error(
            f"🔴 All retries exhausted for event {event.type.value}, "
            f"storing in persistent buffer"
        )
        await self._store_in_persistent_buffer(
            topic=topic,
            event=event,
            key=key,
            partition=partition,
            timestamp_ms=timestamp_ms,
        )

        raise last_exception

    async def publish_batch(
        self,
        events: List[tuple[str, CloudEvent, Optional[str]]],
        fail_fast: bool = False,  # ✅ NEW: Control batch failure behavior
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Publish multiple events in batch with improved error tracking.

        Args:
            events: List of (topic, event, key) tuples
            fail_fast: If True, stop on first failure. If False, continue and track failures.

        Returns:
            List of record metadata (or None for failed events)
        """
        results = []
        failed_events = []  # ✅ NEW: Track failed events for retry

        for topic, event, key in events:
            try:
                metadata = await self.publish(topic, event, key)
                results.append(metadata)
            except Exception as e:
                logger.error(f"Failed to publish event in batch: {e}")
                results.append(None)
                failed_events.append((topic, event, key, e))

                if fail_fast:
                    break

        # ✅ NEW: Log summary of batch results
        successful = sum(1 for r in results if r is not None)
        failed = len(results) - successful

        if failed > 0:
            logger.warning(
                f"⚠️ Batch publish completed: {successful} succeeded, {failed} failed"
            )
            # TODO: Implement retry logic for failed events in batch
            # await self._retry_failed_batch_events(failed_events)

        return results

    async def retry_from_buffer(self) -> Dict[str, int]:
        """
        ✅ NEW: Retry publishing events from persistent buffer.

        This method should be called periodically to flush buffered events.

        Returns:
            Dictionary with retry statistics
        """
        try:
            import redis.asyncio as aioredis

            client = await aioredis.from_url(settings.REDIS_URL)
            stats = {"retried": 0, "succeeded": 0, "failed": 0, "remaining": 0}

            try:
                # Scan for buffered events
                pattern = f"{PERSISTENT_BUFFER_KEY_PREFIX}*"
                async for key in client.iscan(match=pattern):
                    # Get buffered event data
                    data = await client.get(key)
                    if not data:
                        continue

                    event_data = json.loads(data)

                    # Try to publish
                    try:
                        event = CloudEvent.parse_raw(event_data["event"])
                        await self.publish(
                            topic=event_data["topic"],
                            event=event,
                            key=event_data.get("key"),
                            partition=event_data.get("partition"),
                            timestamp_ms=event_data.get("timestamp_ms"),
                        )

                        # Success: remove from buffer
                        await client.delete(key)
                        stats["succeeded"] += 1

                    except Exception as e:
                        logger.error(f"Failed to retry buffered event {key}: {e}")
                        stats["failed"] += 1

                    stats["retried"] += 1

                # Count remaining
                remaining = 0
                async for key in client.iscan(match=pattern):
                    remaining += 1
                stats["remaining"] = remaining

            finally:
                await client.close()

            logger.info(
                f"Buffer retry completed: {stats['succeeded']} succeeded, "
                f"{stats['failed']} failed, {stats['remaining']} remaining"
            )

            return stats

        except Exception as e:
            logger.error(f"Failed to retry from buffer: {e}", exc_info=True)
            return {"error": str(e)}

    def send(
        self,
        topic: str,
        event: CloudEvent,
        key: Optional[str] = None,
        use_buffer_on_failure: bool = True,  # ✅ NEW: Buffer on failure
    ):
        """
        ✅ IMPROVED: Send event asynchronously with delivery tracking.

        Returns immediately, delivery is handled in background.
        Useful for high-throughput scenarios.

        Args:
            topic: Kafka topic
            event: CloudEvent to publish
            key: Partition key (optional)
            use_buffer_on_failure: If True, store in buffer on failure

        Note:
            This method now uses a background task with proper error handling
            instead of pure fire-and-forget.
        """
        if not self.producer:
            raise RuntimeError("Producer not started. Call start() first.")

        event_dict = event.dict()
        partition_key = key or event.tenant_id or event.id

        # ✅ NEW: Create background task with error handling
        async def send_with_tracking():
            try:
                await self.producer.send(
                    topic=topic,
                    value=event_dict,
                    key=partition_key,
                )
                logger.debug(f"Event sent asynchronously: {event.type.value} → {topic}")
            except Exception as e:
                logger.error(f"Async send failed for event {event.type.value}: {e}")
                if use_buffer_on_failure:
                    await self._store_in_persistent_buffer(
                        topic=topic,
                        event=event,
                        key=key,
                        partition=None,
                        timestamp_ms=None,
                    )

        # Schedule background task
        asyncio.create_task(send_with_tracking())

    # =======================================================================
    # HELPER METHODS
    # =======================================================================

    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay with jitter.

        Args:
            attempt: Current retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        base_delay = 1.0  # 1 second base
        max_delay = 60.0  # 60 seconds max
        jitter_percent = 0.1  # ±10% jitter

        # Calculate exponential backoff
        delay = min(base_delay * (2 ** attempt), max_delay)

        # Add jitter
        jitter = delay * jitter_percent
        delay_with_jitter = delay + random.uniform(-jitter, jitter)

        return max(0, delay_with_jitter)

    async def _store_in_persistent_buffer(
        self,
        topic: str,
        event: CloudEvent,
        key: Optional[str],
        partition: Optional[int],
        timestamp_ms: Optional[int],
    ):
        """
        Store failed publish event in Redis persistent buffer.

        Args:
            topic: Kafka topic
            event: CloudEvent to publish
            key: Partition key
            partition: Specific partition
            timestamp_ms: Event timestamp
        """
        try:
            import redis.asyncio as aioredis

            client = await aioredis.from_url(settings.REDIS_URL)

            try:
                # Create buffer key
                buffer_key = f"{PERSISTENT_BUFFER_KEY_PREFIX}{event.id}"

                # Store event data with metadata
                buffer_data = {
                    "topic": topic,
                    "event": event.json(),
                    "key": key,
                    "partition": partition,
                    "timestamp_ms": timestamp_ms,
                    "buffered_at": datetime.utcnow().isoformat(),
                }

                # Store with TTL
                await client.setex(
                    buffer_key,
                    BUFFER_TTL_SECONDS,
                    json.dumps(buffer_data, default=str),
                )

                logger.info(
                    f"✅ Event buffered for later retry: {event.type.value} → {buffer_key}"
                )

            finally:
                await client.close()

        except Exception as e:
            logger.error(
                f"❌ Failed to store event in persistent buffer: {e}",
                exc_info=True,
            )
            # Last resort: log to file
            self._log_failed_event_to_file(
                topic=topic,
                event=event,
                key=key,
                error=str(e),
            )

    def _log_failed_event_to_file(
        self,
        topic: str,
        event: CloudEvent,
        key: Optional[str],
        error: str,
    ):
        """
        Last resort: Log failed event to file.

        Args:
            topic: Kafka topic
            event: CloudEvent
            key: Partition key
            error: Error message
        """
        try:
            from pathlib import Path

            # Create buffer directory
            buffer_dir = Path("logs/kafka_buffer")
            buffer_dir.mkdir(parents=True, exist_ok=True)

            # Write to file
            filename = buffer_dir / f"{event.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(
                    {
                        "topic": topic,
                        "event": event.dict(),
                        "key": key,
                        "error": error,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    f,
                    indent=2,
                    default=str,
                )

            logger.info(f"✅ Failed event logged to file: {filename}")

        except Exception as e:
            logger.error(f"❌ Failed to log event to file: {e}")


class EventPublisher:
    """
    High-level event publisher with topic routing.

    Automatically routes events to appropriate topics based on event type.
    Simplifies event publishing by abstracting Kafka details.

    Usage:
        publisher = EventPublisher(producer)

        # Publish event - topic is automatically determined
        await publisher.publish(assessment_completed_event)
    """

    # Event type → Kafka topic mapping
    TOPIC_MAPPING = {
        # Assessment events
        EventType.ASSESSMENT_STARTED: "assessment-events",
        EventType.ASSESSMENT_COMPLETED: "assessment-events",
        EventType.ASSESSMENT_ABORTED: "assessment-events",
        EventType.ASSESSMENT_EXPIRED: "assessment-events",
        # User events
        EventType.USER_REGISTERED: "user-events",
        EventType.USER_ACTIVATED: "user-events",
        EventType.USER_DEACTIVATED: "user-events",
        EventType.USER_PROFILE_UPDATED: "user-events",
        # Team events
        EventType.TEAM_CREATED: "team-events",
        EventType.TEAM_UPDATED: "team-events",
        EventType.TEAM_DELETED: "team-events",
        EventType.TEAM_MEMBER_ADDED: "team-events",
        EventType.TEAM_MEMBER_REMOVED: "team-events",
        EventType.TEAM_ROLE_CHANGED: "team-events",
        # Organization events
        EventType.ORGANIZATION_CREATED: "organization-events",
        EventType.ORGANIZATION_UPDATED: "organization-events",
        EventType.ORGANIZATION_DELETED: "organization-events",
        EventType.ORGANIZATION_SUSPENDED: "organization-events",
        # Analytics events
        EventType.ANALYTICS_GENERATED: "analytics-events",
        EventType.ANALYTICS_VIEWED: "analytics-events",
        # Billing events
        EventType.SUBSCRIPTION_CREATED: "billing-events",
        EventType.SUBSCRIPTION_UPDATED: "billing-events",
        EventType.SUBSCRIPTION_CANCELLED: "billing-events",
        EventType.INVOICE_GENERATED: "billing-events",
        EventType.INVOICE_PAID: "billing-events",
        # Notification events
        EventType.NOTIFICATION_SENT: "notification-events",
        EventType.NOTIFICATION_DELIVERED: "notification-events",
        EventType.NOTIFICATION_FAILED: "notification-events",
        # System events
        EventType.SYSTEM_ERROR: "system-events",
        EventType.SYSTEM_MAINTENANCE_STARTED: "system-events",
        EventType.SYSTEM_MAINTENANCE_ENDED: "system-events",
    }

    def __init__(self, producer: KafkaEventProducer):
        """
        Initialize event publisher.

        Args:
            producer: Kafka event producer instance
        """
        self.producer = producer

    async def publish(
        self,
        event: CloudEvent,
        topic_override: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Publish event to appropriate topic.

        Args:
            event: CloudEvent to publish
            topic_override: Override automatic topic selection

        Returns:
            Record metadata if successful

        Raises:
            ValueError: If event type has no topic mapping
            KafkaError: If publish fails
        """
        # Determine topic
        if topic_override:
            topic = topic_override
        else:
            topic = self.TOPIC_MAPPING.get(event.type)
            if not topic:
                raise ValueError(f"No topic mapping for event type: {event.type}")

        # Publish event
        return await self.producer.publish(
            topic=topic,
            event=event,
        )

    async def publish_with_retry(
        self,
        event: CloudEvent,
        max_retries: int = 3,
        topic_override: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Publish event with automatic retry on failure.

        Args:
            event: CloudEvent to publish
            max_retries: Maximum retry attempts
            topic_override: Override automatic topic selection

        Returns:
            Record metadata if successful, None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                return await self.publish(event, topic_override)
            except Exception as e:
                logger.warning(
                    f"Publish attempt {attempt + 1}/{max_retries} failed: {e}"
                )
                if attempt == max_retries - 1:
                    logger.error(
                        f"Failed to publish event after {max_retries} attempts"
                    )
                    return None

        return None


# Global producer instance
_producer: Optional[KafkaEventProducer] = None
_publisher: Optional[EventPublisher] = None


async def get_event_publisher() -> EventPublisher:
    """
    Get global event publisher instance.

    Usage:
        publisher = await get_event_publisher()
        await publisher.publish(event)
    """
    global _producer, _publisher

    if _publisher is None:
        _producer = KafkaEventProducer()
        await _producer.start()
        _publisher = EventPublisher(_producer)

    return _publisher


async def close_event_publisher():
    """Close global event publisher."""
    global _producer, _publisher

    if _producer:
        await _producer.stop()
        _producer = None
        _publisher = None


async def publish_event(event: CloudEvent) -> Optional[Dict[str, Any]]:
    """
    Convenience function to publish event.

    Usage:
        from app.events.producer import publish_event

        await publish_event(assessment_completed_event)
    """
    publisher = await get_event_publisher()
    return await publisher.publish(event)
