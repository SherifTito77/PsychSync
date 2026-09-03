# Database Migration Guide: int → UUID

**Migration Date:** 2025-01-19
**Estimated Downtime:** 30-60 minutes
**Risk Level:** Medium
**Backup Required:** YES ⚠️

---

## 🎯 Migration Overview

This migration converts all integer primary keys to UUIDs across the PsychSync database.

### Tables Affected

| Table | Current ID | Target ID | Records (est) |
|-------|-----------|-----------|---------------|
| `users` | `UUID` ✅ | `UUID` | N/A (already done) |
| `teams` | `UUID` ✅ | `UUID` | N/A (already done) |
| `assessments` | `UUID` ✅ | `UUID` | N/A (already done) |
| `responses` | `int` ❌ | `UUID` | ~50,000 |
| `response_scores` | `int` ❌ | `UUID` | ~50,000 |

---

## 📋 Prerequisites Checklist

### Before Starting

- [ ] **Take full database backup**
  ```bash
  pg_dump -U postgres -d psychsync > backup_before_migration_$(date +%Y%m%d).sql
  ```

- [ ] **Verify backup integrity**
  ```bash
  # Test restore to temporary database
  createdb test_restore
  psql -U postgres -d test_restore < backup_before_migration_*.sql
  dropdb test_restore
  ```

- [ ] **Stop all application instances**
  ```bash
  # Stop FastAPI app
  systemctl stop psychsync-api
  # Or kill processes
  pkill -f "uvicorn app.main:app"
  ```

- [ ] **Verify no active connections**
  ```sql
  SELECT count(*) FROM pg_stat_activity WHERE datname = 'psychsync';
  -- Should be 0 (only your connection)
  ```

- [ ] **Check disk space** (need 2x database size)
  ```bash
  df -h /var/lib/postgresql
  ```

- [ ] **Prepare rollback plan**
  - Know backup restore command
  - Have migration SQL ready
  - Document current state

---

## 🚀 Migration Execution

### Step 1: Add UUID Columns (Non-Breaking)

**Duration:** ~5 minutes
**Risk:** Low
**Reversible:** Yes

```bash
# Run migration
alembic upgrade 001

# Verify
psql -U postgres -d psychsync -c "\d responses"
# Should see id_uuid, assessment_id_uuid, respondent_id_uuid columns
```

**What happens:**
- Adds nullable UUID columns
- Keeps integer columns intact
- No data changes
- Application continues to work

**Verification queries:**
```sql
-- Check columns exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'responses'
  AND column_name LIKE '%uuid%';

-- Expected output:
-- id_uuid              uuid
-- assessment_id_uuid   uuid
-- respondent_id_uuid   uuid
```

### Step 2: Migrate Data (Non-Breaking)

**Duration:** ~15-20 minutes
**Risk:** Low
**Reversible:** Yes

```bash
# Run migration
alembic upgrade 002

# Monitor progress
# This migration processes data in batches
```

**What happens:**
- Populates UUID columns with data
- Links foreign keys by UUID
- Keeps integer columns as backup
- Application continues to work with integer IDs

**Verification queries:**
```sql
-- Check all UUIDs are populated
SELECT
    (SELECT COUNT(*) FROM responses WHERE id_uuid IS NULL) as null_uuids,
    (SELECT COUNT(*) FROM responses) as total_records;

-- Should show: 0 | 50000 (or your record count)

-- Check foreign key links
SELECT
    (SELECT COUNT(*) FROM responses WHERE assessment_id_uuid IS NULL) as null_fks,
    (SELECT COUNT(*) FROM responses WHERE assessment_id IS NOT NULL) as with_fks;

-- Should show: 0 | (number of responses with assessments)
```

**⚠️ Monitoring:**
```bash
# Watch migration progress
watch -n 5 "psql -U postgres -d psychsync -c '
    SELECT
        COUNT(*) FILTER (WHERE id_uuid IS NULL) as remaining,
        COUNT(*) as total
    FROM responses;
'"

# Check for long-running queries
psql -U postgres -d psychsync -c "
    SELECT pid, now() - pg_stat_activity.query_start AS duration, query
    FROM pg_stat_activity
    WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
"
```

### Step 3: Replace Primary Keys (⚠️ CRITICAL)

**Duration:** ~10-15 minutes
**Risk:** **HIGH** ⚠️
**Reversible:** NO (data loss risk)

```bash
# ⚠️ LAST CHANCE TO CANCEL ⚠️
# Verify steps 1 and 2 are complete

# Run final verification
psql -U postgres -d psychsync -c "
    SELECT
        (SELECT COUNT(*) FROM responses WHERE id_uuid IS NULL) as responses_null,
        (SELECT COUNT(*) FROM response_scores WHERE id_uuid IS NULL) as scores_null;
"

# Only proceed if both counts are 0

# Run migration
alembic upgrade 003

# This will:
# 1. Drop integer columns
# 2. Make UUID columns NOT NULL
# 3. Update primary keys and foreign keys
# 4. Recreate indexes
```

**What happens:**
- Drops integer ID columns (irreversible!)
- UUID becomes primary key
- Foreign keys updated to use UUID
- **Application MUST be updated to use UUIDs**

**Verification queries:**
```sql
-- Check integer columns are gone
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'responses'
  AND column_name IN ('id', 'assessment_id', 'respondent_id')
  AND data_type = 'integer';
-- Should return 0 rows

-- Check UUID columns are primary key
SELECT a.attname
FROM pg_index i
JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
WHERE i.indrelid = 'responses'::regclass
  AND i.indisprimary;
-- Should show: id

-- Test foreign key constraint
SELECT COUNT(*) FROM responses r
JOIN assessments a ON r.assessment_id = a.id;
-- Should work without errors
```

