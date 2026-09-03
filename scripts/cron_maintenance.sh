#!/bin/bash
#
# Database Maintenance Cron Script
#
# This script runs database maintenance tasks on a schedule.
# It's designed to be called from cron with different frequencies.
#
# Usage:
#   ./cron_maintenance.sh [task_type]
#
# Task Types:
#   hourly    - Light maintenance tasks
#   daily     - Standard maintenance tasks
#   weekly    - Comprehensive maintenance
#   monthly   - Deep maintenance tasks

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/var/log/psychsync"
PYTHON_SCRIPT="${SCRIPT_DIR}/database_maintenance.py"

# Environment variables
export PYTHONPATH="${SCRIPT_DIR}/.."
export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:password@localhost:5432/psychsync}"

# Logging setup
mkdir -p "${LOG_DIR}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="${LOG_DIR}/maintenance_$(date '+%Y%m%d').log"

# Function to log messages
log() {
    echo "[$TIMESTAMP] $1" | tee -a "${LOG_FILE}"
}

# Function to send alert on failure
send_alert() {
    local message="$1"
    local exit_code="$2"

    # Send email alert if configured
    if [[ -n "${ALERT_EMAIL:-}" ]]; then
        echo "$message" | mail -s "Database Maintenance Alert - PsychSync" "$ALERT_EMAIL"
    fi

    # Log to system journal if available
    if command -v logger >/dev/null 2>&1; then
        logger -t "psychsync-maintenance" -p daemon.err "$message"
    fi

    return "$exit_code"
}

# Function to run maintenance task
run_task() {
    local task_type="$1"
    local description="$2"

    log "Starting ${description} (${task_type})..."

    # Run the Python maintenance script
    if python3 "${PYTHON_SCRIPT}" 2>&1 | tee -a "${LOG_FILE}"; then
        log "✅ ${description} completed successfully"
        return 0
    else
        local exit_code=$?
        local error_msg="❌ ${description} failed with exit code ${exit_code}"
        log "$error_msg"
        send_alert "$error_msg" "$exit_code"
        return "$exit_code"
    fi
}

# Check if Python script exists and is executable
if [[ ! -x "${PYTHON_SCRIPT}" ]]; then
    log "❌ Maintenance script not found or not executable: ${PYTHON_SCRIPT}"
    exit 1
fi

# Check Python dependencies
if ! python3 -c "import asyncpg, psycopg2" 2>/dev/null; then
    log "❌ Required Python modules missing (asyncpg, psycopg2)"
    log "Installing missing dependencies..."
    pip3 install asyncpg psycopg2-binary 2>&1 | tee -a "${LOG_FILE}"
fi

# Main logic based on task type
case "${1:-daily}" in
    "hourly")
        log "🔄 Running HOURLY maintenance tasks"

        # Light maintenance - quick checks and updates
        log "Checking database connectivity..."
        python3 -c "
import asyncio
import asyncpg

async def check():
    try:
        conn = await asyncpg.connect('${DATABASE_URL}')
        await conn.execute('SELECT 1')
        await conn.close()
        print('✅ Database connectivity OK')
    except Exception as e:
        print(f'❌ Database connectivity failed: {e}')
        exit(1)

asyncio.run(check())
" 2>&1 | tee -a "${LOG_FILE}"

        # Update statistics for frequently changed tables
        log "Updating statistics for high-traffic tables..."
        python3 -c "
import asyncio
import asyncpg

async def update_stats():
    conn = await asyncpg.connect('${DATABASE_URL}')
    tables = ['responses', 'audit_logs', 'notifications']
    for table in tables:
        try:
            await conn.execute(f'ANALYZE {table}')
            print(f'✅ Updated statistics for {table}')
        except Exception as e:
            print(f'⚠️ Could not update {table}: {e}')
    await conn.close()

asyncio.run(update_stats())
" 2>&1 | tee -a "${LOG_FILE}"

        log "✅ Hourly maintenance completed"
        ;;

    "daily")
        log "🔄 Running DAILY maintenance tasks"

        # Standard maintenance - vacuum, analyze, index checks
        run_task "daily" "Daily Maintenance"

        # Refresh materialized views
        log "Refreshing materialized views..."
        python3 -c "
