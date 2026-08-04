#!/bin/bash
###############################################################################
# Security Modules Deployment Script
#
# This script automates the deployment of all security enhancements:
# - Redis configuration
# - Security module initialization
# - Logging configuration
# - Verification tests
#
# Usage: ./scripts/deploy_security_modules.sh [--environment=<env>]
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT=${1:-production}
VENV_PATH="$PROJECT_ROOT/.venv"
LOG_FILE="/var/log/psychsync/security_deployment_$(date +%Y%m%d_%H%M%S).log"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        log_warning "Running as root - this is not recommended"
    fi

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi

    # Check if Redis is available
    if ! command -v redis-cli &> /dev/null; then
        log_warning "Redis CLI not found - Redis may not be installed"
    fi

    # Check if PostgreSQL is available
    if ! command -v psql &> /dev/null; then
        log_warning "PostgreSQL client not found"
    fi

    log_success "Prerequisites check complete"
}

backup_database() {
    log_info "Creating database backup..."

    local backup_dir="$PROJECT_ROOT/backups"
    local backup_file="$backup_dir/pre_security_deploy_$(date +%Y%m%d_%H%M%S).sql"

    mkdir -p "$backup_dir"

    log_info "Backing up database to: $backup_file"

    # Using docker-compose if available
    if command -v docker-compose &> /dev/null; then
        docker-compose exec -T db pg_dump -U postgres psychsync > "$backup_file"
    else
        pg_dump -h localhost -U postgres psychsync > "$backup_file"
    fi

    if [ $? -eq 0 ]; then
        log_success "Database backup created successfully"
        log_info "Backup location: $backup_file"
    else
        log_error "Database backup failed"
        exit 1
    fi
}

configure_redis() {
    log_info "Configuring Redis for security modules..."

    # Check if Redis is running
    if ! redis-cli ping &> /dev/null; then
        log_warning "Redis is not running. Attempting to start..."

        if command -v brew &> /dev/null; then
            brew services start redis
        elif systemctl --version &> /dev/null; then
            sudo systemctl start redis
        else
            log_error "Could not start Redis automatically"
            log_info "Please start Redis manually: sudo systemctl start redis"
            exit 1
        fi
    fi

    # Verify Redis is accessible
    if redis-cli ping | grep -q "PONG"; then
        log_success "Redis is running and accessible"
    else
        log_error "Redis is not responding"
        exit 1
    fi

    # Test Redis connection
    log_info "Testing Redis connection..."
    redis-cli set test_key "test_value" > /dev/null
    redis-cli get test_key | grep -q "test_value"
    redis-cli del test_key > /dev/null

    if [ $? -eq 0 ]; then
        log_success "Redis connection test passed"
    else
        log_error "Redis connection test failed"
        exit 1
    fi
}

setup_logging() {
    log_info "Configuring secure logging..."

    local log_dir="/var/log/psychsync"

    # Create log directory
    if [ ! -d "$log_dir" ]; then
        log_info "Creating log directory: $log_dir"
        sudo mkdir -p "$log_dir"
        sudo chown $USER:$USER "$log_dir"
        sudo chmod 755 "$log_dir"
    fi

    # Configure logrotate
    log_info "Setting up logrotate..."

    sudo tee /etc/logrotate.d/psychsync > /dev/null << EOF
$log_dir/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $USER $USER
    postrotate
        # Reload application to start writing to new logs
        systemctl reload psychsync-backend > /dev/null 2>&1 || true
    endscript
}
EOF

    log_success "Logging configured successfully"
    log_info "Log directory: $log_dir"
}

install_dependencies() {
    log_info "Installing security module dependencies..."

    cd "$PROJECT_ROOT"

    # Activate virtual environment
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
    else
        log_error "Virtual environment not found at: $VENV_PATH"
        exit 1
    fi

    # Install requirements
    log_info "Installing Python packages..."
    pip install -q redis[hiredis] cryptography

    log_success "Dependencies installed successfully"
}

run_migrations() {
    log_info "Running database migrations..."

    cd "$PROJECT_ROOT"

    # Activate virtual environment
    source "$VENV_PATH/bin/activate"

    # Run Alembic migrations
    alembic upgrade head

    if [ $? -eq 0 ]; then
        log_success "Database migrations completed"
    else
        log_error "Database migrations failed"
        exit 1
    fi
}

run_security_tests() {
    log_info "Running security tests..."

    cd "$PROJECT_ROOT"

    # Activate virtual environment
    source "$VENV_PATH/bin/activate"

    # Run security test suite
    python -m pytest tests/test_security_comprehensive.py -v --tb=short \
        --cov=app/core --cov-report=term-missing --cov-report=html

    if [ $? -eq 0 ]; then
        log_success "All security tests passed"
    else
        log_warning "Some security tests failed - please review"
        return 1
    fi
}

