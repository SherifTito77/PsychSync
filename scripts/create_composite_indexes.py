#!/usr/bin/env python3
"""
Create Composite Indexes for Query Optimization

This script creates the composite indexes defined in the migration.
Run this to apply the indexes if Alembic migration doesn't work.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy import create_engine, text
from app.core.config import settings

def create_indexes():
    """Create all composite indexes for query optimization."""

    # Create sync engine
    engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))

    indexes_to_create = [
        # Team members indexes
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
        # Assessments indexes
        {
            "name": "idx_assessments_org_created",
            "table": "assessments",
            "columns": ["organization_id", "created_at"],
        },
        {
            "name": "idx_assessments_org_status",
            "table": "assessments",
            "columns": ["organization_id", "status"],
        },
        {
            "name": "idx_assessments_creator_created",
            "table": "assessments",
            "columns": ["created_by_id", "created_at"],
        },
        # Users indexes
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
        # Teams indexes
        {
            "name": "idx_teams_org_created",
            "table": "teams",
            "columns": ["organization_id", "created_at"],
        },
        # Organizations indexes
        {
            "name": "idx_organizations_name",
            "table": "organizations",
            "columns": ["name"],
        },
    ]

    created_count = 0
    already_exists = 0

    with engine.connect() as conn:
        for idx in indexes_to_create:
            # Check if index already exists
            result = conn.execute(text("""
                SELECT 1 FROM pg_indexes
                WHERE tablename = :table_name
                AND indexname = :index_name
            """), {"table_name": idx["table"], "index_name": idx["name"]})

            exists = result.scalar() is not None

            if exists:
                print(f"✓ Index already exists: {idx['name']}")
                already_exists += 1
            else:
                # Create index
                columns_str = ", ".join(idx["columns"])
                conn.execute(text(f"""
                    CREATE INDEX {idx['name']}
                    ON {idx['table']} ({columns_str})
                """))
                conn.commit()
                print(f"✓ Created index: {idx['name']}")
                created_count += 1

    print(f"\n{'='*60}")
    print(f"Index Creation Complete!")
    print(f"{'='*60}")
    print(f"Created: {created_count} indexes")
    print(f"Already existed: {already_exists} indexes")
    print(f"Total: {created_count + already_exists} indexes")
    print(f"{'='*60}")

    # Show index usage
    print("\nVerifying indexes...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                schemaname || '.' || tablename as table_name,
                indexname,
                idx_scan as scans
            FROM pg_stat_user_indexes
            WHERE indexname LIKE 'idx_%'
            ORDER BY idx_scan DESC
            LIMIT 10
        """))

        rows = result.fetchall()
        if rows:
            print("\nTop indexes by usage:")
            for row in rows:
                print(f"  {row[1]} on {row[0]}: {row[2]} scans")

if __name__ == "__main__":
    create_indexes()
