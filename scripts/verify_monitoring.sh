#!/bin/bash

# Monitoring Verification Script
# Tests that all monitoring components are working correctly

echo "🔍 PsychSync Monitoring Verification"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if /metrics endpoint exists
echo "📊 Test 1: Prometheus Metrics Endpoint"
echo "---------------------------------------"
METRICS_RESPONSE=$(curl -s http://localhost:8000/metrics 2>&1)

if echo "$METRICS_RESPONSE" | grep -q "psychsync_http_requests_total\|psychsync_http_request_duration_seconds"; then
    echo -e "${GREEN}✅ PASS${NC}: Prometheus metrics endpoint is working"
    echo "   Metrics detected: http_requests_total, http_request_duration_seconds"
else
    echo -e "${RED}❌ FAIL${NC}: Prometheus metrics endpoint not responding correctly"
    echo "   Make sure the app is running: uvicorn app.main:app --reload"
fi
echo ""

# Test 2: Check for SLO/SLI metrics
echo "🎯 Test 2: SLO/SLI Tracking"
echo "---------------------------"
if echo "$METRICS_RESPONSE" | grep -q "psychsync_slo_compliance"; then
    echo -e "${GREEN}✅ PASS${NC}: SLO/SLI metrics are exposed"
    echo "   Metrics detected: slo_compliance"
else
    echo -e "${YELLOW}⚠️  WARN${NC}: SLO/SLI metrics not found (will appear after first request)"
fi
echo ""

# Test 3: Generate some traffic to populate metrics
echo "🔄 Test 3: Generate Test Traffic"
echo "-------------------------------"
echo "Sending test requests to populate metrics..."
curl -s http://localhost:8000/health > /dev/null
curl -s http://localhost:8000/ > /dev/null
curl -s http://localhost:8000/docs > /dev/null

# Wait a moment for metrics to update
sleep 2

echo -e "${GREEN}✅ Test traffic sent${NC}"
echo ""

# Test 4: Check metrics are being populated
echo "📈 Test 4: Metrics Population"
echo "-----------------------------"
METRICS_RESPONSE=$(curl -s http://localhost:8000/metrics 2>&1)

if echo "$METRICS_RESPONSE" | grep -E "psychsync_http_requests_total\{.+\} [1-9]"; then
    echo -e "${GREEN}✅ PASS${NC}: Request metrics are being tracked"
    echo "   Sample metric:"
    echo "$METRICS_RESPONSE" | grep "psychsync_http_requests_total" | head -1
else
    echo -e "${YELLOW}⚠️  WARN${NC}: Request metrics not populated yet"
fi
echo ""

# Test 5: Check database metrics (if DB is available)
echo "💾 Test 5: Database Monitoring"
echo "----------------------------"
if echo "$METRICS_RESPONSE" | grep -q "psychsync_db_query_duration_seconds\|psychsync_db_connections_active"; then
    echo -e "${GREEN}✅ PASS${NC}: Database metrics are exposed"
    echo "   Metrics detected: db_query_duration_seconds, db_connections_active"
else
    echo -e "${YELLOW}⚠️  WARN${NC}: Database metrics not available (requires database connection)"
fi
echo ""

# Test 6: Check cache metrics (if Redis is available)
echo "🗄️  Test 6: Cache Monitoring"
echo "--------------------------"
if echo "$METRICS_RESPONSE" | grep -q "psychsync_cache_operations_total\|psychsync_cache_hits_total"; then
    echo -e "${GREEN}✅ PASS${NC}: Cache metrics are exposed"
    echo "   Metrics detected: cache_operations_total, cache_hits_total"
else
    echo -e "${YELLOW}⚠️  WARN${NC}: Cache metrics not available (requires Redis connection)"
fi
echo ""

# Test 7: Health check endpoint
echo "💚 Test 7: Health Check Endpoint"
echo "--------------------------------"
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health 2>&1)

if echo "$HEALTH_RESPONSE" | grep -q "healthy\|status"; then
    echo -e "${GREEN}✅ PASS${NC}: Health check endpoint is responding"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}❌ FAIL${NC}: Health check endpoint not responding"
fi
echo ""

# Summary
echo "===================================="
echo "📋 Summary"
echo "===================================="
echo ""
echo "Monitoring endpoints available at:"
echo "  • Prometheus metrics:  http://localhost:8000/metrics"
echo "  • Health check:        http://localhost:8000/health"
echo "  • API docs:            http://localhost:8000/docs"
echo ""
echo "Environment variables to configure:"
echo "  • TRACING_ENABLED=true                (Enable distributed tracing)"
echo "  • JAEGER_ENDPOINT=http://localhost:4318   (Jaeger collector endpoint)"
echo "  • SLOW_QUERY_THRESHOLD=1.0            (Slow query threshold in seconds)"
echo ""
echo "Next steps:"
echo "  1. Deploy Prometheus: docker-compose -f monitoring/prometheus/docker-compose.yml up -d"
echo "  2. Deploy Grafana:   docker-compose up -d grafana"
echo "  3. Import dashboards to Grafana"
echo ""
echo "For detailed setup, see: monitoring/MONITORING_BLIND_SPOTS_REPORT.md"
