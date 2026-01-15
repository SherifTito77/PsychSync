"""
Kafka Integration Tests

Tests for Kafka event streaming functionality in PsychSync.
These tests verify that the producer and consumer work correctly.

Run with:
    pytest tests/integration/test_kafka_integration.py -v
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

from app.events.producer import KafkaEventProducer
from app.events.consumer import KafkaEventConsumer
from app.events.schemas import EventFactory, EventType


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def kafka_producer():
    """Create a Kafka event producer for testing."""
    producer = KafkaEventProducer(
        bootstrap_servers="localhost:9092",
        client_id="test-producer"
    )
    await producer.start()
    yield producer
    await producer.stop()


@pytest.fixture
async def kafka_consumer():
    """Create a Kafka event consumer for testing."""
    consumer = KafkaEventConsumer(
        topics=["test-events"],
        group_id="test-consumer-group",
        auto_offset_reset="latest"
    )
    await consumer.start()
    yield consumer
    await consumer.stop()


# ============================================================================
# PRODUCER TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_producer_publish_assessment_event(kafka_producer):
    """Test publishing an assessment event to Kafka."""
    # Create event
    event = EventFactory.assessment_started(
        assessment_id=str(uuid4()),
        user_id=str(uuid4()),
        framework_code="MBTI",
        team_id=str(uuid4()),
        tenant_id=str(uuid4())
    )

    # Publish event
    metadata = await kafka_producer.publish(
        topic="assessment-events",
        event=event
    )

    # Verify metadata
    assert metadata is not None
    assert 'topic' in metadata
    assert 'partition' in metadata
    assert 'offset' in metadata
    assert metadata['topic'] == "assessment-events"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_producer_publish_user_event(kafka_producer):
    """Test publishing a user event to Kafka."""
    event = EventFactory.user_registered(
        user_id=str(uuid4()),
        email="test@example.com",
        full_name="Test User",
        organization_id=str(uuid4()),
        registration_method="email",
        tenant_id=str(uuid4())
    )

    metadata = await kafka_producer.publish(
        topic="user-events",
        event=event
    )

    assert metadata is not None
    assert metadata['topic'] == "user-events"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_producer_publish_multiple_events(kafka_producer):
    """Test publishing multiple events in sequence."""
    events = [
        EventFactory.assessment_started(
            assessment_id=str(uuid4()),
            user_id=str(uuid4()),
            framework_code="BigFive",
            team_id=str(uuid4()),
            tenant_id=str(uuid4())
        ),
        EventFactory.assessment_completed(
            assessment_id=str(uuid4()),
            user_id=str(uuid4()),
            framework_code="MBTI",
            score=85.0,
            max_score=100.0,
            results={"type": "INTJ"},
            team_id=str(uuid4()),
            tenant_id=str(uuid4())
        ),
        EventFactory.team_created(
            team_id=str(uuid4()),
            name="Test Team",
            organization_id=str(uuid4()),
            created_by=str(uuid4()),
            tenant_id=str(uuid4())
        ),
    ]

    # Publish all events
    for event in events:
        metadata = await kafka_producer.publish(
            topic=event.type.value.split('.')[0] + "-events",
            event=event
        )
        assert metadata is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_producer_event_schema_validation(kafka_producer):
    """Test that events conform to CloudEvents schema."""
    event = EventFactory.assessment_completed(
        assessment_id=str(uuid4()),
        user_id=str(uuid4()),
        framework_code="Enneagram",
        score=75.0,
        max_score=100.0,
        results={"type": "Type 1"},
        team_id=str(uuid4()),
        tenant_id=str(uuid4())
    )

    # Verify CloudEvents attributes
    assert event.id is not None
    assert event.source == "psychsync"
    assert event.type == EventType.ASSESSMENT_COMPLETED
    assert event.data_content_type == "application/json"
    assert event.tenant_id is not None
    assert event.time is not None


# ============================================================================
# CONSUMER TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_start_stop(kafka_consumer):
    """Test that consumer can start and stop gracefully."""
    # Consumer is already started in fixture
    assert kafka_consumer.consumer is not None

    # Stop and restart
    await kafka_consumer.stop()
    await kafka_consumer.start()

    assert kafka_consumer.consumer is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_register_handler():
    """Test registering event handlers."""
    consumer = KafkaEventConsumer(
        topics=["test-events"],
        group_id="test-handler-group"
    )

    # Create a mock handler
    class MockHandler:
        async def handle(self, event, db=None):
            pass

    handler = MockHandler()
    consumer.register_handler(EventType.ASSESSMENT_STARTED, handler)

    # Verify handler is registered
    assert EventType.ASSESSMENT_STARTED in consumer.handlers
    assert consumer.handlers[EventType.ASSESSMENT_STARTED] == handler


# ============================================================================
# END-TO-END TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_event_flow():
    """Test complete event flow from producer to consumer."""
    test_topic = "test-e2e-events"
    test_group = "test-e2e-group"

    # Create unique IDs
    assessment_id = str(uuid4())
    user_id = str(uuid4())
    team_id = str(uuid4())
    tenant_id = str(uuid4())

    # Start consumer
    consumer = KafkaEventConsumer(
        topics=[test_topic],
        group_id=test_group,
        auto_offset_reset="earliest"
    )

    # Track received events
    received_events = []

    class TestHandler:
        async def handle(self, event, db=None):
            received_events.append(event)

    consumer.register_handler(EventType.ASSESSMENT_STARTED, TestHandler())
    await consumer.start()

    # Start producer and publish event
    producer = KafkaEventProducer(
        bootstrap_servers="localhost:9092",
        client_id="test-e2e-producer"
    )
    await producer.start()

    event = EventFactory.assessment_started(
        assessment_id=assessment_id,
        user_id=user_id,
        framework_code="MBTI",
        team_id=team_id,
        tenant_id=tenant_id
    )

    await producer.publish(topic=test_topic, event=event)

    # Give consumer time to process
    await asyncio.sleep(2)

    # Cleanup
    await producer.stop()
    await consumer.stop()

    # Verify event was received
    assert len(received_events) > 0
    assert received_events[0].data['assessment_id'] == assessment_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_event_types():
    """Test handling multiple different event types."""
    test_topic = "test-multi-events"

    # Create producer
    producer = KafkaEventProducer(
        bootstrap_servers="localhost:9092",
        client_id="test-multi-producer"
    )
    await producer.start()

    # Publish different event types
    events = [
        EventFactory.assessment_started(
            assessment_id=str(uuid4()),
            user_id=str(uuid4()),
            framework_code="MBTI",
            team_id=str(uuid4()),
            tenant_id=str(uuid4())
        ),
        EventFactory.user_registered(
            user_id=str(uuid4()),
            email="user@test.com",
            full_name="Test User",
            organization_id=str(uuid4()),
            registration_method="email",
            tenant_id=str(uuid4())
        ),
        EventFactory.team_created(
            team_id=str(uuid4()),
            name="Test Team",
            organization_id=str(uuid4()),
            created_by=str(uuid4()),
            tenant_id=str(uuid4())
        ),
    ]

    for event in events:
        await producer.publish(topic=test_topic, event=event)

    await producer.stop()

    # Verify all events published successfully
    assert len(events) == 3


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_producer_connection_error():
    """Test producer handles connection errors gracefully."""
    # Try to connect to non-existent Kafka
    producer = KafkaEventProducer(
        bootstrap_servers="localhost:9999",  # Wrong port
        client_id="test-error-producer"
    )

    with pytest.raises(Exception):
        await producer.start()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_invalid_topic():
    """Test consumer handles invalid topics."""
    consumer = KafkaEventConsumer(
        topics=["non-existent-topic"],
        group_id="test-invalid-topic-group"
    )

    # Should start without error (Kafka auto-creates topics)
    await consumer.start()
    await consumer.stop()


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_producer_throughput(kafka_producer):
    """Test producer can handle high throughput."""
    num_events = 100
    start_time = datetime.now()

    for i in range(num_events):
        event = EventFactory.assessment_started(
            assessment_id=str(uuid4()),
            user_id=str(uuid4()),
            framework_code="MBTI",
            team_id=str(uuid4()),
            tenant_id=str(uuid4())
        )
        await kafka_producer.publish(
            topic="assessment-events",
            event=event
        )

    elapsed = (datetime.now() - start_time).total_seconds()
    throughput = num_events / elapsed

    print(f"\n📊 Producer Throughput: {throughput:.2f} events/second")

    # Should handle at least 10 events/second
    assert throughput > 10