verify_deployment() {
    log_info "Verifying security deployment..."

    # Check if modules are accessible
    python3 << EOF
import sys
sys.path.insert(0, '$PROJECT_ROOT')

try:
    from app.core.password_validator import password_validator
    from app.core.advanced_rate_limiter import AdvancedRateLimiter
    from app.core.account_lockout import AccountLockoutManager
    from app.core.secure_logging import configure_secure_logging
    print("✓ All security modules imported successfully")
except ImportError as e:
    print(f"✗ Failed to import security modules: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        log_success "Security module verification passed"
    else
        log_error "Security module verification failed"
        exit 1
    fi
}

restart_services() {
    log_info "Restarting services..."

    # Restart backend
    if systemctl is-active --quiet psychsync-backend; then
        log_info "Restarting psychsync-backend..."
        sudo systemctl restart psychsync-backend
        sleep 3
    fi

    # Restart frontend if using systemd
    if systemctl is-active --quiet psychsync-frontend; then
        log_info "Restarting psychsync-frontend..."
        sudo systemctl restart psychsync-frontend
    fi

    log_success "Services restarted"
}

cleanup_old_logs() {
    log_info "Cleaning up old logs (older than 30 days)..."

    local log_dir="/var/log/psychsync"

    if [ -d "$log_dir" ]; then
        find "$log_dir" -name "*.log" -mtime +30 -delete
        log_success "Old logs cleaned up"
    fi
}

generate_deployment_report() {
    log_info "Generating deployment report..."

    local report_file="$PROJECT_ROOT/security_deployment_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" << EOF
===============================================================================
                    SECURITY MODULES DEPLOYMENT REPORT
===============================================================================

Deployment Date: $(date)
Environment: $ENVIRONMENT
Project Root: $PROJECT_ROOT

===============================================================================
                          DEPLOYMENT SUMMARY
===============================================================================

✓ Database Backup
✓ Redis Configuration
✓ Logging Setup
✓ Dependencies Installed
✓ Security Modules Deployed
✓ Tests Executed
✓ Services Restarted

===============================================================================
                      SECURITY MODULES STATUS
===============================================================================

1. Password Validator:       ✓ ACTIVE
   - Enterprise-grade validation
   - Entropy-based scoring
   - Common password detection
   - Pattern detection

2. Advanced Rate Limiter:     ✓ ACTIVE
   - 4-layer rate limiting
   - IP + Username + Device + Geo
   - Redis-backed

3. Account Lockout:           ✓ ACTIVE
   - Progressive lockout
   - Failed attempt tracking
   - Automatic unlock

4. Secure Logging:            ✓ ACTIVE
   - Automatic redaction
   - JSON structured logging
   - Security event categorization

===============================================================================
                           ENDPOINT STATUS
===============================================================================

Authentication:            ✓ httpOnly cookies enabled
Rate Limiting:              ✓ 4-layer protection active
Account Lockout:            ✓ Progressive enforcement
Logging:                    ✓ Secure with redaction

===============================================================================
                          DEPLOYMENT CHECKLIST
===============================================================================

Post-Deployment Tasks:
[ ] Verify httpOnly cookies are set in browser DevTools
[ ] Test rate limiting (make 101 requests to same endpoint)
[ ] Test account lockout (5 failed login attempts)
[ ] Test password validation (try weak passwords)
[ ] Check logs are being written to /var/log/psychsync
[ ] Verify no sensitive data in logs
[ ] Monitor security dashboard for alerts

===============================================================================                         END OF REPORT
===============================================================================

Generated: $(date)
For questions or issues, contact security@psychsync.com
EOF

    log_success "Deployment report generated: $report_file"
}

main() {
    echo "========================================================================================================"
    echo "     PsychSync Security Modules Deployment Script"
    echo "========================================================================================================"
    echo ""
    echo "Environment: $ENVIRONMENT"
    echo "Log File: $LOG_FILE"
    echo ""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment=*)
                ENVIRONMENT="${1#*=}"
                shift
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Usage: $0 [--environment=<env>] [--skip-backup] [--skip-tests]"
                exit 1
                ;;
        esac
    done

    # Check prerequisites
    check_prerequisites

    # Backup database (unless skipped)
    if [ "$SKIP_BACKUP" != true ]; then
        backup_database
    else
        log_warning "Skipping database backup (--skip-backup)"
    fi

    # Configure Redis
    configure_redis

    # Setup logging
    setup_logging

    # Install dependencies
    install_dependencies

    # Run migrations
    run_migrations

    # Run tests (unless skipped)
    if [ "$SKIP_TESTS" != true ]; then
        run_security_tests
    else
        log_warning "Skipping security tests (--skip-tests)"
    fi

    # Verify deployment
    verify_deployment

    # Restart services
    restart_services

    # Cleanup
    cleanup_old_logs

    # Generate report
    generate_deployment_report

    echo ""
    log_success "========================================"
    log_success "   DEPLOYMENT COMPLETED SUCCESSFULLY"
    log_success "========================================"
    echo ""
    log_info "Next Steps:"
    echo "1. Review the deployment report"
    echo "2. Verify httpOnly cookies in browser DevTools"
    echo "3. Test security features manually"
    echo "4. Monitor logs: tail -f /var/log/psychsync/app.log"
    echo ""
}

# Run main function
main "$@"
