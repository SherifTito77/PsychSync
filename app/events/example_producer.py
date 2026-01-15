#!/usr/bin/env python
"""
Kafka Event Producer Example

Demonstrates how to publish events to Kafka for the PsychSync platform.
This example publishes assessment completion events.

Usage:
    python -m app.events.example_producer
"""

import asyncio
import json
from datetime import datetime
from uuid import uuid4

from app.events.schemas import EventFactory
from app.events.producer import KafkaEventProducer


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
    """Publish example events to Kafka."""

    print("\n" + "="*80)
    print("KAFKA EVENT PRODUCER - PsychSync")
    print("="*80)

    # Create producer
    producer = KafkaEventProducer(
        bootstrap_servers="localhost:9092",
        client_id="psychsync-example-producer"
    )

    await producer.start()
    print("✅ Producer started\n")

    # Publish example events
    events_to_publish = [
        # Assessment events
        EventFactory.assessment_started(
            assessment_id=str(uuid4()),
            user_id=str(uuid4()),
            framework_code="MBTI",
            team_id=str(uuid4()),
            tenant_id=str(uuid4())
        ),
        EventFactory.assessment_completed(
            assessment_id=str(uuid4()),
            user_id=str(uuid4()),
            framework_code="BigFive",
            score=85.0,
            max_score=100.0,
            results={"trait": "Openness", "percentile": 85},
            team_id=str(uuid4()),
            tenant_id=str(uuid4())
        ),

        # User events
        EventFactory.user_registered(
            user_id=str(uuid4()),
            email="user@example.com",
            full_name="Example User",
            organization_id=str(uuid4()),
            registration_method="email",
            tenant_id=str(uuid4())
        ),

        # Team events
        EventFactory.team_created(
            team_id=str(uuid4()),
            name="Engineering Team",
            organization_id=str(uuid4()),
            created_by=str(uuid4()),
            tenant_id=str(uuid4())
        ),
    ]

    print(f"Publishing {len(events_to_publish)} events...\n")

    for i, event in enumerate(events_to_publish, 1):
        try:
            metadata = await producer.publish(
                topic=event.type.value.split('.')[0] + "-events",
                event=event
            )

            print(f"{i}. ✅ {event.type.value}")
            print(f"   Topic: {metadata['topic']}")
            print(f"   Partition: {metadata['partition']}")
            print(f"   Offset: {metadata['offset']}")
            print(f"   Data: {json.dumps(event.data, indent=2)}")
            print()

        except Exception as e:
            print(f"{i}. ❌ Failed to publish {event.type.value}: {e}")
            print()

    # Wait for messages to be delivered
    await asyncio.sleep(2)

    # Stop producer
    await producer.stop()
    print("="*80)
    print("✅ Event publishing complete!")
    print("="*80)
    print("\nYou can now consume these events with:")
    print("  python -m app.events.example_consumer")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nStopped by user")
