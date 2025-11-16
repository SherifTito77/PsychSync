#!/bin/bash
# File: rollback_migration.sh
# Rollback the bad migration that tried to drop tables

echo "============================================================"
echo "Rolling back bad migration"
echo "============================================================"

# Downgrade to before the bad migration
alembic downgrade -1

# Delete the bad migration files
echo "Deleting bad migration files..."
rm -f alembic/versions/595123337aa3_merge_multiple_heads.py
rm -f alembic/versions/950e4ee0013a_add_organization_support_to_teams.py

echo "✅ Rolled back. Now we need to check your actual database schema."
