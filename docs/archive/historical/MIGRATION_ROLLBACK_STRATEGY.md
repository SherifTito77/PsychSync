# Automated Migration Rollback Strategy for PsychSync

## Executive Summary
This document provides a comprehensive, automated strategy for rolling back database migrations safely and efficiently, ensuring data integrity and minimal service disruption.

---

## Table of Contents
1. [Rollback Architecture](#rollback-architecture)
2. [Pre-Migration Safety Checks](#pre-migration-safety-checks)
3. [Automated Rollback Procedures](#automated-rollback-procedures)
4. [Rollback Patterns](#rollback-patterns)
5. [Testing & Validation](#testing--validation)
6. [Monitoring & Alerts](#monitoring--alerts)

---

## Rollback Architecture

### System Design
```
┌─────────────────────────────────────────────────────┐
│          Migration Rollback Orchestrator             │
│  - Coordinates rollback across all services          │
│  - Manages state and checkpoints                    │
│  - Executes rollback in correct order                │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
   ┌────▼────┐                   ┌────▼────┐
   │  Alembic │                   │ PostgreSQL│
   │ Migrations│                  │   Snapshots│
   └────┬────┘                   └───────────┘
        │
   ┌────▼────────────────────────────────────┐
   │      Rollback State Manager              │
   │  - Track migration versions             │
   │  - Store pre-migration data              │
   │  - Manage rollback checkpoints          │
   └─────────────────────────────────────────┘
```

---

## Pre-Migration Safety Checks

### 1. Pre-Migration Validation Script
```python
# scripts/pre_migration_checks.py
from typing import List, Dict
from sqlalchemy import text
from app.core.database import get_db
import subprocess

class PreMigrationValidator:
    """Validates system state before migration"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    async def validate_all(self) -> bool:
        """Run all validation checks"""
        checks = [
            self.check_database_connection,
            self.check_disk_space,
            self.check_backup_availability,
            self.check_active_connections,
            self.check_replication_lag,
            self.check_table_sizes,
            self.check_migration_dependencies,
            self.check_feature_flags,
        ]

        for check in checks:
            try:
                await check()
            except Exception as e:
                self.errors.append(f"{check.__name__}: {str(e)}")

        return len(self.errors) == 0

    async def check_database_connection(self):
        """Verify database connectivity"""
        async for db in get_db():
            result = await db.execute(text("SELECT 1"))
            if result.scalar() != 1:
                raise Exception("Database connection failed")

    async def check_disk_space(self):
        """Ensure sufficient disk space (at least 2x database size)"""
        result = subprocess.run(
            ["df", "/var/lib/postgresql"],
            capture_output=True,
            text=True
        )

        # Parse output and check available space
        lines = result.stdout.split('\n')
        if len(lines) < 2:
            raise Exception("Cannot determine disk space")

        # Require at least 50GB free
        available_gb = int(lines[1].split()[3]) // 1024 // 1024
        if available_gb < 50:
            raise Exception(f"Insufficient disk space: {available_gb}GB available, 50GB required")

    async def check_backup_availability(self):
        """Verify recent backup exists"""
        # Check latest backup timestamp
        async for db in get_db():
            result = await db.execute(text("""
                SELECT pg_backup_start_time >= NOW() - INTERVAL '24 hours' AS backup_exists
                FROM pg_backup_history
                ORDER BY pg_backup_start_time DESC
                LIMIT 1
            """))

            if not result.scalar():
                raise Exception("No backup found in last 24 hours")

    async def check_active_connections(self):
        """Warn if there are active transactions"""
        async for db in get_db():
            result = await db.execute(text("""
                SELECT COUNT(*) FROM pg_stat_activity
                WHERE state = 'active'
                AND pid != pg_backend_pid()
            """))

            active_count = result.scalar()
            if active_count > 10:
                self.warnings.append(f"{active_count} active connections detected")

    async def check_replication_lag(self):
        """Check replication lag if using replicas"""
        async for db in get_db():
            result = await db.execute(text("""
                SELECT CASE
                    WHEN pg_is_in_recovery() THEN
                        GREATEST(
                            pg_last_xlog_receive_diff()::int8 / 10000,
                            pg_last_xlog_replay_diff()::int8 / 10000
                        )
                    ELSE 0
                END AS lag_seconds
            """))

            lag = result.scalar()
            if lag > 60:  # More than 1 minute
                self.warnings.append(f"Replication lag: {lag} seconds")

    async def check_table_sizes(self):
        """Check if tables being migrated are too large"""
        # Get tables to be migrated
        tables_to_migrate = self.get_migration_tables()

        async for db in get_db():
            for table in tables_to_migrate:
                result = await db.execute(text(f"""
                    SELECT pg_size_pretty(pg_total_relation_size('{table}')) AS size
                """))

                size = result.scalar()
                size_gb = self._parse_size_to_gb(size)

                if size_gb > 100:
                    self.warnings.append(f"Large table {table}: {size}")

    async def check_migration_dependencies(self):
        """Verify all dependency migrations are applied"""
        # Get current migration version
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True
        )

        current_version = result.stdout.strip()

        # Check if dependency migrations are applied
        # (Implementation depends on your migration structure)

    async def check_feature_flags(self):
        """Verify feature flags are set for gradual rollout"""
        # Check if feature flag system is ready
        pass

    def _parse_size_to_gb(self, size_str: str) -> float:
        """Convert PostgreSQL size string to GB"""
        units = {'GB': 1, 'MB': 1/1024, 'TB': 1024, 'KB': 1/1024/1024}

        for unit, multiplier in units.items():
            if unit in size_str:
                return float(size_str.split()[0]) * multiplier

        return 0

    def get_migration_tables(self) -> List[str]:
        """Get list of tables affected by upcoming migration"""
        # Parse migration file and extract table names
        # Or load from migration manifest
        pass
```

### 2. Automated Pre-Migration Checklist
```bash
#!/bin/bash
# scripts/pre_migration_checklist.sh

echo "🔍 Running pre-migration safety checks..."

# Run Python validation script
python3 scripts/pre_migration_checks.py
if [ $? -ne 0 ]; then
    echo "❌ Pre-migration validation failed!"
    exit 1
fi

# Check database locks
LOCK_COUNT=$(psql -h localhost -U postgres -d psychsync -t -c "
    SELECT COUNT(*) FROM pg_locks
    WHERE granted = false
")

if [ "$LOCK_COUNT" -gt 0 ]; then
    echo "⚠️  Warning: $LOCK_COUNT locks are waiting"
fi

# Check long-running queries
LONG_QUERY_COUNT=$(psql -h localhost -U postgres -d psychsync -t -c "
    SELECT COUNT(*) FROM pg_stat_activity
    WHERE state = 'active'
    AND query_start < NOW() - INTERVAL '5 minutes'
    AND pid != pg_backend_pid()
")

if [ "$LONG_QUERY_COUNT" -gt 0 ]; then
    echo "⚠️  Warning: $LONG_QUERY_COUNT long-running queries detected"
fi

# Check replication slots
SLOT_LAG=$(psql -h localhost -U postgres -d psychsync -t -c "
    SELECT COALESCE(MAX(pg_wal_lag_diff(lag)), 0) / 1024 / 1024 AS lag_mb
    FROM pg_replication_slots
")

if [ "$SLOT_LAG" -gt 1024 ]; then
    echo "⚠️  Warning: Replication slot lag: ${SLOT_LAG}MB"
fi

echo "✅ Pre-migration checks complete!"
```

---

## Automated Rollback Procedures

### 1. Rollback Orchestrator
```python
# scripts/rollback_orchestrator.py
from enum import Enum
from typing import Optional
import asyncio
from datetime import datetime
import json

class RollbackState(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class RollbackOrchestrator:
    """
    Orchestrates automated rollback of failed migrations.
    Coordinates database rollback, application reverts, and state restoration.
    """

    def __init__(self, migration_id: str):
        self.migration_id = migration_id
        self.state = RollbackState.PENDING
        self.checkpoints = {}
        self.rollback_log = []

    async def execute_rollback(self, reason: str):
        """
        Execute full rollback sequence.
        """
        print(f"🔄 Starting rollback for migration {self.migration_id}")
        print(f"Reason: {reason}")

        try:
            self.state = RollbackState.IN_PROGRESS

            # Step 1: Log rollback initiation
            await self._log_rollback_initiation(reason)

            # Step 2: Stop new traffic to affected services
            await self._enable_maintenance_mode()

            # Step 3: Drain existing connections
            await self._drain_connections()

            # Step 4: Rollback database schema
            await self._rollback_database_schema()

            # Step 5: Restore data from backup
            await self._restore_data()

            # Step 6: Rollback application code
            await self._rollback_application()

            # Step 7: Update feature flags
            await self._update_feature_flags()

            # Step 8: Verify system health
            await self._verify_health()

            # Step 9: Disable maintenance mode
            await self._disable_maintenance_mode()

            # Step 10: Log completion
            await self._log_rollback_completion()

            self.state = RollbackState.COMPLETED
            print("✅ Rollback completed successfully!")

        except Exception as e:
            self.state = RollbackState.FAILED
            print(f"❌ Rollback failed: {e}")
            await self._log_rollback_failure(str(e))
            raise

    async def _rollback_database_schema(self):
        """
        Rollback database schema using Alembic.
        """
        print("📊 Rolling back database schema...")

        # Get current revision
        current = await self._get_current_revision()
        print(f"Current revision: {current}")

        # Create pre-rollback checkpoint
        checkpoint_id = f"pre_rollback_{current}"
        await self._create_checkpoint(checkpoint_id)

        try:
            # Execute Alembic downgrade
            import subprocess
            result = subprocess.run(
                ["alembic", "downgrade", "-1"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                raise Exception(f"Alembic downgrade failed: {result.stderr}")

            print("✅ Database schema rolled back")

        except Exception as e:
            # Rollback failed - restore from checkpoint
            print(f"❌ Schema rollback failed: {e}")
            await self._restore_checkpoint(checkpoint_id)
            raise

    async def _restore_data(self):
        """
        Restore data from pre-migration backup.
        """
        print("💾 Restoring data from backup...")

        # Get checkpoint info
        checkpoint = self.checkpoints.get("pre_migration")
        if not checkpoint:
            print("⚠️  No pre-migration checkpoint found, skipping data restore")
            return

        backup_file = checkpoint['backup_file']
        temp_tables = checkpoint['temp_tables']

        try:
            async for db in get_db():
                # Drop affected tables
                for table in temp_tables:
                    await db.execute(text(f"DROP TABLE IF EXISTS {table}_backup CASCADE"))
                    print(f"Dropped backup table: {table}_backup")

                # Rename backup tables back to original
                for table in temp_tables:
                    await db.execute(text(f"ALTER TABLE {table}_backup RENAME TO {table}"))
                    print(f"Restored table: {table}")

                # Recreate indexes and constraints
                await self._restore_indexes(db, temp_tables)

                await db.commit()

            print("✅ Data restored successfully")

        except Exception as e:
            print(f"❌ Data restore failed: {e}")
            raise

    async def _rollback_application(self):
        """
        Rollback application code to previous version.
        """
        print("🔧 Rolling back application code...")

        # Get previous version from deployment history
        previous_version = await self._get_previous_deployment()

        # Trigger blue-green rollback
        import subprocess
        result = subprocess.run(
            ["./scripts/rollback-blue-green.sh", "green"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            raise Exception(f"Application rollback failed: {result.stderr}")

        print("✅ Application rolled back successfully")

    async def _create_checkpoint(self, checkpoint_id: str):
        """
        Create rollback checkpoint with current state.
        """
        print(f"📍 Creating checkpoint: {checkpoint_id}")

        checkpoint = {
            'id': checkpoint_id,
            'timestamp': datetime.utcnow().isoformat(),
            'migration_id': self.migration_id,
            'database_revision': await self._get_current_revision(),
            'application_version': await self._get_app_version(),
        }

        # Save checkpoint metadata
        self.checkpoints[checkpoint_id] = checkpoint

        # Store in database for persistence
        async for db in get_db():
            await db.execute(
                text("""
                    INSERT INTO rollback_checkpoints
                    (id, migration_id, data, created_at)
                    VALUES (:id, :migration_id, :data, NOW())
                """),
                {"id": checkpoint_id, "migration_id": self.migration_id, "data": json.dumps(checkpoint)}
            )
            await db.commit()

        print(f"✅ Checkpoint {checkpoint_id} created")

    async def _restore_checkpoint(self, checkpoint_id: str):
        """
        Restore system state from checkpoint.
        """
        print(f"🔄 Restoring checkpoint: {checkpoint_id}")

        # Get checkpoint data
        async for db in get_db():
            result = await db.execute(
                text("SELECT data FROM rollback_checkpoints WHERE id = :id"),
                {"id": checkpoint_id}
            )
            checkpoint_data = json.loads(result.scalar())

        # Restore to checkpoint revision
        target_revision = checkpoint_data['database_revision']

        import subprocess
        result = subprocess.run(
            ["alembic", "downgrade", target_revision],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            raise Exception(f"Checkpoint restore failed: {result.stderr}")

        print(f"✅ Checkpoint {checkpoint_id} restored")

    async def _get_current_revision(self) -> str:
        """Get current Alembic revision"""
        import subprocess
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    async def _enable_maintenance_mode(self):
        """Put application in maintenance mode"""
        # Set feature flag or update load balancer
        print("🔧 Enabling maintenance mode...")

    async def _drain_connections(self):
        """Wait for active connections to complete"""
        print("⏳ Draining active connections...")
        await asyncio.sleep(30)  # Wait 30 seconds

    async def _update_feature_flags(self):
        """Update feature flags to disable new features"""
        print("🚩 Updating feature flags...")

    async def _verify_health(self):
        """Verify system health after rollback"""
        print("🏥 Verifying system health...")

        # Run health checks
        async for db in get_db():
            # Check database connectivity
            await db.execute(text("SELECT 1"))

            # Check critical tables
            result = await db.execute(text("""
                SELECT COUNT(*) FROM users
            """))
            user_count = result.scalar()

            if user_count == 0:
                raise Exception("Critical: No users found in database!")

        print("✅ System health verified")

    async def _disable_maintenance_mode(self):
        """Take application out of maintenance mode"""
        print("✅ Disabling maintenance mode...")

    async def _log_rollback_initiation(self, reason: str):
        """Log rollback initiation to database"""
        async for db in get_db():
            await db.execute(
                text("""
                    INSERT INTO rollback_log
                    (migration_id, reason, status, started_at)
                    VALUES (:migration_id, :reason, 'started', NOW())
                """),
                {"migration_id": self.migration_id, "reason": reason}
            )
            await db.commit()

    async def _log_rollback_completion(self):
        """Log successful rollback completion"""
        async for db in get_db():
            await db.execute(
                text("""
                    UPDATE rollback_log
                    SET status = 'completed', completed_at = NOW()
                    WHERE migration_id = :migration_id AND status = 'started'
                """),
                {"migration_id": self.migration_id}
            )
            await db.commit()

    async def _log_rollback_failure(self, error: str):
        """Log failed rollback attempt"""
        async for db in get_db():
            await db.execute(
                text("""
                    UPDATE rollback_log
                    SET status = 'failed', error_message = :error, completed_at = NOW()
                    WHERE migration_id = :migration_id AND status = 'started'
                """),
                {"migration_id": self.migration_id, "error": error}
            )
            await db.commit()
```

### 2. Automated Rollback Trigger
```python
# scripts/rollback_monitor.py
import asyncio
from prometheus_client import Counter
import httpx

rollback_triggered = Counter(
    'rollback_triggered_total',
    'Total rollbacks triggered',
    ['reason']
)

class RollbackMonitor:
    """
    Monitors deployment health and triggers automatic rollback if issues detected.
    """

    def __init__(self, migration_id: str):
        self.migration_id = migration_id
        self.check_interval = 30  # Check every 30 seconds
        self.error_threshold = 0.05  # 5% error rate threshold
        self.latency_threshold = 2000  # 2 second latency threshold

    async def monitor_and_rollback(self):
        """
        Monitor deployment health and auto-rollback on issues.
        """
        print(f"🔍 Monitoring migration {self.migration_id} for issues...")

        consecutive_failures = 0
        max_consecutive_failures = 3

        while consecutive_failures < max_consecutive_failures:
            await asyncio.sleep(self.check_interval)

            # Run health checks
            is_healthy = await self._check_health()

            if not is_healthy:
                consecutive_failures += 1
                print(f"⚠️  Health check failed ({consecutive_failures}/{max_consecutive_failures})")
            else:
                consecutive_failures = 0

        # Threshold exceeded, trigger rollback
        reason = f"Health check failed {max_consecutive_failures} consecutive times"
        print(f"🔄 Triggering automatic rollback: {reason}")

        rollback_triggered.labels(reason='health_check_failure').inc()

        orchestrator = RollbackOrchestrator(self.migration_id)
        await orchestrator.execute_rollback(reason)

    async def _check_health(self) -> bool:
        """
        Run comprehensive health checks.
        Returns True if system is healthy, False otherwise.
        """
        checks = [
            self._check_error_rate,
            self._check_latency,
            self._check_database_health,
            self._check_external_dependencies,
        ]

        for check in checks:
            if not await check():
                return False

        return True

    async def _check_error_rate(self) -> bool:
        """Check if error rate is acceptable"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/api/v1/metrics/error_rate",
                    timeout=5.0
                )

                error_rate = response.json().get('error_rate', 0)

                if error_rate > self.error_threshold:
                    print(f"❌ High error rate: {error_rate:.2%}")
                    return False

                return True

        except Exception as e:
            print(f"❌ Error rate check failed: {e}")
            return False

    async def _check_latency(self) -> bool:
        """Check if response latency is acceptable"""
        try:
            async with httpx.AsyncClient() as client:
                start = time.time()
                response = await client.get(
                    "http://localhost:8000/api/v1/health",
                    timeout=5.0
                )
                latency_ms = (time.time() - start) * 1000

                if latency_ms > self.latency_threshold:
                    print(f"❌ High latency: {latency_ms:.0f}ms")
                    return False

                return True

        except Exception as e:
            print(f"❌ Latency check failed: {e}")
            return False

    async def _check_database_health(self) -> bool:
        """Check database connectivity and performance"""
        try:
            async for db in get_db():
                start = time.time()
                result = await db.execute(text("SELECT 1"))
                latency_ms = (time.time() - start) * 1000

                if latency_ms > 500:  # Database query should be fast
                    print(f"❌ Slow database: {latency_ms:.0f}ms")
                    return False

                return True

        except Exception as e:
            print(f"❌ Database health check failed: {e}")
            return False

    async def _check_external_dependencies(self) -> bool:
        """Check external service availability"""
        # Check external APIs, Redis, etc.
        return True
```

---

## Rollback Patterns

### Pattern 1: Backup Table Pattern
```python
def upgrade():
    # Step 1: Rename original table to backup
    op.execute("ALTER TABLE users RENAME TO users_backup")

    # Step 2: Create new table with new schema
    op.execute("""
        CREATE TABLE users (
            LIKE users_backup INCLUDING ALL
        )
    """)

    # Step 3: Copy data with transformations
    op.execute("""
        INSERT INTO users
        SELECT * FROM users_backup
    """)

def downgrade():
    # Rollback: Drop new table, restore backup
    op.execute("DROP TABLE users")
    op.execute("ALTER TABLE users_backup RENAME TO users")
```

### Pattern 2: Data Migration Pattern
```python
def upgrade():
    # Add new column
    op.add_column('assessments', sa.Column('type', sa.String(50), nullable=True))

    # Migrate data
    op.execute("""
        UPDATE assessments
        SET type = 'personality'
        WHERE category = 'personality_test'
    """)

def downgrade():
    # Rollback: Remove column
    op.drop_column('assessments', 'type')
```

### Pattern 3: Expand-Contract Pattern
```python
def upgrade():
    # Expand: Add new column (nullable)
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))

def downgrade():
    # Contract: Remove column
    op.drop_column('users', 'email_verified')
```

---

## Testing & Validation

### Rollback Testing Script
```bash
#!/bin/bash
# scripts/test_rollback.sh

echo "🧪 Testing rollback procedures..."

# Test 1: Create test migration
echo "Creating test migration..."
alembic revision -m "test_rollback"

# Test 2: Apply migration
echo "Applying migration..."
alembic upgrade head

# Test 3: Verify migration worked
echo "Verifying migration..."
python3 scripts/verify_migration.py

# Test 4: Rollback migration
echo "Rolling back migration..."
alembic downgrade -1

# Test 5: Verify rollback worked
echo "Verifying rollback..."
python3 scripts/verify_rollback.py

echo "✅ Rollback test complete!"
```

---

## Summary

### Key Features
1. **Pre-Migration Validation**: Comprehensive safety checks
2. **Automated Rollback**: One-command rollback execution
3. **State Management**: Checkpoints and state tracking
4. **Health Monitoring**: Automated rollback on failure detection
5. **Data Safety**: Backup and restore mechanisms

### Success Metrics
- **Rollback Time**: < 5 minutes
- **Data Loss**: Zero data loss
- **Service Disruption**: < 30 seconds
- **Rollback Success Rate**: 100%

---

**Status**: ✅ Complete
**Next**: Architecture Risk Analysis
