# Service Migration Patterns - Real-World Examples

**Purpose**: This document provides detailed, copy-paste examples for migrating specific service patterns to BaseService.

**Patterns Covered**:
1. Assessment Service (Complex CRUD)
2. Analytics Service (Aggregation-heavy)
3. Notification Service (External integration)
4. File Upload Service (Binary data handling)

---

## Pattern 1: Assessment Service (Complex CRUD with Scoring)

### Current State

```python
# app/services/assessment_service.py
from app.core.cache import cached
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

@cached(expire=1800, key_prefix="assessment")
async def get_assessment(db: AsyncSession, assessment_id: int) -> dict | None:
    """Get assessment by ID with scoring."""
    try:
        result = await db.execute(
            select(Assessment)
            .options(selectinload(Assessment.questions))
            .where(Assessment.id == assessment_id)
        )
        assessment = result.scalar_one_or_none()
        if assessment:
            return assessment_to_dict(assessment)
        return None
    except Exception as e:
        logger.error(f"Failed to get assessment: {e}")
        raise

@cached(expire=600, key_prefix="assessment")
async def get_assessments_by_user(
    db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100
) -> list[dict]:
    """Get user's assessments."""
    result = await db.execute(
        select(Assessment)
        .where(Assessment.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return [assessment_to_dict(a) for a in result.scalars().all()]

async def create_assessment(
    db: AsyncSession, data: AssessmentCreate, user_id: UUID
) -> Assessment:
    """Create new assessment."""
    try:
        assessment = Assessment(**data.dict(), user_id=user_id)
        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)
        return assessment
    except Exception as e:
        await db.rollback()
        raise ValueError(f"Failed to create: {e}")

async def calculate_score(
    db: AsyncSession, assessment_id: int
) -> dict:
    """Calculate assessment score."""
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise ValueError("Assessment not found")

    # Complex scoring logic
    score = 0
    for response in assessment.responses:
        score += response.score_value

    return {"assessment_id": assessment_id, "score": score}
```

### Migrated State

```python
# app/services/assessment_service_refactored.py
from app.services.base_service import BaseService
from app.core.database_transactions import transaction_manager
from app.core.structured_logging import EventType

class AssessmentService(BaseService[Assessment, AssessmentCreate, AssessmentUpdate]):
    """Assessment service with automatic error handling and caching."""

    @property
    def model(self) -> type[Assessment]:
        return Assessment

    @property
    def cache_strategy(self) -> CacheStrategy:
        return CacheStrategy(
            enabled=True,
            ttl_seconds=1800,
            key_prefix="assessment",
        )

    def get_cache_key(self, operation: str, **kwargs) -> str:
        if operation == "get_by_id":
            return f"assessment:id:{kwargs.get('assessment_id')}"
        elif operation == "get_by_user":
            return f"assessment:user:{kwargs.get('user_id')}"
        return f"assessment:{operation}"

    def validate_create_data(self, data: AssessmentCreate) -> None:
        if not data.title or len(data.title) < 3:
            raise ValidationException("Title must be at least 3 characters", field="title")

    def validate_update_data(self, data: AssessmentUpdate, existing: Assessment) -> None:
        if data.status == "completed" and existing.status != "completed":
            # Validate all questions answered
            if len(existing.responses) < len(existing.questions):
                raise ValidationException("Cannot complete - not all questions answered", field="status")

    async def get_by_id(
        self, db: AsyncSession, assessment_id: int, include_questions: bool = False
    ) -> Assessment | None:
        """Get assessment with optional eager loading."""
        self.logger.debug(
            EventType.DATABASE_OPERATION,
            f"Retrieving assessment: {assessment_id}",
            operation="get_by_id",
            assessment_id=assessment_id,
        )

        query = select(Assessment).where(Assessment.id == assessment_id)

        if include_questions:
            query = query.options(selectinload(Assessment.questions))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Assessment]:
        """Get assessments by user."""
        self.logger.debug(
            EventType.DATABASE_OPERATION,
            f"Retrieving assessments for user: {user_id}",
            operation="get_by_user",
            user_id=str(user_id),
        )

        result = await db.execute(
            select(Assessment)
            .where(Assessment.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @transaction_manager.transaction
    async def create_assessment(
        self, db: AsyncSession, data: AssessmentCreate, user_id: UUID
    ) -> Assessment:
        """Create assessment with validation."""
        self.validate_create_data(data)

        assessment = Assessment(
            **data.model_dump(),
            user_id=user_id,
            created_at=datetime.utcnow(),
        )
        db.add(assessment)
        await db.flush()
        await db.refresh(assessment)

        self.logger.info(
            EventType.DATABASE_OPERATION,
            f"Assessment created: {assessment.title}",
            operation="create_assessment",
            assessment_id=assessment.id,
        )

        return assessment

    async def calculate_score(
        self, db: AsyncSession, assessment_id: int
    ) -> dict:
        """Calculate assessment score."""
        assessment = await self.get_by_id(db, assessment_id, include_questions=True)

        if not assessment:
            raise ValidationException("Assessment not found", field="id")

        # Complex scoring logic
        score = sum(r.score_value for r in assessment.responses if r.score_value)

        self.logger.debug(
            EventType.DATABASE_OPERATION,
            f"Score calculated: {score}",
            operation="calculate_score",
            assessment_id=assessment_id,
            score=score,
        )

        return {"assessment_id": assessment_id, "score": score}
```

