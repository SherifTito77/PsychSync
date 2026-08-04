#!/bin/bash

# Distributed Rate Limiting Test Script
# Tests Redis-backed rate limiting across multiple app instances

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     Distributed Rate Limiting Test - Setup & Run              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker and Docker Compose are installed"
echo ""

# Step 1: Stop any existing containers
echo "Step 1: Stopping any existing test containers..."
docker-compose -f docker-compose.distributed-test.yml down 2>/dev/null || true
echo -e "${GREEN}✓${NC} Containers stopped"
echo ""

# Step 2: Build and start the distributed test environment
echo "Step 2: Starting distributed test environment..."
echo "  - 3 backend instances (ports 8001, 8002, 8003)"
echo "  - 1 Redis instance (port 6379)"
echo "  - 1 Nginx load balancer (port 8080)"
echo "  - 1 PostgreSQL database (port 5433)"
echo ""

docker-compose -f docker-compose.distributed-test.yml up -d --build

echo ""
echo "Waiting for services to be healthy..."
sleep 10

# Check if all services are running
echo "Checking service health..."
if docker-compose -f docker-compose.distributed-test.yml ps | grep -q "Up"; then
    echo -e "${GREEN}✓${NC} Services are running"
else
    echo -e "${RED}✗${NC} Some services failed to start"
    docker-compose -f docker-compose.distributed-test.yml logs
    exit 1
fi

echo ""
echo "Waiting for backend instances to fully initialize..."
sleep 15

# Step 3: Verify each backend is accessible
echo ""
echo "Step 3: Verifying backend instances..."
for port in 8001 8002 8003; do
    if curl -s -f "http://localhost:$port/api/v1/health" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Backend on port $port is healthy"
    else
        echo -e "  ${YELLOW}⚠${NC}  Backend on port $port is not ready yet"
        sleep 5
    fi
done

# Step 4: Verify load balancer is accessible
echo ""
if curl -s -f "http://localhost:8080/api/v1/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Load balancer is accessible"
else
    echo -e "${RED}✗${NC} Load balancer is not accessible"
    echo "Checking logs..."
    docker-compose -f docker-compose.distributed-test.yml logs nginx-lb
    exit 1
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              Test Environment Ready!                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Services:"
echo "  - Load Balancer:  http://localhost:8080"
echo "  - Backend 1:      http://localhost:8001"
echo "  - Backend 2:      http://localhost:8002"
echo "  - Backend 3:      http://localhost:8003"
echo "  - Redis:          localhost:6379"
echo ""
echo "Running distributed rate limiting test..."
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Step 5: Run the distributed test
python tests/load/test_rate_limiting_load.py --distributed

TEST_EXIT_CODE=$?

echo ""
echo "═══════════════════════════════════════════════════════════════"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ DISTRIBUTED RATE LIMITING TEST PASSED${NC}"
else
    echo -e "${RED}✗ DISTRIBUTED RATE LIMITING TEST FAILED${NC}"
fi

echo ""
echo "Test logs:"
docker-compose -f docker-compose.distributed-test.yml logs --tail=50

echo ""
echo "To view logs manually:"
echo "  docker-compose -f docker-compose.distributed-test.yml logs -f [service_name]"
echo ""
echo "To stop the test environment:"
echo "  docker-compose -f docker-compose.distributed-test.yml down"
echo ""

exit $TEST_EXIT_CODE
