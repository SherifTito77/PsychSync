"""
Kafka Event Producer

Publishes events to Kafka topics for distributed event streaming.
Supports reliable delivery, batching, and error handling.

Created: 2025-01-12
Author: Architecture Team
"""

import json
import logging
from typing import Optional, Dict, Any, List
from asyncio import Queue
from datetime import datetime

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.events.schemas import CloudEvent, EventType

logger = logging.getLogger(__name__)


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
        compression_type: str = 'snappy',
        max_batch_size: int = 16384,  # 16KB
        linger_ms: int = 10,  # Wait up to 10ms for batching
        retries: int = 3,
        acks: str = 'all',  # Wait for all replicas
    ):
        """
        Initialize Kafka producer.

        Args:
            bootstrap_servers: Kafka servers (default: from settings)
            client_id: Client ID for tracking
            compression_type: Compression (snappy, gzip, lz4, none)
            max_batch_size: Max batch size in bytes
            linger_ms: Milliseconds to wait for batching
            retries: Number of retries on failure
            acks: Acknowledgment level (0, 1, all)
        """
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self.client_id = client_id or "psychsync-producer"
        self.compression_type = compression_type
        self.max_batch_size = max_batch_size
        self.linger_ms = linger_ms
        self.retries = retries
        self.acks = acks

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
                retries=self.retries,
                acks=self.acks,
                # Serialization
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
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
    ) -> Optional[Dict[str, Any]]:
        """
        Publish event to Kafka topic.

        Args:
            topic: Kafka topic
            event: CloudEvent to publish
            key: Partition key (optional)
            partition: Specific partition (optional)
            timestamp_ms: Event timestamp (optional)

        Returns:
            Record metadata (topic, partition, offset) if successful

        Raises:
            KafkaError: If publish fails after retries
        """
        if not self.producer:
            raise RuntimeError("Producer not started. Call start() first.")

        try:
            # Serialize event to dict
            event_dict = event.dict()

            # Determine partition key
            # Use tenant_id for consistent hashing (same tenant → same partition)
            partition_key = key or event.tenant_id or event.id

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
            logger.error(f"Failed to publish event {event.type.value}: {e}")
            raise

    async def publish_batch(
        self,
        events: List[tuple[str, CloudEvent, Optional[str]]]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Publish multiple events in batch.

        Args:
            events: List of (topic, event, key) tuples

        Returns:
            List of record metadata (or None for failed events)
        """
        results = []

        for topic, event, key in events:
            try:
                metadata = await self.publish(topic, event, key)
                results.append(metadata)
            except Exception as e:
                logger.error(f"Failed to publish event in batch: {e}")
                results.append(None)

        return results

    def send(
        self,
        topic: str,
        event: CloudEvent,
        key: Optional[str] = None,
    ):
        """
        Send event asynchronously (fire-and-forget).

        Returns immediately, delivery is handled in background.
        Useful for high-throughput scenarios.

        Args:
            topic: Kafka topic
            event: CloudEvent to publish
            key: Partition key (optional)
        """
        if not self.producer:
            raise RuntimeError("Producer not started. Call start() first.")

        event_dict = event.dict()
        partition_key = key or event.tenant_id or event.id

        # Send asynchronously
        self.producer.send(
            topic=topic,
            value=event_dict,
            key=partition_key,
        )

        logger.debug(f"Event sent asynchronously: {event.type.value} → {topic}")


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
                    logger.error(f"Failed to publish event after {max_retries} attempts")
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