**Key Changes**:
- ✅ No more `@cached` decorators (handled by BaseService)
- ✅ No more try/except blocks (handled by BaseService)
- ✅ Consistent logging via `self.logger`
- ✅ Transaction management via `@transaction_manager.transaction`
- ✅ Returns models directly (FastAPI handles serialization)

---

## Pattern 2: Analytics Service (Aggregation-Heavy)

### Current State

```python
# app/services/analytics_service.py
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_analytics(
    db: AsyncSession, user_id: UUID, days: int = 30
) -> dict:
    """Get user analytics."""
    try:
        # Average score
        avg_result = await db.execute(
            select(func.avg(Response.score))
            .join(Assessment)
            .where(Assessment.user_id == user_id)
            .where(Assessment.created_at >= datetime.now() - timedelta(days=days))
        )
        avg_score = avg_result.scalar() or 0

        # Assessment count
        count_result = await db.execute(
            select(func.count(Assessment.id))
            .where(Assessment.user_id == user_id)
        )
        assessment_count = count_result.scalar()

        return {
            "average_score": float(avg_score),
            "assessment_count": assessment_count,
        }
    except Exception as e:
        logger.error(f"Analytics failed: {e}")
        raise
```

### Migrated State

```python
# app/services/analytics_service_refactored.py
from app.services.base_service import BaseService
from app.core.structured_logging import EventType

class AnalyticsService(BaseService):
    """Analytics service with automatic error handling and logging."""

    # Note: Analytics doesn't need full CRUD, just custom queries
    # We still extend BaseService for error handling and logging

    def __init__(self):
        super().__init__()
        # Override cache strategy - shorter TTL for analytics
        self._cache_strategy = CacheStrategy(
            enabled=True,
            ttl_seconds=300,  # 5 minutes
            key_prefix="analytics",
        )

    @property
    def cache_strategy(self) -> CacheStrategy:
        return self._cache_strategy

    # For analytics, we don't need all the abstract methods
    # Override with no-ops or minimal implementations
    def get_cache_key(self, operation: str, **kwargs) -> str:
        return f"analytics:{operation}:{kwargs.get('user_id')}:{kwargs.get('days')}"

    # These are no-ops for analytics service
    @property
    def model(self) -> type | None:
        return None

    def validate_create_data(self, data) -> None:
        pass

    def validate_update_data(self, data, existing) -> None:
        pass

    async def get_user_analytics(
        self, db: AsyncSession, user_id: UUID, days: int = 30
    ) -> dict:
        """Get user analytics."""
        self.logger.debug(
            EventType.DATABASE_OPERATION,
            f"Calculating analytics for user: {user_id}",
            operation="get_user_analytics",
            user_id=str(user_id),
            days=days,
        )

        # Average score
        from app.db.models.response import Response
        from app.db.models.assessment import Assessment

        avg_result = await db.execute(
            select(func.avg(Response.score))
            .join(Assessment, Response.assessment_id == Assessment.id)
            .where(Assessment.user_id == user_id)
            .where(Assessment.created_at >= datetime.utcnow() - timedelta(days=days))
        )
        avg_score = avg_result.scalar() or 0

        # Assessment count
        count_result = await db.execute(
            select(func.count(Assessment.id))
            .where(Assessment.user_id == user_id)
        )
        assessment_count = count_result.scalar()

        analytics = {
            "average_score": float(avg_score),
            "assessment_count": assessment_count,
        }

        self.logger.debug(
            EventType.DATABASE_OPERATION,
            f"Analytics calculated",
            operation="get_user_analytics",
            user_id=str(user_id),
            analytics=analytics,
        )

        return analytics
```

