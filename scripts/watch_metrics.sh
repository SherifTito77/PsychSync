#!/bin/bash
# Real-time metrics monitoring for PsychSync
# Usage: ./watch_metrics.sh

echo "🔍 PsychSync Metrics Monitor"
echo "================================"
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "📊 PsychSync Live Metrics - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"
    echo ""

    # HTTP Requests
    echo "🌐 HTTP Requests (Total):"
    curl -s http://localhost:8000/metrics 2>/dev/null | grep "psychsync_http_requests_total{" | grep -v "#" | awk '{sum+=$NF} END {print "   Total: " sum}'

    # Active Requests
    echo ""
    echo "⚡ Active HTTP Requests:"
    curl -s http://localhost:8000/metrics 2>/dev/null | grep "psychsync_http_requests_active" | grep -v "#" | awk '{print "   " $NF}'

    # Errors
    echo ""
    echo "❌ Authentication Failures:"
    curl -s http://localhost:8000/metrics 2>/dev/null | grep "psychsync_auth_failures_total" | grep -v "#" | awk '{print "   " $NF}'

    # Database
    echo ""
    echo "💾 Database Connections:"
    echo -n "   Active: "
    curl -s http://localhost:8000/metrics 2>/dev/null | grep "psychsync_db_connections_active" | grep -v "#" | awk '{print $NF}'
    echo -n "   Idle: "
    curl -s http://localhost:8000/metrics 2>/dev/null | grep "psychsync_db_connections_idle" | grep -v "#" | awk '{print $NF}'

    # Cache
    echo ""
    echo "🗄️  Cache Performance:"
    HITS=$(curl -s http://localhost:8000/metrics 2>/dev/null | grep "psychsync_cache_hits_total" | grep -v "#" | awk '{sum+=$NF} END {print sum}')
    MISSES=$(curl -s http://localhost:8000/metrics 2>/dev/null | grep "psychsync_cache_misses_total" | grep -v "#" | awk '{sum+=$NF} END {print sum}')
    TOTAL=$((HITS + MISSES))
    if [ $TOTAL -gt 0 ]; then
        HIT_RATE=$((HITS * 100 / TOTAL))
        echo "   Hits: $HITS"
        echo "   Misses: $MISSES"
        echo "   Hit Rate: ${HIT_RATE}%"
    else
        echo "   No cache activity yet"
    fi

    echo ""
    echo "========================================"
    echo "Refreshing in 5 seconds..."
    sleep 5
done
