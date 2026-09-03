# PsychSync Database Migration Guide

**Version:** 2.0.0
**Last Updated:** 2025-01-19

---

## Overview

This guide covers database migration procedures for PsychSync, including:
- Running migrations
- Rolling back migrations
- Zero-downtime migrations
- UUID migration procedures

---

## Table of Contents

1. [Migration Basics](#migration-basics)
2. [Running Migrations](#running-migrations)
3. [Rolling Back](#rolling-back)
4. [Zero-Downtime Migrations](#zero-downtime-migrations)
5. [UUID Migration Procedure](#uuid-migration-procedure)
6. [Troubleshooting](#troubleshooting)

---

## Migration Basics

### Alembic Configuration

**File:** `alembic.ini`

```ini
[alembic]
script_location = alembic
file_template = %%(year)d%%(month).2d%%(day).2d_%%(rev)s_%%(slug)s
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost:5432/psychsync

[post_write_hooks]
# Format migration files with black
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -q

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### Migration Environment

**File:** `alembic/env.py`

```python
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import your Base and models
from app.core.database import Base
from app.db.models import *  # Import all models

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

# Other configuration...
def run_migrations_online() -> None:
    """Run migrations in 'online' mode"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def do_run_migrations(connection):
        await connection.run_sync(do_run_migrations_sync)

    async def run_migrations(connection):
        await connection.run_sync(do_run_migrations_sync)

    # ... rest of configuration
```

---

## Running Migrations

### Create New Migration

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Example
alembic revision --autogenerate -m "add user preferences table"
```

**This creates:** `alembic/versions/YYYYMMDD_add_user_preferences_table.py`

### Review Generated Migration

**Always review auto-generated migrations!**

```python
# alembic/versions/20250119_add_user_preferences_table.py
"""add user preferences table

Revision ID: abc123
Revises: def456
Create Date: 2025-01-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ✓ Check these are correct
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('preferences', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'])


def downgrade() -> None:
    # ✓ Verify rollback is correct
    op.drop_index('ix_user_preferences_user_id', table_name='user_preferences')
    op.drop_table('user_preferences')
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade abc123

# Show current version
alembic current

# Show migration history
alembic history
```

### Production Migration Procedure

```bash
# 1. BACKUP DATABASE FIRST
aws rds create-db-snapshot \
  --db-instance-identifier psychsync-prod \
  --db-snapshot-identifier pre-migration-$(date +%Y%m%d-%H%M%S)

# 2. Review migrations
alembic review

# 3. Test on staging
DATABASE_URL=staging_db_url alembic upgrade head

# 4. Run on production (with transaction)
alembic upgrade head --sql

# 5. Verify
alembic current
```

---

## Rolling Back

### Rollback One Migration

```bash
# Rollback single migration
alembic downgrade -1

# Equivalent to
alembic downgrade base
```

### Rollback to Specific Version

```bash
# Rollback to specific revision
alembic downgrade abc123

# Rollback multiple steps
alembic downgrade -3  # Rollback 3 migrations
```

### Rollback in Production

```bash
# EMERGENCY ROLLBACK PROCEDURE

# 1. Stop application
aws ecs update-service \
  --cluster psychsync-prod \
  --service psychsync-backend \
  --desired-count 0

# 2. Rollback migrations
alembic downgrade abc123

# 3. Restart application
aws ecs update-service \
  --cluster psychsync-prod \
  --service psychsync-backend \
  --desired-count 3

# 4. Verify
curl https://api.psychsync.com/health
```

---

## Zero-Downtime Migrations

### Strategy: Expand-Contract Pattern

For production-critical tables, use expand-contract:

**Step 1: Expand (Add New)**

```python
# Migration 1: Add new column (nullable)
def upgrade() -> None:
    op.add_column('users',
        sa.Column('new_email_field', sa.String(), nullable=True)
    )
```

**Step 2: Migrate Data**

```python
# Migration 2: Copy data
def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        "UPDATE users SET new_email_field = email WHERE new_email_field IS NULL"
    )
```

**Step 3: Backfill & Deploy Code**

```python
# Migration 3: Backfill remaining data
def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        "UPDATE users SET new_email_field = email WHERE new_email_field IS NULL"
    )
```

**Step 4: Contract (Remove Old)**

```python
# Migration 4: Remove old column
def upgrade() -> None:
    op.drop_column('users', 'email')
    op.alter_column('users', 'new_email_field', nullable=False)
```

### Large Table Migrations

**For tables with millions of rows:**

```python
# Batch processing migration
def upgrade() -> None:
    connection = op.get_bind()

    BATCH_SIZE = 10000
    offset = 0

    while True:
        # Process batch
        result = connection.execute(
            f"UPDATE users SET new_field = old_field "
            f"WHERE new_field IS NULL "
            f"LIMIT {BATCH_SIZE} OFFSET {offset}"
        )

        if result.rowcount == 0:
            break

        offset += BATCH_SIZE
        print(f"Processed {offset} rows")
```

---

## UUID Migration Procedure

### Overview

Migrating from integer IDs to UUIDs requires careful planning to avoid breaking foreign keys.

### Migration Strategy

**Three-Step Migration:**

1. **Step 1:** Add UUID columns (non-breaking)
2. **Step 2:** Migrate data and link foreign keys
3. **Step 3:** Replace integer keys (breaking)

### Step 1: Add UUID Columns

```python
# alembic/versions/20250119_standardize_uuids_step1_add_columns.py

def upgrade() -> None:
    # Add UUID columns to all tables
    for table in ['users', 'assessments', 'organizations', 'teams']:
        op.add_column(
            table,
            sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True)
        )
        op.add_column(
            table,
            sa.Column('created_at', sa.DateTime(), nullable=True)
        )
        op.add_column(
            table,
            sa.Column('updated_at', sa.DateTime(), nullable=True)
        )

        # Create indexes on UUID columns
        op.create_index(
            f'ix_{table}_id_uuid',
            table,
            ['id_uuid']
        )
```

### Step 2: Migrate Data

```python
# alembic/versions/20250119_standardize_uuids_step2_migrate_data.py

def upgrade() -> None:
    connection = op.get_bind()

    # Generate UUIDs for existing records
    connection.execute("""
        UPDATE users
        SET
            id_uuid = gen_random_uuid(),
            created_at = NOW(),
            updated_at = NOW()
        WHERE id_uuid IS NULL
    """)

    # Link foreign keys to new UUID columns
    connection.execute("""
        UPDATE assessments a
        SET created_by_id_uuid = (
            SELECT id_uuid FROM users u WHERE u.id = a.created_by_id
        )
        WHERE created_by_id IS NOT NULL
    """)

    # Similar updates for other foreign keys...
```

### Step 3: Replace Keys

```python
# alembic/versions/20250119_standardize_uuids_step3_replace_keys.py

def upgrade() -> None:
    # This requires planned downtime!

    # 1. Drop old integer columns
    op.drop_constraint('users_pkey', 'users', type_='primarykey')
    op.drop_column('users', 'id')

    # 2. Rename UUID columns
    op.alter_column('users', 'id_uuid', new_column_name='id', nullable=False)

    # 3. Recreate primary keys
    op.create_primary_key('users_pkey', 'users', ['id'])

    # 4. Update foreign keys
    # ... (similar for other tables)
```

### Validation Script

```bash
# scripts/validate_uuid_migration.py

import asyncio
from sqlalchemy import text
from app.core.database import get_async_db

async def validate_migration():
    """Validate UUID migration completed successfully"""

    checks = []

    async for db in get_async_db():
        # Check all UUID columns are populated
        result = await db.execute(
            text("SELECT COUNT(*) FROM users WHERE id IS NULL")
        )
        null_count = result.scalar()
        checks.append(("users.id populated", null_count == 0))

        # Check foreign keys linked correctly
        result = await db.execute(text("""
            SELECT COUNT(*) FROM assessments a
            LEFT JOIN users u ON a.created_by_id = u.id
            WHERE u.id IS NULL AND a.created_by_id IS NOT NULL
        """))
        broken_fks = result.scalar()
        checks.append(("foreign keys valid", broken_fks == 0))

    # Print results
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {check_name}")

    return all(passed for _, passed in checks)

# Run validation
asyncio.run(validate_migration())
```

---

## Troubleshooting

### Migration Conflicts

**Problem:** Multiple developers created migrations with same number

**Solution:**
```bash
# 1. Identify conflict
alembic heads

# 2. Merge migrations
alembic merge -m "merge conflicting migrations" abc123 def456

# 3. Resolve conflicts in merged file
# Edit merged migration file

# 4. Continue
alembic upgrade head
```

### Foreign Key Errors

**Problem:** Migration fails with foreign key constraint error

**Solution:**
```python
# Drop constraint before migration
def upgrade() -> None:
    # Drop foreign key
    op.drop_constraint('fk_assessments_created_by_id', 'assessments')

    # Make your changes
    op.alter_column('users', 'id', type_=postgresql.UUID())

    # Recreate foreign key
    op.create_foreign_key(
        'fk_assessments_created_by_id',
        'assessments', 'users',
        ['created_by_id'], ['id']
    )
```

### Long-Running Migrations

**Problem:** Migration taking too long, blocking deployment

**Solution:**
```python
# Use batch processing
def upgrade() -> None:
    connection = op.get_bind()

    BATCH_SIZE = 1000
    total_processed = 0

    while True:
        result = connection.execute(
            f"UPDATE large_table SET new_field = value "
            f"WHERE processed = false "
            f"LIMIT {BATCH_SIZE}"
        )

        if result.rowcount == 0:
            break

        total_processed += result.rowcount
        print(f"Processed {total_processed} rows")

        # Commit each batch
        connection.commit()
```

### Locked Tables

**Problem:** Migration waiting on table locks

**Solution:**
```bash
# Check for locks
SELECT * FROM pg_stat_activity
WHERE state = 'active'
AND wait_event_type = 'Lock';

# Kill blocking sessions (carefully!)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active'
AND wait_event_type = 'Lock'
AND query NOT LIKE '%pg_stat_activity%';
```

---

## Best Practices

### DO ✅

1. **Always backup before migration**
   ```bash
   pg_dump psychsync > backup_before_migration.sql
   ```

2. **Test migrations on staging first**
   ```bash
   DATABASE_URL=staging_db alembic upgrade head
   ```

3. **Review auto-generated migrations**
   ```bash
   cat alembic/versions/latest_migration.py
   ```

4. **Use transactions**
   ```bash
   alembic upgrade head --sql  # Generate SQL first
   ```

5. **Document breaking changes**
   ```python
   """
   BREAKING CHANGE: This migration removes the 'username' column
   Update application code before running.
   """
   ```

### DON'T ❌

1. **Don't skip testing**
   ```bash
   # ✗ Bad
   alembic upgrade head  # Direct to production

   # ✓ Good
   # Test locally → Test staging → Production
   ```

2. **Don't modify existing migrations**
   ```python
   # ✗ Bad
   # Edit migration abc123.py directly

   # ✓ Good
   # Create new migration def456.py to fix
   ```

3. **Don't run migrations during peak hours**
   ```bash
   # Schedule for low-traffic times (e.g., 2 AM Sunday)
   ```

4. **Don't forget rollback plan**
   ```python
   # Always have working downgrade()
   def downgrade() -> None:
       # Implement rollback logic
   ```

---

## Migration Checklist

### Pre-Migration

- [ ] Database backup created
- [ ] Migration tested on staging
- [ ] Application code reviewed for compatibility
- [ ] Rollback procedure documented
- [ ] Team notified of migration

### During Migration

- [ ] Enable maintenance mode (if needed)
- [ ] Run migration with --sql flag first
- [ ] Monitor progress
- [ ] Check for errors
- [ ] Verify data integrity

### Post-Migration

- [ ] Run validation script
- [ ] Test critical application features
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Update documentation

---

**Related Documentation:**
- Architecture: `docs/ARCHITECTURE.md`
- Deployment: `docs/DEPLOYMENT.md`
- Testing: `docs/TESTING_GUIDELINES.md`

**Support:** dba@psychsync.com