import asyncio
import asyncpg

async def refresh_views():
    conn = await asyncpg.connect('${DATABASE_URL}')
    views = ['user_analytics_summary', 'team_analytics_summary', 'assessment_analytics_summary']
    for view in views:
        try:
            await conn.execute(f'REFRESH MATERIALIZED VIEW CONCURRENTLY {view}')
            print(f'✅ Refreshed {view}')
        except Exception as e:
            print(f'⚠️ Could not refresh {view}: {e}')
    await conn.close()

asyncio.run(refresh_views())
" 2>&1 | tee -a "${LOG_FILE}"

        log "✅ Daily maintenance completed"
        ;;

    "weekly")
        log "🔄 Running WEEKLY maintenance tasks"

        # Comprehensive maintenance
        run_task "daily" "Weekly Maintenance"

        # Additional weekly tasks
        log "Running additional weekly tasks..."

        # Check for long-running queries
        log "Checking for long-running queries..."
        python3 -c "
import asyncio
import asyncpg

async def check_long_queries():
    conn = await asyncpg.connect('${DATABASE_URL}')
    try:
        result = await conn.fetch('''
            SELECT pid, now() - query_start as duration, query
            FROM pg_stat_activity
            WHERE state = 'active' AND now() - query_start > interval '1 hour'
            ORDER BY duration DESC
        ''')
        if result:
            print(f'⚠️ Found {len(result)} long-running queries (>1 hour)')
            for row in result:
                print(f'  PID {row['pid']}: {row['duration']}')
        else:
            print('✅ No long-running queries detected')
    except Exception as e:
        print(f'⚠️ Could not check long queries: {e}')
    await conn.close()

asyncio.run(check_long_queries())
" 2>&1 | tee -a "${LOG_FILE}"

        # Database size monitoring
        log "Monitoring database size..."
        python3 -c "
import asyncio
import asyncpg

async def size_check():
    conn = await asyncpg.connect('${DATABASE_URL}')
    try:
        result = await conn.fetchval('SELECT pg_size_pretty(pg_database_size(current_database()))')
        print(f'📊 Current database size: {result}')

        # Check for rapid growth (compare with last week if we have historical data)
        size_bytes = await conn.fetchval('SELECT pg_database_size(current_database())')
        size_gb = size_bytes / (1024**3)

        if size_gb > 50:  # Alert if > 50GB
            print(f'⚠️ Database size is large: {size_gb:.1f} GB')
        elif size_gb > 100:  # Critical alert if > 100GB
            print(f'🚨 Database size is critical: {size_gb:.1f} GB')
    except Exception as e:
        print(f'⚠️ Could not check database size: {e}')
    await conn.close()

asyncio.run(size_check())
" 2>&1 | tee -a "${LOG_FILE}"

        log "✅ Weekly maintenance completed"
        ;;

    "monthly")
        log "🔄 Running MONTHLY maintenance tasks"

        # Deep maintenance - full vacuum and comprehensive checks
        log "Running comprehensive maintenance..."

        # Run all maintenance tasks
        run_task "daily" "Monthly Maintenance"

        # Additional monthly deep maintenance
        log "Running deep maintenance tasks..."

        # Check table bloat
        log "Analyzing table bloat..."
        python3 -c "
import asyncio
import asyncpg

async def bloat_check():
    conn = await asyncpg.connect('${DATABASE_URL}')
    try:
        result = await conn.fetch('''
            SELECT
                schemaname,
                tablename,
                ROUND(CASE WHEN otta=0 THEN 0.0 ELSE sml.relpages/otta::numeric END - 1) * 100 AS bloat_pct
            FROM (
                SELECT
                    cs.schemaname, cs.tablename, cc.reltuples, cc.relpages,
                    FLOOR((cc.reltuples * (24 + MAX(CASE WHEN null_frac <> 0 THEN NULL ELSE avg_width END))) / current_setting('block_size')::integer) AS otta
                FROM pg_stats cs JOIN pg_class cc ON cs.tablename = cc.relname
                WHERE cs.schemaname = 'public' GROUP BY 1,2,3,4
            ) AS sml
            JOIN pg_stat_user_tables psut ON sml.tablename = psut.relname
            WHERE sml.otta > 0
            ORDER BY bloat_pct DESC
            LIMIT 10
        ''')

        if result:
            print(f'📊 Top 10 tables by bloat:')
            for row in result:
                status = '🚨' if row['bloat_pct'] > 50 else '⚠️' if row['bloat_pct'] > 25 else '✅'
                print(f'  {status} {row['tablename']}: {row['bloat_pct']:.1f}% bloat')
        else:
            print('✅ No significant table bloat detected')
    except Exception as e:
        print(f'⚠️ Could not analyze bloat: {e}')
    await conn.close()

