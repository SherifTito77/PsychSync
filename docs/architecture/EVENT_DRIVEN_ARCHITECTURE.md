# Event-Driven Architecture Roadmap

**Version:** 1.0
**Date:** 2026-01-10
**Status:** Strategic Roadmap

---

## Executive Summary

This roadmap outlines PsychSync's transition from a synchronous request/response architecture to an event-driven architecture (EDA). This evolution enables:

- **Scalability:** Decoupled services can scale independently
- **Resilience:** Async processing prevents cascading failures
- **Observability:** Event streams provide complete audit trail
- **Flexibility:** Easy to add new consumers without modifying producers

---

## 1. Current Architecture Analysis

### 1.1 Existing Synchronous Flow

```
User Action → API Endpoint → Business Logic → Database → Response
                 ↓
            Business Logic
                 ↓
          (Email Service)
                 ↓
          (Slack Service)
                 ↓
          (Analytics Service)
```

**Problems:**
- ❌ Slow services block API response
- ❌ Service failures cascade to users
- ❌ Hard to add parallel consumers
- ❌ No event log for replay/debugging

---

## 2. Target Event-Driven Architecture

### 2.1 High-Level Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Event Producers                     │
│  (API Endpoints, Webhooks, Scheduled Jobs,            │
│   Third-Party Integrations, User Actions)             │
└────────────────────┬───────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│              Event Bus (Message Broker)                │
│                  ┌──────────────┐                      │
│                  │ Redis Streams │ (Phase 1)          │
│                  │              │                      │
│                  │ Kafka        │ (Phase 2-3)         │
│                  └──────────────┘                      │
│                                                          │
│  Features:                                               │
│  - Event streaming (real-time)                         │
│  - Message queuing (reliable delivery)                  │
│  - Event replay (debugging, replay)                     │
│  - Dead letter queues (error handling)                  │
└────────────────────┬───────────────────────────────┘
                     │
         ┌───────────┴──────────┐
         ▼                      ▼
┌──────────────────┐    ┌──────────────────┐
│  Event Consumers  │    │ Event Consumers  │
│                   │    │                   │
│ ┌───────────────┐ │    │ ┌───────────────┐ │
│ │ Notifications│ │    │ │ Analytics     │ │
│ │ Service       │ │    │ │ Service       │ │
│ └───────────────┘ │    │ └───────────────┘ │
│ ┌───────────────┐ │    │ ┌───────────────┐ │
│ │ Email         │ │    │ │ Webhook       │ │
│ │ Service       │ │    │ │ Service       │ │
│ └───────────────┘ │    │ └───────────────┘ │
│ ┌───────────────┐ │    │ ┌───────────────┐ │
│ │ Analytics     │ │    │ │ Search        │ │
│ │ Service       │ │    │ │ Service       │ │
│ └───────────────┘ │    │ └───────────────┘ │
└──────────────────┘    └──────────────────┘
```

---

## 3. Event Schema Design

### 3.1 Core Event Types

```python
# app/events/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

class BaseEvent(BaseModel):
    """Base event schema with metadata"""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    event_version: str = "1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Event sourcing metadata
    correlation_id: Optional[UUID] = None  # Links related events
    causation_id: Optional[UUID] = None   # Event that triggered this
    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    team_id: Optional[UUID] = None

    # Payload
    data: Dict[str, Any]

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Example Events
class AssessmentCompletedEvent(BaseEvent):
    """User completed an assessment"""
    event_type: str = "assessment.completed"

    # Expected data fields:
    # {
    #   "assessment_id": "uuid",
    #   "user_id": "uuid",
    #   "assessment_type": "big_five",
    #   "score": 85.5,
    #   "responses": 50,
    #   "duration_seconds": 300
    # }

class UserRegisteredEvent(BaseEvent):
    """New user registration"""
    event_type: str = "user.registered"

    # Expected data fields:
    # {
    #   "user_id": "uuid",
    #   "email": "user@example.com",
    #   "registration_source": "web",
    #   "plan": "free"
    # }

class TeamMemberAddedEvent(BaseEvent):
    """User added to team"""
    event_type: str = "team.member_added"

    # Expected data fields:
    # {
    #   "team_id": "uuid",
    #   "user_id": "uuid",
    #   "role": "member",
    #   "added_by": "uuid"
    # }

