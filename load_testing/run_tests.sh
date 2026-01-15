#!/bin/bash

# PsychSync Load Testing Execution Script
# Provides easy execution of load tests with various configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOAD_TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="$LOAD_TEST_DIR/reports"
LOGS_DIR="$LOAD_TEST_DIR/logs"

# Default values
USERS=1000
SPAWN_RATE=50
RUN_TIME="10m"
HOST="${API_BASE_URL:-http://localhost:8000}"
SCENARIO="mixed"
TOOL="locust"

# Create directories
mkdir -p "$REPORTS_DIR"
mkdir -p "$LOGS_DIR"

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}      PsychSync Load Testing Suite${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Function to print usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -u, --users NUMBER          Number of concurrent users (default: 1000)"
    echo "  -s, --spawn-rate NUMBER     Users spawned per second (default: 50)"
    echo "  -t, --time DURATION        Test duration (default: 10m)"
    echo "  -H, --host URL             API base URL (default: http://localhost:8000)"
    echo "  -c, --scenario SCENARIO    Test scenario: auth|assessment|dashboard|mixed (default: mixed)"
    echo "  -T, --tool TOOL           Testing tool: locust|k6 (default: locust)"
    echo "  -m, --monitor             Start monitoring stack (Prometheus/Grafana)"
    echo "  -g, --generate-data       Generate test data before running tests"
    echo "  -d, --data-size SIZE      Data size: small|medium|large (default: medium)"
    echo "  -h, --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -u 100 -t 5m -c auth                    # Small auth test"
    echo "  $0 -u 5000 -s 100 -t 30m -c mixed          # Large mixed workload"
    echo "  $0 -T k6 -u 1000 -c assessment             # Use k6 for assessment test"
    echo "  $0 -m -g                                   # Start monitoring and generate data"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -s|--spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -t|--time)
            RUN_TIME="$2"
            shift 2
            ;;
        -H|--host)
            HOST="$2"
            shift 2
            ;;
        -c|--scenario)
            SCENARIO="$2"
            shift 2
            ;;
        -T|--tool)
            TOOL="$2"
            shift 2
            ;;
        -m|--monitor)
            START_MONITORING=true
            shift
            ;;
        -g|--generate-data)
            GENERATE_DATA=true
            shift
            ;;
        -d|--data-size)
            DATA_SIZE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Print configuration
echo -e "${GREEN}Configuration:${NC}"
echo "  Users:        $USERS"
echo "  Spawn Rate:   $SPAWN_RATE users/sec"
echo "  Run Time:     $RUN_TIME"
echo "  Host:         $HOST"
echo "  Scenario:     $SCENARIO"
echo "  Tool:         $TOOL"
echo ""

# Function to check if services are running
check_services() {
    echo -e "${YELLOW}Checking if services are running...${NC}"

    # Check if API is accessible
    if curl -s -f "$HOST/health" > /dev/null 2>&1 || curl -s -f "$HOST/docs" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is accessible at $HOST${NC}"
    else
        echo -e "${RED}✗ API is not accessible at $HOST${NC}"
        echo -e "${YELLOW}Please start the API server first${NC}"
        exit 1
    fi

    # Check if database is accessible (optional)
    if command -v psql &> /dev/null; then
        if psql "$TEST_DATABASE_URL" -c "SELECT 1" &> /dev/null; then
            echo -e "${GREEN}✓ Database is accessible${NC}"
        else
            echo -e "${YELLOW}⚠ Database may not be accessible${NC}"
        fi
    fi

    # Check if Redis is accessible (optional)
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            echo -e "${GREEN}✓ Redis is accessible${NC}"
        else
            echo -e "${YELLOW}⚠ Redis may not be accessible${NC}"
        fi
    fi

    echo ""
}

# Function to start monitoring
start_monitoring() {
    echo -e "${YELLOW}Starting monitoring stack...${NC}"

    cd "$LOAD_TEST_DIR/monitoring"

    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}✗ docker-compose not found${NC}"
        echo "Please install Docker and docker-compose"
        return 1
    fi

    # Start monitoring services
    docker-compose up -d prometheus grafana

    echo -e "${GREEN}✓ Monitoring started${NC}"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana:    http://localhost:3001 (admin/loadtest123)"
    echo ""

    sleep 3
}

