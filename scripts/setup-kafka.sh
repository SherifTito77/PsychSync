#!/bin/bash
# Kafka Quick Start Script for PsychSync
# This script sets up Kafka, creates topics, and demonstrates event streaming

set -e

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║           PsychSync Kafka Event Streaming Setup                      ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================
# Step 1: Start Kafka
# ============================================
echo -e "${BLUE}Step 1: Starting Kafka infrastructure...${NC}"
echo ""

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif command -v docker &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo -e "${RED}Error: Neither docker-compose nor docker compose found${NC}"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Start Kafka
$DOCKER_COMPOSE -f docker-compose.kafka.yml up -d

echo ""
echo -e "${GREEN}✅ Kafka started successfully!${NC}"
echo ""
echo "Services:"
echo "  - Kafka Broker: localhost:9092 (internal), localhost:29092 (external)"
echo "  - Zookeeper: localhost:2181"
echo "  - Kafka UI: http://localhost:8080"
echo "  - Redis: localhost:6379"
echo ""

# Wait for Kafka to be ready
echo -e "${YELLOW}Waiting for Kafka to be ready...${NC}"
sleep 10

# ============================================
# Step 2: Create Topics
# ============================================
echo ""
echo -e "${BLUE}Step 2: Creating Kafka topics...${NC}"
echo ""

KAFKA_CONTAINER="psychsync-kafka"
TOPICS=(
    "assessment-events"
    "user-events"
    "team-events"
    "organization-events"
    "analytics-events"
    "billing-events"
    "notification-events"
    "system-events"
)

for topic in "${TOPICS[@]}"; do
    echo -n "  Creating topic: $topic ... "
    docker exec -it $KAFKA_CONTAINER kafka-topics --create \
        --bootstrap-server localhost:9092 \
        --topic $topic \
        --partitions 3 \
        --replication-factor 1 2>&1 | grep -v "WARNING" || true
    echo -e "${GREEN}✓${NC}"
done

echo ""
echo -e "${GREEN}✅ All topics created successfully!${NC}"
echo ""

# ============================================
# Step 3: Verify Setup
# ============================================
echo -e "${BLUE}Step 3: Verifying Kafka setup...${NC}"
echo ""

echo "Listing topics:"
docker exec -it $KAFKA_CONTAINER kafka-topics --list --bootstrap-server localhost:9092

echo ""
echo -e "${GREEN}✅ Kafka setup complete!${NC}"
echo ""

# ============================================
# Step 4: Next Steps
# ============================================
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                        Next Steps                                     ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "1. Test Kafka Producer/Consumer:"
echo ""
echo "   # Terminal 1: Start consumer"
echo "   python -m app.events.example_consumer"
echo ""
echo "   # Terminal 2: Publish event"
echo "   python -m app.events.example_producer"
echo ""
echo "2. View Kafka UI:"
echo "   Open http://localhost:8080 in your browser"
echo ""
echo "3. Stop Kafka:"
echo "   $DOCKER_COMPOSE -f docker-compose.kafka.yml down"
echo ""
echo "4. View logs:"
echo "   $DOCKER_COMPOSE -f docker-compose.kafka.yml logs -f kafka"
echo ""
echo "✅ Setup complete! Kafka is ready for event streaming."
echo ""