asyncio.run(bloat_check())
" 2>&1 | tee -a "${LOG_FILE}"

        # Update all table statistics
        log "Updating statistics for all tables..."
        python3 -c "
import asyncio
import asyncpg

async def update_all_stats():
    conn = await asyncpg.connect('${DATABASE_URL}')
    try:
        result = await conn.fetch('SELECT tablename FROM pg_tables WHERE schemaname = \'public\'')
        for row in result:
            try:
                await conn.execute(f'ANALYZE {row[\"tablename\"]}')
            except Exception as e:
                print(f'⚠️ Could not analyze {row[\"tablename\"]}: {e}')
        print(f'✅ Updated statistics for all tables')
    except Exception as e:
        print(f'⚠️ Could not update all statistics: {e}')
    await conn.close()

asyncio.run(update_all_stats())
" 2>&1 | tee -a "${LOG_FILE}"

        # Generate monthly report
        log "Generating monthly maintenance report..."
        {
            echo "PsychSync Database Maintenance Report - $(date '+%B %Y')"
            echo "=================================================="
            echo ""
            echo "Database Statistics:"
            python3 -c "
import asyncio
import asyncpg

async def report():
    conn = await asyncpg.connect('${DATABASE_URL}')
    try:
        # Database size
        size = await conn.fetchval('SELECT pg_size_pretty(pg_database_size(current_database()))')
        print(f'  Database Size: {size}')

        # Table counts
        tables = await conn.fetchval('SELECT COUNT(*) FROM pg_tables WHERE schemaname = \'public\'')
        print(f'  User Tables: {tables}')

        # Index counts
        indexes = await conn.fetchval('SELECT COUNT(*) FROM pg_indexes WHERE schemaname = \'public\'')
        print(f'  Indexes: {indexes}')

        # Connection stats
        conns = await conn.fetchrow('SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE state = \'active\') as active FROM pg_stat_activity')
        print(f'  Connections: {conns[\"total\"]} total, {conns[\"active\"]} active')

    except Exception as e:
        print(f'  Error generating stats: {e}')
    finally:
        await conn.close()

asyncio.run(report())
"
            echo ""
            echo "Recent Maintenance Log Entries:"
            tail -20 "${LOG_FILE}" | grep -E "(✅|❌|⚠️)" | tail -10
        } | tee -a "${LOG_FILE}"

        log "✅ Monthly maintenance completed"
        ;;

    "help"|"-h"|"--help")
        echo "PsychSync Database Maintenance Script"
        echo ""
        echo "Usage: $0 [task_type]"
        echo ""
        echo "Task Types:"
        echo "  hourly    - Light maintenance tasks (every hour)"
        echo "  daily     - Standard maintenance tasks (every day at 2 AM)"
        echo "  weekly    - Comprehensive maintenance (every Sunday at 3 AM)"
        echo "  monthly   - Deep maintenance tasks (1st of month at 4 AM)"
        echo "  help      - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 daily     # Run daily maintenance"
        echo "  $0 weekly    # Run weekly maintenance"
        echo ""
        echo "Environment Variables:"
        echo "  DATABASE_URL - PostgreSQL connection string"
        echo "  ALERT_EMAIL  - Email for maintenance alerts"
        exit 0
        ;;

    *)
        log "❌ Unknown task type: $1"
        log "Use '$0 help' for usage information"
        exit 1
        ;;
esac

log "🎉 Maintenance script completed successfully"
exit 0