# Function to generate test data
generate_test_data() {
    echo -e "${YELLOW}Generating test data...${NC}"

    # Determine data size
    case "${DATA_SIZE:-medium}" in
        small)
            USERS_COUNT=1000
            TEAMS_COUNT=50
            ASSESSMENTS_COUNT=10
            ;;
        medium)
            USERS_COUNT=10000
            TEAMS_COUNT=500
            ASSESSMENTS_COUNT=100
            ;;
        large)
            USERS_COUNT=100000
            TEAMS_COUNT=5000
            ASSESSMENTS_COUNT=1000
            ;;
        *)
            echo -e "${RED}Invalid data size: $DATA_SIZE${NC}"
            return 1
            ;;
    esac

    echo "  Users:       $USERS_COUNT"
    echo "  Teams:       $TEAMS_COUNT"
    echo "  Assessments: $ASSESSMENTS_COUNT"

    python3 "$LOAD_TEST_DIR/test_data/generate_test_data.py" \
        --users "$USERS_COUNT" \
        --teams "$TEAMS_COUNT" \
        --assessments "$ASSESSMENTS_COUNT"

    echo ""
}

# Function to run Locust tests
run_locust() {
    local scenario_file="$LOAD_TEST_DIR/locust/${SCENARIO}_test.py"

    if [ ! -f "$scenario_file" ]; then
        echo -e "${RED}✗ Scenario file not found: $scenario_file${NC}"
        return 1
    fi

    echo -e "${YELLOW}Running Locust test...${NC}"
    echo "  File:   $scenario_file"
    echo "  Output: $REPORTS_DIR/locust_${SCENARIO}_${USERS}users_$(date +%Y%m%d_%H%M%S).html"
    echo ""

    locust -f "$scenario_file" \
        --host="$HOST" \
        --users "$USERS" \
        --spawn-rate "$SPAWN_RATE" \
        --run-time "$RUN_TIME" \
        --html "$REPORTS_DIR/locust_${SCENARIO}_${USERS}users_$(date +%Y%m%d_%H%M%S).html" \
        --logfile "$LOGS_DIR/locust_${SCENARIO}_$(date +%Y%m%d_%H%M%S).log"
}

# Function to run k6 tests
run_k6() {
    local scenario_file="$LOAD_TEST_DIR/k6/${SCENARIO}_test.js"

    if [ ! -f "$scenario_file" ]; then
        echo -e "${RED}✗ Scenario file not found: $scenario_file${NC}"
        return 1
    fi

    echo -e "${YELLOW}Running k6 test...${NC}"
    echo "  File:   $scenario_file"
    echo "  Output: $REPORTS_DIR/k6_${SCENARIO}_${USERS}users_$(date +%Y%m%d_%H%M%S).json"
    echo ""

    # Set environment variables
    export API_BASE_URL="$HOST"

    k6 run \
        --vus "$USERS" \
        --duration "$RUN_TIME" \
        --out json="$REPORTS_DIR/k6_${SCENARIO}_${USERS}users_$(date +%Y%m%d_%H%M%S).json" \
        "$scenario_file"
}

# Main execution
main() {
    # Check services
    check_services

    # Start monitoring if requested
    if [ "$START_MONITORING" = true ]; then
        start_monitoring
    fi

    # Generate test data if requested
    if [ "$GENERATE_DATA" = true ]; then
        generate_test_data
    fi

    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}Starting Load Test${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""

    # Run the appropriate tool
    case "$TOOL" in
        locust)
            run_locust
            ;;
        k6)
            run_k6
            ;;
        *)
            echo -e "${RED}Unknown tool: $TOOL${NC}"
            exit 1
            ;;
    esac)

    echo ""
    echo -e "${GREEN}================================================================${NC}"
    echo -e "${GREEN}Load Test Completed${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo ""
    echo "Reports saved to: $REPORTS_DIR"
    echo "Logs saved to:    $LOGS_DIR"

    if [ "$START_MONITORING" = true ]; then
        echo ""
        echo "Monitoring still running:"
        echo "  Prometheus: http://localhost:9090"
        echo "  Grafana:    http://localhost:3001"
        echo ""
        echo "To stop monitoring:"
        echo "  cd $LOAD_TEST_DIR/monitoring && docker-compose down"
    fi
}

# Run main function
main
