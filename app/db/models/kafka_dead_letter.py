"""
Kafka Dead Letter Task Model

Stores failed Kafka events for analysis, retry, and monitoring.
This enables comprehensive failure tracking and recovery for Kafka events.

Author: Infrastructure Team
Version: 1.0.0
Date: February 9, 2026
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID

from app.db.base_class import Base

logger = logging.getLogger(__name__)


class KafkaDeadLetterTask(Base):
    """
    Kafka Dead Letter Task - Failed Kafka event storage and tracking

    This model stores failed Kafka events for:
    - Analysis of failure patterns
    - Manual inspection and debugging
    - Automated retry with exponential backoff
    - Compliance and auditing requirements
    """

    __tablename__ = "kafka_dead_letter_tasks"

    # Primary identification
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    event_id = Column(String(255), nullable=False, unique=True, index=True)

    # Event information
    original_topic = Column(String(255), nullable=False, index=True)
    event_type = Column(String(255), nullable=False, index=True)
    partition = Column(Integer, nullable=False)
    offset = Column(Integer, nullable=False)
    consumer_group = Column(String(255), nullable=False, index=True)

    # Event data (truncated JSON)
    event_data = Column(Text)  # Serialized event data (truncated to 10000 chars)

    # Failure information
    reason = Column(String(100), nullable=False, index=True)  # KafkaDLQReason enum
    exception_message = Column(Text)  # Exception message
    traceback = Column(Text)  # Full exception traceback

    # Retry tracking
    retry_count = Column(Integer, nullable=False, default=0)  # Retry attempts
    max_retries = Column(Integer, nullable=False, default=3)  # Max retry attempts

    # Status and lifecycle
    status = Column(String(50), nullable=False, default="pending", index=True)
    next_retry_at = Column(DateTime, index=True)  # Scheduled next retry time
    resolved_at = Column(DateTime)  # When event was successfully retried or discarded

    # Additional metadata (JSON)
    event_metadata = Column(JSON)  # Additional context and debugging info

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_kafka_dlq_event_type_status", "event_type", "status"),
        Index("ix_kafka_dlq_reason_status", "reason", "status"),
        Index("ix_kafka_dlq_created_at_status", "created_at", "status"),
        Index("ix_kafka_dlq_next_retry_at", "next_retry_at"),
        Index("ix_kafka_dlq_consumer_group_status", "consumer_group", "status"),
    )

    def __repr__(self):
        return (
            f"<KafkaDeadLetterTask(id={self.id}, event_id={self.event_id}, "
            f"reason={self.reason}, status={self.status})>"
        )

    # ==========================================================================
    # DOMAIN LOGIC
    # ==========================================================================

    def can_retry(self) -> bool:
        """
        Check if this task can be retried.

        Returns:
            True if task can be retried, False otherwise
        """
        # Cannot retry if already resolved
        if self.status in ["retried", "discarded", "permanent"]:
            return False

        # Cannot retry if max retries exceeded
        if self.retry_count >= self.max_retries:
            return False

        # Check if scheduled retry time has passed
        if self.next_retry_at and self.next_retry_at > datetime.utcnow():
            return False

        return True

    def to_dict(self) -> dict:
        """
        Convert to dictionary for API responses.

        Returns:
            Dictionary representation of the DLQ entry
        """
        return {
            "id": str(self.id),
            "event_id": self.event_id,
            "original_topic": self.original_topic,
            "event_type": self.event_type,
            "partition": self.partition,
            "offset": self.offset,
            "consumer_group": self.consumer_group,
            "reason": self.reason,
            "exception_message": self.exception_message,
            "status": self.status,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "can_retry": self.can_retry(),
            "next_retry_at": (
                self.next_retry_at.isoformat() if self.next_retry_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
