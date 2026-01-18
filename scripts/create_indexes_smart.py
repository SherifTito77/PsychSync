#!/usr/bin/env python3
"""
Create Composite Indexes - Schema-Aware Version

This script checks the actual database schema and only creates indexes
for columns that exist. This makes it more resilient to schema differences.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def get_table_columns(engine, table_name: str) -> list[str]:
    """Get list of columns for a table."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """), {"table_name": table_name})
        return [row[0] for row in result.fetchall()]

def index_exists(engine, index_name: str) -> bool:
    """Check if an index already exists."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 1 FROM pg_indexes
            WHERE indexname = :index_name
        """), {"index_name": index_name})
        return result.scalar() is not None

def create_indexes():
    """Create composite indexes based on actual schema."""

    engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))

    # Define indexes with their required columns
    index_definitions = [
        {
            "name": "idx_team_members_team_user",
            "table": "team_members",
            "columns": ["team_id", "user_id"],
        },
        {
            "name": "idx_team_members_user_created",
            "table": "team_members",
            "columns": ["user_id", "created_at"],
        },
        {
            "name": "idx_team_members_team_role",
            "table": "team_members",
            "columns": ["team_id", "role"],
        },
        {
            "name": "idx_responses_user_assessment",
            "table": "responses",
            "columns": ["user_id", "assessment_id"],
        },
        {
            "name": "idx_assessments_org_created",
            "table": "assessments",
            "columns": ["organization_id", "created_at"],
        },
        {
            "name": "idx_users_org_active",
            "table": "users",
            "columns": ["organization_id", "is_active"],
        },
        {
            "name": "idx_users_org_created",
            "table": "users",
            "columns": ["organization_id", "created_at"],
        },
        {
            "name": "idx_teams_org_created",
            "table": "teams",
            "columns": ["organization_id", "created_at"],
        },
    ]

    created_count = 0
    skipped_count = 0
    already_exists = 0

    print("="*60)
    print("Creating Composite Indexes")
    print("="*60)

    for idx_def in index_definitions:
        # Check if index already exists
        if index_exists(engine, idx_def["name"]):
            print(f"✓ Already exists: {idx_def['name']}")
            already_exists += 1
            continue

        # Check if table exists
        try:
            table_columns = get_table_columns(engine, idx_def["table"])
        except Exception as e:
            print(f"⚠️  Skipped {idx_def['name']}: Table {idx_def['table']} not found")
            skipped_count += 1
            continue

        # Check if all required columns exist
        missing_columns = [col for col in idx_def["columns"] if col not in table_columns]

        if missing_columns:
            print(f"⚠️  Skipped {idx_def['name']}: Missing columns: {missing_columns}")
            skipped_count += 1
            continue

        # Create the index
        columns_str = ", ".join(idx_def["columns"])
        try:
            with engine.connect() as conn:
                conn.execute(text(f"""
                    CREATE INDEX {idx_def['name']}
                    ON {idx_def['table']} ({columns_str})
                """))
                conn.commit()
                print(f"✓ Created: {idx_def['name']} on {idx_def['table']}({columns_str})")
                created_count += 1
        except Exception as e:
            print(f"✗ Failed: {idx_def['name']}: {e}")
            skipped_count += 1

    print("\n" + "="*60)
    print("Index Creation Summary")
    print("="*60)
    print(f"Created: {created_count} indexes")
    print(f"Already existed: {already_exists} indexes")
    print(f"Skipped: {skipped_count} indexes")
    print(f"Total: {created_count + already_exists} indexes created/verified")
    print("="*60)

    # Show what indexes were created
    if created_count > 0:
        print("\nVerifying created indexes...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    schemaname || '.' || relname as table_name,
                    indexrelname as indexname,
                    idx_scan as scans
                FROM pg_stat_user_indexes
                WHERE indexrelname LIKE 'idx_%'
                ORDER BY indexrelname
            """))

            rows = result.fetchall()
            if rows:
                print("\nCreated indexes:")
                for row in rows:
                    print(f"  - {row[1]} on {row[0]}")

if __name__ == "__main__":
    create_indexes()
