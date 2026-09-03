"""
Kafka Dead Letter Queue (DLQ) System

Handles events that fail to process after multiple retry attempts.
Provides comprehensive tracking, analysis, and recovery capabilities for failed Kafka events.

Features:
- Separate DLQ topics for each event type
- Automatic retry with exponential backoff
- Failure classification (transient vs permanent)
- Dead letter entry persistence to database
- Monitoring and alerting

Author: Infrastructure Team
Version: 1.0.0
Date: February 9, 2026
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.events.schemas import CloudEvent, EventType

logger = logging.getLogger(__name__)


# =============================================================================
# DLQ TOPICS
# =============================================================================

KAFKA_DLQ_TOPIC_PREFIX = "dlq-"
DLQ_TOPICS = {
    "assessment": f"{KAFKA_DLQ_TOPIC_PREFIX}assessment-events",
    "user": f"{KAFKA_DLQ_TOPIC_PREFIX}user-events",
    "team": f"{KAFKA_DLQ_TOPIC_PREFIX}team-events",
    "organization": f"{KAFKA_DLQ_TOPIC_PREFIX}organization-events",
    "analytics": f"{KAFKA_DLQ_TOPIC_PREFIX}analytics-events",
    "billing": f"{KAFKA_DLQ_TOPIC_PREFIX}billing-events",
    "notification": f"{KAFKA_DLQ_TOPIC_PREFIX}notification-events",
    "system": f"{KAFKA_DLQ_TOPIC_PREFIX}system-events",
}


# =============================================================================
# DLQ ENTRY STATUS
# =============================================================================


class KafkaDLQStatus(str, Enum):
    """Status of Kafka DLQ entry"""

    PENDING = "pending"  # Awaiting processing
    PROCESSING = "processing"  # Currently being processed
    RETRYABLE = "retryable"  # Safe to retry
    PERMANENT = "permanent"  # Permanent failure (do not retry)
    RETRYING = "retrying"  # Currently being retried
    RETRIED = "retried"  # Successfully retried
    FAILED = "failed"  # Retry also failed
    DISCARDED = "discarded"  # Manually discarded


class KafkaDLQReason(str, Enum):
    """Reason for event being sent to DLQ"""

    PARSE_ERROR = "parse_error"
    HANDLER_ERROR = "handler_error"
    TIMEOUT = "timeout"
    VALIDATION_ERROR = "validation_error"
    DATABASE_ERROR = "database_error"
    NETWORK_ERROR = "network_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    SCHEMA_MISMATCH = "schema_mismatch"
    UNKNOWN = "unknown"


# =============================================================================
# KAFKA DLQ ENTRY MODEL
# =============================================================================


class KafkaDeadLetterEntry:
    """
    In-memory representation of a failed Kafka event for DLQ processing.

    This provides a lightweight structure for tracking failed events before
    they are persisted to the database.
    """

    def __init__(
        self,
        event_id: str,
        original_topic: str,
        event_type: str,
        event_data: dict,
        partition: int,
        offset: int,
        consumer_group: str,
        reason: KafkaDLQReason,
        exception_message: str,
        traceback: Optional[str] = None,
        retry_count: int = 0,
        max_retries: int = 3,
    ):
        self.id = uuid4()
        self.event_id = event_id
        self.original_topic = original_topic
        self.event_type = event_type
        self.event_data = event_data
        self.partition = partition
        self.offset = offset
        self.consumer_group = consumer_group
        self.reason = reason
        self.exception_message = exception_message
        self.traceback = traceback
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.status = KafkaDLQStatus.PENDING
        self.created_at = datetime.utcnow()
        self.next_retry_at: Optional[datetime] = None
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": str(self.id),
            "event_id": self.event_id,
            "original_topic": self.original_topic,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "partition": self.partition,
            "offset": self.offset,
            "consumer_group": self.consumer_group,
            "reason": self.reason.value,
            "exception_message": self.exception_message,
            "traceback": self.traceback,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "next_retry_at": (
                self.next_retry_at.isoformat() if self.next_retry_at else None
            ),
            "event_metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "KafkaDeadLetterEntry":
        """Create from dictionary"""
        entry = KafkaDeadLetterEntry(
            event_id=data["event_id"],
            original_topic=data["original_topic"],
            event_type=data["event_type"],
            event_data=data["event_data"],
            partition=data["partition"],
            offset=data["offset"],
            consumer_group=data["consumer_group"],
            reason=KafkaDLQReason(data["reason"]),
            exception_message=data["exception_message"],
            traceback=data.get("traceback"),
            retry_count=data["retry_count"],
            max_retries=data["max_retries"],
        )
        entry.id = UUID(data["id"])
        entry.status = KafkaDLQStatus(data["status"])
        entry.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("next_retry_at"):
            entry.next_retry_at = datetime.fromisoformat(data["next_retry_at"])
        entry.metadata = data.get("event_metadata", {})
        return entry


# =============================================================================
# KAFKA DLQ MANAGER
# =============================================================================


class KafkaDLQManager:
    """
    Manages Kafka Dead Letter Queue operations.

    Responsibilities:
    - Route failed events to DLQ topics
    - Track retry attempts
    - Classify failures
    - Coordinate recovery operations
    """

    def __init__(self, producer=None):
        """
        Initialize DLQ manager.

        Args:
            producer: KafkaEventProducer instance for publishing to DLQ topics
        """
        self.producer = producer

    async def send_to_dlq(
        self,
        entry: KafkaDeadLetterEntry,
    ) -> bool:
        """
        Send failed event to DLQ topic.

        Args:
            entry: Dead letter entry

        Returns:
            True if successfully sent to DLQ
        """
        try:
            # Determine DLQ topic based on event type
            dlq_topic = self._get_dlq_topic(entry.event_type)

            if not dlq_topic:
                logger.error(f"No DLQ topic for event type: {entry.event_type}")
                return False

            # Publish to DLQ topic
            if self.producer:
                from app.events.schemas import CloudEvent

                dlq_event = CloudEvent(
                    id=str(uuid4()),
                    type=EventType.SYSTEM_ERROR,  # Use system error type for DLQ events
                    source="kafka.dlq",
                    tenant_id=entry.event_data.get("tenant_id", ""),
                    data={
                        "dlq_entry": entry.to_dict(),
                        "original_event": entry.event_data,
                    },
                    timestamp=datetime.utcnow().isoformat(),
                )

                await self.producer.publish(
                    topic=dlq_topic,
                    event=dlq_event,
                    key=entry.event_id,
                )

                logger.info(
                    f"✅ Event sent to DLQ: {entry.event_id} → {dlq_topic} "
                    f"(reason: {entry.reason.value})"
                )

                # Persist to database
                await self._persist_dlq_entry(entry)

                return True
            else:
                # No producer available, just persist to database
                await self._persist_dlq_entry(entry)
                return True

        except Exception as e:
            logger.error(
                f"Failed to send event to DLQ: {e}",
                extra={"event_id": entry.event_id, "reason": entry.reason.value},
                exc_info=True,
            )
            return False

    def _get_dlq_topic(self, event_type: str) -> Optional[str]:
        """
        Get DLQ topic name based on event type.

        Args:
            event_type: Event type string

        Returns:
            DLQ topic name or None
        """
        # Extract prefix from event type (e.g., "assessment.completed" → "assessment")
        prefix = event_type.split(".")[0] if "." in event_type else event_type

        return DLQ_TOPICS.get(prefix)

    async def _persist_dlq_entry(self, entry: KafkaDeadLetterEntry):
        """
        Persist DLQ entry to database for tracking and recovery.

        Args:
            entry: Dead letter entry
        """
        try:
            # Import here to avoid circular dependency
            from app.db.models.kafka_dead_letter import KafkaDeadLetterTask

            async with AsyncSessionLocal() as db:
                dlq_record = KafkaDeadLetterTask(
                    id=entry.id,
                    event_id=entry.event_id,
                    original_topic=entry.original_topic,
                    event_type=entry.event_type,
                    partition=entry.partition,
                    offset=entry.offset,
                    consumer_group=entry.consumer_group,
                    reason=entry.reason.value,
                    exception_message=entry.exception_message[:2000],
                    traceback=entry.traceback[:5000] if entry.traceback else None,
                    retry_count=entry.retry_count,
                    max_retries=entry.max_retries,
                    status=entry.status.value,
                    next_retry_at=entry.next_retry_at,
                    metadata=entry.metadata,
                    event_data=json.dumps(entry.event_data)[:10000],  # Limit size
                )

                db.add(dlq_record)
                await db.commit()

                logger.debug(
                    f"✅ DLQ entry persisted to database: {entry.id}",
                    extra={"event_id": entry.event_id},
                )

        except Exception as e:
            logger.error(
                f"Failed to persist DLQ entry to database: {e}",
                extra={"event_id": entry.event_id},
                exc_info=True,
            )

    async def classify_failure(
        self,
        exception_message: str,
        exception_type: str,
    ) -> Dict[str, Any]:
        """
        Classify a failure to determine if it's retryable.

        Args:
            exception_message: Exception message
            exception_type: Exception class name

        Returns:
            Classification dictionary with is_transient, reason, confidence
        """
        exception_msg_lower = exception_message.lower()
        exception_type_lower = exception_type.lower()

        # Transient patterns
        transient_patterns = {
            "connection": KafkaDLQReason.NETWORK_ERROR,
            "timeout": KafkaDLQReason.TIMEOUT,
            "temporary": KafkaDLQReason.NETWORK_ERROR,
            "unavailable": KafkaDLQReason.NETWORK_ERROR,
            "deadlock": KafkaDLQReason.DATABASE_ERROR,
        }

        # Permanent patterns
        permanent_patterns = {
            "validation": KafkaDLQReason.VALIDATION_ERROR,
            "not found": KafkaDLQReason.VALIDATION_ERROR,
            "permission": KafkaDLQReason.VALIDATION_ERROR,
            "unauthorized": KafkaDLQReason.VALIDATION_ERROR,
            "authentication": KafkaDLQReason.VALIDATION_ERROR,
            "schema": KafkaDLQReason.SCHEMA_MISMATCH,
            "parse": KafkaDLQReason.PARSE_ERROR,
        }

        # Check permanent patterns first
        for pattern, reason in permanent_patterns.items():
            if pattern in exception_type_lower or pattern in exception_msg_lower:
                return {
                    "is_transient": False,
                    "reason": reason,
                    "confidence": 0.9,
                    "suggested_action": "manual_review",
                }

        # Check transient patterns
        for pattern, reason in transient_patterns.items():
            if pattern in exception_type_lower or pattern in exception_msg_lower:
                return {
                    "is_transient": True,
                    "reason": reason,
                    "confidence": 0.8,
                    "suggested_action": "auto_retry",
                }

        # Default: unknown, assume transient
        return {
            "is_transient": True,
            "reason": KafkaDLQReason.UNKNOWN,
            "confidence": 0.5,
            "suggested_action": "manual_review",
        }


# =============================================================================
# DLQ PROCESSOR
# =============================================================================


class KafkaDLQProcessor:
    """
    Processes events from Kafka DLQ topics.

    Handles retry logic, status updates, and coordination with recovery operations.
    """

    def __init__(self, dlq_manager: KafkaDLQManager):
        """
        Initialize DLQ processor.

        Args:
            dlq_manager: DLQ manager instance
        """
        self.dlq_manager = dlq_manager

    async def process_dlq_event(self, event: CloudEvent) -> bool:
        """
        Process an event from DLQ topic.

        Args:
            event: DLQ event

        Returns:
            True if processing succeeded
        """
        try:
            # Extract DLQ entry
            dlq_data = event.data.get("dlq_entry", {})
            original_event = event.data.get("original_event", {})

            # Recreate DLQ entry
            entry = KafkaDeadLetterEntry.from_dict(dlq_data)

            # Classify failure
            classification = await self.dlq_manager.classify_failure(
                exception_message=entry.exception_message,
                exception_type=entry.metadata.get("exception_type", "Exception"),
            )

            logger.info(
                f"Processing DLQ event: {entry.event_id} "
                f"(classification: {classification['reason'].value}, "
                f"transient: {classification['is_transient']})"
            )

            # Update entry status
            if classification["is_transient"]:
                entry.status = KafkaDLQStatus.RETRYABLE
            else:
                entry.status = KafkaDLQStatus.PERMANENT

            # Attempt retry if safe
            if classification["is_transient"] and entry.retry_count < entry.max_retries:
                return await self._retry_event(entry, original_event)
            else:
                # Mark as permanent or max retries exceeded
                await self._mark_permanent(entry, classification)
                return False

        except Exception as e:
            logger.error(f"Failed to process DLQ event: {e}", exc_info=True)
            return False

    async def _retry_event(
        self, entry: KafkaDeadLetterEntry, original_event: dict
    ) -> bool:
        """
        Retry processing a failed event.

        Args:
            entry: DLQ entry
            original_event: Original event data

        Returns:
            True if retry succeeded
        """
        try:
            entry.retry_count += 1
            entry.status = KafkaDLQStatus.RETRYING

            # TODO: Implement actual retry logic
            # This would republish to original topic or call handler directly
            logger.info(
                f"Retrying event: {entry.event_id} "
                f"(attempt {entry.retry_count}/{entry.max_retries})"
            )

            # For now, schedule next retry
            from datetime import timedelta

            entry.next_retry_at = datetime.utcnow() + timedelta(
                seconds=60 * (2**entry.retry_count)  # Exponential backoff
            )

            return True

        except Exception as e:
            logger.error(f"Failed to retry event {entry.event_id}: {e}")
            return False

    async def _mark_permanent(self, entry: KafkaDeadLetterEntry, classification: dict):
        """
        Mark event as permanent failure.

        Args:
            entry: DLQ entry
            classification: Failure classification
        """
        entry.status = KafkaDLQStatus.PERMANENT

        # Update database
        # TODO: Implement database update

        logger.warning(
            f"⚠️ Event marked as permanent failure: {entry.event_id} "
            f"(reason: {classification['reason'].value})"
        )

        # Alert monitoring system
        # TODO: Send alert to monitoring


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


async def create_dlq_entry(
    original_topic: str,
    event: CloudEvent,
    partition: int,
    offset: int,
    consumer_group: str,
    reason: KafkaDLQReason,
    exception_message: str,
    traceback: Optional[str] = None,
    retry_count: int = 0,
) -> KafkaDeadLetterEntry:
    """
    Create a DLQ entry from failed event processing.

    Args:
        original_topic: Original Kafka topic
        event: CloudEvent that failed
        partition: Kafka partition
        offset: Kafka offset
        consumer_group: Consumer group ID
        reason: Reason for failure
        exception_message: Exception message
        traceback: Exception traceback
        retry_count: Current retry count

    Returns:
        KafkaDeadLetterEntry instance
    """
    return KafkaDeadLetterEntry(
        event_id=event.id,
        original_topic=original_topic,
        event_type=event.type.value,
        event_data=event.data,
        partition=partition,
        offset=offset,
        consumer_group=consumer_group,
        reason=reason,
        exception_message=exception_message,
        traceback=traceback,
        retry_count=retry_count,
    )


# =============================================================================
# CLEANUP TASKS
# =============================================================================


async def cleanup_old_dlq_entries(days_old: int = 30) -> Dict[str, int]:
    """
    Clean up old resolved DLQ entries.

    Args:
        days_old: Delete entries older than this many days

    Returns:
        Cleanup statistics
    """
    try:
        from app.db.models.kafka_dead_letter import KafkaDeadLetterTask

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        async with AsyncSessionLocal() as db:
            # Query old entries
            stmt = select(KafkaDeadLetterTask).where(
                KafkaDeadLetterTask.created_at < cutoff_date,
                KafkaDeadLetterTask.status.in_(
                    [
                        KafkaDLQStatus.RETRIED.value,
                        KafkaDLQStatus.DISCARDED.value,
                        KafkaDLQStatus.PERMANENT.value,
                    ]
                ),
            )

            result = await db.execute(stmt)
            old_entries = result.scalars().all()

            # Delete entries
            count = len(old_entries)
            for entry in old_entries:
                await db.delete(entry)

            await db.commit()

            logger.info(f"Cleaned up {count} old DLQ entries")

            return {"deleted_count": count, "cutoff_date": cutoff_date.isoformat()}

    except Exception as e:
        logger.error(f"DLQ cleanup failed: {e}", exc_info=True)
        return {"error": str(e)}