**Key Changes**:
- ✅ Extends BaseService for error handling even without full CRUD
- ✅ Override abstract methods with no-ops for query-only services
- ✅ Shorter cache TTL for analytics (data changes frequently)
- ✅ Consistent logging for all analytics queries

---

## Pattern 3: Notification Service (External Integration)

### Current State

```python
# app/services/notification_service.py
import asyncio

async def send_notification(
    db: AsyncSession, user_id: UUID, message: str, notification_type: str
) -> bool:
    """Send notification to user."""
    try:
        # Save to database
        notification = Notification(
            user_id=user_id,
            message=message,
            type=notification_type,
            sent_at=datetime.utcnow(),
        )
        db.add(notification)
        await db.commit()

        # Send via external service
        if notification_type == "email":
            await email_service.send_email(user_id, message)
        elif notification_type == "push":
            await push_service.send_push(user_id, message)

        return True
    except Exception as e:
        logger.error(f"Notification failed: {e}")
        await db.rollback()
        return False
```

### Migrated State

```python
# app/services/notification_service_refactored.py
from app.services.base_service import BaseService
from app.core.database_transactions import transaction_manager

class NotificationService(BaseService[Notification, NotificationCreate, NotificationUpdate]):
    """Notification service with automatic error handling."""

    @property
    def model(self) -> type[Notification]:
        return Notification

    @property
    def cache_strategy(self) -> CacheStrategy:
        # Notifications don't need caching
        return CacheStrategy(enabled=False)

    def get_cache_key(self, operation: str, **kwargs) -> str:
        return f"notification:{operation}"

    def validate_create_data(self, data: NotificationCreate) -> None:
        if not data.message or len(data.message) > 1000:
            raise ValidationException(
                "Message must be 1-1000 characters", field="message"
            )

    def validate_update_data(self, data, existing) -> None:
        raise ValidationException(
            "Notifications cannot be updated", field="id"
        )

    @transaction_manager.transaction
    async def send_notification(
        self, db: AsyncSession, user_id: UUID, message: str, notification_type: str
    ) -> Notification:
        """Send notification to user."""
        self.logger.info(
            EventType.SECURITY_EVENT,
            f"Sending {notification_type} notification to user",
            operation="send_notification",
            user_id=str(user_id),
            notification_type=notification_type,
        )

        # Create notification record
        notification = Notification(
            user_id=user_id,
            message=message,
            type=notification_type,
            sent_at=datetime.utcnow(),
        )
        db.add(notification)
        await db.flush()

        # Send via external service (outside transaction)
        try:
            if notification_type == "email":
                # Don't await - fire and forget
                asyncio.create_task(email_service.send_email(user_id, message))
            elif notification_type == "push":
                asyncio.create_task(push_service.send_push(user_id, message))

            self.logger.info(
                EventType.SECURITY_EVENT,
                f"Notification sent successfully",
                operation="send_notification",
                notification_id=str(notification.id),
            )
        except Exception as e:
            self.logger.error(
                EventType.SECURITY_EVENT,
                f"External notification failed: {e}",
                operation="send_notification",
                notification_id=str(notification.id),
            )

        return notification
```

**Key Changes**:
- ✅ Fire-and-forget for external integrations (asyncio.create_task)
- ✅ Transaction rollback handled automatically
- ✅ External service failures don't rollback database record
- ✅ Comprehensive logging for debugging

---

## Pattern 4: Search/Filter Pattern

### Current State

```python
# app/services/user_service.py
from sqlalchemy import or_

@cached(expire=300, key_prefix="user_search")
async def search_users(
    db: AsyncSession, query: str, organization_id: int | None = None
) -> list[dict]:
    """Search users by name or email."""
    try:
        q = select(User).where(
            or_(
                User.email.ilike(f"%{query}%"),
                User.full_name.ilike(f"%{query}%"),
            )
        )

        if organization_id:
            q = q.where(User.organization_id == organization_id)

        result = await db.execute(q)
        return [user_to_dict(u) for u in result.scalars().all()]
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise
```

### Migrated State

