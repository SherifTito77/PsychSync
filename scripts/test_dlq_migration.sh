#!/bin/bash

# Test DLQ Migration Script
#
# This script tests the dead_letter_tasks table migration by:
# 1. Showing current migration status
# 2. Upgrading to the new migration
# 3. Verifying table creation
# 4. Testing rollback
# 5. Re-applying migration
#
# Usage: ./scripts/test_dlq_migration.sh

set -e  # Exit on error

echo "================================"
echo "DLQ Migration Test Script"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Alembic is available
if ! command -v alembic &> /dev/null; then
    echo -e "${RED}Error: alembic command not found${NC}"
    echo "Please activate your virtual environment first"
    exit 1
fi

# Step 1: Show current migration status
echo -e "${YELLOW}Step 1: Current migration status${NC}"
echo "-----------------------------------"
alembic current
echo ""

# Step 2: Show migration history
echo -e "${YELLOW}Step 2: Migration history${NC}"
echo "-----------------------------------"
alembic history | grep -E "(dead_letter|Add Dead Letter)" | head -5
echo ""

# Step 3: Upgrade to the new migration
echo -e "${YELLOW}Step 3: Upgrading to DLQ migration${NC}"
echo "-----------------------------------"
read -p "Do you want to upgrade the database? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    alembic upgrade head
    echo -e "${GREEN}✓ Upgrade complete${NC}"
else
    echo "Skipping upgrade"
    exit 0
fi
echo ""

# Step 4: Verify table creation
echo -e "${YELLOW}Step 4: Verifying table creation${NC}"
echo "-----------------------------------"
echo "Checking if dead_letter_tasks table exists..."

# Check table exists in PostgreSQL
TABLE_EXISTS=$(python3 -c "
from app.core.database import engine
import asyncio

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(
            \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'dead_letter_tasks')\"
        )
        exists = result.scalar()
        return exists

exists = asyncio.run(check())
print('1' if exists else '0')
" 2>/dev/null || echo "0")

if [ "$TABLE_EXISTS" = "1" ]; then
    echo -e "${GREEN}✓ Table dead_letter_tasks exists${NC}"

    # Show table structure
    echo ""
    echo "Table structure:"
    python3 -c "
from app.core.database import engine
import asyncio

async def show_structure():
    async with engine.begin() as conn:
        result = await conn.execute(\"\"\"
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'dead_letter_tasks'
            ORDER BY ordinal_position
        \"\"\")
        for row in result:
            print(f'  {row[0]:<25} {row[1]:<20} nullable={row[2]:<5} default={row[3]}')

asyncio.run(show_structure())
" 2>/dev/null || echo "  (Could not fetch structure)"

else
    echo -e "${RED}✗ Table dead_letter_tasks does not exist${NC}"
    exit 1
fi
echo ""

# Step 5: Test rollback
echo -e "${YELLOW}Step 5: Testing rollback${NC}"
echo "-----------------------------------"
read -p "Do you want to test rollback? (This will drop the table) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Rolling back to previous revision..."
    alembic downgrade -1
    echo -e "${GREEN}✓ Rollback complete${NC}"

    # Verify table was dropped
    TABLE_EXISTS=$(python3 -c "
from app.core.database import engine
import asyncio

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(
            \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'dead_letter_tasks')\"
        )
        exists = result.scalar()
        return exists

exists = asyncio.run(check())
print('1' if exists else '0')
" 2>/dev/null || echo "0")

    if [ "$TABLE_EXISTS" = "0" ]; then
        echo -e "${GREEN}✓ Table successfully dropped${NC}"
    else
        echo -e "${RED}✗ Table still exists after rollback${NC}"
        exit 1
    fi

    # Re-apply migration
    echo ""
    echo "Re-applying migration..."
    alembic upgrade head
    echo -e "${GREEN}✓ Migration re-applied${NC}"
else
    echo "Skipping rollback test"
fi
echo ""

# Step 6: Final verification
echo -e "${YELLOW}Step 6: Final verification${NC}"
echo "-----------------------------------"
alembic current
echo ""

# Check indexes
echo "Checking indexes..."
python3 -c "
from app.core.database import engine
import asyncio

async def show_indexes():
    async with engine.begin() as conn:
        result = await conn.execute(\"\"\"
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = 'dead_letter_tasks'
            ORDER BY indexname
        \"\"\")
        indexes = result.fetchall()
        if indexes:
            print(f'  Found {len(indexes)} indexes:')
            for idx in indexes:
                print(f'  - {idx[0]}')
        else:
            print('  No indexes found')

asyncio.run(show_indexes())
" 2>/dev/null || echo "  (Could not fetch indexes)"
echo ""

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}DLQ Migration Test Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Start Celery workers with new tasks:"
echo "     celery -A app.core.config.celery_config worker --loglevel=info"
echo ""
echo "  2. Create admin API endpoints for DLQ management"
echo ""
echo "  3. Test the DLQ recovery system"
echo ""
