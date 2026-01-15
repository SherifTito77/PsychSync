#!/usr/bin/env python
"""
Kafka Event Consumer Example

Demonstrates how to consume events from Kafka for the PsychSync platform.
This example listens for assessment events and processes them.

Usage:
    python -m app.events.example_consumer
"""

import asyncio
import signal
from datetime import datetime

from app.events.consumer import KafkaEventConsumer, EventHandler
from app.events.schemas import EventType, CloudEvent


class AssessmentEventHandler(EventHandler):
    """Example handler for assessment events."""

    async def handle(self, event: CloudEvent, db=None):
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Handle assessment event."""
        timestamp = datetime.utcnow().isoformat()

        print(f"\n[{timestamp}] 📨 Event Received")
        print(f"   Type: {event.type.value}")
        print(f"   ID: {event.id}")
        print(f"   Source: {event.source}")
        print(f"   Tenant: {event.tenant_id}")

        # Display event data
        if event.type == EventType.ASSESSMENT_STARTED:
            print(f"   Assessment: {event.data.get('assessment_id')} started")
            print(f"   Framework: {event.data.get('framework_code')}")
            print(f"   User: {event.data.get('user_id')}")

        elif event.type == EventType.ASSESSMENT_COMPLETED:
            print(f"   Assessment: {event.data.get('assessment_id')} completed")
            print(f"   Framework: {event.data.get('framework_code')}")
            print(f"   Score: {event.data.get('score')}/{event.data.get('max_score')}")
            print(f"   Results: {event.data.get('results')}")

        print(f"   Raw Data: {event.data}")

        # Simulate processing
        await asyncio.sleep(0.1)

        print(f"   ✅ Event processed")


class UserEventHandler(EventHandler):
    """Example handler for user events."""

    async def handle(self, event: CloudEvent, db=None):
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Handle user event."""
        timestamp = datetime.utcnow().isoformat()

        print(f"\n[{timestamp}] 👤 User Event")
        print(f"   Type: {event.type.value}")
        print(f"   Email: {event.data.get('email')}")
        print(f"   Name: {event.data.get('full_name')}")
        print(f"   ✅ User event processed")


class TeamEventHandler(EventHandler):
    """Example handler for team events."""

    async def handle(self, event: CloudEvent, db=None):
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Handle team event."""
        timestamp = datetime.utcnow().isoformat()

        print(f"\n[{timestamp}] 👥 Team Event")
        print(f"   Type: {event.type.value}")
        print(f"   Team: {event.data.get('name')}")
        print(f"   Created by: {event.data.get('created_by')}")
        print(f"   ✅ Team event processed")


class SignalHandler:
    """Handle shutdown signals gracefully."""

    def __init__(self):
        self.shutdown = False

    def signal_handler(self, signum, frame):
        """Handle interrupt signal."""
        print(f"\n\nReceived signal {signum}, shutting down gracefully...")
        self.shutdown = True


async def main():
    """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
    """
    """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
    """
    """Consume events from Kafka."""

    print("\n" + "="*80)
    print("KAFKA EVENT CONSUMER - PsychSync")
    print("="*80)
    print("\nListening for events...")
    print("Press Ctrl+C to stop\n")

    # Create consumer
    consumer = KafkaEventConsumer(
        topics=[
            "assessment-events",
            "user-events",
            "team-events",
            "organization-events",
            "analytics-events",
            "billing-events",
            "notification-events",
            "system-events"
        ],
        group_id="psychsync-example-consumer",
        auto_offset_reset="earliest"
    )

    # Register event handlers
    consumer.register_handler(EventType.ASSESSMENT_STARTED, AssessmentEventHandler())
    consumer.register_handler(EventType.ASSESSMENT_COMPLETED, AssessmentEventHandler())
    consumer.register_handler(EventType.USER_REGISTERED, UserEventHandler())
    consumer.register_handler(EventType.USER_ACTIVATED, UserEventHandler())
    consumer.register_handler(EventType.TEAM_CREATED, TeamEventHandler())

    # Setup signal handler for graceful shutdown
    signal_handler = SignalHandler()
    import signal
    signal.signal(signal.SIGINT, signal_handler.signal_handler)
    signal.signal(signal.SIGTERM, signal_handler.signal_handler)

    # Start consumer
    await consumer.start()
    print("✅ Consumer started\n")

    # Consume events
    try:
        await consumer.consume()
    except Exception as e:
        print(f"\n❌ Error consuming events: {e}")
    finally:
        await consumer.stop()
        print("\n" + "="*80)
        print("✅ Consumer stopped")
        print("="*80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nStopped by user")
