#!/bin/bash
###############################################################################
# Monitoring Stack Deployment Script
# Deploys Prometheus, Grafana, and Redis for PsychSync monitoring
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/monitoring-stack.yml"
PROMETHEUS_CONFIG="$SCRIPT_DIR/prometheus/prometheus.yml"
ALERTS_DIR="$SCRIPT_DIR/prometheus/alerts"

echo "🚀 PsychSync Monitoring Stack Deployment"
echo "========================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo "Please install Docker Desktop first:"
    echo "  - macOS: https://docs.docker.com/desktop/install/mac-install/"
    echo "  - Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null && ! docker-compose version &> /dev/null; then
    echo "❌ Docker Compose is not available!"
    echo "Please install Docker Compose plugin:"
    echo "  - macOS: Included with Docker Desktop"
    echo "  - Linux: https://docs.docker.com/compose/install/"
    exit 1
fi

# Determine which docker compose command to use
DOCKER_COMPOSE=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose -f $COMPOSE_FILE"
    echo "✅ Using: docker compose"
else
    DOCKER_COMPOSE="docker-compose -f $COMPOSE_FILE"
    echo "✅ Using: docker-compose"
fi

echo ""
echo "📋 Prerequisites Check:"
echo "----------------------"

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Compose file not found: $COMPOSE_FILE"
    exit 1
fi
echo "✅ Compose file found"

# Check Prometheus config
if [ ! -f "$PROMETHEUS_CONFIG" ]; then
    echo "❌ Prometheus config not found: $PROMETHEUS_CONFIG"
    exit 1
fi
echo "✅ Prometheus configuration found"

# Check Grafana dashboards
if [ ! -d "$SCRIPT_DIR/grafana/dashboards" ]; then
    echo "❌ Grafana dashboards directory not found"
    exit 1
fi
DASHBOARD_COUNT=$(ls -1 "$SCRIPT_DIR/grafana/dashboards/"*.json 2>/dev/null | wc -l)
echo "✅ Found $DASHBOARD_COUNT Grafana dashboards"

echo ""
echo "🔧 Configuration:"
echo "-----------------"
echo "Compose File: $COMPOSE_FILE"
echo "Prometheus Config: $PROMETHEUS_CONFIG"
echo "Alerts Directory: $ALERTS_DIR"
echo ""

# Ask user what they want to do
echo "Available Actions:"
echo "  1. Start monitoring stack"
echo "  2. Stop monitoring stack"
echo "  3. Restart monitoring stack"
echo "  4. View logs"
echo "  5. Check status"
echo ""
read -p "Select action (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting monitoring stack..."
        $DOCKER_COMPOSE up -d

        echo ""
        echo "✅ Services started!"
        echo ""
        echo "📊 Access Points:"
        echo "  Grafana:     http://localhost:3000 (admin/admin)"
        echo "  Prometheus:  http://localhost:9090"
        echo "  Redis:       localhost:6379"
        echo ""
        echo "📚 Next Steps:"
        echo "  1. Open Grafana at http://localhost:3000"
        echo "  2. Login with admin/admin"
        echo "  3. Navigate to Dashboards"
        echo "  4. Import dashboards from dashboards/ directory"
        echo ""
        ;;

    2)
        echo ""
        echo "🛑 Stopping monitoring stack..."
        $DOCKER_COMPOSE down
        echo ""
        echo "✅ Services stopped!"
        ;;

    3)
        echo ""
        echo "🔄 Restarting monitoring stack..."
        $DOCKER_COMPOSE restart
        echo ""
        echo "✅ Services restarted!"
        ;;

    4)
        echo ""
        echo "📋 Showing logs (Ctrl+C to exit)..."
        $DOCKER_COMPOSE logs -f
        ;;

    5)
        echo ""
        echo "📊 Service Status:"
        $DOCKER_COMPOSE ps
        echo ""

        echo "🌐 Health Check:"
        echo -n "Grafana:    "
        if curl -s http://localhost:3000/api/health > /dev/null; then
            echo "✅ Running"
        else
            echo "❌ Not accessible"
        fi

        echo -n "Prometheus: "
        if curl -s http://localhost:9090/-/healthy > /dev/null; then
            echo "✅ Running"
        else
            echo "❌ Not accessible"
        fi

        echo -n "Redis:      "
        if redis-cli ping > /dev/null 2>&1; then
            echo "✅ Running"
        else
            echo "❌ Not accessible"
        fi
        echo ""
        ;;

    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Done!"
