#!/bin/bash

# Rate Limiting Load Test Runner
# This script runs load tests to validate API rate limiting and throttling

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║        API Rate Limiting & Throttling Load Test Suite         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if server is running
check_server() {
    echo "🔍 Checking if backend server is running..."
    if curl -s http://localhost:8000/api/v1/health > /dev/null; then
        echo -e "${GREEN}✓${NC} Server is running"
        return 0
    else
        echo -e "${RED}✗${NC} Server is not running"
        echo ""
        echo "Please start the backend server first:"
        echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
        exit 1
    fi
}

# Check if Redis is running
check_redis() {
    echo "🔍 Checking if Redis is running..."
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Redis is running"
        return 0
    else
        echo -e "${RED}✗${NC} Redis is not running"
        echo ""
        echo "Please start Redis first:"
        echo "  redis-server"
        echo "  or"
        echo "  docker-compose up -d redis"
        exit 1
    fi
}

# Run pytest-based load tests
run_pytest_tests() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "Running Pytest-based Load Tests"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Install test dependencies if needed
    if ! python -c "import httpx" 2>/dev/null; then
        echo "Installing test dependencies..."
        pip install httpx pytest-asyncio
    fi

    # Run the load tests
    python -m pytest tests/load/test_rate_limiting_load.py \
        -v \
        -m load \
        --tb=short \
        --disable-warnings

    echo ""
    echo -e "${GREEN}✓${NC} Pytest tests completed"
}

# Run Locust load tests
run_locust_tests() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "Running Locust Load Tests"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Check if locust is installed
    if ! command -v locust &> /dev/null; then
        echo "Installing Locust..."
        pip install locust
    fi

    echo "Starting Locust web interface..."
    echo "  URL: http://localhost:8089"
    echo "  Host: http://localhost:8000"
    echo ""
    echo "Press Ctrl+C to stop Locust"
    echo ""

    locust -f tests/load/locustfile.py \
        --host=http://localhost:8000 \
        --users=100 \
        --spawn-rate=10 \
        --run-time=2m \
        --headless \
        --html=reports/locust_rate_limit_report.html \
        --csv=reports/locust_rate_limit_stats
}

# Run quick manual test
run_quick_test() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "Quick Rate Limit Validation Test"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    echo "Sending 60 requests to health endpoint (limit: 50/min for anonymous)..."
    echo ""

    success=0
    throttled=0

    for i in {1..60}; do
        response=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/v1/health)
        http_code=$(echo "$response" | tail -n1)

        if [ "$http_code" = "429" ]; then
            ((throttled++))
            echo -e "  Request $i: ${YELLOW}THROTTLED${NC} (429)"
        else
            ((success++))
            echo -e "  Request $i: ${GREEN}OK${NC} ($http_code)"
        fi

        # Small delay to avoid overwhelming
        sleep 0.05
    done

    echo ""
    echo "Results:"
    echo "  Successful: $success"
    echo "  Throttled:  $throttled"
    echo ""

    if [ $throttled -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Rate limiting is working! ($throttled requests were throttled)"
    else
        echo -e "${RED}✗${NC} Rate limiting may not be working correctly"
    fi
}

# Create reports directory
mkdir -p reports

# Parse command line arguments
case "${1:-all}" in
    all)
        check_server
        check_redis
        run_pytest_tests
        echo ""
        read -p "Run Locust tests? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            run_locust_tests
        fi
        ;;
    pytest)
        check_server
        check_redis
        run_pytest_tests
        ;;
    locust)
        check_server
        check_redis
        run_locust_tests
        ;;
    quick)
        check_server
        run_quick_test
        ;;
    check)
        check_server
        check_redis
        echo ""
        echo -e "${GREEN}✓${NC} All services are running"
        ;;
    *)
        echo "Usage: $0 [all|pytest|locust|quick|check]"
        echo ""
        echo "Commands:"
        echo "  all    - Run pytest and optionally locust tests (default)"
        echo "  pytest - Run pytest-based load tests only"
        echo "  locust - Run Locust load tests with web UI"
        echo "  quick  - Run a quick validation test"
        echo "  check  - Check if required services are running"
        exit 1
        ;;
esac

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ Load testing completed!${NC}"
echo "═══════════════════════════════════════════════════════════════"