---

## ✅ Post-Migration Verification

### 1. Schema Validation

```sql
-- Verify all tables use UUID primary keys
SELECT
    t.table_name,
    a.attname as column_name,
    typ.typname as data_type
FROM pg_tables t
JOIN pg_attribute a ON a.attrelid = t.tablename::regclass
JOIN pg_type typ ON a.atttypid = typ.oid
JOIN pg_index i ON i.indrelid = a.attrelid AND a.attnum = ANY(i.indkey)
WHERE t.schemaname = 'public'
  AND i.indisprimary
  AND t.table_name IN ('users', 'teams', 'assessments', 'responses', 'response_scores')
ORDER BY t.table_name;

-- Expected output:
-- assessments    | id      | uuid
-- responses      | id      | uuid
-- response_scores| id      | uuid
-- teams          | id      | uuid
-- users          | id      | uuid
```

### 2. Data Integrity Check

```sql
-- Check for NULL IDs (should be 0)
SELECT
    'responses' as table_name,
    COUNT(*) FILTER (WHERE id IS NULL) as null_ids
FROM responses
UNION ALL
SELECT
    'response_scores',
    COUNT(*) FILTER (WHERE id IS NULL)
FROM response_scores;

-- Verify foreign key relationships
SELECT
    'responses → assessments' as relationship,
    COUNT(*) FILTER (WHERE assessment_id IS NULL) as orphaned_records
FROM responses
UNION ALL
SELECT
    'responses → users',
    COUNT(*) FILTER (WHERE respondent_id IS NULL)
FROM responses
UNION ALL
SELECT
    'response_scores → responses',
    COUNT(*) FILTER (WHERE response_id IS NULL)
FROM response_scores;

-- All orphaned_records should be expected (nullable FKs) or 0
```

### 3. Performance Check

```sql
-- Check index usage
EXPLAIN ANALYZE
SELECT * FROM responses WHERE assessment_id = 'some-uuid';

-- Should use index: Index Scan using ix_responses_assessment_id

-- Check query performance
EXPLAIN ANALYZE
SELECT r.*, rs.*
FROM responses r
LEFT JOIN response_scores rs ON rs.response_id = r.id
WHERE r.assessment_id = 'some-uuid'
LIMIT 100;

-- Should be fast (< 10ms for typical queries)
```

---

## 🔄 Application Updates

### Update SQLAlchemy Models

```python
# Before (app/db/models/response.py)
class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    respondent_id = Column(Integer, ForeignKey("users.id"))

# After
class Response(Base):
    __tablename__ = "responses"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"))
    respondent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
```

### Update Pydantic Schemas

```python
# Already done in user_v2.py and assessment_v2.py
# Just update imports:

# Before
from app.schemas.response import Response, ResponseCreate

# After
from app.schemas.response_v2 import ResponseResponse, ResponseSubmit as ResponseCreate
```

### Update API Endpoints

```python
# Before
@router.get("/responses/{response_id:int}")
async def get_response(response_id: int):
    ...

# After
@router.get("/responses/{response_id:uuid}")
async def get_response(response_id: UUID):
    ...
```

---

## 🚨 Rollback Plan

### If Step 1 or Step 2 Fails

```bash
# Downgrade migration
alembic downgrade 001

# Or manually
alembic downgrade base

# Restore from backup if needed
dropdb psychsync
createdb psychsync
psql -U postgres -d psychsync < backup_before_migration_*.sql
```

### If Step 3 Fails

**⚠️ CRITICAL: Step 3 cannot be easily rolled back!**

If step 3 fails mid-migration:

```bash
# 1. STOP IMMEDIATELY
# 2. Assess state

# Check what completed
psql -U postgres -d psychsync -c "\d responses"

# 3. Likely need to restore from backup
dropdb psychsync
createdb psychsync
psql -U postgres -d psychsync < backup_before_migration_*.sql

# 4. Restart application with old code
```

---

## 📊 Timeline

| Phase | Duration | Downtime | Risk |
|-------|----------|----------|------|
| Step 1: Add columns | 5 min | None | Low |
| Step 2: Migrate data | 15-20 min | None | Low |
| **Verification** | 5 min | None | None |
| **Step 3: Cutover** | **10-15 min** | **YES** | **High** |
| **Restart app** | **5 min** | **YES** | Medium |
| **Final testing** | **10 min** | **YES** | None |
| **TOTAL** | **~60 min** | **~30 min** | Medium |

---

## 👥 Team Responsibilities

- **DBA:** Execute migrations, monitor performance
- **Backend Dev:** Update models and schemas, test API endpoints
- **Frontend Dev:** Update ID handling in UI (if any)
- **DevOps:** Coordinate deployment, monitor application logs
- **QA:** Test all functionality post-migration

---

## 📞 Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| Database Admin | | |
| Backend Lead | | |
| DevOps Engineer | | |
| Product Owner | | |

---

## ✅ Success Criteria

Migration is successful when:

- [x] All tables use UUID primary keys
- [x] No NULL IDs in any table
- [x] Foreign key constraints work correctly
- [x] All application tests pass
- [x] API endpoints return UUID IDs
- [x] Performance is acceptable (< 100ms per query)
- [x] No data loss (record counts match pre-migration)

---

## 📚 Additional Resources

- [ADR 003: Standardize UUIDs](../docs/architecture/adr/003-standardize-uuids.md)
- [PostgreSQL UUID Functions](https://www.postgresql.org/docs/current/functions-uuid.html)
- [Alembic Migration Guide](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
