"""
Kafka Event Consumer

Consumes events from Kafka topics and routes to handlers.
Supports consumer groups, offset management, and error handling.

Created: 2025-01-12
Author: Architecture Team
"""

import logging
from typing import Dict, List, Optional

from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.events.schemas import CloudEvent, EventType

logger = logging.getLogger(__name__)


class EventHandler:
    """
    Base event handler interface.

    All event handlers should inherit from this class.
    """

    async def handle(self, event: CloudEvent, db: Optional[AsyncSession] = None):
        """
        Handle event.

        Args:
            event: CloudEvent to process
            db: Optional database session
        """
        raise NotImplementedError("Subclasses must implement handle()")


class KafkaEventConsumer:
    """
    Kafka consumer for processing events.

    Features:
    - Consumer group support (for load balancing)
    - Automatic offset management
    - Event routing to handlers
    - Error handling and retries
    - Graceful shutdown

    Usage:
        consumer = KafkaEventConsumer(
            topics=["assessment-events"],
            group_id="analytics-service"
        )

        # Register handlers
        consumer.register_handler(EventType.ASSESSMENT_COMPLETED, AssessmentCompletedHandler())

        # Start consuming
        await consumer.start()
        await consumer.consume()  # Blocks until shutdown

        await consumer.stop()
    """

    def __init__(
        self,
        topics: List[str],
        group_id: str,
        bootstrap_servers: Optional[str] = None,
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = False,  # ✅ FIX: Changed from True to False
        session_timeout_ms: int = 30000,  # 30 seconds
        heartbeat_interval_ms: int = 3000,  # 3 seconds
        max_poll_records: int = 100,
        commit_after_processing: bool = True,  # ✅ NEW: Commit after successful processing
    ):
        """
        Initialize Kafka consumer.

        Args:
            topics: List of topics to consume
            group_id: Consumer group ID
            bootstrap_servers: Kafka servers (default: from settings)
            auto_offset_reset: Where to start if no offset (earliest, latest)
            enable_auto_commit: Auto-commit offsets (default: False for reliability)
            session_timeout_ms: Session timeout
            heartbeat_interval_ms: Heartbeat interval
            max_poll_records: Max records per poll
            commit_after_processing: Manually commit after successful processing
        """
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self.auto_offset_reset = auto_offset_reset
        self.enable_auto_commit = enable_auto_commit
        self.session_timeout_ms = session_timeout_ms
        self.heartbeat_interval_ms = heartbeat_interval_ms
        self.max_poll_records = max_poll_records
        self.commit_after_processing = commit_after_processing

        self.consumer: Optional[AIOKafkaConsumer] = None
        self.handlers: Dict[EventType, List[EventHandler]] = {}
        self._running = False
        self._processed_messages = (
            []
        )  # ✅ NEW: Track processed messages for manual commit

        logger.info(
            f"KafkaEventConsumer initialized: topics={topics}, group_id={group_id}, "
            f"auto_commit={enable_auto_commit}, commit_after_processing={commit_after_processing}"
        )

    def register_handler(
        self,
        event_type: EventType,
        handler: EventHandler,
    ):
        """
        Register event handler for event type.

        Multiple handlers can be registered for the same event type.

        Args:
            event_type: Event type to handle
            handler: Event handler instance
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []

        self.handlers[event_type].append(handler)
        logger.info(
            f"Registered handler for {event_type.value}: {handler.__class__.__name__}"
        )

    async def start(self):
        """Start the Kafka consumer."""
        try:
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset=self.auto_offset_reset,
                enable_auto_commit=self.enable_auto_commit,
                session_timeout_ms=self.session_timeout_ms,
                heartbeat_interval_ms=self.heartbeat_interval_ms,
                max_poll_records=self.max_poll_records,
                # Deserialization
                value_deserializer=lambda m: m.decode("utf-8") if m else None,
                auto_commit_interval_ms=1000,  # Commit every second
            )

            await self.consumer.start()
            logger.info(
                f"✅ Kafka consumer started: topics={self.topics}, group_id={self.group_id}, "
                f"auto_commit={self.enable_auto_commit}"
            )

        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise

    async def stop(self):
        """Stop the Kafka consumer."""
        self._running = False

        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")

    async def consume(self):
        """
        Consume events from Kafka.

        This method blocks until stop() is called.
        Events are dispatched to registered handlers.
        """
        if not self.consumer:
            raise RuntimeError("Consumer not started. Call start() first.")

        self._running = True
        logger.info("Starting to consume events...")

        try:
            async for msg in self.consumer:
                if not self._running:
                    break

                await self._process_message(msg)

        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            raise

    async def _process_message(self, msg):
        """
        Process single message from Kafka.

        Args:
            msg: Kafka message
        """
        try:
            # Parse event
            event_data = msg.value
            event = CloudEvent.parse_raw(event_data)

            logger.debug(
                f"Received event: {event.type.value} "
                f"(topic={msg.topic}, partition={msg.partition}, offset={msg.offset})"
            )

            # Get handlers for event type
            handlers = self.handlers.get(event.type, [])

            if not handlers:
                logger.warning(
                    f"No handlers registered for event type: {event.type.value}"
                )
                # Still commit if no handlers (message successfully consumed but nothing to do)
                if self.commit_after_processing:
                    await self.consumer.commit()
                return

            # Dispatch to all handlers
            all_handlers_succeeded = True
            for handler in handlers:
                try:
                    await handler.handle(event)
                    logger.debug(f"Event handled by {handler.__class__.__name__}")

                except Exception as e:
                    all_handlers_succeeded = False
                    logger.error(
                        f"Handler {handler.__class__.__name__} failed for event "
                        f"{event.type.value}: {e}",
                        exc_info=True,
                    )
                    # Continue processing with other handlers

            # ✅ FIX: Only commit after all handlers succeed
            if self.commit_after_processing and all_handlers_succeeded:
                # Commit the offset for this message
                await self.consumer.commit({msg.partition: msg.offset + 1})
                logger.debug(
                    f"Committed offset for event {event.type.value} "
                    f"(partition={msg.partition}, offset={msg.offset})"
                )
            elif not all_handlers_succeeded:
                # Handler failed, don't commit - message will be reprocessed
                logger.warning(
                    f"⚠️ Not committing offset due to handler failure - "
                    f"message will be reprocessed "
                    f"(topic={msg.topic}, partition={msg.partition}, offset={msg.offset})"
                )

        except Exception as e:
            logger.error(f"Failed to process message: {e}", exc_info=True)
            # Don't commit on parse errors - message will be reprocessed
            if self.commit_after_processing:
                logger.warning(
                    f"⚠️ Not committing offset due to processing error - "
                    f"message will be reprocessed"
                )


class BatchEventConsumer(KafkaEventConsumer):
    """
    Batch consumer for processing events in batches.

    More efficient for high-throughput scenarios.
    Batches events before processing.
    """

    def __init__(
        self, *args, batch_size: int = 10, batch_timeout_ms: int = 1000, **kwargs
    ):
        """
        Initialize batch consumer.

        Args:
            batch_size: Number of events to batch
            batch_timeout_ms: Max time to wait for batch (ms)
        """
        super().__init__(*args, **kwargs)
        self.batch_size = batch_size
        self.batch_timeout_ms = batch_timeout_ms

    async def consume(self):
        """
        Consume and batch events.

        Events are collected into batches and processed together.
        """
        if not self.consumer:
            raise RuntimeError("Consumer not started. Call start() first.")

        self._running = True
        logger.info(f"Starting batch consumer (batch_size={self.batch_size})...")

        try:
            batch = []

            async for msg in self.consumer:
                if not self._running:
                    break

                batch.append(msg)

                # Process batch when full
                if len(batch) >= self.batch_size:
                    await self._process_batch(batch)
                    batch = []

            # Process remaining messages
            if batch:
                await self._process_batch(batch)

        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            raise

    async def _process_batch(self, batch: List):
        """
        Process batch of messages.

        Args:
            batch: List of Kafka messages
        """
        logger.info(f"Processing batch of {len(batch)} messages")

        events = []
        failed_messages = []  # ✅ NEW: Track failed messages for DLQ

        for msg in batch:
            try:
                event_data = msg.value
                event = CloudEvent.parse_raw(event_data)
                events.append((event, msg))  # ✅ NEW: Keep message reference for commit
            except Exception as e:
                logger.error(f"Failed to parse message in batch: {e}")
                # ✅ NEW: Track parse failures
                failed_messages.append((msg, "parse_error", str(e)))

        # Process events
        processed_events = []
        for event, msg in events:
            handlers = self.handlers.get(event.type, [])
            all_succeeded = True

            for handler in handlers:
                try:
                    await handler.handle(event)
                except Exception as e:
                    all_succeeded = False
                    logger.error(
                        f"Handler {handler.__class__.__name__} failed for event "
                        f"{event.type.value}: {e}"
                    )
                    # ✅ NEW: Track handler failures
                    failed_messages.append((msg, "handler_error", str(e)))

            if all_succeeded:
                processed_events.append(msg)

        # ✅ FIX: Only commit successfully processed messages
        if self.commit_after_processing and processed_events:
            # Build commit map: partition -> list of offsets
            commit_map = {}
            for msg in processed_events:
                if msg.partition not in commit_map:
                    commit_map[msg.partition] = []
                commit_map[msg.partition].append(msg.offset + 1)

            # Commit the highest offset for each partition
            final_commit_map = {
                partition: max(offsets) for partition, offsets in commit_map.items()
            }

            await self.consumer.commit(final_commit_map)
            logger.info(
                f"✅ Committed {len(processed_events)} messages in batch, "
                f"{len(failed_messages)} failed"
            )

        # ✅ NEW: Handle failed messages (send to DLQ or log)
        if failed_messages:
            logger.warning(
                f"⚠️ {len(failed_messages)} messages failed in batch, "
                f"offsets not committed - will be reprocessed"
            )
            # TODO: Send to Kafka DLQ for failed events
            # await self._send_failed_to_dlq(failed_messages)


# ============================================
# EXAMPLE HANDLERS
# ============================================


class AssessmentCompletedHandler(EventHandler):
    """
    Example handler for assessment.completed events.

    Updates analytics when assessment is completed.
    """

    async def handle(self, event: CloudEvent, db: Optional[AsyncSession] = None):
        """Handle assessment completion."""
        logger.info(f"Processing assessment completion: {event.data['assessment_id']}")

        # Extract data
        event.data.get("assessment_id")
        user_id = event.data.get("user_id")
        event.data.get("score")

        # Update analytics (in real implementation)
        # await analytics_service.update_user_metrics(user_id, score)

        logger.info(f"Updated analytics for user {user_id}")


class UserRegisteredHandler(EventHandler):
    """
    Example handler for user.registered events.

    Sends welcome email when user registers.
    """

    async def handle(self, event: CloudEvent, db: Optional[AsyncSession] = None):
        """Handle user registration."""
        logger.info(f"Processing user registration: {event.data['email']}")

        # Extract data
        email = event.data.get("email")
        event.data.get("full_name")

        # Send welcome email (in real implementation)
        # await email_service.send_welcome(email, full_name)

        logger.info(f"Welcome email sent to {email}")


class TeamCreatedHandler(EventHandler):
    """
    Example handler for team.created events.

    Initializes team analytics.
    """

    async def handle(self, event: CloudEvent, db: Optional[AsyncSession] = None):
        """Handle team creation."""
        logger.info(f"Processing team creation: {event.data['team_id']}")

        # Extract data
        team_id = event.data.get("team_id")
        event.data.get("organization_id")

        # Initialize team analytics (in real implementation)
        # await analytics_service.initialize_team_analytics(team_id, organization_id)

        logger.info(f"Initialized analytics for team {team_id}")


# ============================================
# CONSUMER FACTORY
# ============================================


async def create_consumer(
    topics: List[str],
    group_id: str,
    handlers: Dict[EventType, List[EventHandler]],
    batch_mode: bool = False,
) -> KafkaEventConsumer:
    """
    Create and configure Kafka consumer.

    Usage:
        consumer = await create_consumer(
            topics=["assessment-events"],
            group_id="analytics-service",
            handlers={
                EventType.ASSESSMENT_COMPLETED: [AssessmentCompletedHandler()],
                EventType.ASSESSMENT_STARTED: [AssessmentStartedHandler()],
            }
        )

        await consumer.start()
        await consumer.consume()

    Args:
        topics: Topics to consume
        group_id: Consumer group ID
        handlers: Event type → handlers mapping
        batch_mode: Use batch processing

    Returns:
        Configured consumer instance
    """
    if batch_mode:
        consumer = BatchEventConsumer(
            topics=topics,
            group_id=group_id,
        )
    else:
        consumer = KafkaEventConsumer(
            topics=topics,
            group_id=group_id,
        )

    # Register handlers
    for event_type, handler_list in handlers.items():
        for handler in handler_list:
            consumer.register_handler(event_type, handler)

    return consumer
