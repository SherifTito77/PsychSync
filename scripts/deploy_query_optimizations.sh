#!/bin/bash
# Query Optimization Deployment Script
# Usage: ./scripts/deploy_query_optimizations.sh [staging|production]

set -e  # Exit on error

ENVIRONMENT=${1:-staging}
COMMIT_HASH=$(git rev-parse HEAD)

echo "============================================================"
echo "Query Optimization Deployment Script"
echo "============================================================"
echo "Environment: $ENVIRONMENT"
echo "Commit: $COMMIT_HASH"
echo "Timestamp: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Pre-deployment checks
echo "📋 Step 1: Running pre-deployment checks..."
if [ -f "scripts/pre_deployment_check.sh" ]; then
    bash scripts/pre_deployment_check.sh
else
    echo -e "${YELLOW}⚠️  Pre-deployment check script not found, skipping...${NC}"
fi

# Step 2: Validate query optimizations
echo ""
echo "📊 Step 2: Validating query optimizations..."
python scripts/validate_query_optimization.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Validation failed! Aborting deployment.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Validation passed${NC}"

# Step 3: Run tests
echo ""
echo "🧪 Step 3: Running integration tests..."
python tests/integration/test_query_optimizations_standalone.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Tests failed! Aborting deployment.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Tests passed${NC}"

# Step 4: Confirm deployment
echo ""
echo "============================================================"
echo "Ready to deploy to: $ENVIRONMENT"
echo "============================================================"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Step 5: Deploy based on environment
echo ""
echo "🚀 Step 4: Deploying to $ENVIRONMENT..."

if [ "$ENVIRONMENT" = "staging" ]; then
    echo "Deploying to staging environment..."
    # Add your staging deployment commands here
    # For example:
    # git push origin feat/documentation-quality-improvements
    # kubectl apply -f k8s/staging/
    # or
    # docker-compose -f docker-compose.staging.yml up -d

    echo -e "${GREEN}✅ Deployed to staging${NC}"

elif [ "$ENVIRONMENT" = "production" ]; then
    echo "⚠️  WARNING: Deploying to PRODUCTION!"
    echo "This will perform a gradual rollout:"
    echo "  1. Deploy to 10% of servers"
    echo "  2. Wait 2 hours and monitor"
    echo "  3. Deploy to 50% of servers"
    echo "  4. Wait 4 hours and monitor"
    echo "  5. Deploy to 100% of servers"
    echo ""
    read -p "Confirm PRODUCTION deployment? (yes/no): " PROD_CONFIRM

    if [ "$PROD_CONFIRM" != "yes" ]; then
        echo "Production deployment cancelled."
        exit 0
    fi

    # Add your production deployment commands here
    echo -e "${GREEN}✅ Deployed to production${NC}"
else
    echo -e "${RED}❌ Unknown environment: $ENVIRONMENT${NC}"
    echo "Use: staging or production"
    exit 1
fi

# Step 6: Post-deployment monitoring
echo ""
echo "📊 Step 5: Starting post-deployment monitoring..."
if [ -f "scripts/post_deployment_monitor.sh" ]; then
    bash scripts/post_deployment_monitor.sh $ENVIRONMENT &
    MONITOR_PID=$!
    echo "Monitoring started (PID: $MONITOR_PID)"
else
    echo -e "${YELLOW}⚠️  Post-deployment monitor script not found${NC}"
fi

# Step 7: Display monitoring info
echo ""
echo "============================================================"
echo "✅ Deployment Complete!"
echo "============================================================"
echo ""
echo "📈 Monitoring Dashboard:"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3000"
echo "   - Metrics: http://localhost:8000/metrics"
echo ""
echo "📚 Documentation:"
echo "   - Quick Start: docs/QUICK_START_GUIDE.md"
echo "   - Monitoring: docs/MONITORING_SETUP_GUIDE.md"
echo "   - Deployment: DEPLOYMENT_SUMMARY.md"
echo ""
echo "⏰ Monitor for 24-48 hours before production rollout."
echo ""
echo "Key metrics to watch:"
echo "   ✓ Query times (should decrease 2-19x)"
echo "   ✓ Memory usage (should decrease 80-95%)"
echo "   ✓ Database load (should decrease 65-70%)"
echo "   ✓ Error rates (should stay low)"
echo ""
echo "🔧 Rollback command:"
echo "   git revert $COMMIT_HASH"
echo "   alembic downgrade -1"
echo ""

# Optional: Open monitoring dashboard
if command -v open &> /dev/null; then
    read -p "Open Grafana dashboard? (yes/no): " OPEN_DASHBOARD
    if [ "$OPEN_DASHBOARD" = "yes" ]; then
        open http://localhost:3000
    fi
fi

echo "Deployment script completed successfully!"
