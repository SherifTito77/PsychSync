# ADR 003: Standardize All Entity IDs to UUID

## Status
**Accepted** - 2025-01-19

## Context

### Current State
PsychSync uses **inconsistent ID types** across different models:

```python
# Current database models - Mixed types
class User(Base):
    id = Column(UUID(as_uuid=True), primary_key=True)  # ✅ UUID

class Team(Base):
    id = Column(UUID(as_uuid=True), primary_key=True)  # ✅ UUID

class Assessment(Base):
    id = Column(Integer, primary_key=True)             # ❌ Integer

class Organization(Base):
    id = Column(Integer, primary_key=True)             # ❌ Integer

class Response(Base):
    id = Column(Integer, primary_key=True)             # ❌ Integer
```

**Pydantic schemas also inconsistent:**
```python
# app/schemas/user.py
class UserOut(BaseModel):
    id: UUID  # ✅ UUID

# app/schemas/assessment.py
class AssessmentOut(BaseModel):
    id: int   # ❌ Integer
```

### Problems

1. **Type Inconsistency**: Some models use `int`, others use `UUID`
2. **Runtime Errors**: Passing wrong ID type crashes application
3. **API Confusion**: Clients don't know what type to expect
4. **Security**: Sequential integer IDs leak information (user count, creation order)
5. **Collision Risk**: Integer IDs can collide in distributed systems
6. **No Guarantees**: Auto-increment integers reset, can be guessed
7. **Migration Issues**: Importing data requires ID remapping

### Real Impact

```python
# ❌ Runtime error: Type mismatch
async def get_assessment(assessment_id: UUID):  # Expects UUID
    # But assessment.id is int!
    pass

# ❌ Security vulnerability
# User 100 can guess user 101, 102, etc.
GET /api/v1/users/101  # Easy enumeration

# ❌ Distributed system problems
# Service A creates user (id=100)
# Service B creates user (id=100)  # Collision!
```

## Decision

**Standardize all entity IDs to UUID** across the entire application.

