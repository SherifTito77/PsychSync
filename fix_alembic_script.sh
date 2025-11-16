#!/bin/bash
# File path: fix_database.sh
# Script to fix alembic migrations and add organization support

echo "============================================================"
echo "PsychSync - Database Fix Script"
echo "============================================================"

# Step 1: Check current alembic heads
echo ""
echo "Step 1: Checking current migration heads..."
alembic heads

# Step 2: Merge multiple heads
echo ""
echo "Step 2: Merging multiple migration heads..."
alembic merge heads -m "merge multiple heads"

# Step 3: Apply merged migrations
echo ""
echo "Step 3: Applying merged migrations..."
alembic upgrade head

# Step 4: Create migration for organization_id in teams
echo ""
echo "Step 4: Creating migration for organization support..."
alembic revision --autogenerate -m "add organization support to teams"

# Step 5: Apply the new migration
echo ""
echo "Step 5: Applying organization migration..."
alembic upgrade head

echo ""
echo "============================================================"
echo "✅ Database migrations completed!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Run: python app/db/seeds/run_seeds.py"
echo "2. Test creating a team"
