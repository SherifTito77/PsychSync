#!/bin/bash
################################################################################
# Health Check Script for PsychSync Application
#
# Monitors application health and provides status information
#
# Usage: ./scripts/health_check.sh [options]
#   --watch    Continuously monitor health (updates every 5 seconds)
#   --once     Run health check once and exit
#   --verbose  Show detailed health information
################################################################################

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
HEALTH_ENDPOINT="$API_URL/api/v1/health"
WATCH_MODE=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --watch)
            WATCH_MODE=true
            shift
            ;;
        --once)
            WATCH_MODE=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--watch] [--once] [--verbose]"
            exit 1
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

################################################################################
# HEALTH CHECK FUNCTIONS
################################################################################

check_process() {
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        PID=$(pgrep -f "uvicorn app.main:app" | head -1)
        echo -e "${GREEN}✓${NC} Application process running (PID: $PID)"
        return 0
    else
        echo -e "${RED}✗${NC} Application process not found"
        return 1
    fi
}

check_endpoint() {
    RESPONSE=$(curl -s -w "\n%{http_code}" "$HEALTH_ENDPOINT" 2>/dev/null)
    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓${NC} Health endpoint responding (HTTP $HTTP_CODE)"
        if [ "$VERBOSE" = true ]; then
            echo "  Response: $BODY"
        fi
        return 0
    else
        echo -e "${RED}✗${NC} Health endpoint error (HTTP $HTTP_CODE)"
        if [ "$VERBOSE" = true ]; then
            echo "  Response: $BODY"
        fi
        return 1
    fi
}

check_database() {
    if psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT 1;" &> /dev/null; then
        TABLE_COUNT=$(psql -h localhost -p 5432 -U sheriftito -d psychsync -t -c \
            "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';")

        echo -e "${GREEN}✓${NC} Database connected ($TABLE_COUNT tables)"
        return 0
    else
        echo -e "${RED}✗${NC} Database connection failed"
        return 1
    fi
}

check_memory() {
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        PID=$(pgrep -f "uvicorn app.main:app" | head -1)
        MEM=$(ps -p "$PID" -o rss= | tr -d ' ')
        MEM_MB=$((MEM / 1024 / 1024))

        if [ "$MEM_MB" -lt 500 ]; then
            echo -e "${GREEN}✓${NC} Memory usage: ${MEM_MB}MB"
        elif [ "$MEM_MB" -lt 1000 ]; then
            echo -e "${YELLOW}⚠${NC} Memory usage: ${MEM_MB}MB"
        else
            echo -e "${RED}✗${NC} Memory usage: ${MEM_MB}MB (high)"
        fi

        return 0
    else
        echo -e "${YELLOW}○${NC} Memory usage: N/A (process not running)"
        return 1
    fi
}

check_logs() {
    if [ -f "logs/application.log" ]; then
        ERROR_COUNT=$(tail -100 logs/application.log | grep -i "error" | wc -l | tr -d ' ')

        if [ "$ERROR_COUNT" -eq 0 ]; then
            echo -e "${GREEN}✓${NC} No errors in last 100 log lines"
        else
            echo -e "${YELLOW}⚠${NC} $ERROR_COUNT error(s) in last 100 log lines"
        fi

        return 0
    else
        echo -e "${YELLOW}○${NC} Log file not found"
        return 1
    fi
}

print_status() {
    clear
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║          PsychSync Application Health Check                  ║"
    echo "║                                                              ║"
    echo "║  $(date '+%Y-%m-%d %H:%M:%S')" | sed 's/./ /g'
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    echo "Application Status:"
    check_process
    check_endpoint
    check_database
    check_memory
    check_logs

    echo ""
    echo "Quick Commands:"
    echo "  View logs:    tail -f logs/application.log"
    echo "  Restart:      pkill -f 'uvicorn app.main:app' && ./scripts/deploy_production.sh"
    echo "  API docs:     $API_URL/docs"
    echo ""
}

################################################################################
# MAIN
################################################################################

if [ "$WATCH_MODE" = true ]; then
    echo "Monitoring health (Ctrl+C to exit)..."
    sleep 2

    while true; do
        print_status
        sleep 5
    done
else
    print_status
fi
