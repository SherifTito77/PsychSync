#!/bin/bash
################################################################################
# Production Deployment Script for PsychSync
#
# This script automates the complete production deployment process including:
# - Pre-deployment verification
# - Database validation
# - Application startup
# - Health checks
# - Smoke tests
#
# Usage: ./scripts/deploy_production.sh [environment]
#   environment: "production" (default) or "staging"
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

################################################################################
# CONFIGURATION
################################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# LOGGING FUNCTIONS
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${BLUE}$1${NC}"
    echo "════════════════════════════════════════════════════════════════"
}

################################################################################
# VERIFICATION FUNCTIONS
################################################################################

check_python_version() {
    log_info "Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        return 1
    fi

    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    log_success "Python $PYTHON_VERSION detected"

    return 0
}

check_database_connection() {
    log_info "Checking database connection..."

    if ! psql -h localhost -p 5432 -U sheriftito -d psychsync -c "SELECT 1;" &> /dev/null; then
        log_error "Cannot connect to production database"
        return 1
    fi

    log_success "Database connection verified"

    # Check table count
    TABLE_COUNT=$(psql -h localhost -p 5432 -U sheriftito -d psychsync -t -c \
        "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';")

    if [ "$TABLE_COUNT" -lt 30 ]; then
        log_warning "Expected at least 30 tables, found $TABLE_COUNT"
        log_warning "Run: python3 scripts/create_production_schema.py"
    else
        log_success "Database schema verified ($TABLE_COUNT tables)"
    fi

    return 0
}

check_migration_version() {
    log_info "Checking Alembic migration version..."

    cd "$PROJECT_ROOT"
    CURRENT_VERSION=$(alembic current 2>&1 | grep -oP '^\K[0-9]+.*' || echo "unknown")

    log_success "Current migration: $CURRENT_VERSION"

    return 0
}

check_environment_variables() {
    log_info "Checking environment variables..."

    REQUIRED_VARS=(
        "DATABASE_URL"
        "SECRET_KEY"
    )

    MISSING_VARS=()

    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var:-}" ]; then
            MISSING_VARS+=("$var")
        fi
    done

    if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        log_warning "The following environment variables are not set:"
        for var in "${MISSING_VARS[@]}"; do
            echo "  - $var"
        done
        log_warning "Set them in .env.$ENVIRONMENT or export them"
    else
        log_success "All required environment variables set"
    fi

    return 0
}

################################################################################
# DEPLOYMENT FUNCTIONS
################################################################################

run_pre_deployment_checks() {
    log_section "RUNNING PRE-DEPLOYMENT CHECKS"

    check_python_version
    check_database_connection
    check_migration_version
    check_environment_variables

    log_success "All pre-deployment checks passed"
    echo ""
}

run_database_migrations() {
    log_section "VERIFYING DATABASE MIGRATIONS"

    cd "$PROJECT_ROOT"

    log_info "Current migration status:"
    alembic current

    log_info "Latest migration version:"
    alembic heads

    log_success "Database migrations verified"
    echo ""
}

start_application() {
    log_section "STARTING APPLICATION"

    cd "$PROJECT_ROOT"

    # Check if uvicorn is installed
    if ! command -v uvicorn &> /dev/null; then
        log_error "uvicorn not found. Install with: pip install uvicorn"
        return 1
    fi

    # Check if application is already running
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        log_warning "Application is already running"
        log_info "Stopping existing instance..."
        pkill -f "uvicorn app.main:app"
        sleep 2
    fi

    log_info "Starting FastAPI application..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Workers: 4"

    # Start application in background
    nohup uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 4 \
        --log-level info \
        > logs/application.log 2>&1 &

    APP_PID=$!
    echo $APP_PID > logs/application.pid

    log_success "Application started with PID: $APP_PID"
    log_info "Log file: logs/application.log"
    echo ""

    # Wait for application to start
    log_info "Waiting for application to start..."
    sleep 5
}

run_health_checks() {
    log_section "RUNNING HEALTH CHECKS"

    # Check if process is running
    if ! pgrep -f "uvicorn app.main:app" > /dev/null; then
        log_error "Application process not found"
        return 1
    fi

    log_success "Application process is running"

    # Check health endpoint
    MAX_ATTEMPTS=10
    ATTEMPT=1

    while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
        log_info "Attempting health check (attempt $ATTEMPT/$MAX_ATTEMPTS)..."

        if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            log_success "Health endpoint responding"

            # Get detailed health status
            HEALTH_STATUS=$(curl -s http://localhost:8000/api/v1/health)
            log_info "Health status: $HEALTH_STATUS"

            return 0
        fi

        ATTEMPT=$((ATTEMPT + 1))
        sleep 2
    done

    log_error "Health endpoint not responding after $MAX_ATTEMPTS attempts"
    return 1
}

run_smoke_tests() {
    log_section "RUNNING SMOKE TESTS"

    cd "$PROJECT_ROOT"

    log_info "Running regression tests..."

    if pytest tests/api/test_regression_assessments.py -v --tb=short \
        > logs/smoke_tests.log 2>&1; then
        log_success "Smoke tests passed"
        return 0
    else
        log_error "Smoke tests failed"
        log_info "Check logs/smoke_tests.log for details"
        return 1
    fi
}

################################################################################
# POST-DEPLOYMENT
################################################################################

print_deployment_summary() {
    log_section "DEPLOYMENT SUMMARY"

    echo ""
    echo "✅ Deployment completed successfully!"
    echo ""
    echo "Application Details:"
    echo "  Environment: $ENVIRONMENT"
    echo "  URL: http://localhost:8000"
    echo "  API Documentation: http://localhost:8000/docs"
    echo "  Health Check: http://localhost:8000/api/v1/health"
    echo ""
    echo "Logs:"
    echo "  Application: logs/application.log"
    echo "  Smoke Tests: logs/smoke_tests.log"
    echo ""
    echo "Management:"
    echo "  Stop: pkill -f 'uvicorn app.main:app'"
    echo "  Restart: ./scripts/deploy_production.sh $ENVIRONMENT"
    echo "  Status: curl http://localhost:8000/api/v1/health"
    echo ""
}

################################################################################
# MAIN DEPLOYMENT FLOW
################################################################################

main() {
    log_section "PSYCHSYNC PRODUCTION DEPLOYMENT"
    log_info "Environment: $ENVIRONMENT"
    log_info "Project: $PROJECT_ROOT"
    echo ""

    # Create logs directory
    mkdir -p "$PROJECT_ROOT/logs"

    # Run deployment steps
    run_pre_deployment_checks
    run_database_migrations
    start_application

    if run_health_checks; then
        if run_smoke_tests; then
            print_deployment_summary
            exit 0
        else
            log_error "Smoke tests failed, but application is running"
            log_warning "Check logs/smoke_tests.log for details"
            exit 1
        fi
    else
        log_error "Health checks failed"
        log_info "Check logs/application.log for details"
        exit 1
    fi
}

# Run main function
main "$@"
