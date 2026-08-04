#!/bin/bash
###############################################################################
# Post-Deployment Monitoring Script
# Monitors key metrics after deployment to ensure stability
###############################################################################

set -e

# Configuration
LOG_FILE="/var/log/psychsync/app.log"
ERROR_PATTERN="ERROR|CRITICAL|Exception"
AUTH_PATTERN="security_event|AUTH|authentication"
RATE_LIMIT_PATTERN="rate limit|429"
MONITORING_DURATION=3600  # Monitor for 1 hour (in seconds)
CHECK_INTERVAL=60  # Check every 60 seconds

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "═══════════════════════════════════════════════════════════════"
echo "     POST-DEPLOYMENT MONITORING - PsychSync Platform"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Monitoring duration: $((MONITORING_DURATION / 60)) minutes"
echo "Check interval: $CHECK_INTERVAL seconds"
echo "Log file: $LOG_FILE"
echo ""

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo -e "${RED}Error: Log file not found: $LOG_FILE${NC}"
    echo "Please update the LOG_FILE variable in this script"
    exit 1
fi

# Get baseline metrics before monitoring
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Establishing baseline metrics..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

baseline_errors=$(grep -cE "$ERROR_PATTERN" "$LOG_FILE" 2>/dev/null || echo "0")
baseline_auth=$(grep -cE "$AUTH_PATTERN" "$LOG_FILE" 2>/dev/null || echo "0")
baseline_rate_limit=$(grep -cE "$RATE_LIMIT_PATTERN" "$LOG_FILE" 2>/dev/null || echo "0")

echo "Baseline errors: $baseline_errors"
echo "Baseline auth events: $baseline_auth"
echo "Baseline rate limit hits: $baseline_rate_limit"
echo ""

# Arrays to store metrics over time
declare -a error_counts
declare -a auth_counts
declare -a rate_limit_counts
iteration=0

# Monitoring loop
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Starting monitoring loop..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop monitoring early"
echo ""

start_time=$(date +%s)
end_time=$((start_time + MONITORING_DURATION))

while [ $(date +%s) -lt $end_time ]; do
    iteration=$((iteration + 1))
    current_time=$(date '+%Y-%m-%d %H:%M:%S')

    # Get current log file size
    current_size=$(du -h "$LOG_FILE" | awk '{print $1}')

    # Count occurrences since last check
    new_errors=$(grep -cE "$ERROR_PATTERN" "$LOG_FILE" 2>/dev/null || echo "0")
    new_auth=$(grep -cE "$AUTH_PATTERN" "$LOG_FILE" 2>/dev/null || echo "0")
    new_rate_limit=$(grep -cE "$RATE_LIMIT_PATTERN" "$LOG_FILE" 2>/dev/null || echo "0")

    # Calculate deltas
    error_delta=$((new_errors - baseline_errors))
    auth_delta=$((new_auth - baseline_auth))
    rate_limit_delta=$((new_rate_limit - baseline_rate_limit))

    # Store for analysis
    error_counts+=($error_delta)
    auth_counts+=($auth_delta)
    rate_limit_counts+=($rate_limit_delta)

    # Display current status
    echo -e "${BLUE}[$current_time]${NC} Check #$iteration | Log size: $current_size"
    echo "  Errors (new): $error_delta | Auth events: $auth_delta | Rate limits: $rate_limit_delta"

    # Alert on concerning patterns
    if [ $error_delta -gt 10 ]; then
        echo -e "  ${RED}⚠️  High error rate detected!${NC}"
        # Show last 5 errors
        echo "  Recent errors:"
        grep -E "$ERROR_PATTERN" "$LOG_FILE" | tail -5 | sed 's/^/    /'
    fi

    if [ $rate_limit_delta -gt 20 ]; then
        echo -e "  ${YELLOW}⚠️  High rate limit activity (possible attack?)${NC}"
    fi

    # Update baseline for next iteration
    baseline_errors=$new_errors
    baseline_auth=$new_auth
    baseline_rate_limit=$new_rate_limit

    # Wait for next check
    echo ""
    sleep $CHECK_INTERVAL
done

# Generate summary report
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "                MONITORING SUMMARY REPORT"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Calculate statistics
total_errors=0
total_auth=0
total_rate_limits=0

for count in "${error_counts[@]}"; do
    total_errors=$((total_errors + count))
done

for count in "${auth_counts[@]}"; do
    total_auth=$((total_auth + count))
done

for count in "${rate_limit_counts[@]}"; do
    total_rate_limits=$((total_rate_limits + count))
done

avg_errors=$((total_errors / iteration))
avg_auth=$((total_auth / iteration))
avg_rate_limits=$((total_rate_limits / iteration))

echo "Monitoring Duration: $((MONITORING_DURATION / 60)) minutes"
echo "Total Checks: $iteration"
echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "ERROR METRICS"
echo "─────────────────────────────────────────────────────────────────"
echo "Total new errors: $total_errors"
echo "Average per check: $avg_errors"
echo ""

# Check if error rate is concerning
if [ $avg_errors -gt 5 ]; then
    echo -e "${RED}⚠️  WARNING: High average error rate${NC}"
    echo "   Review logs for patterns"
elif [ $avg_errors -gt 2 ]; then
    echo -e "${YELLOW}⚠️  NOTICE: Elevated error rate${NC}"
    echo "   Monitor closely"
else
    echo -e "${GREEN}✓ Error rate within normal range${NC}"
fi

echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "AUTHENTICATION METRICS"
echo "─────────────────────────────────────────────────────────────────"
echo "Total auth events: $total_auth"
echo "Average per check: $avg_auth"
echo ""

# Check auth trends
if [ $avg_auth -lt 1 ]; then
    echo -e "${YELLOW}⚠️  Low authentication activity${NC}"
    echo "   This may indicate auth issues"
else
    echo -e "${GREEN}✓ Normal authentication activity${NC}"
fi

echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "RATE LIMITING METRICS"
echo "─────────────────────────────────────────────────────────────────"
echo "Total rate limit hits: $total_rate_limits"
echo "Average per check: $avg_rate_limits"
echo ""

# Check for potential attacks
if [ $avg_rate_limits -gt 10 ]; then
    echo -e "${RED}⚠️  HIGH RATE LIMIT ACTIVITY${NC}"
    echo "   Possible brute force attack or scraping"
    echo "   Review IP addresses in logs"
elif [ $avg_rate_limits -gt 5 ]; then
    echo -e "${YELLOW}⚠️  Elevated rate limit activity${NC}"
    echo "   Monitor for attack patterns"
else
    echo -e "${GREEN}✓ Rate limiting within normal range${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"

# Final assessment
if [ $avg_errors -le 2 ] && [ $avg_auth -ge 1 ] && [ $avg_rate_limits -le 5 ]; then
    echo -e "${GREEN}✅ DEPLOYMENT STABLE - All metrics within normal range${NC}"
    exit 0
elif [ $avg_errors -gt 5 ]; then
    echo -e "${RED}⚠️  DEPLOYMENT UNSTABLE - High error rate detected${NC}"
    echo "   Recommended: Investigate errors immediately"
    exit 1
else
    echo -e "${YELLOW}⚠️  DEPLOYMENT CAUTION - Some metrics outside normal range${NC}"
    echo "   Recommended: Continue monitoring"
    exit 2
fi