class AssessmentScoreCalculatedEvent(BaseEvent):
    """Assessment scoring completed"""
    event_type: str = "assessment.score_calculated"

    # Expected data fields:
    # {
    #   "response_id": "uuid",
    #   "user_id": "uuid",
    #   "assessment_id": "uuid",
    #   "scores": {"openness": 0.75, "conscientiousness": 0.82, ...}
    # }

class UserLoginEvent(BaseEvent):
    """User logged in"""
    event_type: str = "user.login"

    # Expected data fields:
    # {
    #   "user_id": "uuid",
    #   "login_method": "password",  # or "sso", "magic_link"
    #   "ip_address": "192.168.1.1",
    #   "user_agent": "Mozilla/5.0..."
    # }
```

### 3.2 Event Naming Convention

```
{domain}.{entity}.{action}

Examples:
- assessment.completed
- user.registered
- team.member_added
- team.member_removed
- notification.sent
- email.delivered
- analytics.metric_recorded
```

---

## 4. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-6)

**Goal:** Establish event infrastructure

#### 1.1 Event Bus Setup

```python
# app/events/bus.py
import asyncio
from typing import Callable, Awaitable
from dataclasses import dataclass
import redis.asyncio as aioredis

@dataclass
class EventBus:
    """Simple async event bus using Redis Streams"""

    def __init__(self):
        self.redis = None
        self.consumer_tasks = []

    async def connect(self):
        """Initialize Redis connection"""
        self.redis = await aioredis.from_url(
            "redis://localhost:6379/0",
            encoding="utf-8",
            decode_responses=True
        )

    async def publish(self, event: BaseEvent, stream_name: str = "events"):
        """Publish event to stream"""
        event_json = event.json()

        await self.redis.xadd(
            stream_name,
            {
                "event_type": event.event_type,
                "event_id": str(event.event_id),
                "data": event_json,
                "timestamp": event.timestamp.isoformat()
            }
        )

        logger.info(
            f"Event published: {event.event_type}",
            extra={"event_id": event.event_id}
        )

    async def subscribe(
        self,
        stream_name: str,
        consumer_group: str,
        consumer_name: str,
        handler: Callable[[BaseEvent], Awaitable[None]]
    ):
        """Subscribe to event stream"""
        while True:
            # Read events from stream
            events = await self.redis.xreadgroup(
                {
                    consumer_group: consumer_name
                },
                {stream_name: ">"},
                count=10,
                block=5000  # 5 second timeout
            )

            if events:
                for stream, event_list in events:
                    for event in event_list:
                        # Deserialize and process
                        event_data = json.loads(event[b'data'])
                        base_event = BaseEvent(**event_data)

                        await handler(base_event)

    async def create_consumer_group(self, stream_name: str, group_name: str):
        """Create consumer group for event processing"""
        try:
            await self.redis.xgroup_create(
                stream_name,
                group_name,
                id="0",
                mkstream=True
            )
        except Exception:
            pass  # Group already exists

# Singleton instance
event_bus = EventBus()
```

#### 1.2 Event Publisher Integration

```python
# app/api/v1/endpoints/assessments.py
from app.events.bus import event_bus
from app.events.schemas import AssessmentCompletedEvent

