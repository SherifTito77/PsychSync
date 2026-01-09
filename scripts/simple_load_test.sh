#!/bin/bash
# Simple Load Test Script for Async Cache Endpoints
# Uses curl to test endpoint performance under load

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║          ASYNC CACHE LOAD TEST - Simple Bash Version                 ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Testing endpoint: http://localhost:8000/api/v1/health"
echo "Requests: 100"
echo "Concurrency: 10 (background processes)"
echo ""
echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Variables
URL="http://localhost:8000/api/v1/health"
TOTAL_REQUESTS=100
CONCURRENT=10
RESULTS_FILE="/tmp/load_test_results.txt"

# Clear results file
> "$RESULTS_FILE"

# Function to make requests
make_requests() {
    local count=$1
    local start_time=$(date +%s.%N)

    for i in $(seq 1 $count); do
        local req_start=$(date +%s.%N)
        response=$(curl -s -w "\n%{http_code}\n%{time_total}" "$URL" 2>&1)
        local req_end=$(date +%s.%N)

        # Parse response
        local http_code=$(echo "$response" | tail -n 2 | head -n 1)
        local time_total=$(echo "$response" | tail -n 1)

        # Calculate latency
        local latency=$(echo "$req_end - $req_start" | bc)

        # Save result
        echo "$latency|$http_code" >> "$RESULTS_FILE"
    done

    local end_time=$(date +%s.%N)
    local total_time=$(echo "$end_time - $start_time" | bc)
    echo "Batch completed in ${total_time}s"
}

# Run concurrent batches
echo "🚀 Starting load test..."
echo ""

# Calculate requests per batch
REQUESTS_PER_BATCH=$((TOTAL_REQUESTS / CONCURRENT))

# Launch background processes
for i in $(seq 1 $CONCURRENT); do
    make_requests $REQUESTS_PER_BATCH &
    PIDS[$i]=$!
done

# Wait for all processes
for pid in ${PIDS[*]}; do
    wait $pid
done

echo ""
echo "✅ All requests completed!"
echo ""
echo "Processing results..."
echo ""

# Parse results
SUCCESS_COUNT=0
ERROR_COUNT=0
TOTAL_LATENCY=0
COUNT=0

while IFS='|' read -r latency http_code; do
    COUNT=$((COUNT + 1))
    TOTAL_LATENCY=$(echo "$TOTAL_LATENCY + $latency" | bc)

    if [ "$http_code" = "200" ] || [ "$http_code" = "401" ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
done < "$RESULTS_FILE"

# Calculate statistics
AVG_LATENCY=$(echo "scale=3; $TOTAL_LATENCY / $COUNT" | bc)
SUCCESS_RATE=$(echo "scale=2; $SUCCESS_COUNT * 100 / $COUNT" | bc)

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                          LOAD TEST RESULTS                          ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Statistics:"
echo "   Total Requests: $COUNT"
echo "   Successful: $SUCCESS_COUNT ($SUCCESS_RATE%)"
echo "   Errors: $ERROR_COUNT"
echo ""
echo "⏱️  Latency:"
echo "   Average: ${AVG_LATENCY}s"
echo ""
echo "🎯 Performance Targets:"
echo "   Target Success Rate: >95%"
if [ "$(echo "$SUCCESS_RATE > 95" | bc)" -eq 1 ]; then
    echo "   ✅ ACHIEVED: ${SUCCESS_RATE}%"
else
    echo "   ⚠️  NOT ACHIEVED: ${SUCCESS_RATE}%"
fi

echo "   Target Average Latency: <1s"
if [ "$(echo "$AVG_LATENCY < 1.0" | bc)" -eq 1 ]; then
    echo "   ✅ ACHIEVED: ${AVG_LATENCY}s"
else
    echo "   ⚠️  NOT ACHIEVED: ${AVG_LATENCY}s"
fi

echo ""
echo "📈 Sample latencies (first 10):"
head -n 10 "$RESULTS_FILE" | while IFS='|' read -r latency http_code; do
    latency_ms=$(echo "$latency * 1000" | bc)
    echo "   ${latency_ms}ms (HTTP $http_code)"
done

echo ""
echo "✅ Load test complete!"
echo ""
echo "Cache Performance:"
echo "   Check Redis hit rate:"
echo "   redis-cli INFO stats | grep -E '(keyspace_hits|keyspace_misses)'"
echo ""
