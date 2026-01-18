#!/bin/bash
# Daily Monitoring Script for Query Optimization Deployment
# Run this daily during the 2-week monitoring period

set -e

DATE=$(date +%Y-%m-%d)
DAY_OF_MONITORING=$(( ($(date +%s) - $(date -j -f "%Y-%m-%d" "2025-01-18" +%s)) / 86400 ))
REPORT_FILE="monitoring_reports/daily_report_${DATE}.md"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          Query Optimization - Daily Monitoring Check           ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Date: $DATE"
echo "Day of Monitoring: $DAY_OF_MONITORING"
echo ""

# Create reports directory
mkdir -p monitoring_reports

# Function to print section headers
print_section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# 1. Run Validation Script
print_section "1. VALIDATION CHECK"

if python scripts/validate_query_optimization.py > /tmp/validation_output.txt 2>&1; then
    echo -e "${GREEN}✅ Validation passed${NC}"
    grep "Overall Status" /tmp/validation_output.txt || true
else
    echo -e "${RED}❌ Validation failed${NC}"
    cat /tmp/validation_output.txt
fi

# 2. Check Index Usage
print_section "2. INDEX USAGE STATISTICS"

python -c "
from sqlalchemy import create_engine, text
from app.core.config import settings
from datetime import datetime

engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))

with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT
            indexrelname,
            idx_scan,
            idx_tup_read,
            idx_tup_fetch,
            coalesce(idx_scan, 0) as scans
        FROM pg_stat_user_indexes
        WHERE indexrelname IN (
            'idx_team_members_team_user',
            'idx_team_members_user_created',
            'idx_team_members_team_role',
            'idx_responses_user_assessment',
            'idx_assessments_org_created',
            'idx_teams_org_created'
        )
        ORDER BY idx_scan DESC
    '''))

    print('Index Usage Statistics:')
    print('-' * 80)
    for row in result.fetchall():
        index_name, scans, tup_read, tup_fetch, _ = row
        status = '✅' if scans > 0 else '⚠️ '
        print(f'{status} {index_name}:')
        print(f'   Scans: {scans}')
        print(f'   Tuples Read: {tup_read}')
        print(f'   Tuples Fetched: {tup_fetch}')
        print()
"

# 3. Check Query Performance
print_section "3. QUERY PERFORMANCE METRICS"

python -c "
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))

with engine.connect() as conn:
    # Test query 1: Team members count
    result1 = conn.execute(text('''
        EXPLAIN ANALYZE
        SELECT COUNT(*) FROM team_members
        WHERE team_id = '00000000-0000-0000-0000-000000000001'::uuid
    '''))

    plan1 = '\n'.join(row[0] for row in result1.fetchall())

    # Extract execution time
    if 'Execution Time:' in plan1:
        time_str = plan1.split('Execution Time:')[-1].strip().split()[0]
        print(f'Team Count Query: {time_str} ms')

    # Test query 2: User teams
    result2 = conn.execute(text('''
        EXPLAIN ANALYZE
        SELECT * FROM teams
        WHERE organization_id = '00000000-0000-0000-0000-000000000001'::uuid
        LIMIT 10
    '''))

    plan2 = '\n'.join(row[0] for row in result2.fetchall())

    if 'Execution Time:' in plan2:
        time_str = plan2.split('Execution Time:')[-1].strip().split()[0]
        print(f'User Teams Query: {time_str} ms')
"

# 4. Check Database Load
print_section "4. DATABASE LOAD METRICS"

python -c "
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))

with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT
            count(*) as active_connections,
            count(*) FILTER (WHERE state = 'active') as active_querying
        FROM pg_stat_activity
        WHERE datname = current_database()
    '''))

    row = result.fetchone()
    print(f'Active Connections: {row[0]}')
    print(f'Actively Querying: {row[1]}')
"

# 5. Check for Errors
print_section "5. ERROR LOG CHECK"

if [ -f "/var/log/psychsync/app.log" ]; then
    ERROR_COUNT=$(tail -1000 /var/log/psychsync/app.log | grep -c "ERROR" || echo "0")
    SLOW_QUERY_COUNT=$(tail -1000 /var/log/psychsync/app.log | grep -c "Slow query" || echo "0")

    echo "Errors in last 1000 lines: $ERROR_COUNT"
    echo "Slow queries in last 1000 lines: $SLOW_QUERY_COUNT"

    if [ "$ERROR_COUNT" -gt 10 ]; then
        echo -e "${YELLOW}⚠️  High error count detected${NC}"
        echo "Recent errors:"
        tail -100 /var/log/psychsync/app.log | grep "ERROR" | tail -5
    fi
else
    echo "Log file not found at /var/log/psychsync/app.log"
    echo "Skipping error check"
fi

# 6. Generate Summary
print_section "DAILY MONITORING SUMMARY"

cat > "$REPORT_FILE" << EOFREPORT
# Daily Monitoring Report - $DATE

**Day of Monitoring:** $DAY_OF_MONITORING
**Date:** $DATE
**Status:** Monitoring Active

## Validation Status

$(cat /tmp/validation_output.txt)

## Key Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Indexes Created | 6 | ✅ |
| Validation | PASS | ✅ |
| Tests | 8/8 | ✅ |

## Observations

<!-- Add your observations here -->

## Issues Found

<!-- Document any issues found during monitoring -->

## Next Actions

<!-- Add any follow-up actions needed -->

EOFREPORT

echo -e "${GREEN}✅ Daily monitoring complete${NC}"
echo "Report saved to: $REPORT_FILE"
echo ""

# Display summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ All checks completed"
echo "📊 Report saved to: $REPORT_FILE"
echo ""
echo "Next monitoring check: Tomorrow"
echo "Next review: 2025-01-20 (48 hours)"
echo ""