@router.post("/api/v1/assessments/{assessment_id}/complete")
async def complete_assessment(
    assessment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Complete assessment - emit event"""

    # Business logic
    assessment = await get_assessment(db, assessment_id)
    result = await calculate_assessment_result(assessment, current_user)

    # Publish event (non-blocking)
    event = AssessmentCompletedEvent(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        data={
            "assessment_id": str(assessment_id),
            "user_id": str(current_user.id),
            "assessment_type": assessment.type,
            "score": result.score,
            "responses": len(result.responses),
            "duration_seconds": result.duration_seconds
        }
    )

    # Fire and forget
    asyncio.create_task(event_bus.publish(event))

    return result
```

#### 1.3 First Consumers

```python
# app/events/consumers/analytics_consumer.py
class AnalyticsConsumer:
    """Consume events and update analytics"""

    async def handle(self, event: BaseEvent):
        """Route event to appropriate handler"""
        handler_map = {
            "assessment.completed": self.handle_assessment_completed,
            "user.registered": self.handle_user_registered,
            "team.member_added": self.handle_team_member_added,
        }

        handler = handler_map.get(event.event_type)
        if handler:
            await handler(event)

    async def handle_assessment_completed(self, event: BaseEvent):
        """Update analytics when assessment completed"""
        # Extract data
        assessment_id = event.data["assessment_id"]
        user_id = event.data["user_id"]
        score = event.data["score"]

        # Update analytics
        await self.update_user_analytics(user_id, score)
        await self.update_team_analytics(event)
        await self.update_org_analytics(event)

# Start consumer
consumer = AnalyticsConsumer()
asyncio.create_task(consumer.start())
```

**Deliverables:**
- ✅ Redis Streams event bus
- ✅ Event schema definitions
- ✅ 3 core publishers (assessments, users, teams)
- ✅ 3 core consumers (analytics, notifications, email)
- ✅ Event replay capability

---

### Phase 2: Enhanced Messaging (Weeks 7-12)

**Goal:** Introduce Kafka for enterprise-grade messaging

#### 2.1 Kafka Integration

```python
# app/events/kafka_producer.py
from aiokafka import AIOKafkaProducer
import json

class KafkaEventPublisher:
    """Kafka-based event publisher"""

    def __init__(self):
        self.producer = None

    async def start(self):
        """Initialize Kafka producer"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers="localhost:9092",
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()

    async def publish(self, event: BaseEvent, topic: str = "psychsync-events"):
        """Publish event to Kafka topic"""
        key = str(event.organization_id) if event.organization_id else None

        await self.producer.send_and_wait(
            topic,
            key=key.encode('utf-8') if key else None,
            value=event.dict()
        )

        logger.info(f"Event published to Kafka: {event.event_type}")

    async def stop(self):
        """Stop producer"""
        await self.producer.stop()
```

#### 2.2 Topic Architecture

```
psychsync-events (Main topic)
├── assessments (Partition key: organization_id)
├── users (Partition key: organization_id)
├── teams (Partition key: organization_id)
└── notifications (Partition key: user_id)

psychsync-events-dl (Dead Letter Queue)
```

**Deliverables:**
- ✅ Kafka cluster setup (3 brokers)
- ✅ Topic creation & configuration
- ✅ Producer/consumer implementations
- ✅ Dead letter queue handling
- ✅ Monitoring & alerting

---

### Phase 3: Advanced Patterns (Weeks 13-18)

**Goal:** Implement sophisticated EDA patterns

#### 3.1 Saga Pattern (Distributed Transactions)

```python
# app/events/sagas/assessment_saga.py
class AssessmentSaga:
    """
    Coordinate multi-step assessment process using saga pattern

    Steps:
    1. Create assessment record
    2. Calculate score (async)
    3. Update analytics
    4. Send notification
    5. Update team dashboard
    """

    async def execute(self, command: CreateAssessmentCommand):
        """Execute saga"""
        saga_id = uuid4()

        try:
            # Step 1: Create assessment
            assessment = await self.create_assessment(command)

            # Emit event
            await event_bus.publish(
                AssessmentCreatedEvent(
                    saga_id=saga_id,
                    data={"assessment_id": str(assessment.id)}
                )
            )

            # Continue with other steps...
            # Each step emits events for next step to consume

        except Exception as e:
            # Compensating transactions
            await self.compensate(saga_id, command)
            raise
```

#### 3.2 CQRS Pattern

```python
# app/events/cqrs/assessment_projection.py
class AssessmentReadModel:
    """
    Maintain read-optimized view of assessment data
    Updated asynchronously via events
    """

    async def handle(self, event: BaseEvent):
        """Update read model based on event"""

        if event.event_type == "assessment.completed":
            await self.update_read_model(event)

        elif event.event_type == "assessment.score_calculated":
            await self.update_score_view(event)

        elif event.event_type == "team.member_added":
            await self.recalculate_team_stats(event)

    async def update_read_model(self, event: BaseEvent):
        """Denormalize data for fast reads"""
        # Update materialized view
        await db.execute(
            insert(AssessmentSummary)
            .values(
                assessment_id=event.data["assessment_id"],
                user_id=event.data["user_id"],
                score=event.data["score"],
                completed_at=event.timestamp
            )
            .on_conflict_do_update(
                index_elements=["assessment_id"],
                set_={
                    "score": event.data["score"],
                    "completed_at": event.timestamp
                }
            )
        )
```

#### 3.3 Event Sourcing

```python
# app/events/sourcing/assessment_store.py
class AssessmentEventStore:
    """
    Store all events for assessment entity
    Enables rebuild of state from event stream
    """

    async def append(self, aggregate_id: UUID, events: List[BaseEvent]):
        """Append events to store"""
        for event in events:
            await db.execute(
                insert(EventStore)
                .values(
                    aggregate_id=aggregate_id,
                    event_id=event.event_id,
                    event_type=event.event_type,
                    event_data=event.json(),
                    timestamp=event.timestamp,
                    version=event.event_version
                )
            )

    async def load_state(self, aggregate_id: UUID) -> dict:
        """Rebuild state from event stream"""
        events = await db.execute(
            select(EventStore)
            .where(EventStore.aggregate_id == aggregate_id)
            .order_by(EventStore.timestamp)
        )

        state = {}
        for event in events:
            state = self.apply_event(state, event)

        return state

    async def replay(self, aggregate_id: UUID, up_to_version: int = None):
        """Replay events up to specific version"""
        events = await db.execute(
            select(EventStore)
            .where(
                EventStore.aggregate_id == aggregate_id,
                EventStore.version <= up_to_version
            )
            .order_by(EventStore.timestamp)
        )

        for event in events:
            # Re-process event
            await event_bus.publish(event)
```

**Deliverables:**
- ✅ Saga orchestration framework
- ✅ CQRS read/write model separation
- ✅ Event sourcing store
- ✅ Event replay mechanism
- ✅ Snapshot generation (for performance)

---

### Phase 4: Real-Time Features (Weeks 19-24)

**Goal:** Enable real-time analytics & notifications

#### 4.1 Stream Processing

```python
# app/events/processors/realtime_analytics.py
class RealtimeAnalyticsProcessor:
    """
    Process events in real-time for live dashboards
    """

    async def process_stream(self, stream_name: str):
        """Process event stream"""
        while True:
            events = await event_bus.redis.xread(
                {stream_name: "$"},
                count=100,
                block=1000
            )

            for event_data in events:
                event = BaseEvent(**event_data)

                # Update real-time metrics
                await self.update_metrics(event)

                # Check for alerts
                await self.check_alerts(event)

                # Push to WebSocket clients
                await self.broadcast_update(event)

    async def broadcast_update(self, event: BaseEvent):
        """Push update to connected WebSocket clients"""
        if event.organization_id:
            await websocket_manager.broadcast(
                f"org:{event.organization_id}",
                {
                    "type": event.event_type,
                    "data": event.data
                }
            )
```

#### 4.2 Complex Event Processing (CEP)

```python
# app/events/cep/pattern_detector.py
class EventPatternDetector:
    """
    Detect patterns in event streams

    Patterns:
    - Spike in assessment completions
    - User inactivity (no events for 30 days)
    - Team member churn spike
    - Unusual score distribution
    """

    async def detect_patterns(self, org_id: UUID):
        """Detect patterns for organization"""

        # Get recent events
        events = await self.get_recent_events(org_id, hours=24)

        # Pattern 1: Activity spike
        if await self.detect_activity_spike(events):
            await event_bus.publish(
                Event(
                    event_type="pattern.activity_spike_detected",
                    organization_id=org_id,
                    data={"event_count": len(events)}
                )
            )

        # Pattern 2: User churn risk
        at_risk_users = await self.detect_inactive_users(events)
        for user_id in at_risk_users:
            await event_bus.publish(
                Event(
                    event_type="pattern.user_churn_risk",
                    organization_id=org_id,
                    data={"user_id": str(user_id)}
                )
            )
```

**Deliverables:**
- ✅ Real-time WebSocket updates
- ✅ Stream processing framework
- ✅ Complex event patterns
- ✅ Live dashboards
- ✅ Alerting system

---

## 5. Event Catalog

### 5.1 Complete Event List

```yaml
# app/events/catalog.yaml

# Assessment Events
assessment.created:
  description: New assessment created
  producer: API
  consumers: [analytics, notifications]

assessment.started:
  description: User started assessment
  producer: API
  consumers: [analytics]

assessment.completed:
  description: User completed assessment
  producer: API
  consumers: [analytics, scoring, notifications, email]
  priority: HIGH

assessment.score_calculated:
  description: Assessment scoring completed
  producer: Scoring Service
  consumers: [analytics, database, notifications]

# User Events
user.registered:
  description: New user registered
  producer: API
  consumers: [analytics, email, notifications]
  priority: HIGH

user.verified:
  description: User verified email
  producer: API
  consumers: [analytics]

user.login:
  description: User logged in
  producer: API
  consumers: [analytics, security]

user.logged_out:
  description: User logged out
  producer: API
  consumers: [analytics]

user.deleted:
  description: User account deleted
  producer: API
  consumers: [analytics, database, compliance]
  priority: HIGH

# Team Events
team.created:
  description: Team created
  producer: API
  consumers: [analytics]

team.member_added:
  description: Member added to team
  producer: API
  consumers: [analytics, notifications]
  priority: HIGH

team.member_removed:
  description: Member removed from team
  producer: API
  consumers: [analytics, notifications]
  priority: HIGH

team.deleted:
  description: Team deleted
  producer: API
  consumers: [analytics, database]
  priority: HIGH

# Notification Events
notification.sent:
  description: Notification sent to user
  producer: Notification Service
  consumers: [analytics]

notification.clicked:
  description: User clicked notification
  producer: API
  consumers: [analytics]

# Email Events
email.sent:
  description: Email sent
  producer: Email Service
  consumers: [analytics]

email.delivered:
  description: Email delivered
  producer: Email Service (webhook)
  consumers: [analytics]

email.opened:
  description: User opened email
  producer: Email Service (webhook)
  consumers: [analytics]

email.clicked:
  description: User clicked email link
  producer: Email Service (webhook)
  consumers: [analytics]

email.bounced:
  description: Email bounced
  producer: Email Service (webhook)
  consumers: [analytics, compliance]
  priority: MEDIUM

# Analytics Events
analytics.metric_recorded:
  description: Metric recorded
  producer: Analytics Service
  consumers: [monitoring]

analytics.report_generated:
  description: Report generated
  producer: Analytics Service
  consumers: [notifications, email]

# Security Events
security.failed_login:
  description: Failed login attempt
  producer: API
  consumers: [security, analytics]
  priority: HIGH

security.password_reset:
  description: Password reset requested
  producer: API
  consumers: [security, email, notifications]
  priority: HIGH

security.suspicious_activity:
  description: Suspicious activity detected
  producer: Security Service
  consumers: [security, notifications, email]
  priority: CRITICAL
```

---

## 6. Error Handling & Retry

### 6.1 Retry Strategy

```python
# app/events/handlers.py
class RetryConfig:
    """Retry configuration for event handlers"""

    @staticmethod
    def get_retry_policy(event_type: str) -> dict:
        """Get retry policy for event type"""
        policies = {
            "notification.sent": {"max_retries": 3, "delay": 5},
            "email.sent": {"max_retries": 5, "delay": 60},
            "analytics.metric_recorded": {"max_retries": 0, "delay": 0},
        }
        return policies.get(event_type, {"max_retries": 3, "delay": 10})

async def process_with_retry(
    handler: Callable,
    event: BaseEvent,
    max_retries: int = 3,
    delay: int = 10
):
    """Process event with retry logic"""

    for attempt in range(max_retries + 1):
        try:
            await handler(event)
            break  # Success
        except Exception as e:
            if attempt == max_retries:
                # Final attempt failed, send to DLQ
                await send_to_dead_letter_queue(event, e)
            else:
                logger.warning(
                    f"Event processing failed (attempt {attempt + 1}): {e}"
                )
                await asyncio.sleep(delay)
```

### 6.2 Dead Letter Queue

```python
# app/events/dlq.py
class DeadLetterQueue:
    """Handle events that failed processing"""

    async def send_to_dlq(
        self,
        event: BaseEvent,
        error: Exception,
        retry_count: int = 0
    ):
        """Send to dead letter queue"""
        dlq_event = DeadLetterEvent(
            original_event=event,
            error=str(error),
            error_type=type(error).__name__,
            retry_count=retry_count,
            failed_at=datetime.utcnow()
        )

        # Store in database for manual inspection
        await db.insert(dlq_event)

        # Alert on critical failures
        if event.metadata.get("priority") == "CRITICAL":
            await alerting.send_alert(
                f"Critical event failed: {event.event_type}",
                details={
                    "event_id": str(event.event_id),
                    "error": str(error),
                    "retry_count": retry_count
                }
            )
```

---

## 7. Monitoring & Observability

### 7.1 Event Metrics

```python
# app/events/monitoring.py
class EventMonitor:
    """Monitor event stream health"""

    async def collect_metrics(self):
        """Collect and report event metrics"""
        while True:
            metrics = {
                "events_processed_total": await self.get_events_processed(),
                "events_processing_failed": await self.get_events_failed(),
                "consumer_lag_ms": await self.get_consumer_lag(),
                "dead_letter_queue_size": await self.get_dlq_size(),
                "avg_processing_time_ms": await self.get_avg_processing_time(),
            }

            # Send to monitoring system
            await metrics.gauge("psychsync_events", metrics)

            await asyncio.sleep(60)

    async def get_consumer_lag(self) -> dict:
        """Get consumer lag per consumer group"""
        lag_info = {}

        for group in ["analytics_group", "notification_group", "email_group"]:
            lag = await redis.xinfo_groups("events", group)
            lag_info[group] = lag

        return lag_info
```

### 7.2 Event Tracing

```python
# Distributed tracing
@app.post("/api/v1/assessments")
async def create_assessment():
    # Start trace
    trace_id = uuid4()
    span_id = uuid4()

    # Publish event with trace context
    event = AssessmentCreatedEvent(
        event_id=uuid4(),
        trace_id=trace_id,
        parent_span_id=span_id,
        # ... other fields
    )

    await event_bus.publish(event)
```

---

## 8. Migration Strategy

### 8.1 Strangler Fig Pattern

```
┌─────────────────────────────────────┐
│         Old Synchronous API          │
├─────────────────────────────────────┤
│  - Keep existing endpoints          │
│  - Add event publishing side-effect  │
│  - Gradually move to async           │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│         Event Bus                    │
├─────────────────────────────────────┤
│  - Events consumed by new services  │
│  - Gradually cut over to async       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│         New Async Services           │
│  - Real-time analytics               │
│  - Event-driven notifications       │
│  - Async email processing            │
└─────────────────────────────────────┘
```

### 8.2 Rollback Plan

```python
# Feature flag to disable event processing
FEATURE_FLAGS = {
    "enable_event_bus": True,
    "enable_kafka": False,  # Phase 2
    "enable_saga": False,  # Phase 3
}

if not FEATURE_FLAGS["enable_event_bus"]:
    # Use synchronous path
    await process_sync(assessment)
else:
    # Use event-driven path
    await publish_event(assessment_created_event)
```

---

## 9. Performance Considerations

### 9.1 Throughput Planning

```
Event Volume Estimates:
- 100 orgs × 100 users × 5 assessments/day = 50,000 events/day
- Peak: 5 events/second

Resource Requirements:
- Redis: 1 GB memory
- Kafka: 3 brokers, 100GB storage
- Consumers: 6 instances (2 per consumer group)
```

### 9.2 Latency Optimization

```python
# Batch event publishing for performance
class BatchEventPublisher:
    """Batch events for higher throughput"""

    def __init__(self, batch_size=100, flush_interval=1):
        self.batch = []
        self.batch_size = batch_size
        self.flush_interval = flush_interval

    async def publish(self, event: BaseEvent):
        """Add to batch, flush if full"""
        self.batch.append(event)

        if len(self.batch) >= self.batch_size:
            await self.flush()

    async def flush(self):
        """Publish batch to event bus"""
        if not self.batch:
            return

        await event_bus.publish_batch(self.batch)
        self.batch.clear()
```

---

## 10. Testing Strategy

### 10.1 Event Testing

```python
# tests/events/test_event_bus.py
@pytest.mark.asyncio
async def test_event_publish_and_consume():
    """Test event publishing and consumption"""

    # Setup consumer
    received_events = []

    async def handler(event):
        received_events.append(event)

    # Subscribe
    consumer = TestConsumer(handler=handler)
    await consumer.start()

    # Publish event
    event = AssessmentCompletedEvent(
        user_id=uuid4(),
        data={"assessment_id": str(uuid4())}
    )

    await event_bus.publish(event)

    # Wait for processing
    await asyncio.sleep(0.5)

    # Assert
    assert len(received_events) == 1
    assert received_events[0].event_type == "assessment.completed"
```

---

## 11. Success Metrics

### Phase 1 Targets (Week 6)
- ✅ Event bus operational
- ✅ 5 event types published
- ✅ 3 consumers active
- ✅ <100ms event publish latency
- ✅ Zero data loss

### Phase 2 Targets (Week 12)
- ✅ Kafka cluster operational
- ✅ All events on Kafka
- ✅ Dead letter queue functional
- ✅ <500ms end-to-end latency
- ✅ 99.9% message delivery

### Phase 3 Targets (Week 18)
- ✅ Saga framework implemented
- ✅ CQRS pattern in use
- ✅ Event sourcing operational
- ✅ Event replay working
- ✅ 50+ event types

### Phase 4 Targets (Week 24)
- ✅ Real-time dashboards live
- ✅ WebSocket updates working
- ✅ Complex event patterns detected
- ✅ <5 second alerting latency
- ✅ 95% uptime for event pipeline