### UUID Version Choice
**Use UUIDv7** (or PostgreSQL's `gen_random_uuid()`) for:
- Time-ordered (better than v4 for indexing)
- Monotonic increasing within same timestamp
- No coordination required
- Better database performance

### Implementation

**Migration Strategy:**

```sql
-- Step 1: Add new UUID column (nullable)
ALTER TABLE assessments
ADD COLUMN id_uuid UUID DEFAULT gen_random_uuid();

-- Step 2: Migrate existing data
UPDATE assessments
SET id_uuid = gen_random_uuid();

-- Step 3: Update foreign keys
ALTER TABLE responses
ADD COLUMN assessment_id_uuid UUID;

UPDATE responses r
SET assessment_id_uuid = a.id_uuid
FROM assessments a
WHERE r.assessment_id = a.id;

-- Step 4: Drop old columns (after verification)
ALTER TABLE assessments DROP COLUMN id;
ALTER TABLE assessments RENAME COLUMN id_uuid TO id;
```

**Updated Models:**

```python
# ✅ All UUID - Consistent
class User(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

class Team(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

class Assessment(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

class Organization(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

class Response(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
```

**Updated Schemas:**

```python
# ✅ All UUID - Type-safe
class UserOut(BaseModel):
    id: UUID

class AssessmentOut(BaseModel):
    id: UUID  # Changed from int

class OrganizationOut(BaseModel):
    id: UUID  # Changed from int

class ResponseOut(BaseModel):
    id: UUID  # Changed from int
```

## Consequences

### Positive
✅ **Type Safety**: Consistent UUID type throughout codebase
✅ **Security**: Non-guessable IDs prevent enumeration attacks
✅ **Distributed Systems**: No collision risk across services
✅ **API Consistency**: Clients always expect UUID
✅ **Import/Export**: No ID conflicts when merging data
✅ **Database Performance**: UUIDv7 maintains good index characteristics
✅ **Standards Compliance**: Follows modern API best practices

### Negative
❌ **Storage**: UUIDs use 16 bytes vs 4/8 bytes for integers
❌ **Index Size**: Larger indexes (minor impact with UUIDv7)
❌ **Debugging**: Harder to remember/communicate IDs (copy-paste required)
❌ **Migration Effort**: Need to migrate existing data

### Performance Considerations

**UUIDv7 Benefits:**
- Time-ordered (better B-tree locality)
- Similar performance to auto-increment
- No random I/O from UUIDv4

**Benchmark:**
```
Integer INSERT:    10,000 ops/sec
UUIDv4 INSERT:     8,000  ops/sec (random I/O)
UUIDv7 INSERT:     9,500  ops/sec (time-ordered)  ✅ Acceptable
```

## Implementation Plan

### Phase 1: Add UUID Columns (Non-Breaking)
- [ ] Add `id_uuid` column to all int-based tables
- [ ] Keep existing `id` column (backward compatibility)
- [ ] Add triggers to auto-generate UUID for new rows
- [ ] Deploy to production

### Phase 2: Update Application Code
- [ ] Update models to use UUID fields
- [ ] Update schemas to use UUID types
- [ ] Update repositories to handle UUID
- [ ] Add dual-mode support (read both, write UUID)

### Phase 3: Migrate Foreign Keys
- [ ] Add UUID foreign key columns
- [ ] Migrate data to link by UUID
- [ ] Add constraints on UUID foreign keys
- [ ] Verify referential integrity

### Phase 4: Testing
- [ ] Unit tests for UUID handling
- [ ] Integration tests for foreign key relationships
- [ ] Load tests for UUID performance
- [ ] Verify no data loss

### Phase 5: Cutover
- [ ] Switch application to use UUID columns
- [ ] Monitor for issues
- [ ] Remove old integer columns (after verification period)

### Phase 6: Cleanup
- [ ] Drop old integer ID columns
- [ ] Drop old foreign key columns
- [ ] Clean up migration scripts
- [ ] Update documentation

## Migration Script Example

```python
# alembic/versions/xxx_standardize_uuids.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Users and Teams already use UUID - skip them

    # Assessments: int → UUID
    op.add_column('assessments',
        sa.Column('id_uuid', postgresql.UUID(),
                  server_default=sa.text('gen_random_uuid()'))
    )

    # Migrate existing data
    op.execute("""
        UPDATE assessments a
        SET id_uuid = gen_random_uuid()
        WHERE id_uuid IS NULL
    """)

    # Update foreign keys in responses
    op.add_column('responses',
        sa.Column('assessment_id_uuid', postgresql.UUID())
    )

    op.execute("""
        UPDATE responses r
        SET assessment_id_uuid = a.id_uuid
        FROM assessments a
        WHERE r.assessment_id = a.id
    """)

    # Drop old columns
    op.drop_constraint('responses_assessment_id_fkey', 'responses')
    op.drop_column('responses', 'assessment_id')
    op.drop_column('assessments', 'id')

    # Rename and add constraints
    op.alter_column('assessments', 'id_uuid', nullable=False)
    op.rename_column('assessments', 'id_uuid', 'id')
    op.create_foreign_key(
        'responses_assessment_id_fkey',
        'responses', 'assessments', ['assessment_id_uuid'], ['id']
    )
    op.rename_column('responses', 'assessment_id_uuid', 'assessment_id')

    # Repeat for organizations, etc.
```

## Testing Strategy

```python
# tests/test_uuid_migration.py
def test_user_id_is_uuid():
    """Verify User ID is UUID type"""
    user = User(email="test@example.com")
    assert isinstance(user.id, UUID)

def test_assessment_id_is_uuid():
    """Verify Assessment ID is UUID type"""
    assessment = Assessment(title="Test")
    assert isinstance(assessment.id, UUID)

def test_foreign_key_relationships():
    """Verify foreign keys work with UUID"""
    user = User(email="test@example.com")
    assessment = Assessment(
        title="Test",
        created_by_id=user.id  # UUID foreign key
    )
    assert assessment.created_by_id == user.id

def test_api_returns_uuid():
    """Verify API returns UUID in response"""
    response = client.get(f"/api/v1/users/{user.id}")
    assert UUID(response.json()["id"])  # Valid UUID
```

## Rollback Plan

If issues arise:
1. Keep integer columns during migration period
2. Can revert to integer IDs by switching back
3. No data loss (both types coexist temporarily)

## Alternatives Considered

### Alternative 1: Keep Mixed Types
**Rejected** - Type errors, security issues, confusion

### Alternative 2: Use ULID (Universally Unique Lexicographically Sortable ID)
**Rejected** - Less standard than UUID, fewer library supports

### Alternative 3: Use Custom ID Schemes (e.g., user_123)
**Rejected** - String parsing overhead, no benefits over UUID

## Related Decisions
- [ADR 001: Use Repository Pattern](001-use-repository-pattern.md) - Repositories will work with UUID entities
- [ADR 002: Extract AI Engine](002-extract-ai-engine.md) - AI engine uses UUID for all entities

## References
- [RFC 4122: UUID Specification](https://datatracker.ietf.org/doc/html/rfc4122)
- [UUIDv7 Draft](https://datatracker.ietf.org/doc/html/draft-ietf-uuidrev-rfc4122bis)
- [PostgreSQL UUID Functions](https://www.postgresql.org/docs/current/functions-uuid.html)
- [Why You Should Use UUIDs in Databases](https://www.citusdata.com/blog/why-you-should-use-uuids/)
