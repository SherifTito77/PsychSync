# Database Query Optimization Fixes

## Overview

This document describes the fixes implemented to resolve N+1 query patterns and cache staleness issues identified in the codebase.

## Issues Fixed

### 1. N+1 Query Pattern in `team_personality_service.py`

**Location**: `app/services/team_personality_service.py:414-430`

**Problem**: The `compare_teams()` method was executing a separate database query for each team in a loop, resulting in N queries for N teams.

**Solution**: Replaced the loop with a single batch query using SQLAlchemy's `.in_()` clause.

**Before**:
```python
for team_id in team_ids:
    composition = await TeamPersonalityService.get_team_composition(db, team_id)
    # ... process composition
```

**After**:
```python
# Single batch query
result = await db.execute(
    select(TeamPersonalityMap)
    .filter(TeamPersonalityMap.team_id.in_(team_ids))
    .order_by(TeamPersonalityMap.updated_at.desc())
)
compositions = {str(comp.team_id): comp for comp in result.scalars().all()}
```

**Performance Impact**:
- Before: N database queries (one per team)
- After: 1 database query for all teams
- For 10 teams: 10 queries → 1 query (90% reduction)

### 2. Cache Invalidation System

**Problem**: Team composition cache had no invalidation mechanism when underlying data changed (assessments submitted, team members added/removed), leading to stale data being served for up to 24 hours.

**Solution**: Created centralized cache invalidation service.

**New File**: `app/services/cache_invalidation_service.py`

Provides methods for:
- `invalidate_team_composition_cache()` - Invalidate single team cache
- `invalidate_multiple_teams_cache()` - Batch invalidate multiple teams
- `invalidate_assessment_related_caches()` - Triggered when assessments change
- `invalidate_response_related_caches()` - Triggered when responses submitted
- `invalidate_team_membership_cache()` - Triggered when team members change
- `invalidate_user_related_team_caches()` - Invalidate all teams for a user

### 3. Team Personality Service Enhancements

**Added Methods**:
- `invalidate_team_composition_cache(team_id)` - Delete cached composition
- `invalidate_multiple_teams_cache(team_ids)` - Batch delete cached compositions

## Integration Guide

### When to Call Cache Invalidation

```python
from app.services.cache_invalidation_service import cache_invalidation_service

# When assessment is submitted
await cache_invalidation_service.invalidate_assessment_related_caches(db, assessment_id)

# When response is created/updated
await cache_invalidation_service.invalidate_response_related_caches(db, response_id)

# When team member is added/removed
await cache_invalidation_service.invalidate_team_membership_cache(db, team_id)

# When user's assessments change
await cache_invalidation_service.invalidate_user_related_team_caches(db, user_id)
```

### Example: Assessment Submission

```python
# In your assessment submission endpoint
@router.post("/{assessment_id}/responses")
async def submit_response(
    assessment_id: str,
    response_data: ResponseSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Create the response
    response = await create_response(db, assessment_id, current_user.id, response_data)

    # Invalidate related caches
    from app.services.cache_invalidation_service import cache_invalidation_service
    await cache_invalidation_service.invalidate_response_related_caches(db, str(response.id))

    return response
```

## Testing

### Integration Tests

New test file: `tests/integration/test_query_optimization.py`

Tests include:
- `test_compare_teams_no_n_plus_1()` - Verifies batch query prevents N+1
- `test_cache_invalidation_on_assessment_change()` - Verifies cache deletion
- `test_cache_invalidation_for_multiple_teams()` - Verifies batch invalidation
- `test_team_membership_change_invalidates_cache()` - Verifies membership triggers

### Running Tests

```bash
# Run all query optimization tests
pytest tests/integration/test_query_optimization.py -v

# Run specific test
pytest tests/integration/test_query_optimization.py::test_compare_teams_no_n_plus_1 -v

# Run with coverage
pytest tests/integration/test_query_optimization.py --cov=app.services.team_personality_service --cov-report=html
```

## Performance Monitoring

### Query Count Monitoring

The integration tests include a `query_counter` fixture that verifies query counts:

```python
def test_example(db_session: AsyncSession, query_counter):
    query_counter.reset()

    # Execute code
    await some_function(db_session)

    # Assert query count
    assert query_counter.count <= expected_max, "Too many queries!"
```

### Database Query Logging

Enable SQLAlchemy query logging for development:

```python
# In app/core/database.py
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log all queries
    pool_pre_ping=True,
)
```

## Best Practices

### 1. Use Batch Queries

❌ **Bad** - N+1 pattern:
```python
for item_id in item_ids:
    item = await db.execute(select(Item).where(Item.id == item_id))
    # Process item
```

✅ **Good** - Batch query:
```python
result = await db.execute(select(Item).where(Item.id.in_(item_ids)))
items = {item.id: item for item in result.scalars().all()}
```

### 2. Use Eager Loading

❌ **Bad** - Lazy loading:
```python
teams = await db.execute(select(Team))
for team in teams.scalars():
    # This triggers a query for each team's members!
    members = team.members
```

✅ **Good** - Eager loading:
```python
teams = await db.execute(
    select(Team)
    .options(selectinload(Team.members))
)
for team in teams.scalars():
    # Members already loaded, no additional query
    members = team.members
```

### 3. Invalidate Cache on Data Changes

Always invalidate related caches when data changes:

```python
# After creating/updating/deleting data
await cache_invalidation_service.invalidate_[relevant]_cache(db, resource_id)
```

## Migration Checklist

- [x] Fix N+1 query in `team_personality_service.py`
- [x] Create cache invalidation service
- [x] Add invalidation methods to `TeamPersonalityService`
- [x] Create integration tests
- [ ] Integrate cache invalidation into assessment submission endpoints
- [ ] Integrate cache invalidation into team member management
- [ ] Add query count monitoring to CI/CD pipeline
- [ ] Enable query logging in development environment
- [ ] Add performance regression tests to critical paths

## Related Files

### Modified
- `app/services/team_personality_service.py` - Fixed N+1 query, added cache invalidation

### New
- `app/services/cache_invalidation_service.py` - Centralized cache invalidation
- `tests/integration/test_query_optimization.py` - Integration tests

### To Be Updated (TODO)
- Assessment submission endpoints - Add cache invalidation calls
- Team member management endpoints - Add cache invalidation calls
- Response submission endpoints - Add cache invalidation calls

## Resources

- [SQLAlchemy 1.4/2.0 AsyncIO](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
- [Eager Loading Strategies](https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html)
- [Performance Tuning](https://docs.sqlalchemy.org/en/14/core/performance.html)