```python
# app/services/user_service_refactored.py
from sqlalchemy import or_

async def search(
    self,
    db: AsyncSession,
    query: str,
    organization_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[User]:
    """Search users with automatic error handling and logging."""
    self.logger.debug(
        EventType.DATABASE_OPERATION,
        f"Searching users: {query}",
        operation="search_users",
        query=query,
        organization_id=organization_id,
    )

    search_query = select(User).where(
        or_(
            User.email.ilike(f"%{query}%"),
            User.full_name.ilike(f"%{query}%"),
        )
    )

    if organization_id:
        search_query = search_query.where(User.organization_id == organization_id)

    search_query = search_query.offset(skip).limit(limit)
    result = await db.execute(search_query)
    users = result.scalars().all()

    self.logger.debug(
        EventType.DATABASE_OPERATION,
        f"Found {len(users)} users",
        operation="search_users",
        count=len(users),
    )

    return users
```

---

## Quick Reference: Common Conversions

### Remove `@cached` decorator
```python
# BEFORE
@cached(expire=1800, key_prefix="user")
async def get_user(db: AsyncSession, user_id: UUID) -> dict:
    pass

# AFTER
async def get_by_id(self, db: AsyncSession, user_id: UUID) -> User:
    pass
```

### Remove try/except blocks
```python
# BEFORE
async def create_user(db: AsyncSession, data: UserCreate) -> User:
    try:
        user = User(**data.dict())
        db.add(user)
        await db.commit()
        return user
    except Exception as e:
        await db.rollback()
        raise

# AFTER
@transaction_manager.transaction
async def create(self, db: AsyncSession, data: UserCreate) -> User:
    user = User(**data.model_dump())
    db.add(user)
    await db.flush()
    return user
```

### Convert dict to model
```python
# BEFORE
async def get_user(db: AsyncSession, user_id: UUID) -> dict | None:
    user = await _get_user_model(db, user_id)
    return user_to_dict(user) if user else None

# AFTER
async def get_by_id(self, db: AsyncSession, user_id: UUID) -> User | None:
    return await super().get_by_id(db, user_id)
```

### Add logging
```python
# BEFORE
async def create_user(db: AsyncSession, data: UserCreate) -> User:
    user = User(**data.dict())
    db.add(user)
    await db.commit()
    return user

# AFTER
@transaction_manager.transaction
async def create(self, db: AsyncSession, data: UserCreate) -> User:
    user = User(**data.model_dump())
    db.add(user)
    await db.flush()

    self.logger.info(
        EventType.DATABASE_OPERATION,
        f"User created: {user.email}",
        operation="create_user",
        user_id=str(user.id),
    )

    return user
```

---

## Testing Your Migration

### Manual Testing Checklist

After migrating a service, verify:

- [ ] Service can be imported without errors
- [ ] All CRUD operations work via API
- [ ] Caching works (check Redis keys)
- [ ] Error handling works (try invalid inputs)
- [ ] Logging appears in application logs
- [ ] Transactions roll back on errors
- [ ] Validation runs before writes

### Automated Test Template

```python
# tests/api/test_refactored_service.py
import pytest
from app.services.user_service_refactored import user_service

def test_service_creation():
    """Test service can be instantiated."""
    assert user_service is not None
    assert user_service.model == User

@pytest.mark.asyncio
async def test_get_by_id(db, test_user):
    """Test get_by_id returns model."""
    user = await user_service.get_by_id(db, test_user.id)
    assert user is not None
    assert user.email == test_user.email
    assert isinstance(user, User)  # Returns model, not dict

@pytest.mark.asyncio
async def test_validation(db):
    """Test validation runs."""
    from app.core.error_handling import ValidationException
    from app.schemas.user import UserCreate

    invalid_data = UserCreate(
        email="invalid",  # Invalid email
        password="pass123",
    )

    with pytest.raises(ValidationException):
        await user_service.validate_create_data(invalid_data)

@pytest.mark.asyncio
async def test_error_handling(db):
    """Test errors are handled automatically."""
    # BaseService catches database errors
    result = await user_service.get_by_id(db, UUID("00000000-0000-0000-0000-000000000000"))
    assert result is None  # Returns None, doesn't raise
```

---

## Summary

| Pattern | Key Considerations |
|---------|-------------------|
| **Complex CRUD** | Eager loading, validation, transactions |
| **Analytics** | Short cache TTL, aggregation queries |
| **External Integration** | Fire-and-forget, error isolation |
| **Search/Filter** | Dynamic queries, pagination |

**Next Steps**: Apply these patterns to your specific service, then run the validation script to confirm the migration is successful.
