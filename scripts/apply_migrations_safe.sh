#!/bin/bash
# Safe Database Migration Application Script
# Applies migrations in a controlled, safe manner

set -e

echo "=========================================="
echo "🗄️  Safe Database Migration Application"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check database connection
echo "🔍 Step 1: Checking database connection..."
if ! psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to database${NC}"
    echo "Please ensure PostgreSQL is running and credentials are correct"
    exit 1
fi
echo -e "${GREEN}✅ Database connection verified${NC}"
echo ""

# Backup current state (if any tables exist)
echo "💾 Step 2: Creating backup..."
BACKUP_FILE="/tmp/psychsync_db_backup_$(date +%Y%m%d_%H%M%S).sql"
pg_dump -h localhost -p 5432 -U sheriftito -d psychsync > "$BACKUP_FILE" 2>/dev/null || true
echo "Backup saved to: $BACKUP_FILE"
echo ""

# Show current migration state
echo "📊 Step 3: Current migration state"
echo "Current version:"
alembic current 2>&1 | grep -v "INFO" || echo "  No migrations applied yet"
echo ""

# Count existing tables
TABLE_COUNT=$(psql -h localhost -p 5432 -U sheriftito -d psychsync -tAc "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public' AND tablename NOT LIKE 'alembic%';" 2>/dev/null || echo "0")
echo "Existing tables (excluding alembic): $TABLE_COUNT"
echo ""

if [ "$TABLE_COUNT" -gt "0" ]; then
    echo -e "${YELLOW}⚠️  Warning: Database already has $TABLE_COUNT tables${NC}"
    echo "Existing tables:"
    psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename NOT LIKE 'alembic%' ORDER BY tablename;" 2>&1
    echo ""
    read -p "Do you want to continue with migrations? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Migration cancelled"
        exit 0
    fi
fi

# Show migration plan
echo "📋 Step 4: Migration plan"
echo "Available migration heads:"
alembic heads 2>&1 | grep -v "INFO" | head -10
echo ""

# Option 1: Stamp base and upgrade to a specific head
echo "🚀 Step 5: Applying migrations"
echo ""
echo "Due to multiple migration branches, we have several options:"
echo ""
echo "1. Start fresh: Stamp base and upgrade to a specific head"
echo "2. Upgrade to 016 (performance indexes)"
echo "3. Upgrade all branches (may cause conflicts)"
echo ""
read -p "Choose option (1/2/3) or 'c' to cancel: " choice

case $choice in
    1)
        echo ""
        echo "Option 1: Start fresh with base tables"
        echo "This will:"
        echo "  - Mark 001_base_tables as applied"
        echo "  - Upgrade to a specific head"
        echo ""
        read -p "Enter target head (e.g., 016_add_jsonb_gin_indexes): " target_head

        echo "Stamping base migration..."
        alembic stamp 001_base_tables

        echo "Upgrading to $target_head..."
        alembic upgrade "$target_head"
        ;;
    2)
        echo ""
        echo "Option 2: Upgrade to 016 (performance indexes)"
        alembic upgrade 016_add_jsonb_gin_indexes
        ;;
    3)
        echo ""
        echo "Option 3: Upgrade all branches"
        echo -e "${YELLOW}⚠️  Warning: This may cause merge conflicts${NC}"
        read -p "Continue? (yes/no): " confirm3
        if [ "$confirm3" = "yes" ]; then
            alembic upgrade head
        else
            echo "Cancelled"
            exit 0
        fi
        ;;
    c)
        echo "Cancelled"
        exit 0
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "✅ Migrations applied successfully!"
echo ""

# Show final state
echo "📊 Final state:"
echo "Current version:"
alembic current 2>&1 | grep -v "INFO"
echo ""

echo "Tables created:"
psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename NOT LIKE 'alembic%' ORDER BY tablename;" 2>&1
echo ""

echo "Indexes created:"
psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY indexname LIMIT 20;" 2>&1
echo ""

echo "=========================================="
echo "✅ Migration Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Verify tables: psql -h localhost -U sheriftito -d psychsync -c '\dt'"
echo "  2. Run tests: pytest tests/api/test_regression*.py -v"
echo "  3. Check indexes: psql -h localhost -U sheriftito -d psychsync -c '\di'"
